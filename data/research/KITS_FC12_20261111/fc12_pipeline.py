from pathlib import Path,PurePosixPath
from html.parser import HTMLParser
import csv,json,re,hashlib,urllib.request,urllib.parse,concurrent.futures,html,zipfile,stat,collections,unicodedata,posixpath,io,sys
from datetime import datetime
from PIL import Image,ImageOps,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3];R=OUT.parent
CACHE=OUT/'cache';CACHE.mkdir(exist_ok=True)
KITS=ROOT/'Dane/graphics/pictures/kits/2d/modern_2627'
STAGE=OUT/'staging';STAGE.mkdir(exist_ok=True)
POLICY='FM Slovakia / Allstar Kitmakers; personal use only; no redistribution, reupload, mirrors or rebundling. Link to the original pack page.'
COUNTRIES={'Poland':['poland'],'Italy':['italy'],'Hungary':['hungary'],'Wales':['wales'],
 'USA':['usa','united-states','united-states-of-america'],'Uruguay':['uruguay'],'Ukraine':['ukraine'],'Turkey':['turkey'],
 'Sweden':['sweden'],'Switzerland':['switzerland'],'Scotland':['scotland'],'Slovakia':['slovakia'],'Slovenia':['slovenia'],
 'Singapore':['singapore'],'Serbia':['serbia'],'Romania':['romania'],'South Africa':['south-africa'],'Russia':['russia']}
ALIASES_COUNTRY={'USA':'USA','United States':'USA','United States of America':'USA','Liechtenstein':'Switzerland'}
def digest(b):return hashlib.sha256(b).hexdigest()
def pin(p):return digest(p.read_bytes())if p.exists()else None
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def readcsv(p,delimiter=','):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline=''),delimiter=delimiter))
def norm(s):
 s=''.join(c for c in unicodedata.normalize('NFKD',s.casefold())if not unicodedata.combining(c))
 return re.sub('[^a-z0-9]+',' ',s).strip()
def namekey(s):
 skip={'fc','afc','cf','sc','fk','ks','ac','ssc','fcu','nk','sk','ff','bk','if','ik','bsc','us','as','ss','u','s','rfc','cfc'}
 return' '.join(w for w in norm(s).split()if w not in skip)
class Page(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.words=[];self.href=None;self.label=[]
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if tag=='a':self.href=attrs.get('href');self.label=[]
 def handle_data(self,text):
  self.words.append(text)
  if self.href:self.label.append(text)
 def handle_endtag(self,tag):
  if tag=='a'and self.href:self.links.append((self.href,' '.join(self.label)));self.href=None
def parsepage(raw):
 p=Page();p.feed(raw.decode('utf-8',errors='replace'));return p
def get(url,limit=64*1024*1024):
 key=digest(url.encode());path=CACHE/key
 if path.exists():return path.read_bytes(),path,True
 request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'*/*'})
 with urllib.request.urlopen(request,timeout=25)as response:
  data=response.read(limit+1)
 assert 0<len(data)<=limit,('download_size',url,len(data))
 tmp=path.with_suffix('.part');tmp.write_bytes(data);tmp.replace(path)
 return data,path,False
def seasonrank(value):
 m=re.search(r'(20\d\d)(?:\s*[-/]\s*(?:20)?(\d\d))?',str(value))
 if not m:return None
 year=int(m[1]);end=int('20'+m[2])if m[2]else year
 return year+(0.5 if end>year else 0)
def targets():
 packs=[
 ('POLAND_DATABASE_2627_R1_20261108/native-V25-N7/prepared-r2','Poland'),
 ('ITALY_DATABASE_2627_IMPORT_I1_20261108/prepared-r4','Italy'),
 ('HUNGARY_DATABASE_2627_H1_20261109/prepared','Hungary'),
 ('WALES_USA_URUGUAY_2627_B1_20261109/prepared',None),
 ('UKRAINE_TURKEY_X2_20261109/prepared',None),
 ('SWEDEN_SWITZERLAND_X3_20261109/prepared',None),
 ('FOUR_COUNTRY_X7_20261110/prepared',None),
 ('SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/prepared',None)]
 allclubs=readcsv(R/'CLUB_GRAPHICS_20261111/LISTA_KLUBOW_UID_NAZWA_LIGA.csv',';')
 allclubs+=readcsv(R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/graphics-delta/clubs.csv',';')
 target={int(x['UID']):dict(uid=int(x['UID']),name=x['Nazwa klubu'],league=x['Liga'],aliases={namekey(x['Nazwa klubu'])})for x in allclubs}
 assert len(allclubs)==958 and len(target)==958,(len(allclubs),len(target))
 for folder,default in packs:
  for row in readcsv(R/folder/'club_map.csv'):
   uid=int(row['ClubUID'])
   if uid not in target:continue
   country=ALIASES_COUNTRY.get(row.get('Country')or default,row.get('Country')or default)
   if country:target[uid]['country']=country
   for key in ['ClubName','TMName','SourceName']:
    if row.get(key):target[uid]['aliases'].add(namekey(row[key]))
   target[uid]['tmid']=row.get('TMID','')
   target[uid]['kind']=row.get('Kind','')
 for row in readcsv(R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/world-club-identities.csv'):
  uid=int(row['ClubUID'])
  if uid in target:target[uid]['aliases'].update(namekey(x)for x in row['Names'].split('|')if namekey(x))
 for item in target.values():
  assert item.get('country')in COUNTRIES,(item['uid'],item.get('country'))
  item['aliases'].discard('')
 return target

def safezip(raw):
 z=zipfile.ZipFile(io.BytesIO(raw))
 assert len(z.infolist())<=10000
 total=0;names={}
 for item in z.infolist():
  name=item.filename.replace('\\','/')
  path=PurePosixPath(name)
  assert not path.is_absolute()and'..'not in path.parts and not re.match(r'^[a-zA-Z]:',name),('unsafe_zip_path',name)
  assert not stat.S_ISLNK(item.external_attr>>16),('symlink',name)
  assert not item.flag_bits&1,'encrypted_zip'
  assert item.file_size<=32*1024*1024,('member_size',name,item.file_size)
  total+=item.file_size
  assert total<=512*1024*1024,'uncompressed_size'
  assert name.casefold()not in names,('case_collision',name)
  names[name.casefold()]=name
 return z,names

def packjob(entry):
 url,country,year,label=entry
 try:
  raw,pagecache,reusedpage=get(url,3*1024*1024);page=parsepage(raw)
  mirrors=[urllib.parse.urljoin(url,h)for h,t in page.links if urllib.parse.urlparse(h).hostname=='dl.dropboxusercontent.com']
  assert mirrors,'no_official_public_dropbox'
  mirror=mirrors[0]
  archive,cache,reusedzip=get(mirror)
  z,names=safezip(archive)
  maps=[];skipped=[]
  for name in names.values():
   if not name.lower().endswith('/config.xml')and name.lower()!='config.xml':continue
   xml=z.read(name)
   assert len(xml)<=4*1024*1024 and b'<!DOCTYPE'not in xml.upper(),'unsafe_xml'
   import xml.etree.ElementTree as ET
   root=ET.fromstring(xml)
   for node in root.iter('record'):
    to=node.get('to','')
    m=re.fullmatch(r'graphics/pictures/team/(\d+)/kits/(home|away|third)(?:/(20\d\d))?',to)
    if not m:
     if'/kits/'in to:skipped.append(dict(config=name,attributes=node.attrib,reason='unsupported_kit_resource'))
     continue
    source=node.get('from','')
    image=posixpath.normpath(posixpath.join(posixpath.dirname(name),source+(''if source.lower().endswith('.png')else'.png')))
    assert not image.startswith('../')and not image.startswith('/'),'source_escape'
    actual=names.get(image.casefold())
    if actual is None:skipped.append(dict(config=name,attributes=node.attrib,reason='missing_png'));continue
    condition_year=m[3]or node.get('year')
    if condition_year and not re.fullmatch(r'20\d\d',condition_year):
     skipped.append(dict(config=name,attributes=node.attrib,reason='unsupported_year'));continue
    maps.append(dict(source_uid=int(m[1]),slot=m[2],source_from=source,member=actual,config=name,
     conditional_year=int(condition_year)if condition_year else None,attributes=node.attrib))
  plain=' '.join(page.words)
  author=re.search(r'Author\s+(.{1,100}?)\s+Views',plain)
  updated=re.search(r'Last updated\s+(\d{2}\.\d{2}\.\d{4})',plain)
  return dict(status='downloaded',page=url,label=label,country=country,season_index=year,
    season_rank=seasonrank(urllib.parse.unquote(urllib.parse.urlparse(url).path.rstrip('/').split('/')[-1])),
    author=author[1].strip()if author else'FM Slovakia / Allstar Kitmakers (publisher credit; individual author not parsed)',
    updated=updated[1]if updated else None,policy=POLICY,
    mirror=mirror,archive=str(cache),archive_sha256=pin(cache),page_cache=str(pagecache),page_sha256=pin(pagecache),
    reused_archive_cache=reusedzip,images=sum(n.lower().endswith('.png')for n in names.values()),maps=maps,skipped=skipped)
 except Exception as e:return dict(status='failed',page=url,country=country,season_index=year,label=label,error=type(e).__name__+':'+str(e))

def fetch():
 target=targets();dump(OUT/'target-clubs.json',[dict(x,aliases=sorted(x['aliases']))for x in target.values()])
 samples=json.loads((OUT/'sample-pack-audit.json').read_text(encoding='utf-8'))
 for sample in samples:assert pin(Path(sample['archive']))==sample['archive_sha256']
 entries={}
 for year in ['2026-27','2025-26']:
  url='https://fmslovakia.com/downloads/kitpacks/fc12-season-'+year+'/'
  raw,path,reused=get(url,3*1024*1024)
  for href,label in parsepage(raw).links:
   full=urllib.parse.urljoin(url,href)
   if not full.startswith(url)or full==url:continue
   slug=urllib.parse.urlparse(full).path.lower()
   if any(x in(slug+' '+label.casefold())for x in ['women','feminin','femenin','femmin','zeny']):continue
   for country,slugs in COUNTRIES.items():
    if any(re.search(r'/fc12-'+re.escape(s)+r'-',slug)for s in slugs):entries[full]=(full,country,year,label)
 dump(OUT/'pack-plan.json',dict(targets=len(target),systems=18,pages=len(entries),entries=list(entries.values()),policy=POLICY))
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=5)as pool:
  for i,row in enumerate(pool.map(packjob,entries.values()),1):
   results.append(row)
   if i%10==0:print('packs',i,'/',len(entries),'downloaded',sum(x['status']=='downloaded'for x in results),flush=True)
 dump(OUT/'pack-ledger.json',results)
 print(json.dumps(dict(packs=len(results),downloaded=sum(x['status']=='downloaded'for x in results),
  maps=sum(len(x.get('maps',[]))for x in results),countries=dict(collections.Counter(x['country']for x in results if x['status']=='downloaded')),
  failed=[dict(page=x['page'],error=x['error'])for x in results if x['status']=='failed'])),flush=True)

def filenamekeys(value):
 base=PurePosixPath(value.replace('\\\\','/')).name
 if base.lower().endswith('.png'):base=base[:-4]
 base=re.sub(r'(?:[_ .-]+(?:home|away|third)|[_ .-]?[123][a-z]?)$','',base,flags=re.I)
 base=re.sub(r'(?:[_ .-]+(?:202[56][_-]?(?:2[67])?|2526|2627))$','',base,flags=re.I)
 values={norm(base),namekey(base)}
 return{v for v in values if v}|{v.replace(' ','')for v in values if v}
def stagepng(raw):
 with Image.open(io.BytesIO(raw))as source:
  assert source.format=='PNG'and 20<=source.width<=4096 and 20<=source.height<=4096,'invalid_kit_png'
  source.load();image=ImageOps.exif_transpose(source).convert('RGBA')
 image.thumbnail((130,130),Image.Resampling.LANCZOS)
 canvas=Image.new('RGBA',(130,130),(0,0,0,0))
 canvas.alpha_composite(image,((130-image.width)//2,(130-image.height)//2))
 assert canvas.getchannel('A').getextrema()[0]==0 and canvas.getbbox(),'invalid_transparency'
 return canvas
def stage():
 target=targets()
 # Extend only literal verified alias spellings; compact whitespace is not fuzzy matching.
 for row in readcsv(R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/world-club-identities.csv'):
  uid=int(row['ClubUID'])
  if uid in target:
   target[uid]['aliases'].update(norm(x)for x in row['Names'].split('|')if norm(x))
 for item in target.values():
  item['aliases'].add(norm(item['name']))
  item['aliases'].update(x.replace(' ','')for x in list(item['aliases']))
 index=collections.defaultdict(set)
 for uid,item in target.items():
  for alias in item['aliases']:index[item['country'],alias].add(uid)
 packs=json.loads((OUT/'pack-ledger.json').read_text(encoding='utf-8'))
 initial={p.stem:pin(p)for p in KITS.glob('*.png')}
 assert len(initial)==318,('changed_baseline',len(initial))
 known={}
 for file in[R/'GRAPHICS_MODERN_2627_20261111/kits-ledger.json',R/'KITS_EXPANSION_20261111/kits-expanded-ledger.json']:
  for row in json.loads(file.read_text(encoding='utf-8')):
   if row.get('status')!='added':continue
   name=str(row.get('uid'))+'_'+row.get('slot','')
   if name in initial and row.get('sha256')==initial[name]:
    known[name]=dict(row,proof_ledger=str(file),season_rank=seasonrank(row.get('season','')))
 candidates=collections.defaultdict(list);unmatched=[];rejected=[];joins=[]
 for pack in packs:
  if pack['status']!='downloaded':continue
  assert pin(Path(pack['archive']))==pack['archive_sha256']
  country=pack['country']
  for m in pack['maps']:
   keys=filenamekeys(m['source_from'])
   direct=target.get(m['source_uid'])
   direct_ok=direct and direct['country']==country and direct['uid']<1800000000 and m['source_uid']!=1510
   reserve_source=any(re.search(r'\b(?:u19|u21|u23|ii|b|nextgen|futuro)\b',key)for key in keys)
   if direct_ok and reserve_source and not any(re.search(r'\b(?:u19|u21|u23|ii|b|nextgen|futuro)\b',alias)for alias in direct['aliases']):
    direct_ok=False
   matches={uid for key in keys for uid in index.get((country,key),set())}
   if direct_ok:
    uid=direct['uid'];identity='exact_stock_UID_and_pack_country'
   elif len(matches)==1:
    uid=next(iter(matches));identity='unique_verified_alias_and_pack_country'
   else:
    unmatched.append(dict(page=pack['page'],country=country,source_uid=m['source_uid'],source_from=m['source_from'],slot=m['slot'],
      keys=sorted(keys),candidate_uids=sorted(matches),reason='ambiguous_name'if matches else'no_verified_target_identity'))
    continue
   conditional=m['conditional_year']
   if conditional and conditional>2026:
    rejected.append(dict(uid=uid,slot=m['slot'],page=pack['page'],source_year=conditional,reason='future_source_condition'));continue
   rank=pack['season_rank']
   if rank is None:
    rejected.append(dict(uid=uid,slot=m['slot'],page=pack['page'],reason='unknown_pack_season'));continue
   if conditional:rank=min(rank,conditional+0.5)
   updated=0
   if pack.get('updated'):
    updated=int(datetime.strptime(pack['updated'],'%d.%m.%Y').strftime('%Y%m%d'))
   candidate=dict(uid=uid,club=target[uid]['name'],country=country,slot=m['slot'],source_uid=m['source_uid'],
      source_from=m['source_from'],archive_member=m['member'],config_member=m['config'],source_attributes=m['attributes'],
      modern_conditional_year=conditional,normalized_FM08_conditional_year=2007 if conditional else None,
      season_rank=rank,season_index=pack['season_index'],pack_page=pack['page'],pack_updated=pack.get('updated'),author=pack['author'],
      archive=pack['archive'],archive_sha256=pack['archive_sha256'],source_mirror=pack['mirror'],
      identity=identity,identity_keys=sorted(keys&target[uid]['aliases']),target_aliases=sorted(target[uid]['aliases']),
      personal_use_only_no_redistribution=True,priority=[rank,updated,1 if conditional is None else 0])
   candidates[uid,m['slot']].append(candidate)
 rows=[];conflicts=[];errors=[];archives={}
 def image_for(candidate):
  archive=candidate['archive']
  if archive not in archives:
   raw=Path(archive).read_bytes();archives[archive]=safezip(raw)[0]
  raw=archives[archive].read(candidate['archive_member'])
  return stagepng(raw),digest(raw)
 for n,((uid,slot),items)in enumerate(sorted(candidates.items()),1):
  ordered=sorted(items,key=lambda x:x['priority'],reverse=True)
  top=[x for x in ordered if x['priority']==ordered[0]['priority']]
  try:
   source,source_sha=image_for(top[0])
   fingerprint=digest(source.tobytes())
   if len(top)>1:
    for other in top[1:]:
     other_image,other_sha=image_for(other)
     if digest(other_image.tobytes())!=fingerprint:raise ValueError('conflicting_equal_priority_pack_images')
   chosen=dict(top[0],source_png_sha256=source_sha,normalized_pixels_sha256=fingerprint)
   stem=f'{uid}_{slot}';old=known.get(stem)
   if stem in initial:
    if old is None or old.get('season_rank')is None:
     rows.append(dict(status='preserved_unproven_existing_age',uid=uid,club=target[uid]['name'],country=target[uid]['country'],slot=slot,
       existing_sha256=initial[stem],candidate=chosen));continue
    if old['season_rank']>=chosen['season_rank']:
     rows.append(dict(status='preserved_equal_or_newer',uid=uid,club=target[uid]['name'],country=target[uid]['country'],slot=slot,
       existing_sha256=initial[stem],existing_proof=old,candidate=chosen));continue
   path=STAGE/(stem+'.png')
   if path.exists():
    with Image.open(path)as current:assert current.size==(130,130)and digest(current.convert('RGBA').tobytes())==fingerprint
   else:
    tmp=path.with_suffix('.tmp');source.save(tmp,format='PNG',optimize=True);tmp.replace(path)
   with Image.open(path)as image:assert image.format=='PNG'and image.size==(130,130)and image.mode=='RGBA'
   rows.append(dict(status='replace_older'if stem in initial else'add',**chosen,staging=str(path),sha256=pin(path),
    before_sha256=initial.get(stem),existing_proof=old))
  except Exception as e:
   errors.append(dict(uid=uid,club=target[uid]['name'],slot=slot,candidates=top,error=type(e).__name__+':'+str(e)))
  if n%200==0:print('staging',n,'/',len(candidates),flush=True)
 for z in archives.values():z.close()
 selected={(x['uid'],x['slot'])for x in rows if x['status']in['add','replace_older']}
 available={(int(stem.split('_')[0]),stem.split('_')[1])for stem in initial}|selected
 gaps=[dict(uid=uid,club=item['name'],country=item['country'],missing_slots=[s for s in ['home','away','third']if(uid,s)not in available])
  for uid,item in target.items()if any((uid,s)not in available for s in ['home','away','third'])]
 dump(OUT/'stage-ledger.json',dict(status='staged',initial_images=len(initial),known_existing_image_seasons=len(known),
  initial_pins=initial,rows=rows,source_gaps=gaps,errors=errors,rejected=rejected,unmatched_source_mappings=unmatched,
  policy=POLICY,final_image_count=len(initial)+sum(x['status']=='add'for x in rows),
  final_club_count=len({uid for uid,slot in available}),countries=dict(collections.Counter(target[uid]['country']for uid in{uid for uid,slot in available}))))
 # A small local visual audit board, not a redistributable pack.
 samples=[];seen=set()
 for row in rows:
  if row['status']not in['add','replace_older']or row['country']in seen:continue
  samples.append(row);seen.add(row['country'])
  if len(samples)==16:break
 if samples:
  cols=4;w=190;h=170;canvas=Image.new('RGB',(cols*w,((len(samples)+cols-1)//cols)*h),(239,242,247));draw=ImageDraw.Draw(canvas)
  font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',12)
  for i,row in enumerate(samples):
   with Image.open(row['staging'])as im:canvas.paste(im,(i%cols*w+30,i//cols*h),im)
   label=str(row['uid'])+' '+row['club']
   draw.text((i%cols*w+3,i//cols*h+132),label[:27],font=font,fill=(0,0,0))
   draw.text((i%cols*w+3,i//cols*h+148),row['country']+' '+row['slot'],font=font,fill=(30,50,70))
  canvas.save(OUT/'staged-samples.png')
 print(json.dumps(dict(initial=318,known_existing_seasons=len(known),status=dict(collections.Counter(x['status']for x in rows)),
  final_images=len(initial)+sum(x['status']=='add'for x in rows),final_clubs=len({uid for uid,slot in available}),errors=len(errors),
  unmatched_source_mappings=len(unmatched),countries=dict(collections.Counter(target[uid]['country']for uid in{uid for uid,slot in available})))),flush=True)

def kitkey(node):
 m=re.fullmatch(r'graphics/pictures/team/(\d+)/kits/(home|away|third)(?:/(\d{4}))?',node.get('to',''))
 return(int(m[1]),m[2])if m else None
def keepattrs(raw,slots):
 import xml.etree.ElementTree as ET
 return[tuple(sorted(n.attrib.items()))for n in ET.fromstring(raw).iter('record')if n.get('to')and kitkey(n)not in slots]
def decode_xml(raw):
 import runpy
 # Pure UTF8/UTF16/BOM-preserving helper; the Italian installer main is never invoked.
 return runpy.run_path(str(R/'ITALY_AUTHENTIC_LOGOS_20261111/install_authentic_logos.py'),run_name='xml_helpers')['decode'](raw)
def legacy_kits(raw,slots):
 import xml.etree.ElementTree as ET
 text,bom,codec=decode_xml(raw)
 selected=[n for n in ET.fromstring(raw).iter('record')if kitkey(n)in slots]
 spans=[]
 for match in re.finditer(r'<record\b[^>]*?/\s*>',text):
  node=ET.fromstring(match[0])
  if kitkey(node)in slots:spans.append(match.span())
 assert len(spans)==len(selected),('unsupported_legacy_xml',len(spans),len(selected))
 new=text
 for a,b in reversed(spans):new=new[:a]+new[b:]
 new=bom+new.encode(codec)
 assert keepattrs(raw,slots)==keepattrs(new,slots)
 assert not any(kitkey(n)in slots for n in ET.fromstring(new).iter('record'))
 return new,[n.attrib for n in selected],codec
def install():
 import xml.etree.ElementTree as ET
 receipt=OUT/'installation-result.json'
 assert not receipt.exists(),'do_not_repeat_installed_batch'
 stage=json.loads((OUT/'stage-ledger.json').read_text(encoding='utf-8'))
 assert stage['initial_images']==318 and stage['known_existing_image_seasons']==318
 mods=[x for x in stage['rows']if x['status']in['add','replace_older']]
 oldpins=stage['initial_pins']
 current={p.stem:pin(p)for p in KITS.glob('*.png')}
 assert current==oldpins,'baseline_changed'
 final=dict(oldpins)
 for row in mods:
  assert row['slot']in['home','away','third']
  name=str(row['uid'])+'_'+row['slot']
  assert name not in final if row['status']=='add'else name in final
  assert pin(Path(row['staging']))==row['sha256']
  with Image.open(row['staging'])as im:
   assert im.format=='PNG'and im.mode=='RGBA'and im.size==(130,130)and im.getchannel('A').getextrema()[0]==0
  final[name]=row['sha256']
 assert len(final)==1700
 slots=set()
 for name in final:
  m=re.fullmatch(r'(\d+)_(home|away|third)',name);assert m
  slots.add((int(m[1]),m[2]))
 assert len(slots)==len(final)
 base=(ROOT/'Dane/graphics/pictures/kits').resolve()
 config_paths=sorted(base.rglob('config.xml'))
 rawconfigs={str(x):x.read_bytes()for x in config_paths}
 for raw in rawconfigs.values():ET.fromstring(raw)
 changes=[];legacy=[]
 for row in mods:
  name=str(row['uid'])+'_'+row['slot']+'.png';path=KITS/name
  old=path.read_bytes()if path.exists()else None
  changes.append(dict(path=path,old=old,new=Path(row['staging']).read_bytes(),kind='png',
   backup=OUT/'backups/replaced-older-kits'/name if old is not None else None))
 for path in config_paths:
  if path==KITS/'config.xml':continue
  raw=rawconfigs[str(path)]
  if not any(kitkey(n)in slots for n in ET.fromstring(raw).iter('record')):continue
  new,removed,codec=legacy_kits(raw,slots)
  e=dict(path=path,old=raw,new=new,kind='legacy_xml',backup=OUT/'backups/legacy-configs'/path.relative_to(base),
   removed_maps=removed,codec=codec)
  changes.append(e);legacy.append(e)
 path=KITS/'config.xml';old=rawconfigs[str(path)];tree=ET.fromstring(old)
 maps=next((n for n in tree.findall('list')if n.get('id')=='maps'),None);assert maps is not None
 for node in list(maps):
  if kitkey(node)in slots:maps.remove(node)
 for name in sorted(final):
  uid,slot=name.split('_')
  ET.SubElement(maps,'record',{'from':name,'to':f'graphics/pictures/team/{uid}/kits/{slot}'})
 # Where a chosen source used modern conditional years, retain an FM08-year alias, never2026.
 conditioned=[x for x in mods if x.get('modern_conditional_year')is not None]
 for row in conditioned:
  name=str(row['uid'])+'_'+row['slot']
  ET.SubElement(maps,'record',{'from':name,'to':f"graphics/pictures/team/{row['uid']}/kits/{row['slot']}/2007"})
 ET.indent(tree,space='\t')
 text=ET.tostring(tree,encoding='unicode')
 oldtext,bom,codec=decode_xml(old)
 new=bom+text.encode(codec)
 assert keepattrs(old,slots)==keepattrs(new,slots)
 ET.fromstring(new)
 changes.append(dict(path=path,old=old,new=new,kind='modern_xml',backup=OUT/'backups/modern-config-before-FC12.xml',codec=codec))
 def serial(e):
  return dict(path=str(e['path']),kind=e['kind'],before_sha256=digest(e['old'])if e['old']is not None else None,
    after_sha256=digest(e['new']),backup=str(e['backup'])if e['backup']else None,
    **{k:e[k]for k in ['removed_maps','codec']if k in e})
 configpins={p:digest(raw)for p,raw in rawconfigs.items()}
 dump(OUT/'installation-plan.json',dict(status='prevalidated',initial_images=318,final_images=1700,
   png_additions=1382,png_replacements=172,owned_slots=sorted(slots),baseline_image_pins=oldpins,
   final_image_pins=final,config_pins_before=configpins,changes=[serial(e)for e in changes],
   legacy_files=len(legacy),legacy_maps_removed=sum(len(x['removed_maps'])for x in legacy),
   conditioned_FM08_year=2007,source_conditional_selected=len(conditioned),policy=POLICY))
 prepared=[];written=[]
 try:
  for e in changes:
   path=e['path'];assert path.resolve().is_relative_to(base)
   assert pin(path)==(digest(e['old'])if e['old']is not None else None)
   if e['backup']:
    backup=e['backup'];assert not backup.resolve().is_relative_to(ROOT/'Dane/graphics')
    backup.parent.mkdir(parents=True,exist_ok=True)
    if backup.exists():assert backup.read_bytes()==e['old']
    else:backup.write_bytes(e['old'])
    assert pin(backup)==digest(e['old'])
   tmp=path.with_name(path.name+'.FC12.tmp');assert not tmp.exists()
   tmp.write_bytes(e['new'])
   if e['kind']!='png':ET.parse(tmp)
   prepared.append((e,tmp))
  for path,pinhash in configpins.items():assert pin(Path(path))==pinhash
  assert{p.stem:pin(p)for p in KITS.glob('*.png')}==oldpins
  for e,tmp in prepared:
   assert pin(e['path'])==(digest(e['old'])if e['old']is not None else None)
   tmp.replace(e['path']);written.append(e)
  assert{p.stem:pin(p)for p in KITS.glob('*.png')}==final
  for name in set(oldpins)-{str(x['uid'])+'_'+x['slot']for x in mods}:assert pin(KITS/(name+'.png'))==oldpins[name]
  for e in changes:
   assert pin(e['path'])==digest(e['new'])
   if e['kind']!='png':assert keepattrs(e['old'],slots)==keepattrs(e['path'].read_bytes(),slots)
  changed={str(e['path'])for e in changes if e['kind']!='png'}
  for path,pinhash in configpins.items():
   if path not in changed:assert pin(Path(path))==pinhash
  resources=collections.defaultdict(list);xmls=list((ROOT/'Dane/graphics').rglob('config.xml'))
  for path in xmls:
   tree=ET.fromstring(path.read_bytes())
   for node in tree.iter('record'):
    if kitkey(node)in slots:resources[node.get('to')].append(dict(config=str(path),source=node.get('from')))
  for name in final:
   uid,slot=name.split('_');key=f'graphics/pictures/team/{uid}/kits/{slot}'
   assert resources[key]==[dict(config=str(KITS/'config.xml'),source=name)],('resource_collision',key,resources[key])
  for key,entries in resources.items():
   assert len(entries)==1 and entries[0]['config']==str(KITS/'config.xml')
   assert(KITS/(entries[0]['source']+'.png')).is_file()
   suffix=key.rsplit('/',1)[-1]
   if suffix.isdigit():assert suffix=='2007'
  for path in KITS.glob('*.png'):
   with Image.open(path)as im:im.load();assert im.format=='PNG'and im.size==(130,130)
  result=dict(status='verified',initial_images=318,final_images=1700,new_images=1382,replaced_older_images=172,
   preserved_initial_images=146,clubs_with_kits=670,legacy_xml_changed=len(legacy),
   legacy_maps_removed=sum(len(x['removed_maps'])for x in legacy),global_config_xml_parsed=len(xmls),
   non_target_xml_maps_identical=True,untouched_kit_xml_hashes_identical=True,preserved_initial_png_hashes_identical=True,
   target_resource_collisions=0,all_config_links_exist=True,modern_year_2026_not_carried=True,
   selected_conditional_sources=len(conditioned),normalized_FM08_year=2007,policy=POLICY,
   output_image_pins=final,changed_file_pins=[dict(path=str(e['path']),sha256=digest(e['new']))for e in changes])
  dump(receipt,result)
 except Exception as error:
  rollback=[]
  for e in reversed(written):
   if pin(e['path'])!=digest(e['new']):rollback.append(dict(path=str(e['path']),status='concurrent_change_preserved'));continue
   if e['old']is None:e['path'].unlink()
   else:
    temp=e['path'].with_name(e['path'].name+'.FC12.rollback')
    temp.write_bytes(e['old']);temp.replace(e['path'])
   rollback.append(dict(path=str(e['path']),status='restored'))
  for _,tmp in prepared:
   if tmp.exists():tmp.unlink()
  dump(receipt,dict(status='failed_rolled_back',error=repr(error),rollback=rollback))
  raise
 print(json.dumps({k:v for k,v in result.items()if k not in['output_image_pins','changed_file_pins']}),flush=True)
def verify():
 import xml.etree.ElementTree as ET
 result=json.loads((OUT/'installation-result.json').read_text(encoding='utf-8'));assert result['status']=='verified'
 plan=json.loads((OUT/'installation-plan.json').read_text(encoding='utf-8'))
 actual={p.stem:pin(p)for p in KITS.glob('*.png')};assert actual==result['output_image_pins']
 for e in result['changed_file_pins']:assert pin(Path(e['path']))==e['sha256']
 slots={tuple(x)for x in plan['owned_slots']}
 resources=collections.defaultdict(list);xmls=list((ROOT/'Dane/graphics').rglob('config.xml'))
 for path in xmls:
  root=ET.parse(path).getroot()
  for n in root.iter('record'):
   if kitkey(n)in slots:resources[n.get('to')].append((str(path),n.get('from')))
 for key,entries in resources.items():
  assert len(entries)==1 and entries[0][0]==str(KITS/'config.xml')
  assert(KITS/(entries[0][1]+'.png')).is_file()
 pixels=[]
 for row in json.loads((OUT/'stage-ledger.json').read_text(encoding='utf-8'))['rows'][:30]:
  if row['status']not in['add','replace_older']:continue
  name=str(row['uid'])+'_'+row['slot']+'.png'
  with Image.open(STAGE/name)as a,Image.open(KITS/name)as b:
   for point in[(0,0),(65,65),(129,129)]:assert a.getpixel(point)==b.getpixel(point)
   pixels.append(name)
 checked=dict(status='independent_readback_verified',images=len(actual),clubs=len({s.split('_')[0]for s in actual}),
   config_xml_parsed=len(xmls),kit_resources=len(resources),selected_pixel_files=pixels,
   image_hashes_match=True,all_resource_mappings_unique=True,all_links_exist=True,policy=POLICY)
 dump(OUT/'independent-verification.json',checked)
 print(json.dumps(checked),flush=True)

if __name__=='__main__':
 if sys.argv[1]=='fetch':fetch()
 elif sys.argv[1]=='stage':stage()
 elif sys.argv[1]=='install':install()
 elif sys.argv[1]=='verify':verify()
 else:raise ValueError('unknown_phase')
