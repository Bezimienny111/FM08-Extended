"""ReadProcessMemory-only controlled UID8074 probe. No VM writes, remote calls, hooks, launch or suspension."""
from pathlib import Path
import json,struct,hashlib,ctypes,argparse,datetime,sys,os
B=Path(__file__).resolve().parent
EXPECTED_EXE_SHA='157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d'
PROFILE_VT=0x156a984;PLAYER_VT=0x15ab414;PERSON_VT=0x15ab12c
def readjson(p):return json.loads(p.read_text(encoding='utf-8-sig'))
class Rejected(Exception):pass
def require(v,s):
 if not v:raise Rejected(s)
def u32(m,a):return struct.unpack('<I',m.read(a,4))[0]
def i32(m,a):return struct.unpack('<i',m.read(a,4))[0]
def name(m,a):return m.read(a,128).split(bytes(1))[0].decode('ascii')
def col(m,obj):
 vt=u32(m,obj);loc=u32(m,vt-4);sig,off,cd,td,chd=struct.unpack('<IIIII',m.read(loc,20))
 require(sig==0 and cd==0 and 0x400000<=td<0x2000000 and 0x400000<=chd<0x2000000,'unsupported or untrusted RTTI')
 return dict(vtable=vt,locator=loc,subobject_offset=off,complete=obj-off,type_descriptor=td,hierarchy=chd,name=name(m,td+8))
def resolve_base(m,core,hierarchy,typename):
 sig,attrs,n,bca=struct.unpack('<IIII',m.read(hierarchy,16));require(0<n<=128,'RTTI base count')
 found=[]
 for i in range(n):
  bcd=u32(m,bca+4*i);td,contained,mdisp,pdisp,vdisp,flags=struct.unpack('<IIiiiI',m.read(bcd,24))
  if name(m,td+8)!=typename:continue
  require(-1<=pdisp<=0x1000 and -1<=vdisp<=0x1000 and -0x1000<=mdisp<=0x1000,'RTTI PMD bounds')
  out=core+mdisp
  if pdisp!=-1:
   vbptr=u32(m,core+pdisp);out+=pdisp+i32(m,vbptr+vdisp)
  found.append(dict(address=out,bcd=bcd,mdisp=mdisp,pdisp=pdisp,vdisp=vdisp,flags=flags))
 require(found and len({x['address']for x in found})==1,'missing or ambiguous PERSON virtual base')
 return found[0]
def validate_panel(m,panel,expected,layout):
 require(u32(m,panel)==PROFILE_VT,'profile vtable')
 pr=col(m,panel);require(pr['name']=='.?AVPLAYER_PROFILE_PANEL@@'and pr['complete']==panel,'profile RTTI')
 person=u32(m,panel+0x88);require(person,'no selected PERSON')
 rr=col(m,person);require(rr['name']=='.?AVACTUAL_PLAYER@@','profile does not hold actual player')
 core=rr['complete'];cr=col(m,core);require(cr['name']=='.?AVACTUAL_PLAYER@@'and cr['subobject_offset']==0 and u32(m,core)==PLAYER_VT,'complete PLAYER RTTI')
 db=resolve_base(m,core,cr['hierarchy'],'.?AVDATABASE_RECORD@@');br=resolve_base(m,core,cr['hierarchy'],'.?AVPERSON@@');require(db['address']==person and br['address']==person and u32(m,person)==PERSON_VT,'DATABASE_RECORD/PERSON virtual-base mismatch')
 require(u32(m,u32(m,person)+0x10)==0x1096c90 and m.read(0x1096c90,4)==bytes.fromhex('8b4114c3'),'native UID getter guard');require(u32(m,person+0x14)==8074,'selected UID is not8074')
 # Reproduce the inspected thunk arithmetic without executing it.
 vtordisp=i32(m,person-4);require(-0x2000<=vtordisp<=0x2000,'vtordisp bound')
 canonical=person-vtordisp+0x10c
 # DOB recipe is independently named/disassembled evidence. No search-by-elimination.
 require(layout.get('DOB_semantics_proved')and layout.get('uid_person_offset')==0x14,'DOB layout not proved')
 dob_thunk=u32(m,u32(m,person)+0xc8);dob_code=m.read(dob_thunk,14);require(dob_code[:10]==bytes.fromhex('2b49fc81c10c010000e9')and dob_thunk+14+struct.unpack_from('<i',dob_code,10)[0]==0xc88320 and m.read(0xc88320,7)==bytes.fromhex('8d8138ffffffc3'),'native DOB getter guard');dob_start=canonical+layout['dob_date_canonical_delta']
 require(u32(m,dob_start)==layout['expected_date_vtable'],'DOB DATE vtable');dob_raw=m.read(dob_start+layout['dob_payload_delta'],4);day,year=struct.unpack('<HH',dob_raw)
 require(1900<=year<=2100 and day<(366 if year%4==0 and(year%100!=0 or year%400==0)else 365),'DOB format')
 dob=(datetime.date(year,1,1)+datetime.timedelta(days=day)).isoformat();require(dob=='1974-11-09','selected DOB mismatch')
 block=u32(m,canonical-0x40);require(block,'no personality data block')
 rows=[];vt=u32(m,person)
 for i,c in enumerate(expected):
  slot=int(c['runtime_slot'],16);thunk=u32(m,vt+slot);raw=m.read(thunk,14)
  require(raw[:10]==bytes.fromhex('2b49fc81c10c010000e9'),'personality thunk bytes changed')
  getter=thunk+14+struct.unpack_from('<i',raw,10)[0];off=int(c['runtime_getter_offset'],16)
  guard=bytes.fromhex('8b41c085c074050fbe40')+bytes([off])+bytes.fromhex('c333c0c3')
  require(m.read(getter,len(guard))==guard,'personality getter bytes changed')
  value=struct.unpack('<b',m.read(block+off,1))[0];available=1<=value<=20
  rows.append(dict(Name=c['name'],Slot=slot,Thunk=thunk,Getter=getter,BlockOffset=off,Value=value,Available=available,Expected=c['user_unique_value'],MatchesExpected=available and value==c['user_unique_value']))
 require(u32(m,panel+0x88)==person and u32(m,person+0x14)==8074 and u32(m,canonical-0x40)==block,'profile changed during read')
 require(all(m.read(block+r['BlockOffset'],1)==struct.pack('<b',r['Value'])for r in rows),'traits changed during read')
 return dict(Profile=panel,PERSON=person,PLAYER=core,UID=8074,DOB=dob,RTTI=rr,ProfileDeclaredBase='DATABASE_RECORD',DATABASE_RECORD_BaseRecipe=db,PERSONBaseRecipe=br,Vtordisp=vtordisp,CanonicalGetterThis=canonical,PersonalityBlock=block,Fields=rows,All8Match=all(x['MatchesExpected']for x in rows))
def validate_selected_person(m,person,expected,layout):
 rr=col(m,person);require(rr['name']=='.?AVACTUAL_PLAYER@@','profile does not hold actual player')
 core=rr['complete'];cr=col(m,core);require(cr['name']=='.?AVACTUAL_PLAYER@@'and cr['subobject_offset']==0 and u32(m,core)==PLAYER_VT,'complete PLAYER RTTI')
 db=resolve_base(m,core,cr['hierarchy'],'.?AVDATABASE_RECORD@@');br=resolve_base(m,core,cr['hierarchy'],'.?AVPERSON@@');require(db['address']==person and br['address']==person and u32(m,person)==PERSON_VT,'DATABASE_RECORD/PERSON virtual-base mismatch')
 require(u32(m,u32(m,person)+0x10)==0x1096c90 and m.read(0x1096c90,4)==bytes.fromhex('8b4114c3'),'native UID getter guard');require(u32(m,person+0x14)==8074,'selected UID is not8074')
 # Reproduce the inspected thunk arithmetic without executing it.
 vtordisp=i32(m,person-4);require(-0x2000<=vtordisp<=0x2000,'vtordisp bound')
 canonical=person-vtordisp+0x10c
 # DOB recipe is independently named/disassembled evidence. No search-by-elimination.
 require(layout.get('DOB_semantics_proved')and layout.get('uid_person_offset')==0x14,'DOB layout not proved')
 dob_thunk=u32(m,u32(m,person)+0xc8);dob_code=m.read(dob_thunk,14);require(dob_code[:10]==bytes.fromhex('2b49fc81c10c010000e9')and dob_thunk+14+struct.unpack_from('<i',dob_code,10)[0]==0xc88320 and m.read(0xc88320,7)==bytes.fromhex('8d8138ffffffc3'),'native DOB getter guard');dob_start=canonical+layout['dob_date_canonical_delta']
 require(u32(m,dob_start)==layout['expected_date_vtable'],'DOB DATE vtable');dob_raw=m.read(dob_start+layout['dob_payload_delta'],4);day,year=struct.unpack('<HH',dob_raw)
 require(1900<=year<=2100 and day<(366 if year%4==0 and(year%100!=0 or year%400==0)else 365),'DOB format')
 dob=(datetime.date(year,1,1)+datetime.timedelta(days=day)).isoformat();require(dob=='1974-11-09','selected DOB mismatch')
 block=u32(m,canonical-0x40);require(block,'no personality data block')
 rows=[];vt=u32(m,person)
 for i,c in enumerate(expected):
  slot=int(c['runtime_slot'],16);thunk=u32(m,vt+slot);raw=m.read(thunk,14)
  require(raw[:10]==bytes.fromhex('2b49fc81c10c010000e9'),'personality thunk bytes changed')
  getter=thunk+14+struct.unpack_from('<i',raw,10)[0];off=int(c['runtime_getter_offset'],16)
  guard=bytes.fromhex('8b41c085c074050fbe40')+bytes([off])+bytes.fromhex('c333c0c3')
  require(m.read(getter,len(guard))==guard,'personality getter bytes changed')
  value=struct.unpack('<b',m.read(block+off,1))[0];available=1<=value<=20
  rows.append(dict(Name=c['name'],Slot=slot,Thunk=thunk,Getter=getter,BlockOffset=off,Value=value,Available=available,Expected=c['user_unique_value'],MatchesExpected=available and value==c['user_unique_value']))
 require(u32(m,person+0x14)==8074 and u32(m,canonical-0x40)==block,'profile changed during read')
 require(all(m.read(block+r['BlockOffset'],1)==struct.pack('<b',r['Value'])for r in rows),'traits changed during read')
 return dict(PERSON=person,PLAYER=core,UID=8074,DOB=dob,RTTI=rr,ProfileDeclaredBase='DATABASE_RECORD',DATABASE_RECORD_BaseRecipe=db,PERSONBaseRecipe=br,Vtordisp=vtordisp,CanonicalGetterThis=canonical,PersonalityBlock=block,Fields=rows,All8Match=all(x['MatchesExpected']for x in rows))
class WindowsMemory:
 def __init__(self,pid):
  require(os.name=='nt','Windows required')
  self.k=ctypes.WinDLL('kernel32',use_last_error=True)
  self.k.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32];self.k.OpenProcess.restype=ctypes.c_void_p
  self.k.CloseHandle.argtypes=[ctypes.c_void_p]
  self.k.ReadProcessMemory.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];self.k.ReadProcessMemory.restype=ctypes.c_int
  self.k.VirtualQueryEx.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t];self.k.VirtualQueryEx.restype=ctypes.c_size_t
  self.k.QueryFullProcessImageNameW.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_uint32)]
  self.handle=self.k.OpenProcess(0x410,False,pid);require(self.handle,'OpenProcess READ+QUERY denied')
  p=ctypes.create_unicode_buffer(32768);n=ctypes.c_uint32(len(p))
  require(self.k.QueryFullProcessImageNameW(self.handle,0,p,ctypes.byref(n)),'process image path')
  self.image=p.value;require(hashlib.sha256(Path(self.image).read_bytes()).hexdigest()==EXPECTED_EXE_SHA,'unsupported game binary')
  require(self.read(0x400000,2)==b'MZ','unsupported module base')
 def read(self,a,n):
  require(0x10000<=a and a+n<=0x80000000 and n<=1048576,'memory read bounds')
  buf=ctypes.create_string_buffer(n);got=ctypes.c_size_t()
  require(self.k.ReadProcessMemory(self.handle,ctypes.c_void_p(a),buf,n,ctypes.byref(got))and got.value==n,'unreadable process memory')
  return buf.raw
 def regions(self):
  class MBI(ctypes.Structure):
   _fields_=[('BaseAddress',ctypes.c_void_p),('AllocationBase',ctypes.c_void_p),('AllocationProtect',ctypes.c_uint32),('RegionSize',ctypes.c_size_t),('State',ctypes.c_uint32),('Protect',ctypes.c_uint32),('Type',ctypes.c_uint32)]
  addr=0x10000
  while addr<0x80000000:
   mb=MBI();n=self.k.VirtualQueryEx(self.handle,ctypes.c_void_p(addr),ctypes.byref(mb),ctypes.sizeof(mb))
   if not n:break
   start=int(mb.BaseAddress or 0);size=int(mb.RegionSize);require(size>0,'VirtualQueryEx non-progress')
   if mb.State==0x1000 and mb.Type==0x20000 and mb.Protect&0xff in[2,4,8,0x20,0x40,0x80]and not mb.Protect&0x100:
    yield start,min(size,0x80000000-start)
   addr=start+size
 def close(self):
  if self.handle:self.k.CloseHandle(self.handle);self.handle=None
def scan(m):
 needle=struct.pack('<I',PROFILE_VT);examined=0;candidates=[]
 for start,size in m.regions():
  for offset in range(0,size,1048576-3):
   n=min(1048576,size-offset)
   try:data=m.read(start+offset,n)
   except Rejected:continue
   examined+=len(data);require(examined<=1024**3,'scan byte budget exceeded')
   pos=0
   while True:
    pos=data.find(needle,pos)
    if pos<0:break
    address=start+offset+pos
    if address%4==0:candidates.append(address)
    pos+=1
 return sorted(set(candidates)),examined
def main():
 a=argparse.ArgumentParser();a.add_argument('--pid',type=int);a.add_argument('--control',choices=['TEST_X12']);a.add_argument('--output',default='runtime-X12.json');a.add_argument('--self-test',action='store_true');args=a.parse_args()
 if args.self_test:return selftest()
 require(args.pid and args.control,'explicit PID and controlled source required')
 proof=readjson(B/'unique-trait-proof.json');layout=readjson(B/'runtime-field-layout.json');expected=proof['codec']
 require(proof['status']=='PASS_full8_serialized_semantic_mapping_controlled_SI','offline witness unavailable')
 output=B/args.output;require(output.resolve().parent==B.resolve()and not output.exists(),'new report in own folder required')
 m=WindowsMemory(args.pid);result=dict(status='PENDING',control=args.control,pid=args.pid,image=m.image,access_rights='PROCESS_QUERY_INFORMATION|PROCESS_VM_READ only',remote_execution=False,process_writes=False,game_paused=False)
 try:
  candidates,scanned=scan(m);matches=[];rejects=[]
  for p in candidates:
   try:matches.append(validate_panel(m,p,expected,layout))
   except Rejected as e:rejects.append(dict(panel=p,reason=str(e)))
  result.update(scanned_bytes=scanned,profile_candidates=len(candidates),matches=matches,rejected=rejects);require(len(matches)==1 and len({v['PLAYER']for v in matches})==1,'ambiguous or absent validated UID8074 open profile; no field value used for selection')
  result.update(status='PASS_controlled_runtime8fields'if all(v['All8Match']for v in matches)else'FAIL_trait_mismatch',scanned_bytes=scanned,profile_candidates=len(candidates),matches=matches,rejected=rejects)
 except Exception as e:result.update(status='FAIL_readonly_probe',reason=type(e).__name__+':'+str(e))
 finally:m.close()
 output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,ensure_ascii=True,indent=2))
def selftest():
 import pefile
 pe=pefile.PE(str(B.parents[3]/'fm.exe'));image=pe.get_memory_mapped_image()
 class Fake:
  def __init__(self):self.parts={0x400000:image,0x20000000:bytearray(0x5000)}
  def read(self,a,n):
   for st,data in self.parts.items():
    if st<=a and a+n<=st+len(data):return bytes(data[a-st:a-st+n])
   raise Rejected('unmapped fixture')
  def put(self,a,v):
   for st,data in self.parts.items():
    if isinstance(data,bytearray)and st<=a and a+len(v)<=st+len(data):data[a-st:a-st+len(v)]=v;return
   raise AssertionError('fixture write bounds')
  def word(self,a,v):self.put(a,struct.pack('<I',v))
 m=Fake();core=0x20000000;person=core+0xec;panel=core+0x1000;block=core+0x2000;vb=core+0x3000
 m.word(core,PLAYER_VT);m.word(core+4,vb);m.word(vb+4,0xe8);m.word(person,PERSON_VT);m.put(person-4,struct.pack('<i',-0x414));m.word(person+0x14,8074);m.word(panel,PROFILE_VT);m.word(panel+0x88,person);m.word(core+0xcc,core+0x4000);m.word(core+0x500+0xcc,block)
 layout=readjson(B/'runtime-field-layout.json');canonical=core+0x500+0x10c
 m.word(canonical+layout['dob_date_canonical_delta'],layout['expected_date_vtable']);birth=datetime.date(1974,11,9);m.put(canonical+layout['dob_date_canonical_delta']+layout['dob_payload_delta'],struct.pack('<HH',birth.timetuple().tm_yday-1,birth.year))
 expected=readjson(B/'unique-trait-proof.json')['codec']
 for c in expected:m.put(block+int(c['runtime_getter_offset'],16),struct.pack('<b',c['user_unique_value']))
 require(validate_panel(m,panel,expected,layout)['All8Match'],'fixture expected fields')
 tests=['valid8']
 for label,address,value in [('wrongUID',person+0x14,8075),('wrongPERSON',panel+0x88,core),('nullblock',core+0x500+0xcc,0)]:
  old=m.read(address,4);m.word(address,value)
  try:validate_panel(m,panel,expected,layout);raise AssertionError(label+' accepted')
  except Rejected:tests.append(label)
  finally:m.put(address,old)
 old=m.read(block+0x23,1);m.put(block+0x23,b'\x00')
 try:
  result=validate_panel(m,panel,expected,layout);require(not result['Fields'][-1]['Available']and not result['All8Match'],'zero field must remain missing after identity selected');tests.append('zeroisMissing_notIdentitySelection')
 finally:m.put(block+0x23,old)
 # Different valid value must remain a mismatch, never silently clamped or reported success.
 m.put(block+0x23,b'\x14');require(not validate_panel(m,panel,expected,layout)['All8Match'],'wrong value')
 tests.append('validValueMismatch')
 out=dict(status='PASS',tests=tests,synthetic_memory_only=True,active_process_opened=False)
 (B/'probe-selftest.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
if __name__=='__main__':main()
