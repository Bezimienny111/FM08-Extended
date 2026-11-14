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
m=read(P/'manifest.json');full=read(P/'full-native.json');verified=read(P/'independent-verification.json');rating=read(B/'ratings-patch-independent.json');qa=read(B/'selection-readback.json')
assert full['status']==verified['status']==rating['status']=='pass'
assert qa['Status']=='PASS_ALL_CURRENT_AND_INHERITED_SELECTION' and qa['Evaluations']==621 and qa['NewConditions']==32
assert not qa['PriorRegressions'] and not qa['NewFailures'] and not qa['InheritedFailures']
assert all(q['Passed']for q in qa['CurrentChecks'])
source=Path(m['source']);output=Path(rating['output']);assert Path(full['output'])==Path(rating['source'])
assert pins(source)==full['source_hashes'] and pins(output)==rating['output_hashes']
audit={int(r['ID']):r for r in rows(B/'ratings-audit-after/players.csv')}
ps=rows(P/'native_players.csv');ids=rows(P/'identities.csv');proof=read(P/'provenance.json');subjects={int(r['id90']):r for r in full['subjects']};clubs={r['TeamIndex']:r for r in rows(P/'club_map.csv')};ledger=[];talents=[]
assert len(ps)==len(ids)==len(proof)==len(subjects)==m['counts']['prepared']
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
for country in ['England']:
 rs=[r for r in ledger if r['Country']==country];ca=[r['CA']for r in rs];pa=[r['PA']for r in rs]
 summary.append(dict(Country=country,Clubs=sum(c['Country']==country for c in clubs.values()),Players=len(rs),New=sum(r['New']for r in rs),CAmin=min(ca),CAmax=max(ca),CAmean=round(statistics.mean(ca),2),CAstd=round(statistics.pstdev(ca),2),DistinctCA=len(set(ca)),PAmin=min(pa),PAmax=max(pa),MeanDevelopmentGap=round(statistics.mean(y-x for x,y in zip(ca,pa)),2)))
save(B/'final-coverage-ratings.csv',summary)
structure=read(B/'root-structure/root-independent-verification.json');assert structure['status']=='PASS_NATIVE_INVERSE_SCOPE_AND_READBACK_GLOBAL_SELECTION_PENDING' and structure['inverse_SERVER_CLIENT_all_languages'] and structure['UID_TEAM_family_projection_exact'] and structure['unrelated_TEAM_bytes_previous_regional_preserved'] and structure['people_and_other_files_identical'] and structure['source_unchanged']
sr=read(B/'root-structure/structure-report.json');venuegaps=len(sr['venue_gaps'])
freeze=read(B/'source-freeze.json');assert pins(Path(freeze['frozen']))==freeze['hashes'] and pins(Path(freeze['source']))==freeze['hashes']
negative=read(B/'negative-tests.json');assert len(negative)==6 and all(v['rejected']for v in negative)
pilot=read(Path(m['pilot_verification_path']));assert pilot['status']=='pass' and sha(Path(m['pilot_verification_path']))==m['pilot_verification_sha256']
legacyproof=dict(Status='No unsupported source participant bypass; frozen source actor contracts covered by pinned fresh X22 N4 records',SourcePreflightComposite=read(B/'N4-source-contract-composite.json'))
meta=dict(people=len(ledger),prepared=len(ledger),new=sum(r['New']for r in ledger),reused=sum(not r['New']for r in ledger),reuse=sum(not r['New']for r in ledger),loans=len(rows(P/'loans.csv')),clubs=len(clubs),actor_clubs=m['counts']['actor_clubs'],legacy_rating_repairs=rating['scoped_UIDs'],legacy_CA_changed=rating['CA_changed'],legacy_PA_changed=rating['PA_changed'],new_talent_awards=len(talents),deferred=len(read(P/'deferred.json')),source_gaps=len(read(P/'source-gaps.json')),source_collection_gaps=56,source_cards=4312,source_candidates=4256,source_unique_candidates=4256,source_loans=495,new_clubs=10,new_stadiums=int(sr['new_stadiums']),venue_gaps=venuegaps,project_families_SugarDaddy_OFF=structure['project_families_SugarDaddy_OFF'])
assert meta['people']==m['counts']['prepared'] and meta['loans']==m['counts']['loans'] and meta['clubs']==164 and structure['new_TEAM']==10 and structure['new_families']==10 and structure['project_families_SugarDaddy_OFF']==756
readback=dict(status='pass',rated_output=str(output),rated_hashes=pins(output),prepared_manifest_sha256=sha(P/'manifest.json'),prepared_players_sha256=sha(P/'native_players.csv'),prepared_identities_sha256=sha(P/'identities.csv'),prepared_loans_sha256=sha(P/'loans.csv'),source_freeze_sha256=sha(B/'source-freeze.json'),roster_inverse_sha256=sha(P/'independent-verification.json'),ratings_inverse_sha256=sha(B/'ratings-patch-independent.json'),selection_qa_sha256=sha(B/'selection-readback.json'),ledger_sha256=sha(B/'final-native-player-UID-ledger.csv'),all_imported_CA_PA_DOB_owner_verified=True,UID_and_TMID_unique=True,frozen_X22_hashes_unchanged=True,legacy_unsupported_record_preserved=legacyproof,sentinel_names_source_after_verified=verified['sentinel_name_source_after_proofs'],counts=meta,recorded_at=datetime.now(timezone.utc).isoformat())
assert verified['entire_SERVER_inverse_passed']and verified['entire_CLIENT_inverse_passed']and rating['all_other_files_identical']
readback['post_actor_structural_preservation']=dict(Status='PASS_SOURCE_STRUCTURAL_PROOFS_PRESERVED_BY_WHOLE_FILE_INVERSE_AND_CA_PA_ONLY_PATCH',NativeStructureParentCountrySugarProof=str(B/'root-structure/root-independent-verification.json'),NativeStructureParentCountrySugarProofSHA256=sha(B/'root-structure/root-independent-verification.json'),RosterWholeServerClientInverse=str(P/'independent-verification.json'),RosterWholeServerClientInverseSHA256=sha(P/'independent-verification.json'),RatingOtherFilesIdentical=True,Explanation='Root typed kind/parent/country/SugarOFF and Netherlands repair witnesses are pinned on actor source; actor inverse restores only verified roster/name-dictionary/loan spans and preserves TEAM prefixes and suffixes. Rating changes only scoped CA/PA words in PEOPLE.')
dump(B/'final-readback.json',readback)
prior=B.parents[1]/'COUNTRY_BATCH_BLR_BEL_AUT_AUS_ARG_20261114/native-prep';priorpins=read(prior/'final-artifact-pins.json');assert sha(prior/'next-batch-fixes.json')==priorpins['next-batch-fixes.json'];carry=read(prior/'next-batch-fixes.json')
dump(B/'next-batch-fixes.json',dict(inherited_unresolved=carry,current_deferred_profiles=read(P/'deferred.json'),source_gaps=read(P/'source-gaps.json'),legacy_unsupported_preserved=legacyproof,reader_backlog='ReadPlayers missing-firstname heuristic may display fabricated fallback labels; actual NAMEIDs/strings/known-as preserved and source-proven. No editor rebuild or PERSON identity change.',venue_gaps=venuegaps,deferred_club_identities=read(B/'deferred-clubs.json'),structural_physical_fallbacks=read(B/'structural-fallbacks.json'),earlier_unresolved_fixes_preserved_in_inherited_manifest=True,current_deferred_external_owners=[],current_identity_deferred_counts=read(B/'person-preflight-summary.json')['PersonDecisions'],partial_club_rosters=[r for r in read(P/'coverage.json')if r['Confirmed']==0]))
status=dict(status='PRIVATE_NATIVE_VERIFIED_READY_FOR_ROOT_PUBLICATION_REVIEW',private_output=str(output),planned_public_output='ROOT_SELECTS_FIRST_FREE_TEST_Xn',source=str(source),source_X22_user_authorized_for_England=True,source_X22_season='IN_PROGRESS_TARGET_2010',counts=meta,native=True,SI=False,new_career=False,season=False,source_hashes=pins(source),output_hashes=pins(output),structure=structure,global_selection_qa=dict(status=qa['Status'],conditions=qa['Evaluations'],new_regressions=len(qa['PriorRegressions']),new_club_countries_verified=True,runtime_test=False),root_selection_qa_path=str(B/'selection-readback.json'),final_readback=str(B/'final-readback.json'),final_ledger=str(B/'final-native-player-UID-ledger.csv'),metadata='Verified private DAT; root assigns the first free TEST_Xn and replaces inherited XML and metadata at publication.',public_database_mutated=False,EXE_modified=False,recorded_at=datetime.now(timezone.utc).isoformat())
dump(B/'native-ready-for-root-review.json',status)
manifest=read(B/'manifest.json');manifest.update(status=status['status'],current_native_stage=status);dump(B/'manifest.json',manifest)
text='# Anglia - baza zweryfikowana natywnie\n\nNowa paczka na kopii TEST_X22: Anglia, 6 poziomow i 7 grup (20/24/24/24/24/22/22), 160 grajacych klubow +4 zmodernizowane w nizszej puli. Native PASS; SI, nowa kariera i sezon nowej wersji PENDING. X22 nadal w dluzszym tescie, uzytkownik jawnie zlecil kontynuacje.\n\n'+json.dumps(meta,ensure_ascii=False,indent=2)+'\n\nZapisano potwierdzone profile i wypozyczenia, sprawdzono UID, kontrakty, DOB, nazwy, CA/PA, cechy i pelne inverse. Indywidualne rozklady modelu CA/PA sa zachowane; wiarygodne oceny i wczesniejsze talenty chronione. Sugar Daddy OFF756 rodzin projektu, w tym10 nowych.\n\nCztery kluby przesuniete wedlug koncowych tabel poprzedniego sezonu: Hereford FC, Kings Lynn Town i Farnborough do Southern Premier, Dover do Isthmian Premier. Historyczne kluby i kluby odtworzone sa odrebnymi rekordami; profile i historia zachowane. Stadiony96 nowych,7 jawnych luk; brakujacych osob nie dopisano fikcyjnie.621 warunkow ligowych PASS.\n\nTa zmiana nie modyfikuje fm.exe, zasad silnika, launchera ani skorek. Testy SI/kariera/sezon sa osobne.\n'
(B/'RAPORT.md').write_text(text,encoding='utf-8');(B/'WZNOWIENIE.md').write_text(text,encoding='utf-8')
artifacts=[B/'RAPORT.md',B/'WZNOWIENIE.md',B/'native-ready-for-root-review.json',B/'final-readback.json',B/'final-native-player-UID-ledger.csv',B/'talent-native-UID-ledger.json',B/'next-batch-fixes.json',P/'manifest.json',P/'independent-verification.json',P/'sentinel-name-source-after.json',B/'ratings-patch-independent.json',B/'selection-readback.json',B/'typed-family-witness-proof.json',B/'N4-source-contract-composite.json',B/'prepared-scope-verification.json',B/'tools/build-manifest.json',B/'verify_roster.py',B/'apply_legacy_ratings.py',Path(__file__)]
dump(B/'final-artifact-pins.json',{str(p.relative_to(B)):sha(p)for p in artifacts})
print('READY_FOR_ROOT',meta,str(output))
