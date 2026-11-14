"""Record R9.2 runtime evidence and user confirmations; never change game/database files."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,subprocess,shutil
ROOT=Path(__file__).resolve().parents[2]
REPO=ROOT/'FM08-Database-Tools'
OUT=ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_GROUP_FIX_R9_2_20261108'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--career-confirmed',action='store_true')
 parser.add_argument('--fixtures-confirmed',action='store_true')
 parser.add_argument('--save-load-confirmed',action='store_true')
 parser.add_argument('--playoffs-confirmed',action='store_true')
 args=parser.parse_args()
 manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
 log=max((OUT/'pilot-logs').glob('*.jsonl'),key=lambda p:p.stat().st_mtime)
 rows=[json.loads(x) for x in log.read_text(encoding='utf-8-sig').splitlines()]
 installed=next(x for x in rows if x.get('event')=='installed')
 group=next(x for x in reversed(rows) if x.get('event')=='group' and x.get('four_tables_of_25'))
 assert group['input_count']==group['copied_count']==group['group_team_count']==100
 assert group['group_count']==4 and all(x['team_count']==25 and int(x['table'],16)!=0 for x in group['leagues'])
 assert group['initializer_status']==1 and group['xml_index']==0
 assert group.get('season_gate_calls',0)>=1 and group['season_year']>=2007
 assert all(x['first_date_year']==group['season_year'] and x['scheduled_dates']==50 for x in group['leagues'])
 summary_path=OUT/'runtime-group-verification.json'
 previous=json.loads(summary_path.read_text(encoding='utf-8')) if summary_path.exists() else {}
 same_tool=previous.get('tool_sha256')==sha(OUT/'tools/PolandThirdTierGroupFixR92.exe')
 career=args.career_confirmed or args.fixtures_confirmed or (same_tool and previous.get('career_creation_verified',False))
 fixtures=args.fixtures_confirmed or (same_tool and previous.get('current_fixtures_verified_user',False))
 saved=args.save_load_confirmed or (same_tool and previous.get('save_load_verified',False))
 rollover_path=OUT/'season-rollover-verification.json'
 rollover_report=json.loads(rollover_path.read_text(encoding='utf-8')) if rollover_path.exists() else {}
 rollover=bool(rollover_report.get('season_rollover_verified')) and rollover_report.get('tool_sha256')==sha(OUT/'tools/PolandThirdTierGroupFixR92.exe')
 playoffs=args.playoffs_confirmed or (same_tool and previous.get('playoff_stage_results_verified_user',False))
 summary=dict(recorded_at=datetime.now(timezone.utc).isoformat(),repair_revision='R9.2',attempt=manifest['group_initializer_attempt'],process_id=installed['process_id'],tool_sha256=sha(OUT/'tools/PolandThirdTierGroupFixR92.exe'),input_clubs=100,copied_clubs=100,group_count=4,group_team_counts=[25]*4,all_tables_non_null=True,group_xml_index=0,season_gate_calls=group['season_gate_calls'],season_year=group['season_year'],each_group_scheduled_dates=[x['scheduled_dates'] for x in group['leagues']],each_group_first_date_year=[x['first_date_year'] for x in group['leagues']],each_group_generation_called=[bool(x['fixtures_generated']) for x in group['leagues']],original_DC412E_setup_passed=True,career_creation_verified=career,current_fixtures_verified_user=fixtures,save_load_verified=saved,playoffs_verified=False,playoff_stage_results_verified_user=playoffs,playoff_pairings_hosts_verified=False,save_load_during_playoffs_verified=False,season_rollover_verified=rollover,log=str(log.relative_to(OUT)),previous_attempts={'1':'same DC412E crash due stale allocation-address guard','2':'career created; current lower table/fixtures absent Aug1 2007, owner season+D8 and schedule years0'},allocation_identity='D68270 recreates ACTUAL_COMP objects when newer XML versions are loaded; original allocation roles are not stable',year_zero_cause='D644B2 skipped native D714A0 at level3 selected2; scoped gate now takes native initialization path')
 save(summary_path,summary)
 for source in [Path(__file__),REPO/'scratch/prepare_poland_group_fix_r92_20261108.py',REPO/'scratch/inspect_poland_pilot_runtime_r92_20261108.py']:
  shutil.copy2(source,OUT/'tools/src'/source.name)
 snapshots={str(p.relative_to(OUT/'tools/src')):sha(p) for p in (OUT/'tools/src').rglob('*') if p.is_file()}
 for name in ['manifest.json','verification.json']:
  p=OUT/name;data=json.loads(p.read_text(encoding='utf-8'))
  data.update(source_snapshots=snapshots,group_tables_verified_runtime=True,group_initialization_verified_runtime=True,original_DC412E_setup_passed=True,season_year_verified_runtime=True,runtime_group_evidence='runtime-group-verification.json',game_verified=False,selection_verified_in_game=career,new_career_verified=career,current_fixtures_verified_user=fixtures,save_load_verified=saved,playoff_stage_results_verified_user=playoffs,playoff_pairings_hosts_verified=False,save_load_during_playoffs_verified=False,season_rollover_verified=rollover,runtime_crash_repaired=career)
  data['unresolved']=([] if career else ['Confirm career creation'])+([] if fixtures else ['Confirm current tables and fixtures after July27 group draw'])+([] if saved else ['Verify save-load after group draw'])+([] if playoffs else ['Confirm both playoff stage results in2007/08 history'])+([] if rollover else ['Verify next season18/18/100'])+['Audit playoff pairings and hosts','Verify save-load inside playoffs']
  data['validation_stage']='season_rollover_verified_pending_playoff_detail_audit' if rollover else 'basic_career_tables_fixtures_save_load_verified' if career and fixtures and saved else 'career_and_fixtures_verified_pending_save_load' if career and fixtures else 'runtime_groups_and_calendar_verified'
  save(p,data)
 season_text='Przejscie do2008/09: potwierdzone;3 awanse i3 spadki miedzy drugim/trzecim poziomem,5/5 z zapleczem;18/18/100 i nowe terminarze2008.' if rollover else 'Zmiana sezonu18/18/100 nadal niepotwierdzona.'
 playoff_text='Wyniki obu rodzajow barazy potwierdzone przez uzytkownika.' if playoffs else 'Wyniki obu rodzajow barazy w historii czekaja na potwierdzenie.'
 pending_text='Szczegoly par/gospodarzy oraz zapis/odczyt wewnatrz barazy pozostaja niepotwierdzone.'
 progress='Kariera: '+('potwierdzona przez uzytkownika' if career else 'czeka na potwierdzenie')+'. Biezace tabele/terminarze: '+('potwierdzone przez uzytkownika' if fixtures else 'czekaja na potwierdzenie')+'. Zapis/odczyt: '+('potwierdzony przez uzytkownika' if saved else 'niepotwierdzony')+'.'
 content='''# R9.2 — aktualny stan 2026-11-08

Proba3: runtime100 ->4x25, sezon2007,50 dat kazdej grupy w roku2007.
Zakres UID129560, natywna GROUP_STAGE, puste wskazniki/liczniki.
E3A560 kopiuje drużyny do wlasnej tablicy, owner przywrocony, E29270 czyta XML.
Trzeci guard D644B2 dopuszcza natywne virtual+32C (D714A0) przy selected>=2.
Rok jest obliczany natywnie; nie przypisujemy2007 ani nie zmieniamy dat XML.

'''+progress+'''
'''+season_text+'\n'+playoff_text+'\n'+pending_text+'''

Start-Pilot.cmd z tego katalogu; nowa kariera, baza TEST_POL_3_LEVEL_R9_1.
Baza jest identyczna bajtowo z zaakceptowanym SI R9.1. Reguly/zasoby bez zmian.
EXE na dysku bez zmian. Wczesniejsze R8/R9/R9.1 zachowane.
Raport runtime-group-verification.json; log: '''+str(log.relative_to(OUT))+'''.

Proba1: crashDC412E, guard starego adresu alokacji nie przepuscil grupy.
D68270 odtwarza obiekty po nowszej wersji XML; identyfikowac aktualny UID.
Proba2: kariera utworzona,4x25, ale brak aktualnej tabeli i terminarzy na1.08.2007.
Owner+D8=0, daty roku0; D644B2 pomijal sezon, choc dwa pozniejsze guardy
aktywacji przepuszczaly zaplecze. Archiwa: attempts/01-pointer-guard i02-year-zero.
'''
 (OUT/'WZNOWIENIE.md').write_text(content,encoding='utf-8')
 (OUT/'README.md').write_text(content.replace('# R9.2 — aktualny stan','# R9.2 — pilot naprawy grup i sezonu'),encoding='utf-8')
 doc=REPO/'docs/POLAND_THIRD_TIER_GROUP_FIX_R92.md'
 doc.write_text('''# R9.2 — naprawa grup i inicjalizacji sezonu zaplecza

Stan2026-11-08: **runtime100 ->4x25, sezon2007 i50 dat kazdej grupy w roku2007**.
'''+progress+'''
'''+season_text+'\n'+playoff_text+'\n'+pending_text+'''

## Zmiana

D7C950 wywoluje pusty virtual+78 dla GROUP_STAGE. Hook D7C9C9, ograniczony
do aktualnego UID129560, vtable0160F90C i pustego stanu, wywoluje natywny
E3A560 z prawdziwa lista klubow. Konstruktor kopiuje ja do wlasnej tablicy;
alokator, rekordy i destruktor pozostaja natywne. Hook przywraca owner+30
i wywoluje E29270 dla indeksu/id XML. Inne rozgrywki zachowuja oryginalna sciezke.

Dodatkowy guard D644B2 przepuszcza UID129560 przy selected>=2 przez oryginalne
virtual+32C (D714A0), zachowujac argumenty. Natywna procedura inicjalizuje rok
sezonu+D8 przed parsowaniem kalendarza. Poprawka nie wpisuje roku2007 recznie.

Baza jest identyczna bajtowo z zaakceptowanym SI R9.1; reguly, zasoby i pliki
EXE na dysku niezmienione. Hooki dotycza nowego procesu. R8/R9/R9.1 zachowane.

## Dowody

- 13 przypadkow wykonanego kodu x86 inicjalizatora:100 niezaleznych rekordow,
ABI ret16/ret4, owner, fallback, zakres UID, stos i flagi.
- 48 przypadkow nowego guarda sezonu; oryginalne argumenty, galaz, flagi i stos.
- Regresje: 11 scenariuszy dopisywania,96 aktywacji, trzy zmiany POL_SECOND i rollback.
- Kontrola pakietu: hashe bazy/zasobow, ABI i izolowany runtime PASS.
- Proba 3, PID'''+str(installed['process_id'])+''': input100, copied100, index0,4 niepuste tabele po25,
season_year2007,50 dat w roku2007 w kazdej grupie. Biezace generowanie spotkan
jest osobnym stanem od istnienia listy dat; log mierzy oba.

## Dwie poprzednie proby

Proba1: crashDC412E. Guard historycznego adresu alokacji nie dopuscil grupy.
D68270 odtwarza ACTUAL_COMP po nowszej wersji XML, usuwa oryginaly i zastepuje
wpisy kolekcji. Guard oparty na pierwotnym adresie byl bledny; aktualny UID jest
wlasciwa tozsamoscia. Nie znaleziono dowodu wspolnego mutowalnego XML.

Proba2: uzytkownik potwierdzil utworzenie kariery i terminarz trzeciej ligi.
Cztery grupy zaplecza istnialy, ale1.08.2007 nie mialy aktualnych tabel/spotkan.
Odczyt pamieci wykazal owner+D8=0 i50 dat roku0 w kazdej grupie. Wczesny guard
D644B2 pomijal natywna inicjalizacje sezonu dla level3 przy selected2, mimo
przepuszczenia dwoch pozniejszych guardow aktywacji. Proba3 naprawia ten etap.

## Wznowienie

Lokalny pakiet: `FmLauncher/data/research/POLAND_THIRD_TIER_GROUP_FIX_R9_2_20261108`.
Start-Pilot.cmd, baza nadal wyswietla TEST_POL_3_LEVEL_R9_1 dla zachowania bajtow SI.
Raport runtime-group-verification.json i surowe logi pozostaja poza repozytorium.
Nie mylic PASS kontroli ani exit0 z zaliczeniem calego sezonu.

Kod: [inicjalizator i guard](../scratch/PolandThirdTierGroupInitializerR92.cs),
[budowanie pakietu](../scratch/prepare_poland_group_fix_r92_20261108.py),
[zapis dowodow](../scratch/record_poland_group_fix_r92_20261108.py).
[czytnik zywego pilota](../scratch/inspect_poland_pilot_runtime_r92_20261108.py).
Kontekst: [R9.1](POLAND_THIRD_TIER_COUNTRY_FIX_R91.md).

Po odczycie zapisu logger pierwszego GROUP_STAGE moze nadal wskazywac jego
poprzedni adres. Dalsze odczyty sezonu nalezy robic czytnikiem, ktory za kazdym
razem znajduje aktualne obiekty wedlug UID w polskiej kolekcji. Nie interpretowac
starego adresu grupy jako biezacego sezonu. Czytnik potwierdzil po odczycie
18/18/100 roznych klubow, bez duplikatow miedzy tabelami.
''',encoding='utf-8')
 p=REPO/'docs/RESEARCH_INDEX.md';text=p.read_text(encoding='utf-8');lines=text.splitlines()
 for i,line in enumerate(lines):
  if line.startswith('| Awanse, spadki, cztery grupy |'):
   lines[i]='| Awanse, spadki, cztery grupy | [R9](POLAND_THIRD_TIER_FATES_R9.md), [R9.1](POLAND_THIRD_TIER_COUNTRY_FIX_R91.md), [aktualny R9.2](POLAND_THIRD_TIER_GROUP_FIX_R92.md) | R9.2 kariera, zapis/odczyt i przejscie2008/09 potwierdzone;18/18/100; szczegoly barazy nadal wymagaja audytu |'
 p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
 p=REPO/'docs/POLAND_THIRD_TIER_COUNTRY_FIX_R91.md';text=p.read_text(encoding='utf-8')
 a=text.index('## Dalszy etap: R9.2');b=text.index('## Stan R9.1:',a)
 text=text[:a]+'''## Dalszy etap: R9.2

[Aktualny pilot R9.2](POLAND_THIRD_TIER_GROUP_FIX_R92.md) naprawia inicjalizacje
grup i roku sezonu zaplecza. Status testow znajduje sie w nowym raporcie.
Ponizszy opis pozostaje diagnoza poprzedniego pakietu R9.1.

'''+text[b:];p.write_text(text,encoding='utf-8')
 p=REPO/'docs/research/publication.json';publication=json.loads(p.read_text(encoding='utf-8'))
 # Preserve the original publication order and append authored additions.
 baseline=json.loads(subprocess.check_output(['git','-C',str(REPO),'show','HEAD:docs/research/publication.json'],text=True))
 entries={e['path']:e for e in publication['files']}
 changed=['.gitignore','docs/RESEARCH_INDEX.md','docs/POLAND_THIRD_TIER_COUNTRY_FIX_R91.md','docs/POLAND_THIRD_TIER_GROUP_FIX_R92.md','scratch/PolandThirdTierGroupInitializerR92.cs','scratch/prepare_poland_group_fix_r92_20261108.py','scratch/record_poland_group_fix_r92_20261108.py','scratch/inspect_poland_pilot_runtime_r92_20261108.py']
 for rel in changed:
  content=(REPO/rel).read_bytes();entries[rel]=dict(path=rel,origin='FM08-Database-Tools/'+rel,sha256=hashlib.sha256(content).hexdigest(),bytes=len(content))
 ordered=[e['path'] for e in baseline['files']];ordered+=sorted(set(entries)-set(ordered))
 publication['files']=[entries[path] for path in ordered];save(p,publication)
 print(json.dumps({'status':'recorded_runtime_groups_and_calendar','attempt':manifest['group_initializer_attempt'],'career_verified':career,'fixtures_verified':fixtures,'save_load_verified':saved,'season_rollover_verified':rollover,'playoff_results_verified_user':playoffs}))

if __name__=='__main__':main()
