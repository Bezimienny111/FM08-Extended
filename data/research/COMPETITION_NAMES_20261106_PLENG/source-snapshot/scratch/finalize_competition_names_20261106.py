"""Document and archive verified multilingual competition-name editing."""
import json,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
from analyze_buffon_loan_20261106 import ROOT,hashes,sha,require
REPO=ROOT/'FM08-Database-Tools';OUT=ROOT/'FmLauncher/data/research/COMPETITION_NAMES_20261106_PLENG'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
r=read(OUT/'report.json');require(r['status']=='controlled_competition_localized_names_verified','localized names not verified')
for path,key in [('baseline','baseline_hashes'),('fixture','fixture_hashes')]:require(hashes(Path(r[path]))==r[key],'input changed after analysis')
for c in r['si_controls']:require(hashes(Path(c['path']))==c['hashes'],'SI control changed')
p=REPO/'docs/NATIVE_COMPETITION_NAMES.md';require(not p.exists(),'documentation already exists')
p.write_text('''# Nazwy rozgrywek w językach FM08

Stan:2026-11-06. Próbka SI `Dane/db/TEST_NAMEL_PLENG` względem oryginalnej8.0.2
`data/updates/update-802/db/802`. Rozgrywki UID129558, indeks natywny139.
Nie zamieniać UID z indeksem ani z przypadkowym wystąpieniem tej samej liczby.

## Wynik próbki

| Język | language-ID | Pełna nazwa przed | Pełna nazwa po | Skrócona nazwa po | Skrót po |
|---|---:|---|---|---|---|
| Angielski | 8 | Polish First Division | PKO Bank Polski Ekstraklasa | First Division | 1 L |
| Polski | 18 | Polska 1. Liga | PKO Bank Polski Ekstraklasa | 1. Liga | 1L |

Zmieniono tylko pełne nazwy. Krótka nazwa i skrót literowy są osobnymi polami;
nie aktualizują się automatycznie razem z pełną nazwą. Wpis UID129558 w pozostałych
18 językach pozostał identyczny ze źródłem. Zmiana angielskiego wpisu nie zastępuje
zapisanych tłumaczeń w innych blokach, także tych zawierających tekst angielski.
Nie testowano zachowania gry dla pustego tłumaczenia i mechanizmu fallback.

Cały68B rekord rozgrywek w server_db.dat, wraz z indeksem139 i UID129558,
jest identyczny z8.0.2. Nazwy są oddzielone od tego rekordu. Zapis tej próbki
nie zmienia go na nową ligę ani nie dowodzi zmiany zasad rozgrywek.

## lang_db.dat jest archiwum strumieni

Nie rozpakowujemy całego pliku jako jednego zlib po9B nagłówka.

- Pierwsze9B: nagłówek DAT.
- Bajt9: liczba języków, w tej próbce20.
- Od bajtu10:20 par little-endian uint32 language-ID / uint32 relativeOffset.
- Fizyczny początek bloku:9+relativeOffset; pierwszy offset161 daje bajt170.
- Każdy blok jest osobnym pełnym strumieniem zlib. Koniec wyznacza następny
  offset albo koniec pliku. Wszystkie strumienie sprawdzamy niezależnie.

Po zmianie długości tekstu przesuwają się dalsze rekordy rozpakowanego bloku.
Po kompresji przesuwają się kolejne strumienie pliku, więc indeks offsetów trzeba
przebudować z długości faktycznie skompresowanych bloków. Nie wolno zachować
starych offsetów po zastąpieniu tekstu dłuższą nazwą.

## Zaobserwowany wpis rozgrywek

W każdym rozpakowanym bloku wpis identyfikuje int32 UID129558, a nie indeks139.
W tej próbce kolejnym wpisem jest UID129559; sprawdzamy to jako granicę.

```text
int32 competitionUID
uint32 fullNameUtf16Units
UTF-16LE fullName + NUL16
byte suffix1
uint32 shortNameUtf16Units
UTF-16LE shortName + NUL16
byte suffix2
uint32 abbreviationUtf16Units
UTF-16LE abbreviation + NUL16
```

Długości liczymy w jednostkach UTF-16, nie w bajtach ani w ogólnej liczbie
punktów Unicode. Sufiksy zachowano:EN0/0, PL1/1. Ich znaczenia gramatycznego
nie potwierdzono niezależną zmianą; nie zerujemy ich podczas edycji nazwy.
Nie przenosić schematu trzech nazw na dowolny inny rodzaj obiektu.

## Kontrola niezależna od normalizacji SI

Samo porównanie skompresowanych plików8.0.2 i nowego zapisu SI daje więcej
różnic. Użyto również dwóch wcześniejszych, przypiętych hashami zapisów SI:
TEST_STAFF_WAGE oraz TEST_LOAN. Ich20 rozpakowanych bloków językowych jest
identycznych. Względem obu kontroli próba nazwy zmienia dokładnie pełną nazwę
UID129558 w blokach8 i18. Pozostałe18 całych bloków jest bajtowo identycznych.

Zastąpienie wyłącznie dwóch pól długość/tekst/NUL daje całe bloki identyczne z SI.
Ponowne spakowanie i przebudowanie indeksu w pamięci przechodzi odczyt wszystkich
20 bloków i daje zawartość identyczną z próbką. Nie wygenerowano nowej bazy i nie
potwierdzono zapisu naszego wyniku przez SI ani działania w grze.

Liczby osób i wszystkie tabele people_db.dat po PERSON,6210 wypożyczeń oraz sześć
plików historii są identyczne ze źródłem. Nie sklasyfikowano wszystkich różnic
pozostałych plików PEOPLE/SERVER/CLIENT wynikających z ponownego zapisu SI.

W próbce cztery pliki LNC leżą bezpośrednio w lnc zamiast lnc/all, z identyczną
treścią. Brakuje źródłowego `lnc/french league names.edt`. To osobne różnice
opakowania kopii, nie wymagane elementy zmiany tłumaczenia. Nie odtwarzamy ich
w przyszłym minimalnym wykonawcy nazw.

Dowody: `FmLauncher/data/research/COMPETITION_NAMES_20261106_PLENG/report.json`,
rekordy EN/PL przed/po i archiwum źródeł. Bazy wejściowe i kontrole SI pozostały
nietknięte. Implementacja publicznego importera/GUI nazw pozostaje kolejnym etapem.
''',encoding='utf-8')
p=REPO/'fm08_compendium.md';t=p.read_text(encoding='utf-8-sig');t+='''

### Pełne nazwy ligi w EN/PL — TEST_NAMEL_PLENG

Próbka UID129558 potwierdza niezależne wpisy lang_db.dat:EN ID8 iPL ID18.
Oba pełne teksty zmieniono na „PKO Bank Polski Ekstraklasa”, bez zmiany shortName
i skrótu. Pozostałe18 wpisów językowych są identyczne. Rekord68B rozgrywek
w SERVER (indeks139/UID129558) również jest identyczny. Względem dwóch wcześniejszych
zapisów SI całe20 rozpakowanych bloków odpowiada wyłącznie dwóm podmianom nazw.
Repack z przebudową indeksu offsetów sprawdzono w pamięci, bez zapisu bazy.
Szczegóły: [NATIVE_COMPETITION_NAMES.md](docs/NATIVE_COMPETITION_NAMES.md).
''';p.write_text(t,encoding='utf-8')
p=REPO/'IMPORTER_AKTUALNY_SCHEMAT_I_ZASADY.md';t=p.read_text(encoding='utf-8-sig');t+='''

## 19. Wielojęzyczne nazwy rozgrywek — rozpoznanie

Próbka `TEST_NAMEL_PLENG`, UID129558: pełna nazwa EN/PL jest osobno w blokach
ID8/18 pliku lang_db.dat; skrócona nazwa i skrót to niezależne pola.
[Format i kontrola](docs/NATIVE_COMPETITION_NAMES.md) opisują archiwum20 zlib,
bezpieczne wyznaczanie długości UTF-16 i przebudowę indeksu offsetów.
Cały rekord rozgrywek w SERVER pozostaje identyczny. Jest potwierdzona rekonstrukcja
w pamięci względem dwóch zapisów SI, jeszcze bez publicznego wykonawcy/GUI nazw.
''';p.write_text(t,encoding='utf-8')
p=REPO/'README.md';t=p.read_text(encoding='utf-8-sig');t+='\nRozpoznanie nazw lig EN/PL: [NATIVE_COMPETITION_NAMES.md](docs/NATIVE_COMPETITION_NAMES.md).\n';p.write_text(t,encoding='utf-8')
archive=OUT/'source-snapshot';archive.mkdir(exist_ok=False);entries=[]
files=['scratch/analyze_competition_names_20261106.py','scratch/finalize_competition_names_20261106.py','scratch/analyze_buffon_loan_20261106.py','scratch/compare_native_player_tests.py','scratch/create_native_u23_test.py','docs/NATIVE_COMPETITION_NAMES.md','fm08_compendium.md','IMPORTER_AKTUALNY_SCHEMAT_I_ZASADY.md','README.md']
for rel in files:
    dest=archive/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(REPO/rel,dest);entries.append(dict(path=rel,SHA256=sha(dest)))
save(archive/'manifest.json',dict(source_only=True,files=entries))
save(OUT/'result.json',dict(status=r['status'],competition_uid=129558,changed_language_ids=[8,18],full_name='PKO Bank Polski Ekstraklasa',short_names_and_abbreviations_unchanged=True,all_twenty_blocks_match_si=True,native_competition_record_identical=True,inputs_unchanged=True,source_files_archived=len(entries),native_renamed_database_generated=False,game_behavior='not_tested'))
save(OUT.parent/'COMPETITION_NAME_RESEARCH_POLICY.json',dict(baseline=r['baseline'],baseline_hashes=r['baseline_hashes'],baseline_read_only=True,latest_case=str(OUT),verified_language_ids=dict(English=8,Polish=18),competition_key='UID',native_database_generated=False,public_importer_implemented=False))
print(json.dumps(dict(status=r['status'],source_files_archived=len(entries),inputs_unchanged=True)))
