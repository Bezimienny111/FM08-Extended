"""Install only verified X10 graphics delta; reuse image helpers and UTF16-safe logo map removal."""
from pathlib import Path
import sys,json,csv,hashlib,runpy,concurrent.futures,threading,collections,xml.etree.ElementTree as ET,io
from PIL import Image
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111';D=B/'graphics-delta';OUT=D/'installation'
H=runpy.run_path(str(R/'GRAPHICS_MODERN_2627_20261111/build_graphics.py'),run_name='read_helpers')
L=runpy.run_path(str(R/'ITALY_AUTHENTIC_LOGOS_20261111/install_authentic_logos.py'),run_name='read_helpers')
FOLDERS={'face':ROOT/'Dane/graphics/pictures/faces/normal/modern_2627','logo_normal':ROOT/'Dane/graphics/pictures/logos/clubs/normal/modern_2627','logo_small':ROOT/'Dane/graphics/pictures/logos/clubs/small/modern_2627'}
BASE=ROOT/'Dane/graphics/pictures/logos';STAGE=OUT/'staging'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def pins(folder):return {str(p):sha(p)for p in sorted(folder.glob('*.png'))}
def png(path,size):
 with Image.open(path)as im:
  im.load();assert im.format=='PNG'and im.mode=='RGBA'and im.size==(size,size)and im.getbbox()
  assert im.getchannel('A').getextrema()[0]==0,'transparent canvas border required'
 return sha(path)
def mappings(path):return [tuple(sorted(n.attrib.items()))for n in ET.parse(path).getroot().iter('record')if n.get('to')]
def scoped(item):
 return [(FOLDERS['face']/f"{item['uid']}.png",180,'face')]if item['kind']=='face'else[(FOLDERS['logo_normal']/f"{item['uid']}.png",180,'logo_normal'),(FOLDERS['logo_small']/f"{item['uid']}.png",20,'logo_small')]
def start():
 OUT.mkdir(exist_ok=True);(OUT/'backups').mkdir(exist_ok=True)
 baseline_path=OUT/'baseline.json'
 if baseline_path.exists():return read(baseline_path)
 data=read(D/'asset-plan.json');assert len(data['faces'])==2822 and len(data['logos'])==154
 before={k:pins(v)for k,v in FOLDERS.items()};assert {k:len(v)for k,v in before.items()}=={'face':17202,'logo_normal':804,'logo_small':804}
 configs=sorted(set(BASE.rglob('config.xml'))|{FOLDERS['face']/'config.xml'});cp={str(p):sha(p)for p in configs}
 for p in configs:ET.parse(p)
 for kind,folder in FOLDERS.items():
  rows=mappings(folder/'config.xml');assert len(rows)==len(before[kind])
  for row in rows:assert (folder/(dict(row)['from']+'.png')).is_file()
 baseline=dict(status='baseline_pinned',source_plan_sha256=sha(D/'asset-plan.json'),source_manifest_sha256=sha(D/'manifest.json'),existing_png=before,all_graphics_config_pins=cp,modern_configs={k:mappings(v/'config.xml')for k,v in FOLDERS.items()},source_helpers={str(R/'GRAPHICS_MODERN_2627_20261111/build_graphics.py'):sha(R/'GRAPHICS_MODERN_2627_20261111/build_graphics.py'),str(R/'ITALY_AUTHENTIC_LOGOS_20261111/install_authentic_logos.py'):sha(R/'ITALY_AUTHENTIC_LOGOS_20261111/install_authentic_logos.py')},native_mapping_source=str(B/'prepared/full-native.json'),native_mapping_sha256=sha(B/'prepared/full-native.json'))
 dump(baseline_path,baseline);return baseline
def downloads():
 base=start();assert sha(D/'asset-plan.json')==base['source_plan_sha256']
 data=read(D/'asset-plan.json');items=[x for x in data['logos']+data['faces']if x['urls']]
 assert len(items)==1951 and len({(x['kind'],x['uid'])for x in items})==len(items)
 for kind in FOLDERS:(STAGE/kind).mkdir(parents=True,exist_ok=True)
 locks={};mainlock=threading.Lock()
 obtain=H['obtain'];render=H['render'];ledger=OUT/'download-ledger.jsonl';done={}
 if ledger.exists():
  for line in ledger.read_text(encoding='utf-8').splitlines():
   row=json.loads(line);done[row['kind'],row['uid']]=row
 def work(item):
  existing=scoped(item)
  if all(path.exists()for path,_,_ in existing):
   return dict(kind=item['kind'],uid=item['uid'],status='preserved_existing',outputs=[dict(path=str(p),size=z,sha256=png(p,z),kind=k)for p,z,k in existing])
  assert not any(path.exists()for path,_,_ in existing),'partial preexisting pair must be independently reconciled'
  errors=[]
  for url in item['urls']:
   try:
    with mainlock:lock=locks.setdefault(url,threading.Lock())
    with lock:image,cache=obtain(url)
    outputs=[]
    for _,size,kind in existing:
     target=STAGE/kind/f"{item['uid']}.png";render(image,size,target,'bottom'if kind=='face'else'center');outputs.append(dict(path=str(target),size=size,sha256=png(target,size),kind=kind))
    return dict(kind=item['kind'],uid=item['uid'],status='staged',url=url,source_cache=str(cache),source_sha256=sha(cache),outputs=outputs,proof=item['proof'])
   except Exception as error:errors.append(type(error).__name__+':'+str(error)[:220])
  return dict(kind=item['kind'],uid=item['uid'],status='download_failed',errors=errors)
 todo=[x for x in items if (x['kind'],x['uid'])not in done]
 with ledger.open('a',encoding='utf-8',buffering=1)as f,concurrent.futures.ThreadPoolExecutor(max_workers=10)as pool:
  for n,row in enumerate(pool.map(work,todo),1):
   done[row['kind'],row['uid']]=row;f.write(json.dumps(row,ensure_ascii=False)+'\n')
   if n%100==0:print('X10 GRAPHICS',n,'/',len(todo),dict(collections.Counter(x['status']for x in done.values())),flush=True)
 result=dict(status='download_batch_complete',source_plan_sha256=base['source_plan_sha256'],requested=len(items),results=list(done.values()),counts=dict(collections.Counter(x['status']for x in done.values())),no_network_for_missing_urls=True)
 dump(OUT/'download-results.json',result);print('DOWNLOAD DONE',result['counts'],flush=True)
def install():
 base=start();assert not(OUT/'installation-result.json').exists(),'Preserve prior installation receipt'
 results=read(OUT/'download-results.json');assert results['source_plan_sha256']==base['source_plan_sha256']
 good=[x for x in results['results']if x['status']in['staged','preserved_existing']];logos={int(x['uid'])for x in good if x['kind']=='logo'};faces={int(x['uid'])for x in good if x['kind']=='face'}
 for folder,old in base['existing_png'].items():
  for path,digest in old.items():assert sha(path)==digest,'Existing real image changed before install'
 for path,digest in base['all_graphics_config_pins'].items():assert sha(path)==digest,'Config changed concurrently before install'
 for row in good:
  for output in row['outputs']:assert png(Path(output['path']),output['size'])==output['sha256']
 oldconfigs={str(p):p.read_bytes()for p in map(Path,base['all_graphics_config_pins'])};legacychanges=[]
 for path,raw in oldconfigs.items():
  p=Path(path)
  if not p.is_relative_to(BASE)or'modern_2627'in p.parts:continue
  selected=[n for n in ET.fromstring(raw).iter('record')if(m:=L['mapping'](n))and m[0]in logos]
  if not selected:continue
  new,removed,codec=L['strip_legacy'](raw,logos);legacychanges.append(dict(path=path,before_sha256=hashlib.sha256(raw).hexdigest(),after_sha256=hashlib.sha256(new).hexdigest(),removed=removed,codec=codec,new=new))
 cfgbackups={}
 for path,raw in oldconfigs.items():
  target=OUT/'backups/configs'/Path(path).relative_to(ROOT/'Dane/graphics');target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert target.read_bytes()==raw
  else:target.write_bytes(raw)
  cfgbackups[path]=str(target)
 plan=dict(status='prevalidated',source_plan_sha256=base['source_plan_sha256'],successful_face_UIDs=sorted(faces),successful_logo_UIDs=sorted(logos),all_config_backups=cfgbackups,legacy_changes=[{k:v for k,v in x.items()if k!='new'}for x in legacychanges],preserve_all_existing_png_hashes=True,only_scoped_new_png_and_maps=True)
 dump(OUT/'installation-plan.json',plan);added=[];writtenconfigs=[]
 try:
  for row in good:
   if row['status']=='preserved_existing':continue
   for output in row['outputs']:
    dest=FOLDERS[output['kind']]/f"{row['uid']}.png";assert not dest.exists()
    temp=dest.with_suffix('.x10.tmp');assert not temp.exists();temp.write_bytes(Path(output['path']).read_bytes());assert png(temp,output['size'])==output['sha256'];temp.replace(dest);added.append(str(dest))
  H['update_config'].__globals__['OUT']=OUT
  config_added={}
  for kind,folder in FOLDERS.items():
   path=folder/'config.xml';assert path.read_bytes()==oldconfigs[str(path)]
   config_added[kind]=H['update_config'](folder,kind);writtenconfigs.append(str(path))
   expected=faces if kind=='face'else logos;resource='portrait'if kind=='face'else('logo'if kind=='logo_normal'else'icon')
   beforeattrs=base['modern_configs'][kind];after=mappings(path);oldset={tuple(tuple(p)for p in v)for v in beforeattrs}
   extra=[dict(row)for row in after if tuple(row)not in oldset]
   assert {int(x['to'].split('/')[-2])for x in extra}<=expected
   assert oldset<={tuple(v)for v in after}
  for change in legacychanges:
   path=Path(change['path']);assert path.read_bytes()==oldconfigs[str(path)]
   temp=path.with_name(path.name+'.x10.tmp');assert not temp.exists();temp.write_bytes(change['new']);ET.parse(temp);temp.replace(path);writtenconfigs.append(str(path))
  result=dict(status='installed_pending_independent_verification',source_plan_sha256=base['source_plan_sha256'],added_png=added,changed_configs=writtenconfigs,successful_face_UIDs=sorted(faces),successful_logo_UIDs=sorted(logos),config_added=config_added,legacy_files_changed=len(legacychanges),legacy_maps_removed=sum(len(x['removed'])for x in legacychanges),database_launcher_kits_modified=False)
  dump(OUT/'installation-result.json',result)
 except Exception as error:
  for path in reversed(writtenconfigs):
   p=Path(path);tmp=p.with_name(p.name+'.x10.rollback');tmp.write_bytes(oldconfigs[path]);tmp.replace(p)
  for path in reversed(added):Path(path).unlink()
  dump(OUT/'installation-failed.json',dict(error=repr(error),new_files_removed=len(added),configs_restored=writtenconfigs));raise
 print('INSTALLED',len(faces),'faces',len(logos),'logos',len(added),'PNG',flush=True)
def verify():
 base=read(OUT/'baseline.json');r=read(OUT/'installation-result.json');dl=read(OUT/'download-results.json');plan=read(OUT/'installation-plan.json');data=read(D/'asset-plan.json')
 assert sha(D/'asset-plan.json')==base['source_plan_sha256']
 faces=set(r['successful_face_UIDs']);logos=set(r['successful_logo_UIDs']);actualhashes={};beforehashes=base['existing_png'];counts={}
 expected_targets={'face':faces,'logo_normal':logos,'logo_small':logos}
 for kind,folder in FOLDERS.items():
  old=beforehashes[kind]
  for path,digest in old.items():assert sha(path)==digest
  expected=set(old)|{str(folder/f'{uid}.png')for uid in expected_targets[kind]}
  actual={str(p)for p in folder.glob('*.png')};assert actual==expected
  for uid in expected_targets[kind]:actualhashes[str(folder/f'{uid}.png')]=png(folder/f'{uid}.png',20 if kind=='logo_small'else 180)
  counts[kind]=len(actual);nodes=[n for n in ET.parse(folder/'config.xml').getroot().iter('record')if n.get('to')];keys=[n.get('to')for n in nodes];assert len(keys)==len(set(keys))
  for n in nodes:assert(folder/(n.get('from')+'.png')).is_file()
  for uid in expected_targets[kind]:
   target=f"graphics/pictures/person/{uid}/portrait"if kind=='face'else f"graphics/pictures/club/{uid}/"+('icon'if kind=='logo_small'else'logo')
   matches=[n for n in nodes if n.get('to')==target];assert len(matches)==1 and matches[0].get('from')==str(uid)
  oldattrs={tuple(tuple(v)for v in row)for row in base['modern_configs'][kind]};assert oldattrs<={tuple(sorted(n.attrib.items()))for n in nodes}
 for path,digest in base['all_graphics_config_pins'].items():
  raw=Path(path).read_bytes();ET.fromstring(raw)
  if path not in r['changed_configs']:assert sha(path)==digest
  elif Path(path).is_relative_to(BASE)and'modern_2627'not in Path(path).parts:
   old=Path(plan['all_config_backups'][path]).read_bytes();assert L['attrs'](old,logos)==L['attrs'](raw,logos)
 resources=collections.defaultdict(list)
 for p in BASE.rglob('config.xml'):
  for n in ET.parse(p).getroot().iter('record'):
   m=L['mapping'](n)
   if m and m[0]in logos:resources[m].append((str(p),n.get('from')))
 for uid in logos:
  for kind,res in [('logo_normal','logo'),('logo_small','icon')]:assert resources[uid,res]==[(str(FOLDERS[kind]/'config.xml'),str(uid))]
 bykey={(x['kind'],x['uid']):x for x in dl['results']}
 for row in data['faces']+data['logos']:
  done=bykey.get((row['kind'],row['uid']))
  if not done or done['status']!='staged':continue
  assert sha(done['source_cache'])==done['source_sha256']
  for output in done['outputs']:
   dest=FOLDERS[output['kind']]/f"{row['uid']}.png";assert sha(dest)==output['sha256']
 newfaces=sorted(int(Path(p).stem)for p in r['added_png']if Path(p).parent==FOLDERS['face'])
 newlogos=sorted(int(Path(p).stem)for p in r['added_png']if Path(p).parent==FOLDERS['logo_normal'])
 verification=dict(status='pass',actual_PNG_decode_RGBA_dimensions_alpha=True,all_preexisting_real_PNG_hashes_preserved=True,preexisting_counts={k:len(v)for k,v in beforehashes.items()},new_faces=len(newfaces),new_logos=len(newlogos),totals=counts,face_UIDs_added=newfaces,logo_UIDs_added=newlogos,confirmed_image_URLs=1798,confirmed_logo_URLs=153,download_failed=sum(x['status']=='download_failed'for x in dl['results']),all_modern_maps_unique_and_sources_exist=True,legacy_only_successful_logo_UIDs_removed=True,legacy_resource_collisions=0,all_nontarget_mapping_attributes_preserved=True,untouched_config_pins_preserved=True,source_asset_plan_sha256=base['source_plan_sha256'],source_image_hashes_verified=True,actual_target_PNG_hashes=actualhashes,backup_root=str(OUT/'backups'),game_cache_reload_performed=False,database_launcher_kits_modified=False,SI_runtime_graphics_confirmation=False)
 dump(OUT/'independent-verification.json',verification);dump(OUT/'added-UIDs.json',dict(faces=newfaces,logos=newlogos))
 manifest=dict(status='installed_independently_verified',native_database_mapping='TEST_X10 final native UID mapping before SI',source_plan_sha256=base['source_plan_sha256'],verification=str(OUT/'independent-verification.json'),counts=dict(new_faces=len(newfaces),new_logos=len(newlogos),**counts),database_untouched=True,backups=str(OUT/'backups'),faces180_bottom_aligned=True,logos180_small20=True,source_URLs_not_generated_or_guessed=True,no_placeholder_replacement=True,missing_source_faces=1024,missing_logo_source_KSE=True)
 dump(OUT/'manifest.json',manifest)
 (OUT/'REPORT.md').write_text('# Grafiki X10 — instalacja zakończona\n\nNowe zdjęcia: '+str(len(newfaces))+'. Nowe herby: '+str(len(newlogos))+' (wersje normal180 i small20). Łącznie zdjęć: '+str(counts['face'])+', herbów: '+str(counts['logo_normal'])+'.\n\nNiezależny odczyt PNG, rozmiary/RGBA/przezroczystość, hashe źródeł i istniejących plików oraz mapowania XML: PASS. Zachowano wszystkie wcześniejsze grafiki; brakujących źródeł nie zastępowano fikcyjnymi. Legacy mapowania wyłączono wyłącznie dla skutecznie zainstalowanych herbów z tej paczki, z bezpiecznym zachowaniem UTF16/BOM i pozostałych wpisów. Kopie konfiguracji są poza Dane/graphics.\n\nBazy, launchera, zestawów strojów i cache gry nie zmieniano. Potwierdzenie wyglądu w grze oczekuje. Lista nowych UID: added-UIDs.json. Pełne dowody i piny: independent-verification.json oraz installation-plan.json.\n',encoding='utf-8')
 print('X10 GRAPHICS VERIFY PASS',dict(new_faces=len(newfaces),new_logos=len(newlogos),totals=counts,failed=verification['download_failed']),flush=True)
if __name__=='__main__':
 if sys.argv[1]=='run':downloads();install();verify()
 elif sys.argv[1]=='verify':verify()
 else:raise ValueError(sys.argv[1])
