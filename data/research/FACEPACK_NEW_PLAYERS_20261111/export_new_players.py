"""Export project-created players for facepack planning; never edits any DB."""
from pathlib import Path
import csv, json, hashlib, collections, re
ROOT=Path.cwd()
R=ROOT/'FmLauncher/data/research'
OUT=R/'FACEPACK_NEW_PLAYERS_20261111'
PACKS=[
 ('N4','POLAND_DATABASE_2627_R1_20261108/native-V25-N4','prepared','Poland',True),
 ('N7','POLAND_DATABASE_2627_R1_20261108/native-V25-N7/prepared-r2','','Poland',False),
 ('I1','ITALY_DATABASE_2627_IMPORT_I1_20261108/prepared-r4','','Italy',False),
 ('H1','HUNGARY_DATABASE_2627_H1_20261109/prepared','','Hungary',False),
 ('B1','WALES_USA_URUGUAY_2627_B1_20261109/prepared','','',False),
 ('X2','UKRAINE_TURKEY_X2_20261109/prepared','','',False),
 ('X3','SWEDEN_SWITZERLAND_X3_20261109/prepared','','',False),
 ('X7','FOUR_COUNTRY_X7_20261110/prepared','','',False)]
pins={}
def pin(p):
 pins[str(p.relative_to(ROOT)).replace('\\','/')]=hashlib.sha256(p.read_bytes()).hexdigest()
def js(p):
 pin(p)
 return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):
 pin(p)
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def ii(v):return int(v)
clubs={}
loads=[]
for tag,path,sub,country,old in PACKS:
 p=R/path;q=p/sub
 j=js(p/'full-native.json')
 ids=rows(q/'identities.csv')
 ns=rows(q/('native-players.csv' if old else 'native_players.csv'))
 pv=js(q/('profile-provenance.json' if old else 'provenance.json'))
 cm=rows(q/('club-map.csv' if old else 'club_map.csv'))
 assert len(j['subjects'])==len(ids)==len(ns)==len(pv)==j['rows'],tag
 assert sum(ii(x['UID' if old else 'ExistingID'])<0 for x in ids)==j['added'],tag
 for c in cm:
  c=dict(c)
  c['Country']=c.get('Country') or country
  if c['Country']=='Liechtenstein':c['Country']='Switzerland'
  clubs[ii(c['TeamIndex'])]=c
 loads.append((tag,j,ids,ns,pv,old))
structure=js(R/'THAILAND_LEAGUE_REPLACEMENT_REVIEW_20261110/implementation/X8-user-tested-native-structure.json')
byclubuid={ii(x['ClubUID']):x for x in structure['records']}
for ti,c in clubs.items():
 v=byclubuid[ii(c['ClubUID'])]
 assert ii(v['TeamIndex'])==ti,(ti,c['ClubUID'])
 c['CurrentDivisionIndex']=v['CurrentDivisionIndex']
latest={};origins={};batchstats=[];events=[];reused_before_origin=set()
for tag,j,ids,ns,pv,old in loads:
 for field,kind in [('released_uids','released'),('duplicate_retire_uids','technical_duplicate_retired'),('revived_uids','revived')]:
  for u in j.get(field,[]):
   u=ii(u)
   if u in latest:
    r=latest[u]
    events.append({'uid':u,'batch':tag,'event':kind})
    if kind=='revived':r['retired']=False
    else:
     r['last_event_batch']=tag;r['last_event']=kind;r['imported_confirmed']=False
     r['playing_team_index']=-1;r['owner_team_index']=-1
     r['retired']=kind=='technical_duplicate_retired'
     r['released']=kind=='released'
 subjects=j['subjects']
 if not old:
  sb={ii(x['id90']):x for x in subjects}
  assert len(sb)==len(subjects)
 else:sb=None
 newuids=[]
 for n,ident,prov,ordinal in zip(ns,ids,pv,range(len(ids))):
  subject=subjects[ordinal] if old else sb[ii(ident.get('SubjectID') or ident['ID90'])]
  u=ii(subject['uid'])
  eid=ii(ident['UID' if old else 'ExistingID'])
  assert subject['first']==n['FirstName'] and subject['last']==n['LastName'] and subject['dob']==n['BirthDate'],(tag,u,'row identity')
  assert eid<0 or eid==u,(tag,u,eid)
  if eid<0:
   assert u not in origins and u not in reused_before_origin,(tag,u,'ambiguous new UID')
   origins[u]=tag;newuids.append(u)
  elif u not in origins:reused_before_origin.add(u)
  playing=ii(subject['club'] if old else subject['playing'])
  owner=ii(subject['club'] if old else subject['owner'])
  c=clubs.get(playing)
  assert c is not None,(tag,u,playing)
  realdob=prov.get('source_dob') or prov.get('sourceDOB') or prov.get('real_dob') or ''
  precision=prov.get('dob_precision') or prov.get('precision') or ('unspecified_in_journal' if realdob else 'unknown')
  sourceid=str(prov.get('source_player_id') or '')
  profile=prov.get('profile90') or prov.get('bio_source') or ''
  name=prov.get('name') or prov.get('name90') or (subject['first']+' '+subject['last'])
  tm=re.search(r'(?:tm:|/spieler/)(\d+)',sourceid+' '+profile)
  id90=re.search(r'90minut-(\d+)',sourceid)
  latest[u]={
    'uid':u,'first_name':subject['first'],'last_name':subject['last'],'source_name':name,
    'native_dob':subject['dob'],'source_dob':realdob,'dob_precision':precision,
    'playing_team_index':playing,'owner_team_index':owner,'club_uid':ii(c['ClubUID']),
    'club':c['ClubName'],'country':c['Country'],'current_division_index':c['CurrentDivisionIndex'],
    'source_player_id':sourceid,'transfermarkt_id':tm.group(1) if tm else '',
    'id90':id90.group(1) if id90 else str(prov.get('id90') or ''),
    'profile_url':profile,'roster_url':prov.get('source90') or prov.get('roster_source') or '',
    'source_batch':tag,'origin_batch':origins.get(u,'preexisting_before_N4'),
    'new_by_project':u in origins,'last_event_batch':tag,'last_event':'confirmed_import',
    'released':False,'retired':False,'imported_confirmed':True,
    'name_needs_review':'\ufffd' in (name+subject['first']+subject['last']),
    'portrait_filename':str(u)+'.png',
    'portrait_target':'graphics/pictures/person/'+str(u)+'/portrait'}
 batchstats.append({'batch':tag,'subjects':j['rows'],'added':j['added'],'reused':j['reused'],'new_uid_count':len(newuids)})
# Every project-created UID remains identified even if later reused or retired.
assert set(origins).issubset(latest)
allrows=sorted(latest.values(),key=lambda r:r['uid'])
for r in allrows:
 r['new_by_project']=r['uid'] in origins
 r['origin_batch']=origins.get(r['uid'],'preexisting_before_N4')
 if r['released'] or r['retired']:
  r['club']='';r['club_uid']=-1;r['current_division_index']=-1;r['country']=''
newall=[r for r in allrows if r['new_by_project']]
face=[r for r in newall if not r['retired']]
confirmed=[r for r in allrows if r['imported_confirmed'] and not r['retired'] and not r['released']]
summary={
 'scope':'project-created records in accepted lineage N4 -> N7 -> I1 -> H1 -> B1 -> X2 -> X3 -> X7, inherited by X8',
 'evidence':'verified import journals; not fresh PEOPLE reload, not live save or generated career players',
 'historical_project_new_unique':len(origins),
 'new_facepack_candidates_not_technically_retired':len(face),
 'new_confirmed_playing':sum(r['imported_confirmed'] and not r['retired'] and not r['released'] for r in newall),
 'new_released_but_face_eligible':sum(r['released'] and not r['retired'] for r in newall),
 'new_technical_duplicate_retired':sum(r['retired'] for r in newall),
 'all_latest_imported_unique':len(allrows),
 'all_latest_confirmed_playing':len(confirmed),
 'all_latest_released':sum(r['released'] for r in allrows),
 'all_latest_technical_retired':sum(r['retired'] for r in allrows),
 'reused_preexisting_latest_confirmed':sum(not r['new_by_project'] for r in confirmed),
 'face_candidates_with_tm_id':sum(bool(r['transfermarkt_id']) for r in face),
 'face_candidates_with_90minut_id':sum(bool(r['id90']) for r in face),
 'face_candidates_with_source_dob':sum(bool(r['source_dob']) for r in face),
 'face_candidates_with_bio_source_url':sum(bool(r['profile_url']) for r in face),
 'face_candidates_with_replacement_character_names':sum(r['name_needs_review'] for r in face),
 'confirmed_by_country':dict(sorted(collections.Counter(r['country'] for r in confirmed).items())),
 'new_by_origin':dict(sorted(collections.Counter(origins.values()).items())),
 'batch_stats':batchstats}
OUT.mkdir(parents=True,exist_ok=True)
def savecsv(name,data):
 assert data,name
 with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
savecsv('new-players-facepack.csv',face)
savecsv('new-players-history.csv',newall)
savecsv('players-latest-uid.csv',allrows)
(OUT/'players-latest-uid.json').write_text(json.dumps(allrows,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'events-on-imported-uids.json').write_text(json.dumps(events,ensure_ascii=False,indent=2),encoding='utf-8')
manifest={'date':'2026-11-11','source_hashes':pins,'classification':'ExistingID/UID < 0 on original creation plan, joined to final subject UID; later reuse does not alter origin','N4_pairing':'Original writer evidence preserves prepared row order, with exact first/last/DOB guards; modern journals join SubjectID/id90','technical_retire_excluded':True,'released_active_included_for_faces':True,'V25_preexisting_classification':'reused; not automatically project-created even if absent from stock FM08','current_clubs':'TEAM indices independently checked by ClubUID against frozen X8 structure export','base':'TEST_X8; TEST_X9 excluded technical pilot','outputs':{}}
for p in OUT.iterdir():
 if p.is_file() and p.name!='manifest.json':manifest['outputs'][p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=True))
