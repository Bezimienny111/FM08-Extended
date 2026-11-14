from pathlib import Path
from datetime import datetime
import csv,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
OLD=ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_FATES_R9_20261107'
OUT=ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_FATES_R9_1_20261107'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def hashes(p):return {str(x.relative_to(p)):sha(x) for x in p.rglob('*') if x.is_file()}
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def snapshot(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return {int(x['ClubUID']):{k:v for k,v in x.items() if k!='SourceServerSHA256'} for x in csv.DictReader(f)}
assert snapshot(OLD/'native-after-clubs.csv')==snapshot(OUT/'native-after-clubs.csv')
a=json.loads((OUT/'diagnostics-selection/country-audit.json').read_text(encoding='utf-8'))
assert a['clubs_audited']==152 and a['non_polish_country']==[]
assert a['country_counts']=={'139':{'161':16},'140':{'161':18},'141':{'161':100},'1332':{'161':18}}
log=(OUT/'tools/package-self-check.log').read_text(encoding='utf-8-sig')
assert log.rstrip().endswith('PASS: database hashes, resources, x86 ABI and isolated runtime.')
m=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
assert hashes(Path(m['source_database']))==m['source_database_hashes']
assert hashes(OUT/'user-data/db/TEST_POL_3_LEVEL_R9')==m['database_output_hashes']
assert hashes(OUT/'runtime')==hashes(OLD/'runtime')
assert hashes(OUT/'resources')==hashes(OLD/'resources')
for rel,want in m['protected_original_hashes'].items():assert sha(ROOT/rel)==want
m.update(status='prepared_for_r9_game_test',verified_at=datetime.now().astimezone().isoformat(),preflight_passed=True,package_verify_exit_code=0,country_gate_verified=True,country_counts=a['country_counts'],selection_verified_in_game=False,game_verified=False,unresolved=['Confirm Poland selectable in freshR9.1career','R9playoff participants/hosts and season rollover remain unverified'])
save(OUT/'manifest.json',m)
readme='''# R9.1 — poprawka wyboru Polski

Naprawiono 43 puste referencje kraju w istniejących klubach zaplecza.
Silnik pomijał te kluby: liczył 57 zamiast wymaganych 100 i blokował wybór Polski.
Wszystkie 152 kluby polskich rozgrywek mają teraz przypisaną Polskę.
Kontrola skryptu startowego: PASS. Wybór kraju w grze pozostaje do potwierdzenia.

## Uruchomienie

Uruchom **Start-Pilot.cmd z tego katalogu**. W nowej karierze wybierz bazę
**TEST_POL_3_LEVEL_R9_1 - Polish Promotion and Relegation Pilot**, następnie
Polskę i trzeci poziom. Dla tej poprawki katalog danych użytkownika jest nowy.

Reguły są takie jak w R9: awans 2+1, trzy spadki z I ligi, cztery bezpośrednie
spadki z II ligi i baraże miejsc 13–14 z zapleczem. Dalej pozostaje uzgodniony
pilot baraży oraz następnego sezonu: 3 awanse, 4–6 spadków, po 18 drużyn na
obu poziomach oraz 100 klubów w czterech grupach zaplecza.

## Zakres i dowody

W nowej kopii uzupełniono tylko 43 pola Country na Polskę (indeks 161).
Nie obniżono wymogu 100. Nie zmieniono przypisań ligowych, kadr, osób, pensji,
reputacji ani zasad. W SERVER zmieniły się dokładnie 43 pola int32, czyli
172 bajty po dekompresji. CLIENT, PEOPLE, LANG, historie i inne pliki DAT
pozostały identyczne z R9. Metadane dostały nazwę R9_1 i wersję 0.2.1.

Niezależny czytnik C# odczytał wszystkie 23 394 kluby bez zmian w ich polach
TEAM. Audyt 152 klubów po korekcie nie znalazł brakujących krajów. Dodatkowe
przypisania żadnego z 23 394 klubów nie zwiększają liczników tych polskich lig.

Kod silnika, definicje XML i zasoby są identyczne z R9. Wewnętrzny folder bazy
pozostaje TEST_POL_3_LEVEL_R9 dla niezmienionego programu startowego;
widoczna nazwa bazy ma TEST_POL_3_LEVEL_R9_1. Manifest opisuje format silnika
jako revision=R9 i korektę jako repair_revision=R9.1.
R9, działający R8, źródłowa 802 i oryginalny EXE są nietknięte.

Raporty: country-correction.json, verification.json, diagnostics-selection/.
Diagnoza sprzed poprawki: input/diagnostics-selection/validator-trace.md.
Młodzieżowcy, przerwa zimowa i przebudowa kwalifikacji pucharów nie są częścią
tej poprawki. Dotychczasowe ograniczenia prototypu R9 pozostają aktualne.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
checkpoint='''# R9.1 — naprawa wyboru Polski

Status: prepared_for_r9_game_test, preflight PASS. Wybór Polski w grze jeszcze
niepotwierdzony po korekcie. Start-Pilot.cmd z tego katalogu; widoczna baza
TEST_POL_3_LEVEL_R9_1, wewnętrzny folder bazy i kod silnika nadal R9.

Przyczyna blokady R9: 43 z 100 klubów zaplecza miały Country=-1 w bazowym
rekordzie NAME-TREE, a walidator liczył tylko 57. Loader zamieniał -1 na NULL;
C7C7B0→CLUB virtual+6C→D670C0 zwracał NULL bez fallbacku. D353F0 pomijał klub.
D655F0/D35180 wymagały dokładnie 100 i oznaczały kraj jako niedostępny.

Naprawiono wyłącznie 43 int32 Country: -1→161, 172 bajty SERVER. Pola kotwione
przez UID, indeks i dwa footery NAME-TREE. Cofnięcie odtwarza dokładnie R9.
Całe TEAM, CLIENT, PEOPLE, LANG, historie i pozostałe DAT są niezmienione.
Reguły, zasoby i EXE identyczne z R9. Wymóg 100 pozostał. Nie robić obejścia
minimum30 ani nie zmieniać reputacji. Wszystkie 152 audytowane kluby mają
Country161, w tym całe zaplecze100. TEAM rawStart+47 (secondary COMP) nie wskazuje
żadnej z czterech polskich lig we wszystkich 23 394 rekordach.

Niezależny czytnik C# i Start-Pilot.ps1 -VerifyOnly: PASS. R8 i R9 zachowane.
Dalej najpierw potwierdzić wybór Polski, potem wcześniejszy uzgodniony test R9:
baraże awansu/utrzymania, zapis/odczyt i kolejny sezon 18/18/100.
Nowej korekty nie uznawać za zaliczenie całego sezonu. Szczegóły: README.md,
country-correction.json, diagnostics-selection/country-audit.json,
input/diagnostics-selection/validator-trace.md, verification.json.
'''
(OUT/'WZNOWIENIE.md').write_text(checkpoint,encoding='utf-8')
for name in ('audit_poland_r9_selection_countries_20261107.py','ExportNativeClubSelection.cs',Path(__file__).name):shutil.copy2(ROOT/'FM08-Database-Tools/scratch'/name,OUT/'tools/src'/name)
v=dict(status=m['status'],repair_revision='R9.1',country_gate_verified=True,country_audit_clubs=152,country_missing_after=0,lower_eligible_primary_count=100,polish_secondary_entries=0,native_reader_clubs=23394,native_team_fields_unchanged=True,country_fields_changed=43,decompressed_server_bytes_changed=172,preflight_passed=True,package_verify_exit_code=0,engine_and_rules_unchanged_from_R9=True,source_R9_database_unchanged=True,source_R8_untouched=True,original_sources_untouched=True,game_verified=False,selection_verified_in_game=False,season_rollover_verified=False,source_snapshots=hashes(OUT/'tools/src'))
v['package_artifacts']={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.parts[len(OUT.parts)] not in ('runtime','input','user-data','pilot-logs') and p.name!='verification.json'}
save(OUT/'verification.json',v)
doc='''# R9.1 — naprawa niedostępnej Polski

Katalog: `FmLauncher/data/research/POLAND_THIRD_TIER_FATES_R9_1_20261107`.
Start-Pilot.cmd, nowa kariera, widoczna baza TEST_POL_3_LEVEL_R9_1.

Użytkownik nie mógł wybrać Polski w R9. Log miał calls=0/status=0, czyli blokadę
przed pol_setup_comps. Audyt znalazł 43 puste Country w puli 100 klubów; silnik
zliczał tylko 57 wobec exact100. Łańcuch potwierdzono statycznie: C6C940 czyta
Country do CLUB+DC, C68500→C20D20 konwertuje -1 na NULL, D670C0 zwraca +DC
bez fallbacku, C7C7B0→D353F0 pomija taki klub. D655F0→D35180 oznacza błąd
liczebności przed wyborem kraju. TEAM secondary rawStart+47 nie dodaje klubów
polskim ligom; sprawdzono wszystkie 23 394 rekordy.

Nowa kopia R9.1 uzupełnia wyłącznie 43 Country -1→161: 172 bajty danych SERVER.
Wszystkie inne pola i pliki DAT pozostały identyczne z R9. Metadane dostały
nazwę R9_1 i wersję 0.2.1. Zasoby, reguły, kod silnika i wymóg100 są niezmienione.
Po korekcie audyt152/152 ma Polskę, w tym100/100zaplecza. Niezależny czytnik C#
potwierdził identyczność23 394TEAM; Start-Pilot.ps1 -VerifyOnly PASS.

Status prepared_for_r9_game_test, country_gate_verified=true,
selection_verified_in_game=false, season_rollover_verified=false. Najpierw
potwierdzić wybór Polski, następnie wcześniej uzgodniony pilot baraży i zmiany
sezonu. R8, R9, oryginalna802, EXE i projekty Ghidry pozostają nietknięte.
Raporty w pakiecie: country-correction.json,verification.json,diagnostics-selection/.
Poprzednia walidacja R9 nie obejmowała efektywnego kraju klubów zaplecza;
nie wystarcza sama liczba bieżących przypisań CLUB. Zachować bramkę Country
przy dalszych zmianach rozgrywek.
'''
(ROOT/'FM08-Database-Tools/docs/POLAND_THIRD_TIER_COUNTRY_FIX_R91.md').write_text(doc,encoding='utf-8')
entry=ROOT/'FM08-Database-Tools/IMPORTER_AKTUALNY_SCHEMAT_I_ZASADY.md';raw=entry.read_bytes();assert b'## 27.' not in raw
section='''\n\n## 27. R9.1 — poprawka wyboru Polski po nieudanym pilocie R9

R9 nie pozwalał wybrać Polski: 43 ze 100 klubów zaplecza miały Country=-1.
Silnik pomijał je i liczył 57 wobec wymaganych 100. To brak poprzedniej walidacji:
surowa liczba przypisań ligowych nie dowodzi kraju ani zaliczenia do walidatora.
[Poprawka R9.1](docs/POLAND_THIRD_TIER_COUNTRY_FIX_R91.md) powstała w nowej kopii:
POLAND_THIRD_TIER_FATES_R9_1_20261107. Uzupełniono tylko 43 Country na Polskę
(indeks161), 172 bajty SERVER. Wymóg100 i reguły awansów/baraży/spadków bez zmian.
Wszystkie 152 kluby mają teraz kraj, w tym100zaplecza. Dodatkowe przypisania
TEAM+47 nie zwiększają liczników polskich lig (23 394 rekordy sprawdzone).
Czytnik C# potwierdził identyczne TEAM, pozostałe DAT identyczne; preflight PASS.
Start-Pilot.cmd z katalogu R9.1; widoczna nazwa TEST_POL_3_LEVEL_R9_1,
wewnętrzny folder i format launchera R9. R8 i R9 zachowane bez zmian baz.
Status prepared_for_r9_game_test; wybór Polski po poprawce i przejście sezonu
nadal do potwierdzenia w grze. Raporty country-correction.json i verification.json.
Nie obniżać progu ani nie zmieniać reputacji w obejściu brakującego Country.
'''
with entry.open('ab') as f:f.write(section.replace('\n','\r\n').encode('utf-8'))
assert hashes(Path(m['source_database']))==m['source_database_hashes']
print(json.dumps({'status':m['status'],'repair_revision':'R9.1','country_audit':'152/152','lower_eligible_count':100,'preflight':'PASS','game_selection_verified':False}),flush=True)
