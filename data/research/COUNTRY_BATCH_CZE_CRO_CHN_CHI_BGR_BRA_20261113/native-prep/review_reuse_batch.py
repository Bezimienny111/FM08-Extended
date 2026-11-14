"""Independent cache/name/geography review of existing nativeclub candidates, no fetch/writeDB."""
from pathlib import Path
import sys,json,struct,re,unicodedata,hashlib,collections
sys.dont_write_bytecode=True;sys.path.insert(0,'FM08-Database-Tools/scratch')
from create_italy_structure_i1_20261108 import load,languages,lang_sections,find_table
from audit_poland_v25_common_r1_20261108 import stadium,city
B=Path(__file__).resolve().parent;S=B.parent;read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def canon(s):return ''.join(re.findall('[a-z0-9]+',unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower()))
def full(s):
 s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower();s=re.sub(r'\b(gnk|hnk|nk|pfc|ofc|ofk|esporte|esportivo|esportiva|desportiva|desportivo|deportivo|sportivo|sport|sociedade|sociedad|associacao|asociacion|nogometni|klub|futebol|football|club|clube|de|da|do|the|fc|fk|sc|sk|ac|cd|cf|ec|aa|afc|fbc)\b',' ',s);return canon(s)
plans=read(B/'club-plan-draft.json');world=read(B/'native-world-identities.json');byuid={x['ClubUID']:x for x in world};src=B/'input/X19-after-SI';en,_=lang_sections(dict(languages((src/'lang_db.dat').read_bytes()))[8]);a=load(src,'server_db.dat');c=load(src,'client_db.dat');stad,_,_=find_table(a,[x['uid'] for x in en['stadium']],lambda r:stadium(r,62));cities,_,_=find_table(c,[x['uid'] for x in en['city']],city);sl={x['uid']:x['names'] for x in en['stadium']};cl={x['uid']:x['names'] for x in en['city']}
raw={};refs={}
for ref in read(S/'raw-source-index.json'):
 if '/clubs?' not in ref['url'] and not re.search(r'/club/\d+$',ref['url']):continue
 d=json.loads(read(S/ref['raw_file'])['body']).get('data')or[]
 for v in d if isinstance(d,list)else[d]:
  t=str(v.get('id',''))
  if t and ref.get('fetched_at','')>=refs.get(t,{}).get('fetched_at',''):raw[t]=v;refs[t]=ref
out=[]
for p in plans:
 uid=p.get('NativeClubUID')
 if not uid:continue
 w=byuid[uid];profile=read(Path(p['ProfileFile']));base=raw.get(p['TMID'],{}).get('baseDetails')or{};location=(base.get('superiorClub')or{}).get('location')or{};st=profile.get('stadium')or{};sourcecity=[s for s in [location.get('city'),profile.get('address_line_2'),st.get('address_line_2')] if s];nativecity=[];nativevenue=[]
 if w['StadiumIndex']>=0:
  stadiumrow=stad[w['StadiumIndex']];nativevenue=sl.get(stadiumrow['uid'],[]);ci=struct.unpack_from('<i',stadiumrow['raw'],46)[0]
  if ci>=0:nativecity=cl.get(cities[ci]['uid'],[])
 # Cityqualifiers/caseaccents handled explicitly, no invented town from clubnickname.
 nativecity=[s for s in nativecity if s];citykeys={canon(re.sub(r'\s*\([^)]*\)','',n)) for n in nativecity};aliases={'prague':'praha','pilsen':'plzen','saintpetersburg':'sanktpeterburg'};citykeys|={aliases[k] for k in citykeys if k in aliases};sourcekeys=[canon(x) for x in sourcecity];geomatch=bool(citykeys and any(k and k in sk for k in citykeys for sk in sourcekeys));geoconflict=bool(citykeys and sourcekeys and not geomatch)
 current=[p['Name'],profile.get('name'),raw.get(p['TMID'],{}).get('name')];legal=profile.get('official_name');historical=[x.get('name') for x in profile.get('historical_names',[])];nativefull=w['Names'][0] if w['Names'] else ''
 def fullnamekeys(x):
  keys={full(x)}
  if geomatch:
   keys.add(full(re.sub(r'\([^)]*\)','',str(x))))
   for cityname in nativecity:
    ck=canon(re.sub(r'\s*\([^)]*\)','',cityname))
    if ck and ck in canon(x):keys.add(full(x).replace(ck,''))
  return {k for k in keys if len(k)>=4}
 nativekeys=fullnamekeys(nativefull);mainmatch=[x for x in current if x and fullnamekeys(x)&nativekeys];legalmatch=bool(legal and fullnamekeys(legal)&nativekeys);historymatch=[x for x in historical if x and fullnamekeys(x)&nativekeys]
 if geomatch and not historymatch:historymatch=[x for x in historical if x and len(x.split())>=2 and any(full(x)==full(n) and len(n.split())>=2 for n in w['Names'])]
 venue=bool(st.get('name') and any(canon(st['name'])==canon(v) for v in nativevenue));prior=p['IdentityDecision']=='reuse_prior_TM_identity'
 if prior:status='PRIOR_ACCEPTED_TMID_UID_PLUS_TYPED_COUNTRY_PARENT_REVALIDATED'
 elif geoconflict:status='REVIEW_GEOGRAPHY_MISMATCH_NO_AUTOREUSE'
 elif geomatch and (mainmatch or legalmatch or historymatch or venue):status='PASS_RAW_NAME_AND_GEOGRAPHY_SUPPORTED'
 elif (mainmatch or legalmatch) and not geoconflict and len(full(nativefull))>=5:status='PASS_DISTINCT_FULLNAME_KNOWNCOUNTRY_GEO_UNKNOWN_OR_UNAVAILABLE'
 elif geomatch and any(len(full(re.sub(r'\([^)]*\)','',str(x))))>=3 and full(re.sub(r'\([^)]*\)','',str(x))) in full(re.sub(r'\([^)]*\)','',nativefull)) for x in current if x):status='PASS_CURRENT_FOOTBALLNAME_IN_NATIVE_MAIN_NAME_PLUS_CITY_NO_NICKNAME'
 elif geomatch:status='REVIEW_ONLY_SHORT_ALIAS_WITH_CITY_SUPPORT_NEEDS_FULLNAME'
 else:status='REVIEW_ONLY_ALIAS_NO_INDEPENDENT_GEO_FULLNAME'
 out.append(dict(TMID=p['TMID'],Name=p['Name'],NativeClubUID=uid,IdentityDecision=p['IdentityDecision'],Status=status,SourceCurrentNames=current,SourceLegalHolderName=legal,SourceHistoricalNames=historical,NativeNames=w['Names'],SourceCityFacts=sourcecity,NativeCityFacts=nativecity,SourceVenue=st.get('name'),NativeVenue=nativevenue,GeoMatch=geomatch,GeoMismatch=geoconflict,CurrentFullNameMatches=mainmatch,LegalNameMatches=legalmatch,HistoricalFullNameMatches=historymatch,VenueMatches=venue,SourceRawRef=refs.get(p['TMID']),SourceProfileSHA256=sha(Path(p['ProfileFile'])),NativeCountry=w['TeamCountry'],NativeKind=w['NativeTeamKind'],NativeParentUID=w['ParentUID']))
assert len(out)==223;dump(B/'identity-review/reuse223-raw-geo-audit.json',out);pending=[x for x in out if x['Status'].startswith('REVIEW')];dump(B/'identity-review/reuse223-new-review-exceptions.json',pending);print('REUSE223_BATCH',dict(collections.Counter(x['Status'] for x in out)));print('NEWREVIEW',[(x['TMID'],x['Name'],x['NativeClubUID'],x['Status'],x['SourceCityFacts'],x['NativeCityFacts']) for x in pending])
