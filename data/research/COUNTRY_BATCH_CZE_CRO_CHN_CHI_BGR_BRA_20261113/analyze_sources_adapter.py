"""Configured X17 source fact adapter; same engine, only snapshot/country/scope configuration."""
from pathlib import Path
import sys,json,hashlib,collections,csv
from datetime import datetime,timezone
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;ROOT=B.parents[3]
engine=ROOT/'FmLauncher/data/research/COUNTRY_BATCH_GER_MEX_MAS_20261112/analyze_sources.py'
expected='a92988ab73f72f4153fa596c5fbcfb127ee1353c2f4dc555238c2d6b054f978d'
assert hashlib.sha256(engine.read_bytes()).hexdigest()==expected
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
targets=read(B/'source-targets.json');assert targets and len({str(x['TMID']) for x in targets})==len(targets)
source=engine.read_text(encoding='utf-8');needle="coverage=[];stadiums=[];owners={};cutoff='2026-11-12'";assert needle in source;source=source.replace(needle,"coverage=[];stadiums=[];owners={};cutoff='2026-11-13'")
ns={'__file__':str(Path(__file__)),'__name__':'shared_source_fact_engine'}
exec(compile(source,str(engine),'exec'),ns)
facts=ns['facts'];coverage=ns['coverage'];loans=ns['loans'];targets=ns['targets']
clubcfg={str(c['TMID']):c for c in targets}
for f in facts:
 c=clubcfg[f['ClubTMID']];f['ClubSourceScope']=c.get('SourceScope','closed_country_scope');f['ClubIdentityPending']=c.get('ClubIdentityPending',False);f['ReadyForNativeImport']=False
ns['dump']('roster-facts.json',facts);ns['dump']('loan-facts.json',loans)
def dump(name,data):(B/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
counts=[]
for country in ['Czech Republic','Croatia','China','Chile','Bulgaria','Brazil']:
 cs=[c for c in targets if c['Country']==country];cc=[c for c in coverage if c['Country']==country];ff=[f for f in facts if f['Country']==country]
 counts.append(dict(Country=country,PlannedClubs=len(cs),CollectedClubs=sum('PlayersFetched' in c and not c.get('FetchError') for c in cs),Cards=sum(c['Cards'] for c in cc),ConfirmedCandidateRows=sum(f['AcceptedFactCandidate'] for f in ff),UniquePlayerIDs=len({f['TMID'] for f in ff}),AcceptedLoanRows=sum(f['Loan'] and f['AcceptedFactCandidate'] for f in ff),SourceGaps=sum(not f['AcceptedFactCandidate'] for f in ff)))
dup=collections.defaultdict(list)
for f in facts:
 if f['AcceptedFactCandidate']:dup[f['TMID']].append(dict(ClubTMID=f['ClubTMID'],Club=f['ClubName'],Country=f['Country'],MembershipStatus=f['MembershipStatus'],Loan=f['Loan'],OwnerTMID=f['OwnerTMID']))
registry=[dict(TMID=k,Assignments=v,NeedsPlayingClubResolution=len(v)>1,NativeUID=None) for k,v in dup.items()]
(B/'collected').mkdir(exist_ok=True)
dump('collected/global-player-registry.json',registry);dump('multi-club-candidate-queue.json',[dict(TMID=k,Assignments=v,Action='resolve actual current or reserve membership before any native plan; no duplicate person') for k,v in dup.items() if len(v)>1]);dump('coverage-by-country.json',counts)
with (B/'coverage-by-country.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(counts[0]));w.writeheader();w.writerows(counts)
summary=dict(status=('SOURCE_COLLECTION_COMPLETE' if len({x['Country'] for x in targets})==6 else 'CLOSED_COUNTRY_SUBSET_COLLECTED_OTHER_COUNTRIES_OPEN') if sum(x['CollectedClubs'] for x in counts)==len(targets) else 'SOURCE_COLLECTION_IN_PROGRESS',checked_at=datetime.now(timezone.utc).isoformat(),countries=counts,planned_clubs=len(targets),collected_clubs=sum(x['CollectedClubs'] for x in counts),total_cards=len(facts),unique_players=len({f['TMID'] for f in facts}),confirmed_candidate_rows=sum(f['AcceptedFactCandidate'] for f in facts),accepted_loan_rows=sum(f['Loan'] and f['AcceptedFactCandidate'] for f in facts),source_gaps=len(ns['gaps']),multi_club_candidates=sum(len(v)>1 for v in dup.values()),worldwide_loan_owner_clubs=len(ns['owners']),source_dates_shifted=False,CA_PA_generated=False,native_UID_allocated=False,database_written=False)
summary['closed_roster_countries']=sorted({x['Country'] for x in targets});summary['all_six_country_scopes_closed']=len(summary['closed_roster_countries'])==6
for x in counts:x['ScopeStatus']='CLOSED_ROSTER_LIST' if x['PlannedClubs'] else 'OPEN_ROSTER_SCOPE_NOT_YET_LOCKED'
dump('source-progress.json',summary);dump('source-facts-engine-pins.json',dict(engine=str(engine.relative_to(ROOT)),engine_sha256=expected,configured_sha256=hashlib.sha256(source.encode()).hexdigest(),adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),configuration_change='snapshot cutoff12XI→13XI2026 only; countries and count configured by this adapter',snapshot_date='2026-11-13',source_dob_shifted=False,CA_PA_generated=False,database_written=False));print(json.dumps(summary),flush=True)

