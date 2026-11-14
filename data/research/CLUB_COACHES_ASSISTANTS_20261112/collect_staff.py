from pathlib import Path
import sys,json,csv,re,hashlib,html,collections,datetime
sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'J:\FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent
NOW=datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p,sep=','):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline=''),delimiter=sep))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,v):(B/name).write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
def write(name,rs,fields=None):
 with (B/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rs[0]),extrasaction='ignore');w.writeheader();w.writerows(rs)
def clean(v):return html.unescape(re.sub('<[^>]+>',' ',v)).strip()

def scope():
 pins={};maps={};conflicts=[]
 def pin(p):pins[str(p.relative_to(ROOT))]=sha(p)
 # Only lineage maps named by canonical coverage manifests are authoritative for accepted X14.
 manifests=[R/'DATABASE_UPDATE_COVERAGE_20261111/manifest.json',R/'DATABASE_UPDATE_COVERAGE_X14_20261111/manifest.json']
 for m in manifests:
  pin(m)
  for fn in read(m)['sources']:
   p=ROOT/fn
   if p.name!='club_map.csv':continue
   pin(p)
   for x in rows(p):maps[x['ClubUID']]=dict(x,scope_map=str(p.relative_to(ROOT)))
 x15=R/'COUNTRY_BATCH_GER_MEX_MAS_20261112'
 for p in [x15/'prepared/club_map.csv',x15/'final-native-player-UID-ledger.csv',x15/'publication.json',x15/'TEST_X15_TEST_STATUS_20261112.json']:pin(p)
 for x in rows(x15/'prepared/club_map.csv'):maps[x['ClubUID']]=dict(x,scope_map=str((x15/'prepared/club_map.csv').relative_to(ROOT)))
 p=R/'DATABASE_UPDATE_COVERAGE_X14_20261111/kluby.csv';pin(p)
 graphics=R/'GRAPHICS_COVERAGE_X14_20261112/kluby.csv';pin(graphics)
 leagues={x['uid']:x['liga'] for x in rows(graphics,';')}
 clubs={x['club_uid']:dict(ClubUID=x['club_uid'],club=x['club'],country=x['country'],league=leagues.get(x['club_uid'],''),accepted_or_pending='accepted_X15_lineage',scope_origin='X14_lineage',division_index=x['division_index']) for x in rows(p)}
 for x in rows(x15/'prepared/club_map.csv'):
  clubs[x['ClubUID']]=dict(ClubUID=x['ClubUID'],club=x['ClubName'],country=x['Country'],league=x['RealLeague'],accepted_or_pending='accepted_X15_lineage',scope_origin='X15',division_index=x['DivisionIndex'])
 for uid,c in clubs.items():
  m=maps.get(uid,{})
  c.update(TMID=m.get('TMID',''),ClubID90=m.get('ClubID90',''),kind=m.get('Kind',''),parent_uid=m.get('ParentUID',''),scope_map=m.get('scope_map',''),provisionalClubUID='')
 p=R/'COUNTRY_BATCH_KOR_COL_ISR_20261112/six-country-stage/prepared/club_map.csv';pin(p)
 pending=[]
 for x in rows(p):pending.append(dict(ClubUID='',provisionalClubUID=x['ClubUID'],club=x['ClubName'],country=x['Country'],league=x['RealLeague'],accepted_or_pending='pending_X16_NOT_ACCEPTED',scope_origin='X16_staging',division_index=x['DivisionIndex'],TMID=x['TMID'],ClubID90='',kind=x['Kind'],parent_uid=x.get('ParentUID',''),scope_map=str(p.relative_to(ROOT))))
 assert len(clubs)==1465 and len(pending)==181
 write('clubs-scope.csv',list(clubs.values())+pending)
 dump('scope-input-pins.json',pins)
 return list(clubs.values())+pending

def offline():
 clubs=scope();staff=[];coverage=[];gaps=[];used={};profile_index=collections.defaultdict(list)
 for p in R.glob('*/sources/tm-clubs/*profile.json'):
  tid=p.name.split('-')[0]
  try:
   v=read(p)
   if str(v.get('id',''))==tid:profile_index[tid].append((str(v.get('updated_at','')),p,v))
  except Exception:pass
 rawdirs=list(R.glob('*/sources/tm-raw'));print('profiles',len(profile_index),'rawdirs',len(rawdirs),flush=True)
 def rawurl(url):
  key=hashlib.sha256(('GET '+url).encode()).hexdigest()+'.json'
  hits=[d/key for d in rawdirs if (d/key).is_file()]
  if not hits:return None,None
  p=max(hits,key=lambda p:p.stat().st_mtime)
  try:return p,read(p)
  except Exception:return None,None
 def base(c):return {k:c.get(k,'') for k in ['ClubUID','provisionalClubUID','TMID','club','country','league','accepted_or_pending']}
 def record(c):return dict(base(c),role='head_coach',source_role='',name='',first_name='',last_name='',externalPersonID='',nativePersonUID_if_verified='',DOB_real='',DOB_precision='unknown',nationality='',sourceURL='',source_effective_date='',source_season='',source_fetched_at='',source_updated_at='',checked_at=NOW,status='',source_file='',source_sha256='',identity_source_file='',identity_source_sha256='',source_excerpt='',native_import_ready='NO')
 polfolders=list((R/'POLAND_DATABASE_2627_R1_20261108/sources').glob('90minut-*'))
 for c in clubs:
  rr=None;ps=profile_index.get(c['TMID'],[])
  if ps:
   _,p,v=max(ps,key=lambda x:x[0]);coach=v.get('coach')
   if coach:
    rr=record(c);rr.update(name=coach.get('name',''),externalPersonID='TM-coach:'+str(coach.get('id','')),source_role='club_profile.coach',sourceURL='https://www.transfermarkt.com'+v.get('url','') if v.get('url','').startswith('/') else v.get('url',''),source_effective_date=coach.get('since','') or '',source_updated_at=v.get('updated_at',''),source_file=str(p.relative_to(ROOT)),source_sha256=sha(p),source_excerpt=json.dumps(coach,ensure_ascii=False),status='HEAD_COACH_SOURCE_CAPTURE_REQUIRES_12XI_REVALIDATION')
    used[str(p.relative_to(ROOT))]=sha(p)
    # Exact coach ID only: reuse raw person metadata already requested while collecting clubs.
    cp,raw=rawurl('https://tmapi.transfermarkt.technology/coaches?ids%5B%5D='+str(coach.get('id','')))
    if raw:
     body=json.loads(raw['body']);body=body.get('data',body) if isinstance(body,dict) else body;entities=body if isinstance(body,list) else [body]
     matches=[e for e in entities if isinstance(e,dict) and str(e.get('id',''))==str(coach.get('id',''))]
     if len(matches)==1:
      e=matches[0];rr.update(identity_source_file=str(cp.relative_to(ROOT)),identity_source_sha256=sha(cp));used[str(cp.relative_to(ROOT))]=sha(cp)
      rr['source_fetched_at']=raw.get('fetched_at','')
      life=e.get('lifeDates') or {};rr['DOB_real']=life.get('dateOfBirth','') or life.get('birthDate','') or '';rr['DOB_precision']='day' if re.fullmatch(r'\d{4}-\d{2}-\d{2}.*',str(rr['DOB_real'])) else 'unknown'
      rr['nationality']=json.dumps(e.get('nationalityDetails') or {},ensure_ascii=False)
   else:gaps.append(dict(base(c),role='head_coach',status='NO_HEAD_COACH_IN_PROFILE_NOT_PROVEN_VACANCY',detail=str(p.relative_to(ROOT))))
  # 90minut has precedence. Old multiple Trener entries are preserved as historical candidates, never chosen by list order.
  if c['ClubID90']:
   pp=[d/('club-'+c['ClubID90']+'.html') for d in polfolders if (d/('club-'+c['ClubID90']+'.html')).exists()]
   if pp:
    p=max(pp,key=lambda p:p.stat().st_mtime);raw=p.read_bytes().decode('iso-8859-2',errors='replace')
    m=re.search(r'<tr[^>]*>\s*<td[^>]*>\s*Trener:\s*(.*?)</td>\s*</tr>',raw,re.I|re.S)
    if m:
     text=clean(m[1]);text=re.sub(r'\s+',' ',text);rr=record(c);rr.update(name=text,source_role='90minut Trener',sourceURL='http://www.90minut.pl/skarb.php?id_klub='+c['ClubID90'],source_season='2026/27' if '2026/27' in raw else '',source_file=str(p.relative_to(ROOT)),source_sha256=sha(p),source_excerpt=text,status='90MINUT_HEAD_COACH_UNPARSED_TIMELINE_REQUIRES_REVALIDATION');used[str(p.relative_to(ROOT))]=sha(p)
     names=re.findall(r'<b[^>]*>(.*?)</b>',m[1],re.I|re.S);names=[clean(n) for n in names if clean(n)]
     if len(names)==1:
      rr['name']=re.sub(r'\s+[A-Z]{3}(?:/[A-Z]{3})*\s*$','',names[0]).strip();rr['status']='90MINUT_HEAD_COACH_SOURCE_CAPTURE_REQUIRES_12XI_REVALIDATION'
  if rr:staff.append(rr)
  else:gaps.append(dict(base(c),role='head_coach',status='SOURCE_NOT_YET_RESOLVED',detail='No usable cached current club coach evidence mapped by exact identity.'))
  gaps.append(dict(base(c),role='assistant_manager',status='ASSISTANTS_NOT_YET_COLLECTED',detail='SDK provides head coach only; absence is unknown, not vacancy. All assistants require staff-page role evidence.'))
  coverage.append(dict(base(c),head_coach_evidence=int(rr is not None),assistant_evidence=0,coach_status=rr['status'] if rr else 'UNKNOWN',staff_page_url='https://www.transfermarkt.com/club/mitarbeiter/verein/'+c['TMID'] if c['TMID'] else '',needs_current_snapshot_revalidation=1))
 write('staff-report.csv',staff);write('gaps.csv',gaps);write('club-coverage.csv',coverage);dump('evidence-input-pins.json',used)
 stats=dict(snapshot_requested='2026-11-12',checked_at=NOW,accepted_clubs=1465,pending_clubs=181,accepted_mapped_TMID=sum(bool(c['TMID']) for c in clubs if c['accepted_or_pending']=='accepted_X15_lineage'),accepted_mapped_90minut=sum(bool(c['ClubID90']) for c in clubs if c['accepted_or_pending']=='accepted_X15_lineage'),head_coach_rows=len(staff),head_coach_accepted=sum(r['accepted_or_pending']=='accepted_X15_lineage' for r in staff),head_coach_pending=sum(r['accepted_or_pending']!='accepted_X15_lineage' for r in staff),assistant_rows=0,native_person_uids_assigned=0,api_football_calls=0,new_network_calls=0,complete=False,status='INCREMENTAL_SOURCE_REPORT_NOT_IMPORT_READY',DOB_complete=sum(bool(r['DOB_real']) for r in staff))
 dump('summary.json',stats);print(json.dumps(stats),flush=True)
if __name__=='__main__':offline()

