"""Independent X18 selection numeric QA: prior233 + six-country92, no native writes."""
from pathlib import Path
from collections import Counter
import sys,json,hashlib,datetime,importlib.util,re,argparse
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research'
B=R/'COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113';N=B/'native-prep';W=N/'root-structure';O=Path(__file__).resolve().parent
TEMPLATE=R/'COUNTRY_BATCH_IDN_IND_HKG_20261112/independent-selection-qa-r2/selection_regression.py'
sp=importlib.util.spec_from_file_location('x17_numeric_selection',TEMPLATE);prev=importlib.util.module_from_spec(sp);sp.loader.exec_module(prev)
read=prev.read;sha=prev.sha
CA=R/'GHIDRA_ENGINE_20261107_R5/decompiled/functions/ram_ca6460.c';LOADER=CA.with_name('ram_c34a40.c')
OVERSEAS={int(x,16) for x in re.findall(r'iVar1 == (0x[0-9a-f]+)',CA.read_text(encoding='utf-8-sig'))}
assert OVERSEAS=={0xe0004,0xdfff8,0x5a1,0x1f9fc,0xdfffa,0xdfffe,0xe04d9,0xe0006,0xe04d4,0xe04dc,0xe0822}
ES_CHILD=set(range(67023610,67023628));ES_PARENT=7449905;GENERIC=1301432
CACHE=O/'source-profile-cache.json'
def dump(name,x):(O/name).write_text(json.dumps(x,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
def signature(qs):return hashlib.sha256(json.dumps(qs,sort_keys=True).encode()).hexdigest()
def requirements():
 old,pins=prev.requirements();assert len(old)==233
 path=B/'competition-prep/native-competition-requirements.json';n=read(path);pins[str(path)]=sha(path)
 assert len(n['requirements'])==46 and n['RequiredChecksBothForms']==92 and n['PlayableLevels']==16
 for p,h in n['SourcePins'].items():assert sha(Path(p))==h;pins[p]=h
 qs=list(old)
 for x in n['requirements']:
  scoped=bool(x.get('CountrySpecific'));assert not scoped or x['CompetitionUID']==GENERIC
  for form in [0,1]:
   lo=x['Form0Min'] if form==0 else x['Form1DefaultMin'];hi=x['Form0Max'] if form==0 else x['Form1DefaultMax'];assert lo is not None
   qs.append(dict(uid=x['CompetitionUID'],form=form,minimum=lo,maximum=prev.prev.limits(hi,lo),country=x['Country'] if scoped else None,country_fallback_uid=x.get('CountryFallbackUID'),origin='current_X18_six_countries',qualification='native requirements; loadedCurrent overlay then rawALT fallback; regional membership deduplicated; Sweden14 historicalALT explicit exception'))
 assert len(qs)==325 and qs[:233]==old
 for f in [TEMPLATE,Path(prev.TEMPLATE),CA,LOADER,B/'competition-prep/spain-third-loader-evidence.json']:pins[str(f)]=sha(f)
 ev=read(B/'competition-prep/spain-third-loader-evidence.json');assert ev['CurrentChildUIDs']==sorted(ES_CHILD) and ev['ParentUID']==ES_PARENT and sha(LOADER)==ev['SHA256']
 return qs,pins

def recount(p,relevant):
 counts=[Counter(),Counter()];cc=[Counter(),Counter()];nulls=[];nr=[]
 for uid,(cur,alt,regional) in p['loaded'].items():
  for form,selected in enumerate([cur,alt if alt is not None else cur]):
   for comp in {selected,regional}-{None}:
    counts[form][comp]+=1
    if p['countries'][uid] is not None:cc[form][(p['countries'][uid],comp)]+=1
  if p['countries'][uid] is None:
   item=dict(UID=uid,Divisions=p['loaded'][uid],Kind=p['kinds'][uid]);nulls.append(item)
   if relevant & {x for x in p['loaded'][uid] if x is not None}:nr.append(item)
 p.update(counts=counts,countrycounts=cc,nulls=nulls,nullrelevant=nr)
 return p

def extra_loaded_current(country,kind,nationuid,current):
 if kind==0 and country==170 and current in ES_CHILD:current=ES_PARENT
 # CA6460 classifies eleven raw nationUIDs; C34A40 loop236..243 calls A860A0(Lower).
 # It is not a list of COMPUIDs or a filter to hide territory participants.
 if nationuid in OVERSEAS:current=GENERIC
 return current

def profile(path,expected,export,overlays,relevant):
 p=prev.read_profile(path,expected,export,overlays,relevant)
 p['kinds']={u:t['TEAMKind'] for u,t in p['tailproof'].items()};p['extra_replay']=[]
 assert p['nations'][170]==796
 for u,vals in p['loaded'].items():
  cur=vals[0];country=p['countries'][u];new=extra_loaded_current(country,p['kinds'][u],p['nations'].get(country),cur)
  if new!=cur:p['extra_replay'].append(dict(UID=u,CountryIndex=country,NationUID=p['nations'].get(country),Kind=p['kinds'][u],CurrentBefore=cur,CurrentAfter=new,RawAlternateUnchanged=vals[1],RegionalUnchanged=vals[2]));vals[0]=new
 return recount(p,relevant)

def cache_source(p,reqs,pins):
 data=dict(Status='PINNED_SOURCE_ONLY',ScriptSHA256=sha(Path(__file__)),RequirementsSHA256=signature(reqs),EvidencePins=pins,FreezeSHA256=sha(N/'source-freeze.json'),ExportSHA256=sha(N/'native-structure.json'),path=p['path'],pins=p['pins'],records=p['records'],nations=p['nations'],nationnames=p['nationnames'],names=p['names'],replays=p['replays'],indonesia_replay=p['indonesia_replay'],extra_replay=p['extra_replay'],Teams=[dict(UID=u,Raw=p['raw'][u],Loaded=p['loaded'][u],Country=p['countries'][u],Kind=p['kinds'][u]) for u in p['raw']])
 dump(CACHE.name,data)

def cached_source(reqs,pins,relevant):
 x=read(CACHE);assert x['ScriptSHA256']==sha(Path(__file__)) and x['RequirementsSHA256']==signature(reqs)
 assert x['EvidencePins']==pins and x['FreezeSHA256']==sha(N/'source-freeze.json') and x['ExportSHA256']==sha(N/'native-structure.json')
 assert all(sha(Path(x['path'])/n)==h for n,h in x['pins'].items())
 teams=x.pop('Teams');x.update(raw={t['UID']:t['Raw'] for t in teams},loaded={t['UID']:t['Loaded'] for t in teams},countries={t['UID']:t['Country'] for t in teams},kinds={t['UID']:t['Kind'] for t in teams},nations={int(k):v for k,v in x['nations'].items()},names={int(k):v for k,v in x['names'].items()})
 return recount(x,relevant)

def checks_for(reqs,p):
 rows=[]
 for q in reqs:
  if q['country'] is None:n=p['counts'][q['form']][q['uid']]
  else:
   ci=p['nationnames'][q['country'].casefold()];assert q['uid']==GENERIC
   if q.get('country_fallback_uid') is not None:assert p['nations'][ci]==q['country_fallback_uid']
   n=p['countrycounts'][q['form']][(ci,q['uid'])]
  rows.append(dict(q,Count=n,Passed=n>=q['minimum'] and(q['maximum'] is None or n<=q['maximum'])))
 return rows

def selfcheck():
 assert extra_loaded_current(170,0,796,67023610)==ES_PARENT
 assert extra_loaded_current(170,3,796,67023610)==67023610
 assert extra_loaded_current(143,0,784,67023610)==67023610
 assert extra_loaded_current(170,0,796,67023609)==67023609
 for u in OVERSEAS:assert extra_loaded_current(213,0,u,16)==GENERIC
 sample=dict(loaded={1:[ES_PARENT,67,ES_PARENT],2:[ES_PARENT,None,ES_PARENT],3:[29,None,29]},countries={1:170,2:None,3:158},kinds={1:0,2:0,3:0})
 sample=recount(sample,{ES_PARENT,29});assert sample['counts'][0][ES_PARENT]==2 and sample['counts'][1][ES_PARENT]==2 and sample['counts'][1][67]==1
 assert sample['countrycounts'][0][(170,ES_PARENT)]==1 and sample['counts'][0][29]==1
 return dict(Status='PASS_LOADER_BOUNDARIES_ALT_FALLBACK_REGIONAL_DEDUP_COUNTRY_SCOPE',Assertions=18)

def main():
 parser=argparse.ArgumentParser();mode=parser.add_mutually_exclusive_group(required=True);mode.add_argument('--preflight',action='store_true');mode.add_argument('--target-pinned',action='store_true');args=parser.parse_args()
 assert __debug__;reqs,pins=requirements();tests=selfcheck();ovp=R/'SWEDEN_SELECTION_REPAIR_X5_20261110/runtime-X5-Sweden-members.json';overlays=read(ovp)['load_time_changes'];assert len(overlays)==14;pins[str(ovp)]=sha(ovp)
 relevant={q['uid'] for q in reqs if q['country'] is None}
 if args.preflight:
  assert not CACHE.exists(),'Preserve prior source preflight cache; inspect pins before deliberate rerun'
  freeze=read(N/'source-freeze.json');source=profile(Path(freeze['frozen']),freeze['hashes'],N/'native-structure.json',overlays,relevant);cache_source(source,reqs,pins)
  cs=checks_for(reqs,source);dump('source-checks.json',cs);dump('requirements.json',reqs)
  out=dict(Status='READY_325_TARGET_NOT_READ',PreviousChecks=233,CurrentChecks=92,TotalChecks=325,UniqueConditions=len({tuple(q.get(k) for k in ['uid','form','minimum','maximum','country']) for q in reqs}),SourceTEAM=source['records'],SourcePreviousFailures=[x for x in cs[:233] if not x['Passed']],SourceCurrentFailures=[x for x in cs[233:] if not x['Passed']],ReplayCounts=dict(Sweden=14,Indonesia=len(source['indonesia_replay']),SpainAndTerritory=len(source['extra_replay'])),OverlayQualification='Sweden14 witnessed fulltriple replay is retained; all other stock replay changes Current only; ALT is raw if set else loadedCurrent. Regional dedup in both forms.',CA6460RawNationUIDs=sorted(OVERSEAS),SelfChecks=tests,TargetRead=False,DBWrites=False,SourceCacheSHA256=sha(CACHE),ScriptSHA256=sha(Path(__file__)),EvidencePins=pins)
  dump('code-preflight.json',out);print(json.dumps({k:out[k] for k in ['Status','PreviousChecks','CurrentChecks','TotalChecks','SourceTEAM','ReplayCounts','TargetRead']},ensure_ascii=True),flush=True);return
 assert CACHE.exists() and not(O/'regression.json').exists(),'Source preflight must precede target; preserve completed QA'
 report=read(W/'structure-report.json');inverse=read(W/'root-independent-verification.json');assert inverse['status'].startswith('PASS_')
 assert all(inverse['output_hashes'][n].lower()==report['output_hashes'][n].lower() for n in ['server_db.dat','client_db.dat','lang_db.dat'])
 source=cached_source(reqs,pins,relevant);target=profile(Path(report['output']),report['output_hashes'],W/'native-structure-after.json',overlays,relevant)
 assert set(source['raw'])<=set(target['raw']) and source['nations']==target['nations']
 assert list(source['names'])==list(target['names']),'COMP catalogue order changed'
 before=checks_for(reqs,source);after=checks_for(reqs,target);checks=[dict(q,before=a['Count'],after=z['Count'],before_passed=a['Passed'],after_passed=z['Passed']) for q,a,z in zip(reqs,before,after)]
 regressions=[x for x in checks[:233] if x['before_passed'] and not x['after_passed']];currentfail=[x for x in checks[233:] if not x['after_passed']];inherited=[x for x in checks[:233] if not x['before_passed'] and not x['after_passed']]
 cfgp=W/'structure-config.json';cfg=read(cfgp);idx={i:u for i,u in enumerate(source['names'])};allowed={q['uid'] for q in reqs[233:]}|set(prev.CHILD_UIDS)|set(prev.CHILD_UIDS.values())|ES_CHILD|{ES_PARENT,GENERIC}
 for k in cfg['expected_count_deltas']:
  if int(k)>=0:allowed.add(idx[int(k)])
 for group in ['moves','alternate_moves']:
  for m in cfg[group]:
   for k in ['Before','After']:
    if m[k]>=0:allowed.add(idx[m[k]])
 deltas=[]
 for form in [0,1]:
  for u in sorted(set(source['counts'][form])|set(target['counts'][form])):
   a=source['counts'][form][u];z=target['counts'][form][u]
   if a!=z:deltas.append(dict(CompetitionUID=u,Form=form,Before=a,After=z))
 unexpected=[d for d in deltas if d['CompetitionUID'] not in allowed]
 rc=[Counter(v[0] for v in p['raw'].values()) for p in [source,target]];actual={u:rc[1][u]-rc[0][u] for u in set(rc[0])|set(rc[1]) if rc[1][u]!=rc[0][u]};declared={idx.get(int(k)):v for k,v in cfg['expected_count_deltas'].items() if v};mismatch=actual!=declared
 oldnull={x['UID'] for x in source['nulls']};newnull=[x for x in target['nulls'] if x['UID'] not in oldnull];oldnr={(x['UID'],tuple(x['Divisions'])) for x in source['nullrelevant']};newnr=[x for x in target['nullrelevant'] if (x['UID'],tuple(x['Divisions'])) not in oldnr]
 maps=[{m['ClubUID']:m for m in cfg[g]} for g in ['moves','alternate_moves']];assert all(len(maps[i])==len(cfg[g]) for i,g in enumerate(['moves','alternate_moves']))
 slotfind=[];countrychanges=[]
 for u in source['raw']:
  if source['countries'][u]!=target['countries'][u]:countrychanges.append(dict(UID=u,Before=source['countries'][u],After=target['countries'][u],Qualification='root independently verifies approvedAFC/Ilves/Elo repairs and all other identity fields'))
  for slot in [0,1,2]:
   a=source['raw'][u][slot];z=target['raw'][u][slot]
   if a==z:continue
   m=maps[slot].get(u) if slot<2 else None
   if m is None or idx.get(m['Before'])!=a or idx.get(m['After'])!=z:slotfind.append(dict(UID=u,Slot=slot,Before=a,After=z,Reason='raw selection slot delta not exactly declared in root scoped config'))
 findings=bool(regressions or currentfail or unexpected or mismatch or newnull or newnr or slotfind)
 out=dict(Status='NUMERIC_SELECTION_REGRESSION_PASS' if not findings else 'FINDINGS_REQUIRE_REVIEW',CreatedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),Checks=checks,TotalChecks=325,PreviousChecks=233,CurrentBatchChecks=92,NewRegressions=regressions,CurrentBatchFailures=currentfail,InheritedUnchangedFailures=inherited,NewCountryNullTeams=newnull,NewCountryNullParticipants=newnr,RawSelectionSlotFindings=slotfind,CountryChangesDelegatedToRoot=countrychanges,CompetitionCountDeltas=deltas,UnexpectedCompetitionCountDeltas=unexpected,AllowedChangedCompetitionUIDs=sorted(allowed),RawCurrentDeltaMismatch=mismatch,ObservedRawCurrentDeltas=[dict(CompetitionUID=k,Delta=v) for k,v in actual.items()],DeclaredRawCurrentDeltas=[dict(CompetitionUID=k,Delta=v) for k,v in declared.items()],SourceReplay=dict(Sweden=source['replays'],Indonesia=source['indonesia_replay'],SpainAndTerritory=source['extra_replay']),TargetReplay=dict(Sweden=target['replays'],Indonesia=target['indonesia_replay'],SpainAndTerritory=target['extra_replay']),EvidencePins=pins,SourceCacheSHA256=sha(CACHE),RootReportPins={str(p):sha(p) for p in [W/'structure-report.json',W/'root-independent-verification.json',W/'native-structure-after.json',cfgp]},SourceTargetPins=[dict(Path=p['path'],Hashes=p['pins'],TEAM=p['records']) for p in [source,target]],ScriptSHA256=sha(Path(__file__)),DBWrites=False,RuntimeTest=False,Limits='Static numeric QA with witnessed loader overlays. Root separately verifies complete inverse, protectedKolding/Sweden/names/country fields. All92current requirements must PASS regardless of source failures;233prior conditions must not regress.')
 dump('regression.json',out);dump('pins.json',dict(Status=out['Status'],ReportSHA256=sha(O/'regression.json'),ScriptSHA256=sha(Path(__file__)),RootReportPins=out['RootReportPins'],SourceTargetPins=out['SourceTargetPins']));print(json.dumps(dict(Status=out['Status'],Checks=325,NewRegressions=len(regressions),CurrentFailures=len(currentfail),InheritedFailures=len(inherited),RawDeltaMismatch=mismatch,UnexpectedDeltas=len(unexpected),NewNulls=len(newnull),NewNullParticipants=len(newnr),SlotFindings=len(slotfind))),flush=True)
 if findings:raise SystemExit(2)
if __name__=='__main__':main()
