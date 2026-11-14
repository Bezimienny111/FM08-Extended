from pathlib import Path
import sys, json, csv, hashlib, importlib.util, concurrent.futures, collections, argparse
import xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
ROOT=Path(r"J:\FM08dev");R=ROOT/"FmLauncher/data/research";OUT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def rows(p):return list(csv.DictReader(p.open(encoding="utf-8-sig"),delimiter=";"))
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def main():
 parser=argparse.ArgumentParser();parser.add_argument("--plan-only",action="store_true");parser.add_argument("--limit-faces",type=int,default=500);args=parser.parse_args()
 players={p["uid"]:p for p in rows(OUT/"brakujace_zdjecia.csv")}
 clubs={p["uid"]:p for p in rows(OUT/"kluby.csv")}
 missinglogos={k for k,v in clubs.items() if not(int(v["herb_normal"]) and int(v["herb_small"]))}
 prepared=R/"POLAND_GAPS_IMPORT_PACKAGE_20261111/prepared"
 clubmaps=[p for p in [prepared/"club_map.csv",R/"SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/prepared/club_map.csv"] if p.is_file()]
 plan=[];seen=set();inputpins={}
 for path in clubmaps:
  inputpins[str(path.relative_to(ROOT))]=sha(path)
  for c in csv.DictReader(path.open(encoding="utf-8-sig")):
   uid=c["ClubUID"];tmid=c.get("TMID","")
   if uid not in missinglogos or not tmid.isdigit() or ("logo",uid) in seen:continue
   plan.append(dict(kind="logo",uid=uid,name=clubs[uid]["nazwa_klubu"],urls=[f"https://tmssl.akamaized.net/images/wappen/normal/{tmid}.png"],proof=[dict(kind="verified_club_map_TM_ID",id=tmid,source=str(path.relative_to(ROOT)))]));seen.add(("logo",uid))
 native_path=prepared/"full-native.json";prov_path=prepared/"provenance.json"
 native=read(native_path);prov=read(prov_path)
 inputpins[str(native_path.relative_to(ROOT))]=sha(native_path);inputpins[str(prov_path.relative_to(ROOT))]=sha(prov_path)
 subjects={str(p["id90"]):p for p in native["subjects"]}
 rawcache={};rawroot=R/"PORTUGAL_PERU_NORWAY_POLAND_PREP_20261111"
 for p in prov:
  s=subjects[str(p["subject_id"])];uid=str(s["uid"])
  if uid not in players or ("face",uid) in seen:continue
  raw=p.get("PlayerRaw",{});path=rawroot/raw.get("raw_file","MISSING")
  if not path.is_file():continue
  if path not in rawcache:
   assert sha(path)==raw["file_sha256"],"Raw source pin mismatch"
   wrap=read(path);body=wrap["body"]
   assert hashlib.sha256(body.encode("utf-8")).hexdigest()==raw["body_sha256"]
   data=json.loads(body).get("data") or []
   if isinstance(data,dict):data=data.get("players",[])
   rawcache[path]={str(v["id"]):v for v in data};inputpins[str(path.relative_to(ROOT))]=sha(path)
  v=rawcache[path].get(str(p["TMID"]))
  if not v:continue
  if v.get("lifeDates",{}).get("dateOfBirth")!=p.get("source_dob"):continue
  url=v.get("portraitUrl")
  if not isinstance(url,str) or not url.startswith("https://") or "default" in url.lower():continue
  plan.append(dict(kind="face",uid=uid,name=p["name"],urls=[url],proof=[dict(kind="exact_import_subject_TM_ID_and_source_DOB",id=p["TMID"],source=str(prov_path.relative_to(ROOT)),subject_id=p["subject_id"],raw=str(path.relative_to(ROOT)),source_dob=p["source_dob"])]));seen.add(("face",uid))
 oldplan=R/"GRAPHICS_MODERN_2627_20261111/asset-plan.json"
 if oldplan.is_file():
  inputpins[str(oldplan.relative_to(ROOT))]=sha(oldplan)
  for p in read(oldplan)["faces"]:
   uid=str(p["uid"])
   if uid in players and ("face",uid) not in seen and p.get("urls"):
    plan.append(p);seen.add(("face",uid))
 counts=dict(collections.Counter(x["kind"] for x in plan))
 dump(OUT/"confirmed-asset-plan.json",dict(items=plan,counts=counts,input_pins=inputpins,distribution="Rights review required; availability is not permission to redistribute",scope="Incremental confirmed candidates only; not all missing assets"))
 print(json.dumps(dict(planned=counts),ensure_ascii=True),flush=True)
 if args.plan_only:return
 libpath=R/"GRAPHICS_MODERN_2627_20261111/build_graphics.py"
 spec=importlib.util.spec_from_file_location("graphics_existing_pipeline",libpath);lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)
 STAGE=OUT/"staging";lib.CACHE=OUT/"cache";lib.FACES=STAGE/"faces";lib.LOGON=STAGE/"logos/normal";lib.LOGOS=STAGE/"logos/small";lib.OUT=OUT
 for p in [lib.CACHE,lib.FACES,lib.LOGON,lib.LOGOS,OUT/"backups"]:p.mkdir(parents=True,exist_ok=True)
 selected=[p for p in plan if p["kind"]=="logo"]+[p for p in plan if p["kind"]=="face"][:args.limit_faces]
 ledger=OUT/"staging-ledger.jsonl";results=[]
 with ledger.open("a",encoding="utf-8",buffering=1) as f,concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  for n,result in enumerate(pool.map(lib.work,selected),1):
   results.append(result);f.write(json.dumps(result,ensure_ascii=False)+"\n")
   if n%100==0:print(json.dumps(dict(done=n,total=len(selected),status=dict(collections.Counter(x["status"] for x in results)))),flush=True)
 for folder,kind in [(lib.FACES,"face"),(lib.LOGON,"logo_normal"),(lib.LOGOS,"logo_small")]:lib.update_config(folder,kind)
 actual=[]
 from PIL import Image
 for folder,size in [(lib.FACES,180),(lib.LOGON,180),(lib.LOGOS,20)]:
  for node in ET.parse(folder/"config.xml").getroot().iter("record"):
   if not node.get("to"):continue
   path=folder/(node.get("from")+".png")
   with Image.open(path) as im:
    assert im.format=="PNG" and im.size==(size,size);im.verify()
   actual.append(dict(path=str(path.relative_to(ROOT)),target=node.get("to"),sha256=sha(path)))
 audit=read(OUT/"manifest.json")
 assert all(sha(ROOT/p)==h for p,h in audit["inputs"].items() if p.endswith("config.xml")),"Public config changed"
 result=dict(planned=counts,selected=len(selected),status=dict(collections.Counter(x["status"] for x in results)),staged_files=len(actual),assets=actual,public_graphics_modified=False,installed=False,source_pipeline=str(libpath.relative_to(ROOT)),source_pipeline_sha256=sha(libpath),script_sha256=sha(Path(__file__)),distribution="NOT_APPROVED_FOR_PUBLICATION; review specific source rights before distribution")
 dump(OUT/"staging-result.json",result)
 print(json.dumps({k:v for k,v in result.items() if k!="assets"},ensure_ascii=True),flush=True)
if __name__=="__main__":main()
