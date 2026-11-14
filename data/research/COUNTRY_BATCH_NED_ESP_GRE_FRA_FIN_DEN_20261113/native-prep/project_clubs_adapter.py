from pathlib import Path
from collections import Counter
import json,csv,hashlib,sys
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(n,v):(B/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def save(n,rows):
 with(B/n).open('w',encoding='utf-8-sig',newline='')as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
plan=read(B/'club-plan.json');world=read(B/'native-world-identities.json');wu={x['ClubUID']:x for x in world};ti=max(x['TeamIndex']for x in world)+1;fi=max(x['FamilyIndex']for x in world)+1;nextuid=1800220001;used={x['ClubUID']for x in world};maps=[];ledger=[];bytm={}
for c in sorted(plan,key=lambda x:(bool(x['ParentTMID']),x['Country'],int(x['TMID']))):
 u=c['NativeClubUID'];isnew=u is None;parent=bytm.get(c['ParentTMID'])if c['ParentTMID']else None
 if c['ParentTMID']and parent is None:raise AssertionError(('Unresolved projected parent',c['TMID'],c['ParentTMID']))
 if isnew:
  u=nextuid;nextuid+=1;assert u not in used;used.add(u);team=ti;ti+=1;family=parent['FamilyIndex']if parent else fi
  if not parent:fi+=1
  puid=parent['ClubUID']if parent else''
  kind=int(c.get('RequiredNativeReserveKind')or(16 if parent and c['Country']=='Netherlands'else 3 if parent else 0))
 else:
  w=wu[u];team=w['TeamIndex'];family=w['NameFamilyIndex']if w['NameFamilyIndex']is not None else w['TeamTailFamilyIndex'];puid=w['ParentUID']or'';kind=w['NativeTeamKind']
 c.update(ProjectedClubUID=u,ProjectedTeamIndex=team,ProjectedFamilyIndex=family,ProjectedNativeKind=kind)
 row=dict(ClubName=c['Name'],ClubUID=u,TeamIndex=team,FamilyIndex=family,CountryIndex=c['NativeCountryIndex'],DivisionIndex='',Group='root_allocation_pending',RealLeague=c['RealLevel'],Country=c['Country'],TMID=c['TMID'],Kind='projected_new_linked_reserve'if isnew and parent else'projected_new_first_team'if isnew else'existing_native_entity',ParentUID=puid,SourceParentTMID=c['ParentTMID'],IdentityDecision=c['IdentityDecision'],ProjectionOnly=isnew)
 maps.append(row);bytm[c['TMID']]=row;ledger.append(dict(TMID=c['TMID'],ClubUID=u,TeamIndex=team,FamilyIndex=family,IsNew=isnew,NativeTeamKind=kind,SourceParentTMID=c['ParentTMID'],NativeFamilyParentUID=puid,NativeMaterialization='PENDING'if isnew else'X17_postSI_verified'))
assert len(maps)==602 and len({r['ClubUID']for r in maps})==602
save('club-map.csv',maps);dump('club-plan.json',plan);dump('club-UID-projection.json',dict(status='pinned_projection_not_native_materialization',source_pins=read(B/'source-freeze.json')['hashes'],UIDrange=[1800220001,nextuid-1],rows=ledger,no_native_data_changed=True,CoreSourceClubs=602,RootStructuralExtrasAppendOnly=True,NextFreeClubUID=nextuid,NextFreeTEAMindex=ti,NextFreeFamilyIndex=fi,VenueUIDstart=1800230001))
with(B/'foreign-owner-map.csv').open('w',encoding='utf-8-sig',newline='')as f:csv.DictWriter(f,fieldnames=list(maps[0])).writeheader()
dump('foreign-owner-projection.json',dict(status='no_new_foreign_owner_families_unresolved_actors_defer',rows=[]))
print('PROJECTED_CORE',len(maps),'new',sum(x['IsNew']for x in ledger),'UIDrange',1800220001,nextuid-1,'next',nextuid,ti,fi,flush=True)