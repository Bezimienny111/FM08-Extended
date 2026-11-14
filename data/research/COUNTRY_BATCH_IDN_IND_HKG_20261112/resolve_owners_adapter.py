from pathlib import Path
import sys,hashlib,json
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev'); R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent
seed=R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/x10_owners.py'
sys.path.insert(0,str(seed.parent));sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
code=seed.read_text(encoding='utf-8').replace('str(p.relative_to(B))','str(p.resolve())').replace("nation_alias={","nation_alias={'Hongkong':'Hong Kong',")
ns={'__name__':'x17_configured_owner_reader','__file__':str(seed)}
exec(compile(code,str(seed),'exec'),ns);ns['B']=B;ns['S']=B/'sources';ns['col'].B=B;ns['col'].S=B/'sources'
ns['owners']()
(B/'owner-adapter-pins.json').write_text(json.dumps({'seed':str(seed),'seed_sha256':hashlib.sha256(seed.read_bytes()).hexdigest(),'adapter_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'native_writes':False},indent=2),encoding='utf-8')
