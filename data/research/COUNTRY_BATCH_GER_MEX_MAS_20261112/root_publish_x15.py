# Package verified X15; only release metadata changes.
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,csv,hashlib,shutil,zipfile,xml.etree.ElementTree as E
ROOT=Path('J:/FM08dev');B=Path(__file__).resolve().parent;NAME='TEST_X15'
SOURCE=B/'rated-db';WORK=B/'release-ready'/NAME;PUBLIC=ROOT/'Dane/db'/NAME
TEMPZIP=B/'release-ready'/f'{NAME}.zip';ARCHIVE=ROOT/'wydania'/f'{NAME}.zip'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def dump(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def pins(p):return {str(x.relative_to(p)):sha(x)for x in sorted(p.rglob('*'))if x.is_file()}
def rows(p):
 with Path(p).open(encoding='utf-8-sig',newline='')as f:return list(csv.DictReader(f))
def main():
 ready=read(B/'native-ready-for-root-review.json');master=read(B/'manifest.json')
 assert ready['status']=='PRIVATE_NATIVE_VERIFIED_READY_FOR_ROOT_PUBLICATION_REVIEW'and ready['native']is True
 assert ready['counts']['prepared']==5785 and ready['counts']['new']==3210 and ready['counts']['loans']==232
 sourcepins=ready['output_hashes'];assert SOURCE.resolve()==Path(ready['private_output']).resolve()and pins(SOURCE)==sourcepins
 for rel,value in read(B/'final-artifact-pins.json').items():assert sha(B/rel)==value,('artifact_pin',rel)
 roster=read(B/'prepared/independent-verification.json');ratings=read(B/'ratings-patch-independent.json');final=read(B/'final-readback.json');structure=read(B/'structure-root/root-independent-verification.json');qa=read(B/'root-selection-regression-r2.json')
 assert roster['status']==ratings['status']==final['status']=='pass'
 for key in ['entire_PEOPLE_inverse_passed','entire_SERVER_inverse_passed','entire_CLIENT_inverse_passed','all_old_attributes_personalities_identical','all_other_DAT_support_identical']:assert roster[key]is True,key
 for key in ['inverse_entire_PEOPLE','only_CA_PA_words_changed','all_17B_and_89B_tables_unchanged','all_other_files_identical']:assert ratings[key]is True,key
 assert ratings['scoped_UIDs']==184 and ratings['CA_changed']==180 and ratings['PA_changed']==32 and ratings['output_hashes']==sourcepins
 assert final['rated_hashes']==sourcepins and final['all5785_CA_PA_DOB_owner_verified']and final['UID_and_TMID_unique']
 assert final['deferred_EricVoufack1608001583_all_audit_fields_unchanged']
 assert structure['status']=='PASS_PRIVATE_NATIVE_STRUCTURE_NOT_SI_OR_RUNTIME'and len(structure['both_forms'])==36
 assert all(x['passed']for x in structure['both_forms'])and structure['project_families_SugarDaddy_OFF']==429
 assert qa['status']=='NUMERIC_REGRESSION_PASS_INHERITED_COUNTRY_GAPS'
 assert len(qa['checks'])==157 and all(x['after_passed']for x in qa['checks']) and qa['inherited_country_gaps_unchanged'] and not qa['new_country_null_participants']
 assert all(x['rejected']and x['output_not_created']for x in read(B/'negative-tests.json'))
 original=Path(master['source']);accepted=Path(master['source_original']);assert pins(original)==master['source_hashes']and pins(accepted)==master['source_hashes']
 assert not any(x.exists()for x in [WORK,PUBLIC,ARCHIVE,TEMPZIP]),'Never overwrite an existing release'
 for x in [WORK,PUBLIC,ARCHIVE,TEMPZIP]:assert x.resolve().is_relative_to(ROOT.resolve())
 ledger=rows(B/'final-native-player-UID-ledger.csv');clubs=rows(B/'prepared/club_map.csv');loans=rows(B/'prepared/loans.csv')
 assert len(ledger)==len({x['UID']for x in ledger})==5785 and len(clubs)==215 and len(loans)==232
 subjects={x['SubjectID']:x['Country']for x in ledger};stats=[]
 for country in ['Germany','Mexico','Malaysia']:
  people=[x for x in ledger if x['Country']==country]
  stats.append(dict(country=country,clubs=sum(x['Country']==country for x in clubs),players=len(people),new=sum(x['New'].lower()=='true'for x in people),loans=sum(subjects[x['SubjectID']]==country for x in loans)))
 excluded={'manifest.json','README.md','RAPORT_TEST_X14.txt','SHA256SUMS.txt','roster-db.xml'}
 datafiles={r:v for r,v in sourcepins.items()if Path(r).suffix.lower()in ['.dat','.edt','.lnc']}
 assert set(sourcepins)-set(datafiles)==excluded,'Unreviewed private output file type'
 WORK.mkdir(parents=True)
 for rel in datafiles:
  target=WORK/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SOURCE/rel,target)
 tree=E.fromstring((SOURCE/'roster-db.xml').read_bytes());tree.find("./string[@id='name']").set('value',NAME);tree.find("./string[@id='description']").text=NAME
 assert tree.find("./string[@id='required_version']").get('value')=='8.0.2'
 (WORK/f'{NAME}.xml').write_bytes(E.tostring(tree,encoding='utf-8',xml_declaration=True))
 readme='''TEST_X15 - FM08 8.0.2: Niemcy, Meksyk, Malezja

Native PASS. SI / nowa kariera / sezon: NIEPOTWIERDZONE.
Podstawa: TEST_X14 po zaakceptowanym zapisie SI i nowej karierze.
Instalacja lokalna: J:/FM08dev/Dane/db/TEST_X15. Baza wymaga nowej kariery.

215 klubow,5785 profili (3210 nowych UID/2575reuse),232 wypozyczenia.
CA/PA: model indywidualnego rozrzutu i rozwoju;184 stare szacunki
skorygowane (180CA/32PA), wiarygodne profile chronione.
Obsady: Niemcy18+18+19+18, Meksyk18+24, Malezja13+13.
Sugar Daddy OFF we wszystkich429 projektowych rodzinach.

Test zbiorczy:
1. Otworz TEST_X15 w edytorze SI8.0.2, zapisz i zamknij edytor.
2. W zwyklym FM08 wybierz TEST_X15 oraz wszystkie dostepne poziomy
   Niemiec, Meksyku i Malezji. Sprawdz kraje, utworzenie kariery,
   tabele, terminarze, kadry i wypozyczenia. Launcher nie jest wymagany.
3. Zachowaj osobny save; sprawdz niemieckie przejscie do sezonu2008/09
   i natywne uruchomienie3.Ligi. NativePASS nie potwierdza tego przejscia.

Luki:75odlozonych kandydatow,80luk zrodlowych,52stadionowe.
JDTII/SelangorII: zachowano stare typy native, fizyczna konwersja do
B-team pozostaje luka. Szczegoly: RAPORT_TEST_X15.txt i oba pliki gaps/fixes.
Dostepnosc krajow wymaga testu w grze. ZIP nie zawiera grafik.
'''
 (WORK/'README.md').write_text(readme,encoding='utf-8')
 report=(B/'RAPORT.md').read_text(encoding='utf-8')
 report=report.replace('Prywatna baza gotowa do publikacji przez root: '+str(SOURCE),'Baza testowa lokalna: '+str(PUBLIC))
 report+='\nPublikacja root: tylko metadane/XML. Wszystkie DAT/EDT/LNC zgodne bitowo z rated-db. SI/kariera/sezon oczekuja; brak wysylki do uslug zewnetrznych.\n'
 (WORK/f'RAPORT_{NAME}.txt').write_text(report,encoding='utf-8')
 for rel in ['next-batch-fixes.json','native-reserve-role-gaps.json']:shutil.copy2(B/rel,WORK/rel)
 for rel,value in datafiles.items():assert sha(WORK/rel)==value,('native_copy',rel)
 manifest=dict(name=NAME,required_game_version='8.0.2',prepared_date='2026-11-12',release_stage='native_verified_test_candidate',base='TEST_X14 after accepted SI/new career',native_verified=True,SI_verified=False,new_career_verified=False,season_verified=False,countries=stats,counts=ready['counts'],structure=ready['structure'],classic_counts=master['classic_counts'],new_talent_awards=27,native_role_gaps=ready['native_role_gaps'],numeric_regression=dict(checks=157,failed=0,inherited_country_null_participants=47,runtime_test_pending=True),native_file_hashes=datafiles)
 dump(WORK/'manifest.json',manifest)
 sums=pins(WORK);(WORK/'SHA256SUMS.txt').write_text(''.join(v+'  '+r.replace('\\','/')+'\n'for r,v in sums.items()),encoding='utf-8')
 packagepins=pins(WORK)
 with zipfile.ZipFile(TEMPZIP,'x',zipfile.ZIP_DEFLATED,compresslevel=1)as z:
  for rel in sorted(packagepins):z.write(WORK/rel,NAME+'/'+rel.replace('\\','/'))
 with zipfile.ZipFile(TEMPZIP)as z:
  assert z.testzip()is None
  assert set(z.namelist())=={NAME+'/'+r.replace('\\','/')for r in packagepins}
  for rel,value in packagepins.items():assert hashlib.sha256(z.read(NAME+'/'+rel.replace('\\','/'))).hexdigest()==value,('archive_readback',rel)
 assert pins(SOURCE)==sourcepins and pins(original)==master['source_hashes']and pins(accepted)==master['source_hashes']
 shutil.copytree(WORK,PUBLIC);assert pins(PUBLIC)==packagepins
 ARCHIVE.parent.mkdir(exist_ok=True)
 with TEMPZIP.open('rb')as source,ARCHIVE.open('xb')as target:shutil.copyfileobj(source,target,1048576)
 assert sha(ARCHIVE)==sha(TEMPZIP)and pins(PUBLIC)==packagepins
 result=dict(status='LOCAL_TEST_PACKAGE_PREPARED_NOT_EXTERNALLY_UPLOADED',name=NAME,database=str(PUBLIC),archive=str(ARCHIVE),archive_bytes=ARCHIVE.stat().st_size,archive_sha256=sha(ARCHIVE),database_hashes=packagepins,native=True,SI=False,new_career=False,season=False,accepted_X14_unchanged=True,private_source_unchanged=True,all_native_data_identical=True,countries=stats,counts=ready['counts'],external_publication=False)
 dump(B/'publication.json',result)
 master.update(status='TEST_X15_LOCAL_PACKAGE_READY_NATIVE_VERIFIED_SI_GAME_PENDING',output=str(PUBLIC),archive=str(ARCHIVE),output_database_created=True,output_version=NAME,native=True,SI=False,new_career=False,season=False,output_hashes=packagepins,publication=str(B/'publication.json'))
 dump(B/'manifest.json',master)
 print(json.dumps({k:v for k,v in result.items()if k!='database_hashes'},ensure_ascii=True,indent=2))
if __name__=='__main__':main()
