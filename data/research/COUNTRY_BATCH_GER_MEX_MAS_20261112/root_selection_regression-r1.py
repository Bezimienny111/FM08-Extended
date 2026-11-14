"""Read-only X15 selection regression using prior witnessed loaders and bounds."""
from pathlib import Path
from collections import Counter
import hashlib,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(r"J:\FM08dev")
sys.path.insert(0,str(ROOT/"FM08-Database-Tools/scratch"))
from create_club_stadium_native_n1_20261108 import load
from create_native_u23_test import language_blocks
from audit_poland_v25_common_r1_20261108 import Cursor,lang_sections,find_table,club
R=ROOT/"FmLauncher/data/research"
B=R/"COUNTRY_BATCH_GER_MEX_MAS_20261112"
OUT=B/"root-selection-regression.json"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def main():
 assert __debug__ and not OUT.exists()
 freeze=read(B/"source-freeze.json");structure=read(B/"structure-root/structure-report.json")
 sources=[Path(freeze["frozen"]),Path(structure["output"])]
 exports=[B/"native-structure.json",B/"structure-root/native-structure-after.json"]
 cp=R/"SWEDEN_SELECTION_REPAIR_X5_20261110/runtime-X5-Sweden-members.json"
 overlays=read(cp)["load_time_changes"];assert len(overlays)==14
 reqs=[];seen=set()
 for origin,path,key in [
  ("Sweden_43",R/"SWEDEN_SELECTION_REPAIR_X6_20261110/verification.json","gates_after"),
  ("prior_X8_4countries_and_Sweden",R/"SINGAPORE_SELECTION_REPAIR_X8_20261110/verification.json","checks")]:
  for q in read(path)[key]:
   item=dict(uid=q["uid"],form=q["form"],minimum=q["minimum"],maximum=q["maximum"],origin=origin,qualification="prior_verified_requirements")
   sig=(item["uid"],item["form"],item["minimum"],item["maximum"])
   if sig not in seen:seen.add(sig);reqs.append(item)
 for origin,path in [
   ("X14_Portugal_Norway_Peru",R/"PORTUGAL_PERU_NORWAY_POLAND_PREP_20261111/native-competition-requirements.json"),
   ("X15_Germany_Mexico_Malaysia",B/"native-competition-requirements.json")]:
  for q in read(path)["requirements"]:
   for form in (0,1):
    lo=q["Form0Min"] if form==0 else q["Form1DefaultMin"]
    hi=q["Form0Max"] if form==0 else q["Form1DefaultMax"]
    hi=None if hi in (None,-1,4294967295) else hi
    if lo is None:continue
    item=dict(uid=q["CompetitionUID"],form=form,minimum=lo,maximum=hi,origin=origin,
      qualification="form0_native_limit" if form==0 else q.get("Form1Qualification","inherited_default_not_runtime_proof"))
    sig=(item["uid"],form,lo,hi)
    if sig not in seen:seen.add(sig);reqs.append(item)
 relevant={q["uid"] for q in reqs}
 profiles=[];overlay_proofs=[]
 for pos,source in enumerate(sources):
  expected=freeze["hashes"] if pos==0 else structure["output_hashes"]
  for n in ("server_db.dat","client_db.dat","lang_db.dat"):
   assert sha(source/n)==expected[n].lower()
  p0={n:sha(source/n) for n in ("server_db.dat","client_db.dat","lang_db.dat")}
  en,_=lang_sections(dict(language_blocks((source/"lang_db.dat").read_bytes()))[8])
  indices={i:r["uid"] for i,r in enumerate(en["comp"])}
  clubs,_,_=find_table(load(source,"client_db.dat"),[r["uid"] for r in en["club"]],club)
  server=load(source,"server_db.dat")
  rows=read(exports[pos])["records"];byuid={r["ClubUID"]:r for r in rows}
  assert len(byuid)==len(rows)
  raw={}
  for r in rows:
   assert server[r["Start"]]==10 and struct.unpack_from("<iI",server,r["Footer"])==(r["TeamIndex"],r["ClubUID"])
   cur,alt,regional=[struct.unpack_from("<i",server,r["Start"]+off)[0] for off in (7,15,47)]
   assert cur==r["CurrentDivisionIndex"]
   assert all(v==-1 or v in indices for v in (cur,alt,regional))
   raw[r["ClubUID"]]=[indices.get(v) for v in (cur,alt,regional)]
  loaded={uid:list(values) for uid,values in raw.items()}
  for override in overlays:
   uid=override["uid"];assert uid in loaded
   loaded[uid]=[override["runtime"][k] for k in ("primary","alternate","regional")]
   overlay_proofs.append(dict(source=pos,uid=uid,source_values=raw[uid],replayed_values=loaded[uid]))
  counts=[Counter(),Counter()];null_members=[]
  for uid,values in loaded.items():
   cur,alt,reg=values
   used=[cur,alt if alt is not None else cur]
   for form in (0,1):
    if used[form] is not None:counts[form][used[form]]+=1
    if reg is not None:counts[form][reg]+=1
   if not(relevant & {v for v in (cur,alt,reg) if v is not None}):continue
   row=byuid[uid];lo=row["RosterOffset"]+2+4*struct.unpack_from("<H",server,row["RosterOffset"])[0]
   hits=[]
   for at in range(lo+4,row["Footer"]-13):
    mode=server[at-3]
    if mode not in (0,1):continue
    ref=struct.unpack_from("<i",server,at)[0]
    limit=len(clubs) if mode==0 else len(en["nation"])
    if not(-1<=ref<limit):continue
    c=Cursor(server,at+4)
    try:
     c.string();c.byte();c.string();c.byte()
     if c.p==row["Footer"]:hits.append((mode,ref,at))
    except (AssertionError,UnicodeError,struct.error):continue
   assert len(hits)==1,("ambiguous country reference",uid,hits)
   mode,ref,at=hits[0]
   country=None if ref<0 else clubs[ref]["country_index"] if mode==0 else ref
   if country is None or country<0:null_members.append(dict(uid=uid,family_ref=ref,mode=mode,divisions=values))
  assert p0=={n:sha(source/n) for n in p0}
  profiles.append(dict(source=str(source),pins=p0,records=len(rows),raw=raw,counts=counts,null_members=null_members))
 assert set(profiles[0]["raw"])<=set(profiles[1]["raw"])
 for o in overlays:
  assert profiles[0]["raw"][o["uid"]]==profiles[1]["raw"][o["uid"]],("Sweden loader input changed",o["uid"])
 checks=[]
 for q in reqs:
  result=dict(q)
  for pos,p in enumerate(profiles):
   n=p["counts"][q["form"]][q["uid"]]
   result["before" if pos==0 else "after"]=n
   result["before_passed" if pos==0 else "after_passed"]=n>=q["minimum"] and(q["maximum"] is None or n<=q["maximum"])
  checks.append(result)
 cfg=read(B/"structure-root/structure-config.json")
 names={r["uid"]:r["names"][0] for r in en["comp"]}
 deltas=[]
 for form in (0,1):
  keys=set(profiles[0]["counts"][form])|set(profiles[1]["counts"][form])
  for uid in keys:
   a=profiles[0]["counts"][form][uid];b=profiles[1]["counts"][form][uid]
   if a!=b:deltas.append(dict(uid=uid,name=names.get(uid,""),form=form,before=a,after=b))
 failed=[q for q in checks if not q["after_passed"]]
 output=dict(status="STATIC_SELECTION_REGRESSION_PASS" if not failed and not profiles[1]["null_members"] else "FINDINGS_REQUIRE_REVIEW",
  scope="43 means Swedish conditions, NOT43countries; inherited X8 and X14 plus current batch limits",
  checks=checks,failed=failed,swedish_observed_overrides_replayed=14,
  swedish_inputs_preserved=True,source_country_null_members=profiles[0]["null_members"],
  target_country_null_members=profiles[1]["null_members"],count_deltas=deltas,
  source_pins=[dict(source=p["source"],pins=p["pins"],records=p["records"]) for p in profiles],
  overlay_evidence=str(cp),overlay_evidence_sha256=sha(cp),overlay_replay=overlay_proofs,
  data_modified=False,EXE_modified=False,runtime_test=False,
  limits="Historical loader replay and default form1 limits are conditional static checks; not a current live picker or season test",
  source_script_sha256=sha(Path(__file__)))
 OUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(dict(status=output["status"],checks=len(checks),failed=len(failed),null_members=len(profiles[1]["null_members"]),deltas=len(deltas)),ensure_ascii=True))
if __name__=="__main__":main()
