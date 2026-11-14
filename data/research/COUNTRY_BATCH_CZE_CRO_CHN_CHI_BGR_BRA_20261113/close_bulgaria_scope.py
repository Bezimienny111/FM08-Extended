"""Bulgaria data config: saved finalrank cascade, source identities/parents, geographic14+14."""
from pathlib import Path
from fractions import Fraction
import json,hashlib,ast,datetime,sys,re,html,collections
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;P=B/'competition-prep';ROOT=B.parents[3];read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not(B/'scope-closures/Bulgaria.json').exists()
main=read(P/'club-profiles-Bulgaria.json');extra=read(P/'club-profiles-Bulgaria-supplement.json');reg={x['TMID']:x for x in read(P/'club-identities-Bulgaria.json')+read(P/'club-identities-Bulgaria-supplement.json')};assert len(main)==32 and len(extra)==12 and len(reg)==44
previous={};inputs=[]
for c in [c for c in read(P/'source_competitions.json') if c['Country']=='Bulgaria']:
 assert c['CurrentSeason']['name']=='26/27' and c['CurrentSeason']['id']=='2026' and c['PreviousCompletedSeason']['name']=='25/26'
 f=B/c['previous_completed_table_file'];tables=read(f)['tables']
 if c['id']=='BU1':assert [(t['name'],len(t['rows'])) for t in tables]==[('Champions Group',4),('Conference League Group',4),('Relegation group',8)]
 else:assert len(tables)==1 and len(tables[0]['rows'])==17 and all(r['matches']==32 for r in tables[0]['rows'])
 rankedrows=[];offset=0
 for table in tables:
  for row in table['rows']:rankedrows.append(dict(row,FinalPositionGlobal=offset+row['position'],FinalGroup=table['name']))
  offset+=len(table['rows'])
 assert len({r['club_id'] for r in rankedrows})==len(rankedrows)
 for r in rankedrows:
  previous[str(r['club_id'])]=dict(TMID=str(r['club_id']),Name=r['club_name'],PreviousLevel=c['RealLevel'],PreviousCompetition=c['id'],FinalPosition=r['FinalPositionGlobal'],RawGroupPosition=r['position'],RawFinalGroup=r['FinalGroup'],Matches=r['matches'],Wins=r['wins'],Draws=r['draws'],Losses=r['losses'],GoalDifference=r['goal_difference'],GoalsFor=r['goals_for'],GoalsAgainst=r['goals_against'],Points=r['points'],SourceFile=str(f.relative_to(B)),SourceSHA256=sha(f))
 inputs +=[f,B/c['current_clubs_file'],B/c['SeasonMetadataFile']]
for x in extra:
 if x['TMID'] in previous:assert previous[x['TMID']]['PreviousLevel']==2
 else:
  r=x['PreviousRow'];previous[x['TMID']]=dict(TMID=x['TMID'],Name=x['Name'],PreviousLevel=3,PreviousCompetition='BG-THIRD-'+r['RegionalGroup'],FinalPosition=r['Position'],Matches=r['Matches'],Wins=r['Wins'],Draws=r['Draws'],Losses=r['Losses'],GoalsFor=r['GoalsFor'],GoalsAgainst=r['GoalsAgainst'],GoalDifference=r['GoalsFor']-r['GoalsAgainst'],Points=r['Points'],SourceFile='competition-prep/sources/supplemental/bulgaria-previous-third.html',SourceSHA256=sha(P/'sources/supplemental/bulgaria-previous-third.html'))
engine=ROOT/'FmLauncher/data/research/COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/competition-prep/build_source_cascade_plan.py';tree=ast.parse(engine.read_text(encoding='utf-8-sig'));exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='ranking_key'],type_ignores=[]),str(engine),'exec'),globals())
first=[x for x in main if x['RealLevel']==1];second=[x for x in main if x['RealLevel']==2];assert len(first)==14 and len(second)==18
eligible=[x for x in second if not reg[x['TMID']]['ParentTMID'] and x['TMID'] in previous];ordered=sorted(eligible,key=ranking_key);promoted={x['TMID'] for x in ordered[:2]};assert len(promoted)==2
low=[x for x in second if x['TMID'] not in promoted]+extra;assert len(low)==28
geos={}
for x in low:
 profile=read(B/x['ProfileFile']);st=profile.get('stadium') or {};lat=st.get('latitude');lon=st.get('longitude');assert isinstance(lat,(int,float)) and isinstance(lon,(int,float)),('missing geographic evidence',x['TMID'])
 geos[x['TMID']]=dict(Latitude=lat,Longitude=lon,ProfileFile=x['ProfileFile'],ProfileSHA256=sha(B/x['ProfileFile']),Address=st.get('address_line_2'))
geoorder=sorted(low,key=lambda x:(-geos[x['TMID']]['Longitude'],x['TMID']));east={x['TMID'] for x in geoorder[:14]};west={x['TMID'] for x in geoorder[14:]}
# Current regional membership and exact provider identities are sourcefacts; historical native reuse remains separate.
raw=P/'sources/supplemental/bulgaria-current-third.html';text=raw.read_text(encoding='utf-8');links={html.unescape(re.sub('<[^>]+>','',label)).strip():html.unescape(url) for url,label in re.findall(r'<a[^>]+href=[\"\']([^\"\']+)[\"\'][^>]*>(.*?)</a>',text,re.S|re.I)}
assign=[];parents=[]
for x in main+extra:
 t=x['TMID'];r=reg[t];assert r['SourceCountryID']==28 and r['SourceRef'];level=1 if x['RealLevel']==1 or t in promoted else 2;parent=r['ParentTMID']
 if parent:
  assert level==2 and any(y['TMID']==parent for y in first);parents.append(dict(TMID=t,ParentTMID=parent,ParentTier=1,ChildTier=2))
 assert r['SourceClubTypeID']==(2 if parent else 1)
 division=804 if level==1 else 854 if t in east else 855;uid=7500000 if level==1 else 7509144 if t in east else 7509145
 a=dict(x,ParentTMID=parent,SourceClubTypeID=r['SourceClubTypeID'],SourceCountryID=28,SourceScope='closed_country_Bulgaria',ClubIdentityPending=False,SourceIdentityEvidence=r['SourceRef'],TargetNativeLevel=level,TargetNativeDivisionIndex=division,TargetNativeCompetitionUID=uid,SourcePreviousRank=previous.get(t),NativeUIDAllocated=False,ClassicPlacementReason='Modern14+18 ->classicTop16 andB2x14; sourcepreviousrank cascading,12real eligible lowerfillers; classicEast/West approximation sortedprofilelongitude')
 if x in extra:a['NationalSourceEntityURL']=links.get(x['SourceLocalName']);a['SourceCurrentRegionalTableSHA256']=sha(raw);assert a['NationalSourceEntityURL']
 assign.append(a)
assert collections.Counter(x['TargetNativeDivisionIndex'] for x in assign)=={804:16,854:14,855:14} and len(parents)==2
warnings=[dict(TMID=t,Scope='NATIVE_HISTORICAL_REUSE_NOT_AUTHORIZED',Reason=reason) for t,reason in [('19214','currentLokomotivMezdra2012 vs rawofficialno2012; do not reuse vanishedhistoricalentity bynamealone'),('760','officialregionalcurrentNeftochimic1962 vs rawofficialNeftochimic1986; sportscontinuity/nativehistoricalreuse requires boundedreview'),('26535','currentVolovShumen2007 vs rawofficialFCVolov; preserve currentphysicalTMentity, no automatic historicalidentity claim')]]
guards=['Verify actualnativekind/schedulerparenttier for CSKAII andLudogoretsII; sourceparentsclosed but no nativeeligibilityPASS','HistoricalnativeUIDreuse for renamed/revived currententities requires explicitcontinuityproof; sourceTMIDs do not allocate/reuse UID','ClassicEast/West14+14 basedcurrentprofilelongitude is approximateFM08grouping, not contemporaryrealgroupclaim','Futurepreflight reconcile lowerpools,ALT/regional/rawcurrent bothforms independently']
closed=B/'scope-closures/Bulgaria-targets.json';dump(closed,assign)
dump(P/'source-cascade-Bulgaria.json',dict(Status='CLOSED_SOURCE_COUNTRY_SCOPE_NOT_NATIVE_PREFLIGHT',SourceCounts=dict(Main32=32,RequiredLower12=12,Total44=44),ClassicCounts={'Top16':16,'EasternB14':14,'WesternB14':14},PromotedBySavedPreviousRank=[dict(TMID=x['TMID'],Name=x['Name'],Previous=previous[x['TMID']]) for x in ordered[:2]],RequiredFillersRanked=sorted([dict(TMID=x['TMID'],Name=x['Name'],Previous=previous[x['TMID']]) for x in extra],key=lambda x:(x['Previous']['PreviousLevel'],x['Previous']['FinalPosition'],-x['Previous']['Points']/x['Previous']['Matches'])),RegionalMethod='Descendingverifiedstadiumlongitude first14East, remaining14West; stableTMIDonlytie; geographicFM08approximation',GeographyEvidence=geos,ParentGuards=parents,EarlyNativeIdentityExceptions=warnings,RankGaps=[dict(TMID=x['TMID'],Name=x['Name']) for x in main if x['TMID'] not in previous],Assignments=assign,MandatoryBeforeNativeWrite=guards))
inputs +=[raw,P/'sources/supplemental/bulgaria-previous-third.html',P/'club-identities-Bulgaria.json',P/'club-identities-Bulgaria-supplement.json',P/'bulgaria-third-tables-normalized.json',engine]
dump(B/'scope-closures/Bulgaria.json',dict(Status='CLOSED_NATIVE_CASCADE_CLUB_IDENTITIES_AND_PARENTS',Country='Bulgaria',Clubs=44,TargetsSHA256=sha(closed),SourceCollectionScopeApproved=True,AllParentsResolvedOrExplicitDeferred=True,PendingParentCount=0,NativeSchedulerEligibilityReviewed=False,NativeEligibilityStatus='INHERITED_SCHEDULER_PARENTGUARD_UNKNOWN_NOT_NATIVE_PASS',HistoricalNativeIdentityExceptions=warnings,MandatoryBeforeNativeWrite=guards,NativeUIDAllocated=False,DatabaseWritten=False,ClosedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),Inputs={str(p):sha(p) for p in inputs}))
old=read(B/'source-targets.json');assert not any(x['Country']=='Bulgaria' for x in old);dump(B/'source-targets.json',old+assign);print('BULGARIA_CLOSED44',sorted(promoted),'nativeprediction16/14/14;sourceonly')
