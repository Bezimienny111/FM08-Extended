"""Reuse shared verified Transfermarkt stadium identities by three bounded TEAM references."""
from x10_pipeline import *
import csv,struct,zlib
from collections import defaultdict
from create_italy_structure_i1_20261108 import load
def main():
 src=Path(read(B/'manifest.json')['source']);dest=B/'structure-db';sr=read(B/'structure-report.json');before=pins(dest);assert before==sr['output_hashes']
 assert not(B/'shared-stadium-reuse.json').exists()
 plans=read(B/'club-plan.json')+read(B/'foreign-owner-plan.json');bytm={x['TMID']:x for x in plans};cm=list(csv.DictReader((B/'club-map.csv').open(encoding='utf-8-sig')))+list(csv.DictReader((B/'foreign-owner-map.csv').open(encoding='utf-8-sig')));tid={int(x['ClubUID']):x['TMID']for x in cm};groups=defaultdict(list)
 for v in sr['venue_assignments']:
  c=bytm[tid[v['ClubUID']]];stad=c.get('PublicStadium')or{};sid=stad.get('id')
  if sid:groups[(sid,c['NativeCountryIndex'])].append(v)
 data=load(dest,'server_db.dat');out=bytearray(data);records={x['ClubUID']:x for x in read(B/'native-structure-after.json')['records']};patches=[];shared=[]
 for (sid,country),rows in groups.items():
  if len({x['StadiumIndex']for x in rows})<2:continue
  canonical=min(x['StadiumIndex']for x in rows);shared.append(dict(SourceStadiumID=sid,CountryIndex=country,CanonicalStadiumIndex=canonical,ClubUIDs=[v['ClubUID']for v in rows],Evidence='Same positive Transfermarkt stadium ID in cached club profiles, physical country consistent'))
  for v in rows:
   if v['StadiumIndex']==canonical:continue
   r=records[v['ClubUID']];at=r['Start']+19;old=struct.unpack_from('<i',data,at)[0];assert old==v['StadiumIndex'];assert struct.unpack_from('<ii',data,r['Footer'])==(r['TeamIndex'],r['ClubUID'])
   struct.pack_into('<i',out,at,canonical);patches.append(dict(ClubUID=v['ClubUID'],offset=at,before=old,after=canonical,SourceStadiumID=sid));v['StadiumIndex']=canonical;v['Action']='reuse_same_verified_TM_stadium_id'
 assert len(patches)==3
 restored=bytearray(out)
 for p in patches:
  assert struct.unpack_from('<i',restored,p['offset'])[0]==p['after'];struct.pack_into('<i',restored,p['offset'],p['before'])
 assert bytes(restored)==data
 # Preserve completed first-stage report and verification receipts before this explicit second data stage.
 shutil.copyfile(B/'structure-report.json',B/'structure-report-before-shared-stadium.json');shutil.copyfile(B/'structure-independent.json',B/'structure-independent-before-shared-stadium.json')
 file=dest/'server_db.dat';file.write_bytes(file.read_bytes()[:9]+zlib.compress(bytes(out)))
 after=pins(dest);assert set(k for k in before if before[k]!=after[k])=={'server_db.dat'};assert pins(src)==read(B/'manifest.json')['source_hashes']
 proof=dict(status='three_reference_data_patch_pass',source_payload_sha256=hashlib.sha256(data).hexdigest(),output_payload_sha256=hashlib.sha256(out).hexdigest(),patches=patches,shared_identities=shared,all_other_bytes_preserved=True,source_hashes=before,output_hashes=after,unreferenced_duplicate_records_retained=3,no_reindex_or_engine_change=True,existing_future_transfer_bytes_unchanged_by_bounded_nonoverlapping_TEAM_fields=True)
 dump(B/'shared-stadium-reuse.json',proof);sr.update(SERVER_shared_venue_patch=proof,output_hashes=after,status='structure_shared_venues_written_final_readback_pending');dump(B/'structure-report.json',sr)
 print('REUSED3 verified common stadium IDs, changed12TEAMbytes only; full final readback pending.',flush=True)
if __name__=='__main__':main()
