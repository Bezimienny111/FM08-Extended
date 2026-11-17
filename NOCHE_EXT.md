# NocheExt — wariant dev, decyzja 2026-11-13

NocheExt dziedziczy `noche`; oryginalna Noche nie ma jawnego rodzica, więc pozostałe panele korzystają ze standardowego fallbacku archiwów FM. Grafika, fonty, ustawienia i pozostałe zasoby pozostają w Noche. Dziecko zawiera tylko descriptor oraz pięć wspólnych paneli.

Katalog `ExtSkinCatalog` jest jednym źródłem obsługiwanych wariantów: cztery dotychczasowe Ext i NocheExt. Wspólne poprawki paneli mają odtąd obejmować także NocheExt. Instalator tworzy descriptor NocheExt w tej samej transakcji co panele, gdy rodzic Noche jest dostępny. Receipt obejmuje jego własność, backupy, readback i Undo. Oryginalne skórki i dowolne niekatalogowane warianty pozostają poza zakresem zapisu.

Obsługiwane są dotychczasowe CA/PA, zmęczenie, 12 ukrytych cech i 11 ról; wyróżnianie nazwy oraz wartości korzysta z zaakceptowanego mechanizmu R10. Język paneli zależy od zapisanego języka FM: polski daje PL, pozostałe EN. Język UI launchera jest niezależny. Nie dodano RulesUI ani TeamTalk.

Dowody offline i kandydat R11 są w `data/research/NOCHE_EXT_20261113`. R11 jest osobnym katalogiem `J:/FM08dev/Launcher_0.1.3_R11`; konfigurację skopiowano bitowo z backupem/readback. Nie uruchomiono R11, nie restartowano ani nie podmieniono R10.

Instalacja LIVE wymaga wcześniejszego zamknięcia FM przez użytkownika i przeglądu root. Agent wykonuje ją przez produkcyjne `InstallExt`, z ponowną weryfikacją EXE oraz tym samym `WithStoppedGame`; nie należy kopiować paneli ręcznie ani obchodzić guardu. Natywny test wyglądu NocheExt pozostaje do wykonania po instalacji. Aktualnie diagnostyczne okno błędu FM musi pozostać otwarte.
