from pathlib import Path
import sys,json,asyncio,hashlib,shutil,importlib.util,inspect,datetime
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
import ss26prep_collect_20261110 as shared
shared.B=B;shared.S=B/'sources'
COUNTRIES={'England'}
read=shared.read;dump=shared.dump
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def valid_targets(xs):return sorted((str(c['TMID']),c['Country'],str(c['APISeason']))for c in xs)
async def collect(country):
 assert country in COUNTRIES,'Other countries are outside England source scope'
 slug=country.replace(' ','-');gatepath=B/'scope-closures'/(slug+'.json');targetpath=B/'scope-closures'/(slug+'-targets.json')
 gate=read(gatepath);assert gate['Status']=='CLOSED_NATIVE_CASCADE_CLUB_IDENTITIES_AND_PARENTS' and gate['SourceCollectionScopeApproved'] and gate['AllParentsResolvedOrExplicitDeferred']
 assert gate['TargetsSHA256']==sha(targetpath)
 original=read(targetpath);assert original and all(c['Country']==country for c in original) and len({str(c['TMID'])for c in original})==len(original)
 for c in original:assert c.get('TMID')and c.get('APISeason')is not None and c.get('RealSeason')and not c.get('ClubIdentityPending',False)
 progress=B/'roster-progress'/(slug+'-targets.json');progress.parent.mkdir(exist_ok=True)
 if not progress.exists():dump(progress,original)
 assert valid_targets(read(progress))==valid_targets(original),'Closed club list changed'
 # Reuse profiles/catalogues already read for closure, including original raw times.
 for src in (B/'competition-prep/sources/tm-raw').glob('*.json'):
  dest=B/'sources/tm-raw'/src.name;dest.parent.mkdir(parents=True,exist_ok=True)
  if not dest.exists():shutil.copy2(src,dest)
 source=R/'PORTUGAL_PERU_NORWAY_POLAND_PREP_20261111/collect_sources.py'
 spec=importlib.util.spec_from_file_location('existing_country_collector',source);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.OUT=B;mod.shared.B=B;mod.shared.S=B/'sources'
 text=inspect.getsource(mod.rosters);assert text.count("OUT/'source-targets.json'")==2
 text=text.replace("OUT/'source-targets.json'","OUT/'roster-progress/"+slug+"-targets.json'")
 text=text.replace("'roster-capture-'+str(low)","'roster-capture-"+slug+"-'+str(low)")
 exec(compile(text,str(source),'exec'),mod.__dict__)
 initial=[(i,c)for i,c in enumerate(read(progress))if 'PlayersFetched'not in c and not c.get('FetchError')]
 dump(B/('roster-start-'+slug+'.json'),dict(Status='PINNED_COUNTRY_SCOPE_COLLECTION_STARTED',Country=country,Clubs=len(original),ScopeGateSHA256=sha(gatepath),ClosedTargetsSHA256=sha(targetpath),SharedCollectorSHA256=sha(source),ConfiguredFunctionSHA256=hashlib.sha256(text.encode()).hexdigest(),NoDBWrite=True))
 # Bounded chunks keep the existing2000request cache budget and stop policy.
 for start in range(0,len(original),16):
  stop=min(start+16,len(original));current=read(progress)
  if all('PlayersFetched'in c and not c.get('FetchError')for c in current[start:stop]):continue
  if any(c.get('FetchError')for c in current[start:stop]):raise RuntimeError('Recorded source failure: review exact delta, do not refetch country')
  sys.argv=['collector','rosters',str(start),str(stop)];await mod.rosters()
  current=read(progress);errors=[c for c in current[start:stop]if c.get('FetchError')]
  if errors:
   dump(B/('roster-failure-'+slug+'.json'),dict(Status='STOP_REVIEW_CONCRETE_FAILED_CLUBS',Errors=errors,ScopeUnchanged=True));raise RuntimeError('Collection source failures; review only failed clubs')
  assert valid_targets(current)==valid_targets(original)
  print('COUNTRY_PROGRESS',country,stop,len(original),flush=True)
 final=read(progress);assert all('PlayersFetched'in c and not c.get('FetchError')for c in final)
 dump(B/('roster-complete-'+slug+'.json'),dict(Status='COUNTRY_ROSTERS_COLLECTED_SOURCE_ONLY',Country=country,Clubs=len(final),Cards=sum(c['PlayersFetched']for c in final),ProgressFile=str(progress.relative_to(B)),ProgressSHA256=sha(progress),ClosedTargetsSHA256=sha(targetpath),UIDAllocation=False,DBWrite=False))
 print('COUNTRY_SOURCE_COMPLETE',country,len(final),sum(c['PlayersFetched']for c in final),flush=True)
if __name__=='__main__':asyncio.run(collect(sys.argv[1]))

