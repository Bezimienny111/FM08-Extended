"""Independent Italy disk checks layered on the existing whole-file inverse."""
from pathlib import Path
from datetime import date,datetime,timezone
import sys,json,csv,struct,hashlib,unicodedata,re
sys.dont_write_bytecode=True
sys.path.insert(0,'J:/FM08dev/FM08-Database-Tools/scratch')
from verify_poland_full_n7_20261108 import verify,load
from verify_poland_squads_n4_20261108 import names
ROOT=Path('J:/FM08dev')
B=ROOT/'FmLauncher/data/research/COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# SHA256 case differs between existing independent helper and Python manifest; bytes remain exact.
import verify_poland_full_n7_20261108 as inverse_helper
original_pins=inverse_helper.pins
inverse_helper.pins=lambda folder:{k:v.lower()for k,v in original_pins(folder).items()}
def main():
 prepared=B/sys.argv[1];r=read(prepared/'full-native.json');m=read(prepared/'manifest.json')
 verify(prepared,prepared/'inverse-verification.json')
 report=read(prepared/'inverse-verification.json');q=load(Path(r['output']),'people_db.dat');s=load(Path(r['output']),'server_db.dat')
 profiles=rows(prepared/'native_players.csv');identities=rows(prepared/'identities.csv');by={int(i['SubjectID']):(p,i) for p,i in zip(profiles,identities)}
 nations={x['Nation']:int(x['NationIndex']) for x in rows(B/'audit/nations.csv')};families={int(k):v for k,v in r['contracting_family'].items()}
 attrs=dict(PosGK=1,PosSW=2,PosDL=13,PosDC=14,PosDR=15,PosDM=16,PosML=17,PosMC=18,PosMR=19,PosAML=20,PosAMC=21,PosAMR=22,PosST=23,PosWBL=24,PosWBR=25,LeftFoot=51,RightFoot=52,Crossing=26,Dribbling=27,Finishing=28,Heading=29,LongShots=30,Marking=31,Movement=32,Passing=33,Penalties=34,Tackling=35,FirstTouch=49,Technique=50,FreeKicks=62,Acceleration=61,Agility=73,Balance=69,Jumping=66,Pace=65,Stamina=64,Strength=63,Aggression=72,Anticipation=44,Bravery=70,Composure=79,Concentration=80,Decisions=45,Flair=53,Leadership=67,Positioning=47,Teamwork=55,WorkRate=56,Reflexes=48,Handling=37,Kicking=41,AerialAbility=38,OneOnOnes=46,Determination=78)
 traits=['Adaptability','Ambition','Loyalty','Pressure','Professionalism','Sportsmanship','Temperament','Controversy']
 nt=[names(s,x['start'],x['end']) for x in r['name_after']];seen=set();newcount=0
 # Common-name table follows the two mutable first/surname tables; parse exact counted records.
 common_start=r['name_after'][1]['end'];common_end=common_start+4;common_count=struct.unpack_from('<i',s,common_start)[0]
 assert 0<common_count<1000000
 for common_index in range(common_count):
  assert s[common_end]==0;common_length=struct.unpack_from('<I',s,common_end+1)[0];assert common_length<1000
  common_end+=22+common_length*2;assert struct.unpack_from('<i',s,common_end-8)[0]==common_index
 nt.append(names(s,common_start,common_end))
 sentinel_proofs=[];provenance={int(v['subject_id']):v for v in read(prepared/'provenance.json')}
 after={x['Uid']:x for x in r['actor_after']};before={x['Uid']:x for x in r['actor_before']};audit={int(x['ID']):x for x in rows(B/'audit/players.csv')};oldpeople=load(Path(r['source']),'people_db.dat')
 for x in r['subjects']:
  assert x['uid'] not in seen;seen.add(x['uid']);p,i=by[x['id90']];st=x['start'];pi=x['person'];cp=x['payload'];assert struct.unpack_from('<ii',q,x['end']-8)==(pi,x['uid'])
  assert struct.unpack_from('<i',q,x['owner_offset'])[0]==int(i['OwnerClubIndex'])==x['owner']
  assert struct.unpack_from('<i',q,cp+26)[0]==pi and struct.unpack_from('<i',q,cp+31)[0]==families[x['owner']]
  # Existing SI PERSON prefixes have variable length; names precede the DOB year.
  yearoff=after[x['uid']]['Dob'] if x['uid'] in after else st+145
  lastname=p['LastName'];common=audit.get(x['uid'],{}).get('CommonName','')
  if common and lastname.endswith(' ('+common+')'):lastname=lastname[:-(len(common)+3)]
  def name_block(buf,start,year):
   marker=bytes.fromhex('6c07ffffffff');found=[]
   for j in range(start,min(year,start+520)):
    if buf[j:j+6]!=marker:continue
    n=struct.unpack_from('<i',buf,j+18)[0]
    if not 0<=n<=45:continue
    if j+26+2*n+(2 if n else 0)!=year:continue
    inline=buf[j+22:j+22+2*n].decode('utf-16-le')if n else''
    if n:assert buf[j+22+2*n:j+24+2*n]==bytes(2)
    found.append((j,inline))
   assert len(found)==1,('Unique native name block/DOB boundary',x['uid'],found)
   return found[0]
  name_at,inline=name_block(q,st,yearoff)
  if inline:
   assert inline==p['FirstName']+' '+lastname and p['FirstName']==x['first'],('Inline full-name override differs',x['uid'],inline)
  else:
   fi,li,ci=struct.unpack_from('<iii',q,name_at+6)
   if fi<0 or li<0:
    assert x['uid']in before and fi>=-1 and li>=-1 and ci>=0,('Unsupported NAME sentinel',x['uid'],fi,li,ci)
    assert fi<len(nt[0])and li<len(nt[1])and ci<len(nt[2])
    physical_first=nt[0][fi]['text']if fi>=0 else'';physical_last=nt[1][li]['text']if li>=0 else'';physical_knownas=nt[2][ci]['text']
    source_name=provenance[x['id90']]['name']
    def normname(v):return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',v).encode('ascii','ignore').decode().lower())
    assert physical_knownas==common and normname(source_name)==normname(physical_knownas),('Sentinel identity source/knownas mismatch',x['uid'],source_name,physical_knownas)
    assert audit[x['uid']]['FirstName']==p['FirstName']and audit[x['uid']]['LastName']==p['LastName'],'Logical reader fallback changed'
    oldyear=before[x['uid']]['Dob'];old_at,old_inline=name_block(oldpeople,before[x['uid']]['Start'],oldyear)
    assert struct.unpack_from('<iii',oldpeople,old_at+6)==(fi,li,ci) and q[name_at:yearoff-2]==oldpeople[old_at:oldyear-2]
    sentinel_proofs.append(dict(UID=x['uid'],SubjectID=x['id90'],TMID=provenance[x['id90']]['TMID'],SourceName=source_name,SourceDOB=provenance[x['id90']]['source_dob'],NativeDOB=i['TargetDOB'],FirstNameIndex=fi,LastNameIndex=li,CommonNameIndex=ci,PhysicalFirstName=physical_first,PhysicalLastName=physical_last,PhysicalKnownAs=physical_knownas,NameBlockUnchanged=True,SourceNameBlockHex=oldpeople[old_at:oldyear-2].hex(),AfterNameBlockHex=q[name_at:yearoff-2].hex(),ReaderFallbackFirstName=p['FirstName'],ReaderFallbackLastName=p['LastName']))
   else:
    assert nt[0][fi]['text']==p['FirstName']==x['first']and nt[1][li]['text']==lastname,('Native name references differ',x['uid'],fi,li)
  if x['uid'] in before:
   oldyear=before[x['uid']]['Dob'];old_at,old_inline=name_block(oldpeople,before[x['uid']]['Start'],oldyear);assert q[name_at:yearoff-2]==oldpeople[old_at:oldyear-2]and inline==old_inline,('Existing native name references/inline override changed',x['uid'])
  assert struct.unpack_from('<i',q,yearoff+5)[0]==nations[p['Nationality']],('Raw nationality differs',x['uid'])
  if pi<r['original_count']:continue
  newcount+=1;assert x['end']-st==299 and cp==st+199 and x['owner_offset']==st+171
  d=date.fromisoformat(p['BirthDate']);assert struct.unpack_from('<HH',q,st+143)==(d.timetuple().tm_yday-1,d.year)
  assert struct.unpack_from('<i',q,st+150)[0]==nations[p['Nationality']]
  ai=struct.unpack_from('<i',q,st+15)[0];at=r['new_attributes_start']+ai*89;assert q[at]==0 and struct.unpack_from('<i',q,at+81)[0]==ai
  for key,off in attrs.items():assert q[at+off]==int(p[key]),(x['uid'],key,q[at+off],p[key])
  pers=struct.unpack_from('<i',q,st+181)[0];pt=r['new_personality_header']+4+pers*17;assert q[pt]==0 and struct.unpack_from('<i',q,pt+9)[0]==pers
  for off,key in enumerate(traits,1):assert q[pt+off]==int(p[key]),(x['uid'],key)
  assert struct.unpack_from('<i',q,cp+35)[0]==int(p['WeeklyWage']) and struct.unpack_from('<HH',q,cp+39)==(180,2010)
 assert newcount==r['added']
 # Every old future transfer stays byte-identical by whole SERVER inverse; no stale move may involve a changed subject.
 future=rows(B/'future-audit/all_future_transfers.csv');affected={x['Uid'] for x in r['actor_before']};conflicts=[x for x in future if x['UID'] and int(x['UID']) in affected]
 assert not conflicts,('Stale future transfers affect imported/released subjects',conflicts)
 report.update(new_profiles_raw_attributes_personality_names_DOB_nation_contracts_verified=newcount,all_subject_contract_family_and_identity_verified=len(seen),unrelated_future_transfers_preserved=len(future),future_transfer_conflicts=0,source_gaps=read(B/'prepared/source-gaps.json'),recorded_at=datetime.now(timezone.utc).isoformat())
 report['sentinel_name_source_after_proofs']=sentinel_proofs
 dump(prepared/'sentinel-name-source-after.json',dict(Status='PASS_TYPED_SOURCE_AFTER_SENTINEL_NAMES',Rows=sentinel_proofs,NewProfilesStillRequireExactLiteralNames=True,NoPERSONDataChanged=True,ReaderFallbackBacklog='ReadPlayers heuristic scans unrelated ints when firstname index=-1; do not treat fabricated fallback label as actualpersonidentity'))
 dump(prepared/'independent-verification.json',report)
 print('PASS: X7 independent disk/inverse; subjects=%d new=%d future_conflicts=0'%(len(seen),newcount))
if __name__=='__main__':main()
