"""Independent full inverse and actual-disk verification of private X14 structure."""
from pathlib import Path
from collections import Counter
import sys,struct,hashlib
sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');W=Path(__file__).resolve().parent;B=W.parent
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
from create_italy_structure_i1_20261108 import read,rows,dump,load,pins,languages,lang_sections,find_table,club,city,unique
from audit_poland_v25_common_r1_20261108 import Cursor,stadium


def inverse(old,new,edits):
 chunks=[];last=0
 for p in sorted(edits,key=lambda x:x['output_offset']):
  at=p['output_offset'];end=at+p['added_bytes']
  assert at>=last and hashlib.sha256(new[at:end]).hexdigest()==p['added_sha256']
  chunks.extend([new[last:at],old[p['source_offset']:p['source_offset']+p['removed_bytes']]]);last=end
 chunks.append(new[last:]);assert b''.join(chunks)==old,'Whole-buffer inverse failed'

def main():
 m=read(W/'manifest.json');src=Path(m['source']);dest=W/'structure-db';sr=read(W/'structure-report.json');cfg=read(W/'structure-config.json')
 assert {k:v.lower()for k,v in pins(src).items()}==m['source_hashes']
 assert pins(dest)==sr['output_hashes']
 a,c=load(dest,'server_db.dat'),load(dest,'client_db.dat');old=load(src,'server_db.dat')
 inverse(old,a,sr['SERVER_edits']);inverse(load(src,'client_db.dat'),c,sr['CLIENT_edits'])
 sl=dict(languages((src/'lang_db.dat').read_bytes()));dl=dict(languages((dest/'lang_db.dat').read_bytes()));assert sl.keys()==dl.keys()
 for p in sr['language_proofs']:inverse(sl[p['language']],dl[p['language']],p['edits']);lang_sections(dl[p['language']])
 assert (src/'people_db.dat').read_bytes()==(dest/'people_db.dat').read_bytes()
 for rel in pins(src):
  if rel not in ['server_db.dat','client_db.dat','lang_db.dat']:assert (src/rel).read_bytes()==(dest/rel).read_bytes(),('unrelated_file',rel)
 rr=read(W/'native-structure-after.json')['records'];original=read(W/'native-structure.json')['records'];byuid={x['ClubUID']:x for x in rr}
 assert len(rr)==len(original)+sr['new_clubs'] and len(rr)==len(byuid)
 moves={x['ClubUID']:x for x in cfg['moves']};alts={x['ClubUID']:x for x in cfg['alternate_moves']};venues={x['ClubUID']:x['StadiumIndex']for x in sr['venue_assignments']}
 for r in original:
  n=byuid[r['ClubUID']];o=old[r['Start']:r['Footer']+8];v=a[n['Start']:n['Footer']+8]
  assert len(o)==len(v)and o[:7]==v[:7]and o[11:15]==v[11:15]and o[23:]==v[23:],('unrelated_TEAM_bytes',r['ClubUID'])
  assert struct.unpack_from('<i',v,7)[0]==moves.get(r['ClubUID'],{}).get('After',r['CurrentDivisionIndex'])
  assert struct.unpack_from('<i',v,15)[0]==alts.get(r['ClubUID'],{}).get('After',struct.unpack_from('<i',o,15)[0])
  assert struct.unpack_from('<i',v,19)[0]==venues.get(r['ClubUID'],struct.unpack_from('<i',o,19)[0])
 en,_=lang_sections(dl[8]);families,_,_=find_table(c,[x['uid']for x in en['club']],club);fu={x['uid']:x for x in families}
 mapping=rows(W/'club-map.csv')+rows(W/'foreign-owner-map.csv');projection={x['TMID']:x for x in rows(B/'club-map.csv')+rows(B/'foreign-owner-map.csv')}
 assert len(mapping)==len(read(W/'club-plan.json'))+len(read(W/'foreign-owner-plan.json')) and len(rows(W/'club-map.csv'))==m['expected_core_clubs']
 original_world={x['ClubUID']:x for x in read(B/'native-world-identities.json')}
 country={x['ClubUID']:original_world.get(x['ClubUID'],{}).get('TeamCountry')for x in rr}
 for x in mapping:
  u=int(x['ClubUID']);f=fu[int(x['ParentUID']or u)];r=byuid[u];pr=projection[x['TMID']]
  for field in ['ClubUID','TeamIndex','CountryIndex']:assert int(x[field])==int(pr[field]),('projection_changed',x['TMID'],field,x[field],pr[field])
  assert r['TeamIndex']==int(x['TeamIndex'])and r['CurrentDivisionIndex']==int(x['DivisionIndex'])and f['index']==int(x['FamilyIndex'])and f['country_index']==int(x['CountryIndex'])
  country[u]=f['country_index']
 # Independent exact ALT readback covers both existing explicit moves and newly encoded TEAM bytes.
 plans={x['TMID']:x for x in read(W/'club-plan.json')+read(W/'foreign-owner-plan.json')}
 for item in mapping:
  uid=int(item['ClubUID']);plan=plans[item['TMID']];rec=byuid[uid];actual_alt=struct.unpack_from('<i',a,rec['Start']+15)[0]
  if plan.get('DesiredAlternative')is not None:expected_alt=plan['DesiredAlternative']
  elif uid in original_world:
   prior=next(x for x in original if x['ClubUID']==uid);expected_alt=alts.get(uid,{}).get('After',struct.unpack_from('<i',old,prior['Start']+15)[0])
  else:expected_alt=-1
  assert actual_alt==expected_alt,('exact_native_alternate_assignment',uid,actual_alt,expected_alt)
 # Untargeted native linked reserves take country from their existing family index.
 original_world={x['ClubUID']:x for x in read(B/'native-world-identities.json')}
 original_records={x['ClubUID']:x for x in original}
 for r in rr:
  if country[r['ClubUID']]is None:
   fi=r.get('FamilyIndex',-1)
   if fi<0:
    # Some existing variable-tail reserves expose no FamilyIndex in the flat exporter.
    # Require the separately established source parent and unchanged native TEAM body.
    ow=original_world[r['ClubUID']];prior=original_records[r['ClubUID']]
    assert ow['TeamIndex']==r['TeamIndex']==prior['TeamIndex']
    assert ow['ParentUID']in fu and fu[ow['ParentUID']]['index']==ow['FamilyIndex']
    assert old[prior['Start']+23:prior['Footer']+8]==a[r['Start']+23:r['Footer']+8]
    fi=fu[ow['ParentUID']]['index']
   assert 0<=fi<len(families),('native_country_unresolved',r['ClubUID'],fi)
   country[r['ClubUID']]=families[fi]['country_index']
 checks=[] # All325 numeric conditions are independently checked by qa/selection_regression.py.
 _,_,co=find_table(a,[x['uid']for x in en['city']],city);base=co+4;span=a[base:min(r['Start']for r in rr)]
 project={int(x['ClubUID'])for x in rows(W/'new-clubs-sugar-daddy-audit.csv')}|{x['uid']for x in sr['additions']if x['kind']=='new_first_team'};verified=[]
 for f in families:
  if f['uid']not in project:continue
  fi=f['index'];off=base+unique(span,struct.pack('<iI',fi-1,families[fi-1]['uid']))+8;cur=Cursor(a,off)
  assert cur.byte()==0;cur.integer();cur.byte();cur.string();cur.byte();cur.string();cur.take(2);cur.num('<H');cur.integer();cur.take(1+12+1+2+4+1+1)
  for _ in range(2):cur.take(cur.byte()*4)
  assert cur.byte()==0 and cur.take(45)[4]==0;verified.append(f['uid'])
 assert set(verified)==project

 # New typed roles and family references are checked against the prepared semantic plan.
 plan_by_uid={int(x.get('ProjectedClubUID') or x['NativeClubUID']):x for x in read(W/'club-plan.json')+read(W/'foreign-owner-plan.json')}
 for x in sr['additions']:
  u=x['uid'];r=byuid[u];p=plan_by_uid[u]
  expected_kind=int(p['RequiredNativeReserveKind']) if x['kind']=='new_linked_reserve' else 0
  assert a[r['Start']+87]==expected_kind,('new_TEAM_kind_mismatch',u,expected_kind,a[r['Start']+87])
  assert struct.unpack_from('<i',a,r['Start']+91)[0]==int(p['ProjectedFamilyIndex']),('new_TEAM_family_mismatch',u)
  if x['kind']=='new_first_team':
   assert fu[u]['embedded_full_name'] and fu[u]['embedded_short_name'],('new_family_empty_embedded_name',u)
 for patch in read(ROOT/'FmLauncher/data/research/CLUB_NAME_LOOKUP_FIX_20261113/correctedpatch-plan-r2.json')['Patches']:
  f=fu[patch['UID']];assert f['embedded_full_name' if patch['Field']=='EmbeddedFull' else 'embedded_short_name']==patch['AfterUTF16']

 # Reprove carried repair against fresh source/target family containers.
 # No historical source offsets are valid after SI resaves.
 old_en_names,_=lang_sections(sl[8]);old_cf,_,_=find_table(load(src,'client_db.dat'),[e['uid']for e in old_en_names['club']],club)
 _,_,old_name_co=find_table(old,[e['uid']for e in old_en_names['city']],city)
 old_name_base=old_name_co+4;old_name_span=old[old_name_base:min(e['Start']for e in original)]
 for uid in {1800200042,1800200058,1800200060}:
  f=fu[uid];of=next(e for e in old_cf if e['uid']==uid);fi=of['index'];assert f['index']==fi
  os=old_name_base+unique(old_name_span,struct.pack('<iI',fi-1,old_cf[fi-1]['uid']))+8;oe=old_name_base+unique(old_name_span,struct.pack('<iI',fi,uid))+8
  ns=base+unique(span,struct.pack('<iI',fi-1,families[fi-1]['uid']))+8;ne=base+unique(span,struct.pack('<iI',fi,uid))+8
  assert old[os:oe]==a[ns:ne],('carried_namefix_family_not_preserved',uid)
  assert of['embedded_full_name']==f['embedded_full_name'] and of['embedded_short_name']==f['embedded_short_name']

 # Preserve both Kolding family records independently of TEAM offsets and edited ancestors.
 old_en,_=lang_sections(sl[8]);old_families,_,_=find_table(load(src,'client_db.dat'),[x['uid']for x in old_en['club']],club)
 _,_,old_co=find_table(old,[x['uid']for x in old_en['city']],city);old_base=old_co+4;old_span=old[old_base:min(r['Start']for r in original)]
 for uid in [2121,928820]:
  f=fu[uid];of=next(z for z in old_families if z['uid']==uid);assert f['index']==of['index'];fi=f['index']
  os=old_base+unique(old_span,struct.pack('<iI',fi-1,old_families[fi-1]['uid']))+8
  oe=old_base+unique(old_span,struct.pack('<iI',fi,uid))+8
  ns=base+unique(span,struct.pack('<iI',fi-1,families[fi-1]['uid']))+8
  ne=base+unique(span,struct.pack('<iI',fi,uid))+8
  assert old[os:oe]==a[ns:ne],('Kolding_FAMILY_changed',uid)

 st,_,_=find_table(a,[x['uid']for x in en['stadium']],lambda x:stadium(x,62));cs,_,_=find_table(c,[x['uid']for x in en['stadium']],lambda x:stadium(x,19))
 assert len(st)==len(cs)and all(x['raw'][:1]+x['raw'][44:]==y['raw']for x,y in zip(st,cs))
 for x in sr['venues']:assert st[x['index']]['uid']==x['uid']and st[x['index']]['raw']==bytes.fromhex(x['raw'])
 report=dict(status='PASS_NATIVE_INVERSE_SCOPE_AND_READBACK_GLOBAL_SELECTION_PENDING',new_TEAM=sr['new_clubs'],new_families=sr['new_families'],new_stadiums=sr['new_stadiums'],both_forms=checks,UID_TEAM_family_projection_exact=True,inverse_SERVER_CLIENT_all_languages=True,unrelated_TEAM_bytes_previous_regional_preserved=True,people_and_other_files_identical=True,project_families_SugarDaddy_OFF=len(verified),global_selection_QA_pending=True,runtime_loader_overlay='not_yet_confirmed_in_user_game',source_unchanged=True,output_hashes=pins(dest))
 dump(W/'root-independent-verification.json',report)
 print('PASS ROOT native inverse/readback:',sr['new_clubs'],'TEAM,',sr['new_families'],'families, all project SugarOFF',len(verified),'global numericQA pending',flush=True)
if __name__=='__main__':main()