# FM08 Extended - plan zwiekszenia limitow sztabu

Data: 2026-11-06.
Status: plan implementacji; funkcja nie jest wdrozona.
Podstawa: FMExt/fm08_compendium.md, sekcje 1.8-1.9,
audyt trenerow (52 kontrole) i asystentow (54 dodatkowe kontrole).
Analiza launchera i wskazanych ponizej punktow EXE byla tylko odczytowa.

## 1. Przyjety wariant

Uzytkownik wybral dodawanie miejsc do limitu gry i poprosil o prostszy
zakres realizacji. Pierwszy wariant obejmuje **wszystkie kluby**.
Nie wymaga identyfikacji aktualnego menedzera gracza ani filtrowania
wlasciciela klubu. Moze tez zmienic mozliwosci i koszty klubow AI.

Parametry sa ustawiane przed startem gry. Nie przelaczamy patchy podczas
dzialania procesu. Launcher zmienia tylko pamiec uruchomionej gry.
Nowe kontrakty zawarte przez gre beda normalnie zapisywane w karierze.

Trenerzy i asystenci beda wdrazani w dwoch osobnych etapach.
Gotowosc trenerow nie jest dowodem gotowosci wielu asystentow.

## 2. Zasady dzialania i ustawienia

Proponowane pola konfiguracji:

- StaffLimitsEnabled = false;
- AdditionalCoaches = 0;
- AdditionalAssistants = 0.

Brak pol w starym JSON oznacza wylaczone rozszerzenie i zera.
Pozostajemy przy obecnym SchemaVersion=1, dodajac opcjonalne pola,
walidacje i test round-trip. Obecny parser odrzuca nieznane pola;
starszy launcher moze odmowic odczytu nowego pliku konfiguracji.
Trzeba opisac ten przypadek przy aktualizacji i powrocie do starszej wersji.

Propozycja zakresu pierwszego wydania, do potwierdzenia testami:

| Parametr | Zakres poczatkowy | Znaczenie |
|---|---|---|
| Dodatkowi trenerzy | 0-10 | Tyle dodatkowych miejsc w lacznej grupie pieciu rol |
| Dodatkowi asystenci | 0-2 | Docelowo 1-3 asystentow lacznie |
| Modul wylaczony | wszystkie wartosci ignorowane przy instalacji | Oryginalne zachowanie FM08 |

To zakres produktu proponowany do walidacji, nie juz udowodniona
bezpieczna granica silnika. Nie udostepniamy maksymalnej wartosci 127
tylko dlatego, ze w kodzie wystepuja bajtowe liczniki.

Wzory dla zwyklego, kwalifikowanego kontekstu klubu:

    zalecenie_trenerow = natywne_zalecenie + AdditionalCoaches
    prog_blokady_trenerow = zalecenie_trenerow + 2
    limit_asystentow = 1 + AdditionalAssistants

Natywne zalecenie uwzglednia reputacje i istniejaca premie finansowa.
Dodatkowe miejsca trenerow doliczamy jeden raz do kategorii ogolnej.
Pozostale kategorie zachowuja swoje wyliczenia.
Asystent, skaut i fizjoterapeuta nie wchodza do sumy trenerow.

Przyklad demonstracyjny: reputacja 7000, brak premii, +5 trenerow
i +1 asystent. Zalecenie trenerow: 8 -> 13; prog blokady: 10 -> 15;
asystenci: 1 -> 2. Nie sa to jeszcze zaakceptowane ustawienia domyslne.
Domyslnie wszystkie nowe opcje pozostaja wylaczone/zerowe.

## 3. Ustalenia istotne dla implementacji

### 3.1. Wspolne wyliczenie limitow

0x0088F0F0 ma dziewiec wyjsc bajtowych i zwraca ich sume.
Wynik jest uzywany nie tylko przez interfejs kontraktu, ale takze przez
inne sciezki i przygotowanie miejsc personelu.

**Preferowany punkt hooka: 0x0088F2E2**, wspolne wejscie zwyklych
przedzialow reputacji przed premia finansowa i finalnym sumowaniem.

Odczytane instrukcje wejscia:

    0x0088F2E2  mov edx,[esp+0x10]
    0x0088F2E6  mov cl,[edx+0x19]

To 7 bajtow; dalszy kod zaczyna sie od 0x0088F2E9.
W tym miejscu wskaznik wyjscia asystentow jest pod [esp+0x20],
a wskaznik trenerow ogolnych pod [esp+0x34].
Offsety stosu obowiazuja przed dodatkowymi pushami hooka.

Hook ma:

1. zachowac kontekst i wyznaczyc obie wartosci w szerszej arytmetyce;
2. zwiekszyc wyjscie trenerow ogolnych i, jesli wlaczone, asystentow;
3. odtworzyc obie instrukcje oraz wrocic do 0x0088F2E9;
4. pozostawic natywne naliczenie premii i sumowanie dziewieciu wyjsc.

Pozwala to zachowac zgodnosc zwracanego EAX z nowymi wyjsciami.
Samo zmienienie wyjsc bez sumy, np. w wrapperze po powrocie,
mogloby rozjechac liczbe przydzielanych miejsc personelu.

Ten punkt omijaja oryginalne wczesne wyjscia bez wypelnienia danych
oraz specjalna galaz bez zwyklego sztabu, ktora skacze do 0x0088F303.
Ich obsluga ma pozostac natywna.

To kandydat statyczny: przed instalacja wymagany audyt wszystkich
wejsc i skokow do nadpisywanych 7 bajtow, takze w drugim EXE.
Sprawdzic granice instrukcji, tablice skokow, relokacje oraz kolizje
z innymi patchami. Nie deklarowac tego hooka jako przetestowanego.

### 3.2. Trenerzy

Bramka 0x008D9F20 wywoluje wspolny kalkulator przy 0x008DA005.
Nastepnie sumuje piec wyjsc i dodaje 2 przy 0x008DA026.

W pierwszym wariancie nie zmieniamy tej bramki. Dostaje juz podniesione
wyjscie, wiec powinna podniesc prog o zadana liczbe miejsc.
Helper kontraktu pobiera te same wyjscia - trzeba sprawdzic zgodnosc UI
po ponownym otwarciu oferty i po wczytaniu kariery.

Dodatkowe miejsca sa wspolne dla pieciu rol. Nie zmieniamy naraz
limitow kazdej kategorii o N, bo daloby to lacznie +5*N.

### 3.3. Asystenci: poprawny licznik i bramka odmowy

Nie wystarczy podniesc wyjscia asystentow w kalkulatorze.
0x008DA0E6 wywoluje 0x00C62B80, a 0x008DA0EB..0x008DA0ED
odrzuca nowy kontrakt po dowolnym dodatnim wyniku.

0x00C62B80 nie jest poprawnym licznikiem unikalnych osob: wyszukuje
pierwszego asystenta dla kolejnych druzyn i moze trafic wielokrotnie
na te sama osobe.

Nowe ustalenie pomocne do prototypu:

- 0x00C629C0 nadal zbiera tylko pierwsze znalezienia; nie nadaje sie
  bezposrednio do liczenia wszystkich asystentow.
- **0x00C62A30** przechodzi przez cala liste personelu kazdej druzyny
  i filtruje role predykatem 0x00C8C010. Jest kandydatem na natywne
  zrodlo pelnej listy, ale jego ABI, kontener wyjsciowy, wlasnosc
  pamieci, warianty osob i powtorzenia wymagaja osobnego audytu.

Docelowy CountUniqueAssistants(CLUB):

- przeglada rzeczywistych czlonkow personelu wszystkich druzyn tego CLUB;
- rozpoznaje role 0x14/0x15 przez zweryfikowany predykat;
- deduplikuje po zweryfikowanym kanonicznym wskazniku osoby,
  bez trwalego cache adresow pomiedzy wczytaniami;
- odroznia obecnych pracownikow od przyszlych kontraktow;
- nie wchodzi automatycznie do oddzielnych klubow B/U23;
- obsluguje przekroczenie zakresu i bledne dane bez uznawania ich
  za zero wolnych miejsc/zatrudnionych.

Preferencja: lokalna enumeracja w kodzie gry, bez kontaktu z launcherem
podczas negocjacji. O wyborze natywnego enumeratora lub wlasnego
przejscia przez kolekcje zdecyduje audyt - nie zgadywac kontenera C++.

Kandydat do podmiany pojedynczego miejsca w bramce:
0x008DA0E4 (mov ecx,eax; call 0x00C62B80), razem 7 bajtow.
W tym miejscu EAX zawiera juz rozwiazany klub.

Adapter ma zwrocic AL=0, gdy liczba unikalnych asystentow jest mniejsza
od limitu, oraz AL=1, gdy limit osiagnieto/przekroczono.
Powrot pod 0x008DA0EB zachowa oryginalny test, skok i powod odmowy 0x35.
To propozycja do weryfikacji ABI i wejsc, nie gotowy payload.

Nie podmieniac globalnie wszystkich wywolan 0x00C62B80.
Inni callerzy uzywaja tej funkcji do pytan o obecnosc i wybor pojedynczej
osoby. Zmiana semantyki calego gettera rozszerzylaby zakres patcha.

Niezaleznie dostosowac dwa odczyty liczby w helperze kontraktu:
call 0x00C62B80 przy 0x0058E345 i 0x0058E3C5.
Tam potrzebna jest rzeczywista liczba, a nie boolean odmowy.
Zalecenie 1+A pochodzi juz ze wspolnego kalkulatora.

### 3.4. Wiele asystentow a funkcje jednego asystenta

0x00C9DFA0 i wiele jego callerow wybiera jedna osobe.
Podniesiony limit nie oznacza sumowania bonusow, kilku rownoleglych
doradcow ani mozliwosci wyboru dowolnego asystenta w kazdym panelu.

Przed udostepnieniem asystentow trzeba potwierdzic:

- dwie/trzy osoby rzeczywiscie pozostaja zatrudnione w tej roli;
- obie sa widoczne w sztabie, maja osobne kontrakty i mozna je zwolnic;
- zadania treningowe i raporty dzialaja zgodnie z mozliwosciami FM08;
- tam, gdzie gra potrzebuje jednej osoby, jej natywny wybor jest
  przewidywalny i nie prowadzi do bledu po zmianie skladu sztabu;
- zapis/wczytanie i aktualizacja kadry nie redukuja ich do jednej osoby.

Pierwsza wersja nie dodaje selektora glownego asystenta ani nie
przepisuje wszystkich funkcji zwracajacych jedna osobe.
Jesli do poprawnego dzialania wielu asystentow bedzie potrzebna taka
przebudowa, trzeba rozszerzyc projekt przed udostepnieniem tej opcji.
W tym czasie trenerzy moga byc wydani niezaleznie.

AI zachowuje wlasne decyzje o zatrudnianiu. Podniesienie limitu nie jest
poleceniem wypelnienia kazdego miejsca ani dowodem, ze wszystkie kluby AI
same zatrudnia kilku asystentow.

## 4. Integracja z istniejacym launcherem

| Plik | Planowana zmiana |
|---|---|
| src/FmLauncher/StaffLimitPolicy.cs | Nowa walidowana polityka, dwa przyrosty, ograniczenia i opis |
| src/FmLauncher/GameStaffLimitsPatch.cs | Nowy emiter x86 i kotwice binarne; osobne wejscia limitow, licznika i odmowy |
| src/FmLauncher/SuspendedGameProcess.cs | ApplyStaffLimits; preflight, alokacja danych/kodu i instalacja przed Resume |
| src/FmLauncher/GameLauncher.cs | Przekazanie polityki; wymuszenie sciezki suspended, gdy modul jest aktywny |
| src/FmLauncher/Configuration.cs | Opcjonalne pola, domyslne zera, walidacja zakresow i zgodnosc JSON |
| src/FmLauncher/MainForm.cs | Kafel Sztab, przelacznik, dwa pola dodatkowych miejsc i opis globalnego zakresu |
| src/FmLauncher/FmLauncher.languages.json | Pelne etykiety, bledy i opisy PL/EN |
| tests/FmLauncher.Tests/StaffLimitsTests.cs | Polityka, konfiguracja, kontrakt binarny, instalacja i scenariusze graniczne |
| tests/FmLauncher.Tests/StaffNativeFixture.cs | Wykonanie rzeczywistego payloadu x86 w izolowanej fixture |
| tests/FmLauncher.Tests/FmLauncher.Tests.csproj | Wlaczenie nowego pliku do kompilacji fixture x86, a nie glownego testhosta x64 |
| README.md, DOCUMENTATION.md, PL.md, EN.md | Obsluga, wzory, globalny zakres, limity i trwalosc zatrudnienia |

Uzyc obecnych NativeCode oraz mechanizmu Allocate/Protect/Flush.
Nie tworzyc drugiego launchera, skryptu nadpisujacego EXE ani edytora save.

Instalacja:

1. Walidacja konfiguracji oraz SHA256 przez OpenVerifiedGame.
2. Rozpoznanie dokladnego profilu EXE i sprawdzenie wszystkich miejsc
   potrzebnych dla wybranej kombinacji ustawien.
3. Utworzenie procesu zawieszonego, odczyt i porownanie bajtow procesu.
4. Instalacja kompletu wymaganych hookow i parametrow.
5. Resume dopiero po powodzeniu calej instalacji.

Przy bledzie proces pozostaje niewznowiony i jest zamykany przez
istniejacy SuspendedGameProcess.Dispose. Nie uruchamiac gry z czescia
zamowionych zmian ani nie ignorowac bledu asystentow.

Trenerzy=0 i asystenci=0: zadnych hookow tego modulu.
Tylko trenerzy: bez licznika/asystenckich hookow.
Asystenci: wspolny kalkulator oraz nowy licznik, bramka i odczyty UI.

Launcher dopuszcza obecnie dwa hashe:
157F484B...1B62D i 32046D2A...BC4F4.
Dotychczasowe audyty sztabu dotycza tylko pierwszego.
Drugi wymaga niezaleznego sprawdzenia kodu, offsetow i fixture.
Samo dopuszczenie go przez inny modul nie potwierdza zgodnosci sztabu.

## 5. UX i zachowanie kariery

Kafel Sztab:

- przelacznik Zwieksz limity sztabu, domyslnie wylaczony;
- Dodatkowi trenerzy: +N;
- Dodatkowi asystenci: +A;
- krotka informacja Dotyczy wszystkich klubow. Wymaga ponownego uruchomienia gry;
- opis, ze asystenci 1+A, a trenerzy zachowuja natywny zapas +2;
- techniczne adresy i diagnostyka tylko w trybie zaawansowanym.

Do czasu zakonczenia etapu wielu asystentow nie prezentowac pola
asystentow jako dzialajacej funkcji. W wydaniu tylko z trenerami
konfiguracja nie moze przyjac aktywnego A>0.

Ustawienia okreslaja limity, nie zatrudniaja automatycznie pracownikow.
Domyslne place i pozostale warunki kontraktow nadal sa obslugiwane przez gre.

Wylaczenie lub zmniejszenie limitow nie zwalnia nikogo i nie odwraca
kontraktow zapisanych w karierze. Po osiagnieciu/przekroczeniu nowego
progu blokowane sa kolejne zatrudnienia. Dokladne zachowanie odnowien,
przywrocenia oryginalnych limitow i tygodniowych aktualizacji jest
obowiazkowym przedmiotem testu kariery.

## 6. Kolejnosc realizacji i warunki zakonczenia

### Etap A - domkniecie kontraktu binarnego

- Sprawdzic oba hashe i wszystkie skoki do planowanych miejsc hookow.
- Przesledzic wszystkich szesciu bezposrednich callerow 0x0088F0F0,
  wykorzystanie sumy i bajtowe rozmiary/przydzialy personelu.
- Potwierdzic zachowanie wszystkich dziewieciu wyjsc, EAX oraz
  wczesnych/specjalnych sciezek bez odczytu niewypelnionych wyjsc.
- Audyt 0x00C62A30, sposobu wstawiania/usuwania personelu,
  tozsamosci osoby, aktualnych i przyszlych umow i selekcji asystenta.
- Ustalic, gdzie finalnie jest ponawiana kontrola przed podpisaniem:
  kilka rownoczesnych ofert nie moze ominac docelowego limitu.

Wynik: wersjonowany zestaw kotwic, ABI i przypadkow granicznych.
Brak tego wyniku blokuje kod danego hooka.

### Etap B - trenerzy od polityki do kariery

- Dodac konfiguracje, polityke i hook wspolnego kalkulatora.
- Zachowac natywna finansowa premie, wyjatki i zapas +2.
- Sprawdzic interfejs kontraktu i przekroczenie starego progu w grze.
- Dopiero po testach dodac dzialajace sterowanie do UI i dokumentacje.

Wynik: samodzielnie dzialajace dodatkowe miejsca trenerow.

### Etap C - prototyp kilku asystentow

- Najpierw poprawny licznik unikalnych osob i jego fixture.
- Potem podmiana lokalnej bramki odmowy i odczytow helpera.
- Minimalny test: zatrudnienie drugiego asystenta z A=1,
  odmowa trzeciego oraz poprawny zapis/odczyt obu.
- Nastepnie A=2 i trzy osoby, role laczone, zwalnianie, raporty i trening.
- Potwierdzic, ze nie ma nadpisywania slotu poprzedniej osoby ani
  automatycznego usuwania nadmiarowych asystentow.

Wynik: opcja asystentow dostepna dopiero po potwierdzeniu tych zachowan.

### Etap D - testy wspolne i wydanie

- Polaczyc oba warianty i pozostale moduly.
- Test dluzszej symulacji na kopii kariery i sprawdzenie klubow AI.
- Aktualizacja dokumentacji i zapakowanie launchera w obecnym procesie
  wydawniczym. Publikacja jest osobna czynnoscia, poza tym planem.

## 7. Matryca weryfikacji

| Warstwa | Wymagane przypadki |
|---|---|
| Polityka / JSON / UI | stare pliki, nowe round-trip, domyslne OFF, zera, bledne zakresy, PL/EN, ustawienia zmieniane przy uruchomionej grze dopiero na nastepny start |
| Kalkulator x86 | 1999/2000, 3999/4000, 5999/6000, 7999/8000; premia on/off; przyrosty 0/min/max; dziewiec wyjsc i zgodna suma |
| Wyjatki x86 | cache 5/-1, brak klubu, kontekst niekwalifikowany, specjalna galaz z zerowym sztabem; brak nowego odczytu niewypelnionych wyjsc |
| ABI i hooki | stos, rejestry callee-saved, wymagane flagi, FPU, odtworzenie instrukcji, skoki wewnetrzne, brak kolizji |
| Asystenci | zero, limit-1, limit, ponad limit; ta sama osoba na kilku listach, wiele osob w jednej druzynie, 0x14/0x15, rozne podtypy i wirtualne bazy PERSON |
| Negocjacje | nowy kontrakt, odnowienie, zmiana roli, zawodnik/asystent, kontrakt na przyszlosc, kilka oczekujacych ofert, kontrola w momencie finalnego zatrudnienia |
| Instalacja | oba EXE po niezaleznym audycie, modul OFF, zera, tylko trenerzy, tylko asystenci, oba, niezgodne bajty i przerwanie przed Resume |
| Kariery | klub z jedna druzyna oraz rezerwami/mlodzieza, oddzielny klub B/U23, nowa i istniejaca kariera, zapis/odczyt, zwolnienie i ponowne zatrudnienie |
| Wiele asystentow | listy, kontrakty, trening, raporty, wybor jednej osoby w funkcjach singularnych, tygodniowa/sezonowa aktualizacja |
| Regresja | PA, starzenie, panele, reputacja lig, reguly meczowe; wlaczone osobno i razem; EXE na dysku bez zmian |

Do wykonania wykorzystac obecna infrastrukture testow x86 oraz
uruchamiania prawdziwego FM08 jako suspended. Sam pozytywny start
zawieszony nie dowodzi dzialania negocjacji ani wielosezonowej stabilnosci.

Proponowane osobne polecenie testow:
FmLauncher.Tests --staff-limits <fm.exe>.
Dokladne scenariusze kariery dokumentowac z UID klubu, stanem licznikow,
data, ustawieniami i wynikiem podpisania umowy - nie tylko zrzutem UI.

## 8. Definicja gotowosci

Funkcja jest gotowa po spelnieniu lacznie:

1. Jedno zrodlo polityki dla UI limitow i rzeczywistej odmowy.
2. Mozliwosc zatrudnienia ponad oryginalny prog do nowego limitu,
   z poprawna odmowa kolejnej osoby.
3. Brak uszkodzenia/utraty poprzednich pracownikow po zapisie i wczytaniu.
4. Potwierdzone zachowanie wielu asystentow w zadaniach gry, jesli ta
   opcja jest udostepniana.
5. Poprawne instalowanie i wylaczanie modulu oraz regresja innych patchy.
6. Jawne rozroznienie statycznych dowodow, fixture x86 i testow kariery.

Najkrotsza droga do pierwszego dzialajacego wydania:
**globalne +N trenerow**, potem **+A asystentow** po weryfikacji
przechowywania wielu osob i zastapieniu licznika obecnosci.
