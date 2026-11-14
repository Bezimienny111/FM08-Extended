"""X18 configuration of the existing structural writer; no DAT writes here."""
from pathlib import Path
from collections import Counter
import sys,json,csv,hashlib,struct,zlib,shutil
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev')
B=ROOT/'FmLauncher/data/research/COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113'
P=B/'native-prep';W=P/'root-structure'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def dump(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8-sig',newline='')))
IDN={618:615,617:615,885:616,884:616,886:616,895:616}
OVERSEAS={0xe0004,0xdfff8,0x5a1,0x1f9fc,0xdfffa,0xdfffe,0xe04d9,0xe0006,0xe04d4,0xe04dc,0xe0822}
PROTECTED={2121} # Historical parent FAMILY stays bitwise; its obsolete first TEAM may leave the playable division.
FALLBACK={158:550,170:550,146:151,143:15,142:123,138:474}
def prepare():
 assert __debug__
 m=read(W/'manifest.json');src=Path(m['source'])
 assert not (W/'structure-config.json').exists(),'Preserve previous prepared attempt'
 for k in ['server_db.dat','client_db.dat','lang_db.dat','people_db.dat']:assert sha(src/k)==m['source_hashes'][k]
 raw=zlib.decompress((src/'server_db.dat').read_bytes()[9:])
 world={x['ClubUID']:x for x in read(P/'native-world-identities.json')}
 old={x['ClubUID']:x for x in read(P/'native-structure.json')['records']}
 cat=read(P/'competition-catalog.json');ci={x['index']:x['uid']for x in cat}
 q=read(B/'competition-prep/native-competition-requirements.json')['requirements']
 core=read(P/'club-plan.json');owners=read(P/'foreign-owner-plan.json')
 projection=rows(P/'club-map.csv')+rows(P/'foreign-owner-map.csv')
 bytm={str(x['TMID']):x for x in projection}
 allocations=read(W/'source-allocation/assignments.json')
 assign={str(x['TMID']):x for x in allocations if x.get('TMID')}
 allproposals=read(W/'source-allocation/all-source-tier-proposals.json')
 if isinstance(allproposals,list):
  proposals={str(x['TMID']):x for x in allproposals if x.get('TMID')}
 else:proposals={}
 specs=[]
 for source in core+owners:
  x=dict(source);tid=str(x['TMID'])
  assert tid in bytm,('projection_missing',tid)
  if x.get('NativeImportEligible') is False:continue
  a=assign.get(tid)
  if source in core:
   assert a is not None and a.get('DesiredDivision') is not None,('source_assignment_missing',tid,x['Name'],proposals.get(tid))
   assert not a.get('GroupPending'),('regional_group_pending',tid)
   x['DesiredDivision']=a['DesiredDivision'];x['DesiredAlternative']=a.get('DesiredAlternative')
  else:
   assert x.get('DesiredDivision') is not None,('owner_division_missing',tid)
  pr=bytm[tid]
  x['ProjectedClubUID']=int(pr['ClubUID']);x['ProjectedTeamIndex']=int(pr['TeamIndex']);x['ProjectedFamilyIndex']=int(pr['FamilyIndex'])
  assert x['ProjectedClubUID'] not in PROTECTED
  if x.get('NativeClubUID'):
   u=int(x['NativeClubUID']);x['SourceCountryIndex']=world[u]['TeamCountry']
   if x.get('NativeParentUID'):x['ExistingParentUID']=x['NativeParentUID']
   elif x.get('ParentTMID'):
    x['SourceParentTMID']=x['ParentTMID'];x['ParentTMID']=''
  specs.append(x)
 # Preserve projected order so new TEAM/FAMILY indexes never drift.
 corefixed=[x for x in specs if x.get('Role')!='loan_owner_only']
 ownfixed=[x for x in specs if x.get('Role')=='loan_owner_only']
 corefixed.sort(key=lambda x:(x['ProjectedTeamIndex'] if not x.get('NativeClubUID') else -1,int(x['TMID'])))
 ownfixed.sort(key=lambda x:(x['ProjectedTeamIndex'] if not x.get('NativeClubUID') else -1,int(x['TMID'])))
 planned=corefixed+ownfixed
 new=[x for x in planned if not x.get('NativeClubUID')]
 newtis=[x['ProjectedTeamIndex']for x in new]
 assert newtis==sorted(newtis),('new_TEAM_order_inconsistent',newtis)
 desired={x['ProjectedClubUID']:x['DesiredDivision']for x in planned}
 structural=read(W/'source-allocation/structural-assignments.json')
 for x in structural:
  u=int(x['NativeClubUID']);assert u in old and u not in desired and u in {506,510}
  assert world[u]['NativeTeamKind']==0 and world[u]['TeamCountry']==138
  desired[u]=int(x['DesiredDivision'])
 country={u:x['TeamCountry']for u,x in world.items()}
 kinds={u:x['NativeTeamKind']for u,x in world.items()}
 for x in planned:country[x['ProjectedClubUID']]=x['NativeCountryIndex'];kinds[x['ProjectedClubUID']]=int(x.get('RequiredNativeReserveKind')or 3) if x.get('ParentTMID') else kinds.get(x['ProjectedClubUID'],0)
 cur={u:r['CurrentDivisionIndex']for u,r in old.items()};alt={u:struct.unpack_from('<i',raw,r['Start']+15)[0]for u,r in old.items()};reg={u:struct.unpack_from('<i',raw,r['Start']+47)[0]for u,r in old.items()}
 reasons={};playable={x['CatalogueIndex']for x in q if x['Form0Max']==x['Form0Min']}
 spchildren={i for i,uid in ci.items()if 67023610<=uid<=67023627}
 # Source-backed lower catalogues replace old cohorts; unrelated clubs remain as lower records.
 refreshlower={265,1026}|spchildren|{795}
 technical=read(W/'source-allocation/technical-retained-entries.json')
 keep={int(x.get('NativeUID')or x.get('ClubUID'))for x in technical if x.get('NativeUID')or x.get('ClubUID')}
 for u,r in old.items():
  if u in PROTECTED:continue
  if u in desired:cur[u]=desired[u];reasons[u]='final_source_previous_table_classic_assignment'
  elif r['CurrentDivisionIndex'] in playable|refreshlower and country[u] in FALLBACK and u not in keep:
   cur[u]=FALLBACK[country[u]];reasons[u]='displaced_legacy_team_retained_in_same_country_lower_pool'
 for x in new:
  u=x['ProjectedClubUID'];cur[u]=x['DesiredDivision'];alt[u]=x.get('DesiredAlternative')if x.get('DesiredAlternative') is not None else -1;reg[u]=-1
 for u in keep:
  assert u in old and u not in desired,('technical_keep_conflict',u)
  reasons[u]='explicit_reported_existing_technical_minimum_contributor'
 # Every alternative adjustment is scoped to this batch's actual final membership.
 for u,r in old.items():
  if u in PROTECTED:continue
  if u in desired or alt[u] in playable|refreshlower:
   if alt[u]>=0 and alt[u]!=cur[u]:alt[u]=-1
 nations=read(P/'native-nation-catalog.json')
 if isinstance(nations,dict):
  nations=nations.get('records',nations.get('nations',nations))
 if isinstance(nations,list):
  nu={int(x.get('index',x.get('NationIndex',x.get('Index',-1)))):int(x.get('uid',x.get('NationUID',x.get('UID',0))))for x in nations}
 else:raise AssertionError('nation_catalogue_schema')
 def selected(u,form):
  d=cur[u]
  if kinds[u]==0 and country[u]==58:d=IDN.get(d,d)
  if kinds[u]==0 and country[u]==170 and d in spchildren:d=795
  if nu.get(country[u]) in OVERSEAS:d=550
  return alt[u] if form==1 and alt[u]>=0 else d
 def count(t,form):
  di=t['CatalogueIndex']
  return sum((not t['CountrySpecific'] or country[u]==t['NativeCountryIndex'])and di in {selected(u,form),reg[u]}for u in cur)
 lower=[x for x in q if x['Form0Max'] is None]
 backfills=[]
 for t in lower:
  need=t['Form0Min']-count(t,0)
  if need<=0:continue
  ci0=t['NativeCountryIndex'];target=t['CatalogueIndex']
  eligible=[u for u in old if u not in desired and u not in PROTECTED and u not in keep and kinds[u]==0 and country[u]==ci0 and cur[u]!=target and cur[u] not in playable]
  eligible.sort(key=lambda u:(0 if old[u]['CurrentDivisionIndex']==target else 1,u))
  for u in eligible:
   before=cur[u]
   affected=[z for z in lower if z['CatalogueIndex']==before and (not z['CountrySpecific']or z['NativeCountryIndex']==country[u])]
   if any(count(z,0)<=z['Form0Min'] or count(z,1)<=z['Form1DefaultMin']for z in affected):continue
   cur[u]=target
   if alt[u]>=0 and alt[u]!=target:alt[u]=-1
   reasons[u]='reported_existing_same_country_technical_lower_minimum_backfill'
   backfills.append(dict(ClubUID=u,CountryIndex=ci0,Before=before,After=target,Reason=reasons[u]))
   need=t['Form0Min']-count(t,0)
   if need<=0:break
  assert need<=0,('lower_minimum_unfilled',t,need)
 checks=[]
 for t in q:
  assert ci[t['CatalogueIndex']]==t['CompetitionUID']
  for form in [0,1]:
   n=count(t,form);lo=t['Form0Min']if form==0 else t['Form1DefaultMin'];hi=t['Form0Max']if form==0 else t['Form1DefaultMax']
   checks.append(dict(index=t['CatalogueIndex'],uid=t['CompetitionUID'],country=t['Country'],form=form,count=n,min=lo,max=hi,passed=n>=lo and(hi is None or n<=hi)))
 assert all(x['passed']for x in checks),('both_form_failures',[x for x in checks if not x['passed']])
 moves=[dict(ClubUID=u,Before=r['CurrentDivisionIndex'],After=cur[u],Reason=reasons[u])for u,r in old.items()if cur[u]!=r['CurrentDivisionIndex']]
 am=[dict(ClubUID=u,Before=struct.unpack_from('<i',raw,r['Start']+15)[0],After=alt[u],Reason='scoped_alternate_to_effective_final_current')for u,r in old.items()if alt[u]!=struct.unpack_from('<i',raw,r['Start']+15)[0]]
 before=Counter(r['CurrentDivisionIndex']for r in old.values());after=Counter(cur.values())
 config=dict(moves=moves,alternate_moves=am,requirements=[dict(index=t['CatalogueIndex'],uid=t['CompetitionUID'],min=t['Form0Min'],max=t['Form0Max'],country_scope=t['NativeCountryIndex']if t['CountrySpecific']else None)for t in q if t['CatalogueIndex']!=795],expected_count_deltas={str(d):after[d]-before[d]for d in set(before)|set(after)if after[d]!=before[d]})
 assert not(PROTECTED&{x['ClubUID']for x in moves+am})
 dump(W/'club-plan.json',corefixed);dump(W/'foreign-owner-plan.json',ownfixed)
 dump(W/'structure-config.json',config)
 dump(W/'preflight.json',dict(status='PASS_PREWRITE_92_ACTUAL_EFFECTIVE_FORM_CHECKS_NOT_RUNTIME',checks=checks,technical_retained=technical,lower_backfills=backfills,source_hashes=m['source_hashes'],new_TEAM=len(new),core=len(corefixed),owners=len(ownfixed),kolding='DEFERRED_PRESERVED',input_pins={str(p):sha(p)for p in [P/'club-plan.json',P/'foreign-owner-plan.json',P/'club-map.csv',P/'foreign-owner-map.csv',W/'source-allocation/assignments.json']}))
 print('PASS prewrite',len(checks),'form checks;',len(moves),'Current moves;',len(am),'ALT moves;',len(new),'new TEAM')
if __name__=='__main__':prepare()
