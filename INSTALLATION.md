# FM08 Extended — instalacja / installation

[Projekt / Project](README.md) · [Funkcje PL](PL.md) · [Features EN](EN.md) ·
[Dokumentacja techniczna](DOCUMENTATION.md)

[Polski](#polski) · [English](#english)

<a id="polski"></a>
## Polski

### 1. Wymagania

- Windows x64.
- Własna instalacja **Football Manager 2008 8.0.2** ze zgodnym `fm.exe`.
  Integracje rozpoznają konkretne sumy pliku, nie sam numer wersji:
  [obsługiwane pliki gry](DOCUMENTATION.md#1-wymagania-i-zgodnosc).
- **.NET 8 Desktop Runtime dla Windows x64** z
  [oficjalnej strony Microsoft](https://dotnet.microsoft.com/en-us/download/dotnet/8.0).
  Wybierz **.NET Desktop Runtime → Windows → x64**. Sam .NET Runtime,
  ASP.NET Core Runtime ani wariant x86 nie zastępują tej instalacji.
- Folder launchera z prawem zapisu oraz kopia zapasowa testowanej kariery.

Launcher nie zawiera gry, jej EXE, baz ani skórek. Nie pobieraj zamiennika
`fm.exe` z przypadkowej strony, aby ominąć sprawdzanie zgodności.

### 2. Pobranie i rozpakowanie

1. Otwórz [wydania FM08 Extended](https://github.com/Bezimienny111/FM08-Extended/releases).
   Dopóki repozytorium jest prywatne, dostęp wymaga zalogowania na konto
   z uprawnieniami. Pierwsze wydanie to `launcher-v0.1.0` (pre-release).
2. Wybierz wydanie **launchera**, oznaczone tagiem `launcher-v...`,
   i pobierz dołączoną paczkę ZIP. **Source code (zip/tar.gz)** to źródła,
   nie gotowy program. Wydania `db-...` zawierają osobne bazy.
3. Jeżeli wydanie zawiera sumę SHA256, porównaj ją przed rozpakowaniem:

   ```powershell
   Get-FileHash -LiteralPath 'C:\Downloads\FM08-Extended-Launcher-1.0.0.zip' -Algorithm SHA256
   ```

   Nazwa i ścieżka są przykładowe. Wynik musi odpowiadać sumie opublikowanej
   dla dokładnie tej paczki. Przy niezgodności nie uruchamiaj plików.
4. Rozpakuj **całe archiwum**, np. do `D:\Tools\FM08Extended`.
   Nie uruchamiaj programu bezpośrednio z ZIP i nie kopiuj samego EXE.
   Nie trzeba instalować launchera w katalogu gry ani w `Program Files`.
5. Uruchom `FmLauncher.exe` z rozpakowanego folderu. W lokalnym układzie
   projektu gotowa aplikacja znajduje się w `app\FmLauncher.exe`.

Obok EXE muszą pozostać pliki `FmLauncher.dll`, `FmLauncher.deps.json`,
`FmLauncher.runtimeconfig.json` oraz dostarczony
`FmLauncher.languages.json`. Nie zmieniaj ich nazw.

### 3. Pierwsze uruchomienie

1. Zamknij uruchomioną grę. W launcherze wskaż bezpośrednio **`fm.exe`**,
   nie skrót ani inny loader.
2. Opcjonalnie wskaż **folder danych użytkownika FM08**, zawierający
   skórki, grafiki i zapisy. To nie instalacyjny folder `data`.
   Wybór tej ścieżki nie przenosi plików ani nie zmienia miejsca zapisu
   kariery w FM08.
3. Wybierz język, motyw, tryb obrazu i potrzebne moduły. Integracje są
   eksperymentalne; zacznij od kopii kariery i nie włączaj wszystkich
   nowych funkcji naraz.
4. Jeśli chcesz dodatkowe dane paneli, wykonaj osobną instalację XML
   opisaną poniżej.
5. Naciśnij **GRAJ**, przeczytaj potwierdzenie i zaakceptuj je.
   Ustawienia zapiszą się automatycznie.
6. Gdy używasz **rzeczywistych zmian reputacji lig**, pozostaw launcher
   otwarty podczas gry.

Nowa konfiguracja ma włączone moduły obrazu i paneli. Jeśli nie korzystasz
z paneli, możesz je wyłączyć. Pełny ekran wymaga dalszych testów; w razie
problemu sprawdź obsługiwaną rozdzielczość i tryb okna.

### 4. Opcjonalna instalacja paneli

Sam przełącznik paneli nie instaluje plików skórki.

1. Przy zamkniętej grze otwórz zakładkę **Skórki**.
2. Wskaż właściwy katalog `skins` i użyj dostępnego instalatora.
3. Obecny instalator wymaga rozpoznanej skórki **Steklo Black** lub
   **Steklo Left Black**, również przy tworzeniu nadpisań skórki domyślnej.
   Nie jest uniwersalnym instalatorem dla każdej skórki.
4. Po udanej instalacji uruchom FM08. Jeśli stare panele są w pamięci
   podręcznej, wyłącz cache skórek i włącz ponowne wczytywanie skórki
   przy zatwierdzaniu ustawień w preferencjach gry.

Instalator tworzy kopie zastępowanych XML z końcówką
`.before-fmext-panels`. Zachowaj je do ewentualnego przywrócenia.
Szczegóły: [panele i skórki](DOCUMENTATION.md#8-panele-zawodnikow-i-skorki).

### 5. Aktualizacja i usunięcie

- Zamknij launcher i grę przed aktualizacją.
- Zachowaj kopię całego starego folderu. Nowe wydanie rozpakuj do
  **nowego folderu** i przeczytaj jego informacje o zgodności.
- Jeśli wydanie nie wymaga migracji, przenieś kopię
  `FmLauncher.config.json` oraz katalogów `profils`, `league-profiles`,
  `league-changes`, `league-observations` i `league-diagnostics`, o ile
  istnieją. **Nie usuwaj profili kariery i nie mieszaj ich z cudzymi**.
  Lista plików: [konfiguracja i dane](DOCUMENTATION.md#11-pliki-i-schemat-konfiguracji).
- Własne tłumaczenia zachowaj osobno i uzgodnij z nowym katalogiem języków;
  nie zastępuj nowego pliku bez sprawdzenia zmian.
- Przed powrotem do starszego launchera sprawdź zgodność konfiguracji
  i profili. Nie zakładaj automatycznej migracji wstecz.
- Usunięcie folderu aplikacji usuwa także dane zapisane w tym folderze.
  Wcześniej wykonaj ich kopię. XML skórek pozostają osobno; przywracaj
  właściwe kopie plików przy zamkniętej grze.
- Wyłączenie lub usunięcie launchera **nie cofa zmian PA, rozwoju
  i reputacji zapisanych już w karierze**.

### 6. Najczęstsze problemy

| Problem | Co sprawdzić |
|---|---|
| Komunikat o brakującym .NET | Zainstaluj **Desktop Runtime 8 x64**, nie tylko zwykły runtime. |
| Program nie uruchamia się po skopiowaniu EXE | Rozpakuj ponownie kompletną paczkę. |
| Niezgodny plik gry | Sprawdź wersję i SHA256; nie omijaj zabezpieczeń. |
| Błąd zapisu ustawień | Użyj folderu z prawem zapisu; zachowaj błędny plik do diagnozy. |
| Brak danych paneli | Sprawdź moduł, instalację XML, obsługiwaną skórkę i cache gry. |
| Brak pobierania bazy w programie | Ta funkcja nie jest jeszcze wdrożona. |

Nie wyłączaj ochrony systemu ani antywirusa, aby obejść ostrzeżenia.
Zweryfikuj źródło paczki, sumę kontrolną i zgłoś problem.

### 7. Osobna baza sezonu 2026/27

Pobierz paczkę z wydania `db-2026-27-v0.1.0`, nie archiwum Source code.
Rozpakuj folder `FM08Extended_2026-27_0.1.0` do katalogu baz FM08,
obok istniejących baz, bez nadpisywania ich. W grze rozpocznij nową karierę
i wybierz **FM08 Extended 2026/27 0.1.0 Preview (V21)**.

To wersja testowa ze znanymi konfliktami przyszłych transferów i emerytur.
Przeczytaj [pełną instrukcję i ograniczenia bazy](DATABASE.md#polski).
Baza nie aktualizuje istniejących karier, a launcher nie instaluje jej sam.

<a id="english"></a>
## English

### 1. Requirements

- Windows x64 and your own **Football Manager 2008 8.0.2** installation.
  Native integrations accept only the
  [documented executable hashes](DOCUMENTATION.md#1-wymagania-i-zgodnosc).
- **.NET 8 Desktop Runtime for Windows x64** from
  [Microsoft](https://dotnet.microsoft.com/en-us/download/dotnet/8.0).
  Choose **.NET Desktop Runtime → Windows → x64**. The plain .NET Runtime,
  ASP.NET Core Runtime and x86 downloads are not substitutes.
- A writable launcher folder and a backup of your test career.

The package does not include the game, its executable, databases or skins.

### 2. Download and install

1. Open [FM08 Extended releases](https://github.com/Bezimienny111/FM08-Extended/releases).
   While the repository is private, sign in with an authorized account.
   The first release is `launcher-v0.1.0` (pre-release).
2. Select a **launcher** release tagged `launcher-v...` and download its
   attached ZIP. **Source code** archives are not ready-to-run packages.
   Tags starting with `db-` identify separate database releases.
3. If a SHA256 checksum is provided, verify the downloaded ZIP using
   `Get-FileHash` as shown in the Polish section. Do not run a mismatched
   package.
4. Extract the **entire ZIP** to a writable folder, for example
   `D:\Tools\FM08Extended`. Do not run from inside the ZIP or copy only
   the executable. Installing inside the game folder is not required.
5. Run `FmLauncher.exe`. Keep its DLL, `.deps.json`, `.runtimeconfig.json`
   and `FmLauncher.languages.json` alongside it.
   In the local source workspace, the installed app is under `app`.

### 3. First launch and optional panels

1. Close the game and select the actual `fm.exe`, not a shortcut or loader.
2. Optionally select your FM08 **user data folder** containing skins,
   graphics and saves, not the game's installation `data` folder.
   This does not move files or redirect FM08 saves.
3. Choose your language, theme, display settings and optional modules.
   Test experimental integrations on a copy of your career.
4. Press **PLAY** and accept the confirmation. Settings are saved
   automatically.
5. Keep the launcher open when using **actual league reputation changes**.

Display and player panels are enabled in a new configuration. Disable
panels if not needed. Fullscreen needs further testing; try windowed mode
and a supported resolution when diagnosing display problems.

Panel XML requires a **separate installation** from the **Skins** tab
while FM08 is closed. The current installer requires a recognized
**Steklo Black** or **Steklo Left Black** skin, even when preparing
default-skin overrides. It does not support arbitrary skins. Reload the
skin and disable the game's skin cache if old panels remain visible.
Preserve the `.before-fmext-panels` XML backups.

### 4. Updating, removing and troubleshooting

- Close the game and launcher, back up the old folder, and extract an
  update into a **new folder**. Read its compatibility notes first.
- Unless migration instructions say otherwise, copy your
  `FmLauncher.config.json` and existing `profils`, `league-profiles`,
  `league-changes`, `league-observations` and `league-diagnostics` folders.
  Preserve career profiles; do not mix them with another player's data.
- Back up custom translations separately and reconcile them with the new
  language file. Check profile/configuration compatibility before downgrading.
- Removing the application folder also removes data stored there.
  Skin XML is separate; restore the appropriate backups with FM08 closed.
- Disabling or removing the launcher **does not undo PA, development or
  reputation changes already stored in career saves**.
- Missing runtime: install **Desktop Runtime 8 x64**. Missing DLLs:
  extract the complete package. Unsupported executable: check compatibility,
  do not bypass validation. Missing panel data: check the switch, XML,
  supported skin and cache.
- Database downloading is **not implemented yet**. Installing a future
  database package will not update an existing career.
- Do not disable antivirus or system protection to bypass a warning.
  Verify the package source/checksum and report the issue.

See the [English feature guide](EN.md) and
[technical troubleshooting](DOCUMENTATION.md#13-rozwiazywanie-problemow).

### 5. Separate 2026/27 database

Download the package from `db-2026-27-v0.1.0`, not a Source code archive.
Extract `FM08Extended_2026-27_0.1.0` into the FM08 database directory,
alongside existing databases without overwriting them. Start a new career
and select **FM08 Extended 2026/27 0.1.0 Preview (V21)**.

This preview has known future-transfer/retirement conflicts.
Read the [database installation and limitations](DATABASE.md#english).
It does not update existing careers; the launcher does not install it.
