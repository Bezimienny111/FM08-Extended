# FM08 Extended

[ENG](#eng) · [PL](#pl)

### Development R23: direct start, skins and configuration compatibility

PLAY starts directly without a routine summary/confirmation dialog. Configuration
validation, panel readiness checks and actual error/warning messages remain enabled.

Skin installation is available only from **Skins → Basic → Create/update Ext skins**.
Buttons in feature details only open that page. PLAY never changes skin files:
panel-dependent features require installed panels with matching hashes and FM language.
If panels are missing or need a language update, launch stops with instructions.
Choose the installed Ext skin in FM and reload it with skin caching disabled.

Skins now has **Basic** and **Advanced** sections. R21 gives both selectors visible frames and standardizes create/detect/copy actions to the same size and font. Basic detects the built-in
FM08 skin and installed Steklo/Steklo Black variants in the configured skins
folder. One action creates/updates Base Ext, Steklo Ext and Steklo Black Ext,
Left/Right when their parents are available. It includes the selected player
panels and the match reaction column. Originals, graphics and Noche stay unchanged.

Advanced explains child descriptors, target files, widget IDs and manual merging
for other skins, with seven XML/reference topics. It is not an automatic converter
for arbitrary layouts. Installation is blocked while FM is running; writes retain
backups and readback receipts. There is no automatic removal or cleanup. Rollback
restores inherited baseline XML for new overrides and retains created folders.

R14 uses `FmLauncher.ini` next to the launcher. If it is absent, the existing
`FmLauncher.config.json` is read without changing it. PLAY and closing the launcher write INI
and a schema-1 JSON mirror readable by earlier launchers. When both exist,
INI is authoritative. R17 removes the manual Save/Reload buttons from the footer.
Closing writes only changed valid settings; an unchanged close creates no extra
backup. Failed/unreadable configuration is never replaced with defaults. A retry
action appears in Settings only after a configuration read failure.

The optional team-talk flag stays INI-only so older strict schema-1 JSON readers
can still load the compatible JSON mirror. New optional fields must preserve
this compatibility; closing must detect changes to INI-only fields too.

INI schema 1 keeps stable sections `[Launcher]`, `[Display]`, `[Features]` and
`[Rule.0]` through `[Rule.28]`. Strings are JSON-quoted UTF-8 values (including
escaped Windows path backslashes); booleans are `true`/`false`, numbers use
invariant decimal notation. Hand-edited unquoted strings are also accepted.
Rules retain their original numeric meaning. Missing optional keys use the
model defaults. Unknown sections, keys and comments survive subsequent saves.
Duplicate keys, invalid values and unsupported newer schema versions are
rejected rather than silently reset. A schema change must have an explicit
migration; existing keys must not be repurposed in the same schema.

Each replacement retains a unique `.bak`; failed pending `.tmp` files remain.
If an INI commit fails after updating an existing JSON mirror, that JSON is
restored from its backup. No file deletion is used. These guarantees must be
covered in future changes with migration, complete settings/rule roundtrip,
unknown-key preservation, optional-default and failed-save checks.

R18 navigation: Settings, Graphics, Skins, Features, Community Links on the
left. Settings (paths and advanced mode) opens first. The centered heading and
the bottom PLAY/support/log area remain fixed; PLAY is below the left navigation.
Features have independently scrolling selector/details regions; the entire
selected feature card is tinted. Graphics has its own page. Nested editor and
scroll sections use visible frames in both light and dark themes.
The sidebar follows the current skin surface and uses a double frame rather
than a contrasting navy fill. Captions render without mnemonic underlining.
The compact footer retains support links and collapsible logs. Selecting feature
details or resizing reflows descriptions to the available content width.
R19 places the framed language selector in the top-left corner and the bold,
outlined theme button in the top-right corner. The launcher title stays centered.

**PL:** `FmLauncher.ini` ma pierwszeństwo przed JSON. Przy braku INI zachowany
jest odczyt starszej konfiguracji JSON. Od R17 GRAJ i zamknięcie launchera
zapisują oba formaty; bez zmian nie powstaje dodatkowa kopia zapasowa.
Zgodność schematu, domyślne nowe opcje oraz zachowanie nieznanych kluczy są
obowiązującymi zasadami dalszego rozwoju; nie wolno resetować ustawień przy
aktualizacji. Pliki wcześniejszych wersji launchera pozostają chronione.

## ENG

### Run the release — no building required

1. Open [Releases](https://github.com/Bezimienny111/FM08-Extended/releases)
   and select a **launcher** release tagged `launcher-v...`.
2. Under **Assets**, download the launcher ZIP — **not** the automatically
   generated **Source code** archives. Releases tagged `db-...` are
   separate database packages, not the launcher.
3. Install **.NET 8 Desktop Runtime for Windows x64** from
   [Microsoft](https://dotnet.microsoft.com/en-us/download/dotnet/8.0).
   Choose **.NET Desktop Runtime → Windows → x64**.
4. Extract the **entire ZIP** into a writable folder, for example
   `D:\Tools\FM08Extended`. Keep all included files together; do not run
   the application inside the ZIP or copy only the EXE.
5. Run **`FmLauncher.exe`** from the extracted folder.
6. Select your own supported **FM08 8.0.2 `fm.exe`**, choose settings
   and optional modules, then press **PLAY**.
   Settings are saved automatically.

**No SDK, source download or compilation is needed to run a release.**
Use a career backup for initial testing. The game and database are not
included in the launcher package.

[Full installation guide](INSTALLATION.md#english) — requirements,
first launch, optional panels, updating, removal and troubleshooting.

**First preview packages:**
[Launcher 0.1.0](https://github.com/Bezimienny111/FM08-Extended/releases/tag/launcher-v0.1.0) ·
[2026/27 database 0.1.0 (V21)](https://github.com/Bezimienny111/FM08-Extended/releases/tag/db-2026-27-v0.1.0).
These are **pre-releases**, not stable versions. While the repository is
private, downloads and Issues require an authorized account; after it is
made public, downloads are available without signing in.

### Report a bug

Please report bugs through
[GitHub Issues](https://github.com/Bezimienny111/FM08-Extended/issues).
Sign in to GitHub, check whether the problem has already been reported,
and select **New issue** if no matching report exists. Use one issue per
problem; add details to an existing matching issue instead of duplicating it.

Include:

- Launcher version, FM08 version and database version if relevant.
- Windows version, enabled modules and the skin/display settings involved.
- Steps to reproduce the problem, expected behavior and actual behavior.
- The exact error message, screenshots and relevant log excerpts if available.
  Technical logs are accessible through the launcher's advanced mode.

Remove personal information, private paths and sensitive data before
attaching files. Do not upload game executables or complete game files.
While the repository is private, Issues also requires repository access.
Reports in **English or Polish** are welcome.

### The 2026/27 database

The database is a **separate download**, based on the V21 modern overhaul.
It contains modern squads and talents, with over 29,000 modern player
profiles across more than 1,100 clubs. Staff and stadium modernization
are not included. It requires a **new career** and FM08 8.0.2.

**Known preview issue:** the audit found 160 future-transfer/retirement
date conflicts, including Daniele Cacia. Historical players may remain
available or join clubs later. Do not treat this version as fully cleaned.
See [database installation, validation and limitations](DATABASE.md#english).
The launcher does not download or install databases automatically.

Prepared, unpublished update:
[V24.1 changes and remaining checks (PL/EN)](DATABASE_RELEASE_NOTES_V24_1.md).

### About the project

**FM08 Extended is a launcher and optional extensions for Football Manager
2008.** It combines game launching, display settings and independently
switchable gameplay modules. Player mode hides technical tools; advanced
mode exposes diagnostics and logs.

> **Work in progress:** native integrations are experimental. Test on a
> copy of your career before using them in regular play.

### Current features

| Area | Features |
|---|---|
| Launching | Game selection, persistent settings and automatic saving when PLAY is pressed. |
| Interface | English/Polish, light/dark themes, player and advanced modes. |
| Display | Windowed, borderless, fullscreen and resolution detection up to 1920 × 1080. |
| Match rules | Independent substitution/bench overrides, range 0–12, a 29-code table, spin buttons and sorting. |
| Player development | Optional age- and mentality-based PA growth. |
| Aging | Optional three-year delay to physical decline and CA penalty thresholds. |
| Player panels | Seasonal fatigue and CA/PA for your own club in supported views. |
| Skins | Basic creates Base/Steklo/Steklo Black Ext variants; Advanced explains manual integration and provides XML references. |
| League reputation | Optional actual changes for 42 European leagues, career profiles and a journal. |
| Advanced tools | Separate read-only league observation, simulation and event diagnostics. |

The rule-code map is partial. The skin installer targets the three catalogued
families; default Ext creation works without Steklo installed. Other layouts
use the Advanced manual integration guide. Fullscreen and long-term module behavior need
further testing. See the [complete English feature guide](EN.md).

### Safety and scope

- Requires Windows x64, .NET 8 Desktop Runtime x64 and a supported game
  executable. Integrations verify the full SHA256:
  [compatibility details, Polish](DOCUMENTATION.md#1-wymagania-i-zgodnosc).
- Native integrations patch the newly launched process in memory, not
  the game EXE on disk.
- PA, development and reputation effects may persist in career saves.
  Disabling a module does not undo them.
- Settings and skin XML are written to disk. Panels require separate XML
  installation from **Skins** while the game is closed.
- Keep the launcher open when using actual league reputation changes.
- Selecting a user data folder does not move files or redirect FM08 saves.
- Database downloading, a universal skin installer, new position/hidden-
  attribute panels and finance modifiers **are not implemented yet**.

### Documentation

| Guide | Contents |
|---|---|
| [Installation](INSTALLATION.md#english) | Downloading and running the release, updating and troubleshooting. |
| [English features](EN.md) | All current features and limitations in English. |
| [Polish features](PL.md) | All current features and limitations in Polish. |
| [Technical documentation](DOCUMENTATION.md) | Configuration, profiles, integration details and tests; Polish. |
| [Release maintenance](RELEASES.md) | Independent release streams and the future database catalog; Polish. |

### Build from source — developers only

Requires the **.NET 8 SDK**. From the project root:

```powershell
dotnet build .\src\FmLauncher\FmLauncher.csproj -c Release
dotnet run --project .\tests\FmLauncher.Tests\FmLauncher.Tests.csproj -c Release
dotnet publish .\src\FmLauncher\FmLauncher.csproj -c Release -r win-x64 --self-contained false -o .\publish
```

Run `publish\FmLauncher.exe` with its accompanying files. Publishing does
not bundle the runtime or game files.
[Testing and packaging, Polish](DOCUMENTATION.md#14-budowanie-testowanie-i-publikacja).

### Community

[YouTube](https://www.youtube.com/@Bezimienny111) ·
[Discord](https://discord.gg/hP2g4MQS5T) ·
[Ko-fi](https://ko-fi.com/ericaaurora)

Want to support the project? Include **FM08Extended** in your message.

### License

Copyright (C) 2026 Bezimienny111.

The original launcher source code is licensed under
[GNU GPL version 3 only (GPL-3.0-only)](LICENSE), without warranty.
Distribution of the program or modifications must comply with the GPL,
including its corresponding-source requirements.

The code license does not grant rights to FM08, game files, third-party
skins, graphics or separately published databases. Verify their rights
and distribution terms before bundling them.

## PL

### Uruchomienie gotowego wydania — bez kompilacji

1. Otwórz [Releases](https://github.com/Bezimienny111/FM08-Extended/releases)
   i wybierz wydanie **launchera** z tagiem `launcher-v...`.
2. W sekcji **Assets** pobierz ZIP launchera — **nie** automatyczne
   archiwum **Source code**. Wydania z tagiem `db-...` zawierają osobne
   bazy danych, nie launcher.
3. Zainstaluj **.NET 8 Desktop Runtime dla Windows x64** ze strony
   [Microsoft](https://dotnet.microsoft.com/en-us/download/dotnet/8.0).
   Wybierz **.NET Desktop Runtime → Windows → x64**.
4. Rozpakuj **cały ZIP** do katalogu z prawem zapisu, np.
   `D:\Tools\FM08Extended`. Zachowaj wszystkie dołączone pliki razem.
   Nie uruchamiaj programu z wnętrza ZIP i nie kopiuj samego EXE.
5. Uruchom **`FmLauncher.exe`** z rozpakowanego folderu.
6. Wskaż własny zgodny **`fm.exe` z FM08 8.0.2**, wybierz ustawienia
   i potrzebne moduły, naciśnij **GRAJ** i zaakceptuj potwierdzenie.
   Ustawienia zapiszą się automatycznie.

**Do uruchomienia wydania nie potrzebujesz SDK, źródeł ani kompilacji.**
Pierwsze próby wykonuj na kopii kariery. Paczka launchera nie zawiera
gry ani bazy danych.

[Pełna instrukcja instalacji](INSTALLATION.md#polski) — wymagania,
pierwszy start, opcjonalne panele, aktualizacja, usunięcie i pomoc.

**Pierwsze paczki testowe:**
[Launcher 0.1.0](https://github.com/Bezimienny111/FM08-Extended/releases/tag/launcher-v0.1.0) ·
[Baza 2026/27 0.1.0 (V21)](https://github.com/Bezimienny111/FM08-Extended/releases/tag/db-2026-27-v0.1.0).
To **pre-release**, nie wersje stabilne. Dopóki repozytorium jest prywatne,
pobieranie i Issues wymagają uprawnień; po jego upublicznieniu pobieranie
będzie dostępne bez logowania.

### Zgłaszanie błędów

Błędy zgłaszaj przez
[GitHub Issues](https://github.com/Bezimienny111/FM08-Extended/issues).
Zaloguj się do GitHuba, sprawdź, czy problem został już zgłoszony,
i wybierz **New issue**, jeśli nie ma pasującego zgłoszenia. Jeden problem
opisuj w jednym zgłoszeniu; zamiast tworzyć duplikat, dopisz szczegóły
do istniejącego.

Podaj:

- Wersję launchera, FM08 i używanej bazy, jeśli dotyczy problemu.
- Wersję Windows, włączone moduły oraz skórkę i ustawienia obrazu związane
  z problemem.
- Kroki odtworzenia błędu, oczekiwane zachowanie i rzeczywisty wynik.
- Dokładny komunikat błędu, zrzuty ekranu i odpowiednie fragmenty logów,
  jeśli są dostępne. Dostęp do logów technicznych daje tryb zaawansowany.

Przed dołączeniem plików usuń dane osobowe, prywatne ścieżki i informacje
wrażliwe. Nie przesyłaj plików wykonywalnych ani kompletnych plików gry.
Dopóki repozytorium jest prywatne, również Issues wymaga dostępu do niego.
Zgłoszenia można pisać **po polsku lub angielsku**.

### Baza sezonu 2026/27

Baza jest **osobną paczką**, opartą na modernizacji V21.
Obejmuje współczesne kadry i talenty: ponad 29 tys. nowoczesnych profili
w ponad 1100 klubach. Nie modernizuje sztabów ani stadionów.
Wymaga **nowej kariery** oraz FM08 8.0.2.

**Znany problem preview:** audyt wykrył 160 konfliktów dat przyszłych
transferów i emerytur, w tym Cacii. Historyczni gracze mogą pozostać
dostępni lub później dołączyć do klubów. To nie jest w pełni oczyszczona baza.
Zobacz [instalację, potwierdzenia i ograniczenia bazy](DATABASE.md#polski).
Launcher nie pobiera ani nie instaluje baz automatycznie.

### O projekcie

**FM08 Extended to launcher i opcjonalne rozszerzenia dla Football Manager
2008.** Łączy uruchamianie gry, ustawienia obrazu i niezależnie włączane
moduły rozgrywki. Tryb gracza ukrywa narzędzia techniczne; tryb zaawansowany
udostępnia diagnostykę i dzienniki.

> **Projekt w rozwoju:** integracje z silnikiem są eksperymentalne.
> Przed regularną grą przetestuj je na kopii kariery.

### Aktualne możliwości

| Obszar | Funkcje |
|---|---|
| Uruchamianie | Wybór gry, zapamiętywanie ustawień i automatyczny zapis po potwierdzeniu GRAJ. |
| Interfejs | Polski/angielski, jasny/ciemny motyw, tryb gracza i zaawansowany. |
| Obraz | Okno, okno bez ramki, pełny ekran i wykrywanie rozdzielczości do 1920 × 1080. |
| Reguły meczowe | Niezależne nadpisania zmian i rezerwowych, zakres 0–12, tabela 29 kodów, strzałki i sortowanie. |
| Rozwój zawodników | Opcjonalny wzrost PA zależny od wieku i mentalności. |
| Starzenie | Opcjonalne przesunięcie progów spadku fizyczności i kar CA o 3 lata. |
| Panele zawodników | Zmęczenie sezonowe oraz CA/PA dla własnego klubu w obsługiwanych widokach. |
| Skórki | Podstawowe tworzą warianty Base/Steklo/Steklo Black Ext; Zaawansowane opisują ręczną integrację i zawierają wzorce XML. |
| Reputacja lig | Opcjonalne rzeczywiste zmiany dla 42 europejskich lig, profile kariery i dziennik. |
| Narzędzia zaawansowane | Osobna odczytowa obserwacja lig, symulacja i diagnostyka zdarzeń. |

Mapa kodów reguł jest częściowa. Instalator obsługuje trzy rodziny z katalogu;
podstawowe Ext można tworzyć bez zainstalowanego Steklo. Inne układy wymagają
ręcznej integracji opisanej w Zaawansowanych. Pełny ekran i długoterminowe działanie modułów
wymagają dalszych prób. Szczegóły: [pełny opis funkcji PL](PL.md).

### Bezpieczeństwo i zakres

- Wymagany Windows x64, .NET 8 Desktop Runtime x64 i zgodny plik gry.
  Integracje sprawdzają pełną sumę SHA256:
  [wymagania i zgodność](DOCUMENTATION.md#1-wymagania-i-zgodnosc).
- Integracje zmieniają pamięć nowego procesu gry, nie EXE na dysku.
- Zmiany PA, rozwoju i reputacji mogą pozostać w zapisanej karierze.
  Wyłączenie modułu ich nie cofa.
- Ustawienia i XML skórek są zapisywane na dysku. Panele wymagają
  osobnej instalacji XML z zakładki **Skórki** przy zamkniętej grze.
- Dla rzeczywistych zmian reputacji pozostaw launcher otwarty.
- Wybór folderu użytkownika nie przenosi plików ani nie przekierowuje
  zapisów FM08.
- Pobieranie baz, uniwersalny instalator skórek, nowe panele pozycji/ukrytych
  atrybutów i modyfikatory finansów **nie są jeszcze wdrożone**.

### Dokumentacja

| Poradnik | Zawartość |
|---|---|
| [Instalacja](INSTALLATION.md#polski) | Pobranie i uruchomienie wydania, aktualizacja i rozwiązywanie problemów. |
| [Funkcje PL](PL.md) | Wszystkie aktualne funkcje i ograniczenia po polsku. |
| [Funkcje EN](EN.md) | Wszystkie aktualne funkcje i ograniczenia po angielsku. |
| [Dokumentacja techniczna](DOCUMENTATION.md) | Konfiguracja, profile, mechanizmy integracji i testy. |
| [Utrzymanie wydań](RELEASES.md) | Niezależne serie wydań i katalog przyszłych baz. |

### Budowanie ze źródeł — tylko dla deweloperów

Wymagany **.NET 8 SDK**. Z głównego katalogu projektu:

```powershell
dotnet build .\src\FmLauncher\FmLauncher.csproj -c Release
dotnet run --project .\tests\FmLauncher.Tests\FmLauncher.Tests.csproj -c Release
dotnet publish .\src\FmLauncher\FmLauncher.csproj -c Release -r win-x64 --self-contained false -o .\publish
```

Uruchom `publish\FmLauncher.exe` wraz z plikami towarzyszącymi.
Publikacja nie dołącza runtime ani plików gry.
[Testy i publikacja](DOCUMENTATION.md#14-budowanie-testowanie-i-publikacja).

### Społeczność

[YouTube](https://www.youtube.com/@Bezimienny111) ·
[Discord](https://discord.gg/hP2g4MQS5T) ·
[Ko-fi](https://ko-fi.com/ericaaurora)

Chcesz wesprzeć projekt? Wpisz **FM08Extended** w treści wsparcia.

### Licencja

Copyright (C) 2026 Bezimienny111.

Własny kod źródłowy launchera jest udostępniany na
[GNU General Public License, version 3 only (GPL-3.0-only)](LICENSE),
bez gwarancji. Przy rozpowszechnianiu programu lub jego modyfikacji
przestrzegaj wymagań GPL, w tym zapewnienia odpowiedniego kodu źródłowego.

Licencja kodu nie nadaje praw do FM08, plików gry, cudzych skórek, grafik
ani osobno publikowanych baz. Przed dołączeniem takich zasobów sprawdź
ich prawa i warunki dystrybucji.
