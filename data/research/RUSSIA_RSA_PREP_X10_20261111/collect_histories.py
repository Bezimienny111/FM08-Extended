import sys,asyncio,json
from pathlib import Path
sys.dont_write_bytecode=True;sys.path.insert(0,str(Path.cwd()/'FM08-Database-Tools/scratch'))
import ss26prep_collect_20261110 as c
B=Path.cwd()/'FmLauncher/data/research/RUSSIA_RSA_PREP_X10_20261111';S=B/'sources';c.B=B;c.S=S
async def run():
 cache=c.Cache();rosters=list((S/'tm-clubs').glob('*-players-2026.json'))
 pids=sorted({str(v['id'])for p in rosters for v in c.read(p).get('players',[])},key=int)
 print('HISTORY queue',len(pids),'rosters',len(rosters),flush=True)
 errors=[];done=0
 async with c.Transfermarkt(timeout=30,max_concurrency=3,transport=cache)as tm:
  async def one(pid):
   nonlocal done
   try:await c.get(tm,S/'tm-transfers'/(pid+'.json'),'player_transfers',pid)
   except Exception as e:
    errors.append(dict(TMID=pid,error=str(e)))
    if len(errors)<=4:print('HISTORY ERROR',pid,str(e)[:180],flush=True)
   done+=1
  for i in range(0,len(pids),3):
   if cache.stopped or cache.calls>=1995:break
   await asyncio.gather(*(one(pid)for pid in pids[i:i+3]))
   if done%150<3:print('HISTORY progress',done,'of',len(pids),'newcalls',cache.calls,'cachehits',cache.hits,'errors',len(errors),flush=True)
   if done%150<3:c.dump(B/'history-capture-progress.json',dict(queued=len(pids),rosters=len(rosters),processed=done,calls=cache.calls,hits=cache.hits,errors=errors))
 c.dump(B/('history-capture-'+str(len(rosters))+'.json'),dict(queued=len(pids),rosters=len(rosters),processed=done,calls=cache.calls,hits=cache.hits,errors=errors))
 print('HISTORY done',done,'/',len(pids),'calls',cache.calls,'hits',cache.hits,'errors',len(errors),flush=True)
asyncio.run(run())
