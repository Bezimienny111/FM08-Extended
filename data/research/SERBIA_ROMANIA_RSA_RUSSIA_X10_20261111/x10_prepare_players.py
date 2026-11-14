"""Configure existing X7 preparer for the final X10 structural source."""
from x10_pipeline import *
from collections import Counter
import csv
def main():
 import x7prep_rosters_20261110 as p
 p.B=B;p.S=S;p.P=B/'prepared';p.REF='2026-11-11'
 p.CALIBRATION={'Serbia':-20,'Romania':-20,'South Africa':-35,'Russia':-10}
 p.PRIOR=[R/'FOUR_COUNTRY_X7_20261110/prepared']+p.PRIOR
 original=p.profiles
 def profiles():
  result=original()
  for f in result[4]:f['SourceVersion']=f['SourceVersion'].replace('_snapshot_2026_11_10','_snapshot_2026_11_11')
  return result
 p.profiles=profiles
 original_proofs=p.club_proofs
 def club_proofs(source,cm,owners):
  mapped=[dict(x,ParentUID=x.get('ContractFamilyUID')or x.get('ParentUID',''))for x in cm]
  return original_proofs(source,mapped,owners)
 p.club_proofs=club_proofs
 assert read(B/'structure-independent.json')['status']=='pass'
 p.prepare()
 folder=B/'prepared';m=read(folder/'manifest.json');cm=list(csv.DictReader((folder/'club_map.csv').open(encoding='utf-8-sig')));coverage=read(folder/'coverage.json');empty={v['club']for v in coverage if v['confirmed']==0}
 emptyuids=[int(c['ClubUID'])for c in cm if c['ClubName']in empty]
 assert {c['TMID']for c in cm if int(c['ClubUID'])in emptyuids}=={'frf-kse-targu-secuiesc','142733'},('Unexpected empty roster; explicitly reconcile before allowing structural-only',empty)
 m['counts']['actor_clubs']=m['counts']['clubs'];m['counts']['clubs']=len(cm)
 m.update(scope_id='ser-rom-rsa-rus-x10',output=str(ROOT/'Dane/db/TEST_X10'),target_country_indices=[176,164,40,165],structural_only_club_uids=emptyuids,structural_only_policy='Confirmed real club and native league allocation; zero imported actors, existing safe roster preserved; no fake profiles',source_player_audit_from_immutable_X8_people_byte_identical=True,source_reference_date='2026-11-11')
 m['policy']['PA_country_estimate_adjustment']=p.CALIBRATION
 m['policy']['country_calibration_basis']='Explicit project estimate, same established age/real-level model; Russia-10, Serbia/Romania-20, SouthAfrica-35; preserve all existing CA/PA and traits; no implication of SI scouting ratings'
 m['prepared_hashes']={k:v for k,v in pins(folder).items()if k!='manifest.json'}
 dump(folder/'manifest.json',m)
 dump(B/'preparer-configuration.json',dict(shared_preparer=str(ROOT/'FM08-Database-Tools/scratch/x7prep_rosters_20261110.py'),shared_preparer_sha256=hashlib.sha256((ROOT/'FM08-Database-Tools/scratch/x7prep_rosters_20261110.py').read_bytes()).hexdigest(),country_calibration=p.CALIBRATION,prior_batches=[str(v)for v in p.PRIOR],structural_only=emptyuids,scope_id=m['scope_id'],output=m['output'],no_main_editor_rebuild=True))
 print('X10 PREPARED',m['counts'],'structural-only',emptyuids,flush=True)
if __name__=='__main__':main()
