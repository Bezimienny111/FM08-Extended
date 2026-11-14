"""Read-only club identity audit for the 18 official Polish II liga 2026/27 entrants."""
import csv,hashlib,json,pathlib,re,shutil,struct,sys,unicodedata,zlib
from datetime import datetime
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
from compare_native_player_tests import controlled_club_span,occurrences
OUT=ROOT/'FmLauncher/data/research/POLAND_II_LIGA_CLUB_AUDIT_20261107';REPO=ROOT/'FM08-Database-Tools'
PZPN='https://pzpn.pl/public/system/files/articles/13822/7388-Terminarz%20Betclic%202%20Ligi%202026-2027.pdf'
STADIA='https://stadiony.net/aktualnosci/2026/07/polska_nowy_sezon_betclic_2_ligi_nowe_stadiony_i_modernizacje_przed_startem'
ENTRANTS=[
 ('Znicz Pruszków','Znicz Pruszkow',None),('Podhale Nowy Targ',None,None),('Lechia Zielona Góra','Lechia Zielona Gora',None),('Rekord Bielsko-Biała',None,None),('Świt Szczecin',None,None),('Górnik Łęczna','Gornik Leczna',None),('Sandecja Nowy Sącz','Sandecja Nowy Sacz',None),('Hutnik Kraków','Hutnik Krakow',None),('Avia Świdnik','Avia Swidnik',None),('Olimpia Grudziądz',None,None),('Legia II Warszawa',None,'Legia Warszawa'),('Stal Stalowa Wola','Stal Stalowa Wola',None),('Zawisza Bydgoszcz','Zawisza Bydgoszcz',None),('Sokół Kleczew',None,None),('Chojniczanka 1930 Chojnice',None,None),('GKS Tychy','GKS Tychy',None),('Resovia Rzeszów','Resovia Rzeszow',None),('Śląsk II Wrocław',None,'WKS Slask Wroclaw')]
MISSING_ALIASES={
 'Podhale Nowy Targ':['Podhale Nowy Targ','NKP Podhale','Szarotka Nowy Targ','Nowy Targ'],
 'Rekord Bielsko-Biała':['Rekord Bielsko','Rekord Lipnik','BTS Rekord'],
 'Świt Szczecin':['Swit Szczecin','Swit Skolwin','Skolwin'],
 'Olimpia Grudziądz':['Olimpia Grudziadz','Grudziadz'],
 'Sokół Kleczew':['Sokol Kleczew','Kleczew'],
 'Chojniczanka 1930 Chojnice':['Chojniczanka','Chojnice']}
CREATION=[
 dict(Name='Chojniczanka 1930 Chojnice',EditorFullName='MKS Chojniczanka 1930 Chojnice',ShortName='Chojniczanka',Abbreviation='CHO',City='Chojnice',Founded='1930-03-10',Colors='żółty / biały / czerwony',Stadium='Stadion Miejski Chojniczanka 1930',Capacity=3000,Address='ul. Mickiewicza 12, Chojnice',Source='https://www.olimpiagrudziadz.com/informacje-z-klubu/nasz-rywal-chojniczanka-chojnice/',StadiumSource='https://archiwum2.miastochojnice.pl/stadion_miejski_chojnice-2376/'),
 dict(Name='Olimpia Grudziądz',EditorFullName='Olimpia Grudziądz',ShortName='Olimpia Grudziądz',Abbreviation='OLI',City='Grudziądz',Founded='1923-06-30',Colors='biały / zielony',Stadium='Stadion Miejski im. Bronisława Malinowskiego',Capacity=5323,Address='ul. Piłsudskiego 14, Grudziądz',Source='https://www.olimpiagrudziadz.com/klub/',StadiumSource='https://www.olimpiagrudziadz.com/stadion/'),
 dict(Name='Rekord Bielsko-Biała',EditorFullName='BTS Rekord Bielsko-Biała',ShortName='Rekord',Abbreviation='REK',City='Bielsko-Biała',Founded='1994',Colors='biały / zielony',Stadium='Stadion Rekordu Bielsko-Biała',Capacity=660,Address='ul. Startowa 13, Bielsko-Biała',Source='https://bts.rekord.com.pl/klub/historia',ColorsSource='https://www.laczynaspilka.pl/biblioteka/ppns/artykuly/futsal-rekord-bielsko-biala',StadiumSource=STADIA,Notes='Pojemność 660 według zestawienia sezonowego z 22.07.2026; starsze źródła podają inne wartości.'),
 dict(Name='Podhale Nowy Targ',EditorFullName='NKP Podhale Nowy Targ',ShortName='Podhale',Abbreviation='POD',City='Nowy Targ',Founded='2009-09-25',Colors='czerwony / niebieski / żółty',Stadium='Stadion Miejski im. Józefa Piłsudskiego',Capacity=900,Address='ul. Kolejowa 161, Nowy Targ',Source='https://nkp.podhale.pl/historia/',ColorsSource='https://www.nkppodhale.pl/strony/statut-nkp-podhale',StadiumSource=STADIA,Notes='Piłkarskie NKP powstało w 2009, nie hokejowe Podhale z 1932. Rok2009 jest historyczny, nie przeliczony na kalendarz FM08. Pojemność według zestawienia 22.07.2026.'),
 dict(Name='Sokół Kleczew',EditorFullName='KS Sokół Kleczew',ShortName='Sokół Kleczew',Abbreviation='SOK',City='Kleczew',Founded='1928',Colors='zielony / czerwony / biały',Stadium='Stadion Miejski w Kleczewie',Capacity=800,Address='al. 600-lecia 21, Kleczew',Source='https://kleczew.pl/strona-2426-klub_sportowy_sokol_kleczew.html',StadiumSource='https://kleczew.pl/strona-2426-klub_sportowy_sokol_kleczew.html',Notes='Barwy ogólne według gminy; klub nazywa pierwszy zespół także biało-zielonym. To nie kompletny wzór strojów2026/27.'),
 dict(Name='Świt Szczecin',EditorFullName='KS Świt Szczecin',ShortName='Świt Szczecin',Abbreviation='SWI',City='Szczecin',Founded='1952',Colors='niebieski / biały',Stadium='Obiekt Sportowy Skolwin',Capacity=909,Address='ul. Stołczyńska 104, Szczecin',Source='https://swit.szczecin.pl/informacje/',StadiumSource=STADIA,Notes='Nie zastępować istniejącego Świtu Nowy Dwór Mazowiecki. Pojemność 909 według zestawienia22.07.2026, stadion jest modernizowany.')]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def load(folder,name):
 raw=(folder/name).read_bytes();d=zlib.decompressobj();s=d.decompress(raw[9:])+d.flush();assert d.eof and not d.unused_data and not d.unconsumed_tail;return s
def norm(s):return unicodedata.normalize('NFKD',s.replace('ł','l').replace('Ł','L')).encode('ascii','ignore').decode().casefold()
def save(path,value):
 with path.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def writecsv(path,rows,columns):
 with path.open('x',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore');w.writeheader();w.writerows(rows)
assert not (OUT/'report.json').exists(),'Refuse overwrite completed audit'
dbs=[];all_mapping=[];participants=[]
for db,relative in [('802','data/updates/update-802/db/802'),('2627_V25','Dane/db/2627_V25')]:
 folder=ROOT/relative;before=json.loads((OUT/f'{db}-hashes-before.json').read_text(encoding='utf-8-sig'));pins={x['Path']:x['SHA256'] for x in before}
 assert pins=={str(p.relative_to(folder)):sha(p) for p in folder.rglob('*') if p.is_file()},'Source changed since first hash'
 with (OUT/f'{db}-snapshot.csv').open(encoding='utf-8-sig',newline='') as f:records={int(x['ClubIndex']):x for x in csv.DictReader(f)}
 assert len(records)==(23394 if db=='802' else 23397)
 assert {x['SourceServerSHA256'].upper() for x in records.values()}=={pins['server_db.dat']}
 server=load(folder,'server_db.dat');people=load(folder,'people_db.dat');pc=struct.unpack_from('<i',people)[0]
 # Independent name/family join. Bytes+7/+8 of this marker are colours and may be nonzero.
 families=[];byindex={};names=[]
 for m in re.finditer(re.escape(bytes.fromhex('ff00006c070000')),server):
  a=m.start();n=struct.unpack_from('<i',server,a+9)[0]
  if not 0<=n<=120 or server[a+13+2*n:a+15+2*n]!=b'\0\0':continue
  try:name=server[a+13:a+13+2*n].decode('utf-16-le')
  except UnicodeError:continue
  if any(ord(c)<32 for c in name):continue
  pos=a+15+2*n;ln=struct.unpack_from('<i',server,pos)[0]
  if not 0<=ln<=120 or server[pos+4+2*ln:pos+6+2*ln]!=b'\0\0':continue
  short=server[pos+4:pos+4+2*ln].decode('utf-16-le');tail=pos+6+2*ln;colors=server[tail]
  if colors>8:continue
  fam=tail+1+11*colors;count=server[fam]
  if not 1<=count<=20:continue
  indices=list(struct.unpack_from('<'+'i'*count,server,fam+1))
  if len(set(indices))!=len(indices) or not all(i in records for i in indices):continue
  entry=dict(name=name,short_name=short,marker_offset=a,family_offset=fam,members=indices)
  families.append(entry);names.append(name)
  for position,i in enumerate(indices):
   assert i not in byindex,'Ambiguous family mapping'
   byindex[i]=entry
   all_mapping.append(dict(Database=db,ClubIndex=i,ClubUID=int(records[i]['ClubUID']),FamilyName=name,FamilyPosition=position,FamilySize=count,NameOffset=a,FamilyOffset=fam,CurrentDivisionIndex=int(records[i]['CurrentDivisionIndex'])))
 assert set(byindex)==set(records),'Name/family scan does not cover all native clubs'
 mapped=[];missing=[];reserves=[]
 for name,alias,parent in ENTRANTS:
  row=dict(Database=db,Season='2026/27',Team=name,Status='',ClubIndex='',ClubUID='',NativeName='',CurrentDivisionIndex='',ParentClubIndex='',ParentClubUID='')
  wanted=alias or parent
  if wanted:
   hits=[x for x in families if norm(x['name'])==norm(wanted)];assert len(hits)==1,(name,wanted,hits)
   family=hits[0];index=family['members'][0];record=records[index];uid=int(record['ClubUID'])
   start,end=controlled_club_span(server,index,pc);assert struct.unpack_from('<ii',server,end-8)==(index,uid)
   assert struct.unpack_from('<i',server,start+7)[0]==int(record['CurrentDivisionIndex'])
   ref=struct.unpack_from('<i',server,end-22)[0]
   expected_identity=struct.pack('<ii',ref,uid)
   assert expected_identity in server[family['marker_offset']:family['marker_offset']+2048],(name,'NAME-TREE UID verification')
   proof=dict(name=name,native_name=family['name'],club_index=index,club_uid=uid,tree_reference=ref,family_members=family['members'],marker_offset=family['marker_offset'],family_offset=family['family_offset'],native_start=start,native_end=end)
   if parent:
    assert len(family['members'])==1,'Existing reserve member requires review'
    children=[]
    for pos in occurrences(server,struct.pack('<ii',9,ref)):
     footer=pos+18;ci,cu=struct.unpack_from('<ii',server,footer)
     if ci in records and int(records[ci]['ClubUID'])==cu:children.append(ci)
    assert not children,'Existing reserve child found'
    row.update(Status='reserve_record_required',ParentClubIndex=index,ParentClubUID=uid,NativeName=family['name'])
    proof['dedicated_reserve_children']=children;reserves.append(proof)
   else:
    row.update(Status='existing',ClubIndex=index,ClubUID=uid,NativeName=family['name'],CurrentDivisionIndex=int(record['CurrentDivisionIndex']))
    mapped.append(proof)
  else:
   searched=MISSING_ALIASES[name];hits=[x for x in families if any(norm(alias) in norm(x['name']) for alias in searched)]
   assert not hits,(name,'Possible alternative identity found',hits)
   row['Status']='new_club_required';missing.append(dict(name=name,searched_aliases=searched,matched_families=0))
  participants.append(row)
 assert (len(mapped),len(missing),len(reserves))==(10,6,2)
 after={str(p.relative_to(folder)):sha(p) for p in folder.rglob('*') if p.is_file()};assert after==pins
 dbs.append(dict(database=db,path=str(folder),native_club_count=len(records),independently_named_club_indices=len(byindex),all_clubs_covered=True,mapped=mapped,missing=missing,reserves=reserves,input_hashes=pins,input_hashes_after=after,inputs_unchanged=True))
# Same identities in both databases; division assignment alone does not decide whether a club exists.
assert {(x['name'],x['club_uid']) for x in dbs[0]['mapped']}=={(x['name'],x['club_uid']) for x in dbs[1]['mapped']}
writecsv(OUT/'participants-2026-27.csv',participants,list(participants[0]))
writecsv(OUT/'club-family-identity-map.csv',all_mapping,list(all_mapping[0]))
checklist=[]
for x in CREATION:
 row=dict(EntityType='club',Country='Poland',TemporaryDivisionUID=129560,TemporaryDivision='Polish Lower Division',NewClubUID='',ParentClubUID='',CapacityReference='2026/27 reference; check before final realism update')
 row.update(x);checklist.append(row)
for name,parent,uid,city,stadium in [('Legia II Warszawa','Legia Warszawa',1456,'Warszawa','Legia Training Center (Książenice)'),('Śląsk II Wrocław','WKS Slask Wroclaw',1300885,'Wrocław','Stadion Śląska, ul. Oporowska')]:
 checklist.append(dict(EntityType='reserve_team',Name=name,EditorFullName=name,ShortName=name,Abbreviation='LII' if uid==1456 else 'SII',Country='Poland',City=city,Founded='',Colors='odziedziczone po klubie macierzystym',TemporaryDivisionUID=129560,TemporaryDivision='Polish Lower Division',NewClubUID='',ParentClubUID=uid,ParentClub=parent,Stadium=stadium,Capacity='',Source=PZPN,StadiumSource=STADIA,Notes='Powiązana druga drużyna klubu, nie niezależny nowy klub. Sprawdzić mechanizm rezerw generowanych przez grę; audyt dotyczy trwałych rekordów bazy.'))
columns=['EntityType','Name','EditorFullName','ShortName','Abbreviation','Country','City','Founded','Colors','TemporaryDivisionUID','TemporaryDivision','NewClubUID','ParentClubUID','ParentClub','Stadium','Capacity','Address','Source','ColorsSource','StadiumSource','CapacityReference','Notes']
writecsv(OUT/'manual-creation-checklist.csv',checklist,columns)
save(OUT/'creation-data.json',dict(status='ready_for_manual_editor_preparation',new_clubs=CREATION,reserve_teams=checklist[-2:],country='Poland',temporary_division_uid=129560,formal_new_league_uid=None,stadium_existence_in_database='not_audited',city_existence_in_database='not_audited',capacity_reference_date='2026-07-22',abbreviations_and_editor_display_names='proposed_not_external_identifiers',no_squads_or_staff_required_for_identity_fixture=True))
save(OUT/'report.json',dict(status='club_identity_audit_verified_manual_entities_pending',season='2026/27',source=PZPN,checked_at=datetime.now().astimezone().isoformat(),reference_database='802',comparison_database='2627_V25',databases=dbs,expected_teams=18,existing_first_teams=10,missing_first_teams=6,reserve_records_required=2,warning='A persistent reserve CLUB record and a runtime generated reserves team are different; never duplicate the parent first team.',read_only=True,game_pilot_passed=False,source_files_modified=False,legacy_reader_missing_names=904,independent_family_name_coverage='100% native club indices for both inputs',next_input='new saved SI database with 6 clubs and 2 linked reserve teams, then re-audit actual UIDs'))
# Concise user checklist, with sources next to the data they support.
lines=['# II liga 2026/27 — kluby do przygotowania w edytorze','',
 'Audyt czystej8.0.2 i2627_V25: **10 istniejących pierwszych zespołów, 6 brakujących klubów i 2 potrzebne rekordy rezerw**. Wynik tożsamości jest taki sam w obu bazach; różnią się bieżące przypisania ligowe.',
 '',f'Skład18 zespołów potwierdza [oficjalny terminarz PZPN]({PZPN}). Porównano23 394 rekordy w8.0.2 oraz23 397 wV25. Niezależny odczyt nazw i rodzin klubowych objął100% tych rekordów. Potwierdzono UID i strukturę istniejących celów; nie opierano decyzji na nazwach wpisanych na sztywno w starym czytniku.','',
 '## Jak przygotować próbkę','',
 'Otwórz w SI kopię oryginalnej bazy **8.0.2** i zapisz jako **TEST_POL_3_LEVEL_CLUBS**. Źródła802 iV25 pozostaw bez zmian. Przygotuj poniższe6 klubów oraz2 powiązane drugie drużyny. To etap uzupełnienia rekordów, jeszcze bez nowej grywalnej ligi.',
 '',
 'Dla sześciu klubów ustaw kraj i kraj bazowy Polska oraz właściwe miasto. Jako tymczasowe rozgrywki wybierz **Polish Lower Division, UID129560**. Nowa grywalna liga dostanie osobny rekord później. Nie wybieraj obecnego Polish Second Division129559: to historyczny drugi poziom.',
 '',
 'UID nowych rekordów pozostaw edytorowi. Nie zmieniaj UID istniejących klubów i nie przenoś jeszcze istniejącej dziesiątki. Proponowane krótkie nazwy i trzyliterowe skróty służą wygodnemu rozpoznaniu, nie są identyfikatorami PZPN.',
 '',
 '## Sześć nowych klubów','',
 '| Nazwa do pola pełnej nazwy | Krótka / skrót | Miasto | Założony | Barwy |',
 '|---|---|---|---|---|']
for x in CREATION:lines.append(f"| {x['EditorFullName']} | {x['ShortName']} / {x['Abbreviation']} | {x['City']} | {x['Founded']} | {x['Colors']} |")
lines+=['','Daty są rzeczywistymi datami klubów. **NKP Podhale:25.09.2009** według jego własnej historii;1932 dotyczy hokejowego Podhala. Nie zamieniono dat założenia na arbitralne daty z kalendarza2007. Nie zgadywano dnia ani miesiąca tam, gdzie potwierdzony jest sam rok.',
 '',
 'Barwy to ogólne kolory klubowe, nie pełna rekonstrukcja wzorów wszystkich kompletów strojów2026/27. Gmina Kleczew podaje zielono-czerwono-białe, a sam Sokół określa drużynę także jako biało-zieloną.','',
 'Źródła: '+', '.join(f"[{x['Name']}]({x['Source']})" for x in CREATION)+'.',
 '',
 'Dodatkowo: [barwy Podhala — statut](https://www.nkppodhale.pl/strony/statut-nkp-podhale), [Rekord — materiał PZPN przygotowany przez klub](https://www.laczynaspilka.pl/biblioteka/ppns/artykuly/futsal-rekord-bielsko-biala).','',
 '## Stadiony','',
 'Najpierw wyszukaj istniejący stadion i miasto w SI. Poniższa lista podaje docelowe powiązania; **nie jest audytem braku stadionów ani miast w bazie**. Nie twórz ich ponownie, jeżeli odpowiedni obiekt już istnieje.','',
 '| Klub | Stadion | Adres | Pojemność odniesienia |',
 '|---|---|---|---:|']
for x in CREATION:lines.append(f"| {x['Name']} | {x['Stadium']} | {x['Address']} | {x['Capacity']} |")
lines+=['',f'Pojemności Podhala900, Świtu909 i Rekordu660 pochodzą z [zestawienia na sezon2026/27 z22.07.2026]({STADIA}); są wartościami odniesienia z tej daty. Starsze strony podają inne pojemności, a część obiektów jest modernizowana. Chojnice3000 potwierdza [miasto](https://archiwum2.miastochojnice.pl/stadion_miejski_chojnice-2376/), Grudziądz5323 [klub](https://www.olimpiagrudziadz.com/stadion/), Kleczew800 [gmina](https://kleczew.pl/strona-2426-klub_sportowy_sokol_kleczew.html).',
 '',
 '## Dwie drugie drużyny','',
 '| Drużyna | Istniejący klub macierzysty | UID rodzica | Docelowy stadion |',
 '|---|---|---:|---|',
 '| Legia II Warszawa | Legia Warszawa |1456| Legia Training Center, Książenice |',
 '| Śląsk II Wrocław | WKS Slask Wroclaw |1300885| Stadion Śląska, ul.Oporowska, Wrocław |',
 '',
 'Potrzebne są **powiązane drugie drużyny**, zachowujące wspólny klub macierzysty. Nie twórz drugiej niezależnej Legii Warszawa ani drugiego Śląska. W obu bazach rodzina każdego z tych klubów ma obecnie tylko jeden rekord. Nie znaleziono też trwałego rekordu rezerw z odniesieniem do ich NAME-TREE. Gra może dodatkowo generować rezerwy podczas uruchomienia; to nie potwierdza obecności oddzielnego uczestnika w bazie.',
 '',
 'Powiązanie rezerw jest istotne dla wspólnej kadry i ograniczeń awansu. Jeśli edytor nie pozwala utworzyć powiązanej drugiej drużyny, zapisz przygotowane6 klubów i pozostaw rezerwy nieutworzone; nie zastępuj ich niezależnymi klubami. To osobny brak do rozwiązania przed pełnym pilotem.',
 '',
 '## Dziesięć istniejących klubów — nie tworzyć ponownie','',
 '| Uczestnik2026/27 | Nazwa w8.0.2 | UID klubu | Indeks CLUB |',
 '|---|---|---:|---:|']
for x in dbs[0]['mapped']:lines.append(f"| {x['name']} | {x['native_name']} | {x['club_uid']} | {x['club_index']} |")
lines+=['',
 'Świt Nowy Dwór Mazowiecki nie jest Świtem Szczecin. Inne kluby o nazwie Rekord, Sokół, Olimpia lub Podhale nie są automatycznie odpowiednimi celami.',
 '',
 '## Zakres pierwszej próbki','',
 'Na tym etapie wystarczą tożsamość klubu, kraj/miasto, stadion i tymczasowe rozgrywki oraz poprawne relacje rezerw. Zawodnicy, trenerzy, kontrakty, finanse i dokładne reputacje będą osobnym zakresem. Pozostaw nieuzupełnione wartości domyślne; nie wprowadzaj budżetów ani reputacji jako rzekomo sprawdzonych danych.',
 '',
 'Po zapisie i ponownym otwarciu w SI potrzebny będzie świeży audyt nowej bazy:6 nowych UID klubów, ewentualne2 UID rezerw i ich rodzice, brak duplikatów oraz hashe chronionych danych. Dopiero te UID można wpisać do prototypu reguł.',
 '',
 'Przeniesienie istniejących klubów do nowej ligi będzie wymagało zbilansowania dotychczasowych rozgrywek; tego nie wykonano w próbce tożsamości. Gra nie została uruchomiona, baza testowa nie powstała automatycznie.',
 '',
 '## Pliki','',
 '- `participants-2026-27.csv`:pełna18-osobowa lista klubów i status dla obu baz.',
 '- `manual-creation-checklist.csv`:pola do edytora dla6 klubów i2 rezerw.',
 '- `creation-data.json`:dane, źródła i pola niepotwierdzone.',
 '- `club-family-identity-map.csv`:niezależne powiązania nazw z wszystkimi rekordami CLUB.',
 '- `report.json`:dowody UID, zakres wyszukiwań i kontrola hashy źródeł.',
 '- `802-snapshot.csv`, `2627_V25-snapshot.csv`:świeże eksporty wspólnego czytnika. Nazwy ze starego parsera są tylko pomocnicze.',
 '',
 'Pierwsze dwie próby wywołania przez PowerShell nie dały poprawnego eksportu (Add-Type nie obsłużył EXE, następnie Invoke otrzymał PSObject). Właściwe audyty wykonał sprawdzony ExportNativeClubSnapshot.exe. Puste pliki `*-club-records.csv`, jeśli obecne, nie są dowodem i nie były użyte w porównaniu.']
text='\n'.join(lines)+'\n';(OUT/'KLUBY_DO_UTWORZENIA.md').write_text(text,encoding='utf-8')
(OUT/'README.md').write_text(text,encoding='utf-8')
doc=REPO/'docs/POLAND_II_LIGA_CLUB_AUDIT.md';assert not doc.exists();doc.write_text(text,encoding='utf-8')
save(OUT/'pilot-preparation.json',dict(status='awaiting_manual_club_fixture',source='data/updates/update-802/db/802',expected_si_fixture='Dane/db/TEST_POL_3_LEVEL_CLUBS',new_clubs=6,linked_reserve_records=2,expected_teams=18,target_new_league_uid=None,existing_club_uids=[x['club_uid'] for x in dbs[0]['mapped']],resource_package_status='not_built_waiting_for_verified_entity_UIDs',first_pilot=['league_and_club_selection','preserved_existing_Polish_competitions','34_matchweeks_306_matches','save_and_reload'],modern_player_import=False))
entry=REPO/'IMPORTER_AKTUALNY_SCHEMAT_I_ZASADY.md';old=entry.read_bytes();entry.write_bytes(old+('''\r\n\r\n## 23. II liga2026/27 — audyt uczestników przed prototypem\r\n\r\n[Lista do edytora](docs/POLAND_II_LIGA_CLUB_AUDIT.md): w802 iV25\r\n10 istniejących klubów,6 nowych i2 potrzebne rekordy rezerw Legii/Śląska.\r\nPełne pokrycie rekordów CLUB przez niezależne nazwy/rodziny i kontrola UID.\r\nNie zapisano zmian w bazach. Użytkownik tworzy brakujące obiekty ręcznie\r\nw kopii802; zalecana próbka TEST_POL_3_LEVEL_CLUBS, potem świeży audyt UID.\r\nTymczasowe rozgrywki nowych obiektów:129560, nie129559. Nie duplikować\r\nrodziców rezerw ani Świtu Nowy Dwór Mazowiecki. Brak gotowego pakietu\r\nzasobów/pilota; mapowanie UID nowych uczestników czeka na próbkę SI.\r\nMateriały: POLAND_II_LIGA_CLUB_AUDIT_20261107.\r\n''').encode('utf-8'))
archive=OUT/'source-snapshot';archive.mkdir();shutil.copy2(pathlib.Path(__file__),archive/pathlib.Path(__file__).name);shutil.copy2(doc,archive/doc.name)
save(archive/'manifest.json',dict(source_only=True,files=[dict(path=p.name,sha256=sha(p)) for p in archive.iterdir() if p.is_file()]))
print(json.dumps(dict(status='verified',existing=10,new_clubs=6,reserve_records=2,databases=[x['database'] for x in dbs],all_native_clubs_named=True,source_hashes_unchanged=True,checklist=str(OUT/'KLUBY_DO_UTWORZENIA.md')),ensure_ascii=True))
