import csv,json,hashlib,struct,sys
from pathlib import Path
from collections import Counter
B=Path(__file__).resolve().parent.parent; O=Path(__file__).resolve().parent
sys.path.insert(0,str(Path('J:/FM08dev/FM08-Database-Tools/scratch')))
from create_club_stadium_native_n1_20261108 import load
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def csvread(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report=read(B/'prepared/full-native.json'); before={int(x['Uid']):x for x in report['actor_before']}; after={int(x['Uid']):x for x in report['actor_after']}; subs={int(x['uid']):x for x in report['subjects']}
ledger=csvread(B/'final-native-player-UID-ledger.csv'); prepared=csvread(B/'prepared/native_players.csv'); ids=csvread(B/'prepared/identities.csv'); prepared={int(i['SubjectID']):p for i,p in zip(ids,prepared)}
paths={'source':Path(read(B/'source-freeze.json')['frozen']),'structure':B/'structure-root/structure-db','roster':B/'roster-db','rated':B/'rated-db'}
pins={k:sha(p/'people_db.dat') for k,p in paths.items()}
source=load(paths['source'],'people_db.dat'); structure=load(paths['structure'],'people_db.dat'); roster=load(paths['roster'],'people_db.dat'); rated=load(paths['rated'],'people_db.dat')
assert source==structure,'Unexpected PERSON changes in structure'
def contract(data,w,new=False):
 start=int(w['start' if new else 'Start']); end=int(w['end' if new else 'End']); payload=int(w['payload' if new else 'Payload']); length=int(w['length' if new else 'Length']); ct=int(w['contract' if new else 'Contract'])
 if length==0:return {'length':0,'salary_raw':None,'hex':'','payload':payload,'contract':ct}
 assert payload>=start and payload+65<=end-8 and ct>=start and ct+length<=end-8
 raw=data[ct:ct+length]; base=data[payload:payload+65]
 return {'length':length,'salary_raw':struct.unpack_from('<i',base,35)[0],'expiry_day_year':list(struct.unpack_from('<HH',base,39)),'start_day_year':list(struct.unpack_from('<HH',base,54)),'owner_family':struct.unpack_from('<i',base,31)[0],'person_index':struct.unpack_from('<i',base,26)[0],'flags':{str(k):base[k] for k in [0,1,2,3,24,25,30,43,44,45,46,47,48,49,50,51,52,53,58,59,60,61,62,63,64]},'hex':raw.hex(),'payload':payload,'contract':ct}
rows=[]; detail=[]; all_unchanged=True
for r in ledger:
 uid=int(r['UID']); sid=int(r['SubjectID']); new=r['New']=='True'; w=subs[uid] if new else after[uid]
 a=contract(roster,w,new); z=contract(rated,w,new); assert a==z,uid
 old=None if new else contract(source,before[uid]); expected=int(prepared[sid]['WeeklyWage'])
 row={k:r[k] for k in ['UID','SubjectID','TMID','FirstName','LastName','Club','Country','New','CA','PA']}
 row.update(prepared_salary=expected,source_salary=None if old is None else old['salary_raw'],roster_salary=a['salary_raw'],rated_salary=z['salary_raw'],roster_rated_contract_identical=a==z,source_contract_length=None if old is None else old['length'],roster_contract_length=a['length'],prepared_matches_actual=expected==a['salary_raw'])
 row['salary_change']=None if old is None or old['salary_raw'] is None else a['salary_raw']-old['salary_raw']
 rows.append(row);detail.append({'uid':uid,'source':old,'roster':a,'rated':z})
assert len(rows)==4467
with (O/'whole-batch-contracts.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(O/'typed-contracts.json').write_text(json.dumps(detail,ensure_ascii=False,indent=2),encoding='utf-8')
four={1708003007,1708004087,1708002072,1708004315}
summary={'status':'RAW_NATIVE_CONTRACT_COMPARISON_PASS_OPEN_RUNTIME_WAGE_DEFECT','players':len(rows),'new':sum(r['New']=='True' for r in rows),'reused':sum(r['New']!='True' for r in rows),'source_equals_structure_people':source==structure,'all_roster_rated_contracts_identical':all(r['roster_rated_contract_identical'] for r in rows),'existing_wage_changed':[r for r in rows if r['salary_change'] not in (None,0)],'new_max_raw_salary':max(r['rated_salary'] for r in rows if r['New']=='True'),'prepared_actual_mismatches':[r for r in rows if not r['prepared_matches_actual']],'four_cases':[dict(row=r,raw=next(x for x in detail if x['uid']==int(r['UID']))) for r in rows if int(r['UID']) in four],'pins':pins,'input_pins':{f:sha(B/f) for f in ['prepared/full-native.json','prepared/native_players.csv','prepared/identities.csv','final-native-player-UID-ledger.csv']},'unit_caveat':'+35 is reader/writer salary field, no runtime currency or period conversion inferred. Screenshot amounts not reproduced by native raw field.','constructor':'65-byte default generated from controlled SI TOTESTNEW_B; no club contract donor copied.','runtime_status':'OPEN_DEFECT; SI/career launched but financial correctness unaccepted'}
(O/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
assert pins=={k:sha(p/'people_db.dat') for k,p in paths.items()},'Sources changed during audit'
print(json.dumps({k:summary[k] for k in ['status','players','new','reused','source_equals_structure_people','all_roster_rated_contracts_identical','new_max_raw_salary']}));print('existing_salary_changes',len(summary['existing_wage_changed']),'prepared_mismatches',len(summary['prepared_actual_mismatches']))
