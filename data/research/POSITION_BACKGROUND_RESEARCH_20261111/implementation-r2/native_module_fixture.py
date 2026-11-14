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
res={'status':'STARTED','source_sha256':hashlib.sha256(EXE.read_bytes()).hexdigest(),'never_resumed_main_thread':True,'user_process_touched':False,'cases':[],'boundary_doubles':['native widget factory F69F70 replaced ONLY in private process by argument recorder returning a controlled LABEL layout','native text-render tail after actual native FONTcopyFBC080/FBC24C is controlled text-marker callback; no full FONT/UI initialization claimed'],'real_native':['actual name creation caller instructions9B0981..9B0997','IMAGE constructorF7EA50 and vtable16701E4','FillRectF94D30, clippingF928C0, surfaceF7ECE0 and original SIMD blending','SetRole native table invalidationF61160 in non-visible headless widget state','actual LABELDraw nativeprologue, FONTcopyFBC080, local-font hook, native SEH epilogue']}
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
  write(l,pack(0x1675554));write(l+4,pack(table));write(l+0x34,struct.pack('<hhhh',2 if l==label else 32,2,28 if l==label else 12,7));write(l+0x98,pack(0x12345678));write(l+0xA0,pack(0x140))
 call(0xF7EA50,surface);w=48;h=20;baseline=0xFF202020
 write(surface+8,struct.pack('<hhhhhh',0,0,w,h,0,0));write(surface+0x14,pack(pixels));write(surface+0x18,struct.pack('<hhh',w,h,w))
 def blank():write(pixels,pack(baseline)*(w*h))
 def begin(pr=profile):call(P['BeginGenerationEntry'],pr)
 def register(attr,row=5,la=label,ta=table,pr=profile):call(P['RegisterEntry'],args=(pr,ta,la,attr,row))
 def role(r,pr=profile):call(P['SetRoleEntry'],pr,(r,))
 def render(la=label):return call(P['RenderEntry'],la,edx=surface)
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
 # Actual native caller bytes + production NameCreated wrapper, with ONLY native factory boundary substituted.
 # Records all forwarded factory arguments, including caller row and factory pointer.
 recorder=bytearray()
 for j in range(5):recorder+=b'\x8B\x44\x24'+bytes([4+j*4])+b'\xA3'+pack(0x1200B000+j*4)
 recorder+=b'\xB8'+pack(label)+b'\xC2\x14\x00';patch(0xF69F70,recorder)
 patch(0x9B0992,b'\xE8'+pack(P['NativeNameCreatedEntry']-(0x9B0992+5)))
 patch(0x9B0997,b'\xA3'+pack(0x1200B020)+b'\x8B\xE5\x5D\xC3')
 def frame(attr,row,col=0):
  entry=0x1200C000
  stub=b'\x55\x8B\xEC\x81\xEC'+pack(0x200)+b'\xC6\x44\x24\x38'+bytes([attr&255])+b'\xC7\x44\x24\x68'+pack(row)+b'\xBE'+pack(profile)+b'\xBB'+pack(table)+b'\xB8'+pack(factory)
  # 9B0981 retains its original instructions, except controlledcol operand for negative guardtest.
  patch(0x9B098F,bytes([col]))
  stub+=b'\xE9'+pack(0x9B0981-(entry+len(stub)+5));write(entry,stub)
  return call(entry)
 begin();require(frame(13,37)==label,'actual native caller frame returns original label pointer')
 require(rd(state+16)==1 and rd(state+64)==label and rd(state+64+8)==13 and rd(state+64+16)==37,'actual9B0981 caller plus productionwrapper binds enum,row,parent,label')
 require([rd(0x1200B000+j*4) for j in range(5)]==[0,37,factory,0x1B205CC,0],'all five factory arguments forwarded exactly')
 begin();frame(13,37,1);require(rd(state+16)==0,'column1 nativeframe explicitly rejected');patch(0x9B098F,b'\0')
 # Draw wrapper with actual FillRect and controlled text boundary: verifies order and nativefontstate restoration.
 write(label+0x98,pack(0)) # Actual native copy is allowed to retain a null cache; no fake fontpointer.
 text=bytearray(b'\x8B\x44\x24\x18\xA3'+pack(0x1200B040)+b'\x8B\x44\x24\x20\xA3'+pack(0x1200B044))
 pix=pixels+(3*w+3)*4
 text+=b'\xA1'+pack(pix)+b'\xA3'+pack(0x1200B048)+b'\xC7\x05'+pack(pix)+pack(0xFF010203)
 # Native FBC349 epilogue restores original SEH/EDI/ESI/frame and ret4.
 tail=0x1200E000;text+=b'\xE9'+pack(0xFBC301-(tail+len(text)+5));write(tail,text)
 patch(0xFBC24C,b'\xE9'+pack(P['FontCopyEntry']-(0xFBC24C+5))+b'\x90')
 patch(0xFBC252,b'\xE9'+pack(tail-(0xFBC252+5)))
 for r,a,kind in [(10,13,2),(3,14,2),(1,4,2),(4,11,1),(1,13,0)]:
  begin();register(a);role(r);blank();before=read(label,0xB0);call(P['LabelDrawEntry'],label,(surface,))
  require(rd(0x1200B044)==(0x142 if kind==2 else 0x140) and rd(0x1200B040)==0,'scoped bold and cache bypass role'+str(r)+' attr'+str(a))
  require(read(label,0xB0)==before,'original completeLABEL bytes restored after text role'+str(r)+' attr'+str(a))
  require((rd(0x1200B048)!=baseline)==(kind!=0) and rd(pix)==0xFF010203,'underlay precedes text callback role'+str(r)+' attr'+str(a))
  require(all(rd(pixels+(yy*w+xx)*4)==baseline for yy in range(h) for xx in range(32,w)),'Draw wrapper numeric column unchanged role'+str(r)+' attr'+str(a))


 # Original FBC080/FAC5D0 + Interlocked reference ownership, controlled release callback only.
 ref=0x12005000;vt=0x12005100;release=0x12005200
 write(release,b'\xC3');write(vt,pack(release)+pack(release));write(ref,pack(vt)+pack(2));write(label+0x98,pack(ref))
 for r,a,expectedcache in [(10,13,0),(1,13,ref),(4,11,ref)]:
  begin();register(a);role(r);blank();sourcefont=read(label+0x90,32);call(P['LabelDrawEntry'],label,(surface,))
  require(rd(0x1200B040)==expectedcache and rd(ref+4)==2 and read(label+0x90,32)==sourcefont,'native copied-font ownership balanced, sourceFONT unchanged role'+str(r))
 write(label+0x98,pack(0))
 # FXSAVE state around real underlay preserves caller FP/SIMD before the original text boundary.
 begin();register(13);role(10);blank()
 fx=0x1200D000;fx2=fx+0x200;entry=0x1200C800
 marker=bytes.fromhex('00112233445566778899aabbccddeeff');write(0x1200D800,marker)
 stub=b'\xDB\xE3\xF3\x0F\x6F\x05'+pack(0x1200D800)+b'\x0F\xAE\x05'+pack(fx)+b'\x68'+pack(surface)+b'\xB9'+pack(label)+b'\xB8'+pack(P['LabelDrawEntry'])+b'\xFF\xD0\x0F\xAE\x05'+pack(fx2)+b'\xC3'
 write(entry,stub);call(entry)
 beforefx=read(fx,512);afterfx=read(fx2,512)
 require(beforefx[:28]==afterfx[:28] and beforefx[32:160]==afterfx[32:160] and beforefx[160:288]==afterfx[160:288],'Draw underlay preserves x87 control/status/registers and XMM0..7')
 res['role_attribute_combinations']=tested;res['status']='PASS';res['full_real_profile_UI_tested']=False
finally:
 if p.hProcess:
  res['terminated_private_process']=bool(K.TerminateProcess(p.hProcess,0));K.WaitForSingleObject(p.hProcess,3000);K.CloseHandle(p.hThread);K.CloseHandle(p.hProcess)
 (R/'native-fixture-results.json').write_text(json.dumps(res,indent=2),encoding='utf-8')
print(json.dumps({'status':res['status'],'cases':len(res['cases']),'role_attribute_combinations':res.get('role_attribute_combinations'),'private_pid':res.get('private_pid'),'terminated':res.get('terminated_private_process')}))
