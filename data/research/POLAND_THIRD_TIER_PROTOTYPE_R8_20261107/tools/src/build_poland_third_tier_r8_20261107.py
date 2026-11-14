"""Build an isolated third-tier database and append-only resource overlay."""
import csv,hashlib,json,pathlib,shutil,struct,sys,zlib,xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
import pol3_comp_schema_r8_20261107 as comp
import pol3_efa_r8_20261107 as efa
from compare_native_player_tests import controlled_club_span
OUT=ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_PROTOTYPE_R8_20261107';BASE=OUT/'input/802';NEWUID=1800001000

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def save(p,value):
 with p.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def load(name):
 raw=(BASE/name).read_bytes();d=zlib.decompressobj();s=d.decompress(raw[9:])+d.flush();assert d.eof and not d.unused_data and not d.unconsumed_tail;return s
def langblocks(raw):
 count=raw[9];entries=[struct.unpack_from('<ii',raw,10+8*i) for i in range(count)];assert count==20 and entries[0][1]==161
 for i,(lang,offset) in enumerate(entries):
  end=9+entries[i+1][1] if i+1<count else len(raw);d=zlib.decompressobj();data=d.decompress(raw[9+offset:end])+d.flush();assert d.eof and not d.unused_data and not d.unconsumed_tail
  yield lang,data
manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
assert {str(p.relative_to(BASE)):sha(p) for p in BASE.rglob('*') if p.is_file()}==manifest['source_database_hashes']
with (OUT/'participants.csv').open(encoding='utf-8-sig',newline='') as f:participants=list(csv.DictReader(f))
assert len(participants)==18
server=load('server_db.dat');client=load('client_db.dat');people=load('people_db.dat');person_count=struct.unpack_from('<i',people)[0]
ct=comp.find_client_comp_table(client);st=comp.find_server_comp_table(server,ct);uids={r['uid'] for r in ct['records']}
assert NEWUID not in uids
for name,data in [('server',server),('client',client),('people',people)]:assert struct.pack('<i',NEWUID) not in data,'UID bytes already present in '+name
new_server_row=comp.clone_server_comp_record(st,129559,NEWUID,level=2);new_index=st['count'];assert new_index==1332
# Only current-division fields change; identities, previous division and roster bytes remain as input.
modified=bytearray(server);changes=[]
for item in participants:
 idx=int(item['ClubIndex']);uid=int(item['ClubUID']);start,end=controlled_club_span(server,idx,person_count)
 assert struct.unpack_from('<ii',server,end-8)==(idx,uid)
 at=start+7;assert struct.unpack_from('<i',server,at)[0]==141
 struct.pack_into('<i',modified,at,new_index)
 changes.append(dict(club_uid=uid,club_index=idx,source_field_offset=at,before=141,after=new_index))
server_after=comp.append_record(bytes(modified),st,new_server_row)
client_after=comp.append_record(client,ct,comp.client_mirror_of_server_record(new_server_row))
ct_after=comp.find_client_comp_table(client_after,1333);st_after=comp.find_server_comp_table(server_after,ct_after)
assert [x['raw'] for x in ct_after['records'][:-1]]==[x['raw'] for x in ct['records']]
assert [x['raw'] for x in st_after['records'][:-1]]==[x['raw'] for x in st['records']]
assert ct_after['records'][-1]['uid']==st_after['records'][-1]['uid']==NEWUID
assert server_after[st_after['end']:st_after['end']+1000]==bytes(modified)[st['end']:st['end']+1000]
assert client_after[ct_after['end']:]==client[ct['end']:]
# Independent reversal proves that all other SERVER bytes survive exactly.
reverse=bytearray(server_after[:st['end']]+server_after[st['end']+68:]);struct.pack_into('<i',reverse,st['count_offset'],1332)
for change in changes:struct.pack_into('<i',reverse,change['source_field_offset'],141)
assert bytes(reverse)==server
langraw=(BASE/'lang_db.dat').read_bytes();compressed=[];langproof=[]
for language,block in langblocks(langraw):
 assert struct.pack('<i',NEWUID) not in block
 table=comp.find_language_comp_table(block,uids)
 template=next(x for x in table['records'] if x['uid']==129559)
 names=['Polska - III poziom (test R8)','Polska III (test)','PL3'] if language==18 else ['Polish Third Tier - Prototype R8','Third Tier R8','PL3']
 nr=comp.make_language_comp_record(NEWUID,names,template['suffixes']);after=comp.append_record(block,table,nr)
 check=comp.find_language_comp_table(after,uids|{NEWUID})
 assert [x['raw'] for x in check['records'][:-1]]==[x['raw'] for x in table['records']]
 assert after[check['end']:]==block[table['end']:]
 langproof.append(dict(language=language,before_count=1332,after_count=1333,old_records_byte_identical=True,old_suffix_preserved=True,old_trailing_bytes_identical=True,new_names=names))
 compressed.append((language,zlib.compress(after)))
header=bytearray(langraw[:9]+bytes([len(compressed)]));offset=1+len(compressed)*8
for language,data in compressed:header+=struct.pack('<ii',language,offset);offset+=len(data)
lang_after=bytes(header)+b''.join(data for _,data in compressed)
assert [language for language,_ in langblocks(lang_after)]==[x['language'] for x in langproof]
output=OUT/'user-data/db/TEST_POL_3_LEVEL_R8';assert not output.exists(),'Refuse overwrite database'
shutil.copytree(BASE,output,ignore=shutil.ignore_patterns('802.xml'))
for name,payload in [('server_db.dat',server_after),('client_db.dat',client_after)]:
 (output/name).write_bytes((BASE/name).read_bytes()[:9]+zlib.compress(payload))
 assert zlib.decompress((output/name).read_bytes()[9:])==payload
(output/'lang_db.dat').write_bytes(lang_after)
xml=ET.Element('properties',version='1.0')
for key,value in [('name','TEST_POL_3_LEVEL_R8 - Polish Third Tier Pilot'),('author','FM08dev'),('description','Technical third-tier pilot:18 existing Polish clubs,18 teams and34 matchdays. Original8.0.2 players. Promotion,relegation and youth-policy integration are not yet included.'),('version','0.1.0'),('required_version','8.0.2')]:ET.SubElement(xml,'string',id=key,value=value,translate='false')
ET.indent(xml,space='  ');ET.ElementTree(xml).write(output/'TEST_POL_3_LEVEL_R8.xml',encoding='utf-8',xml_declaration=True)
for p in BASE.rglob('*'):
 if p.is_file() and p.name not in ['802.xml','server_db.dat','client_db.dat','lang_db.dat']:assert sha(p)==sha(output/p.relative_to(BASE)),str(p)
# Minimal Polish country override preserves all native factory creation.
country=f'''<properties nation="787">
  <integer id="version" value="1"/>
  <list id="division_levels">
    <record competition="129558"/>
    <record competition="129559"/>
    <record competition="{NEWUID}"/>
  </list>
  <integer id="default_division_level" value="2"/>
  <list id="required_teams">
    <record competition="129558" number_teams="16"/>
    <record competition="129559" number_teams="18"/>
    <record competition="{NEWUID}" number_teams="18"/>
    <record competition="129560" minimum_number_teams="30"/>
  </list>
</properties>
'''
# Use the shipped Scotland generic-league schema; do not copy its fate rules or prize money.
league=f'''<properties competition="{NEWUID}">
  <integer id="version" value="1"/>
  <integer id="type" value="division"/>
  <integer id="level" value="2"/>
  <integer id="year" value="0"/>
  <integer id="year_interval" value="1"/>
  <record id="date_range" start_month="jul" start_year_offset="0" end_month="jun" end_year_offset="1"/>
  <integer id="discipline_index" value="1"/>
  <integer id="base_year" value="2000"/>
  <integer id="fixture_rules_index" value="2"/>
  <list id="stages">
    <record id="leag" index="0" type="league">
      <list id="teams"><record>
        <flags id="id" value="get_division_teams"/>
        <integer id="competition" value="{NEWUID}"/>
      </record></list>
      <integer id="number_teams" value="18"/>
      <integer id="number_rounds" value="2"/>
      <integer id="points_for_win" value="3"/>
      <integer id="points_for_draw" value="1"/>
      <integer id="points_for_defeat" value="0"/>
      <list id="sort_rules">
        <flags value="goal_difference"/>
        <flags value="goals_for"/>
      </list>
      <boolean id="top_team_are_champions" value="true"/>
      <flags id="subs_rules" value="three_from_seven"/>
      <flags id="priority" value="league_low"/>
      <list id="schedule"><record>
        <record id="start_date" day_of_week="sat" day_of_month="29" month="jul" year="2000"/>
        <record id="end_date" day_of_week="sat" day_of_month="26" month="may" year="2001"/>
        <integer id="number_dates" value="34"/>
        <flags id="check_clashes" value="all"/>
        <list id="match_days"><record day_of_week="sat"/><record day_of_week="wed"/></list>
      </record></list>
    </record>
  </list>
</properties>
'''
# Verify key spellings against the executable's registered schema, not English intuition.
exe=(ROOT/'fm.exe').read_bytes()
for key in ['points_for_win','points_for_draw','points_for_defeat','number_dates','fixture_rules_index','division_levels']:
 assert (key.encode()+b'\0') in exe,key
for data in [country,league]:ET.fromstring(data)
assert ET.fromstring(country).find("list[@id='competitions']") is None
resources=OUT/'resources';resources.mkdir()
(resources/'pol.xml').write_text(country,encoding='utf-8');(resources/'pol_third.xml').write_text(league,encoding='utf-8')
archive_path=ROOT/'data/updates/update-802/data/comps.efa';original=efa.parse(archive_path.read_bytes());updated=efa.add_member(original,'pol/pol.xml',country.encode());updated=efa.add_member(updated,'pol/pol_third.xml',league.encode());packed=efa.repack(updated)
(resources/'comps.efa').write_bytes(packed);reopened=efa.parse(packed)
assert all(reopened['members'][k]==v for k,v in original['members'].items())
assert len(reopened['members'])==len(original['members'])+2
report=dict(status='native_structural_verification_passed',output_database=str(output),new_competition_uid=NEWUID,new_competition_index=1332,competition_count_before=1332,competition_count_after=1333,club_changes=changes,new_clubs=0,new_people=0,language_blocks=langproof,all_old_comp_records_unchanged=True,server_exact_reverse_reconstructs_source=True,client_trailing_bytes_unchanged=True,people_and_histories_byte_identical=True,archive_old_members_preserved=len(original['members']),archive_added=['pol/pol.xml','pol/pol_third.xml'],source_archive_unchanged=sha(archive_path)==manifest['protected_source_hashes'][str(archive_path.relative_to(ROOT))],db_output_hashes={str(p.relative_to(output)):sha(p) for p in output.rglob('*') if p.is_file()},si_verified=False,game_verified=False,calendar='minimal generic full-season window; Polish winter break not yet reconstructed',fate_and_youth_rules='not yet integrated in registration pilot',runtime_hook_required='append generic competition after original Polish factory; preserve all5 original objects')
save(OUT/'database-resource-build.json',report)
manifest.update(status='database_and_resources_built',native_db_status=report['status'],resource_status='archive_roundtrip_verified',new_competition_uid=NEWUID,new_competition_index=1332,resource_old_members_preserved=len(original['members']),database_output_hashes=report['db_output_hashes'])
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert {str(p.relative_to(BASE)):sha(p) for p in BASE.rglob('*') if p.is_file()}==manifest['source_database_hashes']
print(json.dumps(dict(status=report['status'],new_uid=NEWUID,new_index=1332,club_changes=18,language_blocks=20,archive_old_members_preserved=len(original['members']),output=str(output)),ensure_ascii=True),flush=True)
