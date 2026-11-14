"""Persist the verified no-club staff format without changing editor behavior."""
import json,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
from analyze_buffon_loan_20261106 import ROOT,hashes,sha,require
REPO=ROOT/'FM08-Database-Tools';OUT=ROOT/'FmLauncher/data/research/STAFF_20261106_RANIERI_NOCLUB'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
r=read(OUT/'report.json');require(r['status']=='controlled_staff_club_removal_verified','analysis not verified')
for path,key in [('baseline','baseline_hashes'),('wage_reference','wage_reference_hashes'),('fixture','fixture_hashes')]:require(hashes(Path(r[path]))==r[key],'input changed after analysis')
p=REPO/'docs/NATIVE_STAFF.md';t=p.read_text(encoding='utf-8-sig');require('## Usunięcie klubu — Test_staff_noclub' not in t,'no-club documentation already exists')
t+='''

## Usunięcie klubu — Test_staff_noclub, 2026-11-06

Próbka SI zachowuje Claudio Ranieriego (UID4201569, PERSON index129460, typ1)
i potwierdza usunięcie jego relacji z Juventusem. Porównano czystą8.0.2,
TEST_STAFF_WAGE i Test_staff_noclub. Nie zmieniano baz wejściowych.

W PERSON następują dokładnie te zmiany, poza rozstrzygniętymi indeksami nazw:

- klub na względnym+75:995→-1;
- data przypisania na+80/+82:01.07.2007→01.01.1900 (sentinel);
- liczba kontraktów na+102:1→0;
- usunięcie65B umowy z+103..+167, rekord272→207B;
- surowy kod roli na+79 pozostaje16; reszta PERSON jest identyczna.

Pensja i koniec umowy znikają razem z blokiem kontraktu. Nie odczytywać starego
+138 jako pensji w skróconym rekordzie. Offsety powyżej dotyczą tej próbki.

Ranieriego nie było w liście87 członków kadry Juventusu już przed zmianą;
lista pozostaje identyczna. Jego powiązanie menedżera jest osobnym int32 na
względnym **CLUB+23**:PERSON index129460→-1. Cały rekord klubu odpowiada
wyłącznie tej zmianie. Nie wolno sprowadzać zwolnienia sztabu do usunięcia
osoby z listy kadry zawodników ani kopiować takiej procedury zawodnika.

SI usuwa również17-bajtowy wpis osobnej tabeli personelu w server_db.dat:
licznik8777→8776, usunięty ordinal4501. Rekord ma zaobserwowany układ:
byte0=0, int32+1=PERSON index, dwa short na+5/+7 o niepotwierdzonym tu znaczeniu,
int32+9=ordinal, int32+13=-1. Pozostałe wiersze zachowują wszystkie dane;
ordinale po usuniętym wpisie zmniejszają się o1. Cała tabela po tej operacji
jest bajtowo identyczna z SI. Nie oznacza to jeszcze rozpoznania całej semantyki
tabeli. Stały offset jej nagłówka nie jest kontraktem API.

Wszystkie6210 wypożyczeń, sześć plików historii i cała część people_db.dat
po tabeli PERSON są identyczne. Imię i nazwisko zachowują te same UID nazw.
W innych zakresach PEOPLE/SERVER/CLIENT występują dodatkowe różnice zapisu SI;
raport podaje liczbę różniących się bajtów po odjęciu opisanej operacji.
Nie sklasyfikowano ich wszystkich i nie kopiujemy ich do przyszłego wykonawcy.

Raport: `FmLauncher/data/research/STAFF_20261106_RANIERI_NOCLUB/report.json`.
To potwierdzenie formatu próbki, nie wdrożenie zwalniania sztabu. Obecny czytnik
r2 nadal odrzuca wolnego pracownika; funkcji zwolnienia ani GUI nie zmieniono.
Wynik natywnego wykonawcy i zachowanie gry pozostają nieprzetestowane.
''';p.write_text(t,encoding='utf-8')
p=REPO/'fm08_compendium.md';t=p.read_text(encoding='utf-8-sig');t+='''

#### Sztab bez klubu — Test_staff_noclub

Próbka SI usuwa65B umowy Ranieriego, ustawia klub-1 i datę1900-01-01,
a liczba umów zmienia się1→0. Typ1, UID i kod roli16 pozostają.
Ponadto CLUB Juventusu+23 zmienia PERSON index129460 na-1; lista87 graczy
jest identyczna i nie zawierała Ranieriego. Osobna17B tabela personelu traci
jego wiersz (8777→8776), a kolejne ordinale są zmniejszane. CA/PA i pozostały
PERSON są chronione. To ustalenie formatu, jeszcze bez wykonawcy zwolnienia.
Dokładne zakresy i ograniczenia: [NATIVE_STAFF.md](docs/NATIVE_STAFF.md).
''';p.write_text(t,encoding='utf-8')
p=REPO/'IMPORTER_AKTUALNY_SCHEMAT_I_ZASADY.md';t=p.read_text(encoding='utf-8-sig');t+='''

Próbka `Test_staff_noclub` potwierdza później format zwolnienia Ranieriego:
usunięcie65B umowy, klub-1, wyczyszczenie wskaźnika menedżera CLUB+23 oraz
usunięcie/przenumerowanie wpisu osobnej tabeli17B. To nie jest usuwanie
ze zwykłej listy kadry. [Szczegóły](docs/NATIVE_STAFF.md) i osobny raport
`STAFF_20261106_RANIERI_NOCLUB` nie oznaczają gotowej funkcji zwolnienia.
''';p.write_text(t,encoding='utf-8')
policy_path=OUT.parent/'STAFF_RESEARCH_POLICY.json';policy=read(policy_path);policy.update(latest_case=str(OUT),confirmed_si_no_club_format=dict(person_contract_bytes_removed=65,club_sentinel=-1,club_date_sentinel='1900-01-01',club_manager_pointer_offset=23,relation_row_size=17,relation_row_ordinal_offset=9),native_staff_release_implemented=False);save(policy_path,policy)
archive=OUT/'source-snapshot';archive.mkdir(exist_ok=False)
files=['scratch/analyze_staff_noclub_20261106.py','scratch/finalize_staff_noclub_20261106.py','scratch/analyze_buffon_loan_20261106.py','scratch/compare_native_player_tests.py','docs/NATIVE_STAFF.md','fm08_compendium.md','IMPORTER_AKTUALNY_SCHEMAT_I_ZASADY.md'];entries=[]
for rel in files:
    dest=archive/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(REPO/rel,dest);entries.append(dict(path=rel,SHA256=sha(dest)))
save(archive/'manifest.json',dict(source_only=True,files=entries))
save(OUT/'result.json',dict(status=r['status'],person_uid=r['person_uid'],contract_removed_bytes=65,manager_pointer_cleared=True,relation_rows_before=8777,relation_rows_after=8776,roster_unchanged=True,loans_preserved=6210,inputs_unchanged=True,source_files_archived=len(entries),native_staff_release_implemented=False,game_behavior='not_tested'))
print(json.dumps(dict(status=r['status'],source_files_archived=len(entries),inputs_unchanged=True,native_staff_release_implemented=False)))
