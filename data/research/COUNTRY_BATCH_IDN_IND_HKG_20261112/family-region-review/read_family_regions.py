from pathlib import Path
import sys,json,struct,hashlib,importlib.util
from collections import Counter
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
from create_italy_structure_i1_20261108 import load,languages,lang_sections,find_table,club,city
from audit_poland_v25_common_r1_20261108 import Cursor
B=Path(__file__).resolve().parents[1];O=Path(__file__).resolve().parent;S=B/'input/X16-after-SI'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sp=importlib.util.spec_from_file_location('fm07',ROOT/'reference/OpenFM2007/tools/fm07db.py');fm=importlib.util.module_from_spec(sp);sp.loader.exec_module(fm)
class FM08Codec(fm.Codec):
 def colours(self,o,k):
  # FM08 D1B4C0 serializes FIVE RGB555 colours and one byte; FM07 has THREE.
  return self.struct(o,k,lambda c,x:([c.u16(x,'c'+str(i)) for i in range(5)],c.u8(x,'f')))
def unique(span,pat):
 p=span.find(pat);assert p>=0 and p==span.rfind(pat),('nonunique_family_boundary',pat.hex());return p

def inspect(a,c,f,cl,beg,span):
 fi=f['index'];assert fi>0;prev=cl[fi-1];st=beg+unique(span,struct.pack('<iI',fi-1,prev['uid']))+8;end=beg+unique(span,struct.pack('<iI',fi,f['uid']))+8
 cu=Cursor(a,st);assert cu.byte()==0;country=cu.integer();cu.byte();cu.string();cu.byte();cu.string();cu.take(2);cu.num('<H');cu.integer()
 assert a[st:cu.p]==c[f['start']:f['start']+cu.p-st] and country==f['country_index']
 cu.take(1+12+1+2+4+1+1)
 for _ in range(2):cu.take(cu.byte()*4)
 kind=cu.byte();assert kind in [0,2],('unsupported_finance',kind)
 if kind==0:cu.take(45)
 cu.take(cu.num('<H')*4)
 for _ in range(cu.num('<H')):
  tag=cu.byte();assert tag==9,('unsupported_club_info',tag);cu.take(12)
  for z in range(4):cu.string()
 cu.take(36)
 # C80270: shortdate + int. C5F6A0: shortdate + byte.
 cu.take(cu.num('<H')*8);cu.take(cu.byte()*5)
 # C5F8A0/C5F930: byte + two shortdates + byte + STRING + int + short.
 for _ in range(cu.byte()):cu.take(10);cu.string();cu.take(6)
 at=cu.p;n=cu.byte();assert 0<=n<128;entries=[{'Category':cu.byte(),'CompetitionUID':cu.integer()} for _ in range(n)];regionend=cu.p
 # This source scope has no UEFA/knowledge payload. Fail closed if that changes.
 assert cu.byte()==0,'unsupported_UEFA_payload';assert cu.byte()==0,'unsupported_knowledge_payload'
 cu.take(2+4+12+4+2+1+4+1)
 codec=FM08Codec(a);codec.p=cu.p;team={};fm.team_container(codec,team,True)
 assert codec.p==end,('family_suffix_end_mismatch',codec.p,end)
 assert team['id']==fi and team['uid']==f['uid'] and team['name']==f['embedded_full_name'] and team['short_name']==f['embedded_short_name']
 return dict(ClubUID=f['uid'],FamilyIndex=fi,Name=f['embedded_full_name'],CountryIndex=country,FamilyStart=st,FamilyEnd=end,FamilySHA256=hashlib.sha256(a[st:end]).hexdigest(),CountOffset=at,Count=n,Entries=entries,EntrySpanEnd=regionend,OriginalSpanHex=a[at:regionend].hex(),Proof='forward_typed_prefix+supported_counted_sections+FM08_5colour_suffix_exact_same_family_footer_UID_index_names')

def main():
 before={k:H(S/k) for k in ['server_db.dat','client_db.dat','lang_db.dat']};a=load(S,'server_db.dat');c=load(S,'client_db.dat');en,_=lang_sections(dict(languages((S/'lang_db.dat').read_bytes()))[8]);cl,_,_=find_table(c,[v['uid'] for v in en['club']],club);_,_,co=find_table(a,[v['uid'] for v in en['city']],city);beg=co+4;last=min(r['Start'] for r in json.loads((B/'native-structure.json').read_text())['records']);span=a[beg:last]
 rows=[];bad=[]
 for f in cl:
  if f['country_index']!=58:continue
  try:rows.append(inspect(a,c,f,cl,beg,span))
  except Exception as e:bad.append(dict(ClubUID=f['uid'],FamilyIndex=f['index'],Error=repr(e)))
 assert before=={k:H(S/k) for k in before}
 dp=ROOT/'FmLauncher/data/research/GHIDRA_ENGINE_20261107_R5/decompiled/functions'
 funcs=['ram_c65c10.c','ram_c6c940.c','ram_c5fa40.c','ram_c5fa80.c','ram_c60630.c','ram_d0f5b0.c','ram_d0d850.c','ram_d0d780.c','ram_cfd9b0.c','ram_c80270.c','ram_c5f8a0.c','ram_c5f930.c','ram_c6f8c0.c','ram_d1b4c0.c','ram_c6efe0.c','ram_ce93c0.c']
 report=dict(Status='PASS_SOURCE_READ_ONLY' if not bad else 'PARTIAL_UNSUPPORTED_RECORDS',Source=str(S),SourceHashes=before,NativeDBWrites=False,Rows=rows,Unsupported=bad,Parsed=len(rows),TotalIndonesianFamilies=sum(f['country_index']==58 for f in cl),Nonempty=sum(r['Count']>0 for r in rows),EntryCount=sum(r['Count'] for r in rows),DiskFormat='count:u8; repeated {category:u8,COMP_UID:s32LE}; no runtime padding. Runtime+1A8 list/+1B0 count are NOT physical disk offsets.',Serializer='C65C10:294-308 and C5FA40; readerC6C940:615-638 andC5FA80',SameCategoryGuard='C60630 exits without insertion if any saved entry category equals competition vfunc+124, so nonempty conflicting entries require typed reconciliation.',NoMutationIfEmpty='If all relevant source FAMILY list counts are zero, do not create a new FAMILY writer. Raw TEAM Current child seeds correct region during C34A40; explicitly read back empty list before loader.',Pins=[dict(Path=str(dp/f),SHA256=H(dp/f)) for f in funcs],ParserPath=str(Path(__file__).resolve()),ParserSHA256=H(Path(__file__)))
 (O/'source-readback.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(report['Status'],'parsed',len(rows),'unsupported',len(bad),'nonempty',report['Nonempty']);print(bad[:6]);assert not bad
if __name__=='__main__':main()
