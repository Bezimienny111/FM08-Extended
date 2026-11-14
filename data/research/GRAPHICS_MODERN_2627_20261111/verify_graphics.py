from pathlib import Path
import json,re,collections,hashlib,csv,xml.etree.ElementTree as ET
from PIL import Image
root=Path('FmLauncher/data/research/GRAPHICS_MODERN_2627_20261111')
folders={'faces':(Path('Dane/graphics/pictures/faces/normal/modern_2627'),180,r'graphics/pictures/person/(\d+)/portrait'),'logos_normal':(Path('Dane/graphics/pictures/logos/clubs/normal/modern_2627'),180,r'graphics/pictures/club/(\d+)/logo'),'logos_small':(Path('Dane/graphics/pictures/logos/clubs/small/modern_2627'),20,r'graphics/pictures/club/(\d+)/icon'),'kits':(Path('Dane/graphics/pictures/kits/2d/modern_2627'),130,r'graphics/pictures/team/(\d+)/kits/(home|away|third)')}
report={}
for kind,(folder,size,pattern) in folders.items():
 records=[r for r in ET.parse(folder/'config.xml').getroot().iter('record') if r.get('to')]
 targets=[r.get('to') for r in records]
 assert len(targets)==len(set(targets)),kind
 files=set()
 for node in records:
  assert re.fullmatch(pattern,node.get('to')),(kind,node.attrib)
  p=folder/(node.get('from')+'.png')
  assert p.is_file(),p
  with Image.open(p) as im:
   assert im.size==(size,size) and im.format=='PNG',(p,im.size)
   im.verify()
  files.add(p.name)
 report[kind]=dict(folder=str(folder.resolve()),maps=len(records),files=len(files),size=[size,size],config_sha256=hashlib.sha256((folder/'config.xml').read_bytes()).hexdigest())
facefolder=folders['faces'][0]
orig=root/'backups/face-110ff144bc0a9e2933049cfdb75ce3be9b2ebaa08a19ae753343905bfebbf2a5.xml'
assert orig.is_file()
old={(x.get('to'),x.get('from')) for x in ET.parse(orig).getroot().iter('record') if x.get('to')}
new={(x.get('to'),x.get('from')) for x in ET.parse(facefolder/'config.xml').getroot().iter('record') if x.get('to')}
assert old<=new
report['original_face_mappings_preserved']=len(old)
report['added_face_mappings']=len(new-old)
logos={p.stem for p in folders['logos_normal'][0].glob('*.png')}
conflicts=[]
for path in Path('Dane/graphics/pictures/logos').rglob('config.xml'):
 if 'modern_2627' in path.parts:continue
 try:nodes=ET.parse(path).getroot().iter('record')
 except ET.ParseError:continue
 for node in nodes:
  target=node.get('to','');m=re.fullmatch(r'graphics/pictures/club/(\d+)/(logo|icon)',target)
  if not m or m[1] not in logos:continue
  source=path.parent/(node.get('from','')+'.png')
  if source.is_file():conflicts.append(dict(uid=int(m[1]),kind=m[2],config=str(path),source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
(root/'legacy-logo-resource-conflicts.json').write_text(json.dumps(conflicts,ensure_ascii=False,indent=2),encoding='utf-8')
report['legacy_logo_conflicting_entries']=len(conflicts)
report['legacy_logo_conflicting_uids']=len(set(x['uid'] for x in conflicts))
kits=json.loads((root/'kits-ledger.json').read_text(encoding='utf-8'))
report['kit_clubs_with_added_images']=len(set(x['uid'] for x in kits if x['status']=='added'))
report['kit_images_added']=sum(x['status']=='added' for x in kits)
report['all_checks_pass']=True
(root/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
