from pathlib import Path
import urllib.request,urllib.error,json,hashlib,concurrent.futures,datetime
B=Path(__file__).resolve().parent;S=B/'sources';S.mkdir(exist_ok=True)
URLS={
'nir-2025-26':'https://rsssf.org/tablesn/nil2026.html',
'isl-2025':'https://rsssf.github.io/tables/ijs2025.html',
'irl-2025':'https://www.rsssf.org/tablesi/ier2025.html',
'irl-munster-finals':'https://www.rsssf.org/tablesi/iermunsterchamp.html',
'irl-leinster-finals':'https://rsssf.org/tablesi/ierleinsterchamp.html',
'treaty-transition':'https://treatyunitedfc.com/treaty-united-confirms-completion-of-agreement-to-unite-behind-the-limerick-fc-identity/',
'irl-licences-2026':'https://www.leagueofireland.ie/news/2026-league-ireland-club-licences-awarded/',
'nir-conference-participants':'https://www.newsletter.co.uk/sport/football/northern-ireland/nafl-confirm-the-12-clubs-set-to-compete-in-inaugural-conference-league-premier-division-8672554'}
def one(item):
 name,url=item;p=S/(name+'.html');r=dict(Name=name,URL=url,File=str(p.relative_to(B)),RetrievedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat())
 try:
  if p.exists():data=p.read_bytes();r['CacheHit']=True
  else:
   req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; FM08dev source archive)'})
   with urllib.request.urlopen(req,timeout=35) as response:data=response.read();r['HTTPStatus']=response.status;r['ContentType']=response.headers.get('Content-Type')
   p.write_bytes(data);r['CacheHit']=False
  r.update(Status='OK',Bytes=len(data),SHA256=hashlib.sha256(data).hexdigest())
 except Exception as e:r.update(Status='ERROR',Error=type(e).__name__+':'+str(e));(S/(name+'-error.json')).write_text(json.dumps(r,indent=2),encoding='utf-8')
 return r
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:r=list(pool.map(one,URLS.items()))
 (B/'source-index.json').write_text(json.dumps(r,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
 for x in r:print(x['Name'],x['Status'],x.get('Bytes',0),flush=True)
