from pathlib import Path
import json,csv,sys,hashlib,struct,bisect
sys.dont_write_bytecode=True
sys.path.insert(0,'J:/FM08dev/FM08-Database-Tools/scratch')
from create_italy_structure_i1_20261108 import load,languages,lang_sections,find_table,club
from audit_poland_v25_common_r1_20261108 import stadium
B=Path(__file__).resolve().parent.parent.parent;OUT=Path(__file__).resolve().parent;PUBLIC=Path('J:/FM08dev/Dane/db/TEST_X17')
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
inputs=[PUBLIC/'lang_db.dat',PUBLIC/'client_db.dat',PUBLIC/'server_db.dat',B/'club-plan.json',B/'structure-root-r2/structure-report.json',B/'prepared/club_map.csv']
pins={str(p):sha(p)for p in inputs}
blocks=dict(languages((PUBLIC/'lang_db.dat').read_bytes()));secs={k:lang_sections(blocks[k])[0]for k in [8,18]}
client=load(PUBLIC,'client_db.dat');fams,_,_=find_table(client,[r['uid']for r in secs[8]['club']],club);byfamily={r['uid']:r for r in fams}
stads,_,_=find_table(client,[r['uid']for r in secs[8]['stadium']],lambda c:stadium(c,19))
maprows=rows(B/'prepared/club_map.csv');mapping={int(r['ClubUID']):r for r in maprows};plans={int(r['NativeClubUID']or 0):r for r in read(B/'club-plan.json')}
plan_by_tm={r['TMID']:r for r in read(B/'club-plan.json')};sr=read(B/'structure-root-r2/structure-report.json');assign={r['ClubUID']:r for r in sr['venue_assignments']};venues={r['index']:r for r in sr['venues']}
uidtargets=[1800200042,1800200058,1800200060,1800200030];out=[]
for u in uidtargets:
 m=mapping[u];v=assign[u];si=v['StadiumIndex'];stad=stads[si];enstad=secs[8]['stadium'][si];plstad=secs[18]['stadium'][si];f=byfamily[u]
 assert stad['index']==si and stad['uid']==enstad['uid']==plstad['uid']==venues[si]['uid']
 positions={str(k):next(i for i,r in enumerate(sec['club'])if r['uid']==u)for k,sec in secs.items()}
 names={str(k):sec['club'][positions[str(k)]]['names']for k,sec in secs.items()}
 assert all(x==f['index']for x in positions.values())
 out.append(dict(UID=u,TMID=m['TMID'],Name=m['ClubName'],Country=m['Country'],Division=int(m['DivisionIndex']),FamilyIndex=f['index'],LANGPositions=positions,LANGNames=names,NativeStadiumIndex=si,NativeStadiumUID=stad['uid'],StadiumEN=enstad['names'],StadiumPL=plstad['names'],SourceVenueAddress=venues[si]['address'],SourceVenueCityIndex=venues[si]['city_index'],ClubProfileCity=plan_by_tm[m['TMID']].get('RegionAssignment',{}).get('City'),StadiumMappingBasis='Verified X17 structure venue assignment; same stadium index/UID/localized label exists in post-SI CLIENT/LANG; no live career access'))
slots={int(r['ClubUID'])for r in maprows if r['Country']=='Indonesia' or r['Country']=='India'and int(r['DivisionIndex'])==643};assert len(slots)==86
def exact_binary(arr,uid):
 lo=0;hi=len(arr)-1
 while lo<=hi:
  mid=(lo+hi)//2
  if arr[mid]==uid:return mid
  if arr[mid]<uid:lo=mid+1
  else:hi=mid-1
 return -1
lookup=[]
for lang,sec in secs.items():
 arr=[r['uid']for r in sec['club']];idx={u:i for i,u in enumerate(arr)}
 inversions=[dict(Position=i,PreviousUID=arr[i-1],UID=arr[i])for i in range(1,len(arr))if arr[i]<arr[i-1]]
 failed=[]
 for u in sorted(slots):
  at=bisect.bisect_left(arr,u)
  if at==len(arr)or arr[at]!=u:
   failed.append(dict(UID=u,Name=mapping[u]['ClubName'],Division=int(mapping[u]['DivisionIndex']),ActualPosition=idx[u],BinaryInsertionPosition=at))
 classic=[dict(UID=u,Name=mapping[u]['ClubName'],Division=int(mapping[u]['DivisionIndex']))for u in sorted(slots)if exact_binary(arr,u)<0]
 lookup.append(dict(ExactMatchBinarySearchSimulationFailuresAmong86=classic,Language=lang,RecordCount=len(arr),UIDOrderStrictlyIncreasing=all(arr[i]>arr[i-1]for i in range(1,len(arr))),Inversions=inversions,BinarySearchSimulationFailuresAmong86=failed,SimulationOnly=True,ActualNativeLookupAlgorithmNotEstablished=True))
assert pins=={str(p):sha(p)for p in inputs}
dump(OUT/'stadium-and-name-readback.json',dict(Status='READ_ONLY_FOUR_CANDIDATES_AND_CONDITIONAL_LOOKUP_AUDIT_COMPLETE',InputsBefore=pins,InputsAfter=pins,Clubs=out,LANGOrder=lookup,ExactUserClubUIDsFromStadium={'Kudungga':1800200042,'DelhiNFL':1800200058},SriwedariUIDCandidates=[1800200060,1800200030],SriwedariCityDiscriminator={'Surakarta_Solo':1800200060,'Kota_Biak':1800200030},NativeLookupCause='UNPROVEN_UNTIL_EXISTING_NATIVE_LOOKUP_EVIDENCE',DatabaseChanged=False,GameOrProcessAccess=False))
print(json.dumps(dict(Clubs=out,Lookup=lookup),ensure_ascii=True))