from pathlib import Path
from fractions import Fraction
import json,sys,hashlib,datetime,ast,httpx,re
import html
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;P=B/'competition-prep';ROOT=B.parents[3]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
country='Austria';dest=B/'scope-closures/Austria.json';assert not dest.exists()
comps=[c for c in read(P/'source_competitions.json')if c['Country']==country and c['RealLevel']<=2];assert len(comps)==2
raw=P/'sources/supplemental/rsssf-austria-final2025-26.html';raw.parent.mkdir(exist_ok=True,parents=True)
if not raw.exists():
 r=httpx.get('https://www.rsssf.org/tableso/oost2026.html',timeout=40);r.raise_for_status();raw.write_bytes(r.content)
text=html.unescape(re.sub(r'<[^>]+>','',raw.read_bytes().decode('utf-8',errors='replace')));secondtext=text[text.index('2. Liga (Second Level)'):];secondtext=secondtext[:secondtext.index('Regionalliga')];assert 'all results annulled' in secondtext
previous={};inputs=[raw]
for c in comps:
 f=B/c['previous_completed_table_file'];inputs.extend([f,B/c['current_clubs_file'],B/c['SeasonMetadataFile']]);tables=read(f)['tables']
 for k,tab in enumerate(tables):
  for r in tab['rows']:
   t=r['club_id'];pos=r['position']+(6*k if c['RealLevel']==1 else 0)
   previous[t]=dict(PreviousLevel=c['RealLevel'],FinalPosition=pos,Matches=r['matches'],Points=r['points'],GoalDifference=r['goal_difference'],Wins=r['wins'],SourceFile=str(f.relative_to(B)))
   if c['RealLevel']==2 and t!='20296':
    # RSSSF final sporting order matches provider; Stripfing games are annulled in final statistics.
    line=next((s for s in secondtext.splitlines()if re.match(r'\s*'+str(pos)+r'\..*?\s+28\s+',s)),None);assert line,(t,pos)
    m=re.match(r'\s*(\d+)\.(.*?)\s+(28)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)-(\s*\d+)\s+(\d+)',line);assert m,line
    _,name,played,w,d,l,gf,ga,pts=m.groups();previous[t].update(Matches=28,Points=int(pts),GoalDifference=int(gf)-int(ga),Wins=int(w),PreviousFinalName=name.strip(),FinalSourceFile=str(raw.relative_to(B)),FinalQualification='RSSSF final28games excludes annulledStripfing; provider rawretained, no doubledeductions')
engine=ROOT/'FmLauncher/data/research/COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/competition-prep/build_source_cascade_plan.py';tree=ast.parse(engine.read_text(encoding='utf-8-sig'));fn=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='ranking_key'];exec(compile(ast.Module(body=fn,type_ignores=[]),str(engine),'exec'),globals())
profiles=[r for r in read(P/'club-profiles-Austria.json')if r['RealLevel']<=2];ids={r['TMID']:r for r in read(P/'club-identities-Austria.json')if r['TMID']in {v['TMID']for v in profiles}};assert len(profiles)==28 and all(v['SourceRef']and v['SourceClubTypeID']in[1,2]and v['SourceCountryID']==127 for v in ids.values())
top=[r for r in profiles if r['RealLevel']==1];continuing=[r for r in top if previous.get(r['TMID'],{}).get('PreviousLevel')==1];assert len(top)==12 and len(continuing)==11
continuing.sort(key=ranking_key);down1={r['TMID']for r in continuing[-2:]};topids={r['TMID']for r in top}-down1
second=[r for r in profiles if r['TMID']not in topids];cont2=[r for r in second if previous.get(r['TMID'],{}).get('PreviousLevel')==2];cont2.sort(key=ranking_key);down2={r['TMID']for r in cont2[-6:]};assert len(second)==18 and down2=={'11853','23158','7001','2394','4443','936'}
regional={'11853':(5607688,628),'936':(5607688,628),'23158':(5607687,627),'2394':(5607687,627),'4443':(5607687,627),'7001':(136546,247)}
assign=[];byid={r['TMID']:r for r in profiles}
for r in profiles:
 t=r['TMID'];i=ids[t];level=1 if t in topids else 3 if t in down2 else 2;uid,index=(136543,244)if level==1 else (136544,245)if level==2 else regional[t]
 parent=i['ParentTMID'];assert not parent or parent in topids,(t,parent)
 q=dict(r,ParentTMID=parent,ParentName=byid[parent]['Name']if parent else None,ParentIdentityEvidence=ids[parent]['SourceRef']if parent else None,SourceClubTypeID=i['SourceClubTypeID'],SourceCountryID=i['SourceCountryID'],ClubIdentityPending=False,SourceScope='closed_country_Austria',SourceIdentityEvidence=i['SourceRef'],TargetNativeLevel=level,TargetNativeCompetitionUID=uid,TargetNativeDivisionIndex=index,NativeUIDAllocated=False,PreviousFacts=previous.get(t),ClassicPlacementReason='12to10top using final25/26lowerphase with globally offsetpositions; newlypromoted protected'if level==1 else '18to12second lowest6continuing by final25/26;2newlypromoted protected'if level==2 else 'sixsecondcascade to nativegeographicalRegionalliga; preserve identity+parent')
 assign.append(q)
assert [sum(r['TargetNativeLevel']==l for r in assign)for l in[1,2,3]]==[10,12,6]
worldfile=ROOT/'FmLauncher/data/research/COUNTRY_BATCH_CZE_CRO_CHN_CHI_BGR_BRA_20261113/native-prep/native-world-identities.json';world=read(worldfile);witness=[r for r in world if r['CurrentDivision']==245 and r['NativeTeamKind']!=0];assert any(r['ClubUID']==137953 and r['NativeTeamKind']==14 and r['ParentUID']==152 for r in witness)
dump(P/'source-cascade-Austria.json',dict(Status='CLOSED_SOURCE_COUNTRY_SCOPE_NOT_NATIVE_PREFLIGHT',Assignments=assign,Counts=[10,12,6],Parents=[i for i in ids.values()if i['ParentTMID']],NativeReservePlayingWitnesses=witness,NativeRequiredLowerPoolsPreserved=True,NativeMinima='East16/Central16/West15 and9statepools4each are preserved; only6incominglower moves planned, no currentwholeregionalupdateclaim',ReserveQualification='StockA2 actualKind14parentlinked Austria/Salzburg amateurs provide supportedclassicreserveplayingwitness; no blanketreserveban. Allfourcurrentparentsremain top10.',SourceConflict=dict(TMA2='invalidatedStripfingmatches remain inraw29/13',FinalChoice='RSSSF endseason28matches; sameplacementboundary',AdditionalSourcesBudget='official2liga historicalURLunavailable + RSSSFfinal, max2used; no furthersearch'),BeforeNativeWrite=['IndependentnativeCurrent/effectiveALT/minmax/regionalstockloaderprojection','NoidentityreuseLiefering/Wacker/etcwithoutcontinuitytypedproof','Preserve documentedstockKind14andparentrelationship; nofantasyfirstteam','Physicallegacyfallback/backfillwherepreservingpoolminima requires; userrules noformatrelaxation'],DeferredSourceMetadata='New2026RegionalligaSouth/North/West have noprevious25/26 undernewcompetitionID. Not needed for2playabletiers+6incomingregionalcascade. No fabricated previoussame-IDtable.'))
target=B/'scope-closures/Austria-targets.json';dump(target,assign);inputs.extend([P/'native-competition-requirements.json',P/'club-profiles-Austria.json',P/'club-identities-Austria.json',P/'source-cascade-Austria.json',worldfile,engine,ROOT/'FmLauncher/data/research/COUNTRY_BATCH_CZE_CRO_CHN_CHI_BGR_BRA_20261113/native-prep/root-structure/native-structure-after.json'])
dump(dest,dict(Status='CLOSED_NATIVE_CASCADE_CLUB_IDENTITIES_AND_PARENTS',Country=country,Clubs=28,TargetsSHA256=sha(target),SourceCollectionScopeApproved=True,AllParentsResolvedOrExplicitDeferred=True,PendingParentCount=0,NativeSchedulerEligibilityReviewed=True,EligibilityQualification='2registeredclassic10/12; allfourreserveparents currenttop10, stockA2Kind14parentlinkedreserve witness retained.6lowercascade geographically fixed. Sourceonly notnativewrite/runtimePASS.',NativeUIDAllocated=False,DatabaseWritten=False,ClosedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),Inputs={str(f):sha(f)for f in inputs}))
old=read(B/'source-targets.json')if(B/'source-targets.json').exists()else[];assert not any(r['Country']==country for r in old);dump(B/'source-targets.json',old+assign);print('CLOSED',country,len(assign),sha(target), 'TOPDOWN',down1,'SECONDDOWN',down2)


