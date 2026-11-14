"""Persist static findings and a target rules model; never writes game resources/databases/projects."""
import csv,hashlib,itertools,json,pathlib,re,shutil,struct
from datetime import datetime
import capstone,pefile
ROOT=pathlib.Path('J:/FM08dev'); R=ROOT/'FmLauncher/data/research/GHIDRA_ENGINE_20261107_R5'; OUT=ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_R6_20261107'; REPO=ROOT/'FM08-Database-Tools'
EXPECTED='157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d'
URL='https://pzpn.pl/public/system/files/site_content/635/7380-Regulamin%201.%20Ligi%202.%20Ligi%20i%203.%20Ligi%20na%20sezon%202026-2027.pdf'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):
 with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
assert not (OUT/'report.json').exists(), 'refuse overwrite final research'
raw=(ROOT/'fm.exe').read_bytes();assert hashlib.sha256(raw).hexdigest()==EXPECTED
assert json.loads((OUT/'targeted-audit.json').read_text())['project_unchanged']
pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
def rd(a,n):return raw[pe.get_offset_from_rva(a-base):][:n]
def u32(a):return struct.unpack('<I',rd(a,4))[0]
def cstr(a):return rd(a,150).split(b'\0')[0].decode('ascii')
def table(a,n):
 out={}
 for k in range(n):
  p,v=struct.unpack('<II',rd(a+8*k,8))
  if not p:break
  out[cstr(p)]=v
 return out
flags=table(0x1602d00,15); fates=table(0x1602cc0,5)
assert flags['fixed_draw']==4 and flags['higher_seeded_team_at_home']==512
assert fates['set_league_fate']==0x34
assert u32(0x165a0ec+0x160)==0xf08c60
instructions={i.address:(i.mnemonic,i.op_str) for i in md.disasm(rd(0xd68cb0,0x110),0xd68cb0)}
assert instructions[0xd68d01]==('call','0xd642a0')
assert instructions[0xd68d08]==('jne','0xd68d4e')
assert instructions[0xd68d49]==('call','eax')
regions=[('native_or_data_competitions',0xd68cb0,0xd68d56),('division_level_override',0xd65340,0xd6548f),('generic_comp_factory',0xd642a0,0xd64405),('English_playoffs',0xf08c60,0xf094ad)]
asm=[]
for name,start,end in regions:
 asm.append('\n'+name+' '+hex(start)+'..'+hex(end))
 asm.extend(f'{i.address:08X} {i.mnemonic:9} {i.op_str}' for i in md.disasm(rd(start,end-start),start))
(OUT/'focused-disassembly.txt').write_text('\n'.join(asm)+'\n',encoding='utf-8')
# A mathematical schedule model, not the game's fixture generator or a game test.
clubs=list(range(1,19));ring=clubs[:];first=[]
for turn in range(17):
 pairs=[(ring[i],ring[-1-i]) for i in range(9)]
 if turn%2:pairs=[(b,a) for a,b in pairs]
 first.append(pairs);ring=[ring[0],ring[-1],*ring[1:-1]]
rounds=first+[[(b,a) for a,b in pairs] for pairs in first]
assert len(rounds)==34 and all(len(set(sum(([a,b] for a,b in pairs),[])))==18 for pairs in rounds)
fixtures=[p for pairs in rounds for p in pairs]
assert len(fixtures)==len(set(fixtures))==306
assert set(fixtures)==set(itertools.permutations(clubs,2))
counts={x:(sum(a==x for a,b in fixtures),sum(b==x for a,b in fixtures)) for x in clubs}
assert set(counts.values())=={(17,17)}
balances=[]
for wins in itertools.product([False,True],repeat=2):
 k=sum(wins);after=18-3-(4+k)+3+(4+k)
 assert after==18
 balances.append(dict(lower_teams_win_playoff_pairs=list(wins),relegated_from_level3=4+k,promoted_from_level4=4+k,from_level2=3,to_level2=3,next_season_teams=after))
save(OUT/'format-model-check.json',dict(status='mathematical_model_verified_not_game_test',rounds=34,total_matches=306,home_per_club=17,away_per_club=17,all_directed_pairs_once=True,season_balance_cases=balances,old_four_down_from_level2_would_produce=19))
save(OUT/'target-rules.json',{
 'status':'design_not_loadable_game_configuration','season_reference':'2026/27','level_zero_based':2,
 'competition_uid':None,'uid_policy':'new_record_keep_129560_as_lower_pool','parent_uid':129559,'legacy_lower_pool_uid':129560,
 'league':{'teams':18,'cycles':2,'matchweeks':34,'matches':306,'points':{'win':3,'draw':1,'loss':0},'observed_settings_offsets':{'teams':'0x0B','cycles':'0x0A','points_win':'0x18','points_draw':'0x1B','points_loss':'0x1C'},'calendar':'not_yet_mapped_to_34_real_matchweeks'},
 'promotion':{'direct_places':[1,2],'playoff_places':[3,4,5,6],'semifinals':[[3,6],[4,5]],'semifinal_legs':1,'final_legs':1,'home_rule':'higher_final_regular_season_position','total_promoted':3,'requires_seed_mapping':True},
 'relegation':{'direct_places':[15,16,17,18],'playoff_places':[13,14],'lower_division_groups':4,'direct_incoming':'four_group_winners','preliminary':'four_group_runners_up_two_single_matches_drawn_pairs_and_hosts','final':'two_preliminary_winners_vs_places_13_14','final_legs':2,'first_leg_home':'lower_division_team','total_relegated_range':[4,6],'requires_lower_group_results':True},
 'upper_boundary':{'relegated_from_uid129559':3,'old_native_relegation_count':4,'change_required':True},
 'youth':{'minimum_on_pitch':2,'citizenship':'Polish','birth_year_minimum':'season_end_year - 21','reference_threshold_2026_27':2006,'fm08_shifted_threshold_2007_08':1987,'shift_context':'V25 dates shifted back 19 years; not a change to base802','reduced_team_exception':True,'injured_youth_goalkeeper_exception':True,'must_cover':['initial_lineup','human_substitutions','AI_selection','AI_substitutions','injuries','dismissals','save_load','season_rollover'],'existing_first11_age_rule':'0x1D','existing_domestic_U21_squad_rule':'0x14','existing_domestic_first11_rule':'0x5E','exact_combined_predicate_implemented':False},
 'regulation_source':URL,'game_verified':False})
source_functions=['d63120','d642a0','d65340','d655f0','d664c0','d66b00','d68cb0','d69200','d805b0','d7ce90','d7cfb0','d70cf0','d9e540','d98ee0','d6bd00','d6c020','dd3640','e8ddc0','e8df90','e8e950','e8e320','e8ee60','e8ed20','dc7160','dc71c0','e17540','e17790','e19a70','e15d70','e1a2b0','e16170','e138b0','e10d80','e10ec0','e495d0','c94320','c961d0','c93f30','cbf920','c8c4e0','a60b70','c8dca0','73ebc0','6cd420','c95670','c911e0','6e30a0','c95490']
evidence=OUT/'evidence/functions';evidence.mkdir(parents=True)
manifest=[]
for address in source_functions:
 src=R/f'decompiled/functions/ram_{address}.c';assert src.exists(),str(src)
 dst=evidence/src.name;shutil.copy2(src,dst);manifest.append(dict(path=str(dst.relative_to(OUT)),source=str(src.relative_to(ROOT)),sha256=sha(dst)))
for address in ['e8f660','e90740','dd2010']:
 src=R/f'supplemental/functions/ram_{address}.c';dst=evidence/src.name;shutil.copy2(src,dst);manifest.append(dict(path=str(dst.relative_to(OUT)),source=str(src.relative_to(ROOT)),sha256=sha(dst)))
save(OUT/'evidence-manifest.json',dict(source_sha256=EXPECTED,files=manifest,method='existing_Ghidra_pseudocode_plus_PE_instruction_and_RTTI_checks'))
report={
 'status':'static_analysis_completed_runtime_unverified','created_at':datetime.now().astimezone().isoformat(),
 'source_sha256':EXPECTED,'previous_research':'POLAND_THIRD_TIER_20261107','ghidra':'GHIDRA_ENGINE_20261107_R5',
 'persistent_Ghidra_function_count':91406,'R5_pseudocode_count':91123,'R6_extra_reference_pseudocode':1,
 'extra_function_created_only_in_memory':True,'persistent_project_unchanged':True,
 'observations':[
  {'id':'PL3-R6-01','kind':'static_observation','finding':'national_resource_loader_accepts_nation_and_competition_headers','functions':['00D9E540']},
  {'id':'PL3-R6-02','kind':'static_observation','finding':'division_levels_resource_replaces_existing_settings_collection','functions':['00D66B00','00D65340'],'keys':['division_levels','competition','default_division_level']},
  {'id':'PL3-R6-03','kind':'static_observation','finding':'data_defined_competition_success_skips_native_setup_comps','functions':['00D68CB0','00D642A0'],'confirmed_instructions':['00D68D01 call D642A0','00D68D08 jne D68D4E','00D68D49 call eax']},
  {'id':'PL3-R6-04','kind':'static_observation','finding':'generic_ACTUAL_COMP_and_league_cup_stage_factories_exist','functions':['00D805B0','00D70CF0','00D7CE90','00D7CFB0','00DD2010']},
  {'id':'PL3-R6-05','kind':'static_observation','finding':'four_team_two_round_playoffs_and_existing_action_serialization','functions':['00F08C60','00E19A70','00E16170','00E10D80','00E10EC0','00E495D0']},
  {'id':'PL3-R6-06','kind':'static_observation','finding':'first11_under21_rule_and_match_substitution_validation_exist','functions':['00C94320','00C961D0','00CBF920','006CD420','0073EBC0','00C95670']}
 ],
 'design_inferences':[
  'resource_defined_third_league_is_a_real_candidate_not_yet_a_working_XML_patch',
  'hybrid_post_native_setup_append_can_preserve_existing_Polish_cups_but_requires_code_hook',
  'prefer_new_competition_record_keep_lower_pool_UID129560',
  'combine_age_and_citizenship_in_one_scoped_rule_covering_AI_and_match_state'
 ],
 'draw_flags_verified':{k:flags[k] for k in ['fixed_draw','lower_seeded_team_at_home','higher_seeded_team_at_home','seeded_draw']},
 'candidate_single_leg_draw_flags':0x204,'candidate_seed_mapping_verified':False,
 'fate_type_set_league_fate':fates['set_league_fate'],
 'checklist':{'original_lower_pool_role':'answered','league_format_settings':'answered_static','country_override_and_generic_factory':'answered_static_runtime_pending','four_team_playoff_mechanism':'answered_static','table_position_selection_and_final_host':'partial','exact_season_birthyear_and_citizenship_predicate':'partial','injured_youth_GK_exception':'unresolved','new_competition_DB_creation_and_UID':'design_only','new_level_UI_and_34_week_calendar':'runtime_pending','new_league_save_load_and_second_season':'runtime_pending'},
 'not_done':['game_patch','database_write','loadable_resource_package','game_pilot','multi_season_simulation'],
 'inputs_modified':False,'game_executed':False,'regulation_source':URL}
save(OUT/'report.json',report)
doc='''# Polska: trzeci grywalny poziom — analiza R6

Stan: analiza statyczna zakończona; prototyp i pilot gry jeszcze nie istnieją. Kontynuacja wcześniejszego rozpoznania, bez ponownej autoanalizy EXE. Podstawa eksperymentów: czysta baza 8.0.2. V25 i oryginalny EXE pozostają nietknięte.

## Wniosek

Istnieje konkretna droga do ligi 18 zespołów z barażami, oparta na wspólnym silniku FM08. Nowe odczyty pokazują, że definicje krajowe mogą zastępować listę poziomów i tworzyć ogólne ACTUAL_COMP. Nie udowodniono jeszcze uruchomienia nowego poziomu samym XML. Wymóg polskich młodzieżowców wymaga dopracowania kodu wspólnego predykatu oraz obsługi AI i zmian podczas meczu.

Zalecany model danych: osobny rekord nowej II ligi, a UID129560 zachować jako zaplecze. UID nowej ligi nie został jeszcze przydzielony. Dotychczasowy UID129560 obejmuje 118 klubów i pełni rolę puli, nie gotowych rozgrywek. Użycie go jako ligi wymagałoby przeniesienia zaplecza i istniejących odwołań; nie daje darmowego skrótu.

## Docelowy format i zależności

Wymagania użytkownika są modelem docelowym. [Regulamin PZPN 2026/27](REGULATION_URL), art.1,5,9–11, potwierdza ten format. Dodatkowo: półfinały 3–6 i 4–5 oraz finał są pojedyncze, wyżej sklasyfikowany klub jest gospodarzem. Baraże utrzymania poprzedzają dwa mecze czterech wicemistrzów grup III ligi; potem zwycięzcy grają dwumecze z miejscami13/14, rewanż u klubu II ligi. Młodzieżowiec wymaga polskiego obywatelstwa i rocznika co najmniej2006; regulamin przewiduje wyjątki osłabienia i urazu młodzieżowego bramkarza.

| Element | Projekt |
|---|---|
| Liga | 18 klubów, 2 cykle, 34 kolejki, 306 spotkań; 17 dom/17 wyjazd na klub |
| Punkty | 3/1/0 |
| Awans | 1–2 bezpośrednio; 3–6 o trzeci awans |
| Spadek | 15–18 bezpośrednio; 13–14 w barażach; łącznie4–6 |
| Uzupełnienie od dołu | Czterej zwycięzcy grup i0–2 zwycięzców dwumeczów |
| Granica z I ligą | Trzy zespoły w każdą stronę |
| Młodzieżowcy | Jeden wspólny warunek wieku i obywatelstwa; minimum2 na boisku |

To ostatnie połączenie lig wymaga zmiany obecnej POL_SECOND: historyczny format FM08 kieruje cztery zespoły do puli129560. Przy trzech awansach nowej ligi i pozostawieniu czterech spadków z I ligi liczebność wzrosłaby do19. Dla k przegranych baraży utrzymania: 18−3−(4+k)+3+(4+k)=18. W `format-model-check.json` sprawdzono wszystkie cztery kombinacje wyników dwóch par i model kołowy306 meczów. To kontrola matematyczna projektu, nie test terminarza FM08.

Pełny model wymaga uporządkowanego zaplecza czterech grup III ligi: ich mistrzów, wicemistrzów i wyników. Losowanie dwóch klubów z puli129560 nie realizuje tych zasad. Grupy mogą pozostać niedostępne do prowadzenia przez gracza, ale muszą dostarczać wiarygodny stan sezonu; sposób ich symulacji pozostaje do potwierdzenia. Samo uruchomienie trzeciego poziomu nie wymusza pełnej modernizacji Ekstraklasy, natomiast granica I/II ligi musi być spójna.

## Co nowego wynika z dekompilacji

Adresy dotyczą wyłącznie EXE SHA256157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d. Numery PL3-R6 odsyłają do lokalnego `report.json`; to dowody statyczne, nie obserwacje uruchomionej gry.

1. **PL3-R6-01/02: zasób krajowy może zmienić listę poziomów.** `D9E540` ładuje zasoby `comps`, rozróżnia nagłówki `competition` i `nation`. `D69200` pobiera krajowe `_get_settings`, a następnie `D66B00` uruchamia parser `D65340`. Klucz `division_levels` (`dvlv`) czyści kolekcję settings+0x30 i buduje ją z listy rekordów `competition`; `default_division_level` (`dfdl`) ustawia wartość domyślną. To mocniejszy dowód niż samo istnienie nazwy klucza. Lista zastępuje poprzednią, więc powinna zachować także istniejące dwa poziomy.
2. **PL3-R6-03: definicje rozgrywek mogą ominąć standardową fabrykę kraju.** `D68CB0` próbuje `D642A0`, a po sukcesie przeskakuje wywołanie `_setup_comps` (instrukcje D68D01/D68D08/D68D49 sprawdzone w assembly). `D642A0` czyta listę `competitions` (`cmps`), opcjonalnie wywołuje `_create_comp`, a w razie braku tworzy `ACTUAL_COMP` przez `D805B0` (0x240B). W eksportach Polski nie ma `pol_create_comp`. Dodanie tylko jednego rekordu do tej listy może zatem zastąpić tworzenie wszystkich pięciu dotychczasowych polskich obiektów, zamiast dopisać szósty. Gałąź zależy też od porównania wersji ustawień.
3. **PL3-R6-04: etapy ligowe są ogólne.** Podstawowy ACTUAL_COMP ma vtable0x015F6D4C; metoda+0x160 to `D70CF0`, która wybiera typ etapu z listy `stages`. `D7CE90`/`D7CFB0` obsługują ich inicjalizację i aktualizację. Parser ligi `DD2010`: `number_teams`→+0x0B, `number_rounds`→+0x0A, `pwin/pdrw/pdef`→+0x18/+0x1B/+0x1C. Dla naszej ligi ustawić18 i2, nie34 w polu liczby cykli. Daty i wyjątki kalendarza są oddzielnym zadaniem.
4. **PL3-R6-05: baraże czterech zespołów mają gotowy wzorzec.** ENG_FIRST: konstruktorF02730, vtable0x0165A0EC, fabryka+0x160→F08C60. Dodatkowo wyeksportowano tę jedną funkcję z istniejącego projektu w trybie readOnly/noanalysis; zmiany definicji funkcji zostały odrzucone przy zamknięciu projektu. Angielski etap1 tworzy CUP_SETTINGS dla4 klubów i rundy4→2→1. Półfinały są dwumeczowe, finał pojedynczy; to wzorzec konstrukcji, nie gotowy polski regulamin. Nasze półfinały trzeba przestawić na pojedynczy mecz.
5. **Gospodarz i przejścia.** E15D70 czyta flagi rundy `drrl` do+0x20. Tablica0x01602D00 potwierdza fixed_draw=0x4, higher_seeded_team_at_home=0x200. Kandydat0x204 wymaga dowodu, że seed jest końcową pozycją ligową, także w finale. Samo nazwanie flagi nie ustawia par3–6/4–5. E1A2B0/E19A70 budują rundy; `nrdw/nrdl` określają dalsze drogi zwycięzcy i przegranego. E16170/E138B0 tworzą akcję set_league_fate (typ0x34).
6. **Zapis istniejących typów.** CUP_SETTINGS vtable0x0160CDD4 ma writerE10D80 i readerE10EC0; reader rekonstruuje akcje fabrykąE495D0, w tym promotion/relegation/set_league_fate. Jest istniejąca ścieżka serializacji etapów. Zgodność całej nowej ligi, stanu osłabień, zapisu i następnego sezonu nadal wymaga pilota.

Nie należy traktować argumentów DC7160/DC71C0 jako gotowej instrukcji bezpośredniego awansu/spadku. Angielski wzorzec przekazuje3 do akcji awansu, choć trzecie miejsce rozstrzygają baraże. Trzeba skoordynować pozycje tabeli, uczestników etapu i jego końcowe fate, aby nie liczyć jednego zespołu dwukrotnie.

## Dwie drogi wykonania

**Najpierw zbadać wariant definicji danych.** Osobny pakiet zasobów krajowych i rozgrywek mógłby opisać trzy poziomy, etapy i zaplecze przez wspólny silnik. Jest realna ścieżka odczytu, ale nie ma jeszcze poprawnego pakietu ani dowodu, że wystarczy sam XML. Pełna lista `competitions` powinna zachować pięć istniejących polskich obiektów i ich zachowanie albo świadomie odtworzyć je ogólnie. Trzeba sprawdzić wersje, hierarchię danych, dostępność zasobu dla nowego rekordu i przejścia sezonowe. `comps.efa` jest archiwum z indeksem; samo doklejenie tekstu do pliku po XOR nie jest wykonawcą.

**Wariant hybrydowy:** pozostawić oryginalne polskie fabryki, a po ich wykonaniu dopisać obiekt nowej ligi z ogólnymi regułami; rozszerzyć ustawienia i kontrolę liczebności oraz przepiąć granicę I/II ligi. Zachowuje więcej zachowania istniejących lig i pucharów, ale wymaga precyzyjnego hooka silnika, właściciela obiektu i zachowania ich przy wczytywaniu. Nie kopiować POL_SECOND wraz z vtable i UID; zachowałoby to jej hardkodowane selekcje, cele i kalendarz.

W obu wariantach baza potrzebuje rekordu rozgrywek, nazw EN/PL, poziomu i kontrolowanego przypisania18 klubów. Zwykły importer kadr nie tworzy nowej piramidy. Nowy UID, obsada i podział zaplecza pozostają do przygotowania. Nie wybierano przypadkowych18 klubów i nie zaimportowano współczesnych kadr.

## Młodzieżowcy: dostępny fundament i brakujące elementy

PL3-R6-06: C94320/C961D0 rozpoznają typ0x1D jako minimum U21 w pierwszej11. C93F30/CBF920 ograniczają go do indeksów0–10. Typ0x14 łączy krajowość i wiek w kadrze meczowej, a0x5E dotyczy krajowych w pierwszej11. Żaden z tych odczytów nie dowodzi gotowego wymogu PZPN. Dwie osobne reguły „2 młodych” i „2 Polaków” dopuszczą dwóch młodych cudzoziemców oraz dwóch starszych Polaków. Potrzebny jest jeden wspólny predykat.

73EBC0, przy powrocie z taktyki do meczu, wywołuje6CD420 i zatrzymuje dalszą ścieżkę przyfalse. 6CD420 buduje liczniki ze stanu GAME_MATCH_PLAYER+0x1200; C95670 uwzględnia brakujących graczy przy porównaniu minimum. Istnieje więc fundament kontroli zmian i gry w osłabieniu. Nie znaleziono potwierdzenia wyjątku młodego kontuzjowanegoGK zastąpionego starszym przy11 osobach. Nie wolno utożsamiać samego braku zawodnika z pełną obsługą tego wyjątku.

Próg rocznika powinien zależeć od roku zakończenia sezonu, nie od dzisiejszej daty ani urodzin w dniu meczu. Przy przesunięciu dat V25 o−19lat równoważny próg dla sezonu2007/08 to1987. Nie wpisywać2006 do gry działającej w2007roku. Trzeba też potwierdzić drugie obywatelstwa: obecne pojęcie „domestic” w C8DCA0 ma wyjątki krajowe i nie jest automatycznie prawnym odpowiednikiem polskiego obywatelstwa.

Rozszerzenie ograniczyć do nowego UID i tej polityki, bez globalnej zmiany U21 w innych krajach. C911E0/6E30A0/C95490 pokazują osobne ścieżki doboru i oceny AI; sama blokada przycisku użytkownika nie wystarcza. WyjątekGK i osłabienia muszą zachowywać się prawidłowo także po zapisie/wczytaniu.

## Kolejność prototypu i granice tej analizy

1. Na nowej kopii8.0.2 przygotować rekord i18 uczestników; zachować pulę129560. Sprawdzić podstawowy wariant danych: ustawienia trzech poziomów i utworzenie aktywnego obiektu bez usunięcia lig/pucharów. Jeśli wymaga odtworzenia całego kraju, wybrać wariant hybrydowy.
2. Doprowadzić do wyboru ligi i klubu,306 spotkań/34kolejek, poprawnego kalendarza, zapisu i wczytania nowej kariery. To pierwszy wąski pilot, bez deklarowania gotowej zgodności PZPN.
3. Dołożyć skoordynowane awanse i spadki, baraże oraz stan czterech grup zaplecza. Sprawdzić przypadki0/1/2 spadków barażowych i liczebność obu lig w następnym sezonie.
4. Dodać wspólną regułę młodzieżową oraz kontrolę składu i zmian gracza/AI, wyjątki osłabienia/GK i zmianę rocznika sezonowego.

Jeszcze niepotwierdzone: pełny konsument UI wyboru poziomu, przydział i zapis nowego rekordu bazy, selekcja pozycji i seed w barażach, kalendarz, dokładne obywatelstwo/rocznik w predykacie, wyjątekGK i stabilność następnego sezonu. Nie uruchomiono gry ani nie utworzono wdrożonej ligi.

## Materiały i kontrola

Katalog: `FmLauncher/data/research/POLAND_THIRD_TIER_R6_20261107`.

- `WZNOWIENIE.md` i `checkpoint.json`: skrócony stan do dalszej pracy.
- `report.json`: obserwacje, wnioski i osobna lista niewiadomych.
- `target-rules.json`: projekt reguł, **nie gotowy plik ładowany przez grę**.
- `format-model-check.json`: matematyczny format i bilans wymiany zespołów.
- `focused-disassembly.txt`, `evidence-manifest.json`, `evidence/functions/`: lokalne dowody i hashe pseudokodu.
- `supplemental/functions/ram_f08c60.c`, `targeted-audit.json`: dodatkowy wzorzec angielski i kontrola niezmienionego projektu.

Bazowe R5 pozostaje przy91 123 plikachC i91 406 funkcjach w zapisanym projekcie. Dodatkowy plik odniesienia R6 nie zmienił tego projektu. Pseudokod ma niepełne typy/ABI; np. unaff_retaddr nie jest dowodem oryginalnej sygnatury. Decyzje implementacyjne opierać na przepływie, assembly i danych, a zgodność funkcjonalną dopiero na pilocie.
'''.replace('REGULATION_URL',URL)
docpath=REPO/'docs/POLAND_THIRD_TIER_R6.md';assert not docpath.exists();docpath.write_text(doc,encoding='utf-8')
(OUT/'README.md').write_text(doc,encoding='utf-8')
# Preserve exact earlier document bytes and CRLF while adding the current pointer.
old=REPO/'docs/POLAND_THIRD_TIER.md';b=old.read_bytes();old.write_bytes(('[Aktualizacja R6: uzgodniony format i analiza po dekompilacji](POLAND_THIRD_TIER_R6.md).\r\n\r\n').encode('utf-8')+b)
entry=REPO/'IMPORTER_AKTUALNY_SCHEMAT_I_ZASADY.md';b=entry.read_bytes();entry.write_bytes(b+('''\r\n\r\n## 22. Polska: trzeci poziom, analiza R6 po dekompilacji\r\n\r\nUżytkownik określił format docelowy: 18 klubów, 34 kolejki, awans2+1,\r\nspadek4–6 i minimum2 polskich młodzieżowców na boisku.\r\n[Analiza R6 i konkretne funkcje silnika](docs/POLAND_THIRD_TIER_R6.md)\r\npokazują krajowe definicje danych, ogólne ligi i baraże oraz fundament\r\nkontroli zmian. Zasoby mogą zastąpić całą fabrykę kraju; nie dopisywać\r\njednej ligi bez zachowania pozostałych obiektów. Granica I/II ligi\r\nwymaga3 spadków zamiast historycznych4. Pełne baraże utrzymania\r\nwymagają wyników czterech grup zaplecza. UID129560 zachować jako pulę;\r\nnowy UID nieprzydzielony. Analiza zakończona, brak prototypu i pilota.\r\nKatalog POLAND_THIRD_TIER_R6_20261107 zawiera punkt wznowienia, model\r\nzasad, dowody i audyt odczytu dodatkowej funkcji angielskich baraży.\r\nEXE, bazy i zapisane projekty Ghidry niezmienione.\r\n''').encode('utf-8'))
(OUT/'WZNOWIENIE.md').write_text('''# Skrócony kontekst do kontynuacji\n\nGhidra R5 gotowa i zweryfikowana:91 123 plikiC,91 406 funkcji (283importy); projekt project-research/FM08_802_FULL_R5.gpr. Nie powtarzać importu/autoanalizy. Oryginalne EXE SHA256'''+EXPECTED+''' i bazy nietknięte.\n\nAnaliza trzeciego poziomu R6 zakończona, jeszcze bez prototypu/pilota. Szczegóły: FM08-Database-Tools/docs/POLAND_THIRD_TIER_R6.md oraz tutaj report.json/target-rules.json.\n\nDocelowo18klubów/34kolejki/306meczów,awans2+1,spadek4–6,2polskichmłodzieżowców. Zachować129560 jako pulę; nowyUID nieprzydzielony. I liga UID129559 powinna oddawać3kluby do nowej ligi (obecnie4). Baraże utrzymania potrzebują wyników4grupIIIligi. Próg rocznika=rok końca sezonu−21; przesunięte2007/08 daje1987.\n\nNowe dowody: D65340 podmienia division_levels; D68CB0/D642A0 przy udanym odczycie competitions omija pol_setup_comps, więc XMLzjednąligą może utracić resztę kraju. ACTUAL_COMP D805B0 i D70CF0 tworzą ogólne etapy. Preferowany kolejny eksperyment: kopia802+rekord18klubów+pełna rejestracja kraju przez zasoby; alternatywa hook dopisujący ogólny obiekt po natywnym setup.\n\nBaraże wzorzecENG_FIRST F08C60 dodatkowo odczytany readOnly/noanalysis; nowa funkcja była tylko w pamięci, projekt bez zmian (targeted-audit.json). CUP_SETTINGS obsługuje4→2→1,flagi0x204kandydat fixed+higherseededhome; selekcja3–6/4–5 i seedfinału jeszcze nieudowodnione. E10D80/E10EC0/E495D0 zapisują istniejące typy etapów/akcji, ale nowej ligi nie przetestowano.\n\nMłodzież: reguła0x1D=minU21First11,0x14=domesticU21matchsquad,0x5E=domesticFirst11. Nie składać minU21+minPolaków, bo predykaty muszą dotyczyć tych samych osób. 6CD420/C95670 kontrolują zmiany i osłabienia,73EBC0blokuje powrót;AI C911E0/6E30A0. Brak potwierdzenia wyjątku kontuzjowanegomłodegoGK oraz szczegółów obywatelstwa/rocznika.\n\nNastępny krok: wąski prototyp na nowej kopii802 pokazujący wybór nowej ligi i klubu, zachowanie pucharów,34kolejki i save/load; następnie spójne awanse/spadki+baraże+zaplecze i młodzież. Nie uruchomiono jeszcze gry i nie ma gotowego pakietu XML.\n''',encoding='utf-8')
state=json.loads((OUT/'checkpoint.json').read_text());state.update(status=report['status'],report='report.json',next_action='isolated_third_tier_registration_and_calendar_prototype_on_fresh_802_copy',static_analysis_saved=True);(OUT/'checkpoint.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
archive=OUT/'source-snapshot';archive.mkdir();sources=[REPO/'scratch/checkpoint_poland_third_tier_r6_20261107.py',REPO/'scratch/probe_poland_third_tier_r6_20261107.py',pathlib.Path(__file__),docpath]
source_manifest=[]
for src in sources:
 dst=archive/src.name;shutil.copy2(src,dst);source_manifest.append(dict(path=dst.name,sha256=sha(dst)))
save(archive/'manifest.json',dict(source_only=True,files=source_manifest))
assert sha(ROOT/'fm.exe')==EXPECTED
print(json.dumps(dict(status=report['status'],evidence_functions=len(manifest),extra_function=1,model='34 rounds / 306 matches / four season-balance cases',document=str(docpath)),ensure_ascii=True))
