"""Thailand FM08 pilot. Builds derived assets; never patches EXE or hooks.
build is confined to this research folder. plan-install is read-only except its plan.
apply/rollback require an explicit flag and are NOT run during preparation.
"""
from __future__ import annotations
import argparse,copy,csv,hashlib,json,os,re,shutil,struct,subprocess,sys,uuid
from pathlib import Path
import xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
SCRATCH=ROOT/'FM08-Database-Tools/scratch'
sys.path.insert(0,str(SCRATCH))
import pol3_efa_r8_20261107 as efa
from create_italy_structure_i1_20261108 import load,languages,lang_sections,find_table,club
import pol3_comp_schema_r8_20261107 as co
EXE_SHA='157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d'
ARCHIVES={'data/comps.efa':'a16bdb9b26454374c1f224b96500e8c4a9e3dd134c83d5822acd611e358b3ead','data/updates/update-802/data/comps.efa':'d5aed6f0058c10a1c4688474e1b2c9c819c052ccdf785d54e368409259473d78'}
PROFILE_COUNTS={'T1':{5624920:16},'T1_T2_DRAFT':{5624920:16,5637986:18}}
TOOLS={ROOT/'FmLauncher/data/research/SWEDEN_SELECTION_REPAIR_X4_20261110/tools/ExportWholeNativeStructure.exe':'1a92d999d80d93f6e00d95ecf72ca7b295610dcfa336b0a244eb31f766dcfdea',ROOT/'FmLauncher/data/research/FOUR_COUNTRY_X7_20261110/tools/FM08_Database_Editor.exe':'56b9a9ff0a66223d9bd5c59bdb74ec2b9ce983eab4984efbe2f92fa4c3a9c645'}
def require(v,msg):
 if not v:raise ValueError(msg)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def blobsha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def pins(p):return {str(f.relative_to(p)).replace('\\','/'):sha(f)for f in sorted(Path(p).rglob('*'))if f.is_file()}
def inside(p,base):
 p=Path(p).resolve();base=Path(base).resolve();require(p==base or base in p.parents,'Path outside declared directory');return p
def add(root,tag,**kw):return ET.SubElement(root,tag,{k:str(v)for k,v in kw.items()})
def item(root,tag,name,value):return add(root,tag,id=name,value=value)
def league(uid,n,level,other=None):
 r=ET.Element('properties',competition=str(uid))
 for k,v in [('version',1),('type','division'),('level',level),('year',0),('year_interval',1),('discipline_index',0),('base_year',2000),('fixture_rules_index',1 if level==0 else 0)]:item(r,'integer',k,v)
 add(r,'record',id='date_range',start_month='sep',start_year_offset=0,end_month='may',end_year_offset=1)
 tv=add(r,'list',id='initial_tv_money');add(tv,'record',cash=0)
 stages=add(r,'list',id='stages');lg=add(stages,'record',id='leag',index=0,type='league')
 teams=add(lg,'list',id='teams');rec=add(teams,'record');item(rec,'flags','id','get_division_teams');item(rec,'integer','competition',uid)
 item(lg,'integer','number_teams',n);item(lg,'integer','number_rounds',2);item(lg,'integer','max_league_games',2*(n-1))
 sorts=add(lg,'list',id='sort_rules');add(sorts,'flags',value='goal_difference');add(sorts,'flags',value='goals_for');item(lg,'boolean','top_team_are_champions','true')
 if other:add(lg,'record',id='relegation' if level==0 else 'promotion',number_places=3,competition=other,min_places=3,max_places=3)
 item(lg,'flags','subs_rules','three_from_seven');item(lg,'flags','priority','league_low')
 sched=add(add(lg,'list',id='schedule'),'record');add(sched,'record',id='start_date',day_of_week='sat',day_of_month=1,month='sep',year=2000);add(sched,'record',id='end_date',day_of_week='sun',day_of_month=25,month='may',year=2001);item(sched,'flags','check_clashes','all')
 md=add(sched,'list',id='match_days');add(md,'record',day_of_week='sat');add(md,'record',day_of_week='wed')
 pm=add(lg,'list',id='prize_money')
 for i in range(n):add(pm,'integer',value=0)
 return r
def nation(profile):
 counts=PROFILE_COUNTS[profile];r=ET.Element('properties',nation='140');item(r,'integer','version',1);add(r,'record',id='season_update_day',day_of_month=20,month='jun');item(r,'integer','weekend_default_fixture_time',1800);item(r,'integer','midweek_default_fixture_time',1900)
 dl=add(r,'list',id='division_levels')
 for uid in counts:add(dl,'record',competition=uid)
 item(r,'integer','default_division_level',len(counts)-1)
 cm=add(r,'list',id='competitions')
 for level,uid in enumerate(counts):add(cm,'record',competition=uid,division_level_required=level)
 req=add(r,'list',id='required_teams')
 for uid,n in counts.items():add(req,'record',competition=uid,nation=140,number_teams=n)
 fx=add(r,'list',id='fixture_rules')
 for idx in [0,1]:
  rec=add(fx,'record',index=idx);item(rec,'boolean','trialists_can_play_in_competitive_fixtures','false');item(rec,'boolean','use_squad_numbers','true')
  if idx==1:
   rules=add(rec,'list',id='squad_selection_rules');add(rules,'record',type='all_foreign_players_in_11',value=7,compare_type='less_than')
 return r

def xmlbytes(root):
 ET.indent(root,space='  ');raw=ET.tostring(root,encoding='utf-8',xml_declaration=True)+b'\n';require(ET.tostring(ET.fromstring(raw))==ET.tostring(root),'XML roundtrip');return raw

def xmlprofile(profile):
 top=league(5624920,16,0,5637986 if profile!='T1' else None);members={'tha/tha.xml':xmlbytes(nation(profile)),'tha/tha_premier.xml':xmlbytes(top)}
 if profile!='T1':members['tha/tha_first.xml']=xmlbytes(league(5637986,18,1,5624920))
 return members

def validate_xml(members,profile):
 roots={k:ET.fromstring(v)for k,v in members.items()};nat=roots['tha/tha.xml'];counts=PROFILE_COUNTS[profile]
 require(nat.attrib=={'nation':'140'},'Nation identity');d=[int(x.get('competition'))for x in nat.find("list[@id='division_levels']")];require(d==list(counts),'division levels')
 for uid,n in counts.items():
  rr=[r for r in roots.values()if r.get('competition')==str(uid)];require(len(rr)==1,'Competition XML collision');r=rr[0];lg=r.find("list[@id='stages']/record");require(int(lg.find("integer[@id='number_teams']").get('value'))==n,'Stage size');require(int(lg.find("integer[@id='number_rounds']").get('value'))==2,'Round count');require(len(lg.find("list[@id='prize_money']"))==n,'Prize size');require(r.find("list[@id='initial_tv_money']/record").get('cash')=='0','Explicit TVmoney')
  req=nat.find("list[@id='required_teams']/record[@competition='%s']"%uid);require(req is not None and int(req.get('number_teams'))==n,'Required count')
  require(lg.find("list[@id='teams']/record/integer[@id='competition']").get('value')==str(uid),'Team source UID')
 if profile!='T1':
  require(roots['tha/tha_premier.xml'].find("list[@id='stages']/record/record[@id='relegation']").get('competition')=='5637986','Relegation target')
  require(roots['tha/tha_first.xml'].find("list[@id='stages']/record/record[@id='promotion']").get('competition')=='5624920','Promotion target')
 return {'xml_parse_roundtrip':True,'counts':counts,'matches_per_season':{str(u):n*(n-1)for u,n in counts.items()},'foreign_rule':'native type2 / all_foreign_players_in_11 max7; registration10 deliberately not claimed','TV_prizes':'zero technical pilot; not real financial update','closed_bottom':True,'direct_exchange':3 if profile!='T1' else 0}

def inverse(child,original,added):
 x=copy.deepcopy(child)
 def prune(t):
  t['files']=[e for e in t['files']if '/'.join([v for v in [t.get('_path',''),e['name']+e['extension']]if v])not in added]
  for d in t['directories']:d['_path']='/'.join([v for v in [t.get('_path',''),d['name']]if v]);prune(d)
  t['directories']=[d for d in t['directories']if d['files']or d['directories']];t.pop('_path',None)
 prune(x['tree'])
 for k in added:del x['members'][k]
 x['data']=child['data'][:len(original['data'])]
 require(x['members']==original['members'],'Inverse original members');raw=efa.repack(x);require(efa.parse(raw)['members']==original['members'],'Inverse parse');return raw

def archives(profile,out):
 members=xmlprofile(profile);checks=validate_xml(members,profile);reports=[]
 for rel,h in ARCHIVES.items():
  src=ROOT/rel;require(sha(src)==h,'Original EFA hash changed: '+rel);raw=src.read_bytes();a=efa.parse(raw);require(efa.repack(a)==raw,'Original exact EFA roundtrip');b=a
  for name,value in members.items():
   require(name.casefold()not in{n.casefold()for n in b['members']},'EFA member collision');b=efa.add_member(b,name,value)
  value=efa.repack(b);check=efa.parse(value);require(all(check['members'][n]==v for n,v in a['members'].items()),'Original member mutation');require(set(check['members'])==set(a['members'])|set(members),'Unexpected additions');require(inverse(check,a,set(members))==raw,'Whole archive inverse mismatch');require(efa.repack(check)==value,'Derived archive roundtrip')
  dest=out/profile/rel;dest.parent.mkdir(parents=True,exist_ok=True);require(not dest.exists(),'Output archive exists');dest.write_bytes(value);require(sha(dest)==blobsha(value),'After disk reread');reports.append(dict(source=str(src),source_sha256=h,output=str(dest),output_sha256=sha(dest),original_members=len(a['members']),added=sorted(members),exact_original_roundtrip=True,all_original_members_unchanged=True,whole_archive_inverse=True))
 for k,v in members.items():
  d=out/profile/'xml'/k;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(v)
 return dict(profile=profile,validation=checks,archives=reports,install_blocked=profile!='T1',blockers=['Choose and validate T2 eighteen real clubs and six lower moves; define real playoff and lower promotion before production']if profile!='T1'else['User approval of concrete installation is pending; runtime untested'])

def inventory(src,structure):
 for tool,h in TOOLS.items():require(sha(tool)==h,'Native audit tool changed')
 audit=HERE/'native-audits'/uuid.uuid4().hex;audit.mkdir(parents=True)
 tools=list(TOOLS);run=subprocess.run([str(tools[0]),str(src),str(tools[1]),str(audit/'structure.json')],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600)
 (audit/'export.log').write_text(run.stdout+run.stderr,encoding='utf-8');require(run.returncode==0,'Whole native export failed: '+str(audit));require(read(audit/'structure.json')['records']==read(structure)['records'],'Provided structure is stale or incomplete')
 en,_=lang_sections(dict(languages((src/'lang_db.dat').read_bytes()))[8]);require(en['nation'][85]['uid']==140,'Unexpected nation mapping');client=load(src,'client_db.dat');ct=co.find_client_comp_table(client,len(en['comp']));co.find_server_comp_table(load(src,'server_db.dat'),ct)
 idx={x['uid']:x['index']for x in ct['records']};rr=read(structure)['records'];families,_,_=find_table(client,[v['uid']for v in en['club']],club);by={f['uid']:f for f in families};names={v['uid']:v['names']for v in en['club']};result=[]
 for r in rr:
  if r['CurrentDivisionIndex']not in[idx[5624920],idx[5637986],idx[7460105]]:continue
  uid=r['ClubUID'];f=by.get(uid);require(f is not None,'Unresolved Thai family');require(f['country_index']==85,'Foreign country in existing Thai pool')
  result.append(dict(club_uid=uid,team_index=r['TeamIndex'],family_index=f['index'],country_uid=140,names=names[uid],current_comp_uid=en['comp'][r['CurrentDivisionIndex']]['uid'],source_offset=r['Start'],roster_size=r['RosterSize']))
  server=load(src,'server_db.dat') if 'server' not in locals() else server;require(struct.unpack_from('<ii',server,r['Footer'])==(r['TeamIndex'],uid),'TEAM identity mismatch');require(struct.unpack_from('<i',server,r['Start']+7)[0]==r['CurrentDivisionIndex'],'TEAM current division mismatch')
 top=[v for v in result if v['current_comp_uid']==5624920];require(len(top)==16 and len({v['club_uid']for v in top})==16,'T1 pilot requires exactly16 unique existing clubs')
 raw_counts={}
 for uid in [5624920,5637986]:
  d=idx[uid];primary=alternate=0
  for r in rr:
   current,previous,alt=struct.unpack_from('<iii',server,r['Start']+7);region=struct.unpack_from('<i',server,r['Start']+47)[0];primary+=int(current==d)+int(region==d);alternate+=int((alt if alt>=0 else current)==d)+int(region==d)
  raw_counts[str(uid)]={'form0_with_regional':primary,'form1_with_regional':alternate}
 require(raw_counts['5624920']=={'form0_with_regional':16,'form1_with_regional':16},'T1 physical min/max forms mismatch')
 return dict(thailand_nation_uid=140,source=str(src),source_pins=pins(src),structure_sha256=sha(structure),T1=top,T2=[v for v in result if v['current_comp_uid']==5637986],lower=[v for v in result if v['current_comp_uid']==7460105],database_changes_for_T1=[],raw_physical_counts=raw_counts,load_time_overrides='not_observed_runtime_pending',new_clubs=0,new_players=0,modern_rosters=False)

def build(args):
 out=inside(args.output,HERE);require(not out.exists(),'Build output exists');require(sha(ROOT/'fm.exe')==EXE_SHA,'Unexpected EXE');src=Path(args.source_db).resolve();expected=read(args.source_pins);require(pins(src)=={k.replace('\\','/'):v.lower()for k,v in expected.items()},'Source pins mismatch');inv=inventory(src,args.structure_json)
 out.mkdir();reports=[archives(x,out)for x in PROFILE_COUNTS];write(out/'pilot-clubs.json',inv)
 support={str(p.relative_to(ROOT)):sha(p)for p in[SCRATCH/'pol3_efa_r8_20261107.py',SCRATCH/'pol3_comp_schema_r8_20261107.py',*TOOLS]}
 report=dict(status='prepared_native_assets_verified_runtime_pending',source_db=str(src),source_pins=inv['source_pins'],exe_sha256=EXE_SHA,profiles=reports,support_hashes=support,script_sha256=sha(__file__),statuses=dict(XML='PASS',archive='PASS',native_T1_club_inventory='PASS',SI='not_tested',new_career='not_tested',fixtures='not_tested',save_load='not_tested',season='not_tested',AFC='not_tested'))
 write(out/'manifest.json',report);require(pins(src)==inv['source_pins'],'Source changed during build');print(json.dumps(report['statuses']))

def running_game():
 r=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,text=True,errors='replace');require(r.returncode==0,'Cannot verify processes')
 return [x for x in csv.reader(r.stdout.splitlines())if x and x[0].lower()in['fm.exe','editor.exe','data editor.exe','fm 2008 data editor.exe']]

def plan_install(args):
 package=inside(args.package,HERE);m=read(package/'manifest.json');require(args.profile=='T1','T2 draft installation blocked');game=Path(args.game_root).resolve();require(sha(game/'fm.exe')==EXE_SHA,'Unexpected installed EXE');require(re.fullmatch(r'TEST_X[1-9][0-9]*',args.db_name),'Use free shared TEST_Xn name');src=Path(args.source_db).resolve();hp=pins(src);require(hp=={k.replace('\\','/'):v.lower()for k,v in read(args.source_pins).items()},'Accepted source pins changed')
 inv=inventory(src,args.structure_json);target=inside(game/'Dane/db'/args.db_name,game/'Dane/db');require(not target.exists(),'Target DB already exists');steps=[]
 for r in next(p for p in m['profiles']if p['profile']==args.profile)['archives']:
  rel=str(Path(r['source']).relative_to(ROOT)).replace('\\','/');a=game/rel;prepared=package/args.profile/rel;require(sha(a)==ARCHIVES[rel],'Installed archive not original');require(sha(prepared)==r['output_sha256'],'Prepared archive changed');steps.append(dict(target=str(a),before_sha256=sha(a),prepared=str(prepared),after_sha256=sha(prepared)))
 plan=dict(status='review_required_not_installed',game_root=str(game),script_sha256=sha(__file__),exe_sha256=EXE_SHA,profile=args.profile,package=str(package),package_manifest_sha256=sha(package/'manifest.json'),source_db=str(src),source_pins=hp,structure_json=str(Path(args.structure_json).resolve()),structure_sha256=sha(args.structure_json),db_name=args.db_name,target_db=str(target),native_T1_uids=[v['club_uid']for v in inv['T1']],archive_steps=steps,limitations=['technical T1 only; no relegation/cups','registration10 not implemented','unchanged native AFC; qualification not tested','global resources require this isolated game root for all later loads'],approval='Run apply-plan --approve-install only after user approves these exact files')
 dest=inside(args.output,HERE);require(not dest.exists(),'Plan exists');write(dest,plan);print(str(dest))

def apply_plan(args):
 require(args.approve_install,'Explicit --approve-install required');planpath=inside(args.plan,HERE);plan=read(planpath);require(plan['script_sha256']==sha(__file__),'Reviewed script changed');require(not running_game(),'Close FM08 and SI editor first');game=Path(plan['game_root']);require(sha(game/'fm.exe')==plan['exe_sha256'],'EXE changed');src=Path(plan['source_db']);require(pins(src)==plan['source_pins'],'DB source changed');require(sha(plan['structure_json'])==plan['structure_sha256'],'Structure evidence changed');inventory(src,plan['structure_json']);target=inside(plan['target_db'],game/'Dane/db');require(not target.exists(),'DB output exists');steps=plan['archive_steps']
 require({str(Path(s['target']).resolve())for s in steps}=={str((game/k).resolve())for k in ARCHIVES},'Unexpected install targets')
 require(sha(Path(plan['package'])/'manifest.json')==plan['package_manifest_sha256'],'Package manifest changed')
 for s in steps:require(sha(s['target'])==s['before_sha256']and sha(s['prepared'])==s['after_sha256'],'Install archive pin mismatch')
 receipt_dir=HERE/'backups'/uuid.uuid4().hex;receipt_dir.mkdir(parents=True);receipt=dict(status='in_progress',plan=plan,plan_sha256=sha(planpath),backups=[])
 for i,s in enumerate(steps):
  backup=receipt_dir/('archive-'+str(i)+'.efa');shutil.copy2(s['target'],backup);require(sha(backup)==s['before_sha256'],'Backup mismatch');receipt['backups'].append(dict(**s,backup=str(backup)))
 write(receipt_dir/'receipt.json',receipt)
 try:
  shutil.copytree(src,target);require(pins(target)==plan['source_pins'],'DB copy mismatch');xmls=list(target.glob('*.xml'));require(len(xmls)==1,'DB metadata XML ambiguous');tree=ET.parse(xmls[0])
  for e in tree.getroot().iter('string'):
   if e.get('id')=='name':e.set('value',plan['db_name'])
   if e.get('id')=='description':e.text=plan['db_name']
  old=xmls[0];new=target/(plan['db_name']+'.xml');tmp=target/'metadata.thai-pilot.tmp';tree.write(tmp,encoding='utf-8',xml_declaration=True);old.unlink();os.replace(tmp,new)
  for s in steps:
   t=Path(s['target']);tmp=t.with_name(t.name+'.thai-'+uuid.uuid4().hex+'.tmp');shutil.copyfile(s['prepared'],tmp);require(sha(tmp)==s['after_sha256'],'Staging archive mismatch');os.replace(tmp,t)
  require(all(sha(s['target'])==s['after_sha256']for s in steps),'Installed archive mismatch');require(pins(src)==plan['source_pins'],'Source DB mutated');receipt.update(status='installed_runtime_unverified',target_db_pins=pins(target));write(receipt_dir/'receipt.json',receipt)
 except BaseException:
  for s in receipt['backups']:
   shutil.copyfile(s['backup'],s['target']);require(sha(s['target'])==s['before_sha256'],'Emergency restore failed')
  receipt['status']='failed_archives_restored_new_db_retained_for_diagnostics';write(receipt_dir/'receipt.json',receipt);raise
 print(str(receipt_dir/'receipt.json'))

def rollback(args):
 require(args.approve_rollback,'Explicit --approve-rollback required');path=inside(args.receipt,HERE);r=read(path);require(r['status']=='installed_runtime_unverified','Unexpected receipt status');require(not running_game(),'Close FM08 and SI editor first')
 for s in r['backups']:require(sha(s['target'])==s['after_sha256']and sha(s['backup'])==s['before_sha256'],'Rollback would overwrite external changes')
 for s in r['backups']:shutil.copyfile(s['backup'],s['target']);require(sha(s['target'])==s['before_sha256'],'Rollback verification failed')
 r['status']='rolled_back_archives_original_DB_copy_retained';write(path,r);print('Original archives restored; new test DB copy retained, no accepted database deleted')

def cli():
 p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='cmd',required=True)
 b=s.add_parser('build');b.add_argument('--output',required=True);b.add_argument('--source-db',required=True);b.add_argument('--source-pins',required=True);b.add_argument('--structure-json',required=True);b.set_defaults(run=build)
 b=s.add_parser('plan-install');b.add_argument('--package',required=True);b.add_argument('--profile',choices=['T1','T1_T2_DRAFT'],default='T1');b.add_argument('--game-root',required=True);b.add_argument('--source-db',required=True);b.add_argument('--source-pins',required=True);b.add_argument('--structure-json',required=True);b.add_argument('--db-name',required=True);b.add_argument('--output',required=True);b.set_defaults(run=plan_install)
 b=s.add_parser('apply-plan');b.add_argument('--plan',required=True);b.add_argument('--approve-install',action='store_true');b.set_defaults(run=apply_plan)
 b=s.add_parser('rollback');b.add_argument('--receipt',required=True);b.add_argument('--approve-rollback',action='store_true');b.set_defaults(run=rollback)
 a=p.parse_args();a.run(a)
if __name__=='__main__':cli()
