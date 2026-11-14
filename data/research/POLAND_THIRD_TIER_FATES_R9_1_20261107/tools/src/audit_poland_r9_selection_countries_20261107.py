from pathlib import Path
from collections import Counter,defaultdict
import csv,json,struct,sys,zlib,hashlib
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
from compare_native_player_tests import controlled_club_record_candidate
import pol3_comp_schema_r8_20261107 as comp
OUT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_FATES_R9_20261107'
DB=OUT/'user-data/db/TEST_POL_3_LEVEL_R9'
DEST=OUT/'diagnostics-selection';DEST.mkdir(exist_ok=True)
server=zlib.decompress((DB/'server_db.dat').read_bytes()[9:]);people=zlib.decompress((DB/'people_db.dat').read_bytes()[9:]);pc=struct.unpack_from('<i',people)[0];del people
with (OUT/'native-after-clubs.csv').open(encoding='utf-8-sig',newline='') as f:clubs={int(x['ClubIndex']):x for x in csv.DictReader(f)}
with (ROOT/'FmLauncher/data/research/POLAND_II_LIGA_CLUB_AUDIT_20261107/club-family-identity-map.csv').open(encoding='utf-8-sig',newline='') as f:families={int(x['ClubIndex']):x for x in csv.DictReader(f) if x['Database']=='802'}
by_family=defaultdict(list)
for x in families.values():by_family[int(x['NameOffset'])].append(x)
all_uids={int(x['ClubUID']) for x in clubs.values()};rows=[]
def known_club_span(data,index,uid,person_count):
 candidates=set();needle=struct.pack('<ii',index,uid);footer=data.find(needle)
 while footer>=0:
  if footer+8<len(data) and data[footer+8]==10:
   lower=max(0,footer-1048576)
   previous=data.rfind(struct.pack('<i',index-1),lower,max(0,footer-70))
   while previous>=0:
    candidate=controlled_club_record_candidate(data,previous+8,person_count)
    if candidate and candidate[0]==index and candidate[2]==footer+8:
     candidates.add(candidate[1:]);break
    previous=data.rfind(struct.pack('<i',index-1),lower,previous)
  footer=data.find(needle,footer+1)
 assert len(candidates)==1,(index,uid,candidates)
 return next(iter(candidates))
for idx,c in clubs.items():
 if int(c['CurrentDivisionIndex']) not in (139,140,141,1332):continue
 start,end=known_club_span(server,idx,int(c['ClubUID']),pc);assert struct.unpack_from('<ii',server,end-8)==(idx,int(c['ClubUID']))
 reference=struct.unpack_from('<i',server,end-22)[0]
 family=families[idx];marker=int(family['NameOffset']);assert server[marker:marker+7]==bytes.fromhex('FF00006C070000')
 primary=next(x for x in by_family[marker] if int(x['FamilyPosition'])==0)
 footer_needle=struct.pack('<ii',reference,int(primary['ClubUID']))
 footers=[];at=marker
 while True:
  at=server.find(footer_needle,at,min(len(server),marker+16000))
  if at<0:break
  if server[at+8]==0:footers.append(at)
  at+=1
 assert len(footers)==1,(idx,reference,footers)
 previous=[];at=max(0,marker-16000);needle=struct.pack('<i',reference-1)
 while True:
  at=server.find(needle,at,marker)
  if at<0:break
  if struct.unpack_from('<i',server,at+4)[0] in all_uids and server[at+8]==0:previous.append(at)
  at+=1
 assert len(previous)==1,(idx,reference,previous)
 base=previous[0]+8;assert server[base]==0 and base<marker<footers[0]
 country=struct.unpack_from('<i',server,base+1)[0]
 rows.append(dict(ClubIndex=idx,ClubUID=int(c['ClubUID']),ClubName=family['FamilyName'],FamilyPosition=int(family['FamilyPosition']),CurrentDivisionIndex=int(c['CurrentDivisionIndex']),CountryIndex=country,BaseStart=base,CountryOffset=base+1,FamilyReference=reference,NameMarker=marker,NameTreeFooter=footers[0],NativeRecordStart=start,NativeRecordEnd=end))
with (DEST/'club-countries.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
client=zlib.decompress((DB/'client_db.dat').read_bytes()[9:]);ct=comp.find_client_comp_table(client,1333);st=comp.find_server_comp_table(server,ct)
comps=[dict(uid=x['uid'],index=x['index'],level=x['raw'][19],country_index=struct.unpack_from('<i',x['raw'],24)[0]) for x in st['records'] if x['uid'] in (129558,129559,129560,1800001000)]
report=dict(clubs_audited=len(rows),country_counts={str(i):dict(Counter(x['CountryIndex'] for x in rows if x['CurrentDivisionIndex']==i)) for i in (139,140,141,1332)},non_polish_country=[x for x in rows if x['CountryIndex']!=161],competitions=comps,database_modified=False)
(DEST/'country-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='non_polish_country'}|{'missing_country_count':len(report['non_polish_country'])},ensure_ascii=True),flush=True)
