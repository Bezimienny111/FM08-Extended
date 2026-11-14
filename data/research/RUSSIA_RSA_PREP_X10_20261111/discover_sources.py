import sys,json,asyncio
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path.cwd()/'FM08-Database-Tools/scratch'))
import ss26prep_collect_20261110 as col
ROOT=Path.cwd();B=ROOT/'FmLauncher/data/research/RUSSIA_RSA_PREP_X10_20261111';S=B/'sources'
col.B=B;col.S=S
async def run():
 cache=col.Cache()
 async with col.Transfermarkt(timeout=30,max_concurrency=3,transport=cache) as tm:
  jobs=[('rus-second','Russian First League'),('rsa-second','South Africa First Division')]
  for label,q in jobs:
   z=await col.get(tm,S/'tm-competitions'/('search-'+label+'.json'),'search_competitions',q)
   print('SEARCH',label,[(x.get('id'),x.get('name'),x.get('country')) for x in z.get('results',[])],flush=True)
  for cid in ['RU1','RU2','SFA1','SFA2']:
   try:
    z=await col.get(tm,S/'tm-competitions'/(cid+'-seasons.json'),'competition_seasons',cid)
    print('SEASONS',cid,str(z)[:1700],flush=True)
   except Exception as e:
    col.dump(B/('error-'+cid+'-seasons.json'),dict(error=str(e)))
    print('ERROR',cid,str(e)[:250],flush=True)
 col.dump(B/'discovery-capture.json',dict(calls=cache.calls,hits=cache.hits))
asyncio.run(run())
