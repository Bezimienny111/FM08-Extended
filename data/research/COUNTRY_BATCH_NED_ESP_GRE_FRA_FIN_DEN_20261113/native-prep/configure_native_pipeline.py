from pathlib import Path
import json,hashlib,shutil,subprocess,ast
B=Path(__file__).resolve().parent;R=B.parents[1];OLD=R/'COUNTRY_BATCH_IDN_IND_HKG_20261112';T=B/'tools';ROOT=Path('J:/FM08dev')
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def edit(s,a,b):
 assert a in s,a
 return s.replace(a,b)
seed=OLD/'tools/roster-build-manifest.json';build=read(seed)
worker=(OLD/'tools/ApplyPolandRosterBatch-X17.cs').read_text(encoding='utf-8-sig')
worker=edit(worker,'x17133','x18602');worker=edit(worker,'x10?133:','x10?602:');worker=edit(worker,'idn-ind-hkg-x17','ned-esp-gre-fra-fin-den-x18');worker=edit(worker,'new[]{58,57,56}','new[]{138,142,143,146,158,170,127}');worker=edit(worker,'Wrong X17 country set','Wrong X18 country set')
worker=edit(worker,'((cp["Country"]=="Indonesia"&&ci==58)||(cp["Country"]=="India"&&ci==57)||(cp["Country"]=="Hong Kong"&&ci==56))','((cp["Country"]=="Netherlands"&&ci==158)||(cp["Country"]=="Spain"&&(ci==170||ci==127))||(cp["Country"]=="Greece"&&ci==146)||(cp["Country"]=="France"&&ci==143)||(cp["Country"]=="Finland"&&ci==142)||(cp["Country"]=="Denmark"&&ci==138))')
worker=worker.replace('X17','X18').replace('x10?1710000000:','x10?1712000000:').replace('x10?1712000000:x7?1696000000:','x10?1714000000:x7?1696000000:').replace('x10?1818000000:','x10?1819000000:').replace('x10?1819000000:x7?1809000000:','x10?1820000000:x7?1809000000:')
# Both pools remain checked by IdPool against physical PEOPLE/SERVER/CLIENT bytes.
assert 'new IdPool(x10?1712000000:'in worker and ',x10?1714000000:'in worker
assert 'new IdPool(x10?1819000000:'in worker and ',x10?1820000000:'in worker
wp=T/'ApplyPolandRosterBatch-X18.cs';wp.write_text(worker,encoding='utf-8')
wrapper=(OLD/'tools/ApplyX17RosterBatch.cs').read_text().replace('X17','X18').replace('x17133','x18602');qp=T/'ApplyX18RosterBatch.cs';qp.write_text(wrapper,encoding='utf-8')
sources=[Path(p)for p in build['sources']if 'ApplyPolandRosterBatch-X17.cs'not in p and 'ApplyX17RosterBatch.cs'not in p]+[wp,qp]
for p in sources[:-2]:assert h(p)==build['sources'][str(p)],('Seed dependency changed',p)
assert h(T/'FM08_Database_Editor.exe')==build['outputs']['FM08_Database_Editor.exe']
exe=T/'ApplyX18RosterBatch.exe';assert not exe.exists()
cmd=['C:/Windows/Microsoft.NET/Framework/v4.0.30319/csc.exe','/nologo','/optimize+','/platform:x64','/target:exe','/main:ApplyX18RosterBatch','/out:'+str(exe),'/r:System.Windows.Forms.dll','/r:System.Drawing.dll','/r:System.Xml.dll','/r:System.Web.Extensions.dll','/r:'+str(T/'FM08_Database_Editor.exe')]+list(map(str,sources))
z=subprocess.run(cmd,capture_output=True,text=True,timeout=180);(T/'roster-build.log').write_text(z.stdout+z.stderr,encoding='utf-8');assert z.returncode==0,z.stdout+z.stderr
dump(T/'roster-build-manifest.json',dict(status='X18_SCOPE_ONLY_COMPILED_FIXED_EDITOR_REUSED',scope='x18602',core_clubs=602,countries=[138,142,143,146,158,170,127],sources={str(p):h(p)for p in sources},outputs={exe.name:h(exe),'FM08_Database_Editor.exe':h(T/'FM08_Database_Editor.exe')},new_player_UID_range=[1712000000,1714000000],loan_UID_range=[1819000000,1820000000],main_editor_rebuilt=False,launcher_or_engine_rebuilt=False,seed_manifest=str(seed),seed_manifest_sha256=h(seed)))
for f in ['verify_roster.py','apply_legacy_ratings.py','resolve_typed_contract_boundaries.ps1']:
 s=(OLD/f).read_text(encoding='utf-8-sig').replace('COUNTRY_BATCH_IDN_IND_HKG_20261112','COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep')
 if f=='apply_legacy_ratings.py':s=s.replace("B/'audit-tools/ApplyVerifiedNativeSquads.exe'","B/'tools/ApplyVerifiedNativeSquads.exe'")
 (B/f).write_text(s,encoding='utf-8')
s=(OLD/'apply_rosters.py').read_text(encoding='utf-8').replace('ApplyX17RosterBatch.exe','ApplyX18RosterBatch.exe').replace('Wrong X17 country set','Wrong X18 country set').replace("d=B/'pilot-r2'","d=B/'pilot'").replace('timeout=1200','timeout=3600')
(B/'apply_rosters.py').write_text(s,encoding='utf-8')
print('COMPILED_X18_SCOPE_ONLY; copied strict actor inverse/sentinel verifier, rating typedactor patch and pilot/full driver',flush=True)
