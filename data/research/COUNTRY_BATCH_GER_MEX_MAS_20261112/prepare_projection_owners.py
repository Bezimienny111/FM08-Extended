from pathlib import Path
import sys,importlib.util
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
source=R/'POLAND_GAPS_IMPORT_PACKAGE_20261111/prepare_package.py'
s=source.read_text(encoding='utf-8')
s=s.replace("B=R/'POLAND_GAPS_IMPORT_PACKAGE_20261111';SRC=R/'PORTUGAL_PERU_NORWAY_POLAND_PREP_20261111'","B=R/'COUNTRY_BATCH_GER_MEX_MAS_20261112';SRC=B")
s=s.replace('==292','==215').replace('nextuid=1800140001','nextuid=1800160001').replace('UIDrange=[1800140001,','UIDrange=[1800160001,')
ns={'__name__':'configured_x15_preparation','__file__':str(source)};exec(compile(s,str(source),'exec'),ns)
ns['project']()
ns['owners']()
ns['finalize_owners']()
ns['project_owners']()
print('X15 projection and cached owner resolution complete; native write not run',flush=True)
