"""X10 local configuration of verified structural writer; original editor and sources unchanged."""
from x10_pipeline import *
import types
def prepare_tools():
 out=B/'tools';out.mkdir(exist_ok=True)
 ed=Path(read(B/'manifest.json')['editor']);dest=out/ed.name
 if not dest.exists():shutil.copyfile(ed,dest)
 assert hashlib.sha256(dest.read_bytes()).hexdigest()==read(B/'manifest.json')['editor_sha256']
 import batch_three_countries_b1_20261109 as fin
 fin.B=B;fin.finance_audit()
 src=ROOT/'FM08-Database-Tools/scratch/apply_four_country_structure_x7_20261110.py'
 original=src.read_text(encoding='utf-8')
 s=original.replace("B=R/'FOUR_COUNTRY_X7_20261110'","B=R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111'")
 s=s.replace('1800030001+len(additions)','1800110001+len(additions)').replace('1800031001+len(venueadd)','1800120001+len(venueadd)')
 old="assert f['country_index']==-1 or(u==5720002 and f['country_index']==172 and cn==152 and x['CountryCorrectionProof']['expected']==172)"
 assert old in s
 s=s.replace(old,"assert u in [136465,130501] and f['country_index']==-1 and x.get('NativeCountryRepairTo')==cn")
 needle=" cfg=read(B/'structure-config.json');planned=cfg['moves']"
 assert needle in s
 s=s.replace(needle," cfg=read(B/'structure-config.json')\n for q in cfg['requirements']:\n  if q['max']==-1:q['max']=None\n cfg['expected_count_deltas']={d:v['current']for d,v in cfg['expected_count_deltas'].items()if v['current']}\n planned=cfg['moves']"+"""
 for move in cfg.get('alternate_moves',[]):
  r=byuid[move['ClubUID']];at=r['Start']+15;before=struct.unpack_from('<i',a,at)[0];assert before==move['Before']
  if before!=move['After']:edits.append((at,4,struct.pack('<i',move['After'])))
""")
 s=s.replace("  if before:edits.append((at,1,b'\\0'))","  edits.append((at,1,b'\\0'))")
 old="assert a[old['Start']+15:old['Start']+19]==s[new['Start']+15:new['Start']+19],('alternate_league_changed',old['ClubUID'])"
 new="expected_alt=next((q['After']for q in cfg.get('alternate_moves',[])if q['ClubUID']==old['ClubUID']),struct.unpack_from('<i',a,old['Start']+15)[0]);assert struct.unpack_from('<i',s,new['Start']+15)[0]==expected_alt,('undeclared_alternate_league_changed',old['ClubUID'])"
 assert old in s;s=s.replace(old,new)
 compile(s,str(out/'ApplyX10Structure.py'),'exec');(out/'ApplyX10Structure.py').write_text(s,encoding='utf-8')
 dump(out/'structure-adapter-manifest.json',dict(source=str(src),source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),configured_sha256=hashlib.sha256(s.encode()).hexdigest(),editor_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),main_editor_rebuilt=False,game_engine_changed=False,changes=['batch path only','fresh noncolliding club/stadium UID ranges','two pinned missing-country repairs mirrored SERVER/CLIENT','explicit planned alternative league fields','explicit zero writes for all project SugarDaddy flags','retain unrelated-alternate verification']))
 print('STRUCTURE ADAPTER READY, editor unchanged.',flush=True)
def apply():
 p=B/'tools/ApplyX10Structure.py';s=p.read_text(encoding='utf-8');ns={'__name__':'x10_structural_adapter','__file__':str(ROOT/'FM08-Database-Tools/scratch/apply_four_country_structure_x7_20261110.py')};exec(compile(s,str(p),'exec'),ns);ns['main']()
if __name__=='__main__':
 if sys.argv[1]=='tools':prepare_tools()
 elif sys.argv[1]=='apply':apply()
 else:raise ValueError(sys.argv[1])
