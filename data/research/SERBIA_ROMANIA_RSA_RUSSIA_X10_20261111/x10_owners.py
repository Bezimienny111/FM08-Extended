"""Bounded foreign-loan-owner resolution using cached raw identities and fresh native maps."""
from x10_pipeline import *
import csv,re
from collections import Counter
from ss26prep_analyze_20261110 import key
from batch_sweden_switzerland_x3_20261109 import load,languages,lang_sections
def owners():
 world=read(B/'native-world-identities.json');targets=read(B/'source-targets.json');facts=read(B/'roster-facts.json');bytid={c['TMID']:c for c in targets};rawclubs={};tmcountries={}
 for p in(S/'tm-raw').glob('*.json'):
  x=read(p)
  if x['status']!=200:continue
  z=json.loads(x['body']).get('data');url=x['url']
  if url.endswith('/attributes')and isinstance(z,dict):tmcountries.update({str(c['id']):c['name']for c in z.get('countries',[])})
  elif '/clubs?'in url and isinstance(z,list):
   for c in z:rawclubs[str(c['id'])]=dict(c,RawFile=str(p.relative_to(B)))
 src=Path(read(B/'manifest.json')['source']);en,_=lang_sections(dict(languages((src/'lang_db.dat').read_bytes()))[8]);nations={key(n):i for i,v in enumerate(en['nation'])for n in v['names']if n}
 nation_alias={'Türkiye':'Turkey','Czechia':'Czech Republic','Korea, South':'South Korea','Korea, North':'North Korea','The Gambia':'The Gambia','Gambia':'The Gambia','United States':'USA','United States of America':'USA','Bosnia-Herzegovina':'Bosnia and Herzegovina','Bosnia & Herzegovina':'Bosnia and Herzegovina','North Macedonia':'FYR of Macedonia','Congo DR':'Democratic Republic of Congo','DR Congo':'Democratic Republic of Congo','Korea, DPR':'North Korea','Côte d\'Ivoire':'Ivory Coast','Eswatini':'Swaziland'}
 prior={}
 for fp in R.glob('*/club-map.csv'):
  for c in csv.DictReader(fp.open(encoding='utf-8-sig')):
   if c.get('TMID')and c.get('ClubUID'):prior.setdefault(c['TMID'],set()).add(int(c['ClubUID']))
 resolution=[];missing=[]
 ownerids=sorted({f['OwnerTMID']for f in facts if f['AcceptedFactCandidate']and f['Loan']})
 for tid in ownerids:
  r=rawclubs.get(tid,{});base=r.get('baseDetails')or{};main=str(base.get('mainClubId')or tid)
  if main in ['0','None']:main=tid
  mother=rawclubs.get(main,r);mb=mother.get('baseDetails')or{};cn=tmcountries.get(str(mb.get('countryId')or base.get('countryId')));ni=nations.get(key(nation_alias.get(cn,cn)))if cn else None
  labels=[mother.get('name'),mb.get('shortName')];keys={key(n)for n in labels if n}
  candidates=[c for c in world if c['Country']==ni and not c['ParentUID']and any(key(n)in keys for n in c['Names'])]if ni is not None else[]
  puids=prior.get(main,set());pre=[c for c in world if c['ClubUID']in puids and (c['Country']==ni or ni is None)]
  uid=None
  if main in bytid:reason='within_core_batch'
  elif len(pre)==1:uid=pre[0]['ClubUID'];ni=pre[0]['Country'];reason='previous_verified_TM_registry'
  elif len(candidates)==1:uid=candidates[0]['ClubUID'];reason='exact_native_name_and_country'
  elif ni is not None and mother.get('name')and not candidates:reason='new_missing_foreign_owner_pending_profile'
  else:reason='defer_unresolved_owner';missing.append(tid)
  resolution.append(dict(SourceTMID=tid,CanonicalMainTMID=main,Name=mother.get('name')or r.get('name'),Country=cn,NativeCountryIndex=ni,NativeClubUID=uid,Decision=reason,WithinCoreBatch=main in bytid,RawFile=mother.get('RawFile'),SourceNames=labels,NativeCandidates=[dict(ClubUID=c['ClubUID'],Names=c['Names'])for c in candidates]))
 dump(B/'foreign-owner-resolution-draft.json',resolution)
 print('OWNERS',len(resolution),Counter(c['Decision']for c in resolution),'missing',missing,flush=True)
 for c in resolution:
  if c['Decision']not in ['within_core_batch','previous_verified_TM_registry','exact_native_name_and_country']:print('OWNER_REVIEW',c['SourceTMID'],c['CanonicalMainTMID'],c['Name'],c['Country'],c['NativeCountryIndex'],c['Decision'],[(v['ClubUID'],v['Names'][:1])for v in c['NativeCandidates']],flush=True)

async def finalize():
 from collections import Counter
 resolution=read(B/'foreign-owner-resolution-draft.json');world={c['ClubUID']:c for c in read(B/'native-world-identities.json')}
 aliases={'10957':12004628,'11648':423,'15300':477907,'4441':5603913,'605':969,'7732':135427,'1091':982}
 plans=[];seen=set()
 for c in resolution:
  main=c['CanonicalMainTMID']
  if main in aliases:
   uid=aliases[main];w=world[uid];assert w['Country']==c['NativeCountryIndex']
   c.update(NativeClubUID=uid,Decision='reuse_verified_historical_city_name_alias',AliasEvidence=dict(source_name=c['Name'],native_names=w['Names'],raw=c['RawFile']))
  if main=='33966':
   c.update(NativeClubUID=None,Decision='defer_inactive_owner_contract_rights_unresolved',OwnerDeferralReason='PolitehnicaIasi withdrew2026; do not create a fictional active lender from stale loan labels')
  if c['Decision']=='new_missing_foreign_owner_pending_profile'and main not in seen:
   seen.add(main);plans.append(dict(TMID=main,Name=c['Name'],Country=c['Country'],LeagueCountry=c['Country'],NativeCountryIndex=c['NativeCountryIndex'],RealLevel=1,DesiredDivision=-1,SourceCompetition='owner_only',IdentityDecision='new_missing_native_owner_family',NativeClubUID=None,ParentTMID='',YearFounded=0,IdentityReason='Real owner confirmed by cached active-loan transfer and country; no safe native entity, preserve other club histories',IdentityEvidence=['https://www.transfermarkt.com/-/startseite/verein/'+main,c['RawFile']],ProfileFile='sources/tm-clubs/'+main+'-profile.json',SugarDaddy=False,OwnerOnly=True,Role='loan_owner_only'))
 cache=col.Cache()
 async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache)as tm:
  for c in plans:
   z=await col.get(tm,B/c['ProfileFile'],'club_profile',c['TMID']);c['PublicStadium']=z.get('stadium')or{};c['OfficialName']=z.get('official_name');print('NEWOWNER',c['TMID'],z.get('name'),flush=True)
 dump(B/'foreign-owner-plan.json',plans);dump(B/'foreign-owner-aliases.json',resolution)
 facts=read(B/'roster-facts.json');gaps=read(B/'source-gaps.json');deferred={c['SourceTMID']:c for c in resolution if c['Decision'].startswith('defer_')}
 for f in facts:
  if f['AcceptedFactCandidate']and f['Loan']and f['OwnerTMID']in deferred:
   f['AcceptedFactCandidate']=False;f['OwnershipDeferred']=True;f['OwnerResolution']=deferred[f['OwnerTMID']]['Decision'];gaps.append(dict(club=f['ClubName'],name=f['Name'],TMID=f['TMID'],reason='loan_owner_contract_rights_unresolved_deferred',owner=f['OwnerTMID']))
 dump(B/'roster-facts.json',facts);dump(B/'source-gaps.json',gaps)
 dump(B/'foreign-owner-finalization.json',dict(new_families=len(plans),owner_decisions=dict(Counter(c['Decision']for c in resolution)),deferred_owners=list(deferred),new_profiles_calls=cache.calls,cache_hits=cache.hits,source_facts_deferred=sum(bool(f.get('OwnershipDeferred'))for f in facts)))
 print('OWNERFINAL',len(plans),Counter(c['Decision']for c in resolution),'deferredfacts',sum(bool(f.get('OwnershipDeferred'))for f in facts),flush=True)

if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='finalize':asyncio.run(finalize())
 else:owners()

