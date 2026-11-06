# FM08 Extended — database / baza 2026/27

[Project / Projekt](README.md) · [Installation / Instalacja](INSTALLATION.md) ·
[Releases](https://github.com/Bezimienny111/FM08-Extended/releases) ·
[Report a bug / Zglos blad](https://github.com/Bezimienny111/FM08-Extended/issues)

## Prepared update / Przygotowywana aktualizacja V24.1

[V24.1 README/release copy, PL/EN](DATABASE_RELEASE_NOTES_V24_1.md)
describes the local corrections and cumulative changes since V21.
It is **not a published download**: V24.1 has native verification,
but SI-editor acceptance and a new-career test remain pending.
The published V21 package described below is unchanged.

[Opis V24.1 do README/release, PL/EN](DATABASE_RELEASE_NOTES_V24_1.md)
obejmuje korekty lokalnej bazy i zmiany od V21. **Nie jest opublikowana
paczka**: pozostaja testy SI i nowej kariery. Ponizszy opis wydania V21
pozostaje aktualny dla tamtej, niezmienionej paczki.

## English

### Preview 0.1.0 — based on V21

The database and launcher are **separate downloads**. Database release
`db-2026-27-v0.1.0` packages the selected V21 overhaul for FM08 8.0.2.
The source DAT and EDT/LNC contents are preserved; only the package's
folder/XML identification and README are adapted for public distribution.

The overhaul contains modern squads, young talents and revised club
assignments: over 29,000 modern profiles and more than 1,100 clubs.
These headline figures describe the overhaul's scope, not the number
of players guaranteed to load in every career. Country/league choices
and database size affect retention.

### Install

1. Download `FM08-Extended-DB-2026-27-0.1.0.zip` from
   [the database release](https://github.com/Bezimienny111/FM08-Extended/releases/tag/db-2026-27-v0.1.0).
   Do not use the generated Source code archives.
2. Compare the ZIP's SHA256 with its `.sha256` attachment using
   `Get-FileHash -Algorithm SHA256`. Do not use a mismatched package.
3. Extract the single folder `FM08Extended_2026-27_0.1.0` into your
   installation's database directory, beside its existing database folders
   (usually `<FM08>\data\db`; installations may use a localized path).
   Keep the XML and all DAT/EDT/LNC files inside that folder.
4. Start FM08 8.0.2, create a **new career** and select
   **FM08 Extended 2026/27 0.1.0 Preview (V21)**.
5. For completeness-oriented testing, use Large and load the countries
   you want to check. Large still does not load every native record.

Never overwrite an edited database or save. Each future release gets a
new folder. Installing another database does not update an existing career.
This package does not require the launcher; automatic database downloading
and installation are not implemented in the launcher.

### Known issues and validation

- **160 future-transfer/retirement date conflicts**: 159 transfers after
  retirement and one on the same day. Historical players may remain
  available or join clubs later. Example: Daniele Cacia, UID 830762,
  retirement 2007-07-30, Fiorentina transfer 2008-01-02.
  These are data conflicts, not 160 proven engine reactivation cases.
- The audit found 425 future transfers, 194 linked to an active retirement.
  It also found 275 active retirement rows with UID -1, not valid person UIDs.
- Four of the 160 conflicts involve type-3 PERSON identities with narrower
  coverage than the type-2 player reader. Names unresolved by the existing
  reader are explicitly marked in the attached conflict CSV.
- Modern player loans are not comprehensively represented. Some historical
  future-transfer records remain. Staff and stadium modernization are not
  included. No claim is made that every duplicate or relationship is fixed.
- Read-only native audit and source preservation were checked for this
  exact V21. Packaging verifies every archived entry and SHA256.
  These checks are **not** SI-editor acceptance or a successful long-term
  new-career test. The Cacia issue was observed by the user in a career;
  no post-fix career test exists because this preview does not fix it.
- The launcher is experimental too. Back up careers and enable modules
  gradually.

Report problems through [GitHub Issues](https://github.com/Bezimienny111/FM08-Extended/issues):
include database/launcher versions, player UID, selected leagues and
database size, start/current dates, reproduction steps and screenshots.
Do not upload game executables, complete game installations or private logs.

### Rights

The launcher source's GPL-3.0-only license does **not** automatically
license this database or original game data. This is a fan-made database
package requiring a legitimately obtained game; original and third-party
rights remain with their respective holders. No game executable, save,
skin or facepack is included. This project is not an official SI release.

## Polski

### Wersja testowa 0.1.0 — na podstawie V21

Baza i launcher to **osobne paczki**. Wydanie `db-2026-27-v0.1.0`
zawiera wskazana V21 dla FM08 8.0.2. Pliki DAT i zawartosc EDT/LNC
zachowano; na potrzeby dystrybucji zmieniaja sie tylko nazwa folderu,
identyfikacja XML oraz README paczki.

Zakres modernizacji: wspolczesne kadry i talenty, zmienione przydzialy
klubow, ponad 29 tys. nowoczesnych profili i ponad 1100 klubow.
Nie jest to gwarantowana liczba osob w kazdej karierze: wybor krajow,
lig i rozmiaru bazy wplywa na wczytanie zawodnikow.

### Instalacja

1. Z [wydania bazy](https://github.com/Bezimienny111/FM08-Extended/releases/tag/db-2026-27-v0.1.0)
   pobierz `FM08-Extended-DB-2026-27-0.1.0.zip`, nie Source code.
2. Porownaj SHA256 ZIP z zalacznikiem `.sha256`, np.
   `Get-FileHash -Algorithm SHA256`. Nie uzywaj niezgodnej paczki.
3. Rozpakuj pojedynczy folder `FM08Extended_2026-27_0.1.0` do katalogu
   baz instalacji FM08, obok istniejacych folderow baz
   (zwykle `<FM08>\data\db`, lokalnie moze to byc `Dane\db`).
   XML, DAT i podkatalogi EDT/LNC musza pozostac wewnatrz tego folderu.
4. Rozpocznij **nowa kariere** w FM08 8.0.2 i wybierz
   **FM08 Extended 2026/27 0.1.0 Preview (V21)**.
5. Do testow kompletnosci polecamy Large i wczytanie potrzebnych krajow.
   Large nadal nie oznacza wszystkich rekordow.

Nie nadpisuj baz zmienionych w edytorze ani zapisow. Kazda wersja
otrzymuje osobny folder; nowa baza nie aktualizuje istniejacej kariery.
Launcher nie jest wymagany do tej paczki i nie pobiera ani nie instaluje
baz automatycznie.

### Znane problemy i potwierdzenia

- **160 konfliktow dat przyszlych transferow i emerytur**:
  159 transferow po emeryturze, jeden tego samego dnia.
  Historyczni gracze moga pozostac dostepni lub pozniej trafic do klubow.
  Cacia, UID 830762: emerytura 30.07.2007, Fiorentina 02.01.2008.
  Nie oznacza to 160 potwierdzonych reaktywacji przez silnik.
- 425 przyszlych transferow, w tym 194 powiazane z aktywna emerytura;
  dodatkowo 275 aktywnych wierszy emerytur z UID -1 zamiast UID osoby.
- Cztery konflikty dotycza tozsamosci PERSON typu 3, z wezsza kontrola
  niz dla graczy typu 2. Nierozpoznane nazwy sa jawnie oznaczone w CSV.
- Wypozyczenia wspolczesnych graczy nie sa kompleksowo odtworzone;
  pozostaly historyczne przyszle transfery. Sztaby i stadiony nie sa
  zmodernizowane. Nie deklarujemy usuniecia wszystkich duplikatow i relacji.
- Potwierdzono swiezy audyt natywny tylko do odczytu, zachowanie zrodla
  i zgodnosc zawartosci ZIP/hashy. To **nie** jest potwierdzenie zapisu
  w SI ani dlugiego testu nowej kariery. Problem Cacii zgloszono z kariery;
  nie ma testu po naprawie, bo ta paczka go nie naprawia.
- Integracje launchera tez sa eksperymentalne; wykonuj kopie karier.

Bledy zglaszaj przez [GitHub Issues](https://github.com/Bezimienny111/FM08-Extended/issues):
podaj wersje, UID zawodnika, ligi, rozmiar bazy, daty kariery, kroki
odtworzenia i screeny. Nie zalaczaj EXE gry, calej instalacji ani prywatnych logow.

### Prawa

GPL-3.0-only kodu launchera nie obejmuje automatycznie tej bazy ani
oryginalnych danych gry. Fanowska paczka wymaga legalnej kopii gry;
prawa oryginalne i osob trzecich pozostaja przy ich wlascicielach.
Nie zawiera EXE gry, zapisow, skorek ani facepackow. Projekt nie jest
oficjalnym wydaniem SI.
