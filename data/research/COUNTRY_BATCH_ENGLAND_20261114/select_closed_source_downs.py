from pathlib import Path
import json,sys
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;P=B/'competition-prep';read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
prev={}
for c in read(P/'source_competitions.json'):
 for tab in read(B/c['previous_completed_table_file'])['tables']:
  for r in tab['rows']:prev[r['club_id']]=dict(r,PreviousLevel=c['RealLevel'],PreviousCompetition=c['id'])
for group in ['NLN6','NLS6']:
 rows=[r for r in read(P/'source-targets-bootstrap.json')if r['SourceCompetition']==group and prev.get(r['TMID'],{}).get('PreviousLevel')==6]
 rows.sort(key=lambda r:prev[r['TMID']]['position'])
 print(group,[(r['TMID'],r['Name'],prev[r['TMID']]['position'],prev[r['TMID']]['PreviousCompetition'])for r in rows[-4:]])
