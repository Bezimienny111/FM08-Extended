from pathlib import Path
import sys,json,hashlib,asyncio,re,datetime
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
import collect_staff as b
sys.path.insert(0,str(b.ROOT/'FM08-Database-Tools/scratch'))
import ss26prep_collect_20261110 as shared
from transfermarkt_api import Transfermarkt
B=b.B;shared.B=B;shared.S=B/'sources'
def identity(raw,p,entity):
 life=entity.get('lifeDates') or {};birth=life.get('dateOfBirth') or '';known=life.get('isDateOfBirthUnknown') is False and re.fullmatch(r'\d{4}-\d{2}-\d{2}',birth)
 return dict(externalPersonID='TM-coach:'+str(entity['id']),name=entity.get('name',''),DOB_real=birth if known else '',DOB_precision='day' if known else 'unknown',DOB_raw=birth,DOB_source_unknown_flag=life.get('isDateOfBirthUnknown'),nationality_raw=entity.get('nationalityDetails'),source_file=str(p.relative_to(b.ROOT)),source_sha256=b.sha(p),body_sha256=raw.get('sha256'),fetched_at=raw.get('fetched_at'),url=raw.get('url'),nativePersonUID_if_verified='',native_reuse_status='NOT_ATTEMPTED_REQUIRES_FULL_NATIVE_IDENTITY_PROOF')
async def main():
 rows=b.rows(B/'staff-report.csv');wanted={r['externalPersonID'].split(':',1)[1] for r in rows if r['externalPersonID'].startswith('TM-coach:') and r['role'] in ['head_coach','assistant_manager']};found={};rawdirs=list(b.R.glob('*/sources/tm-raw'))
 def load(p):
  try:
   raw=b.read(p);obj=json.loads(raw['body']);entities=obj.get('data',obj) if isinstance(obj,dict) else obj
   for e in entities if isinstance(entities,list) else []:
    if str(e.get('id')) in wanted:found[str(e['id'])]=identity(raw,p,e)
  except Exception:pass
 for pid in wanted:
  url='https://tmapi.transfermarkt.technology/coaches?ids%5B%5D='+pid;key=hashlib.sha256(('GET '+url).encode()).hexdigest()+'.json';hits=[d/key for d in rawdirs if (d/key).exists()]
  if hits:load(max(hits,key=lambda p:p.stat().st_mtime))
 missing=sorted(wanted-set(found));print('COACH_IDS',len(wanted),'already_cached',len(found),'new_metadata_needed',len(missing),flush=True)
 cache=shared.Cache();error=''
 try:
  async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache) as tm:
   for lo in range(0,len(missing),50):
    chunk=missing[lo:lo+50];p=B/'sources/coach-batches'/('batch-'+hashlib.sha256('|'.join(chunk).encode()).hexdigest()+'.json');p.parent.mkdir(parents=True,exist_ok=True)
    if not p.exists():
     data=await tm._client.coaches(chunk);shared.dump(p,data)
    print('COACH_BATCH',lo+len(chunk),'/',len(missing),'calls',cache.calls,'hits',cache.hits,flush=True)
 except Exception as e:error=type(e).__name__+': '+str(e);print('METADATA_ERROR',error,flush=True)
 for p in (B/'sources/tm-raw').glob('*.json'):
  try:
   z=b.read(p)
   if '/coaches?' in z.get('url',''):load(p)
  except Exception:pass
 b.dump('person-identities.json',found);b.write('person-identities.csv',[dict(v,nationality_raw=json.dumps(v['nationality_raw'],ensure_ascii=False)) for v in found.values()]);b.dump('identity-capture.json',dict(unique_coach_ids_wanted=len(wanted),found=len(found),DOB_complete=sum(bool(x['DOB_real']) for x in found.values()),new_metadata_calls=cache.calls,cache_hits=cache.hits,provider_stopped=cache.stopped,error=error,api_football_calls=0));print('IDENTITY_COMPLETE',len(found),flush=True)
if __name__=='__main__':asyncio.run(main())
