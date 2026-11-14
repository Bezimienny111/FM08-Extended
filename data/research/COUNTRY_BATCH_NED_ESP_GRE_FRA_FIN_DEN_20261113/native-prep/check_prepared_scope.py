from pathlib import Path
from datetime import date
import json,csv,hashlib,sys
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent;P=B/'prepared'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
m=read(P/'manifest.json');ps=rows(P/'native_players.csv');ids=rows(P/'identities.csv');provs=read(P/'provenance.json');ls=rows(P/'loans.csv');cm=rows(P/'club_map.csv');native={int(r['ID']):r for r in rows(B/'audit/players.csv')};world=read(B/'native-world-identities.json');teams={r['TeamIndex']for r in world}|{int(r['TeamIndex'])for r in cm};playing={int(r['TeamIndex'])for r in cm};seen=set();uid=set()
assert len(ps)==len(ids)==len(provs)==m['counts']['prepared'];assert len(cm)==602
for p,i,v in zip(ps,ids,provs):
 assert int(i['SubjectID'])==int(v['subject_id'])and int(i['ExistingID'])==int(p['ExistingID']);assert v['TMID']not in seen;seen.add(v['TMID'])
 assert int(i['PlayingClubIndex'])in playing and int(i['OwnerClubIndex'])in teams
 assert 1<=int(p['CA'])<=int(p['PA'])<=200
 d=date.fromisoformat(v['source_dob']);target=date.fromisoformat(i['TargetDOB']);assert target.year==d.year-19 and((target.month,target.day)==(d.month,d.day)or(d.month,d.day,target.month,target.day)==(2,29,2,28))
 if int(i['ExistingID'])>0:
  u=int(i['ExistingID']);assert u not in uid;uid.add(u);n=native[u];assert n['BirthDate']==i['ExpectedDOB']and(n['FirstName'],n['LastName'])==(i['ExpectedFirstName'],i['ExpectedLastName'])
  assert n['BirthDate']in[v['source_dob'],i['TargetDOB']]
loanids={int(x['SubjectID'])for x in ls};assert len(loanids)==len(ls);byid={int(x['SubjectID']):x for x in ids}
for l in ls:
 i=byid[int(l['SubjectID'])];assert int(l['OwnerClubIndex'])==int(i['OwnerClubIndex'])and int(l['LoanClubIndex'])==int(i['PlayingClubIndex']);assert l['BuyType']=='unknown'and not l['FeeToBuyNative']
 assert l['RealStartDate']<='2026-11-13'<l['RealEndDate']
proof=read(B/'N4-source-contract-preflight.json');proven={int(x['UID'])for x in proof['Rows']};assert not proof['Failures']and uid<=proven
protected=set(map(int,m['preserve_absent_uids']));legacy={u for u,n in native.items()if int(n['ClubIndex'])in playing and u not in uid and u not in protected};late=sorted(legacy-proven)
request=dict(UIDs=late,ParticipantUIDs=[],PotentialIdentityUIDs=[],LegacyRosterUIDs=late)
dump(B/'N4-late-requested-UIDs.json',request)
r=dict(Status='PASS_PREPARED_SCOPE_CSV_REFERENCES_SOURCE_IDENTITY',Counts=m['counts'],KnownReuseUIDs=len(uid),KnownReuseAllCoveredByOriginal9661=True,OriginalN4SHA256=sha(B/'N4-source-contract-preflight.json'),PotentialLegacyReleaseUIDs=len(legacy),LateUIDSubsetNeedsOneRead=len(late),NoWholePreflightRepeat=True,PlayingTEAMScope=len(playing),CountryAlloc602Complete=True,AllImportedTMIDsUnique=True,DateShiftExactlyOnce=True,AllLoanRowsConfirmedAndNoInventedBuyFee=True,DataFiles={f:sha(P/f)for f in ['native_players.csv','identities.csv','loans.csv','provenance.json','club_map.csv','manifest.json']},NativeWrite=False)
dump(B/'prepared-scope-verification.json',r);print(json.dumps({k:r[k]for k in ['Status','KnownReuseUIDs','PotentialLegacyReleaseUIDs','LateUIDSubsetNeedsOneRead']},ensure_ascii=True))