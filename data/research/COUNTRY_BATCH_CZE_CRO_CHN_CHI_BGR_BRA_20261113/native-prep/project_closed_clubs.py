from pathlib import Path
import sys,json,csv,hashlib
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8');sys.path.insert(0,'FM08-Database-Tools/scratch')
from create_italy_structure_i1_20261108 import languages,lang_sections
B=Path(__file__).resolve().parent;read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,v):
 p=B/n;assert not p.exists(),p;p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def save(n,rows,fields=None):
 p=B/n;assert not p.exists(),p
 with p.open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)
plan=read(B/'club-plan.json');assert sha(B/'club-plan.json')=='6f0c34b65441cfbddfc45ba08ef78356188b235ff508ffd4e77a22f49ab2a2b3';world=read(B/'native-world-identities.json');wu={x['ClubUID']:x for x in world};en,_=lang_sections(dict(languages((B/'input/X19-after-SI/lang_db.dat').read_bytes()))[8]);fi=len(en['club']);ti=max(x['TeamIndex']for x in read(B/'native-structure.json')['records'])+1
assert fi>max(x['FamilyIndex']for x in world)
used=set(wu)
for values in en.values():
 if isinstance(values,list):used.update(x['uid']for x in values if isinstance(x,dict)and 'uid'in x)
used.update(int(x['ID'])for x in csv.DictReader((B/'audit/players.csv').open(encoding='utf-8-sig')))
nextuid=1800240001;startti=ti;startfi=fi;maps=[];ledger=[];bytm={};kinds=[]
for c in sorted(plan,key=lambda x:(bool(x['ParentTMID']),x['Country'],int(x['TMID']))):
 u=c['NativeClubUID'];new=u is None;parent=bytm.get(c['ParentTMID'])if c['ParentTMID']else None
 if c['ParentTMID']:assert parent is not None
 if new:
  u=nextuid;nextuid+=1;assert u not in used;used.add(u);team=ti;ti+=1;family=parent['FamilyIndex']if parent else fi
  if not parent:fi+=1
  puid=parent['ClubUID']if parent else'';kind=c['RequiredNativeReserveKind']if parent else 0
 else:
  w=wu[u];team=w['TeamIndex'];family=w['NameFamilyIndex']if w['NameFamilyIndex']is not None else w['TeamTailFamilyIndex'];puid=w['ParentUID']or'';kind=w['NativeTeamKind']
 row=dict(ClubName=c['Name'],ClubUID=u,TeamIndex=team,FamilyIndex=family,CountryIndex=c['NativeCountryIndex'],DivisionIndex=c['DesiredDivision'],Group=c['Country']+' '+str(c['DesiredDivision']),RealLeague=c['RealLevel'],Country=c['Country'],TMID=c['TMID'],Kind='projected_new_linked_reserve'if new and parent else'projected_new_first_team'if new else'existing_native_entity',ParentUID=puid,SourceParentTMID=c['ParentTMID'],IdentityDecision=c['IdentityDecision'],ProjectionOnly=new)
 maps.append(row);bytm[c['TMID']]=row;ledger.append(dict(TMID=c['TMID'],ClubUID=u,TeamIndex=team,FamilyIndex=family,IsNew=new,NativeTeamKind=kind,SourceParentTMID=c['ParentTMID'],NativeFamilyParentUID=puid,NativeCountryRepairTo=c['NativeCountryRepairTo'],DesiredDivision=c['DesiredDivision'],DesiredAlternative=c['DesiredAlternative'],DesiredRegional=-1,NativeMaterialization='PENDING'if new else'X19_after_SI_verified'))
 if new and parent:kinds.append(dict(TMID=c['TMID'],Name=c['Name'],Country=c['Country'],ParentTMID=c['ParentTMID'],ParentUID=puid,ProjectedClubUID=u,ProjectedTeamIndex=team,ProjectedFamilyIndex=family,RequiredNativeReserveKind=kind,Reason=c['ReserveKindEvidence']))
assert len(maps)==338 and sum(x['IsNew']for x in ledger)==92 and len(set(x['ClubUID']for x in maps))==338
save('club-map.csv',maps);save('foreign-owner-map.csv',[],list(maps[0]));dump('club-UID-projection.json',dict(status='ROOT_APPROVED_PLAN_PINNED_PROJECTION_NOT_NATIVE_MATERIALIZATION',source_pins=read(B/'source-freeze.json')['hashes'],PlanSHA256=sha(B/'club-plan.json'),UIDrange=[1800240001,nextuid-1],rows=ledger,no_native_data_changed=True,CoreSourceClubs=338,RootStructuralExtrasAppendOnly=True,SourceNextTEAM=startti,SourceNextFamily=startfi,NextFreeClubUID=nextuid,NextFreeTEAMindex=ti,NextFreeFamilyIndex=fi,ActualSourceFAMILYCount=startfi))
dump('reserve-kind-overlay.json',dict(Status='ROOT_APPROVED_NEW_ROLE_DECLARATIONS_NO_CONVERSIONS',Rows=kinds,WitnessFile=str(B/'reserve-kind-source-witnesses.json'),WitnessSHA256=sha(B/'reserve-kind-source-witnesses.json'),PlanSHA256=sha(B/'club-plan.json'),ProjectionSHA256=sha(B/'club-UID-projection.json'),RuntimePending=True))
dump('projection-ready.json',dict(Status='READY_FOR_ROOT_NATIVE_STRUCTURE_CONFIG',Clubs=338,NewTEAM=92,NewFAMILY=fi-startfi,CoreSourceSlotCount=338,SeparatePreservedPhysicalSlots=6,NativeWrite=False,Pins={n:sha(B/n)for n in ['club-map.csv','foreign-owner-map.csv','club-UID-projection.json','reserve-kind-overlay.json','core-assignments.json','structural-fallbacks.json','foreign-owner-plan.json','foreign-owner-aliases.json']}))
print('PROJECTED',338,'new92','family',fi-startfi,'TEAMnext',startti,ti,'FAMILYnext',startfi,fi,'UIDnext',nextuid);print('READY_SHA256',sha(B/'projection-ready.json'));print('PROJECTION_SHA256',sha(B/'club-UID-projection.json'));print('KIND_SHA256',sha(B/'reserve-kind-overlay.json'))
