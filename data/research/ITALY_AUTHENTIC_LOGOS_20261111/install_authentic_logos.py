from pathlib import Path
import json,re,hashlib,xml.etree.ElementTree as ET,sys,collections
from PIL import Image
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
BASE=(ROOT/'Dane/graphics/pictures/logos').resolve()
FOLDERS={k:BASE/'clubs'/k/'modern_2627'for k in ['normal','small']}
TARGETS=json.loads((OUT/'authentic-logo-plan.json').read_text(encoding='utf-8'))['targets']
UIDS={int(x['uid'])for x in TARGETS}
STAGE=OUT/'staging'
RESULT=OUT/'installation-result.json'
def sha(data):return hashlib.sha256(data).hexdigest()
def pin(path):return sha(path.read_bytes())if path.exists()else None
def dump(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def mapping(node):
 m=re.fullmatch(r'graphics/pictures/club/(\d+)/(logo|icon)',node.get('to',''))
 return (int(m[1]),m[2])if m else None
def attrs(raw,exclude):
 return [tuple(sorted(n.attrib.items()))for n in ET.fromstring(raw).iter('record')
   if n.get('to')and not((m:=mapping(n))and m[0]in exclude)]
def decode(raw):
 if raw.startswith(b'\xff\xfe'):bom,codec=b'\xff\xfe','utf-16-le'
 elif raw.startswith(b'\xfe\xff'):bom,codec=b'\xfe\xff','utf-16-be'
 elif raw.startswith(b'\xef\xbb\xbf'):bom,codec=b'\xef\xbb\xbf','utf-8'
 elif raw.startswith(b'<\x00'):bom,codec=b'','utf-16-le'
 elif raw.startswith(b'\x00<'):bom,codec=b'','utf-16-be'
 else:
  bom=b''
  m=re.search(br'<\?xml[^>]*encoding=[\x22\x27]([^\x22\x27]+)',raw[:256])
  codec=m[1].decode('ascii')if m else'utf-8'
 text=raw[len(bom):].decode(codec)
 assert bom+text.encode(codec)==raw,'encoding_roundtrip'
 return text,bom,codec
def strip_legacy(raw,uids):
 text,bom,codec=decode(raw)
 selected=[n for n in ET.fromstring(raw).iter('record')if(m:=mapping(n))and m[0]in uids]
 spans=[]
 for match in re.finditer(r'<record\b[^>]*?/\s*>',text):
  node=ET.fromstring(match[0])
  if(m:=mapping(node))and m[0]in uids:spans.append(match.span())
 assert len(spans)==len(selected),('unsupported_non_selfclosing_maps',len(spans),len(selected))
 new=text
 for a,b in reversed(spans):new=new[:a]+new[b:]
 new=bom+new.encode(codec)
 assert attrs(raw,uids)==attrs(new,uids)
 assert not any((m:=mapping(n))and m[0]in uids for n in ET.fromstring(new).iter('record'))
 return new,[n.attrib for n in selected],codec
def pngcheck(path,size):
 with Image.open(path)as im:
  im.load()
  assert im.format=='PNG'and im.mode=='RGBA'and im.size==(size,size)
  assert im.getchannel('A').getextrema()[0]==0 and im.getbbox()
 return pin(path)
def modern_config(raw,kind,expected):
 tree=ET.fromstring(raw)
 nodes=[n for n in tree.iter('record')if n.get('to')]
 keys=[n.get('to')for n in nodes]
 assert len(keys)==len(set(keys))
 resource='logo'if kind=='normal'else'icon'
 for uid in expected:
  found=[n for n in nodes if n.get('to')==f'graphics/pictures/club/{uid}/{resource}']
  assert len(found)==1 and found[0].get('from')==str(uid)
 text,bom,codec=decode(raw)
 added=[]
 for uid in sorted(UIDS):
  key=f'graphics/pictures/club/{uid}/{resource}'
  if key not in keys:added.append(f'\t\t<record from="{uid}" to="{key}" />\n')
 assert text.count('</list>')==1,'unsupported_modern_config'
 new=text.replace('</list>',''.join(added)+'\t</list>',1)
 new=bom+new.encode(codec)
 assert attrs(raw,UIDS)==attrs(new,UIDS)
 ET.fromstring(new)
 return new,len(added),codec

def main():
 assert not RESULT.exists(),'receipt_already_exists_do_not_repeat'
 assert len(UIDS)==132
 ledger=json.loads((OUT/'all-download-ledger.json').read_text(encoding='utf-8'))
 assert ledger['staged']==132 and ledger['failed']==0
 assert ledger['source_plan_sha256']==pin(OUT/'authentic-logo-plan.json')
 byuid={int(x['uid']):x for x in ledger['results']}
 for uid in UIDS:
  for kind,size in [('normal',180),('small',20)]:
   assert pngcheck(STAGE/kind/f'{uid}.png',size)==byuid[uid][kind]['sha256']
 before={kind:{int(p.stem)for p in folder.glob('*.png')if p.stem.isdigit()}for kind,folder in FOLDERS.items()}
 assert before['normal']==before['small']and len(before['normal'])==743
 existing=UIDS&before['normal'];newuids=UIDS-before['normal']
 assert len(existing)==71 and len(newuids)==61
 assert len(before['normal']|UIDS)==804
 config_paths=sorted(BASE.rglob('config.xml'))
 config_before={str(p):pin(p)for p in config_paths}
 allraw={str(p):p.read_bytes()for p in config_paths}
 for data in allraw.values():ET.fromstring(data)
 untouched_png={str(p):pin(p)for folder in FOLDERS.values()for p in folder.glob('*.png')
   if p.stem.isdigit()and int(p.stem)not in UIDS}
 changes=[];legacy=[];modern=[]
 for kind,folder in FOLDERS.items():
  for uid in sorted(UIDS):
   path=folder/f'{uid}.png';old=path.read_bytes()if path.exists()else None
   changes.append(dict(path=path,old=old,new=(STAGE/kind/f'{uid}.png').read_bytes(),kind='png',
    backup=OUT/'backups/modern'/kind/f'{uid}.png'if old is not None else None))
 for path in config_paths:
  if 'modern_2627'in path.parts:continue
  old=allraw[str(path)]
  if not any((m:=mapping(n))and m[0]in newuids for n in ET.fromstring(old).iter('record')):continue
  new,removed,codec=strip_legacy(old,newuids)
  entry=dict(path=path,old=old,new=new,kind='legacy_config',
    backup=OUT/'backups/legacy-configs'/path.relative_to(BASE),removed=removed,codec=codec)
  changes.append(entry);legacy.append(entry)
 for kind,folder in FOLDERS.items():
  path=folder/'config.xml';old=allraw[str(path)]
  new,added,codec=modern_config(old,kind,before[kind])
  assert added==61
  entry=dict(path=path,old=old,new=new,kind='modern_config',
    backup=OUT/'backups/modern-configs'/f'{kind}-config.xml',added=added,codec=codec)
  changes.append(entry);modern.append(entry)
 def serial(e):
  return dict(path=str(e['path']),kind=e['kind'],before_sha256=sha(e['old'])if e['old']is not None else None,
   after_sha256=sha(e['new']),backup=str(e['backup'])if e['backup']else None,
   **({k:e[k]for k in ['removed','added','codec']if k in e}))
 plan=dict(status='prevalidated',source_plan_sha256=pin(OUT/'authentic-logo-plan.json'),
  targets=sorted(UIDS),existing_replaced=sorted(existing),new_added=sorted(newuids),before_count=743,after_count=804,
  legacy_scope_only_new_uids=True,legacy_files=len(legacy),legacy_maps_removed=sum(len(e['removed'])for e in legacy),
  changes=[serial(e)for e in changes],all_config_pins_before=config_before,
  untouched_modern_png_pins=untouched_png)
 dump(OUT/'installation-plan.json',plan)
 prepared=[];written=[]
 try:
  for e in changes:
   path=e['path']
   assert path.resolve().is_relative_to(BASE)
   assert pin(path)==(sha(e['old'])if e['old']is not None else None)
   if e['backup']is not None:
    backup=e['backup'];assert not backup.resolve().is_relative_to(ROOT/'Dane/graphics')
    backup.parent.mkdir(parents=True,exist_ok=True)
    if backup.exists():assert backup.read_bytes()==e['old']
    else:backup.write_bytes(e['old'])
    assert pin(backup)==sha(e['old'])
   tmp=path.with_name(path.name+'.italy-authentic.tmp')
   assert not tmp.exists()
   tmp.write_bytes(e['new'])
   if e['kind']!='png':ET.parse(tmp)
   prepared.append((e,tmp))
  # Every intended write and every untouched config is still pinned before commit.
  for e in changes:assert pin(e['path'])==(sha(e['old'])if e['old']is not None else None)
  for path,digest in config_before.items():assert pin(Path(path))==digest
  for e,tmp in prepared:
   assert pin(e['path'])==(sha(e['old'])if e['old']is not None else None)
   tmp.replace(e['path']);written.append(e)
  for e in changes:
   assert pin(e['path'])==sha(e['new'])
   if e['kind']!='png':
    exclude=newuids if e['kind']=='legacy_config'else UIDS
    assert attrs(e['old'],exclude)==attrs(e['path'].read_bytes(),exclude)
  changed_configs={str(e['path'])for e in changes if e['kind']!='png'}
  for path,digest in config_before.items():
   if path not in changed_configs:assert pin(Path(path))==digest
  for path,digest in untouched_png.items():assert pin(Path(path))==digest
  for kind,folder in FOLDERS.items():
   actual={int(p.stem)for p in folder.glob('*.png')if p.stem.isdigit()}
   assert actual==before[kind]|UIDS and len(actual)==804
   for uid in UIDS:assert pngcheck(folder/f'{uid}.png',180 if kind=='normal'else 20)==byuid[uid][kind]['sha256']
   root=ET.parse(folder/'config.xml').getroot()
   for node in root.iter('record'):
    if node.get('to'):assert (folder/(node.get('from','')+'.png')).is_file()
  resources=collections.defaultdict(list)
  for path in sorted(BASE.rglob('config.xml')):
   tree=ET.parse(path).getroot()
   for node in tree.iter('record'):
    if(m:=mapping(node))and m[0]in UIDS:resources[m].append(dict(config=str(path),source=node.get('from')))
  for uid in UIDS:
   for kind,res in [('normal','logo'),('small','icon')]:
    assert resources[uid,res]==[dict(config=str(FOLDERS[kind]/'config.xml'),source=str(uid))],('resource_collision',uid,res,resources[uid,res])
  pixels=[]
  for uid in [1105,1106,1099,1108,1110]:
   for kind,size in [('normal',180),('small',20)]:
    with Image.open(STAGE/kind/f'{uid}.png')as a,Image.open(FOLDERS[kind]/f'{uid}.png')as b:
     points=[(0,0),(size//2,size//2),(size-1,size-1)]
     for point in points:assert a.getpixel(point)==b.getpixel(point)
     pixels.append(dict(uid=uid,kind=kind,pixels=[dict(x=x,y=y,rgba=b.getpixel((x,y)))for x,y in points]))
  result=dict(status='verified',clubs=132,normal_png=132,small_png=132,existing_replaced=71,new_added=61,
   modern_clubs_total=804,legacy_files_changed=len(legacy),legacy_maps_removed=sum(len(e['removed'])for e in legacy),
   legacy_scope_only_new_61_uids=True,non_target_maps_identical=True,untouched_modern_png_hashes_identical=True,
   untouched_xml_pins_identical=True,all_logo_xml_parse=True,all_modern_config_links_exist=True,
   selected_pixels=pixels,target_resource_collisions=0,backup_root=str(OUT/'backups'),
   expected_file_sha256=[dict(path=str(e['path']),sha256=sha(e['new']))for e in changes],
   visual_review=['samples-authentic.png','all-authentic-1.png','all-authentic-2.png'],
   game_database_launcher_kits_faces_modified=False)
  dump(RESULT,result)
 except Exception as error:
  rollback=[]
  for e in reversed(written):
   path=e['path']
   if pin(path)!=sha(e['new']):
    rollback.append(dict(path=str(path),status='concurrent_change_preserved'));continue
   if e['old']is None:path.unlink()
   else:
    temp=path.with_name(path.name+'.italy-authentic.rollback')
    temp.write_bytes(e['old']);temp.replace(path)
   rollback.append(dict(path=str(path),status='restored'))
  for _,tmp in prepared:
   if tmp.exists():tmp.unlink()
  dump(RESULT,dict(status='failed_rolled_back',error=repr(error),rollback=rollback))
  raise
 print(json.dumps({k:v for k,v in result.items()if k not in ['expected_file_sha256','selected_pixels','visual_review']}),flush=True)

if __name__=='__main__':main()
