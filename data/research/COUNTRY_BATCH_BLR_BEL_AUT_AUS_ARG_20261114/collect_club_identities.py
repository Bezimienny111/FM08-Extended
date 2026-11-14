"""Club-only identity metadata through the same shared cache/get, before detailed player rosters."""
from pathlib import Path
import sys,json,asyncio,hashlib,datetime,collections,re
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;ROOT=B.parents[3];sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
import ss26prep_collect_20261110 as shared
from transfermarkt_api import Transfermarkt
shared.B=B;shared.S=B/'sources';read=shared.read;dump=shared.dump

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
async def main(country):
 primary={'Belarus':['WER1','WER2'],'Belgium':['BE1','BE2','BE3V','BE3A'],'Austria':['A1','A2','ATRO','ARLS','RLNA','RLWA'],'Australia':['AUS1'],'Argentina':['ARG1','ARGC','ARG2']}
 targets=[x for x in read(B/'competition-prep/source-targets-bootstrap.json') if x['Country']==country and any(c in primary[country] for c in x['Competitions'])]
 if len(sys.argv)>2:targets=read(B/sys.argv[2])
 cache=shared.Cache();slug=country.replace(' ','-')+('-supplement' if len(sys.argv)>2 else '');out=B/'competition-prep'/('club-profiles-'+slug+'.json')
 async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache) as tm:
  async def one(c):
   try:
    file=B/'sources/tm-clubs'/(str(c['TMID'])+'-profile.json');v=await shared.get(tm,file,'club_profile',str(c['TMID']));c.update(ProfileFile=str(file.relative_to(B)),ClubProfileFetched=True)
   except Exception as e:c['IdentityFetchError']=type(e).__name__+':'+str(e)
  for i in range(0,len(targets),3):
   await asyncio.gather(*(one(c) for c in targets[i:i+3]));dump(out,targets)
   if cache.stopped:break
   print('IDENTITY_METADATA',country,min(i+3,len(targets)),len(targets),flush=True)
 raw={};refs={}
 for file in (B/'sources/tm-raw').glob('*.json'):
  x=read(file);url=x.get('url','')
  if '/clubs?' not in url and not re.search(r'/club/\d+$',url):continue
  d=json.loads(x['body']).get('data');d=d if isinstance(d,list) else [d] if isinstance(d,dict) else []
  for v in d:
   tid=str(v.get('id',''))
   if tid not in refs or x['fetched_at']>refs[tid]['fetched_at']:
    raw[tid]=v;refs[tid]=dict(URL=url,RawFile=str(file.relative_to(B)),BodySHA256=x['sha256'],FileSHA256=sha(file),fetched_at=x['fetched_at'])
 ids=[]
 for c in targets:
  v=raw.get(str(c['TMID']),{});base=v.get('baseDetails') or {};mother=str(base.get('mainClubId') or '');parent=mother if mother and mother!=str(c['TMID']) else None
  ids.append(dict(TMID=c['TMID'],Name=c['Name'],Country=country,ProfileFile=c.get('ProfileFile'),SourceClubTypeID=base.get('clubTypeId'),SourceCountryID=base.get('countryId'),MainClubID=mother or None,ParentTMID=parent,LegalSuperiorClubID=base.get('superiorClubId'),RawName=v.get('name'),SourceRef=refs.get(str(c['TMID'])),IdentityStatus='SOURCE_IDENTITY_RAW_PRESENT' if v else 'PENDING_RAW_IDENTITY',NativeUIDAllocated=False))
 dump(B/'competition-prep'/('club-identities-'+slug+'.json'),ids);dump(B/'competition-prep'/('club-profile-capture-'+slug+'.json'),dict(NewCalls=cache.calls,CacheHits=cache.hits,Stopped=cache.stopped,Profiles=sum(c.get('ClubProfileFetched',False) for c in targets),DetailedPlayerRostersFetched=False,AtUTC=datetime.datetime.now(datetime.timezone.utc).isoformat()))
 print('IDENTITIES_SAVED',country,len(ids),'parents',sum(bool(x['ParentTMID']) for x in ids),'gaps',sum(x['SourceRef'] is None for x in ids),flush=True)
 if cache.stopped:raise RuntimeError('Provider stopped; no retries/bypass')
if __name__=='__main__':asyncio.run(main(sys.argv[1]))

