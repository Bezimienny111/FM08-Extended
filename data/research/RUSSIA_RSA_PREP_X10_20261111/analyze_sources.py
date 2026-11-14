import json,collections,hashlib
from pathlib import Path
B=Path.cwd()/'FmLauncher/data/research/RUSSIA_RSA_PREP_X10_20261111';S=B/'sources'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
targets=read(B/'source-targets.json')
assert len(targets)==70 and all('RosterFile'in c and 'ProfileFile'in c for c in targets)
for c in targets:c.pop('FetchError',None)
dump(B/'source-targets.json',targets)
players={};hist={};clubs={};rawfiles=[]
for p in (S/'tm-raw').glob('*.json'):
 x=read(p);url=x['url'];rawfiles.append(dict(path=str(p.relative_to(B)),status=x['status'],body_sha256=x['sha256'],url=url))
 if x['status']!=200:continue
 body=json.loads(x['body']);d=body.get('data')
 if '/transfer/history/player/'in url:
  pid=url.rsplit('/',1)[-1].split('?')[0]
  if pid not in hist or x['fetched_at']>hist[pid]['fetched_at']:hist[pid]=dict(data=d,raw_file=str(p.relative_to(B)),fetched_at=x['fetched_at'])
 elif '/players?'in url and isinstance(d,list):
  for v in d:
   pid=str(v['id'])
   if pid not in players or x['fetched_at']>players[pid]['fetched_at']:players[pid]=dict(data=v,raw_file=str(p.relative_to(B)),fetched_at=x['fetched_at'])
 elif '/clubs?'in url and isinstance(d,list):
  for v in d:clubs[str(v['id'])]=v
facts=[];loans=[];gaps=[];coverage=[];owners={};cutoff='2026-11-11';clubplans=[]
for c in targets:
 pf=read(B/c['ProfileFile'])
 clubplans.append(dict(c,PublicStadium=pf.get('stadium')or{},SourceOfficialName=pf.get('official_name'),SourceHistoricalNames=pf.get('historical_names',[]),SourceShortName=pf.get('short_name'),SourceStadiumURL='https://www.transfermarkt.com'+pf.get('url',''),NativeClubUID=None,NativeIdentityStatus='not_resolved_here_delegated_to_batch_integrator'))
 confirmed=0;gk=0;pl=read(B/c['RosterFile'])['players']
 for v in pl:
  pid=str(v['id']);pr=players.get(pid,{}).get('data',{})
  hx=hist.get(pid);history=(hx or{}).get('data')or{}
  terminated=((history.get('history')or{}).get('terminated')or[])
  eligible=[t for t in terminated if not(t.get('details')or{}).get('isPending') and bool((t.get('details')or{}).get('date')) and ((t.get('details')or{}).get('date')or'')[:10]<=cutoff]
  latest=max(eligible,key=lambda t:(t.get('details')or{}).get('date')or'',default=None)
  assign=[t for t in pr.get('clubAssignments',[]) if t.get('type')in['current','additional']]
  assignment=next((t for t in assign if str(t.get('clubId'))==c['TMID']),None)
  status=(('current_assignment_confirmed'if assignment.get('type')=='current'else'additional_assignment_confirmed')if assignment else'current_assignment_unresolved')
  arrival=latest if latest and str((latest.get('transferDestination')or{}).get('clubId'))==c['TMID']else None
  if latest and not arrival and not assignment:status='stale_membership_rejected'
  role=v.get('position')or(pr.get('attributes')or{}).get('positionGroupName')
  roleprecision='main'if v.get('position')else'group'if role else'unknown'
  req=bool(v.get('date_of_birth')and v.get('nationality')and role)
  accepted=req and status in['current_assignment_confirmed','additional_assignment_confirmed'] and hx is not None
  isloan=bool(arrival and(arrival.get('typeDetails')or{}).get('type')=='ACTIVE_LOAN_TRANSFER')
  owner=str((arrival.get('transferSource')or{}).get('clubId'))if isloan else c['TMID']
  pending=((history.get('history')or{}).get('pending')or[])
  end=next((((t.get('details')or{}).get('date')or'')[:10]for t in pending if str((t.get('transferSource')or{}).get('clubId'))==c['TMID']and str((t.get('transferDestination')or{}).get('clubId'))==owner and(t.get('typeDetails')or{}).get('type')in['RETURNED_FROM_PREVIOUS_LOAN','END_OF_LOAN']),None)
  row=dict(TMID=pid,Name=v.get('name'),RealDOB=v.get('date_of_birth'),Nationality=v.get('nationality'),Role=role,RolePrecision=roleprecision,ClubTMID=c['TMID'],ClubName=c['Name'],Country=c['Country'],MembershipStatus=status,RequiredFactsAvailable=req,AcceptedFactCandidate=accepted,Loan=isloan,LoanEvidenceStatus='raw_history_present'if hx else'raw_history_unavailable_defer',OwnerTMID=owner if hx else None,RealLoanStart=((arrival.get('details')or{}).get('date')or'')[:10]if isloan else None,RealLoanEnd=end,BuyOptionFee=None,MandatoryBuy=False,Contract=v.get('contract'),LatestCompletedTransfer=latest,PlayerRaw=players.get(pid,{}).get('raw_file'),HistoryRaw=(hx or{}).get('raw_file'),SourceRosterURL='https://www.transfermarkt.com/-/kader/verein/'+c['TMID']+'/saison_id/2026',SourceBioURL='https://www.transfermarkt.com/-/profil/spieler/'+pid,SourceSnapshotDate=cutoff)
  facts.append(row)
  confirmed+=accepted;gk+=accepted and role=='Goalkeeper'
  if isloan:
   loans.append(row);od=clubs.get(owner,{})
   owners.setdefault(owner,dict(TMID=owner,Name=od.get('name'),SourceCountryId=od.get('countryId'),WithinBatch=owner in{cc['TMID']for cc in targets},PriorNativeMappings=[]))
  reasons=[]
  if not req:reasons.append('missing_required_bio_or_position')
  if status not in['current_assignment_confirmed','additional_assignment_confirmed']:reasons.append(status)
  if not hx:reasons.append('loan_history_unavailable_ownership_not_assumed')
  if reasons:gaps.append(dict(TMID=pid,Name=v.get('name'),club=c['Name'],ClubTMID=c['TMID'],reason=';'.join(reasons),RequiredFactsAvailable=req,MembershipStatus=status))
 coverage.append(dict(Club=c['Name'],TMID=c['TMID'],Country=c['Country'],Cards=len(pl),ConfirmedCandidates=confirmed,Goalkeepers=gk,CurrentAssignments=sum(x['ClubTMID']==c['TMID']and x['MembershipStatus']in['current_assignment_confirmed','additional_assignment_confirmed']for x in facts)))
 if not pl:gaps.append(dict(TMID=None,Name=None,club=c['Name'],ClubTMID=c['TMID'],reason='empty_source_squad; no_forced_fill',RequiredFactsAvailable=False,MembershipStatus='no_source_cards'))
for name,data in [('roster-facts.json',facts),('loan-facts.json',loans),('loan-owner-catalogue.json',list(owners.values())),('coverage.json',coverage),('source-gaps.json',gaps),('club-plan-source.json',clubplans),('source-response-index.json',rawfiles)]:dump(B/name,data)
summary=dict(status='source_preparation_complete_no_DB_write',clubs=len(targets),countries=dict(collections.Counter(c['Country']for c in targets)),classic_counts=dict(collections.Counter(c['DesiredDivision']for c in targets)),roster_cards=len(facts),unique_player_ids=len({x['TMID']for x in facts}),confirmed_candidates=sum(x['AcceptedFactCandidate']for x in facts),unique_confirmed_candidates=len({x['TMID']for x in facts if x['AcceptedFactCandidate']}),loans=len(loans),confirmed_loans=sum(x['AcceptedFactCandidate']for x in loans),loan_owners=len(owners),gaps=len(gaps),raw_history_records=len(hist),raw_player_records=len(players),raw_responses=len(rawfiles),raw_errors=dict(collections.Counter(x['status']for x in rawfiles if x['status']!=200)),short_or_no_GK=[x for x in coverage if x['ConfirmedCandidates']<17 or not x['Goalkeepers']],country_cards=dict(collections.Counter(x['Country']for x in facts)),country_confirmed=dict(collections.Counter(x['Country']for x in facts if x['AcceptedFactCandidate'])),date_shift_applied=False,all_database_files_untouched=True,missing_players_not_forcibly_sourced=True)
dump(B/'preparation-report.json',summary)
manifest=read(B/'manifest.json');manifest.update(summary)
manifest['loan_history_missing_deferred']=True
manifest['source_preparation_only']=True
manifest['native_acceptance']=False;manifest['SI_acceptance']=False;manifest['new_career_acceptance']=False
manifest['files']={str(p.relative_to(B)):hashlib.sha256(p.read_bytes()).hexdigest()for p in B.iterdir()if p.is_file()and p.name!='manifest.json'}
dump(B/'manifest.json',manifest)
print(json.dumps(summary,ensure_ascii=True))
