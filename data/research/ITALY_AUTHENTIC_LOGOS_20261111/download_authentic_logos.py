from pathlib import Path
import json,sys,concurrent.futures,hashlib
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
sys.path.insert(0,str(OUT.parent/'GRAPHICS_MODERN_2627_20261111'))
from build_graphics import obtain,render,sha
PLAN=OUT/'authentic-logo-plan.json'
plan=json.loads(PLAN.read_text(encoding='utf-8'))
targets=plan['targets']
assert len(targets)==132 and len({int(x['uid'])for x in targets})==132
for x in targets:
 assert x['url']=='https://tmssl.akamaized.net/images/wappen/normal/'+str(x['tmid'])+'.png'
STAGE=OUT/'staging'
for size in ['normal','small']:(STAGE/size).mkdir(parents=True,exist_ok=True)

def imagecheck(path,size):
 raw=path.read_bytes()
 assert raw.startswith(b'\x89PNG\r\n\x1a\n'),str(path)
 with Image.open(path)as image:
  image.load()
  assert image.format=='PNG'and image.mode=='RGBA'and image.size==(size,size)
  alpha=image.getchannel('A')
  assert alpha.getbbox()is not None
  assert alpha.getextrema()[0]==0 and alpha.getextrema()[1]>0,('no_transparent_canvas',str(path))
 return {'sha256':sha(path),'bytes':len(raw),'size':[size,size],'mode':'RGBA'}

def job(x):
 try:
  image,cache=obtain(x['url'])
  normal=STAGE/'normal'/f"{x['uid']}.png"
  small=STAGE/'small'/f"{x['uid']}.png"
  render(image,180,normal);render(image,20,small)
  return dict(status='staged',**x,source_cache=str(cache),source_sha256=sha(cache),
    normal=imagecheck(normal,180),small=imagecheck(small,20))
 except Exception as e:return dict(status='failed',**x,error=type(e).__name__+':'+str(e))
 
def board(items,path):
 cols=min(6,len(items));cellw=150;cellh=146
 canvas=Image.new('RGB',(cols*cellw,((len(items)+cols-1)//cols)*cellh),(239,242,247))
 draw=ImageDraw.Draw(canvas)
 try:font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',12)
 except OSError:font=ImageFont.load_default()
 for i,item in enumerate(items):
  im=Image.open(STAGE/'normal'/f"{item['uid']}.png").convert('RGBA')
  im.thumbnail((112,112),Image.Resampling.LANCZOS)
  x=(i%cols)*cellw;y=(i//cols)*cellh
  canvas.paste(im,(x+(cellw-im.width)//2,y+4),im)
  name=str(item['uid'])+' '+item['club']
  draw.text((x+4,y+118),name[:23],fill=(0,0,0),font=font)
  draw.text((x+4,y+132),'TM '+str(item['tmid']),fill=(60,70,80),font=font)
 canvas.save(path)
 
mode=sys.argv[1]
if mode=='samples':
 chosen=[x for x in targets if int(x['uid'])in{1106,1099,1105,1108,1110}]
 assert len(chosen)==5
else:
 assert mode=='all'
 chosen=targets
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=6)as pool:
 for i,item in enumerate(pool.map(job,chosen),1):
  results.append(item)
  if i%25==0:print('staged',i,'/',len(chosen),flush=True)
ledger={'source_plan_sha256':sha(PLAN),'scope':mode,'targets':len(chosen),'staged':sum(x['status']=='staged'for x in results),
 'failed':sum(x['status']=='failed'for x in results),'results':results}
(OUT/(mode+'-download-ledger.json')).write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
ok=[x for x in results if x['status']=='staged']
if mode=='samples'and ok:board(ok,OUT/'samples-authentic.png')
if mode=='all'and len(ok)==132:
 for i in range(2):board(ok[i*66:(i+1)*66],OUT/f'all-authentic-{i+1}.png')
print(json.dumps({'scope':mode,'targets':len(chosen),'staged':len(ok),'failed':ledger['failed']}),flush=True)
if ledger['failed']:
 print(json.dumps([x for x in results if x['status']=='failed'],ensure_ascii=False),flush=True)
 raise SystemExit(1)
