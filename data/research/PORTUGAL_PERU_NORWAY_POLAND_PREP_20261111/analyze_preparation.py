"""Source preparation only. Does not parse or write native player/database bytes."""
from pathlib import Path
import json,csv,hashlib,re,unicodedata,collections,sys
sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;R=B.parent;ROOT=R.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(name,x):(B/name).write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def csvout(name,rs):
 if not rs:return
 with (B/name).open('w',newline='',encoding='utf-8-sig')as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def key(s):
 s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower()
 return ' '.join(sorted(w for w in re.findall('[a-z0-9]+',s)if w not in {'fc','fk','sk','cf','sc','cd','gd','ud','sl','ac','bk','if','il','sad','club','clube','futebol','fotball','de','do','da','d'}))
targets=read(B/'source-targets.json');comps=read(B/'source-competitions.json')
rawplayers={};hist={};rawclubs={};rawlist=[]
for p in (B/'sources/tm-raw').glob('*.json'):
 x=read(p);u=x['url'];body=json.loads(x['body']);d=body.get('data');ref=dict(url=u,raw_file=str(p.relative_to(B)),body_sha256=x['sha256'],file_sha256=sha(p),fetched_at=x['fetched_at']);rawlist.append(ref)
 if '/transfer/history/player/'in u:hist[u.split('/')[-1].split('?')[0]]=dict(data=d,ref=ref)
 elif '/players?'in u and isinstance(d,list):
  for v in d:
   pid=str(v['id'])
   if pid not in rawplayers or x['fetched_at']>rawplayers[pid]['ref']['fetched_at']:rawplayers[pid]=dict(data=v,ref=ref)
 elif '/clubs?'in u and isinstance(d,list):
  for v in d:rawclubs[str(v['id'])]=v
dump('raw-source-index.json',rawlist)
facts=[];loans=[];gaps=[];coverage=[];stadiums=[];owners={};cutoff='2026-11-11'
for c in targets:
 pf=read(B/c['ProfileFile'])if c.get('ProfileFile')else{}
 stadiums.append(dict(Country=c['Country'],ClubTMID=c['TMID'],Club=c['Name'],OfficialName=pf.get('official_name'),ProfileFile=c.get('ProfileFile'),ProfileURL='https://www.transfermarkt.com'+pf.get('url',''),Stadium=pf.get('stadium')or{},CapacityInterpretation='source capacity; not inferred seated capacity',StadiumName=pf.get('stadium_name'),ProfileSeatField=pf.get('stadium_seats')))
 rs=read(B/c['RosterFile']).get('players',[])if c.get('RosterFile')else[];ok=gk=0;cc=collections.Counter()
 for v in rs:
  pid=v['id'];pr=rawplayers.get(pid,{}).get('data',{});h=hist.get(pid,{}).get('data')or{};history=h.get('history')or{}
  eligible=[t for t in history.get('terminated',[])if not(t.get('details')or{}).get('isPending')and (t.get('details')or{}).get('date')and(t['details']['date'][:10]<=cutoff)]
  latest=max(eligible,key=lambda t:t['details']['date'],default=None)
  assignment=next((a for a in pr.get('clubAssignments',[])if a.get('type')in['current','additional']and str(a.get('clubId'))==c['TMID']),None)
  status=(assignment['type']+'_assignment_confirmed')if assignment else'current_assignment_unresolved'
  arrival=latest if latest and str((latest.get('transferDestination')or{}).get('clubId'))==c['TMID']else None
  if latest and not arrival and not assignment:status='stale_membership_rejected'
  role=v.get('position')or(pr.get('attributes')or{}).get('positionGroupName');required=bool(v.get('date_of_birth')and v.get('nationality')and role);accepted=bool(required and assignment)
  loan=bool(arrival and (arrival.get('typeDetails')or{}).get('type')=='ACTIVE_LOAN_TRANSFER')
  owner=str((arrival.get('transferSource')or{}).get('clubId'))if loan else c['TMID']
  end=next(((t.get('details')or{}).get('date','')[:10]for t in history.get('pending',[])if str((t.get('transferSource')or{}).get('clubId'))==c['TMID']and str((t.get('transferDestination')or{}).get('clubId'))==owner and(t.get('typeDetails')or{}).get('type')in['RETURNED_FROM_PREVIOUS_LOAN','END_OF_LOAN']),None)
  row=dict(TMID=pid,Name=v.get('name'),RealDOB=v.get('date_of_birth'),Nationality=v.get('nationality'),Role=role,Country=c['Country'],ClubTMID=c['TMID'],ClubName=c['Name'],MembershipStatus=status,AcceptedFactCandidate=accepted,NativeDOBNotCalculated=True,CA_PA_NotGenerated=True,Loan=loan,OwnerTMID=owner,OwnerSourceCountryId=(arrival.get('transferSource')or{}).get('countryId')if loan else None,RealLoanStart=arrival['details']['date'][:10]if loan else None,RealLoanEnd=end,BuyOptionFee=None,BuyOptionEvidence=None,MandatoryBuy=False,Contract=v.get('contract'),LatestCompletedTransfer=latest,PlayerRaw=rawplayers.get(pid,{}).get('ref'),HistoryRaw=hist.get(pid,{}).get('ref'))
  facts.append(row);ok+=accepted;gk+=accepted and role=='Goalkeeper';cc[status]+=1
  if loan:
   loans.append(row);od=rawclubs.get(owner,{})
   owners[owner]=dict(TMID=owner,Name=od.get('name'),SourceCountryId=(od.get('baseDetails')or{}).get('countryId'),WithinSourceCatalogue=any(t['TMID']==owner for t in targets),NativeUID=None,NativeIdentityResolutionPending=True)
  if not accepted:gaps.append(dict(ClubTMID=c['TMID'],Club=c['Name'],PlayerTMID=pid,Name=v.get('name'),Reason='missing_required_fact_or_current_assignment',RequiredFactsAvailable=required,MembershipStatus=status))
 coverage.append(dict(Country=c['Country'],ClubTMID=c['TMID'],Club=c['Name'],RealLevel=c['RealLevel'],SourceSeason=c['RealSeason'],ProviderSeasonID=c['APISeason'],Cards=len(rs),ConfirmedCandidates=ok,Goalkeepers=gk,MembershipStatuses=dict(cc),FetchError=c.get('FetchError')))
dump('roster-facts.json',facts);dump('loan-facts.json',loans);dump('loan-owner-catalogue.json',list(owners.values()));dump('roster-source-gaps.json',gaps);dump('stadium-catalogue.json',stadiums);dump('coverage.json',coverage)
csvout('coverage-by-club.csv',[dict(x,MembershipStatuses=json.dumps(x['MembershipStatuses']))for x in coverage])
worldfile=R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/world-club-identities.csv'
world=list(csv.DictReader(worldfile.open(encoding='utf-8-sig',newline='')))
country_indices={'Portugal':162,'Norway':160,'Peru':194}
anchors={'Portugal':[1487,1489],'Norway':[1376],'Peru':[1450,117754]}
identity=[]
for c in targets:
 pf=read(B/c['ProfileFile'])if c.get('ProfileFile')else{};names=[c['Name'],pf.get('name'),pf.get('official_name'),pf.get('short_name')]+[n.get('name')for n in pf.get('historical_names',[])]
 keys={key(n)for n in names if n}
 candidates=[dict(ClubUID=int(w['ClubUID']),TeamIndex=int(w['TeamIndex']),FamilyIndex=int(w['FamilyIndex']),ParentUID=int(w['ParentUID'])if w['ParentUID']else None,CountryIndex=int(w['CountryIndex']),Names=w['Names'].split('|'),DivisionIndex=int(w['DivisionIndex']))for w in world if int(w['CountryIndex'])in[country_indices[c['Country']],-1]and any(key(n)in keys for n in w['Names'].split('|'))]
 parentchild=any(re.search(r'(?:\bB\b|\bII\b|\b2\b|U23)',n)for n in names if n)
 phoenix= c['Country']=='Portugal'and any(t in str(pf.get('official_name')or c['Name']).lower()for t in ['estrela','avs','aves','felgueiras'])
 decision='continuity_review_required'if phoenix else'unique_source_alias_candidate'if len(candidates)==1 else'not_safely_matched_yet'if not candidates else'ambiguous_native_candidates'
 identity.append(dict(Country=c['Country'],TMID=c['TMID'],Name=c['Name'],SourceOfficialName=pf.get('official_name'),RealLevel=c['RealLevel'],Competitions=c['Competitions'],SourceMainClubTMID=(rawclubs.get(c['TMID'],{}).get('baseDetails')or{}).get('mainClubId'),SourceClubTypeID=(rawclubs.get(c['TMID'],{}).get('baseDetails')or{}).get('clubTypeId'),Season=c['RealSeason'],ProviderSeasonID=c['APISeason'],NativeCountryIndex=country_indices[c['Country']],NativeCandidates=candidates,IdentityDecision=decision,ReserveOrChildNameDetected=parentchild,NoUIDAllocated=True,ProfileFile=c.get('ProfileFile')))
dump('club-identity-candidates.json',identity)
dump('native-country-anchor-evidence.json',dict(country_indices=country_indices,anchors={c:[w for w in world if int(w['ClubUID'])in ids]for c,ids in anchors.items()},source=str(worldfile),sha256=sha(worldfile),limitation='Current X10 object/index audit required before actual import; candidate matching is not native ownership approval'))
byuid={c['uid']:c for c in read(R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/competition-catalog.json')}
native=[]
for country,uid,mi,ma in [('Portugal',60,16,16),('Portugal',61,16,16),('Portugal',62,14,14),('Portugal',63,13,14),('Portugal',64,14,15),('Portugal',8876419,14,14),('Portugal',65,85,None),('Portugal',1301432,154,None),('Norway',1300397,14,14),('Norway',1300398,16,16),('Norway',1300603,14,14),('Norway',1300604,14,14),('Norway',1300605,14,14),('Norway',1300606,14,14),('Norway',1301420,93,None),('Peru',5290551,11,12),('Peru',5290553,12,None),('Peru',5290552,18,None)]:
 native.append(dict(Country=country,CompetitionUID=uid,NativeName=byuid[uid]['names'][0],CatalogueIndex=byuid[uid]['index'],Form0Min=mi,Form0Max=ma,Form1DefaultMin=mi,Form1DefaultMax=ma,Form1Qualification='inherited only if pre-existing form1 value is zero; no runtime or data-override claim',CountrySpecific=uid==1301432,Playability='lower_pool'if uid in[65,1301432,1301420,5290552,5290553]else'native_playable_settings'))
df=R/'GHIDRA_ENGINE_20261107_R5/decompiled/functions'
evidence=[]
for f in ['ram_ece540.c','ram_ece6a0.c','ram_ef0ae0.c','ram_ef0c10.c','ram_e592c0.c','ram_e593f0.c','ram_d35180.c','ram_d63c10.c']:
 p=df/f;evidence.append(dict(file=str(p),sha256=sha(p),source_exe_sha256='157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d',text=p.read_text(encoding='utf-8')))
dump('native-competition-requirements.json',dict(requirements=native,evidence=evidence,semantics='d35180 max=-2 means min, max=-1 unbounded; form0 sets form1 only when zero. Settings register Portugal levels0/1/2, Norway0/1/2, Peru0 only. No live gate readback performed.',classic_target_counts={'Portugal':[16,16,[14,14,14,14]],'Norway':[14,16,[14,14,14,14]],'Peru':[12]},status='static_native_evidence_not_runtime_validation'))
season_rows=[]
for c in comps:
 prior=read(B/c['previous_completed_table_file']);current=read(B/c['current_table_file']);pr=[r for t in prior.get('tables',[])for r in t.get('rows',[])];cu=[r for t in current.get('tables',[])for r in t.get('rows',[])]
 season_rows.append(dict(Country=c['Country'],Competition=c['id'],Level=c['real_level'],CurrentSeason=c['CurrentSeason'],PreviousCompletedSeason=c['PreviousCompletedSeason'],CurrentMembers=len(read(B/c['current_clubs_file']).get('clubs',[])),PriorTableRows=len(pr),PriorMatchesRange=[min((r.get('matches',0)for r in pr),default=0),max((r.get('matches',0)for r in pr),default=0)],CurrentVsPriorRowsEqual=pr==cu,CurrentClubsFile=c['current_clubs_file'],PreviousTableFile=c['previous_completed_table_file'],SeasonMetadataFile=c['SeasonMetadataFile'],MetadataSHA256=sha(B/c['SeasonMetadataFile']),PreviousTableSHA256=sha(B/c['previous_completed_table_file']),RankingCaveat='Annual final classification / playoff phases require explicit selection before cascade'if c['Country']=='Peru'or c['id']=='PT3A'else'Use completed season ranking; never current season points'))
dump('competition-source-coverage.json',season_rows)
pol=R/'POLAND_DATABASE_2627_R1_20261108/native-V25-N7/prepared-r2'
full=read(pol/'full-native.json');unresolved=read(pol/'unresolved.json');conflicts=read(pol/'source-conflicts.json')
polsum=dict(scope='reuse existing confirmed Poland N7; no rescrape and no API calls',clubs=126,classic_playable_clubs=34,lower_clubs=92,latest_imported_player_UIDs=2456,unresolved_birth_facts=unresolved,nationality_conflicts_preserved=conflicts,source_paths=[str(pol),str(R/'POLAND_DATABASE_2627_R1_20261108/sources/90minut-III-20261108/roster-coverage-summary.json')],raw_III_source_coverage=read(R/'POLAND_DATABASE_2627_R1_20261108/sources/90minut-III-20261108/roster-coverage-summary.json'),gaps_interpretation='Raw III coverage20DOB/20GK is earlier extraction stage; current unresolved list16 is distinct. Small squads/GK shortage do not block.7 cross-club IDs have departed/active rows and are not automatically duplicates.',live_ownership_reaudit=False)
dump('poland-existing-data-audit.json',polsum)
captures={p.name:read(p)for p in B.glob('*capture*.json')}
counts=[]
for country in ['Portugal','Norway','Peru']:
 cs=[c for c in coverage if c['Country']==country];ids={f['TMID']for f in facts if f['Country']==country};ls=[f for f in loans if f['Country']==country]
 counts.append(dict(Country=country,CatalogueClubs=len(cs),FetchedClubRosters=sum(c['Cards']>0 for c in cs),FetchedProfiles=sum(c['Country']==country and bool(c['ProfileFile'])for c in stadiums),SourceCards=sum(c['Cards']for c in cs),UniqueSourcePlayers=len(ids),ConfirmedCandidateRows=sum(c['ConfirmedCandidates']for c in cs),LoanCandidateRows=len(ls),InternationalLoanRows=sum(bool(f['OwnerSourceCountryId'])and str(f['OwnerSourceCountryId'])!={'Portugal':'136','Norway':'125','Peru':'133'}[country]for f in ls)))
csvout('coverage-by-country.csv',counts)
duplicates=collections.defaultdict(list)
for f in facts:
 if f['AcceptedFactCandidate']:duplicates[f['TMID']].append(dict(ClubTMID=f['ClubTMID'],Club=f['ClubName'],Status=f['MembershipStatus']))
dump('multi-club-candidate-queue.json',[dict(TMID=k,Assignments=v,Action='deduplicate by actual current playing club; preserve explicit parent/child/additional roles; never create duplicate profile')for k,v in duplicates.items()if len(v)>1])
before=read(B/'input-X10-source-pins.json');after={p.name:sha(p)for p in (ROOT/'Dane/db/TEST_X10').glob('*.dat')};assert before and before==after,'Source DB changed during preparation'
report=dict(status='source_material_prepared_not_import_ready',countries=counts,source_competitions=len(comps),catalogue_clubs=len(targets),roster_cards=len(facts),unique_source_player_ids=len({f['TMID']for f in facts}),confirmed_candidate_rows=sum(f['AcceptedFactCandidate']for f in facts),loan_candidate_rows=len(loans),owners=len(owners),source_gaps=len(gaps),identity_decisions=dict(collections.Counter(c['IdentityDecision']for c in identity)),fetch_errors=[c for c in targets if c.get('FetchError')],source_profiles_without_stadium=[c['Club']for c in stadiums if not c['Stadium']],captures=captures,new_calls=sum(x.get('new_calls',0)for x in captures.values()),cache_hits=sum(x.get('cache_hits',0)for x in captures.values()),api_sports_calls=0,raw_responses=len(rawlist),output_database_created=False,CA_PA_generated=False,native_writer_executed=False,source_DB_hashes_unchanged=True,source_db_pins=before,import_dependency='TEST_X11 now user SI/career PASS, season pending. No import authorized by this source-preparation task. Future import requires fresh X11 object map and existing agreed audited rating policy; catalogue entity map remains X10.')
dump('preparation-report.json',report)
print(json.dumps({k:v for k,v in report.items()if k not in['captures','source_db_pins','fetch_errors','source_profiles_without_stadium']},ensure_ascii=False,indent=2))
