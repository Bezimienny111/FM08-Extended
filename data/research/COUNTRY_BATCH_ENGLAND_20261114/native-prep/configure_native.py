from pathlib import Path
from collections import Counter
import json,csv,sys,hashlib,struct,subprocess,copy
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent;S=B.parent
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
from create_italy_structure_i1_20261108 import load,languages,lang_sections
rd=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(n,v):(B/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def save(n,vs,fields=None):
 with(B/n).open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.DictWriter(f,fieldnames=fields or list(vs[0]));w.writeheader();w.writerows(vs)
assert not(B/'club-UID-projection.json').exists()
freeze=rd(B/'source-freeze.json');src=Path(freeze['frozen']);assert all(sha(src/k)==v for k,v in freeze['hashes'].items())
refs=S/'native-reference';ip=rd(refs/'club-identity-reference-plan-r2.json');op=rd(refs/'loan-owner-reference-plan-r2.json');ap=rd(refs/'allocation-reference-projection-r2.json')
assert sha(refs/'club-identity-reference-plan-r2.json')=='b4e7b1ca19203bcccbfcce8d8026f83d722b5734d5ffbe98bc742db8e98c6cf8'
assert sha(refs/'loan-owner-reference-plan-r2.json')=='35b0f2e9e21112e9b17f65f527e38edbe4a1a64542d62ffe113caaf0d1296bc3'
assert sha(refs/'allocation-reference-projection-r2.json')=='9ec633ecbd5eb0e6a0bc35711c48f389d693e73c4a5de0e2d15f106551ac9b06'
world={v['ClubUID']:v for v in rd(B/'native-world-identities.json')};records=rd(B/'native-structure.json')['records'];en,_=lang_sections(dict(languages((src/'lang_db.dat').read_bytes()))[8]);comp={v['uid']:i for i,v in enumerate(en['comp'])};backcomp={i:u for u,i in comp.items()};a=load(src,'server_db.dat')
before={str(v['ClubUID']):[struct.unpack_from('<i',a,v['Start']+p)[0]for p in [7,15,47]]for v in records};after=copy.deepcopy(before)
used=set(world)
for values in en.values():
 if isinstance(values,list):used.update(v['uid']for v in values if isinstance(v,dict)and 'uid'in v)
used.update(int(v['ID'])for v in csv.DictReader((B/'audit/players.csv').open(encoding='utf-8-sig')))
ti=max(v['TeamIndex']for v in world.values())+1;fi=len(en['club']);startti=ti;startfi=fi;uid=1800280001;plans=[];owners=[];maps=[];ownmaps=[];ledger=[];bytm={};facts={v['TMID']:v for v in rd(S/'collected-source-targets.json')}
assert len(facts)==164
for z in ip['Rows']:
 x=dict(facts[z['TMID']]);old=z['ReferenceNativeUID'];pf=Path(z['Profile']);assert sha(pf)==z['ProfileSHA256'];profile=rd(pf)
 cn=z['ProposedCountryForNewOnly']if old is None else world[old]['TeamCountry']
 if old is not None:
  w=world[old];assert w['NativeTeamKind']==0 and w['ParentUID']is None and w['TeamTailFamilyUID']==old and cn==z['ReferenceNativeCountryIndex'];assert w['TeamIndex']==z['ReferenceTEAMWitness']['TeamIndex'];t=w['TeamIndex'];f=w['TeamTailFamilyIndex'];u=old
 else:
  u=uid;uid+=1;assert u not in used;used.add(u);t=ti;ti+=1;f=fi;fi+=1
 x.update(LeagueCountry='England',Country='England',SourcePhysicalCountry='Wales'if z['SourcePhysicalCountryIndex']==175 else'England',NativeCountryIndex=cn,SourceCountryIndex=cn,NativeClubUID=old,NativeTeamIndex=t if old else None,NativeFamilyIndex=f if old else None,NativeContractFamilyIndex=f if old else None,NativeContractFamilyUID=old,NativeParentUID=None,NativeTeamKind=0,ExistingStadiumIndex=world[old]['StadiumIndex']if old else-1,ProfileFile=str(pf),RosterFile=str(S/x['RosterFile']),ParentTMID='',ReserveTeam=False,SourceNames=[n for n in [profile.get('name'),profile.get('official_name'),profile.get('short_name')]if n],IdentityDecision=z['Decision'],IdentityReason='reviewed_R2_then_fresh_X22_typed_family_validation',IdentityEvidence=[str(refs/'club-identity-reference-plan-r2.json'),z.get('OfficialContinuityURL')],PublicStadium=profile.get('stadium'),SugarDaddy=False,DesiredDivision=comp[x['TargetNativeCompetitionUID']],DesiredAlternative=-1,RegionalDivision=before[str(old)][2]if old else-1,NativeCountryRepairTo=None,YearFounded=int(str(profile.get('date_founded')or profile.get('year_founded')or'0')[:4])if str(profile.get('date_founded')or profile.get('year_founded')or'0')[:4].isdigit()else 0,NativeImportEligible=True)
 if old is None:x.update(ProjectedClubUID=u,ProjectedTeamIndex=t,ProjectedFamilyIndex=f)
 row=dict(ClubName=x['Name'],ClubUID=u,TeamIndex=t,FamilyIndex=f,CountryIndex=cn,DivisionIndex=x['DesiredDivision'],Group='England '+str(x['DesiredDivision']),RealLeague=x['RealLevel'],Country='England',TMID=x['TMID'],Kind='projected_new_first_team'if old is None else'existing_native_entity',ParentUID='',IdentityDecision=x['IdentityDecision'])
 maps.append(row);bytm[x['TMID']]=row;plans.append(x);ledger.append(dict(TMID=x['TMID'],ClubUID=u,TeamIndex=t,FamilyIndex=f,IsNew=old is None,NativeTeamKind=0,NativeParentUID=None,SourceParentTMID='',DesiredDivision=x['DesiredDivision'],DesiredAlternative=-1));after[str(u)]=[x['DesiredDivision'],-1,x['RegionalDivision']]
assert len(maps)==164 and sum(x['IsNew']for x in ledger)==9
# Preserve reference-edited historical TEAM identities and rederive every slot from COMP UID.
for e in ap['RawSlotEdits']:
 u=str(e['ClubUID']);slot=['Current','Alternate','Regional'].index(e['Slot']);assert backcomp.get(before[u][slot])==e['BeforeCOMPUID'],('source_English_slot_changed',u,e,before[u]);after[u][slot]=comp[e['AfterCOMPUID']]if e['AfterCOMPUID']is not None else-1
for u in ap['CeasedPredecessorUIDs']:after[str(u)][0:2]=[-1,-1]
# Fresh owner resolver uses exact R2 mainClub aliases, with no holding-company substitution.
owner_alias=[]
for z in op['Rows']:
 m=z['CanonicalMainTMID'];u=z['ReferenceNativeClubUID']
 if m in bytm:v=bytm[m];u=v['ClubUID'];country=v['CountryIndex'];fam=v['FamilyIndex']
 elif u is not None:
  w=world[u];assert w['NativeTeamKind']==0 and w['ParentUID']is None and w['TeamCountry']==z['NativeCountryIndex'];country=w['TeamCountry'];fam=w['TeamTailFamilyIndex']
 else:
  assert m=='47026'and z['SourceTMID']==m
  raw=next(Path(fn)for fn in op['RawIdentityPins']if '47026' in rd(fn).get('url',''));assert sha(raw)==op['RawIdentityPins'][str(raw)]
  data=json.loads(rd(raw)['body'])['data'];p=next(v for v in data if str(v['id'])==m);assert p['name']=='Fisher FC'and p['baseDetails']['mainClubId']==m
  pf=B/'Fisher-FC-profile-from-cached-SDK.json';pf.write_text(json.dumps(dict(id=m,name=p['name'],short_name=p['baseDetails']['shortName'],country='England',stadium={},SourceRawFile=str(raw),SourceRawSHA256=sha(raw)),indent=2)+'\n',encoding='utf-8')
  u=uid;uid+=1;assert u not in used;used.add(u);country=139;fam=fi;f=fi;fi+=1;t=ti;ti+=1
  x=dict(Country='England',Name='Fisher FC',TMID=m,RealLevel=8,Role='loan_owner_only',NativeClubUID=None,NativeCountryIndex=139,SourceCountryIndex=139,NativeParentUID=None,ParentTMID='',ProfileFile=str(pf),ProjectedClubUID=u,ProjectedTeamIndex=t,ProjectedFamilyIndex=f,ExistingStadiumIndex=-1,DesiredDivision=comp[1301432],DesiredAlternative=-1,RegionalDivision=-1,YearFounded=2009,IdentityDecision=z['Decision'],SugarDaddy=False)
  owners.append(x);v=dict(ClubName=x['Name'],ClubUID=u,TeamIndex=t,FamilyIndex=f,CountryIndex=139,DivisionIndex=x['DesiredDivision'],Group='England owner only',RealLeague=8,Country='England',TMID=m,Kind='projected_new_first_team',ParentUID='',IdentityDecision=z['Decision']);ownmaps.append(v);bytm[m]=v;after[str(u)]=[x['DesiredDivision'],-1,-1];ledger.append(dict(TMID=m,ClubUID=u,TeamIndex=t,FamilyIndex=f,IsNew=True,Role='loan_owner_only',NativeTeamKind=0,NativeParentUID=None,DesiredDivision=x['DesiredDivision'],DesiredAlternative=-1))
  
 owner_alias.append(dict(z,TMID=z['SourceTMID'],NativeClubUID=u,NativeCountryIndex=country,NativeContractFamilyIndex=fam,FutureFreshNativeRequired=False))
req=rd(S/'competition-prep/native-competition-requirements.json')['requirements'];checks=[]
for q in req:
 idx=comp[q['CompetitionUID']]
 for form in [0,1]:
  n=sum((v[0]if not form or v[1]<0 else v[1])==idx or v[2]==idx for v in after.values());mn=q['Form0Min']if not form else q['Form1DefaultMin'];mx=q['Form0Max']if not form else q['Form1DefaultMax'];ok=n>=mn and(mx is None or n<=mx);checks.append(dict(COMPUID=q['CompetitionUID'],Index=idx,Form=form,Count=n,Minimum=mn,Maximum=mx,Passed=ok));assert ok,checks[-1]
assert len(after)==len(before)+10 and len(checks)==32
save('club-map.csv',maps);save('foreign-owner-map.csv',ownmaps);dump('club-plan.json',plans);dump('foreign-owner-plan.json',owners);dump('foreign-owner-aliases.json',owner_alias);dump('structural-fallbacks.json',[]);dump('core-assignments.json',[dict(x,NativeClubUID=next(v['NativeClubUID']for v in plans if v['TMID']==x['TMID']),DesiredCompetitionUID=backcomp[x['DivisionIndex']],DesiredDivision=x['DivisionIndex'])for x in maps]);dump('club-UID-projection.json',dict(Status='PINNED_PROJECTION_NOT_MATERIALIZED',SourceNextTEAM=startti,SourceNextFamily=startfi,NextFreeTEAMindex=ti,NextFreeFamilyIndex=fi,NewTEAM=10,NewFAMILY=10,rows=ledger,PlanSHA256=sha(B/'club-plan.json')));dump('reserve-kind-overlay.json',dict(Status='NO_NEW_RESERVES_PRESERVE_EXISTING_ROLES',Rows=[],PlanSHA256=sha(B/'club-plan.json')));dump('allocation-raw-state.json',dict(Before=before,After=after));dump('allocation-projection.json',dict(Status='PROJECTION_PASS',Checks=checks,ReferenceR2SHA256=sha(refs/'allocation-reference-projection-r2.json'),NoOldReferenceOffsetsUsed=True));dump('manifest.json',dict(status='IDENTITIES_PROJECTED_AWAIT_PREPARED_ROSTERS',source=freeze['frozen'],source_original=freeze['source'],source_hashes=freeze['hashes'],countries=['England'],counts=dict(clubs=164,reuse=155,new_core=9,new_owner=1),source_season='USER_AUTHORIZED_WHILE_LONG_TEST_CONTINUES',NativeWrite=False,SugarDaddy=False))
print('READY core164 reuse155 new9+Fisher1 owners188 checks32PASS',flush=True)
