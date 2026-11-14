"""Freeze 18 existing baseline clubs for the Poland third-tier pilot; no database writes."""
import csv,hashlib,json,pathlib,shutil
from datetime import datetime
ROOT=pathlib.Path(__file__).resolve().parents[2]
OLD=ROOT/'FmLauncher/data/research/POLAND_II_LIGA_CLUB_AUDIT_20261107'
OUT=ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_PILOT_R7_20261107'
BASE=ROOT/'data/updates/update-802/db/802'
REPO=ROOT/'FM08-Database-Tools'
# Explicit selection; none comes from either currently playable Polish division.
SELECTED=[(129565,'Górnik Łęczna'),(3200068,'Hutnik Kraków'),(710017,'Miedź Legnica'),(129564,'KSZO Ostrowiec Świętokrzyski'),(129584,'Górnik Polkowice'),(714236,'Unia Janikowo'),(710008,'Flota Świnoujście'),(1459,'Pogoń Szczecin'),(722134,'Kolejarz Stróże'),(54003081,'Przebój Wolbrom'),(717327,'Radomiak Radom'),(130127,'Stal Rzeszów'),(130153,'TKP Toruń'),(717315,'Zawisza Bydgoszcz'),(717678,'Dolcan Ząbki'),(714214,'Górnik Wieliczka'),(54001643,'GKP Gorzów Wielkopolski'),(54007052,'MKS Kluczbork')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def pins():return {str(p.relative_to(BASE)):sha(p) for p in BASE.rglob('*') if p.is_file()}
def save(p,x):
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
assert not OUT.exists(),'Refuse overwrite selection'
prior=json.loads((OLD/'report.json').read_text(encoding='utf-8'))
proof=next(x for x in prior['databases'] if x['database']=='802')
before=pins();assert before==proof['input_hashes'],'Baseline changed; refresh identity audit before selecting'
with (OLD/'802-snapshot.csv').open(encoding='utf-8-sig',newline='') as f:snapshot={int(x['ClubUID']):x for x in csv.DictReader(f)}
with (OLD/'club-family-identity-map.csv').open(encoding='utf-8-sig',newline='') as f:family={int(x['ClubUID']):x for x in csv.DictReader(f) if x['Database']=='802'}
assert len(snapshot)==len(family)==23394
assert len(SELECTED)==len(set(x[0] for x in SELECTED))==18
rows=[]
for order,(uid,display) in enumerate(SELECTED,1):
 r=snapshot[uid];n=family[uid]
 assert int(r['ClubIndex'])==int(n['ClubIndex']) and int(r['CurrentDivisionIndex'])==int(n['CurrentDivisionIndex'])==141
 assert int(n['FamilyPosition'])==0 and int(n['FamilySize'])==1,'Reserve or complex family requires review'
 assert r['SourceServerSHA256'].upper()==before['server_db.dat']
 assert int(r['RosterSize'])>=5
 rows.append(dict(Order=order,DisplayName=display,NativeName=n['FamilyName'],ClubUID=uid,ClubIndex=int(r['ClubIndex']),ExpectedDivisionUID=129560,ExpectedDivisionIndex=141,TargetDivisionUID='',RosterEntries=int(r['RosterSize']),FamilyPosition=0,FamilySize=1,SelectionRole='technical_pilot_participant'))
protected={str(d):sorted(int(x['ClubUID']) for x in snapshot.values() if int(x['CurrentDivisionIndex'])==d) for d in [139,140]}
assert {k:len(v) for k,v in protected.items()}=={'139':16,'140':18}
assert not set(uid for uid,_ in SELECTED)&set(protected['139']+protected['140'])
lower=[int(x['ClubUID']) for x in snapshot.values() if int(x['CurrentDivisionIndex'])==141]
assert len(lower)==118 and len(set(lower)-{uid for uid,_ in SELECTED})==100
assert before==pins(),'Input changed during preparation'
OUT.mkdir(parents=True)
with (OUT/'participants.csv').open('x',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
manifest=dict(status='existing_club_selection_verified',revision='R7',created_at=datetime.now().astimezone().isoformat(),user_decision='Use existing clubs for now; do not create new clubs or linked reserves',source_database=str(BASE),participant_count=18,participant_uids=[x['ClubUID'] for x in rows],participant_indices=[x['ClubIndex'] for x in rows],source_competition_uid=129560,source_competition_index=141,target_competition_uid=None,target_competition_record_status='not_created',source_lower_pool_count=118,planned_lower_pool_count_after_selection=100,protected_division_counts={'129558':16,'129559':18},protected_division_club_uids=protected,new_clubs=0,new_people=0,new_reserve_teams=0,squad_updates=False,existing_top_two_memberships_unchanged=True,source_hashes=before,source_hashes_after=before,inputs_unchanged=True,database_modified=False,game_executed=False,resource_package_status='not_built',game_pilot_passed=False,blocks_removed=['missing_6_clubs','missing_2_reserve_records','manual_club_fixture'],remaining_work=['competition_record_and_resource_registration_prototype','calendar_and_preserved_existing_competitions','save_load_and_new_career','coordinated_promotion_relegation_playoffs','youth_policy'],scope_note='Technical pilot composition, not the actual II liga2026/27 field. RosterEntries counts raw CLUB members and does not prove active-player or goalkeeper availability.')
save(OUT/'manifest.json',manifest)
save(OUT/'protected-divisions.json',protected)
rules=json.loads((ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_R6_20261107/target-rules.json').read_text(encoding='utf-8'))
rules['participants']={'mode':'existing_baseline_clubs_for_technical_pilot','selection_file':'participants.csv','uids':[x['ClubUID'] for x in rows],'actual_2026_27_composition':False}
rules['new_clubs_required']=False
save(OUT/'target-rules.json',rules)
lines=['# Polska — obsada pilota trzeciego poziomu, R7','',
 'Aktualna decyzja użytkownika: wykorzystujemy istniejące kluby; na tym etapie nie tworzymy nowych klubów ani rezerw. Ten wybór zastępuje oczekiwanie na próbkę TEST_POL_3_LEVEL_CLUBS z wcześniejszego audytu.','',
 'Wybrano18 pierwszych zespołów z czystej bazy8.0.2, wszystkie z Polish Lower Division, UID129560 / indeks141. Są to uczestnicy technicznego pilota; nie jest to rzeczywisty skład II ligi2026/27.','',
 '| Klub do testu | Nazwa w8.0.2 | UID | CLUB index | Wpisy kadrowe |',
 '|---|---|---:|---:|---:|']
for x in rows:lines.append(f"| {x['DisplayName']} | {x['NativeName']} | {x['ClubUID']} | {x['ClubIndex']} | {x['RosterEntries']} |")
lines+=['',
 'Dobór preferuje kluby z większą liczbą wpisów kadrowych; przy podobnej liczbie wybrano rozpoznawalne pierwsze zespoły. Nie ma pustej listy ani wybranej drużyny rezerw. Wpisy CLUB nie są jednak audytem aktywnych piłkarzy, bramkarzy, kontraktów czy emerytur. Kadr nie uzupełniono.','',
 'Zachowano nazwy bazy: TKP Toruń i GKP Gorzów Wielkopolski nie zostały automatycznie przemianowane na współczesne marki. Polskie znaki w DisplayName są etykietami raportu; NativeName zachowuje zapis źródłowy.','',
 '## Kontrola i zakres','',
 '- Sprawdzono wszystkie UID i indeksy względem świeżo potwierdzonych hashy802 oraz niezależnej mapy nazw/rodzin klubowych.',
 '- Wszystkie18 klubów pochodzi z puli118. Po ich wydzieleniu pozostałoby100 klubów w zapleczu.',
 '- Żaden wybrany klub nie należy do obecnych dwóch grywalnych poziomów. Ich obsada16/18 jest chroniona i zapisana w protected-divisions.json.',
 '- Nie zapisano zmian w żadnej bazie, EXE ani projekcie Ghidry. Nie tworzono klubów, rezerw ani osób.',
 '- Wybranie uczestników nie jest gotowym wdrożeniem ligi. TargetDivisionUID pozostaje pusty do przygotowania rekordu i wykonawcy nowego poziomu.',
 '',
 '## Następny etap','',
 'Można przejść do izolowanego prototypu rejestracji ligi i kalendarza na nowej kopii802. Nie ma już zależności od ręcznego tworzenia sześciu klubów i dwóch rezerw. Nadal trzeba potwierdzić utworzenie obiektu nowej ligi, zachowanie istniejących lig/pucharów,306 spotkań, zapis/wczytanie oraz późniejszą wymianę sezonową i wymóg młodzieżowców.',
 '',
 'Poprzednie materiały z analizą rzeczywistych klubów zachowano jako historię. Nie są aktualnym zadaniem użytkownika.','',
 'Pliki: participants.csv — zamrożona obsada; manifest.json — źródło, hashe i zakres; protected-divisions.json — chronione dwie ligi; target-rules.json — model zasad z techniczną obsadą.']
text='\n'.join(lines)+'\n';(OUT/'README.md').write_text(text,encoding='utf-8');(OUT/'WZNOWIENIE.md').write_text(text,encoding='utf-8')
doc=REPO/'docs/POLAND_THIRD_TIER_PILOT_R7.md';assert not doc.exists();doc.write_text(text,encoding='utf-8')
entry=REPO/'IMPORTER_AKTUALNY_SCHEMAT_I_ZASADY.md';b=entry.read_bytes();entry.write_bytes(b+('''\r\n\r\n## 24. Trzeci poziom Polski — techniczna obsada R7\r\n\r\nNowa decyzja użytkownika: wybieramy istniejące kluby, na razie bez tworzenia\r\nnowych klubów i rezerw. [Obsada R7](docs/POLAND_THIRD_TIER_PILOT_R7.md)\r\nma18 zweryfikowanych UID z puli129560 czystej802. Żaden nie pochodzi\r\nz dwóch obecnych grywalnych lig; ich obsada16/18 jest chroniona.\r\nPo planowanym wydzieleniu zaplecze miałoby100 klubów. Bazy nie zmieniono.\r\nOczekiwanie na TEST_POL_3_LEVEL_CLUBS z sekcji23 jest nieaktualne;\r\nnie trzeba ręcznie tworzyć brakujących sześciu klubów i dwóch rezerw.\r\nDalej prototyp rejestracji ligi i terminarza; nowy UID rozgrywek nadal\r\nnieprzydzielony, brak gotowego pakietu i zaliczonego pilota gry.\r\nMateriały: POLAND_THIRD_TIER_PILOT_R7_20261107.\r\n''').encode('utf-8'))
# Mark old waiting state as superseded, preserving original plans and audits.
oldplan=OLD/'pilot-preparation.json';state=json.loads(oldplan.read_text(encoding='utf-8'));state['superseded_by']='POLAND_THIRD_TIER_PILOT_R7_20261107';state['current_user_decision']='existing_clubs_only_no_manual_entity_creation';state['historical_status']=state['status'];state['status']='superseded_by_existing_club_selection';oldplan.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for olddoc in [OLD/'KLUBY_DO_UTWORZENIA.md',OLD/'README.md',REPO/'docs/POLAND_II_LIGA_CLUB_AUDIT.md']:
 b=olddoc.read_bytes();notice='Aktualizacja decyzji: na razie nie tworzymy nowych klubów. Aktualna techniczna obsada18 istniejących zespołów jest w POLAND_THIRD_TIER_PILOT_R7_20261107. Poniższa lista braków pozostaje historycznym wynikiem audytu.\n\n'
 olddoc.write_bytes(notice.encode('utf-8')+b)
archive=OUT/'source-snapshot';archive.mkdir();shutil.copy2(pathlib.Path(__file__),archive/pathlib.Path(__file__).name);shutil.copy2(doc,archive/doc.name)
save(archive/'manifest.json',dict(source_only=True,files=[dict(path=p.name,sha256=sha(p)) for p in archive.iterdir() if p.is_file()]))
assert before==pins()
print(json.dumps(dict(status=manifest['status'],clubs=len(rows),raw_roster_entries=sum(x['RosterEntries'] for x in rows),new_clubs=0,planned_remaining_lower_pool=100,protected_top_divisions=[16,18],database_modified=False,selection=str(OUT/'participants.csv')),ensure_ascii=True))
