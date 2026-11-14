from pathlib import Path
import sys,json,struct,re,unicodedata,hashlib,difflib
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8');sys.path.insert(0,'FM08-Database-Tools/scratch')
from create_italy_structure_i1_20261108 import load,languages,lang_sections,find_table
from audit_poland_v25_common_r1_20261108 import stadium,city
B=Path(__file__).resolve().parents[1];S=B.parent;O=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def canon(s):return ''.join(re.findall('[a-z0-9]+',unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower()))
def tokens(s):return re.findall('[a-z0-9]+',unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().lower())
STOP=set('gnk hnk nk pfc ofc ofk clube club clubde de da do e y desportivo deportivo sportivo esporte futebol football fbc fc fk sc sk ac cd cf ec aa afc associacao asociacion sociedade sociedad esportivo esportiva deportiva desportiva nogometni klub slezsky ser'.split())
def sig(s):return ''.join(t for t in tokens(s)if t not in STOP and len(t)>1)
plans=read(B/'club-plan-draft.json');world=read(B/'native-world-identities.json');src=B/'input/X19-after-SI';en,_=lang_sections(dict(languages((src/'lang_db.dat').read_bytes()))[8]);a=load(src,'server_db.dat');c=load(src,'client_db.dat');stad,_,_=find_table(a,[x['uid'] for x in en['stadium']],lambda r:stadium(r,62));cities,_,_=find_table(c,[x['uid'] for x in en['city']],city);sl={x['uid']:x['names']for x in en['stadium']};cl={x['uid']:x['names']for x in en['city']};venues={}
for w in world:
 st=w['StadiumIndex'];v={}
 if st>=0:
  q=stad[st];ci=struct.unpack_from('<i',q['raw'],46)[0];v=dict(Names=sl.get(q['uid'],[]),City=cl.get(cities[ci]['uid'],[])if ci>=0 else[],StadiumUID=q['uid'])
 venues[w['ClubUID']]=v
raw={};refs={}
for ref in read(S/'raw-source-index.json'):
 if '/clubs?'not in ref['url']and not re.search(r'/club/\d+$',ref['url']):continue
 d=json.loads(read(S/ref['raw_file'])['body']).get('data')or[]
 for v in d if isinstance(d,list)else[d]:
  t=str(v.get('id',''))
  if t and ref.get('fetched_at','')>=refs.get(t,{}).get('fetched_at',''):raw[t]=v;refs[t]=ref
pending={x['TMID']for x in read(B/'identity-review/reuse223-new-review-exceptions.json')};out=[]
for p in plans:
 if p['NativeClubUID']and p['TMID']not in pending and p['TMID']!='978':continue
 pf=read(Path(p['ProfileFile']));bs=raw.get(p['TMID'],{}).get('baseDetails')or{};loc=(bs.get('superiorClub')or{}).get('location')or{};st=pf.get('stadium')or{};labels=[p['Name'],pf.get('official_name'),pf.get('short_name')]+[x.get('name')for x in pf.get('historical_names',[])];labels=[s for s in labels if s];scities=[s for s in[loc.get('city'),pf.get('address_line_2'),st.get('address_line_2')]if s];hits=[]
 for w in world:
  if w['ParentUID']or w['TeamCountry']not in[p['NativeCountryIndex'],-1]:continue
  v=venues[w['ClubUID']];ncity=[canon(re.sub(r'\([^)]*\)','',n))for n in v.get('City',[])if n];geo=any(n and n in canon(t)for n in ncity for t in scities);venue=any(canon(st.get('name'))==canon(z)for z in v.get('Names',[])if st.get('name'))
  sgs={sig(s)for s in labels};ngs={sig(s)for s in w['Names']};exact=bool(sgs&ngs-{''});overlap=max([difflib.SequenceMatcher(None,s,n).ratio()for s in sgs for n in ngs]+[0]);hint=any(min(len(s),len(n))>=4 and(s in n or n in s)for s in sgs for n in ngs)
  if exact or venue or(geo and overlap>=.42)or hint:
   hits.append(dict(UID=w['ClubUID'],Names=w['Names'],Country=w['TeamCountry'],Kind=w['NativeTeamKind'],Founded=w['YearFounded'],CurrentDivision=w['CurrentDivision'],NativeVenue=v,GeoMatch=geo,ExactExpandedFootballName=exact,ExactVenue=venue,Similarity=round(overlap,3)))
 hits.sort(key=lambda h:(not h['ExactVenue'],not h['GeoMatch'],not h['ExactExpandedFootballName'],-h['Similarity']))
 out.append(dict(TMID=p['TMID'],Name=p['Name'],DraftUID=p['NativeClubUID'],SourceLabels=labels,SourceCities=scities,SourceVenue=st.get('name'),SourceRaw=refs.get(p['TMID']),SourceProfileSHA256=hashlib.sha256(Path(p['ProfileFile']).read_bytes()).hexdigest(),Candidates=hits[:9]))
(O/'remaining-alias-venue-review.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for x in out:
 if x['Candidates']:print(x['TMID'],x['Name'],'=>',[(h['UID'],h['Names'][0],h['GeoMatch'],h['ExactExpandedFootballName'],h['ExactVenue'],h['NativeVenue'].get('City'),h['NativeVenue'].get('Names'))for h in x['Candidates'][:4]])
print('REMAINING_REVIEW',len(out),'venuecatalog',len(venues))
