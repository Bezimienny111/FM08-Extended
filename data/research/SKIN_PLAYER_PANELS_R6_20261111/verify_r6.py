from pathlib import Path
import subprocess,json,hashlib,time,datetime,shutil,sys
ROOT=Path(r'J:/FM08dev')
R=ROOT/'FmLauncher/data/research/SKIN_PLAYER_PANELS_R6_20261111'
V=R/'verification'
V.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((ROOT/'FmLauncher/data/research/SKIN_PLAYER_PANELS_R5_20261111/manifest.json').read_text(encoding='utf-8-sig'))
oldpins={n:sha(ROOT/'Launcher_0.1.3_R5'/n) for n in old['candidate_files']}
assert all(oldpins[n]==v['sha256'] for n,v in old['candidate_files'].items())
results=[]
def run(name,cmd):
 t=time.monotonic()
 p=subprocess.run(cmd,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
 (V/(name+'.log')).write_text(p.stdout,encoding='utf-8')
 item={'name':name,'command':cmd,'exit_code':p.returncode,'seconds':round(time.monotonic()-t,2)}
 results.append(item)
 (V/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
 print(name,p.returncode,item['seconds'],flush=True)
 if p.returncode: print(p.stdout,flush=True);raise SystemExit(p.returncode)
 return p.stdout
T=R/'tests'
if '--skip-build' not in sys.argv:
 run('build',['dotnet','build',str(ROOT/'FmLauncher/tests/FmLauncher.Tests/FmLauncher.Tests.csproj'),'--no-restore','-o',str(T),'-v:minimal'])
guard=subprocess.run(['powershell','-NoProfile','-Command','if(Get-Process fm -ErrorAction SilentlyContinue){exit 19}else{exit 0}'])
assert guard.returncode==0,'FM must be closed before private fixtures.'
run('hook-readback',[str(T/'FmLauncher.Tests.exe'),'--position-hooks',str(ROOT/'fm.exe')])
run('position-selector',[str(T/'FmLauncher.Tests.exe'),'--position-profile-native',str(ROOT/'fm.exe')])
run('installed-upgrade',[str(T/'FmLauncher.Tests.exe'),'--installed-profile-upgrade',str(ROOT/'fm.exe'),str(ROOT/'Dane'),str(V/'upgrade')])
names=['FmLauncher.exe','FmLauncher.dll','FmLauncher.deps.json','FmLauncher.runtimeconfig.json','FmLauncher.languages.json','FmLauncher.pdb']
C=R/'candidate-0.1.3-R6'
assert not C.exists(),'Do not overwrite frozen candidate.'
C.mkdir()
for n in names:shutil.copy2(T/n,C/n)
files={n:{'sha256':sha(C/n),'bytes':(C/n).stat().st_size} for n in names}
sources={n:sha(ROOT/'FmLauncher/src/FmLauncher'/n) for n in ['GamePanelPatch.cs','GameProfileColour.cs','GameProfilePanelPatch.cs','GameProfileRole.cs','GamePositionBackgroundPatch.cs','GameProfileViewer.cs','GameProfileResolver.cs','PlayerProfileXml.cs','SuspendedGameProcess.cs','FmLauncher.languages.json']}
preserved={n:sha(ROOT/'Launcher_0.1.3_R5'/n)==oldpins[n] for n in names}
assert all(preserved.values())
manifest={'version':'0.1.3-R6','status':'TESTED_CANDIDATE_READY_GUI_PENDING','candidate':str(C/'FmLauncher.exe'),'published_executable':str(ROOT/'Launcher_0.1.3_R6/FmLauncher.exe'),'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate_files':files,'source_hashes':sources,'R5_frozen_assets_preserved':preserved,'tested_assets_copied_without_rebuild':True,'actual_R5_GUI':'PARTIAL_PASS hidden values, native colours and highlights; FAIL first selection/menu caption/checkmark/FullHD layout','actual_R6_GUI':'PENDING','actual_installation_performed':False,'checks':results,'native_hook_count':13,'position_hooks':6,'ownclub_SP_guards':'unchanged','new_popup_proof':str(R/'native-popup-property-proof.json'),'private_main_threads_never_resumed':True,'limitations':['Native targeted fixtures do not establish full GUI acceptance.','FullHD scrollbar/caption/checkmark/one-click role need real user UI test.','No active FM process writes or database changes.']}
(R/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('READY',C/'FmLauncher.exe',files['FmLauncher.dll']['sha256'],flush=True)
