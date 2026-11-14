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
res={'status':'STARTED','source_sha256':hashlib.sha256(EXE.read_bytes()).hexdigest(),'never_resumed_main_thread':True,'user_process_touched':False,'cases':[],'boundary_doubles':['controlled STANDARD_COLUMN_LABEL object layout from actual72cell snapshot; actual factory and native getters are NOT replaced','glyph layout tail atFC7D5A is an instrumentation observer, then actual native font cleanupFC7EC1; no OS fontmanager or full GUI claimed','empty already-ready native BOX resource state, real appearance resolve and draw retained'],'real_native':['IMAGE constructorF7EA50 and vtable16701E4','FillRectF94D30, clippingF928C0, surfaceF7ECE0 and original SIMD blending','SetRole native table invalidationF61160 in non-visible headless widget state','actual STANDARD_COLUMN_LABEL vtable and FC2440/48FDD0/FC3D80/10140D0/10144A0/10157C0 appearance renderer','actual native textboundsFC21D0 and FC2080 textcomponent dispatch','actual FC7D00 componentDraw, FONTcopyFBC080, localFONT hook, native ref/SEH cleanup']}
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

 # Replay only real native constructor assignments, not a full GUI constructor.
 ctor=0x1200C400;pe=pefile.PE(data=EXE.read_bytes());off=pe.get_offset_from_rva(0x9AF7C1-pe.OPTIONAL_HEADER.ImageBase)
 instructions=EXE.read_bytes()[off:off+42]
 write(ctor,b'\x56\xBE'+pack(profile)+b'\xB8'+pack(0xFFFFFFFF)+instructions+b'\x5E\xC3');call(ctor)
 require(all(rd(profile+x)==0xFFFFFFFF for x in range(0x90,0xAC,4)),'actual native constructor assigns lazy cachesFFFFFFFF')
 begin();beforector=read(profile,0xAC)
 for r in [10,0,1,2,3,4,5,6,7,8,9,10,11,0]:
  role(r);assert rd(state+12)==r
 require(rd(state+16)==0 and read(profile,0xAC)==beforector,'R3 Count0 sentinel regression, role changes andOFF no dereference/mutation')
 write(profile+0x98,pack(table));write(profile+0x9C,pack(table2))
 begin();register(13);role(10);blank();require(render()==2,'FS Finishing key, native fill')
 require(rd(state+16)==1 and rd(state+32)==13,'Register enum and generation retained')
 require(all(rd(pixels+(yy*w+xx)*4)==baseline for yy in range(h) for xx in range(32,w)),'numeric column bytes unchanged')
 # All eleven roles x all47native enums, shuffled arbitrary row values. No translated text input.
 tested=0
 for r in range(1,12):
  for a in range(47):
   begin();register(a,(a*13)%47);role(r);blank();got=render();expect=classes[r*47+a]
   assert got==expect,(r,a,got,expect)
   changed=[i for i,v in enumerate(struct.unpack('<'+'I'*(w*h),read(pixels,w*h*4))) if v!=baseline]
   assert len(changed)==(28*7 if expect else 0),(r,a,len(changed),expect)
   assert all(i%w<32 for i in changed)
   tested+=1
 require(tested==517,'11 roles x47 native enums, arbitrary sorted-row positions, exact changed region')
 begin();register(13);role(10);blank();render();role(0);blank();require(render()==0 and read(pixels,w*h*4)==pack(baseline)*(w*h),'OFF leaves background fully native after repaint')
 role(999);require(rd(state+12)==0,'invalid role fails OFF')
 role(10);register(13,pr=otherprofile);require(rd(state+16)==1,'foreign stale profile registration rejected')
 begin(otherprofile);register(13,pr=profile);require(rd(state+16)==0,'profile switch clears generation and stale label registry')
 begin();register(4);role(1);blank();require(render()==2,'GK Handling key by native enum')
 role(10);blank();require(render()==0,'position switch GK toFS same label becomes ordinary')
 begin();register(13);role(10);call(P['InvalidateLabelEntry'],label);blank();require(render()==0,'LABEL destruction invalidates pointer before reuse')
 begin();register(13);role(10);write(label+4,pack(table2));blank();require(render()==0,'parentTABLE change rejects registry');write(label+4,pack(table))
 begin();register(-1);register(47);register(13,-1);require(rd(state+16)==0,'negative/special enum and invalid row rejected')
 begin();write(state,pack(0));register(13);role(10);blank();require(render()==0 and rd(state+16)==0,'launch optionOFF registers/renders nothing');write(state,pack(1))
 begin()
 for n in range(65):register(13,n)
 require(rd(state+16)==0 and rd(state+20)==1 and rd(state+12)==0,'capacity overflow fails closed until next generation')

 begin();register(13);role(10);write(state+64+4,pack(0xFFFFFFFF));role(0)
 require(rd(state+12)==0,'R3 explicit -1 registryTABLE repaint guard')
 begin();register(13);role(10);call(P['InvalidateLabelEntry'],label);write(profile+0x98,pack(0xFFFFFFFF));write(profile+0x9C,pack(0xFFFFFFFF));role(0)
 require(rd(state+12)==0,'R3 deadLABEL plus retained lazy caches never repaint')
 write(profile+0x98,pack(table));write(profile+0x9C,pack(table2))
 # Actual snapshot class regression: old exact LABEL guard rejects this real class.
 old=json.loads((R.parent/'implementation-r3/position-payload.json').read_text())
 write(0x12020000,(R.parent/'implementation-r3/position-code.bin').read_bytes());write(state,(R.parent/'implementation-r3/position-data.bin').read_bytes())
 call(old['BeginGenerationEntry'],profile);call(old['RegisterEntry'],args=(profile,table,label,13,5))
 require(rd(state+16)==0,'historical R3 rejects actual STANDARD_COLUMN_LABEL regression reproduced')
 write(0x12020000,(R/'position-code.bin').read_bytes());write(state,(R/'position-data.bin').read_bytes())
 begin();register(13);require(rd(state+16)==1,'R4 exact actual STANDARD_COLUMN_LABEL accepted')
 begin();write(label,pack(0x1675554));register(13);require(rd(state+16)==0,'unrelated LABEL exact type rejected');write(label,pack(0x150C5E4))

 # Hook actual complete COMPOSITE_BUTTON renderer, leaving all native getters intact.
 for a,key,original in [(0xFC251F,'LabelDrawEntry',bytes.fromhex('8a8608010000')),(0xFC7D48,'FontCopyEntry',bytes.fromhex('8a464584c0'))]:
  require(read(a,len(original))==original,'original native bytes at'+hex(a))
  patch(a,b'\xE9'+pack(P[key]-(a+5))+b'\x90'*(len(original)-5))
 # Observe already copied font immediately after native cleanup-state init and before glyph layout.
 # All actual type dispatch, appearance rendering, text bounds, component lookup, font copy and
 # native release/SEH cleanup execute unchanged. Only full font manager/glyph rasterization is excluded.
 tail=0x1200E000;pix=pixels+(3*w+3)*4
 text=bytearray(b'\x8B\x44\x24\x34\xA3'+pack(0x1200B040)+b'\x8B\x44\x24\x3C\xA3'+pack(0x1200B044))
 text+=b'\x89\x35'+pack(0x1200B04C) # actual ESI textcomponent witness
 text+=b'\xA1'+pack(pix)+b'\xA3'+pack(0x1200B048)+b'\xC7\x05'+pack(pix)+pack(0xFF010203)
 text+=b'\xE9'+pack(0xFC7EC1-(tail+len(text)+5));write(tail,text)
 patch(0xFC7D5A,b'\xE9'+pack(tail-(0xFC7D5A+5))+b'\x90')
 require(call(0x48FDD0,label)==0x12006000,'actual COLUMN appearance getter resolves real BOX cache')
 call(0xFC21D0,label,(0x12006A00,))
 require(read(0x12006A00,8)==read(label+0x34,8),'actual native textbounds from emptyBOX retained')
 for r,a,kind in [(10,13,2),(3,14,2),(1,4,2),(4,11,1),(1,13,0),(0,13,0)]:
  begin();register(a);role(r);blank();before=read(label,0x110);call(0xFC2440,label,(surface,))
  require(rd(0x1200B044)==(0x142 if kind==2 else 0x140) and rd(0x1200B040)==0,'actual COLUMN text local bold/cache role'+str(r)+' attr'+str(a))
  require(rd(0x1200B04C)==label+0xA8,'actual native vtable textcomponent binding role'+str(r))
  require(read(label,0x110)==before,'complete COLUMN source widget/font unchanged role'+str(r))
  require((rd(0x1200B048)!=baseline)==(kind!=0) and rd(pix)==0xFF010203,'native appearance underlay text ordering role'+str(r))
  require(all(rd(pixels+(yy*w+xx)*4)==baseline for yy in range(h) for xx in range(32,w)),'actual native Draw numeric column region unchanged role'+str(r))
 # Numeric column uses the SAME real class. It is unregistered and must never receive styles.
 begin();register(13);role(10);blank();before=read(numeric,0x110);call(0xFC2440,numeric,(surface,))
 require(rd(0x1200B044)==0x140 and rd(0x1200B048)==baseline and read(numeric,0x110)==before,'actual same-class numeric cell remains unstyled')
 # Already copied source native FONT cache references balance through the real cleanup.
 ref=0x12005000;vt=0x12005100;release=0x12005200
 write(release,b'\xC3');write(vt,pack(release)+pack(release));write(ref,pack(vt)+pack(2));write(label+0xC0,pack(ref))
 for r,a,expectedcache in [(10,13,0),(1,13,ref),(4,11,ref),(0,13,ref)]:
  begin();register(a);role(r);blank();before=read(label,0x110);call(0xFC2440,label,(surface,))
  require(rd(0x1200B040)==expectedcache and rd(ref+4)==2 and read(label,0x110)==before,'actual component localFONT refcounts balanced role'+str(r))
 write(label+0xC0,pack(0))
 # Image-only native branch must not receive a text underlay or invoke text component.
 begin();register(13);role(10);blank();write(label+0x108,b'\1');call(0xFC2440,label,(surface,))
 require(read(pixels,w*h*4)==pack(baseline)*(w*h),'native image-only branch does not receive underlay');write(label+0x108,b'\0')
 # Record the actual destroyed-class dispatch independently from the controlled storage lifecycle.
 require(rd(0x150C5E4)==0x6C02A0 and rd(0x150C5E4+0x78)==0xFC2440,'actual STANDARD vtable destructor anddraw dispatch')
 require(read(0x4C6020,7)==bytes.fromhex('6aff688eed1401'),'actual COLUMN destructor boundary bytes')
 # Inline hook has no extra function frame: compare full real draw FP/SIMD state across modes.
 fx=0x1200D000;fx2=fx+0x200;entry=0x1200C800
 marker=bytes.fromhex('00112233445566778899aabbccddeeff');write(0x1200D800,marker)
 stub=b'\xDB\xE3\xF3\x0F\x6F\x05'+pack(0x1200D800)+b'\x0F\xAE\x05'+pack(fx)+b'\x68'+pack(surface)+b'\xB9'+pack(label)+b'\xB8'+pack(0xFC2440)+b'\xFF\xD0\x0F\xAE\x05'+pack(fx2)+b'\xC3'
 write(entry,stub);begin();register(13);role(10);call(entry)
 beforefx=read(fx,512);afterfx=read(fx2,512)
 require(beforefx[:28]==afterfx[:28] and beforefx[32:160]==afterfx[32:160] and beforefx[160:288]==afterfx[160:288],'actual native COLUMN draw preserves FP/SIMD with both inline hooks')
 res['role_attribute_combinations']=tested;res['status']='PASS';res['full_real_profile_UI_tested']=False
except BaseException as error:
 res['status']='FAIL';res['error']={'type':type(error).__name__,'message':str(error)}
 raise
finally:
 if p.hProcess:
  res['termination_requested']=bool(K.TerminateProcess(p.hProcess,0));res['private_process_cleanup_confirmed']=K.WaitForSingleObject(p.hProcess,3000)==0;K.CloseHandle(p.hThread);K.CloseHandle(p.hProcess)
 (R/'native-fixture-results.json').write_text(json.dumps(res,indent=2),encoding='utf-8')
print(json.dumps({'status':res['status'],'cases':len(res['cases']),'role_attribute_combinations':res.get('role_attribute_combinations'),'private_pid':res.get('private_pid'),'terminated':res.get('private_process_cleanup_confirmed')}))
