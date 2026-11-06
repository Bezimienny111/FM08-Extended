# FM08 Extended — utrzymanie wydań

[Projekt](README.md) · [Instalacja PL/EN](INSTALLATION.md) ·
[Dokumentacja](DOCUMENTATION.md)

## Przygotowywana baza V24.1

[Gotowy opis zmian PL/EN](DATABASE_RELEASE_NOTES_V24_1.md) obejmuje etapy
V22-V24.1. V24.1 jest robocza nazwa bazy (XML 0.24.1), nie nowym
publicznym tagiem. Korekta natywna przeszla; przed pakowaniem/publikacja
wymagane sa jeszcze kontrola SI, test nowej kariery oraz ustalenie numeru
wydania. Nie zmieniono opublikowanej V21 ani katalogu pobierania.

## Zabezpieczenie aktualnych plikow launchera

Kontrola 2026-11-06: kod i testy launchera odpowiadaja tagowi
`launcher-v0.1.0`; od tego wydania zmienil sie katalog baz i dokumentacja.
Do zabezpieczenia takich zmian wystarczy commit i push, bez nowej paczki
programu. Nowy release jest potrzebny po zmianie programu, gdy chcemy
udostepnic uzytkownikom nowy gotowy build; nie podmieniamy starego ZIP.

Lokalny `app` byl odbudowany po odzyskaniu projektu. Pliki binarne nie
sa bajtowo identyczne z publikacja `win-x64`, ale kod zrodlowy jest ten sam,
a JSON jezykow jest semantycznie identyczny. Nie deklarujemy identycznosci
binariow na podstawie identycznego kodu. Opublikowany ZIP 0.1.0 ma
zweryfikowana sume SHA256 z wydania.

Nie dodawaj `app`, konfiguracji gracza, zrodlowych CSV ani katalogu
lokalnych importow do repozytorium. Sam push dokumentacji nie zmienia
zainstalowanego programu ani ustawien uzytkownika. Przy przyszlej
aktualizacji programu zachowaj jego konfiguracje i profile.

## Zakres repozytorium

Kod launchera, testy, dokumentacja i niewielki katalog wersji są w Git.
Gotowe programy i kompletne paczki baz trafiają wyłącznie do **Releases**.
Nie dodawaj do Git folderu `app`, konfiguracji gracza, profili, logów,
zapisów, plików gry ani dużych archiwów.

Repozytorium jest początkowo prywatne. Nie umieszczaj tokenu w aplikacji
ani publicznym katalogu. Anonimowe pobieranie będzie możliwe dopiero po
udostępnieniu repozytorium publicznie; obecny launcher nie pobiera baz.

## Niezależne wersje

| Produkt | Tag | Nazwa wydania | Przykładowy załącznik |
|---|---|---|---|
| Launcher | `launcher-v1.0.0` | `[Launcher] FM08 Extended 1.0.0` | `FM08-Extended-Launcher-1.0.0.zip` |
| Baza | `db-2026-27-v1.0.0` | `[Database] 2026/27 — 1.0.0` | `FM08-Extended-DB-2026-27-1.0.0.zip` |

Numery są przykładami, nie deklaracją istniejących wydań. Wewnętrzne
nazwy robocze V20/V21 nie są publiczną numeracją.

Pierwsze wydania testowe mają numer **0.1.0**:
`launcher-v0.1.0` i `db-2026-27-v0.1.0` (źródłowa V21).
Oba są pre-release. Baza zachowuje znane 160 konfliktów dat transferów
i emerytur; ich publikację jako preview zaakceptowano zamiast naprawy.
Zakres potwierdzeń i instalację opisuje [DATABASE.md](DATABASE.md).
Zawartość DAT/EDT/LNC pozostaje identyczna ze źródłem; zmieniane są wyłącznie
nazwa folderu, XML i README kopii dystrybucyjnej. Weryfikacja i konflikty
są dołączane do paczki, bez lokalnych ścieżek źródła.

- Każda wersja ma własny tag, paczkę, opis zmian i sumę SHA256.
- Używaj dokładnego adresu załącznika z tagiem, nie `releases/latest/download`.
- Przy publikowaniu bazy nie zaznaczaj jej jako **Latest** dla launchera.
  Przyszły klient i tak powinien wybierać produkt przez katalog/prefiks,
  nie ogólne API najnowszego wydania repozytorium.
- Testowe wydania oznaczaj **pre-release** i statusem `preview` w katalogu.
- Nie zmieniaj zawartości opublikowanego wydania ani nie przesuwaj tagów.
  Poprawka otrzymuje nowy numer. Stare poprawne wydania pozostają dostępne.
- Wadliwe wydanie oznacz `withdrawn`, usuń jego rekomendację i wyjaśnij
  przyczynę w opisie. Usunięcie nielegalnej zawartości lub sekretu ma
  pierwszeństwo przed zasadą zachowywania wydań.

## Publikacja launchera

1. Uruchom build i testy opisane w
   [dokumentacji](DOCUMENTATION.md#14-budowanie-testowanie-i-publikacja).
   CI nie zastępuje testu na zgodnej instalacji gry.
2. Przygotuj czysty katalog publikacji poza `app`, np.:

   ```powershell
   dotnet publish .\src\FmLauncher\FmLauncher.csproj -c Release -r win-x64 --self-contained false -o .\publish
   ```

3. Dołącz `README.md`, `INSTALLATION.md` i `LICENSE`. Zapakuj zawartość
   publikacji, tak aby `FmLauncher.exe` był od razu w głównym folderze
   po rozpakowaniu. Nie dodawaj lokalnego `FmLauncher.config.json`, profili
   ani logów. SDK/runtime i gra nie są częścią tej paczki.
4. Sprawdź instalację z czystego ZIP oraz zachowanie kopii konfiguracji
   i profili podczas aktualizacji.
5. Utwórz tag wskazujący dokładny commit źródeł użyty do budowania.
   GPLv3 wymaga zapewnienia odpowiedniego kodu źródłowego dla publikowanego
   programu; sam link do zmiennej gałęzi `main` nie identyfikuje wydania.
6. Przygotuj draft Release, wgraj ZIP i jego SHA256, opisz wymagania,
   zmiany, znane ograniczenia i instrukcję aktualizacji.
7. Zweryfikuj pliki, opublikuj wydanie i sprawdź dostęp odbiorcy.
   W prywatnym repozytorium również źródła wymagają odpowiednich uprawnień.

## Publikacja bazy

1. Wybierz zaakceptowaną kopię i jawny zakres wydania. Nie pakuj roboczej
   bazy ani nie nadpisuj egzemplarza testowanego przez użytkownika.
2. Zapisz osobno wyniki audytu natywnego, sprawdzenia/zapisu w edytorze SI
   oraz testu nowej kariery. Nie utożsamiaj tych potwierdzeń.
3. Przygotuj pełny ZIP z jednym jednoznacznym folderem bazy, np.
   `FM08Extended_2026-27_1.0.0`. Sprawdź prawa do wszystkich dołączanych
   danych i zasobów. Licencja kodu launchera nie rozstrzyga licencji bazy.
4. Zapisz rozmiar archiwum, sumę SHA256, łączny rozmiar rozpakowanych plików
   i wymagania zgodności. Nie dołączaj gry, save ani cudzych grafik bez praw.
5. Wgraj ZIP i opis do roboczego wydania z właściwym tagiem.
6. Opublikuj wydanie, pobierz ponownie paczkę i zweryfikuj jej hash
   oraz kompletność.
7. **Dopiero wtedy** dopisz wersję do katalogu i ewentualnie ustaw ją jako
   rekomendowaną. Nie dodawaj fikcyjnych adresów lub placeholderów.

## Katalog baz, schemat 1

[catalog/v1/databases.json](catalog/v1/databases.json) jest punktem wejścia
dla przyszłego klienta. Wpis dodaje się dopiero po publikacji i sprawdzeniu
pobranego archiwum. Wersja preview nie otrzymuje rekomendacji:
`recommendedDatabaseId` pozostaje `null`.

[JSON Schema](catalog/v1/databases.schema.json) określa wymagane pola.
Przykład struktury wpisu, **nie gotowy wpis do publikacji**:

```text
id: db-2026-27-v1.0.0
version: 1.0.0
season: 2026/27
name: { pl: ..., en: ... }
publishedAt: data i czas UTC
status: stable | preview | withdrawn
releaseTag: db-2026-27-v1.0.0
releaseNotesUrl: dokładny adres wydania
downloadUrl: dokładny adres załącznika tego wydania
archiveSizeBytes: rozmiar pobieranego ZIP
installedSizeBytes: łączny rozmiar plików po rozpakowaniu
sha256: 64 znaki szesnastkowe
installFolder: jeden bezpieczny, wersjonowany segment nazwy folderu
minimumLauncherVersion: minimalna wersja przyszłego klienta lub null dla instalacji ręcznej
supportedGameHashes: jawna lista obsługiwanych SHA256 gry
requiresNewCareer: true
```

Identyfikatory są unikalne, a `recommendedDatabaseId` wskazuje istniejący
wpis `stable` lub ma wartość `null`. JSON Schema opisuje pojedyncze pola;
unikalność ID, referencję rekomendacji i zgodność tagu/adresów trzeba
sprawdzić również przed publikacją. Nie wpisuj dzisiejszego launchera jako
minimalnej wersji instalatora: funkcja pobierania nie istnieje jeszcze.
`minimumLauncherVersion: null` oznacza bazę do ręcznej instalacji bez
wymagania launchera, nie deklarację dostępności pobierania w aplikacji.

Katalog może zmieniać status i rekomendację, lecz nie tożsamość, hash,
folder ani zawartość opublikowanej wersji. Przyszły klient ma odrzucać
nieznany schemat, niezgodne wymagania i pozycje `withdrawn`; `preview`
powinny być domyślnie ukryte.

## Wymagania przyszłego instalatora

- Pobieranie na żądanie, postęp i anulowanie; cache katalogu oraz jawny
  komunikat o braku sieci. Awaria hostingu nie blokuje lokalnej gry.
- Brak sekretów i tokenów osadzonych w programie.
- Weryfikacja SHA256 przed rozpakowaniem, kontrola ścieżek ZIP, limitów
  rozpakowania, wolnego miejsca i wymaganych plików.
- Instalacja przez staging do nowego folderu wersji; bez nadpisywania
  zaakceptowanych lub zmodyfikowanych baz i zapisów.
- Baza jest wybierana w FM08 przy tworzeniu **nowej kariery**.
  Pobranie innej wersji nie aktualizuje istniejącego zapisu.

To wymagania dla późniejszej implementacji, nie opis gotowych przycisków.
Na początku wystarczą kompletne ZIP-y i ręczna publikacja; automatyzację
Releases można dodać bez zmiany identyfikatorów baz.
