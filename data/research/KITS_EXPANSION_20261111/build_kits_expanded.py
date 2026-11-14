import sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'GRAPHICS_MODERN_2627_20261111'))
from pathlib import Path
import urllib.request,urllib.parse,re,json,time,concurrent.futures,csv,html,sys,hashlib,xml.etree.ElementTree as ET
from html.parser import HTMLParser
from build_graphics import OUT,CACHE,ROOT,LOGON,LOGOS,KITS,obtain,render,update_config,sha
OUT=ROOT/'FmLauncher/data/research/KITS_EXPANSION_20261111'
OUT.mkdir(exist_ok=True)
import shutil
backup=OUT/'backups'
backup.mkdir(exist_ok=True)
if not (backup/'config-before-expansion.xml').exists():shutil.copy2(KITS/'config.xml',backup/'config-before-expansion.xml')
before={p.name:sha(p) for p in KITS.glob('*.png')}
(OUT/'initial-image-pins.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
class Links(HTMLParser):
 def __init__(self):super().__init__();self.rows=[];self.href=None;self.words=[]
 def handle_starttag(self,t,a):
  a=dict(a)
  if t=='a':self.href=a.get('href');self.words=[]
 def handle_data(self,s):
  if self.href:self.words.append(s)
 def handle_endtag(self,t):
  if t=='a' and self.href:self.rows.append((self.href,' '.join(self.words).strip()));self.href=None
def links(t):p=Links();p.feed(t);return p.rows
def fetch(url):
 key=hashlib.sha256(url.encode()).hexdigest()
 p=CACHE/('html-'+key+'.html')
 if not p.exists():
  time.sleep(.6)
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
  raw=urllib.request.urlopen(req,timeout=12).read(3*1024*1024)
  p.write_bytes(raw)
 return p.read_text(encoding='utf-8',errors='replace')
def norm(s):
 import unicodedata
 s=''.join(c for c in unicodedata.normalize('NFKD',s.casefold()) if not unicodedata.combining(c))
 return re.sub('[^a-z0-9]+',' ',s).strip()
def key(s):
 return ' '.join(w for w in norm(s).split() if w not in {'fc','afc','cf','sc','fk','ks','ac','ssc','fcu','nk','sk','ff','bk','if','ik','bsc','us','as','ss','u','s'})
def run():
 base='https://www.thesportsdb.com'
 page=fetch(base+'/sport/soccer?all=1')
 prefixes={'polish':'Polska','italian':'Włochy','hungarian':'Węgry','welsh':'Walia','american-major-league':'USA / MLS','uruguayan':'Urugwaj','ukrainian':'Ukraina','turkish':'Turcja','swedish':'Szwecja','swiss':'Szwajcaria','scottish':'Szkocja','slovak':'Słowacja','slovenian':'Słowenia','singapore':'Singapur'}
 leagueurls={}
 for href,text in links(page):
  slug=href.lower()
  if '/league/' not in slug or any(w in slug for w in ['women','feminin','u21','u19','youth','cup']):continue
  for prefix,country in prefixes.items():
   if re.search(r'/league/\d+-'+prefix+'(?:-|$)',slug):leagueurls[urllib.parse.urljoin(base,href)]=country
 teams={}
 def leaguejob(pair):
  url,country=pair
  try:
   t=fetch(url);found=[]
   for href,label in links(t):
    m=re.search(r'/team/(\d+)-([^/?]+)',href)
    if m:found.append((m.group(1),country,urllib.parse.unquote(m.group(2)).replace('-',' '),label,url))
   return found
  except Exception as e:return []
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for rows in pool.map(leaguejob,leagueurls.items()):
   for tid,country,slug,label,url in rows:
    if tid not in teams:teams[tid]=dict(id=tid,country=country,names=set(),sources=set())
    teams[tid]['names'].update([key(slug),key(label)]);teams[tid]['sources'].add(url)
 targetcsv=ROOT/'FmLauncher/data/research/CLUB_GRAPHICS_20261111/LISTA_KLUBOW_UID_NAZWA_LIGA.csv'
 with targetcsv.open(encoding='utf-8-sig',newline='') as f:clubs=list(csv.DictReader(f,delimiter=';'))
 # Additional aliases are exact native names or exact TM profile names bound by our verified ClubUID.
 aliases={}
 meta=ROOT/'FmLauncher/data/research/SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/world-club-identities.csv'
 for r in csv.DictReader(meta.open(encoding='utf-8-sig',newline='')):
  aliases[r['ClubUID']]=set(key(n) for n in r['Names'].split('|') if key(n))
 matches=[]
 for club in clubs:
  country=club['Liga'].split(' — ')[0]
  clubnames=aliases.get(club['UID'],set())|{key(club['Nazwa klubu'])}
  candidates=[v for v in teams.values() if v['country']==country and bool(clubnames & v['names'])]
  if len(candidates)==1:matches.append(dict(uid=club['UID'],club=club['Nazwa klubu'],country=country,team_id=candidates[0]['id'],league_sources=sorted(candidates[0]['sources'])))
 dump=dict(league_urls=leagueurls,source_teams=len(teams),verified_club_matches=matches)
 (OUT/'kit-club-matches-expanded.json').write_text(json.dumps(dump,ensure_ascii=False,indent=2),encoding='utf-8')
 print('leagues',len(leagueurls),'teams',len(teams),'matches',len(matches),flush=True)
 results=[]
 def kitjob(club):
  uid=club['uid'];url=base+'/equipment/'+club['team_id']
  try:
   t=fetch(url)
   wanted=['2026-2027','2026','2025-2026','2025','2024-2025','2024']
   sections=re.split(r'<h2>([^<]+)</h2>',t)
   selected={}
   for season in wanted:
    for i in range(1,len(sections),2):
     if html.unescape(sections[i]).strip()!=season:continue
     section=sections[i+1]
     for slot,labels in [('home',['1st Kit','Home Kit','Primary Kit']),('away',['Away Kit','2nd Kit']),('third',['3rd Kit','Third Kit'])]:
      if slot in selected:continue
      for card in re.findall(r'<td[^>]*class=[\x22\x27]equipment-card[\x22\x27][^>]*>(.*?)</td>',section,re.S):
       card=card.lstrip()
       if not any(re.match(re.escape(label)+r'(?:<|\s)',card,re.I) for label in labels):continue
       m=re.search(r'<a href=[\x22\x27](https://[^\x22\x27]+/equipment/[^\x22\x27]+)[\x22\x27]',card)
       if m:selected[slot]=(slot,html.unescape(m.group(1)),season);break
   candidates=list(selected.values())
   rows=[]
   for slot,img,season in candidates:
    image,cache=obtain(img)
    target=KITS/(uid+'_'+slot+'.png')
    added=render(image,130,target)
    rows.append(dict(uid=uid,club=club['club'],slot=slot,status='added' if added else 'preserved_existing',season=season,url=img,page=url,source_cache=str(cache),source_sha256=sha(cache),output=str(target),sha256=sha(target)))
   return rows or [dict(uid=uid,club=club['club'],status='no_kit_in_last_three_seasons',page=url)]
  except Exception as e:return [dict(uid=uid,club=club['club'],status='source_error',page=url,error=type(e).__name__+':'+str(e)[:120])]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for n,rows in enumerate(pool.map(kitjob,matches),1):
   results.extend(rows)
   if n%20==0:print('kits',n,'/',len(matches),'added',sum(x['status']=='added' for x in results),flush=True)
 maps=ET.Element('record');ET.SubElement(maps,'boolean',{'id':'preload','value':'false'});ET.SubElement(maps,'boolean',{'id':'amap','value':'false'});lst=ET.SubElement(maps,'list',{'id':'maps'})
 for p in sorted(KITS.glob('*.png')):
  m=re.fullmatch(r'(\d+)_(home|away|third)',p.stem)
  assert m
  ET.SubElement(lst,'record',{'from':p.stem,'to':f'graphics/pictures/team/{m[1]}/kits/{m[2]}'})
 ET.indent(maps,space='\t')
 config=KITS/'config.xml';tmp=config.with_suffix('.xml.tmp');ET.ElementTree(maps).write(tmp,encoding='utf-8');ET.parse(tmp);tmp.replace(config)
 (OUT/'kits-expanded-ledger.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
 assert all((KITS/name).exists() and sha(KITS/name)==digest for name,digest in before.items())
 for file in KITS.glob('*.png'):
  from PIL import Image
  with Image.open(file) as im:assert im.format=='PNG' and im.size==(130,130)
 output=dict(initial_images=len(before),final_images=len(list(KITS.glob('*.png'))),added_images=sum(x['status']=='added' for x in results),clubs_with_kits=len({p.stem.split('_')[0] for p in KITS.glob('*.png')}),matched_clubs=len(matches),policy='newest confirmed actual kit per slot; 2026/27 or calendar2026 first, fallback2025/26 or2025, then2024/25 or2024; existingimagespreserved')
 (OUT/'verification.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
 print(json.dumps(output),flush=True)
 print('KIT_DONE',len(results),'added',sum(x['status']=='added' for x in results),'club_matches',len(matches),flush=True)
if __name__=='__main__':run()
