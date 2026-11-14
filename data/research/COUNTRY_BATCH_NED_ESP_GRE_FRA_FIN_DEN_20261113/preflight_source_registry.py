"""Single source-level six-country preflight; no native DB parse, allocation or assignment."""
from pathlib import Path
import csv,json,collections,hashlib,sys,re
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;ROOT=B.parents[3];R=B.parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,x):(B/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
targets=read(B/'source-targets.json');facts=read(B/'roster-facts.json');owners=read(B/'loan-owner-catalogue.json');index=read(B/'raw-source-index.json');clubs={};clubrefs={}
for ref in index:
 if '/clubs?' not in ref['url'] and not re.search(r'/club/\d+$',ref['url']):continue
 raw=read(B/ref['raw_file']);obj=json.loads(raw['body']);data=obj.get('data',[]) if isinstance(obj,dict) else []
 for x in data if isinstance(data,list) else [data] if isinstance(data,dict) else []:
  if str(x.get('id','')) not in clubs or ref['fetched_at']>=clubrefs[str(x['id'])]['fetched_at']:clubs[str(x['id'])]=x;clubrefs[str(x['id'])]=ref
wanted={str(c['TMID']):c for c in targets};queue=[];registry=[]
for tid in sorted(set(wanted)|{str(x['TMID']) for x in owners}):
 c=wanted.get(tid,{});raw=clubs.get(tid,{});base=raw.get('baseDetails') or {};main=str(base.get('mainClubId') or '');parent=main if main and main!=tid else '';kind=base.get('clubTypeId');role='source_reserve_parent_required' if parent or kind not in [None,1] else 'first_team_or_unclassified'
 registry.append(dict(TMID=tid,Name=c.get('Name') or raw.get('name'),Country=c.get('Country'),SourceCountryID=base.get('countryId'),SourceClubTypeID=kind,ParentTMID=parent,LegalSuperiorClubID=base.get('superiorClubId'),Role=role,WithinSixCountryCatalogue=tid in wanted,SourceRef=clubrefs.get(tid),NativeUID=None,NativeResolution='NOT_ATTEMPTED; later single native identity/contract preflight required'))
 if parent and parent not in wanted:queue.append(dict(Type='reserve_parent_outside_roster_catalogue',ClubTMID=tid,ParentTMID=parent,Action='resolve parent exactly before native; never substitute first-team roster for reserve'))
 if not raw:queue.append(dict(Type='club_raw_identity_missing',ClubTMID=tid,Action='source identity pending; no native UID guessed'))
for x in read(B/'multi-club-candidate-queue.json'):queue.append(dict(Type='multiple_current_memberships',**x))
for x in owners:
 if not x.get('Name') or x.get('SourceCountryId') is None:queue.append(dict(Type='loan_owner_identity_gap',**x))
# Historical registry candidates are evidence queues only, never an assignment to the new source facts.
ledger_paths=[R/'POLAND_GAPS_IMPORT_PACKAGE_20261111/final-native-player-UID-ledger.csv',R/'COUNTRY_BATCH_GER_MEX_MAS_20261112/final-native-player-UID-ledger.csv',R/'COUNTRY_BATCH_KOR_COL_ISR_20261112/six-country-stage/final-native-player-UID-ledger.csv',R/'COUNTRY_BATCH_IDN_IND_HKG_20261112/final-native-player-UID-ledger.csv']
prior=collections.defaultdict(list);pins={}
for p in ledger_paths:
 if not p.exists():continue
 pins[str(p.relative_to(ROOT))]=sha(p)
 for r in csv.DictReader(p.open(encoding='utf-8-sig',newline='')):
  if r.get('TMID'):prior[r['TMID']].append(dict(UID=r.get('UID'),RealDOB=r.get('RealDOB'),ClubUID=r.get('ClubUID'),PlayingTEAM=r.get('PlayingTEAM'),OwnerTEAM=r.get('OwnerTEAM'),SourceName=r.get('SourceName'),Ledger=str(p.relative_to(ROOT))))
existing=[]
for f in facts:
 if not f['AcceptedFactCandidate'] or f['TMID'] not in prior:continue
 evidence=prior[f['TMID']];uids={r['UID'] for r in evidence if r['UID']};dobs={r['RealDOB'] for r in evidence if r['RealDOB']};state='HISTORIC_TM_UID_AND_REAL_DOB_MATCH_REQUIRES_FRESH_CONTRACT_READ' if len(uids)==1 and dobs=={f['RealDOB']} else 'HISTORIC_IDENTITY_CONFLICT_REVIEW'
 row=dict(TMID=f['TMID'],Name=f['Name'],RealDOB=f['RealDOB'],PlayingClubTMID=f['ClubTMID'],Loan=f['Loan'],OwnerTMID=f['OwnerTMID'],Status=state,HistoricalEvidence=evidence,NativeUIDAllocated=False,CurrentNativeContractVerified=False);existing.append(row)
 if state=='HISTORIC_IDENTITY_CONFLICT_REVIEW':queue.append(dict(Type='historical_person_identity_conflict',**row))
dump('collected/global-club-registry.json',registry);dump('collected/existing-native-identity-contract-candidates.json',existing);dump('collected/early-exceptions.json',queue);dump('collected/source-preflight-summary.json',dict(targets=len(targets),clubs_and_worldwide_owners=len(registry),confirmed_player_rows=sum(f['AcceptedFactCandidate'] for f in facts),multiple_membership_persons=len(read(B/'multi-club-candidate-queue.json')),historical_native_contract_candidates=len(existing),exceptions_by_type=dict(collections.Counter(x['Type'] for x in queue)),ledger_pins=pins,NativeUIDAllocation=False,DBWrite=False,FreshPostSIContractPreflightStillRequired=True,Scope='Source-level early queue only; not a ready native plan; no name-only native matching'))
print('SOURCE_PREFLIGHT',len(registry),'CLUBS_OWNERS',len(existing),'HISTORICAL_CONTRACT_CANDIDATES',dict(collections.Counter(x['Type'] for x in queue)),flush=True)

