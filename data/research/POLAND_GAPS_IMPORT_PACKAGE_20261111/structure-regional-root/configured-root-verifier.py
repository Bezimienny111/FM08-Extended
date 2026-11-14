"""Independent full inverse and actual-disk verification of private X14 structure."""
from pathlib import Path
from collections import Counter
import sys,struct,hashlib
sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[4];B=Path(__file__).resolve().parent;W=B/'structure-root'
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
from create_italy_structure_i1_20261108 import read,rows,dump,load,pins,languages,lang_sections,find_table,club,city,unique
from audit_poland_v25_common_r1_20261108 import Cursor,stadium
from root_structure import COUNTRY,REQ

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
 normalized=bytearray(a);rp=sr['root_regional_patch'];assert struct.unpack_from('<i',normalized,rp['offset'])[0]==rp['after'];struct.pack_into('<i',normalized,rp['offset'],rp['before'])
 inverse(old,bytes(normalized),sr['SERVER_edits']);inverse(load(src,'client_db.dat'),c,sr['CLIENT_edits'])
 sl=dict(languages((src/'lang_db.dat').read_bytes()));dl=dict(languages((dest/'lang_db.dat').read_bytes()));assert sl.keys()==dl.keys()
 for p in sr['language_proofs']:inverse(sl[p['language']],dl[p['language']],p['edits']);lang_sections(dl[p['language']])
 assert (src/'people_db.dat').read_bytes()==(dest/'people_db.dat').read_bytes()
 for rel in pins(src):
  if rel not in ['server_db.dat','client_db.dat','lang_db.dat']:assert (src/rel).read_bytes()==(dest/rel).read_bytes(),('unrelated_file',rel)
 rr=read(W/'native-structure-after.json')['records'];original=read(W/'native-structure.json')['records'];byuid={x['ClubUID']:x for x in rr}
 assert len(rr)==len(original)+86 and len(rr)==len(byuid)
 moves={x['ClubUID']:x for x in cfg['moves']};alts={x['ClubUID']:x for x in cfg['alternate_moves']};venues={x['ClubUID']:x['StadiumIndex']for x in sr['venue_assignments']}
 for r in original:
  n=byuid[r['ClubUID']];o=old[r['Start']:r['Footer']+8];v=a[n['Start']:n['Footer']+8]
  assert len(o)==len(v)and o[:7]==v[:7]and o[11:15]==v[11:15]and o[23:]==normalized[n['Start']+23:n['Footer']+8],('unrelated_TEAM_bytes',r['ClubUID'])
  assert struct.unpack_from('<i',v,7)[0]==moves.get(r['ClubUID'],{}).get('After',r['CurrentDivisionIndex'])
  assert struct.unpack_from('<i',v,15)[0]==alts.get(r['ClubUID'],{}).get('After',struct.unpack_from('<i',o,15)[0])
  assert struct.unpack_from('<i',v,19)[0]==venues.get(r['ClubUID'],struct.unpack_from('<i',o,19)[0])
 en,_=lang_sections(dl[8]);families,_,_=find_table(c,[x['uid']for x in en['club']],club);fu={x['uid']:x for x in families}
 mapping=rows(W/'club-map.csv')+rows(W/'foreign-owner-map.csv');projection={x['TMID']:x for x in rows(B/'club-map.csv')+rows(B/'foreign-owner-map.csv')}
 assert len(mapping)==304 and len(rows(W/'club-map.csv'))==292
 country={x['ClubUID']:fu[x['ClubUID']]['country_index']if x['ClubUID']in fu else None for x in rr}
 for x in mapping:
  u=int(x['ClubUID']);f=fu[int(x['ParentUID']or u)];r=byuid[u];pr=projection[x['TMID']]
  for field in ['ClubUID','TeamIndex','FamilyIndex','CountryIndex','DivisionIndex']:assert int(x[field])==int(pr[field]),('projection_changed',x['TMID'],field,x[field],pr[field])
  assert r['TeamIndex']==int(x['TeamIndex'])and r['CurrentDivisionIndex']==int(x['DivisionIndex'])and f['index']==int(x['FamilyIndex'])and f['country_index']==int(x['CountryIndex'])
  country[u]=f['country_index']
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
 checks=[]
 for q in read(REQ)['requirements']:
  ci=COUNTRY[q['Country']];di=q['CatalogueIndex']
  for form in [0,1]:
   count=0
   for r in rr:
    if q['CountrySpecific']and country[r['ClubUID']]!=ci:continue
    current,alt,region=(struct.unpack_from('<i',a,r['Start']+off)[0]for off in [7,15,47]);effective=current if form==0 or alt<0 else alt
    if effective==di or region==di:count+=1
   lo=q['Form0Min']if form==0 else q['Form1DefaultMin'];hi=q['Form0Max']if form==0 else q['Form1DefaultMax']
   assert count>=lo and(hi is None or count<=hi),('actual_both_forms',q,form,count)
   checks.append(dict(uid=q['CompetitionUID'],index=di,country=q['Country'],country_scoped=q['CountrySpecific'],form=form,count=count,min=lo,max=hi,passed=True))
 _,_,co=find_table(a,[x['uid']for x in en['city']],city);base=co+4;span=a[base:min(r['Start']for r in rr)]
 project={int(x['ClubUID'])for x in rows(W/'new-clubs-sugar-daddy-audit.csv')}|{x['uid']for x in sr['additions']if x['kind']=='new_first_team'};verified=[]
 for f in families:
  if f['uid']not in project:continue
  fi=f['index'];off=base+unique(span,struct.pack('<iI',fi-1,families[fi-1]['uid']))+8;cur=Cursor(a,off)
  assert cur.byte()==0;cur.integer();cur.byte();cur.string();cur.byte();cur.string();cur.take(2);cur.num('<H');cur.integer();cur.take(1+12+1+2+4+1+1)
  for _ in range(2):cur.take(cur.byte()*4)
  assert cur.byte()==0 and cur.take(45)[4]==0;verified.append(f['uid'])
 assert set(verified)==project
 st,_,_=find_table(a,[x['uid']for x in en['stadium']],lambda x:stadium(x,62));cs,_,_=find_table(c,[x['uid']for x in en['stadium']],lambda x:stadium(x,19))
 assert len(st)==len(cs)and all(x['raw'][:1]+x['raw'][44:]==y['raw']for x,y in zip(st,cs))
 for x in sr['venues']:assert st[x['index']]['uid']==x['uid']and st[x['index']]['raw']==bytes.fromhex(x['raw'])
 report=dict(status='PASS_PRIVATE_NATIVE_STRUCTURE_NOT_SI_OR_RUNTIME',new_TEAM=86,new_families=sr['new_families'],new_stadiums=sr['new_stadiums'],both_forms=checks,UID_TEAM_family_projection_exact=True,inverse_SERVER_CLIENT_all_languages=True,unrelated_TEAM_bytes_previous_regional_preserved=True,people_and_other_files_identical=True,project_families_SugarDaddy_OFF=len(verified),runtime_loader_overlay='not_yet_confirmed_in_user_game',source_unchanged=True,output_hashes=pins(dest))
 dump(W/'root-independent-verification.json',report)
 print('PASS ROOT structure:86TEAM,',sr['new_families'],'families,36 actual form checks,whole inverse,all project SugarOFF',len(verified),flush=True)
if __name__=='__main__':main()