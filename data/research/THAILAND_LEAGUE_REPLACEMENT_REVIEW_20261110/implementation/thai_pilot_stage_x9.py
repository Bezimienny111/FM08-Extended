"""Prepare TEST_X9 in a NEW isolated stock game root, without starting FM.
Source X8 and the running original game are read-only. Uses R3 validators.
"""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,os,shutil,subprocess,sys,uuid
from pathlib import Path
import xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('thai_package',HERE/'thai_pilot_package.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
ROOT=p.ROOT;GAME=ROOT/'playtests/THAILAND_T1';DB=ROOT/'Dane/db/TEST_X9';STOCK=Path('J:/FM08');INPUT=HERE/'input/X8-current-user-tested';PINS=HERE/'X8-user-tested-source-pins.json';STRUCTURE=HERE/'X8-user-tested-native-structure.json'
ROOTFILES={'fm.exe':p.EXE_SHA,'dbghelp.dll':'f089f6b1aa2a324603728c0453568201cb0ab6b8d3e8d6dcc2b000ad5cdfaba4','msvcr71.dll':'8094af5ee310714caebccaeee7769ffb08048503ba478b879edfef5f1a24fefe'}
PACKAGE=HERE/'package-r4-X8'
PLAN=HERE/'X9-copy-plan.json';RECEIPT=HERE/'X9-isolated-receipt.json'
def normalized(x):return {k.replace('\\','/'):v.lower()for k,v in x.items()}
def processes():
 script="Get-Process -Name fm -ErrorAction SilentlyContinue | Select-Object Id,Path | ConvertTo-Json -Compress"
 r=subprocess.run(['powershell.exe','-NoProfile','-Command',script],capture_output=True,text=True,errors='replace');p.require(r.returncode==0,'Cannot inspect running FM paths');raw=r.stdout.strip()
 if not raw:return []
 a=json.loads(raw);return a if isinstance(a,list)else[a]
def in_path(f,base):
 f=Path(f).resolve();base=Path(base).resolve();return f==base or base in f.parents
def guarded_destination(game=GAME,db=DB):
 p.require(Path(game).resolve()==GAME.resolve()and in_path(game,ROOT/'playtests'),'Unexpected isolated destination')
 p.require(Path(db).resolve()==DB.resolve()and in_path(db,ROOT/'Dane/db'),'Unexpected TEST_X9 path')
def no_target_process(procs,game=GAME):
 for q in procs:
  path=q.get('Path');p.require(path is not None,'Inaccessible FM path; cannot prove isolation');p.require(not in_path(path,game),'Isolated FM is running')
def protect_originals():
 result={}
 for src in [ROOT,STOCK]:
  for n,h in {'fm.exe':p.EXE_SHA,**p.ARCHIVES}.items():
   p.require(p.sha(src/n)==h,'Protected original changed: '+str(src/n));result[str(src/n)]=h
 return result

def copyplan():
 guarded_destination();p.require(not GAME.exists()and not DB.exists(),'Never overwrite an existing game root or TEST_X9');p.require(not PLAN.exists(),'Copy plan exists');protect=protect_originals();p.require(p.pins(INPUT)==normalized(p.read(PINS)),'Frozen X8 source mismatch');p.require(PACKAGE.exists(),'Build package-r4-X8 first');pkg=p.read(PACKAGE/'manifest.json');p.require(pkg['source_pins']==p.pins(INPUT),'Package source mismatch');files=[]
 for name,h in ROOTFILES.items():
  q=STOCK/name;p.require(p.sha(q)==h,'Stock binary changed');files.append(dict(source=str(q),relative=name,bytes=q.stat().st_size,sha256=h))
 for f in sorted((STOCK/'data').rglob('*')):
  if not f.is_file():continue
  p.require(not f.is_symlink()and not(getattr(f.stat(),'st_file_attributes',0)&0x400),'Reparse point in stock data');rel=str(f.relative_to(STOCK)).replace('\\','/');files.append(dict(source=str(f),relative=rel,bytes=f.stat().st_size,sha256=p.sha(f)))
 p.require(len(files)==527,'Stock inventory changed; review new count');total=sum(x['bytes']for x in files);dbbytes=sum(f.stat().st_size for f in INPUT.rglob('*')if f.is_file());procs=processes();no_target_process(procs)
 plan=dict(status='copy_plan_prepared_no_game_started',script_sha256=p.sha(__file__),package_manifest_sha256=p.sha(PACKAGE/'manifest.json'),target_game=str(GAME),target_db=str(DB),source_database=str(INPUT),source_database_pins=p.pins(INPUT),source_status=dict(SI=False,observed_DB_resave=True,new_career_observed=True,season=False),structure_sha256=p.sha(STRUCTURE),protected_originals=protect,files=files,stock_bytes=total,database_bytes=dbbytes,total_bytes=total+dbbytes,running_original_FM=procs,scope='NEW isolated game resources + NEW original userdata TEST_X9 only',userdata_mode='existing configured Dane fallback; CLI user_data_location not proven',excluded=['workspace/research/.git','FMExt/FMLoader/FMDumper','proxy d3d9/winmm/version DLL','old user games/graphics/skins/preferences','jre/editor data/editor exe','unproven msvcp71/unicows dependency'])
 p.write(PLAN,plan);print(json.dumps({'plan':str(PLAN),'files':len(files),'stock_bytes':total,'database_bytes':dbbytes,'MiB':round((total+dbbytes)/1048576,2),'running_FM':procs}))

def launch_scripts(root,receipt):
 root_ps=str(GAME).replace("'","''");receipt_ps=str(RECEIPT).replace("'","''")
 script="""param([switch]$VerifyOnly)
$ErrorActionPreference = 'Stop'
$ThaiGameRoot = 'GAME_ROOT'
$ThaiReceiptPath = 'RECEIPT_PATH'
try {
    $ThaiReceipt = Get-Content -LiteralPath $ThaiReceiptPath -Raw | ConvertFrom-Json
    if ($ThaiReceipt.status -ne 'prepared_not_launched') { throw 'Pilot receipt is not ready.' }
    foreach ($ThaiPin in $ThaiReceipt.startup_pins.PSObject.Properties) {
        $ThaiActual = (Get-FileHash -LiteralPath $ThaiPin.Name -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($ThaiActual -ne $ThaiPin.Value) { throw ('Pilot file changed: ' + $ThaiPin.Name) }
    }
    Write-Host 'TEST_X9: file pins PASS. Use NEW career, select TEST_X9 and Thailand.'
    $ThaiOtherGames = @(Get-Process -Name fm -ErrorAction SilentlyContinue)
    if ($VerifyOnly) {
        if ($ThaiOtherGames.Count -gt 0) { Write-Host 'FM is running: launch remains blocked until it closes.' }
        exit 0
    }
    if ($ThaiOtherGames.Count -gt 0) { throw 'Close the current FM08 first. This script never starts a second fm.exe.' }
    $ThaiEditors = @(Get-Process -Name 'data editor','editor' -ErrorAction SilentlyContinue)
    if ($ThaiEditors.Count -gt 0) { throw 'Close the SI data editor before starting the pilot.' }
    Start-Process -FilePath (Join-Path $ThaiGameRoot 'fm.exe') -WorkingDirectory $ThaiGameRoot -WindowStyle Normal
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    if (-not $VerifyOnly) { Read-Host 'Press Enter to close' | Out-Null }
    exit 1
}
""".replace('GAME_ROOT',root_ps).replace('RECEIPT_PATH',receipt_ps)
 (root/'StartThaiPilot.ps1').write_text(script,encoding='utf-8-sig')
 (root/'START_TEST_X9.cmd').write_text('@echo off\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0StartThaiPilot.ps1"\r\n',encoding='ascii')
 (root/'VERIFY_TEST_X9.cmd').write_text('@echo off\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0StartThaiPilot.ps1" -VerifyOnly\r\npause\r\n',encoding='ascii')
 helper=str(Path(__file__).resolve());receiptstr=str(RECEIPT)
 (root/'RESTORE_ORIGINAL_RESOURCES.cmd').write_text('@echo off\r\npython "'+helper+'" rollback --receipt "'+receiptstr+'"\r\npause\r\n',encoding='ascii')
 (root/'PILOT_README.txt').write_text('TEST_X9 / Thailand T1 technical pilot\n\nStart only with START_TEST_X9.cmd after closing the current FM08.\nEXE is original, no launcher hooks. Both Thai EFA archives exist only in this game root.\nDatabase: '+str(DB)+'\nOnly database name XML changed from frozen X8. Existing historical Thai clubs, not updated 2026 squads.\nSelect NEW career / TEST_X9 / Thailand. T1 has16 clubs,2rounds,30fixtures per club.\nNo relegation, cups or modern AFC update. Registration10 not implemented.\nDo not load the user holiday save here. Keep the normal original game for that save.\nVERIFY_TEST_X9.cmd checks files without starting FM.\nRESTORE_ORIGINAL_RESOURCES.cmd restores ONLY this isolated root archives, retaining DB and saves.\nReceipt and detailed evidence: '+str(RECEIPT)+'\n',encoding='utf-8')

def stage():
 plan=p.read(PLAN);p.require(plan['script_sha256']==p.sha(__file__),'Reviewed script changed');p.require(plan['package_manifest_sha256']==p.sha(PACKAGE/'manifest.json'),'Package changed');guarded_destination();p.require(not GAME.exists()and not DB.exists(),'Output exists');p.require(not RECEIPT.exists(),'Receipt exists');p.require(p.pins(INPUT)==plan['source_database_pins'],'X8 snapshot changed');p.require(p.sha(STRUCTURE)==plan['structure_sha256'],'Structure evidence changed');p.inventory(INPUT,STRUCTURE);protect_originals();before=processes();no_target_process(before)
 token=uuid.uuid4().hex;tmpgame=ROOT/'playtests'/('THAILAND_T1.staging-'+token);tmpdb=HERE/('TEST_X9-staging-'+token);p.require(in_path(tmpgame,ROOT/'playtests')and in_path(tmpdb,HERE),'Invalid staging scope');p.require(not tmpgame.exists()and not tmpdb.exists(),'Staging collision');tmpgame.mkdir(parents=True)
 for f in plan['files']:
  src=Path(f['source']);p.require(p.sha(src)==f['sha256'],'Stock changed after copy plan');dst=tmpgame/f['relative'];p.require(in_path(dst,tmpgame),'Copy target escaped staging');dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);p.require(p.sha(dst)==f['sha256'],'Copied resource pin mismatch')
 backup=tmpgame/'pilot-original-resources';backup.mkdir();archive_steps=[];profile=next(x for x in p.read(PACKAGE/'manifest.json')['profiles']if x['profile']=='T1')
 for i,a in enumerate(profile['archives']):
  rel=str(Path(a['source']).relative_to(ROOT));dst=tmpgame/rel;prepared=Path(a['output']);p.require(p.sha(dst)==a['source_sha256']and p.sha(prepared)==a['output_sha256'],'EFA stage pin mismatch');save=backup/('archive-'+str(i)+'.efa');shutil.copy2(dst,save);shutil.copyfile(prepared,dst);p.require(p.sha(dst)==a['output_sha256'],'Derived EFA after copy mismatch');archive_steps.append(dict(relative=rel,before_sha256=a['source_sha256'],after_sha256=a['output_sha256'],backup_relative=str(save.relative_to(tmpgame))))
 shutil.copytree(INPUT,tmpdb);p.require(p.pins(tmpdb)==plan['source_database_pins'],'DB staging copy mismatch');xmls=list(tmpdb.glob('*.xml'));p.require(len(xmls)==1,'Ambiguous DB metadata');tree=ET.parse(xmls[0]);found=0
 for v in tree.getroot().iter('string'):
  if v.get('id')=='name':v.set('value','TEST_X9');found+=1
  if v.get('id')=='description':v.text='TEST_X9'
 p.require(found==1,'Database name metadata absent or duplicated');old=xmls[0];old.unlink();tree.write(tmpdb/'TEST_X9.xml',encoding='utf-8',xml_declaration=True)
 dbpins=p.pins(tmpdb)
 for n,h in plan['source_database_pins'].items():
  if not n.lower().endswith('.xml'):p.require(dbpins[n]==h,'Unexpected DB modification: '+n)
 startup={str(GAME/'fm.exe'):p.EXE_SHA}
 for a in archive_steps:startup[str(GAME/a['relative'])]=a['after_sha256']
 for n,h in dbpins.items():startup[str(DB/n)]=h
 receipt=dict(status='prepared_not_launched',profile='T1',database='TEST_X9',game_root=str(GAME),database_root=str(DB),copy_plan_sha256=p.sha(PLAN),script_sha256=p.sha(__file__),source_database=str(INPUT),source_database_pins=plan['source_database_pins'],source_status=plan['source_status'],database_pins=dbpins,archive_steps=archive_steps,startup_pins=startup,files_copied=len(plan['files']),copied_bytes=plan['total_bytes'],running_FM_before=before,EXE_original=True,engine_patched=False,hooks=False,SI=False,new_career=False,fixtures=False,save_load=False,season=False,AFC=False)
 launch_scripts(tmpgame,receipt)
 # Both resolved directory move endpoints are checked before these two new outputs are published.
 guarded_destination();p.require(in_path(tmpgame,ROOT/'playtests')and in_path(tmpdb,HERE),'Staging endpoints changed');p.require(not DB.exists()and not GAME.exists(),'Late target collision');DB.parent.mkdir(parents=True,exist_ok=True);os.rename(tmpdb,DB);os.rename(tmpgame,GAME)
 p.require(p.pins(DB)==dbpins,'Published DB pins');p.require(p.pins(INPUT)==plan['source_database_pins'],'Protected X8 changed');protect_originals();after=processes();no_target_process(after);receipt['running_FM_after']=after;receipt['stock_file_pins']={str(GAME/x['relative']):x['sha256']for x in plan['files']if x['relative']not in{a['relative'].replace('\\','/')for a in archive_steps}};p.write(RECEIPT,receipt)
 for path,h in startup.items():p.require(p.sha(path)==h,'Final startup pin mismatch')
 print(json.dumps({'status':receipt['status'],'game_root':str(GAME),'db':str(DB),'running_FM_untouched':after,'start':str(GAME/'START_TEST_X9.cmd')}))

def rollback(args):
 path=p.inside(args.receipt,HERE);r=p.read(path);p.require(r['game_root']==str(GAME)and r['status']in['prepared_not_launched','runtime_failed_missing_discipline'],'Unexpected receipt');no_target_process(processes())
 for a in r['archive_steps']:
  dst=GAME/a['relative'];src=GAME/a['backup_relative'];p.require(in_path(dst,GAME)and in_path(src,GAME),'Rollback scope');p.require(p.sha(dst)==a['after_sha256']and p.sha(src)==a['before_sha256'],'Rollback external change')
 for a in r['archive_steps']:shutil.copyfile(GAME/a['backup_relative'],GAME/a['relative']);p.require(p.sha(GAME/a['relative'])==a['before_sha256'],'Rollback verification')
 r['status']='isolated_archives_restored_new_DB_retained';p.write(path,r);protect_originals();print('Isolated original archives restored; all DBs and saves retained.')

def selftest():
 tests=[]
 for name,call in [('escape game root',lambda:guarded_destination(ROOT)),('escape database',lambda:guarded_destination(GAME,ROOT/'Dane/db/TEST_X8')),('block isolated active FM',lambda:no_target_process([{'Id':1,'Path':str(GAME/'fm.exe')}]))]:
  try:call()
  except ValueError:tests.append({'test':name,'passed':True})
  else:raise ValueError('Guard failed: '+name)
 no_target_process([{'Id':8468,'Path':str(ROOT/'fm.exe')}]);tests.append({'test':'permit read-only staging while other root FM runs','passed':True});p.write(HERE/'X9-scope-tests.json',{'status':'PASS','checks':tests});print('PASS4 scoped staging guards')

def cli():
 q=argparse.ArgumentParser();sub=q.add_subparsers(dest='cmd',required=True)
 for n,f in [('plan',copyplan),('stage',stage),('selftest',selftest)]:x=sub.add_parser(n);x.set_defaults(run=lambda a,f=f:f())
 x=sub.add_parser('rollback');x.add_argument('--receipt',required=True);x.set_defaults(run=rollback);a=q.parse_args();a.run(a)
if __name__=='__main__':cli()
