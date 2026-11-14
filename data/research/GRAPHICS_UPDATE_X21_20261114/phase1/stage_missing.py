from pathlib import Path
import sys,json,csv,hashlib,collections,concurrent.futures,importlib.util,threading,urllib.error,xml.etree.ElementTree as ET,os,base64
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';O=Path(__file__).resolve().parent;STAGE=O/'staging'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,a):p.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def csvrows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter=';'))
def main():
 assert (O/'baseline/manifest.json').is_file(),'Complete baseline first'
 players={p['uid']:p for p in csvrows(O/'baseline/gracze.csv')};clubs={c['uid']:c for c in csvrows(O/'baseline/kluby.csv')};data=read(O/'source-asset-plan.json');selected=[];excluded=[]
 for a in data['items']:
  uid=a['uid']
  if a['kind']=='face':missing=not int(players[uid]['ma_zdjecie_lokalnie'])
  else:missing=not(int(clubs[uid]['herb_normal_lokalnie'])and int(clubs[uid]['herb_small_lokalnie']))
  if missing:selected.append(a)
  else:excluded.append(dict(kind=a['kind'],uid=uid,reason='preserve_existing_valid_mapped_image'))
 selected.sort(key=lambda a:(a['kind']=='face',-int(a['uid'])))
 dump(O/'incremental-asset-plan.json',dict(items=selected,counts=dict(collections.Counter(a['kind']for a in selected)),excluded_existing=len(excluded),source_plan_sha256=sha(O/'source-asset-plan.json'),baseline_manifest_sha256=sha(O/'baseline/manifest.json'),public_modified=False))
 print(json.dumps(dict(selected=dict(collections.Counter(a['kind']for a in selected)),preserved=len(excluded))),flush=True)
 libpath=R/'GRAPHICS_MODERN_2627_20261111/build_graphics.py';sp=importlib.util.spec_from_file_location('existing_graphics_pipeline',libpath);lib=importlib.util.module_from_spec(sp);sp.loader.exec_module(lib)
 lib.OUT=O;lib.CACHE=O/'cache';lib.FACES=STAGE/'faces';lib.LOGON=STAGE/'logos/normal';lib.LOGOS=STAGE/'logos/small'
 for folder in[lib.CACHE,lib.FACES,lib.LOGON,lib.LOGOS,O/'http-errors',O/'backups']:folder.mkdir(parents=True,exist_ok=True)
 cached={}
 for base in[R/'GRAPHICS_MODERN_2627_20261111/cache',R/'GRAPHICS_COVERAGE_X14_20261112/cache']:
  for p in base.glob('*.bin'):cached.setdefault(p.name,p)
 orig=lib.obtain;stop=threading.Event();gate=threading.Lock();locks={}
 def obtain(url):
  key=hashlib.sha256(url.encode()).hexdigest();dest=lib.CACHE/(key+'.bin')
  with gate:lock=locks.setdefault(key,threading.Lock())
  with lock:
   if not dest.exists()and dest.name in cached:os.link(cached[dest.name],dest)
   if stop.is_set()and not dest.exists():raise RuntimeError('Provider access blocked; no new request')
   try:return orig(url)
   except urllib.error.HTTPError as ex:
    body=ex.read(4096);dump(O/'http-errors'/(key+'.json'),dict(url=url,status=ex.code,reason=str(ex.reason),headers=dict(ex.headers),body_prefix_base64=base64.b64encode(body).decode(),body_truncated_at=4096))
    if ex.code in[401,403,429]:stop.set()
    raise
 lib.obtain=obtain
 ledger=O/'staging-ledger.jsonl';done={}
 if ledger.exists():
  for line in ledger.read_text(encoding='utf-8').splitlines():
   a=json.loads(line);done[(a['kind'],a['uid'])]=a
 todo=[a for a in selected if(a['kind'],a['uid'])not in done]
 def work(a):
  if stop.is_set():return dict(kind=a['kind'],uid=a['uid'],status='not_attempted_provider_block')
  return lib.work(a)
 with ledger.open('a',encoding='utf-8',buffering=1)as f,concurrent.futures.ThreadPoolExecutor(max_workers=8)as pool:
  for n,res in enumerate(pool.map(work,todo),1):
   done[(res['kind'],res['uid'])]=res;f.write(json.dumps(res,ensure_ascii=False)+'\n')
   if n%100==0:print(json.dumps(dict(done=n,total=len(todo),status=dict(collections.Counter(x['status']for x in done.values())),provider_block=stop.is_set())),flush=True)
 for folder,kind in[(lib.FACES,'face'),(lib.LOGON,'logo_normal'),(lib.LOGOS,'logo_small')]:lib.update_config(folder,kind)
 from PIL import Image
 assets=[]
 for folder,kind,size in[(lib.FACES,'face',180),(lib.LOGON,'logo',180),(lib.LOGOS,'icon',20)]:
  for node in ET.parse(folder/'config.xml').getroot().iter('record'):
   target=node.get('to');uid=node.get('from')
   if not target:continue
   if kind=='logo'and int(clubs[uid]['herb_normal_lokalnie']):continue
   if kind=='icon'and int(clubs[uid]['herb_small_lokalnie']):continue
   p=folder/(uid+'.png')
   with Image.open(p)as im:assert im.format=='PNG'and im.size==(size,size);im.verify()
   assets.append(dict(path=str(p.relative_to(ROOT)),target=target,sha256=sha(p)))
 baseline=read(O/'baseline/manifest.json');assert all(sha(ROOT/p)==h for p,h in baseline['inputs'].items()if p.endswith('config.xml')),'Public config changed during staging; rebuild plan before installation'
 result=dict(planned=dict(collections.Counter(a['kind']for a in selected)),selected=len(selected),status=dict(collections.Counter(x['status']for x in done.values())),assets=assets,staged_files=len(assets),source_pipeline=str(libpath),source_pipeline_sha256=sha(libpath),script_sha256=sha(Path(__file__)),public_graphics_modified=False,installed=False,provider_block=stop.is_set(),rights='LOCAL_ONLY; NOT_APPROVED_FOR_PUBLIC_REDISTRIBUTION')
 dump(O/'staging-result.json',result);print(json.dumps({k:v for k,v in result.items()if k!='assets'}),flush=True)
if __name__=='__main__':main()
