from pathlib import Path
import json,concurrent.futures
from build_graphics import OUT,LOGON,LOGOS,obtain,render,update_config,sha
data=json.loads((OUT/'root-pl-it-logo-urls.json').read_text(encoding='utf-8'))
def job(c):
 uid=str(c['uid']);target=LOGON/(uid+'.png')
 if target.exists():return dict(uid=uid,status='preserved_existing')
 try:
  image,cache=obtain(c['url'])
  render(image,180,target);render(image,20,LOGOS/(uid+'.png'))
  return dict(uid=uid,status='added',url=c['url'],source_cache=str(cache),source_sha256=sha(cache),normal_sha256=sha(target),small_sha256=sha(LOGOS/(uid+'.png')),proof=c)
 except Exception as e:return dict(uid=uid,status='failed',error=type(e).__name__+':'+str(e)[:120],proof=c)
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as p:
 for i,row in enumerate(p.map(job,data['candidates']),1):
  results.append(row)
  if i%50==0:print('logo_delta',i,flush=True)
for folder,kind in [(LOGON,'logo_normal'),(LOGOS,'logo_small')]:update_config(folder,kind)
(OUT/'logo-delta-ledger.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print('LOGO_DELTA_DONE',len(results),'added',sum(x['status']=='added' for x in results),flush=True)
