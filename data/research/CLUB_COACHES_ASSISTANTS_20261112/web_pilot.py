from pathlib import Path
import urllib.request,urllib.error,json,hashlib,datetime,sys
sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;D=B/'sources/web';D.mkdir(parents=True,exist_ok=True)
urls=['https://www.transfermarkt.com/bayern-munich/mitarbeiter/verein/27','https://fcbayern.com/en/teams/first-team/coaches-and-staff/rene-mari%C4%87','https://fcbayern.com/en/news/2025/12/fc-bayern-extend-contracts-of-coaching-team']
ledger=[]
for url in urls:
 p=D/(hashlib.sha256(url.encode()).hexdigest()+'.html');status=0;err='';reused=p.exists()
 if reused:raw=p.read_bytes();status=200
 else:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'text/html'})
  try:
   with urllib.request.urlopen(req,timeout=25) as res:raw=res.read(6*1024*1024);status=res.status
  except urllib.error.HTTPError as e:status=e.code;raw=e.read(100000);err=str(e)
  except Exception as e:raw=b'';err=type(e).__name__+': '+str(e)
  p.write_bytes(raw)
 x=dict(url=url,status=status,file=str(p.relative_to(B)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),error=err,fetched_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),reused=reused);ledger.append(x);print(json.dumps(x),flush=True)
(B/'web-pilot-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2),encoding='utf-8')
