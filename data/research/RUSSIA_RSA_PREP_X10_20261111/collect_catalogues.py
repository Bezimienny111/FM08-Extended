import sys,asyncio
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path.cwd()/'FM08-Database-Tools/scratch'))
import ss26prep_collect_20261110 as c
B=Path.cwd()/'FmLauncher/data/research/RUSSIA_RSA_PREP_X10_20261111';S=B/'sources';c.B=B;c.S=S
async def run():
 cache=c.Cache()
 async with c.Transfermarkt(timeout=30,max_concurrency=3,transport=cache) as tm:
  for label,q in [('motsepe','Motsepe'),('nationalfirst','National First Division'),('southafrica','South Africa'),('ru3','Second League A')]:
   try:
    z=await c.get(tm,S/'tm-competitions'/('search-'+label+'.json'),'search_competitions',q)
    print('SEARCH',label,[(v.get('id'),v.get('name'),v.get('country')) for v in z.get('results',[])],flush=True)
   except Exception as e:print('ERROR search',label,str(e)[:160],flush=True)
  for cid in ['RU1','RU2','SFA1']:
   for yr in ['2026','2025']:
    for kind in ['clubs','table']:
     z=await c.get(tm,S/'tm-competitions'/(cid+'-'+yr+'-'+kind+'.json'),'competition_'+kind,cid,season_id=yr)
     print('CATALOG',cid,yr,kind,str(z)[:4500],flush=True)
 c.dump(B/'catalogue-capture.json',dict(calls=cache.calls,hits=cache.hits))
asyncio.run(run())
