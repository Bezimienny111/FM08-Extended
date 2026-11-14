from pathlib import Path
import csv,json,re,datetime,sys,collections
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
import collect_staff as b
import collect_staff_pages as web
B=b.B;ROOT=b.ROOT;web.D=B/'sources/poland-pages';web.D.mkdir(parents=True,exist_ok=True)
months={'stycznia':1,'lutego':2,'marca':3,'kwietnia':4,'maja':5,'czerwca':6,'lipca':7,'sierpnia':8,'września':9,'października':10,'listopada':11,'grudnia':12}
def date(t):
 m=re.search(r'(\d{1,2})\s+('+ '|'.join(months)+r')\s+(20\d\d)',t)
 if not m:return ''
 try:return datetime.date(int(m[3]),months[m[2]],int(m[1])).isoformat()
 except ValueError:return ''
def main():
 clubs=[c for c in b.rows(B/'clubs-scope.csv') if c['ClubID90']];jobs=[]
 for c in clubs:c['staff_page_url']='http://www.90minut.pl/skarb.php?id_sezon=109&id_klub='+c['ClubID90'];jobs.append(c)
 got=[]
 from concurrent.futures import ThreadPoolExecutor
 with ThreadPoolExecutor(max_workers=3) as pool:
  for i,(c,x) in enumerate(pool.map(web.fetch,jobs)):
   got.append((c,x))
   if (i+1)%20==0:print('POLAND_PAGES',i+1,'/',len(jobs),'200',sum(z.get('status')==200 for _,z in got),flush=True)
 b.dump('poland-page-ledger.json',[dict(ClubUID=c['ClubUID'],ClubID90=c['ClubID90'],**{k:v for k,v in x.items() if k!='parsed_roles'}) for c,x in got]);timeline=[]
 for c,x in got:
  if x.get('status')!=200:continue
  raw=(ROOT/x['file']).read_bytes().decode('iso-8859-2',errors='replace');m=re.search(r'<tr[^>]*>\s*<td[^>]*>\s*Trener:\s*(.*?)</td>\s*</tr>',raw,re.I|re.S)
  if not m:continue
  names=list(re.finditer(r'<b[^>]*>(.*?)</b>',m[1],re.I|re.S))
  for i,n in enumerate(names):
   name=b.clean(n[1]);name=re.sub(r'\s+',' ',name).strip()
   if not name:continue
   annotation=b.clean(m[1][n.end():names[i+1].start() if i+1<len(names) else None]);name=re.sub(r'\s+[A-Z]{3}(?:/[A-Z]{3})*\s*$','',name).strip()
   start=date(annotation.split('od ',1)[1]) if 'od ' in annotation else '';end=date(annotation.split('do ',1)[1]) if 'do ' in annotation else ''
   if end and end<'2026-11-12':state='HISTORICAL_ENDED'
   elif start and start>'2026-11-12':state='FUTURE_ANNOUNCED'
   elif not end and start:state='CURRENT_AS_OF_12XI_2026_SOURCE_ROLE'
   elif len([z for z in names if b.clean(z[1])])==1:state='CURRENT_SOURCE_ROLE_START_UNKNOWN'
   else:state='TIMELINE_AMBIGUOUS_REVIEW'
   if name.lower() in ['wakat','brak']:state='EXPLICIT_VACANCY_SOURCE' if state.startswith('CURRENT') else state
   timeline.append(dict(ClubUID=c['ClubUID'],provisionalClubUID='',TMID=c['TMID'],club=c['club'],country=c['country'],league=c['league'],accepted_or_pending=c['accepted_or_pending'],role='head_coach',source_role='90minut Trener',name=name,source_effective_date=start,source_end_date=end,status=state,source_annotation=annotation,sourceURL=x['url'],source_file=x['file'],source_sha256=x['sha256'],source_fetched_at=x['fetched_at'],source_season='2026/27' if '2026/27' in raw else '',checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat()))
 if timeline:b.write('poland-coach-timelines.csv',timeline)
 print('POLAND_COMPLETE',len(got),'timeline',len(timeline),'current',sum(x['status'].startswith('CURRENT') for x in timeline),flush=True)
if __name__=='__main__':main()
