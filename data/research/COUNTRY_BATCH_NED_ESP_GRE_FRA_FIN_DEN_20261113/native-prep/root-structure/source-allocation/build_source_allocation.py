"""Small deterministic reuse of saved source-cascade rank helpers; source allocation only."""
from pathlib import Path
from fractions import Fraction
from collections import Counter,defaultdict
import json,sys,ast,hashlib,re,math,datetime
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
O=Path(__file__).resolve().parent;N=O.parents[1];B=N.parent;P=B/'competition-prep';ROOT=B.parents[3]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
main=read(P/'source-targets-bootstrap.json');targets=read(B/'source-targets.json');final=read(P/'previous-final-tables-normalized.json');comps=read(P/'source-competitions.json');cascade=read(P/'source-cascade-plan.json');reg={str(x['TMID']):x for x in read(B/'collected/global-club-registry.json')};world={x['ClubUID']:x for x in read(N/'native-world-identities.json')};catalog={x['uid']:x for x in read(N/'competition-catalog.json')};idxuid={x['index']:x['uid'] for x in catalog.values()};draft={str(x['TMID']):x for x in read(N/'club-plan-draft.json')};source={str(x['TMID']):x for x in targets};levels={c['id']:int(c['RealLevel'])for c in comps};previous={}
for c in final['Competitions']:
 for r in c['Rows']:
  tid=str(r['TMID']);assert tid not in previous;previous[tid]=dict(r,PreviousCompetition=c['Competition'],PreviousLevel=levels[c['Competition']],PreviousSeason=c['Season'],TableSourcePins=c['SourcePins'])
# Reuse exactly the closed cascade ranking/naming functions without executing its top-level file writes.
engine=P/'build_source_cascade_plan.py';tree=ast.parse(engine.read_text(encoding='utf-8-sig'));funcs=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ['named','ranking_key','reserve_hint','order']];assert len(funcs)==4
exec(compile(ast.Module(body=funcs,type_ignores=[]),str(engine),'exec'),globals())
fixedplan=read(N/'club-plan.json');fixed={str(x['TMID']):x for x in fixedplan}
peer=read(N/'identity-review-peer/club-identity-decisions.json');roots=read(N/'root-identity-review/club-identity-decisions.json');knownuid={k:v.get('NativeClubUID') for k,v in draft.items() if v.get('NativeClubUID')}
for d in peer+roots:
 if d.get('NativeClubUID') is not None:knownuid[d['TMID']]=d['NativeClubUID']
knownuid.update({str(x['TMID']):x['NativeClubUID'] for x in fixedplan if x.get('NativeClubUID')})
geo={};rawcache={};deferred=[];rows={};tiers={};fallback=[];geo_evidence=[];technical=[]

def logical(c):return 'TM:'+str(c['TMID']) if c.get('TMID') else c.get('SourceEntityKey') or 'DBUteam:'+str(c['DBUTeamID'])
def namesource(c):return dict(TMID=str(c['TMID']) if c.get('TMID') else None,LogicalKey=logical(c),Country=c.get('Country') or c.get('LeagueCountry'),Name=c['Name'],RealLevel=c.get('RealLevel'),SourceCompetition=c.get('SourceCompetition') or ('DBU_Danmarksserien' if c.get('DBUTeamID') else None),ParentTMID=reg.get(str(c.get('TMID')),{}).get('ParentTMID') or None)
def level(country,n):return [r for r in main if r['Country']==country and r['RealLevel']==n]
def reserve(c):return bool(reg.get(str(c.get('TMID')),{}).get('ParentTMID'))
def rank(c):return ranking_key(c)
def eligible(c,tier):
 parent=reg.get(str(c.get('TMID')),{}).get('ParentTMID')
 if not parent:return True,None
 pt=tiers.get(str(parent));parentc=source.get(str(parent));pt=pt if pt is not None else parentc.get('RealLevel') if parentc else None
 if pt is None:return False,'parent_tier_unproven'
 if tier<=pt:return False,'reserve_cannot_share_or_exceed_parent_native_tier'
 return True,None

def add(c,tier,uid,reason,allowpending=False):
 k=logical(c);assert k not in rows,k;row=namesource(c);row.update(DesiredDivision=catalog[uid]['index'] if uid else None,DesiredAlternative=None,DesiredCompetitionUID=uid,TargetNativeTier=tier,Reason=reason,PreviousFacts=previous.get(str(c.get('TMID'))) or c.get('PreviousFinal') or ({'PreviousRealLevel':c.get('PreviousRealLevel'),'PreviousHigherFinalPosition':c.get('PreviousHigherFinalPosition')} if c.get('PreviousHigherFinalPosition') else None),SourceRankRule='closed previous tier/final place/PPG/GD per match/wins per match/stable sourceID',NativeUID=knownuid.get(str(c.get('TMID'))),GroupPending=uid is None,SourceAllocationOnly=True,IdentityAndLegacyGlobalQAStillRequired=True)
  # Root-approved deferrals retain the source entity and its field, never fabricated reuse.
 if str(c.get('TMID'))=='81451':row.update(ProtectedUnproven=True,NativeUID=None,NativeWriteBlocked=True,IdentityDecision='Riviera_DEFER5395280');deferred.append(dict(row,Deferral='Riviera source place preserved; technical native replacement selected separately'))
 row['SourceRegionalFacts']={f:c.get(f) for f in ['Group','DBUTeamID','DBUPoolID','SourceFile','SourceSHA256','ParentIdentityRequired'] if c.get(f) is not None}
 if str(c.get('TMID')) in fixed:
  f=fixed[str(c['TMID'])];row['RealLevel']=f.get('RealLevel');row['SourceCompetition']=f.get('SourceCompetition') or row['SourceCompetition'];row['ParentTMID']=f.get('ParentTMID') or row['ParentTMID']
 rows[k]=row
 if c.get('TMID'):tiers[str(c['TMID'])]=tier
 return row

def choose(country,candidates,take,tier,reason,banreserve=False):
 ordered=sorted(candidates,key=rank);selected=[];trace=[]
 for c in ordered:
  good,why=eligible(c,tier)
  if banreserve and reserve(c):good=False;why='source eligibility excludes reserve promotion at this level'
  if str(c.get('TMID'))=='12275':good=False;why='ROOT_TECHNICAL_DEFER_Kolding_kind3_preserve_div566_not_sporting_degradation'
  chosen=good and len(selected)<take
  if chosen:selected.append(c)
  trace.append(dict(**namesource(c),CandidateOrder=len(trace)+1,Selected=chosen,Eligibility=good,SkipReason=why,PreviousFacts=previous.get(str(c.get('TMID')))))
 fallback.append(dict(Country=country,Step=reason,Take=take,TargetNativeTier=tier,OrderedCandidates=trace))
 if len(selected)!=take:deferred.append(dict(Country=country,Deferral='ranked_pool_deficit',Step=reason,Need=take,Have=len(selected)))
 return selected

def ids(cs):return {str(c['TMID']) for c in cs}
def put(cs,tier,uid,why):
 for c in cs:add(c,tier,uid,why)
# Top/current membership eligibility first, with numeric cascades from prior sporting rank.
put(level('Netherlands',1),1,29,'retain currentNL1 exact18');put(level('Netherlands',2),2,30,'retain currentNL2 exact20')
for c in level('Netherlands',3):add(c,3,None,'Dutch lower regional group_pending; root retains/balances required six native pools')
put(level('Spain',1),1,67,'retain currentES1 exact20');put(level('Spain',2),2,68,'retain currentES2 exact22')
es3=level('Spain',3);tiers.update({c['TMID']:3 for c in es3});es4=level('Spain',4);tiers.update({c['TMID']:4 for c in es4});esbase=[]
for c in es3:
 ok,why=eligible(c,3)
 if ok:esbase.append(c)
 else:deferred.append(dict(**namesource(c),Deferral=why,RequestedTier=3))
esextra=choose('Spain',es4,80-len(esbase),3,'Spain nativeB80 fill from saved90 previous-rank pool')
put(esbase+esextra,3,None,'Spain nativeB80 regional group_pending until geography balancing')
for c in es3+es4:
 if logical(c) not in rows:add(c,4,7449905,'Spain remaining currentlower to nativeThird min50; loader/legacy reconciliation belongs to root')
# Greece16/18.
put(level('Greece',1),1,129650,'retain currentGR1 fourteen')
grup=choose('Greece',level('Greece',2),2,1,'Greece retain best prior top-tier relegated')
put(grup,1,129650,'source previous-rank +2 to nativeTop16')
put([c for c in level('Greece',2) if c['TMID'] not in ids(grup)],2,129651,'remaining currentS2 fourteen to nativeB')
put(read(P/'greece-extra4-club-targets.json'),2,129651,'four officialGamma/current-identity candidates to nativeB18; native identity proof remains separate')
# France20/20/20 + minimum CFA53 (minimum, not fixed field).
put(level('France',1),1,16,'retain currentFR1 eighteen')
f1=choose('France',level('France',2),2,1,'France +2 previousL1 relegated');put(f1,1,16,'France nativeL1 exact20')
put([c for c in level('France',2) if c['TMID'] not in ids(f1)],2,17,'France currentFR2 remaining16')
f2=choose('France',level('France',3),4,2,'France +4 currentFR3 by closed previous rank',True);put(f2,2,17,'France nativeL2 exact20')
put([c for c in level('France',3) if c['TMID'] not in ids(f2)],3,18,'France remainingFR3 fourteen')
f3=choose('France',level('France',4),6,3,'France +6 currentfourth previous rank',True);put(f3,3,18,'France nativeNational exact20')
put([c for c in level('France',4) if c['TMID'] not in ids(f3)],4,145438,'France remaining currentfourth43 to CFA')
f4=choose('France',level('France',5),10,4,'France +10 fifth to provisional CFA minimum53',True);put(f4,4,145438,'France CFA source envelope reachesminimum53; root validates regional contribution')
put([c for c in level('France',5) if c['TMID'] not in ids(f4)],5,8436980,'France remainingfifth101; min96 preserved by source envelope')
# Finland14/14, calendar real2026(provider2025), previousreal2025(provider2024).
put(level('Finland',1),1,129120,'retain currentFI1 twelve')
fi1=choose('Finland',level('Finland',2),2,1,'Finland +2 priorTop relegated');put(fi1,1,129120,'Finland nativeTop exact14')
put([c for c in level('Finland',2) if c['TMID'] not in ids(fi1)],2,129131,'Finland currentFI2 remaining8')
fi2=choose('Finland',level('Finland',3),6,2,'Finland +6 currentYkkonen by previousfinal');put(fi2,2,129131,'Finland nativeFirst exact14')
for c in level('Finland',3)+level('Finland',4):
 if logical(c) not in rows:add(c,3,None,'Finnish regional lower group_pending; parent/saved lower contributions handled by root')
for c in read(P/'finland-lower6-profile-candidates.json'):
 if logical(c) not in rows:
  eligible_now=c['TMID'] in ['31752','36282','11134','46828'];why='source lower candidate; Elo currentNelonen confirmed by approved peer; root regional group_pending' if eligible_now else 'defer lower eligibility/parent at same tier or nullleague; no forced assignment'
  q=add(c,3,None,why);q['CurrentEligibilityProven']=eligible_now
  if not eligible_now:deferred.append(dict(q,Deferral='lower_current_eligibility_or_parent_unproven'))
# Denmark root bounded Kolding technical defer changes the source fill arithmetic.
put(level('Denmark',1),1,6,'retain currentDK1 exact12')
dk2=[c for c in level('Denmark',2) if c['TMID']!='12275'];put(dk2,2,7,'retain11currentDK2; Kolding deferred technically')
dk_up=choose('Denmark',level('Denmark',3),5,2,'DenmarkFirst16: replace deferredKolding by next eligible saved previousrank');put(dk_up,2,7,'Denmark nativeFirst exact16 with five eligible DK3, not Kolding players reassigned')
dk_core=[c for c in level('Denmark',3) if c['TMID'] not in ids(dk_up)]+level('Denmark',4)
ds=read(P/'denmark-series-catalogue.json');selected12=ds['Selected12'];chosenkeys={c['DBUTeamID'] for c in selected12}
def dsrank(c):
 p=c.get('PreviousFinal') or {};m=p.get('Matches') or 1
 return (p.get('FinalOrderingPosition',999),-Fraction(p.get('Points',0),m),-Fraction(p.get('GoalDifference',0),m),-Fraction(p.get('Wins',0),m),str(c['DBUTeamID']))
next_ds=sorted([c for c in ds['Current'] if c['DBUTeamID'] not in chosenkeys and c.get('PromotionEligibleForClassicFill') and not c.get('ParentIdentityRequired') and c.get('PreviousFinal')],key=dsrank)[0]
selected_ds=selected12+[dict(next_ds,SelectionQualification='13th saved rank replacement after root technical Kolding defer')]
# Reuse exact confirmed/candidate source TMID from the finished delta, never name-only native UID.
delta_dbu={str(c['DBUTeamID']):c for c in targets if c.get('DBUTeamID')}
for c in selected_ds:
 if c['DBUTeamID'] in delta_dbu:c.update(TMID=delta_dbu[c['DBUTeamID']]['TMID'])
for c in dk_core+selected_ds:add(c,3,None,'DenmarkThird32: 7remainingDK3+12DK4+13Series; EastWest group_pending')
selected_dbu={c['DBUTeamID'] for c in selected_ds}
for c in ds['Current']:
 if c['DBUTeamID'] not in selected_dbu:
  q=add(c,4,1702406,'remaining27 currentSeries plus protected legacyKolding slot reaches minimum28');q['ParentIdentityRequired']=c.get('ParentIdentityRequired',False)
old=world[2121];technical.append(dict(LogicalKey='NATIVE:2121',Country='Denmark',NativeUID=2121,DesiredDivision=566,DesiredAlternative=None,DesiredCompetitionUID=1702406,Reason='Root technical preserve Kolding Kind3/current566; counts as retained native entry, NOT a claim of current Series sporting membership',NativeWitness=old,KeepBitwise=True))
deferred.append(dict(TMID='12275',LogicalKey='TM:12275',Country='Denmark',Name=source['12275']['Name'],DesiredDivision=5,RetainExistingNativeDivision=566,NativeUID=2121,Deferral='ROOT_TECHNICAL_DEFER_NOT_SPORTING_DEGRADATION',DeferredSourceProfiles=29,OwnerLoans='preserve existing owner links; no mapping these players to replacement club',DoNotCreateDuplicate=True))
# Riviera has a real source row above. Add one safe already-CFA2 native technical entry, no fictional identity.
used={v for v in knownuid.values() if v};legacy=sorted([w for w in world.values() if w['ClubUID'] not in used and w['Country']==143 and w['TeamCountry']==143 and w['NativeTeamKind']==0 and w['CurrentDivision']==catalog[8436980]['index']],key=lambda w:w['ClubUID'])
if legacy:
 w=legacy[0];technical.append(dict(LogicalKey='NATIVE:'+str(w['ClubUID']),Country='France',NativeUID=w['ClubUID'],DesiredDivision=catalog[8436980]['index'],DesiredAlternative=None,DesiredCompetitionUID=8436980,Reason='RivieraTM81451 native identity deferred: preserve this already-CFA2 unmapped typed first-team entry as technical coverage; no claim of updated real membership',NativeWitness=w,KeepBitwise=True,ReplacesUnprovenSourceLogicalKey='TM:81451'))
else:deferred.append(dict(Country='France',Deferral='No safe native CFA2 technical entry for Riviera slot found; root required'))
# Registered club address, not stadium: cache exact legal-parent location as geographic evidence.
def geog(c):
 tid=str(c.get('TMID'))
 if tid in geo:return geo[tid]
 g=reg.get(tid,{});ref=g.get('SourceRef');result={}
 if ref:
  p=B/ref['raw_file'];key=str(p)
  if key not in rawcache:
   body=read(p);data=json.loads(body['body']).get('data');rawcache[key]=data if isinstance(data,list) else [data]
  raw=next((x for x in rawcache[key] if str(x.get('id'))==tid),{})
  result=dict(((raw.get('baseDetails') or {}).get('superiorClub') or {}).get('location') or {});result.update(SourceRawFile=str(p.relative_to(ROOT)),SHA256=sha(p),Use='registered club superior legal-address geography only; not temporary stadium; superiorClubID is NOT sporting parent')
 geo[tid]=result;return result
# Keep proven old native regional group first, then deterministic capacity-balanced nearest-centroid proposals.
def regional(country,compuids,cap):
 selected=[r for r in rows.values() if r['Country']==country and r['TargetNativeTier']==3 and r['DesiredDivision'] is None and (country!='Finland')];groups={u:[] for u in compuids};pending=[]
 for r in selected:
  old=world.get(knownuid.get(str(r['TMID'])),{});u=idxuid.get(old.get('CurrentDivision'));g=geog(r) if r.get('TMID') else {};r['RegisteredGeography']=g
  if u in groups and len(groups[u])<cap:groups[u].append(r);r.update(DesiredDivision=catalog[u]['index'],DesiredCompetitionUID=u,GroupPending=False,RegionalReason='retain exact verified old native regional group');continue
  pending.append(r)
 centres={}
 for u,rs in groups.items():
  coords=[(r['RegisteredGeography'].get('latitude'),r['RegisteredGeography'].get('longitude')) for r in rs]
  coords=[(a,b) for a,b in coords if isinstance(a,(int,float)) and isinstance(b,(int,float)) and 25<a<60 and -20<b<25]
  if coords:centres[u]=(sum(a for a,b in coords)/len(coords),sum(b for a,b in coords)/len(coords))
 # If no old group seed for a Danish side, use source postal proof as a label, with no invented coordinate.
 for r in list(pending):
  if country!='Denmark':continue
  g=r.get('RegisteredGeography',{});post=str(g.get('postcode') or '')
  if re.fullmatch(r'\d{4}',post):
   u=1701138 if int(post)<5000 else 1701139
   if len(groups[u])<cap:groups[u].append(r);pending.remove(r);r.update(DesiredDivision=catalog[u]['index'],DesiredCompetitionUID=u,GroupPending=False,RegionalReason='registered Danish postcode east<5000 / west>=5000; exact old groups retained first')
  elif not r.get('TMID') and r['LogicalKey']=='DBUteam:291726':r['RegionalReason']='Glostrup official logicalkey retained; current registered geography not inferred from unresolved TMID'
 # Recompute after registered-postcode seeds; never invent missing coordinates.
 for u,rs in groups.items():
  cs=[(r.get('RegisteredGeography',{}).get('latitude'),r.get('RegisteredGeography',{}).get('longitude')) for r in rs]
  cs=[(a,b) for a,b in cs if isinstance(a,(int,float)) and isinstance(b,(int,float)) and 25<a<60 and -20<b<25]
  if cs:centres[u]=(sum(a for a,b in cs)/len(cs),sum(b for a,b in cs)/len(cs))
 # Highest regret first gives a deterministic bounded boundary compromise for remaining proven coordinates.
 while pending:
  choices=[]
  for r in pending:
   g=r.get('RegisteredGeography',{});a=g.get('latitude');b=g.get('longitude')
   if not isinstance(a,(int,float)) or not isinstance(b,(int,float)) or not(25<a<60 and -20<b<25):continue
   opts=sorted((((a-x)**2+(math.cos(math.radians(a))*(b-y))**2,u) for u,(x,y) in centres.items() if len(groups[u])<cap))
   if opts:choices.append((-(opts[1][0]-opts[0][0]) if len(opts)>1 else -1e9,r['LogicalKey'],r,opts[0][1]))
  if not choices:break
  _,_,r,u=sorted(choices,key=lambda x:(x[0],x[1]))[0];groups[u].append(r);pending.remove(r);r.update(DesiredDivision=catalog[u]['index'],DesiredCompetitionUID=u,GroupPending=False,RegionalReason='capacity-balanced registered geography nearest retained-native-group centroid; explicit boundary compromise proposal, not a modern region equivalence')
 # Saved real group is only a regional hint; modern groups are not claimed identical to FM08.
 for r in sorted(pending,key=lambda r:r['LogicalKey']):
  facts=r.get('SourceRegionalFacts',{});hint=None
  if country=='Denmark' and facts.get('Group') in [1,2,3,4]:hint=1701138 if facts['Group'] in [1,2] else 1701139
  if country=='Spain':hint={'E4G1':69,'E4G2':70,'E4G3':71,'E4G4':72,'E4G5':69}.get(r.get('SourceCompetition'))
  opts=[u for u in compuids if len(groups[u])<cap]
  assert opts,('no regional capacity',country,r['LogicalKey'])
  u=hint if hint in opts else sorted(opts,key=lambda u:(len(groups[u]),u))[0]
  compromise=hint is None or u!=hint
  groups[u].append(r)
  r.update(DesiredDivision=catalog[u]['index'],DesiredCompetitionUID=u,GroupPending=False,RegionalHintCompetitionUID=hint,GeographyCompromise=compromise,RegionalReason=('saved source regional-group hint within exact FM08 capacity' if not compromise else 'root-authorized stable logicalkey/capacity tie after registered geography and saved group evidence; no city or coordinate invented; FM08 boundary compromise'),RegionalTieRule='pending sorted LogicalKey; prefer saved regional hint if capacity; else least-filled group then COMPUID')
 pending=[]
 assert all(len(rs)==cap for rs in groups.values()),(country,'exact region counts')
 geo_evidence.append(dict(Country=country,Method='retain existing native regional group; registered club address/postcode; then deterministic balanced nearest-centroid; saved regional hints; stable logicalkey/capacity tie if missing geography; explicit FM08 approximations',Centres={str(k):v for k,v in centres.items()},Groups={str(u):[r['LogicalKey'] for r in rs] for u,rs in groups.items()},TargetEach=cap,ActualCounts={str(u):len(rs) for u,rs in groups.items()},Pending=[r['LogicalKey'] for r in pending]))
regional('Spain',[69,70,71,72],20);regional('Denmark',[1701138,1701139],16)
# Complete lower source catalogue. Only verified same native group/current source region is asserted.
# The generic pool is an explicit technical placement, not a real present-day league claim.
for r in rows.values():
 tid=str(r.get('TMID'));country=r['Country']
 if tid=='55564':
  r.update(NativeWriteBlocked=True,IdentityDecision='ROOT_DEFER_Oulunsalon_current_membership_unproven');continue
 if r['DesiredDivision'] is not None:continue
 old=world.get(knownuid.get(tid),{});oldidx=old.get('CurrentDivision');u=None
 if country=='Netherlands':
  if oldidx in [464,465,466,467,468,469]:u=idxuid[oldidx];why='retain verified old native Dutch lower group; no modern Saturday/Sunday equivalence asserted'
  else:u=1301432;why='technical unclassified Dutch lower550; modern NTD has no proven classic six-group equivalent; root balances legacy lower minima'
 elif country=='Finland':
  if tid in ['46828','75734']:
   u=129123;why='technical nonplayable Finnish lower123: Elo realNelonen6; AtlantisII retained below projected parentTier3, not formal nativeTier3';r['TargetNativeTier']=4
  elif oldidx in [1140,1141,1142]:u=idxuid[oldidx];why='retain verified old native Finnish regional group; classic approximation'
  elif r.get('SourceCompetition') in ['FI3A','FI3B','FI3C']:
   u={'FI3A':33000118,'FI3B':33000117,'FI3C':33000120}[r['SourceCompetition']];why='saved current Kakkonen regional A/B/C used as classic geographic approximation, not exact modern tier equivalence'
  else:u=129123;why='technical unclassified Finnish lower123; saved current club has no proven classical regional group; root balances legacy minima';r['TargetNativeTier']=4
 if u:
  r.update(DesiredDivision=catalog[u]['index'],DesiredCompetitionUID=u,GroupPending=False,LowerRebalanceRequired=True,TechnicalPlacement=(u in [129123,1301432]),Reason=r['Reason']+'; '+why)
# Final physical DBU candidates have no fabricated TMID or person roster.
for key,uid in [('DBUteam:148174',506),('DBUteam:291726',510)]:
 if key in rows:rows[key].update(NativeUID=uid,PhysicalIdentityOnly=True,NoTMID=True,NoSourcePlayerImport=True,PhysicalIdentityStatus='ROOT_APPROVED_EXISTING_REUSE',NativeWitness=world[uid])
# Drop provisional lower deferrals that are now safe explicit technical placements.
deferred=[d for d in deferred if not(d.get('LogicalKey') in rows and rows[d['LogicalKey']].get('DesiredDivision') is not None and not rows[d['LogicalKey']].get('NativeWriteBlocked') and d.get('Deferral')=='lower_current_eligibility_or_parent_unproven')]
# Include all source targets, even lower candidates not projected by this bounded task.
for c in targets:
 if logical(c) not in rows and not any(d.get('LogicalKey')==logical(c) for d in deferred):deferred.append(dict(**namesource(c),Deferral='unallocated_source_lower_or_identity_candidate',SourceScope=c.get('SourceScope','main584')))
assigned=[r for r in rows.values() if r['DesiredDivision'] is not None and not r.get('NativeWriteBlocked')]
for r in assigned:
 if r.get('RegionalReason'):r['Reason']=r['Reason'].replace('group_pending until geography balancing','group finalized').replace('EastWest group_pending','EastWest finalized')+'; '+r['RegionalReason']
physical=[]
for key,uid in [('DBUteam:148174',506),('DBUteam:291726',510)]:
 r=rows[key];facts=r['SourceRegionalFacts'];files=[N/'native-world-identities.json',P/facts['SourceFile'].removeprefix('competition-prep/')]
 if uid==510:files += [P/'glostrup-bounded-identity-decision.json',P/'sources/glostrup-dbu-team-official.html',P/'sources/glostrup-statutes-official.html']
 physical.append(dict(LogicalKey=key,NativeClubUID=uid,Country='Denmark',Name=r['Name'],TMID=None,DesiredDivision=r['DesiredDivision'],DesiredAlternative=-1,DesiredCompetitionUID=r['DesiredCompetitionUID'],Reason='ROOT_APPROVED physical existing club; '+r['Reason']+'; no TMID/provider-roster inference; preserve own TEAM/FAMILY and source persons',EvidencePins=[dict(File=str(f.relative_to(B)),SHA256=sha(f)) for f in files],NativeWitness=world[uid],RootApproval='explicit root message after user X18 resume2026-11-13',NoNewUID=True,NoNewTEAM=True,NoPersonImport=True))
dump('structural-assignments.json',physical)
dump('physical-root-approval-receipt.json',dict(Status='ROOT_APPROVED_EXISTING_PHYSICAL_REUSE',Decisions=[dict(LogicalKey=x['LogicalKey'],NativeClubUID=x['NativeClubUID'],TMID=None,NoPersonImport=True) for x in physical],Scope='physical TEAM only; preserve602 country projection; official cached DBU/statutes/native knowncountry Kind0; no3providerprofile alias; root implements explicit cfg.moves only',NewRawHTTPCapture=False))
for r in rows.values():
 if r['DesiredDivision'] is None and not any(d.get('LogicalKey')==r['LogicalKey'] for d in deferred):deferred.append(dict(r,Deferral='lower_group_pending_root_balance'))
coreids=set(fixed);assignedcore={r['TMID'] for r in assigned if r.get('TMID') in coreids};assert assignedcore==coreids,('missing core',coreids-assignedcore)
assert len({r['LogicalKey'] for r in assigned})==len(assigned)
assert not any(r.get('TMID') in ['12275','81451','55564'] for r in assigned)
summary=dict(Status='FINAL_SOURCE_ALLOCATION_602_CORE_NOT_NATIVE_PREFLIGHT',CoreRows=len(assignedcore),StructuralRows=2,CatalogueExtraRows=sum(not r.get('TMID') for r in assigned),MissingEligibleCoreTMIDs=[],AssignedRows=len(assignedcore),DeferredRows=len(deferred),SourceTierCounts={country:dict(Counter(r['TargetNativeTier'] for r in rows.values() if r['Country']==country)) for country in ['Netherlands','Spain','France','Greece','Finland','Denmark']},DesiredDivisionCounts=dict(Counter(str(r['DesiredDivision']) for r in assigned if r.get('TMID') in coreids)),AllSourceCatalogueDivisionCounts=dict(Counter(str(r['DesiredDivision']) for r in assigned)),TechnicalRetainedEntries=technical,KoldingReplacement=[c['TMID'] for c in dk_up],ExtraDanishSeries13th=namesource(next_ds),NativeDBWrite=False,UIDAllocation=False,NoResearch=True,AlternativeDecision='null=no source ALT assertion; root must reconcile current/effectiveALT independently',RootOwns=['legacy lower pools','ALT','regional stock contributions','whole-world numeric QA'])
dump('core-assignments.json',[r for r in assigned if r.get('TMID') in coreids]);dump('extras-assignments.json',[r for r in assigned if r.get('TMID') not in coreids]);dump('assignments.json',[r for r in assigned if r.get('TMID') in coreids]);dump('deferred.json',deferred);dump('all-source-tier-proposals.json',list(rows.values()));dump('ranked-fallback.json',fallback);dump('geography-evidence.json',geo_evidence);dump('technical-retained-entries.json',technical);dump('summary.json',summary)
inputs=[engine,P/'source-cascade-plan.json',P/'previous-final-tables-normalized.json',P/'source-targets-bootstrap.json',B/'source-targets.json',B/'collected/global-club-registry.json',N/'native-world-identities.json',N/'club-plan.json',N/'competition-catalog.json',P/'denmark-series-catalogue.json',N/'identity-review-peer/root-approval-receipt.json',N/'root-identity-review/club-identity-decisions.json',P/'glostrup-bounded-identity-decision.json',P/'sources/glostrup-dbu-team-official.html',P/'sources/glostrup-statutes-official.html']
dump('manifest.json',dict(Status=summary['Status'],CreatedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),Inputs={str(p.relative_to(ROOT)):sha(p) for p in inputs},HelperReuse='AST-extracted named/ranking_key/reserve_hint/order only; no top-level cascade script execution or rewrite',Outputs={p.name:sha(p) for p in O.iterdir() if p.is_file() and p.name!='manifest.json'},NativeWrite=False,UIDAllocation=False))
print(json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=='__main__':pass
