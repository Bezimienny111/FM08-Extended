from pathlib import Path
from datetime import datetime
import hashlib,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
SCRATCH=ROOT/'FM08-Database-Tools/scratch'
SRC=ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_FATES_R9_1_20261107'
OUT=ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_GROUP_FIX_R9_2_20261108'
NAME='PolandThirdTierGroupFixR92'
BUILD=SCRATCH/'poland_group_r92_build'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def hashes(p):return {str(x.relative_to(p)):sha(x) for x in p.rglob('*') if x.is_file()}
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def replace_once(s,a,b):
 assert s.count(a)==1,(a,s.count(a))
 return s.replace(a,b)

def build():
 BUILD.mkdir(exist_ok=True)
 source=(SCRATCH/'PolandThirdTierFatesR9.cs').read_text(encoding='utf-8-sig')
 source=source.replace('public static class PolandThirdTierFatesR9','public static partial class '+NAME)
 source=source.replace('PolandThirdTierFatesR9.exe',NAME+'.exe')
 source=replace_once(source,'const int StateSize = 48;','const int StateSize = 96;')
 source=replace_once(source,'                VerifyActivationHookFixtures();','                VerifyActivationHookFixtures();\n                VerifyGroupInitializerFixtures();\n                VerifySeasonGateFixtures();')
 source=replace_once(source,'            VerifyUpperBoundaryImage(image);','            VerifyUpperBoundaryImage(image);\n            VerifyGroupImage(image);')
 source=replace_once(source,'                InstallActivationHooks(pi.Process, state);','                InstallActivationHooks(pi.Process, state);\n                InstallGroupInitializer(pi.Process, state);\n                InstallSeasonGate(pi.Process, state);')
 source=replace_once(source,'                string previous = null;','                string previous = null, previousGroup = null;')
 source=replace_once(source,'                    Thread.Sleep(500);','                    var groupLine = GroupTelemetry(pi.Process, bytes);\n                    if (groupLine != previousGroup) { log.WriteLine(groupLine); Console.WriteLine(groupLine); previousGroup = groupLine; }\n                    Thread.Sleep(500);')
 source=replace_once(source,'                uint exit; Check(GetExitCodeProcess', '                try { var finalState = Read(pi.Process, state, StateSize); log.WriteLine(GroupTelemetry(pi.Process, finalState)); } catch (Win32Exception) { }\n                uint exit; Check(GetExitCodeProcess')
 # Restrict launcher to this independently packaged fix, not an older R9 runtime.
 source=replace_once(source,'        var manifest = File.ReadAllText(manifestPath);','        var manifest = File.ReadAllText(manifestPath);\n        Require(System.Text.RegularExpressions.Regex.IsMatch(manifest, "\\\"repair_revision\\\"\\\\s*:\\\\s*\\\"R9[.]2\\\""), "Manifest repair revision is not R9.2.");')
 (BUILD/(NAME+'.cs')).write_text(source,encoding='utf-8')
 helper=(SCRATCH/'PolandThirdTierGroupInitializerR92.cs').read_text(encoding='utf-8-sig')
 # A native fallback is free to clobber flags. This fixture's fake fallback preserves them
 # so the test detects changes introduced by the dispatch trampoline itself.
 (BUILD/'PolandThirdTierGroupInitializerR92.cs').write_text(helper,encoding='utf-8')
 csc=Path('C:/Windows/Microsoft.NET/Framework/v4.0.30319/csc.exe')
 result=subprocess.run([str(csc),'/nologo','/platform:x86','/optimize+','/out:'+str(BUILD/(NAME+'.exe')),str(BUILD/(NAME+'.cs')),str(BUILD/'PolandThirdTierGroupInitializerR92.cs')],capture_output=True,text=True)
 print(result.stdout,result.stderr,flush=True); assert result.returncode==0,'Compilation failed'
 result=subprocess.run([str(BUILD/(NAME+'.exe')),'--verify',str(ROOT/'fm.exe')],capture_output=True,text=True)
 print(result.stdout,result.stderr,flush=True)
 save(BUILD/'verification.json',dict(compiled=True,verify_exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr,game_started=False,tool_sha256=sha(BUILD/(NAME+'.exe'))))
 assert result.returncode==0,'x86 verification failed'
 return BUILD/(NAME+'.exe')

def package(tool):
 assert not OUT.exists(),'Refuse overwriting existing R9.2'
 manifest=json.loads((SRC/'manifest.json').read_text(encoding='utf-8-sig'))
 db=SRC/'user-data/db/TEST_POL_3_LEVEL_R9'
 assert hashes(db)==manifest['database_output_hashes'],'R9.1 database differs from accepted SI save'
 assert sha(SRC/'runtime/fm.exe')==manifest['protected_original_hashes']['fm.exe']
 OUT.mkdir()
 print('Copying isolated runtime/database; R9.1 remains untouched.',flush=True)
 for name in ['runtime','resources','tools','promotion','lower-boundary','upper-boundary']:
  shutil.copytree(SRC/name,OUT/name)
 shutil.copytree(db,OUT/'user-data/db/TEST_POL_3_LEVEL_R9')
 shutil.copy2(SRC/'participants.csv',OUT/'participants.csv')
 for file in [BUILD/(NAME+'.cs'),BUILD/'PolandThirdTierGroupInitializerR92.cs',Path(__file__)]:shutil.copy2(file,OUT/'tools/src'/file.name)
 shutil.copy2(tool,OUT/'tools'/tool.name)
 # Preserve the exact accepted SI database bytes; package display is documented in README.
 manifest.update(repair_revision='R9.2',status='prepared_for_r92_game_test',runtime=str(OUT/'runtime'),output_database=str(OUT/'user-data/db/TEST_POL_3_LEVEL_R9'),source_database=str(db),started_at=datetime.now().astimezone().isoformat(),repair_reason='GROUP_STAGE generic virtual initializer is ret8 and loses real input teams; native constructor and XML initialization added',pilot_tool_sha256=sha(tool),pilot_tool_name=tool.name,source_R91_database_hashes=hashes(db),database_output_hashes=hashes(OUT/'user-data/db/TEST_POL_3_LEVEL_R9'),group_initializer_hook=True,group_initializer_attempt=3,season_initialization_gate=True,preflight_passed=False,game_verified=False,new_career_verified=False,save_load_verified=False,season_rollover_verified=False,group_tables_verified_runtime=False,runtime_crash_repaired=False,rules_changed=False)
 manifest['unresolved']=['Confirm actual constructor input100 and four populated tables25 in runtime','Fresh career creation, save/load, playoffs and season rollover remain unverified']
 manifest['source_snapshots']=hashes(OUT/'tools/src')
 manifest['verified_at']=datetime.now().astimezone().isoformat()
 save(OUT/'manifest.json',manifest)
 start=(SRC/'Start-Pilot.ps1').read_text(encoding='utf-8-sig').replace('PolandThirdTierFatesR9.exe',NAME+'.exe').replace("'prepared_for_r9_game_test', 'r9_game_pilot_passed_user_confirmed'","'prepared_for_r92_game_test', 'r92_game_pilot_passed_user_confirmed'").replace('R9 package has not passed final preflight.','R9.2 package has not passed final preflight.')
 (OUT/'Start-Pilot.ps1').write_text(start,encoding='utf-8-sig')
 shutil.copy2(SRC/'Start-Pilot.cmd',OUT/'Start-Pilot.cmd')
 verification=json.loads((BUILD/'verification.json').read_text(encoding='utf-8'))
 verification.update(status='preflight_pending',repair_revision='R9.2',source_R91_database_unchanged=True,database_bytes_identical_to_accepted_R91_SI_save=True,resources_unchanged_from_R91=True,source_snapshots=hashes(OUT/'tools/src'),native_group_fixture_cases=13,native_season_gate_fixture_cases=48,source_r9_verification='R9.1/verification.json (historical country audit)',game_verified=False,new_career_verified=False,save_load_verified=False,season_rollover_verified=False,group_tables_verified_runtime=False,runtime_crash_repaired=False)
 save(OUT/'verification.json',verification)
 report=dict(source_exe_sha256=sha(ROOT/'fm.exe'),call_site='0x00D7C9C9',original_bytes='897E30FF5278',continuation='0x00D7C9CF',native_constructor='0x00E3A560',native_xml_initializer='0x00E29270',guards=['owner UID129560','GROUP_STAGE vtable0160F90C','owned pointers/counts empty'],constructor_arguments=['index0; XML metadata subsequently initializes actual index','temporary real team list','NULL optional group-byte array','flag1'],native_allocation_and_destructor_preserved=True,global_vtable_changed=False,on_disk_exe_changed=False,input_list_lifetime_independent=True,runtime_verified=False,evidence=['ram_e3a560.c','ram_e3a6e0.c','ram_e29940.c','ram_e29270.c','ram_e62230.c','ram_e3a720.c','ram_d7c950.c'])
 save(OUT/'group-initializer-analysis.json',report)
 (OUT/'README.md').write_text('''# R9.2 — inicjalizacja czterech grup zaplecza

Osobny pilot naprawy awarii R9.1. Uruchom Start-Pilot.cmd z TEGO katalogu.
Nowa kariera, baza TEST_POL_3_LEVEL_R9_1 (widoczna nazwa pozostaje taka sama,
bo zachowano dokładne bajty bazy zaakceptowanej po zapisie w edytorze SI).
Wybierz Polskę i trzeci poziom. R8, R9 i R9.1 pozostają nietknięte.

Kod w pamięci wyłącznie nowego procesu przejmuje wywołanie inicjalizatora
GROUP_STAGE tylko dla obiektu o aktualnym UID129560. Pusty obiekt
otrzymuje prawdziwą listę przez natywny konstruktor E3A560, następnie właściciela
i metadane XML przez E29270. Alokator, rekordy, destruktor i vtable są natywne.
Baza, zasoby, reguły i pliki EXE na dysku nie zmieniają się względem R9.1.

Log pilot-logs zawiera event group: input_count, copied_count, xml_index,
group_count oraz team_count/table dla każdej grupy. Oczekiwane100,100,0,4
oraz cztery niepuste tabele po25 (four_tables_of_25=true).
Kontrola nie potwierdza jeszcze zakończenia tworzenia kariery. Pozostają
start kariery, zapis/odczyt, baraże i zmiana sezonu z bilansem18/18/100.

Nie traktować wyjścia procesu code0 ani preflight PASS jako zaliczenia gry.
Dowody statyczne: group-initializer-analysis.json. Testy: verification.json.
''',encoding='utf-8')
 (OUT/'WZNOWIENIE.md').write_text('''# R9.2 — naprawa inicjalizacji GROUP_STAGE

Nowy, osobny pakiet. Natywny konstruktor E3A560 kopiuje drużyny do własnej tablicy;
owner przywrócony, E29270 odczytuje indeks/id XML. Zakres tylko UID129560,
aktualny UID obiektu i pusta grupa. Inne przypadki zachowują oryginalne wywołanie.
Baza identyczna bajtowo z zaakceptowanym zapisem SI R9.1; reguły bez zmian.
Start-Pilot.cmd; baza nadal wyświetla TEST_POL_3_LEVEL_R9_1.
Runtime i sezon NIEPOTWIERDZONE. Wymagane100 ->4x25, nowa kariera, zapis/odczyt,
baraże i kolejny sezon. Log event group mierzy faktyczne tabele.
''',encoding='utf-8')
 result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(OUT/'Start-Pilot.ps1'),'-VerifyOnly'],capture_output=True,text=True)
 print(result.stdout,result.stderr,flush=True)
 verification.update(package_verify_exit_code=result.returncode,preflight_passed=result.returncode==0,status='prepared_for_r92_game_test' if result.returncode==0 else 'preflight_failed')
 manifest.update(preflight_passed=result.returncode==0,status=verification['status'])
 save(OUT/'verification.json',verification);save(OUT/'manifest.json',manifest)
 assert result.returncode==0,'Package verification failed'
 assert hashes(db)==manifest['source_R91_database_hashes']
 for rel,want in manifest['protected_original_hashes'].items():assert sha(ROOT/rel)==want,rel
 assert hashes(OUT/'user-data/db/TEST_POL_3_LEVEL_R9')==manifest['source_R91_database_hashes']
 print(json.dumps({'status':verification['status'],'output':str(OUT),'game_started':False}),flush=True)

def refresh(tool):
 manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
 assert sha(OUT/'tools'/tool.name)==manifest['pilot_tool_sha256']
 previous_attempt=manifest.get('group_initializer_attempt',1)
 next_attempt=previous_attempt+1
 attempt=OUT/('attempts/%02d-'%previous_attempt+('pointer-guard' if previous_attempt==1 else 'year-zero'))
 attempt.mkdir(parents=True,exist_ok=False)
 for file in [OUT/'manifest.json',OUT/'verification.json',OUT/'tools'/tool.name,OUT/'tools/src'/(NAME+'.cs'),OUT/'tools/src/PolandThirdTierGroupInitializerR92.cs',OUT/'group-initializer-analysis.json']:
  shutil.copy2(file,attempt/file.name)
 dump=Path('C:/Users/Bezi/AppData/Local/CrashDumps/fm.exe.15384.dmp')
 if previous_attempt==1:
  save(attempt/'result.json',dict(status='runtime_failed_same_DC412E',process_id=15384,exception='0xC0000005',fault_va='0x00DC412E',dump_sha256=sha(dump),initializer_not_applied=True,group_event='waiting',third_allocation='0x212D3FD8',lower_allocation='0x212D4218',crash_stack_owner='0x212D3FD8',owner_uid_in_dump='heap not captured; cannot infer UID from allocation role',next_change='Remove allocation-address equality guard; retain exact current UID129560 and group class/emptiness guards; record all group owner UIDs'))
 else:
  save(attempt/'result.json',dict(status='career_created_current_lower_season_missing',career_creation_verified_user=True,third_fixtures_visible_user=True,lower_groups_visible_user=4,current_game_date='2007-08-01',current_lower_table_visible=False,current_lower_fixtures_visible=False,owner_season_year_D8=0,owner_base_year_14A=2000,each_group_team_count=25,each_group_schedule_dates_count=50,each_group_first_date_year=0,each_group_generation_called=True,root_cause='D644B2 selected-level guard skipped native season initialization D714A0 at lowerlevel3 selected2',next_change='Allow native season initializer path for current UID129560 selected>=2, preserving original arguments and year calculation'))

 for file in [BUILD/(NAME+'.cs'),BUILD/'PolandThirdTierGroupInitializerR92.cs',Path(__file__)]:shutil.copy2(file,OUT/'tools/src'/file.name)
 shutil.copy2(tool,OUT/'tools'/tool.name)
 manifest.update(status='prepared_for_r92_game_test',pilot_tool_sha256=sha(tool),source_snapshots=hashes(OUT/'tools/src'),group_initializer_attempt=next_attempt,previous_attempt_failed=True,preflight_passed=False,runtime_crash_repaired=False,game_verified=False,new_career_verified=False,save_load_verified=False,season_rollover_verified=False,group_tables_verified_runtime=False,group_initialization_verified_runtime=False,season_initialization_gate=True)
 save(OUT/'manifest.json',manifest)
 report=json.loads((OUT/'group-initializer-analysis.json').read_text(encoding='utf-8'))
 report['guards']=['current owner UID129560','GROUP_STAGE vtable0160F90C','owned pointers/counts empty']
 report['allocation_address_guard_removed']=True
 report['runtime_verified']=False
 report['season_initialization_gate']=dict(site='0x00D644B2',original='3AC17F1B8B44242C',active_continuation='0x00D644BA',fallback='0x00D644D1',native_initializer='ACTUAL_COMP virtual+32C = D714A0',scope='current UID129560, selected>=2',year_hardcoded=False)
 report['allocation_identity_explanation']='D68270 recreates competition objects after loading newer XML versions; original allocation addresses become stale.'
 save(OUT/'group-initializer-analysis.json',report)
 result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(OUT/'Start-Pilot.ps1'),'-VerifyOnly'],capture_output=True,text=True)
 print(result.stdout,result.stderr,flush=True)
 verify=json.loads((BUILD/'verification.json').read_text(encoding='utf-8'))
 verify.update(status='prepared_for_r92_game_test' if result.returncode==0 else 'preflight_failed',repair_revision='R9.2',attempt=next_attempt,native_season_gate_fixture_cases=48,package_verify_exit_code=result.returncode,preflight_passed=result.returncode==0,game_verified=False,new_career_verified=False,group_tables_verified_runtime=False,save_load_verified=False,season_rollover_verified=False,runtime_crash_repaired=False,previous_attempt_failed=True)
 save(OUT/'verification.json',verify)
 manifest['preflight_passed']=result.returncode==0;manifest['status']=verify['status'];save(OUT/'manifest.json',manifest)
 assert result.returncode==0
 assert hashes(OUT/'user-data/db/TEST_POL_3_LEVEL_R9')==manifest['source_R91_database_hashes']
 for rel,want in manifest['protected_original_hashes'].items():assert sha(ROOT/rel)==want
 print('R9.2 attempt'+str(next_attempt)+' prepared; previous executable/source/result preserved.',flush=True)

if __name__=='__main__':
 tool=build()
 if '--package' in sys.argv:package(tool)
 if '--refresh' in sys.argv:refresh(tool)
