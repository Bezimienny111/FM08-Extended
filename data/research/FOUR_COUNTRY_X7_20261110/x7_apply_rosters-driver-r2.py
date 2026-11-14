"""X7 bounded pilot, negative gates, full import and independent verification."""
from pathlib import Path
from collections import Counter
import sys,json,hashlib,shutil,subprocess
sys.dont_write_bytecode=True
from x7prep_rosters_20261110 import B,P,ROOT,read,rows,dump,writecsv,pins
def apply():
 from verify_poland_full_n7_20261108 import verify
 m=read(P/'manifest.json');assert m['counts']['issues']==0 and m['counts']['clubs']==len(rows(P/'club_map.csv'))
 coverage=read(P/'coverage.json');assert all((v['confirmed']>=17 and v['goalkeepers'])or int(next(c['ClubUID']for c in rows(P/'club_map.csv')if c['ClubName']==v['club']))in set(m['partial_roster_club_uids']) for v in coverage),'Core playable squads require full confirmed coverage; lower incomplete clubs are explicit and preserve old members'
 pilot=B/'pilot-r2';assert not pilot.exists();pilot.mkdir();rs=rows(P/'native_players.csv');ids=rows(P/'identities.csv');prov=read(P/'provenance.json');loans=rows(P/'loans.csv');loanids={l['SubjectID'] for l in loans};sel={}
 def take(pred):
  for i,(r,k,p) in enumerate(zip(rs,ids,prov)):
   if pred(r,k,p):sel[k['SubjectID']]=i;return
 for pred in [lambda r,i,p:int(r['ExistingID'])>0,lambda r,i,p:int(r['ExistingID'])<0,lambda r,i,p:int(r['ExistingID'])<0 and r['PosGK']=='20',lambda r,i,p:i['SubjectID'] in loanids,lambda r,i,p:i['SubjectID'] in loanids and int(i['OwnerClubIndex']) not in {int(c['TeamIndex']) for c in rows(P/'club_map.csv')},lambda r,i,p:p.get('talent_estimate',False)]:take(pred)
 for u in m.get('nationality_repairs',{}):take(lambda r,i,p:i['ExistingID']==u)
 for ci in ['167','168','169','79']:
  teams={c['TeamIndex']for c in rows(P/'club_map.csv')if c['CountryIndex']==ci};take(lambda r,i,p:i['PlayingClubIndex']in teams)
 take(lambda r,i,p:any(ord(ch)>127 for ch in r['FirstName']+r['LastName']))
 for c in rows(P/'club_map.csv'):
  if c['Kind']in ['new_first_team','new_linked_reserve']:take(lambda r,i,p:int(r['ExistingID'])<0 and i['PlayingClubIndex']==c['TeamIndex'])
 for f in ['club_map.csv','club_proofs.csv','cleanup_subjects.csv']:shutil.copyfile(P/f,pilot/f)
 writecsv(pilot/'native_players.csv',[rs[i] for i in sel.values()]);writecsv(pilot/'identities.csv',[ids[i] for i in sel.values()]);writecsv(pilot/'loans.csv',[l for l in loans if l['SubjectID'] in sel],fields=list(loans[0]));dump(pilot/'provenance.json',[prov[i] for i in sel.values()])
 pm=dict(m,stage='pilot',status='pilot_prepared',output=str(B/'pilot-db-r2'),prepared_rows=len(sel),prepared_loans=sum(l['SubjectID'] in sel for l in loans),pilot_clubs=len({ids[i]['PlayingClubIndex'] for i in sel.values()}));used={int(ids[i]['ExistingID']) for i in sel.values()};pm['duplicate_proofs']={k:v for k,v in m['duplicate_proofs'].items() if v['canonical_uid'] in used};pm['duplicate_retire_uids']=list(map(int,pm['duplicate_proofs']));pm['prepared_hashes']=pins(pilot);dump(pilot/'manifest.json',pm)
 exe=B/'tools-r2/ApplyX7RosterBatch.exe';editor=B/'tools-r2/FM08_Database_Editor.exe'
 def rawcheck(folder):
  p=subprocess.run([sys.executable,str(ROOT/'FM08-Database-Tools/scratch/verify_x7_native_20261110.py'),folder.name],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300);(folder/'independent.log').write_text(p.stdout+p.stderr,encoding='utf-8');print(p.stdout[-1000:]+p.stderr[-1800:],flush=True);assert p.returncode==0
 # Rejection checks are early, so they do not repeat the expensive native import.
 neg=B/'negative-tests-r2';neg.mkdir(exist_ok=True);negative=[]
 for case in (['wrong_country','missing_club','mandatory_buy']+(['unwitnessed_nation']if m.get('nationality_repairs')else[])):
  d=neg/case;d.mkdir(exist_ok=True)
  for f in P.glob('*'):
   if f.is_file():shutil.copyfile(f,d/f.name)
  z=read(d/'manifest.json');z['output']=str(d/'must-not-exist')
  if case=='unwitnessed_nation':z['nationality_repairs']={}
  if case=='wrong_country':z['target_country_indices']=[167,168,169]
  if case=='missing_club':v=rows(d/'club_map.csv');writecsv(d/'club_map.csv',v[:-1])
  if case=='mandatory_buy':v=rows(d/'loans.csv');v[0]['BuyType']='mandatory';writecsv(d/'loans.csv',v)
  z['prepared_hashes']={k:v for k,v in pins(d).items() if k!='manifest.json'};dump(d/'manifest.json',z)
  result=subprocess.run([str(exe),str(editor),z['source'],z['output'],str(d),'--validate'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90);(d/'run.log').write_text(result.stdout+result.stderr,encoding='utf-8');assert result.returncode!=0 and not Path(z['output']).exists();expected={'wrong_country':'Wrong X7 country set','missing_club':'Incomplete scoped prepared batch','mandatory_buy':'Mandatory/unsupported buy type rejected','unwitnessed_nation':'Unwitnessed nationality correction'}[case];assert expected in result.stdout+result.stderr,(case,result.stderr);negative.append(dict(case=case,rejected=True,expected_error=expected))
 dump(B/'negative-tests.json',negative)
 def run(folder):
  z=read(folder/'manifest.json');p=subprocess.run([str(exe),str(editor),z['source'],z['output'],str(folder)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=1200);(folder/'run.log').write_text(p.stdout+p.stderr,encoding='utf-8');print(p.stdout[-1400:]+p.stderr[-2200:],flush=True);assert p.returncode==0
 run(pilot);rawcheck(pilot);m['pilot_verification_path']=str(pilot/'independent-verification.json');m['pilot_verification_sha256']=hashlib.sha256((pilot/'independent-verification.json').read_bytes()).hexdigest();dump(P/'manifest.json',m);run(P);rawcheck(P)
 publication=dict(status='native_verified_SI_and_career_pending',output=m['output'],output_hashes=pins(Path(m['output'])),counts=m['counts'],SI=False,new_career=False,source_gaps=read(P/'source-gaps.json'));dump(B/'publication.json',publication);print('PASS X7 native country batch; SI/game test pending',flush=True)


if __name__=='__main__':apply()
