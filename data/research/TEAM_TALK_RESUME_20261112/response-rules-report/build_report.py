from pathlib import Path
import json,hashlib,shutil,re,struct,pefile
OUT=Path("FmLauncher/data/research/TEAM_TALK_RESUME_20261112/response-rules-report")
R5=Path("FmLauncher/data/research/GHIDRA_ENGINE_20261107_R5/decompiled")
INDEX=json.loads((R5/"function-index.json").read_text("utf-8"))
SHA="157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d"
assert INDEX["source_sha256"]==SHA
BY={f["address"]:f for f in INDEX["functions"]}
(OUT/"evidence").mkdir(exist_ok=True)
PINS={}
for address in "b0a830 b1aa70 b092e0 b0a600 b2d1f0 b2d280 b2d2f0 b2d3d0 b2d360 b2a920 b5c380 b48b90 b48ba0 f56800 f566e0 b63b10 6e18a0 6da050 b39f60 b39d50 b62c70 b48830 b48890".split():
 rec=BY["00"+address];source=R5/rec["path"];raw=source.read_bytes()
 assert hashlib.sha256(raw).hexdigest()==rec["sha256"]
 target=OUT/"evidence"/source.name;shutil.copy2(source,target)
 PINS[address]={"function":"0x00"+address,"path":target.relative_to(OUT).as_posix(),
                "sha256":rec["sha256"],"body_ranges":rec["body_ranges"],
                "lines":len(raw.decode("utf-8").splitlines())}
def ref(address,start,end):
 pin=PINS[address]
 return {"function":pin["function"],"file":pin["path"],"lines":[start,end],"sha256":pin["sha256"]}
def excerpt(address,start,end):
 return "\n".join((OUT/PINS[address]["path"]).read_text("utf-8").splitlines()[start-1:end])
pe=pefile.PE("fm.exe")
assert hashlib.sha256(Path("fm.exe").read_bytes()).hexdigest()==SHA
table=pe.get_data(0xb0bf4c-0x400000,17)
assert table.hex()=="0001020603060606040606060606060605"
actions_data=[
 (0,"None","team",44,52,"absence_of_selected_speech"),
 (1,"Angry","team",53,102,"deep_branch_not_fully_reconstructed"),
 (2,"Disappointing","team",103,148,"deep_branch_not_fully_reconstructed"),
 (4,"Encourage / You can win today","team",149,227,"selected_ordered_branch"),
 (8,"Sympathise / Unlucky not to be winning","team",228,249,"selected_outer_branches"),
 (16,"Pleased","team",250,370,"deep_branch_not_fully_reconstructed"),
 (32,"Thrilled","team",1171,1188,"deep_branch_not_fully_reconstructed"),
 (64,"Warn against complacency / Don't get careless","team",973,1020,"selected_outer_branches"),
 (128,"Wish luck","team",1021,1032,"selected_ordered_branch"),
 (256,"I expect a win","team",1032,1068,"shared_expectation_group"),
 (512,"Take revenge","team",954,972,"unreconstructed"),
 (1024,"For the fans!","team",1069,1092,"selected_score_split"),
 (2048,"Must show improvement","team",1093,1170,"shared_expect_better_group"),
 (4096,"Pick up where you left off!","team",903,951,"shared_same_again_group"),
 (8192,"Enjoy the rest of the game / Pressure off","team",654,862,"shared_no_pressure_group"),
 (16384,"Prove a point!","team",863,900,"shared_prove_point_group"),
 (32768,"Team","inheritance_selector",21,40,"inheritance_not_new_speech"),
 (65536,"Angry / Embarrassment","player",630,651,"deep_branch_not_fully_reconstructed"),
 (131072,"Disappointing / Not good enough","player",565,595,"deep_branch_not_fully_reconstructed"),
 (262144,"You have faith / You can make the difference!","player",596,627,"individual_faith_branch_partial"),
 (524288,"Pleased / Did well / Well done","player",524,562,"deep_branch_not_fully_reconstructed"),
 (1048576,"Delighted / Fantastic","player",407,455,"deep_branch_not_fully_reconstructed"),
 (2097152,"Expect better!","player",457,474,"shared_expect_better_group"),
 (4194304,"Pick up where you left off!","player",476,487,"shared_same_again_group"),
 (8388608,"No pressure!","player",388,405,"shared_no_pressure_group"),
 (16777216,"Expect a performance!","player",490,509,"shared_expectation_group"),
 (33554432,"Prove a point!","player",511,520,"shared_prove_point_group")]
actions=[]
for mask,name,scope,lo,hi,coverage in actions_data:
 actions.append({"mask":mask,"hex":hex(mask),"name_en":name,"name_en_is_contextual_family":True,
   "name_pl":None,"name_pl_status":"SI Polish resource not verified",
   "scope":scope,"label_evidence":ref("b0a830",lo,hi),"conditions_coverage":coverage,
   "menu_availability_phase0_phase1":"not exhaustively reconstructed",
   "confirmed_observation_phases":([0] if mask==4 else [1] if mask==64 else [])})
# Rules intentionally use raw helper labels when the football/trait meaning is not proven.
common={"phase_scope":[0,1],"guard":"common_negative_override_NOT_taken",
 "guard_raw_source":excerpt("b1aa70",195,278),
 "guard_evidence":ref("b1aa70",195,278),
 "warning":"The global earlier branch can bypass the nominal action branch. Local trees are not unconditional outcomes."}
A=lambda text:{"op":"raw_predicate","expression":text}
AND=lambda *args:{"op":"and","args":list(args)}
OR=lambda *args:{"op":"or","args":list(args)}
NOT=lambda arg:{"op":"not","arg":arg}
rules=[
 {"id":"encourage4","actions":["0x4"],"evidence":ref("b1aa70",1094,1152),
  "preconditions":common,
  "sequence":[
   {"draw":"uStack_1c = RANGE(-1000,2000)","note":"upper bound excluded"},
   {"call":"B39F60(0x40004,0,0,1)","note":"history-related helper; do not discard call/RNG effects"},
   {"draw":"d1=RNG(500)"},
   {"if":A("(int)(uStack_1c - (int)(short)P[A2A]/5) < d1"),
    "then":[{"draw":"d2=RNG(morale)"},
      {"if":A("d2==0"),"then":[
       {"draw":"d3=RANGE(-100,1000)"},{"if":A("d3 < P[F94]"),"then_effect_or":"0x4"},
       {"draw":"d4=RANGE(-3,2000)"},{"if":A("d4 < P[FF4]"),"then_effect_or":"0x20"}]}],
    "else":[{"draw":"d5=RANGE(20,500)"},
      {"if":AND(A("d5 < (int)uStack_1c"),A("RNG(P[DA4]+iVar24*(-10)) > (int)local_20")),
       "then_effect_or":"0x2010","meaning":"admired AND demotivate; mixed effect"}]},
   {"draw":"d6=RNG(10000); d7=RNG((short)P[A2A])"},
   {"if":A("d6<d7"),"then_effect_or":"0x204"},
   {"goto":"B1C329","shared_tail":[{"draw":"d8=RNG(500)"},
      {"if":A("d8 < (char)P[928]"),"then_effect_or":"0x1",
       "else":[{"draw":"d9=RNG(10000)"},{"if":A("d9 < (char)P[929]"),"then_effect_or":"0x90"}]}],
    "evidence":ref("b1aa70",591,608)}],
  "limits":["phase2 special case excluded from this phase0/1 report",
            "iVar24/local_20 are decompiler temporaries; see raw scope rather than treating them as stable named attributes",
            "later common postprocessing can add/change flags"]},
 {"id":"warn64","actions":["0x40"],"evidence":ref("b1aa70",1521,1596),"preconditions":common,
  "decision":{"if":OR(AND(A("!LOSING"),OR(A("WINNING"),A("M[AB8] <= G"))),
                          A("opponent[710] < own_team[710]"),A("B5C380(own_team)>69")),
    "then":[{"call":"history_count=B39F60(0x40,0,0,1)"},{"draw":"uStack_1c=RNG(20)"},
      {"draw":"d1=RNG(1000)"},{"if":A("history_count < d1"),"then":[
        {"call":"mental=B2D2F0(-1)"},
        {"if":A("iVar15 < mental"),"then_effect_or":"0x100",
         "else":[{"draw":"d2=RNG(5000)"},{"if":A("d2 < P[DA4]-iVar24*10"),
           "then":[{"draw":"d3=RNG(P[10C0]+2)"},{"if":OR(A("d3==0"),A("B63B10(2,manager)!=0")),
              "then_effect_or":"0x18"}],
           "else":[{"call":"mental2=B2D1F0(-1)"},{"if":A("iVar15<mental2"),"then_effect_or":"0x1"}]}]},
        {"draw":"d4=RNG(100)"},{"if":A("d4<P[FF4]"),"then_effect_or":"0x40",
         "else":[{"draw":"d5=RNG(morale)"},{"if":A("d5==0"),"then_effect_or":"0x40"}]}]}],
    "else":[{"effect_or":"0x8090","meaning":"confused + lower_professionalism + demotivate"},
      {"branch":"Additional unhappy path through B28380 / B2D3D0 / B2D2F0 / B63B10 not fully reconstructed"}]},
  "limits":["iVar15 is inherited temporary, not confirmed CA/PA or a single database trait",
            "Team+710 meaning unresolved; do not call it reputation as a fact"]},
 {"id":"sympathise8","actions":["0x8"],"evidence":ref("b1aa70",1153,1217),"preconditions":common,
  "decision":{"if":AND(A("!WINNING"),OR(A("LOSING"),A("B5C380(own_team)>64"))),
    "then":[{"call":"history_count=B39F60(8,0,0,1)"},{"draw":"d1=RANGE(-1000,50)"},
     {"if":AND(A("P[DA4]+(P[F94]-iVar24)*10 < d1"),A("B2D2F0(18)==0")),"then_effect_or":"0x10"},
     {"if":A("B63B10(2,0)!=0"),"then":{"if":A("effect has0x10"),
       "then_clear_bits":"0x10","else_effect_or":"0x1"}},
     {"if":A("LOSING"),"then":[{"if":A("RNG(morale)>5"),"then_effect_or":"0x20"},
         {"if":A("history_count<RNG(1000)"),"then_effect_or":"0x4"}]}],
    "else":[{"effect_or":"0x8098","meaning":"confused + demotivate + morale_drop + lower_professionalism"},
       {"branch":"unhappy/manager-context subpath partly unresolved"}]}},
 {"id":"wish_luck128","actions":["0x80"],"evidence":ref("b1aa70",1597,1643),"preconditions":common,
  "sequence":[{"draw":"unused=RANGE(-1000,2000)","note":"call retained even though its result appears unused"},
   {"call":"h=B39F60(0x80,0,0,1)"},{"draw":"d1=RNG(500)"},
   {"if":A("h-(short)P[A2A]/5 < d1"),
    "then":[{"if":A("RNG(morale)==0"),"then":[
      {"if":A("RANGE(-3,2000)<P[FF4]"),"then_effect_or":"0x24"},
      {"if":A("RNG(10000)<RNG((short)P[A2A])"),"then_effect_or":"0x204"},
      {"if":A("RNG(500)<(char)P[928]"),"then_effect_or":"0x1",
       "else":[{"if":A("RNG(10000)<(char)P[929]"),"then_effect_or":"0x90"}]}]}],
    "else":[{"if":AND(A("RANGE(20,500)<h"),A("RNG(P[DA4]-iVar24*10)>(int)uStack_1c")),
             "then_effect_or":"0x2010"}]}]},
 {"id":"no_pressure_group","actions":["0x2000","0x800000"],"evidence":ref("b1aa70",1644,1670),"preconditions":common,
  "sequence":[{"call":"unused=RANGE(-1000,2000)"},{"call":"h=B39F60(0x802000,0,0,1)"},{"draw":"d1=RNG(500)"},
   {"if":AND(A("h-(short)P[A2A]/5 < d1"),A("P[FF4] <= RNG(100)")),
    "then":[{"if":AND(A("B2D280(-1)!=0"),A("RNG(morale)!=0")),"then_effect_or":"0x20"},
      {"if":OR(A("B2D2F0(-1)==0"),AND(A("context_bits&0x100000"),A("fresh B2D2F0(-1)<P[F94]/10+5"))),
       "then_effect_or":"0x10","note":"second alternative depends on raw context bits, not the action mask"}]}],
  "limits":["Only the two pure actions enter this shared arm after earlier action masks are excluded."]},
 {"id":"for_fans_score_split","actions":["0x400"],"evidence":ref("b1aa70",1723,1792),"preconditions":common,
  "decision":{"if":A("G<3"),"then":[
    {"set":"s=0; if((opp_goals-M[AB8])-own_goals>2 AND B2D2F0(-1)>10) s=5"},
    {"branch":"history/RNG(500), B2D360 and relationship-like fields924/925 plus B54020/B53FE0 choose morale boost, pressure or demotivation; exact raw source attached"}],
   "else":[{"effect_or":"0x8000"},
       {"if":A("B2D280(-1)==0"),"then_effect_or":"0x40"},
       {"if":A("(char)P[924] <= P[108C]"),"then":[
         {"if":A("B2D2F0(-1)==0"),"then_effect_or":"0x10",
          "else":[{"if":A("B63B10(3,0)!=0"),"then_effect_or":"0x10"}]}]}]},
   "limits":["G includes own/opponent +5A0 and +8 score components; not necessarily only the visible single-leg score."]},
 {"id":"mechanics_motivation_priority","evidence":ref("b1aa70",2590,2646),
  "decision":{"if":A("effect&0x2"),"then":"P[F98]+=RNG(50), then native branch-specific clamp",
    "else":{"if":A("effect&0x1"),"then":"P[F98]+=RNG(25), then native branch-specific cap",
      "else":{"if":A("(effect&0x5010)==0x5010"),"then":"P[F98]-=50+RNG(50)",
        "else":{"if":A("effect&0x5010"),"then":"P[F98]-=RNG(50)"}}}},
  "phase_guard":"phase !=5; applies to0/1","field_semantics":"match drive/motivation-like state inferred; not a confirmed DB attribute name"},
 {"id":"mechanics_morale_priority","evidence":ref("b1aa70",2647,2680),
  "decision":{"if":A("(effect&0x2004)==0x2004"),"then":"morale +=5+RNG(5)",
    "else":{"if":A("(effect&0x2004)!=0"),"then":"morale +=RNG(5)",
      "else":{"if":A("(effect&0x5008)==0x5008"),"then":"morale -=5+RNG(5)",
        "else":{"if":A("(effect&0x5008)!=0"),"then":"morale -=RNG(5)"}}}},
  "after":"clamp morale to1..20; recompute P[F90] with B2D5F0",
  "zero_delta_possible":True}
]
for rule in rules:
 r=rule["evidence"];address=r["function"][4:];lo,hi=r["lines"]
 rule["raw_source"]=excerpt(address,lo,hi)
unknown=[
 "Complete common prelude/negative override has exact source but is not fully converted into named football predicates.",
 "Exact UI menu availability for every mask and phase is not exhaustively reconstructed.",
 "Full trees for Angry, Disappointing, Pleased, Thrilled and most individual praise/criticism remain unexpanded.",
 "Fields1058/110C/1110/44C and their randomized helpers are not safely mapped to named hidden DB attributes.",
 "Relationship getter argument roles and some decompiler inherited temporaries/calling conventions remain unresolved.",
 "Later common modifiers and repeated-history reactions may alter the local branch outcome.",
 "Postmatch behavior excluded, even where shared formatter contains postmatch variants."]
doc={"schema_version":1,"scope":{"phases":[{"raw":0,"name":"prematch"},{"raw":1,"name":"ordinary halftime"}],
 "postmatch_excluded":True,"completeness":"PARTIAL_RULE_MATRIX_WITH_COMPLETE_CONFIRMED_NAME_FAMILIES",
 "game_process_read":False,"game_state_changed":False},"source_sha256":SHA,
 "mapping_proof":{"lookup_address":"0x00b0bf4c","lookup_bytes_hex":table.hex(),"entries":17,
 "dispatch_instruction":"00b0a93a movzx ecx,byte ptr[eax+0xb0bf4c];00b0a941 jmp[ecx*4+0xb0bf30]",
 "mapped_cases":{str(i):table[i] for i in [0,1,2,4,8,16]},
 "default_case":6,"case_index_is_not_action_mask":True},
 "notation":{"RNG(n)":"B48B90 -> F56800, integer result0..n-1 for admitted positive n",
 "RANGE(a,b)":"B48BA0 swaps endpoints if needed then min+RNG(max-min); upper endpoint excluded",
 "G":"own(TEAM+5A0 +TEAM+8)-opponent(TEAM+5A0+TEAM+8)",
 "WINNING":"6E18A0(own_team,0); aggregate score plus tie-break helper",
 "LOSING":"6DA050(own_team,0); aggregate score plus tie-break helper",
 "P[hex]":"raw player runtime offset; no automatic DB personality-name mapping",
 "M[hex]":"match-manager raw runtime offset",
 "morale":"signed byte P+9CC, later clamped1..20",
 "helpers":"Repeated calls are fresh calls, sometimes fresh RNG; do not coalesce.",
 "raw_variables":"Decompiled source aliases are preserved; undefined/inherited aliases are NOT executable specifications."},
 "actions":actions,"rules":rules,"unknowns":unknown,"sources":list(PINS.values()),
 "runtime_examples":[{"phase":"prematch","action":"0x4","name":"Encourage","counts":{"0":5,"1":1,"0x2010":4,"0x2011":1}},
 {"phase":"halftime","action":"0x40","name":"Warn against complacency","counts":{"0":3,"0x100":5,"1":3}}],
 "runtime_example_warning":"One already recorded match; counts are not general probabilities. No new RPM performed."}
(OUT/"conditions.json").write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(OUT/"source-pins.json").write_text(json.dumps({"source_sha256":SHA,"sources":list(PINS.values())},indent=2)+"\n",encoding="utf-8")
print("Saved conditions:",len(actions),"name/selector entries;",len(rules),"rule groups;",len(PINS),"pinned functions")
