from pathlib import Path
from datetime import datetime
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_FATES_R9_20261107'
R8=ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_PROTOTYPE_R8_20261107'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def hashes(p):return {str(x.relative_to(p)):sha(x) for x in p.rglob('*') if x.is_file()}
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
m=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'));assert m['status']=='resources_built_validation_pending'
assert not (OUT/'Start-Pilot.cmd').exists()
source_paths=hashes(R8/'runtime');runtime_paths=hashes(OUT/'runtime');assert source_paths.keys()==runtime_paths.keys()
changes=[k for k in source_paths if source_paths[k]!=runtime_paths[k]]
assert changes==['data\\updates\\update-802\\data\\comps.efa'],changes
assert runtime_paths['fm.exe']==m['protected_original_hashes']['fm.exe']
assert hashes(Path(m['source_database']))==m['source_database_hashes']
assert hashes(R8/'resources')==m['source_resource_hashes']
assert hashes(OUT/'user-data/db/TEST_POL_3_LEVEL_R9')==m['database_output_hashes']
sources=['prepare_poland_fates_r9_20261107.py','build_poland_fates_database_r9_20261107.py','build_poland_fates_resources_r9_20261107.py','pol3_promotion_r9_20261107.py','pol3_lower_r9_20261107.py','pol3_comp_schema_r8_20261107.py','pol3_efa_r8_20261107.py','PolandThirdTierFatesR9.cs',Path(__file__).name]
(OUT/'tools/src').mkdir()
for name in sources:shutil.copy2(ROOT/'FM08-Database-Tools/scratch'/name,OUT/'tools/src'/name)
# Reuse the accepted wrapper layout, with R9-specific database/tool names and a readiness guard.
script=(R8/'Start-Pilot.ps1').read_text(encoding='utf-8-sig')
script=script.replace('TEST_POL_3_LEVEL_R8','TEST_POL_3_LEVEL_R9').replace('PolandThirdTierPilotR8.exe','PolandThirdTierFatesR9.exe')
needle="    $dbRoot = Join-Path $pilotRoot 'user-data\\db\\TEST_POL_3_LEVEL_R9'"
assert needle in script
script=script.replace(needle,"    if (!$VerifyOnly -and $manifest.status -notin @('prepared_for_r9_game_test', 'r9_game_pilot_passed_user_confirmed')) { throw 'R9 package has not passed final preflight.' }\n"+needle)
(OUT/'Start-Pilot.ps1').write_text(script,encoding='utf-8-sig')
(OUT/'Start-Pilot.cmd').write_bytes(b'@echo off\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Pilot.ps1"\r\nif errorlevel 1 pause\r\n')
readme='''# R9 — awanse, baraże i spadki w Polsce

Pakiet R9 jest zbudowany do testu nowego sezonu. Kontrole struktury danych,
reguł, archiwum i kodu x86 przeszły. **Przejście sezonu w grze R9 nie jest jeszcze
potwierdzone.** Działający R8 i jego zapis pozostawiono bez zmian.

## Uruchomienie i jeden potrzebny pilot

1. Zamknij inne FM08 i uruchom **Start-Pilot.cmd z katalogu R9**. W nowej karierze
   wybierz bazę **TEST_POL_3_LEVEL_R9 - Polish Promotion and Relegation Pilot**.
   W Polsce wybierz trzeci poziom: **Polska - II liga (test R9)**.
   Ta rewizja wymaga nowej kariery; zapis R8 zachowuje wcześniejsze reguły.
2. Przewiń sezon do baraży i sprawdź pary awansowe **3–6 i 4–5**. Półfinały
   i finał są pojedyncze; gospodarzem jest wyżej sklasyfikowany klub.
   Przy dolnej granicy miejsca **13–14** grają dwa mecze z kwalifikantami
   zaplecza, z rewanżem u klubu II ligi. Zapis i odczyt w trakcie baraży jest
   istotny dla nowej struktury etapów.
3. Przejdź do następnego sezonu: z II ligi powinny awansować **3 kluby**, spaść
   **4–6**, a I i II liga nadal mieć **po 18 drużyn**. Zaplecze powinno zachować
   **100 klubów** i ponownie utworzyć cztery grupy. Zachowaj zapis przed barażami
   i po zmianie sezonu, jeśli pojawi się błąd.

Nie trzeba ponownie udowadniać podstawowego terminarza i zapisu działającego R8.
Ten pilot sprawdza nowe baraże, wymianę klubów i rozpoczęcie kolejnego sezonu.
Pozostaw konsolę otwartą, aby zbierała `pilot-logs/pilot-*.jsonl`.

Kontrola techniczna bez startu gry:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\Start-Pilot.ps1 -VerifyOnly
```

## Wdrożone reguły kandydata R9

| Granica | Reguła |
|---|---|
| II → I liga | Miejsca 1–2 bezpośrednio; 3–6 o jedno dodatkowe miejsce |
| I → II liga | Trzy ostatnie kluby I ligi, miejsca 16–18 |
| II → zaplecze | Miejsca 15–18 bezpośrednio, miejsca 13–14 w barażach |
| Zaplecze → II liga | Czterej mistrzowie grup oraz 0–2 zwycięzców baraży |
| Eliminacje zaplecza | Czterej wicemistrzowie, losowane pary i gospodarze, dwa pojedyncze mecze |
| Finały utrzymania | Dwaj zwycięzcy eliminacji przeciw 13–14, dwumecze, rewanż u klubu II ligi |

Liga ma 18 klubów, 34 mecze na klub i punktację 3/1/0. Baraże przewidują dogrywkę
oraz karne po remisie rozstrzygającego spotkania, bez zasady bramek wyjazdowych.
Terminy bazowe: 3/10 czerwca dla awansu; 3 czerwca eliminacje zaplecza,
10/17 czerwca dwumecze utrzymania. Rzeczywiste daty przelicza silnik sezonowy.

Zaplecze tworzy **100 istniejących klubów w czterech grupach po 25**.
To techniczna obsada z historycznej 8.0.2, nie współczesne składy III ligi.
Każdy klub zaplecza ma 48 spotkań i dwie pauzy w 50 terminach. Mistrzowie
oraz wicemistrzowie wynikają z rozgrywanych tabel; nie są losowani z puli.
Zaplecze działa pomocniczo przy wyborze trzeciego poziomu, bez dodawania
czwartego poziomu do listy wyboru nowej kariery.

Nie wdrażano tu młodzieżowców ani polskiej przerwy zimowej. Kadry, osoby,
kontrakty, historyczne wypożyczenia i sztab pozostają z pełnej bazy 8.0.2.
Nie utworzono klubów ani zawodników. Polskie puchary zachowują dotychczasowy
mechanizm kwalifikacji; włączanie nowego poziomu do współczesnego pucharu
pozostaje osobnym zadaniem.

## Co sprawdzono

- Niezależny czytnik C# odczytał wszystkie 23 394 kluby. Ich odczytane pola
  i przypisania są identyczne z działającym R8: 16/18/18/100.
- W SERVER i CLIENT zmieniono tylko poziom COMP 129560 z 2 na 3;
  nazwy dwóch rozgrywek uaktualniono w 20 językach. PEOPLE i historie są identyczne.
- Archiwum zachowało wszystkie siedem wcześniejszych plików. Dodano trzy XML.
- Model 3072 wyników i losowań zachował liczebność 18/18/100 oraz wszystkie UID,
  bez duplikatów. To kontrola matematyczna, a nie wynik symulacji gry.
- Test x86 objął dodanie dwóch obiektów po pięciu natywnych, awarie i ponowne
  wejście. Sprawdzono 96 przypadków aktywacji zaplecza oraz guardy poprawek.
- Osobna kopia gry różni się od R8 tylko prywatnym archiwum definicji.
  EXE na dysku ma oryginalną sumę; poprawki działają wyłącznie w pamięci procesu.

Główny log powinien pokazać `status:1`, `before:5`, `after:7` i `lower_uid:129560`.
Liczniki `lower_activation_a/b` pokazują działanie aktywacji zaplecza.
Sam ten wpis nie potwierdza poprawności baraży ani wymiany klubów po sezonie.

Materiały: `manifest.json`, `verification.json`, `database-build.json`,
`resource-build.json`, `format-and-resource-model-check.json`, `native-after-clubs.csv`.
Szczegółowe dowody: `promotion/`, `lower-boundary/`, `upper-boundary/`.
Źródła i ich kopie: `FM08-Database-Tools/scratch/` i `tools/src/`.
'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
checkpoint='''# Wznowienie — R9: awanse, baraże i spadki

Status: pakiet zbudowany, końcowy preflight w toku. R8 został zachowany jako
zaliczony punkt odniesienia (liga/terminarz/zapis-odczyt). Nie mylić z pilotem R9.

Uruchomienie: Start-Pilot.cmd w tym katalogu, NOWA KARIERA i baza TEST_POL_3_LEVEL_R9.
R9 dodaje dwie ścieżki: awans 2+1 do129559, spadek4–6 do129560 (4x25grup).
POL_SECOND ma trzy spadki16–18 do1800001000. Pole UID obiektu silnika jest+14.
Pięć rodzimych obiektów Polski zachowano; dwa ogólne dopisuje memory-onlyhook.
UID129560 pozostaje runtimelevel3, ale dwa zakresowane hooki podtrzymują jego
aktywność przy selected>=2 także w standardowej gałęzi zmiany sezonu.

Reguły w resources/pol.xml,pol_third.xml,pol_lower.xml; archiwumcomps.efa
zawiera7oryginalnych+3noweXML. Nazwy dwóchCOMP w20językach; SERVER/CLIENT tylko
poziom129560:2→3. CLUBidentyczne zR8. Nowegrupy mają rzeczywistetabele,4mistrzów,
4wicemistrzów; losowanie dotyczy par/gospodarzy eliminacji, nie awansujących.

Kontrole: 23394CLUB niezależnego czytnika;3072wariantybilansu18/18/100;
11scenariuszyx86+repeat7;96przypadkówdwóchguardów aktywacji;3patchyPOL_SECOND.
Do potwierdzenia: nowe baraże i ich gospodarze,save-loadwewnątrzbaraży,
3awanse/4–6spadków i następny sezon bez zmiany liczebności.
Nie wdrożono młodzieżowców/przerwyzimowej ani nowej kwalifikacji pucharowej.

Nie modyfikowaćR8 ani źródłowych802/EXE. Nie ładowaćR8save jako migracjiR9.
Źródła wykonawców tools/src/, raporty patrzREADME.md. OryginalnyprojektGhidrybez zmian.
'''
(OUT/'WZNOWIENIE.md').write_text(checkpoint,encoding='utf-8')
verification=dict(status='preflight_pending',game_verified=False,season_rollover_verified=False,new_career_verified=False,save_load_verified=False,fixtures_r8_already_verified=True,r8_preserved=True,source_r8_database_hashes_unchanged=True,runtime_differences_from_r8=changes,runtime_hashes=runtime_paths,native_reader_clubs=23394,mathematical_model_cases=3072,source_snapshots=hashes(OUT/'tools/src'),pilot_tool_sha256=sha(OUT/'tools/PolandThirdTierFatesR9.exe'),resource_hashes=hashes(OUT/'resources'))
save(OUT/'verification.json',verification)
m.update(status='preflight_pending',prepared_at=datetime.now().astimezone().isoformat(),source_r8_preserved=True,launcher='Start-Pilot.cmd',game_verified=False,season_rollover_verified=False)
save(OUT/'manifest.json',m)
print(json.dumps({'status':'preflight_pending','sources_archived':len(sources),'runtime_files':len(runtime_paths),'runtime_changed_files':changes,'R8_preserved':True}),flush=True)
