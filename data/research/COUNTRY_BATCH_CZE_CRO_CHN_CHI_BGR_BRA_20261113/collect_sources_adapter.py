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
 raise RuntimeError('Preparation is initialized by the native-plan-first manifest; do not refreeze or reset this batch')
async def discover():
 if len({x['Country'] for x in read(B/'source-targets.json')})==6:raise RuntimeError('Allsixcountriesclosed: use explicitincremental targets/cache, never rediscover/refetch fullbatch')
 cache=shared.Cache();results=[]
 queries=[(c['Country'],c['SourceName']) for c in read(B/'competition-prep/source_competitions.json')]
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
 dump(B/"discovery.json",results);dump(B/"discovery-capture.json",dict(new_calls=cache.calls,cache_hits=cache.hits,provider_stopped=cache.stopped))
def collector():
 path=R/"PORTUGAL_PERU_NORWAY_POLAND_PREP_20261111/collect_sources.py"
 spec=importlib.util.spec_from_file_location("shared_collector_isl_nir_irl",path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 m.OUT=B;m.shared.B=B;m.shared.S=B/"sources";return m
async def resolve():
 m=collector();source=inspect.getsource(m.resolved_catalogues)
 old="calendar=c['Country']in['Norway','Peru']";new="calendar=c['Country']in['China','Chile','Brazil']";assert old in source;source=source.replace(old,new)
 dump(B/"collector-adapter-pins.json",dict(original_sha256=sha(Path(m.__file__)),adapter_sha256=sha(Path(__file__)),transformed_resolution_sha256=hashlib.sha256(source.encode()).hexdigest(),changes="Calendar countries China/Chile/Brazil; exact metadata display-label resolution and scope gate"))
 exec(compile(source,str(B/"configured_resolved_catalogues"),"exec"),m.__dict__);await m.resolved_catalogues()
async def rosters():
 current=read(B/'source-targets.json')
 signature=lambda xs:sorted((str(x['TMID']),x['Country'],str(x['APISeason'])) for x in xs)
 for country in sorted({x['Country'] for x in current}):
  slug=country.replace(' ','-');gate=read(B/'scope-closures'/(slug+'.json'));closed=B/'scope-closures'/(slug+'-targets.json')
  assert gate['Status']=='CLOSED_NATIVE_CASCADE_CLUB_IDENTITIES_AND_PARENTS'
  assert gate['TargetsSHA256']==sha(closed) and gate['SourceCollectionScopeApproved'] and gate['AllParentsResolvedOrExplicitDeferred']
  assert signature([x for x in current if x['Country']==country])==signature(read(closed))
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

