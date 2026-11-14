# Metadata-only packaging, reusing the X15 copy/hash/ZIP/readback procedure.
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,csv,hashlib,shutil,zipfile,xml.etree.ElementTree as ET
ROOT=Path('J:/FM08dev');B=Path(__file__).resolve().parent;NAME='TEST_X16'
SOURCE=B/'rated-db';WORK=B/'release-ready'/NAME;PUBLIC=ROOT/'Dane/db'/NAME
TEMP=B/'release-ready'/f'{NAME}.zip';ARCHIVE=ROOT/'wydania'/f'{NAME}.zip'
COUNTRIES=['South Korea','Colombia','Israel','Iceland','Northern Ireland','Ireland']
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def pins(p):return{str(x.relative_to(p)):sha(x)for x in sorted(p.rglob('*'))if x.is_file()}
def rows(p):
 with Path(p).open(encoding='utf-8-sig',newline='')as f:return list(csv.DictReader(f))
def main():
 ready=read(B/'native-ready-for-root-review.json');master=read(B/'manifest.json');rawcounts=ready['counts']
 counts=dict(rawcounts,prepared=int(rawcounts['people']),reuse=int(rawcounts['reused']))
 assert ready['status']=='PRIVATE_NATIVE_VERIFIED_READY_FOR_ROOT_PUBLICATION_REVIEW'and ready['native']is True
 n=int(counts['prepared']);assert n==int(counts['new'])+int(counts['reuse'])and n>4000
 assert SOURCE.resolve()==Path(ready['private_output']).resolve()
 expected=ready['output_hashes'];assert pins(SOURCE)==expected
 for rel,h in read(B/'final-artifact-pins.json').items():assert sha(B/rel)==h,('artifact',rel)
 roster=read(B/'prepared/independent-verification.json');rating=read(B/'ratings-patch-independent.json');final=read(B/'final-readback.json')
 assert roster['status']==rating['status']==final['status']=='pass'
 assert roster['players']==n and roster['added']==int(counts['new'])and roster['loans']==int(counts['loans'])
 for k in ['entire_PEOPLE_inverse_passed','entire_SERVER_inverse_passed','entire_CLIENT_inverse_passed','all_old_attributes_personalities_identical','all_other_DAT_support_identical']:assert roster[k]is True,k
 for k in ['inverse_entire_PEOPLE','only_CA_PA_words_changed','all_17B_and_89B_tables_unchanged','all_other_files_identical']:assert rating[k]is True,k
 assert rating['scoped_UIDs']==counts['legacy_rating_repairs']and rating['CA_changed']==counts['legacy_CA_changed']and rating['PA_changed']==counts['legacy_PA_changed']
 assert rating['output_hashes']==expected and final['rated_hashes']==expected
 assert final['all_imported_CA_PA_DOB_owner_verified']and final['UID_and_TMID_unique']and final['counts']['people']==n
 structure=read(B/'structure-root/root-independent-verification.json')
 assert structure['status']=='PASS_PRIVATE_NATIVE_STRUCTURE_NOT_SI_OR_RUNTIME'
 assert len(structure['both_forms'])==58 and all(x['passed']for x in structure['both_forms'])
 assert structure['new_TEAM']==33 and structure['new_families']==33 and structure['new_stadiums']==124 and structure['project_families_SugarDaddy_OFF']==462
 q=B/'root-selection-qa';qa=read(q/'regression.json');qp=read(q/'pins.json');delta=read(q/'global-count-scope-readback.json')
 assert qp['ReportSHA256']==sha(q/'regression.json')and qa['Status']=='NUMERIC_SELECTION_REGRESSION_PASS'
 assert len(qa['Checks'])==215 and all(x['after_passed']for x in qa['Checks'])
 assert not qa['NewRegressions']and not qa['NewCountryNullTeams']and not qa['NewCountryNullParticipants']
 assert qa['SwedenRawInputsAndCountriesPreserved']and delta['AllOtherCompetitionCountersBothFormsUnchanged']and delta['ReportSHA256']==sha(q/'regression.json')
 for path,h in qp['Inputs'].items():assert sha(path)==h,('QAinput',path)
 for path,h in qa['EvidencePins'].items():assert sha(path)==h,('QAevidence',path)
 assert all(x['rejected']and x['output_not_created']for x in read(B/'negative-tests.json'))
 frozen=Path(master['source']);accepted=Path(master['source_original']);sourcepins=master['source_hashes']
 assert pins(frozen)==sourcepins and pins(accepted)==sourcepins
 assert not any(x.exists()for x in [WORK,PUBLIC,TEMP,ARCHIVE]),'Never overwrite a release'
 for x in [WORK,PUBLIC,TEMP,ARCHIVE]:assert x.resolve().is_relative_to(ROOT.resolve())
 people=rows(B/'final-native-player-UID-ledger.csv');clubs=rows(B/'prepared/club_map.csv');loans=rows(B/'prepared/loans.csv')
 assert len(people)==len({x['UID']for x in people})==n and len(clubs)==counts['clubs']and len(loans)==counts['loans']
 assert set(x['Country']for x in clubs)==set(COUNTRIES)
 bysubject={x['SubjectID']:x['Country']for x in people};stats=[]
 for c in COUNTRIES:
  ps=[x for x in people if x['Country']==c]
  stats.append(dict(country=c,clubs=sum(x['Country']==c for x in clubs),players=len(ps),new=sum(x['New'].lower()=='true'for x in ps),loans=sum(bysubject[x['SubjectID']]==c for x in loans)))
 assert sum(x['players']for x in stats)==n
 native={rel:h for rel,h in expected.items()if Path(rel).suffix.lower()in ['.dat','.edt','.lnc']}
 assert all(Path(rel).suffix.lower()in ['.dat','.edt','.lnc','.xml','.json','.txt','.md']for rel in expected)
 xmls=list(SOURCE.glob('*.xml'));assert len(xmls)==1
 tree=ET.fromstring(xmls[0].read_bytes());assert tree.find("./string[@id='required_version']").get('value')=='8.0.2'
 tree.find("./string[@id='name']").set('value',NAME);tree.find("./string[@id='description']").text=NAME
 WORK.mkdir(parents=True)
 for rel,h in native.items():
  dest=WORK/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SOURCE/rel,dest);assert sha(dest)==h
 (WORK/f'{NAME}.xml').write_bytes(ET.tostring(tree,encoding='utf-8',xml_declaration=True))
 text=f'''TEST_X16 - FM08 8.0.2

Korea Poludniowa, Kolumbia, Izrael, Islandia, Irlandia Polnocna, Irlandia.
Podstawa: zaakceptowana TEST_X15 po SI i nowej karierze; jej test przejscia
sezonu i niemieckiej3.Ligi zostal potwierdzony przez uzytkownika.

STATUS X16: Native PASS. SI / nowa kariera / sezon: NIEPOTWIERDZONE.
{n} profili, {counts['new']} nowychUID, {counts['loans']} wypozyczen.
{counts['clubs']} klubow w planie; kadry niepelne i luki sa jawne.
SugarDaddy OFF we wszystkich462projektowychrodzinach.

Test zbiorczy:
1. Otworz TEST_X16 w edytorze SI8.0.2, zapisz i zamknij edytor.
2. Utworz nowa kariere w FM08 z wszystkimi dostepnymi poziomami szesciu
   wymienionych krajow. Sprawdz wybor krajow, zakonczenie tworzenia,
   tabele, terminarze, przykladowe kadry i wypozyczenia.
3. Zachowaj osobny save kontrolny. Na kopii sprawdz przejscie sezonu,
   zwlaszcza islandzkie rozszerzenie Premier10do12 wraz z terminarzem.
   Test sezonu pozostaje osobny od SI i pierwszego dnia kariery.

Baza wymaga nowej kariery. Lokalnie: J:/FM08dev/Dane/db/TEST_X16.
Paczka nie zawiera grafik ani nowych funkcji launchera.
Szczegoly zmian i luk: RAPORT_TEST_X16.txt, manifest.json.
'''
 (WORK/'README.md').write_text(text,encoding='utf-8')
 report='TEST_X16 - wydanie testowe szesciu krajow\nNativePASS. SI/kariera/sezonPENDING. Dane DAT/EDT/LNC identyczne z finalnie sprawdzona rated-db.\n\n'
 report+='Podstawa: zaakceptowana X15 po SI i nowej karierze. X15 i jej ZIP zachowane bez zmian.\n\n'
 for x in stats:report+=f"{x['country']}: {x['clubs']} klubow, {x['players']} profili, {x['new']} nowych UID, {x['loans']} wypozyczen.\n"
 report+=f'''\nLacznie {n} profili: {counts['new']} nowychUID i {counts['reuse']} reuse.
{counts['actor_clubs']} klubow z kadrami oraz14czesciowych klubow granicznych;181klubow planu.
Korea14+12; Kolumbia18+18; Izrael12+12; Islandia10->12+12;
IrlandiaPolnocna16+12+12; Irlandia12+10.170miejsc startowych,172poekspansji.
Klasyczne zasadyFM08 zachowane; EXE i reguly silnika bez zmian.

33noweTEAM/33FAMILY/124stadiony;462rodziny projektu SugarDaddyOFF.
33luki stadionowe zachowane bez wymyslania obiektow lub miejscowosci.
{counts['deferred']} odlozonych kandydatow;{counts['source_gaps']} luk zrodlowych.
Brakujacych zawodnikow nie szukano na sile; silnik moze uzupelnic kadry.
7technicznych miejsc nizszej puliNI wypelniono istniejacymi klubami,
z jawnie niepotwierdzonym wspolczesnym przydzialem i zachowaniem minimow.

CA/PA:modelv2, odtwarzalny indywidualny rozrzut i margines rozwoju.
{counts['legacy_rating_repairs']} dowiedzionych starych szacunkow skorygowano
({counts['legacy_CA_changed']}CA/{counts['legacy_PA_changed']}PA), bez obnizaniaPA.
{counts['new_talent_awards']} nowych przydzialow talentu. Wiarygodne oceny chronione.
Pozostale atrybuty/osobowosci/tozsamosci/umowy zachowane wedlug inverse.
353aktywne wypozyczenia z potwierdzonym wlascicielem, takze miedzynarodowe.
Bez obowiazku wykupu i zgadywania nieznanych cen. Realne daty zachowane
w ewidencji; natywne starty aktywnych loan korzystaja z granicy1VII2007.
Daty osob przesuniete19lat tylko wedlug potwierdzonego planu.

Tozsamosci: Alianza309345Kolumbia, Uruguay5512639chroniona;
RealCundinamarca8830832Valledupar; Cartagenaosobno. Gwangju/Gimcheonosobno.
Kerry/Treaty/Strabane noweencje; Galway zachowuje oficjalna ciagloscsportowa
z jawnym odnotowaniem projektu prawnego2013. Nie zgadywano rokuKiryatGat.
Odlozenia Ludogorets, Kolding/Voufack/Cejudo i poprzednie role rezerw
opisane w next-batch-fixes.json oraz X15_CARRIED_FORWARD_GAPS.json.

Kontrole:6negatywnych przypadkow,Pilot688,Full4467 i caly inverse
PEOPLE/SERVER/CLIENT PASS;0future-conflicts. Patchocen ma calyPEOPLEinverse.
Kazdy finalnyUID/CA/PA/DOB/owner ponownie odczytany.
58kontroli obu form dla6krajow oraz215warunkow selektorow PASS;
0nowychregresji,0nowychuczestnikow bezkraju,14Swedenoverlayowzachowane.
To kontrola danych, nie potwierdzenie runtime wszystkich krajow.
Poprawiony prywatny readerNATION odczytuje229etykiet; daneNATION/PEOPLE
nie byly zmieniane w celu obejscia braku etykiet w starym skanie9.0-9.6MB.

Nastepny krok: jeden zbiorczy zapisSI i nowa kariera ze wszystkimi6krajami.
Testsezonu osobno, w szczegolnosci islandzkie Premier10->12/terminarz.
Nie aktualizuje istniejacej kariery. Grafiki, sztaby i nowe panele launchera
nie sa czescia tego wydania danych. Archiwum utworzone tylko lokalnie.
'''

 (WORK/'RAPORT_TEST_X16.txt').write_text(report,encoding='utf-8')
 inherited={}
 for name in ['next-batch-fixes.json','native-reserve-role-gaps.json']:
  if (SOURCE/name).exists():inherited[name]=read(SOURCE/name)
  if (B/name).exists():shutil.copy2(B/name,WORK/name)
 if inherited:dump(WORK/'X15_CARRIED_FORWARD_GAPS.json',inherited)
 manifest=dict(name=NAME,required_game_version='8.0.2',prepared_date='2026-11-12',release_stage='native_verified_test_candidate',base='accepted TEST_X15 after SI',native_verified=True,SI_verified=False,new_career_verified=False,season_verified=False,countries=stats,counts=counts,structure=ready['structure'],classic_counts=master['classic_counts'],new_talent_awards=counts['new_talent_awards'],numeric_regression=dict(checks=215,new_country_form_checks=58,new_regressions=0,live_test_pending=True),native_file_hashes=native)
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
 result=dict(status='LOCAL_TEST_PACKAGE_PREPARED_NOT_EXTERNALLY_UPLOADED',name=NAME,database=str(PUBLIC),archive=str(ARCHIVE),archive_bytes=ARCHIVE.stat().st_size,archive_sha256=sha(ARCHIVE),database_hashes=package,native=True,SI=False,new_career=False,season=False,accepted_X15_unchanged=True,private_source_unchanged=True,all_native_data_identical=True,countries=stats,counts=counts,external_publication=False)
 dump(B/'publication.json',result)
 master.update(status='TEST_X16_SIX_COUNTRY_LOCAL_PACKAGE_READY_SI_GAME_PENDING',output=str(PUBLIC),archive=str(ARCHIVE),output_database_created=True,native=True,SI=False,new_career=False,season=False,output_hashes=package,publication=str(B/'publication.json'))
 dump(B/'manifest.json',master)
 print(json.dumps({k:v for k,v in result.items()if k!='database_hashes'},ensure_ascii=True,indent=2))
if __name__=='__main__':main()
