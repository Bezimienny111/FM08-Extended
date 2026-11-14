from pathlib import Path
import json,hashlib,struct,zlib,csv
B=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
dump=lambda n,x:(B/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
pin=read(B/'input-pins.json');base=read(B/'offline-proof.json')
paths={'original':Path('J:/FM08/data/updates/update-802/db/802'),'contro20':Path('J:/FM08dev/Dane/db/TEST_CONTRO'),'unique':Path('J:/FM08dev/Dane/db/TEST_X12')}
personidx=2389;uid=8074
names=['Adaptability','Ambition','Loyalty','Pressure','Professionalism','Sportsmanship','Temperament','Controversy']
desired=[2,4,6,8,10,12,14,16];result={};payloads={}
for label,path in paths.items():
 raw=(path/'people_db.dat').read_bytes();z=zlib.decompressobj();p=z.decompress(raw[9:])+z.flush();assert z.eof and not z.unused_data and not z.unconsumed_tail
 pc,n,ac=struct.unpack_from('<iii',p);hits=[];at=0
 while True:
  at=p.find(struct.pack('<i',ac),at)
  if at<0:break
  st=at+4
  if st+4*89<=len(p)and all(p[st+89*k]==0 and struct.unpack_from('<i',p,st+89*k+81)[0]==k for k in range(4)):hits.append(st)
  at+=1
 assert len(hits)==1
 ah=hits[0];ph=ah-8-17*n;assert struct.unpack_from('<i',p,ph)[0]==n
 matches=[i for i in range(n)if p[ph+4+i*17]==0 and struct.unpack_from('<ii',p,ph+4+i*17+9)==(i,uid)]
 assert len(matches)==1
 i=matches[0];off=ph+4+17*i;row=p[off:off+17]
 actor=base['actors']['stock'];assert hashlib.sha256(p[actor['start']:actor['end']]).hexdigest()==actor['sha256']
 ar=base['attribute_records']['stock'];assert hashlib.sha256(p[ar['offset']:ar['offset']+89]).hexdigest()==ar['sha256']
 assert struct.unpack_from('<i',p,actor['personality_reference_offset'])[0]==i
 result[label]=dict(source=str(path),table_header=ph,count=n,index=i,uid=uid,row_offset=off,row=row.hex(),serialized_values=list(row[1:9]),row_sha256=hashlib.sha256(row).hexdigest(),PERSON488_identical=True,attributes89_identical=True)
 payloads[label]=p
audit=list(csv.DictReader((B/'unique-audit/players.csv').open(encoding='utf-8-sig')));match=[r for r in audit if r['ID']=='8074'];assert len(match)==1 and match[0]==base['identity']
assert result['unique']['serialized_values']==desired
a,c=result['contro20'],result['unique'];assert(a['table_header'],a['count'],a['index'])==(c['table_header'],c['count'],c['index'])
lo=a['table_header']+4;hi=lo+a['count']*17
changed=[i for i in range(lo,hi)if payloads['contro20'][i]!=payloads['unique'][i]]
assert changed==list(range(c['row_offset']+1,c['row_offset']+9))
inverse=bytearray(payloads['unique'][lo:hi]);x=c['row_offset']-lo;inverse[x+1:x+9]=bytes(result['contro20']['serialized_values']);assert bytes(inverse)==payloads['contro20'][lo:hi]
assert all({q.name:hashlib.sha256(q.read_bytes()).hexdigest()for q in path.glob('*.dat')}==pin[str(path)]for path in paths.values())
mapping=[dict(name=name,serialized17B_offset=i+1,user_unique_value=desired[i],original_value=result['original']['serialized_values'][i],contro20_value=result['contro20']['serialized_values'][i],runtime_slot=hex(slot),runtime_getter_offset=hex(0x1c+i),runtime_status='known_named_property_static'if i<7 else'candidate_pending_controlled_runtime')for i,(name,slot)in enumerate(zip(names,[0x218,0x21c,0x224,0x228,0x22c,0x230,0x234,0x238]))]
proof=dict(status='PASS_full8_serialized_semantic_mapping_controlled_SI',uid=8074,identity=match[0],steps=result,codec=mapping,whole_personality_table_changed_bytes=8,all_other_personality_rows_identical=True,whole_personality_inverse_pass=True,source_DAT_hashes_unchanged=True,proof_scope='All8 serialized names from distinct user SI values; only first7 runtime names independently bound before test. Eighth runtime must still be verified.',runtime='PENDING_no_game_attach_or_remote_execution')
dump('unique-trait-proof.json',proof)
dump('IMPORTER_PERSONALITY_SEMANTICS_DEFECT.json',dict(severity='CRITICAL_future_personality_writes',status='PROVED_controlled_original802_Contro20_unique8',affected_source='FM08-Database-Tools/FM08_Database_Editor.cs:6485-6515 and writers using Adaptability,Ambition,Controversy,Loyalty,Pressure,Professionalism,Sportsmanship,Temperament',incorrect_order=['Adaptability','Ambition','Controversy','Loyalty','Pressure','Professionalism','Sportsmanship','Temperament'],verified_serialized_order=names,evidence='unique-trait-proof.json',affected_mechanism='Native17B personality decode/encode; prefix-variable actor reference must also be mapped, not presumed+181',future_policy='Block new personality writes relying on old order until coordinated codec correction+existing-batch impact audit; do not rewrite databases during panel release',native7_getters_unchanged=True,existing_databases_modified=False,main_editor_modified=False,all_previous_personality_values_not_recalculated=True,actual_impact_requires_per_batch_audit=True))
print(json.dumps(proof,ensure_ascii=True,indent=2))
