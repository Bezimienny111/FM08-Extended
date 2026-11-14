from pathlib import Path
from collections import Counter
import json,csv,hashlib,sys
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent;ROOT=Path('J:/FM08dev')
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,v):(B/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
draft=read(B/'club-plan-draft.json');world={x['ClubUID']:x for x in read(B/'native-world-identities.json')};peer=B/'identity-review-peer/club-identity-decisions.json';approval=read(B/'identity-review-peer/root-approval-receipt.json');assert approval['ApprovedPeerDecisionSHA256']==sha(peer)
root=B/'root-identity-review/club-identity-decisions.json';decisions={x['TMID']:dict(x,DecisionFile=str(peer))for x in read(peer)};decisions.update({x['TMID']:dict(x,DecisionFile=str(root))for x in read(root)})
plans=[];deferred=[]
for x in draft:
 x=dict(x);tid=x['TMID'];d=decisions.get(tid)
 if d:
  flag=d['Decision'];x['IdentityDecision']=flag;x['IdentityReason']=d['Reason'];x['IdentityEvidence'].append(d['DecisionFile']);uid=d.get('NativeClubUID')
  if flag.startswith('DEFER')or tid=='12275':
   deferred.append(dict(TMID=tid,Name=x['Name'],Reason='Kolding typedrole conversion deferred by root; preserve2121/1648/8540/928820 and actorUIDs'if tid=='12275'else d['Reason'],PreserveNativeUIDs=[2121,928820]if tid=='12275'else d.get('PreserveNativeUIDs',[]),SourceProfile=x['ProfileFile'],SourceRoster=x['RosterFile']));continue
  if flag.startswith('NEW'):uid=None
  x['NativeClubUID']=uid
  if tid=='52109':x['ParentTMID']='24420';x['RequiredNativeReserveKind']=3
  if tid=='46828':x['RealLevel']=6;x['SourceCompetition']='FIN_NELONEN_2026_CONFIRMED';x['MembershipEvidenceFile']=str(peer)
 if tid=='55564':
  deferred.append(dict(TMID=tid,Name=x['Name'],Reason='Unresolved current lower membership/identity in bounded feeder delta; no force research, preserve source/native candidates',PreserveNativeUIDs=[q['UID']for q in x['FreshCandidates']],SourceProfile=x['ProfileFile'],SourceRoster=x['RosterFile']));continue
 if tid=='24420':x['NativeClubUID']=None;x['IdentityDecision']='NEW_ROOT_APPROVED_UD_LOGRONES_PARENT';x['IdentityReason']='Root explicitly approves current UDLogrones parent as separate from historical CDLogrones1679';x['IdentityEvidence'].append(str(root))
 if tid=='60225':x['NativeClubUID']=None;x['IdentityDecision']='NEW_CURRENT_UD_OURENSE_NO_CD_HISTORY_TAKEOVER';x['IdentityReason']='Current distinct UDOurense source entity, no confirmed continuity into historical CDOurense1700; preserve historical club and current separate OurenseCF';x['PreserveNativeUIDs']=[1700]
 if tid=='55398':x['NativeClubUID']=4212292;x['IdentityDecision']='REUSE_DOCUMENTED_PONTE_OURENSE_ALIAS';x['IdentityReason']='Cached profile explicitly contains PonteOurenseCF/PuenteOurenseCF; native4212292 exactPonteOurenseCF, country170, kind0; reject generic cityCDOurense1700';x['PreserveNativeUIDs']=[1700]
 if tid=='8817':x['NativeClubUID']=856118;x['IdentityDecision']='REUSE_EXISTING_AJAX_SECOND_TEAM';x['IdentityReason']='SourceAjaxU21/Jong exactparent610, existing nativeAjax2 typedkind16/parent992; preserve secondteam rather than create independent duplicate'
 u=x.get('NativeClubUID');w=world.get(u,{})
 if u:
  assert w['TeamCountry']in[x['NativeCountryIndex'],-1],(tid,u,w['TeamCountry'],x['NativeCountryIndex'])
  x.update(NativeTeamIndex=w['TeamIndex'],NativeFamilyIndex=w['NameFamilyIndex']if w['NameFamilyIndex']is not None else w['TeamTailFamilyIndex'],NativeContractFamilyIndex=w['TeamTailFamilyIndex'],NativeContractFamilyUID=w['TeamTailFamilyUID'],NativeParentUID=w['ParentUID'],NativeTeamKind=w['NativeTeamKind'],ExistingStadiumIndex=w['StadiumIndex'],YearFounded=w['YearFounded'])
  x['NativeCountryRepairTo']=x['NativeCountryIndex']if w['TeamCountry']==-1 and d and d.get('CountryRepairRequired')else None
  if w['TeamCountry']==-1:assert x['NativeCountryRepairTo']is not None,(tid,'unknown-country reuse without explicit decision')
 else:
  x.update(NativeTeamIndex=None,NativeFamilyIndex=None,NativeContractFamilyIndex=None,NativeContractFamilyUID=None,NativeParentUID=None,NativeTeamKind=None,ExistingStadiumIndex=-1,NativeCountryRepairTo=None,YearFounded=0)
  if x['IdentityDecision']=='new_entity_candidate':x['IdentityDecision']='NEW_REAL_CURRENT_SOURCE_ENTITY_NO_VERIFIED_NATIVE_PREDECESSOR';x['IdentityReason']='Real current source club/name/country; no proved safe existing identity. Preserve all unrelated histories and unresolved old candidates.'
 x['NativeImportEligible']=True;x['SugarDaddy']=False;x['RegionalDivision']=None
 if x.get('RealLevel')is None:x['RealLevel']=3 if x['Country']=='Greece'else 5;x['LevelEvidence']='Bounded source delta official competition/profile; not current table rank'
 plans.append(x)
bytm={x['TMID']:x for x in plans};used=[x['NativeClubUID']for x in plans if x['NativeClubUID']];assert len(used)==len(set(used)),Counter(used)
for x in plans:
 if x['ParentTMID']:
  assert x['ParentTMID']in bytm or x['NativeParentUID'],('Missing parent',x['TMID'],x['ParentTMID'])
  if x['NativeClubUID']and x['ParentTMID']in bytm:assert bytm[x['ParentTMID']]['NativeClubUID']==x['NativeParentUID'],('native/source parent conflict',x['TMID'])
assert len(plans)==602 and len(deferred)==3
# Empty foreign-owner plan: unverified external identities are deferred; no invented lender family.
dump('club-plan.json',plans);dump('deferred-clubs.json',deferred);dump('foreign-owner-plan.json',[])
freeze=read(B/'source-freeze.json');dump('manifest.json',dict(status='CLUB_IDENTITY_PLAN_CLOSED_PROJECTION_AND_CSV_PENDING',source=freeze['frozen'],source_original=freeze['source'],source_hashes=freeze['hashes'],countries=['Netherlands','Spain','Greece','France','Finland','Denmark'],counts=dict(clubs=len(plans),reuse=len(used),new=len(plans)-len(used),deferred_clubs=len(deferred)),source_SI=True,source_new_career=True,source_season=False,NativeWrite=False))
dump('club-plan-proof-pins.json',{str(p):sha(p)for p in[peer,B/'identity-review-peer/root-approval-receipt.json',root,B/'local-identity-decisions.json',B/'club-plan-draft.json',B.parent/'competition-prep/source-cascade-plan.json']})
print('CLOSED_CLUB_PLAN',len(plans),'reuse',len(used),'new',len(plans)-len(used),'deferred',len(deferred))