"""Offline integration tests, confined to this research directory. No FM launch."""
import argparse,copy,importlib.util,json,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('thai_pilot',HERE/'thai_pilot_package.py');t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
def main():
 out=HERE/'integration-test-r3';t.require(not out.exists(),'Test output exists');out.mkdir();checks=[]
 def expect_fail(name,f):
  try:f()
  except (ValueError,FileExistsError):checks.append(dict(test=name,result='PASS rejected'))
  else:raise ValueError('Failed to reject: '+name)
 members=t.xmlprofile('T1');bad=copy.deepcopy(members);r=t.ET.fromstring(bad['tha/tha_premier.xml']);r.find("list[@id='stages']/record/integer[@id='number_teams']").set('value','17');bad['tha/tha_premier.xml']=t.xmlbytes(r);expect_fail('stage-required count mismatch',lambda:t.validate_xml(bad,'T1'))
 original=t.efa.parse((t.ROOT/'data/comps.efa').read_bytes());expect_fail('existing member collision',lambda:t.efa.add_member(original,'sco/sco.xml',b'<bad/>'))
 source=t.ROOT/'Dane/db/TEST_X6';structure=t.ROOT/'FmLauncher/data/research/SWEDEN_SELECTION_REPAIR_X6_20261110/X6-native-structure.json';hp=t.pins(source);old=t.read(structure);old['records']=old['records'][:-1];t.write(out/'stale-structure.json',old);expect_fail('stale structure evidence',lambda:t.inventory(source,out/'stale-structure.json'))
 game=out/'isolated-game';game.mkdir();shutil.copyfile(t.ROOT/'fm.exe',game/'fm.exe')
 for rel in t.ARCHIVES:
  dest=game/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(t.ROOT/rel,dest)
 args=argparse.Namespace(package=HERE/'package-r3',profile='T1_T2_DRAFT',game_root=game,source_db=source,source_pins=HERE/'X6-source-pins.json',structure_json=structure,db_name='TEST_X999999',output=out/'draft-plan.json')
 expect_fail('T2 draft cannot install',lambda:t.plan_install(args));args.profile='T1';t.plan_install(args)
 plan=t.read(args.output);t.require(all(game.resolve() in Path(s['target']).resolve().parents for s in plan['archive_steps']),'Test escaped isolated root')
 expect_fail('no installation approval flag',lambda:t.apply_plan(argparse.Namespace(plan=args.output,approve_install=False)))
 t.running_game=lambda:[]  # Offline fixture only; real CLI process guard remains active.
 t.apply_plan(argparse.Namespace(plan=args.output,approve_install=True))
 receipts=[p for p in(HERE/'backups').glob('*/receipt.json')if t.read(p)['plan']['game_root']==str(game.resolve())];t.require(len(receipts)==1,'Fixture receipt ambiguity');receipt=receipts[0]
 for s in plan['archive_steps']:t.require(t.sha(s['target'])==s['after_sha256'],'Fixture install hash')
 dest=Path(plan['target_db']);t.require((dest/'TEST_X999999.xml').exists(),'Metadata rename');metadata=t.ET.parse(dest/'TEST_X999999.xml');t.require(any(v.get('value')=='TEST_X999999'for v in metadata.getroot().iter('string')if v.get('id')=='name'),'Metadata display name')
 for n,h in hp.items():
  if not n.lower().endswith('.xml'):t.require(t.sha(dest/n)==h,'Unexpected DB change: '+n)
 checks.append(dict(test='isolated install, backups, only cloned metadata changed',result='PASS'))
 t.rollback(argparse.Namespace(receipt=receipt,approve_rollback=True))
 for rel,h in t.ARCHIVES.items():t.require(t.sha(game/rel)==h,'Original EFA rollback mismatch');t.require(t.sha(t.ROOT/rel)==h,'Real installed EFA touched')
 expect_fail('double rollback',lambda:t.rollback(argparse.Namespace(receipt=receipt,approve_rollback=True)))
 t.require(t.pins(source)==hp,'Accepted source DB touched');checks.append(dict(test='isolated rollback and protected real source hashes',result='PASS'))
 t.write(out/'test-results.json',dict(status='PASS',scope='offline isolated files only; no actual installed archive mutation; no FM/runtime validation',checks=checks,fixture_receipt=str(receipt),original_source_pins_unchanged=True));print('PASS',len(checks),'offline integration checks')
if __name__=='__main__':main()
