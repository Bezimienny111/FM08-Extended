# FM08 Extended - plan paneli zawodnika

Data: 2026-11-05.
Status: plan wdrozenia; opisane ponizej nowe panele nie sa jeszcze gotowe.

## 1. Cel i zakres

Dodac do profilu zawodnika dwa niezalezne rozszerzenia:

1. **Pozycja** w menu widokow: wybor pozycji i wyroznianie istotnych
   atrybutow bez zmiany ich wartosci.
2. **Ukryte atrybuty**: dodatkowy panel pod obecnymi kolumnami atrybutow,
   w miejscu zaznaczonym przez uzytkownika.

Udostepnic instalacje rozszerzen z zakladki **Skorki** launchera.
Najpierw obsluzyc jedna potwierdzona skorke, pozniej rozszerzac zgodnosc.
Nie obiecywac dzialania na dowolnej skorce ani samego XML jako rozwiazania
wszystkich ograniczen silnika.

Poza pierwszym wdrozeniem:

- oceny procentowe i prognozy potencjalu Genie Scout;
- edycja atrybutow, zapisow kariery i baz;
- pobieranie baz i facepackow;
- automatyczne przepakowywanie dowolnych archiwow FMF;
- przebudowa calego profilu i zmiany niezwiazanych paneli.

## 2. Stan obecny - sprawdzone punkty zaczepienia

- [SkinPanelInstaller.cs](src/FmLauncher/SkinPanelInstaller.cs) instaluje
  luzne XML dla skorki domyslnej oraz Steklo Black / Left Black.
  Obsluguje cztery konkretne panele, nie nowy panel profilu zawodnika.
- Instalator odczytuje zasoby FMF, uwzglednia konkretne lancuchy dziedziczenia,
  robi kopie istniejacych plikow i probuje cofnac zapis po bledzie.
  Nie jest jeszcze ogolnym instalatorem dla kazdej skorki.
- [GamePanelPatch.cs](src/FmLauncher/GamePanelPatch.cs) dostarcza wlasne
  wlasciwosci zmeczenia i CA/PA oraz integracje z panelem treningu.
  Ma kontrole typu obiektu i ograniczenia dostepu do danych wlasnego klubu.
  Nie potwierdza to jeszcze dzialania ukrytych cech na ekranie profilu.
- [SkinGuidePage.cs](src/FmLauncher/SkinGuidePage.cs) udostepnia instalacje
  i instrukcje. Instalowanie wymaga zamknietej gry.
- Istnieja testy paneli w
  [PanelTests.cs](tests/FmLauncher.Tests/PanelTests.cs).
- Z analizy Genie Scout mamy tabele wag 11 grup pozycji. To model zewnetrzny,
  nie oficjalne wymagania silnika FM08. Wyniki analizy statycznej nie sa
  jeszcze walidacja ocen na rzeczywistych profilach.

Nie przenosic offsetow ani identyfikatorow obiektow Genie do FM08.
Nie traktowac UID, wskaznika PERSON i indeksu rekordu jako tego samego.

## 3. Docelowe zachowanie

### A. Wyroznianie wedlug pozycji

Preferowany interfejs: **Tryby widoku -> Pozycja -> wybrana pozycja**.
Na poczatek: GK, SW, DC, DL/DR, WBL/WBR, DM, MC, AMC,
ML/MR/AML/AMR, szybki napastnik i napastnik typu target.
Nazwy w grze po polsku i angielsku, bez wymagania znajomosci skrotow.

- Opcja **Bez wyrozniania** przywraca zwykly wyglad.
- Kluczowe cechy: pogrubiona nazwa i wyrazniejsze tlo.
- Wazne cechy: subtelniejsze tlo.
- Kolory wartosci nadal oznaczaja poziom atrybutu; nie nadpisywac ich
  kolorem znaczenia pozycyjnego.
- Dodac legende i nie polegac tylko na kolorze.
- Wyroznienie dotyczy widocznych atrybutow; nie ujawnia ukrytych cech.
- Brak oceny 0-100 i brak prognozowania rozwoju w pierwszej wersji.
- Wstepnie wybrany widok pozostaje podczas przegladania kolejnych graczy.
  Zakres zapamietywania po wyjsciu z gry wymaga sprawdzenia mechanizmu widokow.

Wagi przechowywac jako wspolna, jawna tabele. Przed implementacja zatwierdzic
progi kategorii "kluczowe" i "wazne"; nie przyjmowac ich jako faktu z Genie.
Sprawdzic osobno profil bramkarza i brak atrybutu w danym wariancie panelu.

### B. Panel ukrytych atrybutow

Naglowek **Ukryte atrybuty**, ponizej obecnych trzech grup.
Uklad dopasowuje liczbe kolumn do miejsca; przy malej wysokosci umozliwia
przewijanie lub zwijanie, zamiast nachodzic na sekcje Szczegoly.

Pierwszy zestaw kandydatow:

- regularnosc, wazne mecze, podatnosc na kontuzje, nieczysta gra;
- profesjonalizm, ambicja, lojalnosc, presja;
- temperament, sportowa postawa, kontrowersyjnosc, adaptacja.

Kazde pole wlaczyc dopiero po potwierdzeniu znaczenia, skali i zrodla danych.
Cechy osobowosci moga nalezec do PERSON, a pozostale do czesci PLAYER;
nie zakladac wspolnego ukladu rekordu.

- Odczyt zawsze dotyczy aktualnie ogladanej osoby.
- Przy zmianie osoby najpierw uniewaznic stare wartosci.
- Brak danych wyswietlac jako kreske / **Niedostepne**, nigdy jako zero.
- Po wylaczeniu funkcji nie pozostawiac ostatnich odczytanych danych.
- Nie przeliczac blednych odczytow do przedzialu 1-20.
- CA/PA pozostawic poza pierwsza wersja panelu; ewentualne dodanie osobno.

## 4. Decyzje do zatwierdzenia przed wdrozeniem

1. Skorka i jej dokladny folder do pierwszego prototypu; nie identyfikowac
   skorki wylacznie na podstawie wygladu zrzutu ekranu.
2. Ukryte cechy tylko wlasnego klubu czy wszystkich ogladanych zawodnikow?
   Istniejacych ograniczen wlasnego klubu nie zdejmowac przy okazji zmian.
3. Czy obsluga rozgrywki sieciowej jest wymagana? Do czasu potwierdzenia
   bezpiecznego ograniczenia dostepu nowy panel pozostaje nieobslugiwany
   w multiplayerze, z jawnym komunikatem.
4. Progi i ostateczne nazwy grup wyrozniania pozycyjnego.

Proponowane ustawienia: dwa osobne przelaczniki launchera, domyslnie OFF:
**Wyroznianie atrybutow pozycji** oraz **Pokaz ukryte atrybuty**.
Ustawienia gracza dostepne bez trybu zaawansowanego; diagnostyka pod nim.

## 5. Kolejnosc realizacji i bramki akceptacji

### Etap 1 - audyt skorki i powiazania z zawodnikiem

- Zidentyfikowac rzeczywisty panel profilu, jego rodzicow, podwidoki,
  menu i kontrolki atrybutow w wybranej skorce.
- Ustalic, ktore zasoby sa lokalne, dziedziczone lub pochodza z FMF.
- Sprawdzic natywne wlasciwosci ukrytych cech i warunki ich udostepniania.
- Przesledzic zmiane osoby w profilu, odswiezanie i niszczenie panelu.
- Dla kazdego nowego pola spisac: nazwe, skale, typ obiektu, zweryfikowany
  sposob odczytu, ograniczenia i dowod testowy.

**Bramka:** znany panel, pewna identyfikacja ogladanego zawodnika i decyzja,
czy wystarczy XML, czy potrzebne jest rozszerzenie natywne. Brak dowodu
oznacza blokade danego pola, nie zgadywanie offsetow.

### Etap 2 - minimalny prototyp XML na kopii skorki

- Utworzyc kopie testowa, nie edytowac aktywnej skorki gracza.
- Dodac jeden widok pozycyjny, np. srodkowy obronca, oraz powrot do zwyklego.
- Dodac miejsce na ukryte cechy z oznaczeniem braku danych.
- Sprawdzic menu, uklad, kolory i profil bramkarza.
- Jesli podmenu nie jest wspierane, sprawdzic liste nazwanych wariantow
  w istniejacym menu. Zmiane UX przedstawic do akceptacji.
- Jesli XML nie daje wymaganej interakcji, zatrzymac ten wariant i ocenic
  koszt integracji natywnej, zamiast deklarowac gotowa funkcje.

**Bramka:** oba uklady sa czytelne i nie psuja istniejacych widokow.

### Etap 3 - rzeczywiste dane ukrytych cech

- Najpierw uruchomic jedno pole, porownac z niezaleznym odczytem tego samego
  zawodnika i tego samego stanu kariery; potem rozszerzyc zestaw.
- Preferowac zweryfikowane natywne wlasciwosci. Gdy ich brak, rozszerzyc
  istniejacy mechanizm wlasciwosci tylko w potrzebnym zakresie.
- Zweryfikowac obiekty PLAYER, PERSON i PLAYER/STAFF oraz ich czas zycia.
- Nie uzywac globalnej ostatniej osoby jako zrodla dla wszystkich paneli.
- Zachowac ABI, rejestry, stos, wlasnosc lancuchow i oryginalna sciezke
  dla wlasciwosci spoza rozszerzenia.
- Rozpoznawac obslugiwany EXE, sprawdzac sygnatury przed hookiem i bezpiecznie
  odmawiac instalacji na nieznanej wersji.
- Tylko odczyt danych zawodnika; hooki, jesli konieczne, w pamieci procesu.
  Bez modyfikowania oryginalnego EXE i danych kariery na dysku.
- Rozdzielic bledy: widoczny stan niedostepnosci dla gracza oraz ograniczona
  diagnostyka przyczyny. Bez zalewania logow kazdym odrysowaniem.

**Bramka:** brak cudzych lub przestarzalych danych po szybkiej zmianie profilu,
wczytaniu kariery i zamknieciu panelu.

### Etap 4 - komplet widokow pozycyjnych

- Dodac wszystkie zatwierdzone grupy ze wspolnej tabeli.
- Stosowac przewidywalne kategorie wyrozniania i lokalizowana legende.
- Potwierdzic, ze wybor pozycji nie zmienia zawodnika, jego znajomosci
  pozycji ani danych zapisu.
- Sprawdzic wspoldzialanie z wlaczonym i wylaczonym panelem ukrytych cech.

**Bramka:** wszystkie grupy maja test przypisania atrybutow i przywracania
zwyklego widoku.

### Etap 5 - instalator i launcher

- Rozszerzyc obecny instalator, nie tworzyc drugiego konkurencyjnego.
- Lista wykrytych skorek i status: **zgodna**, **wymaga sprawdzenia**,
  **nieobslugiwana**, z przyczyna.
- Uogolnic odczyt dziedziczenia, wykrywac cykle, braki i niejednoznacznosci.
- Pierwsze wydanie: rozpakowane skorki XML o potwierdzonej strukturze.
  Nie przepisywac archiwow FMF uzytkownika.
- Modyfikowac tylko rozpoznane wezly. Nie zastapowac calego panelu wzorcem
  z innej skorki. Stosowac unikalne, sprawdzone identyfikatory kontrolek.
- Przed zapisem wykonac pelny plan zmian i walidacje wszystkich wynikow.
- Instalacje blokowac podczas dzialania gry, rowniez przy ponownej kontroli
  bezposrednio przed zapisem.
- Zachowac kopie i manifest: wersja dodatku, pliki utworzone/zmienione,
  hash przed i po instalacji. Powtorna instalacja nie dodaje duplikatow.
- Blad zapisu uruchamia rollback; blad rollbacku musi byc jawnie zgloszony.
- **Cofnij instalacje** przywraca tylko pliki nadal zgodne z manifestem.
  Przy pozniejszych edycjach gracza zatrzymac cofanie i pokazac konflikt.
  Nowe pliki usuwac tylko po potwierdzeniu ich pochodzenia i hasha.
- Nowe opcjonalne pola konfiguracji domyslnie OFF, zgodne ze starym JSON.
- Wlaczenie funkcji sprawdza gotowosc integracji ze skorka; pokazac instrukcje
  instalacji, restartu gry i przeladowania skorki, gdy sa wymagane.
- Zachowac obecne dzialanie zmeczenia i CA/PA oraz wszystkich innych opcji.

**Bramka:** instalacja, powtorna instalacja, aktualizacja i cofniecie dzialaja
na kopiach skorek bez utraty zmian uzytkownika.

## 6. Walidacja

### Automatyczna

- Transformacje XML: zachowanie cudzych elementow, brak duplikatow,
  brakujace identyfikatory, dziedziczenie, cykle i uszkodzone pliki.
- Instalator: brak uprawnien, czesciowy zapis, rollback, manifest,
  konflikt po recznej edycji i blokada uruchomionej gry.
- Konfiguracja: starszy JSON, niezaleznosc przelacznikow, zapis przez GRAJ,
  tryb gracza/zaawansowany i oba jezyki.
- Natywne fixture x86: poprawne typy i zakresy, brak osoby, zmiana osoby,
  PLAYER/STAFF, wskazniki i czas zycia, ABI oraz oryginalny fallback.
- Testowac konkretne zestawy wyroznien, nie tylko poprawnosc XML.
- Uruchamiac najpierw testy zmienionych powierzchni, potem odpowiednie
  regresje istniejacych paneli i pozostalych hookow.

### W rzeczywistej grze

- Zweryfikowany EXE i kopia testowa skorki; obie wspierane wersje EXE przed
  oznaczeniem ich jako zgodnych z nowymi hookami.
- Co najmniej 10 roznych zawodnikow, w tym bramkarz, zawodnik/personel,
  zawodnik wlasnego i obcego klubu, wolny zawodnik i niepelny profil.
- Co najmniej 100 przejsc miedzy profilami bez starej wartosci, wycieku
  informacji poza dozwolony zakres i crasha.
- Nawigacja wstecz/dalej, ponowne otwarcie widoku, przeladowanie skorki,
  wczytanie innej kariery i zmiana aktywnego menedzera.
- Maly obslugiwany rozmiar okna, 1366x768 i 1920x1080; brak nachodzenia
  panelu na Szczegoly, przyciec nazw i utraty dostepu do menu.
- Porownanie wartosci z niezaleznym odczytem; puste dane to nie sukces.
- Pomiar kosztu przed/po na tej samej scenie i sprzecie; przed publikacja
  ustalic i zapisac budzet opoznienia. Bez pelnego skanowania bazy na klatke.
- Zweryfikowac brak zmiany atrybutow i brak dodawania danych rozszerzenia
  do zapisu kariery; nie wymagac identycznego hasha dwoch zapisow gry.

## 7. Publikacja i kryterium gotowosci

1. Wydanie testowe dla jednej potwierdzonej skorki.
2. Akceptacja wygladu i zachowania obu funkcji przez uzytkownika.
3. Dopiero potem adaptery dla kolejnych rozpoznanych skorek.
4. README i instrukcje PL/EN: zakres, ograniczenia, wlaczanie, reload
   i cofanie. Nie opisywac funkcji jako uniwersalnej.
5. Publikacja launchera z kopia poprzednich plikow programu, przy zamknietej
   aplikacji i zachowaniu konfiguracji, profili, baz oraz zapisow.
6. Smoke-test zainstalowanego launchera i kontrola zachowania plikow gracza.

Funkcja jest gotowa dopiero po testach jednostkowych/natywnych,
potwierdzeniu dzialania w FM08 i akceptacji UI. Te trzy potwierdzenia
nie zastepuja sie wzajemnie.

## 8. Najblizszy krok

Potwierdzic folder skorki ze zrzutu oraz zakres dostepu do ukrytych cech.
Nastepnie wykonac etap 1 i maly prototyp na kopii tej skorki.
Na tym etapie nie modyfikowac aktywnej instalacji ani zapisu kariery.
