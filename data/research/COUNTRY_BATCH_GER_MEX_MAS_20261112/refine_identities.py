from pathlib import Path
from collections import Counter
import json,re,unicodedata,sys
sys.stdout.reconfigure(encoding='utf-8')
b=Path(__file__).resolve().parent;read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));plans=read(b/'club-plan-draft.json');world=read(b/'native-world-identities.json');by={x['ClubUID']:x for x in world}
def norm(s):
 s=str(s).replace(chr(223),'ss')
 s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
 return ''.join(re.findall('[a-z0-9]+',s))
manual={'4':899,'269':2245,'10':904,'8':900,'109':6000005,'1557':8709077,'139':6000001,'111':2244,'45':121190,'4700':879612,'2442':879856,'72':955,'473':876841,'393':877165,'7055':104360,'13353':136021,'7633':1260,'23505':5661084,'28185':136018,'14320':5626771}
rootreview={'40188','12728','18662','15817','7013','131747','132253','5608','10284'}
index={}
for w in world:
 for k in {norm(n)for n in w['Names']if n}:index.setdefault(k,[]).append(w)
for c in plans:
 if c['TMID']in rootreview:c['IdentityDecision']='continuity_root_review';continue
 uid=manual.get(c['TMID']);reason='explicit current source/native alias, prefix/transliteration/reserve-name reviewed'
 if uid is None:
  matches={}
  p=read(b/c['ProfileFile'])
  source=[p.get('name'),p.get('official_name'),p.get('short_name')]+[n.get('name')for n in p.get('historical_names',[])]
  for n,label in enumerate(source):
   if not label:continue
   for w in index.get(norm(label),[]):
    if w['Country']not in[c['NativeCountryIndex'],-1]:continue
    if not c['ReserveTeam'] and (w['ParentUID']or re.search(r'\b(II|U23|U19|Reserves|Amateure)\b',w['Names'][0],re.I)):continue
    if c['ReserveTeam']and not(w['ParentUID']or re.search(r'\b(II|U23|Reserves|Amateure)\b',w['Names'][0],re.I)):continue
    score=(100 if n<2 else 60 if n==2 else 20)+(5 if w['Country']==c['NativeCountryIndex']else 0)
    matches[w['ClubUID']]=max(score,matches.get(w['ClubUID'],0))
  if matches:
   high=max(matches.values());best=[u for u,s in matches.items()if s==high]
   if len(best)==1:uid=best[0];reason='unique strongest exact current/official source name; historical aliases lower priority; reserve and country checked'
  if uid is None and c.get('NativeClubUID')and c['IdentityDecision']in['reuse_unique_source_alias_country','reuse_prior_TM_identity']:
   uid=c['NativeClubUID'];reason=c['IdentityReason']
 if uid:
  w=by[uid];assert w['Country']in[c['NativeCountryIndex'],-1]or uid==5626771
  c.update(NativeClubUID=uid,NativeTeamIndex=w['TeamIndex'],NativeFamilyIndex=w['FamilyIndex'],ExistingStadiumIndex=w['StadiumIndex'],NativeParentUID=w['ParentUID'],IdentityDecision='reuse_reviewed_native_identity',IdentityReason=reason,SourceCountryIndex=w['Country'],NativeCountryRepairTo=c['NativeCountryIndex']if w['Country']!=c['NativeCountryIndex']else None,NativeNames=w['Names'])
 else:
  c.update(NativeClubUID=None,NativeTeamIndex=None,NativeFamilyIndex=None,NativeParentUID=None,ExistingStadiumIndex=-1)
  if c['IdentityDecision']!='unresolved':c['IdentityDecision']='new_verified_source_entity_no_safe_native_match'
used={}
for c in plans:
 u=c['NativeClubUID']
 if u and u in used:print('COLLISION',u,used[u],c['TMID'],flush=True)
 if u:used[u]=c['TMID']
(b/'club-plan-reviewed.json').write_text(json.dumps(plans,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('DECISIONS',dict(Counter(c['IdentityDecision']for c in plans)),flush=True)
for c in plans:
 if c['IdentityDecision']=='unresolved':print('UNRESOLVED',c['TMID'],c['Name'],c['FreshCandidates'])
print('NEW',[c['Name']for c in plans if c['IdentityDecision'].startswith('new_')],flush=True)
