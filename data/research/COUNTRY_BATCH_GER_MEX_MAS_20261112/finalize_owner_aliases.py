from pathlib import Path
from collections import Counter
import json,csv,sys,hashlib,importlib.util
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(n,x):(B/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
world={x['ClubUID']:x for x in read(B/'native-world-identities.json')};rs=read(B/'foreign-owner-aliases.json')
fix={'1091':982,'1496':1800030031,'200':1010,'610':992,'1037':404,'603':625,'667':872,'12275':2121}
proofs=[]
for c in rs:
 tid=c['CanonicalMainTMID']
 if tid not in fix:continue
 w=world[fix[tid]];nativecountry=138 if tid=='12275'else w['Country']
 if tid=='603':c['NativeCountryConventionNote']='Existing Cardiff FAMILY countryEngland139 is preserved for outside-batch owner; real locationWales retained separately; no duplicate Cardiff.'
 if tid=='1037':c['Name']='CF Universidad de Chile';c['ParentOwnerResolution']='source youth20062 mainClubId1037; use canonical senior404, never create U21 name as first team'
 c.update(NativeClubUID=w['ClubUID'],NativeTeamIndex=w['TeamIndex'],NativeFamilyIndex=w['FamilyIndex'],NativeCountryIndex=nativecountry,Decision='explicit_verified_full_identity_or_canonical_parent_owner',NativeNameWitness=w['Names'])
 if tid=='12275':c['IdentityEvidence']=['https://kolding-if.dk/klubben/klubbens-historie/'];c['NativeCountryRepairTo']=138
 proofs.append(dict(SourceTMID=c['SourceTMID'],CanonicalMainTMID=tid,ClubUID=w['ClubUID'],NativeNames=w['Names'],NativeCountryBefore=w['Country'],NativeCountryAfter=nativecountry,Proof=c.get('IdentityEvidence')or c['RawFile']))
dump('foreign-owner-aliases.json',rs)
keep=[p for p in read(B/'foreign-owner-plan.json')if p['TMID']not in fix]
k=world[2121];profile=B/'owner-source-profiles/12275.json'
profile.write_text(json.dumps(dict(id='12275',name='Kolding IF',official_name='Kolding Idraetsforening',short_name='Kolding IF',stadium={},stadium_name='',source='https://kolding-if.dk/klubben/klubbens-historie/',SourceType='official_identity_existing_native_owner_no_new_stadium_claim'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
keep.append(dict(TMID='12275',Name='Kolding IF',Country='Denmark',LeagueCountry='Denmark',NativeCountryIndex=138,RealLevel=1,DesiredDivision=k['CurrentDivision'],SourceCompetition='owner_only',NativeClubUID=2121,NativeTeamIndex=k['TeamIndex'],NativeFamilyIndex=k['FamilyIndex'],NativeParentUID=None,ParentTMID='',SourceCountryIndex=-1,NativeCountryRepairTo=138,YearFounded=1895,ExistingStadiumIndex=k['StadiumIndex'],IdentityDecision='reuse_official_KIF_continuity_not_KoldingFC928820',IdentityReason='OfficialKIF history1895/1900/eliteFC2001/Vejleproject/return2013; countryrepair on exact2121 only',IdentityEvidence=['https://kolding-if.dk/klubben/klubbens-historie/'],ProfileFile=str(profile),SugarDaddy=False,OwnerOnly=True,Role='loan_owner_only',PublicStadium={}))
dump('foreign-owner-plan.json',keep);dump('owner-identity-repairs.json',proofs)
cm=list(csv.DictReader((B/'club-map.csv').open(encoding='utf-8-sig',newline='')));nextuid=read(B/'club-UID-projection.json')['UIDrange'][1]+1;ti=max([int(x['TeamIndex'])for x in cm]+[w['TeamIndex']for w in world.values()])+1;fi=max([int(x['FamilyIndex'])for x in cm]+[w['FamilyIndex']for w in world.values()])+1;out=[]
for c in sorted(keep,key=lambda c:int(c['TMID'])):
 if c['NativeClubUID']:
  w=world[c['NativeClubUID']];u=w['ClubUID'];t=w['TeamIndex'];f=w['FamilyIndex'];kind='existing_native_owner_country_repair'
 else:u=nextuid;nextuid+=1;t=ti;ti+=1;f=fi;fi+=1;kind='projected_new_owner_family'
 out.append(dict(ClubName=c['Name'],ClubUID=u,TeamIndex=t,FamilyIndex=f,CountryIndex=c['NativeCountryIndex'],DivisionIndex=c['DesiredDivision'],Group='loan_owner_only',RealLeague=1,Country=c['Country'],TMID=c['TMID'],Kind=kind,ParentUID='',SourceParentTMID='',IdentityDecision=c['IdentityDecision'],ProjectionOnly=not bool(c['NativeClubUID'])))
with(B/'foreign-owner-map.csv').open('w',encoding='utf-8-sig',newline='')as f:w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
dump('foreign-owner-projection.json',dict(status='pinned_projection_not_native_materialization',rows=out))
dump('foreign-owner-finalization.json',dict(status='all149cachedowners_resolved_after_explicit_alias_review',new_owner_families=sum(not c['NativeClubUID']for c in keep),existing_owner_country_repairs=[2121],decisions=dict(Counter(c['Decision']for c in rs)),deferred_source_owners=[c['SourceTMID']for c in rs if c['Decision'].startswith('defer_')],no_network=True))
print('OWNERS_FINAL',len(rs),'new',sum(not c['NativeClubUID']for c in keep),'existingrepair',2121,'unresolved',[c['SourceTMID']for c in rs if c['Decision'].startswith('defer_')],flush=True)
