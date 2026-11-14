import sys,asyncio,json,collections
from pathlib import Path
sys.dont_write_bytecode=True;sys.path.insert(0,str(Path.cwd()/'FM08-Database-Tools/scratch'))
import ss26prep_collect_20261110 as c
B=Path.cwd()/'FmLauncher/data/research/RUSSIA_RSA_PREP_X10_20261111';S=B/'sources';c.B=B;c.S=S
def table(cid,yr):
 return {r['club_id']:r for t in c.read(S/'tm-competitions'/(cid+'-'+yr+'-table.json'))['tables'] for r in t['rows']}
def target(name,tid,country,ci,lev,div,comp,rank,reason):
 return dict(Name=name.strip(),TMID=str(tid),Country=country,LeagueCountry=country,NativeCountryIndex=ci,RealLevel=lev,DesiredDivision=div,SourceCompetition=comp,RealSeason='2026/27',APISeason='2026',PreviousRank=rank,SelectionReason=reason)
def init():
 assert not (B/'source-targets.json').exists()
 out=[]
 for cid,country,ci,level,div in [('RU1','Russia',165,1,177),('RU2','Russia',165,2,178),('SFA1','South Africa',40,1,202)]:
  ranks=table(cid,'2025')
  for v in c.read(S/'tm-competitions'/(cid+'-2026-clubs.json'))['clubs']:
   out.append(target(v['name'],v['id'],country,ci,level,div,cid,(ranks.get(v['id'])or{}).get('position'),'real_2026_27_participant'))
 gold=c.read(S/'tm-competitions/R3D2-2025-table.json')['tables'][0]['rows']
 for tid in ['3834','75068','11123','6432']:
  if tid=='3834':
   v=table('RU2','2025')[tid];reason='best_eligible_relegated_second_tier_club; Chernomorets and Chayka excluded inactive/licensing';lev=3
  else:
   v=next(x for x in gold if x['club_id']==tid);reason='best_remaining_eligible_previous_final_gold_phase2_2025_26; already_promoted_clubs_skipped';lev=3
  out.append(target(v['club_name'],tid,'Russia',165,lev,178,'R3D1',v['position'],reason))
 rsa=[
 ('Cape Town City FC','2303'),('Gomora United','132261'),('Highbury','120449'),('Hope FC','138946'),
 ('Hungry Lions FC','78609'),('Leicesterford City FC','133914'),('Lerumo Lions','125314'),('Magesi FC','54146'),
 ('Midlands Wanderers','132262'),('North West University','142733'),('Orbit College FC','45783'),
 ('Pretoria University FC','23285'),('Real Native FC','102349'),('The Bees','125315'),('Upington City','110032'),('Venda FC','91937')]
 for name,tid in rsa:
  out.append(target(name,tid,'South Africa',40,2,203,'PSL_NFD',None,'official_PSL_National_First_Division_2026_27_list; no_count_adaptation_required'))
 assert len(out)==70 and len({x['TMID'] for x in out})==70
 assert collections.Counter(x['DesiredDivision']for x in out)=={177:16,178:22,202:16,203:16}
 c.dump(B/'source-targets.json',out)
 c.dump(B/'source-competitions.json',[dict(id='RU1',Country='Russia',level=1,classic_count=16,division=177),dict(id='RU2',Country='Russia',level=2,classic_count=22,division=178),dict(id='SFA1',Country='South Africa',level=1,classic_count=16,division=202),dict(id='PSL_NFD',Country='South Africa',level=2,classic_count=16,division=203,SourceURL='https://www.psl.co.za/',not_transfermarkt_competition_id=True)])
 c.dump(B/'selection-decisions.json',dict(previous_completed_season='2025/26',russia_extra_second_tier=['3834','75068','11123','6432'],russia_relegation_exclusions=[dict(TMID='5287',reason='no current league/squad; licence refused2026/27',source='https://www.kommersant.ru/doc/8736796'),dict(TMID='36972',reason='historical name ends2026; no current league/squad; absent from activeR3D1')],russia_lower_rank_source='https://www.transfermarkt.com/-/tabelle/wettbewerb/R3D2/saison_id/2025',rsa_nfd_source='https://www.psl.co.za/',rsa_nfd_aliases=[dict(Name='Real Native FC',TMID='102349',PriorName='Casric Stars FC',decision='official name change; source TM retains old name'),dict(Name='Leicesterford City FC',TMID='133914',DifferentTMID='54668',DifferentName='JDR Stars FC',decision='distinct TM entity; do not auto-reuse old JDR')]))
 c.dump(B/'manifest.json',dict(status='source_preparation_only',countries=['Russia','South Africa'],source_candidate='../SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/input/X8-accepted',database_write=False,output_database_created=False,retirements=False,classic_counts={'Russia':[16,22],'South Africa':[16,16]},date_shift_applied=False,sugar_daddy_new_clubs=False,loans_owner_and_playing_separate=True))
async def run():
 cache=c.Cache();targets=c.read(B/'source-targets.json')
 async with c.Transfermarkt(timeout=30,max_concurrency=3,transport=cache)as tm:
  async def one(v):
   tid=v['TMID'];p=S/'tm-clubs'/(tid+'-profile.json');q=S/'tm-clubs'/(tid+'-players-2026.json')
   try:
    await c.get(tm,p,'club_profile',tid)
    z=await c.get(tm,q,'club_players',tid,season_id='2026')
    v.update(ProfileFile=str(p.relative_to(B)),RosterFile=str(q.relative_to(B)),PlayersFetched=len(z.get('players',[])))
    print('ROSTER',v['Country'],v['Name'],v['PlayersFetched'],flush=True)
   except Exception as e:
    v['FetchError']=str(e);print('ERROR',v['Name'],str(e)[:180],flush=True)
  for i in range(0,len(targets),3):
   await asyncio.gather(*(one(v)for v in targets[i:i+3]));c.dump(B/'source-targets.json',targets)
 c.dump(B/'roster-capture.json',dict(calls=cache.calls,hits=cache.hits,clubs_fetched=sum('PlayersFetched'in v for v in targets),player_cards=sum(v.get('PlayersFetched',0)for v in targets)))
if not (B/'source-targets.json').exists():init()
asyncio.run(run())
