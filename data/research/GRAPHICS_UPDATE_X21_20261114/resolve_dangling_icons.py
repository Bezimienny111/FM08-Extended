from pathlib import Path
import json,sys,hashlib,collections,importlib.util,xml.etree.ElementTree as ET,argparse
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;ENGINE=O/'install_delta.py';ENGINE_SHA='275e74017d3bd4fce97bd4f64ff0e22481a6ad7432b96a2e639b8be14b637e2c'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
EXPECTED={'graphics/pictures/club/'+str(u)+'/icon'for u in[5643279,2068,1978,3500217,1987]}
CONFIGS={r'Dane\graphics\pictures\logos\old_form\small\clubs\cze\all\config.xml',r'Dane\graphics\pictures\logos\old_form\small\clubs\fra\Ligue 2 and other\config.xml'}
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--apply',type=Path);a=parser.parse_args();assert sha(ENGINE)==ENGINE_SHA
 sp=importlib.util.spec_from_file_location('reviewed_delta_transaction',ENGINE);core=importlib.util.module_from_spec(sp);sp.loader.exec_module(core)
 rejected=O/'installation-plan-all.json';p=O/'installation-plan-all-reviewed-dangling.json'
 if a.apply:
  assert a.apply.resolve()==p.resolve();d=read(p);assert d['review_adapter_sha256']==sha(Path(__file__))and d['rejected_plan_sha256']==sha(rejected)
  assert {m['to']for c in d['neutralizations']for m in c['removed_maps']}==EXPECTED
  assert {c['path']for c in d['neutralizations']}==CONFIGS and sum(c['removed']for c in d['neutralizations'])==5
  core.apply(p);return
 d=read(rejected);assert d['status']=='BLOCKED_COLLISIONS'and len(d['collisions'])==5
 assert {c['target']for c in d['collisions']}==EXPECTED and {c['config']for c in d['collisions']}==CONFIGS
 assert all(c['type']=='existing_target_elsewhere'and c['existing_file']is False for c in d['collisions'])
 grouped=collections.defaultdict(list)
 for c in d['collisions']:
  assert not(core.ROOT/c['source']).exists();grouped[c['config']].append(c)
 changes=[]
 for rel,cs in sorted(grouped.items()):
  path=core.safe(core.ROOT/rel,core.GRAPHICS);assert sha(path)==d['all_public_config_pins'][rel]
  targets={c['target']for c in cs};selected=[dict(n.attrib)for n in ET.parse(path).getroot().iter('record')if n.get('to')in targets];assert len(selected)==len(cs)
  after,old,new=core.neutralbytes(path,selected);assert old-new==len(cs)
  changes.append(dict(path=rel,neutralization=True,before_sha256=sha(path),after_sha256=hashlib.sha256(after).hexdigest(),old_mappings=old,new_mappings=new,removed=len(selected),removed_maps=selected,source_png_pins={}))
 d.update(status='READY_FOR_ROOT_REVIEW',collisions=[],neutralizations=changes,review_adapter_sha256=sha(Path(__file__)),rejected_plan_sha256=sha(rejected),neutralization_policy='EXACT5_DANGLING_ICON_MAPS_IN2CONFIGS_ONLY; nonexistent PNGs; preserve all other maps and all PNGs')
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(status=d['status'],plan=str(p),sha256=sha(p),counts=d['counts'],neutral_maps=5,neutral_configs=2,collisions=0)),flush=True)
if __name__=='__main__':main()
