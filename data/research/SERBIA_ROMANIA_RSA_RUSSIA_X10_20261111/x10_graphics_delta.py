"""Export X10 final UID graphics delta from existing caches only; no DB writes/network."""
from x10_pipeline import *
import csv
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def csvout(path,fields,values):
 with path.open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.DictWriter(f,fieldnames=fields,delimiter=';');w.writeheader();w.writerows(values)
def valid(url):return isinstance(url,str)and url.startswith('https://')and not any(x in url.lower()for x in ['default','placeholder','data:image'])
def main():
 publication=read(B/'publication.json');assert publication['native']and read(B/'prepared/independent-verification.json')['status']=='pass'
 observed=pins(ROOT/'Dane/db/TEST_X10');drift={k:dict(native_verified=publication['output_hashes'].get(k),current=observed.get(k))for k in set(observed)|set(publication['output_hashes'])if observed.get(k)!=publication['output_hashes'].get(k)}
 D=B/'graphics-delta';assert not D.exists();D.mkdir()
 full=read(B/'prepared/full-native.json');ids={int(x['SubjectID']):x for x in rows(B/'prepared/identities.csv')};prov={int(x['subject_id']):x for x in read(B/'prepared/provenance.json')};cm=rows(B/'prepared/club_map.csv');byti={int(x['TeamIndex']):x for x in cm};plans={x['TMID']:x for x in read(B/'club-plan.json')};competitions={x['index']:x for x in read(B/'competition-catalog.json')};facts=read(B/'roster-facts.json');factby={}
 for f in facts:factby.setdefault((str(f['TMID']),str(f['ClubTMID']),f.get('RealDOB')),[]).append(f)
 rawcache={};faces=[];players=[];gaps=[]
 for x in full['subjects']:
  sid=x['id90'];identity=ids[sid]
  if int(identity['ExistingID'])>0:continue
  p=prov[sid];tid=str(p['source_player_id']).removeprefix('tm:');club=byti[x['playing']];urls=[];proof=[]
  assert x['uid']>=1698000000 and x['playing']==int(identity['PlayingClubIndex'])and x['owner']==int(identity['OwnerClubIndex'])
  matches=factby.get((tid,club['TMID'],p['source_dob']),[])
  for f in matches:
   rawpath=B/f['PlayerRaw']
   if rawpath not in rawcache:
    j=json.loads(read(rawpath)['body']);values=j.get('data')or[]
    if isinstance(values,dict):values=values.get('players',[])
    rawcache[rawpath]={str(z.get('id')):z for z in values}
   person=rawcache[rawpath].get(tid)
   if not person:continue
   date=(person.get('lifeDates')or{}).get('dateOfBirth')
   if date!=p['source_dob']:continue
   url=person.get('portraitUrl')
   if valid(url)and url not in urls:urls.append(url);proof.append(dict(kind='Transfermarkt',id=tid,source=str(rawpath),cached_ID_and_real_DOB_verified=True,real_dob=date))
  if not urls:
   rosterpath=B/plans[club['TMID']]['RosterFile'];roster=read(rosterpath)
   for person in roster.get('players',[]):
    if str(person.get('id'))!=tid or person.get('date_of_birth')!=p['source_dob']:continue
    url=person.get('image_url')or person.get('image')
    if valid(url)and url not in urls:urls.append(url);proof.append(dict(kind='Transfermarkt',id=tid,source=str(rosterpath),cached_ID_and_real_DOB_verified=True,real_dob=person.get('date_of_birth')))
  face=dict(kind='face',uid=str(x['uid']),name=p['name'],urls=urls,proof=proof,playing_club_uid=club['ClubUID'],playing_club_name=club['ClubName'],playing_team_index=x['playing'],owner_team_index=x['owner'],source_TMID=tid,source_real_DOB=p['source_dob'],status='native_verified_final_UID_cached_image'if urls else'native_verified_final_UID_no_confirmed_image')
  faces.append(face);players.append({'UID':str(x['uid']),'Imię':x['first'],'Nazwisko':x['last'],'Klub':club['ClubName'],'Ma zdjęcie':'tak'if urls else'nie'})
  if not urls:gaps.append(dict(kind='face',uid=str(x['uid']),TMID=tid,reason='no_nonplaceholder_cached_portrait_with_matching_ID_and_real_DOB'))
 assert len(faces)==2822 and len({x['uid']for x in faces})==2822
 logos=[];clubs=[]
 for c in cm:
  plan=plans[c['TMID']];profilepath=B/plan['ProfileFile'];profile=read(profilepath);tid=c['TMID'];url=profile.get('image');urls=[];proof=[];league=competitions[int(c['DivisionIndex'])]
  if tid.isdigit()and str(profile.get('id'))==tid and valid(url):
   urls=[url];proof=[dict(kind='verified_club_map_TM_ID',id=tid,source=str(profilepath),native_uid=c['ClubUID'],cached_profile_image=True)]
  logos.append(dict(kind='logo',uid=c['ClubUID'],name=c['ClubName'],urls=urls,proof=proof,source_TMID=tid if tid.isdigit()else'',source_identity_namespace='Transfermarkt'if tid.isdigit()else plan.get('SourceIdentityNamespace','official'),actual_division_index=int(c['DivisionIndex']),actual_division_uid=league['uid'],actual_division_name=league['names'][0],team_index=int(c['TeamIndex']),country=c['Country'],required_outputs=['normal','small'],status='native_verified_final_UID_cached_logo'if urls else'native_verified_final_UID_no_confirmed_logo'))
  clubs.append({'UID':c['ClubUID'],'Nazwa klubu':c['ClubName'],'Liga':league['names'][0]})
  if not urls:gaps.append(dict(kind='logo',uid=c['ClubUID'],source_key=tid,reason='no_authentic_cached_club_logo_or_non_TM_official_identity'))
 assert len(logos)==154 and len({x['uid']for x in logos})==154
 plan=dict(faces=faces,logos=logos);dump(D/'asset-plan.json',plan)
 csvout(D/'newplayers.csv',['UID','Imię','Nazwisko','Klub','Ma zdjęcie'],players);csvout(D/'clubs.csv',['UID','Nazwa klubu','Liga'],clubs)
 manifest=dict(status='native_verified_UIDs_asset_plan_only_no_download_or_runtime_acceptance',source_publication=str(B/'publication.json'),source_database='TEST_X10',source_database_hashes=publication['output_hashes'],current_database_observed_hashes=observed,current_database_drift_after_native_publication=drift,source_basis='verified prepared/full-native.json final UID mapping before user SI save; later SI state requires separate acceptance',new_player_UIDs=len(faces),faces_with_confirmed_cached_image=sum(bool(x['urls'])for x in faces),clubs=len(logos),clubs_with_confirmed_cached_logo=sum(bool(x['urls'])for x in logos),face_output='normal portrait; inherited graphics builder supports render',logo_outputs=['normal','small'],files=pins(D),encoding='UTF8_BOM_CSV_semicolon',no_database_mutations=True,no_network_calls=True,placeholder_images_rejected=True,real_DOB_and_source_ID_required_for_face=True,gaps=gaps,SI=False,new_career=False,season=False)
 dump(D/'manifest.json',manifest);assert pins(ROOT/'Dane/db/TEST_X10')==observed,'Database changed concurrently while exporting; lists remain based on native verified mapping'
 print('GRAPHICS DELTA',dict(faces=len(faces),face_urls=manifest['faces_with_confirmed_cached_image'],clubs=len(logos),logo_urls=manifest['clubs_with_confirmed_cached_logo'],gaps=len(gaps)),flush=True)
if __name__=='__main__':main()
