from pathlib import Path
import json,csv,hashlib,sys,statistics,ast,collections,subprocess
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');B=Path(__file__).resolve().parent;R=B.parent.parent;OLD=R/'COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep'
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'));import x7prep_rosters_20261110 as shared
from prepare_english_fc27 import scale_ca
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,v):(B/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Country offsets remain explicit project estimates, EA anchors are applied per identified player.
cal={'Czech Republic':-20,'Croatia':-20,'China':-30,'Chile':-20,'Bulgaria':-25,'Brazil':-10}
code=(OLD/'rating_model_v2.py').read_text(encoding='utf-8');node=next(n for n in ast.parse(code).body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='COUNTRY_ADJUSTMENT'for t in n.targets));before=ast.literal_eval(node.value);after=dict(before,**cal);lines=code.splitlines();lines[node.lineno-1]='COUNTRY_ADJUSTMENT='+repr(after);model='\n'.join(lines)+'\n';(B/'rating_model_v2.py').write_text(model,encoding='utf-8')
# Exact real DOB plus current source/full/common name; never use EA as proof of club or current transfer.
people=read(B/'person-identity-candidates.json');plans={x['TMID']:x for x in read(B/'club-plan.json')};ea=list(csv.DictReader((ROOT/'FMExt/data/fc27_players_all_2026_09_12.csv').open(encoding='utf-8-sig')));bydob=collections.defaultdict(list)
for e in ea:
 if e['gender']=="Men's Football":bydob[e['birthdate']].append(e)
matched=[]
for p in people:
 if p['PlayingClubTMID']not in plans:continue
 c=plans[p['PlayingClubTMID']];names=[p['Name'],p['SourceFullName']];hits=[e for e in bydob[p['RealDOB']]if any(shared.related(e['first_name']+' '+e['last_name'],n)or shared.norm(e.get('common_name',''))==shared.norm(n)for n in names if n)]
 if len({e['player_id']for e in hits})==1:
  e=hits[0];matched.append(dict(TMID=p['TMID'],Country=c['Country'],RealLevel=c['RealLevel'],RealDOB=p['RealDOB'],EAID=e['player_id'],Overall=int(e['overall_rating']),AnchorCA=scale_ca(int(e['overall_rating'])),IdentityBasis='exact real DOB + compatible full/common source name; one EA ID',NoMembershipInference=True))
summary=[]
for country in cal:
 values=[x['AnchorCA']for x in matched if x['Country']==country];summary.append(dict(Country=country,ExplicitEstimatedOffset=cal[country],MatchedEAProfiles=len(values),EAAnchorCAMedian=statistics.median(values)if values else None,EAAnchorCAMin=min(values)if values else None,EAAnchorCAMax=max(values)if values else None,CalibrationQualification='EA direct per-person anchors; sample is selective, national fallback offset remains an explicit estimate'))
dump('model-configuration.json',dict(ModelVersion='squad-spread-2026-27-v2',CountryCalibration=cal,CountryEASummary=summary,EAFileSHA256=sha(ROOT/'FMExt/data/fc27_players_all_2026_09_12.csv'),SourceModelSHA256=sha(OLD/'rating_model_v2.py'),ConfiguredModelSHA256=sha(B/'rating_model_v2.py'),StableRandomCAAndPA=True,PreserveCredibleAndPriorTalent=True,DateShift=19,NoGeneratorOrEngineChange=True));dump('EA-identity-rating-anchors.json',matched)
s=(OLD/'prepare_players.py').read_text(encoding='utf-8')
def rep(a,b):
 global s
 assert a in s,('missing checked seed anchor',a[:100]);s=s.replace(a,b)
rep("B/'root-structure/source-allocation/core-assignments.json'","B/'core-assignments.json'");rep('assert len(am)==602','assert len(am)==338')
rep("shared.PRIOR=[R/'COUNTRY_BATCH_IDN_IND_HKG_20261112/prepared'","shared.PRIOR=[R/'COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep/prepared',R/'COUNTRY_BATCH_IDN_IND_HKG_20261112/prepared'")
rep("for country in ['Netherlands','Spain','Greece','France','Finland','Denmark']:","for country in ['Czech Republic','Croatia','China','Chile','Bulgaria','Brazil']:")
rep("scope_id='ned-esp-gre-fra-fin-den-x18'","scope_id='cze-cro-chn-chi-bgr-bra-20261113'");rep('target_country_indices=[138,142,143,146,158,170,127]','target_country_indices=[137,135,55,190,134,189]')
rep("('Denmark',138)","('Denmark',138),('Czech Republic',137),('Croatia',135),('China',55),('Chile',190),('Bulgaria',134),('Brazil',189)")
# Source preflight resolved 32 memberships already; retain that exact choice rather than a second sorting rule.
rep("values.sort(key=lambda f:(not bool(f['Loan']),f['MembershipStatus']!='current_assignment_confirmed',plans[f['ClubTMID']]['RealLevel'],f['ClubTMID']))", "values.sort(key=lambda f:(f['ClubTMID']!=prechecked[tid]['PlayingClubTMID'],f['MembershipStatus']!='current_assignment_confirmed',plans[f['ClubTMID']]['RealLevel'],f['ClubTMID']))")
# Preserve all native people in the 6 physical stand-ins and explicit unresolved candidates.
rep("registry,protected=shared.registry();future=", "registry,protected=shared.registry();preserveclubs={u for x in read(B/'deferred-clubs.json')for u in x['PreserveNativeUIDs']}|{104982};preserveteams={x['TeamIndex']for x in read(B/'native-world-identities.json')if x['ClubUID']in preserveclubs};protected.update(int(n['ID'])for n in native if int(n['ClubIndex'])in preserveteams);future=")
# Inferred nationwide population is not a gate for partial rosters. Technical identity checks stay unchanged.
(B/'prepare_players.py').write_text(s,encoding='utf-8')
dump('prepared-csv-adapter-pins.json',dict(Status='CONFIGURED_AWAIT_ACTUAL_STRUCTURE_MAP_AND_FINAL_N4',Seed=str(OLD/'prepare_players.py'),SeedSHA256=sha(OLD/'prepare_players.py'),ConfiguredSHA256=sha(B/'prepare_players.py'),ModelSHA256=sha(B/'rating_model_v2.py'),Core=338,NoNativeWrite=True,NoNewBuild=True))
fut=B/'future-audit'
if not fut.exists():
 z=subprocess.run([str(B/'tools/AuditNativeFutureTransfers.exe'),str(B/'input/X19-after-SI'),str(fut),'2007-07-01'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600);(B/'future-audit.log').write_text(z.stdout+z.stderr,encoding='utf-8');assert z.returncode==0,z.stderr[-2000:]
print('CSV_SETUP_READY',summary,'futureaudit',fut.exists())
