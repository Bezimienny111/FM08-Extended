from pathlib import Path
import json
B=Path(__file__).resolve().parent
specs=[('GB1',1),('GB2',2),('GB3',3),('GB4',4),('CNAT',5),('NLN6',6),('NLS6',6)]
(B/'source-competitions.json').write_text(json.dumps([dict(Country='England',id=i,RealLevel=l,Role='main_playable')for i,l in specs],indent=2),encoding='utf-8')
old=Path('J:/FM08dev/FmLauncher/data/research/COUNTRY_BATCH_CZE_CRO_CHN_CHI_BGR_BRA_20261113/competition-prep/resolve_catalogues.py').read_text(encoding='utf-8')
old=old.replace("['China','Chile','Brazil']","[]").replace('Only China/Chile/Brazil are calendar','England uses26/27wintercalendar').replace('for China/Chile/Brazil','for calendarcountriesoutsidecurrentEnglandscope')
(B/'resolve_catalogues.py').write_text(old,encoding='utf-8')
