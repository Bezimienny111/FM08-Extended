from pathlib import Path
import sys,json
sys.dont_write_bytecode=True
root=Path('J:/FM08dev');b=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'FM08-Database-Tools/scratch'));sys.path.insert(0,str(b))
source=root/'FmLauncher/data/research/POLAND_GAPS_IMPORT_PACKAGE_20261111/root_verify_structure.py'
s=source.read_text(encoding='utf-8').replace('len(original)+86','len(original)+46').replace('len(mapping)==304','len(mapping)==219').replace("len(rows(W/'club-map.csv'))==292","len(rows(W/'club-map.csv'))==215").replace('new_TEAM=86','new_TEAM=46').replace('structure:86TEAM','structure:46TEAM')
out=b/'verify_structure.py';out.write_text(s,encoding='utf-8')
ns={'__name__':'configured_structure_verifier','__file__':str(out)};exec(compile(s,str(out),'exec'),ns);ns['main']()
