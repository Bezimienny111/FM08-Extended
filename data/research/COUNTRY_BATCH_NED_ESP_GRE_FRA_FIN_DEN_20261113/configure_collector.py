from pathlib import Path
import sys,json,hashlib,collections
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
bootstrap=read(B/'competition-prep/source-targets-bootstrap.json');comps=read(B/'competition-prep/source_competitions.json')
assert len(bootstrap)==584 and len({str(c['TMID']) for c in bootstrap})==584
assert len(comps)==38 and all(c.get('CurrentSeason') and not c.get('SeasonResolutionError') for c in comps)
old=read(B/'source-targets.json') if (B/'source-targets.json').exists() else []
existing={str(c['TMID']):c for c in old};merged=[]
for c in bootstrap:
 prior=existing.get(str(c['TMID']),{})
 assert not prior or (prior.get('APISeason')==c['APISeason'] and prior.get('Country')==c['Country'])
 merged.append(dict(c,**{k:v for k,v in prior.items() if k in ['ProfileFile','RosterFile','PlayersFetched','FetchError']}))
assert all(c['RealSeason']=='2026' and c['APISeason']=='2025' for c in merged if c['Country']=='Finland')
dump(B/'source-targets.json',merged);dump(B/'source-competitions.json',comps)
pins={str(p.relative_to(B)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [B/'competition-prep/source-targets-bootstrap.json',B/'competition-prep/source_competitions.json',B/'collect_sources_adapter.py']}
dump(B/'collector-config.json',dict(countries=['Netherlands','Spain','Greece','France','Finland','Denmark'],clubs=584,competitions=38,by_country=dict(collections.Counter(c['Country'] for c in merged)),snapshot_date='2026-11-13',policies=dict(real_dates_only=True,DOB_shift=False,CA_PA_generated=False,native_UID_allocation=False,native_DB_write=False,loan_owners='worldwide',optional_buy='only confirmed facts',mandatory_buy=False,missing_profiles='explicit gaps; no forced research',Finland='real2026→API2025; previousreal2025→API2024'),pins=pins))
print('SIX_COUNTRY_CONFIG_READY',len(merged),dict(collections.Counter(c['Country'] for c in merged)),flush=True)
