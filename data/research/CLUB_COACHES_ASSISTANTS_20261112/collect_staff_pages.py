from pathlib import Path
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor
import sys,csv,json,re,html,datetime,hashlib,urllib.request,urllib.error,time,threading
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
import collect_staff as base
B=Path(__file__).resolve().parent;ROOT=base.ROOT;R=base.R
D=B/'sources/staff-pages';D.mkdir(parents=True,exist_ok=True)
class Node:
 def __init__(self,tag='',attrs=None,parent=None):self.tag=tag;self.attrs=dict(attrs or []);self.children=[];self.parent=parent
 def text(self):return ' '.join((x.text() if isinstance(x,Node) else x) for x in self.children).strip()
 def all(self,tag):return [x for c in self.children if isinstance(c,Node) for x in ([c] if c.tag==tag else [])+c.all(tag)]
class DOM(HTMLParser):
 def __init__(self):super().__init__();self.root=Node();self.cur=self.root
 def handle_starttag(self,tag,attrs):
  n=Node(tag,attrs,self.cur);self.cur.children.append(n)
  if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:self.cur=n
 def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs);self.handle_endtag(tag)
 def handle_endtag(self,tag):
  n=self.cur
  while n.parent:
   if n.tag==tag:self.cur=n.parent;return
   n=n.parent
 def handle_data(self,data):self.cur.children.append(data)
def parse(raw):
 dom=DOM();dom.feed(raw);out=[]
 for table in dom.root.all('table'):
  if table.attrs.get('class')=='inline-table':continue
  # Every staff row has its own nested inline table with a trainer link and role row.
  for tb in [x for x in table.children if isinstance(x,Node) and x.tag=='tbody']:
   for tr in [x for x in tb.children if isinstance(x,Node) and x.tag=='tr']:
    cells=[x for x in tr.children if isinstance(x,Node) and x.tag=='td']
    if len(cells)<4:continue
    inner=[x for x in cells[0].all('table') if 'inline-table' in x.attrs.get('class','')]
    if len(inner)!=1:continue
    links=[a for a in inner[0].all('a') if re.search(r'/profil/trainer/\d+',a.attrs.get('href',''))]
    if len(links)!=1:continue
    trs=[x for x in inner[0].children if isinstance(x,Node) and x.tag=='tr']
    if len(trs)<2:continue
    role=re.sub(r'\s+',' ',trs[-1].text()).strip();a=links[0];pid=re.search('/trainer/(\d+)',a.attrs['href'])[1]
    out.append(dict(name=a.text(),externalPersonID='TM-coach:'+pid,source_role=role,source_person_url='https://www.transfermarkt.com'+a.attrs['href'],source_effective_date=re.sub(r'\s+',' ',cells[3].text()),contract_expires_raw=re.sub(r'\s+',' ',cells[4].text()) if len(cells)>4 else '',nationality='|'.join(x.attrs.get('title','') for x in cells[2].all('img')),age_display=cells[1].text()))
 return out
STOP=threading.Event()
def fetch(c):
 tid=c['TMID'];url=c['staff_page_url'];key=hashlib.sha256(url.encode()).hexdigest();p=D/(key+'.html');mp=D/(key+'.json')
 if mp.exists():
  x=base.read(mp);x['reused']=True;return c,x
 if STOP.is_set():return c,dict(status='skipped_provider_stop')
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'text/html'})
  try:
   with urllib.request.urlopen(req,timeout=22) as res:raw=res.read(6*1024*1024);status=res.status
  except urllib.error.HTTPError as e:status=e.code;raw=e.read(200000)
  p.write_bytes(raw);x=dict(url=url,status=status,file=str(p.relative_to(ROOT)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),fetched_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),reused=False)
  if status in [403,429]:STOP.set();x['provider_stop']=True
  if status==200:x['parsed_roles']=parse(raw.decode('utf-8',errors='replace'))
 except Exception as e:x=dict(url=url,status=0,error=type(e).__name__+': '+str(e),fetched_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
 mp.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8');return c,x

def run():
 base.offline()
 cov=base.rows(B/'club-coverage.csv');profiles={}
 for p in R.glob('*/sources/tm-clubs/*profile.json'):
  try:
   v=base.read(p)
   if v.get('url') and v.get('updated_at','')>=profiles.get(str(v.get('id')),{}).get('updated_at',''):profiles[str(v.get('id'))]=v
  except Exception:pass
 jobs=[]
 for c in cov:
  if not c['TMID']:continue
  v=profiles.get(c['TMID'],{});url=v.get('url','')
  c['staff_page_url']='https://www.transfermarkt.com'+url.replace('/startseite/','/mitarbeiter/') if '/startseite/' in url else c['staff_page_url']
  jobs.append(c)
 # Interleave countries so a bounded first pass covers the entire accepted footprint.
 bycountry=collections.defaultdict(list)
 for c in jobs:bycountry[(c['accepted_or_pending'],c['country'])].append(c)
 queue=[]
 for state in ['accepted_X15_lineage','pending_X16_NOT_ACCEPTED']:
  groups=[xs for (s,k),xs in bycountry.items() if s==state]
  for i in range(max([len(xs) for xs in groups],default=0)):
   queue.extend(xs[i] for xs in groups if i<len(xs))
 limit=int(sys.argv[1]) if len(sys.argv)>1 else len(queue);queue=queue[:limit]
 results=[];ledger=[]
 with ThreadPoolExecutor(max_workers=3) as pool:
  for i,(c,x) in enumerate(pool.map(fetch,queue)):
   results.append((c,x));ledger.append(dict(ClubUID=c['ClubUID'],provisionalClubUID=c['provisionalClubUID'],TMID=c['TMID'],**{k:v for k,v in x.items() if k!='parsed_roles'}))
   if (i+1)%15==0:base.dump('staff-page-ledger.json',ledger);print('STAFF_PAGES',i+1,'/',len(queue),'200',sum(y.get('status')==200 for _,y in results),'roles',sum(len(y.get('parsed_roles',[])) for _,y in results),'stop',STOP.is_set(),flush=True)
 base.dump('staff-page-ledger.json',ledger)
 # Report rerender is a separate deterministic action over immutable per-page captures.
 render(results)

def render(results):
 staff=base.rows(B/'staff-report.csv');excluded=[];confirmed=[];keys=set()
 for c,x in results:
  if x.get('status')!=200:continue
  for s in x.get('parsed_roles',[]):
   role=s['source_role'];r=role.casefold();target=''
   if r in {'manager','head coach','head manager','caretaker manager','interim manager','interim coach','caretaker coach'}:target='head_coach'
   elif r in {'assistant manager','assistant coach','assistant trainer','co-trainer'}:target='assistant_manager'
   elif 'assistant' in r and 'goal' not in r and 'fit' not in r and 'athletic' not in r and 'performance' not in r:target='assistant_role_REVIEW_REQUIRED'
   if not target:excluded.append(dict(c,**s,reason='Role outside head coach / assistant manager scope'));continue
   row={k:c[k] for k in ['ClubUID','provisionalClubUID','TMID','club','country','league','accepted_or_pending']};row.update(s);row.update(role=target,first_name='',last_name='',nativePersonUID_if_verified='',DOB_real='',DOB_precision='unknown',sourceURL=x['url'],source_season='2026' if re.search(r'season="2026"',Path(ROOT/x['file']).read_text(encoding='utf-8',errors='replace')) else '',source_fetched_at=x['fetched_at'],source_updated_at='',checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='CURRENT_STAFF_PAGE_ROLE_CONFIRMED_IDENTITY_ENRICHMENT_PENDING' if target!='assistant_role_REVIEW_REQUIRED' else 'ROLE_REVIEW_REQUIRED',source_file=x['file'],source_sha256=x['sha256'],identity_source_file='',identity_source_sha256='',source_excerpt=role+' | '+s['name']+' | appointed '+s['source_effective_date'],native_import_ready='NO')
   confirmed.append(row);keys.add((c['ClubUID'],c['provisionalClubUID']))
 # Preserve 90minut as primary Poland head evidence; other cached profile rows become corroboration.
 for r in staff:
  if (r['ClubUID'],r['provisionalClubUID']) in keys and r['country'] not in {'Polska','Poland'}:r['status']='SUPERSEDED_BY_NEW_STAFF_PAGE_CAPTURE'
 rows=staff+confirmed;fields=list(staff[0])+['source_person_url','contract_expires_raw','age_display'];base.write('staff-report.csv',rows,fields)
 if excluded:base.write('staff-roles-outside-scope.csv',excluded)
 gap=base.rows(B/'gaps.csv');have={(r['ClubUID'],r['provisionalClubUID'],r['role']) for r in confirmed if r['role'] in ['head_coach','assistant_manager']}
 for g in gap:
  if (g['ClubUID'],g['provisionalClubUID'],g['role']) in have:g['status']='EVIDENCE_COLLECTED_SEE_STAFF_REPORT';g['detail']='All matching assistants retained. Identity metadata / native mapping still pending.'
 base.write('gaps.csv',gap)
 stats=base.read(B/'summary.json');stats.update(staff_pages_requested=len(results),staff_pages_200=sum(x.get('status')==200 for _,x in results),new_network_calls=sum(not x.get('reused',False) and isinstance(x.get('status'),int) for _,x in results),assistant_rows=sum(r['role']=='assistant_manager' for r in confirmed),confirmed_current_head_coach_rows=sum(r['role']=='head_coach' for r in confirmed),staff_page_role_rows=len(confirmed),excluded_specialist_role_rows=len(excluded),provider_stopped=STOP.is_set(),head_coach_rows=len([r for r in rows if r['role']=='head_coach']),DOB_complete=sum(bool(r['DOB_real']) for r in rows));base.dump('summary.json',stats);print(json.dumps(stats),flush=True)
import collections
if __name__=='__main__':run()
