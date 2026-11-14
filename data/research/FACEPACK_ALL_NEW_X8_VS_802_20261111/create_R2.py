from pathlib import Path
import csv,json,hashlib,zlib,struct
R=Path.cwd()/'FmLauncher/data/research';P=R/'FACEPACK_ALL_NEW_X8_VS_802_20261111';B=P/'R2'
assert not B.exists();B.mkdir()
def rows(p):
 with p.open(encoding='utf-8-sig',newline='')as f:return list(csv.DictReader(f))
s=rows(P/'stock802-audit/players.csv');x=rows(R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/audit/players.csv')
sx=[r for r in s if int(r['PersonIndex'])==0];xx=[r for r in x if int(r['PersonIndex'])==0]
assert len(sx)==len(xx)==1
excluded={int(sx[0]['ID']),int(xx[0]['ID'])}
assert excluded=={1811939328,486400}
a={int(r['ID'])for r in s if int(r['PersonIndex'])!=0}
b={int(r['ID'])for r in x if int(r['PersonIndex'])!=0}
assert len(b-a)==46800 and not(a-b)
fields=None;counts={}
for name in ['all-new-players-vs802.csv','new-players-no-retirement.csv','new-players-with-retirement.csv','additional-new-players-facepack.csv','new-players-without-local-portrait.csv']:
 data=rows(P/name);fields=list(data[0]);data=[r for r in data if int(r['uid'])not in excluded]
 with (B/name).open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(data)
 counts[name]=len(data)
assert counts['all-new-players-vs802.csv']==46800
assert counts['new-players-no-retirement.csv']==45467
assert counts['new-players-with-retirement.csv']==1333
assert counts['new-players-without-local-portrait.csv']==33785
sraw=Path('J:/FM08/data/updates/update-802/db/802/people_db.dat')
xraw=R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/input/X8-accepted/people_db.dat'
evidence=[]
for label,p,start,footer in [('802',sraw,19645049,19646884),('X8',xraw,21520686,21521197)]:
 buf=zlib.decompress(p.read_bytes()[9:])
 assert struct.unpack_from('<i',buf,start)[0]==0 and buf[start+4]==2
 evidence.append(dict(source=label,path=str(p),file_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),PERSONindex=0,record_start=start,parsed_candidate_footer=footer,parsed_candidate_uid=struct.unpack_from('<i',buf,footer+4)[0],record_prefix_hex=buf[start:start+64].hex(),candidate_footer_context_hex=buf[footer-8:footer+24].hex(),finding='candidate footer not independently established; zero index and date-like bytes produce ambiguous matches; no UID correction inferred'))
(P/'R2'/'unresolved-PERSON0-evidence.json').write_text(json.dumps(dict(status='unresolved_record_boundary_deferred_from_both_audits',excluded_stock_row=sx[0],excluded_X8_row=xx[0],evidence=evidence,native_database_unchanged=True),ensure_ascii=False,indent=2),encoding='utf-8')
summary=json.loads((P/'summary.json').read_text(encoding='utf-8'))
summary.update(revision='R2',scope='difference of verified remaining audited PLAYER records with PERSONindex0 deferred in BOTH inputs; PERSON0 UID unresolved',raw_stock802_audit_rows=len(s),raw_X8_audit_rows=len(x),stock802_player_uids=len(a),X8_player_uids=len(b),new_X8_not_stock802=46800,stock_uids_missing_in_X8=0,new_with_explicit_retirement=1333,new_without_explicit_retirement=45467,additional_nonretired_beyond_N4_X7=32842,nonretired_new_with_existing_mapped_png=11682,nonretired_new_without_local_mapped_png=33785,new_without_joined_source=26439,excluded_PERSON0_records_each_input=1,excluded_parsed_UIDs=sorted(excluded),portrait_inventory_scope='unchanged R1 snapshot at export time; graphics agent is independently adding files, not rescanned in R2')
(B/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
manifest=dict(revision='R2',exclusion_policy='defer PERSONindex0 in BOTH stock and X8 audits; do not guess/correct UID',original_R1_unchanged=True,native_inputs_unchanged=True,no_native_writer_or_build=True,source_pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in [P/'summary.json',P/'stock802-audit/players.csv',R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/audit/players.csv',P/'X8-retirements.csv']},outputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in B.iterdir()if p.is_file()})
(B/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=True))
