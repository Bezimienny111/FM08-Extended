# FM08 Extended — dokumentacja

[Projekt](README.md) · [Instalacja PL/EN](INSTALLATION.md) ·
[Funkcje po polsku](PL.md) · [Features in English](EN.md)

Dokumentacja aktualnego kodu launchera. Integracje z silnikiem FM08 są
eksperymentalne. Test kodu natywnego, poprawny start do menu i wielosezonowy
test kariery to różne poziomy potwierdzenia — nie zastępują się wzajemnie.

## Spis treści

- [1. Wymagania i zgodność](#1-wymagania-i-zgodnosc)
- [2. Instalacja i pierwszy start](#2-instalacja-i-pierwszy-start)
- [3. Interfejs i konfiguracja sesji](#3-interfejs-i-konfiguracja-sesji)
- [4. Obraz](#4-obraz)
- [5. Zmiany i rezerwowi](#5-zmiany-i-rezerwowi)
- [6. Dynamiczne PA](#6-dynamiczne-pa)
- [7. Opóźnienie starzenia](#7-opoznienie-starzenia)
- [8. Panele zawodników i skórki](#8-panele-zawodnikow-i-skorki)
- [9. Rzeczywista reputacja lig](#9-rzeczywista-reputacja-lig)
- [10. Obserwacja i diagnostyka](#10-obserwacja-i-diagnostyka)
- [11. Pliki i schemat konfiguracji](#11-pliki-i-schemat-konfiguracji)
- [12. Mechanizm integracji i trwałość zmian](#12-mechanizm-integracji-i-trwalosc-zmian)
- [13. Rozwiązywanie problemów](#13-rozwiazywanie-problemow)
- [14. Budowanie, testowanie i publikacja](#14-budowanie-testowanie-i-publikacja)
- [15. Mapa kodu](#15-mapa-kodu)
- [16. Zakres poza aktualnym wydaniem](#16-zakres-poza-aktualnym-wydaniem)

<a id="1-wymagania-i-zgodnosc"></a>
## 1. Wymagania i zgodność

- Windows x64 i **.NET 8 Desktop Runtime x64** do uruchomienia standardowej
  publikacji. Sam .NET Runtime bez składników Desktop nie wystarcza.
- Własna instalacja Football Manager 2008. Projekt nie zawiera gry ani bazy.
- .NET 8 SDK do budowania źródeł i testów.
- Prawo zapisu w katalogu launchera; instalacja paneli wymaga również prawa
  zapisu w wybranym katalogu skórek.
- Integracje natywne obsługują wyłącznie dwa rozpoznane pliki FM08 8.0.2.
  Nazwa `fm.exe` ani informacja o wersji nie wystarczają.

Akceptowane sumy SHA256, zapisane w
[MatchRulePatch.cs](src/FmLauncher/MatchRulePatch.cs):

```text
157F484BE2EAD4AB27006D1002C2C666A7228197B88B14C8D026E76F31B1D62D
32046D2AC71459036B60E72321DFFEEB39A1A8E1A63E6CCBEE6220680E9BC4F4
```

Inny plik jest odrzucany przy aktywnych integracjach. Launcher dodatkowo
sprawdza instrukcje w pamięci przed instalacją hooków. Nie dostarcza
zamiennika EXE ani nie modyfikuje pliku gry na dysku.

Do zwykłego uruchomienia bez patchowania trzeba wyłączyć wszystkie moduły
natywne: obraz, aktywne nadpisania reguł, PA, opóźnienie starzenia, panele,
diagnostykę oraz rzeczywiste zmiany reputacji. Obserwacja lig pozostaje
osobnym narzędziem odczytowym, które także sprawdza zgodność gry.

<a id="2-instalacja-i-pierwszy-start"></a>
## 2. Instalacja i pierwszy start

Pełna [instrukcja instalacji PL/EN](INSTALLATION.md) obejmuje również
pobieranie wydań GitHub, aktualizację i usunięcie aplikacji.

1. Zainstaluj wymagany Desktop Runtime i rozpakuj kompletną publikację
   launchera do katalogu z prawem zapisu.
2. W lokalnym układzie projektu uruchom `app\FmLauncher.exe`.
   Nie przenoś samego EXE bez jego plików towarzyszących.
3. Wskaż bezpośrednio plik gry `fm.exe`, nie zewnętrzny loader.
   Launcher próbuje odnaleźć grę w katalogach nadrzędnych.
4. Opcjonalnie wskaż **folder danych użytkownika FM08**: ten ze skórkami,
   grafiką i zapisami, nie instalacyjny folder `data`.
5. Wybierz język, ustawienia obrazu i potrzebne moduły.
6. Wykonaj kopię kariery przed pierwszym testem funkcji zmieniających grę.
7. Naciśnij **GRAJ / PLAY**, przeczytaj i zaakceptuj potwierdzenie.
   Konfiguracja zostanie zwalidowana i zapisana przed uruchomieniem gry.

Domyślne ustawienia nowej konfiguracji: język angielski, jasny motyw,
tryb gracza, obraz włączony z trybem pełnoekranowym, panele włączone,
PA/starzenie/reputacja/obserwacja/diagnostyka wyłączone. Nadrzędny
przełącznik reguł jest włączony, ale żaden wiersz nie nadpisuje limitów.
Pełny ekran nadal wymaga dodatkowego ręcznego potwierdzenia działania.

Wskazanie folderu użytkownika nie przenosi plików, nie zmienia ustawień
FM08 i nie przekierowuje automatycznie zapisów gry. Służy obecnie m.in.
do podpowiedzi katalogu `skins` w instalatorze.

<a id="3-interfejs-i-konfiguracja-sesji"></a>
## 3. Interfejs i konfiguracja sesji

Interfejs ma dwie zakładki: **Główna / Home** i **Skórki / Skins**.
Funkcje są kartami na stronie głównej, nie osobnymi zakładkami.

- **ON/OFF** decyduje o aktywacji modułu.
- **Szczegóły / Details** rozwija opis i kontrolki; nie włącza funkcji.
- Ustawienia grafiki pozostają widoczne również po zwinięciu opisu.
- Język PL/EN i jasny/ciemny motyw zmieniają się bez restartu launchera
  i bez utraty edytowanych ustawień.
- Systemowe dialogi i część elementów systemowych zachowują wygląd Windows.
- Język tekstów wstrzykiwanych do gry jest wybierany przy jej starcie.
  Zmiana języka launchera nie przestawia już uruchomionej gry.

### Tryb gracza i tryb zaawansowany

Domyślny tryb gracza ukrywa obserwację lig, diagnostykę wczytywania/zdarzeń,
logi i liczniki techniczne oraz ręczne **Zapisz / Wczytaj**.
Tryb zaawansowany udostępnia te narzędzia. Panele skórek i ich instrukcje,
reguły meczowe, rzeczywiste zmiany reputacji oraz profil kariery pozostają
dostępne w trybie gracza.

Ukrycie narzędzia **nie wyłącza jego konfiguracji ani działania**.
Jeżeli ukryta obserwacja lub diagnostyka nadal jest włączona, interfejs
wyświetla informację. Wyjście z trybu zaawansowanego zamyka wewnętrzne
okna logów/raportów, nie proces gry.

### Zapis i uruchamianie

Konfiguracja jest odczytywana przy starcie launchera. GRAJ zapisuje
zaakceptowane ustawienia automatycznie. Anulowanie potwierdzenia nie
zapisuje ich; błąd walidacji lub zapisu blokuje start.

Ręczne **Zapisz** zapisuje konfigurację launchera, a **Wczytaj** odczytuje
ją ponownie z dysku — **nie są to przyciski zapisu/wczytania kariery FM08**.
Zmiany integracji dotyczą następnego procesu gry, nie trwającej sesji.

Dolny pasek otwiera YouTube, Discord i Ko-fi w domyślnej przeglądarce.
Ikona Git pozostaje nieaktywna do skonfigurowania adresu repozytorium.
Dokumentacja nie oznacza, że projekt został już opublikowany.

<a id="4-obraz"></a>
## 4. Obraz

Niezależny moduł oferuje:

| Tryb | Zachowanie |
|---|---|
| Okno | Stały rozmiar klienta, ramka i minimalizacja; bez zmiany rozmiaru/maksymalizacji. |
| Okno bez ramki | Wybrany rozmiar, wyśrodkowany na głównym ekranie; bez rozciągania pulpitu. |
| Pełny ekran | Natywny tryb FM08 z tymczasową zmianą trybu pulpitu; wymaga dalszej ręcznej weryfikacji. |

Lista zawiera wykryte tryby głównego ekranu mieszczące się w pulpicie,
od **640 × 480 do 1920 × 1080**. Dla okna dodatkowo uwzględnia ramkę,
pasek tytułu, obszar roboczy i DPI. Domyślnie preferowane są proporcje
pulpitu, następnie największa pasująca rozdzielczość.

Zmiana trybu może wybrać nowy pasujący rozmiar z komunikatem.
Niedostępna rozdzielczość odczytana z pliku nie jest po cichu zastępowana:
przy aktywnej integracji trzeba ją poprawić przed zapisem/startem.

Launcher wymusza rozmiar okna i bufora renderowania przez całą sesję.
Weryfikuje inicjalizację, rzeczywiste rozmiary, style i DPI. Błąd startu
może zakończyć wyłącznie nowy proces uruchomiony przez launcher.
Minimalizacja nie jest błędem rozmiaru.

Warstwa `HIGHDPIAWARE` dotyczy procesu, bez zmiany rejestru.
Wyłączenie modułu pozostawia natywne zachowanie FM08. Obraz nadal działa
po zamknięciu launchera. Okno i borderless sprawdzono do menu przy
1280 × 720; nie oznacza to walidacji wszystkich ekranów i skórek.

<a id="5-zmiany-i-rezerwowi"></a>
## 5. Zmiany i rezerwowi

Tabela obejmuje **29 kodów reguł, 0–28**. Dla każdego można niezależnie
włączyć nadpisanie liczby zmian i liczby rezerwowych oraz ustawić **0–12**.
Przyciski/strzałki pod tabelą edytują zaznaczony wiersz.
Kliknięcie nagłówka sortuje rosnąco/malejąco; liczby są sortowane liczbowo.
Sortowanie nie zmienia powiązania ustawień z kodem.

Nadrzędne OFF pomija wszystkie nadpisania, ale zachowuje ich wybór
i wartości. ON nie wystarcza: trzeba również zaznaczyć nadpisanie
odpowiedniego limitu w konkretnym wierszu.

Wyłączone nadpisanie wywołuje oryginalny getter, nie globalne „3 zmiany”.
Zachowane zostają m.in. warunkowe 5/7 rezerwowych kodu 22 oraz 10/12
zmian i ławki kodu 28. Nie zmieniamy dodatkowej puli/wyjątków zmian.

### Zakres reguły a konkretna liga

Opisy to **częściowa statyczna mapa**: 45 przypisań do 15 z 29 kodów,
nie skan aktualnej kariery. Pozostałe kody mają nierozpoznany zakres,
nie są automatycznie nieużywane. Ten sam kod może dotyczyć wielu rozgrywek,
etapów i sytuacji. Ustawienie kodu zmienia wszystkie korzystające z niego
mecze, również niewymienione w przykładach.

Przykładowo kod 21 obejmuje polski Puchar Ligi, nie całą polską ligę.
Kod 18 wskazuje amerykański Combine, nie całą MLS.
Pełny katalog i źródła przypisań:
[MatchRuleScope.cs](src/FmLauncher/MatchRuleScope.cs).

Zakres 0–12 jest zakresem udostępnionej integracji, nie gwarancją, że
silnik bezpiecznie obsłuży każdą kombinację. Dostępni rezerwowi mogą
ograniczać liczbę faktycznie wykonanych zmian. Sparingi, rezerwy,
młodzież i dogrywka wymagają osobnych prób w grze.

<a id="6-dynamiczne-pa"></a>
## 6. Dynamiczne PA

CA to bieżące umiejętności, PA — potencjał. Wzrost PA jest opcjonalny,
domyślnie wyłączony i obejmuje **wszystkich kwalifikujących się zawodników**,
nie tylko klub gracza.

Warunki:

- CA i PA w zakresie 1–200, PA < 200, różnica PA−CA od 0 do 4.
- Najwyżej jedno losowanie przy nowej natywnej tygodniowej aktualizacji.
- Sukces daje **+1 PA**, bez bezpośredniej zmiany CA; maksimum PA to 200.
- Odświeżanie ekranów nie daje kolejnych losowań w tej samej epoce.
- Pominięte tygodnie nie naliczają wielu punktów naraz.
- Brak sezonowego limitu punktów; nadal obowiązują warunki kwalifikacji.
- Nieprawidłowy wiek/mentalność powoduje pominięcie, nie neutralny zamiennik.

### Prawdopodobieństwo

```text
M = 0.60 × Profesjonalizm + 0.25 × Ambicja + 0.15 × Determinacja
F_mental = 0.50 + (M − 1) / 19
szansa = min(100%, 8% × F_wiek × F_mental)
```

| Wiek | F_wiek |
|---|---:|
| 14–18 | 1.25 |
| 19–21 | 1.10 |
| 22–24 | 1.00 |
| 25–27 | 0.70 |
| 28–30 | 0.40 |
| 31–33 | 0.15 |
| 34–100 | 0.05 |

Atrybuty mentalne muszą mieścić się w 1–20; mnożnik mentalności wynosi
0.50–1.50. Przykład: zawodnik 18-letni z trzema atrybutami po 20 ma 15%
szansy w kwalifikującym się tygodniu. To losowanie, nie gwarantowany wzrost.

Kod C# i emiter x86 korzystają z jednej polityki
[PaGrowthPolicy.cs](src/FmLauncher/PaGrowthPolicy.cs). Dokładny zapis:

```text
W = 60 × Pro + 25 × Amb + 15 × Det
chanceBP = min(10000, (8 × agePercent × (W + 850) + 950) / 1900)
```

Dzielenie jest całkowite; 1 BP = 0.01 punktu procentowego.
Losowanie używa prywatnego xorshift32 z odrzucaniem niepełnego przedziału,
bez zużywania RNG gry. Współczynniki nie mają obecnie edytora ani
konfiguracji JSON. Historyczne `PaChance` jest zachowywane, ale ignorowane.
Wartość 0 w tym polu **nie wyłącza** aktualnego modelu — służy do tego
`PaEnabled`.

### Dziennik

Tryb zaawansowany udostępnia liczniki i okno wzrostów: nazwisko, imię,
ID, aktualizacja treningu, CA oraz PA przed/po. Dane są pobierane
w momencie wzrostu, również dla zawodników będących członkami sztabu.

Bufor natywny mieści 4096 oczekujących wpisów; utrata jest sygnalizowana.
Launcher odbiera wpisy co sekundę. Dziennik pozostaje do następnego startu
gry lub zamknięcia launchera i **nie jest zapisywany na dysku**.
Błąd odbioru zatrzymuje dziennik, nie mechanizm PA. Sam hook działa
również po zamknięciu launchera.

Zwiększone PA utrwala zwykły zapis kariery. OFF nie cofa wcześniejszych
wzrostów. Regresje kodu natywnego nie zastępują długiego testu kariery.

<a id="7-opoznienie-starzenia"></a>
## 7. Opóźnienie starzenia

Osobny, domyślnie wyłączony moduł, niezależny od PA. Przesuwa o **3 lata**
efektywne progi utraty fizyczności i kary CA za wiek, zachowując indywidualny
wpływ sprawności ogólnej, kontuzjogenności i profesjonalizmu.

Nie zmienia dat urodzenia, wyświetlanego wieku, rozwoju młodych ani
decyzji o emeryturze. Nie gwarantuje grania do określonego wieku.
Osiem sprawdzanych hooków i jedna stała dotyczą gałęzi starzenia
w miesięcznej procedurze, a nie ogólnego gettera wieku.

Patch istnieje tylko w pamięci nowego procesu; efekty rozwoju mogą
pozostać w zapisanej karierze. Wymagany restart gry i test na kopii.
Implementacja: [GameAgingPatch.cs](src/FmLauncher/GameAgingPatch.cs).

<a id="8-panele-zawodnikow-i-skorki"></a>
## 8. Panele zawodników i skórki

Moduł danych jest domyślnie włączony i niezależny od wzrostu PA.
Potrzebuje **zarówno integracji natywnej przy starcie, jak i odpowiednich XML**.
Sam przełącznik nie instaluje plików skórek.

| Ekran | Dodawane informacje |
|---|---|
| Trening zawodnika | Zmęczenie sezonowe i objaśniający tooltip. |
| Skład / Selection | Zmęczenie oraz liczbowe CA i PA; oceny asystenta pozostają. |
| Taktyka / Pozycja | Zmęczenie obok kondycji. |
| Widoki → Edycja | Dodatkowy, uproszczony widok listy; nie zastępuje dotychczasowych. |

Nowe dane są dostępne dla klubu aktywnego ludzkiego menedżera, jego
rzeczywistych rezerw/U23 i wypożyczonych **do** klubu. Nie obejmują
wypożyczonych **z** klubu, osobnych afiliantów, reprezentacji i obcych
zawodników. Brak uprawnienia lub danych daje `----`.
Uprawnienie jest ponownie sprawdzane przed serializacją danych.

### Znaczenie zmęczenia

| Wartość J | Kategoria |
|---|---|
| ≤ 0 | Wypoczęty |
| 1–250 | Normalne |
| 251–374 | Narastające |
| 375–499 | Wysokie |
| ≥ 500 | Bardzo wysokie |

To nie bieżąca kondycja ani diagnoza medyczna. Tooltip opisuje karę 0–40%
do **jednego natywnego mnożnika treningu**, nie spadek całkowitej
efektywności i nie ryzyko kontuzji. Liczbowe dane i sortowanie pozostają
niezmienione; opisy zastępują tekst etykiet.

### Instalator

1. Zamknij grę.
2. W zakładce Skórki wskaż istniejący katalog `skins` użytkownika.
3. Uruchom instalator paneli.
4. W FM08 wyłącz cache skórek, przeładuj skórkę i wybierz dodany widok.
5. Jeżeli zachowany stary widok ukrywa kolumny, zresetuj go lub wybierz
   ponownie widok Edycja.

Obecny instalator rozpoznaje **Steklo Black** (`steklo_black`) oraz
**Steklo Black (Left)** (`steklo_left_black`). Tworzy też luźne nadpisanie
domyślnej skórki `fm2008`, korzystając z archiwów własnej instalacji gry.
**Aktualny kod wymaga co najmniej jednego rozpoznanego wariantu Steklo
w wybranym katalogu, również przy tworzeniu nadpisania skórki domyślnej.**
Nie jest uniwersalnym instalatorem wszystkich skórek.

Wariant Left zachowuje dziedziczenie przez `steklo_left`, następnie
`steklo`; zwykły Black przez `steklo`. Archiwa FMF i panele rodzica
nie są nadpisywane. Zmieniane istniejące pliki otrzymują jednorazową
kopię `.before-fmext-panels`. Powtórzenie identycznej instalacji jest
bez zmian; błędy zapisu wywołują próbę przywrócenia zmienionych plików,
a ewentualne błędy przywracania są zgłaszane.

Instalator przekształca:

```text
panels\player training.xml
panels\team squad.xml
panels\tactic person list.xml
panels\person list table.xml
```

### Własna skórka i cofnięcie instalacji

Zakładka Skórki udostępnia cztery fragmenty XML do kopiowania.
Pola `Fjad`, `Fcab`, `Fpab` muszą być również zarejestrowane w istniejącej
liście `column_display_properties` w `person list table.xml`.
Sam wpis w widoku nie tworzy kolumny bez rejestru.
Trening wymaga kontrolki `Fmjd` wewnątrz tabeli `phpb` oraz wolnego wiersza.
Tooltip korzysta z `Fjht`; dodatkowy widok ma identyfikator `Fmed`.

Fragmenty i transformacje:
[SkinPanelInstaller.cs](src/FmLauncher/SkinPanelInstaller.cs),
instrukcje interfejsu: [SkinGuidePage.cs](src/FmLauncher/SkinGuidePage.cs).
Nie zastępuj całego pliku skórki pojedynczym fragmentem.

Brak automatycznego przycisku odinstalowania. Przy zamkniętej grze można
przywrócić odpowiednie kopie `.before-fmext-panels`; pliki nowo utworzone
nie mają takiej kopii. Przed instalacją wykonaj także własną kopię skórki,
szczególnie jeśli chcesz wracać do jej późniejszych ręcznych modyfikacji.

Znane ograniczenie: lista składu czasem pokazuje surową liczbę zmęczenia.
Przełącz widok i wróć do Edycja. Pełne odświeżanie, sortowanie i wygląd
na wszystkich ekranach kariery nadal wymagają prób w grze.

<a id="9-rzeczywista-reputacja-lig"></a>
## 9. Rzeczywista reputacja lig

Domyślnie wyłączony moduł obejmuje **42 najwyższe ligi europejskie**.
Nie edytuje współczynników UEFA, miejsc pucharowych ani niższych lig.
Włącza też potrzebną diagnostykę roczną/wczytywania i wykrywanie zapisu.
Pozostaw launcher otwarty podczas gry.

### Profil kariery

- **Nowa kariera:** po pierwszym udanym zapisie ręcznym lub autosave
  automat tworzy profil w `profils\<GUID>.json` obok programu,
  używając bazy odczytanej przed zapisem.
- Jeżeli baza nie została pobrana na czas, launcher prosi o kolejny
  zapis; nie odtwarza zmyślonego wcześniejszego stanu.
- **Wczytana kariera:** jeden zgodny profil jest wybierany automatycznie.
  Przy jego braku profil może powstać z aktualnego stanu po udanym
  wczytaniu, o ile nie ma nierozstrzygniętych starszych profili.
  Nie odtwarza to utraconej historycznej bazy.
- Profil znajdujący się poza folderem launchera należy zaimportować,
  zamiast tworzyć nową bazę.
- Kilka zgodnych profili wymaga jawnego wyboru. Stary profil bez klucza
  kariery wymaga jednorazowego wskazania.
- Profile z kluczem ze starego `league-profiles` są kopiowane do `profils`
  bez nadpisywania oryginałów i istniejących plików.
- Nie twórz nowego profilu co sezon. Kopie, zmiana nazwy save i odgałęzienia
  tej samej kariery korzystają z tej samej tożsamości.

Dopasowanie sprawdza natywny token kariery `GAME+0x20`, znaczniki daty
`GAME+0x28/+0x2A/+0x2C`, ligi i kraje. Nazwa pliku i adresy obiektów
nie są trwałym kluczem. Mechanizm ogranicza ryzyko błędnego dopasowania,
ale nie stanowi matematycznego dowodu braku kolizji.

Profil sprzed daty bazowej jest odrzucany. Aktywacja 15 czerwca jest
blokowana; automat ponawia próbę po tej dacie, bez nadrabiania zdarzenia.
Przycisk ponownego wykrywania służy do wznowienia po usunięciu problemu.
Ręczne tworzenie profilu pozostaje trybem awaryjnym.

### Model zmian

```text
cel = round-half-up(clamp(R_start + 1.7 × (sqrt(C_now) − sqrt(C_start)), 1, 20))
```

`R_start` i `C_start` pochodzą z niezmiennego profilu; `C_now` to suma
pięciu zakończonych sezonów współczynnika kraju, nie miejsce w rankingu.
Szósty wpis natywnej historii dotyczy bieżącego sezonu i jest pomijany.

Zmiana następuje **15 czerwca co dwa lata od sezonu bazowego**:
np. baza 2007 → 2009, 2011. Liga przesuwa się najwyżej o **1 punkt**
w stronę celu. Współczynnik 1.7 jest parametrem modelu projektu.
Rzeczywisty writer **nie wymaga dwóch kolejnych zgodnych ocen** —
ten warunek należy do osobnej, starszej symulacji obserwatora.

Normalny zapis FM08 utrwala nowe reputacje. Wczytanie starszego save
przywraca jego stan; po ponownym uzbrojeniu odtworzona linia czasu
może wykonać zdarzenie ponownie. Nie jest to podwójne naliczenie
w tej samej nieprzerwanej sesji/sezonie.

### Kontrola i dziennik

Status profilu nad GRAJ jest widoczny przy włączonej funkcji. Zielony
oznacza aktywację, żółty — oczekiwanie lub wymagane działanie.
Kliknięcie otwiera szczegóły. Nie jest to walidator kompletnej bazy gry.

Tryb zaawansowany udostępnia okno wykonanych zmian i trwały JSONL
w `league-changes`. Zawiera datę, kraj, ligę, poprzednią/nową reputację,
cel i współczynnik. To nie raport symulacji.

Sprawdzane są wszystkie 42 pozycje i pojemność bufora przed zmianą.
Utrata danych/diagnostyki lub błąd logu wstrzymuje kolejne zmiany
z komunikatem. Limit to 1024 zmiany na proces — potem wymagany restart.
Zamknięcie launchera rozbraja writer. Awaria może utracić nieodebrane
wpisy; dziennik nie jest dowodem zapisu kariery na dysku.

Automatyczne dopasowanie profilu sprawdzono po ponownym wczytaniu kariery;
długoterminowy balans i wielosezonowa stabilność wymagają dalszych prób.

<a id="10-obserwacja-i-diagnostyka"></a>
## 10. Obserwacja i diagnostyka

Narzędzia zaawansowane, domyślnie wyłączone. Nie należy utożsamiać ich
z rzeczywistym zapisem reputacji.

### Odczytowa obserwacja lig

Może odczytać zgodny, już uruchomiony proces gry bez instalowania hooków:

1. Wczytaj właściwą karierę i zatrzymaj przetwarzanie.
2. Włącz obserwację i odczytaj **NOWĄ bazę**, potwierdzając karierę.
3. Odczytuj kolejne obserwacje co sezon.
4. Po wczytaniu save, zmianie świata lub restarcie utwórz nową bazę.

Raport pokazuje reputację faktyczną/bazową, współczynnik bazowy/aktualny,
cel, reputację symulowaną i licznik potwierdzeń. Nie zmienia gry.
Starsza symulacja wykonuje krok ±1 po **dwóch zgodnych ocenach rocznych**,
po przekroczeniu 15 czerwca i potwierdzeniu przesunięcia historii.
Licznik wynosi 0 lub 1; druga ocena zeruje go po wykonaniu kroku.
Powtarzanie odczytu w jednym sezonie nie daje kolejnych ocen.

Niestabilne/niepełne dane, cofnięcie daty, pominięcie sezonów albo
nieoczekiwana historia blokują naliczanie. Nie ma cichego uzupełniania
wartości. Raporty JSON w `league-observations` są zapisywane atomowo,
nie są automatycznie łączone ani wznawiane jako profil writera.

### Natywna diagnostyka

Wymaga nowego startu przez launcher. Loguje:

| Zdarzenie | Znaczenie |
|---|---|
| `AnnualHistory` | Roczna gałąź historii UEFA; nie zakończenie całego rocznego przeliczenia. |
| `LoadBegin` | Wejście do loadera z surowym trybem; nie każde wejście jest pełnym wczytaniem. |
| `LoadReturn` | Normalny powrót z wynikiem; nie dowód gotowości całego interfejsu. |

Każde wejście loadera unieważnia poprzednią generację obserwacji.
Odczyt jest chroniony licznikiem otwartych wywołań i kontrolą metadanych.
Wyjątkowe wyjście bez normalnego powrotu może wymagać restartu gry.
Bufor mieści 4096 zdarzeń; kolizje/przepełnienie mają jawny licznik utraty.

JSONL powstaje w `league-diagnostics` przed wznowieniem gry, z identyfikatorem
sesji, PID i kolejnymi zdarzeniami. Błąd zapisu lub utrata blokuje
diagnostykę i chronione odczyty, nie zatrzymuje samej gry.
Zamknięcie launchera kończy odbiór logów; brak wpisu nie dowodzi braku
zdarzenia. Włączenie samych hooków diagnostycznych nie zmienia reputacji.

<a id="11-pliki-i-schemat-konfiguracji"></a>
## 11. Pliki i schemat konfiguracji

Ścieżki są względne wobec folderu aplikacji — w lokalnym układzie to `app`.
Nazwa produktu to FM08 Extended; kompatybilne nazwy plików `FmLauncher.*`
pozostają bez zmian.

| Plik/katalog | Przeznaczenie |
|---|---|
| `FmLauncher.exe`, `.dll`, `.deps.json`, `.runtimeconfig.json` | Program i pliki wymagane do uruchomienia publikacji zależnej od runtime. |
| `FmLauncher.pdb` | Symbole debugowania, jeżeli dołączono je do publikacji. |
| `FmLauncher.languages.json` | Zewnętrzny katalog tłumaczeń UTF-8. |
| `FmLauncher.config.json` | Ustawienia launchera; powstają po zapisie lub zatwierdzonym GRAJ. |
| `profils` | Niezmienne profile bazowe kariery i ich tożsamość. |
| `league-profiles` | Starszy katalog profili, źródło zgodnej migracji. |
| `league-changes` | Trwałe dzienniki rzeczywistych zmian reputacji. |
| `league-observations` | Raporty odczytu i starszej symulacji. |
| `league-diagnostics` | Dzienniki natywnych zdarzeń. |

PA nie ma trwałego pliku dziennika. Kopie paneli leżą przy zmienianych
XML w katalogu skórek, nie w powyższych folderach.

### Schemat 1

Źródło: [Configuration.cs](src/FmLauncher/Configuration.cs).
Pola opcjonalne uzupełniają starsze konfiguracje bez automatycznego
przepisywania pliku.

| Pole | Znaczenie / zachowanie |
|---|---|
| `SchemaVersion` | Wymagane `1`; inna wersja jest odrzucana. |
| `Language` | Kod języka; nowa konfiguracja `en`. |
| `GamePath` | Ścieżka do bezpośredniego EXE gry. |
| `UserDataPath` | Opcjonalna pełna ścieżka folderu użytkownika; domyślnie pusty tekst. |
| `MatchRulesEnabled` | Nadrzędne reguły; domyślnie `true`, bez aktywowania wierszy. |
| `DarkMode` | Opcjonalny ciemny motyw; brak = `false`. |
| `AdvancedMode` | Opcjonalny tryb zaawansowany; brak = `false`. |
| `DisplayMode` | Tekst: `Fullscreen`, `Window`, `Borderless`. |
| `DisplayOverride` | Brak w starszym pliku = `false`; nowa konfiguracja = `true`. |
| `Resolution` | Obiekt `Width`, `Height`; aktywny obraz wymaga dostępnego trybu. |
| `PaEnabled` | Wzrost PA; nowa konfiguracja `false`. |
| `PaChance` | Wymagane pole zgodności 0–100; zachowywane, ignorowane przez aktualny model. |
| `PanelInformationEnabled` | Brak = `true`; dane paneli wymagają też XML. |
| `AgingDelayEnabled` | Brak = `false`; opóźnienie starzenia. |
| `LeagueChangesEnabled` | Brak = `false`; rzeczywiste zmiany reputacji. |
| `LeagueReputationEnabled` | Brak = `false`; wyłącznie obserwator. |
| `LeagueDiagnosticsEnabled` | Brak = `false`; osobna diagnostyka; writer instaluje ją także dla własnych potrzeb. |
| `Rules` | Dokładnie 29 różnych wpisów, po jednym dla każdego kodu 0–28. |

Wpis `Rules`: `Code`, `Override` (zmiany), opcjonalne `BenchOverride`
(brak = `false`), `Substitutions`, `Bench`. Aktywne nadpisania wymagają
wartości 0–12. Historyczne nieaktywne wartości do 127 są zachowywane,
nie przycinane; przed ich aktywacją trzeba je poprawić w tabeli.

Nieznane pola JSON są odrzucane. Zapis używa pliku tymczasowego,
`Flush(true)` i atomowego zastąpienia/przeniesienia. Błędny plik blokuje
zapis i start zamiast nadpisania go wartościami domyślnymi.

### Tłumaczenia

Do `Languages` w katalogu języków można dodać obiekt z unikalnym `Code`,
`Name` i słownikiem `Texts`. Zachowaj parametry `{0}`, `{1}` itd.
Restart wystarcza; przebudowa nie jest potrzebna. Brakujące klucze
korzystają z wbudowanego angielskiego. Brak/uszkodzenie katalogu powoduje
ostrzeżenie i wbudowane tłumaczenia, bez nadpisania pliku.
Zachowaj własną kopię tłumaczeń przed aktualizacją publikacji.

<a id="12-mechanizm-integracji-i-trwalosc-zmian"></a>
## 12. Mechanizm integracji i trwałość zmian

Przy aktywnym module natywnym launcher:

1. Sprawdza pełny hash i blokuje plik źródłowy przed modyfikacją.
2. Tworzy własny proces gry w stanie wstrzymanym.
3. Weryfikuje oryginalne instrukcje w pamięci.
4. Instaluje potrzebne tabele/payloady x86 i skoki, weryfikuje zapis,
   ustawia ochronę pamięci i odświeża cache instrukcji.
5. Wznawia proces dopiero po powodzeniu wszystkich instalacji.

Błąd instalacji kończy nowy proces, nie kontynuuje z częściowym patchem.
Blokada między launcherami i kontrola procesów o tej samej nazwie chronią
przed drugim startem. Zewnętrzne loadery nie są obsługiwanym zamiennikiem
bezpośredniego EXE.

| Rodzaj zmiany | Czy pozostaje po zamknięciu gry? |
|---|---|
| Hooki obrazu, reguł, PA, starzenia i paneli | Nie, istnieją w pamięci procesu. |
| Ustawienia launchera | Tak, po zapisie konfiguracji. |
| Zainstalowane XML i kopie skórek | Tak, to pliki użytkownika. |
| Uzyskane PA, efekty rozwoju/starzenia, reputacje lig | Mogą pozostać przez zwykły zapis kariery FM08. |
| Profile i dzienniki lig | Tak, w katalogu aplikacji. |
| Dziennik PA | Nie, pozostaje tylko w sesji launchera. |

Zamknięcie launchera nie zamyka gry i nie usuwa już zainstalowanych hooków.
Wyjątek funkcjonalny: writer reputacji zostaje rozbrojony, a odbiór
wszystkich logów ustaje. Restart gry bez modułu nie cofa zmian już
utrwalonych w save — do porównania potrzebna jest wcześniejsza kopia.

<a id="13-rozwiazywanie-problemow"></a>
## 13. Rozwiązywanie problemów

| Objaw | Zalecane działanie |
|---|---|
| Program wymaga .NET | Zainstaluj .NET 8 Desktop Runtime x64, nie tylko podstawowy runtime. |
| Nieobsługiwany plik gry | Sprawdź bezpośredni EXE i SHA256; nie omijaj kontroli wersji. |
| Gra jest już uruchomiona | Zamknij ją samodzielnie przed nowym startem lub instalacją skórek. |
| Nieprawidłowa konfiguracja | Zabezpiecz plik, popraw błąd i użyj Wczytaj w trybie zaawansowanym. |
| Zapisana rozdzielczość jest niedostępna | Wykryj ekran i wybierz tryb dostępny na aktualnym monitorze. |
| Brak kolumn lub `----` | Sprawdź moduł, instalację XML, rejestr kolumn, aktywny klub i przeładuj skórkę. |
| Zmęczenie jest liczbą zamiast opisu | Zmień widok i wróć do Edycja; sprawdź odświeżenie listy. |
| Instalator nie widzi Steklo | Wskaż poprawny `skins` z rozpoznanym Black lub Left Black. |
| PA nie rośnie | Sprawdź kwalifikację CA/PA i nową aktualizację tygodniową; brak sukcesu jest prawidłowym wynikiem losowania. |
| Nie widać logów lub Zapisz/Wczytaj | Włącz tryb zaawansowany. |
| Profil oczekuje na zapis/wybór | Wykonaj wymagany udany zapis lub wskaż właściwy profil; nie twórz nowej bazy co sezon. |
| Reputacja nie zmienia się | Sprawdź profil, datę, dwuletni harmonogram, status i otwarty launcher; obserwator sam niczego nie zapisuje. |
| Ochrona systemu blokuje aplikację | Sprawdź konkretny komunikat i pochodzenie pliku. Launcher nie obchodzi ochrony ani nie wyłącza antywirusa. |

Przy zgłaszaniu błędu podaj wersję/paczkę launchera, SHA256 EXE gry,
Windows/runtime, aktywne moduły, kroki odtworzenia oraz komunikat.
Przetestuj problem na kopii kariery. Przed udostępnianiem logów usuń
prywatne ścieżki i dane, których nie chcesz publikować. Nie publikuj
plików gry ani całych zapisów bez sprawdzenia praw do ich udostępnienia.

<a id="14-budowanie-testowanie-i-publikacja"></a>
## 14. Budowanie, testowanie i publikacja

Polecenia PowerShell uruchamiane z głównego katalogu projektu:

```powershell
dotnet build .\src\FmLauncher\FmLauncher.csproj -c Release
dotnet run --project .\tests\FmLauncher.Tests\FmLauncher.Tests.csproj -c Release
dotnet publish .\src\FmLauncher\FmLauncher.csproj -c Release -r win-x64 --self-contained false -o .\publish
```

Publikacja nie zawiera runtime ani plików gry. `publish` jest osobnym
katalogiem roboczym: nie publikuj bezpośrednio na używany folder aplikacji,
aby nie nadpisać konfiguracji, profili i dzienników użytkownika.

Przy aktualizacji wymieniaj pliki programu, zachowując dane użytkownika,
w szczególności `FmLauncher.config.json`, `profils`, starsze profile,
raporty i dzienniki. Przed wymianą zamknij launcher i zrób kopię.
Nowy launcher nie aktualizuje hooków w już działającej grze.

### Testy skupione

Poniższe opcje należą do **programu testowego**, nie interfejsu CLI
publicznego launchera. Podaj własną lokalną ścieżkę gry.

```powershell
$game = 'C:\Games\FM08\fm.exe'
$tests = '.\tests\FmLauncher.Tests\FmLauncher.Tests.csproj'
dotnet run --project $tests -c Release -- --ui-layout 'C:\Temp\FmLauncherUi'
dotnet run --project $tests -c Release -- --rule-scope $game
dotnet run --project $tests -c Release -- --pa-analysis $game
dotnet run --project $tests -c Release -- --pa-native
dotnet run --project $tests -c Release -- --league-reputation
dotnet run --project $tests -c Release -- --league-diagnostics $game
dotnet run --project $tests -c Release -- --modern-rules $game
dotnet run --project $tests -c Release -- --panels $game
dotnet run --project $tests -c Release -- --game $game
dotnet run --project $tests -c Release -- --display-game $game Window
dotnet run --project $tests -c Release -- --display-game $game Borderless
```

- `--pa-analysis` jest statyczny; `--pa-native` wykonuje izolowany payload x86.
- `--game` obejmuje m.in. instalację w zatrzymanym FM08 bez wczytania kariery.
- Testy paneli/diagnostyki/modernizacji mogą uruchamiać własne procesy
  natywne i sprawdzać kod x86; nie zastępują normalnej symulacji kariery.
- Testy obrazu uruchamiają grę do menu i kończą własny proces.
  Pełny ekran może zmienić tryb pulpitu; nie traktuj go jako testu bez wpływu
  na pulpit.
- Odczyt istniejącej kariery: `--league-live <PID> <folder-raportow>`.
  Wymaga ręcznie wczytanej, zgodnej kariery; nie przewija czasu.

Przed wydaniem potrzebne są również próby w kopii kariery: rzeczywisty
mecz z limitami i bez nich, rozwój PA oraz zapis/odczyt, starzenie,
przejścia przez daty reputacji, ponowne wczytywanie i odmienne skórki/DPI.
Wyniki fixture nie są deklaracją stabilności wszystkich kombinacji.

### Zawartość przyszłego repozytorium

Dokumentacja używa linków względnych i nie wymaga GitHub Pages.
Źródła i testy można publikować wraz z tymi czterema dokumentami.
Przed pierwszym publicznym udostępnieniem trzeba ustalić licencję kodu
i prawa do dołączanych zasobów. Ten dokument nie nadaje licencji.

Nie dodawaj do repozytorium EXE/data gry, zapisów kariery, własnych profili,
prywatnych logów, zrzutów awarii ani zasobów osób trzecich bez uprawnienia.
Paczki binarne launchera można przygotować jako osobne załączniki wydania.
Dokumentacja nie tworzy repozytorium ani wydania automatycznie.

<a id="15-mapa-kodu"></a>
## 15. Mapa kodu

| Obszar | Źródła |
|---|---|
| Interfejs i motywy | [MainForm.cs](src/FmLauncher/MainForm.cs), [LauncherControls.cs](src/FmLauncher/LauncherControls.cs), [LauncherTheme.cs](src/FmLauncher/LauncherTheme.cs) |
| Konfiguracja i języki | [Configuration.cs](src/FmLauncher/Configuration.cs), [Localization.cs](src/FmLauncher/Localization.cs), [katalog języków](src/FmLauncher/FmLauncher.languages.json) |
| Start i zapis w pamięci | [GameLauncher.cs](src/FmLauncher/GameLauncher.cs), [SuspendedGameProcess.cs](src/FmLauncher/SuspendedGameProcess.cs), [NativeCode.cs](src/FmLauncher/NativeCode.cs) |
| Reguły | [MatchRulePatch.cs](src/FmLauncher/MatchRulePatch.cs), [MatchRuleScope.cs](src/FmLauncher/MatchRuleScope.cs) |
| Obraz | [DisplayService.cs](src/FmLauncher/DisplayService.cs), [GameDisplayPatch.cs](src/FmLauncher/GameDisplayPatch.cs), [GameDisplayController.cs](src/FmLauncher/GameDisplayController.cs) |
| PA i starzenie | [PaGrowthPolicy.cs](src/FmLauncher/PaGrowthPolicy.cs), [GamePaPatch.cs](src/FmLauncher/GamePaPatch.cs), [GamePaJournal.cs](src/FmLauncher/GamePaJournal.cs), [GameAgingPatch.cs](src/FmLauncher/GameAgingPatch.cs) |
| Panele/skórki | [GamePanelPatch.cs](src/FmLauncher/GamePanelPatch.cs), [SkinPanelInstaller.cs](src/FmLauncher/SkinPanelInstaller.cs), [SkinGuidePage.cs](src/FmLauncher/SkinGuidePage.cs) |
| Ligi i profile | [LeagueReputation.cs](src/FmLauncher/LeagueReputation.cs), [CareerIdentity.cs](src/FmLauncher/CareerIdentity.cs), [LeagueProfileAutomation.cs](src/FmLauncher/LeagueProfileAutomation.cs), [LeagueChanges.cs](src/FmLauncher/LeagueChanges.cs), [GameLeagueChangesPatch.cs](src/FmLauncher/GameLeagueChangesPatch.cs) |
| Diagnostyka lig | [LeagueDiagnostics.cs](src/FmLauncher/LeagueDiagnostics.cs), [GameLeagueDiagnosticsPatch.cs](src/FmLauncher/GameLeagueDiagnosticsPatch.cs) |
| Testy i selektory | [Program.cs](tests/FmLauncher.Tests/Program.cs), [LauncherUiTests.cs](tests/FmLauncher.Tests/LauncherUiTests.cs) |

Adresy natywne są zależne od rozpoznanej wersji, nie stanowią publicznego
API. Główne punkty dotychczasowej integracji to gettery reguł
`0x00AFE0D0` / `0x00AFE150`, tygodniowe PA `0x008D3F33`,
procedura starzenia `0x00A34E00`, zdarzenie roczne `0x00E26113`,
loader `0x00465210` / `0x00466978` i sukces zapisu `0x00467F23`.
Wiążący kontrakt bajtów i powroty znajdują się w kodzie oraz testach.

<a id="16-zakres-poza-aktualnym-wydaniem"></a>
## 16. Zakres poza aktualnym wydaniem

Poniższe prace nie są gotowymi funkcjami launchera:

- Pobieranie i instalowanie paczek baz danych z GitHub Releases lub
  innego serwisu; automatyczny updater launchera.
- Uniwersalne wstrzykiwanie paneli do dowolnej skórki.
- Wyróżnianie atrybutów zależnie od pozycji i nowy panel ukrytych
  atrybutów w profilu zawodnika.
- Ocena pozycji według analizowanego modelu Genie Scout.
- Modyfikowanie nagród pieniężnych i wartości sponsoringu.
- Gwarantowana obsługa innych EXE, wszystkich skórek, ekranów i trybu
  wieloosobowego.

Istniejący [plan paneli zawodnika](PLAN_PANELI_ZAWODNIKA.md) opisuje przyszłe
prace, nie listę zainstalowanych funkcji. Analizy importu baz i finansów
nie oznaczają ich wdrożenia w launcherze.
