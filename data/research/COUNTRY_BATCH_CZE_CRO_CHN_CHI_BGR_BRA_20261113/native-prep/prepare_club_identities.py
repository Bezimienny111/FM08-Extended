from pathlib import Path
from collections import defaultdict,Counter
import json,csv,re,unicodedata,hashlib,sys
from functools import lru_cache
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;S=B.parent;R=S.parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(n,v):(B/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
@lru_cache(maxsize=None)
def norm(s):
 s=unicodedata.normalize('NFKD',str(s).translate(str.maketrans({248:'o',216:'O',322:'l',321:'L',273:'d',272:'D',230:'ae',198:'Ae',339:'oe',338:'Oe',223:'ss'}))).encode('ascii','ignore').decode().lower();s=re.sub(r'\.(?=[a-z])','',s)
 s=re.sub(r'\b(as|sd|rc|rcd|ca|cs|us|afc|ff|boldklub|fodbold|forening|sad|football|footballclub|futbol|club|clube|futebol|deportivo|desportivo|associacao|asociacion|de|da|do|cf|fc|fbc|cd|sc|fk|ik|if|il|sk|ad|gd|ud|sv|vfb|vfl|e\.v\.)\b',' ',s)
 return ''.join(re.findall('[a-z0-9]+',s))
world=read(B/'native-world-identities.json');byuid={x['ClubUID']:x for x in world};targets=read(S/'source-targets.json');registry=read(S/'collected/global-club-registry.json');regby={x['TMID']:x for x in registry};rawclubs={};tmcountries={};rawpins={}
# Reuse the closed raw index; read only identity and attributes responses, never query API.
for x in read(S/'raw-source-index.json'):
 url=x['url']
 if '/clubs?'not in url and not re.search(r'/club/\d+$',url) and not url.endswith('/attributes'):continue
 p=S/x['raw_file']
 if str(p)in rawpins:continue
 obj=read(p);data=json.loads(obj['body']).get('data');rawpins[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 if url.endswith('/attributes')and isinstance(data,dict):tmcountries.update({str(c['id']):c['name']for c in data.get('countries',[])})
 elif isinstance(data,(list,dict)):
  for c in data if isinstance(data,list) else [data]:rawclubs[str(c['id'])]=c
countries={norm(n):r['index']for r in read(B/'native-nation-catalog.json')for n in r['names']if n};countryalias={'Netherlands':'Holland','Hongkong':'Hong Kong','United States of America':'USA','Czechia':'Czech Republic','North Macedonia':'FYR of Macedonia','Korea, South':'South Korea','Korea, North':'North Korea','Bosnia & Herzegovina':'Bosnia and Herzegovina'}
prior=defaultdict(set)
for fp in list(R.glob('*/club-map.csv'))+list(R.glob('*/foreign-owner-map.csv'))+[R/'COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep/club-map.csv',R/'COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep/foreign-owner-map.csv',R/'COUNTRY_BATCH_KOR_COL_ISR_20261112/six-country-stage/club-map.csv',R/'COUNTRY_BATCH_KOR_COL_ISR_20261112/six-country-stage/foreign-owner-map.csv']:
 for r in csv.DictReader(fp.open(encoding='utf-8-sig')):
  if r.get('TMID')and r.get('ClubUID')and int(r['ClubUID'])in byuid:prior[r['TMID']].add(int(r['ClubUID']))
for fp in list(R.glob('*/foreign-owner-aliases.json'))+[R/'COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep/foreign-owner-aliases.json',R/'COUNTRY_BATCH_KOR_COL_ISR_20261112/six-country-stage/foreign-owner-aliases.json']:
 if not fp.exists():continue
 for a in read(fp):
  u=a.get('NativeClubUID');tid=a.get('CanonicalMainTMID')
  if u and tid and int(u)in byuid and not str(a.get('Decision','')).startswith('defer'):prior[str(tid)].add(int(u))
def plain(v):
 return ''.join(re.findall('[a-z0-9]+',unicodedata.normalize('NFKD',str(v).translate(str.maketrans({248:'o',216:'O',322:'l',321:'L',273:'d',272:'D',230:'ae',198:'Ae',339:'oe',338:'Oe',223:'ss'}))).encode('ascii','ignore').decode().lower()))
root_review={'19214','760','26535','96026','5752'}
plans=[]
for c in targets:
 tid=c['TMID'];p=read(S/c['ProfileFile']);raw=rawclubs.get(tid,{});base=raw.get('baseDetails')or{};source=regby.get(tid,{})
 parent=source.get('ParentTMID')or'';countrylabel=tmcountries.get(str(base.get('countryId') or source.get('SourceCountryID')));ni=countries.get(norm(countryalias.get(countrylabel,countrylabel)))if countrylabel else None
 if ni is None:ni=countries.get(norm(c['Country']))
 labels=list(dict.fromkeys(n for n in[c['Name'],p.get('name'),p.get('official_name'),p.get('short_name')]+[n.get('name')for n in p.get('historical_names',[])]if n))
 keys={norm(n)for n in labels if len(norm(n))>=3};hits=[w for w in world if w['TeamCountry']in[ni,-1]and any(norm(n)in keys for n in w['Names'])]
 parented_first_candidates=[w for w in hits if w['ParentUID']] if not parent else []
 if not parent:hits=[w for w in hits if not w['ParentUID']]
 else:hits=[w for w in hits if w['ParentUID']]
 if tid=='162':
  # Sporting affiliation of the existing Monaco club is France; preserve it, do not replace by geographic Monaco.
  league_ni=countries[norm(c['Country'])]
  cross=[w for w in world if w['TeamCountry']==league_ni and not w['ParentUID']and any(norm(n)in keys for n in w['Names'])]
  if len(cross)==1:hits=cross;ni=league_ni
 knowncountryhits=[w for w in hits if w['TeamCountry']==ni]
 if knowncountryhits:hits=knowncountryhits
 known=[byuid[u]for u in prior[tid]if byuid[u]['TeamCountry']in[ni,countries.get(norm(c['Country']))] and bool(byuid[u]['ParentUID'])<=bool(parent)]
 ranked=[]
 current=[(c['Name'],40),(p.get('name'),40),(p.get('official_name'),50),(p.get('short_name'),30),(p.get('abbreviation'),25)]
 for w0 in hits:
  score=max([weight for label,weight in current if label and any(plain(label)==plain(n)for n in w0['Names'])]+[0])
  if score:ranked.append((score,w0))
 if ranked and tid not in root_review:
  best=max(v[0]for v in ranked);preferred=[w0 for score,w0 in ranked if score==best]
  if len(preferred)==1:hits=preferred
 uid=None;decision='unresolved';reason='requires exact identity/parent review'
 if len(known)==1:uid=known[0]['ClubUID'];ni=known[0]['TeamCountry'];decision='reuse_prior_TM_identity';reason='prior confirmed exactTMID mapping, current knowncountry and type revalidated'
 elif len(hits)==1 and hits[0]['TeamCountry']==ni:
  matched=[n for n in labels if any(norm(n)==norm(v)for v in hits[0]['Names'])]
  if any(len(norm(n))>=4 or n==p.get('official_name') or n==c['Name'] or n==p.get('abbreviation') or n==p.get('club_code')for n in matched):uid=hits[0]['ClubUID'];decision='reuse_unique_profile_alias_country';reason='single exact normalized current/official/historical profilealias in knowncountry'
  else:reason='only short/generic alias requires review'
 elif not hits and not known:decision='new_entity_candidate';reason='current real source club; no native exact match, preserve unrelated histories'
 if decision=='new_entity_candidate' and parented_first_candidates:decision='requires_typed_representation_review';reason='Potentialsamecurrentfirstidentity already exists asparentedTEAM; do not create duplicate or blindflipkind'
 if tid in root_review:uid=None;decision='requires_root_review';reason='explicit bounded continuity/representation review; no automatic generic alias, country repair or reserve conversion'
 local_path=B/'local-identity-decisions.json'
 local=next((z for z in read(local_path)if z['TMID']==tid),None)if local_path.exists()else None
 if local and tid not in root_review:
  uid=local['NativeClubUID'];decision='reuse_documented_local_cache_alias';reason=local['Reason']
  assert byuid[uid]['TeamCountry']==ni
 w=byuid.get(uid,{})
 plans.append(dict(c,ProfileFile=str((S/c['ProfileFile']).resolve()),RosterFile=str((S/c['RosterFile']).resolve()),LeagueCountry=c['Country'],SourcePhysicalCountry=countrylabel,NativeCountryIndex=ni,ParentTMID=parent,ReserveTeam=bool(parent),SourceClubTypeID=source.get('SourceClubTypeID',c.get('SourceClubTypeID')),SourceNames=labels,NativeClubUID=uid,NativeTeamIndex=w.get('TeamIndex'),NativeFamilyIndex=w.get('NameFamilyIndex'),NativeContractFamilyIndex=w.get('TeamTailFamilyIndex'),NativeContractFamilyUID=w.get('TeamTailFamilyUID'),NativeParentUID=w.get('ParentUID'),NativeTeamKind=w.get('NativeTeamKind'),ExistingStadiumIndex=w.get('StadiumIndex',-1),IdentityDecision=decision,IdentityReason=reason,IdentityEvidence=[str(S/c['ProfileFile']),str(S/'collected/global-club-registry.json')],FreshCandidates=[dict(UID=x['ClubUID'],Country=x['Country'],TeamCountry=x['TeamCountry'],Kind=x['NativeTeamKind'],ParentUID=x['ParentUID'],Names=x['Names'])for x in hits+parented_first_candidates],PriorRegistryCandidates=[x['ClubUID']for x in known],PublicStadium=p.get('stadium')or{},SugarDaddy=False,DesiredDivision=None))
# Existing typed parent contracts must agree with a proven source parent; never convert reserve kind blindly.
bytm={x['TMID']:x for x in plans};exceptions=[]
for x in plans:
 if x['ParentTMID']and x['NativeClubUID']:
  par=bytm.get(x['ParentTMID'],{});expected=par.get('NativeClubUID');actual=x['NativeParentUID']
  x['ParentPreflight']='PASS_SOURCE_PARENT_AND_TYPED_NATIVE_TEAMTAIL'if expected and actual==expected else'REQUIRES_PARENT_OR_AFFILIATION_REVIEW'
  if x['ParentPreflight'].startswith('REQUIRES'):exceptions.append(dict(Type='reserve_parent',TMID=x['TMID'],Name=x['Name'],ParentTMID=x['ParentTMID'],ExpectedNativeParent=expected,ActualTypedParent=actual,ClubUID=x['NativeClubUID']))
 if x['NativeClubUID']is None:exceptions.append(dict(Type='club_identity',TMID=x['TMID'],Name=x['Name'],Decision=x['IdentityDecision'],Candidates=x['FreshCandidates'],ParentTMID=x['ParentTMID']))
used=defaultdict(list)
for x in plans:
 if x['NativeClubUID']:used[x['NativeClubUID']].append(x['TMID'])
for u,ts in used.items():
 if len(ts)>1:exceptions.append(dict(Type='repeated_native_club_UID',UID=u,TMIDs=ts))
dump('club-plan-draft.json',plans);dump('club-identity-exceptions.json',exceptions);dump('source-identity-cache-pins.json',rawpins)
dump('identity-summary.json',dict(SourceTargets=len(plans),Decisions=dict(Counter(x['IdentityDecision']for x in plans)),ExceptionsByType=dict(Counter(x['Type']for x in exceptions)),RawIdentityFilesReused=len(rawpins),NativeAllocation=False,NativeWrite=False))
print('CLUB_DRAFT',len(plans),dict(Counter(x['IdentityDecision']for x in plans)),'EXCEPTIONS',dict(Counter(x['Type']for x in exceptions)),flush=True)