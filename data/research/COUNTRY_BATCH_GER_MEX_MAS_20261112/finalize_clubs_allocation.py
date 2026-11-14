from pathlib import Path
from collections import Counter
from fractions import Fraction
import json,sys,struct,hashlib,csv
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(n,x):(B/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
plan=read(B/'club-plan-reviewed.json');world={w['ClubUID']:w for w in read(B/'native-world-identities.json')};bytm={c['TMID']:c for c in plan}
dec=read(R/'WORK_20261112/identity-decisions.json')
for d in dec['decisions']:
 c=bytm[d['tmid']];uid=d.get('reuse_uid');c.update(IdentityDecision=d['action'],IdentityReason=d['basis'],IdentityEvidence=d['sources'],IdentitySourceNote=d.get('source_note'))
 if d.get('founded_year')is not None:c['YearFounded']=d['founded_year']
 if uid:
  w=world[uid];c.update(NativeClubUID=uid,NativeTeamIndex=w['TeamIndex'],NativeFamilyIndex=w['FamilyIndex'],ExistingStadiumIndex=w['StadiumIndex'],NativeParentUID=w['ParentUID'],SourceCountryIndex=w['Country'],NativeNames=w['Names'],NativeCountryRepairTo=c['NativeCountryIndex']if c['NativeCountryIndex']!=w['Country']else None)
 else:c.update(NativeClubUID=None,NativeTeamIndex=None,NativeFamilyIndex=None,ExistingStadiumIndex=-1,NativeParentUID=None)
c=bytm['3631'];w=world[1253];c.update(NativeClubUID=1253,NativeTeamIndex=w['TeamIndex'],NativeFamilyIndex=w['FamilyIndex'],ExistingStadiumIndex=w['StadiumIndex'],NativeParentUID=w['ParentUID'],SourceCountryIndex=w['Country'],IdentityDecision='reuse_explicit_Club_de_Futbol_America_Mexico',IdentityReason='Current Mexican America, not extinct SantaCatarina Brazil record309757',NativeNames=w['Names'])
c=bytm['122506'];c.update(NativeClubUID=None,NativeTeamIndex=None,NativeFamilyIndex=None,ExistingStadiumIndex=-1,NativeParentUID=None,IdentityDecision='create_distinct_entity',IdentityReason='TapachulaSoconusco founded26Oct2023; not oldJaguaresTapachula5661071; preserve both identities',IdentityEvidence=['https://en.wikipedia.org/wiki/Tapachula_Soconusco_F.C.'],YearFounded=2023)
used=[c['NativeClubUID']for c in plan if c['NativeClubUID']];assert len(used)==len(set(used))
assert not any(c['IdentityDecision']in['unresolved','continuity_root_review']for c in plan)
cs=read(B/'source-competitions.json')
def table(code):
 c=next(c for c in cs if c['id']==code);z=read(B/c['previous_completed_table_file']);return {x['club_id']:dict(x,Competition=code,Source=c['previous_completed_table_file'])for t in z['tables']for x in t['rows']}
def key(c,rows):
 x=rows[c['TMID']];return (x['position'],-Fraction(x['points'],x['matches']),-Fraction(x['goal_difference'],x['matches']),-Fraction(x['wins'],x['matches']),int(c['TMID']))
decisions=[]
ger=[c for c in plan if c['Country']=='Germany']
for c in ger:
 c['DesiredDivision']=16 if 'L1'in c['Competitions']else 17 if 'L2'in c['Competitions']else None
third=[c for c in ger if 'L3'in c['Competitions']];lower=[c for c in ger if c['RealLevel']==4];prev3=table('L3');prev4={}
for code in ['RLN3','RLN4','RLW3','RLSW','RLB3']:prev4.update(table(code))
relegated=sorted([c for c in lower if c['TMID']in prev3],key=lambda c:key(c,prev3))
rest=sorted([c for c in lower if c['TMID']not in prev3 and c['TMID']in prev4],key=lambda c:key(c,prev4))
selected=(relegated+rest)[:37-len(third)];assert len(third)==20 and len(selected)==17
third+=selected
for c in selected:c['SelectionReason']='preserve_best_previous_3Liga_relegated'if c in relegated else'best_available_previous_Regionalliga_rank_then_PPG_GD_win';c['PreviousRank']=(prev3 if c in relegated else prev4)[c['TMID']]
def latitude(c):
 s=c['PublicStadium'];lat=s.get('latitude')
 if lat is not None and float(lat)!=0:return float(lat)
 return None
missing=[c for c in third if latitude(c)is None]
assert not missing,('geographic_coordinate_missing',[(c['TMID'],c['Name'])for c in missing])
third.sort(key=lambda c:(-latitude(c),int(c['TMID'])))
for i,c in enumerate(third):c['DesiredDivision']=18 if i<19 else 19;c['RegionalRule']='classic two latitude bands North19/South18 from actual stadium latitude; native2008transition later uses sporting outcomes';c['RegionalLatitude']=latitude(c)
for c in ger:
 if c['DesiredDivision']is None:c['DesiredDivision']=1058;c['SelectionReason']='retained_real_current_Regionalliga_catalogue_outside_classic_playable_capacity'
decisions.append(dict(Country='Germany',CurrentTop=18,CurrentSecond=18,ActualThird=20,ClassicThird=37,SelectedLower=[dict(TMID=c['TMID'],Name=c['Name'],Previous=c['PreviousRank'],Reason=c['SelectionReason'])for c in selected],Groups={'North':19,'South':18},Historical2008Transition='Engine native third division UID35010926 and third Regionalliga are created later. No EXE changes. Runtime season test remains required and not inferred from DAT counts.'))
for c in plan:
 if c['Country']=='Mexico':
  c['DesiredDivision']=214 if 'MEXA'in c['Competitions']else 215;c['SelectionReason']=c.get('SelectionReason','current_real_members_preserved')
mal=[c for c in plan if c['Country']=='Malaysia'];mprev=table('MAY2')
eligible=[c for c in mal if c['TMID']in['132529','120017']];promoted=sorted(eligible,key=lambda c:key(c,mprev))[0]
assert promoted['TMID']=='132529'
for c in mal:
 c['DesiredDivision']=650 if 'MYS1'in c['Competitions']or c['TMID']==promoted['TMID']else 651
 c['SelectionReason']=c.get('SelectionReason','current_real_members_preserved')
promoted['SelectionReason']='UMDamansara previous_position6; highest available licensed eligible lower first-team. PDRMwithdrawn/KelantanTRWunlicensed; reservesJohor/Selangor blocked alongside parent; PerakFA/KedahFA no top licence proof.'
decisions.append(dict(Country='Malaysia',RealTop=12,RealSecond=14,ClassicTop=13,ClassicSecond=13,PromotedTMID=promoted['TMID'],Previous=mprev[promoted['TMID']],ExcludedPreviousTop=['PDRM withdrew','KelantanTheRealWarriors unlicensed'],ExcludedHigherLower=['JDTII parent top','SelangorII parent top','PerakFA no national top licence proof','KedahFA no national top licence proof'],Sources=['https://www.malaysianfootballleague.com/Content/Post/Watch/5997','https://www.malaysianfootballleague.com/Content/Post/Watch/5998','https://www.malaysianfootballleague.com/Content/Post/Watch/5975'],BruneiDPMM='Retain real Brunei country54; repair existing Malaysia70 with exact UID5626771 inverse guard; official MFL foreign entrant, not nationality change to satisfy gate.'))
for c in plan:
 c['ProfileFile']=str((B/c['ProfileFile']).resolve());c['RosterFile']=str((B/c['RosterFile']).resolve())
 if c['NativeClubUID']and 'SourceCountryIndex'not in c:c['SourceCountryIndex']=world[c['NativeClubUID']]['Country']
counts=Counter(c['DesiredDivision']for c in plan);assert all(counts[d]==n for d,n in {16:18,17:18,18:19,19:18,214:18,215:24,650:13,651:13}.items()),counts
dump('club-plan.json',plan);dump('allocation-decisions.json',decisions);dump('root-identity-decisions-applied.json',dec)
dump('allocation-counts.json',dict(status='source_plan_balanced_not_native_write',counts=dict(counts),source_catalogue=len(plan),new=sum(not c['NativeClubUID']for c in plan),reuse=sum(bool(c['NativeClubUID'])for c in plan),phase='current2007classical; 2008Germanyruntimepending',real_season='2026/27',previous_completed_season='2025/26'))
print('ALLOCATED',dict(counts),'new',sum(not c['NativeClubUID']for c in plan),flush=True)
