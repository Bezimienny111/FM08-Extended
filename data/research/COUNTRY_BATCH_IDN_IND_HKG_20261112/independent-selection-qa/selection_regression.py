"""Independent read-only X17 numeric QA; stock Indonesia Current loader replay + historical Sweden14."""
from pathlib import Path
from collections import Counter
import importlib.util,sys,json,hashlib,datetime
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=R/'COUNTRY_BATCH_IDN_IND_HKG_20261112';O=Path(__file__).resolve().parent;W=B/'structure-root'
if '--writer-dir' in sys.argv:
 name=sys.argv[sys.argv.index('--writer-dir')+1];assert name in ['structure-root-r2','structure-root-r3','structure-root-r4'];W=B/name
TEMPLATE=R/'COUNTRY_BATCH_KOR_COL_ISR_20261112/six-country-stage/root-selection-qa/selection_regression.py'
sp=importlib.util.spec_from_file_location('previous_selection',TEMPLATE);prev=importlib.util.module_from_spec(sp);sp.loader.exec_module(prev)
read=prev.read;sha=prev.sha
CHILD_UIDS={5385746:5385513,5385747:5385513,7744910:5385703,7744911:5385703,7746527:5385703,7746876:5385703}
def dump(name,x):(O/name).write_text(json.dumps(x,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
def requirements():
 old,pins=prev.requirements();assert len(old)==215,len(old)
 p=B/'competition-prep/native-competition-requirements.json';pins[str(p)]=sha(p);new=read(p);assert len(new['requirements'])==9
 qs=list(old)
 for x in new['requirements']:
  scoped=bool(x.get('CountrySpecific'));assert not scoped or x['CompetitionUID']==1301432
  for form in [0,1]:
   lo=x['Form0Min'] if form==0 else x['Form1DefaultMin'];hi=x['Form0Max'] if form==0 else x['Form1DefaultMax'];assert lo is not None
   qs.append(dict(uid=x['CompetitionUID'],form=form,minimum=lo,maximum=prev.limits(hi,lo),country=x['Country'] if scoped else None,country_fallback_uid=x.get('CountryFallbackUID'),origin='current_X17_Indonesia_India_HongKong',qualification='C34A40 Current loader replay; raw ALT-or-normalizedCurrent pre-D64470; Form1conditional, not live proof'))
 assert len(qs)==233
 for f in [TEMPLATE,B/'competition-prep/indonesia-loader-evidence.json',B/'family-region-review/source-readback.json',B/'family-region-review/read_family_regions.py']:
  pins[str(f)]=sha(f)
 ev=read(B/'competition-prep/indonesia-loader-evidence.json')
 for pin in ev['Pins']:
  p=Path(pin['Path']);assert sha(p)==pin['SHA256'];pins[str(p)]=sha(p)
 return qs,pins

def read_profile(source,expected,export,overlays,relevant):
 p=prev.read_profile(source,expected,export,overlays,relevant);changes=[]
 assert p['nations'].get(58)==113
 # C34A40: first TEAM, own typed FAMILY, countryUID113, guarded newDB path.
 for uid,vals in p['loaded'].items():
  if p['countries'][uid]!=58 or p['tailproof'][uid]['TEAMKind']!=0:continue
  if vals[0] in CHILD_UIDS:
   before=vals[0];vals[0]=CHILD_UIDS[before];changes.append(dict(UID=uid,RawCurrentUID=before,CurrentAfterStockLoaderUID=vals[0],AlternateUnmodified=vals[1],RegionalUnmodified=vals[2]))
 counts=[Counter(),Counter()];cc=[Counter(),Counter()];nulls=[];nr=[]
 for uid,(cur,alt,regional) in p['loaded'].items():
  for form,selected in enumerate([cur,alt if alt is not None else cur]):
   for comp in {selected,regional}-{None}:
    counts[form][comp]+=1
    if p['countries'][uid] is not None:cc[form][(p['countries'][uid],comp)]+=1
  if p['countries'][uid] is None:
   v=dict(UID=uid,Divisions=p['loaded'][uid],Tail=p['tailproof'][uid]);nulls.append(v)
   if relevant & {v for v in p['loaded'][uid] if v is not None}:nr.append(v)
 p.update(counts=counts,countrycounts=cc,nulls=nulls,nullrelevant=nr,indonesia_replay=changes)
 return p

def main():
 assert __debug__;reqs,pins=requirements()
 if '--preflight' in sys.argv:
  freeze=read(B/'source-freeze.json');assert all(sha(Path(freeze['frozen'])/n)==freeze['hashes'][n] for n in ['server_db.dat','client_db.dat','lang_db.dat'])
  dump('code-preflight.json',dict(Status='READY_TARGET_NOT_READ',Requirements=len(reqs),PreviousChecks=215,NewBatchChecks=18,UniqueConditions=len({tuple(q.get(k) for k in ['uid','form','minimum','maximum','country']) for q in reqs}),SourceFreezeSHA256=sha(B/'source-freeze.json'),ScriptSHA256=sha(Path(__file__)),Pins=pins,TargetRead=False,DBWrites=False));print('READY:215 previous+18current=233checks; target not read');return
 assert '--target-pinned' in sys.argv,'Only run after writer confirms closed pinned target'
 assert W.name!='structure-root','Original structure-root rejected for three unproved country-null aliases'
 assert not(O/'regression.json').exists(),'Keep prior QA result frozen'
 freeze=read(B/'source-freeze.json');report=read(W/'structure-report.json');inverse=read(W/'root-independent-verification.json');assert inverse['status'].startswith('PASS_')
 assert all(inverse['output_hashes'][n].lower()==report['output_hashes'][n].lower() for n in ['server_db.dat','client_db.dat','lang_db.dat'])
 ovp=R/'SWEDEN_SELECTION_REPAIR_X5_20261110/runtime-X5-Sweden-members.json';overlays=read(ovp)['load_time_changes'];assert len(overlays)==14;pins[str(ovp)]=sha(ovp)
 relevant={q['uid'] for q in reqs if q['country'] is None}
 source=read_profile(Path(freeze['frozen']),freeze['hashes'],B/'native-structure.json',overlays,relevant)
 target=read_profile(Path(report['output']),report['output_hashes'],W/'native-structure-after.json',overlays,relevant)
 assert set(source['raw'])<=set(target['raw']) and source['nations']==target['nations']
 for ov in overlays:
  u=ov['uid'];assert source['raw'][u]==target['raw'][u] and source['countries'][u]==target['countries'][u],('Sweden_input_changed',u)
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
 current=[q for q in checks if q['origin'].startswith('current_X17')];assert len(current)==18
 regressions=[q for q in checks if q['before_passed'] and not q['after_passed']];failures=[q for q in current if not q['after_passed']];inherited=[q for q in checks if not q['before_passed'] and not q['after_passed'] and not q['origin'].startswith('current_X17')]
 oldnull={x['UID'] for x in source['nulls']};newnull=[x for x in target['nulls'] if x['UID'] not in oldnull];oldnr={(x['UID'],tuple(x['Divisions'])) for x in source['nullrelevant']};newnr=[x for x in target['nullrelevant'] if(x['UID'],tuple(x['Divisions']))not in oldnr]
 deltas=[]
 for form in [0,1]:
  for uid in sorted(set(source['counts'][form])|set(target['counts'][form])):
   a=source['counts'][form][uid];z=target['counts'][form][uid]
   if a!=z:deltas.append(dict(CompetitionUID=uid,Name=target['names'].get(uid),Form=form,Before=a,After=z))
 cfgp=W/'structure-config.json';cfg=read(cfgp);pins[str(cfgp)]=sha(cfgp)
 idx={i:uid for i,uid in enumerate(source['names'])};assert idx=={i:uid for i,uid in enumerate(target['names'])},'COMP catalogue order changed'
 assert -1 not in idx
 allowed_comp={q['uid'] for q in current}|set(CHILD_UIDS)|set(CHILD_UIDS.values())
 for k in cfg['expected_count_deltas']:
  if int(k)>=0:allowed_comp.add(idx[int(k)])
 for group in ['moves','alternate_moves']:
  for m in cfg[group]:
   for key in ['Before','After']:
    if m[key]>=0:allowed_comp.add(idx[m[key]])
 raw_counts=[Counter(v[0] for v in profile['raw'].values()) for profile in [source,target]]
 actual_raw_delta={uid:raw_counts[1][uid]-raw_counts[0][uid] for uid in set(raw_counts[0])|set(raw_counts[1]) if raw_counts[1][uid]!=raw_counts[0][uid]}
 declared_raw_delta={idx.get(int(k)):v for k,v in cfg['expected_count_deltas'].items() if v}
 raw_delta_mismatch=actual_raw_delta!=declared_raw_delta
 move_maps=[{m['ClubUID']:m for m in cfg[k]} for k in ['moves','alternate_moves']]
 assert all(len(move_maps[i])==len(cfg[k]) for i,k in enumerate(['moves','alternate_moves']))
 slot_findings=[];country_findings=[];slot_changes=[]
 for uid in source['raw']:
  if source['countries'][uid]!=target['countries'][uid]:country_findings.append(dict(UID=uid,Before=source['countries'][uid],After=target['countries'][uid],Reason='existing_TEAM_country_changed_without_independent_identity_authorization'))
  for slot,label in enumerate(['Current','Alternate','Regional']):
   a=source['raw'][uid][slot];z=target['raw'][uid][slot]
   if a==z:continue
   item=dict(UID=uid,Slot=label,BeforeUID=a,AfterUID=z,SourceCountry=source['countries'][uid],TargetCountry=target['countries'][uid]);slot_changes.append(item)
   if slot==2:slot_findings.append(dict(**item,Reason='regional_slot_change_requires_explicit_plan')) ;continue
   m=move_maps[slot].get(uid)
   if m is None or idx.get(m['Before'])!=a or idx.get(m['After'])!=z:slot_findings.append(dict(**item,Reason='raw_slot_change_not_declared_in_scoped_config'))
   if source['countries'][uid] not in [56,57,58] or target['countries'][uid] not in [56,57,58]:slot_findings.append(dict(**item,Reason='existing_TEAM_move_outside_proven_three_country_scope'))
 protected_aliases=[]
 for uid in [1408,1001749,5629894]:
  passed=source['raw'][uid]==target['raw'][uid] and source['countries'][uid]==target['countries'][uid]
  protected_aliases.append(dict(UID=uid,Passed=passed,SourceRaw=source['raw'][uid],TargetRaw=target['raw'][uid],SourceCountry=source['countries'][uid],TargetCountry=target['countries'][uid]))
  if not passed:slot_findings.append(dict(UID=uid,Reason='protected_rejected_short_alias_historical_record_changed'))

 unexpected_deltas=[d for d in deltas if d['CompetitionUID'] not in allowed_comp]
 country_lower_deltas=[]
 for form in [0,1]:
  for ci,comp in sorted(set(source['countrycounts'][form])|set(target['countrycounts'][form])):
   if comp!=1301432:continue
   a=source['countrycounts'][form][(ci,comp)];z=target['countrycounts'][form][(ci,comp)]
   if a!=z:country_lower_deltas.append(dict(CountryIndex=ci,CountryUID=target['nations'].get(ci),CompetitionUID=comp,Form=form,Before=a,After=z))
 result=dict(Status='NUMERIC_SELECTION_REGRESSION_PASS' if not(regressions or failures or newnull or newnr or unexpected_deltas or slot_findings or country_findings or raw_delta_mismatch) else 'FINDINGS_REQUIRE_REVIEW',CreatedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),Scope='215 previous condition records+18 current checks; overlaps retained explicitly. Static source/target counts, Sweden14 witnessed replay, Indonesia stock Current loader replay. NOT live all-country PASS.',Checks=checks,TotalChecks=len(checks),CurrentBatchChecks=18,NewRegressions=regressions,CurrentBatchFailures=failures,InheritedUnchangedFailures=inherited,NewCountryNullTeams=newnull,NewCountryNullParticipants=newnr,SourceCountryNullRelevantMembers=source['nullrelevant'],TargetCountryNullRelevantMembers=target['nullrelevant'],SourceAllCountryNullCount=len(source['nulls']),TargetAllCountryNullCount=len(target['nulls']),SwedenHistoricalOverlaysReplayed=14,SwedenRawInputsAndCountriesPreserved=True,IndonesiaStockCurrentReplay=[dict(Source='X16',Changes=source['indonesia_replay']),dict(Source='new_structure',Changes=target['indonesia_replay'])],IndonesiaAlternateQualification='ALT remains raw; C34A40 Current normalization applies first. D64470 later chooses/clears ALT conditionally. Target explicit parent36/40; no claim source raw ALT or runtime season behavior.',CountrySpecificCounters=[dict(Country=q['country'],CountryIndex=q['CountryIndex'],CompetitionUID=q['uid'],Form=q['form'],Before=q['before'],After=q['after'],Scope='typed TEAM-tail country only for COMP1301432') for q in checks if q['country'] is not None],CompetitionCountDeltas=deltas,UnexpectedCompetitionCountDeltas=unexpected_deltas,DeclaredRawCurrentDeltas=[dict(CompetitionUID=k,Delta=v) for k,v in declared_raw_delta.items()],ObservedRawCurrentDeltas=[dict(CompetitionUID=k,Delta=v) for k,v in actual_raw_delta.items()],RawCurrentDeltaMismatch=raw_delta_mismatch,RawSlotChanges=slot_changes,RawSlotScopeFindings=slot_findings,ExistingTEAMCountryChangeFindings=country_findings,ProtectedRejectedShortAliases=protected_aliases,AllCountryGenericLowerDeltas=country_lower_deltas,AllowedChangedCompetitionUIDs=sorted(allowed_comp),SourceTargetPins=[dict(Path=p['path'],Hashes=p['pins'],TEAMRecords=p['records']) for p in [source,target]],EvidencePins=pins,InputReportsSHA256={str(p):sha(p) for p in [B/'source-freeze.json',B/'native-structure.json',W/'structure-report.json',W/'root-independent-verification.json',W/'native-structure-after.json']},SourceScriptSHA256=sha(Path(__file__)),DBModified=False,EXEModified=False,RuntimeTest=False)
 dump('regression.json',result);dump('pins.json',dict(Status=result['Status'],ReportSHA256=sha(O/'regression.json'),ScriptSHA256=sha(Path(__file__)),Inputs=result['InputReportsSHA256'],SourceTargetPins=result['SourceTargetPins']))
 print(json.dumps(dict(Status=result['Status'],Checks=len(checks),CurrentChecks=18,Regressions=len(regressions),CurrentFailures=len(failures),InheritedFailures=len(inherited),NewNullTeams=len(newnull),NewNullParticipants=len(newnr),CountDeltas=len(deltas),UnexpectedCompetitionDeltas=len(unexpected_deltas),RawSlotScopeFindings=len(slot_findings),CountryChanges=len(country_findings),RawCurrentDeltaMismatch=raw_delta_mismatch,IndonesiaSourceReplay=len(source['indonesia_replay']),IndonesiaTargetReplay=len(target['indonesia_replay']))))
if __name__=='__main__':main()
