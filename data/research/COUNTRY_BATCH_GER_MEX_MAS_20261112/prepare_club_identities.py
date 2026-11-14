from pathlib import Path
from collections import defaultdict,Counter
import sys,json,csv,re,unicodedata,hashlib
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
root=Path('J:/FM08dev');b=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(n,x):(b/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(s):
 s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower()
 s=re.sub(r'\b(sad|football|footballclub|futbol|club|clube|futebol|deportivo|desportivo|associacao|asociacion|de|da|do|cf|fc|fbc|cd|sc|fk|ik|if|il|sk|ad|gd|ud|sv|vfb|vfl|e\.v\.)\b',' ',s)
 return ''.join(re.findall('[a-z0-9]+',s))
world=read(b/'native-world-identities.json');byuid={x['ClubUID']:x for x in world};targets=read(b/'source-targets.json')
rawclubs={}
for p in (b/'sources/tm-raw').glob('*.json'):
 x=read(p)
 if '/clubs?'not in x['url']:continue
 data=json.loads(x['body']).get('data')
 if isinstance(data,list):
  for row in data:rawclubs[str(row['id'])]=row
countries={'Germany':145,'Mexico':109,'Malaysia':70};reg=defaultdict(set)
for folder in ['POLAND_GAPS_IMPORT_PACKAGE_20261111','SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111','FOUR_COUNTRY_X7_20261110','SWEDEN_SWITZERLAND_X3_20261109','UKRAINE_TURKEY_X2_20261109','WALES_USA_URUGUAY_2627_B1_20261109','HUNGARY_DATABASE_2627_H1_20261109']:
 for name in ['club-map.csv','foreign-owner-map.csv']:
  path=b.parent/folder/name
  if path.exists():
   for row in csv.DictReader(path.open(encoding='utf-8-sig',newline='')):
    if row.get('TMID')and row.get('ClubUID')and int(row['ClubUID'])in byuid:reg[row['TMID']].add(int(row['ClubUID']))
plans=[]
for c in targets:
 p=read(b/c['ProfileFile']);raw=rawclubs.get(c['TMID'],{});base=raw.get('baseDetails')or{}
 parent=str(base.get('mainClubId')or'');parent=parent if base.get('clubTypeId')==2 and parent!=c['TMID']else''
 country=54 if c['TMID']=='14320'else countries[c['Country']]
 labels=list(dict.fromkeys(n for n in [c['Name'],p.get('name'),p.get('official_name'),p.get('short_name')]+[n.get('name')for n in p.get('historical_names',[])]if n))
 keys={norm(n)for n in labels if n};hits=[x for x in world if x['Country']in[country,-1]and any(norm(n)in keys for n in x['Names'])]
 if not parent:hits=[x for x in hits if not x['ParentUID']]
 known=[byuid[u]for u in reg[c['TMID']]if byuid[u]['Country']in[country,-1]and bool(byuid[u]['ParentUID'])<=bool(parent)]
 uid=None;reason='requires_review';decision='unresolved'
 if len(known)==1:uid=known[0]['ClubUID'];decision='reuse_prior_TM_identity';reason='existing project TMID mapping revalidated against current source country/type; name proof retained'
 elif len(hits)==1:uid=hits[0]['ClubUID'];decision='reuse_unique_source_alias_country';reason='unique current/official/short/historical alias in same country'
 elif not hits and not known:decision='new_entity_candidate';reason='no verified native same-identity match'
 w=byuid.get(uid,{})
 plans.append(dict(c,NativeCountryIndex=country,ParentTMID=parent,ReserveTeam=bool(parent),SourceClubTypeID=base.get('clubTypeId'),SourceNames=labels,NativeClubUID=uid,NativeTeamIndex=w.get('TeamIndex'),NativeFamilyIndex=w.get('FamilyIndex'),ExistingStadiumIndex=w.get('StadiumIndex',-1),NativeParentUID=w.get('ParentUID'),IdentityDecision=decision,IdentityReason=reason,IdentityEvidence=['https://www.transfermarkt.com/-/startseite/verein/'+c['TMID']],FreshCandidates=[x['ClubUID']for x in hits],PriorRegistryCandidates=[x['ClubUID']for x in known],PublicStadium=p.get('stadium')or{},SugarDaddy=False,DesiredDivision=None))
dump('club-plan-draft.json',plans)
dump('identity-summary.json',dict(countries=dict(Counter(c['Country']for c in plans)),decisions=dict(Counter(c['IdentityDecision']for c in plans)),source_profiles=len(plans),publications=False,needs_review=[dict(TMID=c['TMID'],Name=c['Name'],Decision=c['IdentityDecision'],Candidates=c['FreshCandidates'],Prior=c['PriorRegistryCandidates'],Parent=c['ParentTMID'])for c in plans if c['NativeClubUID']is None]))
print('IDENTITY',dict(Counter(c['IdentityDecision']for c in plans)),flush=True)
for c in plans:
 if not c['NativeClubUID']:print(c['TMID'],c['Name'],c['IdentityDecision'],c['FreshCandidates'],c['ParentTMID'],flush=True)
