from pathlib import Path
from datetime import datetime
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_FATES_R9_20261107'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def hashes(p):return {str(x.relative_to(p)):sha(x) for x in p.rglob('*') if x.is_file()}
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
log=OUT/'tools/package-self-check.log';text=log.read_text(encoding='utf-8-sig')
assert text.rstrip().endswith('PASS: database hashes, resources, x86 ABI and isolated runtime.')
assert '96 native x86 cases' in text and 'ABI scenario 10 passed' in text
m=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'));assert m['status']=='preflight_pending'
assert hashes(OUT/'user-data/db/TEST_POL_3_LEVEL_R9')==m['database_output_hashes']
assert hashes(Path(m['source_database']))==m['source_database_hashes']
assert sha(OUT/'tools/PolandThirdTierFatesR9.exe')==m['pilot_tool_sha256']
for rel,want in m['protected_original_hashes'].items():assert sha(ROOT/rel)==want
for rel,want in m['protected_original_database_hashes'].items():assert sha(ROOT/'data/updates/update-802/db/802'/rel)==want
m.update(status='prepared_for_r9_game_test',verified_at=datetime.now().astimezone().isoformat(),preflight_passed=True,package_verify_command='Start-Pilot.ps1 -VerifyOnly',package_verify_exit_code=0,game_verified=False,season_rollover_verified=False,save_load_verified=False,source_modified=False,unresolved=['R9 new-career playoff participants and hosts in running game','Save/reload within new playoff stages','First season rollover with3promoted and4-6relegated','Next-season18/18/100 and four lower groups'])
save(OUT/'manifest.json',m)
p=OUT/'WZNOWIENIE.md';s=p.read_text(encoding='utf-8')
s=s.replace('Status: pakiet zbudowany, końcowy preflight w toku.', 'Status: prepared_for_r9_game_test. Końcowy preflight PASS, kod 0.')
s=s.replace('Status: prepared_for_r9_game_test. Końcowy preflight PASS, kod 0. R8 został zachowany jako\nzaliczony punkt odniesienia', 'Status: prepared_for_r9_game_test. Końcowy preflight PASS, kod 0.\nR8 został zachowany jako zaliczony punkt odniesienia')
p.write_text(s,encoding='utf-8')
doc='''# Polska: R9 — awanse, spadki i baraże

Pakiet kandydujący do testu gry:
`J:\\FM08dev\\FmLauncher\\data\\research\\POLAND_THIRD_TIER_FATES_R9_20261107`.
Uruchomienie `Start-Pilot.cmd`, nowa kariera z bazą `TEST_POL_3_LEVEL_R9`,
wybrany trzeci poziom Polski. R8 z zaliczonym pilotem pozostawiono bez zmian.

Wdrożono do pakietu:

- Nowa II liga UID 1800001000: miejsca 1–2 awansują, 3–6 grają pojedyncze
  półfinały 3–6 i 4–5 oraz finał. Gospodarz według wyższej pozycji w lidze.
- Dotychczasowa POL_SECOND UID 129559: trzy miejsca spadkowe 16–18 kierowane
  do 1800001000. Zachowano jej górną granicę, kalendarz i rodzimą fabrykę.
- II liga: 15–18 spadają do 129560; 13–14 grają dwumecze o utrzymanie,
  z rewanżem u klubu II ligi. Bilans spadków 4–6.
- COMP 129560: cztery rzeczywiście rozgrywane grupy po 25 istniejących klubów.
  Czterej mistrzowie awansują, czterej wicemistrzowie grają dwa pojedyncze
  mecze w losowanych parach i lokalizacjach. Zwycięzcy trafiają do dwumeczów.
  To techniczna obsada 100 klubów historycznej 802, nie współczesne składy.

Każdy klub zaplecza ma 48 meczów i dwie pauzy w 50 terminach. Po sezonie dolna
pula ma nadal 100 klubów. Nie tworzono klubów/osób ani nowych wypożyczeń.
Nie wdrażano młodzieżowców, polskiej przerwy zimowej ani zmiany kwalifikacji
polskich pucharów. Wyjście jest pełną historyczną bazą 8.0.2 z tym eksperymentem.

## Wykonanie techniczne

Nowy `scratch/PolandThirdTierFatesR9.cs` zachowuje pięć polskich obiektów
natywnych i dopisuje ogólne ACTUAL_COMP dla 1800001000 oraz 129560 (5→7).
Reguły są w trzech XML archiwum prywatnego `comps.efa`. Zachowano siedem
oryginalnych plików archiwum. EXE na dysku ma oryginalną sumę SHA-256.

Trzy poprawki pamięci w fabryce POL_SECOND: E8F761 (4→3), E8F7DB (4→3),
E8F7DD (cel 129560→1800001000), łącznie sześć zmienionych bajtów.
Dwa hooki D68DD3 i D69AF0 kierują pomocnicze zaplecze do standardowej gałęzi
aktywnej wyłącznie dla UID 129560 i wybranego poziomu >=2. Poziom zaplecza
pozostaje 3, lista krajowa nadal ma tylko trzy poziomy. UID obiektu jest w+14.
Sam brak deaktywacji nie wystarczałby do inicjalizacji kolejnego sezonu.

`team_order` jest kluczem sortowania, nie permutacją indeksów. Zachowano
osobny seeding pozycji ligowej. Cztery akcje fate dwumeczów odpowiadają
oryginalnemu wzorcowi szkockiemu; docelowe grupy obsługuje E330E0→DD09B0.
Nieobecna w tabeli drużyna jest pomijana, co pozwala łączyć obie ligi.

## Kontrole i następny test

`Start-Pilot.ps1 -VerifyOnly`: PASS, kod 0. Niezależny czytnik C# odczytał
23 394 kluby; wszystkie ich odczytane pola są identyczne z R8. W bazie zmieniono
jeden bajt poziomu COMP 129560 w SERVER i CLIENT oraz nazwy dwóch COMP
w 20 językach. PEOPLE, historie i pozostałe pliki są identyczne.

Model 3072 wariantów zachował wszystkie UID, rozłączność i liczebności 18/18/100.
Test x86 sprawdził 11 scenariuszy dodawania obiektów, ponowne wejście bez
alokacji, awarie i 96 przypadków aktywacji. Guardy, preflight i rollback przeszły.
Prywatny runtime różni się od kopii R8 tylko archiwum definicji.

**game_verified=false, season_rollover_verified=false.** Nowa kariera R9
wymaga sprawdzenia baraży, gospodarzy, zapisu/odczytu wewnątrz etapów oraz
następnego sezonu: trzy awanse, 4–6 spadków, 18/18/100 i ponowne cztery grupy.
Nie wymagać powtarzania bez zmian podstawowego pilota R8. Nie uznawać
modelu matematycznego ani testów ABI za zaliczony sezon w grze.

Pełna instrukcja i raporty w README.md pakietu. Szczegółowe dowody w
promotion/, lower-boundary/, upper-boundary/; zamrożone źródła tools/src/.
Oryginalne EXE, zasoby instalacji, 802, R8 i projekty Ghidry nietknięte.
'''
(ROOT/'FM08-Database-Tools/docs/POLAND_THIRD_TIER_FATES_R9.md').write_text(doc,encoding='utf-8')
entry=ROOT/'FM08-Database-Tools/IMPORTER_AKTUALNY_SCHEMAT_I_ZASADY.md';raw=entry.read_bytes();assert b'## 26.' not in raw
section='''\n\n## 26. Polska — R9: awanse, spadki i baraże przygotowane do testu

Użytkownik zlecił dodanie awansów, baraży i spadków. [Pakiet R9](docs/POLAND_THIRD_TIER_FATES_R9.md)
powstał w nowej kopii działającego R8, który pozostaje zachowany.
Nowa II liga UID 1800001000: awans 2+1 z miejsc 3–6; spadek 4–6 z barażami
13–14. POL_SECOND UID 129559 ma trzy spadki 16–18 do nowej II ligi.
Zaplecze UID 129560: cztery prawdziwe grupy po 25 istniejących klubów,
czterej mistrzowie oraz 0–2 zwycięzców baraży awansują. Wicemistrzowie grają
losowane eliminacje, potem dwa dwumecze z 13–14 (rewanż u II ligi).

Start-Pilot.cmd w POLAND_THIRD_TIER_FATES_R9_20261107; NOWA KARIERA z bazą R9.
Poprawki działają tylko w pamięci: 5→7 obiektów, trzy zmiany POL_SECOND i dwa
UID-scoped hooki aktywacji zaplecza (także przy zmianie sezonu). Reguły w XML.
Baza zachowuje wszystkie przypisania CLUB z R8; zmieniono poziom COMP 129560
na 3 i nazwy dwóch lig w 20 językach. Nowych klubów/osób/wypożyczeń brak.
Kontrola całego skryptu startowego: PASS, kod 0; niezależny czytnik 23 394 klubów,
3072 modele bilansu 18/18/100, 11 scenariuszy ABI oraz 96 przypadków aktywacji.

Status prepared_for_r9_game_test; game_verified=false, season_rollover_verified=false.
Następny test to baraże, save/load w ich trakcie i sezonowe przejście z 3 awansami,
4–6 spadkami oraz ponowną obsadą 18/18/100. Nie traktować zaliczonego R8 jako
zaliczonego R9. Młodzieżowcy, przerwa zimowa i współczesna kwalifikacja do pucharów
pozostają osobno. Oryginały, R8 oraz zapisane projekty Ghidry nietknięte.
'''
with entry.open('ab') as f:f.write(section.replace('\n','\r\n').encode('utf-8'))
shutil.copy2(Path(__file__),OUT/'tools/src'/Path(__file__).name)
v=json.loads((OUT/'verification.json').read_text(encoding='utf-8'))
v.update(status=m['status'],preflight_passed=True,package_verify_exit_code=0,package_verify_command='Start-Pilot.ps1 -VerifyOnly',package_verify_log='tools/package-self-check.log',source_snapshots=hashes(OUT/'tools/src'),game_verified=False,season_rollover_verified=False)
v['package_artifacts']={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.parts[len(OUT.parts)] not in ('input','runtime','user-data','pilot-logs') and p.name!='verification.json'}
save(OUT/'verification.json',v)
assert json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))['preflight_passed']
assert hashes(Path(m['source_database']))==m['source_database_hashes']
print(json.dumps({'status':m['status'],'preflight':'PASS','source_R8_preserved':True,'game_verified':False,'season_rollover_verified':False,'source_files_archived':len(v['source_snapshots'])}),flush=True)
