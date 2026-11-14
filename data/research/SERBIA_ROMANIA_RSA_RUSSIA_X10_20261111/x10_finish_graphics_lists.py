"""Record user acceptance and publish a new X10 graphics list snapshot without DB writes."""
from x10_pipeline import *
import csv,xml.etree.ElementTree as ET
G=B/'graphics-delta';I=G/'installation';O=R/'GRAPHICS_LISTS_X10_20261111'
def rows(path,delimiter=','):return list(csv.DictReader(Path(path).open(encoding='utf-8-sig',newline=''),delimiter=delimiter))
def writecsv(path,fields,values):
 with path.open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.DictWriter(f,fieldnames=fields,delimiter=';');w.writeheader();w.writerows(values)
def acceptance():
 evidence=dict(date='2026-11-11',user_response='baza dla tych4krajów działa',source='User response relayed by root to combined SI+new-career test',SI=True,new_career=True,season=False,raw_SI_file_audit_performed=False)
 observed=pins(ROOT/'Dane/db/TEST_X10')
 dump(B/'SI-user-acceptance.json',dict(**evidence,observed_post_SI_hashes=observed,hash_scope='Read-only observation after user acceptance; native inverse pins retained separately'))
 for file in [B/'manifest.json',B/'publication.json']:
  data=read(file);data.update(SI=True,new_career=True,season=False,user_acceptance=evidence,observed_post_SI_hashes=observed,output_hashes_scope='Original independently verified native publication before user SI save',status='native_SI_new_career_pass_season_pending');dump(file,data)
 data=read(I/'installation-result.json');data.update(status='installed_independently_verified',independent_verification=str(I/'independent-verification.json'));dump(I/'installation-result.json',data)
 data=read(I/'manifest.json');data.update(incident=read(I/'incident.json'),download_failed_clubs=[dict(uid='1800110081',name='North West University',TMID='142733',reason='Source image URL returns HTTP404; no replacement invented')]);dump(I/'manifest.json',data)
 p=I/'REPORT.md';text=p.read_text(encoding='utf-8');text+='\nIncydent i dokładne odtworzenie: podczas zapisu baseline błędnie użyta zmienna p spowodowała zapis JSON do jednego starego config.xml flag narodowych. Instalacja zatrzymała się przed instalowaniem PNG. Wcześniejsza wzmianka o dostępnej kopii była niepotwierdzonym założeniem. Oryginał znaleziono następnie w J:/FM08/Dane/...; odtworzono jego dokładne bajty i potwierdzono SHA256 0982ba6474c050b5029b8445f026da7c9999ab32b6e140e315a5d8e679b1f833. Przed kontynuacją wszystkie 1214 XML i 18810 wcześniejszych PNG miały identyczne hashe z baseline. Pełny ślad w incident.json.\n\nJedno pobranie herbu NWU (TM142733) zwróciło404; klub pozostaje bez nowego herbu. KSE nie miało potwierdzonego URL. Nie użyto obrazów zastępczych.\n';p.write_text(text,encoding='utf-8')
 p=B/'REPORT.md';text=p.read_text(encoding='utf-8');text=text.replace('SI, nowa kariera i sezon: OCZEKUJĄ na test użytkownika, osobne statusy.','SI i nowa kariera: PASS potwierdzone przez użytkownika 11 listopada 2026 („baza dla tych4krajów działa”). Sezon: OCZEKUJE, osobny status.').replace('Status SI/kariera/sezon nadal oczekuje.','Status historyczny eksportu był oczekujący; później użytkownik potwierdził SI i nową karierę. Sezon nadal oczekuje.')
 text+='\n## Grafiki zainstalowane\n\nX10: 1798 nowych zdjęć i 152 nowe herby (normal180 oraz small20), niezależne sprawdzenie PNG/map/hashów PASS. Razem modern_2627: 19000 zdjęć i 956 herbów w każdym rozmiarze. Zachowano wszystkie wcześniejsze grafiki. NWU404 i KSE bez URL pozostają jawnymi lukami. Raport i pełny incydent z dokładnym odtworzeniem jednego configu: graphics-delta/installation/REPORT.md i incident.json. Bazy nie zmieniano przy instalacji grafik.\n';p.write_text(text,encoding='utf-8')
 (B/'WZNOWIENIE.md').write_text('# TEST_X10 — native, SI i nowa kariera PASS\n\nSerbia/Rumunia/RPA/Rosja: 154 kluby, 4230 osób, 317 wypożyczeń. Native/pilot/inverse PASS. Użytkownik 11 listopada 2026 potwierdził: „baza dla tych4krajów działa” (SI i nowa kariera PASS). Sezon oczekuje. Nie powtarzać testów SI/kariery bez nowego powodu.\n\nPubliczna Dane/db/TEST_X10 zawiera zapis SI użytkownika — NIE NADPISYWAĆ. Oryginalne piny natywne publication.json/output_hashes zachowane, hashobserwacja po SI i akceptacja oddzielnie SI-user-acceptance.json. Tożsamości i mapy UID w prepared/full-native.json dotyczą zweryfikowanego zapisu natywnego przed SI. X8 niezmieniona; X9/Tajlandia odłożone. CA/PA oceniane przez osobnego agenta, bez zmian DB w tej sesji.\n\nGrafiki X10 zainstalowane: 1798 zdjęć i 152 herby normal180/small20; modern_2627 łącznie 19000/956/956. Kontrole niezależne PASS; NWU404 i KSE bez URL jawne luki. Raport graphics-delta/installation/REPORT.md, dodane UID added-UIDs.json. Błąd zapisu baseline do starego configu flag odtworzono dokładnie z oryginału i potwierdzono wszystkie poprzednie1214XML/18810PNG przed kontynuacją; pełny dowód incident.json. Bez DB/launchera/cache/reload.\n',encoding='utf-8')
def lists():
 assert read(I/'independent-verification.json')['status']=='pass'
 assert not O.exists();O.mkdir()
 oldp=R/'FACEPACK_NEW_PLAYERS_20261111/LISTA_FACEPACK_UID_IMIE_NAZWISKO_KLUB.csv';oldc=R/'CLUB_GRAPHICS_20261111/LISTA_KLUBOW_UID_NAZWA_LIGA.csv'
 previous=rows(oldp,';');delta=rows(G/'newplayers.csv',';');oldclubs=rows(oldc,';');cm=rows(B/'prepared/club_map.csv');full=read(B/'prepared/full-native.json');proof=read(B/'prepared/manifest.json')
 assert len(previous)==12625 and len(delta)==2822 and len(oldclubs)==804 and len(cm)==154
 people={x['UID']:x for x in previous};assert len(people)==len(previous)
 for x in delta:assert x['UID']not in people;people[x['UID']]=x
 byti={int(x['TeamIndex']):x for x in cm};world=rows(B/'world-club-identities.csv')+rows(B/'foreign-owner-map.csv')+cm;ownerbyti={int(x['TeamIndex']):x for x in world};ledger=[];updates=[]
 for x in full['subjects']:
  uid=str(x['uid']);club=byti[x['playing']];owner=ownerbyti.get(x['owner'],{})
  ledger.append(dict(UID=uid,playing_club_UID=club['ClubUID'],playing_club_name=club['ClubName'],owner_club_UID=owner.get('ClubUID'),owner_club_name=owner.get('ClubName')or owner.get('Names'),native_playing_TEAM_index=x['playing'],native_owner_TEAM_index=x['owner'],mapping_scope='verified native pre-SI, not re-audited SI TEAM indices'))
  if uid in people:
   if people[uid]['Klub']!=club['ClubName']:updates.append(dict(uid=uid,before=people[uid]['Klub'],after=club['ClubName']))
   people[uid]['Klub']=club['ClubName']
 retired=set(map(str,full['duplicate_retire_uids']));removed=[]
 for uid in sorted(retired):
  if uid in people:
   assert uid in proof['duplicate_proofs'];removed.append(dict(uid=uid,proof=proof['duplicate_proofs'][uid]));del people[uid]
 faces=ROOT/'Dane/graphics/pictures/faces/normal/modern_2627';config=faces/'config.xml';maps={}
 for n in ET.parse(config).getroot().iter('record'):
  to=n.get('to','')
  if to.startswith('graphics/pictures/person/')and to.endswith('/portrait'):
   uid=to.split('/')[-2];assert uid not in maps;maps[uid]=faces/(n.get('from')+'.png')
 for uid,row in people.items():row['Ma zdjęcie']='TAK'if uid in maps and maps[uid].is_file()else'NIE'
 competitions={x['index']:x for x in read(B/'competition-catalog.json')};country={'Serbia':'Serbia','Romania':'Rumunia','South Africa':'RPA','Russia':'Rosja'};clubs={x['UID']:x for x in oldclubs};assert len(clubs)==804
 for c in cm:
  league=competitions[int(c['DivisionIndex'])]
  clubs[c['ClubUID']]={'UID':c['ClubUID'],'Nazwa klubu':c['ClubName'],'Liga':country[c['Country']]+' — '+league['names'][0]}
 ps=sorted(people.values(),key=lambda x:int(x['UID']));cs=sorted(clubs.values(),key=lambda x:int(x['UID']))
 writecsv(O/'LISTA_FACEPACK_UID_IMIE_NAZWISKO_KLUB.csv',['UID','Imię','Nazwisko','Klub','Ma zdjęcie'],ps);writecsv(O/'LISTA_KLUBOW_UID_NAZWA_LIGA.csv',['UID','Nazwa klubu','Liga'],cs)
 dump(O/'playing-owner-ledger-X10.json',ledger);dump(O/'retired-duplicate-removals.json',removed);dump(O/'playing-club-updates.json',updates)
 inputfiles=[oldp,oldc,G/'newplayers.csv',B/'prepared/full-native.json',B/'prepared/manifest.json',B/'prepared/club_map.csv',config,I/'independent-verification.json']
 manifest=dict(status='complete_new_snapshot_X8_lists_unchanged',source_database='TEST_X10 user SI+new-career accepted; native UID mapping used',people=len(ps),previous_people=len(previous),X10_new_people=len(delta),X10_reused_people_not_added=len(full['subjects'])-len(delta),retired_duplicates_removed=len(removed),club_updates=len(updates),people_with_actual_modern_PNG_and_config=sum(x['Ma zdjęcie']=='TAK'for x in ps),people_without_photo=sum(x['Ma zdjęcie']=='NIE'for x in ps),clubs=len(cs),previous_clubs=len(oldclubs),X10_clubs=len(cm),source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in inputfiles},files=pins(O),photo_status_basis='Existing modern config.xml person/{UID}/portrait target plus linked PNG file, not URL availability',clubs_league_basis='Actual classic FM08 assigned country and division; not invented modern placement',only_proven_new_person_lineage=True,no_DB_mutation=True,no_previous_list_overwrites=True,encoding='UTF8_BOM',delimiter='semicolon')
 dump(O/'manifest.json',manifest)
 (O/'RAPORT.md').write_text('# Listy grafik po X10\n\nZawodnicy: '+str(len(ps))+' (12625 wcześniejszych +2822 nowych X10, usunięte potwierdzone duplikaty: '+str(len(removed))+'). Nie dopisano 1408 ponownie użytych osób spoza pewnej linii nowych rekordów. Klub zaktualizowano według rzeczywistego miejsca gry; właściciele kontraktów osobno w playing-owner-ledger-X10.json.\n\nZdjęcie obecne: '+str(manifest['people_with_actual_modern_PNG_and_config'])+'; brak: '+str(manifest['people_without_photo'])+'. Status sprawdzono na istniejącym PNG i wpisie config.xml.\n\nKluby: '+str(len(cs))+' (804 wcześniejsze +154 X10, deduplikacja UID). Liga oznacza kraj i rzeczywisty przydział klasycznego FM08. Listy UTF8 z BOM, separator średnik. Oryginalnych list X8 ani baz nie nadpisano. Piny wejściowe i wynikowe: manifest.json.\n',encoding='utf-8')
 print('X10 LISTS',dict(people=len(ps),photos=manifest['people_with_actual_modern_PNG_and_config'],clubs=len(cs),club_updates=len(updates),retired_removed=len(removed)),flush=True)
if __name__=='__main__':acceptance();lists()
