"""One negative suite, bounded representative pilot, then one full X10 native import."""
from pathlib import Path
import sys,json,hashlib,shutil,subprocess
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev');B=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def pins(p):return{str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest()for f in sorted(p.rglob('*'))if f.is_file()}

from collections import Counter
import csv,copy
P=B/'prepared';EXE=B/'tools/ApplyX14RosterBatch.exe';EDITOR=B/'tools/FM08_Database_Editor.exe'
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8-sig',newline='')))
def save(p,rs,fields=None):
 with Path(p).open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rs[0]));w.writeheader();w.writerows(rs)
def run(folder,validate=False):
 m=read(folder/'manifest.json');args=[EXE,EDITOR,m['source'],m['output'],folder]+(['--validate']if validate else[]);z=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=1200);(folder/'run.log').write_text(z.stdout+z.stderr,encoding='utf-8');return z
def verify(folder):
 import verify_x14_native as v
 v.B=B;old=sys.argv;sys.argv=['verify',folder.name]
 try:v.main()
 finally:sys.argv=old
def negatives():
 assert read(B/'contract-preflight.json')['status']=='pass'
 assert not(B/'negative-tests-r2.json').exists()
 m=read(P/'manifest.json');targets=rows(P/'club_map.csv');ids=rows(P/'identities.csv');actorclub=next(c for c in targets if any(int(i['PlayingClubIndex'])==int(c['TeamIndex'])for i in ids));tests=[]
 cases=[('source_pin','Source hash differs'),('country_set','Wrong X14 country set'),('empty_unknown','Structural-only UID outside target map'),('empty_with_actor','Declared structural-only club has actors'),('unlisted_empty','Unlisted empty club'),('mandatory_buy','Mandatory/unsupported buy type rejected'),('csv_pin','Prepared pin missing/differs')]
 for name,expected in cases:
  d=B/'negative-cases-r2'/name;assert not d.exists();d.mkdir(parents=True)
  for filename in ['native_players.csv','identities.csv','loans.csv','club_map.csv','club_proofs.csv','cleanup_subjects.csv']:shutil.copyfile(P/filename,d/filename)
  n=copy.deepcopy(m);n['output']=str(B/('negative-no-output-'+name));n['prepared_hashes']={k:v for k,v in pins(d).items()}
  if name=='source_pin':n['source_hashes']['client_db.dat']='0'*64
  elif name=='country_set':n['target_country_indices']=[176,164,40,173]
  elif name=='empty_unknown':n['structural_only_club_uids'].append(1999999999)
  elif name=='empty_with_actor':n['structural_only_club_uids'].append(int(actorclub['ClubUID']))
  elif name=='unlisted_empty':n['structural_only_club_uids']=n['structural_only_club_uids'][1:]
  elif name=='mandatory_buy':
   rs=rows(d/'loans.csv');rs[0]['BuyType']='mandatory';save(d/'loans.csv',rs);n['prepared_hashes']['loans.csv']=pins(d)['loans.csv']
  elif name=='csv_pin':
   with(d/'native_players.csv').open('a',encoding='utf-8')as f:f.write('\n')
  dump(d/'manifest.json',n);z=run(d,True);rejected=z.returncode!=0 and expected in z.stdout+z.stderr and not Path(n['output']).exists();assert rejected,(name,z.stdout[-1200:],z.stderr[-1800:]);tests.append(dict(case=name,rejected=True,expected_reason=expected,output_not_created=True));print('NEGATIVE PASS',name,flush=True)
 dump(B/'negative-tests-r2.json',tests)
def pilot():
 assert all(x['rejected']for x in read(B/'negative-tests-r2.json'))
 m=read(P/'manifest.json');ps=rows(P/'native_players.csv');ids=rows(P/'identities.csv');prov=read(P/'provenance.json');loans=rows(P/'loans.csv');cm=rows(P/'club_map.csv');loanids={l['SubjectID']for l in loans};sel={}
 def take(pred):
  for i,(p,k,v)in enumerate(zip(ps,ids,prov)):
   if pred(p,k,v):sel[k['SubjectID']]=i;return
 for pred in [lambda p,i,v:int(p['ExistingID'])>0,lambda p,i,v:int(p['ExistingID'])<0,lambda p,i,v:int(p['ExistingID'])<0 and p['PosGK']=='20',lambda p,i,v:i['SubjectID']in loanids,lambda p,i,v:v.get('talent_estimate',False),lambda p,i,v:any(ord(x)>127 for x in p['FirstName']+p['LastName'])]:take(pred)
 for c in cm:
  if c['Kind']in ['new_first_team','new_linked_reserve']:take(lambda p,i,v:i['PlayingClubIndex']==c['TeamIndex'])
 for c in ['162','160','194']:
  teams={x['TeamIndex']for x in cm if x['CountryIndex']==c};take(lambda p,i,v:i['PlayingClubIndex']in teams)
 for u in m.get('nationality_repairs',{}):take(lambda p,i,v:i['ExistingID']==u)
 for owner in {l['OwnerClubIndex']for l in loans}:take(lambda p,i,v:i['SubjectID']in loanids and i['OwnerClubIndex']==owner)
 # Cover every reused native prefix/contract format and all17 literal-DOB corrections before full writer.
 for idx,k in enumerate(ids):
  if int(k['ExistingID'])>0:sel[k['SubjectID']]=idx
 for c in cm:
  if c.get('OwnFamilyIndex')or c.get('ParentUID'):take(lambda p,i,v:i['PlayingClubIndex']==c['TeamIndex'])
 d=B/'pilot-r6';assert not d.exists();d.mkdir()
 for f in ['club_map.csv','club_proofs.csv','cleanup_subjects.csv']:shutil.copyfile(P/f,d/f)
 save(d/'native_players.csv',[ps[i]for i in sel.values()]);save(d/'identities.csv',[ids[i]for i in sel.values()]);save(d/'loans.csv',[l for l in loans if l['SubjectID']in sel],list(loans[0]));dump(d/'provenance.json',[prov[i]for i in sel.values()])
 n=copy.deepcopy(m);n.update(status='pilot_prepared',stage='pilot',output=str(B/'pilot-db-r6'),prepared_rows=len(sel),prepared_loans=sum(l['SubjectID']in sel for l in loans),pilot_clubs=len({ids[i]['PlayingClubIndex']for i in sel.values()}));used={int(ids[i]['ExistingID'])for i in sel.values()};n['duplicate_proofs']={k:v for k,v in m['duplicate_proofs'].items()if v['canonical_uid']in used};n['duplicate_retire_uids']=list(map(int,n['duplicate_proofs']));n['prepared_hashes']=pins(d);dump(d/'manifest.json',n)
 print('PILOT',len(sel),'rows',n['prepared_loans'],'loans',n['pilot_clubs'],'actorclubs',flush=True)
 z=run(d);print(z.stdout[-1800:]+z.stderr[-2200:],flush=True);assert z.returncode==0
 verify(d)
 m['pilot_verification_path']=str(d/'independent-verification.json');m['pilot_verification_sha256']=hashlib.sha256((d/'independent-verification.json').read_bytes()).hexdigest();dump(P/'manifest.json',m)
 print('PILOT NATIVE+INVERSE PASS',flush=True)
def full():
 m=read(P/'manifest.json');assert read(Path(m['pilot_verification_path']))['status']=='pass';assert not Path(m['output']).exists()
 z=run(P);print(z.stdout[-2000:]+z.stderr[-2500:],flush=True);assert z.returncode==0
 verify(P);dump(B/'native-publication-pending-metadata.json',dict(status='native_verified_metadata_pending_SI_game_not_tested',output=m['output'],counts=m['counts'],output_hashes=pins(Path(m['output'])),SI=False,new_career=False,season=False))
 print('FULL X14 NATIVE+INVERSE PASS',flush=True)
def accept_pilot():
 d=B/'pilot-r6';verify(d)
 m=read(P/'manifest.json');assert read(d/'full-native.json')['source']==m['source']
 m['pilot_verification_path']=str(d/'independent-verification.json');m['pilot_verification_sha256']=hashlib.sha256((d/'independent-verification.json').read_bytes()).hexdigest();dump(P/'manifest.json',m)
 print('PILOT NATIVE+INVERSE PASS; pinned for full',flush=True)
if __name__=='__main__':
 if sys.argv[1]=='validate':
  z=run(P,True);print(z.stdout[-2000:]+z.stderr[-4000:],flush=True);assert z.returncode==0
 elif sys.argv[1]=='accept_pilot':accept_pilot()
 elif sys.argv[1]=='negative':negatives()
 elif sys.argv[1]=='pilot':pilot()
 elif sys.argv[1]=='full':full()
 else:raise ValueError(sys.argv[1])
