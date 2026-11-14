from pathlib import Path
import subprocess,json,hashlib,time,datetime,shutil
ROOT=Path(r'J:/FM08dev')
R=ROOT/'FmLauncher/data/research/SKIN_PLAYER_PANELS_R7_20261111'
V=R/'verification'
V.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((ROOT/'FmLauncher/data/research/SKIN_PLAYER_PANELS_R6_20261111/manifest.json').read_text(encoding='utf-8-sig'))
assert all(sha(ROOT/'Launcher_0.1.3_R6'/n)==v['sha256'] for n,v in old['candidate_files'].items())
current={n:sha(ROOT/'FmLauncher/src/FmLauncher'/n) for n in old['source_hashes']}
changed=[n for n,h in current.items() if h!=old['source_hashes'][n]]
assert changed==['PlayerProfileXml.cs'],('Only cosmetic XML change expected',changed)
results=[]
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
run('build',['dotnet','build',str(ROOT/'FmLauncher/tests/FmLauncher.Tests/FmLauncher.Tests.csproj'),'--no-restore','-o',str(T),'-v:minimal'])
run('installed-upgrade',[str(T/'FmLauncher.Tests.exe'),'--installed-profile-upgrade',str(ROOT/'fm.exe'),str(ROOT/'Dane'),str(V/'upgrade')])
names=list(old['candidate_files'])
C=R/'candidate-0.1.3-R7'
assert not C.exists(),'Do not overwrite candidate.'
C.mkdir()
for n in names:shutil.copy2(T/n,C/n)
files={n:{'sha256':sha(C/n),'bytes':(C/n).stat().st_size} for n in names}
manifest={'version':'0.1.3-R7','status':'MANAGED_UPGRADE_PASS_CANDIDATE_READY_GUI_PENDING','build_configuration':'Debug/devcandidate','candidate':str(C/'FmLauncher.exe'),'published_executable':str(ROOT/'Launcher_0.1.3_R7/FmLauncher.exe'),'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate_files':files,'source_hashes':current,'changed_application_sources':changed,'R6_frozen_assets_preserved':{n:sha(ROOT/'Launcher_0.1.3_R6'/n)==old['candidate_files'][n]['sha256'] for n in names},'tested_assets_copied_without_rebuild':True,'actual_R6_GUI':'USER_ACCEPTED_LAYOUT_AND_FIRST_SELECTION','actual_R7_GUI':'PENDING','actual_installation_performed':False,'checks':results,'native_hooks_retested':False,'native_hooks_unchanged':True,'CA_PA_and_database_changed':False,'language':'pl_unchanged','scope':'Cosmetic XML only: hidden block immediately below native attributes; legend skin-styled header/frame.','limitations':['Actual R7 cosmetic appearance requires GUI confirmation.','No private FM/native fixtures were run for this cosmetic change.']}
(R/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('READY',C/'FmLauncher.exe',files['FmLauncher.dll']['sha256'],flush=True)
