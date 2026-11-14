import sys,asyncio,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True;sys.path.insert(0,str(Path.cwd()/'FM08-Database-Tools/scratch'))
import ss26prep_collect_20261110 as c
import httpx
B=Path.cwd()/'FmLauncher/data/research/RUSSIA_RSA_PREP_X10_20261111';S=B/'sources';c.B=B;c.S=S
queries=[('Cape Town City FC','Cape Town City'),('Gomora United','Gomora United'),('Highbury','Highbury'),('Hope FC','Hope FC'),('Hungry Lions FC','Hungry Lions'),('Leicesterford City FC','Leicesterford'),('Leicesterford/JDR','JDR Stars'),('Lerumo Lions','Lerumo Lions'),('Magesi FC','Magesi'),('Midlands Wanderers','Midlands Wanderers'),('North West University','North West University'),('NWU Soccer Institute','NWU Soccer Institute'),('Orbit College FC','Orbit College'),('Pretoria University FC','University of Pretoria'),('Real Native FC','Real Native'),('Casric/RealNative','Casric Stars'),('The Bees','The Bees'),('Upington City','Upington City'),('Venda FC','Venda')]
async def run():
 cache=c.Cache()
 async with httpx.AsyncClient(timeout=30,follow_redirects=True)as hc:
  res=await hc.get('https://www.psl.co.za/')
  res.raise_for_status();c.dump(S/'official/psl-home-20261111.json',dict(url=str(res.url),fetched_at=datetime.now(timezone.utc).isoformat(),status=res.status_code,sha256=hashlib.sha256(res.content).hexdigest(),body=res.text))
 async with c.Transfermarkt(timeout=30,max_concurrency=3,transport=cache)as tm:
  async def one(label,q):
   z=await c.get(tm,S/'tm-clubs'/('search-'+q.lower().replace(' ','-')+'.json'),'search_clubs',q)
   print('SEARCH',label,[(v['id'],v['name'],v.get('country'),v.get('squad')) for v in z.get('results',[])][:7],flush=True)
  for i in range(0,len(queries),3):await asyncio.gather(*(one(*q)for q in queries[i:i+3]))
 c.dump(B/'rsa-club-search-capture.json',dict(calls=cache.calls,hits=cache.hits))
asyncio.run(run())
