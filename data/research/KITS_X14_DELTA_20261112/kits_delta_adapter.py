"""Incremental X14 adapter of the existing FC12 pipeline; no public install in this script."""
from pathlib import Path
import sys,importlib.util,inspect,csv,json,collections,hashlib,re,urllib.parse,urllib.error,concurrent.futures,argparse
sys.dont_write_bytecode=True
ROOT=Path(r"J:\FM08dev");R=ROOT/"FmLauncher/data/research";BASE=Path(__file__).resolve().parent;OLD=R/"KITS_FC12_20261111"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def load():
 path=OLD/"fc12_pipeline.py";spec=importlib.util.spec_from_file_location("fc12_existing_x14",path);lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)
 oldtargets=lib.targets;oldget=lib.get
 lib.OUT=BASE;lib.CACHE=BASE/"cache";lib.STAGE=BASE/"staging"
 for p in [lib.CACHE,lib.STAGE]:p.mkdir(parents=True,exist_ok=True)
 lib.COUNTRIES.update({"Norway":["norway"],"Peru":["peru"],"Portugal":["portugal"]})
 def cached_get(url,limit=64*1024*1024):
  key=lib.digest(url.encode());previous=OLD/"cache"/key
  if previous.is_file():return previous.read_bytes(),previous,True
  try:return oldget(url,limit)
  except urllib.error.HTTPError as error:
   body=error.read()
   dump(lib.CACHE/(key+".http-error.json"),dict(url=url,status=error.code,headers=dict(error.headers),body_hex=body.hex(),body_sha256=lib.digest(body)))
   raise
 lib.get=cached_get
 def targets():
  target=oldtargets()
  coverage={int(x["uid"]):x for x in lib.readcsv(R/"GRAPHICS_COVERAGE_X14_20261112/after-install/kluby.csv",";")}
  for row in lib.readcsv(R/"POLAND_GAPS_IMPORT_PACKAGE_20261111/prepared/club_map.csv"):
   uid=int(row["ClubUID"]);assert uid in coverage and uid not in target
   c=coverage[uid];target[uid]=dict(uid=uid,name=c["nazwa_klubu"],league=c["liga"],aliases={lib.namekey(c["nazwa_klubu"]),lib.namekey(row["ClubName"])},country=row["Country"],tmid=row.get("TMID",""),kind=row.get("Kind",""))
  assert len(target)==1250 and set(target)==set(coverage)
  for item in target.values():
   assert item["country"] in lib.COUNTRIES;item["aliases"].discard("")
  return target
 lib.targets=targets
 return lib
def fetch(lib):
 target=lib.targets();dump(BASE/"target-clubs.json",[dict(x,aliases=sorted(x["aliases"])) for x in target.values()])
 prior=read(OLD/"pack-ledger.json")
 assert all(p["status"]=="downloaded" and sha(Path(p["archive"]))==p["archive_sha256"] for p in prior)
 seen={p["page"] for p in prior};entries={}
 for year in ["2026-27","2025-26"]:
  url="https://fmslovakia.com/downloads/kitpacks/fc12-season-"+year+"/";raw,path,reused=lib.get(url,3*1024*1024)
  for href,label in lib.parsepage(raw).links:
   full=urllib.parse.urljoin(url,href)
   if not full.startswith(url) or full==url or full in seen:continue
   slug=urllib.parse.urlparse(full).path.lower()
   if any(word in slug+" "+label.casefold() for word in ["women","feminin","femenin","femmin","zeny"]):continue
   for country,slugs in lib.COUNTRIES.items():
    if any(re.search(r"/fc12-"+re.escape(s)+r"-",slug) for s in slugs):entries[full]=(full,country,year,label)
 dump(BASE/"pack-plan.json",dict(targets=len(target),systems=len(lib.COUNTRIES),prior_packs_reused=len(prior),new_entries=list(entries.values()),policy=lib.POLICY,old_pipeline_sha256=sha(OLD/"fc12_pipeline.py")))
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for i,result in enumerate(pool.map(lib.packjob,entries.values()),1):
   results.append(result);print(json.dumps(dict(pack=i,total=len(entries),country=result["country"],status=result["status"])),flush=True)
 dump(BASE/"pack-ledger.json",prior+results)
 dump(BASE/"fetch-summary.json",dict(prior_packs_reused=len(prior),new_pack_counts=dict(collections.Counter(p["status"] for p in results)),new_countries=dict(collections.Counter(p["country"] for p in results if p["status"]=="downloaded")),failed=[p for p in results if p["status"]!="downloaded"],public_graphics_modified=False))
 print(json.dumps(read(BASE/"fetch-summary.json"),ensure_ascii=True),flush=True)
def stage(lib):
 prior=read(OLD/"final-kits-ledger.json");known=[]
 for row in prior:
  image=lib.KITS/row["filename"];assert sha(image)==row["sha256"]
  source=row["source"];rank=source.get("season_rank") or lib.seasonrank(source.get("season",""))
  assert rank is not None,(row["uid"],row["slot"])
  year=int(rank);season=str(year)+"-"+str(year+1)[-2:] if rank>year else str(year)
  known.append(dict(uid=row["uid"],slot=row["slot"],status="baseline_preserved",sha256=row["sha256"],season=season,original_proof=row))
 assert len(known)==1700
 proofpath=BASE/"known-existing-proof.json";dump(proofpath,known)
 code=inspect.getsource(lib.stage)
 replacements=[
  ("assert len(initial)==318","assert len(initial)==1700"),
  ("for file in[R/'GRAPHICS_MODERN_2627_20261111/kits-ledger.json',R/'KITS_EXPANSION_20261111/kits-expanded-ledger.json']:","for file in[OUT/'known-existing-proof.json']:"),
  ("if row.get('status')!='added':continue","if row.get('status')!='baseline_preserved':continue"),
  ("print(json.dumps(dict(initial=318,","print(json.dumps(dict(initial=1700,")]
 for before,after in replacements:
  assert before in code,before;code=code.replace(before,after)
 needle=" for n,((uid,slot),items)in enumerate(sorted(candidates.items()),1):\n"
 replacement=needle+"  if f'{uid}_{slot}' in initial:\n   rows.append(dict(status='preserved_existing_no_change',uid=uid,club=target[uid]['name'],country=target[uid]['country'],slot=slot,existing_sha256=initial[f'{uid}_{slot}'],existing_proof=known.get(f'{uid}_{slot}')))\n   continue\n"
 assert needle in code;code=code.replace(needle,replacement)
 dump(BASE/"adapter-manifest.json",dict(original_pipeline=str((OLD/"fc12_pipeline.py").relative_to(ROOT)),original_sha256=sha(OLD/"fc12_pipeline.py"),adapter_sha256=sha(Path(__file__)),transformed_stage_sha256=hashlib.sha256(code.encode()).hexdigest(),changes=["targets extended to pinned1250","baseline count1700","known existing seasons pinned from final ledger","never replace any existing file; skip existing slots before rendering"],public_graphics_modified=False,rights="FC12 personal use only; no redistribution"))
 exec(compile(code,str(BASE/"adapted_existing_stage"),"exec"),lib.__dict__)
 lib.stage()
 for row in read(BASE/"stage-ledger.json")["rows"]:
  assert row["status"]!="replace_older","Unexpected overwrite"
 if read(BASE/"stage-ledger.json")["errors"]:print("Staging has explicit errors; see stage-ledger.json",flush=True)
if __name__=="__main__":
 parser=argparse.ArgumentParser();parser.add_argument("action",choices=["fetch","stage"]);args=parser.parse_args()
 BASE.mkdir(exist_ok=True);lib=load()
 if args.action=="fetch":fetch(lib)
 else:stage(lib)
