from x10_pipeline import *
import re
LOWER=[
 ('37227','CS Tunari',None),('8687','CSM Ceahlaul Piatra Neamt',None),
 ('111687','ACS Minerul Lupeni',(3,2,27,15)),('101586','CSM Unirea Alba Iulia',(4,2,27,12)),
 ('41292','Sporting Liesti',(1,3,25,-2)),('32290','AS Flacara Moreni',(2,3,23,0)),
 ('43912','Universitatea Craiova II',(3,3,25,2)),('84455','SCM Zalau',(4,3,24,6)),
 ('frf-kse-targu-secuiesc','KSE Targu Secuiesc',(1,4,19,-1)),('34972','Sanatatea Cluj',(4,4,24,4)),
 ('60793','Agricola Borcea',(2,4,18,8)),('97081','CSM Cetatea Turnu Magurele',(3,4,18,-6)),
 ('117908','Viitorul Onesti',(1,5,18,-1)),('95321','Olimpic Zarnesti',(2,5,18,-2)),
 ('11267','Minaur Baia Mare',(4,5,18,3)),('9830','CSM Jiul Petrosani',(3,5,16,-1))]
def allocate():
 assert not(B/'allocation-decisions.json').exists()
 targets=read(B/'source-targets.json');dump(B/'source-targets-before-final-allocation.json',targets)
 targets=[c for c in targets if c['TMID']!='58049'];bytid={c['TMID']:c for c in targets}
 bytid['86094'].update(RealLevel=2,SelectionReason='FRF20260731_Olimpia_replaces_withdrawn_Hermannstadt',OfficialMembershipEvidence='https://www.frf.ro/wp-content/uploads/2026/07/Anexa-1-locuri-vacante-liga-2-iulie-2026.pdf')
 final={}
 for comp,offset in [('SR1C',0),('SR1R',8)]:
  for t in read(S/'tm-competitions'/(comp+'-2025-table.json'))['tables']:
   for row in t['rows']:final[row['club_id']]=dict(row,OverallPosition=row['position']+offset,FinalPhase=comp)
 currenttop=[c for c in targets if c['SourceCompetition']=='SER1']
 continuing=[c for c in currenttop if c['TMID']in final]
 moved=sorted(continuing,key=lambda c:(final[c['TMID']]['OverallPosition'],c['TMID']),reverse=True)[:len(currenttop)-12];movedids={c['TMID']for c in moved}
 for c in targets:
  if c['Country']=='Serbia':
   c['DesiredDivision']=210 if c['SourceCompetition']=='SER1'and c['TMID']not in movedids else 767
   c['PreviousRank']=final.get(c['TMID'],c['PreviousRank'])
   c['SelectionReason']='two_worst_eligible_continuing_by_final2025_26_to_native_second'if c['TMID']in movedids else'actual_current_membership_classic_allocation'
  else:
   c['DesiredDivision']=862 if c['SourceCompetition']=='RO1'or c['TMID']in{'29700','37624'}else None
   if c['TMID']in{'29700','37624'}:c['SelectionReason']='best_eligible_real_relegated_by_final2025_26_Hermannstadt_excluded_withdrawn'
 for tid,name,rank in LOWER:
  assert tid not in bytid
  prev=dict(Group=rank[0],position=rank[1],matches=8,points=rank[2],goal_difference=rank[3],FinalPhase='FRF2025_26_L3_playoff')if rank else next(v for t in read(S/'tm-competitions/R2AO-2025-table.json')['tables']for v in t['rows']if v['club_id']==tid)
  c=dict(Name=name,TMID=tid,Country='Romania',LeagueCountry='Romania',NativeCountryIndex=164,RealLevel=3,DesiredDivision=None,SourceCompetition='FRF_L3',RealSeason='2026/27',APISeason='2026',PreviousRank=prev,SelectionReason='preserve_best_eligible_real_second_relegated'if not rank else'best_eligible_lower_by_final_FRF2025_26_playoff_rank_then_normalized_points_GD',RankingEvidence='https://www.frf.ro/wp-content/uploads/2026/07/clasamente_fotbal_2025-2026-l3-Anexa-2.pdf',MembershipEvidence='https://www.frf.ro/recomandate/joi-20-august-tragerea-la-sorti-pentru-programul-superscore-liga-3-editia-2026-2027/')
  if tid=='43912':c.update(ParentTMID='40812',ReserveTeam=True)
  if tid.startswith('frf-'):
   c.update(SourceIdentityNamespace='FRF_official_name_not_Transfermarkt_ID',NativeClubUID=57002781,StructuralOnly=True,ProfileFile='sources/official/KSE-club-profile.json',RosterFile='sources/official/KSE-unavailable-roster.json',PlayersFetched=0)
   dump(B/c['ProfileFile'],dict(name='ACS KSE Târgu Secuiesc',official_name='ACS KSE Târgu Secuiesc',short_name='KSE Tg. Secuiesc',stadium={},url='',source_url='https://ksetargusecuiesc.com/',source_identity_namespace='FRF_official_name',source_roster_unavailable=True))
   dump(B/c['RosterFile'],dict(players=[],source_roster_unavailable=True,reason='No matching TMclub after bounded discovery; confirmed native club and FRF2025_26 ranking. Do not force source missing players. Preserve native safe roster.'))
  targets.append(c)
 assert len(targets)==84
 assert sum(c['Country']=='Serbia'and c['DesiredDivision']==210 for c in targets)==12
 assert sum(c['Country']=='Serbia'and c['DesiredDivision']==767 for c in targets)==18
 dump(B/'source-targets.json',targets)
 decisions={'Serbia':dict(real_top=14,native_top=12,native_second=18,moved=[dict(TMID=c['TMID'],Name=c['Name'],final_rank=final[c['TMID']])for c in moved],rule='Final2025_26phase, not regular/live table; promoted Macva/Zemun retained')}
 decisions['Romania']=dict(real_top=16,native_top=18,real_second=22,native_second=36,top_rescued=['29700','37624'],excluded_withdrawn=['58049','33966','94872','116379'],lower_selected=[dict(TMID=t,Name=n,PreviousRank=r)for t,n,r in LOWER],rule='Eligible relegated clubs first, then final FRFplayoff rank/normalized points/GD; no forced player sourcing',Olimpia_correction='FRF31July overrides21July list; retain86094 as second, exclude withdrawn58049')
 dump(B/'allocation-decisions.json',decisions)
 print('ALLOCATED84 Serbia30/Romania54, lower16, KSE structural-only.',flush=True)
async def fetch_remaining():
 cache=col.Cache();targets=read(B/'source-targets.json')
 async with Transfermarkt(timeout=30,max_concurrency=3,transport=cache)as tm:
  pending=[c for c in targets if not c.get('StructuralOnly')and not c.get('RosterFile')]
  async def one(c):
   tid=c['TMID'];pf=S/'tm-clubs'/(tid+'-profile.json');rf=S/'tm-clubs'/(tid+'-players-2026.json')
   await col.get(tm,pf,'club_profile',tid);z=await col.get(tm,rf,'club_players',tid,season_id='2026')
   c.update(ProfileFile=str(pf.relative_to(B)),RosterFile=str(rf.relative_to(B)),PlayersFetched=len(z.get('players',[])))
   print('SUPPLEMENT',tid,c['Name'],c['PlayersFetched'],flush=True)
  for i in range(0,len(pending),3):
   await asyncio.gather(*(one(c)for c in pending[i:i+3]));dump(B/'source-targets.json',targets)
 dump(B/'supplement-capture.json',dict(network_calls=cache.calls,cache_hits=cache.hits))
if __name__=='__main__':
 if sys.argv[1]=='allocate':allocate()
 elif sys.argv[1]=='fetch':asyncio.run(fetch_remaining())
 else:raise ValueError(sys.argv[1])
