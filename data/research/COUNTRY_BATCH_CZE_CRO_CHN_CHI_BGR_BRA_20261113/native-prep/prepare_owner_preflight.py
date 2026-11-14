from pathlib import Path
from collections import defaultdict,Counter
from functools import lru_cache
import json,csv,ast,hashlib,sys
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent;S=B.parent;R=S.parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(n,v):(B/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Exact normalization already used by the shared X17-derived club mapper; no second matcher implementation.
import unicodedata,re
node=next(x for x in ast.parse((B/'prepare_club_identities.py').read_text(encoding='utf-8')).body if isinstance(x,ast.FunctionDef)and x.name=='norm');exec(compile(ast.Module(body=[node],type_ignores=[]),'shared_club_norm','exec'))
core={x['TMID']:x for x in read(B/'club-plan-draft.json')};world=read(B/'native-world-identities.json');byuid={x['ClubUID']:x for x in world};reg=read(S/'collected/global-club-registry.json');raw={};cache={};tmcountries={}
for ref in read(S/'raw-source-index.json'):
 if '/clubs?' not in ref['url'] and not re.search(r'/club/\d+$',ref['url']):continue
 p=S/ref['raw_file'];data=json.loads(read(p)['body']).get('data')or[]
 for c in data if isinstance(data,list) else [data]:
  if isinstance(c,dict) and c.get('id') is not None:raw[str(c['id'])]=c
for ref in read(S/'raw-source-index.json'):
 if ref['url'].endswith('/attributes'):
  d=json.loads(read(S/ref['raw_file'])['body']).get('data')or{}
  tmcountries.update({str(c['id']):c['name']for c in d.get('countries',[])})
nations={norm(n):x['index']for x in read(B/'native-nation-catalog.json')for n in x['names']if n}
na={'Netherlands':'Holland','Hongkong':'Hong Kong','United States of America':'USA','United States':'USA','Czechia':'Czech Republic','North Macedonia':'FYR of Macedonia','Korea, South':'South Korea','Korea, North':'North Korea','Bosnia & Herzegovina':'Bosnia and Herzegovina'}
prior=defaultdict(set)
for p in list(R.glob('*/club-map.csv'))+list(R.glob('*/foreign-owner-map.csv'))+[R/'COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep/club-map.csv',R/'COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep/foreign-owner-map.csv',R/'COUNTRY_BATCH_KOR_COL_ISR_20261112/six-country-stage/club-map.csv',R/'COUNTRY_BATCH_KOR_COL_ISR_20261112/six-country-stage/foreign-owner-map.csv']:
 if not p.exists():continue
 for x in csv.DictReader(p.open(encoding='utf-8-sig')):
  if x.get('TMID')and x.get('ClubUID')and int(x['ClubUID'])in byuid:prior[x['TMID']].add(int(x['ClubUID']))
for p in list(R.glob('*/foreign-owner-aliases.json'))+[R/'COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep/foreign-owner-aliases.json',R/'COUNTRY_BATCH_KOR_COL_ISR_20261112/six-country-stage/foreign-owner-aliases.json']:
 if not p.exists():continue
 for x in read(p):
  if x.get('NativeClubUID')and x.get('CanonicalMainTMID')and int(x['NativeClubUID'])in byuid and not str(x.get('Decision','')).startswith('defer'):prior[str(x['CanonicalMainTMID'])].add(int(x['NativeClubUID']))
facts=[x['SourceFact']for x in read(B/'person-identity-candidates.json')if x['Loan']];owners=sorted({str(x['OwnerTMID'])for x in facts},key=int);result=[]
for tid in owners:
 child=raw.get(tid,{});cb=child.get('baseDetails')or{};main=str(cb.get('mainClubId')or tid);main=tid if main in['0','None']else main;mother=raw.get(main)or(child if main==tid else{});mb=mother.get('baseDetails')or{};country=tmcountries.get(str(mb.get('countryId')or cb.get('countryId')or next((r.get('SourceCountryID') for r in reg if r['TMID']==tid),None)));ni=nations.get(norm(na.get(country,country)))if country else None
 labels=list(dict.fromkeys(n for n in[mother.get('name'),mb.get('shortName')]if n));keys={norm(n)for n in labels};hits=[w for w in world if w['TeamCountry']==ni and not w['ParentUID']and any(norm(n)in keys for n in w['Names'])]if ni is not None else[];known=[byuid[u]for u in prior[main]if byuid[u]['TeamCountry']==ni and not byuid[u]['ParentUID']]
 uid=None;decision='defer_owner_identity_unresolved';c=core.get(main)
 if c:
  uid=c['NativeClubUID'];decision='within_core_verified_existing'if uid else'within_core_pending_identity_or_new_linked_allocation'
 elif len(known)==1:uid=known[0]['ClubUID'];decision='reuse_prior_verified_TM_owner'
 elif len(hits)==1:uid=hits[0]['ClubUID'];decision='reuse_unique_raw_name_country_first_team'
 row=dict(SourceTMID=tid,CanonicalMainTMID=main,Name=mother.get('name')or child.get('name'),Country=country,NativeCountryIndex=ni,NativeClubUID=uid,Decision=decision,WithinCoreBatch=main in core,RawMainPresent=bool(mother),SourceReserveCanonicalization=tid!=main,NativeCandidates=[dict(UID=w['ClubUID'],Names=w['Names'],Country=w['TeamCountry'],Kind=w['NativeTeamKind'])for w in hits],PriorCandidates=[w['ClubUID']for w in known],AffectedPlayerTMIDs=[x['TMID']for x in facts if str(x['OwnerTMID'])==tid],NoNativeWrite=True)
 result.append(row)
dump('foreign-owner-aliases-draft.json',result);dump('foreign-owner-preflight-summary.json',dict(SourceOwners=len(result),ChosenLoanPeople=len(facts),Decisions=dict(Counter(x['Decision']for x in result)),PendingOwnerActors=sum(len(x['AffectedPlayerTMIDs'])for x in result if x['NativeClubUID']is None),RawCacheOnly=True,NewRequests=0,NativeWrite=False))
print('OWNER_PREFLIGHT',len(result),'owners',len(facts),'loanpeople',dict(Counter(x['Decision']for x in result)))