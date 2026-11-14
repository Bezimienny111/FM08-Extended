"""Normalize previous completed phase order; preserve final official points, never add carried points twice."""
from pathlib import Path
import json,hashlib,sys
sys.dont_write_bytecode=True;O=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
comps=read(O/'source-competitions.json');phase_index={r['id']:r for r in read(O/'previous-final-phases.json')};assert len(phase_index)==23 and all(x['Status']=='FETCHED'for x in phase_index.values())
phase_specs={'GR1':[('POGR',0),('GRPL',4),('S1PO',8)],'GRS2':[('S2PA',0),('S2PO',4)],'FI1':[('F1CL',0),('F1CC',6)],'FIYK':[('FI3P',0),('FI3R',6)],'FI3A':[('FP3A',0),('F3KA',6)],'FI3B':[('KP3B',0),('F3KB',6)],'FI3C':[('KP3C',0),('F3KC',6)],'DK1':[('DKMR',0),('DKAR',6)],'DK2':[('DK2P',0),('DK2R',6)],'DK3O':[('DK3V',0),('DKDA',6)],'DK4L':[('D4P1',0),('D4P2',6)]}
checks=0;gaps=[];output=[]
def validate(r,p):
 global checks
 assert r['wins']+r['draws']+r['losses']==r['matches'],(p,r);assert r['goals_for']-r['goals_against']==r['goal_difference'],(p,r);checks+=1
for c in comps:
 path=O/c['previous_completed_table_file'];raw=read(path);reg={};groups={}
 for table in raw['tables']:
  for row in table['rows']:
   validate(row,str(path));tid=row['club_id'];assert tid not in reg,(c['id'],tid);reg[tid]=row;groups[tid]=table['name']
 rows=[];refs=[dict(Path=str(path),SHA256=sha(path))]
 if c['id'] not in phase_specs:
  rows=[dict(TMID=tid,Name=r['club_name'],Group=groups[tid],FinalPosition=r['position'],Matches=r['matches'],Wins=r['wins'],Draws=r['draws'],Losses=r['losses'],GoalsFor=r['goals_for'],GoalsAgainst=r['goals_against'],GoalDifference=r['goal_difference'],Points=r['points'],FinalRaw=r,ClassificationStatus='single_phase_closed_table')for tid,r in reg.items()]
 else:
  for code,offset in phase_specs[c['id']]:
   p=O/phase_index[code]['TableFile'];leaf=read(p);refs.append(dict(Path=str(p),SHA256=sha(p)))
   for table in leaf['tables']:
    for r in table['rows']:
     validate(r,str(p));tid=r['club_id'];assert tid in reg,(c['id'],tid,'final_not_regular');a=reg[tid]
     q=dict(TMID=tid,Name=r['club_name'],Group=groups[tid],FinalPosition=r['position']+offset,Matches=a['matches']+r['matches'],Wins=a['wins']+r['wins'],Draws=a['draws']+r['draws'],Losses=a['losses']+r['losses'],GoalsFor=a['goals_for']+r['goals_for'],GoalsAgainst=a['goals_against']+r['goals_against'],GoalDifference=a['goal_difference']+r['goal_difference'],Points=r['points'],RegularRaw=a,FinalRaw=r,FinalPhaseCode=code,ClassificationStatus='terminal_phase_order_and_reported_final_points',Derivation='WDL/GF/GA/matches regular+phase; points ONLY terminalreported value; retains official bonus/halving/deductions, not3W+D reconstruction')
     assert q['Wins']+q['Draws']+q['Losses']==q['Matches']and q['GoalsFor']-q['GoalsAgainst']==q['GoalDifference'];rows.append(q)
  assert len({r['TMID']for r in rows})==len(rows),(c['id'],'duplicate_final')
  missing=set(reg)-{r['TMID']for r in rows}
  for tid in sorted(missing):
   r=reg[tid];gap=dict(Competition=c['id'],TMID=tid,Name=r['club_name'],Reason='present_in_regular_but_absent_from_all_final_phases; no invented_finalrank, withdrawal/eligibility requires profileconfirmation',RegularFacts=r);gaps.append(gap);rows.append(dict(TMID=tid,Name=r['club_name'],Group=groups[tid],FinalPosition=None,ClassificationStatus='unranked_missing_terminal_phase',RegularRaw=r))
  assert len(rows)==len(reg)
 if c['id']=='FI1':assert sorted(r['Matches']for r in rows)==[27]*6+[32]*6
 if c['id']=='FIYK':assert {r['Matches']for r in rows}=={27}
 if c['Country']=='Denmark':assert {r['Matches']for r in rows}=={32}
 if c['id']=='GR1':assert sorted(r['Matches']for r in rows)==[32]*8+[36]*6
 if c['id']=='GRS2':assert sorted(r['Matches']for r in rows)==[24]*8+[28]*12
 output.append(dict(Country=c['Country'],Competition=c['id'],Season=c['PreviousCompletedSeason'],CurrentParticipantSeason=c['CurrentSeason'],Rows=rows,SourcePins=refs,Status='complete_previous_participants_with_explicit_unranked_gap'if any(r['FinalPosition']is None for r in rows)else'complete_previous_final_order'))
result=dict(Status='PREVIOUS_SEASON_FINAL_TABLES_38_WITH23_PHASES_PINNED',Competitions=output,MainTableCount=38,FinalPhaseCount=23,RawRowsArithmeticChecked=checks,UnrankedGaps=gaps,SeasonPolicy='FINrosters2026 provider2025 use previous2025 provider2024; allotherrosters26/27 provider2026 use25/26 provider2025',CumulativeDerivationQualification='Phase row statistics and regular statistics retained sidebyside; terminalpoints copied, no duplicatedcarry. Order officialperfinalgroup; crossgroupPPG uses cumulativeactualmatches, no artificialmatchesforwithdrawnclubs.',NativeWrite=False)
(O/'previous-final-tables-normalized.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('PASS38tables+23phases; rawrows',checks,'unranked',[(g['Competition'],g['TMID'],ascii(g['Name']))for g in gaps])
