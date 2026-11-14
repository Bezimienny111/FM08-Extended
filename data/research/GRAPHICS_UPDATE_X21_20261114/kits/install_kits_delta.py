"""Kit-only adapter over the reviewed graphics transaction; plan default, no FM controls."""
from pathlib import Path
import sys,json,re,hashlib,importlib.util,argparse
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent;ENGINE=BASE.parent/'install_delta.py';ENGINE_SHA='275e74017d3bd4fce97bd4f64ff0e22481a6ad7432b96a2e639b8be14b637e2c'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def main():
 args=argparse.ArgumentParser();args.add_argument('--apply',type=Path);a=args.parse_args()
 assert sha(ENGINE)==ENGINE_SHA
 sp=importlib.util.spec_from_file_location('guarded_graphics_transaction',ENGINE);core=importlib.util.module_from_spec(sp);sp.loader.exec_module(core);core.OUT=BASE;core.STAGE=BASE/'staging'
 core.DEST={'kit':core.GRAPHICS/'pictures/kits/2d/modern_2627'};core.SIZE={'kit':130};core.PATTERNS={'kit':r'graphics/pictures/team/(\d+)/kits/(home|away|third)'}
 def classify(target):
  m=re.fullmatch(core.PATTERNS['kit'],target);assert m,'Unexpected kit target';return 'kit',m[1]+'_'+m[2]
 core.classification=classify
 ledger=read(BASE/'stage-ledger.json');stage=read(BASE/'staging-result.json');assert ledger['initial_images']==2082 and len(stage['assets'])==1707
 assert sum(x['status']=='add'for x in ledger['rows'])==1707 and not any(x['status']=='replace_older'for x in ledger['rows'])
 assert all(x.get('modern_conditional_year')is None for x in ledger['rows']if x['status']=='add')
 if not a.apply:
  core.plan('all');p=BASE/'installation-plan-all.json';d=read(p);d.update(adapter_sha256=sha(Path(__file__)),stage_ledger_sha256=sha(BASE/'stage-ledger.json'),expected_initial_kits=2082,expected_additions=1707,expected_final_kits=3789,distribution='FC12 LOCAL PERSONAL USE ONLY; NO REDISTRIBUTION');p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Kit plan',d['status'],'collisions',len(d['collisions']),'SHA256',sha(p),flush=True)
 else:
  p=a.apply.resolve();p.relative_to(BASE);d=read(p);assert d['adapter_sha256']==sha(Path(__file__))and d['stage_ledger_sha256']==sha(BASE/'stage-ledger.json');assert d['counts']=={'kit':1707}and not d['neutralizations'];assert len(list(core.DEST['kit'].glob('*.png')))==2082;core.apply(p);assert len(list(core.DEST['kit'].glob('*.png')))==3789
if __name__=='__main__':main()
