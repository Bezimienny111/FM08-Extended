from pathlib import Path
from collections import defaultdict
from datetime import datetime,timezone
import csv,json,hashlib,statistics,sys
sys.dont_write_bytecode=True
sys.path.insert(0,'J:/FM08dev/FM08-Database-Tools/scratch')
from create_club_stadium_native_n1_20261108 import load
B=Path(__file__).resolve().parent;P=B/'prepared'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pins(p):return {str(f.relative_to(p)):sha(f) for f in sorted(p.rglob('*')) if f.is_file()}
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def save(p,v):
 with p.open('w',encoding='utf-8-sig',newline='')as f:w=csv.DictWriter(f,fieldnames=list(v[0]));w.writeheader();w.writerows(v)
m=read(P/'manifest.json');full=read(P/'full-native.json');verified=read(P/'independent-verification.json');rating=read(B/'ratings-patch-independent.json');qa=read(B/'independent-selection-qa-r2/regression.json')
assert full['status']==verified['status']==rating['status']=='pass'
assert qa['Status']=='NUMERIC_SELECTION_REGRESSION_PASS' and len(qa['Checks'])==233 and not qa['NewRegressions'] and not qa['CurrentBatchFailures']
source=Path(m['source']);output=Path(rating['output']);assert Path(full['output'])==Path(rating['source'])
assert pins(source)==full['source_hashes'] and pins(output)==rating['output_hashes']
audit={int(r['ID']):r for r in rows(B/'ratings-audit-after/players.csv')}
ps=rows(P/'native_players.csv');ids=rows(P/'identities.csv');proof=read(P/'provenance.json');subjects={int(r['id90']):r for r in full['subjects']};clubs={r['TeamIndex']:r for r in rows(P/'club_map.csv')};ledger=[];talents=[]
assert len(ps)==len(ids)==len(proof)==len(subjects)==m['counts']['prepared']==3555
sentinel={int(r['UID']):r for r in verified['sentinel_name_source_after_proofs']}
for p,i,v in zip(ps,ids,proof):
 u=subjects[int(i['SubjectID'])]['uid'];a=audit[u]
 assert (int(a['CA']),int(a['PA']))==(int(p['CA']),int(p['PA'])),('final_CA_PA',u)
 assert a['BirthDate']==i['TargetDOB'] and int(a['ClubIndex'])==int(i['OwnerClubIndex']),('final_DOB_owner',u)
 c=clubs[i['PlayingClubIndex']];first=p['FirstName'];last=p['LastName']
 if u in sentinel:
  n=sentinel[u];assert n['NameBlockUnchanged'] and n['SourceName']==v['name'] and str(n['TMID'])==v['TMID']
  first=n['PhysicalFirstName'];last=n['PhysicalLastName']
 record=dict(TMID=v['TMID'],UID=u,SubjectID=i['SubjectID'],FirstName=first,LastName=last,SourceName=v['name'],ClubUID=int(c['ClubUID']),Club=c['ClubName'],Country=c['Country'],RealDOB=v['source_dob'],NativeDOB=i['TargetDOB'],PlayingTEAM=int(i['PlayingClubIndex']),OwnerTEAM=int(i['OwnerClubIndex']),New=int(i['ExistingID'])<0,CA=int(a['CA']),PA=int(a['PA']),ModelVersion=v['model_version'],SeedUID=v['seed_uid'],AbilitySource=v['ability_source'],TalentAward=bool(v.get('talent_estimate')),Source=v['bio_source'])
 ledger.append(record)
 if record['TalentAward']:talents.append(record)
assert len({r['UID']for r in ledger})==len(ledger)==len({r['TMID']for r in ledger})
assert sum(r['New']for r in ledger)==m['counts']['new'] and len(read(P/'deferred.json'))==m['counts']['deferred']
save(B/'final-native-player-UID-ledger.csv',ledger);dump(B/'talent-native-UID-ledger.json',talents)
summary=[]
for country in ['Indonesia','India','Hong Kong']:
 rs=[r for r in ledger if r['Country']==country];ca=[r['CA']for r in rs];pa=[r['PA']for r in rs]
 summary.append(dict(Country=country,Clubs=sum(c['Country']==country for c in clubs.values()),Players=len(rs),New=sum(r['New']for r in rs),CAmin=min(ca),CAmax=max(ca),CAmean=round(statistics.mean(ca),2),CAstd=round(statistics.pstdev(ca),2),DistinctCA=len(set(ca)),PAmin=min(pa),PAmax=max(pa),MeanDevelopmentGap=round(statistics.mean(y-x for x,y in zip(ca,pa)),2)))
save(B/'final-coverage-ratings.csv',summary)
structure=read(B/'structure-root-r2/root-independent-verification.json');assert structure['status']=='PASS_PRIVATE_NATIVE_STRUCTURE_NOT_SI_OR_RUNTIME' and len(structure['both_forms'])==18 and all(r['passed']for r in structure['both_forms'])
sr=read(B/'structure-root-r2/structure-report.json');venuegaps=len(sr['venue_gaps']);assert venuegaps==69
freeze=read(B/'source-freeze.json');assert pins(Path(freeze['frozen']))==freeze['hashes'] and pins(Path(freeze['source']))==freeze['hashes']
negative=read(B/'negative-tests.json');assert len(negative)==6 and all(v['rejected']for v in negative)
pilot=read(Path(m['pilot_verification_path']));assert pilot['status']=='pass' and sha(Path(m['pilot_verification_path']))==m['pilot_verification_sha256']
# Unsupported old release is not an imported subject; preserve its complete physical record.
legacy=read(B/'legacy-format-preserve23042954.json');lr=legacy['preflight']['failures'][0];uid=lr['uid'];assert uid==23042954 and uid not in {r['UID']for r in ledger}
old=load(Path(freeze['frozen']),'people_db.dat');finalpeople=load(output,'people_db.dat');span=old[lr['source_start']:lr['source_end']];assert len(span)==284 and finalpeople.count(span)==1
legacyproof=dict(UID=uid,Length=284,WholeRecordSHA256=hashlib.sha256(span).hexdigest(),WholeRecordIdentical=True,ImportedParticipant=False)
meta=dict(people=len(ledger),prepared=len(ledger),new=sum(r['New']for r in ledger),reused=sum(not r['New']for r in ledger),reuse=sum(not r['New']for r in ledger),loans=len(rows(P/'loans.csv')),clubs=len(clubs),actor_clubs=m['counts']['actor_clubs'],legacy_rating_repairs=rating['scoped_UIDs'],legacy_CA_changed=rating['CA_changed'],legacy_PA_changed=rating['PA_changed'],new_talent_awards=len(talents),deferred=len(read(P/'deferred.json')),source_gaps=len(read(P/'source-gaps.json')),source_collection_gaps=184,source_cards=3787,source_candidates=3603,source_loans=103,new_clubs=60,new_stadiums=97,venue_gaps=venuegaps,project_families_SugarDaddy_OFF=522)
assert meta['people']==3555 and meta['loans']==101 and meta['legacy_rating_repairs']==408 and meta['source_gaps']==232
readback=dict(status='pass',rated_output=str(output),rated_hashes=pins(output),prepared_manifest_sha256=sha(P/'manifest.json'),prepared_players_sha256=sha(P/'native_players.csv'),prepared_identities_sha256=sha(P/'identities.csv'),prepared_loans_sha256=sha(P/'loans.csv'),source_freeze_sha256=sha(B/'source-freeze.json'),roster_inverse_sha256=sha(P/'independent-verification.json'),ratings_inverse_sha256=sha(B/'ratings-patch-independent.json'),selection_qa_sha256=sha(B/'independent-selection-qa-r2/regression.json'),ledger_sha256=sha(B/'final-native-player-UID-ledger.csv'),all_imported_CA_PA_DOB_owner_verified=True,UID_and_TMID_unique=True,frozen_X16_hashes_unchanged=True,legacy_unsupported_record_preserved=legacyproof,sentinel_names_source_after_verified=verified['sentinel_name_source_after_proofs'],counts=meta,recorded_at=datetime.now(timezone.utc).isoformat())
dump(B/'final-readback.json',readback)
carry=read(Path(freeze['frozen'])/'next-batch-fixes.json')
dump(B/'next-batch-fixes.json',dict(inherited_unresolved=carry,current_deferred_profiles=read(P/'deferred.json'),source_gaps=read(P/'source-gaps.json'),legacy_unsupported_preserved=legacyproof,reader_backlog='ReadPlayers missing-firstname heuristic may display fabricated fallback labels; actual NAMEIDs/strings/known-as preserved and source-proven. No editor rebuild or PERSON identity change.',venue_gaps=venuegaps,partial_club_rosters=[r for r in read(P/'coverage.json')if r['Confirmed']==0]))
status=dict(status='PRIVATE_NATIVE_VERIFIED_READY_FOR_ROOT_PUBLICATION_REVIEW',private_output=str(output),planned_public_output='J:/FM08dev/Dane/db/TEST_X17',source=str(source),source_X16_accepted_SI=True,source_X16_accepted_new_career=True,source_X16_season='NOT_CONFIRMED',counts=meta,native=True,SI=False,new_career=False,season=False,source_hashes=pins(source),output_hashes=pins(output),structure=structure,global_selection_qa=dict(status=qa['Status'],conditions=len(qa['Checks']),new_regressions=len(qa['NewRegressions']),new_country_null=len(qa['NewCountryNullTeams']),runtime_test=False),root_selection_qa_path=str(B/'independent-selection-qa-r2/regression.json'),final_readback=str(B/'final-readback.json'),final_ledger=str(B/'final-native-player-UID-ledger.csv'),metadata='Verified private DAT; root replaces inherited X16 XML and metadata when publishing X17.',public_database_mutated=False,EXE_modified=False,recorded_at=datetime.now(timezone.utc).isoformat())
dump(B/'native-ready-for-root-review.json',status)
manifest=read(B/'manifest.json');manifest.update(status=status['status'],current_native_stage=status);dump(B/'manifest.json',manifest)
text='# TEST_X17 - Indonesia, India, Hong Kong\n\nNative PASS; SI, new career and season PENDING. Accepted frozen X16 preserved.\n\n'+json.dumps(meta,ensure_ascii=False,indent=2)+'\n\nClassic format: Indonesia Premier2x18 / First4x10, IndiaNFL10, HongKongFirst10. Source/current squads and completed previous seasons pinned in competition-prep. No EXE or native-rule change.\n\nWhole PEOPLE/SERVER/CLIENT inverse and protected data PASS, 233 selector conditions PASS, 408 proven CA/PA repairs have full inverse and unchanged attribute/personality tables. Confirmed loans include international owners; no mandatory buys or invented dates. Missing profiles remain explicit gaps.\n\nUID23042954 unsupported legacy release preserved as entire284B record. Hariono UID41001663 physical NAME sentinel/source identity verified; misleading generic reader fallback not accepted as a true name. Ledger uses proven source names.\n\nRoot publishes TEST_X17/ZIP after review; private metadata is inherited and must be replaced.\n'
(B/'RAPORT.md').write_text(text,encoding='utf-8');(B/'WZNOWIENIE.md').write_text(text,encoding='utf-8')
artifacts=[B/'RAPORT.md',B/'WZNOWIENIE.md',B/'native-ready-for-root-review.json',B/'final-readback.json',B/'final-native-player-UID-ledger.csv',B/'talent-native-UID-ledger.json',B/'next-batch-fixes.json',P/'manifest.json',P/'independent-verification.json',P/'sentinel-name-source-after.json',B/'ratings-patch-independent.json',B/'independent-selection-qa-r2/regression.json',B/'typed-family-witness-proof.json',B/'legacy-format-preserve23042954.json',B/'tools/roster-build-manifest.json',B/'verify_roster.py',B/'apply_legacy_ratings.py',Path(__file__)]
dump(B/'final-artifact-pins.json',{str(p.relative_to(B)):sha(p)for p in artifacts})
print('READY_FOR_ROOT',meta,str(output))