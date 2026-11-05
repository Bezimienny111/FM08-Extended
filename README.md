# FM08 Extended

**Launcher i opcjonalne rozszerzenia dla Football Manager 2008.**  
**A launcher and optional extensions for Football Manager 2008.**

[Polski — wszystkie funkcje](PL.md) · [English — all features](EN.md) ·
[Instalacja / Installation PL/EN](INSTALLATION.md) ·
[Pełna dokumentacja techniczna / Technical documentation (PL)](DOCUMENTATION.md)

[GitHub](https://github.com/Bezimienny111/FM08-Extended) ·
[Wydania / Releases](https://github.com/Bezimienny111/FM08-Extended/releases)

Repozytorium jest na etapie prywatnych przygotowań. Dostęp do plików
i wydań wymaga uprawnień; przygotowanie katalogu nie oznacza publikacji paczek.  
The repository is private during preparation. Files and releases require
access; preparing the catalog does not mean packages have been published.

> **Projekt w rozwoju / Work in progress**  
> Integracje z silnikiem są eksperymentalne. Pierwsze testy wykonuj na kopii
> kariery. / Native integrations are experimental. Test on a career backup.

## O projekcie

FM08 Extended łączy uruchamianie gry, ustawienia obrazu i opcjonalne
rozszerzenia rozgrywki w jednym interfejsie. Każdy moduł można włączać
osobno. Domyślny tryb gracza ukrywa narzędzia techniczne; tryb zaawansowany
udostępnia diagnostykę i dzienniki.

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
| Skórki | Instalator dla rozpoznanych wariantów Steklo Black, nadpisanie skórki domyślnej i fragmenty XML. |
| Reputacja lig | Opcjonalne rzeczywiste zmiany dla 42 europejskich lig, profile kariery i dziennik. |
| Narzędzia zaawansowane | Osobna odczytowa obserwacja lig, symulacja i diagnostyka zdarzeń. |

Mapa kodów reguł jest częściowa, a instalator nie obsługuje dowolnej
skórki. Pełny ekran i długoterminowe działanie modułów wymagają dalszych
prób. Szczegóły i ograniczenia: [PL](PL.md), [EN](EN.md).

## Szybki start

Pełna [instrukcja instalacji PL/EN](INSTALLATION.md) opisuje pobieranie,
runtime, pierwszy start, panele, aktualizację i rozwiązywanie problemów.

1. Przygotuj własną instalację zgodnego **FM08 8.0.2**, Windows x64
   i **.NET 8 Desktop Runtime x64**.
2. Uruchom kompletną publikację launchera — w układzie projektu
   `app\FmLauncher.exe`.
3. Wskaż `fm.exe`; opcjonalnie folder użytkownika ze skórkami i zapisami.
4. Wybierz ustawienia oraz moduły, wykonaj kopię kariery i naciśnij **GRAJ**.
5. Zaakceptuj potwierdzenie. Ustawienia zapiszą się automatycznie.

Panele wymagają również instalacji XML z zakładki Skórki przy zamkniętej
grze. Dla rzeczywistych zmian reputacji pozostaw launcher otwarty.
Integracje są ograniczone do rozpoznanych hashy EXE:
[wymagania i zgodność](DOCUMENTATION.md#1-wymagania-i-zgodnosc).

## About the project

FM08 Extended combines game launching, display settings and independently
switchable gameplay extensions. It includes substitution/bench overrides,
age- and mentality-based PA growth, delayed aging, own-club player panels,
targeted skin installation and optional actual league reputation changes.
Advanced mode exposes separate read-only observation, diagnostics and logs.

Requires Windows x64, .NET 8 Desktop Runtime x64 and a supported FM08 8.0.2
executable. Run the complete launcher package, select your game, choose
features and press **PLAY**. Accepted settings are saved automatically.
See the [complete English feature guide](EN.md) for setup and limitations.

## Bezpieczeństwo i zakres / Safety and scope

- Projekt nie zawiera gry ani bazy danych. / The game and database are
  not included.
- Integracje sprawdzają plik gry i zmieniają pamięć nowego procesu, nie
  EXE na dysku. / Integrations validate the executable and patch the new
  process in memory, not the EXE on disk.
- Zmiany PA, rozwoju i reputacji mogą pozostać w zapisanej karierze.
  OFF ich nie cofa. / PA, development and reputation effects may persist
  in career saves; disabling a module does not undo them.
- XML skórek i konfiguracja są zapisywane na dysku. / Skin XML and
  launcher settings are written to disk.
- Pobieranie baz, uniwersalny instalator skórek, nowe panele pozycji/ukrytych
  atrybutów i modyfikatory finansów **nie są jeszcze wdrożone**. /
  Database downloads, a universal skin installer, new position/hidden-
  attribute panels and finance modifiers **are not implemented yet**.

## Dokumentacja / Documentation

| Plik / File | Zawartość / Contents |
|---|---|
| [README](README.md) | Ogólny opis i szybki start / Overview and quick start. |
| [INSTALLATION](INSTALLATION.md) | Instalacja, pierwszy start, aktualizacja i usunięcie / Installation, first launch, updating and removal (PL/EN). |
| [DOCUMENTATION](DOCUMENTATION.md) | Pełna dokumentacja techniczna po polsku: konfiguracja, modele, profile, instalacja, testy i ograniczenia. |
| [PL](PL.md) | Wszystkie aktualne funkcje opisane dla gracza po polsku. |
| [EN](EN.md) | All current features explained for players in English. |
| [RELEASES](RELEASES.md) | Zasady wersjonowania, publikacji i katalogu baz / Release and catalog maintenance (PL). |

## Budowanie / Building

Wymagany .NET 8 SDK. / Requires the .NET 8 SDK.
Z głównego katalogu projektu / From the project root:

```powershell
dotnet build .\src\FmLauncher\FmLauncher.csproj -c Release
dotnet run --project .\tests\FmLauncher.Tests\FmLauncher.Tests.csproj -c Release
dotnet publish .\src\FmLauncher\FmLauncher.csproj -c Release -r win-x64 --self-contained false -o .\publish
```

Publikacja nie dołącza runtime ani plików gry. / Publishing does not bundle
the runtime or game files.
[Testy i publikacja / Testing and packaging](DOCUMENTATION.md#14-budowanie-testowanie-i-publikacja).

## Społeczność / Community

[YouTube](https://www.youtube.com/@Bezimienny111) ·
[Discord](https://discord.gg/hP2g4MQS5T) ·
[Ko-fi](https://ko-fi.com/ericaaurora)

Chcesz wesprzeć projekt? Wpisz **FM08Extended** w treści wsparcia.  
Want to support the project? Include **FM08Extended** in your message.

## Licencja / License

Copyright (C) 2026 Bezimienny111.

Własny kod źródłowy launchera jest udostępniany na
[GNU General Public License, version 3 only (GPL-3.0-only)](LICENSE),
bez gwarancji. Przy rozpowszechnianiu programu lub jego modyfikacji
przestrzegaj wymagań GPL, w tym zapewnienia odpowiedniego kodu źródłowego.  
The original launcher source code is licensed under
[GNU GPL version 3 only (GPL-3.0-only)](LICENSE), without warranty.
Distribution of the program or modifications must comply with the GPL,
including its corresponding-source requirements.

Licencja kodu nie nadaje praw do FM08, plików gry, cudzych skórek, grafik
ani osobno publikowanych baz. Przed dołączeniem takich zasobów sprawdź
ich prawa i warunki dystrybucji.  
The code license does not grant rights to FM08, game files, third-party
skins, graphics or separately published databases. Verify their rights
and distribution terms before bundling them.
