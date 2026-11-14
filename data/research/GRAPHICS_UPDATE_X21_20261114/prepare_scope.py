from pathlib import Path
import sys,csv,json,hashlib,collections,importlib.util
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';O=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def dump(n,a):(O/n).write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def csvwrite(n,a):
 with(O/n).open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(a[0]));w.writeheader();w.writerows(a)
BATCHES=[('X15',R/'COUNTRY_BATCH_GER_MEX_MAS_20261112','prepared'),('X16',R/'COUNTRY_BATCH_KOR_COL_ISR_20261112/six-country-stage','prepared'),('X17',R/'COUNTRY_BATCH_IDN_IND_HKG_20261112','prepared'),('X18',R/'COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep','prepared'),('X20',R/'COUNTRY_BATCH_CZE_CRO_CHN_CHI_BGR_BRA_20261113/native-prep','prepared-r3'),('X21',R/'COUNTRY_BATCH_BLR_BEL_AUT_AUS_ARG_20261114/native-prep','prepared')]
def main():
 baseline=R/'DATABASE_UPDATE_COVERAGE_X14_20261111';players={p['uid']:dict(p,tmid='',dob='',new='',ledger='X14 baseline')for p in rows(baseline/'zawodnicy_latest.csv')};clubs={p['club_uid']:dict(p,tmid='',ledger='X14 baseline')for p in rows(baseline/'kluby.csv')};pins={str(p):sha(p)for p in[baseline/'zawodnicy_latest.csv',baseline/'kluby.csv']};plans={};clplans={};issues=[];stats=[];rawcache={}
 for label,b,prepname in BATCHES:
  lp=b/'final-native-player-UID-ledger.csv';manifest=read(b/'final-artifact-pins.json');assert sha(lp)==manifest['final-native-player-UID-ledger.csv'];pins[str(lp)]=sha(lp);pins[str(b/'final-artifact-pins.json')]=sha(b/'final-artifact-pins.json');ledger=rows(lp)
  cp=b/'club-map.csv';pins[str(cp)]=sha(cp)
  for c in rows(cp):
   uid=c['ClubUID'];clubs[uid]=dict(country=c['Country'],club_uid=uid,club=c['ClubName'],division_index=c['DivisionIndex'],source_group=c['Group'],confirmed_latest_imported_players='',complete_playable_assignment='',tmid=c['TMID'],ledger=label)
   if c['TMID'].isdigit():clplans[uid]=dict(kind='logo',uid=uid,name=c['ClubName'],urls=[f"https://tmssl.akamaized.net/images/wappen/normal/{c['TMID']}.png"],proof=[dict(kind='final_club_map_TMID_UID',source=str(cp),TMID=c['TMID'],ClubUID=uid)])
  pp=b/prepname/'provenance.json';pins[str(pp)]=sha(pp);prov={str(p['subject_id']):p for p in read(pp)}
  assert len(prov)==len(ledger),(label,len(prov),len(ledger))
  counturls=0;new=0
  for x in ledger:
   uid=x['UID'];pr=prov[x['SubjectID']];assert str(pr['TMID'])==x['TMID']and pr['source_dob']==x['RealDOB'];new+=x['New']=='True'
   old=players.get(uid)
   if old and old.get('tmid')and old['tmid']!=x['TMID']:issues.append(dict(kind='UID_TMID_changed_across_final_ledgers',UID=uid,old=old['tmid'],new=x['TMID'],ledger=label));plans.pop(uid,None)
   players[uid]=dict(uid=uid,club_uid=x['ClubUID'],country=x['Country'],first=x['FirstName'],last=x['LastName'],last_import_batch=label,tmid=x['TMID'],dob=x['RealDOB'],new=x['New'],ledger=str(lp))
   raw=pr.get('PlayerRaw')or{};rel=raw.get('raw_file','');candidate=next((base/rel for base in[b,b.parent,b.parent.parent]if rel and(base/rel).is_file()),None)
   if candidate is None:issues.append(dict(kind='missing_raw_provenance',UID=uid,ledger=label,raw=rel));continue
   if candidate not in rawcache:
    wrap=read(candidate);assert sha(candidate)==raw['file_sha256'];body=wrap['body'];assert hashlib.sha256(body.encode()).hexdigest()==raw['body_sha256'];data=json.loads(body).get('data')or[];data=data.get('players',[])if isinstance(data,dict)else data;rawcache[candidate]={str(v['id']):v for v in data};pins[str(candidate)]=sha(candidate)
   item=rawcache[candidate].get(x['TMID']);url=item.get('portraitUrl')if item else None
   if not item or item.get('lifeDates',{}).get('dateOfBirth')!=x['RealDOB']:issues.append(dict(kind='source_identity_or_DOB_mismatch',UID=uid,ledger=label));continue
   if isinstance(url,str)and url.startswith('https://')and'default'not in url.lower():
    plans[uid]=dict(kind='face',uid=uid,name=pr['name'],urls=[url],proof=[dict(kind='final_UID_ledger_exact_TMID_DOB_raw',TMID=x['TMID'],DOB=x['RealDOB'],ledger=str(lp),provenance=str(pp),raw=str(candidate),raw_sha256=sha(candidate))]);counturls+=1
  stats.append(dict(batch=label,profiles=len(ledger),new=new,confirmed_source_portraits=counturls))
 # Reuse previously confirmed face/logo plans for baseline, never infer UID from a name.
 for pp in[R/'GRAPHICS_MODERN_2627_20261111/asset-plan.json',R/'GRAPHICS_COVERAGE_X14_20261112/confirmed-asset-plan.json']:
  data=read(pp);pins[str(pp)]=sha(pp);items=data.get('items',data.get('faces',[])+data.get('logos',[]))
  for a in items:
   uid=str(a['uid']);a['uid']=uid
   if a['kind']=='face'and uid in players and uid not in plans and a.get('urls'):plans[uid]=a
   if a['kind']=='logo'and uid in clubs and uid not in clplans and a.get('urls'):clplans[uid]=a
 csvwrite('scope-players.csv',list(players.values()));csvwrite('scope-clubs.csv',list(clubs.values()));dump('source-asset-plan.json',dict(items=list(plans.values())+list(clplans.values()),input_pins=pins,rights='LOCAL_ONLY_NOT_APPROVED_FOR_PUBLIC_REDISTRIBUTION',issues=issues));dump('source-scope.json',dict(players=len(players),clubs=len(clubs),batches=stats,face_candidates=len(plans),logo_candidates=len(clplans),issues=len(issues),DBModified=False))
 # Reuse the existing exact XML+PNG auditor with only scope/title/output parameters changed.
 src=R/'GRAPHICS_COVERAGE_X14_20261112/audit_graphics.py';s=src.read_text(encoding='utf-8-sig');s=s.replace('OUT=R/"GRAPHICS_COVERAGE_X14_20261112"','OUT=R/"GRAPHICS_UPDATE_X21_20261114/baseline"');s=s.replace('coverage=R/"DATABASE_UPDATE_COVERAGE_X14_20261111"','coverage=R/"GRAPHICS_UPDATE_X21_20261114"');s=s.replace('coverage/"zawodnicy_latest.csv"','coverage/"scope-players.csv"').replace('coverage/"kluby.csv"','coverage/"scope-clubs.csv"').replace('coverage/"manifest.json"','coverage/"source-scope.json"');s=s.replace('assert len(players)==30897 and len({p["uid"] for p in players})==30897','assert len(players)==len({p["uid"] for p in players})');s=s.replace('assert len(clubs)==1250 and len({c["club_uid"] for c in clubs})==1250','assert len(clubs)==len({c["club_uid"] for c in clubs})');s=s.replace('X14','X21').replace('12 listopada 2026','14 listopada 2026');(O/'baseline').mkdir(exist_ok=True);(O/'audit_scope.py').write_text(s,encoding='utf-8');print(json.dumps(read(O/'source-scope.json'),ensure_ascii=True),flush=True)
if __name__=='__main__':main()
