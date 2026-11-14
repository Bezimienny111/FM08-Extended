from pathlib import Path
import sys,hashlib,json,shutil,subprocess
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent
source=R/'POLAND_GAPS_IMPORT_PACKAGE_20261111'
model=(source/'rating_model_v2.py').read_text(encoding='utf-8').replace('COUNTRY_ADJUSTMENT={"Portugal":-5,"Norway":-15,"Peru":-30,"Poland":-15}','COUNTRY_ADJUSTMENT={"Portugal":-5,"Norway":-15,"Peru":-30,"Poland":-15,"Germany":0,"Mexico":-10,"Malaysia":-40}')
assert '"Germany":0'in model
(B/'rating_model_v2.py').write_text(model,encoding='utf-8')
p=(source/'prepare_players.py').read_text(encoding='utf-8').replace("SRC=R/'PORTUGAL_PERU_NORWAY_POLAND_PREP_20261111'","SRC=B").replace("REF='2026-11-11'","REF='2026-11-12'").replace("['Portugal','Norway','Peru']","['Germany','Mexico','Malaysia']").replace("target_country_indices=[162,160,194]","target_country_indices=[145,109,70,54]").replace("scope_id='por-per-nor-pol-gaps-x14'","scope_id='ger-mex-mas-x15'").replace("str(ROOT/'Dane/db/TEST_X14')","str(B/'roster-db')").replace("TM_snapshot_2026_11_11","TM_snapshot_2026_11_12")
needle="shared.PRIOR=[R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/prepared',"
assert needle in p;p=p.replace(needle,"shared.PRIOR=[R/'POLAND_GAPS_IMPORT_PACKAGE_20261111/prepared',R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/prepared',")
(B/'prepare_players.py').write_text(p,encoding='utf-8')
T=B/'tools';T.mkdir(exist_ok=True);editor=source/'tools/FM08_Database_Editor.exe';shutil.copyfile(editor,T/editor.name)
s=(source/'tools/ApplyPolandRosterBatch-X14.cs').read_text(encoding='utf-8')
assert 'scope=="x14292"'in s and 'expectedClubs=x10?292:'in s
s=s.replace('scope=="x14292"','scope=="x15215"').replace('expectedClubs=x10?292:','expectedClubs=x10?215:').replace('por-per-nor-pol-gaps-x14','ger-mex-mas-x15').replace('new[]{162,160,194}','new[]{145,109,70,54}')
old='((cp["Country"]=="Portugal"&&ci==162)||(cp["Country"]=="Norway"&&ci==160)||(cp["Country"]=="Peru"&&ci==194))'
new='((cp["Country"]=="Germany"&&ci==145)||(cp["Country"]=="Mexico"&&ci==109)||(cp["Country"]=="Malaysia"&&(ci==70||ci==54)))'
assert old in s;s=s.replace(old,new)
for a,z in [('x10?1702000000:','x10?1706000000:'),('x10?1704000000:','x10?1708000000:'),('x10?1814000000:','x10?1816000000:'),('x10?1815000000:','x10?1817000000:')]:
 assert a in s;s=s.replace(a,z)
s=s.replace('X14','X15');worker=T/'ApplyPolandRosterBatch-X15.cs';worker.write_text(s,encoding='utf-8')
wrapper=(source/'tools/ApplyX14RosterBatch.cs').read_text(encoding='utf-8').replace('X14','X15').replace('x14292','x15215');wrap=T/'ApplyX15RosterBatch.cs';wrap.write_text(wrapper,encoding='utf-8')
d=ROOT/'FM08-Database-Tools/scratch';sources=list(d.glob('*NativeSquads.cs'))+[d/'PolandSquadsN4.cs',d/'RepairNativeContracts.cs',worker,wrap]
args=['C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe','/nologo','/optimize+','/platform:x64','/target:exe','/main:ApplyX15RosterBatch','/out:'+str(T/'ApplyX15RosterBatch.exe'),'/r:System.Windows.Forms.dll','/r:System.Drawing.dll','/r:System.Xml.dll','/r:System.Web.Extensions.dll','/r:'+str(T/editor.name)]+list(map(str,sources))
z=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace');(T/'roster-build.log').write_text(z.stdout+z.stderr,encoding='utf-8');assert z.returncode==0,z.stdout+z.stderr
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(T/'roster-build-manifest.json').write_text(json.dumps(dict(status='scope_adapter_compiled_main_editor_reused',scope='x15215',countries=[145,109,70,54],core_clubs=215,foreign_entrant='BruneiDPMMinMalaysia',source_editor=str(editor),source_editor_sha256=H(editor),main_editor_rebuilt=False,source_worker=str(source/'tools/ApplyPolandRosterBatch-X14.cs'),source_worker_sha256=H(source/'tools/ApplyPolandRosterBatch-X14.cs'),sources={str(p):H(p)for p in sources},outputs={p.name:H(p)for p in[T/editor.name,T/'ApplyX15RosterBatch.exe']},new_player_UID_range=[1706000000,1708000000],loan_UID_range=[1816000000,1817000000]),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Configured existing v2 ratings and X15 scope adapter; editor reused; no DAT changed',flush=True)
