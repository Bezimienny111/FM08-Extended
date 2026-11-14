"""X18 verified-byte metadata packaging, REQUIRES ROOT REVIEW. Default validation only.
Reuses X17 helper functions and byte-preserving copy/XML/ZIP/readback sequence.
No native writer, SQL, source refreeze or person generation is invoked.
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
from collections import Counter
import json,csv,hashlib,shutil,zipfile,xml.etree.ElementTree as ET,argparse,re,datetime
ROOT=Path('J:/FM08dev');B=Path(__file__).resolve().parent;S=B/'root-structure';Q=S/'qa';P=B/'prepared'
NAME='TEST_X18';COUNTRIES=['Netherlands','Spain','Greece','France','Finland','Denmark']
SOURCE=B/'rated-db';WORK=B/'release-ready'/NAME;PUBLIC=ROOT/'Dane/db'/NAME;TEMP=B/'release-ready'/f'{NAME}.zip';ARCHIVE=ROOT/'wydania'/f'{NAME}.zip'
PREVIOUS_ZIP_SHA256='3e7ea551ce570dc3892b06ddf1022e5b32c84d44b3bf51440673c3589ac6c565'
EXPECTED=dict(prepared=14170,new=8531,reuse=5639,loans=535,clubs=602,legacy_rating_repairs=921,legacy_CA_changed=913,legacy_PA_changed=811,source_gaps=1157)
REUSE_X17_SHA256='e7cbab55edc244b2db3808caef5301b989135637a840554425292a67b2670624'

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()

def pins(p):return{str(x.relative_to(p)):sha(x)for x in sorted(p.rglob('*'))if x.is_file()}

def rows(p):
 with Path(p).open(encoding='utf-8-sig',newline='')as f:return list(csv.DictReader(f))

def norm(d):return {k:v.lower() for k,v in d.items()}
def samepins(path,expected):assert pins(path)==norm(expected),('data_pin_mismatch',str(path))
def proofpath(rel):
 p=(B/rel).resolve();assert p.is_relative_to(B.resolve());return p

def validate(ready_sha256):
 rp=B/'native-ready-for-root-review.json';assert sha(rp)==ready_sha256,'Root-reviewed ready hash changed'
 ready=read(rp);master=read(B/'manifest.json');counts=dict(ready['counts'])
 counts['prepared']=int(counts.get('prepared',counts.get('people',0)));counts['reuse']=int(counts.get('reuse',counts.get('reused',0)))
 assert all(int(counts[k])==v for k,v in EXPECTED.items()),('reviewed_counts_changed',counts)
 n=counts['prepared'];assert n==counts['new']+counts['reuse']
 assert ready['status']=='PRIVATE_NATIVE_VERIFIED_READY_FOR_ROOT_PUBLICATION_REVIEW' and ready['native'] is True
 assert ready['source_X17_accepted_SI'] and ready['source_X17_accepted_new_career']
 assert SOURCE.resolve()==Path(ready['private_output']).resolve();expected=norm(ready['output_hashes']);samepins(SOURCE,expected)
 artifacts=read(B/'final-artifact-pins.json')
 required={'final-readback.json','final-native-player-UID-ledger.csv','prepared/independent-verification.json','ratings-patch-independent.json','root-structure/qa/regression.json','typed-family-witness-proof.json','N4-source-contract-composite.json'}
 assert required<={k.replace('\\','/') for k in artifacts}
 for rel,h in artifacts.items():assert sha(proofpath(rel))==h.lower(),('artifact',rel)
 roster=read(P/'independent-verification.json');rating=read(B/'ratings-patch-independent.json');final=read(B/'final-readback.json');full=read(P/'full-native.json')
 assert roster['status']==rating['status']==final['status']==full['status']=='pass'
 assert roster['players']==n and roster['added']==counts['new'] and roster['loans']==counts['loans']
 assert roster['all_subject_contract_family_and_identity_verified']==n and roster['new_profiles_raw_attributes_personality_names_DOB_nation_contracts_verified']==counts['new']
 for k in ['entire_PEOPLE_inverse_passed','entire_SERVER_inverse_passed','entire_CLIENT_inverse_passed','all_old_attributes_personalities_identical','all_other_DAT_support_identical']:assert roster[k] is True,k
 for k in ['inverse_entire_PEOPLE','only_CA_PA_words_changed','all_17B_and_89B_tables_unchanged','all_other_files_identical','attributes_personality_rosters_loans_contracts_UIDs_DOB_unchanged']:assert rating[k] is True,k
 assert (rating['scoped_UIDs'],rating['CA_changed'],rating['PA_changed'])==(921,913,811)
 assert norm(rating['output_hashes'])==norm(final['rated_hashes'])==expected
 assert Path(full['output']).resolve()==Path(rating['source']).resolve()
 assert final['all_imported_CA_PA_DOB_owner_verified'] and final['UID_and_TMID_unique'] and final['frozen_X17_hashes_unchanged']
 assert int(final['counts']['prepared'])==n
 for rel,key in [('prepared/manifest.json','prepared_manifest_sha256'),('prepared/native_players.csv','prepared_players_sha256'),('prepared/identities.csv','prepared_identities_sha256'),('prepared/loans.csv','prepared_loans_sha256'),('source-freeze.json','source_freeze_sha256'),('prepared/independent-verification.json','roster_inverse_sha256'),('ratings-patch-independent.json','ratings_inverse_sha256'),('root-structure/qa/regression.json','selection_qa_sha256'),('final-native-player-UID-ledger.csv','ledger_sha256')]:assert sha(B/rel)==final[key].lower(),key
 structure=read(S/'root-independent-verification.json');sr=read(S/'structure-report.json');si=read(S/'structure-independent.json')
 assert structure['status']=='PASS_NATIVE_INVERSE_SCOPE_AND_READBACK_GLOBAL_SELECTION_PENDING'
 # Empty both_forms in inverse is not selection proof: all92 current QA records must pass below.
 for k in ['UID_TEAM_family_projection_exact','inverse_SERVER_CLIENT_all_languages','unrelated_TEAM_bytes_previous_regional_preserved','people_and_other_files_identical','source_unchanged']:assert structure[k] is True,k
 assert (structure['new_TEAM'],structure['new_families'],structure['new_stadiums'],structure['project_families_SugarDaddy_OFF'])==(165,110,385,632)
 assert (sr['new_clubs'],sr['new_families'],sr['new_stadiums'])==(165,110,385) and sr['inverse_verified'] and sr['people_identical']
 assert si['status']=='pass' and si['inverse_all_buffers'] and si['typed_parent_member_readback'] and si['project_clubs_sugar_daddy_off']==632
 assert si['namefix_logical_fields']==6 and si['namefix_physical_edits']==12
 assert norm(sr['output_hashes'])==norm(structure['output_hashes'])==norm(full['source_hashes'])
 assert Path(full['source']).resolve()==Path(sr['output']).resolve()
 roles=read(S/'tools/reserve-kind-overlay.json')['Rows'];assert len(roles)==55 and len({x['ProjectedClubUID'] for x in roles})==55
 assert all(x['RequiredNativeReserveKind'] in [3,16] for x in roles)
 linked=[x for x in sr['additions'] if x['kind']=='new_linked_reserve'];assert len(linked)==55 and {x['uid'] for x in linked}=={x['ProjectedClubUID'] for x in roles}
 assert all(x['parent_uid'] is not None for x in linked)
 plan={int(x['ProjectedClubUID']):x for x in read(S/'club-plan.json')}
 for x in roles:assert plan[x['ProjectedClubUID']]['RequiredNativeReserveKind']==x['RequiredNativeReserveKind']
 nameproof=read(S/'tools/new-embedded-and-namefix-r2-proof.json')
 assert nameproof['Status']=='PASS_NEW_EMBEDDED_AND_R2_ACTUAL_SERVER_SUFFIX_INDEPENDENT_RELOAD'
 assert nameproof['IndependentExistingCodecReload'] and nameproof['FinancePrefixBitwiseUnchanged'] and nameproof['CLIENTSERVERHeaderAndNameKitFieldsMatch']
 assert nameproof['CorrectedNamefixSHA256']==sr['namefix_plan_sha256']
 assert {x['UID'] for x in nameproof['ActualR2SERVERFamilies']}=={1800200042,1800200058,1800200060}
 assert all(x['FinanceAndAllPreSuffixBytesIdentical'] and x['AllOtherSuffixFieldsIdentical'] and x['ExactFamilyFooterPreserved'] for x in nameproof['ActualR2SERVERFamilies'])
 assert len(sr['namefix_edits'])==12 and {x['UID'] for x in sr['namefix_edits']}=={1800200042,1800200058,1800200060}
 assert {x['Name'] for x in sr['preserved_kolding']}=={'TEAM_2121_kind3_div566','FAMILY_2121','FAMILY_928820'} and all(x['BitwisePASS'] for x in sr['preserved_kolding'])
 assert si['preserved_kolding']==sr['preserved_kolding']
 family=read(B/'typed-family-witness-proof.json');assert family['status']=='typed_native_family_footer_unique_for_all_requested_families' and family['database_modified'] is False
 assert family['requested_TEAMs']==731 and family['typed_FAMILYs']==652
 assert family['source_server_sha256']==sr['output_hashes']['server_db.dat'].lower() and family['source_client_sha256']==sr['output_hashes']['client_db.dat'].lower()
 n4=read(B/'N4-source-contract-composite.json');assert n4['Status']=='PASS_PINNED_SOURCE_N4_ACTOR_SCOPE' and n4['Failures']==0 and n4['AllImportedReuseCovered'] and n4['ImportedReuseUIDs']==5639 and n4['TotalDistinctUIDs']==10091
 qa=read(Q/'regression.json');qp=read(Q/'pins.json')
 assert qp['Status']==qa['Status']=='NUMERIC_SELECTION_REGRESSION_PASS' and qp['ReportSHA256']==sha(Q/'regression.json')
 assert qp['ScriptSHA256']==qa['ScriptSHA256']==sha(Q/'selection_regression.py')
 assert len(qa['Checks'])==qa['TotalChecks']==325 and qa['PreviousChecks']==233 and qa['CurrentBatchChecks']==92
 current=[x for x in qa['Checks'] if x['origin']=='current_X18_six_countries'];assert len(current)==92 and all(x['after_passed'] for x in current)
 for k in ['NewRegressions','CurrentBatchFailures','NewCountryNullTeams','NewCountryNullParticipants','UnexpectedCompetitionCountDeltas','RawSelectionSlotFindings']:assert not qa[k],k
 assert not qa['RawCurrentDeltaMismatch']
 assert len(qa['SourceReplay']['Sweden'])==len(qa['TargetReplay']['Sweden'])==14
 for path,h in qp['RootReportPins'].items():assert sha(path)==h.lower(),('QArootpin',path)
 for path,h in qa['EvidencePins'].items():assert sha(path)==h.lower(),('QAevidence',path)
 for item in qp['SourceTargetPins']:
  for rel,h in item['Hashes'].items():assert sha(Path(item['Path'])/rel)==h.lower(),('QAdata',rel)
 assert norm(structure['output_hashes'])['server_db.dat']==qp['SourceTargetPins'][1]['Hashes']['server_db.dat'].lower()
 negatives=read(B/'negative-tests.json');assert len(negatives)==6 and all(x['rejected'] for x in negatives)
 freeze=read(B/'source-freeze.json');frozen=Path(freeze['frozen']);accepted=Path(freeze['source']);sourcepins=norm(freeze['hashes']);samepins(frozen,sourcepins);samepins(accepted,sourcepins)
 previous_zip=ROOT/'wydania/TEST_X17.zip';assert sha(previous_zip)==PREVIOUS_ZIP_SHA256
 assert not any(x.exists() for x in [WORK,PUBLIC,TEMP,ARCHIVE]),'Never overwrite release, staging or ZIP'
 for x in [WORK,PUBLIC,TEMP,ARCHIVE]:assert x.resolve().is_relative_to(ROOT.resolve())
 people=rows(B/'final-native-player-UID-ledger.csv');clubs=rows(P/'club_map.csv');loans=rows(P/'loans.csv');identities=rows(P/'identities.csv')
 assert len(people)==len({x['UID'] for x in people})==len({x['TMID'] for x in people})==len({x['SubjectID'] for x in people})==n
 assert len(clubs)==602 and len(loans)==535 and set(x['Country'] for x in clubs)==set(COUNTRIES)
 assert sum(x['New'].lower()=='true' for x in people)==8531
 identity={x['SubjectID']:x for x in identities};assert len(identity)==n
 for x in people:
  i=identity[x['SubjectID']];assert x['NativeDOB']==i['TargetDOB'] and int(x['OwnerTEAM'])==int(i['OwnerClubIndex']) and int(x['PlayingTEAM'])==int(i['PlayingClubIndex']),('UID_DOB_owner',x['UID'])
 # DOB itself is not unique: distinct real people can share the same date.
 sentinels=final['sentinel_names_source_after_verified'];ledger={x['UID']:x for x in people}
 for x in sentinels:
  z=ledger[str(x['UID'])];assert x['NameBlockUnchanged'] and str(x['TMID'])==z['TMID'] and x['SourceName']==z['SourceName']
  assert x['PhysicalFirstName']==z['FirstName'] and x['PhysicalLastName']==z['LastName']
 bysubject={x['SubjectID']:x['Country'] for x in people};stats=[]
 for c in COUNTRIES:
  ps=[x for x in people if x['Country']==c];stats.append(dict(country=c,clubs=sum(x['Country']==c for x in clubs),players=len(ps),new=sum(x['New'].lower()=='true' for x in ps),loans=sum(bysubject[x['SubjectID']]==c for x in loans)))
 assert sum(x['players'] for x in stats)==n
 native={rel:h for rel,h in expected.items() if Path(rel).suffix.lower() in ['.dat','.edt','.lnc']}
 assert all(Path(rel).suffix.lower() in ['.dat','.edt','.lnc','.xml','.json','.txt','.md'] for rel in expected)
 xmls=list(SOURCE.glob('*.xml'));assert len(xmls)==1;tree=ET.fromstring(xmls[0].read_bytes());assert tree.find("./string[@id='required_version']").get('value')=='8.0.2'
 return dict(ready=ready,master=master,counts=counts,expected=expected,native=native,tree=tree,stats=stats,qa=qa,frozen=frozen,accepted=accepted,sourcepins=sourcepins,previous_zip=previous_zip,structure=structure)

def publish(v):
 counts=v['counts'];native=v['native'];tree=v['tree'];stats=v['stats'];ready=v['ready']
 tree.find("./string[@id='name']").set('value',NAME);tree.find("./string[@id='description']").text=NAME
 WORK.mkdir(parents=True)
 for rel,h in native.items():
  dest=WORK/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SOURCE/rel,dest);assert sha(dest)==h
 (WORK/f'{NAME}.xml').write_bytes(ET.tostring(tree,encoding='utf-8',xml_declaration=True))
 text='''TEST_X18 - FM08 8.0.2
Holandia, Hiszpania, Grecja, Francja, Finlandia, Dania.
Podstawa: zaakceptowana TEST_X17 po SI i nowej karierze; sezon X17 niepotwierdzony.
STATUS X18: Native PASS. SI / nowa kariera / sezon: PENDING.
14170 profili: 8531 nowych UID, 5639 reuse; 535 wypozyczen; 602 kluby planu.
1157 wpisow luk: 739 zrodlowych i 418 odlozen. Braki pozostaja dla silnika.

TEST ZBIORCZY:
1. Otworz TEST_X18 w SI 8.0.2, zapisz i wczytaj ponownie.
2. Utworz nowa kariere ze wszystkimi 16 klasycznymi poziomami szesciu krajow:
   Holandia 2, Hiszpania 3, Grecja 2, Francja 3, Finlandia 3, Dania 3.
   Grupy liczymy osobno. Sprawdz tabele, terminarze, kadry i wypozyczenia.
3. Na osobnej kopii sprawdz kolejny sezon; to osobny test od nowej kariery.

NL 18/20; ES 20/22/4x20; GR 16/18; FR 20/20/20;
FI 14/14/3 grupy; DEN 12/16/2x16.
Dolne pule i dodatkowe kluby pozostaja katalogiem. Grupy FM08 sa przyblizeniem geografii.
Baza wymaga NOWEJ kariery. Grafiki i nowe funkcje launchera nie sa czescia paczki.
Szczegoly: RAPORT_TEST_X18.txt, manifest.json.
'''
 (WORK/'README.md').write_text(text,encoding='utf-8')
 report='TEST_X18 - lokalne wydanie testowe\nNative PASS; SI / kariera / sezon PENDING.\n\n'
 for x in stats:report+=f"{x['country']}: {x['clubs']} klubow, {x['players']} profili, {x['new']} nowych UID, {x['loans']} wypozyczen.\n"
 report+=f'''
Razem 14170 profili: 8531 nowych, 5639 reuse; 535 potwierdzonych loan; 602 kluby.
165 nowych TEAM, 110 nowych FAMILY, 55 rezerw pod prawdziwymi rodzicami, 385 stadionow.
632 rodziny projektu: Sugar Daddy OFF, niezalezny odczyt. Role 3/16 zamiast slepego seed10.
921 poprawek dawnych szacunkow: 913 CA / 811 PA. Zmieniono tylko slowa CA/PA,
bez zmian tabel 17B/89B, atrybutow, osobowosci, umow, UID i DOB.
{counts['new_talent_awards']} nowych przydzialow talentu; eksperymentalnego generatora nie wdrazano.
Wypozyczenia zachowuja wlascicieli. Tylko potwierdzone opcje wykupu, bez obowiazkowego wykupu.
1157 luk obejmuje 739 zrodlowych i 418 odlozonych profili; luki stadionowe: {counts['venue_gaps']}.
Nie uzupelniamy fikcyjnych osob i dat. To nie deklaracja kompletnej aktualizacji calego kraju.

Kaskady: koncowe tabele poprzedniego sezonu i klasyczny format 16 grywalnych poziomow.
NL 18/20; ES 20/22/4x20; GR 16/18; FR 20/20/20; FI 14/14; DEN 12/16/2x16.
Finnish Second i pozostale dolne pule spelniaja potwierdzone minima obu form.
Kompromisy geograficzne sa jawne w source-allocation; nie udajemy wspolczesnych grup.
Frederikssund 506 i Glostrup 510: istniejace fizyczne kluby, bez falszywego TMID i rosteru.
Elo (realny Nelonen6) i Atlantis II pozostaja w nizszej niegrywalnej puli123.
Kolding 2121 Kind3 / FAMILY2121+928820 / div566 zachowany. Jego29profili odlozone;
nie przenosimy ich do zastepcy. Riviera81451 i Oulunsalon55564 nadal odlozone.
UCAM, Ceuta, KTP, Jazz i nowy Calvo: udowodnione tozsamosci sportowe,
bez zapozyczania historii odrebnych klubow.

KONTROLE:
Cale PEOPLE/SERVER/CLIENT inverse. Kazdy UID, DOB, wlasciciel i CA/PA odczytany.
Stare atrybuty/osobowosci chronione; 55 rol i rodzicow obejmuje source-to-actor inverse.
Trzy poprawki nazw X17 (Persikutim/Punjab/Kendal): tylko12pol embedded full/short R2,
bez sortowania UID lub FAMILY i bez zmian EXE.
325 globalnych warunkow: 233 poprzednie i 92 nowe (obie formy), zero nowych regresji i country-null.
Sweden14, stock IDN, ES child-to-parent oraz CA6460 territory-to-Lower odtworzone statycznie.
ALT pozostaje surowy poza swiadkowanym Sweden14. Nie jest to dowod runtime lub sezonu.
Wszystkie natywne bajty wydania sa identyczne z rated-db; zmieniaja sie tylko metadane i XML.
X17 i jej ZIP chronione. Bez zmian aktywnej gry, EXE i poprzednich zapisow SI.
'''
 (WORK/'RAPORT_TEST_X18.txt').write_text(report,encoding='utf-8')
 inherited={p.name:read(p) for p in SOURCE.glob('*.json') if p.name in ['next-batch-fixes.json','native-reserve-role-gaps.json'] or 'CARRIED_FORWARD_GAPS' in p.name}
 if inherited:dump(WORK/'X17_CARRIED_FORWARD_GAPS.json',inherited)
 for name in ['next-batch-fixes.json','native-reserve-role-gaps.json']:
  if (B/name).exists():shutil.copy2(B/name,WORK/name)
 manifest=dict(name=NAME,required_game_version='8.0.2',prepared_date=datetime.date.today().isoformat(),release_stage='native_verified_test_candidate',base='accepted TEST_X17 after SI/newcareer; season notconfirmed',native_verified=True,SI_verified=False,new_career_verified=False,season_verified=False,countries=stats,counts=counts,structure=ready['structure'],classic_playable_levels=16,classic_counts=dict(Netherlands=[18,20],Spain=[20,22,[20,20,20,20]],Greece=[16,18],France=[20,20,20],Finland=[14,14,'regionalSecond'],Denmark=[12,16,[16,16]]),numeric_regression=dict(checks=325,previouschecks=233,new_country_form_checks=92,new_regressions=0,live_test_pending=True),native_file_hashes=native)
 dump(WORK/'manifest.json',manifest)
 sums=pins(WORK);(WORK/'SHA256SUMS.txt').write_text(''.join(h+'  '+rel.replace('\\','/')+'\n' for rel,h in sums.items()),encoding='utf-8');package=pins(WORK)
 with zipfile.ZipFile(TEMP,'x',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
  for rel in sorted(package):z.write(WORK/rel,NAME+'/'+rel.replace('\\','/'))
 with zipfile.ZipFile(TEMP) as z:
  assert z.testzip() is None and set(z.namelist())=={NAME+'/'+r.replace('\\','/') for r in package}
  for rel,h in package.items():assert hashlib.sha256(z.read(NAME+'/'+rel.replace('\\','/'))).hexdigest()==h
 samepins(SOURCE,v['expected']);samepins(v['frozen'],v['sourcepins']);samepins(v['accepted'],v['sourcepins']);assert sha(v['previous_zip'])==PREVIOUS_ZIP_SHA256
 shutil.copytree(WORK,PUBLIC);assert pins(PUBLIC)==package;ARCHIVE.parent.mkdir(exist_ok=True)
 with TEMP.open('rb') as inp,ARCHIVE.open('xb') as out:shutil.copyfileobj(inp,out,1048576)
 assert sha(ARCHIVE)==sha(TEMP) and pins(PUBLIC)==package;assert sha(v['previous_zip'])==PREVIOUS_ZIP_SHA256
 samepins(SOURCE,v['expected']);samepins(v['frozen'],v['sourcepins']);samepins(v['accepted'],v['sourcepins'])
 result=dict(status='LOCAL_TEST_PACKAGE_PREPARED_NOT_EXTERNALLY_UPLOADED',name=NAME,database=str(PUBLIC),archive=str(ARCHIVE),archive_bytes=ARCHIVE.stat().st_size,archive_sha256=sha(ARCHIVE),database_hashes=package,native=True,SI=False,new_career=False,season=False,accepted_X17_unchanged=True,private_source_unchanged=True,all_native_data_identical=True,countries=stats,counts=counts,external_publication=False)
 dump(B/'publication.json',result);master=v['master'];master.update(status='TEST_X18_LOCAL_PACKAGE_READY_SI_GAME_PENDING',output=str(PUBLIC),archive=str(ARCHIVE),output_database_created=True,native=True,SI=False,new_career=False,season=False,output_hashes=package,publication=str(B/'publication.json'),counts=counts);dump(B/'manifest.json',master)
 print(json.dumps({k:v for k,v in result.items() if k!='database_hashes'},ensure_ascii=True,indent=2))

def main():
 parser=argparse.ArgumentParser(description='ROOT REVIEW REQUIRED. Default validates only: no ZIP/database copy.')
 parser.add_argument('--ready-sha256',required=True,help='Exact root-reviewed native-ready-for-root-review.json SHA256')
 parser.add_argument('--publish',action='store_true',help='Explicit root action after code and ready/proofs review; creates TEST_X18 and ZIP')
 args=parser.parse_args();assert __debug__ and re.fullmatch(r'[0-9a-fA-F]{64}',args.ready_sha256)
 v=validate(args.ready_sha256.lower())
 if not args.publish:print(json.dumps(dict(status='VALIDATED_ONLY_REQUIRES_ROOT_PUBLICATION_REVIEW',name=NAME,counts=v['counts'],database_created=False,ZIP_created=False,script_sha256=sha(Path(__file__))),ensure_ascii=True));return
 publish(v)
if __name__=='__main__':main()
