# Kontynuacja: generowanie graczy, PA i cechy — 16 XI 2026

Czytaj REPORT.md oraz VERIFICATION.json. Aktualny launcher nadal R23, bez zmian.
Nie wdrożono hooka nowych graczy ani nie otwarto procesu gry. Tylko analiza
statyczna R5, oryginalne bajty zgodnego EXE i istniejący model native_budget.py.

Nowe: gałąź PA bez klubu/country+11B==0 ma skalowanie szans przez bieżącą
populację kraju: floor(n/450), pole +F7 i clamp1..10. To nie licznik wysokiegoPA
ani twarda kwota talentów. W sprawdzonych ścieżkach nie znaleziono globalnego
limitu ilości PA180+, ale brak pełnego dowodu dla reszty silnika. F48DC0 z
finalizatora to porównanie dat, nie licznik populacji. Ograniczenia2CA/3CA tylko
w warunkowej naprawie PA; poprawne PA>=CA omija je. Dokładne warunki w raporcie.

Model propozycji: Genie wybiera premiowane cechy, native Q liczy koszt;
losowe1–2 cechy +5/+10 raw, ograniczeni dawcy, odrzucenie CAŁEJ zmiany przy
braku bilansu.352 syntetyczne przypadki,231 accepted/121 unchanged. To nie
ustalona polityka ani wynik testu gry. Parametry/tolerancja wciąż propozycją.
Nie dodawać powtórnie premii przy wczytaniu/treningu. Osobne rozróżnienie
zwykłego naboru, startowego uzupełnienia, presetów/donora i wirtualnych graczy.

Następny etap: ograniczony obserwator nowej pełnej osoby, bez zmiany danych,
potem test bilansu po następnym natywnym przeliczeniu. Punkty statyczne:
88236C przed CA (ECX=PLAYER);882523 po finalizacji/treningu (ESI=PLAYER,
dalej konwersja do PERSON). ABI hooka, zachowanie rejestrów/FPU, once-only oraz
save/load nie są jeszcze potwierdzone. Nie stawiać globalnego hooka na CB1350.

REA list_documents nie zwróciło wyniku; przerwano oczekujący caller, bez
otwierania targetu/zmian konfiguracji/reanalizy. Kontynuacja przez eksport R5.
Wszystkie dowody i braki zachowane. Nie wymagać od użytkownika ponownego
odczytu macierzy B — jest już odzyskana. Nie usuwać żadnych plików.
