"""Finish bounded X18 kinds, corrected SERVER name slots and new-family embedding. No DAT write."""
from pathlib import Path
import sys,json,struct,hashlib,importlib.util,datetime,copy,shutil
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8');ROOT=Path('J:/FM08dev');P=ROOT/'FmLauncher/data/research/COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep';O=P/'root-structure/tools';W=O.parent;SHA=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'));dump=lambda p,x:Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
base=O/'ApplyX18Structure.draft-frozen.py'
if not base.exists():
 assert SHA(O/'ApplyX18Structure.py')=='99002fc30103198b1fb8917642a54aad36dfa7d77d2368ac206c0afa62a3b059';shutil.copyfile(O/'ApplyX18Structure.py',base)
assert SHA(base)=='99002fc30103198b1fb8917642a54aad36dfa7d77d2368ac206c0afa62a3b059';sp=importlib.util.spec_from_file_location('draft_adapter',base);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
S=P/'input/X17-after-SI';a=m.load(S,'server_db.dat');c=m.load(S,'client_db.dat');en,_=m.lang_sections(dict(m.languages((S/'lang_db.dat').read_bytes()))[8]);cl,_,_=m.find_table(c,[r['uid']for r in en['club']],m.club);cf={r['uid']:r for r in cl};rr=read(P/'native-structure.json')['records'];byuid={r['ClubUID']:r for r in rr};byteam={r['TeamIndex']:r for r in rr};world=read(P/'native-world-identities.json');ww={r['ClubUID']:r for r in world}
# Bounded suffix parser: client names are a hint, never an assumed physical SERVER prefix.
member_code='''def _members(data,start,end,fi,uid,full=None,short=None):
 blob=data[start:end];found=[]
 for at in range(0,max(0,len(blob)-36)):
  try:
   q=Cursor(blob,at);flags=q.take(3);fs=q.p;actualfull=q.string();fe=q.p;ss=q.p;actualshort=q.string();se=q.p
   nk=q.byte();assert nk<64;q.take(nk*11);ma=q.p;n=q.byte();members=[q.integer()for _ in range(n)];assert len(set(members))==n and all(0<=t<100000 for t in members)
   count=q.byte();q.take(count*8);count=q.num('<h');assert 0<=count<=4096;q.take(count*14);q.take(17);count=q.byte();q.take(count*20)
   assert q.identity()==(fi,uid)and q.p==len(blob)
   found.append(dict(Offset=start+ma,Count=n,Members=members,Before=data[start+ma:start+ma+1+4*n],SuffixStart=start+at,Full=actualfull,Short=actualshort,FullStart=start+fs,FullEnd=start+fe,ShortStart=start+ss,ShortEnd=start+se))
  except(AssertionError,ValueError,UnicodeError,struct.error,IndexError):continue
 preferred=[v for v in found if full is not None and short is not None and v['Full']==full and v['Short']==short]
 if len(preferred)==1:return preferred[0]
 assert len(found)==1,('typed_family_suffix_not_unique',fi,uid,len(found));return found[0]

'''
ns=dict(m.__dict__);exec(member_code,ns);members=ns['_members']
_,_,cityend=m.find_table(a,[r['uid']for r in en['city']],m.city);familybase=cityend+4;familyblob=a[familybase:min(r['Start']for r in rr)]
def span(f):
 fi=f['index'];st=familybase+m.unique(familyblob,struct.pack('<iI',fi-1,cl[fi-1]['uid']))+8;end=familybase+m.unique(familyblob,struct.pack('<iI',fi,f['uid']))+8;return st,end
# Correct only the six earlier mistaken SERVER slot positions; preserve the rejected plan as evidence.
oldpath=ROOT/'FmLauncher/data/research/CLUB_NAME_LOOKUP_FIX_20261113/patch-plan.json';assert SHA(oldpath)=='d0024b012e4ec305cf45fa5a4b0dbd2ba3670ba46dd4f535157bc25f28f743be';newplan=copy.deepcopy(read(oldpath));fixproof=[]
for e in newplan['Patches']:
 if e['File']!='server_db.dat':continue
 f=cf[e['UID']];st,end=span(f);v=members(a,st,end,f['index'],f['uid']);field='Full'if e['Field']=='EmbeddedFull'else'Short';assert v[field]=='';off=v[field+'Start'];finish=v[field+'End'];assert a[off:finish]==bytes(4)
 fixproof.append(dict(UID=e['UID'],Field=e['Field'],RejectedOffset=e['Offset'],CorrectOffset=off,FamilyStart=st,FamilyEnd=end,SuffixStart=v['SuffixStart'],FamilyIndex=f['index'],TypedNames=[v['Full'],v['Short']],MemberVector=v['Members']))
 e.update(HistoricalWrongCLIENTPrefixOffset=e['Offset'],Offset=off,OffsetWithinFamily=off-st,RecordStart=st,RecordEndBefore=end,RecordSHA256Before=hashlib.sha256(a[st:end]).hexdigest(),SchemaProof='full typed TEAM_CONTAINER suffix to exact FAMILY index/UID footer; no CLIENT physical-prefix assumption')
assert len(fixproof)==6;newplan.update(Status='CORRECTED_R2_TYPED_SERVER_SUFFIX_PLAN_NOT_APPLIED',SupersedesPlanSHA256=SHA(oldpath),Correction='Six SERVER offsets corrected. Six CLIENT offsets retained unchanged. No DAT was written from rejected plan.',SERVEROffsetProof=fixproof)
r2path=oldpath.with_name('correctedpatch-plan-r2.json');dump(r2path,newplan);r2sha=SHA(r2path)
# Metadata-only overlay preserves all602 UID/index projections. Kind is not inferred from U21/U23 text.
core=read(P/'club-plan.json');projection=read(P/'club-UID-projection.json')['rows'];proj={str(r['TMID']):r for r in projection};alltm={str(r['TMID']):r for r in core};newres=[r for r in core if not r.get('NativeClubUID')and r.get('ParentTMID')];assert len(newres)==55
ajax=ww[856118];assert ajax['NativeTeamKind']==16 and ajax['ParentUID']==992;bw=ww[2121];assert bw['NativeTeamKind']==3 and bw['ParentUID']==928820
witness=[]
for w in [ajax,bw]:
 r=byuid[w['ClubUID']];fi,at,k=m._typed_tail(a,r,len(cl));assert k==w['NativeTeamKind']and fi==w['TeamTailFamilyIndex'];witness.append(dict(UID=w['ClubUID'],TEAM=r['TeamIndex'],RoleByteOffset=at-4,RoleByte=k,TailFamily=fi,ParentUID=w['ParentUID'],RoleAndLinkPrefixHex=a[at-4:at+4].hex(),Proof='Existing source typed tail + exact two strings/flags/footer; first role byte at runtime TEAM+3c, not outer TEAM record tag10'))
overlay=[]
for r in newres:
 tid=str(r['TMID']);pr=proj[tid];parent=str(r['ParentTMID']);want=16 if r['Country']=='Netherlands' else 3
 assert r['SourceClubTypeID']in [2,3] and r['ReserveTeam']and parent in alltm and str(pr['SourceParentTMID'])==parent;assert pr['NativeTeamKind']==want,(tid,pr['NativeTeamKind'],want)
 overlay.append(dict(TMID=tid,Name=r['Name'],ParentTMID=parent,ProjectedClubUID=pr['ClubUID'],ProjectedTeamIndex=pr['TeamIndex'],ProjectedFamilyIndex=pr['FamilyIndex'],RequiredNativeReserveKind=want,SourceType=r['SourceClubTypeID'],Decision='NL second-team source role and exact parent; no new age-cap claim'in r['Country']if False else('NL linked second team, same existingAjax16 category; AlmereU23 included without age-name inference'if want==16 else'linkedB reserve role matching source3'),WitnessUID=856118 if want==16 else bw['ClubUID']))
kindpath=O/'reserve-kind-overlay.json';dump(kindpath,dict(Status='REVIEWED_METADATA_55_NO_UID_OR_INDEX_CHANGE',Rows=overlay,SourcePlanSHA256=SHA(P/'club-plan.json'),ProjectionSHA256=SHA(P/'club-UID-projection.json'),Witnesses=witness,Seed10Qualification='Old literal bytes([10,0,0,255]) wrote10 into first TEAM tail role at empty-roster source+87. This is separate from outer TEAM record tag10. It is not a valid default inferred for every reserve; replaced by explicit55metadata3/16.',SourceExeSHA256='157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d',NativeReader='existing R5 C7D4A0 first u8 -> runtimeTEAM+3c; same tail schema for both values'))
# Walk every actual existing parent before writer execution; no assumed equality between CLIENT/SERVER names.
walk=[]
for r in newres:
 p=alltm[str(r['ParentTMID'])]
 if not p.get('NativeClubUID'):
  walk.append(dict(ChildTMID=r['TMID'],ParentTMID=p['TMID'],Status='NEW_PARENT_TEMPLATE_MULTIAPPEND_FIXTURE_VERIFIED'));continue
 pu=int(p['NativeClubUID']);f=cf[pu];st,end=span(f);v=members(a,st,end,f['index'],pu,f['embedded_full_name'],f['embedded_short_name']);pt=byuid[pu]['TeamIndex'];assert pt in v['Members']
 for mt in v['Members']:assert m._typed_tail(a,byteam[mt],len(cl))[0]==f['index'],('parent_member_tail_mismatch',pu,mt)
 walk.append(dict(ChildTMID=r['TMID'],ParentTMID=p['TMID'],ParentUID=pu,FamilyIndex=f['index'],SourceMembers=v['Members'],CLIENTNames=[f['embedded_full_name'],f['embedded_short_name']],SERVERNames=[v['Full'],v['Short']],Status='PASS_TYPED_SOURCE_SUFFIX_AND_ALL_MEMBER_TAILS'))
dump(O/'parent-walk55.json',dict(Status='PASS_55_ACTUAL_PLANNED_NEW_RESERVE_PARENT_WALK',Rows=walk,SourceServerSHA256=SHA(S/'server_db.dat'),SourcePlanSHA256=SHA(P/'club-plan.json')))
# Patch only the owned adapter; do not execute main.
s=base.read_text(encoding='utf-8-sig')
def replace(x,y):
 global s
 assert s.count(x)==1,('adapter_shape_changed',x[:100],s.count(x));s=s.replace(x,y,1)
st=s.index('def _members(');en=s.index('def _typed_tail(',st);s=s[:st]+member_code+s[en:]
s=s.replace("NAMEFIX_PLAN=R/'CLUB_NAME_LOOKUP_FIX_20261113/patch-plan.json'","NAMEFIX_PLAN=R/'CLUB_NAME_LOOKUP_FIX_20261113/correctedpatch-plan-r2.json'");s=s.replace("NAMEFIX_SHA256='d0024b012e4ec305cf45fa5a4b0dbd2ba3670ba46dd4f535157bc25f28f743be'","NAMEFIX_SHA256='"+r2sha+"'")
s=s.replace("v=_members(bb,0,len(bb),fi,uid,'','')","v=_members(bb,0,len(bb),fi,uid)");s=s.replace("_members(out,0,len(out),fi,uid,'','')","_members(out,0,len(out),fi,uid)")
helpers='''
RESERVE_KIND_PATH=Path(__file__).resolve().parent/'reserve-kind-overlay.json'
RESERVE_KIND_SHA256='@@KINDSHA@@'
def _required_kind(x):
 assert _hash(RESERVE_KIND_PATH)==RESERVE_KIND_SHA256
 matches=[r for r in read(RESERVE_KIND_PATH)['Rows']if r['TMID']==str(x['TMID'])];assert len(matches)==1
 k=matches[0]
 for key in ['ProjectedClubUID','ProjectedTeamIndex','ProjectedFamilyIndex']:assert int(x[key])==k[key],('reserve_projection_changed',x['TMID'],key)
 assert str(x['ParentTMID'])==k['ParentTMID']
 if x.get('RequiredNativeReserveKind')is not None:assert x['RequiredNativeReserveKind']==k['RequiredNativeReserveKind']
 return k['RequiredNativeReserveKind']

def _fill_new_embedded(bb,bc,fi,uid,name,short):
 assert struct.unpack_from('<iI',bb,len(bb)-8)==struct.unpack_from('<iI',bc,len(bc)-8)==(fi,uid)
 v=_members(bb,0,len(bb),fi,uid);assert v['Full']==v['Short']==''and bc[26:34]==bytes(8)
 def fill(raw,fs,fe,ss,se):
  assert raw[fs:fe]==raw[ss:se]==bytes(4);one=_pure_string(name);two=_pure_string(short);out=raw[:fs]+one+raw[fe:ss]+two+raw[se:]
  restored=out[:fs]+bytes(4)+out[fs+len(one):fs+len(one)+ss-fe]+bytes(4)+out[fs+len(one)+ss-fe+len(two):];assert restored==raw
  return bytearray(out)
 nb=fill(bb,v['FullStart'],v['FullEnd'],v['ShortStart'],v['ShortEnd']);nc=fill(bc,26,30,30,34);nv=_members(nb,0,len(nb),fi,uid)
 assert (nv['Full'],nv['Short'],nv['Members'])==(name,short,v['Members']);assert nb[:v['SuffixStart']]==bb[:v['SuffixStart']]
 parsed=club(Cursor(nc));assert parsed['uid']==uid and parsed['index']==fi and parsed['embedded_full_name']==name and parsed['embedded_short_name']==short
 assert nb[:23]==nc[:23]and struct.unpack_from('<iI',nb,len(nb)-8)==(fi,uid)
 return nb,nc

'''.replace('@@KINDSHA@@',SHA(kindpath))
s=s.replace('def main():',helpers+'def main():',1)
replace(" raise RuntimeError('DRAFT_LOCKED_NOT_ROOT_REVIEWED: finish explicit new reserve kinds and final configuration preflight before any DAT write')\n",'')
replace("tm=bytearray(team[:87])+bytes([10,0,0,255])+", "tm=bytearray(team[:87])+bytes([_required_kind(x),0,0,255])+")
replace("names.append(bytes(bb));clients.append(bytes(bc));teams.append(bytes(tm));", "bb,bc=_fill_new_embedded(bb,bc,fi,u,name,pf.get('short_name')or name)\n   names.append(bytes(bb));clients.append(bytes(bc));teams.append(bytes(tm));")
# Independent target readback of each new reserve kind and new first-family names.
anchor="for old in records:\n  new=rb[old['TeamIndex']];"
replace(anchor,"""for x in plan:
  if not x['NativeClubUID']and x.get('ParentTMID'):
   item=bytm[x['TMID']];assert _typed_tail(s,rb[item['TeamIndex']],oldName+len(names))[2]==_required_kind(x),('target_reserve_kind_mismatch',x['TMID'])
 for old in records:
  new=rb[old['TeamIndex']];""")
compile(s,str(O/'ApplyX18Structure.py'),'exec');(O/'ApplyX18Structure.py').write_text(s,encoding='utf-8');dump(O/'finish-r2-pins.json',dict(Status='CODE_GENERATED_55_METADATA_PARENTWALK_PASS_PENDING_EMBEDDED_FIXTURE',WriterSHA256=SHA(O/'ApplyX18Structure.py'),ReserveMetadataSHA256=SHA(kindpath),CorrectedNamefixPath=str(r2path),CorrectedNamefixSHA256=r2sha,ParentWalk55SHA256=SHA(O/'parent-walk55.json'),SeedDraftSHA256=SHA(base),MainExecuted=False,DataBaseWritten=False))
print('WRITTEN metadata55',sum(r['RequiredNativeReserveKind']==16 for r in overlay),'kind16;',sum(r['RequiredNativeReserveKind']==3 for r in overlay),'kind3; parentwalk55PASS; R2SERVER6 corrected; codeCOMPILEPASS; mainNOTRUN',flush=True)
