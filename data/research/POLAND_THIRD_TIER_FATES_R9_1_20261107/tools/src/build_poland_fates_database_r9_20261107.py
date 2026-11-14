from pathlib import Path
import hashlib,json,shutil,struct,sys,zlib,xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
import pol3_comp_schema_r8_20261107 as comp
OUT=ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_FATES_R9_20261107'
BASE=OUT/'input/TEST_POL_3_LEVEL_R8'
DEST=OUT/'user-data/db/TEST_POL_3_LEVEL_R9'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def hashes(p):return {str(x.relative_to(p)):sha(x) for x in p.rglob('*') if x.is_file()}
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
m=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
assert hashes(BASE)==m['source_database_hashes']
assert not DEST.exists(),'Refuse overwrite R9 database'
server=zlib.decompress((BASE/'server_db.dat').read_bytes()[9:]);client=zlib.decompress((BASE/'client_db.dat').read_bytes()[9:])
ct=comp.find_client_comp_table(client,1333);st=comp.find_server_comp_table(server,ct)
sr=next(x for x in st['records'] if x['uid']==129560);cr=next(x for x in ct['records'] if x['uid']==129560)
assert sr['index']==cr['index']==141 and sr['raw'][19]==cr['raw'][19]==2
sa=bytearray(server);ca=bytearray(client);sa[sr['start']+19]=3;ca[cr['start']+19]=3
assert sum(a!=b for a,b in zip(server,sa))==1
assert sum(a!=b for a,b in zip(client,ca))==1
cta=comp.find_client_comp_table(ca,1333);sta=comp.find_server_comp_table(sa,cta)
assert all(a['raw']==b['raw'] for a,b in zip(st['records'],sta['records']) if a['uid']!=129560)
raw=(BASE/'lang_db.dat').read_bytes();count=raw[9];assert count==20
entries=[struct.unpack_from('<ii',raw,10+8*i) for i in range(count)]
uids={x['uid'] for x in ct['records']};blocks=[];proof=[]
for i,(language,offset) in enumerate(entries):
 end=9+entries[i+1][1] if i+1<count else len(raw)
 d=zlib.decompressobj();block=d.decompress(raw[9+offset:end])+d.flush();assert d.eof and not d.unused_data
 table=comp.find_language_comp_table(block,uids);new=[]
 for r in table['records']:
  if r['uid']==1800001000:
   names=['Polska - II liga (test R9)','II liga R9','PL3'] if language==18 else ['Polish Third Tier - R9','Third Tier R9','PL3']
   new.append(comp.make_language_comp_record(r['uid'],names,r['suffixes']))
  elif r['uid']==129560:
   names=['Polska - III liga (zaplecze R9)','III liga R9','PL4'] if language==18 else ['Polish Fourth Tier Groups - R9','Fourth Tier R9','PL4']
   new.append(comp.make_language_comp_record(r['uid'],names,r['suffixes']))
  else:new.append(r['raw'])
 after=block[:table['start']]+b''.join(new)+block[table['end']:]
 check=comp.find_language_comp_table(after,uids)
 assert after[check['end']:]==block[table['end']:]
 assert all(a['raw']==b['raw'] for a,b in zip(table['records'],check['records']) if a['uid'] not in (129560,1800001000))
 blocks.append((language,zlib.compress(after)))
 proof.append(dict(language=language,competition_count=1333,renamed_uids=[129560,1800001000],other_names_unchanged=True,trailing_bytes_unchanged=True))
header=bytearray(raw[:9]+bytes([count]));at=1+count*8
for language,data in blocks:header+=struct.pack('<ii',language,at);at+=len(data)
la=bytes(header)+b''.join(x[1] for x in blocks)
shutil.copytree(BASE,DEST,ignore=shutil.ignore_patterns('TEST_POL_3_LEVEL_R8.xml'))
for name,data in [('server_db.dat',bytes(sa)),('client_db.dat',bytes(ca))]:
 (DEST/name).write_bytes((BASE/name).read_bytes()[:9]+zlib.compress(data))
(DEST/'lang_db.dat').write_bytes(la)
meta=ET.Element('properties',version='1.0')
for key,value in [('name','TEST_POL_3_LEVEL_R9 - Polish Promotion and Relegation Pilot'),('author','FM08dev'),('description','Complete historical FM08 8.0.2 database with an experimental Polish third-tier league and promotion/relegation playoffs. Eighteen existing clubs in the third tier; one hundred existing clubs in four supporting groups. Historical player, coaching staff and loan data retained; no modern squad import. Youth eligibility and the Polish winter break are not implemented. New career required.'),('version','0.2.0'),('required_version','8.0.2')]:ET.SubElement(meta,'string',id=key,value=value,translate='false')
ET.indent(meta,space='  ');ET.ElementTree(meta).write(DEST/'TEST_POL_3_LEVEL_R9.xml',encoding='utf-8',xml_declaration=True)
for p in BASE.rglob('*'):
 if p.is_file() and p.name not in ('server_db.dat','client_db.dat','lang_db.dat','TEST_POL_3_LEVEL_R8.xml'):
  assert sha(p)==sha(DEST/p.relative_to(BASE))
assert hashes(BASE)==m['source_database_hashes']
assert hashes(Path(m['source_database']))==m['source_database_hashes']
report=dict(status='database_structural_verification_passed',competition_count=1333,new_competitions=0,new_clubs=0,new_people=0,club_assignments_unchanged_from_R8=True,server_decompressed_byte_changes=[dict(uid=129560,index=141,field_offset=19,before_level=2,after_level=3)],client_decompressed_byte_changes=1,other_comp_records_unchanged=True,people_histories_other_files_identical=True,language_blocks=proof,source_R8_unchanged=True,output_database_hashes=hashes(DEST),game_verified=False)
save(OUT/'database-build.json',report)
m.update(status='database_built_resources_in_progress',database_output_hashes=report['output_database_hashes'],native_db_status=report['status'])
save(OUT/'manifest.json',m)
print(json.dumps({'status':report['status'],'competition_count':1333,'club_changes_from_R8':0,'lower_uid':129560,'lower_level':3,'language_blocks':20,'R8_unchanged':True}),flush=True)
