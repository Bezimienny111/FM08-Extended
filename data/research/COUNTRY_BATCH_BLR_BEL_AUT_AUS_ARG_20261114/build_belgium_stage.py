from pathlib import Path
from fractions import Fraction
import json,sys,hashlib,datetime,ast
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;P=B/'competition-prep';ROOT=B.parents[3]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
comps=[c for c in read(P/'source_competitions.json')if c['Country']=='Belgium'];previous={};inputs=[]
for c in comps:
 f=B/c['previous_completed_table_file'];inputs.extend([f,B/c['current_clubs_file'],B/c['SeasonMetadataFile']]);tables=read(f)['tables'];assert len(tables)==1
 for r in tables[0]['rows']:
  t=r['club_id'];previous[t]=dict(TMID=t,Name=r['club_name'],PreviousLevel=c['RealLevel'],FinalPosition=r['position'],Matches=r['matches'],Points=r['points'],GoalDifference=r['goal_difference'],Wins=r['wins'],SourceFile=str(f.relative_to(B)),Competition=c['id'])
phasefacts=[]
for code,offset in [('B3AB',0),('BE3B',6)]:
 f=P/'sources/tm-competitions'/(code+'-previous_completed-label2025-id2025-table.json');meta=P/'sources/tm-competitions'/(code+'-available-seasons.json');assert any(r['name']=='25/26'and r['id']=='2025'for r in read(meta)['seasons']);inputs.extend([f,meta]);tab=read(f)['tables'];assert len(tab)==1 and len(tab[0]['rows'])==6
 for r in tab[0]['rows']:
  t=r['club_id'];old=previous[t];assert old['Competition']=='BE3A'and old['Matches']==22 and r['matches']==10
  # Retain official final points/order; phase-only10matches is not total season32.
  q=dict(old,FinalPosition=r['position']+offset,Matches=32,Points=r['points'],PhaseOnlyMatches=r['matches'],RegularMatches=22,PhaseOnlyGoalDifference=r['goal_difference'],PhaseOnlyWins=r['wins'],SourceFile=str(f.relative_to(B)),RegularFacts=old,RankQualification='Final play-off order with championship1..6/relegation7..12. Matches32=22regular+10playoff; retain final official points includingcarryover, do not add phasepoints. Rawfilename label2025islegacyhelpertext; metadata exact25/26id2025. GD/wins totalsnotneeded atpromotioncut becausePPGuntied.')
  previous[t]=q;phasefacts.append(q)
engine=ROOT/'FmLauncher/data/research/COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/competition-prep/build_source_cascade_plan.py';tree=ast.parse(engine.read_text(encoding='utf-8-sig'));fn=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='ranking_key'];exec(compile(ast.Module(body=fn,type_ignores=[]),str(engine),'exec'),globals())
profiles=read(P/'club-profiles-Belgium.json');ids={r['TMID']:r for r in read(P/'club-identities-Belgium.json')};assert len(profiles)==61 and all(r['SourceRef']and r['SourceCountryID']==19 and r['SourceClubTypeID']in[1,2,3]for r in ids.values())
top={r['TMID']for r in profiles if r['RealLevel']==1};reserves={t for t,r in ids.items()if r['ParentTMID']};assert len(top)==18 and len(reserves)==9 and all(ids[t]['ParentTMID']in top for t in reserves)
second={r['TMID']for r in profiles if r['RealLevel']==2 and r['TMID']not in reserves};assert len(second)==11
third=[r for r in profiles if r['RealLevel']==3 and r['TMID']not in reserves];assert len(third)==23;rankable=[r for r in third if r['TMID']in previous];unranked=[r for r in third if r['TMID']not in previous];assert len(rankable)>=7;third=sorted(rankable,key=ranking_key)+unranked;promoted={r['TMID']for r in third[:7]};second|=promoted
assert promoted=={'54189','3146','18940','54291','64099','3772','21366'},promoted
assert previous['21366']['Points']*previous['11939']['Matches']>previous['11939']['Points']*previous['21366']['Matches'],'cutoffPPGdominateswithoutneedingunresolvedGDaggregate'
assign=[];byid={r['TMID']:r for r in profiles}
for r in profiles:
 t=r['TMID'];i=ids[t];level=1 if t in top else 5 if t in reserves else 2 if t in second else 3;uid,index=(1,0)if level==1 else (2,1)if level==2 else (1301432,550)if level==5 else (None,None)
 parent=i['ParentTMID'];assign.append(dict(r,ParentTMID=parent,ParentName=byid[parent]['Name']if parent else None,ParentIdentityEvidence=ids[parent]['SourceRef']if parent else None,SourceClubTypeID=i['SourceClubTypeID'],SourceCountryID=19,ClubIdentityPending=False,SourceScope='staged_Belgium_notclosed_wait16Fourth',SourceIdentityEvidence=i['SourceRef'],TargetNativeLevel=level,TargetNativeCompetitionUID=uid,TargetNativeDivisionIndex=index,TargetNativeCompetitionUIDs=[3,4]if level==3 else [uid],NativeUIDAllocated=False,PreviousFacts=previous.get(t),ClassicPlacementReason='retain18currentfirstteams'if level==1 else '9B/U23preservedwithparents;genericLower1301432/index550keepsoutofSecond+Thirdperiodplayoffs pendingproof'if level==5 else '11currentsecondsenior+7bestcurrentThirdseniorbycompleted25/26finalorder'if level==2 else '16remainingmodernThirdsenior;16moreeligibleFourth/explicitphysicallegacystandinsrequiredtocomplete2x16',ReserveNativeEligibility='UNKNOWN; do notreinterpret sourceclubtype2/3asNativeKind0'if t in reserves else 'seniorclubtype1'))
assert [sum(r['TargetNativeLevel']==l for r in assign)for l in[1,2,3,5]]==[18,18,16,9]
D=ROOT/'FmLauncher/data/research/GHIDRA_ENGINE_20261107_R5/decompiled/functions';inputs.extend([D/'ram_ee8350.c',D/'ram_ee8830.c',D/'ram_ee88e0.c',P/'club-profiles-Belgium.json',P/'club-identities-Belgium.json',P/'native-competition-requirements.json',engine,ROOT/'FmLauncher/data/research/COUNTRY_BATCH_CZE_CRO_CHN_CHI_BGR_BRA_20261113/native-prep/competition-catalog.json'])
dump(P/'belgium-previous-final-normalized.json',dict(Status='SOURCE_FINAL_PHASE_ORDER_NORMALIZED',Rows=list(previous.values()),FinalFFA=phasefacts,NoInProgress2026_27Performance=True,FinalPointSummation=False,CutoffInvariant='SelectedprevioussecondRWDM/Olympic; finalranks2Knokke/Mons;3Roeselare/Tubize;4BelisiaBilzen beats4Meux by officialfinalpoints/seasonmatches; nophasepointsum, noGDneeded.'))
dump(P/'source-cascade-Belgium-staged.json',dict(Status='WAIT_ROOT_BOUNDED_FOURTH_CATALOGUE_OR_EXPLICIT_PHYSICAL_STANDINS',SourceClubs=61,Assignments=assign,CurrentSources=[18,15,28],SourceTypes=dict(Senior=52,Reserve=9),ProjectedModern=[18,18,16,9],ClassicPlayingTarget=[18,18,32],UnfilledPlayableThird=16,ProtectedNativeFourthMinima={'6600088':15,'6600089':14,'6600090':14,'6600091':15},NativeWriterAllowed=False,SecondPromotions=[dict(TMID=r['TMID'],Name=r['Name'],Previous=previous[r['TMID']])for r in third[:7]],Parents=[r for r in ids.values()if r['ParentTMID']],RawSchedulerEvidence={'ee8350':'COMP2 ctor +0xb1=0/D6BC50(4); semantics notinferred','ee8830':'thirdregion ctor +0xb1=1/D6BC50(2); semantics notinferred','ee88e0':'2007sizecheckexpected16; no blanketmin==playingcountclaim'},ReservePolicy='9currentB/U23to verifiedgenericLowerCOMP1301432/index550, actualcountry+parents+nativeKindpreserved. No stockreserveplayingwitness inBelgium; avoid moving B intoThirdperiodplayoffs. NativeCurrent/ALT and pool eligibility separatebeforewrite.',RejectedFalseLead='COMP1301404/index525 isBelgianCup, NEVERlowerpool; noassignmentusesit',SourceSearchBudget='TMFourthsearchesnoresults;2RSSSFwholecountryhistorical/currentURLs unavailable. Rootownsoneboundedlookup; thisagentdoesnotrenewresearchbudget.',Inputs={str(f):sha(f)for f in inputs}))
dump(P/'belgium-staged-targets.json',assign);print('STAGED_BEL61',[sum(r['TargetNativeLevel']==l for r in assign)for l in[1,2,3,5]],'SOURCE_NOT_CLOSED;16Thirdslotsmissing');print('SECOND_PROMOTIONS',[(r['Name'],r['TMID'])for r in third[:7]])


