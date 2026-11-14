from pathlib import Path
import sys,json,asyncio,importlib.util
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
root=Path('J:/FM08dev');b=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'FM08-Database-Tools/scratch'))
import collect_country_batch_ger_mex_mas_20261112 as w
spec=importlib.util.spec_from_file_location('shared_country_collector',root/'FmLauncher/data/research/PORTUGAL_PERU_NORWAY_POLAND_PREP_20261111/collect_sources.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.OUT=b;mod.shared.B=b;mod.shared.S=b/'sources'
async def main():
 for low,high in [(54,94),(94,134),(134,174),(174,207)]:
  sys.argv=['collector','rosters',str(low),str(high)]
  await mod.rosters()
  ts=w.read(b/'source-targets.json')
  for c in ts:
   if 'PlayersFetched'in c and (b/c['RosterFile']).exists()and(b/c['ProfileFile']).exists():c.pop('FetchError',None)
  w.dump(b/'source-targets.json',ts)
  print('BATCH_COMPLETE',low,high,sum('PlayersFetched'in c for c in ts),flush=True)
asyncio.run(main())
