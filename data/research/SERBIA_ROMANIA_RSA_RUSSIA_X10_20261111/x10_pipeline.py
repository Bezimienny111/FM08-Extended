"""X10 source collection and immutable input audit. Uses existing shared collectors."""
from pathlib import Path
import sys,json,hashlib,shutil,subprocess,asyncio
from concurrent.futures import ThreadPoolExecutor
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev'); R=ROOT/'FmLauncher/data/research'
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
import ss26prep_collect_20261110 as col
from batch_sweden_switzerland_x3_20261109 import pins
from transfermarkt_api import Transfermarkt
B=R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111';S=B/'sources'
col.B=B;col.S=S
read=col.read;dump=col.dump
COUNTRIES={'Serbia':176,'Romania':164,'South Africa':40,'Russia':165}
def begin():
 assert not (B/'manifest.json').exists() and not (ROOT/'Dane/db/TEST_X10').exists()
 src=ROOT/'Dane/db/TEST_X8'; old=read(R/'THAILAND_LEAGUE_REPLACEMENT_REVIEW_20261110/implementation/X8-user-tested-source-pins.json')
 hp=pins(src);assert hp==old,'X8 changed after last accepted source snapshot'
 frozen=B/'input/X8-accepted';shutil.copytree(src,frozen);assert pins(src)==pins(frozen)==hp
 dump(B/'manifest.json',dict(status='X8_frozen_sources_and_fresh_audit_started',source=str(frozen),source_original=str(src),source_hashes=hp,output=str(ROOT/'Dane/db/TEST_X10'),output_name='TEST_X10',countries=list(COUNTRIES),country_indices=COUNTRIES,real_season='2026/27',previous_completed_season='2025/26',date_shift_years=19,source_country_selection_and_new_career_accepted=True,source_SI_separate_confirmation=False,source_season_confirmation=False,SI=False,new_career=False,season=False,scope=dict(squads=True,loans=True,classic_leagues=True,new_clubs=True,stadiums=True,sugar_daddy_off=True,FCJurong_name_alias=True,engine=False,Thailand=False),output_database_created=False))
 (B/'WZNOWIENIE.md').write_text('# TEST_X10 — przygotowanie rozpoczęte, 11 listopada 2026\n\nSerbia, Rumunia, RPA, Rosja. Własny snapshot X8 i świeży audyt; X10 jeszcze nieutworzona. Klasyczny silnik, brak Tajlandii. Pełne statusy i piny: manifest.json. Nie ponawiać begin.\n',encoding='utf-8')
 print('FROZEN X8',len(hp),'files',flush=True)
def audit():
 m=read(B/'manifest.json');src=Path(m['source']);assert pins(src)==m['source_hashes']
 editor=R/'FOUR_COUNTRY_X7_20261110/tools-r2/FM08_Database_Editor.exe'
 assert hashlib.sha256(editor.read_bytes()).hexdigest()=='884ae78d9d9f72ed90de583f8d586c83984bbc43cb996b9219f42c1aa16f6b4e'
 it=R/'ITALY_DATABASE_2627_IMPORT_I1_20261108/tools-r1'
 jobs=[([it/'ApplyVerifiedNativeSquads.exe',editor,src,B/'audit','--audit'],B/'audit.log'),([R/'SWEDEN_SELECTION_REPAIR_X4_20261110/tools/ExportWholeNativeStructure.exe',src,editor,B/'native-structure.json'],B/'native-structure.log'),([it/'ExportNativeClubSnapshot.exe',src,editor,B/'club-snapshot.csv'],B/'snapshot.log')]
 def run(v):
  args,log=v
  z=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600);log.write_text(z.stdout+z.stderr,encoding='utf-8');assert z.returncode==0,(log,z.stderr[-600:])
 with ThreadPoolExecutor(max_workers=3)as ex:list(ex.map(run,jobs))
 assert pins(src)==m['source_hashes'];m.update(fresh_audit=True,editor=str(editor),editor_sha256=hashlib.sha256(editor.read_bytes()).hexdigest());dump(B/'manifest.json',m)
 print('AUDIT PASS',flush=True)
async def discover():
 cache=col.Cache()
 labels=[('ser-first','Serbian SuperLiga'),('ser-second','Prva liga Srbije'),('rom-first','SuperLiga Romania'),('rom-second','Liga 2'),('rom-third','Liga 3'),('rsa-first','Betway Premiership'),('rsa-second','Motsepe Foundation Championship'),('rus-first','Premier Liga'),('rus-second','First League Russia'),('rus-third','Second League Russia')]
 async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache)as tm:
  for label,q in labels:
   try:
    z=await col.get(tm,S/'tm-competitions'/('search-'+label+'.json'),'search_competitions',q)
    print(label,[(v.get('id'),v.get('name'),v.get('country'))for v in z.get('results',[])],flush=True)
   except Exception as e:print('DISCOVERY_ERROR',label,str(e),flush=True)
 dump(B/'discovery-capture.json',dict(network_calls=cache.calls,cache_hits=cache.hits))
async def catalogues():
 cache=col.Cache();comps=read(B/'source-competitions.json')
 async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache)as tm:
  jobs=[(c,y,k)for c in comps for y in ['2026','2025']for k in ['clubs','table']]
  async def one(c,y,k):
   try:
    z=await col.get(tm,S/'tm-competitions'/(c['id']+'-'+y+'-'+k+'.json'),'competition_'+k,c['id'],season_id=y)
    print(c['Country'],c['id'],y,k,len(z.get('clubs',[]))if k=='clubs'else[(t.get('name'),len(t.get('rows',[])))for t in z.get('tables',[])],flush=True)
   except Exception as e: print('CATALOGUE_ERROR',c['id'],y,k,str(e),flush=True)
  for i in range(0,len(jobs),3):await asyncio.gather(*(one(*v)for v in jobs[i:i+3]))
 dump(B/'catalogue-capture.json',dict(network_calls=cache.calls,cache_hits=cache.hits))

async def extras():
 cache=col.Cache()
 async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache)as tm:
  for label,q in [('rom-third-iii','Liga III'),('rom-country','Romania'),('rom-playoff','SuperLiga Playoff'),('ser-playoff','Super liga Srbije Champions'),('ser-releg','Super liga Srbije Relegation')]:
   z=await col.get(tm,S/'tm-competitions'/('search-'+label+'.json'),'search_competitions',q)
   print(label,'pages',z.get('last_page_number'),[(v.get('id'),v.get('name'),v.get('country'))for v in z.get('results',[])],flush=True)
 dump(B/'extra-discovery-capture.json',dict(network_calls=cache.calls,cache_hits=cache.hits))


async def extra2():
 cache=col.Cache()
 async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache)as tm:
  for label,q,page in [('rom-country-p2','Romania',2),('ser-country','Serbia',1),('ser-country-p2','Serbia',2)]:
   z=await col.get(tm,S/'tm-competitions'/('search-'+label+'.json'),'search_competitions',q,page_number=page)
   print(label,'pages',z.get('last_page_number'),[(v.get('id'),v.get('name'),v.get('country'))for v in z.get('results',[])],flush=True)
  for comp in ['RO1R','RO1C','R2AP','R2AO']:
   z=await col.get(tm,S/'tm-competitions'/(comp+'-2025-table.json'),'competition_table',comp,season_id='2025')
   print('FINALPHASE',comp,[(t.get('name'),len(t.get('rows',[])))for t in z.get('tables',[])],flush=True)
 dump(B/'extra2-capture.json',dict(network_calls=cache.calls,cache_hits=cache.hits))
def initial_targets():
 assert not (B/'source-targets.json').exists();out=[]
 for c in read(B/'source-competitions.json'):
  prev={v['club_id']:v for t in read(S/'tm-competitions'/(c['id']+'-2025-table.json'))['tables']for v in t['rows']}
  for v in read(S/'tm-competitions'/(c['id']+'-2026-clubs.json'))['clubs']:
   out.append(dict(Name=v['name'],TMID=v['id'],Country=c['Country'],LeagueCountry=c['Country'],NativeCountryIndex=COUNTRIES[c['Country']],RealLevel=c['level'],DesiredDivision=None,SourceCompetition=c['id'],RealSeason='2026/27',APISeason='2026',PreviousRank=prev.get(v['id']),SelectionReason='source_membership_initial_native_allocation_pending'))
 assert len({v['TMID']for v in out})==len(out)
 for c in out:
  if c['TMID']=='86094':c.update(RealLevel=3,SelectionReason='FRF20260717_excludes_Olimpia_from_Liga2_preserve_as_third_catalogue',OfficialMembershipEvidence='https://www.frf.ro/comunicari/comunicate-frf/hotararea-comitetului-de-urgenta-al-frf-din-17-iulie-2026/')
 dump(B/'source-targets.json',out)
 print('INITIAL SOURCE TARGETS',len(out),flush=True)
def world():
 import struct
 from batch_sweden_switzerland_x3_20261109 import load,languages,lang_sections,find_table,club,save
 from audit_poland_v25_common_r1_20261108 import Cursor
 m=read(B/'manifest.json');src=Path(m['source']);assert pins(src)==m['source_hashes']
 rr=read(B/'native-structure.json')['records'];en,_=lang_sections(dict(languages((src/'lang_db.dat').read_bytes()))[8]);a=load(src,'server_db.dat');cl,_,_=find_table(load(src,'client_db.dat'),[v['uid']for v in en['club']],club);cf={f['uid']:f for f in cl};nf={f['uid']:f['names']for f in en['club']};out=[]
 for r in rr:
  f=cf.get(r['ClubUID']);labels=nf.get(r['ClubUID'],[]);parent=None
  if not f:
   end=r['RosterOffset']+2+4*struct.unpack_from('<H',a,r['RosterOffset'])[0]
   for z in range(end,r['Footer']-7):
    if a[z:z+3]!=bytes([0,0,255]):continue
    fi=struct.unpack_from('<i',a,z+3)[0]
    if not(0<=fi<len(cl)):continue
    cur=Cursor(a,z+7)
    try:
     ns=[]
     for _ in range(2):ns.append(cur.string());cur.byte()
     assert cur.p==r['Footer']
    except(AssertionError,ValueError,UnicodeError,struct.error):continue
    f=cl[fi];parent=f['uid'];labels=labels+ns;break
  if not f:continue
  if parent is None:labels=labels+[f['embedded_full_name'],f['embedded_short_name']]
  out.append(dict(ClubUID=r['ClubUID'],TeamIndex=r['TeamIndex'],FamilyIndex=f['index'],ParentUID=parent,Country=f['country_index'],Names=list(dict.fromkeys(n for n in labels if n)),CurrentDivision=r['CurrentDivisionIndex'],YearFounded=f['year_founded_raw'],StadiumIndex=struct.unpack_from('<i',a,r['Start']+19)[0]))
 dump(B/'native-world-identities.json',out);dump(B/'competition-catalog.json',[dict(index=i,**v)for i,v in enumerate(en['comp'])])
 save(B/'world-club-identities.csv',[dict(ClubUID=v['ClubUID'],TeamIndex=v['TeamIndex'],FamilyIndex=v['FamilyIndex'],ParentUID=v['ParentUID']or'',CountryIndex=v['Country'],Names='|'.join(v['Names']),DivisionIndex=v['CurrentDivision'],StadiumIndex=v['StadiumIndex'])for v in out])
 print('WORLD',len(out),'records',flush=True)


async def finalphases():
 cache=col.Cache()
 async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache)as tm:
  for comp,kind in [('SR1C','table'),('SR1R','table'),('PVCR','table'),('PVRR','table'),('RO3F','clubs'),('RO3F','table')]:
   try:
    z=await col.get(tm,S/'tm-competitions'/(comp+'-2025-'+kind+'.json'),'competition_'+kind,comp,season_id='2025')
    print('FINAL',comp,kind,len(z.get('clubs',[]))if kind=='clubs'else[(t.get('name'),len(t.get('rows',[])))for t in z.get('tables',[])],flush=True)
   except Exception as e:print('PHASE_ERROR',comp,kind,str(e),flush=True)
 dump(B/'finalphases-capture.json',dict(network_calls=cache.calls,cache_hits=cache.hits))
def official():
 import httpx,re
 from datetime import datetime,timezone
 out=S/'official';out.mkdir(exist_ok=True)
 urls={
 'FRF-L3-final-2025-2026.pdf':'https://www.frf.ro/wp-content/uploads/2026/07/clasamente_fotbal_2025-2026-l3-Anexa-2.pdf',
 'FRF-L3-final-decision-2026.pdf':'https://www.frf.ro/wp-content/uploads/2026/07/informare-curg-omologari-iulie-2026-Anexa-1.pdf',
 'FRF-L2-participants-july21.html':'https://www.frf.ro/competitii/procedura-de-programare-a-jocurilor-din-campionatul-liga-2-casa-pariurilor-sezon-2026-2027/',
 'FRF-L3-participants-august20.html':'https://www.frf.ro/recomandate/joi-20-august-tragerea-la-sorti-pentru-programul-superscore-liga-3-editia-2026-2027/',
 'FRF-withdrawal-july31.html':'https://www.frf.ro/comunicari/comunicate-frf/hotararea-comitetului-de-urgenta-al-frf-din-31-iulie-2026/',
 'Hermannstadt-withdrawal-quoted-FRF.html':'https://liga2.prosport.ro/seria-1/frf-confirma-retragerea-echipei-fc-hermannstadt-din-liga-2-19394338'}
 ledger=[]
 with httpx.Client(timeout=35,follow_redirects=True)as client:
  for filename,url in urls.items():
   f=out/filename
   if not f.exists():
    z=client.get(url);f.write_bytes(z.content);status=z.status_code
    dump(out/(filename+'.capture.json'),dict(url=url,status=status,fetched_at=datetime.now(timezone.utc).isoformat(),sha256=hashlib.sha256(z.content).hexdigest()))
   else:status=read(out/(filename+'.capture.json'))['status']
   ledger.append(dict(file=filename,url=url,status=status,sha256=hashlib.sha256(f.read_bytes()).hexdigest()));print('OFFICIAL',filename,status,len(f.read_bytes()),flush=True)
 dump(out/'ledger.json',ledger)
 sys.path.insert(0,str(R/'WALES_USA_URUGUAY_2627_B1_20261109/tools-python'))
 from pypdf import PdfReader
 f=out/'FRF-L3-final-2025-2026.pdf'
 if read(out/(f.name+'.capture.json'))['status']==200:
  pages=[p.extract_text()for p in PdfReader(str(f)).pages];dump(out/'FRF-L3-final-pages.json',pages);print('PDF PAGES',len(pages),flush=True)
def identities_draft():
 from ss26prep_analyze_20261110 import key
 world=read(B/'native-world-identities.json');targets=read(B/'source-targets.json');out=[]
 for c in targets:
  pf=S/'tm-clubs'/(c['TMID']+'-profile.json')
  if not pf.exists():continue
  p=read(pf);labels=[c['Name'],p.get('name'),p.get('official_name'),p.get('short_name')]+[v.get('name')for v in p.get('historical_names',[])];keys={key(n)for n in labels if n};hits=[v for v in world if v['Country']==c['NativeCountryIndex']and any(key(n)in keys for n in v['Names'])]
  out.append(dict(c,IdentityDecision='reuse_exact_country_name_pending_continuity'if len(hits)==1 else'new_missing_native_or_alias_review'if not hits else'ambiguous_native_identity',NativeClubUID=hits[0]['ClubUID']if len(hits)==1 else None,NativeCandidates=hits,PublicStadium=p.get('stadium')or{},OfficialName=p.get('official_name'),SourceFounded=p.get('founded'),HistoricalNames=p.get('historical_names',[])))
 dump(B/'club-plan-draft.json',out)
 print('IDENTITIES',len(out),'reuse',sum(bool(x['NativeClubUID'])for x in out),flush=True)
 for x in out:
  print('IDENTITY',x['TMID'],x['Name'],x['IdentityDecision'],[(v['ClubUID'],v['Names'][:2])for v in x['NativeCandidates']],flush=True)


async def lower_discover():
 cache=col.Cache()
 queries=[('sporting','Sporting Liesti'),('moreni','Flacara Moreni'),('craiova2','Craiova II'),('zalau','Zalau'),('targu','Targu Secuiesc'),('sanatatea','Sanatatea Cluj'),('agricola','Agricola Borcea'),('cetatea','Turnu Magurele'),('onesti','Viitorul Onesti'),('zarnesti','Olimpic Zarnesti'),('minaur','Minaur Baia Mare'),('jiul','Jiul Petrosani')]
 async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache)as tm:
  for label,q in queries:
   z=await col.get(tm,S/'tm-clubs'/('search-lower-'+label+'.json'),'search_clubs',q)
   print('LOWER',label,[(v.get('id'),v.get('name'),v.get('country'),v.get('league'))for v in z.get('results',[])],flush=True)
 dump(B/'lower-discovery-capture.json',dict(network_calls=cache.calls,cache_hits=cache.hits))

if __name__=='__main__':
 command=sys.argv[1]
 if command=='begin':begin()
 elif command=='audit':audit()
 elif command=='discover':asyncio.run(discover())
 elif command=='catalogues':asyncio.run(catalogues())
 elif command=='extras':asyncio.run(extras())
 elif command=='extra2':asyncio.run(extra2())
 elif command=='initial_targets':initial_targets()
 elif command=='world':world()
 elif command=='rosters':asyncio.run(col.rosters())
 elif command=='finalphases':asyncio.run(finalphases())
 elif command=='official':official()
 elif command=='identities':identities_draft()
 elif command=='lower_discover':asyncio.run(lower_discover())
 else:raise ValueError(command)
