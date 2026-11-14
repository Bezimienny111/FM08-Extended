"""Native CSV preparation against immutable X22 + pinned projected club map. Never writes DAT."""
from pathlib import Path
from collections import Counter,defaultdict
from datetime import date
import sys,json,csv,hashlib,ast,statistics,math
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent;SRC=B.parent;P=B/'prepared';P.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
import x7prep_rosters_20261110 as shared
import prepare_missing_squads as prep
from squad_update_policy import shift_birth,SOURCE_LEVELS
from prepare_english_fc27 import scale_ca
import rating_model_v2 as model
read=shared.read;rows=shared.rows;norm=shared.norm;related=shared.related;dump=shared.dump;writecsv=shared.writecsv
REF='2026-11-14';RAW={}
def raw_person(f):
 path=SRC/f['PlayerRaw']['raw_file']
 if path not in RAW:
  values=json.loads(read(path)['body']).get('data')or[]
  if isinstance(values,dict):values=values.get('players',[])
  RAW[path]={str(x['id']):x for x in values}
 return RAW[path].get(f['TMID'],{})
def abilities(key,country,competition,dob,position,rating=None,potential=None):
 key=key.replace('tm:tm:','tm:')
 value=model.estimate(key,country,int(competition[-1]),dob,position,fc_ca=scale_ca(rating)if rating else None,fc_pa=scale_ca(potential)if potential else None)
 return value['CA'],value['PA'],value['AbilitySource']
prep.abilities=abilities
SOURCE_LEVELS.update({'B1L1':1,'B1L2':2,'B1L3':3,'B1L4':4,'B1L5':5,'B1L6':6})
def main():
 source_facts=read(SRC/'roster-facts.json');assert sum(f['AcceptedFactCandidate']for f in source_facts)==4256 and sum(f['AcceptedFactCandidate']and f['Loan']for f in source_facts)==495,'Pinned England source4256/495 changed'
 assert all(f['Country']=='England'for f in source_facts),'Other country in England source facts'
 cm=rows(B/'club-map.csv');alloc=read(B/'core-assignments.json');alloc=alloc.get('Assignments',alloc.get('assignments',[]))if isinstance(alloc,dict)else alloc;am={str(a.get('TMID',a.get('SourceTMID'))):a for a in alloc};assert len(am)==164;assert len(cm)==164;
 for c in cm:
  assert c['TMID']in am and am[c['TMID']]['DesiredDivision']is not None;c['DivisionIndex']=str(am[c['TMID']]['DesiredDivision']);c['Group']=c['Country']+' '+c['DivisionIndex']
 core={x['TMID']:x for x in cm};plans={x['TMID']:dict(x,RealLevel=x['RealLevel'] or x.get('PreviousRealLevel') or 4,RatingLevelEvidence='confirmed_source_real_level' if x['RealLevel'] else 'previous_completed_national_D_level4_only_current_level_unknown') for x in read(B/'club-plan.json')};foreign={x['TMID']:x for x in rows(B/'foreign-owner-map.csv')if x['TMID']};aliases={x['SourceTMID']:x for x in read(B/'foreign-owner-aliases.json')};world={str(x['ClubUID']):x for x in read(B/'native-world-identities.json')}
 native=rows(B/'audit/players.csv');byuid={int(x['ID']):x for x in native};bydob=defaultdict(list);modern=defaultdict(list)
 for n in native:
  bydob[n['BirthDate']].append(n)
  if int(n['ID'])>=1600000000 and n['BirthDate']:modern[norm(n['FirstName']+' '+n['LastName'].split(' (')[0])].append(n)
 shared.PRIOR=[R/'COUNTRY_BATCH_BLR_BEL_AUT_AUS_ARG_20261114/native-prep/prepared',R/'COUNTRY_BATCH_CZE_CRO_CHN_CHI_BGR_BRA_20261113/native-prep/prepared-r3',R/'COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep/prepared',R/'COUNTRY_BATCH_IDN_IND_HKG_20261112/prepared',R/'COUNTRY_BATCH_KOR_COL_ISR_20261112/six-country-stage/prepared',R/'COUNTRY_BATCH_GER_MEX_MAS_20261112/prepared',R/'POLAND_GAPS_IMPORT_PACKAGE_20261111/prepared',R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/prepared',R/'FOUR_COUNTRY_X7_20261110/prepared']+shared.PRIOR
 registry,protected=shared.registry();preserveclubs={u for x in read(B/'deferred-clubs.json')for u in x['PreserveNativeUIDs']}|{104982};preserveteams={x['TeamIndex']for x in read(B/'native-world-identities.json')if x['ClubUID']in preserveclubs};protected.update(int(n['ID'])for n in native if int(n['ClubIndex'])in preserveteams);future=rows(B/'future-audit/all_future_transfers.csv');futureuids={int(x['UID'])for x in future if x.get('UID')and int(x['UID'])in byuid};hard=set(shared.HARD)|futureuids;protected|=futureuids
 nations=rows(B/'audit/nations.csv');nn={norm(x['Nation']):x['Nation']for x in nations};nalias=dict(prep.NATION_ALIASES,**{'China':'China PR','Macao':'Macau','Bonaire':'Netherlands Antilles','North Macedonia':'FYR of Macedonia','Kosovo':'Serbia','Bosnia & Herzegovina':'Bosnia and Herzegovina','Czechia':'Czech Republic','Ivory Coast':'WKS','Republic of Ireland':'Irlandia','Curacao':'Netherlands Antilles','CuraÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€šĂ‚Â§ao':'Netherlands Antilles','Southern Sudan':'Sudan','The Gambia':'The Gambia','Gambia':'The Gambia','Korea, North':'North Korea','Philippines':'The Philippines','Jersey':'Anglia','TÄ‚â€žĂ˘â‚¬ĹˇÄ‚â€žĂ‹ĹĄrkiye':'Turcja','Timor-Leste':'East Timor'})
 for source_label,native_index in [('Iceland',148),('Northern Ireland',159),('Ireland',163),('Hong Kong',56),('India',57),('Indonesia',58),('Netherlands',158),('Spain',170),('Greece',146),('France',143),('Finland',142),('Denmark',138),('Czech Republic',137),('Croatia',135),('China',55),('Chile',190),('Bulgaria',134),('Brazil',189),('Belarus',132),('Belgium',131),('Austria',129),('Australia',177),('Argentina',187),('England',139),('Wales',175)]:
  native_labels=[n['Nation']for n in nations if int(n['NationIndex'])==native_index];assert len(native_labels)==1;nalias[source_label]=native_labels[0]
 def nation(raw):
  v=nn.get(norm(nalias.get(raw,raw)))
  if not v:raise ValueError('unmapped_nationality:'+raw)
  return v
 def entity(tid):
  if tid in core:return core[tid]
  a=aliases.get(tid)
  if not a or a['Decision'].startswith('defer'):raise ValueError('unresolved_foreign_loan_owner:'+tid)
  tid=a['CanonicalMainTMID']
  if tid in core:return core[tid]
  if tid in foreign:return foreign[tid]
  uid=a['NativeClubUID']
  if not uid:raise ValueError('unresolved_native_owner:'+tid)
  w=world[str(uid)]
  return dict(ClubUID=uid,TeamIndex=w['TeamIndex'],FamilyIndex=w['TeamTailFamilyIndex'],ParentUID=w['ParentUID']or'',ClubName=w['Names'][0],CountryIndex=w['TeamCountry'],TMID=tid)
 prechecked={v['TMID']:v for v in read(B/'person-identity-candidates.json')};pre_source_deferred=[]
 groups=defaultdict(list)
 for f in read(SRC/'roster-facts.json'):
  if f['AcceptedFactCandidate']and f['ClubTMID']in core:groups[f['TMID']].append(f)
 chosen=[];membership=[]
 for tid,values in sorted(groups.items(),key=lambda x:int(x[0])):
  values.sort(key=lambda f:(f['ClubTMID']!=prechecked[tid]['PlayingClubTMID'],f['MembershipStatus']!='current_assignment_confirmed',plans[f['ClubTMID']]['RealLevel'],f['ClubTMID']))
  chosen.append(values[0]);membership.extend(dict(TMID=tid,ChosenClubTMID=values[0]['ClubTMID'],ExcludedClubTMID=f['ClubTMID'],Reason='one_source_UID_current_assignment_then_first_reserve_reconciliation')for f in values[1:])
 roster={tid:{str(p['id']):p for p in read(Path(c['RosterFile']))['players']}for tid,c in plans.items()}
 ea=rows(ROOT/'FMExt/data/fc27_players_all_2026_09_12.csv');eadob=defaultdict(list)
 for f in ea:
  if f['gender']=="Men's Football":eadob[f['birthdate']].append(f)
 tree=ast.parse((ROOT/'FM08-Database-Tools/scratch/prepare_poland_squads_n4_20261108.py').read_text(encoding='utf-8'));fcmap=next(ast.literal_eval(x.value)for x in ast.walk(tree)if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='fcmap'for t in x.targets))
 entries=[];idents=[];loans=[];deferred=[];used=set();gapuids=set();ownerentities={};reusedregistry=[];oldproposals=[]
 for checked in prechecked.values():
  if checked['PlayingClubTMID']not in core:
   uids=[int(n['ID'])for n in checked['NativeCandidates']];gapuids.update(uids);deferred.append(dict(TMID=checked['TMID'],Name=checked['Name'],Club=checked['PlayingClubTMID'],Reason='excluded_club_identity_or_role_deferred',NativeUIDsProtected=uids))
 for sid,f in enumerate(chosen,1):
  possible=[]
  try:
   tid=f['TMID'];club=core[f['ClubTMID']];real=f['RealDOB'];nd=shift_birth(date.fromisoformat(real)).isoformat();nat=nation(f['Nationality'][0]);role=prep.TM_POSITIONS.get(f['Role'])or prep.GROUP_POSITIONS.get(f['Role']);assert role,'unresolved_role'
   playing=int(club['TeamIndex'])
   raw=raw_person(f);full=' '.join([raw.get('firstName')or'',raw.get('lastName')or'']).strip();source_names=[f['Name']]+([full]if len(full.split())>=2 else[])
   checked=prechecked[tid];possible=[byuid[int(n['ID'])]for n in checked['NativeCandidates']];reg=checked['PriorEvidence'];reguids={v['uid']for v in reg};existing=None
   assert checked['PlayingClubTMID']==f['ClubTMID'] and checked['RealDOB']==real,('closed membership drift',tid)
   if checked['Decision'].startswith('defer'):raise ValueError(checked['Decision'])
   if checked['ExistingUID']:existing=byuid[int(checked['ExistingUID'])]
   uid=int(existing['ID'])if existing else -1
   if uid in hard:raise ValueError('explicit_protected_or_future_transfer')
   if existing and uid in protected and uid not in reguids:raise ValueError('protected_prior_import_without_same_TMID_DOB')
   if uid>0 and uid in used:raise ValueError('repeated_native_UID')
   if existing:
    assert existing['BirthDate']in[real,nd],'native_DOB_outside_verified_real_or_shifted_phase'
    assert 1<=int(existing['CA'])<=int(existing['PA'])<=200,'native_CA_PA_unknown_or_special_preserve_defer'
   else:
    conflict=[n for n in modern[norm(f['Name'])]if abs(date.fromisoformat(n['BirthDate']).year+19-date.fromisoformat(real).year)<=1 and n['Nationality']==nat]
    if conflict:possible+=conflict;raise ValueError('modern_name_nearby_DOB_conflict_defer')
   if existing:
    supported=[]
    for source_nation in f['Nationality']:
     try:supported.append(nation(source_nation))
     except ValueError:pass
    if existing['Nationality']in supported:nat=existing['Nationality']
   owner=entity(str(f['OwnerTMID']))if f['Loan']else club;oi=int(owner['TeamIndex']);ownerentities[oi]=owner
   if f['Loan']:
    start=f['RealLoanStart'];end=f['RealLoanEnd']
    assert start and end,'loan_dates_incomplete_defer_no_synthetic_end'
    assert start<=REF<end,'not_active_loan_at_snapshot'
    assert oi!=playing,'loan_owner_equals_borrower'
    assert not f.get('MandatoryBuy'),'mandatory_buy_unsupported'
    assert f.get('BuyOptionFee')in[None,''],'known_fee_needs_verified_converter'
   data=roster[f['ClubTMID']][tid];name=f['Name']
   fcs=[z for z in eadob[real]if related(z['first_name']+' '+z['last_name'],name)or norm(z.get('common_name'))==norm(name)];fc=None
   if len({z['player_id']for z in fcs})==1:
    z=fcs[0];fc={k:z.get(v,'')for k,v in fcmap.items()};fc.update(rating=z['overall_rating'],potential='',height=z.get('height_cm'),foot=z['preferred_foot'],weak_foot=z['weak_foot'],position=z['position'],position_alt='',position_alt_2='',position_alt_3='')
   if len(name.split())<2 and not existing:
    if len(full.split())>=2:name=full
    elif len({z['player_id']for z in fcs})==1:name=fcs[0]['first_name']+' '+fcs[0]['last_name']
    else:raise ValueError('unverified_full_name_mononym')
   row,proof=prep.generate_profile(dict(id=tid,name=name,shirt_number=data.get('shirt_number')or 0,height=data.get('height'),foot=data.get('foot')),{},dict(country=club['Country'],source_competition='B1L'+str(plans[f['ClubTMID']]['RealLevel']),club_index=oi,native_name=owner['ClubName']),dict(RealBirthDate=real,NativeBirthDate=nd,DOBPrecision='day'),nat,role,fc)
   if existing:
    row.update(ExistingID=uid,FirstName=existing['FirstName'],LastName=existing['LastName'],CA=int(existing['CA']),PA=int(existing['PA']),Height=int(existing['Height']),Weight=int(existing['Weight']),WeeklyWage=max(300,int(existing['WeeklyWage'])));used.add(uid)
    proof.update(ca=row['CA'],pa=row['PA'],existing_id=uid,ability_source='preserved_native_profile')
    if uid in reguids:reusedregistry.append(dict(TMID=tid,UID=uid,real_dob=real,native_dob=nd,Registries=reg))
   proof.update(rating_level=plans[f['ClubTMID']]['RealLevel'],rating_level_evidence=plans[f['ClubTMID']]['RatingLevelEvidence'],subject_id=sid,TMID=tid,name=f['Name'],source_dob=real,native_dob=nd,source_nationality=f['Nationality'][0],native_nationality=nat,playing_club=playing,owner_club=oi,source_player_id=tid,existing_id=uid,model_version=model.VERSION,seed_uid=str(uid)if uid>0 else'tm:'+tid,seed_basis='preserved_native_no_reroll'if uid>0 else'canonical_source_UID_namespace_stable_before_native_allocation',source_version='TM_snapshot_2026_11_14_season_resolved_by_name',roster_source='https://www.transfermarkt.com/-/kader/verein/'+f['ClubTMID'],bio_source='https://www.transfermarkt.com/-/profil/spieler/'+tid,playing_club_TMID=f['ClubTMID'],owner_TMID=str(f['OwnerTMID'])if f['Loan']else f['ClubTMID'],existing_CA_PA_attributes_preserved=bool(existing),PlayerRaw=f['PlayerRaw'],HistoryRaw=f['HistoryRaw'])
   entries.append(dict(row=row,proof=proof))
   idents.append(dict(SubjectID=sid,ExistingID=uid,ExpectedFirstName=existing['FirstName']if existing else'',ExpectedLastName=existing['LastName']if existing else'',ExpectedDOB=existing['BirthDate']if existing else'',ExpectedClubIndex=int(existing['ClubIndex'])if existing else -1,TargetDOB=nd,PlayingClubIndex=playing,OwnerClubIndex=oi,ExistingCA=int(existing['CA'])if existing else -1,ExistingPA=int(existing['PA'])if existing else -1))
   if f['Loan']:loans.append(dict(SubjectID=sid,OwnerClubIndex=oi,LoanClubIndex=playing,RealStartDate=start,RealEndDate=end,NativeStartDate=min(shift_birth(date.fromisoformat(start)),date(2007,7,1)).isoformat(),NativeEndDate=shift_birth(date.fromisoformat(end)).isoformat(),FeeToBuyNative='',FeeConversionStatus='unknown_no_fee_written',BuyType='unknown',SourceURL=proof['bio_source'].replace('/profil/','/transfers/'),LoanShirt='',WagePercent='',Recall='',StartPrecision='active_at_snapshot_native_start_clamped_real_preserved',EndPrecision='published_return_date'))
  except(ValueError,AssertionError,KeyError,TypeError)as ex:
   gapuids.update(int(n['ID'])for n in possible);deferred.append(dict(TMID=f['TMID'],Name=f['Name'],Club=f['ClubName'],Reason=str(ex),Source=f['PlayerRaw'],NativeUIDsProtected=[int(n['ID'])for n in possible]))
 # Source-proven legacy correction is confined to current target reuse.
 mappingpath=ROOT/'FmLauncher/data/imports/FURTHER_MAPPING_AUDIT_20261106_1433/mapping-audit/mapping-results.json'
 baselinepath=ROOT/'FmLauncher/data/imports/STRASBOURG_INTERNACIONAL_AUDIT_20261106/audit/players.csv'
 mappings=read(mappingpath);mapped=defaultdict(list)
 for m in mappings:
  for uid in m['current_uids']:mapped[int(uid)].append(m)
 baseline={int(n['ID']):n for n in rows(baselinepath)}
 x11guard={int(n['uid'])for n in rows(R/'CA_PA_REPAIR_X11_20261111/before-after.csv')}
 globaltalent=read(R/'CA_PA_AUDIT_20261111/R2/global-talent-draw-register.json')
 winneruids={int(u)for w in globaltalent['winners']for u in w['known_uids']}
 winnersource={str(w['source_key'])for w in globaltalent['winners']}
 sourcepins={str(f):hashlib.sha256(f.read_bytes()).hexdigest()for f in[mappingpath,baselinepath,R/'CA_PA_REPAIR_X11_20261111/before-after.csv',R/'CA_PA_AUDIT_20261111/R2/global-talent-draw-register.json']}
 ratingrepairs=[];classification=[]
 for e in entries:
  pr=e['proof'];uid=pr['existing_id'];row=e['row']
  if uid<0:
   classification.append(dict(UID='',TMID=pr['TMID'],Club=core[pr['playing_club_TMID']]['ClubName'],Class='new_profile',CA_before='',PA_before='',CA_after=row['CA'],PA_after=row['PA'],Changed=False,SourceEvidence='current_confirmed_TMID_DOB'));continue
  old=baseline.get(uid);cur=byuid[uid];ms=mapped.get(uid,[]);cls='preserved_unknown_provenance';why='No exact single-source historical rating provenance';eligible=False
  equal=bool(old and tuple(old[k]for k in['FirstName','LastName','BirthDate','CA','PA'])==tuple(cur[k]for k in['FirstName','LastName','BirthDate','CA','PA']))
  if uid in x11guard:cls='protected_accepted_X11_repair';why='Already accepted542scope; do not recalculate again'
  elif uid in winneruids or'tm:'+pr['TMID']in winnersource or row['PA']>=150:cls='protected_previous_talent_or_high_PA';why='Known award or conservative protection for unjournalled historical PA'
  elif any(m['source_kind']=='FC27'for m in ms):cls='protected_FC27_source';why='Exact UID in historical FC27 mapping'
  elif uid<1600000000:cls='preserved_original_or_credible_native';why='Not a proven project-generated fallback'
  elif equal and ms and all(m['source_kind']=='TM'for m in ms):
   script=ROOT/'FM08-Database-Tools/archive/historical-squad-imports'/ms[0]['script']
   allscripts=list(dict.fromkeys(ROOT/'FM08-Database-Tools/archive/historical-squad-imports'/m['script']for m in ms))
   if all(q.exists()for q in allscripts):
    cls='reestimated_proven_legacy_project';why='Exact UID in historical exclusively-TM mappings + identical baseline identity/CA/PA + all linked generators; previous club/source ambiguity retained, not inferred';eligible=True
    for q in allscripts:sourcepins[str(q)]=hashlib.sha256(q.read_bytes()).hexdigest()
  beforeca,beforepa=row['CA'],row['PA']
  if eligible:
   country=core[pr['playing_club_TMID']]['Country'];level=plans[pr['playing_club_TMID']]['RealLevel'];role=next((k[3:]for k,v in row.items()if k.startswith('Pos')and v==20),None)
   # Use the authenticated EA anchor when present; otherwise deterministic nativeUID+model v2.
   fcs=[z for z in eadob[pr['source_dob']]if related(z['first_name']+' '+z['last_name'],pr['name'])or norm(z.get('common_name'))==norm(pr['name'])]
   fc=next(iter(fcs))if len({z['player_id']for z in fcs})==1 else None
   after=model.estimate(uid,country,level,date.fromisoformat(pr['source_dob']),role,fc_ca=scale_ca(int(fc['overall_rating']))if fc else None)
   afterca=after['CA'];afterpa=max(beforepa,after['PA'],afterca)
   row.update(CA=afterca,PA=afterpa);pr.update(ca=afterca,pa=afterpa,ability_source='reestimated_proven_legacy_project_v2',seed_uid=str(uid),seed_basis='native_UID_and_model_version',existing_CA_PA_attributes_preserved=False,existing_attributes_and_personality_preserved=True,previous_ca=beforeca,previous_pa=beforepa,legacy_provenance=why,legacy_source_script=' | '.join(m['script']for m in ms),legacy_historical_source_candidates=ms)
   ratingrepairs.append(dict(UID=uid,TMID=pr['TMID'],FirstName=row['FirstName'],LastName=row['LastName'],ExpectedDOB=cur['BirthDate'],CA_before=beforeca,PA_before=beforepa,CA_after=afterca,PA_after=afterpa,ModelVersion=model.VERSION,SeedUID=uid,PlayingClubTMID=pr['playing_club_TMID'],SourceLevel=level,SourceScript=' | '.join(m['script']for m in ms),CurrentEAID=fc['player_id']if fc else'',ProtectedAward=False,AttributesAction='preserve_byte_exact',PersonalityAction='preserve_byte_exact'))
  classification.append(dict(UID=uid,TMID=pr['TMID'],Club=core[pr['playing_club_TMID']]['ClubName'],Class=cls,CA_before=beforeca,PA_before=beforepa,CA_after=row['CA'],PA_after=row['PA'],Changed=(beforeca,beforepa)!=(row['CA'],row['PA']),SourceEvidence=why))
 writecsv(P/'legacy-rating-repairs.csv',ratingrepairs);writecsv(P/'rating-source-classification.csv',classification)
 dump(P/'legacy-rating-evidence-pins.json',sourcepins)
 priorlottery={int(d['club_uid']):d for d in globaltalent['known_draws']}
 historicalclubs={int(m['club_uid'])for m in mappings if m.get('source_kind')=='TM'and m.get('club_uid')}
 for folder in shared.PRIOR:
  fp=folder/'talent-lottery.json'
  if fp.exists():
   for decision in read(fp):
    key=decision.get('club_uid')
    if key is not None:priorlottery[int(key)]=decision
 lottery=[]
 for c in cm:
  group=[e for e in entries if e['proof']['playing_club']==int(c['TeamIndex'])];prep.assign_numbers(group)
  if int(c['ClubUID'])in historicalclubs and int(c['ClubUID'])not in priorlottery:decision=dict(club_uid=int(c['ClubUID']),awarded=False,reason='historical_project_club_lottery_unknown_no_free_reroll')
  elif int(c['ClubUID'])in priorlottery:decision=dict(club_uid=int(c['ClubUID']),awarded=False,reason='prior_club_lottery_decision_preserved_no_reroll',prior=priorlottery[int(c['ClubUID'])])
  else:
   oldtypes={e['proof']['subject_id']:e['proof']['ability_source']for e in group}
   for e in group:
    if e['proof']['ability_source']=='estimated_real_level_age_individual_spread_v2':e['proof']['ability_source']='estimated_source_league_and_age'
   decision=prep.assign_club_talent(int(c['ClubUID']),[e['proof']for e in group])
   for e in group:e['proof']['ability_source']=oldtypes[e['proof']['subject_id']]
  lottery.append(dict(club=c['ClubName'],**decision))
  for e in group:e['row']['PA']=e['proof']['pa']
 for l in loans:l['LoanShirt']=next(e['row']['SquadNumber']for e in entries if e['proof']['subject_id']==l['SubjectID'])
 assert len({e['proof']['TMID']for e in entries})==len(entries)
 for e in entries:
  assert 1<=e['row']['CA']<=e['row']['PA']<=200
  assert e['row']['ExistingID']<=0 or e['proof']['ability_source']=='reestimated_proven_legacy_project_v2' or(e['row']['CA']==int(byuid[e['row']['ExistingID']]['CA'])and e['row']['PA']==int(byuid[e['row']['ExistingID']]['PA']))
 sourcegaps=read(SRC/'roster-source-gaps.json')+deferred;protected|=gapuids
 coverage=[dict(ClubUID=int(c['ClubUID']),Club=c['ClubName'],Country=c['Country'],TEAM=int(c['TeamIndex']),DivisionIndex=int(c['DivisionIndex']),Confirmed=sum(i['PlayingClubIndex']==int(c['TeamIndex'])for i in idents),Goalkeepers=sum(e['proof']['playing_club']==int(c['TeamIndex'])and e['row']['PosGK']==20 for e in entries))for c in cm]
 for c in coverage:
  if c['Confirmed']<17 or not c['Goalkeepers']:
   protected.update(int(n['ID'])for n in native if int(n['ClubIndex'])==c['TEAM'])
 # Never invent technical proofs for projected new club families. Root integration must materialize then regenerate.
 nationalityrepairs={str(e['row']['ExistingID']):dict(expected_native_nation=byuid[e['row']['ExistingID']]['Nationality'],target_native_nation=e['row']['Nationality'],source_url=e['proof']['bio_source'])for e in entries if e['row']['ExistingID']>0 and byuid[e['row']['ExistingID']]['Nationality']!=e['row']['Nationality']}
 dobphases=[dict(UID=i['ExistingID'],ExpectedDOB=i['ExpectedDOB'],TargetDOB=i['TargetDOB'],Rule='one_explicit_19year_shift_from_verified_real_DOB',Source='https://www.transfermarkt.com/-/profil/spieler/'+next(e['proof']['TMID']for e in entries if e['proof']['subject_id']==i['SubjectID']))for i in idents if i['ExistingID']>0 and i['ExpectedDOB']!=i['TargetDOB']]
 dump(P/'native-DOB-phase-corrections.json',dobphases)
 writecsv(P/'native_players.csv',[e['row']for e in entries]);writecsv(P/'identities.csv',idents);writecsv(P/'loans.csv',loans);writecsv(P/'club_map.csv',cm)
 dump(P/'provenance.json',[e['proof']for e in entries]);dump(P/'deferred.json',deferred);dump(P/'source-gaps.json',sourcegaps);dump(P/'coverage.json',coverage);dump(P/'membership-reconciliation.json',membership);dump(P/'registry-reuse.json',reusedregistry);dump(P/'talent-lottery.json',lottery)
 stats=[]
 for country in ['England']:
  for level in [1,2,3,4,5,6]:
   es=[e for e in entries if core[e['proof']['playing_club_TMID']]['Country']==country and plans[e['proof']['playing_club_TMID']]['RealLevel']==level]
   if not es:continue
   ca=[e['row']['CA']for e in es];pa=[e['row']['PA']for e in es];new=[e for e in es if e['row']['ExistingID']<0]
   stats.append(dict(Country=country,RealLevel=level,Players=len(es),New=len(new),Preserved=len(es)-len(new),CAmin=min(ca),CAmean=round(statistics.mean(ca),2),CAstd=round(statistics.pstdev(ca),2),CAmax=max(ca),PAmin=min(pa),PAmean=round(statistics.mean(pa),2),PAmax=max(pa),PA150plus=sum(v>=150 for v in pa),PA180plus=sum(v>=180 for v in pa),UniqueCA=len(set(ca)),MeanDevelopmentGap=round(statistics.mean(p-c for p,c in zip(pa,ca)),2)))
 writecsv(P/'rating-distribution.csv',stats)
 classbytm={c['TMID']:c['Class']for c in classification};parts=[]
 for country in ['England']:
  for cls in sorted({c['Class']for c in classification}):
   es=[e for e in entries if core[e['proof']['playing_club_TMID']]['Country']==country and classbytm[e['proof']['TMID']]==cls]
   if not es:continue
   ca=[e['row']['CA']for e in es];pa=[e['row']['PA']for e in es]
   parts.append(dict(Country=country,RatingClass=cls,Players=len(es),CAmin=min(ca),CAmean=round(statistics.mean(ca),2),CAstd=round(statistics.pstdev(ca),2),CAmax=max(ca),PAmin=min(pa),PAmean=round(statistics.mean(pa),2),PAmax=max(pa),UniqueCA=len(set(ca)),MeanDevelopmentGap=round(statistics.mean(p-c for p,c in zip(pa,ca)),2),PA150plus=sum(v>=150 for v in pa),PA180plus=sum(v>=180 for v in pa)))
 writecsv(P/'rating-distribution-by-provenance.csv',parts)
 flat=[]
 for c in cm:
  es=[e for e in entries if e['proof']['playing_club']==int(c['TeamIndex'])and e['row']['ExistingID']>0]
  if not es:continue
  bc=Counter(int(byuid[e['row']['ExistingID']]['CA'])for e in es);ac=Counter(e['row']['CA']for e in es)
  flat.append(dict(ClubUID=c['ClubUID'],Club=c['ClubName'],Reused=len(es),MostCommonCA_before=bc.most_common(1)[0][0],CommonCount_before=bc.most_common(1)[0][1],MostCommonCA_after=ac.most_common(1)[0][0],CommonCount_after=ac.most_common(1)[0][1],LegacyReestimated=sum(e['proof']['ability_source']=='reestimated_proven_legacy_project_v2'for e in es),CredibleOrUnknownPreserved=sum(e['proof']['ability_source']!='reestimated_proven_legacy_project_v2'for e in es)))
 writecsv(P/'flat-reuse-before-after.csv',flat)
 pins={str(p.relative_to(P)):hashlib.sha256(p.read_bytes()).hexdigest()for p in P.rglob('*')if p.is_file()and p.name!='manifest.json'}
 m=dict(status='data_prepared_native_materialization_and_contract_proofs_pending',scope_id='england-20261114',stage='full_data_preparation_only',source=read(B/'manifest.json')['source'],source_hashes=read(B/'manifest.json')['source_hashes'],output=str(B/'roster-db'),output_database_created=False,prepared_hashes=pins,counts=dict(prepared=len(entries),reuse=len(used),new=sum(e['row']['ExistingID']<0 for e in entries),loans=len(loans),clubs=len(cm),actor_clubs=sum(c['Confirmed']>0 for c in coverage),deferred=len(deferred),source_gaps=len(sourcegaps),legacy_rating_repairs=len(ratingrepairs),legacy_CA_changed=sum(r['CA_before']!=r['CA_after']for r in ratingrepairs),legacy_PA_changed=sum(r['PA_before']!=r['PA_after']for r in ratingrepairs)),target_country_indices=[139,175],nationality_repairs=nationalityrepairs,dob_repairs={},duplicate_proofs={},duplicate_retire_uids=[],allow_replace_subject_loans=True,structural_only_club_uids=[c['ClubUID']for c in coverage if c['Confirmed']==0],protected_player_uids=sorted(protected-used),preserve_absent_uids=sorted(protected-used),target_club_uids=[int(c['ClubUID'])for c in cm],policy=dict(model_version=model.VERSION,preserve_credible_CA_PA_and_all_prior_talents=True,selective_proven_legacy_CA_PA_plan=True,source_seed_namespace='tm:stableSourceUID until immutable native allocation ledger exists',missing_players_not_forced=True,no_mandatory_buy=True,no_synthetic_loan_end=True,unknown_buy_fee=-1,personality_codec='verified_X17_no_full_rebuild'),pending_gates=['materialize finalpinned core+requiredownerTEAM families in private staging; independent inverse/readback/all_country_formgates','regenerate actual club_map and native contract-family/country proofs after materialization','root reviewed personality codec toolset build and pilot','scoped writer adapter preflight and full import; metadata publication only after readback'])
 dump(P/'manifest.json',m);print('PREPARED',m['counts'],flush=True);print('DEFERRED',Counter(x['Reason']for x in deferred),flush=True);print('STATS',stats,flush=True)
if __name__=='__main__':main()
