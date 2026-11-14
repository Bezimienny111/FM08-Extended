"""Archive the verified SI free-staff creation schema; no database writes."""
import json,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
from analyze_buffon_loan_20261106 import ROOT,hashes,sha,require
REPO=ROOT/'FM08-Database-Tools';OUT=ROOT/'FmLauncher/data/research/STAFF_20261106_NEW_MANAGER'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
r=read(OUT/'report.json');require(r['status']=='controlled_free_staff_creation_verified','creation analysis not verified')
for path,key in [('baseline','baseline_hashes'),('fixture','fixture_hashes')]:require(hashes(Path(r[path]))==r[key],'input changed since analysis')
p=REPO/'docs/NATIVE_STAFF.md';t=p.read_text(encoding='utf-8-sig');require('## Nowy wolny menedżer — TEST_STAFF_NEW' not in t,'creation schema already documented')
t+='''

## Nowy wolny menedżer — TEST_STAFF_NEW, 2026-11-06

Próbka SI utworzyła osobę UID1394631303, PERSON index334475, typ1,
w roli menedżera zgłoszonej przez użytkownika. Surowy kod roli wynosi16,
klub=-1, liczba umów0. Nie powstaje blok umowy ani klubowa relacja personelu.
Osoba nie ma odniesienia przez swój indeks w SERVER ani CLIENT.

| Tabela / licznik PEOPLE | 8.0.2 | TEST_STAFF_NEW | Nowy rekord |
|---|---:|---:|---:|
| PERSON | 334475 | 334476 | 138B, UID1394631303 |
| Osobowość | 347896 | 347897 | 17B, UID1394631302 |
| Atrybuty zawodników | 273506 | 273506 | Brak |
| Atrybuty sztabu | 77073 | 77074 | 49B, UID1394631306 |

W PEOPLE przybywa204B =138+17+49. PERSON wskazuje rekord atrybutów sztabu
przez int32 na+19 (wartość77073), a osobowość przez int32 na+85 (347896).
Są to offsety rozpoznanej minimalnej próbki, nie obietnica stałych offsetów
każdego historycznego profilu. Rekord może leżeć wewnątrz fizycznej tabeli;
nie wyprowadzamy fizycznego położenia z wartości indeksu ani UID.

Tabela atrybutów sztabu leży za tabelą89B zawodników, ma licznik int32,
rekordy49B i kolejne indeksy. W rekordzie49B int32+41 to indeks, int32+45
— UID. Pozostałe41B nowej próbki są zerowe; znaczeń poszczególnych pól
szkoleniowych jeszcze nie przypisano. W17B osobowości indeks jest na+9,
UID na+13, a pierwsze9B nowej próbki są zerowe.

Nowe słowniki nazw powstają w SERVER i CLIENT, z identycznymi UID:
- imię: **`Trener `** (spacja na końcu), indeks0, UID1394631304;
- nazwisko: **`Nowy`**, indeks0, UID1394631305.

Raport zachowuje dokładną pisownię. Nie usuwa spacji i nie zmienia próbki.
Każdy nowy UID osoby, nazw, osobowości i atrybutów jest nieobecny w oryginalnych
buforach8.0.2. Nie zakładamy, że UID osobowości musi być większy od UID osoby.

Wszystkie wcześniejsze rekordy osobowości, wszystkie atrybuty zawodników,
wcześniejsze atrybuty sztabu i końcowe bajty PEOPLE są identyczne z8.0.2.
Tabela8777 powiązań klubowego personelu, rekord Juventusu i6210 wypożyczeń
są identyczne. Sześć plików historii zachowuje hashe. Pozostałych historycznych
PERSON nie porównano po pełnym rozstrzygnięciu zmienionych indeksów nazw SI;
nie deklarujemy identyczności wszystkich plików poza dopisanymi bajtami.

Dowody: `FmLauncher/data/research/STAFF_20261106_NEW_MANAGER/report.json`,
rekordy138/17/49B i archiwum źródeł. Bazy wejściowe pozostały nietknięte.
Potwierdzono format nowego wolnego pracownika, ale natywny wykonawca tworzenia
sztabu oraz odczyt wolnego sztabu w aktualnym buildzie r2 nadal nie istnieją.
Nie testowano zachowania nowej osoby w grze.
''';p.write_text(t,encoding='utf-8')
p=REPO/'fm08_compendium.md';t=p.read_text(encoding='utf-8-sig');t+='''

#### Nowy menedżer bez klubu — TEST_STAFF_NEW

Nowa osoba UID1394631303, typ1, indeks334475: PERSON138B, osobowość17B
UID1394631302, atrybuty sztabu49B UID1394631306. Liczba graczy nie zmienia się.
PERSON+19 wskazuje indeks77073 atrybutów sztabu, +85 osobowość347896.
Rekord49B ma indeks+41 i UID+45; nowe surowe pola są zerowe, bez rozpoznania
znaczenia poszczególnych ocen. Nowe nazwy UID1394631304/1305 są w SERVER/CLIENT.
Imię ma końcową spację: „Trener ”. Klub-1, zero umów, kod roli16.
Powiązania klubowego sztabu i wypożyczenia są identyczne; format jest potwierdzony,
ale wykonawcy tworzenia osób jeszcze nie wdrożono.
Szczegóły: [NATIVE_STAFF.md](docs/NATIVE_STAFF.md).
''';p.write_text(t,encoding='utf-8')
p=REPO/'IMPORTER_AKTUALNY_SCHEMAT_I_ZASADY.md';t=p.read_text(encoding='utf-8-sig');t+='''

`TEST_STAFF_NEW` potwierdza format nowego menedżera bez klubu, UID1394631303:
PERSON138B + osobowość17B + atrybuty sztabu49B; bez nowego gracza, umowy
ani powiązań klubowych. Szczegóły w NATIVE_STAFF.md i raporcie
`STAFF_20261106_NEW_MANAGER`. To rozpoznany schemat, nie wdrożona funkcja tworzenia.
''';p.write_text(t,encoding='utf-8')
policy_path=OUT.parent/'STAFF_RESEARCH_POLICY.json';policy=read(policy_path);policy.update(latest_case=str(OUT),confirmed_si_free_staff_creation_format=dict(person_type=1,person_bytes_this_fixture=138,personality_row_bytes=17,staff_attribute_row_bytes=49,staff_attribute_index_offset=41,staff_attribute_uid_offset=45,player_count_delta=0,club=-1,contracts=0),native_staff_creation_implemented=False);save(policy_path,policy)
archive=OUT/'source-snapshot';archive.mkdir(exist_ok=False);entries=[]
files=['scratch/analyze_staff_new_20261106.py','scratch/finalize_staff_new_20261106.py','scratch/analyze_staff_noclub_20261106.py','scratch/analyze_buffon_loan_20261106.py','scratch/compare_native_player_tests.py','docs/NATIVE_STAFF.md','fm08_compendium.md','IMPORTER_AKTUALNY_SCHEMAT_I_ZASADY.md']
for rel in files:
    dest=archive/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(REPO/rel,dest);entries.append(dict(path=rel,SHA256=sha(dest)))
save(archive/'manifest.json',dict(source_only=True,files=entries))
save(OUT/'result.json',dict(status=r['status'],person_uid=r['person_uid'],person_index=r['person_index'],new_records_bytes=[138,17,49],existing_attribute_tables_preserved=True,loans_preserved=6210,inputs_unchanged=True,source_files_archived=len(entries),native_staff_creation_implemented=False,game_behavior='not_tested'))
print(json.dumps(dict(status=r['status'],source_files_archived=len(entries),inputs_unchanged=True,native_staff_creation_implemented=False)))
