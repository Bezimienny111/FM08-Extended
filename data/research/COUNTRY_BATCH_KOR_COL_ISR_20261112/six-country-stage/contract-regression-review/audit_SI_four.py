import sys,json,struct,hashlib
from pathlib import Path
sys.path.insert(0,'J:/FM08dev/FM08-Database-Tools/scratch')
from create_club_stadium_native_n1_20261108 import load
from compare_native_player_tests import known_person_span
O=Path(__file__).parent; B=O.parent; S=Path('J:/FM08dev/FmLauncher/data/research/WORK_20261112/X16_CONTRACT_REVIEW/input/X16-after-SI')
raw=load(S,'people_db.dat'); old=json.loads((O/'summary.json').read_text(encoding='utf-8')); rows=[]
for case in old['four_cases']:
 uid=int(case['row']['UID']);a,z=known_person_span(raw,uid);assert z-a==299 and raw[a+198]==1
 c=raw[a+199:a+264]; n=bytes.fromhex(case['raw']['rated']['hex']);diff=[{'offset':i,'native':x,'afterSI':y} for i,(x,y) in enumerate(zip(n,c)) if x!=y]
 assert struct.unpack_from('<i',c,26)[0]==struct.unpack_from('<i',raw,a)[0]
 rows.append({'uid':uid,'name':case['row']['FirstName']+' '+case['row']['LastName'],'contract65_identical':not diff,'differences':diff,'afterSI_salary35':struct.unpack_from('<i',c,35)[0],'afterSI_hex':c.hex()})
r={'status':'FOUR_TYPED_MAIN_CONTRACTS_COMPARE','source':str(S),'source_people_sha256':hashlib.sha256((S/'people_db.dat').read_bytes()).hexdigest(),'rows':rows,'all_identical':all(x['contract65_identical']for x in rows),'unit_inference':'NONE'}
(O/'after-SI-four-typed.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r))
