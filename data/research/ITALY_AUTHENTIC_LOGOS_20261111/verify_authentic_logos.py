from pathlib import Path
import json,hashlib,re,collections,xml.etree.ElementTree as ET
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
G=ROOT/'Dane/graphics'
BASE=G/'pictures/logos'
def pin(p):return hashlib.sha256(p.read_bytes()).hexdigest()
result=json.loads((OUT/'installation-result.json').read_text(encoding='utf-8'))
plan=json.loads((OUT/'installation-plan.json').read_text(encoding='utf-8'))
source=json.loads((OUT/'authentic-logo-plan.json').read_text(encoding='utf-8'))['targets']
ledger=json.loads((OUT/'all-download-ledger.json').read_text(encoding='utf-8'))['results']
assert result['status']=='verified'
uids={int(x['uid'])for x in source}
for entry in result['expected_file_sha256']:assert pin(Path(entry['path']))==entry['sha256']
changedxml={x['path']for x in plan['changes']if x['kind']!='png'}
for path,digest in plan['all_config_pins_before'].items():
 if path not in changedxml:assert pin(Path(path))==digest
for path,digest in plan['untouched_modern_png_pins'].items():assert pin(Path(path))==digest
resources=collections.defaultdict(list)
xmls=list(G.rglob('config.xml'))
for path in xmls:
 root=ET.fromstring(path.read_bytes())
 for node in root.iter('record'):
  m=re.fullmatch(r'graphics/pictures/club/(\d+)/(logo|icon)',node.get('to',''))
  if m and int(m[1])in uids:resources[int(m[1]),m[2]].append((str(path),node.get('from')))
for uid in uids:
 for size,kind in [('normal','logo'),('small','icon')]:
  folder=BASE/'clubs'/size/'modern_2627'
  assert resources[uid,kind]==[(str(folder/'config.xml'),str(uid))]
  path=folder/f'{uid}.png'
  with Image.open(path)as im:
   im.load();assert im.mode=='RGBA'and im.size==((180,180)if size=='normal'else(20,20))
  expected=next(x for x in ledger if int(x['uid'])==uid)[size]['sha256']
  assert pin(path)==expected
selected=[next(x for x in source if int(x['uid'])==uid)for uid in [1105,1106,1099,1108,1110]]
canvas=Image.new('RGB',(750,150),(239,242,247));draw=ImageDraw.Draw(canvas)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',13)
for i,row in enumerate(selected):
 im=Image.open(BASE/'clubs/normal/modern_2627'/f"{row['uid']}.png").convert('RGBA')
 im.thumbnail((110,110),Image.Resampling.LANCZOS)
 canvas.paste(im,(i*150+(150-im.width)//2,0),im)
 draw.text((i*150+4,115),str(row['uid'])+' '+row['club'][:17],fill=(0,0,0),font=font)
 draw.text((i*150+4,132),'Transfermarkt '+str(row['tmid']),fill=(50,60,70),font=font)
canvas.save(OUT/'installed-samples-authentic.png')
dups=collections.defaultdict(list)
for row in ledger:dups[row['source_sha256']].append({'uid':row['uid'],'club':row['club'],'tmid':row['tmid']})
audit=dict(status='verified_independently',graphics_config_xml_parsed=len(xmls),
 all_132_club_logo_and_icon_mappings_globally_unique=True,all_264_png_hashes_match_staged_authentic_images=True,
 untouched_logo_xml_and_png_pins_preserved=True,serie_a_b_clubs_included=sum(x['division']in[22,23]for x in source),
 installed_normal_clubs=len(list((BASE/'clubs/normal/modern_2627').glob('*.png'))),
 installed_small_clubs=len(list((BASE/'clubs/small/modern_2627').glob('*.png'))),
 authentic_source_hash_duplicates=[v for v in dups.values()if len(v)>1],
 installed_samples_sha256=pin(OUT/'installed-samples-authentic.png'))
(OUT/'independent-verification.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False),flush=True)
