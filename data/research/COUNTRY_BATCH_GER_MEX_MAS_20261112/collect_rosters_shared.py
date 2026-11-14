from pathlib import Path
import sys,asyncio,json,importlib.util
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
root=Path('J:/FM08dev');sys.path.insert(0,str(root/'FM08-Database-Tools/scratch'))
import collect_country_batch_ger_mex_mas_20261112 as w
from transfermarkt_api import Transfermarkt
b=w.B;shared=w.shared();cache=shared.Cache();cs=w.read(b/'source-competitions.json')
targets={}
for c in cs:
 if c['id']in ['MEX1','MEX2']:continue
 z=w.read(b/c['current_clubs_file'])
 for row in z.get('clubs',[]):
  tid=str(row.get('id')or row.get('club_id'))
  if tid=='None':raise ValueError('missing club id')
  key=(c['Country'],tid)
  if key not in targets:targets[key]=dict(Country=c['Country'],TMID=tid,Name=row.get('name')or row.get('club_name'),RealLevel=c['RealLevel'],APISeason=c['current_season']['id'],RealSeason=c['current_season']['name'],Competitions=[])
  targets[key]['Competitions'].append(c['id'])
ts=list(targets.values());w.dump(b/'source-targets.json',ts)
from collections import Counter
print('TARGETS',dict(Counter(c['Country']for c in ts)),len(ts))
async def discover_lower():
 async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache)as tm:
  for query in ['Liga Premier Serie A','Liga Premier Serie B','Mexico Serie A','Malaysia A2']:
   z=await shared.get(tm,b/'sources/tm-competitions'/('search-lower-'+query.replace(' ','-')+'.json'),'search_competitions',query)
   print('LOWER',query,[(v.get('id'),v.get('name'),v.get('country'))for v in z.get('results',[])],flush=True)
 w.dump(b/'lower-discovery-capture.json',dict(new_calls=cache.calls,cache_hits=cache.hits))
asyncio.run(discover_lower())
path=root/'FmLauncher/data/research/PORTUGAL_PERU_NORWAY_POLAND_PREP_20261111/collect_sources.py'
spec=importlib.util.spec_from_file_location('shared_country_collector',path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.OUT=b;mod.shared.B=b;mod.shared.S=b/'sources'
sys.argv=['collector','rosters','0',str(len(ts))]
asyncio.run(mod.rosters())
