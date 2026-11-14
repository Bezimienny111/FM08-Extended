from pathlib import Path
import copy,csv,hashlib,itertools,json,shutil,sys,xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
import pol3_efa_r8_20261107 as efa
OUT=ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_FATES_R9_20261107'
R8=ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_PROTOTYPE_R8_20261107'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def hashes(p):return {str(x.relative_to(p)):sha(x) for x in p.rglob('*') if x.is_file()}
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def dump(root):
 root=copy.deepcopy(root);ET.indent(root,space='  ')
 return ET.tostring(root,encoding='utf-8',xml_declaration=True)+b'\n'
def readxml(p):return ET.fromstring(p.read_bytes())
def prop(root,key):
 items=[x for x in root if x.get('id')==key];assert len(items)==1,(root.tag,key,len(items));return items[0]
def val(root,key):return prop(root,key).get('value')
m=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
assert m['status']=='database_built_resources_in_progress'
assert not (OUT/'resources').exists(),'Refuse overwrite resource build'
# Preserve country settings and factories; only make required lower population exact100.
country=readxml(OUT/'input/resources-r8/pol.xml')
assert [int(x.get('competition')) for x in prop(country,'division_levels')]==[129558,129559,1800001000]
assert not any(x.get('id')=='competitions' for x in country)
required=prop(country,'required_teams');lower_req=next(x for x in required if x.get('competition')=='129560')
lower_req.attrib.clear();lower_req.set('competition','129560');lower_req.set('number_teams','100')
league=readxml(OUT/'promotion/pol_third-promotion.xml');stages=prop(league,'stages');regular=next(x for x in stages if x.get('id')=='leag')
fragment=readxml(OUT/'lower-boundary/league-lower-boundary.xml')
for x in fragment:assert not any(y.get('id')==x.get('id') for y in regular);regular.append(copy.deepcopy(x))
survival=readxml(OUT/'lower-boundary/survival-stage.xml');assert survival.get('index')=='2';stages.append(survival)
lower=readxml(OUT/'lower-boundary/pol_lower.xml')
assert val(league,'level')=='2' and val(lower,'level')=='3'
assert [x.get('index') for x in stages]==['0','1','2']
assert len({x.get('id') for x in stages})==3
assert val(regular,'number_teams')=='18' and val(regular,'number_rounds')=='2'
promotion=prop(regular,'promotion');assert promotion.attrib==dict(id='promotion',number_places='2',competition='129559',min_places='3',max_places='3')
relegation=prop(regular,'relegation');assert relegation.attrib==dict(id='relegation',number_places='4',competition='129560',min_places='4',max_places='6')
assert prop(regular,'top_playoff').get('number_places')=='4'
assert prop(regular,'bottom_playoff').get('number_places')=='2'
ls=prop(lower,'stages');groups=next(x for x in ls if x.get('id')=='grou');prelim=next(x for x in ls if x.get('id')=='lpre')
assert val(groups,'number_groups')=='4' and val(groups,'number_teams')=='25' and val(groups,'number_rounds')=='2'
assert val(prop(prelim,'teams')[0],'randomise_teams')=='true'
assert val(prop(groups,'schedule')[0],'number_dates')=='50'
assert len(prop(survival,'rounds'))==1 and val(prop(survival,'rounds')[0],'number_legs')=='2'
assert len(prop(survival,'fate_actions'))==4
# All stage dependencies/selectors refer to existing stages and correctly marked next-round names.
lookup={1800001000:{x.get('id'):x for x in stages},129560:{x.get('id'):x for x in ls}}
links=[]
for uid,items in lookup.items():
 for sid,stage in items.items():
  for req in stage.findall("list[@id='requirements']/record"):
   target=int(req.get('competition',uid));assert req.get('stage') in lookup[target]
   links.append([uid,sid,target,req.get('stage')])
  for selector in stage.findall("list[@id='teams']/record"):
   if val(selector,'id')=='get_qualified_teams':
    target=int(val(selector,'competition'));assert val(selector,'stage') in lookup[target]
  for action in stage.findall("list[@id='fate_actions']/record[@type='set_league_fate']"):
   target=int(action.get('competition'));assert action.get('stage') in lookup[target]
# Qualification graph may add a display-only virtual stage; executable requirements must be acyclic.
edge={(a,b):[] for a,items in lookup.items() for b in items}
for a,b,c,d in links:edge[(a,b)].append((c,d))
def visit(node,path):
 assert node not in path,('cycle',node,path)
 for dependency in edge[node]:visit(dependency,path+[node])
for node in edge:visit(node,[])
# Independent native reader: exactly the same23394 clubs/fields as acceptedR8.
def snapshot(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return {int(x['ClubUID']):x for x in csv.DictReader(f)}
before=snapshot(R8/'native-after-clubs.csv');after=snapshot(OUT/'native-after-clubs.csv')
assert len(before)==len(after)==23394 and set(before)==set(after)
for uid,a in after.items():assert {k:v for k,v in a.items() if k!='SourceServerSHA256'}=={k:v for k,v in before[uid].items() if k!='SourceServerSHA256'}
counts={str(i):sum(x['CurrentDivisionIndex']==str(i) for x in after.values()) for i in (139,140,141,1332)}
assert counts=={'139':16,'140':18,'141':100,'1332':18}
# Exhaustively model promotion8outcomes, lower preliminary24draworders*4results, survival4results.
second=set(uid for uid,x in after.items() if x['CurrentDivisionIndex']=='140')
third_order=[int(x['ClubUID']) for x in csv.DictReader((OUT/'participants.csv').open(encoding='utf-8-sig',newline=''))]
assert len(set(third_order))==18;third=set(third_order)
pool=sorted(uid for uid,x in after.items() if x['CurrentDivisionIndex']=='141');assert len(pool)==100
model_groups=[pool[i*25:(i+1)*25] for i in range(4)]
champions={x[0] for x in model_groups};runners=[x[1] for x in model_groups]
second_down=set(sorted(second)[-3:]);direct_up=set(third_order[:2]);direct_down=set(third_order[14:]);upper_survival=third_order[12:14]
case_count=0;relegation_counts=set();directed_pairs=set()
for left in (2,5):
 for right in (3,4):
  finalists=[third_order[left],third_order[right]]
  for playoff_winner in finalists:
   promoted=direct_up|{playoff_winner};assert len(promoted)==3
   for draw in itertools.permutations(runners):
    directed_pairs.add((draw[0],draw[1]));directed_pairs.add((draw[2],draw[3]))
    for pa,pb in itertools.product((0,1),repeat=2):
     lower_finalists=[draw[pa],draw[2+pb]]
     for lower_a,lower_b in itertools.product((False,True),repeat=2):
      lower_winners={x for x,w in zip(lower_finalists,(lower_a,lower_b)) if w}
      upper_losers={x for x,w in zip(upper_survival,(lower_a,lower_b)) if w}
      up_from_pool=champions|lower_winners;down_to_pool=direct_down|upper_losers
      new_second=(second-second_down)|promoted
      new_third=(third-promoted-down_to_pool)|second_down|up_from_pool
      new_pool=(set(pool)-up_from_pool)|down_to_pool
      assert len(new_second)==18 and len(new_third)==18 and len(new_pool)==100
      assert not(new_second&new_third or new_second&new_pool or new_third&new_pool)
      assert new_second|new_third|new_pool==second|third|set(pool)
      assert 4<=len(down_to_pool)<=6 and len(down_to_pool)==len(up_from_pool)
      relegation_counts.add(len(down_to_pool));case_count+=1
assert case_count==3072 and relegation_counts=={4,5,6} and len(directed_pairs)==12
model=dict(status='mathematical_and_resource_consistency_passed_not_game_verified',cases=case_count,preliminary_orderings=24,possible_directed_preliminary_pairs=12,promotion_outcomes=8,survival_outcomes=4,relegation_counts=sorted(relegation_counts),all_populations_preserved=counts,all_identities_conserved=True,all_competitions_disjoint=True,stage_dependency_graph_acyclic=True,stage_links=links,native_clubs_read=23394,native_club_fields_unchanged_from_R8=True,game_verified=False)
save(OUT/'format-and-resource-model-check.json',model)
resources=OUT/'resources';resources.mkdir()
payloads={'pol/pol.xml':dump(country),'pol/pol_third.xml':dump(league),'pol/pol_lower.xml':dump(lower)}
for path,data in payloads.items():(resources/Path(path).name).write_bytes(data)
original_path=ROOT/'data/updates/update-802/data/comps.efa'
assert sha(original_path)==m['protected_original_hashes']['data\\updates\\update-802\\data\\comps.efa']
original=efa.parse(original_path.read_bytes());frozen_r8=efa.parse((OUT/'input/resources-r8/comps.efa').read_bytes())
assert len(original['members'])==7 and set(frozen_r8['members'])==set(original['members'])|{'pol/pol.xml','pol/pol_third.xml'}
assert all(frozen_r8['members'][k]==v for k,v in original['members'].items())
archive=original
for path,data in payloads.items():archive=efa.add_member(archive,path,data)
packed=efa.repack(archive);check=efa.parse(packed)
assert len(check['members'])==10 and all(check['members'][k]==v for k,v in original['members'].items())
assert all(check['members'][k]==v for k,v in payloads.items())
(resources/'comps.efa').write_bytes(packed)
private=OUT/'runtime/data/updates/update-802/data/comps.efa'
assert sha(private)==sha(OUT/'input/resources-r8/comps.efa')
shutil.copy2(resources/'comps.efa',private)
assert sha(private)==sha(resources/'comps.efa')
assert hashes(Path(m['source_database']))==m['source_database_hashes']
assert hashes(R8/'resources')==m['source_resource_hashes']
assert hashes(OUT/'user-data/db/TEST_POL_3_LEVEL_R9')==m['database_output_hashes']
for rel,expected in m['protected_original_hashes'].items():assert sha(ROOT/rel)==expected
report=dict(status='resources_built_and_model_verified',native_reader_clubs=23394,club_fields_identical_to_R8=True,division_counts=counts,original_archive_members_preserved=7,output_archive_members=10,resource_hashes=hashes(resources),model_cases=case_count,source_R8_unchanged=True,original_exe_unchanged=True,game_verified=False)
save(OUT/'resource-build.json',report)
m.update(status='resources_built_validation_pending',runtime_comp_archive_sha256=sha(private),resource_hashes=report['resource_hashes'],division_counts=counts,model_cases=case_count,pilot_tool_sha256=sha(OUT/'tools/PolandThirdTierFatesR9.exe'),game_verified=False)
save(OUT/'manifest.json',m)
print(json.dumps({'status':report['status'],'model_cases':case_count,'archive_members':10,'original_members_preserved':7,'native_club_count':23394,'division_counts':counts,'R8_unchanged':True}),flush=True)
