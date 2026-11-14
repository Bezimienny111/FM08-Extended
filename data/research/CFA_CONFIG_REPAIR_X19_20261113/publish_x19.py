"""Approved minimal local X19 publication; metadata + exact reviewed48B patch only."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,struct,zlib,zipfile,xml.etree.ElementTree as ET,sys
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');B=Path(__file__).resolve().parent;NAME='TEST_X19';PUBLIC=ROOT/'Dane/db'/NAME;ARCHIVE=ROOT/'wydania'/f'{NAME}.zip';STAGE=B/'release-ready'/NAME;TEMP=B/'release-ready'/f'{NAME}.zip'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pins(d):return{str(p.relative_to(d)):sha(p)for p in sorted(d.rglob('*'))if p.is_file()}
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def unpack(p):return zlib.decompress(p.read_bytes()[9:])
assert not any(p.exists()for p in[PUBLIC,ROOT/'Dane/db/TEST_X19.xml',ARCHIVE,STAGE,TEMP]),'Never overwrite an existing version/staging/archive'
assert sha(B/'native-ready-for-root-review.json')=='bc67cb9cd21bebfc2df1cb3327113fb0a93d5ab0e8c907d552bfcec3f003e7c7';ready=read(B/'native-ready-for-root-review.json');proof=read(B/'native-patch-proof.json');qa=read(B/'selection-regression.json');semantic=read(B/'semantic-cfa-guard.json');freeze=read(B/'source-freeze.json');artifact=read(B/'artifact-pins.json')
assert all(sha(B/k)==v for k,v in artifact.items()),'Final artifact pins changed'
assert ready['status']=='PRIVATE_NATIVE_VERIFIED_READY_FOR_ROOT_PUBLICATION_REVIEW'and ready['native']and not ready['SI']and not ready['new_career']and not ready['season']
assert qa['Status']=='NUMERIC_SELECTION_REGRESSION_PASS'and qa['TotalChecks']==325 and qa['CurrentBatchChecks']==92 and all(x['after_passed']for x in qa['Checks'])
source=Path(ready['source']);original=Path(freeze['source']);private=Path(ready['private_output']);before=freeze['hashes'];after=ready['output_hashes'];assert pins(source)==pins(original)==before and pins(private)==after
assert sha(Path(freeze['original_X18_ZIP']))==freeze['original_X18_ZIP_SHA256'];assert{k:v for k,v in before.items()if k!='server_db.dat'}=={k:v for k,v in after.items()if k!='server_db.dat'}
# Independent inverse: rederive the only permitted field addresses from frozen typed TEAM export.
expected_uids={8162290,143844,8444331,1800220048,1975,1800220066};records={x['ClubUID']:x for x in read(B/'source-native-structure.json')['records']};expected_offsets={records[u]['Start']+o for u in expected_uids for o in[7,15]};edits=proof['Edits'];assert len(edits)==12 and {x['Offset']for x in edits}==expected_offsets and set(proof['AllowedUIDs'])==expected_uids
old=unpack(source/'server_db.dat');new=unpack(private/'server_db.dat');restored=bytearray(new);assert len(old)==len(new)and(source/'server_db.dat').read_bytes()[:9]==(private/'server_db.dat').read_bytes()[:9]
for e in edits:
 at=e['Offset'];b=bytes.fromhex(e['BeforeHex']);a=bytes.fromhex(e['AfterHex']);assert len(a)==len(b)==4 and old[at:at+4]==b and new[at:at+4]==a;restored[at:at+4]=b
assert bytes(restored)==old and 0<sum(x!=y for x,y in zip(old,new))<=48
assert ready['counts']['people']==14170 and ready['counts']['loans']==535 and ready['counts']['clubs']==602
STAGE.parent.mkdir(exist_ok=True);shutil.copytree(private,STAGE);assert pins(STAGE)==after
xml=ET.parse(STAGE/'TEST_X18.xml');root=xml.getroot();found=set()
for s in root.findall('string'):
 if s.get('id')=='name':s.set('value',NAME);s.text=None;found.add('name')
 if s.get('id')=='description':s.attrib.pop('value',None);s.text='TEST_X19: poprawka inicjalizacji francuskiej CFA na najnowszej X18 po zapisie SI. Kadry i oceny bez zmian.';found.add('description')
assert found=={'name','description'};xml.write(STAGE/f'{NAME}.xml',encoding='utf-8',xml_declaration=True)
(STAGE/'TEST_X18.xml').unlink();(STAGE/'RAPORT_TEST_X18.txt').unlink()
old_manifest=read(source/'manifest.json');counts=ready['counts'];countries=old_manifest['countries'];now=datetime.now(timezone.utc).isoformat()
manifest=dict(name=NAME,required_game_version='8.0.2',prepared_date='2026-11-13',release_stage='native_verified_cfa_configuration_fix_test_candidate',base='latest public TEST_X18 after SI save; X18 new career failed in FRE_CFA initial draw',source_X18_SI_saved=True,source_X18_new_career='FAILED_CFA_ARRAY_REMOVE_RANGE',native_verified=True,SI_verified=False,new_career_verified=False,season_verified=False,countries=countries,counts=counts,counts_inherited_unchanged_from_X18=True,scope='Six source-backed kind0 clubs CFA2 to CFA; Current and Alternate only,12int32fields/max48rawbytes',six_clubs=[dict(UID=x['UID'],TMID=x['TMID'],Name=x['Name'],CurrentCOMPBefore=x['CurrentCOMPBefore'],CurrentCOMPAfter=145438,AlternateCOMPBefore=x['AlternateCOMPBefore'],AlternateCOMPAfter=145438)for x in proof['TEAMWitnesses']],native_checks=dict(whole_SERVER_inverse=True,all_other_native_support_files_identical=True,fresh_selection_checks=325,source_cache_used=False,all_players_rosters_contracts_CA_PA_sugar_daddy_unchanged=True),scheduler_prediction=dict(CFA_before_candidates=67,CFA_after_candidates=73,predicted_only=True,game_verified=False,CFA2_after=99,CFA2_minimum=96),source_native_hashes={k:v for k,v in before.items()if k.lower().endswith('.dat')},output_native_hashes={k:v for k,v in after.items()if k.lower().endswith('.dat')},source_freeze_sha256=sha(B/'source-freeze.json'),reviewed_ready_sha256=sha(B/'native-ready-for-root-review.json'),patch_proof_sha256=sha(B/'native-patch-proof.json'),selection_qa_sha256=sha(B/'selection-regression.json'),recorded_at=now)
dump(STAGE/'manifest.json',manifest)
provenance=dict(scope=manifest['scope'],source='latest TEST_X18 after SI',source_X18_native_hashes=manifest['source_native_hashes'],X19_native_hashes=manifest['output_native_hashes'],TEAMWitnesses=proof['TEAMWitnesses'],Edits=proof['Edits'],SemanticPrediction=semantic,NativePASS=True,SI=False,new_career=False,season=False,source_X18_and_ZIP_preserved=True,all_other_native_support_files_identical=True)
dump(STAGE/'CFA_PATCH_PROVENANCE.json',provenance)
report='TEST_X19 — poprawka inicjalizacji francuskiej CFA\n\nŹródło: najnowsza publiczna TEST_X18 po zapisie SI. Konfiguracja nowej kariery X18 zakończyła się błędem ARRAY::remove_range w FRE_CFA. Nie wracamy do wcześniejszej bazy przed zapisem SI.\n\nPrzesunięcia z CFA2 do CFA (kolejność z końcowych tabel poprzedniego sezonu):\n'+'\n'.join(f"- {x['Name']} (UID{x['UID']})"for x in proof['TEAMWitnesses'])+'\n\nZmieniono12 pól int32: Current i Alternate tych sześciu klubów; maksymalnie48 bajtów nieskompresowanego SERVER. Kadry, zawodnicy, kontrakty, CA/PA, rodziny klubów, SugarDaddy, CLIENT, LANG oraz pliki pomocnicze identyczne z X18 po SI.\n\nNative: PASS — pełna inwersja SERVER, kontrola pozostałych plików, świeże325 warunków selekcji obu form. CFA:59 bezpośrednich +14 wcześniej zaobserwowanych rezerw daje przewidywane73 kandydatury; ten wynik NIE jest potwierdzeniem działania gry. CFA2 zachowuje99 klubów przy minimum96.\n\nOdziedziczone dane ostatniej paczki pozostają:14170 zawodników,535 wypożyczeń,602 kluby. Nie wykonano nowego importu kadr ani zmian silnika/EXE.\n\nTEST_X19: zapis SI, nowa kariera i sezon OCZEKUJĄ NA TEST. Poprzednia X18 i jej ZIP zostały zachowane.\n'
(STAGE/f'RAPORT_{NAME}.txt').write_text(report,encoding='utf-8');(STAGE/'README.md').write_text('# TEST_X19\n\nData-only CFA configuration correction based on the latest TEST_X18 after SI save. X18 career creation failed; X19 is a native-verified test candidate.\n\nSix clubs move from CFA2 to CFA through12 Current/Alternate int32 fields. Player and squad data remain unchanged:14170 players,535 loans,602 clubs from the preceding batch. All native files except SERVER remain byte-identical to post-SI X18.\n\nNative inverse and fresh325 selection checks: PASS. Predicted CFA candidates:73; this is not a game test. SI save, new career and season: PENDING.\n\nSee RAPORT_TEST_X19.txt, manifest.json and CFA_PATCH_PROVENANCE.json. Existing next-batch gaps are preserved.\n',encoding='utf-8')
# Only stated metadata is replaced; every native/support/gap byte remains from the reviewed private result.
metadata={'TEST_X18.xml','RAPORT_TEST_X18.txt','README.md','manifest.json','SHA256SUMS.txt'}
for rel,h in after.items():
 if rel not in metadata:assert sha(STAGE/rel)==h,('Nonmetadata copy changed',rel)
assert not any(p.name=='TEST_X18.xml'for p in STAGE.iterdir());assert ET.parse(STAGE/f'{NAME}.xml').find("string[@id='name']").get('value')==NAME
sums={str(p.relative_to(STAGE)).replace('\\','/'):sha(p)for p in sorted(STAGE.rglob('*'))if p.is_file()and p.name!='SHA256SUMS.txt'};(STAGE/'SHA256SUMS.txt').write_text(''.join(f'{h}  {rel}\n'for rel,h in sums.items()),encoding='utf-8')
package=pins(STAGE)
with zipfile.ZipFile(TEMP,'x',zipfile.ZIP_DEFLATED,compresslevel=1)as z:
 for p in sorted(STAGE.rglob('*')):
  if p.is_file():z.write(p,NAME+'/'+str(p.relative_to(STAGE)).replace('\\','/'))
with zipfile.ZipFile(TEMP)as z:
 assert z.testzip()is None and set(z.namelist())=={NAME+'/'+rel.replace('\\','/')for rel in package}
 for rel,h in package.items():assert hashlib.sha256(z.read(NAME+'/'+rel.replace('\\','/'))).hexdigest()==h
assert pins(original)==pins(source)==before and pins(private)==after and sha(Path(freeze['original_X18_ZIP']))==freeze['original_X18_ZIP_SHA256']
assert not PUBLIC.exists()and not ARCHIVE.exists();shutil.copytree(STAGE,PUBLIC)
with TEMP.open('rb')as src,ARCHIVE.open('xb')as out:shutil.copyfileobj(src,out)
assert pins(PUBLIC)==package and sha(ARCHIVE)==sha(TEMP);assert pins(original)==pins(source)==before and pins(private)==after and sha(Path(freeze['original_X18_ZIP']))==freeze['original_X18_ZIP_SHA256']
result=dict(status='LOCAL_TEST_PACKAGE_PREPARED_NOT_EXTERNALLY_UPLOADED',name=NAME,database=str(PUBLIC),archive=str(ARCHIVE),archive_bytes=ARCHIVE.stat().st_size,archive_sha256=sha(ARCHIVE),database_hashes=package,private_source_hashes=after,source_X18_after_SI_hashes=before,source_X18_and_original_ZIP_unchanged=True,native=True,SI=False,new_career=False,season=False,previous_X18_new_career='FAILED_CFA_ARRAY_REMOVE_RANGE',scheduler73_prediction_not_gamePASS=True,counts=counts,patch_fields=12,max_raw_span_bytes=48,independent_publication_inverse=True,artifact_pins_verified=True,external_publication=False,recorded_at=datetime.now(timezone.utc).isoformat(),publisher_sha256=sha(Path(__file__)))
dump(B/'publication.json',result);dump(B/'source-protection-after-publication.json',dict(status='PASS_SOURCE_AND_ARCHIVE_PROTECTED',source=freeze['source'],source_hashes_before=before,source_hashes_after=pins(original),frozen_unchanged=True,private_unchanged=True,X18_ZIP_SHA256=sha(Path(freeze['original_X18_ZIP'])),X19_PublicMatchesStage=True,X19_ZIPReadbackMatchesEveryFile=True))
print('PUBLISHED_LOCAL',NAME,str(PUBLIC),str(ARCHIVE),sha(ARCHIVE),'SI/CAREER/SEASON_PENDING',flush=True)
