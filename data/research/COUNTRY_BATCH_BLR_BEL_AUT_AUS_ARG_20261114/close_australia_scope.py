from pathlib import Path
from fractions import Fraction
import json,sys,hashlib,datetime,ast
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;P=B/'competition-prep';ROOT=B.parents[3]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
country='Australia';dest=B/'scope-closures/Australia.json';assert not dest.exists()
comps=[c for c in read(P/'source_competitions.json')if c['Country']==country];assert len(comps)==1
c=comps[0];prev=read(B/c['previous_completed_table_file']);rows=prev['tables'][0]['rows'];assert len(rows)==12 and all(r['matches']==26 for r in rows)
previous={r['club_id']:dict(PreviousLevel=1,FinalPosition=r['position'],Matches=r['matches'],Points=r['points'],GoalDifference=r['goal_difference'],Wins=r['wins'])for r in rows}
engine=ROOT/'FmLauncher/data/research/COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/competition-prep/build_source_cascade_plan.py'
tree=ast.parse(engine.read_text(encoding='utf-8-sig'));fn=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='ranking_key'];exec(compile(ast.Module(body=fn,type_ignores=[]),str(engine),'exec'),globals())
profiles=read(P/'club-profiles-Australia.json');ids={x['TMID']:x for x in read(P/'club-identities-Australia.json')};assert len(profiles)==12 and all(v['SourceRef']and v['SourceClubTypeID']==1 and not v['ParentTMID']for v in ids.values())
selected={r['TMID']for r in sorted(profiles,key=ranking_key)[:8]};lower={'6954':(130185,168),'970':(130189,172),'7831':(130186,169),'36100':(130185,168)};assert set(ids)-selected==set(lower)
assign=[]
for r in profiles:
 t=r['TMID'];i=ids[t];uid,index=(129985,157)if t in selected else lower[t]
 assert i['SourceCountryID']==(120 if t in ['118373','8445']else 12),(t,i['SourceCountryID'])
 q=dict(r,ParentTMID=None,SourceClubTypeID=1,SourceCountryID=i['SourceCountryID'],ClubIdentityPending=False,SourceScope='closed_country_Australia',SourceIdentityEvidence=i['SourceRef'],SourceIdentity='exact current26/27 club ID and raw firstteam metadata; foreign NZcountry retained',TargetNativeLevel=1 if t in selected else 2,TargetNativeCompetitionUID=uid,TargetNativeDivisionIndex=index,NativeUIDAllocated=False,ClassicPlacementReason='top8 by completed25/26 table'if t in selected else 'bottom4 by completed25/26 table to documented geographical native lowerpool',PreviousFacts=previous[t]);assign.append(q)
inputs=[P/'source_competitions.json',P/'club-identities-Australia.json',P/'club-profiles-Australia.json',P/'native-competition-requirements.json',B/c['previous_completed_table_file'],B/c['current_clubs_file'],engine]
ref=ROOT/'FmLauncher/data/research/COUNTRY_BATCH_CZE_CRO_CHN_CHI_BGR_BRA_20261113/native-prep/root-structure/native-structure-after.json';inputs.append(ref)
dump(P/'source-cascade-Australia.json',dict(Status='CLOSED_SOURCE_COUNTRY_SCOPE_NOT_NATIVE_PREFLIGHT',CurrentFirst=12,NativeFirst=8,Assignments=assign,NativeRequiredLowerPoolsPreserved=True,RequiredLowerMinima={'130186':3,'130185':6,'432083':1,'130188':7,'432090':1,'432091':1,'130187':3,'130189':3},NativeMandatoryTEAMRegistry='Keep all6D35150 identity registrations from R5; no deletion inferred',Policy='Never rank in-progress26/27; use final25/26 regularleague26matches official sporting table. NZ Auckland/Wellington retain NZcountry. No reserve imported as firstteam.',BeforeNativeWrite=['Full Current/effectiveALT/minmax and stockloader projection','Independently map oldphysical participants including defunct clubs without identity reuse','Preserve all8required regional pools and6selectorTEAMregistry identities','Runtime/SI/career/season acceptance separate']))
target=B/'scope-closures/Australia-targets.json';dump(target,assign)
dump(dest,dict(Status='CLOSED_NATIVE_CASCADE_CLUB_IDENTITIES_AND_PARENTS',Country=country,Clubs=len(assign),TargetsSHA256=sha(target),SourceCollectionScopeApproved=True,AllParentsResolvedOrExplicitDeferred=True,PendingParentCount=0,NativeSchedulerEligibilityReviewed=True,EligibilityQualification='R5A-League registered0/minexact8; all12current firstteams sourceclubtype1/parentless;8+4completed25/26cascade closed. Nativeprojection/runtime acceptance separate.',NativeUIDAllocated=False,DatabaseWritten=False,ClosedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),Inputs={str(f):sha(f)for f in inputs}))
old=read(B/'source-targets.json')if(B/'source-targets.json').exists()else[];assert not any(r['Country']==country for r in old);dump(B/'source-targets.json',old+assign);dump(B/'source-competitions.json',read(P/'source_competitions.json'));print('CLOSED',country,len(assign),sha(target))

