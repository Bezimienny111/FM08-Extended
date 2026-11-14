"""Bounded final-phase collection through existing cache; no club/player collection."""
from pathlib import Path
import sys,json,asyncio,importlib.util,re,concurrent.futures
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
O=Path(__file__).resolve().parent;ROOT=Path('J:/FM08dev');sp=importlib.util.spec_from_file_location('existing_config',O/'collect_competitions.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
FIN=['F1CL','F1CC','FI3P','FI3R','FP3A','KP3B','KP3C','F3KA','F3KB','F3KC'];DEN=['DKMR','DKAR','DK2P','DK2R','DK3V','DKDA','D4P1','D4P2'];GRE=['POGR','S1PO','GRPL','S2PA','S2PO']
def years(label):
 a=re.findall(r'20\d{2}',str(label))
 if a:return tuple(map(int,a))
 b=re.fullmatch(r'(\d{2})[/ -](\d{2})',str(label).strip());return tuple(2000+int(x) for x in b.groups()) if b else ()
async def phases():
 cache=m.shared.Cache();rows=[]
 async with m.Transfermarkt(timeout=30,max_concurrency=3,transport=cache) as tm:
  async def one(country,code):
   meta=O/'sources/tm-competitions'/(code+'-available-seasons.json');row=dict(Country=country,id=code,Role='previous_final_phase',PrepareRoster=False)
   try:
    data=await m.shared.get(tm,meta,'competition_seasons',code);wanted=(2025,) if country=='Finland' else (2025,2026);sel=[x for x in data.get('seasons',[]) if years(x.get('name'))==wanted];assert len(sel)==1,('missing_previous_label',wanted);choice=sel[0];file=O/'sources/tm-competitions'/(code+'-previous-final-label'+choice['name'].replace('/','-')+'-id'+choice['id']+'-table.json');value=await m.shared.get(tm,file,'competition_table',code,season_id=choice['id']);row.update(Name=data.get('name'),Season=choice,MetadataFile=str(meta.relative_to(O)),TableFile=str(file.relative_to(O)),Tables=[dict(Name=g.get('name'),Rows=len(g.get('rows',[])),Matches=sorted({x.get('matches')for x in g.get('rows',[])},key=str))for g in value.get('tables',[])],Status='FETCHED');print('FINAL_PHASE',country,code,row['Tables'],flush=True)
   except Exception as e:row.update(Status='GAP',Error=type(e).__name__+':'+str(e));print('PHASE_GAP',country,code,str(e)[:150],flush=True)
   rows.append(row)
  jobs=[(c,i)for c,ids in [('Finland',FIN),('Denmark',DEN),('Greece',GRE)]for i in ids]
  for start in range(0,len(jobs),3):
   await asyncio.gather(*(one(*v)for v in jobs[start:start+3]));m.dump(O/'previous-final-phases.json',rows)
   if cache.stopped:break
 m.dump(O/'final-phase-capture.json',dict(NewCalls=cache.calls,CacheHits=cache.hits,Stopped=cache.stopped,Rows=len(rows)))
def archives():
 p=ROOT/'FmLauncher/data/research/COUNTRY_BATCH_ISL_NIR_IRL_20261112/competition-prep/fetch_competition_sources.py';sp=importlib.util.spec_from_file_location('existing_archive',p);a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);a.B=O;a.S=O/'sources'
 urls=[('finland-2025-rsssf','https://www.rsssf.org/tablesf/fin2025.html'),('denmark-2025-26-rsssf','https://www.rsssf.org/tablesd/den2026.html'),('denmark-2026-27-rsssf','https://www.rsssf.org/tablesd/den2027.html'),('greece-2025-26-rsssf','https://www.rsssf.org/tablesg/grk2026.html'),('greece-2026-27-rsssf','https://www.rsssf.org/tablesg/grk2027.html')]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:rows=list(pool.map(a.one,urls))
 m.dump(O/'web-source-index.json',rows)
 for x in rows:print('ARCHIVE',x['Name'],x['Status'],x.get('Bytes'),flush=True)
if __name__=='__main__':
 if sys.argv[1]=='phases':asyncio.run(phases())
 elif sys.argv[1]=='archives':archives()
 else:raise ValueError(sys.argv[1])
