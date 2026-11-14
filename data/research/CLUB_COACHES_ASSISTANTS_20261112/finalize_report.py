from pathlib import Path
import csv,json,datetime,collections,re,hashlib,unicodedata
import collect_staff as b
B=b.B;ROOT=b.ROOT;NOW=datetime.datetime.now(datetime.timezone.utc).isoformat()
def key(r):return (r['ClubUID'],r.get('provisionalClubUID',''))
def num_date(t):
 for fmt in ['%d/%m/%Y','%d.%m.%Y','%Y-%m-%d']:
  try:return datetime.datetime.strptime(t,fmt).date().isoformat()
  except ValueError:pass
 return ''
def norm(t):return ''.join(x for x in unicodedata.normalize('NFKD',t.casefold()) if not unicodedata.combining(x)).replace('’',"'")
def main():
 scope=b.rows(B/'clubs-scope.csv');ident=b.read(B/'person-identities.json');report=[r for r in b.rows(B/'staff-report.csv') if r['source_role']!='90minut Trener refreshed'];pol=b.rows(B/'poland-coach-timelines.csv');pg=collections.defaultdict(list)
 for r in pol:pg[key(r)].append(r)
 for k,ls in pg.items():
  if len(ls)>1:
   dates=[r['source_effective_date'] for r in ls if r['source_effective_date'] and r['source_effective_date']<='2026-11-12'];latest=max(dates,default='');newest=[r for r in ls if latest and r['source_effective_date']==latest]
   for r in ls:r['status']='LATEST_APPOINTMENT_INFERRED_ENDDATES_MISSING' if len(newest)==1 and r in newest else 'TIMELINE_AMBIGUOUS_OR_SUPERSEDED_START_DATES_ONLY';r['selection_reason']='More than one named coach with start date but no explicit end date; newest dated appointment is candidate, not independently confirmed dismissal.'
  else:ls[0]['selection_reason']='Single named coach on current 90minut club page.'
  for r in ls:
   out=dict(r,source_role='90minut Trener refreshed',externalPersonID='',first_name='',last_name='',nativePersonUID_if_verified='',DOB_real='',DOB_precision='unknown',nationality='',identity_source_file='',identity_source_sha256='',source_updated_at='',source_excerpt=r['name']+' '+r['source_annotation'],native_import_ready='NO')
   report.append(out)
 for r in report:
  pid=r.get('externalPersonID','').replace('TM-coach:','');v=ident.get(pid)
  if v:
   r.update(DOB_real=v['DOB_real'],DOB_precision=v['DOB_precision'],identity_source_file=v['source_file'],identity_source_sha256=v['source_sha256']);r['identity_name']=v['name'];r['identity_name_match']='MATCH' if norm(r['name'])==norm(v['name']) else 'DIFFERENT_DISPLAY_NAME_REVIEW';r['identity_external_ID_verified']='YES';r['DOB_source_unknown_flag']=str(v['DOB_source_unknown_flag'])
  else:r['identity_external_ID_verified']='NO';r['identity_name_match']='UNKNOWN';r['identity_name']='';r['DOB_source_unknown_flag']=''
  r['source_effective_date_raw']=r.get('source_effective_date','');parsed=num_date(r['source_effective_date_raw']);r['source_effective_date_iso']=parsed;r['source_effective_date_precision']='day' if parsed else 'unknown';r['source_date_interpretation']='90minut Polish named month' if r['source_role'].startswith('90minut') else 'Transfermarkt page day/month/year; raw retained'
  r['employment_status']='interim' if r['source_role'] in ['Caretaker Manager','Interim Manager','Interim Coach','Caretaker Coach'] else 'current_at_source' if r['status'].startswith('CURRENT_') else 'source_candidate'
  r['temporal_caveat']='APPOINTMENT_AFTER_REQUESTED_SNAPSHOT' if parsed and parsed>'2026-11-12' else ''
  end=num_date(r.get('contract_expires_raw',''))
  if end and end<'2026-11-12':r['temporal_caveat']+=';CONTRACT_END_DISPLAY_PAST_MEMBERSHIP_REVALIDATION_REQUIRED'
  if r['source_role'] in ['Executive Assistant','Executive assistant of the director']:r['role']='out_of_scope_executive_assistant';r['status']='EXCLUDED_EXECUTIVE_ROLE'
  if r['source_role']=='Technical Assistant':r['status']='TECHNICAL_ASSISTANT_ROLE_REVIEW_REQUIRED'
 current=[];candidates=[];selectedkeys=set();primarypol={}
 for k,ls in pg.items():
  keep=[r for r in report if key(r)==k and r['source_role']=='90minut Trener refreshed' and (r['status'].startswith('CURRENT') or r['status']=='EXPLICIT_VACANCY_SOURCE')]
  if len(keep)==1:current.extend(keep);selectedkeys.add(k);primarypol[k]=keep[0]
  else:candidates.extend(r for r in report if key(r)==k and r['source_role']=='90minut Trener refreshed')
 for r in report:
  if 'staff-pages' in Path(r['source_file']).parts and r['role'] in ['head_coach','assistant_manager']:
   if r['temporal_caveat']:r['status']='SOURCE_CURRENT_TEMPORAL_CONFLICT_REVIEW';candidates.append(r)
   else:r['status']='CURRENT_STAFF_PAGE_ROLE_AND_EXTERNAL_ID_CONFIRMED';current.append(r)
 # Multiple listed head coaches are not automatically treated as a jointly confirmed staff.
 # The complete source rows survive; operational candidates require role/timeline reconciliation.
 grouped=collections.defaultdict(list)
 for r in current:
  if r['role']=='head_coach':grouped[key(r)].append(r)
 remove=set();dedup=[]
 for k,ls in grouped.items():
  ids={r.get('externalPersonID') or r['name'] for r in ls}
  if len(ids)>1:
   for r in ls:r['status']='MULTIPLE_HEAD_COACH_SOURCE_LISTINGS_REVIEW';candidates.append(r);remove.add(id(r))
  elif len(ls)>1:
   first=dict(ls[0]);first['source_effective_date_raw']=' | '.join(r['source_effective_date_raw'] for r in ls);first['source_effective_date_iso']='';first['source_effective_date_precision']='unknown';first['source_excerpt']=' | '.join(r['source_excerpt'] for r in ls);first['temporal_caveat']='SOURCE_DUPLICATE_PERSON_APPOINTMENT_DATES_CONFLICT';first['status']='CURRENT_PERSON_ROLE_DATE_CONFLICT_REVIEW';dedup.append(first)
   for r in ls:remove.add(id(r))
 current=[r for r in current if id(r) not in remove]+dedup
 # Preserve source history, keeping current operational selection in a separate table.
 fields=list(dict.fromkeys(k for r in report for k in r));b.write('staff-report.csv',report,fields);b.write('staff-current.csv',current,fields)
 if candidates:b.write('staff-candidates.csv',candidates,fields)
 b.write('poland-coach-timelines.csv',pol)
 by=collections.defaultdict(list)
 for r in current:by[key(r)].append(r)
 ledger=b.read(B/'staff-page-ledger.json');pages={(r['ClubUID'],r['provisionalClubUID']):r for r in ledger};polpages={r['ClubUID']:r for r in b.read(B/'poland-page-ledger.json')};coverage=[];gaps=[]
 for c in scope:
  k=key(c);rs=by[k];head=[r for r in rs if r['role']=='head_coach' and r['status']!='EXPLICIT_VACANCY_SOURCE'];assist=[r for r in rs if r['role']=='assistant_manager'];page=pages.get(k,{})
  state='CURRENT_ROLE_SOURCE_CONFIRMED' if head else 'EXPLICIT_VACANCY' if any(r['status']=='EXPLICIT_VACANCY_SOURCE' for r in rs) else 'TIMELINE_REVIEW' if k in pg else 'UNKNOWN'
  tc=[r for r in candidates if key(r)==k];cov=dict(c,head_coach_current_rows=len(head),head_coach_state=state,interim_head_coach_rows=sum(r['employment_status']=='interim' for r in head),assistant_current_rows=len(assist),assistant_state='SOURCE_ROLES_CAPTURED_COMPLETENESS_NOT_INDEPENDENTLY_VERIFIED' if assist else 'NONE_LISTED_ON_CAPTURE_NOT_PROVEN_VACANCY' if page.get('status')==200 else 'SOURCE_NOT_COLLECTED',temporal_or_timeline_candidate_rows=len(tc),staff_page_status=page.get('status','NOT_MAPPED'),head_source_latest_capture=max([r['source_fetched_at'] for r in head],default=''),native_import_ready='NO',TMID_type='Transfermarkt_numeric' if c['TMID'].isdigit() else 'non_Transfermarkt_source_key' if c['TMID'] else 'not_mapped');coverage.append(cov)
  def gap(role,status,detail):gaps.append(dict(ClubUID=c['ClubUID'],provisionalClubUID=c['provisionalClubUID'],TMID=c['TMID'],club=c['club'],country=c['country'],league=c['league'],accepted_or_pending=c['accepted_or_pending'],role=role,status=status,detail=detail))
  if not head:gap('head_coach',state,'See staff-report / staff-candidates; source missing, ambiguous timeline or temporal conflict is not vacancy.')
  if not assist:gap('assistant_manager',cov['assistant_state'],'No validated assistant role row collected. Never infer no assistants from a coach-only API or missing profile.')
  if not c['TMID']:gap('source_identity','CANONICAL_TMID_MISSING','Italy/Poland native maps did not establish a TMID. No name-only match or guessed new ID made.')
  elif not c['TMID'].isdigit():gap('source_identity','NON_TM_SOURCE_KEY','Historical map field is a provider-specific key, not a numeric Transfermarkt identity.')
  if page.get('status') not in [None,200]:gap('source_page','SOURCE_FETCH_ERROR',str(page.get('status'))+' '+page.get('error',''))
  for r in rs:
   if r['role'] in ['head_coach','assistant_manager'] and (not r['DOB_real'] or r.get('identity_name_match')=='DIFFERENT_DISPLAY_NAME_REVIEW'):gap(r['role'],'PERSON_IDENTITY_METADATA_GAP',r['name']+' '+r.get('externalPersonID','')+' DOB:'+r['DOB_precision']+' identity:'+r.get('identity_name_match',''))
 b.write('club-coverage.csv',coverage);b.write('gaps.csv',gaps)
 stats={}
 for status,label in [('accepted_X15_lineage','accepted'),('pending_X16_NOT_ACCEPTED','pending')]:
  cc=[c for c in coverage if c['accepted_or_pending']==status];rr=[r for r in current if r['accepted_or_pending']==status];cand=[r for r in candidates if r['accepted_or_pending']==status]
  stats[label]=dict(clubs=len(cc),countries=len({c['country'] for c in cc}),head_coach_clubs=sum(c['head_coach_current_rows']>0 for c in cc),head_coach_rows=sum(r['role']=='head_coach' for r in rr),assistant_clubs=sum(c['assistant_current_rows']>0 for c in cc),assistant_rows=sum(r['role']=='assistant_manager' for r in rr),head_coach_missing_or_review=sum(c['head_coach_current_rows']==0 for c in cc),assistant_missing_or_not_listed=sum(c['assistant_current_rows']==0 for c in cc),DOB_complete=sum(bool(r['DOB_real']) for r in rr),unique_external_person_ids=len({r['externalPersonID'] for r in rr if r['externalPersonID']}),timeline_or_temporal_candidates=len(cand),interim_head_coach_rows=sum(r['employment_status']=='interim' for r in rr))
 country=[]
 for state in ['accepted_X15_lineage','pending_X16_NOT_ACCEPTED']:
  for name in sorted({c['country'] for c in coverage if c['accepted_or_pending']==state}):
   cs=[c for c in coverage if c['country']==name and c['accepted_or_pending']==state];country.append(dict(country=name,status=state,clubs=len(cs),head_coach_clubs=sum(c['head_coach_current_rows']>0 for c in cs),assistant_clubs=sum(c['assistant_current_rows']>0 for c in cs),assistant_rows=sum(c['assistant_current_rows'] for c in cs),no_TMID=sum(not c['TMID'] for c in cs)))
 b.write('country-coverage.csv',country)
 result=dict(status='SOURCE_REPORT_FIRST_PASS_PARTIAL_NOT_NATIVE_IMPORT_READY',snapshot='2026-11-12',checked_at=NOW,coverage=stats,source_report_rows=len(report),current_rows=len(current),candidate_rows=len(candidates),TM_staff_pages=len(ledger),TM_staff_pages_200=sum(r.get('status')==200 for r in ledger),poland_pages=len(polpages),poland_pages_200=sum(r.get('status')==200 for r in polpages.values()),poland_timeline_rows=len(pol),poland_ambiguous_clubs=sum(len(x)>1 for x in pg.values()),person_identities=b.read(B/'identity-capture.json'),api_football_calls=0,native_UID_assigned=0,raw_dates_shifted=False,DB_modified=False,EXE_modified=False,active_game_accessed=False,known_TMID_gaps=dict(Italy=132,Poland=126),source_role_method='All Assistant Manager/Assistant Coach rows retained; Technical Assistant deferred; executive assistants and specialist coaches excluded.',native_staff_evidence=dict(past_wage_pilot_only=True,general_staff_importer_ready=False))
 b.dump('summary.json',result)
 # Invariants and representative independent readback from raw page content.
 checks=[]
 def check(name,test):checks.append(dict(name=name,passed=bool(test)))
 check('accepted_scope1465',sum(c['ClubUID']!='' for c in scope)==1465);check('pending181_no_accepted_UID',sum(c['ClubUID']=='' and c['provisionalClubUID']!='' for c in scope)==181);check('native_UIDs_empty',all(not r['nativePersonUID_if_verified'] for r in report));check('all_current_have_source_pin',all(r['source_file'] and r['source_sha256'] for r in current));check('known_DOB_ISO',all(not r['DOB_real'] or re.fullmatch(r'\d{4}-\d{2}-\d{2}',r['DOB_real']) for r in report));check('assistants_not_specialists',all(r['source_role'] in ['Assistant Manager','Assistant coach','Assistant Coach','Co-Trainer'] for r in current if r['role']=='assistant_manager'));check('unique_current_role_rows',len(current)==len({(key(r),r['role'],r['externalPersonID'],r['name']) for r in current}));check('no_future_current',all(not r['source_effective_date_iso'] or r['source_effective_date_iso']<='2026-11-12' for r in current));check('Bayern4assistants_all_retained',len([r for r in current if r['ClubUID']=='915' and r['role']=='assistant_manager'])==4);check('no_Coach_first_last_guesses',all(not r.get('first_name') and not r.get('last_name') for r in report))
 sourcepins={r['source_file']:r['source_sha256'] for r in report if r.get('source_file')};sourcepins.update({v['source_file']:v['source_sha256'] for v in ident.values()})
 check('all_external_pins_readback',all((ROOT/p).is_file() and b.sha(ROOT/p)==h for p,h in sourcepins.items()));b.dump('all-evidence-pins.json',sourcepins)
 b.dump('verification.json',dict(passed=all(c['passed'] for c in checks),checks=checks,notes='Source coverage/invariants and hashes. No native import or game acceptance test.'))
 if not all(c['passed'] for c in checks):raise AssertionError(checks)
 print(json.dumps(result,ensure_ascii=False),flush=True)
if __name__=='__main__':main()

