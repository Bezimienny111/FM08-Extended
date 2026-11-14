from pathlib import Path
import json,sys,struct,csv,shutil,hashlib,collections
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent;W=B/'root-structure';OLD=R/'COUNTRY_BATCH_BLR_BEL_AUT_AUS_ARG_20261114/native-prep';assert not W.exists();W.mkdir();(W/'tools').mkdir();(W/'audit').mkdir()
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
from create_italy_structure_i1_20261108 import load,languages,lang_sections,find_table,club,city,unique
from audit_poland_v25_common_r1_20261108 import Cursor
rd=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
pr=rd(B/'allocation-projection.json');assert pr['Status']=='PROJECTION_PASS';freeze=rd(B/'source-freeze.json');state=rd(B/'allocation-raw-state.json');ledger=rd(B/'club-UID-projection.json')['rows'];newkey={'tm:'+x['TMID']:str(x['ClubUID'])for x in ledger if x['IsNew']};before=state['Before'];after={newkey.get(k,k):v for k,v in state['After'].items()}
assert len(after)==len(before)+10
cb=collections.Counter(v[0]for v in before.values());ca=collections.Counter(v[0]for v in after.values());deltas={str(i):ca[i]-cb[i]for i in set(cb)|set(ca)if ca[i]!=cb[i]}
moves={name:[dict(ClubUID=int(u),Before=v[s],After=after[u][s],Reason='reviewed_England_membership_historical_ALT_and_lower_pools')for u,v in before.items()if v[s]!=after[u][s]]for s,name in enumerate(['moves','alternate_moves','regional_moves'])};assert not moves['regional_moves']
indices={q['Index']for q in pr['Checks']}|{q['Before']for q in moves['moves']}|{q['After']for q in moves['moves']};cfg=dict(**moves,requirements=[dict(index=i,min=ca[i],max=ca[i])for i in sorted(indices)if i>=0],expected_count_deltas=deltas,first_new_stadium_uid=1800290001)
dump(W/'structure-config.json',cfg)
for fn in ['club-plan.json','foreign-owner-plan.json','native-structure.json']:shutil.copy2(B/fn,W/fn)
for fn in ['FM08_Database_Editor.exe','ApplyVerifiedNativeSquads.exe']:shutil.copy2(B/'tools'/fn,W/'tools'/fn)
shutil.copy2(B/'audit/nations.csv',W/'audit/nations.csv');shutil.copy2(B/'reserve-kind-overlay.json',W/'tools/reserve-kind-overlay.json')
s=(OLD/'root-structure/tools/ApplyBatchStructure.py').read_text(encoding='utf-8-sig').replace("m['scope']=='blr-bel-aut-aus-arg'","m['scope']=='england'")
s=s.replace("country.update({x['Country']:x['NativeCountryIndex']for x in plan})","country.update({'Belarus':132,'Belgium':131,'Austria':129,'Australia':177,'Argentina':187,'New Zealand':180})")
(W/'tools/ApplyBatchStructure.py').write_text(s,encoding='utf-8');compile(s,str(W/'tools/ApplyBatchStructure.py'),'exec')
shutil.copy2(OLD/'root-structure/verify_structure.py',W/'verify_structure.py')
# Read every previously created project FAMILY flag again at fresh typed boundaries.
project={int(x['ClubUID'])for x in csv.DictReader((OLD/'root-structure/new-clubs-sugar-daddy-audit.csv').open(encoding='utf-8-sig'))};project|={x['uid']for x in rd(OLD/'root-structure/structure-report.json')['additions']if x['kind']=='new_first_team'};assert len(project)==746
src=Path(freeze['frozen']);a=load(src,'server_db.dat');c=load(src,'client_db.dat');en,_=lang_sections(dict(languages((src/'lang_db.dat').read_bytes()))[8]);families,_,_=find_table(c,[x['uid']for x in en['club']],club);_,_,co=find_table(a,[x['uid']for x in en['city']],city);fb=co+4;first=min(x['Start']for x in rd(B/'native-structure.json')['records']);span=a[fb:first];sugar=[]
for f in families:
 if f['uid']not in project:continue
 assert f['index']>0;at=fb+unique(span,struct.pack('<iI',f['index']-1,families[f['index']-1]['uid']))+8;cur=Cursor(a,at);assert cur.byte()==0;cur.integer();cur.byte();cur.string();cur.byte();cur.string();cur.take(2);cur.num('<H');cur.integer();cur.take(1+12+1+2+4+1+1)
 for _ in range(2):cur.take(cur.byte()*4)
 assert cur.byte()==0;flag=cur.p+4;raw=cur.take(45);assert raw[4]in[0,1];sugar.append(dict(ClubUID=f['uid'],SugarDaddyOffset=flag,SugarDaddyBefore=raw[4]))
assert len(sugar)==746
with(W/'new-clubs-sugar-daddy-audit.csv').open('w',encoding='utf-8-sig',newline='')as f:ww=csv.DictWriter(f,fieldnames=list(sugar[0]));ww.writeheader();ww.writerows(sugar)
files=['club-plan.json','foreign-owner-plan.json','structure-config.json','native-structure.json','new-clubs-sugar-daddy-audit.csv','tools/reserve-kind-overlay.json','audit/nations.csv']
m=dict(status='APPROVED_PRIVATE_STRUCTURE_PLAN_NO_PUBLIC_WRITE',scope='england',source=freeze['frozen'],source_hashes=freeze['hashes'],expected_core_clubs=164,source_SI='USER_PASS',source_new_career='USER_PASS',source_season='USER_AUTHORIZED_WHILE_X22_TEST_IN_PROGRESS_TO_2010',reserve_kind_overlay_sha256=sha(W/'tools/reserve-kind-overlay.json'),approved_plan_files={fn:sha(W/fn)for fn in files},SugarDaddySourceProjectFamilies=746,allocation_preflight_sha256=sha(B/'allocation-projection.json'))
dump(W/'manifest.json',m);dump(B/'structure-configuration-ready.json',dict(Status='READY_PRIVATE_STRUCTURE_WRITE',Checks=32,NewTEAM=10,NewFAMILY=10,SourceProjectSugarFlags=746,StructuralFallbacks=0,LowerBackfills=0,WriterSHA256=sha(W/'tools/ApplyBatchStructure.py'),ManifestSHA256=sha(W/'manifest.json'),NativeWritten=False))
print('STRUCTURE_CONFIG_READY10TEAM10FAMILY32checks SugarOFF746; no public database touched',flush=True)
