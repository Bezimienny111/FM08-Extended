from pathlib import Path
import csv,json,collections,re,unicodedata,urllib.request,concurrent.futures,io,hashlib,time,sys,xml.etree.ElementTree as ET,shutil
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parents[4]
R=ROOT/'FmLauncher/data/research'
OUT=R/'GRAPHICS_MODERN_2627_20261111'
CACHE=OUT/'cache'
FACES=ROOT/'Dane/graphics/pictures/faces/normal/modern_2627'
LOGON=ROOT/'Dane/graphics/pictures/logos/clubs/normal/modern_2627'
LOGOS=ROOT/'Dane/graphics/pictures/logos/clubs/small/modern_2627'
KITS=ROOT/'Dane/graphics/pictures/kits/2d/modern_2627'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readcsv(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def norm(s):return ' '.join(''.join(c for c in unicodedata.normalize('NFKD',s.casefold()) if not unicodedata.combining(c)).replace('-',' ').split())
def dump(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def plan():
 players=readcsv(R/'FACEPACK_NEW_PLAYERS_20261111/new-players-facepack.csv')
 ea=collections.defaultdict(set)
 for row in readcsv(ROOT/'FMExt/data/fc27_players_all_2026_09_12.csv'):
  if row.get('gender')=="Women's Football":continue
  for name in set([norm(row['first_name']+' '+row['last_name']),norm(row['common_name'])]):
   if name:ea[(row['birthdate'],name)].add(row['player_id'])
 tm={}; files=[]
 packnames=['FOUR_COUNTRY_X7_20261110','SWEDEN_SWITZERLAND_X3_20261109','UKRAINE_TURKEY_X2_20261109','WALES_USA_URUGUAY_2627_B1_20261109','HUNGARY_DATABASE_2627_H1_20261109','ITALY_DATABASE_2627_IMPORT_I1_20261108']
 for folder in packnames:files.extend((R/folder/'sources/tm-clubs').glob('*players*.json'))
 for p in files:
  try:data=json.loads(p.read_text(encoding='utf-8-sig'))
  except Exception:continue
  for item in data.get('players',[]):
   url=item.get('image_url')
   if url and 'default' not in url.lower() and 'data:image' not in url:tm[str(item['id'])]=(url,str(p),item.get('date_of_birth'))
 faceplan=[]
 for p in players:
  urls=[];proof=[]
  if p['transfermarkt_id'] in tm:
   url,source,dob=tm[p['transfermarkt_id']]
   if not dob or dob==p['source_dob']:
    urls.append(url);proof.append(dict(kind='Transfermarkt',id=p['transfermarkt_id'],source=source))
  ids={pid for name in {norm(p['first_name']+' '+p['last_name']),norm(p['source_name'])} for pid in ea.get((p['source_dob'],name),set())}
  if len(ids)==1 and p['dob_precision']!='year':
   pid=next(iter(ids))
   urls.extend([f'https://cdn.futbin.com/content/fifa25/img/players/{pid}.png',f'https://cdn.futwiz.com/assets/img/fc25/faces/{pid}.png'])
   proof.append(dict(kind='EA_exact_unique_name_DOB',id=pid,source='FMExt/data/fc27_players_all_2026_09_12.csv'))
  faceplan.append(dict(kind='face',uid=p['uid'],name=p['source_name'],urls=urls,proof=proof))
 clubmap={}
 packs=['POLAND_DATABASE_2627_R1_20261108/native-V25-N7/prepared-r2','ITALY_DATABASE_2627_IMPORT_I1_20261108/prepared-r4','HUNGARY_DATABASE_2627_H1_20261109/prepared','WALES_USA_URUGUAY_2627_B1_20261109/prepared','UKRAINE_TURKEY_X2_20261109/prepared','SWEDEN_SWITZERLAND_X3_20261109/prepared','FOUR_COUNTRY_X7_20261110/prepared']
 for rel in packs:
  for p in readcsv(R/rel/'club_map.csv'):
   clubmap[p['ClubUID']]=p
 logos=[]
 for p in readcsv(R/'CLUB_GRAPHICS_20261111/LISTA_KLUBOW_UID_NAZWA_LIGA.csv'):
  pass
 # Club graphics list is semicolon delimited.
 with (R/'CLUB_GRAPHICS_20261111/LISTA_KLUBOW_UID_NAZWA_LIGA.csv').open(encoding='utf-8-sig',newline='') as f:clubs=list(csv.DictReader(f,delimiter=';'))
 for p in clubs:
  c=clubmap[p['UID']];tmid=c.get('TMID','').strip()
  urls=[f'https://tmssl.akamaized.net/images/wappen/normal/{tmid}.png'] if tmid and tmid.isdigit() else []
  logos.append(dict(kind='logo',uid=p['UID'],name=p['Nazwa klubu'],urls=urls,proof=[dict(kind='verified_club_map_TM_ID',id=tmid)] if urls else []))
 OUT.mkdir(exist_ok=True);CACHE.mkdir(exist_ok=True)
 dump(OUT/'asset-plan.json',dict(faces=faceplan,logos=logos))
 print(json.dumps(dict(faces=len(faceplan),face_urls=sum(bool(x['urls']) for x in faceplan),clubs=len(logos),logo_urls=sum(bool(x['urls']) for x in logos))))
def obtain(url):
 key=hashlib.sha256(url.encode()).hexdigest()
 path=CACHE/(key+'.bin')
 if path.exists():
  raw=path.read_bytes()
 else:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'image/avif,image/webp,image/png,image/jpeg,image/*;q=0.8','Referer':'https://www.transfermarkt.com/'})
  with urllib.request.urlopen(req,timeout=10) as res:raw=res.read(8*1024*1024)
  if not raw:raise ValueError('empty_image')
  with Image.open(io.BytesIO(raw)) as im:im.verify()
  tmp=path.with_suffix('.tmp');tmp.write_bytes(raw);tmp.replace(path)
 with Image.open(io.BytesIO(raw)) as source:
  if source.width<20 or source.height<20:raise ValueError('tiny_placeholder')
  im=ImageOps.exif_transpose(source).convert('RGBA')
  if im.getbbox() is None:raise ValueError('empty_alpha')
 return im,path
def render(im,size,path,align='center'):
 if path.exists():return False
 image=im.copy();image.thumbnail((size,size),Image.Resampling.LANCZOS)
 canvas=Image.new('RGBA',(size,size),(0,0,0,0))
 canvas.alpha_composite(image,((size-image.width)//2,(size-image.height) if align=='bottom' else (size-image.height)//2))
 tmp=path.with_suffix('.tmp')
 canvas.save(tmp,format='PNG',optimize=True)
 with Image.open(tmp) as test:assert test.size==(size,size) and test.format=='PNG'
 tmp.replace(path)
 return True
def work(item):
 kind=item['kind'];uid=item['uid']
 target=FACES/f'{uid}.png' if kind=='face' else LOGON/f'{uid}.png'
 if target.exists():return dict(kind=kind,uid=uid,status='preserved_existing',output=str(target),sha256=sha(target))
 errors=[]
 for url in item['urls']:
  try:
   image,cache=obtain(url)
   if kind=='face':render(image,180,target,'bottom')
   else:
    render(image,180,LOGON/f'{uid}.png');render(image,20,LOGOS/f'{uid}.png')
   return dict(kind=kind,uid=uid,status='added',url=url,source_cache=str(cache),source_sha256=sha(cache),output=str(target),sha256=sha(target),proof=item['proof'])
  except Exception as e:errors.append(type(e).__name__+':'+str(e)[:160])
 return dict(kind=kind,uid=uid,status='no_confirmed_image' if not item['urls'] else 'download_failed',errors=errors)
def update_config(folder,kind):
 config=folder/'config.xml'
 if config.exists():
  raw=config.read_bytes();h=hashlib.sha256(raw).hexdigest()
  backup=OUT/'backups'/f'{kind}-{h}.xml'
  backup.parent.mkdir(exist_ok=True)
  if not backup.exists():backup.write_bytes(raw)
  root=ET.fromstring(raw)
 else:
  root=ET.Element('record')
  ET.SubElement(root,'boolean',{'id':'preload','value':'false'})
  ET.SubElement(root,'boolean',{'id':'amap','value':'false'})
 maps=next((x for x in root.findall('list') if x.get('id')=='maps'),None)
 if maps is None:maps=ET.SubElement(root,'list',{'id':'maps'})
 targets={x.get('to') for x in maps.findall('record')}
 assert len(targets)==len(maps.findall('record')),'duplicate_config_targets'
 count=0
 for p in sorted(folder.glob('*.png'),key=lambda x:x.stem):
  if not p.stem.isdigit():continue
  uid=p.stem
  to=f'graphics/pictures/person/{uid}/portrait' if kind=='face' else f'graphics/pictures/club/{uid}/'+('icon' if kind=='logo_small' else 'logo')
  if to not in targets:
   ET.SubElement(maps,'record',{'from':uid,'to':to});targets.add(to);count+=1
 for item in maps.findall('record'):
  source=folder/(item.get('from','')+'.png')
  assert source.is_file(),f'config_missing_image:{source}'
 ET.indent(root,space='\t')
 tmp=config.with_suffix('.xml.tmp')
 ET.ElementTree(root).write(tmp,encoding='utf-8',xml_declaration=False)
 ET.parse(tmp);tmp.replace(config)
 return count
def run():
 data=json.loads((OUT/'asset-plan.json').read_text(encoding='utf-8'))
 for folder in [FACES,LOGON,LOGOS,KITS]:folder.mkdir(parents=True,exist_ok=True)
 items=data['faces']+data['logos']
 # Prioritize actual download work and useful badges, then record explicit missing sources.
 items.sort(key=lambda x:(not bool(x['urls']),x['kind']!='logo',int(x['uid'])))
 ledger=OUT/'download-ledger.jsonl';done={}
 if ledger.exists():
  for line in ledger.read_text(encoding='utf-8').splitlines():
   try:row=json.loads(line);done[(row['kind'],row['uid'])]=row
   except ValueError:pass
 todo=[x for x in items if (x['kind'],x['uid']) not in done]
 with ledger.open('a',encoding='utf-8',buffering=1) as f,concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
  for n,res in enumerate(pool.map(work,todo),1):
   done[(res['kind'],res['uid'])]=res;f.write(json.dumps(res,ensure_ascii=False)+'\n')
   if n%100==0:
    print(n,'/',len(todo),dict(collections.Counter(x['status'] for x in done.values())),flush=True)
    update_config(FACES,'face');update_config(LOGON,'logo_normal');update_config(LOGOS,'logo_small')
 for folder,kind in [(FACES,'face'),(LOGON,'logo_normal'),(LOGOS,'logo_small')]:update_config(folder,kind)
 dump(OUT/'coverage.json',dict(total_targets=len(items),status_counts=dict(collections.Counter(x['status'] for x in done.values())),face_added=sum(x['kind']=='face' and x['status']=='added' for x in done.values()),logos_added=sum(x['kind']=='logo' and x['status']=='added' for x in done.values()),face_uids_present=sorted(int(x['uid']) for x in done.values() if x['kind']=='face' and x['status'] in ['added','preserved_existing']),logo_uids_present=sorted(int(x['uid']) for x in done.values() if x['kind']=='logo' and x['status'] in ['added','preserved_existing'])))
 print('DONE',dict(collections.Counter(x['status'] for x in done.values())),flush=True)
if __name__=='__main__':
 if sys.argv[1]=='plan':plan()
 elif sys.argv[1]=='run':run()
