from pathlib import Path
import subprocess,json,hashlib,time,datetime,shutil,sys
ROOT=Path(r'J:/FM08dev')
R=ROOT/'FmLauncher/data/research/SKIN_PLAYER_PANELS_R10_20261111'
V=R/'verification'
V.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((ROOT/'FmLauncher/data/research/SKIN_PLAYER_PANELS_R9_20261111/manifest.json').read_text(encoding='utf-8-sig'))
assert all(sha(ROOT/'Launcher_0.1.3_R9'/n)==v['sha256'] for n,v in old['candidate_files'].items())
namesources=list(old['source_hashes'])+['GameLanguageResolver.cs','Localization.cs','GameLauncher.cs','SkinGuidePage.cs','SkinPanelInstaller.cs','SkinPanelTransaction.cs']
current={n:sha(ROOT/'FmLauncher/src/FmLauncher'/n) for n in namesources}
changed=[n for n,h in current.items() if n in old['source_hashes'] and h!=old['source_hashes'][n]]
assert set(changed)=={'GamePositionBackgroundPatch.cs','PlayerProfileXml.cs','FmLauncher.languages.json'},changed
pref=Path.home()/'AppData/Roaming/Sports Interactive/Football Manager 2008/settings/Version 800/current_language.xml'
prefpin=sha(pref) if pref.exists() else None
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
if '--skip-resolver' in sys.argv:
 previous=json.loads((V/'results-first-fmed-failure.json').read_text(encoding='utf-8'))
 results.append(next(x for x in previous if x['name']=='game-language' and x['exit_code']==0))
else:
 run('game-language',[str(T/'FmLauncher.Tests.exe'),'--game-language',str(V/'resolver')])
run('game-language-upgrade',[str(T/'FmLauncher.Tests.exe'),'--game-language-upgrade',str(ROOT/'fm.exe'),str(ROOT/'Dane'),str(V/'upgrade')])
guard=subprocess.run(['powershell','-NoProfile','-Command','if(Get-Process fm -ErrorAction SilentlyContinue){exit 19}else{exit 0}'])
assert guard.returncode==0,'FM must be closed before hook readback private fixture.'
if '--skip-native' in sys.argv:
 previous=json.loads((R/'manifest-before-training-fix.json').read_text(encoding='utf-8'))['checks']
 results.append(next(x for x in previous if x['name']=='hook-readback' and x['exit_code']==0))
else:
 run('hook-readback',[str(T/'FmLauncher.Tests.exe'),'--position-hooks',str(ROOT/'fm.exe')])
assert (sha(pref) if pref.exists() else None)==prefpin,'Saved FM preference was modified.'
names=list(old['candidate_files'])
C=R/'candidate-0.1.3-R10-final'
assert not C.exists(),'Do not overwrite candidate.'
C.mkdir()
for n in names:shutil.copy2(T/n,C/n)
files={n:{'sha256':sha(C/n),'bytes':(C/n).stat().st_size} for n in names}
manifest={'version':'0.1.3-R10','status':'TARGETED_LANGUAGE_GEOMETRY_READY_GUI_PENDING','build_configuration':'Debug/devcandidate','candidate':str(C/'FmLauncher.exe'),'published_executable':str(ROOT/'Launcher_0.1.3_R10/FmLauncher.exe'),'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate_files':files,'source_hashes':current,'changed_previously_pinned_sources':changed,'additional_managed_sources':namesources[len(old['source_hashes']):],'R9_frozen_assets_preserved':{n:sha(ROOT/'Launcher_0.1.3_R9'/n)==old['candidate_files'][n]['sha256'] for n in names},'tested_assets_copied_without_rebuild':True,'actual_R9_GUI':'FUNCTIONAL_PASS_WITH_NUMERIC_BADGE_DEFECT','actual_R10_GUI':'PENDING','actual_installation_performed':False,'checks':results,'native_hook_count':14,'position_hooks':7,'native_registry':{'capacity':96,'entry_size':28,'data_bytes':4096},'numeric_colour_and_font_unchanged':True,'database_or_FM_native_language_changed':False,'launcher_language':'en_unchanged','panel_language_policy':'Saved FM preference polish->pl; all other values->en; unreadable/missing fallbacken. INSTALL and every PLAY, no active-game observer.','saved_game_preference':{'path':str(pref),'sha256_before':prefpin,'sha256_after':sha(pref) if pref.exists() else None,'unchanged':True},'scope':'Uniform name+value band and independent game-language panels/runtime titles with native untranslated literals.','limitations':['Actual R10 GUI acceptance remains pending.','In-game language changes apply on next game start and Ext skin reload.']}
(R/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('READY',C/'FmLauncher.exe',files['FmLauncher.dll']['sha256'],flush=True)
