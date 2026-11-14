from pathlib import Path
import csv,hashlib,json,shutil,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_PROTOTYPE_R8_20261107'
RUNTIME=OUT/'runtime'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest().upper()
def save(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
m=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
assert m['status']=='database_and_resources_built'
assert not RUNTIME.exists(),'Refuse to overwrite runtime'
assert RUNTIME.resolve().parent==OUT.resolve()
# Independent reader results must differ only in these 18 division assignments.
def snapshot(p):
 with p.open(encoding='utf-8-sig',newline='') as f:
  return {int(x['ClubUID']):x for x in csv.DictReader(f)}
before=snapshot(ROOT/'FmLauncher/data/research/POLAND_II_LIGA_CLUB_AUDIT_20261107/802-snapshot.csv')
after=snapshot(OUT/'native-after-clubs.csv')
assert set(before)==set(after) and len(after)==23394
selected=set(m['participant_uids']);changes=[]
for uid,a in after.items():
 b=before[uid]
 diff=[k for k in b if k!='SourceServerSHA256' and b[k]!=a[k]]
 if uid in selected:
  assert diff==['CurrentDivisionIndex'],(uid,diff)
  assert b['CurrentDivisionIndex']=='141' and a['CurrentDivisionIndex']=='1332'
  changes.append(uid)
 else:assert not diff,(uid,diff)
counts={str(i):sum(x['CurrentDivisionIndex']==str(i) for x in after.values()) for i in (139,140,141,1332)}
assert counts=={'139':16,'140':18,'141':100,'1332':18}
source_files=[p for p in (ROOT/'data').rglob('*') if p.is_file()]
assert not any(p.is_symlink() for p in (ROOT/'data').rglob('*')),'No linked game data'
print(json.dumps({'step':'copy_private_runtime','source_files':len(source_files),'bytes':sum(p.stat().st_size for p in source_files),'division_counts':counts}),flush=True)
RUNTIME.mkdir()
for name in ('fm.exe','dbghelp.dll','msvcp71.dll','msvcr71.dll','unicows.dll'):shutil.copy2(ROOT/name,RUNTIME/name)
shutil.copytree(ROOT/'data',RUNTIME/'data')
private_archive=RUNTIME/'data/updates/update-802/data/comps.efa'
assert sha(private_archive)==m['protected_source_hashes']['data\\updates\\update-802\\data\\comps.efa']
shutil.copy2(OUT/'resources/comps.efa',private_archive)
fileproof=[]
for i,p in enumerate(source_files):
 rel=p.relative_to(ROOT)
 q=RUNTIME/rel
 old=sha(p);new=sha(q)
 changed=str(rel)=='data\\updates\\update-802\\data\\comps.efa'
 assert changed or old==new,str(rel)
 assert not changed or new==sha(OUT/'resources/comps.efa')
 fileproof.append(dict(path=str(rel),source_sha256=old,runtime_sha256=new,modified_in_runtime=changed))
 if i and i%100==0:print(json.dumps({'step':'hash_private_copy','files':i}),flush=True)
for rel,expected in m['protected_source_hashes'].items():assert sha(ROOT/rel)==expected,rel
for rel,expected in m['source_database_hashes'].items():assert sha(ROOT/'data/updates/update-802/db/802'/rel)==expected,rel
for name in ('fm.exe','dbghelp.dll','msvcp71.dll','msvcr71.dll','unicows.dll'):assert sha(ROOT/name)==sha(RUNTIME/name)
report=dict(status='private_runtime_verified',runtime=str(RUNTIME),files_copied=len(source_files),data_bytes=sum(p.stat().st_size for p in source_files),originals_unchanged=True,original_exe_hash=sha(RUNTIME/'fm.exe'),runtime_data_differences=['data/updates/update-802/data/comps.efa'],database_native_reader=dict(clubs=23394,changed_clubs=len(changes),only_current_division_changed=True,division_counts=counts),data_files=fileproof)
save(OUT/'runtime-verification.json',report)
m.update(status='private_runtime_built',runtime_verified=True,native_club_reader_verified=True,division_counts=counts)
save(OUT/'manifest.json',m)
print(json.dumps({'status':report['status'],'source_files':len(source_files),'division_counts':counts,'originals_unchanged':True}),flush=True)
