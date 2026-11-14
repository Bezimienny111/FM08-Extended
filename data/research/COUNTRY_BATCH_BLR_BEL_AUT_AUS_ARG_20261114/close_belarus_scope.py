from pathlib import Path
from fractions import Fraction
import json,sys,hashlib,datetime,ast
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;P=B/'competition-prep';ROOT=B.parents[3]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
country='Belarus';dest=B/'scope-closures/Belarus.json';assert not dest.exists()
comps=[c for c in read(P/'source_competitions.json')if c['Country']==country];assert len(comps)==2
previous={};inputs=[]
for c in comps:
 f=B/c['previous_completed_table_file'];inputs.extend([f,B/c['current_clubs_file'],B/c['SeasonMetadataFile']]);tab=read(f)['tables'];assert len(tab)==1
 for r in tab[0]['rows']:
  assert r['matches']==(30 if c['RealLevel']==1 else 34)
  previous[r['club_id']]=dict(PreviousLevel=c['RealLevel'],FinalPosition=r['position'],Matches=r['matches'],Points=r['points'],GoalDifference=r['goal_difference'],Wins=r['wins'],SourceFile=str(f.relative_to(B)))
engine=ROOT/'FmLauncher/data/research/COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/competition-prep/build_source_cascade_plan.py';tree=ast.parse(engine.read_text(encoding='utf-8-sig'));fn=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='ranking_key'];exec(compile(ast.Module(body=fn,type_ignores=[]),str(engine),'exec'),globals())
profiles=read(P/'club-profiles-Belarus.json');ids={r['TMID']:r for r in read(P/'club-identities-Belarus.json')};assert len(profiles)==34 and all(v['SourceRef']and v['SourceClubTypeID']in[1,2]and v['SourceCountryID']==18 for v in ids.values())
top=[r for r in profiles if r['RealLevel']==1];continuing=[r for r in top if previous.get(r['TMID'],{}).get('PreviousLevel')==1];assert len(top)==16 and len(continuing)==13
continuing.sort(key=ranking_key);down1={r['TMID']for r in continuing[-2:]};topids={r['TMID']for r in top}-down1
second=[r for r in profiles if r['TMID']not in topids];cont2=[r for r in second if previous.get(r['TMID'],{}).get('PreviousLevel')==2];cont2.sort(key=ranking_key);down2={r['TMID']for r in cont2[-6:]};assert len(second)==20 and len(down2)==6
assign=[];byid={r['TMID']:r for r in profiles}
for r in profiles:
 t=r['TMID'];i=ids[t];level=1 if t in topids else 3 if t in down2 else 2;uid,index={1:(7483354,799),2:(7483366,800),3:(7483369,801)}[level];parent=i['ParentTMID'];assert not parent or parent in topids,(t,parent)
 assign.append(dict(r,ParentTMID=parent,ParentName=byid[parent]['Name']if parent else None,ParentIdentityEvidence=ids[parent]['SourceRef']if parent else None,SourceClubTypeID=i['SourceClubTypeID'],SourceCountryID=18,ClubIdentityPending=False,SourceScope='closed_country_Belarus',SourceIdentityEvidence=i['SourceRef'],TargetNativeLevel=level,TargetNativeCompetitionUID=uid,TargetNativeDivisionIndex=index,NativeUIDAllocated=False,PreviousFacts=previous.get(t),ClassicPlacementReason='16to14top completed2025rank;newpromotedprotected'if level==1 else '20to14second completed2025rank;newpromotedprotected'if level==2 else '6demotedfromsecondtoexact16nonplayableSecondLeague',TechnicalScopeGap='10nativephysicallegacy senior stand-ins still required beside6modernsourceThirdteams; no current2026identity/rank asserted for stand-ins'))
assert [sum(r['TargetNativeLevel']==l for r in assign)for l in[1,2,3]]==[14,14,6]
D=ROOT/'FmLauncher/data/research/GHIDRA_ENGINE_20261107_R5/decompiled/functions';inputs.extend([D/'ram_e53a80.c',D/'ram_e53b80.c',D/'ram_e54920.c',D/'ram_e54e50.c'])
dump(P/'source-cascade-Belarus.json',dict(Status='CLOSED_SOURCE_SCOPE_WITH_EXPLICIT_NATIVE_LOWER_GAP',Assignments=assign,Counts=[14,14,6],ExactThird16Required=True,RequiredNativeLegacyStandIns=10,LegacyStandInPolicy='Futurepinnednativeprojection must choose10unambiguousphysicalKind0/knowncountry existingThirdstand-ins; reporttechnicallegacyunmodernized, notcurrent2026membersorcurrentrank.6otherlegacydisplacements togenericLower; min8preserved. NoDATwritebeforefullCurrent/effectiveALT checks.',NativeWriterAllowed=False,Parents=[r for r in ids.values()if r['ParentTMID']],SchedulerQualification='e54920mainseasoninitializer14firstyear, historical>=2008default16; e54e50second14. R5selector declarations14/14/16exact+Lower8. Do notdeclareALTequalCurrent fromcounts; futurestockloaderoverlaymustrespecthistoricalexpansion.',ReserveEligibility='All4parentlinks exactrawmainClubId; allparentsremaintop14. NativeKind/periodeligibilitynotyetproven forBelarus modernreserves, do not claim seasonPASS. Futuretypednativeproof or explicitdefer/physicalfallback beforeDAT.',SourceBoundaryBudget='TMthirdsearch unavailable;2025/2026football.by/2liga evidence showslargeamateurregionaltournament. No forced122amateurrosters; rootacceptedsource34withexplicittechnicallegacygap2026-11-14.'))
target=B/'scope-closures/Belarus-targets.json';dump(target,assign);inputs.extend([P/'native-competition-requirements.json',P/'club-profiles-Belarus.json',P/'club-identities-Belarus.json',P/'source-cascade-Belarus.json',engine,ROOT/'FmLauncher/data/research/COUNTRY_BATCH_CZE_CRO_CHN_CHI_BGR_BRA_20261113/native-prep/root-structure/native-structure-after.json'])
dump(dest,dict(Status='CLOSED_NATIVE_CASCADE_CLUB_IDENTITIES_AND_PARENTS',Country=country,Clubs=34,TargetsSHA256=sha(target),SourceCollectionScopeApproved=True,AllParentsResolvedOrExplicitDeferred=True,PendingParentCount=0,NativeSchedulerEligibilityReviewed=False,EligibilityQualification='ClosedDATAcollection34with14/14plus6lowercascade;4rawparents resolved. Stockreserveeligibility/ALTprojection separatependinggate. NativeWriterAllowed=False.',ExactThird16Required=True,TechnicalScopeGap='10knowncountryKind0nativephysicallegacystand-insmustbedocumentedbeforeDAT; notmodern2026clubs',NativeWriterAllowed=False,NativeUIDAllocated=False,DatabaseWritten=False,ClosedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),Inputs={str(f):sha(f)for f in inputs}))
old=read(B/'source-targets.json')if(B/'source-targets.json').exists()else[];assert not any(r['Country']==country for r in old);dump(B/'source-targets.json',old+assign);print('CLOSED_SOURCE',country,len(assign),sha(target),'TOPDOWN',down1,'SECONDDOWN',down2)

