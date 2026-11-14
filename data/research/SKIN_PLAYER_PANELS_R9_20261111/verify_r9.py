from pathlib import Path
import subprocess,json,hashlib,time,datetime,shutil,sys
ROOT=Path(r'J:/FM08dev')
R=ROOT/'FmLauncher/data/research/SKIN_PLAYER_PANELS_R9_20261111'
V=R/'verification'
V.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((ROOT/'FmLauncher/data/research/SKIN_PLAYER_PANELS_R8_20261111/manifest.json').read_text(encoding='utf-8-sig'))
assert all(sha(ROOT/'Launcher_0.1.3_R8'/n)==v['sha256'] for n,v in old['candidate_files'].items())
current={n:sha(ROOT/'FmLauncher/src/FmLauncher'/n) for n in old['source_hashes']}
changed=[n for n,h in current.items() if h!=old['source_hashes'][n]]
assert set(changed)=={'GamePositionBackgroundPatch.cs','SuspendedGameProcess.cs','FmLauncher.languages.json'},changed
results=json.loads((V/'results.json').read_text(encoding='utf-8')) if '--skip-build' in sys.argv and (V/'results.json').exists() else []
def run(name,cmd):
 t=time.monotonic()
 p=subprocess.run(cmd,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
 (V/(name+'.log')).write_text(p.stdout,encoding='utf-8')
 item={'name':name,'command':cmd,'exit_code':p.returncode,'seconds':round(time.monotonic()-t,2)}
 results.append(item)
 (V/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
 print(name,p.returncode,item['seconds'],flush=True)
 if p.returncode:print(p.stdout,flush=True);raise SystemExit(p.returncode)
T=R/'tests'
if '--skip-build' not in sys.argv:
 run('build',['dotnet','build',str(ROOT/'FmLauncher/tests/FmLauncher.Tests/FmLauncher.Tests.csproj'),'--no-restore','-o',str(T),'-v:minimal'])
if '--build-only' in sys.argv: raise SystemExit(0)
guard=subprocess.run(['powershell','-NoProfile','-Command','if(Get-Process fm -ErrorAction SilentlyContinue){exit 19}else{exit 0}'])
assert guard.returncode==0,'FM must be closed before private hook fixture.'
run('hook-readback',[str(T/'FmLauncher.Tests.exe'),'--position-hooks',str(ROOT/'fm.exe')])
run('installed-upgrade-en',[str(T/'FmLauncher.Tests.exe'),'--installed-profile-upgrade-en',str(ROOT/'fm.exe'),str(ROOT/'Dane'),str(V/'upgrade')])
names=list(old['candidate_files'])
C=R/'candidate-0.1.3-R9'
assert not C.exists(),'Do not overwrite candidate.'
C.mkdir()
for n in names:shutil.copy2(T/n,C/n)
files={n:{'sha256':sha(C/n),'bytes':(C/n).stat().st_size} for n in names}
manifest={'version':'0.1.3-R9','status':'TARGETED_HOOK_AND_MANAGED_EN_PASS_CANDIDATE_READY_GUI_PENDING','build_configuration':'Debug/devcandidate','candidate':str(C/'FmLauncher.exe'),'published_executable':str(ROOT/'Launcher_0.1.3_R9/FmLauncher.exe'),'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate_files':files,'source_hashes':current,'changed_application_sources':changed,'R8_frozen_assets_preserved':{n:sha(ROOT/'Launcher_0.1.3_R8'/n)==old['candidate_files'][n]['sha256'] for n in names},'tested_assets_copied_without_rebuild':True,'actual_R8_GUI':'USER_ACCEPTED_LEGEND_FRAME','actual_R9_GUI':'PENDING','actual_installation_performed':False,'checks':results,'native_hook_count':14,'position_hooks':7,'numeric_colour_and_bold_unchanged':True,'database_or_FM_native_language_changed':False,'target_launcher_and_panel_language':'en','scope':'Background covers native attribute names plus numeric cells; English launcher and Ext labels.','limitations':['Actual row background + English UI acceptance remains pending.','Only new hook readback and scoped peer native fixture; unchanged hidden/colour batches not repeated.']}
(R/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('READY',C/'FmLauncher.exe',files['FmLauncher.dll']['sha256'],flush=True)
