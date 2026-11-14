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
facts=[];loans=[];gaps=[];coverage=[];stadiums=[];owners={};cutoff='2026-11-12'
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

print('SOURCE_FACTS',len(facts),'LOANS',len(loans),'GAPS',len(gaps),'OWNERS',len(owners),flush=True)
