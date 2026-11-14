from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,subprocess,sys
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent;R=B.parents[1];ROOT=Path('J:/FM08dev');OLD=R/'COUNTRY_BATCH_BLR_BEL_AUT_AUS_ARG_20261114/native-prep';SRC=ROOT/'Dane/db/TEST_X22';DST=B/'input/X22-after-SI'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pins(p):return{str(f.relative_to(p)):sha(f)for f in sorted(p.rglob('*'))if f.is_file()}
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not DST.exists();proc=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,text=True,errors='replace',check=True);assert 'data editor.exe' not in proc.stdout.lower(),'Editor must be closed; FM may keep testing immutable database';before=pins(SRC);shutil.copytree(SRC,DST);copied=pins(DST);after=pins(SRC);assert before==copied==after
receipt=dict(status='PASS_SOURCE_COPY_AFTER_IDENTICAL',source=str(SRC),source_original=str(SRC),frozen=str(DST),hashes=before,source_before=before,copied=copied,source_after=after,source_SI='USER_REPORTED_WORKING',source_new_career='USER_REPORTED_WORKING',source_season='USER_AUTHORIZED_PROCEED_WHILE_LONG_TEST_CONTINUES_TARGET_2010',source_open_issue='User says X22 looks OK and explicitly authorizes England build while long test continues. Do not claim completed2010season test.',game_access=False,created_at=datetime.now(timezone.utc).isoformat())
dump(B/'source-freeze.json',receipt)
T=B/'tools';T.mkdir();files=[OLD/'tools/FM08_Database_Editor.exe',OLD/'tools/ApplyVerifiedNativeSquads.exe',OLD/'tools/AuditNativeFutureTransfers.exe',R/'SWEDEN_SELECTION_REPAIR_X4_20261110/tools/ExportWholeNativeStructure.exe']
for f in files:shutil.copy2(f,T/f.name)
dump(T/'pins.json',{f.name:sha(f)for f in T.iterdir()if f.is_file()})
print('FREEZE_PASS',len(before),'files;229NATIONtool copied; source unchanged',flush=True)
for label,args in [('source-audit',[T/'ApplyVerifiedNativeSquads.exe',T/'FM08_Database_Editor.exe',DST,B/'audit','--audit']),('native-structure',[T/'ExportWholeNativeStructure.exe',DST,T/'FM08_Database_Editor.exe',B/'native-structure.json'])]:
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=1200);(B/(label+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8');assert p.returncode==0,(label,p.stderr[-1500:]);print(label,'PASS',p.stdout[-300:],flush=True)
assert pins(DST)==before and pins(SRC)==before
print('SOURCE_AUDIT_STRUCTURE_READY',flush=True)