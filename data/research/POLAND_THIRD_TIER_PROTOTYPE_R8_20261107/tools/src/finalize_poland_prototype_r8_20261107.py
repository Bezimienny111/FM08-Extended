from pathlib import Path
import hashlib,json,shutil,sys
from datetime import datetime
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_PROTOTYPE_R8_20261107'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def save(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
m=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
assert m['status']=='private_runtime_built'
assert json.loads((OUT/'runtime-verification.json').read_text(encoding='utf-8'))['originals_unchanged']
source_names=['prepare_poland_third_tier_r8_20261107.py','build_poland_third_tier_r8_20261107.py','prepare_poland_runtime_r8_20261107.py','pol3_comp_schema_r8_20261107.py','pol3_efa_r8_20261107.py','PolandThirdTierPilotR8.cs',Path(__file__).name]
sources=OUT/'tools/src';sources.mkdir(exist_ok=False)
for name in source_names:shutil.copy2(ROOT/'FM08-Database-Tools/scratch'/name,sources/name)
ps=r'''param([switch]$VerifyOnly)
$ErrorActionPreference = 'Stop'
try {
    $pilotRoot = $PSScriptRoot
    $manifest = Get-Content -LiteralPath (Join-Path $pilotRoot 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $dbRoot = Join-Path $pilotRoot 'user-data\db\TEST_POL_3_LEVEL_R8'
    foreach ($entry in $manifest.database_output_hashes.PSObject.Properties) {
        $path = Join-Path $dbRoot $entry.Name
        if (!(Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing database file: $path" }
        if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $entry.Value) { throw "Database file changed: $path" }
    }
    $archive = Join-Path $pilotRoot 'runtime\data\updates\update-802\data\comps.efa'
    if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $manifest.runtime_comp_archive_sha256) { throw 'Unexpected competition resource archive.' }
    $tool = Join-Path $pilotRoot 'tools\PolandThirdTierPilotR8.exe'
    if ((Get-FileHash -LiteralPath $tool -Algorithm SHA256).Hash -ne $manifest.pilot_tool_sha256) { throw 'Pilot tool hash differs.' }
    $runtime = Join-Path $pilotRoot 'runtime'
    & $tool --verify (Join-Path $runtime 'fm.exe')
    if ($LASTEXITCODE -ne 0) { throw 'Native ABI / executable check failed.' }
    & $tool --verify-runtime $runtime
    if ($LASTEXITCODE -ne 0) { throw 'Runtime layout check failed.' }
    Write-Host 'PASS: database hashes, resources, x86 ABI and isolated runtime.'
    if ($VerifyOnly) { exit 0 }
    & $tool --launch $runtime
    exit $LASTEXITCODE
} catch {
    Write-Error $_ -ErrorAction Continue
    exit 1
}
'''
(OUT/'Start-Pilot.ps1').write_text(ps.replace('\n','\r\n'),encoding='utf-8-sig')
(OUT/'Start-Pilot.cmd').write_bytes(b'@echo off\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Pilot.ps1"\r\nif errorlevel 1 pause\r\n')
readme='''# Trzeci poziom Polski — prototyp R8

Pakiet jest przygotowany do pierwszego testu w grze. Kontrole struktury bazy,
niezależnego czytnika klubów, archiwum zasobów i kodu x86 przeszły. Nie ma jeszcze
zaliczonego uruchomienia nowej kariery, sprawdzenia terminarza ani zapisu/odczytu.

## Uruchomienie

1. Zamknij inne uruchomione FM08. Uruchom `Start-Pilot.cmd` z tego katalogu.
   Program sprawdzi pliki, a potem uruchomi osobną kopię gry z poprawką w pamięci.
   Pozostaw okno konsoli otwarte — zapisuje wyniki do `pilot-logs`.
2. Rozpocznij **nową karierę** i wybierz bazę
   **TEST_POL_3_LEVEL_R8 - Polish Third Tier Pilot**.
3. Dodaj Polskę i sprawdź, czy można wybrać trzeci poziom:
   **Polska - III poziom (test R8)** / **Polish Third Tier - Prototype R8**.
   Zachowano także dwa dotychczasowe poziomy oraz ich fabryki pucharów.
4. Po utworzeniu kariery sprawdź tabelę: **18 drużyn** z `participants.csv`.
   Terminarz powinien mieć **34 mecze na klub, 17 u siebie i 17 na wyjeździe**,
   łącznie **306 meczów**, po dwa spotkania każdej pary. Sprawdź też dotychczasowe
   ligi (16 i 18 klubów) i obecność polskich pucharów.
5. Zapisz karierę w `user-data/games`, wyjdź z gry i ponownie uruchom
   **Start-Pilot.cmd**. Wczytaj zapis i sprawdź tabelę oraz terminarz.

Do sprawdzenia plików bez uruchamiania gry:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\Start-Pilot.ps1 -VerifyOnly
```

Zwykłe uruchomienie `runtime/fm.exe` pomija poprawkę dopisującą rozgrywki.
Jeśli trzeciego poziomu brakuje albo gra zgłosi błąd, zachowaj komunikat oraz
najnowszy plik `pilot-logs/pilot-*.jsonl`. Status `1`, `before:5`, `after:6`
potwierdza dopisanie obiektu; sam ten wpis nie potwierdza terminarza. Status `0`
przed tworzeniem polskich rozgrywek jest możliwy. Statusy `2`–`5` oznaczają
niepowodzenie, a `6` oznacza kolekcję mającą już sześć elementów.

## Zakres prototypu

To pełna historyczna baza **8.0.2**, z kadrami z epoki FM08, oraz jedna nowa
liga techniczna i zmiana przypisania 18 istniejących klubów. To nie jest
aktualizacja sezonu 2026/27. Nie utworzono klubów, osób ani nowych wypożyczeń.
Istniejące dane zawodników, sztabu, wypożyczeń i historii pozostawiono.
Surowe kadry wybranych klubów są niepełne; nie importowano zawodników.

Definicja ligi: 18 zespołów, dwie rundy, punktacja 3/1/0. Kalendarz jest prostą
próbą pełnego sezonu, bez odtworzonej polskiej przerwy zimowej. Nie połączono
jeszcze awansów, spadków, baraży ani wymogu dwóch polskich młodzieżowców.
Nie traktuj przejścia sezonu jako testu docelowego systemu PZPN.

## Co zapisano

- `user-data/db/TEST_POL_3_LEVEL_R8`: baza do wybrania w grze.
- `runtime`: kopia EXE, bibliotek i 585 plików danych; tylko prywatny update
  `comps.efa` ma dwie nowe definicje XML.
- `resources`: jawne `pol.xml`, `pol_third.xml` i wynikowe archiwum.
- `input/802`: zamrożona baza odniesienia.
- `database-resource-build.json`: dowody zmian COMP/CLUB/nazw.
- `native-after-clubs.csv` i `runtime-verification.json`: niezależny odczyt
  23 394 klubów oraz kontrola kopii i źródeł.
- `tools/src`: kopie źródeł wykonawców; `tools/launcher-self-test.log`: test x86.

Nowa liga: UID **1800001000**, indeks COMP **1332**. Pula UID **129560** nadal
istnieje i ma 100 klubów. Dwie dotychczasowe ligi zachowały wszystkie swoje
kluby. Poza 18 polami bieżącej ligi pozostałe odczytane pola klubów są identyczne.
Wszystkie stare rekordy COMP pozostały identyczne; dopisano rekord 1333.
Nazwy nowej ligi dopisano we wszystkich 20 blokach językowych.

Oryginalne `fm.exe`, zasoby instalacji, baza 8.0.2 i bazy modernizacji pozostały
nietknięte. Kod dodający ligę działa wyłącznie w pamięci nowego procesu tej
kopii gry. Odczyt zasobów przez działającą grę pozostaje częścią pierwszego testu.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
checkpoint='''# Wznowienie — trzeci poziom Polski R8

Status: pakiet przygotowany do pierwszego testu w grze, nie game_verified.
Wejście: czysta 8.0.2. Wyjście: user-data/db/TEST_POL_3_LEVEL_R8.
Start: Start-Pilot.cmd; kontrola bez gry: Start-Pilot.ps1 -VerifyOnly.

Zbudowano nowy COMP UID1800001000 / index1332 (1332→1333), przeniesiono tylko
18 bieżących przypisań CLUB z141 do1332. Po niezależnym odczycie C#: ligi
139=16,140=18,141=100,1332=18. Całe PEOPLE/historie i pozostałe pola klubów
identyczne. SERVER odwrócony dokładnie rekonstruuje oryginał; CLIENT ma
identyczny ogon; stare rekordy nazw w20językach zachowane.

EFA: oryginalny update802 ma7 plików; dodano pol/pol.xml i pol/pol_third.xml.
Wszystkie stare payloady zachowane. Prywatny runtime zawiera585 plików data,
zmieniono tylko jego update802/data/comps.efa. EXE ma oryginalny SHA256.

Minimalny hook tylko w pamięci E8EA41 (5E59C3CCCC→JMP): po oryginalnych5
obiektach Polski tworzy ogólny ACTUAL_COMP przez D805B0, dopisuje szósty.
Oryginalne ligi/puchary zachowane. Fixture x86:7 scenariuszy + ponowne wejście
PASS, stos/rejestry/flagi zachowane. Źródło tools/src/PolandThirdTierPilotR8.cs.

Do wykonania: uruchomić Start-Pilot.cmd, wybrać bazę R8, Polskę i trzeci poziom;
potwierdzić18drużyn/34mecze-na-klub/306łącznie, puchary i zapis→restart→odczyt.
Nie uznawać samego fixture lub JSONstatus1 za pilot gry. Nie ma jeszcze
awansów/spadków/baraży/młodzieżowców ani polskiej przerwy zimowej.

Raporty i instrukcja: README.md, manifest.json, database-resource-build.json,
runtime-verification.json, native-after-clubs.csv, verification.json.
Nie ponawiać przygotowania/budowy na tych samych katalogach: skrypty chronią
przed nadpisaniem. Oryginały i zapisane projekty Ghidry bez zmian.
'''
(OUT/'WZNOWIENIE.md').write_text(checkpoint,encoding='utf-8')
m.update(status='prepared_for_first_game_test',prepared_at=datetime.now().astimezone().isoformat(),game_verified=False,si_verified=False,runtime_resource_loading_observed=False,pilot_tool_sha256=sha(OUT/'tools/PolandThirdTierPilotR8.exe'),runtime_comp_archive_sha256=sha(OUT/'runtime/data/updates/update-802/data/comps.efa'),runtime_hook_required=True,first_test_instructions='README.md',launcher='Start-Pilot.cmd')
save(OUT/'manifest.json',m)
verification=dict(status='prepared_for_first_game_test',database_structure=True,independent_club_reader=True,language_blocks=20,archive_members_preserved=7,private_runtime_hashes_verified=True,native_abi_fixture='7 scenarios and repeat-entry passed',game_verified=False,si_verified=False,new_career_verified=False,fixtures_verified=False,save_load_verified=False,source_hashes_unchanged=True,source_snapshots={p.name:sha(p) for p in sources.iterdir()},tool_sha256=m['pilot_tool_sha256'])
save(OUT/'verification.json',verification)
doc=ROOT/'FM08-Database-Tools/docs/POLAND_THIRD_TIER_PROTOTYPE_R8.md'
doc.write_text('''# Trzeci poziom Polski — pakiet R8

Przygotowany do pierwszego testu gry, bez zaliczonego pilota kariery.
Pakiet: `J:\\FM08dev\\FmLauncher\\data\\research\\POLAND_THIRD_TIER_PROTOTYPE_R8_20261107`.
Uruchomienie: `Start-Pilot.cmd`; pełna instrukcja i ograniczenia w `README.md`.

Czysta802, nowa liga UID1800001000/index1332,18 istniejących klubów z R7,
18zespołów/2rundy/34kolejki. Pula129560pozostaje i ma100klubów. Obecne grywalne
ligi zachowują16/18klubów; nie zmieniono ich fabryk ani pucharów. Ogólny obiekt
nowych rozgrywek dodaje minimalny hook w pamięci, po oryginalnym pol_setup_comps.
Reguły nowej ligi są w zasobach XML, a nie w nowej klasie natywnej.

Kontrole zaliczone: stary COMP identyczny wSERVER/CLIENT,20bloków nazw,
odwracalność zmian, pełny niezależny odczyt23394CLUB, tylko18bieżących przypisań,
identycznePEOPLE/historie, EFAroundtrip i7starych payloadów,585plikówprywatnego
data, oryginalnyhashEXE,7scenariuszyfixturex86+ponownewejście.

Do potwierdzenia w grze: wybór poziomu,18uczestników,306spotkań,34na klub,
obecnośćpucharów,zapis/odczyt. Nie ma jeszcze integracji awansów/spadków/baraży
ani przepisu2polskichmłodzieżowców. Kalendarz bez polskiej przerwy zimowej.
Raporty: manifest.json,database-resource-build.json,runtime-verification.json,
verification.json,WZNOWIENIE.md. Źródła wykonawców w scratch/ i pakietowymtools/src.
Źródłowe EXE, zasoby,802,modernizacja i projektyGhidry pozostały nietknięte.
''',encoding='utf-8')
entry=ROOT/'FM08-Database-Tools/IMPORTER_AKTUALNY_SCHEMAT_I_ZASADY.md'
text='''\n\n## 25. Trzeci poziom Polski — prototyp R8 przygotowany do testu\n\nUżytkownik zlecił rozpoczęcie wdrożenia na istniejących klubach.\n[Pakiet R8](docs/POLAND_THIRD_TIER_PROTOTYPE_R8.md) ma osobną bazę czystej802,\nnową ligę UID1800001000/index1332 i18klubów z R7; zaplecze129560zachowane.\nBaza i zasoby są zbudowane, kontrola struktury i niezależny odczyt CLUB\nzaliczone; ligi16/18chronione. Osobnyruntime ma kopię585plikówdata.\nMinimalnyhook tylko w pamięci dopisuje ogólny obiekt po5oryginalnych polskich\nrozgrywkach;7scenariuszyABI i ponowne wejście PASS. Start-Pilot.cmd w katalogu\nPOLAND_THIRD_TIER_PROTOTYPE_R8_20261107 uruchamia tę kopię gry.\nNie ma jeszcze zaliczonej nowej kariery/terminarza/zapisu-odczytu.\nAwansów,spadków,baraży,młodzieżowców i przerwy zimowej jeszcze nie połączono.\nStatus prepared_for_first_game_test, game_verified=false; źródła nietknięte.\nSekcje22–24 są historycznymi etapami, nie aktualnym stanem wykonawcy.\n'''
raw=entry.read_bytes();assert b'## 25.' not in raw
with entry.open('ab') as f:f.write(text.replace('\n','\r\n').encode('utf-8'))
print(json.dumps({'status':m['status'],'sources_archived':len(source_names),'launch_script':str(OUT/'Start-Pilot.cmd'),'game_verified':False}),flush=True)
