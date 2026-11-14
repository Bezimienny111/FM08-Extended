"""Publish the verified X14 native candidate: metadata only, archive and hash readback."""
from pathlib import Path
from collections import Counter
import csv,json,hashlib,shutil,zipfile,xml.etree.ElementTree as E
ROOT=Path('J:/FM08dev');B=Path(__file__).resolve().parent
SOURCE=B/'rated-db';WORK=B/'release-ready'/'TEST_X14';PUBLIC=ROOT/'Dane/db/TEST_X14';ARCHIVE=ROOT/'wydania/TEST_X14.zip';TEMPZIP=B/'release-ready/TEST_X14.zip'
NAME='TEST_X14'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def dump(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def pins(p):return{str(x.relative_to(p)):sha(x)for x in sorted(p.rglob('*'))if x.is_file()}
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8-sig',newline='')))
def main():
 ready=read(B/'native-ready-for-root-review.json');sourcepins=ready['output_hashes'];master=read(B/'manifest.json')
 assert ready['status']=='PRIVATE_NATIVE_VERIFIED_READY_FOR_ROOT_PUBLICATION_REVIEW'and ready['native']is True
 assert ready['counts']['prepared']==7533 and ready['counts']['new']==6384 and ready['counts']['loans']==289
 assert SOURCE.resolve()==Path(ready['private_output']).resolve()and pins(SOURCE)==sourcepins
 for rel,value in read(B/'final-artifact-pins.json').items():assert sha(B/rel)==value,('artifact_pin',rel)
 roster=read(B/'prepared/independent-verification.json');ratings=read(B/'ratings-patch-independent.json');structure=read(B/'structure-regional-root/root-independent-verification.json')
 assert roster['status']==ratings['status']=='pass'
 for key in ['entire_PEOPLE_inverse_passed','entire_SERVER_inverse_passed','entire_CLIENT_inverse_passed','all_old_attributes_personalities_identical','all_other_DAT_support_identical']:assert roster[key]is True,key
 for key in ['inverse_entire_PEOPLE','only_CA_PA_words_changed','all_17B_and_89B_tables_unchanged','all_other_files_identical']:assert ratings[key]is True,key
 assert ratings['scoped_UIDs']==71 and ratings['CA_changed']==70 and ratings['PA_changed']==63 and ratings['output_hashes']==sourcepins
 assert structure['status']=='PASS_PRIVATE_NATIVE_STRUCTURE_NOT_SI_OR_RUNTIME'and len(structure['both_forms'])==36
 assert all(x['passed']for x in structure['both_forms'])and structure['project_families_SugarDaddy_OFF']==385
 assert all(x['rejected']for x in read(B/'negative-tests-r2.json'))
 original=Path(master['source']);assert pins(original)==master['source_hashes'],'Frozen accepted X11 changed'
 assert not WORK.exists()and not PUBLIC.exists()and not ARCHIVE.exists()and not TEMPZIP.exists(),'Never overwrite an existing release'
 for p in [WORK,PUBLIC,ARCHIVE,TEMPZIP]:assert p.resolve().is_relative_to(ROOT.resolve())
 ledger=rows(B/'final-native-player-UID-ledger.csv');clubs=rows(B/'prepared/club_map.csv');loans=rows(B/'prepared/loans.csv')
 assert len(ledger)==7533 and len({x['UID']for x in ledger})==7533 and len(clubs)==292 and len(loans)==289
 countries={x['TeamIndex']:x['Country']for x in clubs};subjects={x['SubjectID']:countries[x['PlayingTEAM']]for x in ledger};stats=[]
 for country in ['Portugal','Norway','Peru']:
  people=[x for x in ledger if countries[x['PlayingTEAM']]==country];stats.append(dict(country=country,clubs=sum(x['Country']==country for x in clubs),players=len(people),new=sum(str(x['New']).lower()=='true'for x in people),loans=sum(subjects[x['SubjectID']]==country for x in loans)))
 WORK.parent.mkdir(exist_ok=True);shutil.copytree(SOURCE,WORK)
 oldxml=WORK/'roster-db.xml';assert oldxml.is_file()and len(list(WORK.glob('*.xml')))==1
 tree=E.fromstring(oldxml.read_bytes());tree.find("./string[@id='name']").set('value',NAME);tree.find("./string[@id='description']").text=NAME
 xml=WORK/(NAME+'.xml');oldxml.rename(xml);xml.write_bytes(E.tostring(tree,encoding='utf-8',xml_declaration=True))
 assert tree.find("./string[@id='required_version']").get('value')=='8.0.2'
 readme='''TEST_X14 — paczka testowa FM08 8.0.2

STATUS: kontrola natywna PASS. Zapis SI, nowa kariera i przejście sezonu: NIEPOTWIERDZONE.

Instalacja
Wypakuj katalog TEST_X14 do folderu db w katalogu danych użytkownika FM08.
W tym projekcie: J:/FM08dev/Dane/db/TEST_X14.
Baza wymaga nowej kariery. Nie aktualizuje istniejącego zapisu gry.

Zakres
Portugalia, Norwegia i Peru: aktualizacja 292 klubów, 7533 zawodników i 289 wypożyczeń.
Polska: przegląd luk w 126 klubach i kontrola 2456 istniejących UID; nie dopisywano fikcyjnych osób.
Nowe oszacowania CA/PA mają większy, odtwarzalny rozrzut oraz margines rozwoju zależny od wieku.
71 wcześniejszych profili szacunkowych otrzymało selektywną korektę CA/PA.

Test
1. Otwórz TEST_X14 w edytorze SI 8.0.2, zapisz bazę i zamknij edytor.
2. Uruchom zwykły fm.exe i utwórz nową karierę: Portugalia i Norwegia po trzy dostępne poziomy, Peru najwyższy poziom.
3. Sprawdź dostępność krajów, zakończenie tworzenia, tabele, terminarze oraz przykładowe kadry i wypożyczenia.
4. Zapisz osobny punkt kontrolny, następnie sprawdź przejścia sezonów (np. urlop do 1 lipca 2008).

Test bazy wykonujemy w klasycznym FM08. Wersja launchera R2 ma osobno zgłoszony błąd interfejsu.
Instrukcja, zakres i jawne luki: RAPORT_TEST_X14.txt. Hashe: manifest.json oraz SHA256SUMS.txt.
'''
 (WORK/'README.md').write_text(readme,encoding='utf-8')
 report=['TEST_X14 — zakres i status wydania testowego','', 'Podstawa: zaakceptowana TEST_X11 po zapisie SI i nowej karierze.','Kontrole natywne i końcowy odczyt: PASS. Test SI / nowej kariery / sezonu dla X14: OCZEKUJĄ.','', 'Klasyczne obsady FM08: Portugalia16+16+4x14; Norwegia14+16+4x14; Peru12.', 'Razem186 miejsc grywalnych; pozostałe106 klubów katalogu w niższych pulach.','']
 for x in stats:report.append(x['country']+': '+str(x['clubs'])+' klubów, '+str(x['players'])+' osób, '+str(x['new'])+' nowych UID, '+str(x['loans'])+' wypożyczeń.')
 report+=['','Łącznie7533 osób:6384nowe/1149reuse;289wypożyczeń.','86nowychTEAM,61rodzin,187stadionów;385projektowychrodzinSugarDaddyOFF.','ModelCA/PA:squad-spread-2026-27-v2;trwałyseed,bezponownychlosowań.','71selektywnychkorektlegacy:70CA/63PA;PA nieobniżono, wiarygodneFC27 i wcześniejsze talenty chronione.','54nowe przydziały talentów;udokumentowane reguły20%klubów i pasma wysokiegoPA.','','Jawne ograniczenia:','76odłożonych kandydatów;744luk źródłowych;nie szukano brakujących osób na siłę.','1514dawnych rekordów bez zweryfikowanych dat/ocen zachowano;nie czyszczono nieudowodnionych formatów.','Jedna kadra katalogu pozostaje structural_only; silnik może uzupełnić niedobory.','Polska:126klubów/2456UID sprawdzone;16brakówDOB pozostaje.','Daty nowych profili przesunięte o19lat do kalendarzaFM08;17zweryfikowanych starych profili z literalnym realDOB skorygowano dokładnie raz.','Nowe osobowości zapisane poprawionym kodekiem; istniejących osobowości nie obracano masowo.','Brak obowiązku wykupu; nieznanych kwot opcji nie wymyślano.','RosenborgII zachowuje własną rodzinę2336; kontrakty wskazują natywną rodzinęRosenborg1025.','Povoense:usunięto jedno stare regionalne przypisanie48->-1, zachowując main49 i pozostałe dane.','','Weryfikacja:','7negatywnych kontroli PASS;pilot1320osób/195loans, pełnyimport i niezależny inverse PEOPLE/SERVER/CLIENT PASS.','7533/7533 końcoweCA/PA/DOB/właściciel zgodne zplanem; wszystkie stare17B/89B zachowane.','36kontroli min/max obu formularzy struktur; dostępność po rzeczywistym loaderze gry wymaga testu użytkownika.','Kopie źródłowe i zaakceptowane bazy nie zostały nadpisane.','','Wersja: TEST_X14, przygotowana11listopada2026.']
 (WORK/'RAPORT_TEST_X14.txt').write_text('\n'.join(report)+'\n',encoding='utf-8')
 dbpins=pins(WORK)
 for rel,value in sourcepins.items():
  if rel not in ['README.md','roster-db.xml']:assert dbpins[rel]==value,('unexpected_data_change',rel)
 manifest=dict(name=NAME,required_game_version='8.0.2',release_stage='native_verified_test_candidate',prepared_date='2026-11-11',base='TEST_X11 after accepted SI/new career',native_verified=True,SI_verified=False,new_career_verified=False,season_verified=False,countries=stats,counts=ready['counts'],new_TEAM=86,new_families=61,new_stadiums=187,sugar_daddy_off_project_families=385,new_talent_awards=54,poland=dict(clubs_reviewed=126,existing_UIDs_checked=2456,DOB_gaps_retained=16),native_file_hashes=dbpins)
 dump(WORK/'manifest.json',manifest)
 sums=pins(WORK);(WORK/'SHA256SUMS.txt').write_text(''.join(v+'  '+k.replace('\\','/')+'\n'for k,v in sums.items()),encoding='utf-8')
 packagepins=pins(WORK)
 with zipfile.ZipFile(TEMPZIP,'x',zipfile.ZIP_DEFLATED,compresslevel=1)as z:
  for rel in sorted(packagepins):z.write(WORK/rel,NAME+'/'+rel.replace('\\','/'))
 with zipfile.ZipFile(TEMPZIP)as z:
  assert z.testzip()is None
  assert set(z.namelist())=={NAME+'/'+r.replace('\\','/')for r in packagepins}
  for rel,value in packagepins.items():assert hashlib.sha256(z.read(NAME+'/'+rel.replace('\\','/'))).hexdigest()==value,('archive_readback',rel)
 assert pins(SOURCE)==sourcepins and pins(original)==master['source_hashes']
 shutil.copytree(WORK,PUBLIC);assert pins(PUBLIC)==packagepins
 ARCHIVE.parent.mkdir(exist_ok=True)
 with TEMPZIP.open('rb')as incoming,ARCHIVE.open('xb')as outgoing:shutil.copyfileobj(incoming,outgoing,1048576)
 assert sha(ARCHIVE)==sha(TEMPZIP)and pins(PUBLIC)==packagepins
 result=dict(status='LOCAL_TEST_PACKAGE_PREPARED_NOT_EXTERNALLY_UPLOADED',name=NAME,database=str(PUBLIC),archive=str(ARCHIVE),archive_bytes=ARCHIVE.stat().st_size,archive_sha256=sha(ARCHIVE),database_hashes=packagepins,private_source_unchanged=True,accepted_X11_snapshot_unchanged=True,metadata_only_changes=True,all_native_data_files_identical_to_verified_rated_db=True,native=True,SI=False,new_career=False,season=False,countries=stats,counts=ready['counts'],root_review='PASS',external_publication=False)
 dump(B/'publication.json',result)
 master.update(status='TEST_X14_LOCAL_PACKAGE_READY_NATIVE_VERIFIED_SI_GAME_PENDING',output=str(PUBLIC),archive=str(ARCHIVE),output_database_created=True,native=True,SI=False,new_career=False,season=False,publication=str(B/'publication.json'),output_hashes=packagepins)
 dump(B/'manifest.json',master)
 print(json.dumps({k:v for k,v in result.items()if k not in ['database_hashes']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()