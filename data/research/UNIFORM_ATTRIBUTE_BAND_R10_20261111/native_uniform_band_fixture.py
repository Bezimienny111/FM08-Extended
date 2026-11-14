"""Private native FM08 rectangle render proof. Never resumes main thread; no attach, no disk EXE/DB write."""
from pathlib import Path
import ctypes as C, ctypes.wintypes as W, struct, hashlib, json, time
R=Path(__file__).resolve().parent
EXE=Path(r'J:\FM08dev\fm.exe')
assert hashlib.sha256(EXE.read_bytes()).hexdigest()=='157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d'
K=C.WinDLL('kernel32',use_last_error=True)
class STARTUP(C.Structure):
 _fields_=[('cb',W.DWORD),('lpReserved',W.LPWSTR),('lpDesktop',W.LPWSTR),('lpTitle',W.LPWSTR),('dwX',W.DWORD),('dwY',W.DWORD),('dwXSize',W.DWORD),('dwYSize',W.DWORD),('dwXCountChars',W.DWORD),('dwYCountChars',W.DWORD),('dwFillAttribute',W.DWORD),('dwFlags',W.DWORD),('wShowWindow',W.WORD),('cbReserved2',W.WORD),('lpReserved2',C.c_void_p),('hStdInput',W.HANDLE),('hStdOutput',W.HANDLE),('hStdError',W.HANDLE)]
class PROCESS(C.Structure):
 _fields_=[('hProcess',W.HANDLE),('hThread',W.HANDLE),('dwProcessId',W.DWORD),('dwThreadId',W.DWORD)]
K.CreateProcessW.argtypes=[W.LPCWSTR,W.LPWSTR,C.c_void_p,C.c_void_p,W.BOOL,W.DWORD,C.c_void_p,W.LPCWSTR,C.POINTER(STARTUP),C.POINTER(PROCESS)];K.CreateProcessW.restype=W.BOOL
K.VirtualAllocEx.argtypes=[W.HANDLE,C.c_void_p,C.c_size_t,W.DWORD,W.DWORD];K.VirtualAllocEx.restype=C.c_void_p
K.WriteProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)];K.WriteProcessMemory.restype=W.BOOL
K.ReadProcessMemory.argtypes=K.WriteProcessMemory.argtypes;K.ReadProcessMemory.restype=W.BOOL
K.FlushInstructionCache.argtypes=[W.HANDLE,C.c_void_p,C.c_size_t];K.FlushInstructionCache.restype=W.BOOL
K.CreateRemoteThread.argtypes=[W.HANDLE,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,W.DWORD,C.POINTER(W.DWORD)];K.CreateRemoteThread.restype=W.HANDLE
K.WaitForSingleObject.argtypes=[W.HANDLE,W.DWORD];K.WaitForSingleObject.restype=W.DWORD
K.GetExitCodeThread.argtypes=[W.HANDLE,C.POINTER(W.DWORD)];K.GetExitCodeThread.restype=W.BOOL
K.TerminateProcess.argtypes=[W.HANDLE,W.UINT];K.TerminateProcess.restype=W.BOOL
K.CloseHandle.argtypes=[W.HANDLE];K.CloseHandle.restype=W.BOOL

import base64, pefile
def ck(ok):
 if not ok:raise C.WinError(C.get_last_error())
P=json.loads((R/'position-payload.json').read_text());classes=base64.b64decode(P['Classes'])
p=PROCESS();si=STARTUP();si.cb=C.sizeof(si);si.dwFlags=1;si.wShowWindow=0
res={'status':'STARTED','source_sha256':hashlib.sha256(EXE.read_bytes()).hexdigest(),'never_resumed_main_thread':True,'user_process_touched':False,'cases':[],'boundary_doubles':['controlled actual STANDARD_COLUMN_LABEL layouts for name/value, ready native BOX margins; actual renderer/getters retained','glyph tail observerFC7D5A then nativeFONTcleanup, no full OS fontmanager/UI','native glyph tail observes colour/font after original copy then uses nativecleanup; fullGUI/rasterizer remains separate'],'real_native':['IMAGE constructorF7EA50 and vtable16701E4','FillRectF94D30, clippingF928C0, surfaceF7ECE0 and original SIMD blending','SetRole native table invalidationF61160 in non-visible headless widget state','actual STANDARD_COLUMN_LABEL vtable and FC2440/48FDD0/FC3D80/10140D0/10144A0/10157C0 appearance renderer','actual native textboundsFC21D0 and FC2080 textcomponent dispatch','actual FC7D00 componentDraw, FONTcopyFBC080, localFONT hook, native ref/SEH cleanup']}
pack=lambda n:struct.pack('<I',n&0xFFFFFFFF)
try:
 ck(K.CreateProcessW(str(EXE),C.create_unicode_buffer('"'+str(EXE)+'"'),None,None,False,4,None,str(EXE.parent),C.byref(si),C.byref(p)))
 res['private_pid']=p.dwProcessId
 mem=K.VirtualAllocEx(p.hProcess,C.c_void_p(0x12000000),0x50000,0x3000,0x40);assert mem==0x12000000
 def write(a,b):
  n=C.c_size_t();v=C.create_string_buffer(bytes(b));ck(K.WriteProcessMemory(p.hProcess,C.c_void_p(a),v,len(b),C.byref(n)));assert n.value==len(b)
 def read(a,n):
  buf=C.create_string_buffer(n);got=C.c_size_t();ck(K.ReadProcessMemory(p.hProcess,C.c_void_p(a),buf,n,C.byref(got)));assert got.value==n;return buf.raw
 def rd(a):return struct.unpack('<I',read(a,4))[0]
 K.VirtualProtectEx.argtypes=[W.HANDLE,C.c_void_p,C.c_size_t,W.DWORD,C.POINTER(W.DWORD)];K.VirtualProtectEx.restype=W.BOOL
 def patch(a,b):
  old=W.DWORD();ck(K.VirtualProtectEx(p.hProcess,C.c_void_p(a),len(b),0x40,C.byref(old)))
  write(a,b);tmp=W.DWORD();ck(K.VirtualProtectEx(p.hProcess,C.c_void_p(a),len(b),old.value,C.byref(tmp)))
  ck(K.FlushInstructionCache(p.hProcess,C.c_void_p(a),len(b)))
 def call(a,self=0,args=(),edx=0):
  stub=b''.join(b'\x68'+pack(x) for x in reversed(args))+b'\xB9'+pack(self)+b'\xBA'+pack(edx)+b'\xB8'+pack(a)+b'\xFF\xD0\xA3'+pack(0x1200F100)+b'\x33\xC0\xC2\x04\x00'
  write(0x1200F000,stub);ck(K.FlushInstructionCache(p.hProcess,C.c_void_p(0x1200F000),len(stub)))
  tid=W.DWORD();t=K.CreateRemoteThread(p.hProcess,None,0,C.c_void_p(0x1200F000),None,0,C.byref(tid));ck(t)
  try:
   assert K.WaitForSingleObject(t,10000)==0,'private native thread timeout'
   ec=W.DWORD();ck(K.GetExitCodeThread(t,C.byref(ec)));assert ec.value==0,(hex(a),hex(ec.value))
   return rd(0x1200F100)
  finally:K.CloseHandle(t)
 def require(ok,name):
  assert ok,name
  res['cases'].append({'name':name,'PASS':True})
 state=P['State'];profile=0x12001000;otherprofile=0x12001400;table=0x12002000;table2=0x12002400;label=0x12003000;numeric=0x12003400;surface=0x12004000;pixels=0x12010000;factory=0x1200A100
 write(0x12020000,(R/'position-code.bin').read_bytes());write(state,(R/'position-data.bin').read_bytes())
 write(profile,pack(0x156A984));write(otherprofile,pack(0x156A984))
 write(profile+0x98,pack(table));write(profile+0x9C,pack(table2))
 for t in [table,table2]:write(t,pack(0x166F4A4))
 for l in [label,numeric]:
  write(l,pack(0x150C5E4));write(l+4,pack(table));write(l+0x34,struct.pack('<hhhh',2 if l==label else 32,2,28 if l==label else 12,7));write(l+0x28,pack(4))
  # Real COMPOSITE_BUTTON appearance resolver uses embedded appearance+98/cache+4.
  box=0x12006000+(0 if l==label else 0x400);write(box+0x204,b'\1');write(l+0x9C,pack(box))
  for style in [0x10,0x70,0xD0,0x130,0x190]:write(box+style+0x50,pack(0x12006B00))
  # Real text component object, no substituted native getter/vtable.
  component=l+0xA8;write(component,pack(0x1677284));write(component+0x20,pack(0x140));write(component+0x38,pack(0x12006900));write(component+0x3E,struct.pack('<hh',28 if l==label else 12,7));write(component+0x46,b'\0')
 call(0xF7EA50,surface);w=48;h=20;baseline=0xFF202020
 write(surface+8,struct.pack('<hhhhhh',0,0,w,h,0,0));write(surface+0x14,pack(pixels));write(surface+0x18,struct.pack('<hhh',w,h,w))
 def blank():write(pixels,pack(baseline)*(w*h))
 def begin(pr=profile):call(P['BeginGenerationEntry'],pr)
 def register(attr,row=5,la=label,ta=table,pr=profile):call(P['RegisterEntry'],args=(pr,ta,la,attr,row))
 def role(r,pr=profile):call(P['SetRoleEntry'],pr,(r,))
 def render(la=label):return call(P['RenderEntry'],la,edx=surface)

 # Independent palette oracle: original native FillRect, literal approved colours/alphas.
 oracle_rect=0x12006D00;write(oracle_rect,struct.pack('<hhhh',2,2,42,10));palette={0:baseline}
 for emphasis,colour,alpha in [(1,0xFFB79D52,38),(2,0xFF4B8A66,88)]:
  blank();call(0xF94D30,surface,(oracle_rect,colour,alpha));palette[emphasis]=rd(pixels+(3*w+3)*4)
 res['native_palette_oracle']={'method':'original F94D30 called directly, no module palette selection','baseline':hex(baseline),'important':{'input_colour':'FFB79D52','alpha':38,'output_RGBA':hex(palette[1])},'key':{'input_colour':'FF4B8A66','alpha':88,'output_RGBA':hex(palette[2])}}
 assert palette[1]!=palette[2] and palette[1]!=baseline and palette[2]!=baseline
 arrow=0x12003800;write(arrow,pack(0x16701E4));write(arrow+4,pack(table));write(arrow+0x34,struct.pack('<hhhh',45,2,3,7))
 def reg_value(attr,row=5,pr=profile,la=numeric):call(P['RegisterValueEntry'],args=(pr,table,la,attr,row))
 def register_pair(a):begin();register(a);reg_value(a)
 register_pair(13);role(10);blank();require(render()==2 and call(P['RenderEntry'],numeric,edx=surface)==2,'name and native value underlay registered independently')
 require(rd(state+16)==2 and rd(state+64+24)==0 and rd(state+64+28+24)==1,'explicit column-kind and28Bstride recorded')
 require(call(P['RenderEntry'],label,edx=0)==2 and call(P['RenderEntry'],numeric,edx=0)==0,'numeric font classification OFF while name key stays bold')
 # Capacity covers every one of47native attributes twice, including goalkeeper roles.
 begin()
 for a in range(47):register(a,a);reg_value(a,a)
 require(rd(state+16)==94 and rd(state+20)==0,'47nativeenums name+value fit below96capacity')
 register(13);reg_value(13);require(rd(state+16)==96,'capacity96 exact boundary accepted')
 register(13);require(rd(state+16)==0 and rd(state+20)==1 and rd(state+12)==0,'entry97 overflow fails OFF without corrupting weights')
 register_pair(13);role(10);call(P['InvalidateLabelEntry'],label);blank()
 require(render()==0 and call(P['RenderEntry'],numeric,edx=surface)==2,'name destruction invalidates name, value class remains recognized without stale paired geometry')
 call(P['InvalidateLabelEntry'],numeric);blank();require(call(P['RenderEntry'],numeric,edx=surface)==0,'value destruction invalidates second28Bentry')
 begin(otherprofile);register(13);reg_value(13);require(rd(state+16)==0,'both cellkinds reject previous profile generation')
 register_pair(13);role(0);blank();require(render()==0 and call(P['RenderEntry'],numeric,edx=surface)==0,'OFF clears both kinds')
 register_pair(13);reg_value(13,la=arrow);require(rd(state+16)==2,'native arrow PICTURE class is not accepted as number')
 # Real measured shape: nameRECT encloses numberRECT, which has native insets.
 write(label+0x34,struct.pack('<hhhh',2,2,42,10));write(numeric+0x34,struct.pack('<hhhh',32,5,12,4))
 write(label+0xA8+0x3E,struct.pack('<hh',42,10));write(numeric+0xA8+0x3E,struct.pack('<hh',12,4))
 # Actual renderer with each cells own BOX before its underlay, retaining native component/font paths.
 for adr,key,original in [(0xFC251F,'LabelDrawEntry',bytes.fromhex('8a8608010000')),(0xFC7D48,'FontCopyEntry',bytes.fromhex('8a464584c0'))]:
  require(read(adr,len(original))==original,'original renderer bytes '+hex(adr));patch(adr,b'\xE9'+pack(P[key]-(adr+5))+b'\x90'*(len(original)-5))
 write(label+0xD4,pack(0xFF445566));write(numeric+0xD4,pack(0xFF123456))
 # Controlled native SI_WSTRING value17, not a player value or a replacement getter.
 value_ref=0x12006940;value_chars=0x12006980
 write(numeric+0xAC,pack(0x166A398)+pack(0x166A38C)+pack(value_ref));write(value_ref,struct.pack('<HHHHIII',2,1,2,3,value_chars,0,0));write(value_chars,'17'.encode('utf-16le')+b'\0\0')
 value_bytes=read(numeric+0xAC,12)+read(value_ref,20)+read(value_chars,6)
 tail=0x1200E000;obs_name=0x1200B000;obs_value=0x1200B040;pixname=pixels+(3*w+3)*4;pixvalue=pixels+(6*w+33)*4
 # Preserve actual native copy/colour override then observe localFONT atS+2C before glyph rasterization.
 z=bytearray(b'\xBF'+pack(obs_name)+b'\xBA'+pack(pixname)+b'\x81\xFE'+pack(numeric+0xA8)+b'\x75\x0A\xBF'+pack(obs_value)+b'\xBA'+pack(pixvalue))
 z+=b'\x8B\x44\x24\x34\x89\x07\x8B\x44\x24\x3C\x89\x47\x04\x8B\x44\x24\x48\x89\x47\x08\x8B\x02\x89\x47\x0C\xC7\x02'+pack(0xFF010203)
 z+=b'\xE9'+pack(0xFC7EC1-(tail+len(z)+5));write(tail,z);patch(0xFC7D5A,b'\xE9'+pack(tail-(0xFC7D5A+5))+b'\x90')
 tested=0
 source_name=read(label,0x110);source_value=read(numeric,0x110)
 for r in range(1,12):
  for a in range(47):
   for order in [(label,numeric),(numeric,label)]:
    register_pair(a);role(r);blank()
    for widget in order:call(0xFC2440,widget,(surface,))
    kind=classes[r*47+a]
    assert rd(obs_name+4)==(0x142 if kind==2 else 0x140),(r,a,'namefont')
    assert rd(obs_value+4)==0x140 and rd(obs_value+8)==0xFF123456,(r,a,'numericfont/colour')
    assert rd(obs_name+8)==0xFF445566
    pp=struct.unpack('<'+'I'*(w*h),read(pixels,w*h*4));changed=[i for i,v in enumerate(pp) if v!=baseline]
    assert len(changed)==(420 if kind else 2),(r,a,order,len(changed),kind)
    samples=[pp[yy*w+xx] for yy in range(2,12) for xx in range(2,44) if (yy,xx) not in [(3,3),(6,33)]]
    assert len(set(samples))==1,(r,a,order,'nonuniform RGBA or double alpha badge')
    assert set(samples)=={palette[kind]},(r,a,order,kind,hex(samples[0]),hex(palette[kind]),'wrong exact native palette/alpha')
    assert all(2<=i//w<12 and 2<=i%w<44 for i in changed),(r,a,'painted arrow/history/outside row band')
    assert read(numeric,0x110)==source_value and read(label,0x110)==source_name,(r,a,'source widget/font/rect mutated')
    assert read(numeric+0xAC,12)+read(value_ref,20)+read(value_chars,6)==value_bytes,(r,a,'native value17 changed')
   tested+=1
 require(tested==517,'actual ownBOX/name+value all11roles x47enums BOTHdraworders, single uniform finalRGBA across entire row and split, source immutable')
 role(0);blank();call(0xFC2440,label,(surface,));call(0xFC2440,numeric,(surface,))
 require(rd(obs_name+12)==baseline and rd(obs_value+12)==baseline and rd(obs_name+4)==0x140 and rd(obs_value+4)==0x140,'singleOFF restores both native backgrounds/fonts')
 # Numbers with a real cached font must retain original cache; key name may bypass its LOCAL copy only.
 ref=0x12005000;vt=0x12005100;release=0x12005200;write(release,b'\xC3');write(vt,pack(release)+pack(release));write(ref,pack(vt)+pack(2));write(numeric+0xC0,pack(ref))
 register_pair(13);role(10);blank();sourcefont=read(numeric+0xB8,32);call(0xFC2440,numeric,(surface,))
 require(rd(obs_value)==ref and rd(ref+4)==2 and read(numeric+0xB8,32)==sourcefont,'numeric original font-cache reference balanced and never bypassed even for key attribute')
 write(numeric+0xC0,pack(0))
 # No numeric badge when its name partner has died, even though registryCount remains positive.
 register_pair(13);role(10);call(P['InvalidateLabelEntry'],label);blank();beforefills=rd(state+28);call(0xFC2440,numeric,(surface,))
 require(rd(obs_value+12)==baseline and rd(state+28)==beforefills,'missing name -> numeric failclosed no badge despite Count2')
 # Original name-only behavior is safe; its own native rect already covers the row.
 register_pair(13);role(10);call(P['InvalidateLabelEntry'],numeric);blank();call(0xFC2440,label,(surface,));call(0xFC2440,numeric,(surface,))
 pp=struct.unpack('<'+'I'*(w*h),read(pixels,w*h*4));samples=[pp[y*w+x] for y in range(2,12) for x in range(2,44) if (y,x) not in [(3,3),(6,33)]]
 require(set(samples)=={palette[2]},'missing numeric -> original natural NAME-only full native rect without second blend')
 for off,bad,name in [(4,table2,'table'),(8,14,'enum'),(12,0xDEAD,'generation'),(16,6,'native row'),(20,otherprofile,'profile')]:
  register_pair(13);role(10);write(state+64+off,pack(bad));blank();beforefills=rd(state+28);call(0xFC2440,numeric,(surface,))
  require(rd(obs_value+12)==baseline and rd(state+28)==beforefills,'partner '+name+' mismatch fails closed')
 register_pair(13);role(10);write(label+4,pack(table2));blank();call(0xFC2440,numeric,(surface,));require(rd(obs_value+12)==baseline,'partner actual parentTABLE mismatch fails closed');write(label+4,pack(table))
 # Different widths/insets and a gap come from native geometry; no padding constants are used.
 for nr,vr in [((2,2,42,10),(30,4,12,6)),((2,2,28,10),(32,3,12,8)),((2,2,42,10),(32,2,12,10))]:
  write(label+0x34,struct.pack('<hhhh',*nr));write(numeric+0x34,struct.pack('<hhhh',*vr));write(label+0xE6,struct.pack('<hh',nr[2],nr[3]));write(numeric+0xE6,struct.pack('<hh',vr[2],vr[3]))
  for order in [(label,numeric),(numeric,label)]:
   register_pair(13);role(10);blank()
   for widget in order:call(0xFC2440,widget,(surface,))
   pp=struct.unpack('<'+'I'*(w*h),read(pixels,w*h*4));right=max(nr[0]+nr[2],vr[0]+vr[2]);samples=[pp[y*w+x] for y in range(nr[1],nr[1]+nr[3]) for x in range(nr[0],right) if (y,x) not in [(3,3),(6,33)]]
   assert set(samples)=={palette[2]},(nr,vr,order,'uniform exact key palette varied geometry')
 require(True,'native right-inset/gap/zero-inset variants both draworders uniform, no hardcoded padding')
 res['draw_order_variants']=2;res['actual_cell_draws']=2068
 res['role_attribute_combinations']=tested;res['status']='PASS';res['full_real_profile_UI_tested']=False
except BaseException as error:
 res['status']='FAIL';res['error']={'type':type(error).__name__,'message':str(error)}
 raise
finally:
 if p.hProcess:
  res['termination_requested']=bool(K.TerminateProcess(p.hProcess,0));res['private_process_cleanup_confirmed']=K.WaitForSingleObject(p.hProcess,3000)==0;K.CloseHandle(p.hThread);K.CloseHandle(p.hProcess)
 (R/'native-fixture-results.json').write_text(json.dumps(res,indent=2),encoding='utf-8')
print(json.dumps({'status':res['status'],'cases':len(res['cases']),'role_attribute_combinations':res.get('role_attribute_combinations'),'private_pid':res.get('private_pid'),'terminated':res.get('private_process_cleanup_confirmed')}))
