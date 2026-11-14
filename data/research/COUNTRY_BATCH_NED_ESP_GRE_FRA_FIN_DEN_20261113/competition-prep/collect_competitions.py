"""Six-country configuration of existing shared TM cache/get and catalogue pipeline; no rosters/DB writes."""
from pathlib import Path
import sys,json,asyncio,hashlib,datetime
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
import ss26prep_collect_20261110 as shared
from transfermarkt_api import Transfermarkt
B=Path(__file__).resolve().parent;shared.B=B;shared.S=B/'sources';dump=shared.dump;read=shared.read
QUERIES=[('Netherlands','Eredivisie'),('Netherlands','Eerste Divisie'),('Netherlands','Tweede Divisie'),('Spain','LaLiga'),('Spain','Segunda Division'),('Spain','Primera Federacion'),('Spain','Segunda Federacion'),('Spain','Tercera Federacion'),('Greece','Super League 1'),('Greece','Super League 2'),('Greece','Gamma Ethniki'),('France','Ligue 1'),('France','Ligue 2'),('France','National'),('France','National 2'),('France','National 3'),('Finland','Veikkausliiga'),('Finland','Ykkosliiga'),('Finland','Ykkonen'),('Finland','Kakkonen'),('Denmark','Superliga'),('Denmark','1. Division'),('Denmark','2. Division'),('Denmark','3. Division'),('Denmark','Danmarksserien')]
async def discover(country=None):
 cache=shared.Cache();results=[]
 async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache) as tm:
  for c,q in QUERIES:
   if country and c!=country:continue
   p=B/'sources/tm-competitions'/('search-'+c+'-'+q.replace(' ','-')+'.json')
   try:
    v=await shared.get(tm,p,'search_competitions',q);results.append(dict(Country=c,Query=q,File=str(p.relative_to(B)),Results=v.get('results',[])));print(c,q,[(x.get('id'),x.get('name'),x.get('country')) for x in v.get('results',[])],flush=True)
   except Exception as e:
    results.append(dict(Country=c,Query=q,Error=type(e).__name__+':'+str(e)));print('ERROR',c,q,str(e)[:140],flush=True)
    if cache.stopped:break
   dump(B/('discovery-'+(country or 'all')+'.json'),results)
 dump(B/('discovery-capture-'+(country or 'all')+'.json'),dict(NewCalls=cache.calls,CacheHits=cache.hits,Stopped=cache.stopped,AtUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),AdapterSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
if __name__=='__main__':
 if sys.argv[1]=='discover':asyncio.run(discover(sys.argv[2] if len(sys.argv)>2 else None))
 else:raise ValueError(sys.argv[1])
