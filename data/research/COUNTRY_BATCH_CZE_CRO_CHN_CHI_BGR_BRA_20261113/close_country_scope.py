"""Country data adapter reusing the closed cascade ranking; no native UID allocation or DB writes."""
from pathlib import Path
from fractions import Fraction
import json,hashlib,datetime,ast,sys
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;P=B/'competition-prep';ROOT=B.parents[3]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
country=sys.argv[1];assert country=='Chile','Only reviewed country configuration is currently provided'
slug=country.replace(' ','-');dest=B/'scope-closures'/(slug+'.json');assert not dest.exists(),'Country scope is immutable after closure; later gaps use explicit delta'
comps=[x for x in read(P/'source_competitions.json') if x['Country']==country and x['RealLevel']<=2]
assert len(comps)==2 and all(x['CurrentSeason']['name']=='2026' and x['PreviousCompletedSeason']['name']=='2025' for x in comps)
targets=read(P/('club-profiles-'+slug+'.json'));reg={str(x['TMID']):x for x in read(P/('club-identities-'+slug+'.json'))};assert len(targets)==len(reg)==32
assert all(x['SourceClubTypeID']==1 and x['SourceCountryID']==33 and x['ParentTMID'] is None and x['SourceRef'] for x in reg.values())
previous={};inputs=[]
for c in [x for x in read(P/'source_competitions.json') if x['Country']==country]:
 file=B/c['previous_completed_table_file'];table=read(file);tables=table['tables'];assert len(tables)==1
 if c['RealLevel']<=2:
  assert len(tables[0]['rows'])==16 and all(r['matches']==30 for r in tables[0]['rows']),'Use completed league table only, no current in-progress table'
 else:
  assert len(tables[0]['rows'])==14 and sum(r['matches']>0 for r in tables[0]['rows'])==13
  assert all(r['matches'] in [0,24] for r in tables[0]['rows']),'Previous third:13active clubs double roundrobin24, onezero-match entry'
 inputs.extend([file,B/c['CurrentCatalogueFile']] if c.get('CurrentCatalogueFile') else [file,B/c['current_clubs_file']])
 for r in tables[0]['rows']:
  tid=str(r['club_id']);assert tid not in previous
  previous[tid]=dict(TMID=tid,Name=r['club_name'],PreviousCompetition=c['id'],PreviousLevel=c['RealLevel'],FinalPosition=r['position'],Matches=r['matches'],Wins=r['wins'],Draws=r['draws'],Losses=r['losses'],GoalsFor=r['goals_for'],GoalsAgainst=r['goals_against'],GoalDifference=r['goal_difference'],Points=r['points'],SourceFile=str(file.relative_to(B)),SourceSHA256=sha(file),Season=c['PreviousCompletedSeason'])
engine=ROOT/'FmLauncher/data/research/COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/competition-prep/build_source_cascade_plan.py'
tree=ast.parse(engine.read_text(encoding='utf-8-sig'));functions=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='ranking_key'];assert len(functions)==1;exec(compile(ast.Module(body=functions,type_ignores=[]),str(engine),'exec'),globals())
top=[x for x in targets if x['RealLevel']==1];second=[x for x in targets if x['RealLevel']==2];assert len(top)==len(second)==16
ordered=sorted(second,key=ranking_key);chosen={str(x['TMID']) for x in ordered[:4]};assert all(str(x['TMID']) in previous for x in second);assert all(previous[t]['PreviousLevel']<=2 for t in chosen)
assign=[]
for c in targets:
 tid=str(c['TMID']);tier=1 if c['RealLevel']==1 or tid in chosen else 2;c=dict(c,ParentTMID=None,SourceClubTypeID=1,SourceCountryID=33,SourceScope='closed_country_Chile',ClubIdentityPending=False,SourceIdentity='current authoritative2026catalogue + exactTMID/rawprofile parentless firstteam/Chile',TargetNativeLevel=tier,TargetNativeCompetitionUID=5250792 if tier==1 else 5250793,TargetNativeDivisionIndex=590 if tier==1 else 591,NativeUIDAllocated=False)
 c['SourceIdentityEvidence']=reg[tid]['SourceRef'];c['ClassicPlacementReason']='retain current first division' if c['RealLevel']==1 else 'best saved2025 previous-rank eligible lowerclub to complete classicTop20' if tid in chosen else 'remaining currentsecond to classicFirstB12'
 assign.append(c)
assert sum(c['TargetNativeLevel']==1 for c in assign)==20 and sum(c['TargetNativeLevel']==2 for c in assign)==12
ranked=[dict(TMID=x['TMID'],Name=x['Name'],Selected=x['TMID'] in chosen,Previous=previous[x['TMID']]) for x in ordered]
dump(P/'source-cascade-Chile.json',dict(Status='CLOSED_SOURCE_COUNTRY_SCOPE_NOT_NATIVE_PREFLIGHT',CurrentFirst=16,CurrentSecond=16,NativeFirst=20,NativeFirstB=12,PromotedBySavedPreviousRank=ranked,Assignments=assign,NoReserveOrForeignExceptions=True,LowerPool='Existing nativeThird minimum16/stock43 preserved for future nativepreflight; not a current updated-source league claim',StageSchedulerQualification='Preserve registered CHI_FIRST/CHI_FIRST_B classic template; source population uses only first-team clubtype1, no parent/reserve eligibility conflict. Static registration/minimum does not claim runtime acceptance.'))
closed=B/'scope-closures'/(slug+'-targets.json');dump(closed,assign)
for f in [P/'native-competition-requirements.json',P/('club-profiles-'+slug+'.json'),P/('club-identities-'+slug+'.json'),engine]:inputs.append(f)
D=ROOT/'FmLauncher/data/research/GHIDRA_ENGINE_20261107_R5/decompiled/functions'
inputs.extend([D/'ram_e558a0.c',D/'ram_e55a00.c'])
gate=dict(Status='CLOSED_NATIVE_CASCADE_CLUB_IDENTITIES_AND_PARENTS',Country=country,Clubs=32,TargetsSHA256=sha(closed),NativeSchedulerEligibilityReviewed=True,EligibilityQualification='All32 firstteams sourceclubtype1/country33/parentless; registered2levels20/12 and previousfinal cascade closed. No unknown reserve kind imported as firstteam. Runtime/nativewrite preflight is separate.',AllParentsResolvedOrExplicitDeferred=True,PendingParentCount=0,NativeUIDAllocated=False,DatabaseWritten=False,ClosedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),Inputs={str(p):sha(p) for p in inputs})
dump(dest,gate)
old=read(B/'source-targets.json') if (B/'source-targets.json').exists() else [];assert not any(c['Country']==country for c in old),'No reset/refetch of closed country'
dump(B/'source-targets.json',old+assign);dump(B/'source-competitions.json',read(P/'source_competitions.json'))
print('CLOSED_COUNTRY',country,'clubs32,Top20/FirstB12,parents0; rankedpromotions',sorted(chosen),flush=True)
