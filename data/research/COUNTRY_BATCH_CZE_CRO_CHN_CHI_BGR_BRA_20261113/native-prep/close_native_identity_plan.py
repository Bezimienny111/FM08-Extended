"""Close cached club/owner decisions. No allocation or native write."""
from pathlib import Path
from collections import Counter
import json,csv,hashlib,sys
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;S=B.parent;R=S.parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,v):
 p=B/n;text=json.dumps(v,ensure_ascii=False,indent=2)+'\n'
 if p.exists():assert p.read_text(encoding='utf-8')==text,('immutable content drift',str(p));return
 p.parent.mkdir(exist_ok=True,parents=True);p.write_text(text,encoding='utf-8')
w={x['ClubUID']:x for x in read(B/'native-world-identities.json')};draft=read(B/'club-plan-draft.json');review={x['TMID']:x for x in read(B/'identity-review/remaining-alias-venue-review.json')}
# Explicit full football names, geographic aliases and venue readback from the one cached batch.
reuse={'7020':130782,'18720':130788,'18076':130787,'23162':130785,'479':130859,'419':432,'9554':1300245,'552':446,'22558':661680,'34147':129852,'86486':7501930,'978':339,'210':324,'3876':301344,'15882':302144,'9141':301266,'1785':107232,'11931':301129,'52513':313251,'52517':301251,'33050':319115,'31428':301155,'7535':301284,'12602':303018,'32037':318913,'30489':301142,'21599':8832317,'27837':310392,'64925':309640,'40120':19051303}
defer={'521':[354,7500436,22012484],'19214':[7500417],'760':[347],'26535':[7500434],'36963':[319165],'76155':[8832346]}
# Distinct current physical clubs; never take histories solely from generic aliases or predecessor names.
new_overrides={'121518':[301235],'51851':[2105689,314235],'37474':[302141],'64918':[19005336],'52519':[311110,313190],'96026':[],'5752':[301157]}
physical={'521':7500436,'19214':7500417,'760':347,'26535':7500434,'36963':319165,'76155':8832346}
plans=[];deferred=[];decisions=[];fallback=[]
for src in draft:
 x=dict(src);t=x['TMID'];original=x['NativeClubUID'];evidence=list(x['IdentityEvidence']);evidence.extend([str(B/'identity-review/reuse223-raw-geo-audit.json'),str(B/'identity-review/remaining-alias-venue-review.json')]);u=original;reason=x['IdentityReason'];flag=x['IdentityDecision']
 if t in defer:
  d=dict(TMID=t,Name=x['Name'],Country=x['Country'],Decision='DEFER_IDENTITY_PRESERVE_SOURCE_AND_NATIVE',Reason='Two-source conflict budget is not renewed; continuity or location remains unresolved. No source-person import and no guessed history takeover.',PreserveNativeUIDs=defer[t],SourceProfile=x['ProfileFile'],SourceRoster=x['RosterFile'],SourceFactsPreserved=True,NoForcedResearch=True)
  deferred.append(d);v=w[physical[t]];assert v['TeamCountry']==x['NativeCountryIndex'] and v['NativeTeamKind']==0 and not v['ParentUID'];fallback.append(dict(LogicalKey='preserved-physical-'+str(v['ClubUID']),TMID=None,DeferredSourceTMID=t,NativeClubUID=v['ClubUID'],Name=v['Names'][0],Country=x['Country'],NativeCountryIndex=v['TeamCountry'],DesiredDivision=x['TargetNativeDivisionIndex'],DesiredAlternative=x.get('TargetNativeAlternativeDivisionIndex',-1),DesiredRegional=-1,DesiredCompetitionUID=x['TargetNativeCompetitionUID'],NoPersonImport=True,PreserveRosterAndFamily=True,PreserveNames=True,PreserveNativeUIDs=defer[t],Reason='Structural classic slot only, not a declaration of continuity with deferred source entity.',NativeWitness=v));decisions.append(d);continue
 if t in new_overrides:u=None;flag='NEW_REAL_CURRENT_ENTITY_PRESERVE_UNPROVEN_PREDECESSOR';reason='Current source identity retained as distinct; bounded cached evidence does not authorize takeover of historical candidates.';x['PreserveNativeUIDs']=new_overrides[t]
 elif t in reuse:
  u=reuse[t];flag='REUSE_EXPLICIT_CACHED_FULL_NAME_GEO_VENUE';reason='Closed one-batch native/source identity witness: full football name and locality/venue, distinct entity and known country; explicit corrected alias, never nickname alone.'
  if t=='978':reason='CR Vasco da Gama Rio: native339 / Rio de Janeiro / Sao Januario. Reject prior wrong AD Vasco AC104982, preserve its 9 historical players; 2 carried owners deferred separately.';x['PreserveNativeUIDs']=[104982]
  if t=='52513':reason='Clube Sociedade Esportiva at Palmeira dos Indios/Juca Sampaio matches313251; reject generic CSE310905.';x['PreserveNativeUIDs']=[310905]
  if t=='52517':reason='AA Portuguesa Rio: raw current Rio de Janeiro and Luso Brasileiro match301251; preserve Santos107224, Sao Paulo333 and Londrina301222.';x['PreserveNativeUIDs']=[107224,333,301222]
  if t=='27837':reason='Cached source historical Uniclinic AC, native CT Uniclinic310392 / Fortaleza, country189; current Atletico Cearense identity retained.'
 if u:
  z=w[u];assert z['TeamCountry']in[x['NativeCountryIndex'],-1],(t,u,'country');assert bool(z['ParentUID'])==bool(x['ParentTMID']),(t,u,'native type')
  x.update(NativeClubUID=u,NativeTeamIndex=z['TeamIndex'],NativeFamilyIndex=z['NameFamilyIndex'] if z['NameFamilyIndex'] is not None else z['TeamTailFamilyIndex'],NativeContractFamilyIndex=z['TeamTailFamilyIndex'],NativeContractFamilyUID=z['TeamTailFamilyUID'],NativeParentUID=z['ParentUID'],NativeTeamKind=z['NativeTeamKind'],ExistingStadiumIndex=z['StadiumIndex'],YearFounded=z['YearFounded'],NativeCountryRepairTo=x['NativeCountryIndex'] if z['TeamCountry']==-1 else None)
  if z['TeamCountry']==-1:assert t in ['22558','34147','86486','40120'];reason+=' Explicit country repair from source exact legal/football identity + locality/country; original country=-1, never overwrite known foreign country.'
 else:
  flag='NEW_REAL_CURRENT_ENTITY_PRESERVE_UNPROVEN_PREDECESSOR';reason='Closed current real source first/reserve identity; no confirmed safe native predecessor after full cached alias/venue review. Preserve every historical candidate.'
  x.update(NativeClubUID=None,NativeTeamIndex=None,NativeFamilyIndex=None,NativeContractFamilyIndex=None,NativeContractFamilyUID=None,NativeParentUID=None,NativeTeamKind=None,ExistingStadiumIndex=-1,NativeCountryRepairTo=None,YearFounded=0)
  x['PreserveNativeUIDs']=sorted(set(x.get('PreserveNativeUIDs',[])+[q['UID']for q in x['FreshCandidates']]))
 x.update(IdentityDecision=flag,IdentityReason=reason,IdentityEvidence=list(dict.fromkeys(evidence)),NativeImportEligible=True,SugarDaddy=False,DesiredDivision=x['TargetNativeDivisionIndex'],DesiredAlternative=x.get('TargetNativeAlternativeDivisionIndex',-1),RegionalDivision=-1)
 if x['ParentTMID'] and not x['NativeClubUID']:
  x['RequiredNativeReserveKind']=15 if x['Country']=='Bulgaria'else 3
  x['ReserveKindEvidence']='9 existing Bulgaria linked second teams kind15 in frozen world'if x['Country']=='Bulgaria'else'Project classic B-team role3, existing Czech/Spanish B role3 schema; no conversion of historical Croatian TEAM'
 plans.append(x);decisions.append(dict(TMID=t,Name=x['Name'],Decision=flag,NativeClubUID=u,Reason=reason,SourceProfileSHA256=sha(Path(x['ProfileFile'])),PreserveNativeUIDs=x.get('PreserveNativeUIDs',[]),NativeCountryRepairTo=x['NativeCountryRepairTo']))
bytm={x['TMID']:x for x in plans};used=[x['NativeClubUID']for x in plans if x['NativeClubUID']];assert len(plans)==338 and len(deferred)==6 and len(set(used))==len(used)
for x in plans:
 if x['ParentTMID']:
  p=bytm[x['ParentTMID']];assert x['DesiredDivision']!=p['DesiredDivision'];assert not x['NativeClubUID']or p['NativeClubUID']==x['NativeParentUID']
assert len({x['NativeClubUID']for x in fallback}|set(used))==len(fallback)+len(used)
# Reuse prior verified owners and full distinct raw names; unresolved actors are deferred, no lender creation.
alias=[];worldnames={u:' | '.join(x['Names'])for u,x in w.items()}
for old in read(B/'foreign-owner-aliases-draft.json'):
 a=dict(old);main=a['CanonicalMainTMID']
 if main in bytm:a.update(Decision='within_core_final_identity_allocation_pending'if bytm[main]['NativeClubUID']is None else'within_core_final_verified_identity',NativeClubUID=bytm[main]['NativeClubUID'])
 elif main in defer:a.update(Decision='defer_core_identity_no_fiction_owner_transfer',NativeClubUID=None)
 elif main in ['56221','45457']:a.update(Decision='defer_unsafe_generic_alias_or_unproved_successor',NativeClubUID=None)
 elif a.get('NativeClubUID'):
  z=w[a['NativeClubUID']];assert z['TeamCountry']==a['NativeCountryIndex']and not z['ParentUID'];a['IdentityEvidence']='existing pinned prior exact TMID registry, or distinct full current football name/country in cached raw'
 else:a.update(Decision='defer_unresolved_external_owner_no_fiction_transfer',NativeClubUID=None)
 a['NativeWrite']=False;alias.append(a)
# Vasco carried assignments are out of core: preserve this import, retain exact future repair scope.
carried=[];native=list(csv.DictReader((B/'audit/players.csv').open(encoding='utf-8-sig')));byuid={int(x['ID']):x for x in native}
for folder,tmid,uid in [('POLAND_GAPS_IMPORT_PACKAGE_20261111','1083962',1616007393),('COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep','462977',1616005011)]:
 fp=R/folder/'prepared/provenance.json';pr=next(x for x in read(fp)if x.get('TMID')==tmid);n=byuid[uid];assert int(n['ClubIndex'])==2571 and pr['owner_TMID']=='978'and pr['owner_club']==2571
 carried.append(dict(Status='DEFERRED_CARRIED_OWNER_FIX_PRESERVE_THIS_IMPORT',TMID=tmid,UID=uid,Name=pr['name'],ExpectedDOB=n['BirthDate'],WrongOwnerTEAM=2571,WrongFamily=2372,WrongClubUID=104982,CorrectOwnerTEAM=306,CorrectFamily=214,CorrectClubUID=339,PlayingTEAM=pr['playing_club'],SourceProvenance=str(fp),SourceProvenanceSHA256=sha(fp),PlayerRaw=pr['PlayerRaw'],HistoryRaw=pr['HistoryRaw'],RequiredFutureScope=['PERSON owner TEAM','main contract FAMILY','loan owner FAMILY/TEAM','owner roster membership'],BorrowerDatesRatingsAttributesPersonalityPreserved=True))
for name,value in [('club-plan.json',plans),('deferred-clubs.json',deferred),('identity-review/final-identity-decisions.json',decisions),('structural-fallbacks.json',fallback),('foreign-owner-aliases.json',alias),('foreign-owner-plan.json',[]),('carried-owner-fixes-deferred.json',carried)]:dump(name,value)
assign=[dict(TMID=x['TMID'],Name=x['Name'],Country=x['Country'],NativeClubUID=x['NativeClubUID'],DesiredDivision=x['DesiredDivision'],DesiredAlternative=x['DesiredAlternative'],DesiredRegional=-1,DesiredCompetitionUID=next(z['uid']for z in read(B/'competition-catalog.json')if z['index']==x['DesiredDivision']),SourceParentTMID=x['ParentTMID'],RequiredNativeReserveKind=x.get('RequiredNativeReserveKind'),PreserveNativeKind=x.get('NativeTeamKind'),Reason=x['ClassicPlacementReason'])for x in plans]
dump('core-assignments.json',assign)
freeze=read(B/'source-freeze.json');counts=dict(clubs=len(plans),reuse=len(used),new=len(plans)-len(used),deferred_clubs=6,physical_fallbacks=6)
dump('manifest.json',dict(status='CLOSED_CLUB_OWNER_SOURCE_ASSIGNMENTS_AWAIT_ROOT_REVIEW_AND_UID_ALLOCATION',source=freeze['frozen'],source_original=freeze['source'],source_hashes=freeze['hashes'],countries=sorted({x['Country']for x in plans}),counts=counts,source_SI=True,source_new_career=True,source_season=False,NativeWrite=False,UIDAllocation=False,SugarDaddy=False))
paths=[B/n for n in ['club-plan-draft.json','identity-review/reuse223-raw-geo-audit.json','identity-review/reuse223-new-review-exceptions.json','identity-review/additional-local-venue-witnesses.json','identity-review/cache-witnesses.json','identity-review/remaining-alias-venue-review.json','club-plan.json','deferred-clubs.json','identity-review/final-identity-decisions.json','structural-fallbacks.json','foreign-owner-aliases.json','foreign-owner-plan.json','core-assignments.json','carried-owner-fixes-deferred.json']]
dump('identity-plan-closed.json',dict(Status='CLOSED_IMMUTABLE_PLAN_ROOT_REVIEW_PENDING',Counts=counts,SourceScope344=344,ClosedSourceSlots344=len(plans)+len(fallback),Owners=Counter(a['Decision']for a in alias),AdditionalNetworkRequests=0,ConflictBudgetNotReset=True,Allocation=False,NativeWrite=False,Pins={str(p):sha(p)for p in paths}))
print('CLOSED',counts);print('PINS',sha(B/'identity-plan-closed.json'),sha(B/'club-plan.json'),sha(B/'structural-fallbacks.json'));print('OWNERS',Counter(a['Decision']for a in alias))
