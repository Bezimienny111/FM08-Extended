from pathlib import Path
import csv,json,hashlib,xml.etree.ElementTree as ET,re,collections
ROOT=Path.cwd();R=ROOT/'FmLauncher/data/research';B=R/'FACEPACK_ALL_NEW_X8_VS_802_20261111'
def rows(p):
 with p.open(encoding='utf-8-sig',newline='')as f:return list(csv.DictReader(f))
stock=rows(B/'stock802-audit/players.csv')
current=rows(R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/audit/players.csv')
uids={int(r['ID'])for r in stock}
assert len(uids)==len(stock)
assert len({int(r['ID'])for r in current})==len(current)
ret={int(r['UID']):r['NativeRetirementDate']for r in rows(B/'X8-retirements.csv')}
latest={int(r['uid']):r for r in json.loads((R/'FACEPACK_NEW_PLAYERS_20261111/players-latest-uid.json').read_text(encoding='utf-8'))}
newer={int(r['uid'])for r in rows(R/'FACEPACK_NEW_PLAYERS_20261111/new-players-facepack.csv')}
portraituids=set();configs=list((ROOT/'Dane/graphics/pictures/faces/normal').rglob('config.xml'))
rx=re.compile(r'graphics/pictures/person/(\d+)/portrait$')
for p in configs:
 for x in ET.parse(p).iter('record'):
  m=rx.search(x.get('to',''))
  if m and (p.parent/(x.get('from','')+'.png')).is_file():portraituids.add(int(m.group(1)))
out=[]
for p in current:
 u=int(p['ID'])
 if u in uids:continue
 l=latest.get(u,{})
 full=(p['FirstName']+' '+p['LastName']).strip()
 out.append(dict(uid=u,first_name=p['FirstName'],last_name=p['LastName'],native_dob=p['BirthDate'],source_name=l.get('source_name',full),source_dob=l.get('source_dob',''),dob_precision=l.get('dob_precision','unknown_no_joined_source'),nationality=p['Nationality'],owner_team_index=int(p['ClubIndex']),owner_club=p['Club'],playing_team_index=l.get('playing_team_index',''),playing_club=l.get('club',''),source_player_id=l.get('source_player_id',''),transfermarkt_id=l.get('transfermarkt_id',''),id90=l.get('id90',''),profile_url=l.get('profile_url',''),roster_url=l.get('roster_url',''),origin_batch=l.get('origin_batch','legacy_not_joined_to_creation_journal'),created_in_N4_X7=u in newer or bool(l.get('new_by_project')),native_retirement_date=ret.get(u,''),has_explicit_retirement=u in ret,existing_mapped_png=u in portraituids,portrait_filename=str(u)+'.png',portrait_target='graphics/pictures/person/'+str(u)+'/portrait'))
out.sort(key=lambda r:r['uid'])
no_ret=[r for r in out if not r['has_explicit_retirement']]
with_ret=[r for r in out if r['has_explicit_retirement']]
additional=[r for r in no_ret if r['uid']not in newer]
missing=[r for r in no_ret if not r['existing_mapped_png']]
def save(name,data):
 with (B/name).open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(data)
save('all-new-players-vs802.csv',out)
save('new-players-no-retirement.csv',no_ret)
save('new-players-with-retirement.csv',with_ret)
save('additional-new-players-facepack.csv',additional)
save('new-players-without-local-portrait.csv',missing)
assert newer.issubset({r['uid']for r in no_ret})
assert len(out)==len(no_ret)+len(with_ret)
summary=dict(date='2026-11-11',stock802_player_uids=len(stock),X8_player_uids=len(current),new_X8_not_stock802=len(out),stock_uids_missing_in_X8=len(uids-{int(r['ID'])for r in current}),new_with_explicit_retirement=len(with_ret),new_without_explicit_retirement=len(no_ret),retirement_dates=dict(collections.Counter(r['native_retirement_date']for r in with_ret)),N4_X7_candidates_included=len(newer),additional_nonretired_beyond_N4_X7=len(additional),nonretired_new_with_existing_mapped_png=sum(r['existing_mapped_png']for r in no_ret),nonretired_new_without_local_mapped_png=len(missing),existing_portrait_check_config_files=len(configs),new_without_joined_source=len([r for r in no_ret if not r['source_player_id']]),source_dob_not_inferred=True,native_input_changed=False)
(B/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
inputs=[B/'stock802-audit/players.csv',B/'X8-retirements.csv',R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/audit/players.csv',R/'FACEPACK_NEW_PLAYERS_20261111/players-latest-uid.json']
stockroot=Path('J:/FM08/data/updates/update-802/db/802')
xroot=R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/input/X8-accepted'
inputs += [p/n for p in [stockroot,xroot]for n in ['people_db.dat','server_db.dat','client_db.dat']]
inputs+=[R/'FOUR_COUNTRY_X7_20261110/tools-r2/FM08_Database_Editor.exe',R/'ITALY_DATABASE_2627_IMPORT_I1_20261108/tools-r1/ApplyVerifiedNativeSquads.exe']
manifest=dict(scope='all audited PLAYER UID in frozen TEST_X8 absent from local original802 baseline; not PERSON count difference',stock_source=str(stockroot),X8_source=str(xroot),retirement_filter='explicit enabled retirement table entries; all new excluded dates lie between2006-01-01 and2007-07-30; not claiming all were duplicate retirements',source_identity_limit='34175 historical newUID outside creation journalsN4-X7; full list is UID complete relative to local802 but source IDs not yet joined for earlier V21-V25',no_real_DOB_inversion=True,read_only_database_operations=True,sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in inputs},outputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in B.glob('*.csv')})
(B/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=True))
