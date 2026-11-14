# X17 metadata-only packaging; preserves verified native bytes and accepted X16.
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,csv,hashlib,shutil,zipfile,xml.etree.ElementTree as ET
ROOT=Path('J:/FM08dev')
B=Path(__file__).resolve().parent
NAME='TEST_X17'
COUNTRIES=['Indonesia','India','Hong Kong']
SOURCE=B/'rated-db'
WORK=B/'release-ready'/NAME
PUBLIC=ROOT/'Dane/db'/NAME
TEMP=B/'release-ready'/f'{NAME}.zip'
ARCHIVE=ROOT/'wydania'/f'{NAME}.zip'
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
def main():
 assert __debug__
 ready=read(B/'native-ready-for-root-review.json')
 assert sha(B/'native-ready-for-root-review.json')=='ffdf06d0fd53bd7d06ef7a6e6b88b3ba132a42b5694c50c16dc7ae46042a6f5a'
 master=read(B/'manifest.json')
 rc=ready['counts'];counts=dict(rc)
 counts['prepared']=int(rc.get('prepared',rc.get('people',0)))
 counts['reuse']=int(rc.get('reuse',rc.get('reused',0)))
 n=counts['prepared']
 assert ready['status']=='PRIVATE_NATIVE_VERIFIED_READY_FOR_ROOT_PUBLICATION_REVIEW'and ready['native']is True
 assert n==3555==int(counts['new'])+counts['reuse']
 assert counts['clubs']==133 and counts['loans']==101 and counts['legacy_rating_repairs']==408
 assert SOURCE.resolve()==Path(ready['private_output']).resolve()
 expected=ready['output_hashes'];assert pins(SOURCE)==expected
 for rel,h in read(B/'final-artifact-pins.json').items():assert sha(B/rel)==h,('artifact',rel)
 roster=read(B/'prepared/independent-verification.json')
 rating=read(B/'ratings-patch-independent.json')
 final=read(B/'final-readback.json')
 assert roster['status']==rating['status']==final['status']=='pass'
 assert roster['players']==n and roster['added']==int(counts['new'])and roster['loans']==counts['loans']
 for k in ['entire_PEOPLE_inverse_passed','entire_SERVER_inverse_passed','entire_CLIENT_inverse_passed','all_old_attributes_personalities_identical','all_other_DAT_support_identical']:assert roster[k]is True,k
 for k in ['inverse_entire_PEOPLE','only_CA_PA_words_changed','all_17B_and_89B_tables_unchanged','all_other_files_identical']:assert rating[k]is True,k
 assert rating['scoped_UIDs']==counts['legacy_rating_repairs']
 assert rating['CA_changed']==counts['legacy_CA_changed']and rating['PA_changed']==counts['legacy_PA_changed']
 assert rating['output_hashes']==expected and final['rated_hashes']==expected
 assert final['all_imported_CA_PA_DOB_owner_verified']and final['UID_and_TMID_unique']
 legacy=final['legacy_unsupported_record_preserved']
 assert legacy['UID']==23042954 and legacy['Length']==284 and legacy['WholeRecordIdentical'] and not legacy['ImportedParticipant']
 assert legacy['WholeRecordSHA256']=='b37bb9afadef93fd1941c50cba2d8f4c7874dc16078062b62abf45c389519ba2'
 sentinel=final['sentinel_names_source_after_verified']
 assert len(sentinel)==1 and sentinel[0]['UID']==41001663 and sentinel[0]['TMID']=='206993'
 assert sentinel[0]['NameBlockUnchanged'] and sentinel[0]['PhysicalKnownAs']==sentinel[0]['SourceName']=='Hariono'
 assert int(final['counts'].get('people',final['counts'].get('prepared',0)))==n
 structure=read(B/'structure-root-r2/root-independent-verification.json')
 assert structure['status']=='PASS_PRIVATE_NATIVE_STRUCTURE_NOT_SI_OR_RUNTIME'
 assert len(structure['both_forms'])==18 and all(x['passed']for x in structure['both_forms'])
 assert structure['new_TEAM']==60 and structure['new_families']==60 and structure['new_stadiums']==97
 assert structure['project_families_SugarDaddy_OFF']==522
 q=B/'independent-selection-qa-r2';qa=read(q/'regression.json');qp=read(q/'pins.json')
 assert sha(q/'regression.json')=='cbb32b956b36e378a0ac717fa8dfb875ea7ed968cf61f029f34cf8d0bf31014c'
 witness=read(q/'authorized-alt-cleanup-witness.json')
 assert sha(q/'authorized-alt-cleanup-witness.json')=='1ed635a2fb3c656c169d134cc3dec6dbe822e8143f2366a93f39626102ae34d7'
 assert witness['PreservationPASS'] and witness['OtherTEAMBytesUnchanged'] and witness['FamilyBytesUnchanged'] and witness['PeopleDBUnchanged'] and witness['NamesUnchanged']
 assert len(witness['NegativeCases'])==10 and all(x['Rejected'] for x in witness['NegativeCases'])
 assert witness['OtherSourceCountryNullUIDsRejected']==4419
 assert sha(witness['DecisionPath'])==witness['DecisionSHA256']=='d470f84f6ffce2f0329572aea332eadd836d50f0507423eaa1278e8685fb083a'
 for path,h in witness['InputPins'].items():assert sha(path)==h,('ALT witness',path)
 assert qp['ReportSHA256']==sha(q/'regression.json')and qa['Status']=='NUMERIC_SELECTION_REGRESSION_PASS'
 assert len(qa['Checks'])==233 and qa['CurrentBatchChecks']==18
 for k in ['NewRegressions','CurrentBatchFailures','NewCountryNullTeams','NewCountryNullParticipants','UnexpectedCompetitionCountDeltas','RawSlotScopeFindings','ExistingTEAMCountryChangeFindings']:assert not qa[k],k
 assert qa['SwedenRawInputsAndCountriesPreserved']and qa['SwedenHistoricalOverlaysReplayed']==14
 assert not qa['RawCurrentDeltaMismatch']and all(x['Passed']for x in qa['ProtectedRejectedShortAliases'])
 for path,h in qp['Inputs'].items():assert sha(path)==h,('QAinput',path)
 for path,h in qa['EvidencePins'].items():assert sha(path)==h,('QAevidence',path)
 for item in qa['SourceTargetPins']:
  for rel,h in item['Hashes'].items():assert sha(Path(item['Path'])/rel)==h,('QAdata',rel)
 assert all(x['rejected']and x['output_not_created']for x in read(B/'negative-tests.json'))
 frozen=Path(master['source']);accepted=Path(master['source_original']);sourcepins=master['source_hashes']
 assert pins(frozen)==sourcepins and pins(accepted)==sourcepins
 previous_zip=ROOT/'wydania/TEST_X16.zip'
 assert sha(previous_zip)=='2409147622db43709adbf9859a1ffb3930ab45ea4b954874d369040467c2d899'
 assert not any(x.exists()for x in [WORK,PUBLIC,TEMP,ARCHIVE]),'Never overwrite a release'
 for x in [WORK,PUBLIC,TEMP,ARCHIVE]:assert x.resolve().is_relative_to(ROOT.resolve())
 people=rows(B/'final-native-player-UID-ledger.csv');clubs=rows(B/'prepared/club_map.csv');loans=rows(B/'prepared/loans.csv')
 assert len(people)==len({x['UID']for x in people})==n
 assert len(clubs)==133 and len(loans)==101
 assert set(x['Country']for x in clubs)==set(COUNTRIES)
 bysubject={x['SubjectID']:x['Country']for x in people};stats=[]
 for c in COUNTRIES:
  ps=[x for x in people if x['Country']==c]
  stats.append(dict(country=c,clubs=sum(x['Country']==c for x in clubs),players=len(ps),new=sum(x['New'].lower()=='true'for x in ps),loans=sum(bysubject[x['SubjectID']]==c for x in loans)))
 assert sum(x['players']for x in stats)==n
 hariono=[x for x in people if x['UID']=='41001663']
 assert len(hariono)==1 and hariono[0]['FirstName']=='' and hariono[0]['LastName']=='Hariono'
 native={rel:h for rel,h in expected.items()if Path(rel).suffix.lower()in ['.dat','.edt','.lnc']}
 assert all(Path(rel).suffix.lower()in ['.dat','.edt','.lnc','.xml','.json','.txt','.md']for rel in expected)
 xmls=list(SOURCE.glob('*.xml'));assert len(xmls)==1
 tree=ET.fromstring(xmls[0].read_bytes())
 assert tree.find("./string[@id='required_version']").get('value')=='8.0.2'
 tree.find("./string[@id='name']").set('value',NAME)
 tree.find("./string[@id='description']").text=NAME
 WORK.mkdir(parents=True)
 for rel,h in native.items():
  dest=WORK/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SOURCE/rel,dest);assert sha(dest)==h
 (WORK/f'{NAME}.xml').write_bytes(ET.tostring(tree,encoding='utf-8',xml_declaration=True))
 text=f'''TEST_X17 - FM08 8.0.2
Indonezja, Indie, Hongkong.
Podstawa: zaakceptowana TEST_X16 po zapisie SI i nowej karierze.
Test sezonu X16, w tym ekspansja Islandii, pozostaje niepotwierdzony.

STATUS X17: Native PASS. SI / nowa kariera / sezon: NIEPOTWIERDZONE.
{n} profili, {counts['new']} nowych UID, {counts['loans']} wypozyczen.
133 kluby objete planem. Niepelne kadry i odlozenia sa opisane w raporcie.
Sugar Daddy OFF we wszystkich 522 klubach dodanych w projekcie.

TEST ZBIORCZY:
1. Otworz TEST_X17 w edytorze SI 8.0.2, zapisz i zamknij edytor.
2. Utworz nowa kariere ze wszystkimi dostepnymi poziomami Indonezji,
   Indii oraz Hongkongu: 2 + 1 + 1 poziomy. Sprawdz dostepnosc krajow,
   zakonczenie tworzenia, grupy, tabele, terminarze, kadry i wypozyczenia.
3. Zachowaj osobny zapis kontrolny; na kopii sprawdz kolejny sezon
   tych trzech krajow. To osobny test od uruchomienia nowej kariery.

Klasyczny format: Indonezja Premier 2x18 / First 4x10;
Indie NFL10; Hongkong First10. Wspolczesne nizsze ligi pozostaja
katalogiem klubow w niegrywalnych pulach. Silnik i EXE bez zmian.
Baza wymaga NOWEJ kariery. Nie aktualizuje istniejacych zapisow.
Paczka nie zawiera grafik ani nowych funkcji launchera/generatora.
Szczegoly: RAPORT_TEST_X17.txt, manifest.json.
'''
 (WORK/'README.md').write_text(text,encoding='utf-8')
 report='TEST_X17 - lokalne wydanie testowe\nNative PASS; SI / kariera / sezon PENDING.\n\n'
 for x in stats:report+=f"{x['country']}: {x['clubs']} klubow, {x['players']} profili, {x['new']} nowych UID, {x['loans']} wypozyczen.\n"
 report+=f'''
Razem {n} profili: {counts['new']} nowych i {counts['reuse']} ponownie uzytych.
133 kluby planu; 60 nowych TEAM/FAMILY, 97 nowych stadionow.
522 rodziny utworzone w projekcie: Sugar Daddy OFF, niezalezny odczyt.
{counts['deferred']} odlozonych osob; {counts['source_gaps']} lacznych wpisow luk.
Potwierdzone profile importowane; brakow nie uzupelniamy fikcyjnymi osobami.
69 luk stadionowych zachowano bez wymyslania danych.
Laczne232 wpisy luk obejmuja184 luki zrodlowe i48 odlozonych kandydatow.

CA/PA: model squad-spread-2026-27-v2, indywidualny odtwarzalny rozrzut,
margines rozwoju wedlug wieku i zachowanie wiarygodnych ocen.
{counts['legacy_rating_repairs']} dowiedzionych wczesniejszych szacunkow poprawiono:
{counts['legacy_CA_changed']} zmian CA / {counts['legacy_PA_changed']} zmian PA.
{counts['new_talent_awards']} nowych przydzialow talentu w przygotowaniu tej paczki.
Nie wdrozono eksperymentalnych premii atrybutow nowo generowanych juniorow.
{counts['loans']} wypozyczen, takze miedzynarodowych; wlasciciele potwierdzeni.
Nie dodajemy obowiazkowego wykupu ani nie zgadujemy nieznanych kwot.

OBSADA:
Indonezja: 18 aktualnych Super League i 18 dobranych z nizszych poziomow
w Premier (2x18); First40 (4x10). Zakonczone tabele2025/26 oraz
15 potwierdzonych klubow Liga4 dobranych zgodnie z rankingiem faz.
Indie: NFL10; Chennaiyin, Odisha, SC Delhi do nizszej puli;
promowany Churchill zachowany. Wszystkie32 zrodlowe kluby ujete.
Hongkong: First10; HKFC przesuniety nizej wedlug poprzedniej koncowej
tabeli, Sha Tin zachowany. Wszystkie25 zrodlowych klubow ujete.
Geografia grup i klasyczne wymagania FM08 zachowane.
Aktualne katalogi lig nie zwiekszaja liczby grywalnych poziomow.

TOZSAMOSCI:
Hariono zachowal oryginalny fizyczny rekord; poprawiono odczyt braku imienia.
Dawny nieobslugiwany rekord UID23042954 zachowano w calosci284B,
bez zwalniania ani ponownego tworzenia zawodnika.
Bali/Persisam, Madura/Pelita Jaya, Bhayangkara/Persikubar i Mohun Bagan
oparte na udokumentowanej ciaglosci sportowej; nie deklarujemy niezmiennej
tozsamosci prawnej ani nie przenosimy historii odrebnych klubow.
FC Goa i Sporting de Goa oddzielne. Kendal Tornado, Punjab FC i
Karbi Anglong Morning Star sa osobnymi encjami; historyczne UID1408,
5629894 i1001749 zachowane bez zmian. Persikotas Nusantara nie scalona
z historyczna Persikotas bez dowodu. Pozostale luki jawne w raportach.

KONTROLE:
Cale PEOPLE/SERVER/CLIENT odtworzone odwrotnie; stare atrybuty i osobowosci
chronione. Patch ocen ograniczony do udowodnionych slow CA/PA.
Kazdy finalny UID/CA/PA/DOB/wlasciciel ponownie odczytany.
18kontroli obuform nowych krajow i233niezalezne warunki selektorow;
0nowych regresji,0nowych bezkrajowych uczestnikow,Sweden14 zachowane.
Stockloader Indonezji odtworzony statycznie; akceptacja runtime OCZEKUJE.
Przypisanie grup FAMILY nie wymaga nowego writera.
Wszystkie natywne pliki wydania identyczne z koncowa sprawdzona rated-db.

X16, jej zapis SI i ZIP zachowane. X17 wymaga nowej kariery.
Grafiki i nowe funkcje launchera nie sa czescia paczki.
'''
 (WORK/'RAPORT_TEST_X17.txt').write_text(report,encoding='utf-8')
 inherited={}
 for p in SOURCE.glob('*.json'):
  if p.name in ['next-batch-fixes.json','native-reserve-role-gaps.json']or 'CARRIED_FORWARD_GAPS'in p.name:inherited[p.name]=read(p)
 if inherited:dump(WORK/'X16_CARRIED_FORWARD_GAPS.json',inherited)
 for name in ['next-batch-fixes.json','native-reserve-role-gaps.json']:
  if(B/name).exists():shutil.copy2(B/name,WORK/name)
 manifest=dict(name=NAME,required_game_version='8.0.2',prepared_date='2026-11-13',release_stage='native_verified_test_candidate',base='accepted TEST_X16 after SI and new career; source season not confirmed',native_verified=True,SI_verified=False,new_career_verified=False,season_verified=False,countries=stats,counts=counts,structure=ready['structure'],classic_counts=dict(Indonesia=dict(Premier=[18,18],First=[10,10,10,10]),India=dict(NFL=10),Hong_Kong=dict(First=10)),numeric_regression=dict(checks=233,new_country_form_checks=18,new_regressions=0,inherited_unchanged_failures=qa['InheritedUnchangedFailures'],live_test_pending=True),native_file_hashes=native)
 dump(WORK/'manifest.json',manifest)
 sums=pins(WORK);(WORK/'SHA256SUMS.txt').write_text(''.join(h+'  '+rel.replace('\\','/')+'\n'for rel,h in sums.items()),encoding='utf-8')
 package=pins(WORK)
 with zipfile.ZipFile(TEMP,'x',zipfile.ZIP_DEFLATED,compresslevel=1)as z:
  for rel in sorted(package):z.write(WORK/rel,NAME+'/'+rel.replace('\\','/'))
 with zipfile.ZipFile(TEMP)as z:
  assert z.testzip()is None and set(z.namelist())=={NAME+'/'+r.replace('\\','/')for r in package}
  for rel,h in package.items():assert hashlib.sha256(z.read(NAME+'/'+rel.replace('\\','/'))).hexdigest()==h
 assert pins(SOURCE)==expected and pins(frozen)==sourcepins and pins(accepted)==sourcepins
 shutil.copytree(WORK,PUBLIC);assert pins(PUBLIC)==package
 ARCHIVE.parent.mkdir(exist_ok=True)
 with TEMP.open('rb')as inp,ARCHIVE.open('xb')as out:shutil.copyfileobj(inp,out,1048576)
 assert sha(ARCHIVE)==sha(TEMP)and pins(PUBLIC)==package
 assert sha(previous_zip)=='2409147622db43709adbf9859a1ffb3930ab45ea4b954874d369040467c2d899'
 result=dict(status='LOCAL_TEST_PACKAGE_PREPARED_NOT_EXTERNALLY_UPLOADED',name=NAME,database=str(PUBLIC),archive=str(ARCHIVE),archive_bytes=ARCHIVE.stat().st_size,archive_sha256=sha(ARCHIVE),database_hashes=package,native=True,SI=False,new_career=False,season=False,accepted_X16_unchanged=True,private_source_unchanged=True,all_native_data_identical=True,countries=stats,counts=counts,external_publication=False)
 dump(B/'publication.json',result)
 master.update(status='TEST_X17_LOCAL_PACKAGE_READY_SI_GAME_PENDING',output=str(PUBLIC),archive=str(ARCHIVE),output_database_created=True,native=True,SI=False,new_career=False,season=False,output_hashes=package,publication=str(B/'publication.json'),source_collection=dict(clubs=133,cards=3787,confirmed_candidates=3603,accepted_loan_rows=103,source_gaps=184),counts=counts)
 for k in ['Northern_Ireland_current_season','Northern_Ireland_previous_completed','excluded']:master.pop(k,None)
 dump(B/'manifest.json',master)
 print(json.dumps({k:v for k,v in result.items()if k!='database_hashes'},ensure_ascii=True,indent=2))
if __name__=='__main__':main()
