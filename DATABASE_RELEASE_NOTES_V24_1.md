# [Database] FM08 Extended 2026/27 - V24.1

**Opis do README / przyszlego release'u. Nie opublikowano wydania ani ZIP.**
V24.1 to identyfikator roboczej bazy; nie oznacza utworzonego publicznego
tagu. Wersja XML: 0.24.1. Launcher ma osobna numeracje i paczke.

## Polski

### Najwazniejsze zmiany od poprzedniej paczki V21

- **Aktualizacja lig pieciu krajow:** Anglia, Hiszpania, Polska, Niemcy,
  Francja - 449 miejsc w 22 rozgrywkach, 425 zmian przydzialow.
  Zachowano liczbe zespolow i zasady FM08; dodatkowe awanse i spadki
  dobrano wedlug koncowych tabel poprzedniego sezonu. W liczbie zmian
  jest 137 technicznych przesuniec na granicy nizszych lig.
- **Naprawa niewidocznych krajow przy zakladaniu kariery:** uzupelniono
  dziesiec brakujacych przypisan kraju klubow, w tym Stali Mielec.
  Poprawiona V23.1 dziala po zapisie w SI wedlug potwierdzenia uzytkownika.
- **Uzupelnienie 171 kadr:** 4156 profili, w tym 3984 nowych oraz
  172 zachowane istniejace UID. Przy braku zawodnika w FC27 wykorzystano
  fakty z Transfermarkt i jawne szacunki ocen wedlug ligi oraz wieku.
  Nowe oceny: 42 zestawy FC27 i 3942 szacowane; 41 wyroznionych talentow
  z PA 150-180. Nie przedstawiamy szacunkow jako rzeczywistych ocen skautow.
- **Kontrola brakujacych dat:** pominieto 79 pozycji zrodla bez roku
  urodzenia; szesc zatwierdzonych dat przyblizono do 1 stycznia znanego roku.
- **Porzadkowanie historycznych i zdublowanych profili:** V22 obejmuje
  24 graczy Vorskli, 35 Santos Cape Town i cztery slabsze duplikaty.
  Zachowano wybrane mocniejsze rekordy Bernala, Pitarcha, Cirii i Quendy;
  poprawiono DOB Pitarcha i Cirii. V24 dodatkowo zwalnia i ustawia emerytury
  3169 historycznym zawodnikom, zachowujac 46 niegraczowych wpisow kadr.

### Nowa poprawka V24.1

- Usunieto **20 blednych przypisan zawodnikow Polski U17 do PSM Makassar**.
  Przyczyna: stary importer pomylil identyfikator reprezentacji
  (TM 23136) z klubem PSM (TM 14104).
- 18 zawodnikow otrzymalo poprawny klub lub zatwierdzony odpowiednik
  macierzysty: Lech (3), Pogon (2), Widzew (2), Legia (6), Slask (2),
  Espanyol (1), Gornik Zabrze (1), Jagiellonia (1).
- Dla Mateusza Grygiera i Adama Garwolinskiego ustawiono zwolnienie
  i techniczna emeryture 30.07.2007 z powodu braku ich klubow w bazie.
  **To adaptacja bazy, nie informacja o rzeczywistym zakonczeniu karier.**
- Zachowano UID, CA/PA, atrybuty, osobowosci i DOB. Zaktualizowano
  wlascicieli, kadry, powiazania glownych umow i kolidujace numery koszulek.
- Wybrany profil Oliwiera Madeja pozostaje w Stali Rzeszow, bez zmian V24.1.
  Data Bartosza Kowalskiego nadal jest niepotwierdzona; poprawiono tylko klub.

### Wazne ograniczenia

- **PSM nie ma teraz kadry zawodniczej.** Ta poprawka nie dodaje jego
  rzeczywistego skladu. Zespoly mlodziezowe/rezerwy bez odpowiednika
  zostaly odwzorowane przez istniejace kluby macierzyste.
- Nie naprawiono wszystkich duplikatow, wypozyczen ani historycznych
  przyszlych transferow; wczesniejsze 160 konfliktow dat pozostaje poza
  zakresem. Drugi rekord Madeja w Resovii nie zostal usuniety.
- Sztaby, stadiony, facepack i inne grafiki nie sa czescia aktualizacji.
- Silnik nadal startuje w 2007; daty graczy przystosowano przesunieciem
  o 19 lat. To nie jest zmiana daty startowej silnika na 2026.
- Nowa baza wymaga **nowej kariery** i FM08 8.0.2; nie aktualizuje save.
  Launcher jest osobna, opcjonalna paczka.

### Stan testow przed publikacja

V24.1 przeszla pilota trzech profili, cztery natywne testy negatywne
oraz pelna i niezalezna weryfikacje 20 korekt. Sprawdzono caly PERSON
poza dozwolonymi zmianami, 23397 klubow i chronione pliki. V24 zachowano
bez zmian. **Zapis/kontrola V24.1 w SI oraz test nowej kariery pozostaja
do wykonania.** Nie deklarujemy jeszcze stabilnego wydania.

Po testach nalezy uzupelnic ich faktyczny wynik, ustalic publiczny numer,
spakowac zweryfikowana kopie i dolaczyc SHA256. Nie publikowac fikcyjnego
linku ani oznaczenia pobierania przed utworzeniem i sprawdzeniem paczki.

## English

### Changes since the V21 package

- Updated **449 places across 22 competitions** in England, Spain,
  Poland, Germany and France: **425 division changes**, including 137
  technical lower-boundary movements. Native FM08 capacities/rules
  remain unchanged; additional promotions/relegations follow previous
  final standings.
- Fixed ten missing club-country references responsible for countries
  disappearing from new-game selection. The user confirmed V23.1
  worked after saving it in SI.
- Updated **171 squads / 4156 profiles**: **3984 new**, **172 reused**.
  New ratings comprise 42 FC27 sets and 3942 explicit league/age estimates,
  including 41 selected talents with PA 150-180. Transfermarkt supplies
  squad/identity facts where FC27 does not cover the player.
- Omitted 79 source entries without a known birth year; retained six
  approved January 1 approximations with known years.
- V22 released/retired 24 imported Vorskla players, 35 Santos Cape Town
  players and four weaker duplicates, preserving the selected stronger
  Bernal, Pitarch, Ciria and Quenda profiles and correcting two birth dates.
  V24 additionally released/retired 3169 historical players while preserving
  46 non-player roster entries.

### V24.1 fix

- Corrected **20 Poland U17 profiles wrongly assigned to PSM Makassar**
  by an old Transfermarkt club-ID mapping.
- Reassigned **18 players** to verified clubs or approved parent-club
  representations; preserved UIDs, CA/PA, attributes, personalities and DOB.
  Updated ownership, main contract links and conflicting shirt numbers.
- Technically retired **Mateusz Grygier and Adam Garwolinski** on
  2007-07-30 because their clubs are absent from this native database.
  This is an approved adaptation, **not a real-life retirement claim**.
- Madej's selected Stal Rzeszow profile is unchanged. Kowalski's inherited
  birth date remains unresolved; only his club was corrected.

**Limitations:** PSM now has no player squad; its real squad was not
imported. No global duplicate/loan/future-transfer cleanup; the previously
reported 160 date conflicts and Madej's other existing Resovia record
were not removed. Staff, stadiums and graphics are not updated.
The engine still starts in 2007, with player dates shifted by 19 years.
Requires FM08 8.0.2 and a **new career**; the launcher is separate/optional.

**Validation:** three-profile pilot, four native rejection tests, full and
independent verification of all 20 edits, the PERSON buffer outside
allowlisted changes, all 23397 clubs and protected files. V24 is unchanged.
**V24.1 SI-editor acceptance and a new-career test remain pending.**
This document is prepared release copy, not a published release or ZIP.

---

README instalacyjny i pelny zakres lokalnej kopii:
[README V24.1](../Dane/db/2627_V24_1/README.md).
Dokumentacja opublikowanej paczki V21 pozostaje w
[DATABASE.md](DATABASE.md); ten opis jej nie podmienia.
