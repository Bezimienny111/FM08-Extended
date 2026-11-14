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
p=PROCESS();si=STARTUP();si.cb=C.sizeof(si);si.dwFlags=1;si.wShowWindow=0
res={'source_sha256':hashlib.sha256(EXE.read_bytes()).hexdigest(),'created_private_suspended':False,'never_resumed_main_thread':True,'native_functions_modified':False,'user_process_opened':False,'cases':[],'status':'STARTED'}
def ck(ok):
 if not ok:raise C.WinError(C.get_last_error())
try:
 ck(K.CreateProcessW(str(EXE),C.create_unicode_buffer('"'+str(EXE)+'"'),None,None,False,4,None,str(EXE.parent),C.byref(si),C.byref(p)))
 res['created_private_suspended']=True;res['private_pid']=p.dwProcessId
 mem=K.VirtualAllocEx(p.hProcess,C.c_void_p(0x12000000),0x40000,0x3000,0x40);assert mem==0x12000000
 def write(a,b):
  n=C.c_size_t();v=C.create_string_buffer(b);ck(K.WriteProcessMemory(p.hProcess,C.c_void_p(a),v,len(b),C.byref(n)));assert n.value==len(b)
 def read(a,n):
  buf=C.create_string_buffer(n);got=C.c_size_t();ck(K.ReadProcessMemory(p.hProcess,C.c_void_p(a),buf,n,C.byref(got)));assert got.value==n;return buf.raw
 pack=lambda n:struct.pack('<I',n&0xFFFFFFFF)
 def call(a,self,args=()):
  stub=b''.join(b'\x68'+pack(x) for x in reversed(args))+b'\xB9'+pack(self)+b'\xB8'+pack(a)+b'\xFF\xD0\xA3'+pack(0x1200F100)+b'\x33\xC0\xC2\x04\x00'
  write(0x1200F000,stub);ck(K.FlushInstructionCache(p.hProcess,C.c_void_p(0x1200F000),len(stub)))
  tid=W.DWORD();t=K.CreateRemoteThread(p.hProcess,None,0,C.c_void_p(0x1200F000),None,0,C.byref(tid));ck(t)
  try:
   assert K.WaitForSingleObject(t,10000)==0,'private native thread timeout'
   ec=W.DWORD();ck(K.GetExitCodeThread(t,C.byref(ec)));assert ec.value==0,hex(ec.value)
   return struct.unpack('<I',read(0x1200F100,4))[0]
  finally:K.CloseHandle(t)
 surface=0x12001000;rect=0x12001200;pixels=0x12010000;w=48;h=20;baseline=0xFF202020
 call(0xF7EA50,surface)
 assert struct.unpack('<I',read(surface,4))[0]==0x16701E4
 # Equivalent buffer state of native F7EC50 allocator, using our VirtualAllocEx storage.
 # Retain real native vtable; no mocked methods or modified engine code.
 write(surface+8,struct.pack('<hhhhhh',0,0,w,h,0,0));write(surface+0x14,pack(pixels));write(surface+0x18,struct.pack('<hhh',w,h,w))
 assert read(0xF94D30,3)==bytes.fromhex('83ec20')
 cases=[('cell0-key',(2,2,28,7),0xFF406050,255),('cell0-important',(2,10,28,7),0xFF304038,255),('clip-left',(-3,3,10,4),0xFF507090,255),('clip-right',(43,3,12,4),0xFF507090,255),('outside',(60,2,5,4),0xFF507090,255),('alpha',(2,2,28,7),0xFF406050,96)]
 for name,rc,color,alpha in cases:
  write(pixels,pack(baseline)*(w*h));write(rect,struct.pack('<hhhh',*rc));before=read(pixels,w*h*4)
  call(0xF94D30,surface,(rect,color,alpha));after=read(pixels,w*h*4)
  vals=struct.unpack('<'+'I'*(w*h),after);changed=[(i%w,i//w) for i,v in enumerate(vals) if v!=baseline]
  x,y,rw,rh=rc;expect={(xx,yy) for yy in range(max(0,y),min(h,y+rh)) for xx in range(max(0,x),min(w,x+rw))}
  assert set(changed)==expect,(name,len(changed),len(expect))
  if alpha==255:assert all(vals[yy*w+xx]==color for xx,yy in expect)
  assert all(vals[yy*w+xx]==baseline for yy in range(h) for xx in range(32,w)) if name.startswith('cell0') else True
  (R/(name+'-pixels.bgra')).write_bytes(after)
  res['cases'].append({'name':name,'rect':rc,'color':hex(color),'alpha':alpha,'changed_pixels':len(changed),'exact_clipped_region':True,'unchanged_column1':True if name.startswith('cell0') else None,'unique_written_colors':sorted({hex(vals[yy*w+xx]) for xx,yy in expect}),'buffer_sha256':hashlib.sha256(after).hexdigest()})
 res['status']='PASS';res['native_fillrect']={'va':'0x00F94D30','calling_convention':'thiscall','ecx':'real IMAGE surface','arguments':['RECT4xint16 pointer','packed color value uint32','alpha uint8 in uint32'],'callee_cleanup_bytes':12}
finally:
 if p.hProcess:
  res['terminated_private_process']=bool(K.TerminateProcess(p.hProcess,0));K.WaitForSingleObject(p.hProcess,3000)
  K.CloseHandle(p.hThread);K.CloseHandle(p.hProcess)
 (R/'private-render-proof.json').write_text(json.dumps(res,indent=2),encoding='utf-8')
print(json.dumps({'status':res['status'],'cases':len(res['cases']),'pid':res.get('private_pid'),'terminated':res.get('terminated_private_process')}))
