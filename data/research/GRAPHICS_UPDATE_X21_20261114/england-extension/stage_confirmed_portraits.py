from pathlib import Path
import sys,json,csv,hashlib,collections,concurrent.futures,importlib.util,urllib.parse,urllib.error,threading,base64,datetime
from PIL import Image
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent;O=B/'portrait-stage'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,a):(O/n).write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 O.mkdir(exist_ok=True);(O/'http-errors').mkdir(exist_ok=True)
 audit=read(B/'manifest.json');csvpath=B/'potential-new368-image-cache.csv';assert sha(csvpath)==audit['Outputs'][csvpath.name];allrows=list(csv.DictReader(csvpath.open(encoding='utf-8-sig'),delimiter=';'));items=[x for x in allrows if x['Status']=='CONFIRMED_SOURCE_URL_NOT_CACHED'];assert len(allrows)==368 and len(items)==214
 libpath=R/'GRAPHICS_MODERN_2627_20261111/build_graphics.py';sp=importlib.util.spec_from_file_location('existing_graphics_renderer',libpath);lib=importlib.util.module_from_spec(sp);sp.loader.exec_module(lib);lib.CACHE=B.parent/'cache';lib.CACHE.mkdir(exist_ok=True)
 stop=threading.Event();allowed={'img.a.transfermarkt.technology','tmssl.akamaized.net'}
 def work(x):
  tm=x['TMID'];dob=x['SourceDOB'];url=x['SourcePortraitURL'];assert urllib.parse.urlparse(url).hostname in allowed;target=O/f'tmid_{tm}_{dob}.png';base=dict(TMID=tm,SourceDOB=dob,Name=x['Name'],FinalNativeUID='',SourceURL=url,StagingPath=str(target.relative_to(ROOT)))
  if stop.is_set():return dict(base,Status='not_attempted_provider_block')
  try:
   if target.exists():
    with Image.open(target)as im:assert im.format=='PNG'and im.size==(180,180);im.verify()
    return dict(base,Status='preserved_existing_pending_PNG',SHA256=sha(target))
   image,cache=lib.obtain(url);lib.render(image,180,target,'bottom')
   with Image.open(target)as im:assert im.format=='PNG'and im.size==(180,180);im.verify()
   with Image.open(target)as im:im.load();assert im.convert('RGBA').getbbox()is not None
   return dict(base,Status='ready_PNG_await_final_UID',SHA256=sha(target),SourceCache=str(cache.relative_to(ROOT)),SourceImageSHA256=sha(cache))
  except urllib.error.HTTPError as ex:
   body=ex.read(4096);err=dict(URL=url,HTTPStatus=ex.code,Headers=dict(ex.headers),BodyPrefixBase64=base64.b64encode(body).decode());(O/'http-errors'/f'{tm}.json').write_text(json.dumps(err,indent=2)+'\n',encoding='utf-8')
   if ex.code in[401,403,429]:stop.set()
   return dict(base,Status='HTTP_failure',HTTPStatus=ex.code,Error=str(ex))
  except Exception as ex:return dict(base,Status='render_or_download_failure',Error=type(ex).__name__+': '+str(ex)[:200])
 ledger=O/'download-ledger.jsonl';results=[]
 with ledger.open('a',encoding='utf-8',buffering=1)as f,concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
  for n,res in enumerate(pool.map(work,items),1):
   results.append(res);f.write(json.dumps(res,ensure_ascii=False)+'\n')
   if n%25==0:print(json.dumps(dict(done=n,total=len(items),status=dict(collections.Counter(x['Status']for x in results)),provider_block=stop.is_set())),flush=True)
 ready=[x for x in results if x['Status']in['ready_PNG_await_final_UID','preserved_existing_pending_PNG']]
 assert len({(x['TMID'],x['SourceDOB'])for x in results})==214
 for x in ready:
  p=ROOT/x['StagingPath'];assert sha(p)==x['SHA256']
  with Image.open(p)as im:assert im.format=='PNG'and im.size==(180,180);im.verify()
 assert not(O/'config.xml').exists(),'No gameUID map may be created before final ledger'
 summary=dict(Status='ENGLAND_PORTRAIT_STAGING_AWAIT_FINAL_UID_LEDGER',PotentialNew=368,ConfirmedURLCandidates=214,ReadyPNG=len(ready),Failures=214-len(ready),ExplicitNoURLGaps=154,PNGSize=[180,180],ConfigXMLCreated=False,FinalUIDsAssigned=False,NetworkScope='Only214pinnedportraitURLs; no roster/profile/club queries',ProviderBlocked=stop.is_set(),PublicWrites=0,DBWrites=0,GameAccess=False,Existing23881PNGAndPlansUntouched=True,Distribution='LOCAL_ONLY_NOT_PUBLICATION_APPROVED')
 dump('staging-result.json',dict(Summary=summary,Assets=ready,Unresolved=[x for x in results if x not in ready]));dump('summary.json',summary)
 (O/'WZNOWIENIE.md').write_text('# England portraits - pending final UIDs\n\n'+summary['Status']+'\n\nDo not create config.xml or inferUID fromfilename/TMID. Files tmid_ID_DOB.png are identified bysourceTMID+realDOB only. Join final-native-player-UID-ledger.csv with verifiedfinal-artifact-pins when root sendsit. Then createincremental finalUID mapping/delta withoutchanging threeapproved23881plans.154sourceURLgaps remainexplicit; do notsearchforcibly. No publicinstall until rootHOLDrelease and FM==0.\n',encoding='utf-8')
 dump('manifest.json',dict(Status=summary['Status'],UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),Inputs={str(csvpath):sha(csvpath),str(B/'manifest.json'):sha(B/'manifest.json'),str(libpath):sha(libpath)},ScriptSHA256=sha(Path(__file__)),Outputs={n:sha(O/n)for n in['summary.json','staging-result.json','download-ledger.jsonl','WZNOWIENIE.md']},PublicWrites=0,DBWrites=0,NoGameUIDAssumptions=True));print(json.dumps(summary,ensure_ascii=True),flush=True);print('MANIFEST_SHA256',sha(O/'manifest.json'),flush=True)
if __name__=='__main__':main()
