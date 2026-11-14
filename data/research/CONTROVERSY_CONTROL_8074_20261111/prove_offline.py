from pathlib import Path
import json,csv,hashlib,struct,zlib,datetime,sys
sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;ROOT=B.parents[3]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(n,x):(B/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(v):return hashlib.sha256(v).hexdigest()
def unpack(data):
 z=zlib.decompressobj();v=z.decompress(data[9:])+z.flush();assert z.eof and not z.unused_data and not z.unconsumed_tail;return v
uid=8074
inputs=read(B/'input-pins.json')
paths=[Path(p)for p in inputs];stock,test=paths[0],paths[2]
assert inputs[str(paths[0])]==inputs[str(paths[1])]
audits={}
for label in ['stock','test']:
 rows=list(csv.DictReader((B/(label+'-audit')/'players.csv').open(encoding='utf-8-sig')))
 selected=[r for r in rows if r['ID']==str(uid)];assert len(selected)==1
 audits[label]=selected[0]
assert audits['stock']==audits['test']
assert audits['stock']['FirstName']=='Alessandro'and audits['stock']['LastName']=='Del Piero'and audits['stock']['BirthDate']=='1974-11-09'
actors={};tables={};attrs={};data={}
for label,path in [('stock',stock),('test',test)]:
 p=unpack((path/'people_db.dat').read_bytes());data[label]=p
 persons,personalities,attributes=struct.unpack_from('<iii',p);candidates=[];needle=struct.pack('<i',attributes);at=0
 while True:
  at=p.find(needle,at)
  if at<0:break
  start=at+4
  if start+89*4<=len(p)and all(p[start+89*k]==0 and struct.unpack_from('<i',p,start+89*k+81)[0]==k for k in range(4)):candidates.append(start)
  at+=1
 assert len(candidates)==1,candidates
 attribute_start=candidates[0];ph=attribute_start-8-personalities*17
 assert struct.unpack_from('<i',p,ph)[0]==personalities
 pi=int(audits[label]['PersonIndex']);frames=[];needle=struct.pack('<iB',pi,2);at=16
 while True:
  at=p.find(needle,at,ph)
  if at<0:break
  if p[at+26:at+30]==bytes.fromhex('6c071027'):
   footer=p.find(struct.pack('<ii',pi,uid),at+200,min(at+4096,ph))
   if footer>=0:
    following=footer+8
    if following==ph or (0<=struct.unpack_from('<i',p,following)[0]<persons and 1<=p[following+4]<=5):frames.append((at,footer+8))
  at+=1
 assert len(frames)==1,frames
 st,en=frames[0]
 rows=[i for i in range(personalities)if p[ph+4+17*i]==0 and struct.unpack_from('<ii',p,ph+4+17*i+9)==(i,uid)]
 assert len(rows)==1,rows
 personality_index=rows[0];rt=ph+4+17*personality_index
 refs=[i for i in range(st,en-3)if p[i:i+4]==struct.pack('<i',personality_index)]
 assert len(refs)==1,refs
 # The validated indexed17B table plus matching UID establish the reference without any fixed prefix assumption.
 raw=p[rt:rt+17];assert all(0<=x<=20 for x in raw[1:9])
 ars=[i for i in range(attributes)if p[attribute_start+89*i]==0 and struct.unpack_from('<ii',p,attribute_start+89*i+81)==(i,uid)]
 assert len(ars)==1,ars
 ar=attribute_start+89*ars[0];attrs[label]=dict(index=ars[0],offset=ar,raw=p[ar:ar+89].hex(),sha256=sha(p[ar:ar+89]))
 actors[label]=dict(index=pi,uid=uid,start=st,end=en,length=en-st,type=p[st+4],personality_reference_offset=refs[0],personality_reference_relative=refs[0]-st,sha256=sha(p[st:en]),raw=p[st:en].hex())
 tables[label]=dict(header=ph,count=personalities,record_index=personality_index,record_uid=uid,record_offset=rt,raw=raw.hex(),values_raw_serialized=list(raw[1:9]),record_sha256=sha(raw),table_sha256=sha(p[ph+4:ph+4+17*personalities]),attributes_start=attribute_start,attributes_count=attributes,person_count=persons)
assert actors['stock']==actors['test']and attrs['stock']==attrs['test']
a,b=data['stock'],data['test'];t=tables['stock'];u=tables['test'];assert t['header']==u['header']and t['count']==u['count']
lo=t['header']+4;hi=lo+17*t['count'];changes=[i for i in range(lo,hi)if a[i]!=b[i]]
expected=t['record_offset']+8
assert changes==[expected]and a[expected]==1 and b[expected]==20
assert bytes.fromhex(t['raw'])[:8]==bytes.fromhex(u['raw'])[:8]and bytes.fromhex(t['raw'])[9:]==bytes.fromhex(u['raw'])[9:]
inverse=bytearray(b[lo:hi]);inverse[expected-lo]=1;assert bytes(inverse)==a[lo:hi]
assert len(a)==len(b);allchanges=sum(x!=y for x,y in zip(a,b))
after={str(p):{x.name:sha(x.read_bytes())for x in p.glob('*.dat')}for p in paths};assert after==inputs
reader=ROOT/'FM08-Database-Tools/FM08_Database_Editor.cs';lines=reader.read_text(encoding='utf-8-sig').splitlines()
dump('offline-proof.json',dict(status='PASS_controlled_serialized_Controversy_field_proved',uid=uid,identity=audits['stock'],original802_copies_hash_identical=True,source_pins=inputs,source_unchanged_after_audits=True,actors=actors,attribute_records=attrs,personality_records=tables,controlled_change=dict(source='User SI editor instruction Controversy1->20, TEST_CONTRO from original802',table_record_size=17,field_relative_to_record=8,offset_people_decompressed=expected,before=1,after=20,all_other_seven_serialized_values_unchanged=True,entire_personality_table_changed_bytes=1,whole_personality_table_inverse_pass=True),whole_people=dict(decompressed_bytes=len(a),changed_bytes=allchanges,limitation='SI resave also changed other PERSON bytes globally; controlled proof is target PERSON/attributes and whole indexed personality table, not whole DB single-byte equality'),old_reader_caution=dict(file=str(reader),sha256=sha(reader.read_bytes()),lines6485_6515='\n'.join(lines[6484:6515]),issue='Old source maps row+3 to Controversy, row+8 Temperament and only accepts standard prefix+181; controlled SI witness disproves row+3 Controversy. Do not use its naming/order as semantic ground truth. DelPiero variable prefix reference+252 verified independently; no global old profile correction attempted.'),runtime=dict(status='PENDING_user_has_not_started_control_career',candidate='PERSON virtual238 -> CBAB90 -> C81A90 -> personality data signedbyte+23',determination_excluded='PERSONslot220 is Determination; never use',no_runtime_attach=True,no_game_launch=True,no_injection=True),name_exception='TEST_CONTRO is user requested independent control; X12/X13 remain reserved; next import X14'))
print(json.dumps(dict(status='PASS',uid=uid,personality_index=t['record_index'],record_offset=t['record_offset'],field_offset=8,before=1,after=20,values_before=t['values_raw_serialized'],values_after=u['values_raw_serialized'],person_bytes_identical=True,attributes89_identical=True,entire_personality_changed_bytes=1,whole_people_other_SI_changes=allchanges-1,runtime='PENDING'),indent=2))
