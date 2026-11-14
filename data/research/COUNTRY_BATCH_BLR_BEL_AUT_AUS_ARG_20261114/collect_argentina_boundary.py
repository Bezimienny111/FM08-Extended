from pathlib import Path
import sys,json,asyncio,datetime
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;ROOT=B.parents[3];sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
import ss26prep_collect_20261110 as shared
from transfermarkt_api import Transfermarkt
shared.B=B;shared.S=B/'sources'
async def main():
 cache=shared.Cache()
 async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache)as tm:
  for code in ['ARG3','AR3C','AR3D']:
   meta=await shared.get(tm,B/'competition-prep/sources/tm-competitions'/(code+'-available-seasons.json'),'competition_seasons',code)
   matches=[x for x in meta['seasons']if x['name']=='2025'];assert len(matches)==1
   y=matches[0]['id'];x=await shared.get(tm,B/'competition-prep/sources/tm-competitions'/(code+'-previous_completed-label2025-id'+y+'-clubs.json'),'competition_clubs',code,season_id=y);print(code,y,len(x['clubs']))
 shared.dump(B/'competition-prep/argentina-boundary-capture.json',dict(NewCalls=cache.calls,CacheHits=cache.hits,NoPlayers=True))
asyncio.run(main())

