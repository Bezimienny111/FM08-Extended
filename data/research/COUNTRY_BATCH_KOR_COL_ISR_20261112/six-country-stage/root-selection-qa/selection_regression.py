"""Read-only X16 selection regression; source X15, typed TEAM country, witnessed Sweden replay."""
from pathlib import Path
from collections import Counter
import hashlib,json,struct,sys,datetime
sys.dont_write_bytecode=True
ROOT=Path(r"J:/FM08dev");R=ROOT/'FmLauncher/data/research';B=R/'COUNTRY_BATCH_KOR_COL_ISR_20261112';S=B/'six-country-stage';W=S/'structure-root';O=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
from create_club_stadium_native_n1_20261108 import load
from create_native_u23_test import language_blocks
from audit_poland_v25_common_r1_20261108 import Cursor,lang_sections,find_table,club
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,x):(O/name).write_text(json.dumps(x,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
def limits(v,lo):
 if v in (None,-1,4294967295):return None
 if v in (-2,4294967294):return lo
 return v
def requirements():
 qs=[];seen=set();pins={}
 def add(q):
  sig=tuple(q.get(k) for k in ['uid','form','minimum','maximum','country'])
  if sig not in seen:seen.add(sig);qs.append(q)
 for origin,path,key in [('prior_Sweden43',R/'SWEDEN_SELECTION_REPAIR_X6_20261110/verification.json','gates_after'),('prior_X8_Scotland_Slovakia_Slovenia_Singapore_Sweden',R/'SINGAPORE_SELECTION_REPAIR_X8_20261110/verification.json','checks')]:
  pins[str(path)]=sha(path)
  for x in read(path)[key]:add(dict(uid=x['uid'],form=x['form'],minimum=x['minimum'],maximum=limits(x['maximum'],x['minimum']),country=None,origin=origin,qualification='previously_witnessed_requirement'))
 for origin,path in [('prior_X14_Portugal_Peru_Norway',R/'PORTUGAL_PERU_NORWAY_POLAND_PREP_20261111/native-competition-requirements.json'),('prior_X15_Germany_Mexico_Malaysia',R/'COUNTRY_BATCH_GER_MEX_MAS_20261112/native-competition-requirements.json'),('current_X16_six_countries',S/'native-competition-requirements.json')]:
  pins[str(path)]=sha(path)
  for x in read(path)['requirements']:
   scoped=bool(x.get('CountrySpecific'));assert not scoped or x['CompetitionUID']==1301432
   for form in [0,1]:
    lo=x['Form0Min'] if form==0 else x['Form1DefaultMin'];hi=x['Form0Max'] if form==0 else x['Form1DefaultMax']
    if lo is None:continue
    add(dict(uid=x['CompetitionUID'],form=form,minimum=lo,maximum=limits(hi,lo),country=x['Country'] if scoped else None,country_fallback_uid=x.get('CountryFallbackUID'),origin=origin,qualification='native_form0_limit' if form==0 else x.get('Form1Qualification','inherited_default_not_live_proof')))
 return qs,pins

def read_profile(source,expected,export,overlays,relevant):
 before={n:sha(source/n) for n in ['client_db.dat','server_db.dat','lang_db.dat']}
 assert all(v==expected[n].lower() for n,v in before.items())
 en,_=lang_sections(dict(language_blocks((source/'lang_db.dat').read_bytes()))[8]);idx={i:v['uid'] for i,v in enumerate(en['comp'])};names={v['uid']:v['names'][0] for v in en['comp']}
 nations={i:v['uid'] for i,v in enumerate(en['nation'])};nationnames={n.casefold():i for i,v in enumerate(en['nation']) for n in v['names'] if n}
 families,_,_=find_table(load(source,'client_db.dat'),[v['uid'] for v in en['club']],club)
 server=load(source,'server_db.dat');rows=read(export)['records'];raw={};countries={};tailproof={};duplicate=Counter(x['ClubUID'] for x in rows);assert max(duplicate.values())==1
 for row in rows:
  uid=row['ClubUID'];assert server[row['Start']]==10 and struct.unpack_from('<iI',server,row['Footer'])==(row['TeamIndex'],uid)
  vals=[struct.unpack_from('<i',server,row['Start']+offset)[0] for offset in [7,15,47]];assert vals[0]==row['CurrentDivisionIndex'];assert all(v==-1 or v in idx for v in vals)
  raw[uid]=[idx.get(v) for v in vals]
  low=row['RosterOffset']+2+4*struct.unpack_from('<H',server,row['RosterOffset'])[0];hits=[]
  for at in range(low+4,row['Footer']-13):
   # The TEAM tail is typed FAMILY reference mode0; NAME-family-by-UID is not used.
   if server[at-3]!=0:continue
   ref=struct.unpack_from('<i',server,at)[0]
   if not 0<=ref<len(families):continue
   cur=Cursor(server,at+4)
   try:
    cur.string();cur.byte();cur.string();cur.byte()
    if cur.p==row['Footer']:hits.append((ref,at,server[at-4]))
   except(AssertionError,ValueError,UnicodeError,struct.error):continue
  assert len(hits)==1,('typed_TEAM_tail_not_unique',uid,hits)
  fi,at,kind=hits[0];f=families[fi];country=f['country_index'];countries[uid]=country if country is not None and country>=0 else None
  tailproof[uid]=dict(TEAMFamilyIndex=fi,TEAMFamilyUID=f['uid'],TEAMCountry=countries[uid],TEAMKind=kind,ReferenceOffset=at)
 loaded={u:list(v) for u,v in raw.items()};replays=[]
 for ov in overlays:
  u=ov['uid'];assert u in loaded
  loaded[u]=[ov['runtime'][k] for k in ['primary','alternate','regional']]
  replays.append(dict(UID=u,Raw=raw[u],HistoricalReplay=loaded[u]))
 counts=[Counter(),Counter()];countrycounts=[Counter(),Counter()];nulls=[];nullrelevant=[]
 for uid,(current,alternate,regional) in loaded.items():
  for form,selected in enumerate([current,alternate if alternate is not None else current]):
   for competition in {selected,regional}-{None}:
    counts[form][competition]+=1
    if countries[uid] is not None:countrycounts[form][(countries[uid],competition)]+=1
  if countries[uid] is None:
   member=dict(UID=uid,Divisions=loaded[uid],Tail=tailproof[uid]);nulls.append(member)
   if relevant & {v for v in loaded[uid] if v is not None}:nullrelevant.append(member)
 assert before=={n:sha(source/n) for n in before}
 return dict(path=str(source),pins=before,records=len(rows),raw=raw,loaded=loaded,countries=countries,tailproof=tailproof,counts=counts,countrycounts=countrycounts,nulls=nulls,nullrelevant=nullrelevant,replays=replays,nationnames=nationnames,nations=nations,names=names)

def main():
 assert __debug__ and not(O/'regression.json').exists()
 freeze=read(B/'source-freeze.json');report=read(W/'structure-report.json');inverse=read(W/'root-independent-verification.json');assert inverse['status'].startswith('PASS_') and len(inverse['both_forms'])==58
 assert all(inverse['output_hashes'][n].lower()==report['output_hashes'][n].lower() for n in ['client_db.dat','server_db.dat','lang_db.dat'])
 reqs,pins=requirements();six=read(S/'native-competition-requirements.json');assert len(six['requirements'])==29
 code=Path(six['country_scope_code']);assert sha(code)==six['country_scope_code_sha256'];pins[str(code)]=sha(code)
 for p,h in six['source_requirements'].items():assert sha(Path(p))==h;pins[p]=h
 overlaypath=R/'SWEDEN_SELECTION_REPAIR_X5_20261110/runtime-X5-Sweden-members.json';overlays=read(overlaypath)['load_time_changes'];assert len(overlays)==14
 pins[str(overlaypath)]=sha(overlaypath)
 relevant={q['uid'] for q in reqs if q['country'] is None}
 source=read_profile(Path(freeze['frozen']),freeze['hashes'],B/'native-structure.json',overlays,relevant)
 target=read_profile(Path(report['output']),report['output_hashes'],W/'native-structure-after.json',overlays,relevant)
 assert set(source['raw'])<=set(target['raw']) and source['nations']==target['nations']
 for ov in overlays:
  uid=ov['uid'];assert source['raw'][uid]==target['raw'][uid] and source['countries'][uid]==target['countries'][uid],('Sweden_overlay_input_changed',uid)
 checks=[]
 for q in reqs:
  result=dict(q)
  for label,p in [('before',source),('after',target)]:
   if q['country'] is None:n=p['counts'][q['form']][q['uid']]
   else:
    ci=p['nationnames'][q['country'].casefold()];assert q['uid']==1301432
    if q.get('country_fallback_uid') is not None:assert p['nations'][ci]==q['country_fallback_uid']
    result['CountryIndex']=ci;n=p['countrycounts'][q['form']][(ci,q['uid'])]
   result[label]=n;result[label+'_passed']=n>=q['minimum'] and(q['maximum'] is None or n<=q['maximum'])
  checks.append(result)
 current=[q for q in checks if q['origin']=='current_X16_six_countries'];assert len(current)==58
 # Same signature for an earlier six-country overlapping condition can hide origin; none may be lost.
 regressions=[q for q in checks if q['before_passed'] and not q['after_passed']]
 failures=[q for q in current if not q['after_passed']]
 inherited=[q for q in checks if not q['before_passed'] and not q['after_passed'] and q['origin']!='current_X16_six_countries']
 oldnull={x['UID'] for x in source['nulls']};newnull=[x for x in target['nulls'] if x['UID'] not in oldnull]
 oldrelevant={(x['UID'],tuple(x['Divisions'])) for x in source['nullrelevant']};newnullparticipants=[x for x in target['nullrelevant'] if(x['UID'],tuple(x['Divisions']))not in oldrelevant]
 changes=[]
 for form in [0,1]:
  for uid in sorted(set(source['counts'][form])|set(target['counts'][form])):
   a=source['counts'][form][uid];b=target['counts'][form][uid]
   if a!=b:changes.append(dict(CompetitionUID=uid,Name=target['names'].get(uid),Form=form,Before=a,After=b))
 countryproofs=[]
 for q in checks:
  if q['country'] is not None:countryproofs.append(dict(Country=q['country'],CountryIndex=q['CountryIndex'],CompetitionUID=q['uid'],Form=q['form'],Before=q['before'],After=q['after'],Minimum=q['minimum'],Scope='typed_TEAM_tail_country AND selected_COMP_or_regional_COMP',NoFallbackFilteringForOtherCOMP=True))
 result=dict(Status='NUMERIC_SELECTION_REGRESSION_PASS' if not(regressions or failures or newnull or newnullparticipants) else 'FINDINGS_REQUIRE_REVIEW',CreatedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),Scope='Prior witnessedSweden43conditions,X8fourcountries,X14PortugalPeruNorway,X15GermanyMexicoMalaysia,currentX16sixcountries29requirements58formchecks. NotallcountrieslivePASS.',Checks=checks,TotalChecks=len(checks),CurrentSixCountryChecks=len(current),NewRegressions=regressions,CurrentSixCountryFailures=failures,InheritedUnchangedFailures=inherited,NewCountryNullTeams=newnull,NewCountryNullParticipants=newnullparticipants,SourceCountryNullRelevantMembers=source['nullrelevant'],TargetCountryNullRelevantMembers=target['nullrelevant'],SourceAllCountryNullCount=len(source['nulls']),TargetAllCountryNullCount=len(target['nulls']),SwedenHistoricalOverlaysReplayed=14,SwedenRawInputsAndCountriesPreserved=True,SwedenReplay=[dict(Source='X15',**v)for v in source['replays']]+[dict(Source='X16structure',**v)for v in target['replays']],CountrySpecificCounters=countryproofs,CompetitionCountDeltas=changes,SourceTargetPins=[dict(Path=p['path'],Hashes=p['pins'],TEAMRecords=p['records'])for p in [source,target]],EvidencePins=pins,PriorTemplate=dict(Path=str(R/'COUNTRY_BATCH_GER_MEX_MAS_20261112/root_selection_regression.py'),SHA256=sha(R/'COUNTRY_BATCH_GER_MEX_MAS_20261112/root_selection_regression.py')),SourceScriptSHA256=sha(Path(__file__)),InputReportsSHA256={str(p):sha(p)for p in [B/'source-freeze.json',W/'structure-report.json',W/'root-independent-verification.json',B/'native-structure.json',W/'native-structure-after.json']},DBModified=False,EXEModified=False,RuntimeTest=False,Limits='Numeric staticregression with historicalSwedenloaderreplay and inheritedform1defaults; nativeinversechecktrustedseparately. No live picker/newcareer/seasonclaim.')
 dump('regression.json',result)
 dump('pins.json',dict(Status=result['Status'],ReportSHA256=sha(O/'regression.json'),ScriptSHA256=sha(Path(__file__)),Inputs=result['InputReportsSHA256'],SourceTargetPins=result['SourceTargetPins']))
 print(json.dumps(dict(Status=result['Status'],Checks=len(checks),SixCountryChecks=len(current),Regressions=len(regressions),SixFailures=len(failures),InheritedFailures=len(inherited),NewNullTeams=len(newnull),NewNullParticipants=len(newnullparticipants),SourceNullRelevant=len(source['nullrelevant']),TargetNullRelevant=len(target['nullrelevant']),Deltas=len(changes))))
if __name__=='__main__':main()
