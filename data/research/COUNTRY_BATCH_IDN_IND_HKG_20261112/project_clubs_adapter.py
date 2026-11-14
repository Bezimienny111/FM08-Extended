from pathlib import Path
import sys,inspect,json,hashlib
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent
seed=R/'POLAND_GAPS_IMPORT_PACKAGE_20261111/prepare_package.py'
ns={'__name__':'x17_project_configuration','__file__':str(seed)}
exec(compile(seed.read_text(encoding='utf-8'),str(seed),'exec'),ns);ns['B']=B;ns['SRC']=B
code=inspect.getsource(ns['project']);assert '==292'in code and 'nextuid=1800140001'in code
code=code.replace('==292','==133').replace('1800140001','1800200001').replace("'X11_verified'","'X16_postSI_verified'")
prior=json.loads((B/'rejected-first-structure-inputs/club-UID-projection.json').read_text(encoding='utf-8'))
prioruids={str(r['TMID']):int(r['ClubUID'])for r in prior['rows']if r['IsNew']};assert len(prioruids)==57
ns['PRIOR_NEW_UIDS']=prioruids
code=code.replace('nextuid=1800200001','nextuid='+str(max(prioruids.values())+1))
needle='uid=nextuid;nextuid+=1;assert uid not in useduids;useduids.add(uid);team=ti;ti+=1;family=parent[\'FamilyIndex\']if parent else fi'
replacement='uid=PRIOR_NEW_UIDS.get(c[\'TMID\']);\n   if uid is None:uid=nextuid;nextuid+=1\n   assert uid not in useduids;useduids.add(uid);team=ti;ti+=1;family=parent[\'FamilyIndex\']if parent else fi'
assert needle in code
code=code.replace(needle,replacement)

exec(compile(code,'configured_X17_project','exec'),ns);ns['project']();ns['project_owners']()
import csv
fp=B/'foreign-owner-map.csv'
with fp.open(encoding='utf-8-sig',newline='') as f: rr=list(csv.DictReader(f))
if rr and all(not r['TMID'] for r in rr):
 with fp.open('w',encoding='utf-8-sig',newline='') as f: csv.DictWriter(f,fieldnames=list(rr[0])).writeheader()
(B/'projection-tool-pins.json').write_text(json.dumps({'seed':str(seed),'seed_sha256':hashlib.sha256(seed.read_bytes()).hexdigest(),'configured_projection_sha256':hashlib.sha256(code.encode()).hexdigest(),'scope':'133clubs;57newfirstTEAM/FAMILY; noforeignnew; sourceactualTEAMtail kept separate','native_write':False},indent=2),encoding='utf-8')
