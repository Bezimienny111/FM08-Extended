from pathlib import Path
from datetime import date
import json,csv,hashlib,sys
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;P=B/'prepared';read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));rows=lambda p:list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
m=read(P/'manifest.json');ps=rows(P/'native_players.csv');ids=rows(P/'identities.csv');provs=read(P/'provenance.json');loans=rows(P/'loans.csv');cm=rows(P/'club_map.csv');projection={x['TMID']:x for x in rows(B/'club-map.csv')};native={int(x['ID']):x for x in rows(B/'audit/players.csv')};world=read(B/'native-world-identities.json');teams={x['TeamIndex']for x in world}|{int(x['TeamIndex'])for x in cm};playing={int(x['TeamIndex'])for x in cm};used=set();seen=set()
teams.update(int(x['TeamIndex'])for x in rows(B/'root-structure/foreign-owner-map.csv'));assert len(cm)==164 and len(ps)==len(ids)==len(provs)==m['counts']['prepared'] and 0<len(ps)<=4256
assert len(loans)==m['counts']['loans'] and len(loans)<=495
assert {int(c['CountryIndex'])for c in cm}<={139,175}
for c in cm:
 for k in ['ClubUID','TeamIndex','FamilyIndex','CountryIndex','ParentUID']:assert c[k]==projection[c['TMID']][k]
for p,i,v in zip(ps,ids,provs):
 assert int(i['SubjectID'])==int(v['subject_id'])and int(i['ExistingID'])==int(p['ExistingID']);assert v['TMID']not in seen;seen.add(v['TMID']);assert int(i['PlayingClubIndex'])in playing and int(i['OwnerClubIndex'])in teams;assert 1<=int(p['CA'])<=int(p['PA'])<=200
 d=date.fromisoformat(v['source_dob']);t=date.fromisoformat(i['TargetDOB']);assert t.year==d.year-19 and((t.month,t.day)==(d.month,d.day)or(d.month,d.day,t.month,t.day)==(2,29,2,28))
 if int(i['ExistingID'])>0:
  u=int(i['ExistingID']);assert u not in used;used.add(u);n=native[u];assert n['BirthDate']==i['ExpectedDOB']and(n['FirstName'],n['LastName'])==(i['ExpectedFirstName'],i['ExpectedLastName']);assert n['BirthDate']in[v['source_dob'],i['TargetDOB']]
byid={int(x['SubjectID']):x for x in ids};assert len({int(x['SubjectID'])for x in loans})==len(loans)
for l in loans:
 i=byid[int(l['SubjectID'])];assert int(l['OwnerClubIndex'])==int(i['OwnerClubIndex'])and int(l['LoanClubIndex'])==int(i['PlayingClubIndex']);assert l['BuyType']=='unknown'and not l['FeeToBuyNative'];assert l['RealStartDate']<='2026-11-14'<l['RealEndDate']
n4=read(B/'N4-source-contract-preflight.json');proven={int(x['UID'])for x in n4['Rows']};assert not n4['Failures']and len(proven)==n4['Requested']==n4['Passed'] and used<=proven
protected=set(map(int,m['preserve_absent_uids']));legacy={u for u,n in native.items()if int(n['ClubIndex'])in playing and u not in used and u not in protected};assert legacy<=proven,('unsupported legacy format',len(legacy-proven))
freeze=read(B/'source-freeze.json');assert all(sha(Path(freeze['frozen'])/k)==v for k,v in freeze['hashes'].items())
composite=dict(Status='PASS_PINNED_SOURCE_N4_ACTOR_SCOPE',OriginalCount=len(proven),LateSubsetCount=0,TotalDistinctUIDs=len(proven),Failures=0,ImportedReuseUIDs=len(used),AllImportedReuseCovered=True,AllPotentialLegacyReleasesCovered=True,ReadOnce=True,OriginalProofSHA256=sha(B/'N4-source-contract-preflight.json'),SourceHashes=freeze['hashes'],PredicateUnchanged='Unchanged N4Evidence from hash-pinned verified prior worker; X22 source and England actor scope only',NativeWrite=False)
dump(B/'N4-source-contract-composite.json',composite)
m.update(status='prepared_data_ready_actual_structure_contract_proofs_pending',source_identity_contract_composite_path=str(B/'N4-source-contract-composite.json'),source_identity_contract_composite_sha256=sha(B/'N4-source-contract-composite.json'),scope_id='england-20261114',pending_gates=['Actual England structure164club map and10newTEAM/FAMILY must pass inverse/country/parent/SugarOFF/global bank QA','Actual contract FAMILY proofs regenerate from materialized target; immutable projection must agree','Existing writer one collective pilot/full and exact actor readback; any explicitly prepared legacy rating repairs separately verified','Native pass does not imply SI/new-career/season pass'])
m['prepared_hashes']={str(p.relative_to(P)):sha(p)for p in P.rglob('*')if p.is_file()and p.name!='manifest.json'};dump(P/'manifest.json',m)
check=dict(Status='PASS_PREPARED_SCOPE_CSV_REFERENCES_SOURCE_IDENTITY',Counts=m['counts'],KnownReuseUIDs=len(used),N4CoveredRequestedCount=n4['Requested'],N4SHA256=sha(B/'N4-source-contract-preflight.json'),PotentialLegacyReleaseUIDs=len(legacy),AdditionalN4Required=0,PlayingTEAMScope=len(playing),CountryAllocation164Complete=True,AllImportedTMIDsUnique=True,DateShiftExactlyOnce=True,AllLoansConfirmedNoInventedDatesOrBuyFee=True,NativeWrite=False);dump(B/'prepared-scope-verification.json',check)
ready=dict(Status='PREPARED_CSV_READY_ACTUAL_NATIVE_STRUCTURE_PENDING',Counts=m['counts'],Files={f:sha(P/f)for f in ['native_players.csv','identities.csv','loans.csv','club_map.csv','provenance.json','deferred.json','legacy-rating-repairs.csv','manifest.json']},SourceN4CompositeSHA256=sha(B/'N4-source-contract-composite.json'),SourceFrozen22Unchanged=True,Projection164Unchanged=True,SourceCollectionNotRepeated=True,SingleN4ReadVerified=True,NativeWriteReady=False,NativeWrite=False,SI=False,NewCareer=False,Season=False);dump(B/'prepared-csv-ready.json',ready)
print('CSV_READY',m['counts']);print('N4',sha(B/'N4-source-contract-composite.json'));print('READY',sha(B/'prepared-csv-ready.json'));print('MANIFEST',sha(P/'manifest.json'));print('PROFILES',sha(P/'native_players.csv'))

