"""Configuration adapter of shared collectors; no DB writes, ratings, UID or version allocation."""
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
 dump(B/"manifest.json",dict(status="PREPARING_SOURCE_CATALOGUES",countries=["Indonesia","India","Hong Kong"],snapshot_date="2026-11-12",calendar_countries=[],current_calendar_season=2026,previous_calendar_season=2025,Northern_Ireland_current_season="2026/27",Northern_Ireland_previous_completed="2025/26",source_db_written=False,output_database_created=False,version_reserved=False,api_football_calls=0,source_dates_shifted=False,CA_PA_generated=False,scope=["participants","source_players","profiles","DOB","worldwide_loans","owner_clubs","stadiums"],policies=dict(DOB="keep actual dates, no shift until future native preparation; no forced research/no fabricated dates",CA_PA="preserve reliable ratings; deterministic_v2_estimated_variation only at later native preparation",sugar_daddy="OFF all new families and independent readback",seasons="resolve metadata display name to provider ID independently; no global offset",provider="shared cache; stop403/429; no API-Football needed"),native_format_status="existing source evidence lookup pending; does not block gathering real squads",excluded=["native_DB_write","X14_X15_changes","other_batch_changes","EXE_or_game_changes","publication","shared_checkpoint_edits"]))
 print("IDN_IND_HKG source preparation initialized",flush=True)
async def discover():
 cache=shared.Cache();results=[]
 queries=[("Indonesia","BRI"),("Indonesia","Pegadaian"),("Indonesia","Nusantara"),("Indonesia","Indonesia"),("Indonesia","Indonesian")]
 async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache) as tm:
  for country,query in queries:
   path=B/"sources/tm-competitions"/("search-"+country.replace(" ","-")+"-"+query.replace(" ","-").replace("'","")+".json")
   try:
    value=await shared.get(tm,path,"search_competitions",query)
    results.append(dict(Country=country,Query=query,File=str(path.relative_to(B)),Results=value.get("results",[])))
    print(country,query,[(v.get("id"),v.get("name"),v.get("country")) for v in value.get("results",[])],flush=True)
   except Exception as e:
    results.append(dict(Country=country,Query=query,Error=type(e).__name__+":"+str(e)));print("DISCOVERY_ERROR",country,query,str(e)[:150],flush=True)
    if cache.stopped:break
 dump(B/"discovery-indonesia.json",results);dump(B/"discovery-indonesia-capture.json",dict(new_calls=cache.calls,cache_hits=cache.hits,provider_stopped=cache.stopped))
def collector():
 path=R/"PORTUGAL_PERU_NORWAY_POLAND_PREP_20261111/collect_sources.py"
 spec=importlib.util.spec_from_file_location("shared_collector_isl_nir_irl",path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 m.OUT=B;m.shared.B=B;m.shared.S=B/"sources";return m
async def resolve():
 m=collector();source=inspect.getsource(m.resolved_catalogues)
 old="calendar=c['Country']in['Norway','Peru']";new="calendar=c['Country']in['Norway','Peru','Iceland','Ireland']";assert old in source;source=source.replace(old,new)
 dump(B/"collector-adapter-pins.json",dict(original_sha256=sha(Path(m.__file__)),adapter_sha256=sha(Path(__file__)),transformed_resolution_sha256=hashlib.sha256(source.encode()).hexdigest(),changes="No calendar-country extension relevant; shared resolved catalogue implementation"))
 exec(compile(source,str(B/"configured_resolved_catalogues"),"exec"),m.__dict__);await m.resolved_catalogues()
async def rosters():
 m=collector();low=int(sys.argv[2]) if len(sys.argv)>2 else 0;end=int(sys.argv[3]) if len(sys.argv)>3 else len(read(B/"source-targets.json"))
 for start in range(low,end,40):
  stop=min(start+40,end);sys.argv=["collector","rosters",str(start),str(stop)];await m.rosters()
  ts=read(B/"source-targets.json");errors=[c for c in ts[start:stop] if c.get("FetchError")]
  if any(any(s in c["FetchError"] for s in ["403","429","Provider stopped"]) for c in errors):
   dump(B/"provider-stop.json",dict(range=[start,stop],errors=errors,rule="stop provider refusal; do not bypass"));break
  print("SOURCE_CHUNK_COMPLETE",start,stop,sum("PlayersFetched" in c for c in ts),flush=True)
if __name__=="__main__":
 action=sys.argv[1]
 if action=="begin":setup()
 elif action=="discover":asyncio.run(discover())
 elif action=="resolve":asyncio.run(resolve())
 elif action=="rosters":asyncio.run(rosters())
 else:raise ValueError(action)
