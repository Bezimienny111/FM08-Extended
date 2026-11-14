from pathlib import Path
from datetime import datetime
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
R8=ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_PROTOTYPE_R8_20261107'
OUT=ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_FATES_R9_20261107'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def hashes(folder):return {str(p.relative_to(folder)):sha(p) for p in folder.rglob('*') if p.is_file()}
m8=json.loads((R8/'manifest.json').read_text(encoding='utf-8'))
assert m8['basic_pilot_verified'] and m8['fixtures_verified'] and m8['save_load_verified']
source=R8/'user-data/db/TEST_POL_3_LEVEL_R8'
assert hashes(source)==m8['database_output_hashes']
assert sha(R8/'runtime/fm.exe')==m8['protected_source_hashes']['fm.exe']
OUT.mkdir(parents=True,exist_ok=True)
assert not (OUT/'manifest.json').exists(),'Do not restart existing R9'
assert not (OUT/'input').exists() and not (OUT/'runtime').exists()
(OUT/'input').mkdir();shutil.copytree(source,OUT/'input/TEST_POL_3_LEVEL_R8')
shutil.copytree(R8/'resources',OUT/'input/resources-r8')
shutil.copy2(R8/'participants.csv',OUT/'participants.csv')
(OUT/'tools').mkdir(exist_ok=True)
print(json.dumps({'step':'copy_private_R9_runtime','preserve_R8':True}),flush=True)
shutil.copytree(R8/'runtime',OUT/'runtime')
manifest=dict(revision='R9',status='building',started_at=datetime.now().astimezone().isoformat(),source_database=str(source),frozen_input=str(OUT/'input/TEST_POL_3_LEVEL_R8'),source_r8_status=m8['status'],source_database_hashes=hashes(source),source_resource_hashes=hashes(R8/'resources'),protected_original_hashes=m8['protected_source_hashes'],protected_original_database_hashes=m8['source_database_hashes'],runtime=str(OUT/'runtime'),output_database=str(OUT/'user-data/db/TEST_POL_3_LEVEL_R9'),new_competition_uid=1800001000,preserve_lower_pool_uid=129560,participant_uids=m8['participant_uids'],scope=dict(promotion='places1-2 direct;3-6 semifinal+final;3 promoted',upper_relegation='129559 three to1800001000',relegation='15-18 direct;13-14 two-leg ties against lower qualifiers',lower_qualification='four group winners and four runners-up',new_clubs=0,new_people=0,loans=0,youth_rule=False),game_verified=False,source_modified=False,unresolved=['lower-group activation and reusable resource stage','qualification and exact playoff seeding','season rollover integration'])
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'WZNOWIENIE.md').write_text('''# R9 — prace nad awansami, spadkami i barażami

Źródło: działający R8; pilot rejestracji, terminarza i zapisu/odczytu zaliczony.
R8 nie zmieniać. Zamrożone wejście: input/TEST_POL_3_LEVEL_R8.
Prywatny runtime skopiowany z R8. Pakiet R9 nie jest jeszcze gotowy do testu.

Docelowo: nowy trzeci poziom UID1800001000: 2+1 awanse, 4–6 spadków;
granica górna trzy w obie strony; cztery grupy zaplecza. Bez nowych klubów,
osób i wypożyczeń. Reguły młodzieżowców pozostają osobnym etapem.

Zakresy: promotion/ (XML i dokładna kolejność baraży), upper-boundary/
(minimalne poprawki POL_SECOND), lower-boundary/ (rzeczywiste grupy i baraże).
Root integruje dane/archiwum/launcher i kontrolę, bez ponownej analizy EXE.
''',encoding='utf-8')
assert hashes(source)==m8['database_output_hashes']
print(json.dumps({'status':'R9_prepared','files_frozen':len(manifest['source_database_hashes']),'runtime_copied':True,'R8_unchanged':True}),flush=True)
