"""Six-country configuration of existing shared TM cache/get and catalogue pipeline; no rosters/DB writes."""
from pathlib import Path
import sys,json,asyncio,hashlib,datetime
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
import ss26prep_collect_20261110 as shared
from transfermarkt_api import Transfermarkt
B=Path(__file__).resolve().parent;shared.B=B;shared.S=B/'sources';dump=shared.dump;read=shared.read
QUERIES=[('Czech Republic', 'Chance Liga'), ('Czech Republic', 'Chance Narodni Liga'), ('Czech Republic', 'Ceska fotbalova liga'), ('Czech Republic', 'Moravskoslezska fotbalova liga'), ('Croatia', 'SuperSport HNL'), ('Croatia', 'Prva nogometna liga'), ('Croatia', 'Druga nogometna liga'), ('China', 'Chinese Super League'), ('China', 'China League One'), ('China', 'China League Two'), ('Chile', 'Liga de Primera'), ('Chile', 'Liga de Ascenso'), ('Chile', 'Segunda Division Profesional'), ('Bulgaria', 'efbet Liga'), ('Bulgaria', 'Vtora Liga'), ('Bulgaria', 'Treta Liga'), ('Brazil', 'Campeonato Brasileiro Serie A'), ('Brazil', 'Campeonato Brasileiro Serie B'), ('Brazil', 'Campeonato Brasileiro Serie C'), ('Brazil', 'Campeonato Brasileiro Serie D')]
async def discover(country=None):
 cache=shared.Cache();results=[]
 async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache) as tm:
  for c,q in QUERIES:
   if country and c!=country:continue
   p=B/'sources/tm-competitions'/('search-'+c+'-'+q.replace(' ','-')+'.json')
   try:
    v=await shared.get(tm,p,'search_competitions',q);results.append(dict(Country=c,Query=q,File=str(p.relative_to(B)),Results=v.get('results',[])));print(c,q,[(x.get('id'),x.get('name'),x.get('country')) for x in v.get('results',[])[:8]],'totalResults',len(v.get('results',[])),flush=True)
   except Exception as e:
    results.append(dict(Country=c,Query=q,Error=type(e).__name__+':'+str(e)));print('ERROR',c,q,str(e)[:140],flush=True)
    if cache.stopped:break
   dump(B/('discovery-'+(country or 'all')+'.json'),results)
 dump(B/('discovery-capture-'+(country or 'all')+'.json'),dict(NewCalls=cache.calls,CacheHits=cache.hits,Stopped=cache.stopped,AtUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),AdapterSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
if __name__=='__main__':
 if sys.argv[1]=='discover':asyncio.run(discover(sys.argv[2] if len(sys.argv)>2 else None))
 else:raise ValueError(sys.argv[1])
