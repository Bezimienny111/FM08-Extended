from pathlib import Path
import sys,json,asyncio
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
import collect_sources_adapter as a
B=Path(__file__).resolve().parent
async def main():
 pending=a.read(B/'collected/feeder-unresolved-identities.json');evidence=a.read(B/'collected/feeder-search-evidence.json');lookup={x['Name']:x for x in evidence};cache=a.shared.Cache();out=[]
 async with a.Transfermarkt(timeout=30,max_concurrency=3,transport=cache) as tm:
  for c in pending:
   results=lookup.get(c['Name'],{}).get('Results',[])
   candidates=[x for x in results if x.get('country')==c['Country'] and not any(w in x.get('name','') for w in ['U19',' U21',' II',' III','Youth'])]
   for x in candidates[:3]:
    p=B/'sources/tm-clubs'/(str(x['id'])+'-profile.json')
    try:
     profile=await a.shared.get(tm,p,'club_profile',str(x['id']));out.append(dict(SourceEntity=c,ProviderResult=x,ProfileFile=str(p.relative_to(B)),Profile=profile));print('UNRESOLVED_PROFILE',x['id'],profile.get('name'),profile.get('official_name'),profile.get('league'),flush=True)
    except Exception as e:out.append(dict(SourceEntity=c,ProviderResult=x,Error=type(e).__name__+': '+str(e)))
 a.dump(B/'collected/feeder-candidate-profile-comparisons.json',out);a.dump(B/'collected/feeder-candidate-profile-capture.json',dict(new_calls=cache.calls,cache_hits=cache.hits,provider_stopped=cache.stopped,NativeUIDAllocated=False))
if __name__=='__main__':asyncio.run(main())
