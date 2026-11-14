"""China country data adapter: reuse saved ranking and exact Current/ALT selector witness."""
from pathlib import Path
from fractions import Fraction
import json,ast,hashlib,datetime,sys,collections
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;P=B/'competition-prep';ROOT=B.parents[3]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not (B/'scope-closures/China.json').exists(),'No reset of closed country'
comps=[x for x in read(P/'source_competitions.json') if x['Country']=='China'];assert len(comps)==4
alltargets=read(P/'club-profiles-China.json');reg={str(x['TMID']):x for x in read(P/'club-identities-China.json')};assert len(reg)==56
previous={};inputs=[]
for c in comps:
 assert c['CurrentSeason']['name']=='2026' and c['CurrentSeason']['id']=='2025' and c['PreviousCompletedSeason']['name']=='2025'
 f=B/c['previous_completed_table_file'];tables=read(f)['tables'];assert len(tables)==1
 rows=tables[0]['rows'];assert len(rows)==(16 if c['RealLevel']<3 else 12) and all(r['matches']==(30 if c['RealLevel']<3 else 22) for r in rows)
 inputs.extend([f,B/c['current_clubs_file'],B/c['SeasonMetadataFile']])
 for r in rows:
  t=str(r['club_id']);assert t not in previous
  previous[t]=dict(TMID=t,Name=r['club_name'],PreviousCompetition=c['id'],PreviousLevel=c['RealLevel'],FinalPosition=r['position'],Matches=r['matches'],Wins=r['wins'],Draws=r['draws'],Losses=r['losses'],GoalsFor=r['goals_for'],GoalsAgainst=r['goals_against'],GoalDifference=r['goal_difference'],Points=r['points'],SourceFile=str(f.relative_to(B)),SourceSHA256=sha(f),TableContext='Completed2025top/second30matches or regional LeagueTwo phase22matches; NOT overall promotion-stage final')
engine=ROOT/'FmLauncher/data/research/COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/competition-prep/build_source_cascade_plan.py';tree=ast.parse(engine.read_text(encoding='utf-8-sig'));fn=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='ranking_key'];exec(compile(ast.Module(body=fn,type_ignores=[]),str(engine),'exec'),globals())
first=[x for x in alltargets if x['RealLevel']==1];second=[x for x in alltargets if x['RealLevel']==2];assert len(first)==len(second)==16
assert all(reg[x['TMID']]['SourceClubTypeID']==1 and reg[x['TMID']]['ParentTMID'] is None for x in first+second)
rank_gaps=[];lower=[];ranked={}
for code in ['CHL3','CL3S']:
 pool=[x for x in alltargets if x['SourceCompetition']==code and reg[x['TMID']]['SourceClubTypeID']==1 and reg[x['TMID']]['ParentTMID'] is None]
 rank_gaps.extend([dict(TMID=x['TMID'],Name=x['Name'],Reason='No saved completed2025 rank; not eligible as required ranked filler') for x in pool if x['TMID'] not in previous])
 pool=sorted([x for x in pool if x['TMID'] in previous],key=ranking_key);assert len(pool)>=4
 ranked[code]=[dict(TMID=x['TMID'],Name=x['Name'],Selected=i<4,Previous=previous[x['TMID']]) for i,x in enumerate(pool)];lower.extend(pool[:4])
# Geographic approximation for classic FM08 groups, independent of modern A/B names.
def geo(x):
 profile=read(B/x['ProfileFile']);stad=profile.get('stadium') or {};lat=stad.get('latitude');lon=stad.get('longitude')
 assert isinstance(lat,(float,int)) and isinstance(lon,(float,int)),('missing geographic evidence',x['TMID'])
 return dict(Latitude=lat,Longitude=lon,Address=stad.get('address_line_2'),ProfileFile=x['ProfileFile'],ProfileSHA256=sha(B/x['ProfileFile']))
geos={x['TMID']:geo(x) for x in lower};ordered=sorted(lower,key=lambda x:(-geos[x['TMID']]['Latitude'],str(x['TMID'])));north={x['TMID'] for x in ordered[:4]};south={x['TMID'] for x in ordered[4:]};cut=(geos[ordered[3]['TMID']]['Latitude']+geos[ordered[4]['TMID']]['Latitude'])/2
currenttop={x['TMID'] for x in sorted(first,key=ranking_key)[:15]};alttop={x['TMID'] for x in first}
currentsecond={x['TMID'] for x in sorted(second+[x for x in first if x['TMID'] not in currenttop],key=ranking_key)[:13]};altsecond={x['TMID'] for x in sorted(second,key=ranking_key)[:14]}
def division(x,top,sec):
 t=x['TMID']
 if t in top:return 195
 if t in sec:return 201
 if t in north:return 482
 if t in south:return 483
 g=geo(x);geos[t]=g;return 482 if g['Latitude']>=cut else 483
assign=[]
for x in first+second+lower:
 t=x['TMID'];r=reg[t];assert r['SourceCountryID']==34 and r['SourceClubTypeID']==1 and not r['ParentTMID'] and r['SourceRef']
 a=dict(x,ParentTMID=None,SourceClubTypeID=1,SourceCountryID=34,SourceScope='closed_country_China',ClubIdentityPending=False,SourceIdentityEvidence=r['SourceRef'],TargetNativeDivisionIndex=division(x,currenttop,currentsecond),TargetNativeAlternativeDivisionIndex=division(x,alttop,altsecond),NativeUIDAllocated=False,SourcePreviousRank=previous.get(t),ClassicPlacementReason='Exact native Current15/13 and EffectiveALT16/14; required lower minimum4/group; saved previous-rank cascade and profile latitude classic approximation')
 assign.append(a)
assert len(assign)==40
counts={bank:dict(collections.Counter(x[field] for x in assign)) for bank,field in [('Current','TargetNativeDivisionIndex'),('EffectiveALT','TargetNativeAlternativeDivisionIndex')]}
assert counts['Current'][195]==15 and counts['Current'][201]==13 and counts['EffectiveALT'][195]==16 and counts['EffectiveALT'][201]==14
assert all(counts[k].get(i,0)>=4 for k in counts for i in [482,483])
witness=P/'china-native-review/decision.json';assert sha(witness)=='52fa80409fde3648837bb0fafacb1a95c79f5e7875c50729f6b7ce88897edc67'
closed=B/'scope-closures/China-targets.json';dump(closed,assign)
inputs +=[engine,witness,P/'club-identities-China.json',P/'club-profiles-China.json',P/'native-competition-requirements.json']
guards=['Before nativewrite independently verify both simultaneous counterbanks15/13 and16/14; lastASMflag is bank not season','Country nonnull required; normalCOMP counters global, onlygeneric1301432 countryfiltered','Regional+64 increments independently; detect selected==regional instead of silently deduping','Inherited stage scheduler eligibility UNKNOWN, no selectorPASS to schedulerPASS','No UIDallocation or DBwrites authorized by this source scope']
dump(P/'source-cascade-China.json',dict(Status='CLOSED_SOURCE_COUNTRY_SCOPE_NOT_NATIVE_PREFLIGHT',SourceCounts=dict(Main32=32,RequiredFirstTeamFillers8=8,SourceRosterTargets40=40,MetadataOnlyUnselected16=16),PredictedSelectorPopulations=counts,RegionalMethod='Choose4previousrank eligible firstteams per currentprovider lowergroup, then split selected8 by descending verified stadiumlatitude4north/4south; other main spillovers use that median. FM08 geographic approximation, NOT modernrealgroup claim.',LatitudeBoundary=cut,GeographyEvidence=geos,RankedCandidates=ranked,RankGaps=rank_gaps,Assignments=assign,MandatoryBeforeNativeWrite=guards,Snapshot='2026-11-13',RawRequestSeason='2025',DisplayedCurrentSeason='2026',PreviousDisplayedSeason='2025'))
dump(B/'scope-closures/China.json',dict(Status='CLOSED_NATIVE_CASCADE_CLUB_IDENTITIES_AND_PARENTS',Country='China',Clubs=40,TargetsSHA256=sha(closed),SourceCollectionScopeApproved=True,AllParentsResolvedOrExplicitDeferred=True,PendingParentCount=0,NativeSchedulerEligibilityReviewed=False,NativeEligibilityStatus='SCHEDULER_INHERITED_GUARD_UNKNOWN_NOT_NATIVE_PASS',MandatoryBeforeNativeWrite=guards,SourceOnly=True,NativeUIDAllocated=False,DatabaseWritten=False,ClosedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),Inputs={str(p):sha(p) for p in inputs}))
old=read(B/'source-targets.json');assert not any(x['Country']=='China' for x in old);dump(B/'source-targets.json',old+assign)
print('CHINA_SOURCE_CLOSED40',counts,'main32+rankedlower8; no nativewrite',flush=True)
