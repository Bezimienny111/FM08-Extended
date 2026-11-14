"""Bounded post-roster CA/PA words only. Never touches public DB; no new random draws."""
from pathlib import Path
import ast,csv,json,hashlib,shutil,struct,zlib,subprocess,sys
from datetime import date
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent;P=B/'prepared'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pins(d):return{str(p.relative_to(d)):sha(p)for p in sorted(d.rglob('*'))if p.is_file()}
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def audit(src,out):
 assert not out.exists()
 tool=B/'tools/ApplyVerifiedNativeSquads.exe';editor=B/'tools/FM08_Database_Editor.exe'
 z=subprocess.run([str(tool),str(editor),str(src),str(out),'--audit'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600)
 out.with_suffix('.log').write_text(z.stdout+z.stderr,encoding='utf-8');assert z.returncode==0,z.stderr[-1000:]
 return rows(out/'players.csv')
def main():
 assert len(sys.argv)==3,'private-roster-source new-private-rating-output'
 source=Path(sys.argv[1]).resolve();dest=Path(sys.argv[2]).resolve()
 assert source.is_relative_to(B.resolve())and dest.is_relative_to(B.resolve())and source!=dest
 assert source.is_dir()and not dest.exists()
 full=read(P/'full-native.json');assert Path(full['output']).resolve()==source and full['status']=='pass'
 prepared=read(P/'manifest.json');planfile=P/'legacy-rating-repairs.csv'
 assert sha(planfile)==prepared['prepared_hashes']['legacy-rating-repairs.csv']
 plan=rows(planfile);allowed={int(x['UID']):x for x in plan};assert len(allowed)==len(plan)>0
 original=pins(source)
 assert {k:v.lower()for k,v in original.items()}=={k:v.lower()for k,v in read(B/'native-roster-stage.json')['output_hashes'].items()}
 before_folder=B/'ratings-audit-before'
 live=rows(before_folder/'players.csv')if before_folder.exists()else audit(source,before_folder)
 byuid={int(x['ID']):x for x in live};assert len(byuid)==len(live)
 typed={int(x['Uid']):x for x in full['actor_after']}
 typed_subjects={int(x['uid']):x for x in full['subjects']}
 typed_witnesses=[]
 # Reuse independently proven X11 physical record/table/inverse algorithms, not its CLI or output globals.
 helper=R/'CA_PA_REPAIR_X11_20261111/repair_x11.py';tree=ast.parse(helper.read_text(encoding='utf-8'))
 env=dict(Path=Path,hashlib=hashlib,struct=struct,zlib=zlib,NEIGHBOR_AUDIT={int(x['PersonIndex']):x for x in live})
 names={'decode','one','patch','table_bounds','locate'}
 for node in tree.body:
  if isinstance(node,ast.FunctionDef)and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),str(helper),'exec'),env)
 orighelper=ROOT/'FM08-Database-Tools/scratch/create_club_stadium_native_n1_20261108.py';t=ast.parse(orighelper.read_text(encoding='utf-8-sig'));node=next(n for n in t.body if isinstance(n,ast.FunctionDef)and n.name=='apply_verified')
 exec(compile(ast.Module(body=[node],type_ignores=[]),str(orighelper),'exec'),env)
 header,data=env['decode'](source/'people_db.dat');bounds=env['table_bounds'](data);edits=[];beforeafter=[]
 targets={int(x['ExistingID']):x for x in rows(P/'identities.csv')if int(x['ExistingID'])>0}
 x11={int(x['uid'])for x in rows(R/'CA_PA_REPAIR_X11_20261111/before-after.csv')}
 awards=read(R/'CA_PA_AUDIT_20261111/R2/global-talent-draw-register.json');awarded={int(u)for x in awards['winners']for u in x['known_uids']}
 for uid,q in sorted(allowed.items()):
  assert uid not in x11 and uid not in awarded and q['ProtectedAward']=='False'
  r=byuid[uid];assert r['FirstName']==q['FirstName']and r['LastName']==q['LastName']and r['BirthDate']==targets[uid]['TargetDOB']
  assert(int(r['CA']),int(r['PA']))==(int(q['CA_before']),int(q['PA_before']))
  ca,pa=int(q['CA_after']),int(q['PA_after']);assert 1<=ca<=pa<=200 and pa>=int(q['PA_before'])
  witness=typed[uid];subject=typed_subjects[uid];start=witness['Start'];footer=witness['End']-8;pi=int(r['PersonIndex'])
  assert start>=20 and start+200<=footer<bounds['person_end']
  assert data[start:footer+8]==bytes(witness['Bytes']),('N4 actor raw-body witness differs',uid)
  assert struct.unpack_from('<iB',data,start)==(pi,2)and struct.unpack_from('<iI',data,footer)==(pi,uid)
  assert subject['person']==pi and subject['start']==start and subject['end']==footer+8
  assert subject['first']==r['FirstName']and subject['last']==r['LastName']and subject['dob']==r['BirthDate']
  assert struct.unpack_from('<hh',data,start+11)==(int(r['CA']),int(r['PA']))
  dob=date.fromisoformat(r['BirthDate']);assert struct.unpack_from('<HH',data,witness['Dob']-2)==(dob.timetuple().tm_yday-1,dob.year)
  assert struct.unpack_from('<i',data,witness['Owner'])[0]==int(r['ClubIndex'])==subject['owner']
  assert 0<=struct.unpack_from('<i',data,start+15)[0]<bounds['attributes_count']
  typed_witnesses.append(dict(uid=uid,person_index=pi,start=start,footer=footer,raw_body_sha256=hashlib.sha256(data[start:footer+8]).hexdigest(),CA_before=int(r['CA']),PA_before=int(r['PA']),DOB=r['BirthDate'],owner=int(r['ClubIndex'])))
  edits.extend([(start+11,2,struct.pack('<h',ca)),(start+13,2,struct.pack('<h',pa))])
  beforeafter.append(dict(uid=uid,person_index=int(r['PersonIndex']),person_start=start,person_end=footer+8,CA_offset=start+11,PA_offset=start+13,CA_before=int(r['CA']),PA_before=int(r['PA']),CA_after=ca,PA_after=pa))
 assert len(typed_witnesses)==len(plan)
 dump(B/'legacy-rating-N4-boundary-preflight.json',dict(status='PASS_ALL_PLANNED_PERSON_BOUNDARIES_TYPED',rows=len(plan),whole_N4_output_hashes_match=True,all_personindex_UID_CA_PA_rawDOB_owner_and_entire_actor_bytes_verified=True,full_native_sha256=sha(P/'full-native.json'),audit_before_sha256=sha(B/'ratings-audit-before/players.csv'),no_new_raw_scan=True,output_not_yet_created=not dest.exists(),witnesses=typed_witnesses))
 # Negative in-memory controls before creation of output.
 negative=[]
 for name,mutate in [('PA_below_CA',lambda v:dict(v,PA_after='1')),('PA_decrease',lambda v:dict(v,PA_after=str(int(v['PA_before'])-1)))]:
  v=mutate(plan[0])
  try:assert 1<=int(v['CA_after'])<=int(v['PA_after'])<=200 and int(v['PA_after'])>=int(v['PA_before'])
  except AssertionError:negative.append(name)
  else:raise AssertionError('negative accepted '+name)
 try:env['apply_verified'](data,[(11,2,b'AA'),(12,2,b'BB')])
 except AssertionError:negative.append('overlapping_edits')
 else:raise AssertionError('overlapping edits accepted')
 changed,evidence=env['apply_verified'](data,edits);assert len(changed)==len(data)and changed[bounds['person_end']:]==data[bounds['person_end']:]
 inverse=bytearray(changed)
 for q in beforeafter:struct.pack_into('<hh',inverse,q['CA_offset'],q['CA_before'],q['PA_before'])
 assert bytes(inverse)==data
 assert pins(source)==original
 shutil.copytree(source,dest);(dest/'people_db.dat').write_bytes(header+zlib.compress(changed))
 header2,data2=env['decode'](dest/'people_db.dat');assert header2==header and data2==changed
 after=audit(dest,B/'ratings-audit-after');ab={int(x['ID']):x for x in after};assert set(ab)==set(byuid)
 for uid,r in byuid.items():
  a=ab[uid]
  if uid in allowed:
   q=allowed[uid];assert(int(a['CA']),int(a['PA']))==(int(q['CA_after']),int(q['PA_after']))
   assert{k:v for k,v in a.items()if k not in['CA','PA']}=={k:v for k,v in r.items()if k not in['CA','PA']}
  else:assert a==r,('unrelated_player',uid)
 actual=pins(dest);assert{k:v for k,v in actual.items()if k!='people_db.dat'}=={k:v for k,v in original.items()if k!='people_db.dat'}
 assert pins(source)==original
 dump(B/'ratings-patch-independent.json',dict(status='pass',source=str(source),output=str(dest),source_hashes=original,output_hashes=actual,scoped_UIDs=len(plan),CA_changed=sum(q['CA_before']!=q['CA_after']for q in beforeafter),PA_changed=sum(q['PA_before']!=q['PA_after']for q in beforeafter),all_player_rows_compared=len(live),inverse_entire_PEOPLE=True,only_CA_PA_words_changed=True,all_17B_and_89B_tables_unchanged=True,all_other_files_identical=True,attributes_personality_rosters_loans_contracts_UIDs_DOB_unchanged=True,random_draws=0,negative_controls=negative,plan_sha256=sha(planfile),helper_sha256=sha(helper),original_inverse_helper_sha256=sha(orighelper),offsets=beforeafter,edits=evidence,SI=False,new_career=False,season=False))
 print('PASS post-roster model repairs',len(plan),'UIDs; complete inverse/readback; no public DB writes')
if __name__=='__main__':main()
