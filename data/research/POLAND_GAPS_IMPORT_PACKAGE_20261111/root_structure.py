"""Configured reuse of the witnessed X7/X10 structural writer; private X14 staging only."""
from pathlib import Path
from collections import Counter
import sys,json,csv,struct,shutil,hashlib,importlib.util
sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[4]
B=Path(__file__).resolve().parent
W=B/'structure-root'
SCR=ROOT/'FM08-Database-Tools/scratch'
sys.path.insert(0,str(SCR))
from create_italy_structure_i1_20261108 import read,rows,dump,save,load,pins
COUNTRY={'Portugal':162,'Norway':160,'Peru':194}
POOLS={'Portugal':49,'Norway':539,'Peru':598}
EDITOR=ROOT/'FmLauncher/data/research/PERSONALITY_CODEC_REPAIR_20261111/root-applied/build/FM08_Database_Editor.exe'
BASE=ROOT/'FmLauncher/data/research/SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/tools/ApplyX10Structure.py'
REQ=ROOT/'FmLauncher/data/research/PORTUGAL_PERU_NORWAY_POLAND_PREP_20261111/native-competition-requirements.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def replace1(s,a,b):
 assert s.count(a)==1,('adapter_seed_changed',a[:90],s.count(a))
 return s.replace(a,b,1)
def prepare():
 assert not W.exists(),'Do not overwrite an existing structural attempt'
 m=read(B/'manifest.json');src=Path(m['source'])
 assert {k:v.lower() for k,v in pins(src).items()}==m['source_hashes']
 core=read(B/'club-plan.json');owners=read(B/'foreign-owner-plan.json')
 proj={x['TMID']:x for x in rows(B/'club-map.csv')+rows(B/'foreign-owner-map.csv')}
 world={x['ClubUID']:x for x in read(B/'native-world-identities.json')}
 records=read(B/'native-structure.json')['records'];old={x['ClubUID']:x for x in records}
 raw=load(src,'server_db.dat');requirements=read(REQ)['requirements']
 catalog={x['index']:x for x in read(B/'competition-catalog.json')}
 for q in requirements:assert catalog[q['CatalogueIndex']]['uid']==q['CompetitionUID']
 playable={q['CatalogueIndex']:q['Country']for q in requirements if q['Playability']=='native_playable_settings'}
 desired={int(proj[x['TMID']]['ClubUID']):x['DesiredDivision']for x in core}
 country={u:x['Country']for u,x in world.items()}
 for x in core+owners:country[int(proj[x['TMID']]['ClubUID'])]=x['NativeCountryIndex']
 proposed={u:desired.get(u,r['CurrentDivisionIndex']) for u,r in old.items()}
 reasons={u:'final_classic_allocation_from_previous_completed_tables' for u in desired if u in old}
 for u,r in old.items():
  if u not in desired and r['CurrentDivisionIndex']in playable:
   cn=playable[r['CurrentDivisionIndex']];proposed[u]=POOLS[cn];reasons[u]='displaced_old_playable_team_retained_in_own_country_lower_pool'
 # Country-scoped lower-pool minima are separate from global competition counts.
 lower=[q for q in requirements if q['Playability']=='lower_pool']
 def poolcount(q):
  div=q['CatalogueIndex'];ci=COUNTRY[q['Country']]
  return sum(d==div and(not q['CountrySpecific']or country[u]==ci)for u,d in proposed.items())+sum(x['DesiredDivision']==div and(not q['CountrySpecific']or x['NativeCountryIndex']==ci)for x in core+owners if not x['NativeClubUID'])
 poolmoves=[]
 for q in lower:
  need=q['Form0Min']-poolcount(q)
  if need<=0:continue
  cn=q['Country'];dest=q['CatalogueIndex'];ci=COUNTRY[cn]
  donorqs=[z for z in lower if z['Country']==cn and z['CatalogueIndex']!=dest]
  for donor in donorqs:
   spare=poolcount(donor)-donor['Form0Min']
   eligible=sorted(u for u,d in proposed.items()if d==donor['CatalogueIndex']and u not in desired and country[u]==ci)
   for u in eligible[:min(need,max(0,spare))]:
    proposed[u]=dest;reasons[u]='country_lower_pool_minimum_cascade_without_changing_confirmed_catalogue';poolmoves.append(dict(ClubUID=u,Before=old[u]['CurrentDivisionIndex'],After=dest,Country=cn));need-=1
   if need<=0:break
  assert need<=0,('unresolved_lower_pool_minimum',q,need)
 moves=[dict(ClubUID=u,Before=r['CurrentDivisionIndex'],After=proposed[u],Reason=reasons.get(u,''))for u,r in sorted(old.items())if proposed[u]!=r['CurrentDivisionIndex']]
 altmoves=[]
 for u,r in old.items():
  alt=struct.unpack_from('<i',raw,r['Start']+15)[0]
  if alt>=0 and alt!=proposed[u]and(u in desired or alt in playable):altmoves.append(dict(ClubUID=u,Before=alt,After=-1,Reason='scoped_old_alternate_must_fall_back_to_final_current_assignment'))
 alts={x['ClubUID']:-1 for x in altmoves}
 current=Counter(r['CurrentDivisionIndex']for r in records);after=Counter(proposed.values())
 newcore=[x for x in core+owners if not x['NativeClubUID']]
 for x in newcore:after[x['DesiredDivision']]+=1
 checks=[]
 def count(q,form):
  result=0;di=q['CatalogueIndex'];ci=COUNTRY[q['Country']]
  for u,r in old.items():
   if q['CountrySpecific']and country[u]!=ci:continue
   d=proposed[u]
   if form==1:
    alt=alts.get(u,struct.unpack_from('<i',raw,r['Start']+15)[0]);d=alt if alt>=0 else d
   region=struct.unpack_from('<i',raw,r['Start']+47)[0]
   if d==di or region==di:result+=1
  result+=sum(x['DesiredDivision']==di and(not q['CountrySpecific']or x['NativeCountryIndex']==ci)for x in newcore)
  return result
 for q in requirements:
  for form in [0,1]:
   n=count(q,form);lo=q['Form0Min']if not form else q['Form1DefaultMin'];hi=q['Form0Max']if not form else q['Form1DefaultMax']
   assert n>=lo and(hi is None or n<=hi),('preflight_actual_forms',q,form,n)
   checks.append(dict(index=q['CatalogueIndex'],uid=q['CompetitionUID'],country=q['Country'],country_scoped=q['CountrySpecific'],form=form,count=n,min=lo,max=hi))
 cfg=dict(moves=moves,alternate_moves=altmoves,requirements=[dict(index=q['CatalogueIndex'],uid=q['CompetitionUID'],min=q['Form0Min'],max=q['Form0Max'],country_scope=COUNTRY[q['Country']]if q['CountrySpecific']else None)for q in requirements],expected_count_deltas={str(d):after[d]-current[d]for d in after if after[d]!=current[d]})
 fixed=[]
 for item in sorted(core,key=lambda x:(bool(x.get('ParentTMID')),x['Country'],int(x['TMID'])))+sorted(owners,key=lambda x:int(x['TMID'])):
  x=dict(item);pr=proj[x['TMID']];x['ProjectedClubUID']=int(pr['ClubUID']);x['ProjectedTeamIndex']=int(pr['TeamIndex']);x['ProjectedFamilyIndex']=int(pr['FamilyIndex'])
  if x['NativeClubUID']:
   u=x['NativeClubUID'];x['SourceCountryIndex']=world[u]['Country']
   if x.get('ParentTMID')and not x.get('NativeParentUID'):
    x['SourceParentTMID']=x['ParentTMID'];x['ParentTMID']=''
   elif x.get('NativeParentUID'):x['ExistingParentUID']=x['NativeParentUID']
  fixed.append(x)
 W.mkdir();(W/'audit').mkdir();(W/'tools').mkdir()
 dump(W/'manifest.json',dict(m,editor=str(EDITOR),editor_sha256=sha(EDITOR)))
 dump(W/'club-plan.json',fixed[:len(core)]);dump(W/'foreign-owner-plan.json',fixed[len(core):]);dump(W/'structure-config.json',cfg)
 shutil.copyfile(B/'native-structure.json',W/'native-structure.json');shutil.copyfile(B/'audit/nations.csv',W/'audit/nations.csv');shutil.copyfile(EDITOR,W/'tools/FM08_Database_Editor.exe')
 dump(W/'preflight.json',dict(status='PASS_ACTUAL_DAT_FORMS_PRE_WRITE_RUNTIME_LOADER_PENDING',new_TEAM=len(newcore),new_core_TEAM=74,new_owner_TEAM=12,both_form_checks=checks,lower_pool_cascades=poolmoves,projected_source_pins={str(p):sha(p)for p in [B/'club-plan.json',B/'foreign-owner-plan.json',B/'club-map.csv',B/'foreign-owner-map.csv',REQ]}))
 import batch_three_countries_b1_20261109 as fin
 fin.B=W;fin.finance_audit();assert not read(W/'new-clubs-sugar-daddy-audit.json')['unsupported']
 s=BASE.read_text(encoding='utf-8')
 s=replace1(s,"B=R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111'","B=R/'POLAND_GAPS_IMPORT_PACKAGE_20261111/structure-root'")
 s=replace1(s,'1800120001+len(venueadd)','1800150001+len(venueadd)')
 s=replace1(s,"u=1800110001+len(additions);ti=oldTeam+len(teams);fi=parent['FamilyIndex']if parent else oldName+len(names)","u=x['ProjectedClubUID'];ti=oldTeam+len(teams);fi=parent['FamilyIndex']if parent else oldName+len(names);assert ti==x['ProjectedTeamIndex']and fi==x['ProjectedFamilyIndex'],('projection_changed',x['TMID'],ti,fi,x['ProjectedTeamIndex'],x['ProjectedFamilyIndex'])")
 s=replace1(s,"assert u in [136465,130501] and f['country_index']==-1 and x.get('NativeCountryRepairTo')==cn","assert f['country_index']==-1 and x.get('NativeCountryRepairTo')==cn")
 s=replace1(s,"cfg['expected_count_deltas']={d:v['current']for d,v in cfg['expected_count_deltas'].items()if v['current']}","cfg['expected_count_deltas']={d:v for d,v in cfg['expected_count_deltas'].items()if v}")
 s=replace1(s,"if q['max']==-1:q['max']=None","if q['max']==-1:q['max']=None")
 compile(s,str(W/'tools/ApplyX14Structure.py'),'exec');(W/'tools/ApplyX14Structure.py').write_text(s,encoding='utf-8')
 dump(W/'adapter-pins.json',dict(base=str(BASE),base_sha256=sha(BASE),configured_sha256=sha(W/'tools/ApplyX14Structure.py'),editor_sha256=sha(EDITOR),scope='stable projected74core+12ownerTEAM, country repairs, scoped alternates, venues, projectSugarOFF',engine_changed=False))
 print('PREPARED private structure:86TEAM,36 both-form checks,immutable UID projection;runtime loader pending',flush=True)
def apply():
 assert read(W/'preflight.json')['status'].startswith('PASS')
 code=(W/'tools/ApplyX14Structure.py').read_text(encoding='utf-8');assert sha(W/'tools/ApplyX14Structure.py')==read(W/'adapter-pins.json')['configured_sha256']
 ns={'__name__':'x14_structural_adapter','__file__':str(SCR/'apply_four_country_structure_x7_20261110.py')}
 exec(compile(code,str(W/'tools/ApplyX14Structure.py'),'exec'),ns);ns['main']()
if __name__=='__main__':
 if sys.argv[1]=='prepare':prepare()
 elif sys.argv[1]=='apply':apply()
 else:raise ValueError(sys.argv[1])