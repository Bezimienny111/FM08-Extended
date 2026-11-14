"""Use the existing resolved_catalogues function; season labels are verified per competition."""
from pathlib import Path
import sys,json,asyncio,importlib.util,inspect,hashlib
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');O=Path(__file__).resolve().parent;R=ROOT/'FmLauncher/data/research';sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
sp=importlib.util.spec_from_file_location('shared_six_country_catalogue',R/'PORTUGAL_PERU_NORWAY_POLAND_PREP_20261111/collect_sources.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);m.OUT=O;m.shared.B=O;m.shared.S=O/'sources'
text=inspect.getsource(m.resolved_catalogues);old="calendar=c['Country']in['Norway','Peru']";assert old in text;text=text.replace(old,"calendar=c['Country']in['Belarus','Argentina']");exec(compile(text,str(O/'configured_resolved_catalogues'),'exec'),m.__dict__)
async def main():
 await m.resolved_catalogues();comps=m.read(O/'source-competitions.json');bootstrap={}
 for c in comps:
  if c.get('SeasonResolutionError'):continue
  assert c['CurrentSeason']['name'] in ['26/27','2026'] and c['PreviousCompletedSeason']['name'] in ['25/26','2025']
  clubs=m.read(O/c['current_clubs_file'])['clubs']
  for x in clubs:
   key=(c['Country'],x['id'])
   if key not in bootstrap:bootstrap[key]=dict(Country=c['Country'],TMID=x['id'],Name=x['name'],RealLevel=c['RealLevel'],RealSeason=c['CurrentSeason']['name'],APISeason=c['CurrentSeason']['id'],CurrentCatalogueFile='competition-prep/'+c['current_clubs_file'].replace('\\','/'),SourceCompetition=c['id'],Competitions=[c['id']],Role=c.get('Role','main'))
   else:bootstrap[key]['Competitions'].append(c['id']);bootstrap[key]['RealLevel']=min(bootstrap[key]['RealLevel'],c['RealLevel'])
 canonical=[]
 for c in comps:
  x=dict(c)
  for k,v in list(x.items()):
   if k.endswith('_file') or k=='SeasonMetadataFile':x[k]='competition-prep/'+v.replace('\\','/')
  x['SeasonPolicy']='Current26/27 for winter countries and real2026 for Belarus/Argentina; previous25/26 or2025 relative to chosen current, not latest arbitrary finished table; future transfers excluded'
  canonical.append(x)
 m.dump(O/'source_competitions.json',canonical);m.dump(O/'source-targets-bootstrap.json',list(bootstrap.values()));m.dump(O/'catalogue-adapter-pins.json',dict(SharedCollector=str(Path(m.__file__)),SharedCollectorSHA256=hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest(),AdapterSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),CalendarAdjustment='Only Belarus/Argentina are calendar; exact display-label metadata resolution percompetition; previous season relative to chosen current',MetadataResolutionFunctionSHA256=hashlib.sha256(text.encode()).hexdigest(),SourceDatesUnshifted=True,DBWrites=False,APIfootballCalls=0))
 for c in [x for x in canonical if not x.get('SeasonResolutionError')]:print('READY',c['Country'],c['id'],c['CurrentSeason']['name'],c['CurrentSeason']['id'],'clubs',len(m.read(O.parent/c['current_clubs_file'])['clubs']),flush=True)
 print('PROVISIONAL_CATALOGUE_TARGETS',len(bootstrap),'ROSTERS_REMAIN_LOCKED',flush=True)
if __name__=='__main__':asyncio.run(main())
