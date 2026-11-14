from pathlib import Path
import sys,asyncio,json
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8');ROOT=Path(r"J:/FM08dev");B=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
import ss26prep_collect_20261110 as shared
shared.B=B;shared.S=B/'sources'
from transfermarkt_api import Transfermarkt
NAMES=['Dollingstown','Ballymacash Rangers','Portstewart','Oxford Sunnyside','Dergview','Ballyclare Comrades','Knockbreda','Coagh United','Lisburn Distillery','Banbridge Town','St James Swifts','Rosario YC','St Mochtas','Midleton']
async def main():
 cache=shared.Cache();out=[]
 async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache) as tm:
  for name in NAMES:
   if cache.stopped:break
   path=B/'sources'/('search-'+name.replace(' ','-')+'.json')
   try:
    r=await shared.get(tm,path,'search_clubs',name)
    out.append(dict(Query=name,File=str(path.relative_to(B)),Results=r.get('results',[])))
    print(name,[(x.get('id'),x.get('name'),x.get('country')) for x in r.get('results',[])][:5],flush=True)
   except Exception as e:out.append(dict(Query=name,Error=type(e).__name__+':'+str(e)));print('ERROR',name,str(e)[:100],flush=True)
 shared.dump(B/'extra-club-search.json',out);shared.dump(B/'extra-club-search-capture.json',dict(new_calls=cache.calls,hits=cache.hits,stopped=cache.stopped))
if __name__=='__main__':asyncio.run(main())
