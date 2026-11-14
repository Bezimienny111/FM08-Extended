"""One configured feeder delta through the same SDK/cache and roster adapter; source identities stay pending."""
from pathlib import Path
import sys,json,asyncio,unicodedata,re,collections
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
import collect_sources_adapter as adapter
B=Path(__file__).resolve().parent;read=adapter.read;dump=adapter.dump

def norm(t):return re.sub('[^a-z0-9]','',''.join(c for c in unicodedata.normalize('NFKD',str(t).casefold().replace('ø','o').replace('å','aa')) if not unicodedata.combining(c)))
async def main():
 paths=[B/'competition-prep/greece-extra4-club-targets.json',B/'competition-prep/denmark-extra12-club-candidates.json',B/'competition-prep/finland-lower6-profile-candidates.json']
 candidates=[];pins={}
 for p in paths:
  if p.exists():
   values=read(p);assert isinstance(values,list);candidates.extend(dict(v,DeltaSourceFile=str(p.relative_to(B))) for v in values);pins[str(p.relative_to(B))]=adapter.sha(p)
 unresolved=[];searches=[];cache=adapter.shared.Cache()
 async with adapter.Transfermarkt(timeout=30,max_concurrency=3,transport=cache) as tm:
  for c in candidates:
   if c.get('TMID'):continue
   query=c['Name'];p=B/'sources/tm-search'/('feeder-'+c['Country']+'-'+norm(query)+'.json')
   try:
    data=await adapter.shared.get(tm,p,'search_clubs',query);results=data.get('results',[]);hits=[r for r in results if norm(r.get('name',''))==norm(query) and r.get('country') in [c['Country'],'Dänemark','Denmark','Finland','Finnland','Greece','Griechenland']]
    searches.append(dict(Name=query,Country=c['Country'],File=str(p.relative_to(B)),Results=results,ExactCountryNameHits=hits))
    if len(hits)==1:c['TMID']=str(hits[0]['id']);c['TMIDResolution']='unique_exact_source_name_and_country_search; official_DBUTeam_continuity still pending';c['SearchEvidenceFile']=str(p.relative_to(B))
    else:
     senior=[r for r in results if r.get('country')==c['Country'] and not re.search(r'(?:\bU\d+\b|\bII\b|\bIII\b|\bYouth\b)',r.get('name',''),re.I)]
     if len(senior)==1:
      c['TMID']=str(senior[0]['id']);c['TMIDResolution']='unique_non_youth_search_RESULT_PROFILE_CANDIDATE_ONLY_NOT_CONFIRMED_OfficialEntity';c['SearchEvidenceFile']=str(p.relative_to(B));c['ProviderCandidateName']=senior[0]['name']
     else:
      unresolved.append(dict(c,Status='SOURCE_IDENTITY_PENDING_NO_UNIQUE_EXACT_COUNTRY_NAME_MATCH',SearchFile=str(p.relative_to(B))));print('FEEDER_SEARCH_PENDING',query,[(r.get('id'),r.get('name'),r.get('country')) for r in results[:6]],flush=True)
   except Exception as e:
    unresolved.append(dict(c,Status='SOURCE_SEARCH_ERROR',Error=type(e).__name__+': '+str(e)));print('FEEDER_SEARCH_ERROR',query,str(e)[:120],flush=True)
    if cache.stopped:break
 dump(B/'collected/feeder-search-evidence.json',searches);dump(B/'collected/feeder-unresolved-identities.json',unresolved)
 targets=read(B/'source-targets.json');existing={str(c['TMID']):c for c in targets};start=len(targets);added=[]
 for c in candidates:
  if not c.get('TMID'):continue
  tid=str(c['TMID'])
  if tid in existing:continue
  c=dict(c,TMID=tid,RealSeason='2026' if c['Country']=='Finland' else '26/27',APISeason='2025' if c['Country']=='Finland' else '2026',RealLevel=c.get('RealLevel',5),Role='feeder_identity_candidate_source_only',ClubIdentityPending=True,NativeImportEligible=False,SourceScope='extra_feeder_delta_NOT_main584',Competitions=c.get('Competitions',[]))
  targets.append(c);existing[tid]=c;added.append(c)
 dump(B/'source-targets.json',targets);dump(B/'collected/feeder-delta-config.json',dict(main_base_clubs=584,delta_before=start-584,added=len(added),total_source_targets=len(targets),candidate_files=pins,new_search_calls=cache.calls,cache_hits=cache.hits,provider_stopped=cache.stopped,unresolved=len(unresolved),added_targets=added,NativeUIDAllocated=False,DatabaseWritten=False))
 print('FEEDER_DELTA_CONFIG',start,len(targets),'added',len(added),'unresolved',len(unresolved),flush=True)
 if start<len(targets) and not cache.stopped:
  sys.argv=['collect_sources_adapter.py','rosters',str(start),str(len(targets))];await adapter.rosters()
if __name__=='__main__':asyncio.run(main())

