from pathlib import Path
from collections import defaultdict,Counter
import sys,json,csv,copy,hashlib,shutil,subprocess,importlib.util
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent;P=B/'prepared';T=B/'tools'
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def save(p,rs,fields=None):
 with p.open('w',encoding='utf-8-sig',newline='')as f:w=csv.DictWriter(f,fieldnames=fields or list(rs[0]));w.writeheader();w.writerows(rs)
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pins(p):return{str(f.relative_to(p)):h(f)for f in sorted(p.rglob('*'))if f.is_file()and f.name!='manifest.json'}
def run(d,validate=False):
 m=read(d/'manifest.json');args=[T/'ApplyBatchRoster-Current.exe',T/'FM08_Database_Editor.exe',m['source'],m['output'],d]+(['--validate']if validate else[])
 with(d/'run.log').open('w',encoding='utf-8')as log:z=subprocess.run(list(map(str,args)),stdout=log,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',timeout=3600)
 z.stdout=(d/'run.log').read_text(encoding='utf-8');z.stderr='';return z
def verify(d):
 path=B/'verify_roster.py'
 if not path.exists():
  s=(R/'POLAND_GAPS_IMPORT_PACKAGE_20261111/verify_x14_native.py').read_text(encoding='utf-8').replace("ROOT=Path(__file__).resolve().parents[2]","ROOT=Path('J:/FM08dev')").replace("B=ROOT/'FmLauncher/data/research/FOUR_COUNTRY_X7_20261110'","B=ROOT/'FmLauncher/data/research/COUNTRY_BATCH_IDN_IND_HKG_20261112'")
  path.write_text(s,encoding='utf-8')
 spec=importlib.util.spec_from_file_location('x15_independent',path);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);v.B=B;old=sys.argv;sys.argv=['verify',d.name]
 try:v.main()
 finally:sys.argv=old
def negative():
 m=read(P/'manifest.json');tests=[]
 for name,expected in [('source_pin','Source hash differs'),('country_set','Wrong current five-country set'),('unknown_structural_uid','Structural-only UID outside target map'),('structural_uid_with_actor','Declared structural-only club has actors'),('csv_pin','Prepared pin missing/differs'),('mandatory_buy','Mandatory/unsupported buy type rejected')]:
  d=B/'negative-cases'/name;assert not d.exists();d.mkdir(parents=True)
  for filename in ['native_players.csv','identities.csv','loans.csv','club_map.csv','club_proofs.csv','cleanup_subjects.csv']:shutil.copyfile(P/filename,d/filename)
  n=copy.deepcopy(m);n['output']=str(B/('negative-no-output-'+name));n['prepared_hashes']=pins(d)
  if name=='source_pin':n['source_hashes']['client_db.dat']='0'*64
  elif name=='country_set':n['target_country_indices']=[80,191]
  elif name=='unknown_structural_uid':n['structural_only_club_uids'].append(1999999999)
  elif name=='structural_uid_with_actor':n['structural_only_club_uids'].append(int(rows(P/'club_map.csv')[0]['ClubUID']))
  elif name=='csv_pin':
   with(d/'native_players.csv').open('a',encoding='utf-8')as f:f.write('\n')
  elif name=='mandatory_buy':
   ls=rows(d/'loans.csv');ls[0]['BuyType']='mandatory';save(d/'loans.csv',ls);n['prepared_hashes']['loans.csv']=h(d/'loans.csv')
  dump(d/'manifest.json',n);z=run(d,True);passed=z.returncode!=0 and expected in z.stdout+z.stderr and not Path(n['output']).exists()
  tests.append(dict(case=name,rejected=passed,expected=expected,exit_code=z.returncode,output_not_created=not Path(n['output']).exists()))
  assert passed,(name,z.stdout[-1200:],z.stderr[-2200:]);print('NEGATIVE PASS',name,flush=True)
 dump(B/'negative-tests.json',tests)
def pilot():
 assert all(t['rejected']for t in read(B/'negative-tests.json'))
 m=read(P/'manifest.json');ps=rows(P/'native_players.csv');ids=rows(P/'identities.csv');prov=read(P/'provenance.json');ls=rows(P/'loans.csv')
 byclub=defaultdict(list)
 for i,ident in enumerate(ids):byclub[ident['PlayingClubIndex']].append(i)
 selected=set()
 for indices in byclub.values():
  selected.add(indices[0])
  for reuse in [True,False]:
   choices=[i for i in indices if (int(ids[i]['ExistingID'])>0)==reuse]
   if choices:selected.add(choices[0])
  gks=[i for i in indices if ps[i]['PosGK']=='20']
  if gks:selected.add(gks[0])
 loanids={l['SubjectID']for l in ls}
 selected.update(i for i,k in enumerate(ids)if k['SubjectID']in loanids)
 selected=sorted(selected);d=B/'pilot';assert not d.exists();d.mkdir()
 for f in ['club_map.csv','club_proofs.csv','cleanup_subjects.csv']:shutil.copyfile(P/f,d/f)
 save(d/'native_players.csv',[ps[i]for i in selected]);save(d/'identities.csv',[ids[i]for i in selected]);save(d/'loans.csv',ls);dump(d/'provenance.json',[prov[i]for i in selected])
 n=copy.deepcopy(m);n.update(status='pilot_prepared',stage='pilot',output=str(B/'pilot-db'),prepared_rows=len(selected),prepared_loans=len(ls),pilot_clubs=len(byclub));n['prepared_hashes']=pins(d);dump(d/'manifest.json',n)
 print('PILOT',len(selected),'rows',len(ls),'loans',len(byclub),'actorclubs',flush=True)
 z=run(d);print(z.stdout[-1500:]+z.stderr[-2200:],flush=True);assert z.returncode==0;verify(d)
 m['pilot_verification_path']=str(d/'independent-verification.json');m['pilot_verification_sha256']=h(d/'independent-verification.json');dump(P/'manifest.json',m);print('PILOT NATIVE+INVERSE PASS',flush=True)
def full():
 m=read(P/'manifest.json');assert read(Path(m['pilot_verification_path']))['status']=='pass';assert not Path(m['output']).exists()
 z=run(P);print(z.stdout[-1800:]+z.stderr[-2600:],flush=True);assert z.returncode==0;verify(P)
 dump(B/'native-roster-stage.json',dict(status='roster_native_verified_legacy_rating_patch_pending',output=m['output'],counts=m['counts'],source= m['source'],output_hashes={str(p.relative_to(Path(m['output']))):h(p)for p in sorted(Path(m['output']).rglob('*'))if p.is_file()},SI=False,new_career=False,season=False))
 print('FULL NATIVE+INVERSE PASS',flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
