# FM08dev: aktualizacja baz

## Start bez rutynowego podsumowania - 2026-11-16

GRAJ uruchamia gre bez modalnego potwierdzenia/podsumowania wlaczonych funkcji.
Okna ostrzezen/bledow tylko przy rzeczywistych problemach. Zachowac walidacje,
zapis ustawien, guardy paneli i obsluge bledow; nie mylic braku podsumowania
z pomijaniem sprawdzen. Informacje o poprawnym uruchomieniu pozostaja w logach.

## Instalacja skorek tylko z zakladki Skins - 2026-11-16

Jedyna akcja instalacji/aktualizacji paneli: Skins > Basic > Create/update Ext skins.
Przyciski w szczegolach funkcji jedynie otwieraja Skins > Basic, bez zapisu skorek.
GRAJ wykonuje tylko odczyt gotowosci/hashow/jezyka paneli; nie instaluje ani nie
aktualizuje XML. Brak lub niezgodnosc paneli blokuje uruchomienie z instrukcja.
Zmiana jezyka FM wymaga aktualizacji z Basic przy zamknietej grze. Nie przywracac
automatycznej instalacji przy GRAJ ani bocznych przyciskow instalacyjnych/CLI.

## Szybkie skrypty gotowe natywnie - 2026-11-15

Rutynowe7operacji na istniejacych osobach/klubach wykonywac przez
FM08-Database-Tools/operations/quick/01_emerytura.py ..07_klub_menedzera.py
(wspolne quick_db.py/QuickNative.cs), zamiast budowac oddzielne adaptery.
CSV oraz wieleUIDobslugiwane; --source/--outputopcjonalne(domyslnie najwyzsza
publicznaTEST_X i nastepnaTEST_X). Przy znanej zaakceptowanej podstawie
podawac --source jawnie. Zawsze nowakopia; hashe zrodla, readback, raport
i XML; przerwanie paczki przy zlymUID przed utworzeniem wynikowej bazy.
7operacji po2rekordy NativePASS;8testowCSV;inverseCA/chainingloan/
rejectUIDPASS wVALIDATION.json. SI/nowakariera/sezon technicznych probek
sa osobnymiPENDING. Runtimecachepo hashach kodu; niebuildowac dla CSV.
Nie tworzaPERSON; imiona moga dodac wspoldzielone rekordyNAME(bez dubli osob).
Known guards: menago wspieranytype1, nie konwertowacplayerstaff/nie
tworzyc kopii; niejednoznaczneTEAM/FAMILY i wielokrotneumowywypozyczen
wymagaja decyzji; nie omijacwarunkow. Przy emeryturze kontrakt/kadra/loan/
future zwalniane; loan zachowuje wlasciciela i termy;CA/PA nie zmienia pensji.
540wczesniejszychwyjatkowplacowych pozostawicBEZZMIAN - najnowsza decyzja
uzytkownika; nie wznawiac ich poprawki bez nowegozlecenia.

## Dodatkowe skalowanie pensji wedlug CA - najnowsza decyzja 2026-11-15

Uzytkownik zlecil mnozenie KONCOWEJ aktualnej pensji: CA>190 x1;
CA180..190 x0.8; CA160..179 x0.6; CA140..159 x0.4; CA<140 x0.3.
Przy nakladajacych sie granicach180i160 przyjmujemy wyzszy przedzial,
co przekazano uzytkownikowi przed migracja. GBP/tydzien, zaokraglenie do
pelnego funta(polowki w gore). Migracja na X36 zachowuje130zatwierdzonych
emerytur, nie przywraca kontraktow. Mnoznik stosowac RAZ do koncowej
stawki bazowej; nie nakladac ponownie na juz przeskalowana pensje.
Limity225000dlaCA>190 i125000dlareszty oraz nizsze krajowe nadalobowiazuja.
Nie przywracac starych CA-only stawek(CA-30)*350/150 ani limitu300000.

## Szybkie operacje zbiorcze - zlecenie 2026-11-15

Zapewnic7polecen: emerytura UID(data2007-01-01), transfer gracza UID+klubUID,
wypozyczenie UID+klubdocelowyUID+koniec, nazwa klubu UID+nazwa, imiona gracza
UID+FirstName/LastName/CommonName, CA/PA UID+CA+PA, menedzer UID+klubUID.
Kazde obsluguje wiele wierszy CSV i samodzielnie wyznacza indeksy/relacje,
przygotowuje nowa kopie bazy i niezalezny odczyt. Bez tworzenia osob,
kasowania plikow i recznego ustawiania adapterow/indeksow. Zachowac istniejace
klauzule, pensje, oceny i inne pola nieobjete operacja. Jawne jednostki dat
(kalendarz FM08,bez automatycznego podwojnego przesuwania19lat). Nie uznawac
komendy za gotowa bez rzeczywistego zapisu i sprawdzenia na nowej probce.

## Sporne zmiany i duble - najnowsza decyzja 2026-11-15

W przyszlych zmianach kazdy przypadek watpliwy (tozsamosc, duplikat lub
inna niejednoznaczna zmiana) przedstawic uzytkownikowi OSOBNO, kolejno,
z proponowana decyzja i powodem. Nie rozstrzygac ich samodzielnie ani
domyslnie tworzyc nowej osoby. Rutynowe jednoznaczne zmiany kontynuowac.
Ta pozniejsza decyzja ma pierwszenstwo nad starszymi zasadami automatycznego
rozstrzygania konfliktow. Aktualna kontrola dubli poprzedza korekte plac.
Nie scalac automatycznie kandydatow po nazwisku, +/-1 dniu DOB ani roznicy
19 lat. Wymagac kontroli kolizji przed CREATE i wewnatrz jednej paczki.
PlayerCreationGuard wdrozony w scratch/prepare_missing_squads.py; inne
adaptery NIE sa przez to automatycznie objete - przed ich uzyciem dolaczyc
te sama bramke do planowanych CREATE na aktualnym globalnym eksporcie.
Korekta samych plac nie tworzy PERSON/kontraktow i zachowuje UID/liczebnosci.

## Nowe limity pensji - pozniejsza decyzja 2026-11-15

GBP/tydzien: CA SCIŚLE >190 moze miec maksymalnie225000. Dla pozostalych
gorny limit100000..125000; obecna korekta przyjmuje125000 jako maksimum,
zachowujac nizsze limity kraju/ligi. Nie przywracac starego limitu300000.
Do100000 bez zmian; gorna czesc skali kompresowana proporcjonalnie
w obrebie aktualnego kontraktowego poziomu rozgrywek, bez zmiany CA/PA.

## Launcher INI - zgodnosc konfiguracji, decyzja 2026-11-15

Od R14 ustawienia maja plik FmLauncher.ini obok EXE. WYMAGANA trwała
kompatybilnosc kolejnych wersji: odczyt starszych ustawien, jawny numer
schematu, domyslne wartosci nowych opcjonalnych kluczy, zachowanie nieznanych
sekcji/kluczy i komentarzy przy zapisie. Nie zmieniac znaczenia kluczy ani
numerow29regul w istniejacym schemacie. Nie obcinac ani nie nadpisywac
nowszego nieobslugiwanego schematu. Przy brakuINI odczytywac staryJSON.
JSONschema1 pozostaje zgodna kopia dla wczesniejszych wersji. INI ma
pierwszenstwo, gdy oba pliki istnieja. Zapisz/GRAJ zapisuje oba formaty,
z unikalnymi backupami i bez kasowania plikow; testowac roundtrip,
migracje, brak nowych kluczy, zachowanie nieznanych oraz blad zapisu.
Kontrakt konfiguracji ma byc uwzgledniany we wszystkich przyszlych pracach.
Grafika ma osobna zakladke po lewej; funkcje dwa niezalezne obszary
przelacznikow/szczegolow, zaznaczona karta ma odmienna cala powierzchnie.

R17: reczne Save/Reload usuniete ze stopki. Zapis przez GRAJ i przy zamknieciu
launchera; zamkniecie bez zmian nie przepisuje konfiguracji. Zly/nowszy plik
po nieudanym odczycie nie moze zostac zastapiony domyslnymi ustawieniami.
Ponowienie odczytu w Ustawieniach widoczne tylko przy bledzie konfiguracji.
Detekcja zmian musi obejmowac opcje tylko INI (np. TeamTalkReactionsEnabled),
mimo JsonIgnore w zgodnej kopii JSON. Schemat/29regul pozostaja bez zmian.

R18 UI wedlug korekty uzytkownika: neutralny lewy panel zgodny z motywem,
podwojna ramka zamiast granatowego wypelnienia. Kolejnosc: Ustawienia ze
sciezkami/trybem zaawansowanym (otwarte przy starcie), Grafika, Skorki,
Funkcje, Spolecznosc/linki. GRAJ po lewej pod nawigacja; mniejsza stopka
zachowuje stale zwijane logi i wsparcie. Szczegoly musza przeliczac szerokosc
opisow przy zmianie funkcji i rozmiaru okna, bez waskiej kolumny160px.

R20 Skins: Basic wykrywa oryginalne FM08/Steklo/Steklo Black i tworzy
warianty Ext Left/Right; katalog rozszerzony z4do6 o steklo_ext_left/right.
Noche/NocheExt nadal poza wsparciem. Advanced sluzy recznej integracji innych
ukladow, z mapa plikow/ID i7przykladami XML. Kanoniczny katalog ExtSkinCatalog
steruje tworzeniem i kontrola gotowosci; tworzyc dzieci oryginalnych rodzicow,
zachowac ich ustawienia fontow i autorstwo, nie kopiowac calej grafiki.
SkinPanelInstaller R20 obejmuje tez Frtt i nowy domyslny lewy/prawy uklad.
Instalacja tylko przy zamknietym FM, backup/readback/ochrona recznych edycji.
Skin installer/rollback nie kasuja plikow: nowe override przy rollbacku
otrzymuja odziedziczony bazowy XML; katalogi i pending zostaja zachowane.
Uninstall zablokowany. Nie uruchamiac starych instalatorow zawierajacych Delete.

## Korekta wynagrodzen importowanych graczy - decyzje 2026-11-15

Po potwierdzeniu wadliwego kraju-niezaleznego modelu(CA-30)*350/150
uzytkownik zlecil szeroki audyt, nastepnie JAWNIE go uproscil: zebrac
wszystkie IMPORTOWANE UID(nowi i reuse) i opracowac szybki wzor ligowy,
zmieniajac tylko pensje. Nie kontynuowac kosztownego audytu calego swiata,
staff/residualplayer ani pobierania rzeczywistych pensji kazdejosoby.
Kraje/poziomy musza miec jawne stawki i jednostki; przedimportem pokazac
efekt old->new i sumy plac. Czytac prawdziwy kontrakt poUID i sprawdzic
expectedoldwage/owner; nie uzywac slabych ownerfallbackow do zapisu.
Wypozyczenia zachowuja udzialy wplacach; brak kontraktu nie oznacza
zlecenia utworzeniaumowy. Korygowac nowakopie, zachowac SI/zrodla.
GBPtygodniowo - podane przez uzytkownika przyklady widelek najwyzszejligi:
Polska dobrzy1000-3000/gwiazdy3000-5000; Top5ENG/ITA/ESP/GER/FRA
dobrzy50000-100000/gwiazdy>100000; Argentyna dobrzy2000-7000/
gwiazdy8000-12000; Brazylia dobrzy5000-10000/gwiazdy>10000;
Holandia dobrzy10000-20000/gwiazdy20000-30000+. Pozostale kraje,
szczeble i gorne limity otwartych przedzialow musza byc jawnie oznaczone
jako propozycjeprojektowe, nie fakty zrodlowe ani zaakceptowane decyzje.

Pozniejsza decyzja tego dnia: uzytkownik po przegladzie widelek Serbia,
Singapur,MLS,Chorwacja,Czechy polecil "dobrze wdrazaj to do bazy".
Zaakceptowano wdrozenie przygotowanegomodelur2 jako szacunkuprojektowego,
co nie czyni stawek rzeczywistymi udokumentowanymi kontraktami.
WdrozonewX34:75629zmian,81juzzgodnych,540modelreviewbez zmian.
Nie powtarzac importu ani nie nadpisywac X34/SI. Nastepne korekty pensji
reuse operations/apply_verified_wages.py + hash-bound typedledger;
sam CSVzgenericexportem niejestdowodembezpiecznychadresowzapisu.

## NocheExt - wstrzymanie i wycofanie wsparcia R13 (2026-11-15)

Najnowsza decyzja uzytkownika: po bledzie czcionki i czarnym ekranie NIE
prowadzic dalszych prac ani zmian w Noche/NocheExt. Wycofac wsparcie NocheExt
z launchera R13: katalogu, listy obslugiwanych skorek, instalacji/regeneracji
i kontroli gotowosci. Pozostaja cztery warianty bazowe Ext i Steklo Black Ext.
Nie usuwac, nie przenosic ani nie zmieniac istniejacych plikow skorek/cache
lub ustawien gry. R12 i oryginalna Noche pozostaja chronione.
Ta pozniejsza decyzja ma pierwszenstwo nad starsza regula NocheExt z 13 XI.


## Zakaz usuwania - decyzja uzytkownika 2026-11-15

Doprecyzowanie uzytkownika 2026-11-15: zakaz dotyczy kasowania PLIKOW
i FOLDEROW oraz skryptow/komend, ktore moga je kasowac, takze temp/cleanup.
Uzgodnione zmiany rekordow WEWNATRZ NOWEJ KOPII BAZY (np. zastapienie
starego kontraktu lub wylaczenie emerytury przyszlego menedzera) sa dozwolone.
Nie jest to zgoda na kasowanie plikow zrodlowych ani zaakceptowanych baz.

Nie kasowac zadnych plikow, katalogow ani innych zasobow plikowych.
Nie tworzyc, nie generowac ani nie uruchamiac skryptow lub komend, ktore
moga kasowac pliki lub foldery. Nie rozszerzac istniejacych skryptow o takie operacje.
Zakaz obejmuje rowniez pliki tymczasowe, katalogi robocze, backupy,
automatyczne sprzatanie oraz kasowanie po bledzie. Nie obchodzic zakazu
przez inna powloke, biblioteke, narzedzie ani proces potomny.
Etapy wymagajace usuwania pozostawic niewykonane i jawnie opisac.
Ta decyzja ma pierwszenstwo nad starszymi procedurami sprzatania/usuwania.

Przed praca sprawdz wznowienie.md i wskazany aktualny checkpoint.
Dla modernizacji baz stosuj [reguly decyzji](FM08-Database-Tools/docs/DATABASE_UPDATE_RULES.md)
oraz [procedure importu](FMExt/IMPORT_LIG_KROK_PO_KROKU.md).
Wczesniejsze konkretne decyzje uzytkownika maja pierwszenstwo nad domyslnymi.
Typowe konflikty i kaskady liczebnosci rozstrzygaj bez ponownego pytania;
slad decyzji i jawne luki zapisz w raporcie. Nie oslabiaj technicznych walidacji.
Nie nadpisuj zaakceptowanej bazy ani zapisu SI. Native/SI/nowa kariera/sezon
maja osobne statusy. Zmiana samych danych nie wymaga ponownego pelnego builda.
Polska:90minut ma pierwszenstwo nad API. Wspolny cache zachowuje surowe odpowiedzi.
Reguly i JSON polityki nie oznaczaja gotowego uniwersalnego importera.

Nowe kluby: Sugar Daddy zawsze OFF. Przy najbliższym imporcie wyłączyć odziedziczone flagi we wszystkich wcześniej dodanych klubach; jawny zapis i niezależny odczyt, bez zaufania do szablonu. Decyzja użytkownika2026-11-09.

Nazwy nowych baz testowych: TEST_X1, TEST_X2, TEST_X3, itd. Ten sam krotki identyfikator dla folderu, nazwy w SI/grze i pliku XML. Opis krajow i zmian tylko w raporcie/manifescie. Numeracja wspolna dla kolejnych paczek; nie nadpisywac istniejacych wersji. Decyzja uzytkownika 2026-11-09; od nastepnej bazy, obecna B1 zachowuje nazwe.

Kadry niepelne: Nie szukamy na sile brakujacych zawodnikow. Importujemy potwierdzone profile; jawne luki zostawiamy silnikowi do uzupelnienia generowanymi graczami. Niedobor osob lub GK sam nie blokuje importu. Nie tworzymy fikcyjnych profili ani dat i nie oslabiamy technicznych walidacji. Decyzja uzytkownika 2026-11-10.

Launcher i skórki dev: użytkownik2026-11-11 zlecił agentowi samodzielne aktualizowanie naszych wersji dev. Rutynową instalację/aktualizację czterech skórek Ext w Dane/skins wykonuje agent przez sprawdzony instalator z backupem/readback; nie przerzuca tego kroku na użytkownika. Dopuszczony bezpieczny restart wyłącznie naszego launchera dev (grzeczne zamknięcie/zapis ustawień, kopia config, ponowne otwarcie); nie zabijać ani samodzielnie zamykać gry FM. Oryginalne skórki, stabilny launcher i zaakceptowane bazy/SI pozostają chronione. Systemowe ograniczenia uprawnień nadal obowiązują.

Kolejność następnych paczek: przed masowym pobieraniem kadr ustalić pełną obsadę klasycznych lig, kaskady według końcowych tabel poprzedniego sezonu oraz tożsamości klubów i rodziców rezerw. Zamknąć jedną listę klubów, w tym kandydatów koniecznych do uzupełnienia miejsc, i dopiero dla niej zbierać zawodników. Późniejsze braki uzupełniać wyłącznie jako przyrostową listę konkretnych klubów, z użyciem cache; nie pobierać ponownie kraju ani całej paczki. Nieweryfikowalne dane osób pozostawić jako jawne luki dla silnika. Nie osłabiać walidacji technicznych. Decyzja użytkownika 2026-11-13.

NocheExt: decyzja użytkownika 2026-11-13. NocheExt jest wspieranym wariantem Ext dziedziczącym oryginalną Noche. Każda przyszła zmiana wspólnych paneli i katalogu instalatora ma obejmować także NocheExt, z tymi samymi opcjami i językiem gry (polski -> PL, pozostałe -> EN). Oryginalna Noche i jej zasoby są chronione; nie kopiować masowo grafiki do dziecka. Instalację wykonuje agent transakcyjnie z backupem/readback. Aktywna gra nadal blokuje instalację; nie obchodzić guardu ani nie zamykać FM.


Aktualizacje dla uzytkownika: podczas pracy informowac regularnie, przy dluzszych etapach mniej wiecej co minute, o konkretnej czynnosci, wyniku lub blokadzie. Decyzja uzytkownika 2026-11-15.


## Styl pracy i zglaszanie blokad - decyzja uzytkownika 2026-11-15

1. Blokade dostarczenia wyniku zglaszac natychmiast po wykryciu: co nie dziala,
   jaki etap zatrzymuje, czy zmieniono pliki/dane oraz proponowany nastepny krok.
   Nie czekac na pytanie uzytkownika i nie ukrywac blokady pod statusem "pracuje".
2. Samodzielnie wykonac krotka diagnoze oczywistych przyczyn. Jesli rozwiazanie
   wymaga nowego narzedzia, duzej analizy lub zmiany podejscia, najpierw pokazac
   wyniki i warianty uzytkownikowi, zanim rozszerzy sie zakres prac.
3. Jeden glowny cel: obecnie paczka sztabu. Zadania rownolegle maja zamkniety
   uzgodniony zakres; nie otwierac kolejnych analiz bez uzgodnienia.
4. Podczas aktywnej pracy aktualizacja mniej wiecej co minute: konkretny wynik,
   aktualna czynnosc i przeszkoda. Jesli nic nie dziala w tle, napisac to wprost.
5. Oddzielac statusy: dane zebrane -> import wykonany -> kontrola techniczna ->
   paczka do testu uzytkownika. SI, nowa kariera i sezon maja osobne wyniki.
   Gotowe narzedzie lub plan nie oznacza gotowej bazy.
6. Bez nieuzasadnionych terminow. Podawac pozostale kroki i niepewnosci.
   Nie obiecywac bliskiego konca przed usunieciem znanej blokady.


## Zakres aktualizacji sztabu - decyzja uzytkownika 2026-11-15

Aktualizujemy WYLACZNIE glownego menedzera / pierwszego trenera pierwszego
zespolu seniorow. Wykluczone sa asystenci i pozostaly sztab oraz druzyny
rezerw, B/II, Next Gen i zespoly mlodziezowe/U18/U19/U21/U23.
Przynaleznosc do rezerw/mlodziezy ustalac po potwierdzonym rodzaju TEAM,
rodzicu i udziale w rozgrywkach; sama nazwa nie przesadza o wykluczeniu.
Uzgodniony zakres dotyczy kolejnych pobran, planow i importow. Nie prowadzi
sie dalszych prac nad asystentami ani poprawkami ich rol. Nie usuwa sie juz
zebranych danych ani samowolnie nie cofa zmian w zaakceptowanych kopiach.
Literalne 'Manager' dyrektora klubowego nie oznacza glownego trenera.
Bledy laczenia klubow z ID zrodla zglaszac jako brak pokrycia, a nie jako
brak trenera w rzeczywistosci. Aktualizacje sa przyrostowe i uzywaja cache.


## Priorytet paczki glownych trenerow - decyzja uzytkownika 2026-11-15

Najpierw WSZYSCY glowni trenerzy pierwszych zespolow seniorow w dwoch
najwyzszych poziomach naszej klasycznej bazy dla krajow, w kolejnosci:
Anglia, Argentyna, Brazylia, Chile, Holandia, Francja, Hiszpania, Grecja,
Polska, Niemcy, Wlochy, Belgia, Portugalia.
Asystenci, pozostaly sztab, rezerwy i mlodziez pozostaja poza zakresem.
Zamknac kanoniczna liste klubow wedlug aktualnych przydzialow w bazie,
zweryfikowac wszystkie laczenia ID zrodel (w tym brakujace Italy TMID),
nastepnie uzyc cache i pobierac tylko konkretne braki. Raport pokrycia
wedlug kraju/ligi musi odroznic importowanych trenerow, przygotowane dane,
luki i wykluczone zespoly. Nie przedstawia sie czesciowej paczki jako pelnej.


## Pomoc uzytkownika w tozsamosciach trenerow - 2026-11-15
Uzytkownik dostarcza WYLACZNIE nazwisko z listy oraz UID znalezione w8.0.2,
albo wynik nie znalazlem. Nie wymagac od niego dat, typu osoby, narodowosci,
klubu ani pozostalych kolumn. Te fakty agent odczytuje i weryfikuje sam po UID.
Uproszczenie dotyczy pracy recznej uzytkownika, nie usuwa technicznych guardow
importera. Nie uzalezniac paczki od recznego uzupelnienia reszty arkusza.


## Trenerzy jako NOWE OSOBY - nadrzedna decyzja uzytkownika2026-11-15

ZAKONCZYC dopasowywanie tozsamosci, deduplikacje, badanie czy stary profil
istnieje i reczne kolejkiUID. Dla wszystkich potwierdzonych wybranych glow-
nych trenerow tworzyc NOWE profile i przypisywac je do pierwszych zespolow.
Uzytkownik jawnie zaakceptowal istnienie starszych profili tej samej osoby.
NoweUID alokowac sprawdzonym mechanizmem bez kolizji technicznych.
Zachowac scope13krajow/dwa poziomy/seniorzy; bezasystentow/rezerw/mlodziezy.
Nie wymyslac osoby przy potwierdzonym wakacie lub braku nazwiska trenera.
BrakDOB2osob jest jawna luka i nie blokuje476kompletnych profili.
Pozostaja walidacje struktury i zakresu zapisu; nie wracac do identityQA.
Nie tworzyc dalszych arkuszy/pomocniczych formatow dla uzytkownika bez zlecenia.
Kolejna paczka ma tez poprawic stadionJuventusu i wylaczyc niemiecka blokade
FAKE_NATIONAL_TEAM771 w NOWEJ kopii, bez nadpisywaniazaakceptowanejX30/SI.

## Korekta duplikatow znanych trenerow - pozniejsza decyzja 2026-11-15

Uzytkownik zakwestionowal tworzenie nowych kopii jednoznacznie znanych
trenerow (Mourinho, Spalletti). Ta korekta ma pierwszenstwo nad powyzszym
bezwzglednym CREATE AS NEW: wykorzystac juz zapisane, zweryfikowane
dopasowania istniejacych menedzerow typu1 zamiast ich nowych kopii.
Nie wracac do masowego szukania tozsamosci, konwersji zawodnikow ani kolejek
recznego UID. PlanV7 ma86takich dopasowan dla476utworzonychprofili.
Mourinho4211801, Spalletti705161 sa juz potwierdzeni; nie pytac ponownie.
Zachowac wartosciowe istniejace oceny i preferencje tych trenerow; nie
zastepowac ich domyslnymi zerami. PublicznaX32/SI sa chronione; korekta
nie zostala jeszcze wykonana i wymaga nowej kopii, nie nadpisaniaX32.
