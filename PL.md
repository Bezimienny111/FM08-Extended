# FM08 Extended — funkcje po polsku

[Projekt](README.md) · [Instalacja](INSTALLATION.md#polski) ·
[Pełna dokumentacja](DOCUMENTATION.md) · [English](EN.md)

FM08 Extended uruchamia Football Manager 2008 z wybranymi rozszerzeniami.
Nie zastępuje gry ani jej bazy danych. Integracje z silnikiem są
**eksperymentalne** — pierwsze próby wykonuj na kopii kariery.

## Spis funkcji

- [Uruchamianie i ustawienia](#uruchamianie)
- [Interfejs, język i motyw](#interfejs)
- [Tryb zaawansowany](#zaawansowane)
- [Obraz](#obraz)
- [Liczba zmian i rezerwowych](#reguly)
- [Dynamiczny potencjał zawodników](#pa)
- [Opóźnienie starzenia](#starzenie)
- [Dodatkowe dane zawodników](#panele)
- [Instalator skórek](#skorki)
- [Dynamiczna reputacja lig i profile](#reputacja)
- [Odczytowa obserwacja lig](#obserwacja)
- [Diagnostyka i dzienniki](#diagnostyka)
- [Społeczność i wsparcie](#spolecznosc)
- [Ograniczenia i planowane funkcje](#ograniczenia)

<a id="uruchamianie"></a>
## Uruchamianie i ustawienia

- Wybór pliku `fm.exe` i próba automatycznego odnalezienia go w katalogach
  nadrzędnych.
- Opcjonalny wybór folderu użytkownika FM08 ze skórkami, grafikami i save.
  Nie jest to folder instalacyjny `data`; wybór nie przenosi plików
  i nie zmienia miejsca zapisu kariery w grze.
- **GRAJ** sprawdza ustawienia, wyświetla potwierdzenie, zapisuje
  konfigurację i uruchamia grę. Nie trzeba wcześniej klikać Zapisz.
- Anulowanie potwierdzenia nie zapisuje zmian; błąd walidacji/zapisu
  blokuje uruchomienie.
- Ustawienia są odczytywane przy następnym starcie launchera.
  Ręczne **Zapisz / Wczytaj** są dostępne w trybie zaawansowanym
  i dotyczą ustawień launchera, nie zapisów kariery.
- Zmiana przełączników podczas gry nie zmienia jej aktywnej sesji.
  Nowe integracje wymagają ponownego uruchomienia gry przez launcher.

Wymagany jest Windows x64, .NET 8 Desktop Runtime x64 i zgodny FM08 8.0.2.
Integracje sprawdzają pełną sumę SHA256 oraz instrukcje gry.
Lista obsługiwanych plików: [zgodność](DOCUMENTATION.md#1-wymagania-i-zgodnosc).

<a id="interfejs"></a>
## Interfejs, język i motyw

- Dwie zakładki: **Główna** oraz **Skórki**.
- Karty funkcji mają osobne przełączniki ON/OFF.
- **Szczegóły** pokazują opis i kontrolki, ale nie włączają funkcji.
- Języki polski i angielski można przełączać bez restartu i utraty
  edytowanych ustawień. Język launchera nie zmienia języka samego FM08.
- Jasny i ciemny motyw obejmują główny interfejs i okna raportów.
  Systemowe dialogi pozostają pod kontrolą Windows.
- Pola trybu obrazu i rozdzielczości są zawsze widoczne.
- Przycisk GRAJ pozostaje w dolnej części okna; status profilu pojawia się
  przy włączonych rzeczywistych zmianach reputacji.

Teksty nowych paneli w grze przyjmują język wybrany przy jej starcie.
Zmiana tych tekstów w działającej sesji wymaga restartu gry.

<a id="zaawansowane"></a>
## Tryb zaawansowany

Domyślny tryb gracza ukrywa techniczne narzędzia: obserwację i diagnostykę
lig, liczniki/logi PA, dziennik reputacji oraz ręczne Zapisz/Wczytaj.
Tryb zaawansowany je udostępnia.

**Ukrycie nie wyłącza funkcji.** Jeżeli obserwacja lub diagnostyka nadal
jest włączona, launcher pokazuje ostrzeżenie. Instrukcje skórek, XML,
ustawienia meczowe i profil kariery pozostają dostępne również bez
trybu zaawansowanego.

<a id="obraz"></a>
## Obraz

- **Okno:** stała rozdzielczość, ramka, pasek tytułu i minimalizacja.
- **Okno bez ramki:** wybrany rozmiar wyśrodkowany na głównym ekranie,
  bez rozciągania i zmiany rozdzielczości pulpitu.
- **Pełny ekran:** natywny tryb FM08; wymaga dalszego ręcznego potwierdzenia.
- Wykrywanie dostępnych rozdzielczości głównego monitora w zakresie
  **640 × 480–1920 × 1080**, z uwzględnieniem pulpitu, ramki i DPI.
- Kontrola rzeczywistego rozmiaru okna i bufora renderowania przy starcie.
- OFF pozostawia oryginalne zachowanie gry.

Nie ma gwarancji zgodności każdej skórki i każdego układu monitorów.

<a id="reguly"></a>
## Liczba zmian i rezerwowych

- Niezależne ustawienie liczby zmian oraz miejsc na ławce.
- Osobne nadpisania dla **29 kodów reguł, 0–28**.
- Aktywny zakres **0–12**; edycja tabelą lub strzałkami pod nią.
- Sortowanie kolumn rosnąco/malejąco, z liczbowym sortowaniem wartości.
- Nadrzędne OFF pomija nadpisania, ale zachowuje ustawienia.
- Wyłączony limit zachowuje oryginalne zasady, w tym warunkowe wyjątki.
- Przykłady rozgrywek pomagają rozpoznać kod, ale nie są pełną mapą ligi.

Kod reguły **nie jest wyborem jednej ligi**. Ta sama reguła może obsługiwać
wiele rozgrywek i etapów. Aktualna mapa ma 45 przypisań do 15 kodów;
pozostałe mają nierozpoznany zakres. Zmiana dotyczy także niewymienionych
meczów korzystających z kodu.

Zakres 0–12 nie gwarantuje bezpieczeństwa każdej kombinacji; potrzebne są
próby rzeczywistego meczu. Dostępni rezerwowi ograniczają możliwe zmiany.
Dogrywka, sparingi i zespoły młodzieżowe wymagają osobnej weryfikacji.

<a id="pa"></a>
## Dynamiczny potencjał zawodników

Opcjonalny wzrost **PA**, niezależny od wyświetlania danych w panelach.
Obejmuje wszystkich kwalifikujących się zawodników, nie tylko własny klub.

- Warunek: CA/PA 1–200, PA < 200 oraz różnica PA−CA od 0 do 4.
- Najwyżej jedno losowanie przy nowej tygodniowej aktualizacji treningu.
- Sukces: **+1 PA**, bez bezpośredniego zwiększenia CA.
- Baza szansy: **8%**, modyfikowana wiekiem i mentalnością.
- Wagi mentalności: profesjonalizm 60%, ambicja 25%, determinacja 15%.
- Mnożniki wieku: do 18 lat 1.25; 19–21: 1.10; 22–24: 1.00;
  25–27: 0.70; 28–30: 0.40; 31–33: 0.15; 34+: 0.05.
- Maksimum PA: 200. Nie ma sezonowej puli ani limitu +5.
- Odświeżanie paneli nie daje dodatkowych losowań.
- Brak wzrostu w danym tygodniu jest prawidłowym wynikiem losowania.

Przykład: 18-latek z profesjonalizmem, ambicją i determinacją po 20
ma 15% szansy w kwalifikującym się tygodniu.
Pełny wzór: [model PA](DOCUMENTATION.md#6-dynamiczne-pa).

Tryb zaawansowany pokazuje liczniki i dziennik z zawodnikiem, CA,
PA przed/po i numerem aktualizacji. Dziennik jest sesyjny, nie na dysku;
może zgłaszać utracone wpisy. Sam wzrost działa po zamknięciu launchera.
Zapis kariery utrwala uzyskane PA; wyłączenie nie cofa wcześniejszych zmian.

<a id="starzenie"></a>
## Opóźnienie starzenia

Niezależny, domyślnie wyłączony moduł przesuwa o **3 lata** efektywne
progi utraty fizyczności i kary CA związanej z wiekiem.
Zachowuje wpływ indywidualnych cech zawodnika.

Nie zmienia daty urodzenia, widocznego wieku, rozwoju młodych ani
decyzji emerytalnych. Nie gwarantuje dłuższej kariery konkretnego gracza.
Efekty rozwoju mogą zostać utrwalone przez zapis kariery.

<a id="panele"></a>
## Dodatkowe dane zawodników

- **Trening:** zmęczenie sezonowe i objaśniający tooltip.
- **Skład / Selection:** zmęczenie, liczbowe CA i PA.
- **Taktyka / Pozycja:** zmęczenie obok kondycji.
- Dodatkowy, uproszczony widok **Edycja**, bez usuwania starych widoków.

Dane dotyczą klubu aktywnego ludzkiego menedżera, jego rzeczywistych
rezerw/U23 i graczy wypożyczonych do klubu. Nie obejmują osobnych afiliantów,
reprezentacji, obcych graczy i wypożyczonych z klubu. Brak dostępu daje `----`.

Zmęczenie sezonowe to nie kondycja. Kategorie: wypoczęty (J ≤ 0),
normalne (1–250), narastające (251–374), wysokie (375–499),
bardzo wysokie (≥ 500). Tooltip opisuje wpływ na jeden mnożnik treningu,
nie całkowitą efektywność ani ryzyko kontuzji.

Funkcja wymaga aktywnego modułu oraz poprawnych XML skórki.
Czasem trzeba przełączyć widok, aby odświeżyć opis zmęczenia.
Panele nie zmieniają CA, PA ani wartości zmęczenia.

<a id="skorki"></a>
## Instalator skórek

- Obsługa Steklo Black i Steklo Black (Left).
- Tworzenie luźnego nadpisania domyślnej skórki `fm2008`.
- Zachowanie dziedziczenia i istniejących kolumn.
- Kopie zmienianych plików z końcówką `.before-fmext-panels`.
- Brak zmian w archiwach FMF.
- Cztery fragmenty XML do ręcznej integracji z własną skórką.

**Aktualny instalator wymaga obecności co najmniej jednego rozpoznanego
wariantu Steklo w wybranym `skins`.** Nie instaluje dodatków automatycznie
do dowolnej skórki.

Instaluj przy zamkniętej grze. Następnie wyłącz cache skórek w FM08,
przeładuj skórkę i wybierz dodany widok. Przed instalacją wykonaj własną
kopię skórki; nie ma automatycznego przycisku odinstalowania.
Szczegóły: [panele i instalacja](DOCUMENTATION.md#8-panele-zawodnikow-i-skorki).

<a id="reputacja"></a>
## Dynamiczna reputacja lig i profile

Opcjonalne **rzeczywiste zmiany reputacji 42 najwyższych lig europejskich**
w oparciu o zmianę pięcioletniego współczynnika kraju.

- Profil bazowy jest przypisywany do kariery, nie nazwy pliku save.
- Nowa kariera: automat tworzy profil po udanym zapisie, gdy ma bazę.
- Wczytana kariera: automatyczne dopasowanie zgodnego profilu; przy braku
  profilu możliwe utworzenie bazy z aktualnego stanu.
- Ręczny import/wybór profilu i ponowne wykrywanie w razie problemu.
- Profile trafiają do `profils` obok programu. Zachowuj je razem z karierą.
- Zmiany przypadają 15 czerwca co dwa lata od sezonu bazowego.
- Jedna liga zmienia reputację najwyżej o **±1 punkt** na takie zdarzenie.
- Zwykły zapis FM08 utrwala zmiany.
- Status profilu jest widoczny nad GRAJ, a dziennik zmian w trybie
  zaawansowanym.

**Pozostaw launcher otwarty.** Zamknięcie rozbraja writer. Nie twórz profilu
ponownie co sezon. Kilka zgodnych profili wymaga wyboru; aktywacja 15 czerwca
i cofnięcie przed bazę są blokowane.

Moduł nie zmienia współczynników UEFA, liczby miejsc pucharowych ani
niższych lig. Nie nadrabia pominiętych zdarzeń.
Pełny model i zasady profilu:
[reputacja lig](DOCUMENTATION.md#9-rzeczywista-reputacja-lig).

<a id="obserwacja"></a>
## Odczytowa obserwacja lig

Osobne narzędzie zaawansowane: odczyt reputacji i współczynników,
porównanie z bazą oraz **symulacja**, bez zmiany gry.
Może działać z już uruchomionym, zgodnym FM08.

Pokazuje faktyczne i bazowe reputacje, współczynniki, cel modelu,
symulację i potwierdzenia roczne. Starsza symulacja wymaga dwóch zgodnych
ocen rocznych do kroku ±1 — nie jest to reguła rzeczywistego writera.
Raporty JSON pozostają w `league-observations`. Po wczytaniu save lub
zmianie procesu trzeba utworzyć nową, potwierdzoną bazę.

<a id="diagnostyka"></a>
## Diagnostyka i dzienniki

Tryb zaawansowany udostępnia:

- sesyjny dziennik wzrostów PA;
- trwały dziennik wykonanych zmian reputacji (`league-changes`);
- raporty odczytowej obserwacji (`league-observations`);
- diagnostykę rocznej historii UEFA i loadera (`league-diagnostics`).

Osobna diagnostyka wymaga startu gry przez launcher i sama nie zmienia
reputacji. Moduł rzeczywistych zmian instaluje ją także na własne potrzeby.
Błędy i utrata wpisów są zgłaszane. Log nie zastępuje zapisu kariery,
a brak wpisu nie dowodzi, że zdarzenie nie wystąpiło.

<a id="spolecznosc"></a>
## Społeczność i wsparcie

- [YouTube](https://www.youtube.com/@Bezimienny111)
- [Discord](https://discord.gg/hP2g4MQS5T)
- [Ko-fi — wsparcie projektu](https://ko-fi.com/ericaaurora)

Przy wsparciu wpisz w treści **FM08Extended**.
Ikona Git w aplikacji pozostaje nieaktywna do ustawienia adresu repozytorium.

<a id="ograniczenia"></a>
## Ograniczenia i planowane funkcje

Launcher nie zmienia EXE gry na dysku. Instaluje hooki w pamięci nowego
procesu; skutki rozgrywki mogą jednak pozostać w zapisanej karierze.
Nie gwarantuje zgodności innych EXE, każdej skórki, wszystkich kombinacji
reguł ani trybu wieloosobowego. Długie testy kariery nadal są potrzebne.

**Nie są jeszcze wdrożone:** pobieranie baz i automatyczny updater,
uniwersalny instalator skórek, wyróżnianie atrybutów według pozycji,
nowy panel ukrytych atrybutów, oceny pozycji Genie Scout oraz modyfikatory
nagród pieniężnych i sponsoringu.

Pełne wymagania, konfiguracja, testy i rozwiązywanie problemów:
[DOCUMENTATION.md](DOCUMENTATION.md).
