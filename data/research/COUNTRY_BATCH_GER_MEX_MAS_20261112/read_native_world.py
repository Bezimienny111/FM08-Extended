from pathlib import Path
import sys,json,hashlib,struct
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
root=Path('J:/FM08dev');b=Path(__file__).resolve().parent;sys.path.insert(0,str(root/'FM08-Database-Tools/scratch'))
from create_italy_structure_i1_20261108 import load,languages,lang_sections,find_table,club
from audit_poland_v25_common_r1_20261108 import Cursor
src=b/'input/X14-after-SI';m=json.loads((b/'source-freeze.json').read_text())
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert all(h(src/k)==v for k,v in m['hashes'].items())
rr=json.loads((b/'native-structure.json').read_text())['records']
en,_=lang_sections(dict(languages((src/'lang_db.dat').read_bytes()))[8])
a=load(src,'server_db.dat');cc=load(src,'client_db.dat')
cl,_,_=find_table(cc,[v['uid']for v in en['club']],club);cf={f['uid']:f for f in cl};nf={f['uid']:f['names']for f in en['club']};world=[];unresolved=[]
for r in rr:
 f=cf.get(r['ClubUID']);labels=nf.get(r['ClubUID'],[]);parent=None;proof='direct_CLIENT_FAMILY_UID'
 if not f:
  end=r['RosterOffset']+2+4*struct.unpack_from('<H',a,r['RosterOffset'])[0]
  candidates=[]
  for z in range(end,r['Footer']-7):
   if a[z:z+3]!=bytes([0,0,255]):continue
   fi=struct.unpack_from('<i',a,z+3)[0]
   if not(0<=fi<len(cl)):continue
   cur=Cursor(a,z+7)
   try:
    ns=[]
    for _ in range(2):ns.append(cur.string());cur.byte()
    assert cur.p==r['Footer']
   except(AssertionError,ValueError,UnicodeError,struct.error):continue
   candidates.append((fi,ns,z))
  if len(candidates)==1:
   fi,ns,z=candidates[0];f=cl[fi];parent=f['uid'];labels=labels+ns;proof='unique_TEAM_tail_00_00_FF_family_index_two_strings_exact_footer';proof_offset=z+3
  else:
   unresolved.append(dict(ClubUID=r['ClubUID'],TeamIndex=r['TeamIndex'],Reason='no_unique_family_tail',candidates=candidates));continue
 if parent is None:labels=labels+[f['embedded_full_name'],f['embedded_short_name']]
 world.append(dict(ClubUID=r['ClubUID'],TeamIndex=r['TeamIndex'],FamilyIndex=f['index'],FamilyUID=f['uid'],ParentUID=parent,Country=f['country_index'],Names=list(dict.fromkeys(n for n in labels if n)),CurrentDivision=r['CurrentDivisionIndex'],YearFounded=f['year_founded_raw'],StadiumIndex=struct.unpack_from('<i',a,r['Start']+19)[0],FamilyProof=proof,FamilyProofOffset=proof_offset if parent else None))
for name,value in [('native-world-identities.json',world),('native-world-unresolved.json',unresolved),('competition-catalog.json',[dict(index=i,**v)for i,v in enumerate(en['comp'])]),('native-nation-catalog.json',[dict(index=i,**v)for i,v in enumerate(en['nation'])])]:
 (b/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert all(h(src/k)==v for k,v in m['hashes'].items())
print('WORLD',len(world),'UNRESOLVED',len(unresolved),'CHILDREN',sum(v['ParentUID']is not None for v in world))
print('Witness',next((v for v in world if v['ClubUID']==1800002012),None))
