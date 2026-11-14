from pathlib import Path
from fractions import Fraction
import json,sys,hashlib,datetime,ast,httpx
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;P=B/'competition-prep';ROOT=B.parents[3]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
country='Argentina';dest=B/'scope-closures/Argentina.json';assert not dest.exists()
comps=[c for c in read(P/'source_competitions.json')if c['Country']==country];assert len(comps)==3
pdf=P/'sources/supplemental/afa6616-2025-regulations.pdf';pdf.parent.mkdir(exist_ok=True,parents=True)
if not pdf.exists():
 r=httpx.get('https://assets1.afa.com.ar/6616.pdf',timeout=40);r.raise_for_status();pdf.write_bytes(r.content)
dump(pdf.with_suffix('.source.json'),dict(URL='https://assets1.afa.com.ar/6616.pdf',SHA256=sha(pdf),Season=2025,Article='24.1+24.2,page28',Fact='Annual table sums points in Apertura regular zonephase and Clausura regular zonephase; tie GD then GF then headtohead. No playoff points included.',Budget='one new primarysource for multiphase ranking interpretation'))
phase={};previous={};inputs=[pdf,pdf.with_suffix('.source.json')]
for c in comps:
 f=B/c['previous_completed_table_file'];inputs.extend([f,B/c['current_clubs_file'],B/c['SeasonMetadataFile']]);tables=read(f)['tables'];assert len(tables)==2
 for table in tables:
  for r in table['rows']:
   tid=r['club_id'];q=dict(TMID=tid,Name=r['club_name'],PreviousLevel=c['RealLevel'],FinalPosition=r['position'],Matches=r['matches'],Points=r['points'],GoalDifference=r['goal_difference'],GoalsFor=r['goals_for'],Wins=r['wins'],SourceFile=str(f.relative_to(B)),Group=table['name'])
   if c['RealLevel']==1:
    assert r['matches']==16;phase.setdefault(tid,[]).append(q)
   else:
    assert r['matches']==34 and tid not in previous;previous[tid]=q
for f in (P/'sources/tm-competitions').glob('*-previous_completed-label2025-id*-clubs.json'):
 if f.name.split('-')[0]not in ['ARG3','AR3C','AR3D']:continue
 inputs.append(f)
 for r in read(f)['clubs']:
  t=r['id']
  if t not in previous:previous[t]=dict(TMID=t,Name=r['name'],PreviousLevel=3,FinalPosition=None,Matches=0,Points=0,GoalDifference=0,Wins=0,SourceFile=str(f.relative_to(B)),RankQualification='boundary membership proven; precise rank unnecessary allthirdlevelcandidates remain below top20secondcut')
annual=[]
for t,v in phase.items():
 assert len(v)==2
 q=dict(TMID=t,Name=v[0]['Name'],PreviousLevel=1,Matches=32,Points=sum(r['Points']for r in v),GoalDifference=sum(r['GoalDifference']for r in v),GoalsFor=sum(r['GoalsFor']for r in v),Wins=sum(r['Wins']for r in v),Components=v);annual.append(q)
annual.sort(key=lambda r:(-r['Points'],-r['GoalDifference'],-r['GoalsFor'],int(r['TMID'])))
assert len(annual)==30 and annual[0]['Points']==66 and 'Rosario' in annual[0]['Name']
for i,r in enumerate(annual,1):r['FinalPosition']=i;previous[r['TMID']]=r
engine=ROOT/'FmLauncher/data/research/COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/competition-prep/build_source_cascade_plan.py';tree=ast.parse(engine.read_text(encoding='utf-8-sig'));fn=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='ranking_key'];exec(compile(ast.Module(body=fn,type_ignores=[]),str(engine),'exec'),globals())
profiles=read(P/'club-profiles-Argentina.json');ids={r['TMID']:r for r in read(P/'club-identities-Argentina.json')};assert len(profiles)==66 and all(v['SourceRef']and v['SourceClubTypeID']==1 and not v['ParentTMID']and v['SourceCountryID']==9 for v in ids.values())
top=[r for r in profiles if r['RealLevel']==1];continuing=[r for r in top if previous.get(r['TMID'],{}).get('PreviousLevel')==1];assert len(top)==30 and len(continuing)==28
continuing.sort(key=ranking_key);demote={r['TMID']for r in continuing[-10:]};topids={r['TMID']for r in top}-demote
secondpool=[r for r in profiles if r['TMID']not in topids];assert len(secondpool)==46 and all(r['TMID']in previous for r in secondpool);secondpool.sort(key=ranking_key);secondids={r['TMID']for r in secondpool[:20]};assert demote<=secondids
assign=[]
for r in profiles:
 t=r['TMID'];level=1 if t in topids else 2 if t in secondids else 3;uid,index={1:(102421,71),2:(102422,72),3:(108573,94)}[level]
 q=dict(r,ParentTMID=None,SourceClubTypeID=1,SourceCountryID=9,ClubIdentityPending=False,SourceScope='closed_country_Argentina',SourceIdentityEvidence=ids[t]['SourceRef'],TargetNativeLevel=level,TargetNativeCompetitionUID=uid,TargetNativeDivisionIndex=index,NativeUIDAllocated=False,PreviousFacts=previous.get(t),ClassicPlacementReason='currenttop30 minus10lowest continuing by final2025annual; current2promoted protected'if level==1 else 'cascade20:previous higherlevel first then completed2025groupplace/PPG/GD/Wins/stableID'if level==2 else 'remaining26to existingnonplayableThirdpool');assign.append(q)
assert [sum(r['TargetNativeLevel']==l for r in assign)for l in [1,2,3]]==[20,20,26]
dump(P/'argentina-2025-annual-normalized.json',dict(Rule='AFA6616article24.1/24.2',Rows=annual,SourceOnly=True,NoInProgress2026Performance=True,UnresolvedTieQualification='No points/GD/GF tie crosses top20 cutoff; later crossgroup cascade uses saved universal rank'))
dump(P/'source-cascade-Argentina.json',dict(Status='CLOSED_SOURCE_COUNTRY_SCOPE_NOT_NATIVE_PREFLIGHT',Assignments=assign,DemotedTopTMIDs=sorted(demote),Counts=[20,20,26],CurrentSource=[30,36],ProtectedNewTop=[r for r in top if r not in continuing],SecondOrderedCandidates=secondpool,LowerPoolQualification='26remainder toexistingCOMP108573 noR5minimum forlowerArgentinepools; do notinfersecondexact20 fromcount, R5explicitexact20.',BeforeNativeWrite=['Preserve Current andeffectiveALT exact20/20 independently','Pinned nativeidentity mapping and no reuse bycity/namealone','Full native selector and legacy physicalparticipants projection','SI/newcareer/season separate']))
target=B/'scope-closures/Argentina-targets.json';dump(target,assign)
inputs.extend([P/'argentina-2025-annual-normalized.json',P/'native-competition-requirements.json',P/'club-profiles-Argentina.json',P/'club-identities-Argentina.json',engine,ROOT/'FmLauncher/data/research/COUNTRY_BATCH_CZE_CRO_CHN_CHI_BGR_BRA_20261113/native-prep/root-structure/native-structure-after.json'])
dump(dest,dict(Status='CLOSED_NATIVE_CASCADE_CLUB_IDENTITIES_AND_PARENTS',Country=country,Clubs=66,TargetsSHA256=sha(target),SourceCollectionScopeApproved=True,AllParentsResolvedOrExplicitDeferred=True,PendingParentCount=0,NativeSchedulerEligibilityReviewed=True,EligibilityQualification='All66source firstteams country9/parentless; R5registered2exact20levels; completed2025annual and secondgroup ranking cascade20/20/26closed. Nativeprojection/runtime separate.',NativeUIDAllocated=False,DatabaseWritten=False,ClosedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),Inputs={str(f):sha(f)for f in inputs}))
old=read(B/'source-targets.json')if(B/'source-targets.json').exists()else[];assert not any(r['Country']==country for r in old);dump(B/'source-targets.json',old+assign);print('CLOSED',country,len(assign),sha(target));print('TOPDEMOTIONS',[(r['Name'],previous[r['TMID']]['FinalPosition'])for r in continuing[-10:]])

