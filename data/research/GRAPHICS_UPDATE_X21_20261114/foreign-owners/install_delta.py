"""Plan/apply a pinned graphics delta. Default is plan only. Never closes or accesses FM."""
from pathlib import Path
import argparse,collections,hashlib,json,os,re,shutil,sys,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from PIL import Image
ROOT=Path(r"J:\FM08dev");OUT=Path(__file__).resolve().parent
GRAPHICS=ROOT/"Dane/graphics";STAGE=OUT/"staging"
DEST={"face":GRAPHICS/"pictures/faces/normal/modern_2627","logo":GRAPHICS/"pictures/logos/clubs/normal/modern_2627","icon":GRAPHICS/"pictures/logos/clubs/small/modern_2627"}
PATTERNS={"face":r"graphics/pictures/person/(\d+)/portrait","logo":r"graphics/pictures/club/(\d+)/logo","icon":r"graphics/pictures/club/(\d+)/icon"}
SIZE={"face":180,"logo":180,"icon":20}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def jread(p):return json.loads(p.read_text(encoding="utf-8"))
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def safe(p,base):
 p=p.resolve();p.relative_to(base.resolve());return p
def classification(target):
 for kind,pat in PATTERNS.items():
  m=re.fullmatch(pat,target)
  if m:return kind,m[1]
 raise ValueError("Unexpected target "+target)
def checkpng(p,size):
 with Image.open(p) as im:
  assert im.format=="PNG" and im.size==(size,size),(str(p),im.format,im.size);im.verify()
 with Image.open(p) as im:im.load()
def configbytes(path,assets):
 original=ET.fromstring(path.read_bytes());maps=next(x for x in original.findall("list") if x.get("id")=="maps")
 old=[dict(n.attrib) for n in maps.findall("record")]
 bytarget={}
 for node in maps.findall("record"):
  target=node.get("to")
  if target in bytarget:raise ValueError("Existing duplicate target in destination config")
  bytarget[target]=node
 for asset in sorted(assets,key=lambda a:a["target"]):
  target=asset["target"];source=Path(asset["destination"]).stem
  if target in bytarget:
   if bytarget[target].get("from")!=source:raise ValueError("Mapping collision "+target)
   continue
  node=ET.SubElement(maps,"record",{"from":source,"to":target});bytarget[target]=node
 assert all(any(n.attrib==d for n in maps.findall("record")) for d in old),"Old mapping changed"
 assert [dict(n.attrib) for n in maps.findall("record")][:len(old)]==old
 ET.indent(original,space="\t");return ET.tostring(original,encoding="utf-8"),len(old),len(maps.findall("record"))
def recordattrs(blob):
 return [tuple(sorted(node.attrib.items())) for node in ET.fromstring(blob).iter("record") if node.get("to")]
def neutralbytes(path,removed_maps):
 old=path.read_bytes();wanted=collections.Counter(tuple(sorted(m.items())) for m in removed_maps);spans=[];found=collections.Counter()
 for match in re.finditer(rb"<record\b[^>]*?/\s*>",old):
  node=ET.fromstring(match.group(0));key=tuple(sorted(node.attrib.items()))
  if found[key]<wanted[key]:spans.append((match.start(),match.end()));found[key]+=1
 assert found==wanted,"Exact neutralization maps not found"
 new=old
 for a,b in reversed(spans):new=new[:a]+new[b:]
 remaining=[];take=wanted.copy()
 for key in recordattrs(old):
  if take[key]:take[key]-=1
  else:remaining.append(key)
 assert recordattrs(new)==remaining,"Non-target map changed"
 ET.fromstring(new);return new,len(recordattrs(old)),len(recordattrs(new))
def plan(scope,neutralize=False):
 resultpath=OUT/"staging-result.json";result=jread(resultpath)
 expected={a["target"]:a for a in result["assets"]}
 assert len(expected)==len(result["assets"])
 assets=[]
 for target,entry in sorted(expected.items()):
  kind,uid=classification(target)
  if scope=="faces" and kind!="face":continue
  if scope=="logos" and kind=="face":continue
  source=safe(ROOT/entry["path"],STAGE)
  assert sha(source)==entry["sha256"];checkpng(source,SIZE[kind])
  dest=DEST[kind]/(uid+".png")
  assets.append(dict(kind=kind,uid=uid,target=target,source=str(source.relative_to(ROOT)),destination=str(dest.relative_to(ROOT)),sha256=entry["sha256"],size=SIZE[kind],destination_already_exists=dest.is_file()))
 bytarget={a["target"]:a for a in assets};collisions=[];configpins={};allconfigs=[]
 for config in sorted(GRAPHICS.rglob("config.xml")):
  rel=str(config.relative_to(ROOT));configpins[rel]=sha(config)
  try:tree=ET.parse(config)
  except Exception as e:
   collisions.append(dict(type="unparseable_config",config=rel,error=str(e)));continue
  for node in tree.getroot().iter("record"):
   target=node.get("to")
   if target not in bytarget:continue
   asset=bytarget[target];source=node.get("from","")
   src=config.parent/source
   if src.suffix.lower()!=".png":src=Path(str(src)+".png")
   if config==DEST[asset["kind"]]/"config.xml" and src.resolve()==(ROOT/asset["destination"]).resolve():continue
   identical=src.is_file() and sha(src)==asset["sha256"]
   if not identical:collisions.append(dict(type="existing_target_elsewhere",target=target,config=rel,source=str(src.relative_to(ROOT)),existing_file=src.is_file()))
 for asset in assets:
  dest=ROOT/asset["destination"]
  if dest.exists() and (not dest.is_file() or sha(dest)!=asset["sha256"]):collisions.append(dict(type="existing_destination_differs",destination=asset["destination"],target=asset["target"]))
 changes=[];old_png_pins={}
 for kind in sorted({a["kind"] for a in assets}):
  config=DEST[kind]/"config.xml";selected=[a for a in assets if a["kind"]==kind]
  if not config.is_file():raise ValueError("Missing expected destination config")
  try:after,old,new=configbytes(config,selected)
  except Exception as e:collisions.append(dict(type="destination_mapping_collision",config=str(config.relative_to(ROOT)),error=str(e)));continue
  for image in DEST[kind].rglob("*.png"):
   old_png_pins[str(image.relative_to(ROOT))]=sha(image)
  changes.append(dict(path=str(config.relative_to(ROOT)),before_sha256=sha(config),after_sha256=hashlib.sha256(after).hexdigest(),old_mappings=old,new_mappings=new,append_mappings=new-old))
 neutralizations=[]
 if neutralize:
  pending=collections.defaultdict(list)
  for c in collisions:
   if c["type"]=="existing_target_elsewhere":pending[c["config"]].append(c)
  resolved=set()
  for rel,conflicts in sorted(pending.items()):
   config=safe(ROOT/rel,GRAPHICS);assert config not in {v/"config.xml" for v in DEST.values()}
   targets={c["target"] for c in conflicts}
   selected=[dict(n.attrib) for n in ET.parse(config).getroot().iter("record") if n.get("to") in targets]
   assert len(selected)==len(conflicts)
   after,old,new=neutralbytes(config,selected)
   source_pins={}
   for c in conflicts:
    p=safe(ROOT/c["source"],GRAPHICS)
    if p.is_file():source_pins[c["source"]]=sha(p);old_png_pins[c["source"]]=sha(p)
   neutralizations.append(dict(path=rel,neutralization=True,before_sha256=sha(config),after_sha256=hashlib.sha256(after).hexdigest(),old_mappings=old,new_mappings=new,removed=len(selected),removed_maps=selected,source_png_pins=source_pins))
   resolved.add(rel)
  collisions=[c for c in collisions if not(c["type"]=="existing_target_elsewhere" and c["config"] in resolved)]
  assert sum(c["removed"] for c in neutralizations)==232,"Neutralization scope differs from reviewed 232"
  assert collections.Counter(classification(m["to"])[0] for c in neutralizations for m in c["removed_maps"])=={"face":2,"logo":86,"icon":144}
 output=OUT/("installation-plan-"+scope+("-neutralized" if neutralize else "")+".json")
 data=dict(schema=1,scope=scope,status="BLOCKED_COLLISIONS" if collisions else "READY_FOR_ROOT_REVIEW",script_sha256=sha(Path(__file__)),staging_result_sha256=sha(resultpath),assets=assets,config_changes=changes,all_public_config_pins=configpins,existing_destination_png_pins=old_png_pins,neutralizations=neutralizations,collisions=collisions,counts=dict(collections.Counter(a["kind"] for a in assets)),public_graphics_modified=False,distribution="LOCAL_INSTALL_ONLY; rights not approved for public redistribution")
 dump(output,data)
 print(json.dumps(dict(plan=str(output),status=data["status"],counts=data["counts"],collisions=len(collisions)),ensure_ascii=True))
def assert_game_stopped():
 import subprocess,csv,io
 result=subprocess.run(['tasklist','/FI','IMAGENAME eq fm.exe','/FO','CSV','/NH'],capture_output=True,text=True,check=True,timeout=15)
 live=[row for row in csv.reader(io.StringIO(result.stdout)) if row and row[0].casefold()=='fm.exe']
 assert not live,'FM is running; installation blocked without closing the game'

def apply(path):
 assert_game_stopped()
 path=safe(path,OUT);data=jread(path);assert data["schema"]==1
 assert data["status"]=="READY_FOR_ROOT_REVIEW" and not data["collisions"],"Unresolved collisions"
 assert data["script_sha256"]==sha(Path(__file__)),"Installer changed after review"
 assert data["staging_result_sha256"]==sha(OUT/"staging-result.json")
 assets=data["assets"]
 assert {str(p.relative_to(ROOT)) for p in GRAPHICS.rglob("config.xml")}==set(data["all_public_config_pins"]),"Config set changed after review"
 for rel,digest in data["existing_destination_png_pins"].items():assert sha(safe(ROOT/rel,GRAPHICS))==digest,"Existing PNG changed after review"
 for rel,digest in data["all_public_config_pins"].items():assert sha(safe(ROOT/rel,GRAPHICS))==digest,"Public config changed after review"
 for a in assets:
  kind,uid=classification(a["target"]);assert kind==a["kind"] and uid==a["uid"]
  source=safe(ROOT/a["source"],STAGE);dest=safe(ROOT/a["destination"],DEST[kind])
  assert dest.name==uid+".png" and sha(source)==a["sha256"]
  checkpng(source,SIZE[kind])
  if dest.exists():assert dest.is_file() and sha(dest)==a["sha256"],"Destination collision"
 configs=[]
 for c in data["config_changes"]:
  p=safe(ROOT/c["path"],GRAPHICS);kind=next(k for k,v in DEST.items() if p==v/"config.xml")
  assert sha(p)==c["before_sha256"]
  after,old,new=configbytes(p,[a for a in assets if a["kind"]==kind])
  assert hashlib.sha256(after).hexdigest()==c["after_sha256"] and old==c["old_mappings"] and new==c["new_mappings"]
  configs.append((p,c,after))
 for c in data.get("neutralizations",[]):
  p=safe(ROOT/c["path"],GRAPHICS);assert p not in {v/"config.xml" for v in DEST.values()}
  assert sha(p)==c["before_sha256"]
  after,old,new=neutralbytes(p,c["removed_maps"])
  assert hashlib.sha256(after).hexdigest()==c["after_sha256"] and old==c["old_mappings"] and new==c["new_mappings"]
  configs.append((p,c,after))
 transaction=OUT/"installation-backups"/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ");transaction.mkdir(parents=True)
 dump(transaction/"reviewed-plan.json",data)
 for p,c,after in configs:
  backup=transaction/c["path"];backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(p.read_bytes());assert sha(backup)==c["before_sha256"]
 created=[];written=[]
 try:
  for a in assets:
   dest=ROOT/a["destination"]
   if dest.exists():continue
   dest.parent.mkdir(parents=True,exist_ok=True)
   ready=transaction/"ready-files"/a["kind"]/dest.name;ready.parent.mkdir(parents=True,exist_ok=True)
   with (ROOT/a["source"]).open("rb") as source,ready.open("xb") as target:shutil.copyfileobj(source,target)
   assert sha(ready)==a["sha256"]
   os.link(ready,dest);created.append(a);ready.unlink()
   assert sha(dest)==a["sha256"];checkpng(dest,SIZE[a["kind"]])
  for p,c,after in configs:
   assert_game_stopped()
   assert sha(p)==c["before_sha256"],"Concurrent config change"
   temporary=p.with_name(p.name+".x14-delta.tmp")
   with temporary.open("xb") as stream:stream.write(after);stream.flush();os.fsync(stream.fileno())
   ET.parse(temporary);os.replace(temporary,p);written.append((p,c))
   assert sha(p)==c["after_sha256"]
  for a in assets:
   dest=ROOT/a["destination"];assert sha(dest)==a["sha256"];checkpng(dest,SIZE[a["kind"]])
  for p,c,after in configs:
   assert_game_stopped()
   assert sha(p)==c["after_sha256"]
   nodes=[n for n in ET.parse(p).getroot().iter("record") if n.get("to")]
   targets=[n.get("to") for n in nodes];assert len(targets)==c["new_mappings"]
   if c.get("neutralization"):
    assert not any(tuple(sorted(n.attrib.items())) in {tuple(sorted(m.items())) for m in c["removed_maps"]} for n in nodes)
    continue
   assert len(targets)==len(set(targets))
   for node in nodes:
    dest=p.parent/node.get("from")
    if dest.suffix.lower()!=".png":dest=Path(str(dest)+".png")
    safe(dest,GRAPHICS);assert dest.is_file();checkpng(dest,SIZE[next(k for k,v in DEST.items() if p==v/"config.xml")])
  assert all(sha(ROOT/p)==h for p,h in data["existing_destination_png_pins"].items()),"Existing PNG changed"
  assert {str(p.relative_to(ROOT)) for p in GRAPHICS.rglob("config.xml")}==set(data["all_public_config_pins"]),"Config set changed during installation"
  changed={str(p.relative_to(ROOT)) for p,c in written}
  assert all(sha(ROOT/p)==h for p,h in data["all_public_config_pins"].items() if p not in changed),"Unrelated config changed"
 except Exception as error:
  rollback=[]
  for p,c in reversed(written):
   if p.is_file() and sha(p)==c["after_sha256"]:
    p.write_bytes((transaction/c["path"]).read_bytes());rollback.append("restored "+str(p.relative_to(ROOT)))
   else:rollback.append("MANUAL_REVIEW "+str(p.relative_to(ROOT)))
  for a in reversed(created):
   p=ROOT/a["destination"]
   if p.is_file() and sha(p)==a["sha256"]:p.unlink()
  dump(transaction/"failure.json",dict(error=repr(error),rollback=rollback))
  raise
 outcome=dict(status="INSTALLED_READBACK_PASS",scope=data["scope"],plan_sha256=sha(path),backup=str(transaction.relative_to(ROOT)),counts=data["counts"],created_files=len(created),preserved_existing_files=len(assets)-len(created),config_changes=data["config_changes"],neutralizations=data.get("neutralizations",[]),unrelated_configs_preserved=True,game_not_accessed=True,game_cache_reload_not_tested=True,distribution="LOCAL_INSTALL_ONLY; rights not approved for public redistribution")
 dump(OUT/("installation-result-"+data["scope"]+".json"),outcome)
 print(json.dumps(outcome,ensure_ascii=True))
if __name__=="__main__":
 parser=argparse.ArgumentParser();parser.add_argument("--scope",choices=["all","faces","logos"],default="all");parser.add_argument("--apply",type=Path)
 parser.add_argument("--neutralize-reviewed-conflicts",action="store_true")
 args=parser.parse_args()
 if args.apply:apply(args.apply)
 else:plan(args.scope,args.neutralize_reviewed_conflicts)
