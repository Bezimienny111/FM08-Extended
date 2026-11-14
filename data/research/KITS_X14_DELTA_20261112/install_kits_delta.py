"""Use the already reviewed graphics transaction engine for an additive kit-only delta."""
from pathlib import Path
import importlib.util,sys,argparse,json,re,hashlib
sys.dont_write_bytecode=True
ROOT=Path(r"J:\FM08dev");BASE=Path(__file__).resolve().parent
ENGINE=ROOT/"FmLauncher/data/research/GRAPHICS_COVERAGE_X14_20261112/install_delta.py"
ENGINE_SHA="cc7b0325271e4d65161611a492d751e3eeb9ed3bee9a411da25266e8ae1cd725"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def getengine():
 assert sha(ENGINE)==ENGINE_SHA,"Reviewed transaction engine changed"
 spec=importlib.util.spec_from_file_location("reviewed_graphics_transaction_for_kits",ENGINE);core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
 core.OUT=BASE;core.STAGE=BASE/"staging"
 core.DEST={"kit":ROOT/"Dane/graphics/pictures/kits/2d/modern_2627"}
 core.PATTERNS={"kit":r"graphics/pictures/team/(\d+)/kits/(home|away|third)"}
 core.SIZE={"kit":130}
 def classify(target):
  m=re.fullmatch(core.PATTERNS["kit"],target)
  if not m:raise ValueError("Unexpected kit target "+target)
  return "kit",m[1]+"_"+m[2]
 core.classification=classify
 return core
def prepare(core):
 stagepath=BASE/"stage-ledger.json";stage=read(stagepath)
 assert stage["initial_images"]==stage["known_existing_image_seasons"]==1700
 added=[x for x in stage["rows"] if x["status"]=="add"]
 assert len(added)==382 and not any(x["status"]=="replace_older" for x in stage["rows"])
 assert not any(x.get("modern_conditional_year") is not None for x in added),"Conditional sources need explicit FM08 aliases; not in this approved batch"
 assets=[]
 for row in added:
  path=(Path(row["staging"])).resolve();path.relative_to(BASE/"staging")
  assert sha(path)==row["sha256"]
  core.checkpng(path,130)
  assets.append(dict(path=str(path.relative_to(ROOT)),target=f"graphics/pictures/team/{row['uid']}/kits/{row['slot']}",sha256=row["sha256"]))
 assert len({x["target"] for x in assets})==len(assets)
 dump(BASE/"staging-result.json",dict(assets=assets,source_stage_sha256=sha(stagepath),distribution="FC12 personal use only; no redistribution",public_graphics_modified=False))
 core.plan("all")
 path=BASE/"installation-plan-all.json";plan=read(path)
 plan.update(adapter_sha256=sha(Path(__file__)),adapter_contract="Generic engine uid field stores filename stem clubUID_slot; real club UID and slot are encoded in target and source stage ledger",transaction_engine=str(ENGINE.relative_to(ROOT)),transaction_engine_sha256=ENGINE_SHA,stage_ledger_sha256=sha(stagepath),expected_png_additions=382,expected_initial_kits=1700,expected_final_kits=2082,expected_final_clubs=826,conditional_source_count=0,distribution="FC12 personal use only; no redistribution")
 dump(path,plan)
 print(json.dumps(dict(plan=str(path),status=plan["status"],collisions=len(plan["collisions"]),adapter_sha256=plan["adapter_sha256"],plan_sha256=sha(path),expected_additions=382)),flush=True)
def apply(core,path):
 path=path.resolve();path.relative_to(BASE)
 plan=read(path)
 assert plan["adapter_sha256"]==sha(Path(__file__))
 assert plan["transaction_engine_sha256"]==sha(ENGINE)==ENGINE_SHA
 assert plan["stage_ledger_sha256"]==sha(BASE/"stage-ledger.json")
 assert plan["expected_png_additions"]==382 and plan["expected_initial_kits"]==1700
 assert plan["counts"]=={"kit":382} and plan["conditional_source_count"]==0
 assert not plan["neutralizations"],"Unexpected legacy removals require separate review"
 assert len(list(core.DEST["kit"].glob("*.png")))==1700
 core.apply(path)
 assert len(list(core.DEST["kit"].glob("*.png")))==2082
if __name__=="__main__":
 parser=argparse.ArgumentParser();parser.add_argument("--apply",type=Path);args=parser.parse_args()
 core=getengine()
 if args.apply:apply(core,args.apply)
 else:prepare(core)
