"""Concrete allocation only; cached world identity reused, no world audit/DB write."""
from pathlib import Path
from collections import Counter
import sys,json,hashlib,struct,copy
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';N=R/'COUNTRY_BATCH_CZE_CRO_CHN_CHI_BGR_BRA_20261113/native-prep';O=Path(__file__).resolve().parent
rd=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
cat=rd(N/'competition-catalog.json');idx={v['index']:v['uid']for v in cat};toidx={v:k for k,v in idx.items()};idx[-1]=None;toidx[None]=-1
freeze=rd(N/'source-freeze.json');world={v['ClubUID']:v for v in rd(N/'native-world-identities.json')};cache=O/'source-raw3-cache.json'
if cache.exists():
 data=rd(cache);assert data['SourceServerSHA256']==freeze['hashes']['server_db.dat'];raw={int(k):v for k,v in data['Raw'].items()}
else:
 sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'));from create_italy_structure_i1_20261108 import load
 src=Path(freeze['frozen']);assert sha(src/'server_db.dat')==freeze['hashes']['server_db.dat'];buf=load(src,'server_db.dat');raw={}
 for row in rd(N/'native-structure.json')['records']:
  u=row['ClubUID'];assert struct.unpack_from('<iI',buf,row['Footer'])==(row['TeamIndex'],u)
  vals=[struct.unpack_from('<i',buf,row['Start']+s)[0]for s in(7,15,47)];assert vals[0]==world[u]['CurrentDivision'];assert all(v in idx for v in vals);raw[u]=vals
 assert sha(src/'server_db.dat')==freeze['hashes']['server_db.dat'];dump(cache.name,dict(SourceServerSHA256=freeze['hashes']['server_db.dat'],Raw=raw))
projection=rd(N/'club-UID-projection.json')['rows'];bytm={v['TMID']:v for v in projection};plan={v['TMID']:v for v in rd(N/'club-plan.json')};core=rd(N/'core-assignments.json');fallback=rd(N/'structural-fallbacks.json');qs=rd(N/'qa-root/requirements.json')['NativeCurrentBatch'];qmap={(toidx[q['uid']],q['form']):q for q in qs}
country={u:v['TeamCountry']if v['TeamCountry']is not None and v['TeamCountry']>=0 else None for u,v in world.items()};kind={u:v['NativeTeamKind']for u,v in world.items()};before=copy.deepcopy(raw);bc=country.copy();target=copy.deepcopy(raw);reasons={};assignments=[]
def setslot(u,slot,after,reason):
 if target[u][slot]!=after:target[u][slot]=after;reasons[u,slot]=reason
coreuids=set();country_owner={};newteams=[];countryrepairs=[];BRAnational={73,85,86}
for a in core:
 row=bytm[a['TMID']];u=row['ClubUID'];p=plan[a['TMID']];coreuids.add(u);country_owner[p['NativeCountryIndex']]=p['Country'];ci=p['NativeCountryRepairTo']or p['NativeCountryIndex']
 if row['IsNew']:target[u]=[-1,-1,-1];country[u]=ci;kind[u]=row['NativeTeamKind'];newteams.append(u)
 elif p['NativeCountryRepairTo']is not None:countryrepairs.append(dict(uid=u,before=country[u],after=p['NativeCountryRepairTo'],TMID=a['TMID']));country[u]=p['NativeCountryRepairTo']
 original=list(target[u]);setslot(u,0,a['DesiredDivision'],'accepted_closed_classic_source_allocation');setslot(u,1,a['DesiredAlternative'],'accepted_closed_current_ALT_allocation')
 if p['Country']=='Brazil'and not row['IsNew']:
  reg=original[2]if original[2]>=0 else(original[0]if original[0]>=0 and original[0]not in BRAnational and original[0]!=550 else -1)
  setslot(u,2,reg,'preserve_existing_Brazil_state_or_lower_membership_on_national_move')
 elif row['IsNew']:setslot(u,2,a['DesiredRegional'],'new_TEAM_regional_default')
 assignments.append(dict(TMID=a['TMID'],ClubUID=u,Country=p['Country'],NativeCountryIndex=ci,Kind=kind[u],IsNew=row['IsNew'],Raw=target[u],DesiredSourceRaw=[a['DesiredDivision'],a['DesiredAlternative'],a['DesiredRegional']]))
for a in fallback:
 u=a['NativeClubUID'];coreuids.add(u);setslot(u,0,a['DesiredDivision'],'accepted_structural_fallback_without_person_import');setslot(u,1,a['DesiredAlternative'],'fallback_effective_current')
 if a['Country']=='Brazil'and before[u][2]==-1 and before[u][0]>=0 and before[u][0]not in BRAnational and before[u][0]!=550:setslot(u,2,before[u][0],'preserve_Brazil_state_on_fallback_national_move')
 assignments.append(dict(TMID=None,ClubUID=u,Country=a['Country'],NativeCountryIndex=country[u],Kind=kind[u],IsNew=False,Raw=target[u],StructuralFallback=True))
playable={207,208,144,145,195,201,590,591,804,854,855,73,85,86}
for u,vals in list(target.items()):
 if u in coreuids:continue
 if vals[0]in playable:setslot(u,0,146 if country[u]==135 else 550,'displaced_legacy_preserved_below_closed_modern_playable_field');setslot(u,1,-1,'displaced_legacy_ALT_follows_final_Current')
nedpath=R/'X19_RUNTIME_ERROR_20261113/reserve-eligibility-review/minimal-data-repair/approved-12-team-moves.json';ned=rd(nedpath)
for a in ned['Moves']:
 u=a['ClubUID'];assert before[u]==[a['Before'],a['AlternateBefore'],a['RegionalBefore']];setslot(u,0,a['After'],'approved_NED12_'+a['Role'])
def counts(state):
 c=[Counter(),Counter()]
 for u,(cur,alt,regional)in state.items():
  if country[u]is None:continue
  for f,selected in enumerate((cur,alt if alt>=0 else cur)):
   if selected>=0:c[f][selected]+=1
   if regional>=0:c[f][regional]+=1
 return c
def checks(state):
 c=counts(state)
 return[dict(q,index=toidx[q['uid']],Count=c[q['form']][toidx[q['uid']]],Passed=c[q['form']][toidx[q['uid']]]>=q['minimum']and(q['maximum']is None or c[q['form']][toidx[q['uid']]]<=q['maximum']))for q in qs]
initial=checks(target);dump('initial-projection-checks.json',initial)
print(json.dumps(dict(InitialFailures=[dict(index=q['index'],form=q['form'],n=q['Count'],lo=q['minimum'],hi=q['maximum'])for q in initial if not q['Passed']],SourceCollisions=[dict(UID=u,Raw=v)for u,v in before.items()if country[u]==189 and v[0]==v[2]and v[0]>=0],NewTEAM=len(newteams))),flush=True)
dump('simulation-state.json',dict(SourceRaw=before,TargetRaw=target,Country=country,Kind=kind,CoreUIDs=sorted(coreuids),NewTEAM=newteams,CountryRepairs=countryrepairs,Assignments=assignments,Reasons=[dict(UID=u,Slot=s,Reason=r)for(u,s),r in reasons.items()]))

# Existing first teams retained structurally, with geographic Czech lower pools.
for u,d,why in [(470,221,'CFL_Bohemia_Ceske_Budejovice'),(136151,221,'CFL_Bohemia_Most'),(136152,222,'MSFL_Moravia_Vitkovice'),(136155,222,'MSFL_Moravia_Olomouc_Holice')]:
 assert u not in coreuids and country[u]==137 and kind[u]==0 and before[u][0]in(207,208)and target[u][0]==550
 setslot(u,0,d,'technical_retained_legacy_lower_backfill_'+why);setslot(u,1,-1,'retained_legacy_effective_Current_ALT')
for u in(415,5625398,23003359):
 assert u not in coreuids and country[u]==55 and before[u][1]==201 and target[u][0]in(482,483)
 setslot(u,1,-1,'remove_stale_legacy_China_First_ALT_preserve_raw_lower_Current')
final=checks(target);assert all(q['Passed']for q in final),[(q['index'],q['form'],q['Count'])for q in final if not q['Passed']]
rawbefore=Counter(v[0]for v in before.values());rawafter=Counter(v[0]for v in target.values());delta={str(i):rawafter[i]-rawbefore[i]for i in sorted(set(rawbefore)|set(rawafter))if rawafter[i]!=rawbefore[i]}
movegroups={group:[dict(ClubUID=u,Before=before[u][slot],After=v[slot],Reason=reasons[u,slot])for u,v in sorted(target.items())if u in before and before[u][slot]!=v[slot]]for slot,group in enumerate(('moves','alternate_moves','regional_moves'))}
# Writer counts raw Current only. Exact projection counters are separate from
# all190 native selected+Regional requirements, retained unmodified in output.
raw_indices={toidx[q['uid']]for q in qs if q['form']==0}|{a['Before']for a in ned['Moves']}|{a['After']for a in ned['Moves']}
rawreq=[dict(index=i,uid=idx[i],min=rawafter[i],max=rawafter[i],country_scope=None,Qualification='Exact raw_Current count of this closed projection; native selected_plus_Regional limits checked independently in native-requirements190.json')for i in sorted(raw_indices)if i>=0]
cfg=dict(**movegroups,requirements=rawreq,expected_count_deltas=delta)
dump('structure-config.json',cfg);dump('native-requirements190.json',qs);dump('simulated-native-checks.json',final)
dump('allocation344.json',assignments)
dump('target-manifest-declarations.json',dict(new_teams=[dict(uid=u,raw=[idx[d]for d in target[u]],country=country[u],kind=kind[u])for u in newteams],country_changes=[{k:v for k,v in r.items()if k!='TMID'}for r in countryrepairs],kind_changes=[]))
regional=[dict(m,ClubNames=world[m['ClubUID']]['Names'][:2])for m in movegroups['regional_moves']]
assert all(country[m['ClubUID']]==189 for m in regional)
assert all(before[u][2]==target[u][2]for u in before if country[u]!=189)
assert all(before[u][2]==target[u][2]for u in before if country[u]==189 and before[u][2]>=0)
allstate={toidx[q['uid']]for q in qs if q['form']==0 and toidx[q['uid']]not in(73,85,86)and q['uid']in{r['CompetitionUID']for r in rd(N.parent/'competition-prep/native-competition-requirements.json')['requirements']if r['Country']=='Brazil'}}
statechecks=[q for q in final if q['index']in allstate]
assert len(statechecks)==108 and all(q['Passed']for q in statechecks)
report=dict(Status='READY_CONCRETE_CONFIG_SIMULATED_NATIVE190_PASS_TARGET_NOT_WRITTEN',AllocationMain=338,StructuralFallbacks=6,NewTEAM=len(newteams),CurrentMoves=len(cfg['moves']),AlternateMoves=len(cfg['alternate_moves']),RegionalMoves=len(regional),RegionalMoveDetails=regional,NewNativeChecks=190,NewNativeFailures=0,BrazilStateLowerChecks=108,BrazilStateLowerFailures=0,ChinaChecks=[q for q in final if q['index']in(195,201,482,483)],CzechLowerBackfillUIDs=[470,136151,136152,136155],ChinaStaleALTUIDs=[415,5625398,23003359],CountryRepairs=countryrepairs,NEDApprovedMoves=len(ned['Moves']),RootWriterRawCurrentRequirements=len(rawreq),NativeRequirementQualification='All190 D35180 bank conditions preserved separately; writer exact rawCurrent counters are not a replacement for native selected+Regional counters',ExpectedRawCurrentDeltas=delta,SourceRawRead='One compressed server read via existing loader, all24131 footer anchors/current match cached world; subsequent preparation reuses source-raw3-cache. No typed world audit repeated',SourcePins={str(p):sha(p)for p in[N/'source-freeze.json',N/'club-plan.json',N/'core-assignments.json',N/'structural-fallbacks.json',N/'club-UID-projection.json',N/'native-world-identities.json',N/'native-structure.json',nedpath,O/'source-raw3-cache.json']},DBWrite=False,TargetRead=False,Scope='Prewrite simulation only; scheduler/SI/newcareer/season remain independent')
dump('configuration-ready.json',report)
print(json.dumps({k:report[k]for k in('Status','AllocationMain','StructuralFallbacks','NewTEAM','CurrentMoves','AlternateMoves','RegionalMoves','NewNativeChecks','NewNativeFailures','BrazilStateLowerChecks','RootWriterRawCurrentRequirements')}),flush=True)
