from pathlib import Path
from collections import Counter
import json,csv,hashlib,subprocess,sys
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent;S=B.parent;R=S.parent;OLD=R/'COUNTRY_BATCH_IDN_IND_HKG_20261112'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
core={x['TMID']:x for x in rows(B/'club-map.csv')};world={int(x['ClubUID']):x for x in read(B/'native-world-identities.json')};aliases=[]
for a0 in read(B/'foreign-owner-aliases-draft.json'):
 a=dict(a0);main=a['CanonicalMainTMID']
 if main in core:a.update(Decision='within_core_projected_verified_identity',NativeClubUID=int(core[main]['ClubUID']))
 elif main=='12275':a.update(Decision='defer_excluded_Kolding_typed_role',NativeClubUID=None)
 elif a.get('NativeClubUID'):
  w=world[int(a['NativeClubUID'])];assert not w['ParentUID']and w['TeamCountry']==a['NativeCountryIndex']
 else:a.update(Decision='defer_unresolved_external_owner_no_forced_research',NativeClubUID=None)
 aliases.append(a)
dump(B/'foreign-owner-aliases.json',aliases);dump(B/'foreign-owner-finalization.json',dict(SourceOwners=len(aliases),Decisions=dict(Counter(a['Decision']for a in aliases)),deferred_source_owners=[a['SourceTMID']for a in aliases if a['Decision'].startswith('defer')],NewFamilies=0,NewRequests=0))
# Reuse unchanged v2 algorithm, explicit country/lowertier calibration data only.
model=(OLD/'rating_model_v2.py').read_text(encoding='utf-8');model=model.replace('"Indonesia":-40,','"Netherlands":-5,"Spain":0,"Greece":-15,"France":0,"Finland":-25,"Denmark":-15,"Indonesia":-40,');model=model.replace('5:(40,88)}','5:(40,88),6:(30,75)}');(B/'rating_model_v2.py').write_text(model,encoding='utf-8')
dump(B/'model-configuration.json',dict(ModelVersion='squad-spread-2026-27-v2',CountryCalibration={'Netherlands':-5,'Spain':0,'Greece':-15,'France':0,'Finland':-25,'Denmark':-15},RealLevel6AdultCA=[30,75],PreserveCredibleAndPriorTalent=True,DateShift=19,AlreadyShiftedDatePreserved=True,NoGeneratorOrEngineChange=True))
fut=B/'future-audit'
if not fut.exists():
 z=subprocess.run([str(B/'tools/AuditNativeFutureTransfers.exe'),str(B/'input/X17-after-SI'),str(fut),'2007-07-01'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600);(B/'future-audit.log').write_text(z.stdout+z.stderr,encoding='utf-8');assert z.returncode==0,z.stderr[-1500:]
print('OWNER_FINAL',dict(Counter(a['Decision']for a in aliases)),'FUTURE_AUDIT_READY',flush=True)
code=(OLD/'prepare_players.py').read_text(encoding='utf-8')
def replace(old,new):
 global code
 assert old in code,('missing shared adapter anchor',old[:100]);code=code.replace(old,new)
replace('SRC=B;P=', 'SRC=B.parent;P=')
replace("REF='2026-11-12'", "REF='2026-11-13'")
replace("'B1L4':4", "'B1L4':4,'B1L5':5,'B1L6':6")
replace(" cm=rows(B/'club-map.csv');core=", " cm=rows(B/'club-map.csv');alloc=read(B/'root-structure/source-allocation/core-assignments.json');alloc=alloc.get('Assignments',alloc.get('assignments',[]))if isinstance(alloc,dict)else alloc;am={str(a.get('TMID',a.get('SourceTMID'))):a for a in alloc};assert len(am)==602;\n for c in cm:\n  assert c['TMID']in am and am[c['TMID']]['DesiredDivision']is not None;c['DivisionIndex']=str(am[c['TMID']]['DesiredDivision']);c['Group']=c['Country']+' '+c['DivisionIndex']\n core=")
replace("shared.PRIOR=[R/'COUNTRY_BATCH_KOR_COL_ISR_20261112", "shared.PRIOR=[R/'COUNTRY_BATCH_IDN_IND_HKG_20261112/prepared',R/'COUNTRY_BATCH_KOR_COL_ISR_20261112")
replace("('Indonesia',58)","('Indonesia',58),('Netherlands',158),('Spain',170),('Greece',146),('France',143),('Finland',142),('Denmark',138)")
replace(" groups=defaultdict(list)\n", " prechecked={v['TMID']:v for v in read(B/'person-identity-candidates.json')};pre_source_deferred=[]\n groups=defaultdict(list)\n")
replace("if f['AcceptedFactCandidate']:groups[f['TMID']].append(f)","if f['AcceptedFactCandidate']and f['ClubTMID']in core:groups[f['TMID']].append(f)")
start=code.index("   reg=[v for v in registry.get(tid,[])");end=code.index("   uid=int(existing['ID'])if existing else -1",start)
code=code[:start]+'''   checked=prechecked[tid];possible=[byuid[int(n['ID'])]for n in checked['NativeCandidates']];reg=checked['PriorEvidence'];reguids={v['uid']for v in reg};existing=None
   assert checked['PlayingClubTMID']==f['ClubTMID'] and checked['RealDOB']==real,('closed membership drift',tid)
   if checked['Decision'].startswith('defer'):raise ValueError(checked['Decision'])
   if checked['ExistingUID']:existing=byuid[int(checked['ExistingUID'])]
'''+code[end:]
replace(" entries=[];idents=[];loans=[];deferred=[];used=set();gapuids=set();ownerentities={};reusedregistry=[];oldproposals=[]", " entries=[];idents=[];loans=[];deferred=[];used=set();gapuids=set();ownerentities={};reusedregistry=[];oldproposals=[]\n for checked in prechecked.values():\n  if checked['PlayingClubTMID']not in core:\n   uids=[int(n['ID'])for n in checked['NativeCandidates']];gapuids.update(uids);deferred.append(dict(TMID=checked['TMID'],Name=checked['Name'],Club=checked['PlayingClubTMID'],Reason='excluded_club_identity_or_role_deferred',NativeUIDsProtected=uids))")
replace("for country in ['Indonesia','India','Hong Kong']:","for country in ['Netherlands','Spain','Greece','France','Finland','Denmark']:")
replace("for level in [1,2,3,4]:", "for level in [1,2,3,4,5,6]:")
replace("source_version='TM_snapshot_2026_11_12_season_resolved_by_name'", "source_version='TM_snapshot_2026_11_13_season_resolved_by_name'")
replace("scope_id='idn-ind-hkg-x17'", "scope_id='ned-esp-gre-fra-fin-den-x18'")
replace("target_country_indices=[58,57,56]", "target_country_indices=[138,142,143,146,158,170,127]")
# Existing type2 evidence source pins remain authoritative; no re-read of9661 or new identity guesses.
replace("personality_codec_requires_reviewed_rebuild=True", "personality_codec='verified_X17_no_full_rebuild'")
# Real six-country model data now; no C# build triggered by CSV preparation.
(B/'prepare_players.py').write_text(code,encoding='utf-8')
dump(B/'player-preparation-adapter-pins.json',dict(Seed=str(OLD/'prepare_players.py'),SeedSHA256=hashlib.sha256((OLD/'prepare_players.py').read_bytes()).hexdigest(),ConfiguredSHA256=hashlib.sha256(code.encode()).hexdigest(),ModelSHA256=hashlib.sha256((B/'rating_model_v2.py').read_bytes()).hexdigest(),NoNativeWrite=True))
print('PLAYER_ADAPTER_CONFIGURED',flush=True)