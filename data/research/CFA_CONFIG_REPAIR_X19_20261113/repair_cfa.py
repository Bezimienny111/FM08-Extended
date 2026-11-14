"""X19 narrow data-only repair on frozen latest SI X18; no roster import."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import json,hashlib,shutil,sys,struct,zlib,subprocess,importlib.util
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent;X=R/'COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep';S=B/'input/X18-after-SI-failed';D=B/'private-db';T=X/'tools'
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'));from create_club_stadium_native_n1_20261108 import load
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pins(d):return{str(p.relative_to(d)):sha(p)for p in sorted(d.rglob('*'))if p.is_file()}
def dump(n,x):(B/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
f=read(B/'source-freeze.json');expected=f['hashes'];assert pins(S)==pins(Path(f['source']))==expected;assert sha(Path(f['original_X18_ZIP']))==f['original_X18_ZIP_SHA256'];assert not D.exists();assert not any(p.exists()for p in[ROOT/'Dane/db/TEST_X19',ROOT/'Dane/db/TEST_X19.xml',ROOT/'wydania/TEST_X19.zip'])
planpath=X/'reserve-cfa-config-review/fix-plan.json';plan=read(planpath);assert sha(planpath)=='f1af0e478720c6a01a9542f84ab8efb637ddad5c43f17f35d867d474bb58759e';moves=plan['Edits'];assert len(moves)==6
qafile=X/'root-structure/qa/selection_regression.py';sp=importlib.util.spec_from_file_location('x18_known_selection_reader',qafile);q=importlib.util.module_from_spec(sp);sp.loader.exec_module(q);reqs,evidencepins=q.requirements();assert len(reqs)==325;ovpath=R/'SWEDEN_SELECTION_REPAIR_X5_20261110/runtime-X5-Sweden-members.json';overlays=read(ovpath)['load_time_changes'];relevant={x['uid']for x in reqs if x['country']is None};source=q.profile(S,expected,B/'source-native-structure.json',overlays,relevant)
print('FRESH_SOURCE_325_PROFILE_READ; no source cache',flush=True)
idx={u:i for i,u in enumerate(source['names'])};cfa=idx[145438];cfa2=idx[8436980];raw=load(S,'server_db.dat');records=read(B/'source-native-structure.json')['records'];by={x['ClubUID']:x for x in records};edits=[];witness=[];allowed=set()
assert sum(x['CurrentDivisionIndex']==cfa for x in records)==53
for m in moves:
 u=m['UID'];z=by[u];ti=z['TeamIndex'];start=z['Start'];tail=source['tailproof'][u];cur,alt,regional=source['raw'][u]
 assert cur==8436980 and alt in[None,8436980],('PostSI source membership differs',u,source['raw'][u])
 assert source['kinds'][u]==0 and source['countries'][u]==143 and tail['TEAMFamilyUID']==u,('Expected source-backed firstTEAM selfFAMILY France',u,tail)
 assert raw[start]==10 and struct.unpack_from('<iI',raw,z['Footer'])==(ti,u)
 beforecur,beforealt=struct.unpack_from('<i',raw,start+7)[0],struct.unpack_from('<i',raw,start+15)[0];assert beforecur==cfa2 and beforealt in[-1,cfa2]
 row=dict(UID=u,TMID=m['TMID'],Name=m['Name'],TeamIndex=ti,Start=start,Footer=z['Footer'],FamilyUID=tail['TEAMFamilyUID'],FamilyIndex=tail['TEAMFamilyIndex'],Kind=source['kinds'][u],Country=source['countries'][u],CurrentCOMPBefore=cur,AlternateCOMPBefore=alt,CurrentIndexBefore=beforecur,AlternateIndexBefore=beforealt,CurrentIndexAfter=cfa,AlternateIndexAfter=cfa,PreviousIndexPreserved=struct.unpack_from('<i',raw,start+11)[0],RegionalIndexPreserved=struct.unpack_from('<i',raw,start+47)[0],WholeTEAMSourceSHA256=hashlib.sha256(raw[start:z['Footer']+8]).hexdigest(),SourceRankingOrder=m['SourceRankingOrder'],PreviousFacts=m['PreviousFacts'])
 witness.append(row);allowed.add(u)
 for off in[start+7,start+15]:edits.append((off,raw[off:off+4],struct.pack('<i',cfa)))
assert len(edits)==12 and len({o for o,_,_ in edits})==12
changed=bytearray(raw)
for off,before,after in edits:assert changed[off:off+4]==before;changed[off:off+4]=after
assert len(changed)==len(raw);inverse=bytearray(changed)
for off,before,after in edits:assert inverse[off:off+4]==after;inverse[off:off+4]=before
assert bytes(inverse)==raw
# Only six firstTEAM Current/ALT fields change. Even their complete roster/prefix/tail bytes remain identical otherwise.
for row in witness:
 z=by[row['UID']];restored=bytearray(changed[z['Start']:z['Footer']+8])
 for off,before,after in edits:
  if z['Start']<=off<z['Footer']:restored[off-z['Start']:off-z['Start']+4]=before
 assert bytes(restored)==raw[z['Start']:z['Footer']+8]
assert pins(S)==expected and pins(Path(f['source']))==expected
shutil.copytree(S,D);header=(S/'server_db.dat').read_bytes()[:9];(D/'server_db.dat').write_bytes(header+zlib.compress(bytes(changed)));assert load(D,'server_db.dat')==bytes(changed)and(D/'server_db.dat').read_bytes()[:9]==header
actual=pins(D);assert{k:v for k,v in actual.items()if k!='server_db.dat'}=={k:v for k,v in expected.items()if k!='server_db.dat'}
args=[T/'ExportWholeNativeStructure.exe',D,T/'FM08_Database_Editor.exe',B/'target-native-structure.json'];z=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300);(B/'target-export.log').write_text(z.stdout+z.stderr,encoding='utf-8');assert z.returncode==0,z.stderr[-1500:]
print('PRIVATE_PATCH_12_INT32_48B_INVERSE_PASS; all other files identical',flush=True)
target=q.profile(D,actual,B/'target-native-structure.json',overlays,relevant);assert set(source['raw'])==set(target['raw']) and source['nations']==target['nations'] and source['names']==target['names'] and source['countries']==target['countries'] and source['kinds']==target['kinds']
slotchanges=[]
for u in source['raw']:
 for slot in[0,1,2]:
  before,after=source['raw'][u][slot],target['raw'][u][slot]
  if before!=after:
   assert u in allowed and slot in[0,1]and before in[None,8436980]and after==145438,(u,slot,before,after);slotchanges.append(dict(UID=u,Slot=['Current','Alternate','Regional'][slot],Before=before,After=after))
assert len(slotchanges)==12
before=q.checks_for(reqs,source);after=q.checks_for(reqs,target);checks=[dict(x,before=a['Count'],after=z['Count'],before_passed=a['Passed'],after_passed=z['Passed'])for x,a,z in zip(reqs,before,after)];regressions=[x for x in checks[:233]if x['before_passed']and not x['after_passed']];currentfail=[x for x in checks[233:]if not x['after_passed']];inherited=[x for x in checks[:233]if not x['before_passed']and not x['after_passed']];assert not regressions and not currentfail and not inherited
raw_before=Counter(v[0]for v in source['raw'].values());raw_after=Counter(v[0]for v in target['raw'].values());deltas={u:raw_after[u]-raw_before[u]for u in set(raw_before)|set(raw_after)if raw_after[u]!=raw_before[u]};assert deltas=={145438:6,8436980:-6}
for form in[0,1]:assert source['counts'][form][8436980]==105 and target['counts'][form][8436980]==99 and target['counts'][form][145438]==source['counts'][form][145438]+6
struct_after=read(B/'target-native-structure.json')['records'];ab={x['ClubUID']:x for x in struct_after};assert len(ab)==len(by)
for u,z in by.items():
 a=ab[u]
 if u in allowed:assert a['CurrentDivisionIndex']==cfa and{k:v for k,v in a.items()if k!='CurrentDivisionIndex'}=={k:v for k,v in z.items()if k!='CurrentDivisionIndex'}
 else:assert a==z
assert sum(x['CurrentDivisionIndex']==cfa for x in struct_after)==59
# EB8DE0 live-derived semantic precondition: existing53direct and14generatedkind1; all Top2 parents/FAMILY data untouched.
semantic=dict(Status='PASS_DATA_PREDICTION_PENDING_GAME_TEST',NativeFunction='EB8DE0 FRE_CFA',Groups=4,TeamsPerGroup=18,RequiredCandidateCount=73,BeforeDirect=53,AfterDirect=59,LiveGeneratedKind1=14,PredictedAfterCandidates=73,PredictedPruneInclusiveIndices=[72,72],AllGeneratedReserveParentsTop2AndFAMILYUnchanged=True,Why='Only six kind0 self-FAMILY main TEAMs move from CFA2 to CFA; neither before nor after is Top2, no FAMILY or otherTEAM changes. Root live join showed all previous53direct included plus14generatedkind1. Extra6 follow identical directCurrentparent branch.',CFA2After=99,CFA2Minimum=96,CFA2RegisteredPlayable=False,RuntimeVerified=False,NoClaimOfCareerPass=True)
qa=dict(Status='NUMERIC_SELECTION_REGRESSION_PASS',Checks=checks,TotalChecks=325,PreviousChecks=233,CurrentBatchChecks=92,NewRegressions=regressions,CurrentBatchFailures=currentfail,InheritedUnchangedFailures=inherited,NewCountryNullTeams=[],NewCountryNullParticipants=[],RawSelectionSlotFindings=[],UnexpectedCompetitionCountDeltas=[],RawCurrentDeltaMismatch=False,DeclaredRawCurrentDeltas=deltas,RawSlotChanges=slotchanges,FreshSourceSIRead=True,SourceCacheUsed=False,SourceHashes=expected,TargetHashes=actual,Reader=str(qafile),ReaderSHA256=sha(qafile),RequirementsEvidencePins=evidencepins,RuntimeTest=False)
dump('selection-regression.json',qa);dump('semantic-cfa-guard.json',semantic)
proof=dict(Status='PASS_EXACT_12_INT32_FIELDS_WHOLE_SERVER_INVERSE_ALL_OTHER_FILES_IDENTICAL',Source=str(S),Output=str(D),SourceHashes=expected,OutputHashes=actual,AllowedUIDs=sorted(allowed),EditedInt32Fields=12,MaximumChangedRawSpanBytes=48,ActualChangedBytes=sum(x!=y for x,y in zip(raw,changed)),WholeSERVERInverse=True,OriginalHeader9BytesUnchanged=True,UncompressedLengthUnchanged=True,AllOtherFilesIdentical=True,PEOPLE_CLIENT_LANG_Rosters_Contracts_CA_PA_SugarDaddyUnchanged=True,SourceFrozenAndPublicUnchanged=True,Edits=[dict(Offset=o,BeforeHex=b.hex(),AfterHex=a.hex())for o,b,a in edits],TEAMWitnesses=witness,NoEngineHook=True,NoRosterImporter=True,NoNewUIDs=True,SI=False,new_career=False,season=False)
dump('native-patch-proof.json',proof)
assert pins(S)==pins(Path(f['source']))==expected and pins(D)==actual and sha(Path(f['original_X18_ZIP']))==f['original_X18_ZIP_SHA256']
ready=dict(status='PRIVATE_NATIVE_VERIFIED_READY_FOR_ROOT_PUBLICATION_REVIEW',name='TEST_X19',private_output=str(D),source=str(S),source_original=f['source'],source_status='X18_SI_SAVED_NEW_CAREER_FAILED_CFA',native=True,SI=False,new_career=False,season=False,source_hashes=expected,output_hashes=actual,scope='Six source-backed kind0 CFA2→CFA Current/ALT corrections only;12int32fields/max48rawbytes',source_freeze=str(B/'source-freeze.json'),native_proof=str(B/'native-patch-proof.json'),global_selection_qa=str(B/'selection-regression.json'),semantic_guard=str(B/'semantic-cfa-guard.json'),counts=read(X/'native-ready-for-root-review.json')['counts'],existing_roster_and_rating_counts_unchanged=True,source_X18_and_original_ZIP_unchanged=True,external_publication=False,public_X19_created=False,recorded_at=datetime.now(timezone.utc).isoformat())
dump('native-ready-for-root-review.json',ready);artifacts=[B/'source-freeze.json',B/'source-native-structure.json',B/'target-native-structure.json',B/'selection-regression.json',B/'semantic-cfa-guard.json',B/'native-patch-proof.json',B/'native-ready-for-root-review.json',Path(__file__)];dump('artifact-pins.json',{str(p.relative_to(B)):sha(p)for p in artifacts})
print('READY_X19_PRIVATE_NATIVE_ONLY;325QA/12fields/48BfullinversePASS; candidates59+14=73prediction; CFA2=99; gamePENDING',flush=True)
