"""Document the confirmed commentary and native dissent paths, with unresolved causes."""
import json,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REPO=ROOT/'FM08-Database-Tools';OUT=ROOT/'FmLauncher/data/research/MATCH_CONTROVERSIES_20261107'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
r=json.loads((OUT/'report.json').read_text(encoding='utf-8'))
assert r['status']=='static_commentary_and_dissent_paths_audited' and len(r['checks'])==28
for rel,digest in r['input_hashes'].items():assert sha(ROOT/rel)==digest
p=REPO/'docs/MATCH_CONTROVERSIES.md';assert not p.exists()
p.write_text('''# Kontrowersje bramkowe i protesty — FM08 8.0.2

Analiza statyczna2026-11-07, bez uruchamiania i modyfikacji gry.
EXE SHA256:157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d.
Dowody: `FmLauncher/data/research/MATCH_CONTROVERSIES_20261107`.

## Co wyjaśniają dokładne komunikaty

Teksty komentarza znaleziono w `data/match events/events.cfg` (UTF-16),
nie w tłumaczeniach nazw ligi ani jako dosłowne polskie teksty w EXE.
Numery poniżej są identyfikatorami komentarza, nie kodami akcji piłkarza.

| ID | Symbol zdarzenia | Znaczenie tekstu |
|---:|---|---|
| 409 | EVENT_TEAM_ARGUES_WITH_REFEREE | Zespół otacza sędziego/protestuje |
| 429 | EVENT_GOAL_DISALLOWED | Bramka nie zostanie uznana; gwizdek/chorągiewka |
| 733 | EVENT_PLAYERS_GATHER_ROUND_REFEREE | Zawodnicy zbierają się przy arbitrze, żądają zmiany decyzji |
| 894 | EVENT_DISSENT_TEAM_WANT_GOAL_TO_STAND | Niedowierzanie zespołu po anulowaniu bramki; domaganie się jej uznania |
| 896 | EVENT_DISSENT_TEAM_WANT_GOAL_RULED_OUT_FOUL | Żądanie anulowania gola z powodu faulu |
| 898 | EVENT_DISSENT_TEAM_WANT_GOAL_RULED_OUT_OFFSIDE | Żądanie anulowania gola ze spalonego |
| 900 | EVENT_DISSENT_TEAM_WANT_GOAL_RULED_OUT_HANDBALL | Żądanie anulowania gola po ręce |
| 916 | EVENT_CONTROVERSY_LOOKED_LIKE_A_FAIR_GOAL | Komentarz sugeruje, że anulowany gol był prawidłowy |
| 919 | EVENT_CONTROVERSY_DODGY_GOAL | Komentarz kwestionuje prawidłowość uznanego gola |
| 957 | EVENT_CONTROVERSY_BALL_WENT_OUT_BEFORE_GOAL | Sprzeciw: piłka miała opuścić boisko przed golem |

Dokładny cytat o piłkarzach niewierzących własnym oczom należy do894.
To ich sprzeciw wobec anulowania, a nie samodzielny dowód błędu arbitra.
Istnieją również warianty protestu pojedynczego zawodnika893/895/897/899.
W EXE odnaleziono tekst relacji medialnej, w którym późniejsze powtórki
potwierdzają prawidłowość decyzji mimo wcześniejszego sprzeciwu.

Oddzielne numery DISSENT i CONTROVERSY potwierdzają rozdzielenie opisów
protestu oraz oceny kontrowersji w komentarzu. Nie oznacza to jeszcze pełnego
odtworzenia natywnej ścieżki, która wybiera916 zamiast919.

## Potwierdzone ścieżki kodu reakcji

- `0x00B2C7A5..0x00B2C827`: switch debugowych nazw akcji. Odczyt tabel
  skoku dowodzi, że **0x76D = ME_DISSENT**, a nie numer894 z events.cfg.
- Sąsiednie rozpoznane akcje:0x76C kopnięcie piłki,0x76E przeklinanie na
  sędziego,0x76F na asystenta,0x770 popchnięcie sędziego,0x771 uderzenie.
- `0x00B6AFD0`: funkcja indywidualnej reakcji, z warunkami wejścia i kontekstu.
  W trzech gałęziach przygotowuje0x76D i przez `0x00B6B4BC` wywołuje
  dyspozytor `0x00B64AE0`. Nie każda decyzja przechodzi wszystkie warunki.
- `0x00B63B10`: wybór reakcji, uwzględniający stan wykonania i modyfikatory,
  z wywołaniami generatora losowego. Silnik może wybrać brak reakcji,
  protest albo ostrzejsze zachowanie. Nie wyliczono kompletnej szansy procentowej.
- `0x00B5BB80`: przechodzi po grupie zawodników i warunkowo wywołuje reakcje.
  Fragment od0x00B5BCDF liczy różnice współrzędnych, odległość i używa losowań.
  Nie przypisano jeszcze wszystkim wskaźnikom znaczenia aktora incydentu.
  Nie twierdzimy, że chodzi zawsze o odległość od sędziego.
- `0x00B48B90`: używa generatora meczu pod match+0xC4C przez `0x00F56800`.
- `0x00B06BA0` i constructor `0x00B08400`: obsługa konfiguracji komentarza;
  identyfikację wspierają dosłowne diagnostyki MATCH_EVENT_HANDLER w EXE.

## Stan reakcji i atrybuty — granica rozpoznania

Wybór korzysta z dynamicznego int32 na obiekcie zawodnika **+0x108C**.
Funkcja `0x00B30450` aktualizuje ten stan i ogranicza go z góry do100.
Interpretacja jako natężenie pobudzenia/złości jest wnioskiem z użycia;
nie jest odzyskaną nazwą symbolu ani polem osobowości w bazie.

Parametr efektywny na+0x1118 pochodzi m.in. z+0x444 w `0x00B62C70`;
może być obliczany przez ważenie dwóch wartości. Jego tożsamości jako
Temperament, Sportsmanship, Controversy czy innej cechy jeszcze nie udowodniono.
Nie wolno przeliczyć tych adresów bezpośrednio na kolumny CSV importera.

Dla parametru T funkcja aktualizacji zawiera dolne ograniczenie stanu:
`10*(10-T)` przy T<5, a `65-3*T` przy T>=5. Nie jest to kompletny wzór
prawdopodobieństwa protestu: są dalsze warunki i ograniczenia kontekstowe.
W wariantach wyboru reakcji kategorii4..7 są dodatkowe bramki stanu>45,
>60,>75,>95. Nazwane akcje eskalacyjne są potwierdzone przez switch;
nie należy traktować tych progów jako wartości cechy z bazy1..20.

## Czego ta analiza nie potwierdza

Nie rozpoznano dokładnego losowania błędu sędziego ani pełnego przepływu
uznania/anulowania bramki. Powody sprzeciwu (faul, spalony, ręka, aut)
wynikają z kategorii komentarza; ich szczegółowe warunki geometryczne,
umiejętności arbitra i prawdopodobieństwa wymagają dalszego prześledzenia.
Nie zmierzono częstości w żywym meczu ani wpływu zmiany konkretnej cechy.
Nie udowodniono bezpośredniego przejścia ME_DISSENT→komunikat894 dla każdej ścieżki.

Ważna pułapka: getter0x007CEC30 zwraca409, ale RTTI wskazuje
MEDIA_PLAYER_MORALE_NEWS. To obiekt wiadomości, nie dowód wywołania komentarza409.
Sama zgodność małej liczby nie potwierdza mapowania zdarzenia.

Raport zawiera34 kategorie komentarza, nazwy akcji,28 kontroli kotwic,
hashe wejść i deasemblację wskazanych funkcji. To audyt statyczny,
nie test wykonania meczu i nie patch. EXE, events.cfg, LTC oraz bazy są nietknięte.
''',encoding='utf-8')
p=REPO/'fm08_compendium.md';t=p.read_text(encoding='utf-8-sig');t+='''

### Kontrowersje bramkowe i protesty — rozpoznanie2026-11-07

Komunikat o piłkarzach niewierzących własnym oczom występuje w events.cfg
w zdarzeniu894, żądaniu uznania anulowanej bramki.409 i733 opisują grupowe
protesty.896/898/900/957 obejmują żądania anulowania gola z powodu faulu,
spalonego, ręki lub piłki poza boiskiem;916/919 są osobną oceną kontrowersji.
W silniku nazwany switch rozpoznaje ME_DISSENT jako0x76D. Funkcje0xB6AFD0,
0xB63B10 i0xB5BB80 wiążą reakcje z warunkami kontekstu, stanem zawodnika
oraz RNG; kod grupy zawiera obliczenia odległości. Nie rozpoznano jeszcze
przypisania stanu+0x108C/parametru+0x1118 do cech bazy ani szansy błędu arbitra.
Szczegóły i granice dowodów: [MATCH_CONTROVERSIES.md](docs/MATCH_CONTROVERSIES.md).
''';p.write_text(t,encoding='utf-8')
p=REPO/'README.md';t=p.read_text(encoding='utf-8-sig');t+='\nAudyt protestów i komentarzy kontrowersyjnych bramek: [MATCH_CONTROVERSIES.md](docs/MATCH_CONTROVERSIES.md).\n';p.write_text(t,encoding='utf-8')
archive=OUT/'source-snapshot';archive.mkdir(exist_ok=False);files=['scratch/analyze_match_controversies_20261107.py','scratch/finalize_match_controversies_20261107.py','docs/MATCH_CONTROVERSIES.md','fm08_compendium.md','README.md'];entries=[]
for rel in files:
    dest=archive/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(REPO/rel,dest);entries.append(dict(path=rel,SHA256=sha(dest)))
save(archive/'manifest.json',dict(source_only=True,files=entries))
save(OUT/'result.json',dict(status=r['status'],native_dissent_action='0x76D',native_reaction_rng_confirmed=True,database_attribute_mapping='unresolved',goal_award_error_probability='unresolved',checks_passed=28,source_files_archived=len(entries),inputs_unchanged=True,game_executed=False,game_patched=False))
print(json.dumps(dict(status=r['status'],source_files_archived=len(entries),checks_passed=28,inputs_unchanged=True)))
