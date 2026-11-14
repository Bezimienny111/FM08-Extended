from pathlib import Path
import json
B=Path(__file__).resolve().parent
specs=[('Belarus','WER1',1),('Belarus','WER2',2),('Belgium','BE1',1),('Belgium','BE2',2),('Belgium','BE3V',3),('Belgium','BE3A',3),('Austria','A1',1),('Austria','A2',2),('Austria','ATRO',3),('Austria','ARLS',3),('Austria','RLNA',3),('Austria','RLWA',3),('Australia','AUS1',1),('Argentina','ARG1',1),('Argentina','ARGC',1),('Argentina','ARG2',2)]
(B/'source-competitions.json').write_text(json.dumps([dict(Country=c,id=i,RealLevel=l,Role='main_or_required_cascade')for c,i,l in specs],indent=2),encoding='utf-8')
old=Path('J:/FM08dev/FmLauncher/data/research/COUNTRY_BATCH_CZE_CRO_CHN_CHI_BGR_BRA_20261113/competition-prep/resolve_catalogues.py').read_text(encoding='utf-8')
old=old.replace("['China','Chile','Brazil']","['Belarus','Argentina']").replace('Only China/Chile/Brazil','Only Belarus/Argentina').replace('for China/Chile/Brazil','for Belarus/Argentina')
(B/'resolve_catalogues.py').write_text(old,encoding='utf-8')
