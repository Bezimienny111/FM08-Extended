"""Incremental X21 kits staging using existing FC12 transport/ZIP/PNG pipeline. No public writes."""
from pathlib import Path
import sys,importlib.util,inspect,csv,json,collections,hashlib,re,urllib.parse,urllib.error,concurrent.futures,argparse
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';BASE=Path(__file__).resolve().parent;OLD=R/'KITS_FC12_20261111';PREV=R/'KITS_X14_DELTA_20261112'
MAPS=['COUNTRY_BATCH_GER_MEX_MAS_20261112/club-map.csv','COUNTRY_BATCH_KOR_COL_ISR_20261112/six-country-stage/club-map.csv','COUNTRY_BATCH_IDN_IND_HKG_20261112/club-map.csv','COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep/club-map.csv','COUNTRY_BATCH_CZE_CRO_CHN_CHI_BGR_BRA_20261113/native-prep/club-map.csv','COUNTRY_BATCH_BLR_BEL_AUT_AUS_ARG_20261114/native-prep/club-map.csv']
COUNTRIES={'Germany':['germany'],'Malaysia':['malaysia'],'Mexico':['mexico'],'Colombia':['colombia'],'Iceland':['iceland'],'Ireland':['ireland'],'Israel':['israel'],'Northern Ireland':['northern-ireland'],'South Korea':['south-korea','korea-south'],'Hong Kong':['hong-kong'],'India':['india'],'Indonesia':['indonesia'],'Denmark':['denmark'],'Finland':['finland'],'France':['france'],'Greece':['greece'],'Netherlands':['netherlands','holland'],'Spain':['spain'],'Brazil':['brazil'],'Bulgaria':['bulgaria'],'Chile':['chile'],'China':['china'],'Croatia':['croatia'],'Czech Republic':['czech-republic','czechia'],'Argentina':['argentina'],'Australia':['australia'],'Austria':['austria'],'Belarus':['belarus'],'Belgium':['belgium']}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
def load():
 path=PREV/'kits_delta_adapter.py';spec=importlib.util.spec_from_file_location('x14_kits_adapter',path);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old);lib=old.load();oldtargets=lib.targets;oldget=lib.get
 lib.OUT=BASE;lib.CACHE=BASE/'cache';lib.STAGE=BASE/'staging'
 for p in [lib.CACHE,lib.STAGE]:p.mkdir(parents=True,exist_ok=True)
 lib.COUNTRIES.update(COUNTRIES)
 def cached_get(url,limit=64*1024*1024):
  key=lib.digest(url.encode())
  for folder in [BASE/'cache',PREV/'cache',OLD/'cache']:
   p=folder/key
   if p.is_file():return p.read_bytes(),p,True
  try:return oldget(url,limit)
  except urllib.error.HTTPError as e:
   body=e.read();dump(BASE/'cache'/(key+'.http-error.json'),dict(url=url,status=e.code,headers=dict(e.headers),body_hex=body.hex(),body_sha256=lib.digest(body)));raise
 lib.get=cached_get
 def targets():
  target=oldtargets();pins={}
  for pp in MAPS:
   p=R/pp;pins[str(p)]=sha(p)
   for row in lib.readcsv(p):
    uid=int(row['ClubUID']);country=row['Country'];name=row['ClubName'];tmid=row.get('TMID','')
    if uid in target and target[uid].get('tmid') and tmid and str(target[uid]['tmid'])!=str(tmid):raise AssertionError(('UID_TMID_collision',uid,target[uid]['tmid'],tmid))
    aliases=set(target.get(uid,{}).get('aliases',[]))|{lib.namekey(name),lib.norm(name)}
    target[uid]=dict(uid=uid,name=name,league=row.get('Group')or row.get('RealLeague')or '',country=country,tmid=tmid,kind=row.get('Kind',''),aliases=aliases,parent_uid=row.get('ParentUID',''),mapping_source=str(p))
  for x in target.values():
   assert x['country']in lib.COUNTRIES;x['aliases'].discard('')
  dump(BASE/'scope-input-pins.json',pins);return target
 lib.targets=targets;return lib

def fetch(lib):
 target=lib.targets();dump(BASE/'target-clubs.json',[dict(x,aliases=sorted(x['aliases']))for x in target.values()]);prior=read(PREV/'pack-ledger.json')
 assert all(x['status']=='downloaded'and sha(Path(x['archive']))==x['archive_sha256']for x in prior)
 seen={x['page']for x in prior};entries={}
 for year in ['2026-27','2025-26']:
  url='https://fmslovakia.com/downloads/kitpacks/fc12-season-'+year+'/';raw,path,reused=lib.get(url,3*1024*1024)
  for href,label in lib.parsepage(raw).links:
   full=urllib.parse.urljoin(url,href)
   if not full.startswith(url)or full==url or full in seen:continue
   slug=urllib.parse.urlparse(full).path.lower()
   if any(w in slug+' '+label.casefold()for w in ['women','feminin','femenin','femmin','zeny']):continue
   for country,slugs in lib.COUNTRIES.items():
    if any(re.search(r'/fc12-'+re.escape(s)+r'-',slug)for s in slugs):entries[full]=(full,country,year,label)
 dump(BASE/'pack-plan.json',dict(targets=len(target),systems=len(lib.COUNTRIES),prior_packs_reused=len(prior),new_entries=list(entries.values()),policy=lib.POLICY,original_pipeline_sha256=sha(OLD/'fc12_pipeline.py')))
 ledger=BASE/'fetch-progress.jsonl';results=[]
 with ledger.open('a',encoding='utf-8',buffering=1)as f,concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
  for i,x in enumerate(pool.map(lib.packjob,entries.values()),1):
   results.append(x);f.write(json.dumps(x,ensure_ascii=True)+'\n');print(json.dumps(dict(pack=i,total=len(entries),country=x['country'],status=x['status'])),flush=True)
 dump(BASE/'pack-ledger.json',prior+results);dump(BASE/'fetch-summary.json',dict(prior_packs_reused=len(prior),new_pack_counts=dict(collections.Counter(x['status']for x in results)),new_countries=dict(collections.Counter(x['country']for x in results if x['status']=='downloaded')),failed=[x for x in results if x['status']!='downloaded'],public_graphics_modified=False))
 print(json.dumps(read(BASE/'fetch-summary.json')),flush=True)

def stage(lib):
 existing=list(lib.KITS.glob('*.png'));assert len(existing)==2082,('baseline_changed',len(existing));prior=read(PREV/'final-kits-ledger.json');known=[]
 for row in prior:
  assert sha(lib.KITS/row['filename'])==row['sha256'];src=row['source'];rank=src.get('season_rank')or lib.seasonrank(src.get('season',''));assert rank is not None;yr=int(rank);season=str(yr)+'-'+str(yr+1)[-2:]if rank>yr else str(yr)
  known.append(dict(uid=row['uid'],slot=row['slot'],status='baseline_preserved',sha256=row['sha256'],season=season,original_proof=row))
 assert len(known)==2082;dump(BASE/'known-existing-proof.json',known)
 code=inspect.getsource(lib.stage);edits=[("assert len(initial)==318","assert len(initial)==2082"),("for file in[R/'GRAPHICS_MODERN_2627_20261111/kits-ledger.json',R/'KITS_EXPANSION_20261111/kits-expanded-ledger.json']:","for file in[OUT/'known-existing-proof.json']:"),("if row.get('status')!='added':continue","if row.get('status')!='baseline_preserved':continue"),("print(json.dumps(dict(initial=318,","print(json.dumps(dict(initial=2082,")]
 for before,after in edits:assert before in code,before;code=code.replace(before,after)
 # Modern FM UID alone is insufficient: require unique source filename identity even for old native UID.
 needle="   if direct_ok:\n    uid=direct['uid'];identity='exact_stock_UID_and_pack_country'"
 repl="   if direct_ok and matches=={direct['uid']}:\n    uid=direct['uid'];identity='exact_stock_UID_unique_verified_alias_and_pack_country'"
 assert needle in code;code=code.replace(needle,repl)
 needle=" for n,((uid,slot),items)in enumerate(sorted(candidates.items()),1):\n";repl=needle+"  if f'{uid}_{slot}' in initial:\n   rows.append(dict(status='preserved_existing_no_change',uid=uid,club=target[uid]['name'],country=target[uid]['country'],slot=slot,existing_sha256=initial[f'{uid}_{slot}'],existing_proof=known.get(f'{uid}_{slot}')))\n   continue\n"
 assert needle in code;code=code.replace(needle,repl)
 dump(BASE/'adapter-manifest.json',dict(original_pipeline=str(OLD/'fc12_pipeline.py'),original_sha256=sha(OLD/'fc12_pipeline.py'),adapter_sha256=sha(Path(__file__)),transformed_stage_sha256=hashlib.sha256(code.encode()).hexdigest(),baseline_count=2082,changes=['exact final club-map incremental UID scope','reuse85 verified archives and cache','preserve ALL existing2082 images','stock UID requires unique verified filename alias and country','no public writes'],rights='FC12 personal use only; no redistribution'))
 exec(compile(code,str(BASE/'adapted_existing_stage'),'exec'),lib.__dict__);lib.stage();assert not any(x['status']=='replace_older'for x in read(BASE/'stage-ledger.json')['rows'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['fetch','stage']);a=p.parse_args();BASE.mkdir(exist_ok=True);lib=load();fetch(lib)if a.action=='fetch'else stage(lib)
