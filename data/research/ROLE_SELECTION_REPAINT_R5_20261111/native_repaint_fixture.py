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
res={'status':'STARTED','source_sha256':hashlib.sha256(EXE.read_bytes()).hexdigest(),'never_resumed_main_thread':True,'user_process_touched':False,'cases':[],'boundary_doubles':['controlled realclass/GUI-manager/RECT-pool/ARRAY storage; original visible invalidator and dirtyqueue execute','source-pinned nativeFill body boundary creates registered cells then returns; no full database/client fill claimed','role callback uses actual POPUPgetter and SYMBOLdecoder; popup lookup boundary controlled'],'real_native':['IMAGEF7EA50/FillRectF94D30','visibleWIDGETF61160/GUIFE6F60/nativeRECTpoolF55FE0/nativeARRAY1285110','nativeTYPEbootstrapF5E080/POPUPslctFB61E0/SYMBOLF5BDA0','productionbackground postFill wrapper with unchanged native aligned prologue; body boundary controlled']}
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

 # Real visible rectangle invalidation: native GUI dirty ARRAY and native RECT pool.
 # Ready controlled memory replaces no getter/callee; native FE6F60 and allocation from prefilled pool execute.
 gui=0x12007000;vector=0x12008000;pool=0x12009000;free=0x1200A000;popup=0x1200B400;variant=0x1200B800
 write(0x1B24260,pack(gui));write(gui+0x19C,pack(surface));write(gui+0x1E0,pack(0x1285110));write(gui+0x1E4,pack(vector));write(gui+0x1EC,pack(64))
 write(0x1915030,pack(pool));write(pool+0x14,pack(8));write(pool+0x18,pack(free));write(pool+0x1C,pack(64))
 for k in range(64):write(free+k*8,pack(free+(k+1)*8 if k<63 else 0))
 for t in [table,table2]:write(t+0x28,pack(2));write(t+0x34,struct.pack('<hhhh',2,2,28,7))
 write(popup,pack(0x167466C));write(popup+0x10,pack(0x167465C));write(popup+0x160,pack(0x46703033))
 # Reuse existing PositionProfileNativeFixture native datatype bootstrap, not a mock constructor.
 call(0xF5E080,0x1200B900);write(0x1B24238,pack(0x1200B900))
 # Existing actual native popup SYMBOL getter is independently witnessed here; no substitute getter.
 call(0xF5E670,variant);require(call(0xFB61E0,popup+0x10,(0x736C6374,variant))&255!=0,'actual popup slct getter succeeds')
 require(call(0xF5BDA0,variant)==0x46703033,'actual native SYMBOL decode returns CURRENT Fp03');call(0xF5BC90,variant)
 # Callback retains the production selector ABI, with controlled popup lookup boundary only.
 callback=0x1200C000
 def callback_for(setrole):
  z=bytearray(b'\x56\x8B\xF1\x83\xEC\x08\x8B\xCC')
  def cc(a):z.extend(b'\xE8'+pack(a-(callback+len(z)+5)))
  cc(0xF5E670);z.extend(b'\x8B\xC4\x50\x68'+pack(0x736C6374)+b'\xB9'+pack(popup+0x10));cc(0xFB61E0)
  z.extend(b'\x8B\xCC');cc(0xF5BDA0)
  z.extend(b'\x2D'+pack(0x46703030)+b'\x50\x8B\xCE');cc(setrole)
  z.extend(b'\x8B\xCC');cc(0xF5BC90);z.extend(b'\x83\xC4\x08\x5E\xC3');write(callback,z)
 # Native Fill boundary emits cells then returns using the unchanged native aligned-frame epilogue.
 # This is a source-pinned boundary, not a full native player/client database fixture.
 fill=0x1200C400
 def fill_for(registerentry):
  z=bytearray(b'\x68'+pack(5)+b'\x68'+pack(14)+b'\x68'+pack(label)+b'\x68'+pack(table)+b'\x68'+pack(profile))
  z+=b'\xE8'+pack(registerentry-(fill+len(z)+5))+b'\x8B\xE5\x5D\xC3';write(fill,z)
  patch(0x9AFCE6,b'\xE9'+pack(fill-(0x9AFCE6+5)))
 oldr=R.parent/'POSITION_BACKGROUND_RESEARCH_20261111/implementation-r4'
 old=json.loads((oldr/'position-payload.json').read_text())
 write(0x12020000,(oldr/'position-code.bin').read_bytes());write(state,(oldr/'position-data.bin').read_bytes())
 callback_for(old['SetRoleEntry']);fill_for(old['RegisterEntry']);write(state+40,pack(callback))
 call(old['BeginGenerationEntry'],profile);call(old['SetRoleEntry'],profile,(1,));call(old['BeginGenerationHookEntry'],profile)
 require(rd(state+12)==0 and rd(state+16)==1,'R4 regression selectedFp03 lost after direct same-profile nativeFill boundary')
 write(0x12020000,(R/'position-code.bin').read_bytes());write(state,(R/'position-data.bin').read_bytes());callback_for(P['SetRoleEntry']);fill_for(P['RegisterEntry']);write(state+40,pack(callback))
 begin();role(1);call(P['BeginGenerationHookEntry'],profile)
 require(rd(state+12)==3 and rd(state+16)==1,'R5 first postFill synchronize reads CURRENTFp03 after all cells registered')
 require(rd(gui+0x1E8)>0 and rd(pool+0x20)>0,'first selection invokes real visible F61160 FE6F60 RECTpool dirty queue')
 require(rd(gui+0x1B8)==0,'native rectangle queue works without invented GUIglobalflag2')
 rect=rd(vector);q=struct.unpack('<hhhh',read(rect,8))
 require(q[0]<=2 and q[1]<=2 and q[0]+q[2]>=30 and q[1]+q[3]>=9,'native queued dirty rectangle covers name-cell drawing area')
 # Use a different current selection and same object identity. No old-role preservation by profileptr.
 write(popup+0x160,pack(0x46703031));call(P['BeginGenerationHookEntry'],profile)
 require(rd(state+12)==1 and rd(state+16)==1,'same profile object different selectedrole after rebuild uses currentpopup not oldrolecache')
 # No selector means OFF, even though the previous profile had a role. No unsafe fallback.
 write(state+40,pack(0));call(P['BeginGenerationHookEntry'],profile)
 require(rd(state+12)==0 and rd(state+16)==1,'absent callback fails OFF without reading stale UI pointers')
 write(state+40,pack(callback));write(popup+0x160,pack(0x46703033))
 for n in range(20):
  call(P['BeginGenerationHookEntry'],profile);assert rd(state+12)==3 and rd(state+16)==1
 require(rd(state+8)>=24 and rd(state+12)==3,'20 subsequent nativeFill boundaries retain current selection without repeated user event')
 # Real renderer after the queued first selection; no second role event occurs.
 call(P['BeginGenerationHookEntry'],profile);blank();require(render()==2,'first selection after rebuild renders native Heading key without secondevent')
 role(0);blank();require(render()==0 and read(pixels,w*h*4)==pack(baseline)*(w*h),'singleOFF event removes underlay with visible invalidation queued')
 # Preserve the native return register contract around the postFill callback (which clobbers EAX).
 # The actual native Fill is void, but wrappers still retain native volatile return values/flags.
 z=bytearray(b'\x68'+pack(5)+b'\x68'+pack(14)+b'\x68'+pack(label)+b'\x68'+pack(table)+b'\x68'+pack(profile))
 z+=b'\xE8'+pack(P['RegisterEntry']-(fill+len(z)+5))+b'\xB8'+pack(0x1234ABCD)+b'\x8B\xE5\x5D\xC3';write(fill,z)
 require(call(P['BeginGenerationHookEntry'],profile)==0x1234ABCD,'postFill callback preserves original nativeEAX return')
 tested=0
 res['role_attribute_combinations']=tested;res['status']='PASS';res['full_real_profile_UI_tested']=False
except BaseException as error:
 res['status']='FAIL';res['error']={'type':type(error).__name__,'message':str(error)}
 raise
finally:
 if p.hProcess:
  res['termination_requested']=bool(K.TerminateProcess(p.hProcess,0));res['private_process_cleanup_confirmed']=K.WaitForSingleObject(p.hProcess,3000)==0;K.CloseHandle(p.hThread);K.CloseHandle(p.hProcess)
 (R/'native-fixture-results.json').write_text(json.dumps(res,indent=2),encoding='utf-8')
print(json.dumps({'status':res['status'],'cases':len(res['cases']),'role_attribute_combinations':res.get('role_attribute_combinations'),'private_pid':res.get('private_pid'),'terminated':res.get('private_process_cleanup_confirmed')}))
