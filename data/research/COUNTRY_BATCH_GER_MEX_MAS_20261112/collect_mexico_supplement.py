from pathlib import Path
import sys,json,asyncio
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
root=Path('J:/FM08dev');b=root/'FmLauncher/data/research/COUNTRY_BATCH_GER_MEX_MAS_20261112'
sys.path.insert(0,str(root/'FM08-Database-Tools/scratch'))
import collect_country_batch_ger_mex_mas_20261112 as w
from transfermarkt_api import Transfermarkt
s=w.shared();cache=s.Cache()
candidates=[('Irapuato','Irapuato',0,0,0,0),('Racing de Veracruz','Racing de Veracruz',3,1,24,71),('Real Apodaca','Real Apodaca',2,1,26,66),('Deportiva Venados','Deportiva Venados',3,2,24,52),('Tigres de Alica','Tigres de Alica',1,2,26,56),('Santiago FC','Santiago',2,2,26,51),('Tapachula FC','Tapachula',3,3,24,44),('Zacatepec','Zacatepec',2,3,26,45)]
async def main():
 results=[]
 async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache)as tm:
  for query,name,group,pos,played,pts in candidates:
   p=b/'sources/tm-clubs'/('search-supplement-'+query.replace(' ','-')+'.json')
   z=await s.get(tm,p,'search_clubs',query)
   rows=z.get('results',[]);results.append(dict(Name=name,Query=query,Group=group,PreviousPosition=pos,PreviousPlayed=played,PreviousPoints=pts,Results=rows,Source=str(p.relative_to(b))))
   print(query,[(v.get('id'),v.get('name'),v.get('country'))for v in rows],flush=True)
 w.dump(b/'mexico-supplement-identity-search.json',results);w.dump(b/'supplement-search-capture.json',dict(new_calls=cache.calls,cache_hits=cache.hits))
asyncio.run(main())
