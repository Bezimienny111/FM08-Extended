from pathlib import Path
from collections import defaultdict,Counter
from datetime import date
from functools import lru_cache
import json,csv,sys,hashlib
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');B=Path(__file__).resolve().parent;S=B.parent;R=S.parent
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
import x7prep_rosters_20261110 as shared
from squad_update_policy import shift_birth
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(n,v):(B/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
plans={r['TMID']:r for r in read(B/'club-plan.json')};facts=read(S/'roster-facts.json');groups=defaultdict(list)
for f in facts:
 if f['AcceptedFactCandidate']:groups[f['TMID']].append(f)
chosen=[];members=[];deferred=[]
for tid,vs in sorted(groups.items(),key=lambda x:int(x[0])):
 current=[f for f in vs if f['MembershipStatus']=='current_assignment_confirmed']
 # Current assignment outranks additional main/B association; a conflicting current owner is never guessed.
 base=current if current else vs
 semantics={(f['ClubTMID'],bool(f['Loan']),str(f['OwnerTMID']))for f in base}
 if len(base)>1 and len(semantics)>1:
  deferred.append(dict(TMID=tid,Names=list(dict.fromkeys(f['Name']for f in vs)),Reason='multiple_unresolved_actual_current_memberships',Assignments=[{k:f[k]for k in ['ClubTMID','ClubName','MembershipStatus','Loan','OwnerTMID']}for f in vs]));continue
 f=base[0];chosen.append(f)
 if len(vs)>1:members.append(dict(TMID=tid,Name=f['Name'],ChosenClub=f['ClubTMID'],ChosenOwner=f['OwnerTMID'],Loan=f['Loan'],Choice='unique_current_assignment'if current else'unique_additional_semantics',Excluded=[{k:g[k]for k in ['ClubTMID','MembershipStatus','Loan','OwnerTMID']}for g in vs if g is not f]))
native=list(csv.DictReader((B/'audit/players.csv').open(encoding='utf-8-sig',newline='')));byuid={int(n['ID']):n for n in native};bydob=defaultdict(list)
for n in native:bydob[n['BirthDate']].append(n)
shared.PRIOR=[R/'COUNTRY_BATCH_CZE_CRO_CHN_CHI_BGR_BRA_20261113/native-prep/prepared-r3',R/'COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep/prepared',R/'COUNTRY_BATCH_IDN_IND_HKG_20261112/prepared',R/'COUNTRY_BATCH_KOR_COL_ISR_20261112/six-country-stage/prepared',R/'COUNTRY_BATCH_GER_MEX_MAS_20261112/prepared',R/'POLAND_GAPS_IMPORT_PACKAGE_20261111/prepared',R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/prepared',R/'FOUR_COUNTRY_X7_20261110/prepared']+shared.PRIOR
registry,protected=shared.registry();rawcache={};candidates=[];allwanted=set();used=defaultdict(list)
import prepare_missing_squads as prep
native_nation_rows=list(csv.DictReader((B/'audit/nations.csv').open(encoding='utf-8-sig')));native_label_by_index={int(n['NationIndex']):n['Nation'] for n in native_nation_rows};nation_alias=dict(prep.NATION_ALIASES,**{'China':'China PR','Czechia':'Czech Republic','Kosovo':'Serbia','Curacao':'Netherlands Antilles','Bonaire':'Netherlands Antilles','Southern Sudan':'Sudan','Gambia':'The Gambia','Korea, North':'North Korea','Timor-Leste':'East Timor'})
source_to_native_nation={shared.norm(n):native_label_by_index[x['index']] for x in read(B/'native-nation-catalog.json') for n in x['names'] if x['index'] in native_label_by_index}
source_to_native_nation.update({shared.norm(n['Nation']):n['Nation'] for n in native_nation_rows})
def verified_nations(f):return {source_to_native_nation.get(shared.norm(nation_alias.get(n,n))) for n in f['Nationality']} - {None}

related=lru_cache(maxsize=None)(shared.related)
def raw_person(f):
 p=S/f['PlayerRaw']['raw_file']
 if p not in rawcache:
  d=json.loads(read(p)['body']).get('data')or[]
  if isinstance(d,dict):d=d.get('players',[])
  rawcache[p]={str(r['id']):r for r in d}
 return rawcache[p].get(f['TMID'],{})
for f in chosen:
 tid=f['TMID'];real=f['RealDOB'];nd=shift_birth(date.fromisoformat(real)).isoformat();raw=raw_person(f);full=' '.join([raw.get('firstName')or'',raw.get('lastName')or'']).strip();names=list(dict.fromkeys(n for n in[f['Name'],full]if n))
 prior=[r for r in registry.get(tid,[])if r['uid']in byuid and r['real_dob']==real and byuid[r['uid']]['BirthDate']in[real,nd]];pu={r['uid']for r in prior}
 possible=[n for d in [real,nd]for n in bydob[d]if any(related(n['FirstName']+' '+n['LastName'].split(' (')[0],name)or n.get('CommonName')and shared.norm(n['CommonName'])==shared.norm(name)for name in names)]
 all_identity_matches=list({int(n['ID']):n for n in possible}.values())
 possible=[n for n in all_identity_matches if n['Nationality'] in verified_nations(f)];uid=None;kind='new_profile_candidate'
 if len(pu)==1:uid=next(iter(pu));kind='reuse_exact_prior_TMID_DOB'
 elif len(pu)>1:kind='defer_prior_TMID_multiple_UID'
 elif len(possible)==1:uid=int(possible[0]['ID']);kind='reuse_name_or_knownas_plus_exact_real_or_shifted_DOB'
 elif possible:
  shifted=[n for n in possible if n['BirthDate']==nd]
  if len(shifted)==1:uid=int(shifted[0]['ID']);kind='reuse_unique_already_shifted_DOB'
  else:kind='defer_ambiguous_native_person'
 if not uid and kind=='new_profile_candidate' and all_identity_matches:
  kind='defer_matching_identity_with_conflicting_nationality';possible=all_identity_matches
 if uid and uid in protected and not pu:kind='defer_protected_prior_profile_without_same_TMID';uid=None
 if uid and byuid[uid]['Nationality'] not in verified_nations(f):kind='defer_native_source_nationality_conflict';uid=None
 if uid and uid in shared.HARD:kind='defer_explicit_protected';uid=None
 allwanted.update(int(n['ID'])for n in possible);allwanted.update(pu)
 if uid:used[uid].append(tid)
 candidates.append(dict(TMID=tid,Name=f['Name'],SourceFullName=full,RealDOB=real,NativeDOB=nd,ExistingUID=uid,Decision=kind,PlayingClubTMID=f['ClubTMID'],OwnerTMID=str(f['OwnerTMID'])if f['Loan']else f['ClubTMID'],Loan=f['Loan'],NativeCandidates=[{k:n[k]for k in ['ID','FirstName','LastName','CommonName','BirthDate','ClubIndex','CA','PA','Nationality']}for n in possible],PriorEvidence=prior,DOBAction='PRESERVE_ALREADY_SHIFTED'if uid and byuid[uid]['BirthDate']==nd else'ONE_SHIFT_REAL_TO_NATIVE_ONCE'if uid else'NEW_DATE_SHIFT_ONCE',SourceFact=f))
conflicts={u:ts for u,ts in used.items()if len(ts)>1}
for c in candidates:
 if c['ExistingUID']in conflicts:c['Decision']='defer_repeated_native_UID_between_source_people';c['ExistingUID']=None
for d in deferred:
 # Preserve source registry UIDs for any unresolved membership.
 allwanted.update(r['uid']for r in registry.get(d['TMID'],[])if r['uid']in byuid)
clubteams={int(c['NativeTeamIndex'])for c in plans.values()if c['NativeTeamIndex']is not None};legacy={int(n['ID'])for n in native if int(n['ClubIndex'])in clubteams}
requested=allwanted|legacy
manifest=dict(Status='PERSON_IDENTITY_CANDIDATES_READY_TYPED_CONTRACTS_PENDING',AcceptedRows=sum(len(v)for v in groups.values()),UniqueSourcePeople=len(groups),ChosenPeople=len(chosen),ReconciledMultiMemberships=len(members),UnresolvedMembershipPeople=len(deferred),PersonDecisions=dict(Counter(c['Decision']for c in candidates)),PotentialReuseUIDs=len(allwanted),LegacyRosterUIDs=len(legacy),AllRequestedN4UIDs=len(requested),RepeatedUIDConflicts=conflicts,AlreadyShiftedDOBPreserved=sum(c['DOBAction']=='PRESERVE_ALREADY_SHIFTED'for c in candidates),NativeAllocation=False,NativeWrite=False)
dump('membership-reconciliation.json',dict(Decisions=members,Deferred=deferred));dump('person-identity-candidates.json',candidates);dump('person-preflight-summary.json',manifest);dump('N4-requested-UIDs.json',dict(UIDs=sorted(requested),ParticipantUIDs=sorted({c['ExistingUID']for c in candidates if c['ExistingUID']}),PotentialIdentityUIDs=sorted(allwanted),LegacyRosterUIDs=sorted(legacy)))
print(json.dumps(manifest,ensure_ascii=True),flush=True)