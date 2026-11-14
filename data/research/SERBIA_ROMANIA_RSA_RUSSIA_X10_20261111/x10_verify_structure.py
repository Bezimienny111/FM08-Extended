"""X10 actual-file inverse, club/family/SugarDaddy and both-form verification."""
from x10_pipeline import *
import struct,re,csv
from collections import Counter
from create_italy_structure_i1_20261108 import load,languages,lang_sections,find_table,club,city,rows,unique
from audit_poland_v25_common_r1_20261108 import Cursor,stadium
def inverse(old,new,edits):
 pieces=[];last=0
 for p in sorted(edits,key=lambda v:v['output_offset']):
  at=p['output_offset'];end=at+p['added_bytes'];assert at>=last and hashlib.sha256(new[at:end]).hexdigest()==p['added_sha256']
  pieces.extend([new[last:at],old[p['source_offset']:p['source_offset']+p['removed_bytes']]]);last=end
 pieces.append(new[last:]);assert b''.join(pieces)==old,'Whole structural inverse failed'
def main():
 m=read(B/'manifest.json');src=Path(m['source']);dest=B/'structure-db';sr=read(B/'structure-report.json');cfg=read(B/'structure-config.json')
 assert pins(src)==m['source_hashes']and pins(dest)==sr['output_hashes']
 a,c=load(dest,'server_db.dat'),load(dest,'client_db.dat');old=load(src,'server_db.dat')
 restored=bytearray(a)
 if sr.get('SERVER_shared_venue_patch'):
  proof=sr['SERVER_shared_venue_patch'];assert hashlib.sha256(a).hexdigest()==proof['output_payload_sha256']
  for p in proof['patches']:
   assert struct.unpack_from('<i',restored,p['offset'])[0]==p['after'];struct.pack_into('<i',restored,p['offset'],p['before'])
  assert hashlib.sha256(restored).hexdigest()==proof['source_payload_sha256']
 inverse(old,bytes(restored),sr['SERVER_edits']);inverse(load(src,'client_db.dat'),c,sr['CLIENT_edits'])
 sl=dict(languages((src/'lang_db.dat').read_bytes()));dl=dict(languages((dest/'lang_db.dat').read_bytes()));assert sl.keys()==dl.keys()
 for p in sr['language_proofs']:inverse(sl[p['language']],dl[p['language']],p['edits']);lang_sections(dl[p['language']])
 assert load(src,'people_db.dat')==load(dest,'people_db.dat')
 rr=read(B/'native-structure-after.json')['records'];original=read(B/'native-structure.json')['records'];byuid={r['ClubUID']:r for r in rr};assert len(rr)==len(original)+102
 move={x['ClubUID']:x for x in cfg['moves']};alts={x['ClubUID']:x for x in cfg['alternate_moves']};venues={x['ClubUID']:x['StadiumIndex']for x in sr['venue_assignments']}
 for r in original:
  n=byuid[r['ClubUID']];o=old[r['Start']:r['Footer']+8];v=a[n['Start']:n['Footer']+8];assert len(o)==len(v)
  assert o[:7]==v[:7]and o[11:15]==v[11:15]and o[23:]==v[23:],('Unrelated TEAM bytes changed',r['ClubUID'])
  assert struct.unpack_from('<i',v,7)[0]==move.get(r['ClubUID'],{}).get('After',r['CurrentDivisionIndex'])
  assert struct.unpack_from('<i',v,15)[0]==alts.get(r['ClubUID'],{}).get('After',struct.unpack_from('<i',o,15)[0])
  assert struct.unpack_from('<i',v,19)[0]==venues.get(r['ClubUID'],struct.unpack_from('<i',o,19)[0])
 current=Counter();alternate=Counter()
 for r in rr:
  p,alt,region=(struct.unpack_from('<i',a,r['Start']+off)[0]for off in [7,15,47]);alt=alt if alt>=0 else p
  current[p]+=1;alternate[alt]+=1
  if region>=0 and region!=p:current[region]+=1
  if region>=0 and region!=alt:alternate[region]+=1
 checks=[]
 for q in cfg['requirements']:
  maximum=None if q['max']==-1 else q['max']
  for form,cnt in [('current',current[q['index']]),('alternate',alternate[q['index']])]:
   good=cnt>=q['min']and(maximum is None or cnt<=maximum);assert good,('Actual disk requirement',q,form,cnt);checks.append(dict(uid=q['uid'],index=q['index'],form=form,count=cnt,min=q['min'],max=maximum,passed=True))
 en,_=lang_sections(dl[8]);families,_,_=find_table(c,[x['uid']for x in en['club']],club);fu={x['uid']:x for x in families};_,_,co=find_table(a,[x['uid']for x in en['city']],city);base=co+4;span=a[base:min(r['Start']for r in rr)]
 mapping=rows(B/'club-map.csv')+rows(B/'foreign-owner-map.csv');assert len(rows(B/'club-map.csv'))==154
 for x in mapping:
  r=byuid[int(x['ClubUID'])];f=fu[int(x.get('ContractFamilyUID')or x['ParentUID']or x['ClubUID'])]
  assert r['TeamIndex']==int(x['TeamIndex'])and r['CurrentDivisionIndex']==int(x['DivisionIndex'])and f['index']==int(x['FamilyIndex'])and f['country_index']==int(x['CountryIndex'])
  if x.get('OwnFamilyIndex'):assert fu[int(x['ClubUID'])]['index']==int(x['OwnFamilyIndex'])and fu[int(x['ClubUID'])]['country_index']==int(x['CountryIndex'])
 project={int(x['ClubUID'])for x in rows(B/'new-clubs-sugar-daddy-audit.csv')}|{x['uid']for x in sr['additions']if x['kind']=='new_first_team'};verified=[]
 for f in families:
  if f['uid']not in project:continue
  fi=f['index'];off=base+unique(span,struct.pack('<iI',fi-1,families[fi-1]['uid']))+8;cur=Cursor(a,off);assert cur.byte()==0;cur.integer();cur.byte();cur.string();cur.byte();cur.string();cur.take(2);cur.num('<H');cur.integer();cur.take(1+12+1+2+4+1+1)
  for _ in range(2):cur.take(cur.byte()*4)
  assert cur.byte()==0 and cur.take(45)[4]==0;verified.append(f['uid'])
 assert set(verified)==project and len(project)==324
 st,_,_=find_table(a,[x['uid']for x in en['stadium']],lambda x:stadium(x,62));cs,_,_=find_table(c,[x['uid']for x in en['stadium']],lambda x:stadium(x,19));assert all(x['raw'][:1]+x['raw'][44:]==y['raw']for x,y in zip(st,cs))
 for x in sr['venues']:assert st[x['index']]['uid']==x['uid']and st[x['index']]['raw']==bytes.fromhex(x['raw'])
 for lang in [8,18]:
  ln={x['uid']:x['names']for x in lang_sections(dl[lang])[0]['club']}
  for x in read(B/'club-plan.json')+read(B/'foreign-owner-plan.json'):
   if x['NativeClubUID']and not x.get('ParentTMID'):assert ln[x['NativeClubUID']][0]==x['Name']
 support=Path('lnc/nleague.lnc');raw=(src/support).read_bytes();assert raw[:2]==bytes.fromhex('fffe');txt=raw[2:].decode('utf-16-le');lines=txt.splitlines(keepends=True);changed=[];new=[]
 for i,line in enumerate(lines):
  if re.match(r'^\s*"CLUB_NAME_CHANGE"\s+1000037(?:\s|$)',line):changed.append(i);new.append('# '+line)
  else:new.append(line)
 assert len(changed)==15;patched=raw[:2]+''.join(new).encode('utf-16-le')
 assert all(new[i]==lines[i]for i in range(len(lines))if i not in changed)
 assert (dest/support).read_bytes()in[raw,patched];(dest/support).write_bytes(patched)
 supportproof=dict(path=str(support),before=hashlib.sha256(raw).hexdigest(),after=hashlib.sha256(patched).hexdigest(),changed_lines=changed,disabled_only='CLUB_NAME_CHANGE1000037',count=15,preserved_Japan107280=True,encoding='UTF16LE_BOM')
 sr.update(status='structure_verified_rosters_pending',support_patch=supportproof,output_hashes=pins(dest));dump(B/'structure-report.json',sr)
 report=dict(status='pass',source_db=str(src),new_teams=102,new_families=101,new_stadiums=sr['new_stadiums'],project_sugar_daddy_off=324,both_form_actual_checks=checks,inverse_all_DAT_and_language_buffers=True,people_identical=True,unrelated_TEAM_bytes_preserved=True,previous_and_regional_fields_preserved=True,support_patch=supportproof,output_hashes=pins(dest),source_unchanged=pins(src)==m['source_hashes'])
 dump(B/'structure-independent.json',report)
 m.update(status='structure_verified_player_preparation_pending',structure_native=True,output_database_created=False);dump(B/'manifest.json',m)
 future=B/'future-audit'
 if not future.exists():
  args=[R/'ITALY_DATABASE_2627_IMPORT_I1_20261108/tools-r1/AuditNativeFutureTransfers.exe',dest,future,'2007-07-01'];z=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300);(B/'future-audit.log').write_text(z.stdout+z.stderr,encoding='utf-8');assert z.returncode==0,z.stderr
 else:assert sr.get('SERVER_shared_venue_patch')and read(B/'structure-independent-before-shared-stadium.json')['status']=='pass'
 alias=B/'future-audit-fcjurong'
 if not alias.exists():shutil.copytree(future,alias)
 print('ACTUAL STRUCTURE PASS102newTEAM/101families,54checks,SugarOFF324,Jurong15aliases,futureaudit.',flush=True)
if __name__=='__main__':main()
