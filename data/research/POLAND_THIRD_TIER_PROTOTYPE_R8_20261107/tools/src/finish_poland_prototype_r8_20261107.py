from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_PROTOTYPE_R8_20261107'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
doc='''# Trzeci poziom Polski — pakiet R8

Pakiet jest przygotowany do pierwszego testu gry. Nie ma jeszcze zaliczonego
pilota nowej kariery. Katalog:
`J:\\FM08dev\\FmLauncher\\data\\research\\POLAND_THIRD_TIER_PROTOTYPE_R8_20261107`.
Uruchomienie: `Start-Pilot.cmd`; instrukcja i ograniczenia w `README.md`.

Podstawą jest pełna historyczna baza 8.0.2. Dodano ligę UID 1800001000,
indeks COMP 1332, oraz przeniesiono 18 istniejących klubów wybranych w R7.
Definicja: 18 zespołów, dwie rundy, 34 kolejki, punktacja 3/1/0.
Pula UID 129560 pozostała i ma 100 klubów. Dotychczasowe grywalne ligi zachowały
16 i 18 klubów. Zachowano fabryki obu lig i polskich pucharów.

Minimalna poprawka w pamięci dopisuje ogólny obiekt rozgrywek po wykonaniu
oryginalnego `pol_setup_comps`. Reguły nowej ligi zapisano w zasobach XML.
Kod działa tylko w nowym procesie prywatnej kopii gry; EXE na dysku jest oryginalny.

Zaliczone kontrole:

- Wszystkie stare rekordy COMP w SERVER i CLIENT oraz nazwy w 20 językach
  zachowano. Zmiany SERVER można odwrócić do dokładnego oryginału.
- Niezależny czytnik C# odczytał 23 394 kluby. Zmieniło się tylko 18 pól
  bieżącej ligi. PEOPLE, historie i pozostałe odczytane pola klubów są identyczne.
- Archiwum EFA zachowało siedem wcześniejszych plików i dostało dwie definicje.
- Prywatny katalog gry ma kopię 585 plików danych. Zmieniono tylko jego
  `data/updates/update-802/data/comps.efa`. Sumy plików źródłowych są identyczne.
- Siedem scenariuszy testu x86 i ponowne wejście przeszły. Stos, rejestry,
  flagi i pięć dotychczasowych wpisów zostały zachowane.
- `Start-Pilot.ps1 -VerifyOnly` zakończył się kodem 0 i wynikiem PASS.

Do sprawdzenia w grze: wybór poziomu, 18 uczestników, 306 spotkań łącznie,
34 mecze na klub, obecność pucharów oraz zapis i ponowny odczyt kariery.
Nie połączono jeszcze awansów, spadków, baraży ani przepisu dwóch polskich
młodzieżowców. Kalendarz nie odtwarza polskiej przerwy zimowej.

Raporty w pakiecie: `manifest.json`, `database-resource-build.json`,
`runtime-verification.json`, `verification.json`, `WZNOWIENIE.md`.
Źródła wykonawców: `scratch/` oraz pakietowe `tools/src/`.
Źródłowe EXE, zasoby, baza 8.0.2, modernizacja i projekty Ghidry są nietknięte.
'''
(ROOT/'FM08-Database-Tools/docs/POLAND_THIRD_TIER_PROTOTYPE_R8.md').write_text(doc,encoding='utf-8')
entry=ROOT/'FM08-Database-Tools/IMPORTER_AKTUALNY_SCHEMAT_I_ZASADY.md'
raw=entry.read_bytes();start=raw.index(b'## 25.');assert b'## 26.' not in raw[start:]
section='''## 25. Trzeci poziom Polski — prototyp R8 przygotowany do testu

Użytkownik zlecił rozpoczęcie wdrożenia na istniejących klubach.
[Pakiet R8](docs/POLAND_THIRD_TIER_PROTOTYPE_R8.md) ma osobną bazę czystej 802,
nową ligę UID 1800001000 / indeks 1332 i 18 klubów z R7; zaplecze 129560 zachowano.
Baza i zasoby są zbudowane. Kontrola struktury i niezależny odczyt CLUB przeszły;
obsada dotychczasowych lig 16/18 pozostała identyczna. Osobny katalog gry ma
kopię 585 plików danych. Minimalna poprawka tylko w pamięci dopisuje ogólny
obiekt po pięciu oryginalnych polskich rozgrywkach. Test siedmiu scenariuszy
ABI oraz ponownego wejścia przeszedł. Start-Pilot.ps1 -VerifyOnly: PASS, kod 0.
Start-Pilot.cmd w katalogu POLAND_THIRD_TIER_PROTOTYPE_R8_20261107 uruchamia
prywatną kopię gry. Nie ma jeszcze zaliczonej nowej kariery, terminarza ani
zapisu/odczytu. Awansów, spadków, baraży, młodzieżowców i przerwy zimowej
jeszcze nie połączono. Status prepared_for_first_game_test, game_verified=false.
Źródła nietknięte. Sekcje 22–24 opisują historyczne etapy przygotowania.
'''
entry.write_bytes(raw[:start]+section.replace('\n','\r\n').encode('utf-8'))
v=json.loads((OUT/'verification.json').read_text(encoding='utf-8'))
v.update(package_verify_command='Start-Pilot.ps1 -VerifyOnly',package_verify_exit_code=0,package_verify_result='PASS: database hashes, resources, x86 ABI and isolated runtime.')
archived=OUT/'tools/src'/Path(__file__).name;shutil.copy2(Path(__file__),archived)
v['source_snapshots']={p.name:sha(p) for p in (OUT/'tools/src').iterdir()}
# Snapshot all deliverables, excluding game files already covered by dedicated reports.
v['package_artifacts']={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.parts[len(OUT.parts)] not in ('input','runtime','user-data','pilot-logs') and p.name!='verification.json'}
save(OUT/'verification.json',v)
m=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
for rel,expected in m['protected_source_hashes'].items():assert sha(ROOT/rel)==expected
for rel,expected in m['source_database_hashes'].items():assert sha(ROOT/'data/updates/update-802/db/802'/rel)==expected
for rel,expected in m['database_output_hashes'].items():assert sha(OUT/'user-data/db/TEST_POL_3_LEVEL_R8'/rel)==expected
assert sha(OUT/'tools/PolandThirdTierPilotR8.exe')==m['pilot_tool_sha256']
assert sha(OUT/'runtime/data/updates/update-802/data/comps.efa')==m['runtime_comp_archive_sha256']
print(json.dumps({'final_status':m['status'],'package_check':'PASS','source_files_unchanged':21,'source_snapshots':len(v['source_snapshots']),'game_verified':False}),flush=True)
