"""Configuration adapter of the shared source collector. No DB writes or output version reservation."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,asyncio,hashlib,importlib.util,inspect,collections
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding="utf-8")
ROOT=Path(r"J:\FM08dev");R=ROOT/"FmLauncher/data/research";B=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"FM08-Database-Tools/scratch"))
import ss26prep_collect_20261110 as shared
shared.B=B;shared.S=B/"sources"
from transfermarkt_api import Transfermarkt
read=shared.read;dump=shared.dump
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def setup():
 assert not (B/"manifest.json").exists()
 native=R/"COUNTRY_BATCH_GER_MEX_MAS_20261112"
 comps=read(native/"competition-catalog.json");nations=read(native/"native-nation-catalog.json");teams=read(native/"native-structure.json")["records"]
 wanted={229,748,594,596,595,905,906,909}
 counts=collections.Counter(t["CurrentDivisionIndex"] for t in teams)
 evidence=[dict(c,current_raw_teams=counts[c["index"]],proof_status="DAT_snapshot_only; native playable gates not yet established") for c in comps if c["index"] in wanted]
 dump(B/"native-format-evidence.json",dict(competitions=evidence,nations=[x for x in nations if x["index"] in [80,149,191]],source_snapshot=str(native.relative_to(ROOT)),source_pins={f:sha(native/f) for f in ["competition-catalog.json","native-nation-catalog.json","native-structure.json"]},status="source_preparation; raw_counts_are_not_engine_requirements",runtime_or_exe_modified=False))
 dump(B/"manifest.json",dict(status="SOURCE_PREPARATION_ONLY",countries=["South Korea","Colombia","Israel"],snapshot_date="2026-11-12",calendar_countries=["South Korea","Colombia"],calendar_current_season=2026,calendar_previous_completed=2025,Israel_current_season="2026/27",Israel_previous_completed="2025/26",source_base_policy="wait_for_accepted_X15_before_any_import; no DB snapshot copied here",source_db_written=False,output_version_reserved=False,api_football_calls=0,policies=dict(previous_tables="completed previous season only; Colombia cumulative/multiphase table requires explicit proof",source_dates="actual real DOB only; do not shift at collection",future_import_shift_years=19,sugar_daddy="OFF; independent readback all added club families",CA_PA="preserve reliable ratings; deterministic_v2_estimated_variation",missing_profiles="explicit gaps; no forced research/no fabricated DOB",loans="worldwide owner/player memberships; supported optional buy only; no mandatory buyout"),pipeline=dict(transport=str((ROOT/"FM08-Database-Tools/scratch/ss26prep_collect_20261110.py").relative_to(ROOT)),collector="FmLauncher/data/research/PORTUGAL_PERU_NORWAY_POLAND_PREP_20261111/collect_sources.py"),excluded=["DB_write","X14_X15_mutation","GER_MEX_MAS_batch_mutation","EXE_or_game_mutation","publication","root_checkpoint_edits"]))
 print("Source preparation initialized",flush=True)
async def discover():
 cache=shared.Cache();results=[]
 queries=[("South Korea","K League 1"),("South Korea","K League 2"),("South Korea","K3 League"),("Colombia","Liga Dimayor"),("Colombia","Torneo Dimayor"),("Colombia","Primera A"),("Colombia","Primera B"),("Israel","Ligat ha'Al"),("Israel","Liga Leumit"),("Israel","Liga Alef")]
 async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache) as tm:
  for country,query in queries:
   path=B/"sources/tm-competitions"/("search-"+country.replace(" ","-")+"-"+query.replace(" ","-").replace("'","")+".json")
   try:
    data=await shared.get(tm,path,"search_competitions",query);results.append(dict(country=country,query=query,file=str(path.relative_to(B)),results=data.get("results",[])))
    print(country,query,[(v.get("id"),v.get("name"),v.get("country")) for v in data.get("results",[])],flush=True)
   except Exception as e:
    results.append(dict(country=country,query=query,error=type(e).__name__+":"+str(e)));print("SEARCH_ERROR",country,query,str(e)[:130],flush=True)
    if cache.stopped:break
 dump(B/"discovery.json",results);dump(B/"discovery-capture.json",dict(new_calls=cache.calls,cache_hits=cache.hits,provider_stopped=cache.stopped))
def collector():
 path=R/"PORTUGAL_PERU_NORWAY_POLAND_PREP_20261111/collect_sources.py";spec=importlib.util.spec_from_file_location("shared_source_collector_kor_col_isr",path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 m.OUT=B;m.shared.B=B;m.shared.S=B/"sources"
 return m
async def resolve():
 m=collector();source=inspect.getsource(m.resolved_catalogues);before="calendar=c['Country']in['Norway','Peru']";after="calendar=c['Country']in['Norway','Peru','South Korea','Colombia']";assert before in source;source=source.replace(before,after)
 dump(B/"collector-adapter-pins.json",dict(original_sha256=sha(Path(m.__file__)),adapter_sha256=sha(Path(__file__)),transformed_resolution_sha256=hashlib.sha256(source.encode()).hexdigest(),change="calendar label resolution extended to South Korea/Colombia; no global season offset"))
 exec(compile(source,str(B/"adapted_resolved_catalogues"),"exec"),m.__dict__)
 await m.resolved_catalogues()
async def rosters():
 m=collector();start=int(sys.argv[2]) if len(sys.argv)>2 else 0;end=int(sys.argv[3]) if len(sys.argv)>3 else len(read(B/"source-targets.json"))
 for low in range(start,end,40):
  high=min(low+40,end);sys.argv=["collector","rosters",str(low),str(high)];await m.rosters()
  targets=read(B/"source-targets.json")
  errors=[x for x in targets[low:high] if x.get("FetchError")]
  if any("403" in x["FetchError"] or "429" in x["FetchError"] or "Provider stopped" in x["FetchError"] for x in errors):
   dump(B/"provider-stop.json",dict(range=[low,high],errors=errors,rule="do not restart around provider refusal"));break
  print("ROSTER_CHUNK_COMPLETE",low,high,sum("PlayersFetched" in c for c in targets),flush=True)
async def previous_phases():
 cache=shared.Cache();comps=read(B/"source-competitions.json");decisions=[]
 def years(name):
  import re
  parts=re.findall(r"20\d{2}",str(name))
  if parts:return tuple(map(int,parts))
  match=re.fullmatch(r"(\d{2})/(\d{2})",str(name))
  return tuple(2000+int(x) for x in match.groups()) if match else ()
 async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache) as tm:
  for c in comps:
   if c["Role"]!="final_phase" or c.get("previous_completed_table_file"):continue
   metadata_path=B/"sources/tm-competitions"/(c["id"]+"-available-seasons.json")
   metadata=read(metadata_path)
   wanted=(2025,2026) if c["Country"]=="Israel" else (2025,)
   selected=[x for x in metadata.get("seasons",[]) if years(x["name"])==wanted]
   if len(selected)!=1:
    decisions.append(dict(competition=c["id"],status="phase_source_unavailable_for_previous_completed_season",latest_available=metadata.get("seasons",[])[:1],action="use_main_competition_nested_final_tables_or_official_source"));continue
   choice=selected[0]
   try:
    for kind in ["clubs","table"]:
     path=B/"sources/tm-competitions"/(c["id"]+"-previous_completed-label"+choice["name"].replace("/","-")+"-id"+choice["id"]+"-"+kind+".json")
     await shared.get(tm,path,"competition_"+kind,c["id"],season_id=choice["id"])
     c["previous_completed_"+kind+"_file"]=str(path.relative_to(B))
    c["PreviousCompletedSeason"]=choice;c["CurrentPhaseNotRequiredForSourceRanking"]=True
    decisions.append(dict(competition=c["id"],status="previous_completed_phase_fetched",season=choice))
    print("PREVIOUS_PHASE",c["id"],choice,flush=True)
   except Exception as e:
    decisions.append(dict(competition=c["id"],status="fetch_error",error=type(e).__name__+":"+str(e)))
    if cache.stopped:break
 dump(B/"source-competitions.json",comps);dump(B/"previous-phase-resolution.json",decisions);dump(B/"previous-phase-capture.json",dict(new_calls=cache.calls,cache_hits=cache.hits,provider_stopped=cache.stopped))
if __name__=="__main__":
 action=sys.argv[1]
 if action=="begin":setup()
 elif action=="discover":asyncio.run(discover())
 elif action=="resolve":asyncio.run(resolve())
 elif action=="rosters":asyncio.run(rosters())
 elif action=="previous-phases":asyncio.run(previous_phases())
 else:raise ValueError(action)
