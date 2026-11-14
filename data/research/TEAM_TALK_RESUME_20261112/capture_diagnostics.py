"""Offline diagnostics for frozen RPM captures. Never opens a process."""
import argparse
from collections import Counter
import hashlib
import html
import json
from pathlib import Path
from team_talk_model import decode_effect, native_ui_stage

class Rejected(ValueError):
    pass

NULL_LABELS = ((0x200, "Happy"), (0x400, "Unhappy"), (0x800, "Angered"),
 (0x1000, "Felt harshly treated"), (0x2000, "Looked delighted"),
 (0x4000, "Looked envious"), (0x8000, "Seemed confused"),
 (0x10000, "Didn't seem to be listening"))

def native_null_context_labels(effect):
    """B092E0 with param_2=NULL only; not a complete performance formatter."""
    decoded = decode_effect(effect)
    if decoded.unknown_bits:
        return {"status":"unsupported_unknown_bits", "labels":[]}
    labels = [label for mask,label in NULL_LABELS if effect & mask]
    return {"status":"native_null_context_profile",
            "labels":labels or ["Nothing specific noted"]}

def fingerprint(entries):
    rows = [(e["uid"],e["action"],e["context"]) for e in entries]
    if len(rows) != len(set(r[0] for r in rows)):
        raise Rejected("duplicate player UID in talk fingerprint")
    if any(not 0 < r[0] < 0xffffffff for r in rows):
        raise Rejected("placeholder UID in talk fingerprint")
    return tuple(sorted(rows))

def same_process(a,b):
    return a.get("pid")==b.get("pid") and a.get("creation_filetime")==b.get("creation_filetime") and a.get("sha256")==b.get("sha256")

def diagnostic(capture, human_capture):
    if not capture.get("snapshots_equal") or capture["first"] != capture["second"]:
        raise Rejected("torn or incomplete capture")
    if not human_capture.get("snapshots_equal") or human_capture["first"] != human_capture["second"]:
        raise Rejected("unstable frontend HUMAN capture")
    if not same_process(capture["process"],human_capture["process"]):
        raise Rejected("different process generation or EXE")
    human=human_capture["first"]["human"]
    if human["status"] != "VERIFIED_FRONTEND_HUMAN_MEMBER":
        raise Rejected("frontend HUMAN not admitted")
    s=capture["first"]
    slots=s["match_slots"]
    if not slots.get("controller_3c") or slots["controller_3c"] != slots.get("controller_2648"):
        raise Rejected("ambiguous MATCH identity")
    m=s["matches"]["controller_3c"]
    if m["address"] != slots["controller_3c"]:
        raise Rejected("MATCH slot mismatch")
    teams=[t for t in m.get("teams",[]) if t["core_team"]["address"]==human["team"] and t["core_team"]["uid"]==human["team_uid"]]
    if len(teams)!=1:
        raise Rejected("later HUMAN TEAM cannot uniquely correlate participant")
    t=teams[0]; manager=t["manager"]
    if manager["match_backlink"] != m["address"] or manager["team_backlink"] != t["address"]:
        raise Rejected("manager backlink mismatch")
    talk=manager.get("last_or_staged_talk") or {}
    entries=talk.get("entries",[])
    if len(entries) != talk.get("entry_count",len(entries)):
        raise Rejected("entry count mismatch")
    valid=[e for e in entries if 0 < e["uid"] < 0xffffffff]
    if len(valid)!=len(entries):
        raise Rejected("placeholder present in correlated manual talk")
    fp=fingerprint(valid)
    side=m["teams"].index(t)
    matching=[]
    for event in m.get("queue_events",[]):
        if event.get("type")!=7 or event.get("side")!=side or event.get("payload_phase")!=talk.get("phase"):
            continue
        try: same=fingerprint(event.get("entries",[]))==fp
        except Rejected: same=False
        if same and valid:
            matching.append({"timestamp":event["timestamp"],"phase":event["payload_phase"],
                             "tick_after_timestamp":m["tick"]>event["timestamp"]})
    count=manager["talk_counter"]
    raw_phase=m["phase"]
    kind={0:"prematch",1:"halftime"}.get(raw_phase,"unsupported")
    relevant=(count>0 and talk.get("phase")==raw_phase and bool(valid))
    return {
      "tag":capture["tag"],"captured_utc":capture["captured_utc"],
      "process":capture["process"],"match_address":m["address"],
      "tick":m["tick"],"raw_phase":raw_phase,"observed_talk_kind":kind,
      "status_hex":hex(m["status"]),"native_ui_stage":native_ui_stage(m["status"]),
      "talk_counter":count,"talk_slot":talk.get("slot"),"stored_talk_phase":talk.get("phase"),
      "talk_relevant_to_current_phase":relevant,
      "own_scope":"LATER_FRONTEND_TEAM_CORRELATION_ONLY",
      "human_capture_utc":human_capture["captured_utc"],"human_uid":human["person_uid"],
      "team_uid":human["team_uid"],"club_uid":human["club_uid"],
      "control_flags":manager["control_flags"],
      "controlled_side_raw":s["controller"]["controlled_side"],
      "matching_event7":matching,
      "completion_gate":"UNVERIFIED_CONDITIONAL_CFG_CANDIDATE",
      "edit_gate":"STANDARD_BUILDER_BLOCKED_AT_OBSERVED_RUNNING_STAGES_ONLY",
      "publication_ready":False,
      "effect_histogram":dict(Counter(hex(e["effect"]) for e in valid)),
      "players":[{"uid":e["uid"],"raw_effect":hex(e["effect"]),
                  "raw_flags":list(decode_effect(e["effect"]).names),
                  "null_context_feedback":native_null_context_labels(e["effect"])}
                 for e in valid]
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--captures",type=Path,default=Path(__file__).parent/"captures")
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    hp=a.captures/"frontend_human_8020_20261112T103744526014Z.json"
    human=json.loads(hp.read_text("utf-8"))
    out={"mode":"OFFLINE_DIAGNOSTIC_NOT_GAME_UI","publication_ready":False,
         "caveats":["Later HUMAN proof is not simultaneous with earlier MATCH captures.",
                    "No label predicts later performance.",
                    "Nothing specific noted does not mean no effect."],
         "inputs":[],"states":[],"rejections":[]}
    for f in sorted(a.captures.glob("*.json")):
        out["inputs"].append({"file":f.name,"sha256":hashlib.sha256(f.read_bytes()).hexdigest()})
        d=json.loads(f.read_text("utf-8"))
        if not d.get("tag"): continue
        try: out["states"].append(diagnostic(d,human))
        except (Rejected,KeyError) as e: out["rejections"].append({"file":f.name,"reason":str(e)})
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"diagnostics.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    chunks=['<!doctype html><meta charset="utf-8"><title>Team talk diagnostic</title>',
      '<style>body{font:16px system-ui;max-width:1150px;margin:2rem auto}table{border-collapse:collapse;width:100%}td,th{border:1px solid #aaa;padding:.4rem}small{color:#555}</style>',
      '<h1>Frozen team-talk captures</h1><p>Offline diagnostic. Publication in FM remains disabled.</p>',
      '<p>Later HUMAN proof correlates a participant; it does not retroactively prove simultaneous own scope. Native NULL-context feedback is separate from raw flags.</p>']
    for s in out["states"]:
        chunks += [f'<h2>{html.escape(s["tag"])} — tick {s["tick"]}, phase {s["raw_phase"]}</h2>',
          '<p>'+html.escape(f'Team {s["team_uid"]}; counter {s["talk_counter"]}; slot {s["talk_slot"]}; relevant={s["talk_relevant_to_current_phase"]}; effects={s["effect_histogram"]}')+'</p>',
          '<table><tr><th>UID</th><th>Raw effect</th><th>Native NULL-context feedback</th></tr>']
        for e in s["players"]:
            chunks.append('<tr><td>'+str(e["uid"])+'</td><td>'+e["raw_effect"]+'</td><td>'+html.escape("; ".join(e["null_context_feedback"]["labels"]))+'</td></tr>')
        chunks.append('</table>')
    (a.out/"diagnostics.html").write_text("\n".join(chunks),encoding="utf-8")
    print(json.dumps({"states":len(out["states"]),"rejected":len(out["rejections"]),"publication_ready":False}))
if __name__=="__main__": main()
