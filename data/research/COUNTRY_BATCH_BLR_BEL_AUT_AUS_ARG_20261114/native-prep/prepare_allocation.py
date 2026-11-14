from pathlib import Path
from collections import Counter
import json,sys,struct,copy,unicodedata,re
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent;S=B.parent
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
from create_italy_structure_i1_20261108 import load,languages,lang_sections,find_table
from audit_poland_v25_common_r1_20261108 import stadium,city
rd=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(name,x):(B/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
world={x['ClubUID']:x for x in rd(B/'native-world-identities.json')};plans=rd(B/'club-plan.json');fallback=rd(B/'structural-fallbacks.json');cat=rd(B/'competition-catalog.json');uididx={x['uid']:x['index']for x in cat};idxuid={x['index']:x['uid']for x in cat};idxuid[-1]=None
src=Path(rd(B/'source-freeze.json')['frozen']);buf=load(src,'server_db.dat');en,_=lang_sections(dict(languages((src/'lang_db.dat').read_bytes()))[8]);st,_,_=find_table(buf,[x['uid']for x in en['stadium']],lambda c:stadium(c,62));cities,_,_=find_table(buf,[x['uid']for x in en['city']],city)
geo={x['ClubUID']:{'stadium':en['stadium'][x['StadiumIndex']]['names'] if 0<=x['StadiumIndex']<len(st)else[], 'city': en['city'][struct.unpack_from('<i',st[x['StadiumIndex']]['raw'],46)[0]]['names'] if 0<=x['StadiumIndex']<len(st) and 0<=struct.unpack_from('<i',st[x['StadiumIndex']]['raw'],46)[0]<len(cities)else[]} for x in world.values()}
raw={}
for x in rd(B/'native-structure.json')['records']:
 assert struct.unpack_from('<iI',buf,x['Footer'])==(x['TeamIndex'],x['ClubUID']);v=[struct.unpack_from('<i',buf,x['Start']+p)[0]for p in [7,15,47]];assert v[0]==world[x['ClubUID']]['CurrentDivision'] and all(i in idxuid for i in v);raw[x['ClubUID']]=v
country={u:x['TeamCountry'] for u,x in world.items()};kind={u:x['NativeTeamKind']for u,x in world.items()};target=copy.deepcopy(raw);core=set();assign=[]
# One logical key per new TEAM until complete projection passes.
for x in plans:
 k=x['NativeClubUID'] or 'tm:'+x['TMID'];core.add(k)
 if isinstance(k,str):target[k]=[-1,-1,-1];country[k]=x['NativeCountryIndex'];kind[k]=x.get('RequiredNativeReserveKind',0)
 d=x['DesiredDivision'];target[k][0]=d;target[k][1]=x['DesiredAlternative'] if x['DesiredAlternative']is not None else -1
 assign.append(dict(Key=k,TMID=x['TMID'],Country=x['Country'],DesiredDivision=d,DesiredAlternative=target[k][1],DesiredRegional=target[k][2],NativeKind=kind[k]))
for x in fallback:
 k=x['NativeClubUID'];core.add(k);target[k][0]=x['DesiredDivision'];target[k][1]=-1;assign.append(dict(Key=k,TMID=None,Country=x['Country'],DesiredDivision=x['DesiredDivision'],DesiredAlternative=-1,DesiredRegional=target[k][2],StructuralOnly=True,NativeKind=kind[k]))
# Balance 32 Belgian third-level seniors into existing two classic regions.
third=[a for a in assign if a['Country']=='Belgium' and a['DesiredDivision']is None];assert len(third)==32
bytm={x['TMID']:x for x in plans};assigned=Counter()
for a in sorted(third,key=lambda a:(a['TMID']is not None,str(a['Key']))):
 old=raw.get(a['Key'],[-1])[0]
 if old in [2,3] and assigned[old]<16:d=old
 else:
  p=rd(Path(bytm[a['TMID']]['ProfileFile']))if a['TMID']else{};longitude=(p.get('stadium')or{}).get('longitude');preferred=2 if longitude is None or longitude<4.6 else 3;d=preferred if assigned[preferred]<16 else 5-preferred
 assigned[d]+=1;a['DesiredDivision']=d;target[a['Key']][0]=d
assert assigned==Counter({2:16,3:16})
# Preserve every existing kind/family; displace old playing fields below modernized fields.
playing={0,1,2,3,799,800,244,245,157,71,72};displaced=[]
for k,v in target.items():
 if k in core or raw[k][0]not in playing:continue
 ni=country[k];d=550
 if ni==132:d=802
 elif ni==129:
  if raw[k][2]in [247,627,628]:d=raw[k][2]
  else:
   text=' '.join(geo[k]['city']+world[k]['Names']).lower()
   d=247 if any(s in text for s in ['wien','vienna','schwadorf','parndorf','mattersburg','burgenland']) else 628 if any(s in text for s in ['salzburg','lustenau','tirol','innsbruck','bregenz']) else 627
 elif ni==177:d=1071
 elif ni==187:d=94
 target[k][0]=d;target[k][1]=-1;displaced.append(dict(ClubUID=k,Before=raw[k],After=list(v),Names=world[k]['Names'][:2],Reason='Preserve displaced historical club below closed current playing fields'))
# Exact unplayable Belarus pool: retained10 plus source6; move remaining historical members to existing lower802.
for k,v in target.items():
 if k not in core and raw[k][0]==801:target[k][0]=802;target[k][1]=-1
# Concrete existing senior backfills for vacated regional feeder slots. No roster/name/kind changes.
lower_backfill={539784:785,539801:786,527960:786,230:787,295:787,527936:787,16009509:247}
for u,d in lower_backfill.items():
 assert u not in core and world[u]['NativeTeamKind']==0 and not world[u]['ParentUID']
 assert country[u]==(129 if d==247 else 131)
 target[u][0]=d;target[u][1]=-1
# Native counters include effective ALT and additive regional membership.
req=rd(S/'competition-prep/native-competition-requirements-scoped-r2.json')['requirements'];checks=[]
def counts():
 cc=[Counter(),Counter()]
 for k,(cur,alt,regional)in target.items():
  if country[k] is None or country[k]<0:continue
  assert cur is not None
  for f,d in enumerate([cur,alt if alt>=0 else cur]):
   if d>=0:cc[f][d]+=1
   if regional>=0:cc[f][regional]+=1
 return cc
c=counts()
for q in req:
 i=uididx[q['CompetitionUID']]
 for f in [0,1]:
  lo=q['Form0Min']if f==0 else q['Form1DefaultMin'];hi=q['Form0Max']if f==0 else q['Form1DefaultMax'];number=c[f][i]
  checks.append(dict(Country=q['Country'],UID=q['CompetitionUID'],Index=i,Form=f,Count=number,Min=lo,Max=hi,Passed=number>=lo and(hi is None or number<=hi)))
for a in assign:
 if a['TMID']:
  x=bytm[a['TMID']];x['DesiredDivision']=a['DesiredDivision'];x['TargetNativeCompetitionUID']=idxuid[a['DesiredDivision']];x['DesiredAlternative']=a['DesiredAlternative']
 else:next(x for x in fallback if x['NativeClubUID']==a['Key'])['DesiredDivision']=a['DesiredDivision']
# Output draft even on a technical failure, without allocating UIDs or writing DAT.
dump('allocation-projection.json',dict(Status='PROJECTION_PASS'if all(q['Passed']for q in checks)else'PROJECTION_REQUIRES_BACKFILL',Assignments=assign,Checks=checks,Displaced=displaced,LowerBackfills=[dict(ClubUID=u,Before=raw[u],After=target[u],Names=world[u]['Names'][:2],Modernized=False)for u in lower_backfill],Failures=[q for q in checks if not q['Passed']],NativeWrite=False))
dump('allocation-raw-state.json',dict(Before=raw,After=target,Country=country,Kind=kind,ProtectedCore=list(core)));dump('native-venue-identity-cache.json',geo)
dump('club-plan-allocated.json',plans);dump('structural-fallbacks-allocated.json',fallback)
print(json.dumps(dict(Assignments=len(assign),NewLogicalTeams=sum(isinstance(a['Key'],str)for a in assign),NativeChecks=len(checks),Failures=[q for q in checks if not q['Passed']],Displaced=len(displaced)),ensure_ascii=False),flush=True)
