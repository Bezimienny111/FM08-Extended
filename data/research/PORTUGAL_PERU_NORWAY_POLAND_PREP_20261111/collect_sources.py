from pathlib import Path
import sys,json,asyncio,hashlib,collections
sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf-8')
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
import ss26prep_collect_20261110 as shared
from transfermarkt_api import Transfermarkt
shared.B=OUT;shared.S=OUT/'sources'
read=shared.read;dump=shared.dump
async def discover():
 cache=shared.Cache()
 async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache)as tm:
  queries=[('Portugal','Primeira Liga'),('Portugal','Liga Portugal 2'),('Portugal','Liga 3'),('Portugal','Campeonato Portugal'),('Portugal','Campeonato de Portugal'),('Portugal','Liga 3 Serie'),
    ('Peru','Liga 1'),('Peru','Liga 2'),('Norway','Eliteserien'),('Norway','OBOS'),('Norway','PostNord'),('Norway','Norsk Tipping')]
  results=[]
  for country,query in queries:
   name=country.lower()+'-'+query.lower().replace(' ','-')+'.json'
   path=OUT/'sources/tm-competitions'/('search-'+name)
   try:
    data=await shared.get(tm,path,'search_competitions',query)
    rows=[x for x in data.get('results',[])if x.get('country')in[country,{'Norway':'Norwegen','Portugal':'Portugal','Peru':'Peru'}[country]]]
    results.append(dict(country=country,query=query,file=str(path.relative_to(OUT)),results=rows))
    print(country,query,[(x.get('id'),x.get('name'),x.get('country'))for x in rows],flush=True)
   except Exception as e:
    results.append(dict(country=country,query=query,error=type(e).__name__+':'+str(e)));print('SEARCH_ERROR',country,query,str(e)[:100],flush=True)
 dump(OUT/'discovery.json',results)
 dump(OUT/'discovery-capture.json',dict(new_calls=cache.calls,cache_hits=cache.hits))
async def catalogues():
 cache=shared.Cache();comps=read(OUT/'source-competitions.json')
 async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache)as tm:
  async def one(c,year,kind):
   path=OUT/'sources/tm-competitions'/(c['id']+'-'+year+'-'+kind+'.json')
   try:
    value=await shared.get(tm,path,'competition_'+kind,c['id'],season_id=year)
    count=len(value.get('clubs',[]))if kind=='clubs'else sum(len(x.get('rows',[]))for x in value.get('tables',[]))
    print(c['Country'],c['id'],year,kind,count,flush=True)
   except Exception as e:dump(path.with_suffix('.error.json'),dict(error=type(e).__name__+':'+str(e),country=c['Country'],competition=c['id'],season=year,kind=kind))
  jobs=[(c,y,k)for c in comps for y in['2026','2025']for k in['clubs','table']]
  for i in range(0,len(jobs),3):await asyncio.gather(*(one(*x)for x in jobs[i:i+3]))
 dump(OUT/'catalogue-capture.json',dict(new_calls=cache.calls,cache_hits=cache.hits))
async def rosters():
 cache=shared.Cache();targets=read(OUT/'source-targets.json');low=int(sys.argv[2])if len(sys.argv)>2 else 0;high=int(sys.argv[3])if len(sys.argv)>3 else len(targets)
 async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache)as tm:
  async def one(c):
   tid=c['TMID'];base=OUT/'sources/tm-clubs'
   try:
    profile=await shared.get(tm,base/(tid+'-profile.json'),'club_profile',tid)
    roster=await shared.get(tm,base/(tid+'-players-real2026-api'+c['APISeason']+'.json'),'club_players',tid,season_id=c['APISeason'])
    c.update(ProfileFile=str((base/(tid+'-profile.json')).relative_to(OUT)),RosterFile=str((base/(tid+'-players-real2026-api'+c['APISeason']+'.json')).relative_to(OUT)),PlayersFetched=len(roster.get('players',[])))
    print('ROSTER',c['Country'],c['Name'],c['PlayersFetched'],flush=True)
   except Exception as e:c['FetchError']=type(e).__name__+':'+str(e);print('ROSTER_ERROR',c['Country'],c['Name'],str(e)[:100],flush=True)
  for i in range(low,high,3):
   await asyncio.gather(*(one(c)for c in targets[i:min(i+3,high)]));dump(OUT/'source-targets.json',targets)
 dump(OUT/('roster-capture-'+str(low)+'-'+str(high)+'.json'),dict(new_calls=cache.calls,cache_hits=cache.hits,range=[low,high],cards=sum(x.get('PlayersFetched',0)for x in targets),clubs_fetched=sum('PlayersFetched'in x for x in targets)))
async def resolved_catalogues():
 cache=shared.Cache();comps=read(OUT/'source-competitions.json');decisions=[]
 def years(name):
  import re
  values=re.findall(r'20\d{2}',str(name))
  if values:return tuple(int(x)for x in values)
  values=re.fullmatch(r'(\d{2})[/ -](\d{2})',str(name).strip())
  return tuple(2000+int(x)for x in values.groups())if values else()
 async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache)as tm:
  async def one(c):
   path=OUT/'sources/tm-competitions'/(c['id']+'-available-seasons.json')
   try:
    metadata=await shared.get(tm,path,'competition_seasons',c['id'])
    calendar=c['Country']in['Norway','Peru']
    expected=[(2026,),(2025,)]if calendar else[(2026,2027),(2025,2026)]
    selected=[]
    for wanted in expected:
     hits=[x for x in metadata.get('seasons',[])if years(x.get('name'))==wanted]
     if len(hits)!=1:raise ValueError('ambiguous_or_missing_season_display:'+str(wanted))
     selected.append(hits[0])
    c['CurrentSeason']=selected[0];c['PreviousCompletedSeason']=selected[1]
    c['SeasonMetadataFile']=str(path.relative_to(OUT))
    for label,choice in zip(['current','previous_completed'],selected):
     for kind in['clubs','table']:
      file=OUT/'sources/tm-competitions'/(c['id']+'-'+label+'-label'+str(choice['name']).replace('/','-')+'-id'+choice['id']+'-'+kind+'.json')
      value=await shared.get(tm,file,'competition_'+kind,c['id'],season_id=choice['id'])
      c[label+'_'+kind+'_file']=str(file.relative_to(OUT))
    decisions.append(dict(competition=c['id'],country=c['Country'],current=selected[0],previous=selected[1],metadata_file=c['SeasonMetadataFile'],rule='resolve actual season label to provider id independently per competition; never global year minus one'))
    print('RESOLVED',c['Country'],c['id'],[(x['name'],x['id'])for x in selected],flush=True)
   except Exception as e:c['SeasonResolutionError']=type(e).__name__+':'+str(e);print('RESOLUTION_ERROR',c['id'],str(e)[:120],flush=True)
  for i in range(0,len(comps),3):await asyncio.gather(*(one(c)for c in comps[i:i+3]));dump(OUT/'source-competitions.json',comps)
 dump(OUT/'season-resolution.json',decisions)
 dump(OUT/'resolved-catalogue-capture.json',dict(new_calls=cache.calls,cache_hits=cache.hits))
async def calendars():
 cache=shared.Cache();comps=read(OUT/'source-competitions.json');summary=[]
 async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache)as tm:
  for c in comps:
   if c['Country']not in['Norway','Peru']:continue
   path=OUT/'sources/tm-competitions'/(c['id']+'-current-clubs.json')
   try:
    value=await shared.get(tm,path,'competition_clubs',c['id'])
    summary.append(dict(competition=c['id'],country=c['Country'],current_clubs=len(value.get('clubs',[])),file=str(path.relative_to(OUT))))
    print('CURRENT_CATALOGUE',c['id'],len(value.get('clubs',[])),flush=True)
   except Exception as e:summary.append(dict(competition=c['id'],error=type(e).__name__+':'+str(e)))
  for code in['NO1','TDeA']:
   try:await shared.get(tm,OUT/'sources/tm-competitions'/(code+'-available-seasons.json'),'competition_seasons',code)
   except Exception as e:print('SEASON_ERROR',code,str(e)[:120],flush=True)
 dump(OUT/'calendar-current-catalogue.json',summary)
 dump(OUT/'calendar-capture.json',dict(new_calls=cache.calls,cache_hits=cache.hits))
if __name__=='__main__':
 if sys.argv[1]=='discover':asyncio.run(discover())
 elif sys.argv[1]=='catalogues':asyncio.run(catalogues())
 elif sys.argv[1]=='calendars':asyncio.run(calendars())
 elif sys.argv[1]=='resolved':asyncio.run(resolved_catalogues())
 elif sys.argv[1]=='rosters':asyncio.run(rosters())
 else:raise ValueError('unknown_phase')
