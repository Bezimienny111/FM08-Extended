from pathlib import Path
from collections import Counter
import json,csv,sys,hashlib,shutil,ast,subprocess
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent;S=B.parent;OLD=R/'COUNTRY_BATCH_CZE_CRO_CHN_CHI_BGR_BRA_20261113/native-prep'
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
from create_italy_structure_i1_20261108 import languages,lang_sections
rd=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,v):(B/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def save(name,vs,fields=None):
 with (B/name).open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.DictWriter(f,fieldnames=fields or list(vs[0]));w.writeheader();w.writerows(vs)
assert rd(B/'allocation-projection.json')['Status']=='PROJECTION_PASS';assert not(B/'club-UID-projection.json').exists()
world={x['ClubUID']:x for x in rd(B/'native-world-identities.json')};plan=rd(B/'club-plan-allocated.json');en,_=lang_sections(dict(languages((B/'input/X20-after-SI/lang_db.dat').read_bytes()))[8]);fi=len(en['club']);ti=max(x['TeamIndex']for x in world.values())+1;startfi=fi;startti=ti
used=set(world)
for values in en.values():
 if isinstance(values,list):used.update(x['uid']for x in values if isinstance(x,dict)and 'uid'in x)
used.update(int(x['ID'])for x in csv.DictReader((B/'audit/players.csv').open(encoding='utf-8-sig')))
nextuid=1800260001;maps=[];ledger=[];bytm={};kinds=[];ordered=[]
for x in sorted(plan,key=lambda x:(bool(x['ParentTMID']),x['Country'],int(x['TMID']))):
 x=dict(x);u=x['NativeClubUID'];new=u is None;parent=bytm.get(x['ParentTMID'])if x['ParentTMID']else None
 if x['ParentTMID']:assert parent is not None
 if new:
  u=nextuid;nextuid+=1;assert u not in used;used.add(u);team=ti;ti+=1;family=parent['FamilyIndex']if parent else fi
  if not parent:fi+=1
  pu=parent['ClubUID']if parent else None;kind=x['RequiredNativeReserveKind']if parent else 0
  x.update(ProjectedClubUID=u,ProjectedTeamIndex=team,ProjectedFamilyIndex=family)
 else:z=world[u];team=z['TeamIndex'];family=z['TeamTailFamilyIndex'];pu=z['ParentUID'];kind=z['NativeTeamKind']
 row=dict(ClubName=x['Name'],ClubUID=u,TeamIndex=team,FamilyIndex=family,CountryIndex=x['NativeCountryIndex'],DivisionIndex=x['DesiredDivision'],Group=x['Country']+' '+str(x['DesiredDivision']),RealLeague=x['RealLevel'],Country=x['Country'],TMID=x['TMID'],Kind='projected_new_linked_reserve'if new and parent else'projected_new_first_team'if new else'existing_native_entity',ParentUID=pu or'',IdentityDecision=x['IdentityDecision'])
 maps.append(row);bytm[x['TMID']]=row;ordered.append(x);ledger.append(dict(TMID=x['TMID'],ClubUID=u,TeamIndex=team,FamilyIndex=family,IsNew=new,NativeTeamKind=kind,NativeParentUID=pu,SourceParentTMID=x['ParentTMID'],DesiredDivision=x['DesiredDivision'],DesiredAlternative=x['DesiredAlternative']))
 if new and parent:kinds.append(dict(TMID=x['TMID'],Name=x['Name'],ParentTMID=x['ParentTMID'],ProjectedClubUID=u,ProjectedTeamIndex=team,ProjectedFamilyIndex=family,RequiredNativeReserveKind=kind))
assert len(maps)==201 and len({x['ClubUID']for x in maps})==201 and sum(x['IsNew']for x in ledger)==39
save('club-map.csv',maps);save('foreign-owner-map.csv',[],list(maps[0]));dump('club-plan.json',ordered);dump('structural-fallbacks.json',rd(B/'structural-fallbacks-allocated.json'))
assign=rd(B/'allocation-projection.json')['Assignments'];assignby={a['TMID']:a for a in assign if a['TMID']}
for x in ordered:assignby[x['TMID']].update(NativeClubUID=x['NativeClubUID'],DesiredCompetitionUID=next(v['uid']for v in rd(B/'competition-catalog.json')if v['index']==x['DesiredDivision']))
dump('core-assignments.json',[assignby[x['TMID']]for x in ordered]);dump('club-UID-projection.json',dict(Status='PINNED_PROJECTION_NOT_MATERIALIZED',SourceNextTEAM=startti,SourceNextFamily=startfi,NextFreeTEAMindex=ti,NextFreeFamilyIndex=fi,NewTEAM=39,NewFAMILY=fi-startfi,UIDrange=[1800260001,nextuid-1],rows=ledger,PlanSHA256=sha(B/'club-plan.json')))
dump('reserve-kind-overlay.json',dict(Status='PRESERVE_EXISTING_ROLES_NEW_ROLE_DECLARATIONS',Rows=kinds,PlanSHA256=sha(B/'club-plan.json'),ProjectionSHA256=sha(B/'club-UID-projection.json')))
# Owners: retain exact existing contract families, including sporting-country exceptions.
explicit={'162':826,'676':138025,'978':339,'1066':1191,'7452':107305,'8023':106063}
alias=[]
for a0 in rd(B/'foreign-owner-aliases-draft.json'):
 a=dict(a0);main=a['CanonicalMainTMID']
 if main in bytm:a.update(NativeClubUID=bytm[main]['ClubUID'],Decision='within_core_closed_identity_and_projection')
 elif main in explicit:
  z=world[explicit[main]];assert z['TeamCountry']==a['NativeCountryIndex'] or main=='162';a.update(NativeClubUID=z['ClubUID'],NativeCountryIndex=z['TeamCountry'],Decision='reuse_explicit_native_identity_country_alias',NativeContractFamilyIndex=z['TeamTailFamilyIndex'])
 elif a.get('NativeClubUID'):
  z=world[a['NativeClubUID']];assert z['TeamCountry']==a['NativeCountryIndex'];a['NativeContractFamilyIndex']=z['TeamTailFamilyIndex']
 else:a['Decision']='defer_unverified_external_owner_preserve_player'
 alias.append(a)
dump('foreign-owner-aliases.json',alias);dump('foreign-owner-plan.json',[])
freeze=rd(B/'source-freeze.json');dump('manifest.json',dict(status='IDENTITIES_PROJECTED_AWAIT_PREPARED_ROSTERS',source=freeze['frozen'],source_original=freeze['source'],source_hashes=freeze['hashes'],countries=['Belarus','Belgium','Austria','Australia','Argentina'],counts=dict(clubs=201,reuse=162,new=39,physical_fallbacks=26),source_SI=True,source_new_career=True,source_season='IN_PROGRESS_TO_2011',NativeWrite=False,SugarDaddy=False))
cal={'Belarus':-30,'Belgium':-10,'Austria':-20,'Australia':-25,'Argentina':-10};code=(OLD/'rating_model_v2.py').read_text(encoding='utf-8-sig');node=next(x for x in ast.parse(code).body if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='COUNTRY_ADJUSTMENT'for t in x.targets));lines=code.splitlines();lines[node.lineno-1]='COUNTRY_ADJUSTMENT='+repr(dict(ast.literal_eval(node.value),**cal));(B/'rating_model_v2.py').write_text('\n'.join(lines)+'\n',encoding='utf-8')
dump('model-configuration.json',dict(ModelVersion='squad-spread-2026-27-v2',CountryCalibration=cal,PreserveCredibleProfilesAndPriorAwards=True,IndividualStableCAAndPASeeds=True,RealSourceLevel=True,DateShift=19,ExplicitProjectEstimates=True,ModelSHA256=sha(B/'rating_model_v2.py')))
p=(OLD/'prepare_players.py').read_text(encoding='utf-8-sig').replace('assert len(am)==338','assert len(am)==201').replace("REF='2026-11-13'","REF='2026-11-14'")
p=p.replace("shared.PRIOR=[R/'COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep/prepared'","shared.PRIOR=[R/'COUNTRY_BATCH_CZE_CRO_CHN_CHI_BGR_BRA_20261113/native-prep/prepared-r3',R/'COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep/prepared'")
p=p.replace("('Brazil',189)","('Brazil',189),('Belarus',132),('Belgium',131),('Austria',129),('Australia',177),('Argentina',187)")
p=p.replace("FamilyIndex=w['FamilyIndex']","FamilyIndex=w['TeamTailFamilyIndex']").replace("CountryIndex=w['Country']","CountryIndex=w['TeamCountry']")
p=p.replace("for country in ['Czech Republic','Croatia','China','Chile','Bulgaria','Brazil']:","for country in ['Belarus','Belgium','Austria','Australia','Argentina']:")
p=p.replace("scope_id='cze-cro-chn-chi-bgr-bra'","scope_id='blr-bel-aut-aus-arg-20261114'").replace('target_country_indices=[137,135,55,190,134,189]','target_country_indices=[132,131,129,177,180,187]').replace('TM_snapshot_2026_11_13','TM_snapshot_2026_11_14')
(B/'prepare_players.py').write_text(p,encoding='utf-8');compile(p,str(B/'prepare_players.py'),'exec')
# Source N4 uses the unchanged latest compiled worker and typed contract evidence.
shutil.copy2(OLD/'tools/ApplyBatchRoster-r2.exe',B/'tools/ApplyBatchRoster.exe');p=(OLD/'preflight_native_N4_final.ps1').read_text(encoding='utf-8-sig').replace('X19-after-SI','X20-after-SI').replace('N4-final-requested-UIDs.json','N4-requested-UIDs.json');(B/'preflight_native_N4.ps1').write_text(p,encoding='utf-8')
if not(B/'future-audit').exists():
 z=subprocess.run([str(B/'tools/AuditNativeFutureTransfers.exe'),freeze['frozen'],str(B/'future-audit'),'2007-07-01'],capture_output=True,text=True,encoding='utf-8',errors='replace');(B/'future-audit.log').write_text(z.stdout+z.stderr,encoding='utf-8');assert z.returncode==0,z.stderr
print('PROJECTION',len(maps),'newTEAM39 newFAMILY',fi-startfi,'owners',Counter(x['Decision']for x in alias),'models configured; future audit complete',flush=True)
