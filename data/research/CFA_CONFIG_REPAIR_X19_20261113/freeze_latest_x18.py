from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,subprocess,sys
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent;X=R/'COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep';SRC=ROOT/'Dane/db/TEST_X18';DST=B/'input/X18-after-SI-failed'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pins(d):return{str(p.relative_to(d)):sha(p)for p in sorted(d.rglob('*'))if p.is_file()}
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not any(p.exists()for p in[ROOT/'Dane/db/TEST_X19',ROOT/'Dane/db/TEST_X19.xml',ROOT/'wydania/TEST_X19.zip',DST]);before=pins(SRC);shutil.copytree(SRC,DST);copied=pins(DST);after=pins(SRC);assert before==copied==after
archive=ROOT/'wydania/TEST_X18.zip';dump(B/'source-freeze.json',dict(status='PASS_LATEST_PUBLIC_X18_SI_SOURCE_COPY_AFTER_IDENTICAL',source=str(SRC),frozen=str(DST),hashes=before,source_before=before,copied=copied,source_after=after,source_SI='USER_SAVED_POST_SI',source_new_career='FAILED_CFA_ARRAY_REMOVE_RANGE',source_accepted_for_next_country_import=False,original_X18_ZIP=str(archive),original_X18_ZIP_SHA256=sha(archive),DAT_source='latest user SI public X18; not raw rated-db',game_access=False,created_at=datetime.now(timezone.utc).isoformat()))
print('FROZEN_LATEST_X18_SI',len(before),'files BEFORE=COPY=AFTER; X18ZIP preserved',flush=True)
T=X/'tools';args=[T/'ExportWholeNativeStructure.exe',DST,T/'FM08_Database_Editor.exe',B/'source-native-structure.json'];z=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300);(B/'source-export.log').write_text(z.stdout+z.stderr,encoding='utf-8');assert z.returncode==0,z.stderr[-1500:];assert pins(SRC)==before and pins(DST)==before;print('SOURCE_EXPORT_PASS',flush=True)
