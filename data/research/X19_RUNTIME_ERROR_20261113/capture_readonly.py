from pathlib import Path
import sys,ctypes,struct,json,hashlib,datetime,importlib.util
from ctypes import wintypes as w
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('rpm',B.parent/'CONTROVERSY_CONTROL_8074_20261111/probe_runtime_readonly.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
u=ctypes.WinDLL('user32',use_last_error=True);k=ctypes.WinDLL('kernel32',use_last_error=True);nt=ctypes.WinDLL('ntdll')
CB=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
u.EnumWindows.argtypes=[CB,w.LPARAM];u.EnumChildWindows.argtypes=[w.HWND,CB,w.LPARAM];u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)];u.GetWindowTextW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int];u.GetClassNameW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int];u.SendMessageTimeoutW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM,w.UINT,w.UINT,ctypes.POINTER(ctypes.c_size_t)]
k.OpenThread.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenThread.restype=ctypes.c_void_p;k.CloseHandle.argtypes=[ctypes.c_void_p]
class TBI(ctypes.Structure):_fields_=[('ExitStatus',ctypes.c_long),('Teb',ctypes.c_void_p),('PID',ctypes.c_void_p),('TID',ctypes.c_void_p),('Affinity',ctypes.c_size_t),('Priority',ctypes.c_long),('BasePriority',ctypes.c_long)]
nt.NtQueryInformationThread.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_void_p,ctypes.c_uint,ctypes.c_void_p]
def win(h):
 t=ctypes.create_unicode_buffer(2048);c=ctypes.create_unicode_buffer(128);u.GetWindowTextW(h,t,2048);u.GetClassNameW(h,c,128)
 if not t.value:
  n=ctypes.c_size_t();u.SendMessageTimeoutW(h,0xD,2048,ctypes.cast(t,ctypes.c_void_p).value,2,100,ctypes.byref(n))
 p=w.DWORD();tid=u.GetWindowThreadProcessId(h,ctypes.byref(p));return dict(hwnd=int(h),tid=tid,pid=p.value,className=c.value,text=t.value)
windows=[]
@CB
def each(h,l):
 r=win(h)
 if r['pid']==19308:
  r['children']=[]
  @CB
  def child(c,l):r['children'].append(win(c));return len(r['children'])<128
  u.EnumChildWindows(h,child,0);windows.append(r)
 return True
u.EnumWindows(each,0)
res=dict(status='READ_ONLY_CAPTURE',pid=19308,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),windows=windows,noProcessWrites=True,noDebuggerAttach=True,noSuspend=True,noRemoteCalls=True,stackEvidence='RAW_RANGE_POINTERS_NOT_EXECUTION_TRACE')
m=mod.WindowsMemory(19308)
def read(a,n):
 if not 0x10000<=a<0x7fffffffffff or not 0<n<=1048576:raise ValueError('bounded RPM')
 buf=ctypes.create_string_buffer(n);got=ctypes.c_size_t()
 if not m.k.ReadProcessMemory(m.handle,ctypes.c_void_p(a),buf,n,ctypes.byref(got)) or got.value!=n:raise ValueError('unreadable')
 return buf.raw
try:
 res['image']=m.image;res['imageSha256']=hashlib.sha256(Path(m.image).read_bytes()).hexdigest()
 res['getterEntries']={hex(a):read(a,5).hex()for a in [0xafe0d0,0xafe150]}
 warning=next((x for x in windows if x['className']=='#32770'),None)
 if warning:
  th=k.OpenThread(0x40,False,warning['tid'])
  if not th:raise ValueError('OpenThread QUERY_INFORMATION failed')
  try:
   t=TBI();status=nt.NtQueryInformationThread(th,0,ctypes.byref(t),ctypes.sizeof(t),None);res['threadQuery']=dict(status=int(status),tid=warning['tid'],teb=int(t.Teb or 0),clientPID=int(t.PID or 0),clientTID=int(t.TID or 0))
   if status!=0 or int(t.PID or 0)!=19308 or int(t.TID or 0)!=warning['tid']:raise ValueError('thread identity')
   teb=int(t.Teb);raw=read(teb,0x2000);candidates={teb,teb+0x2000,teb-0x2000}
   for off in range(0,len(raw)-8,4):
    q=struct.unpack_from('<I',raw,off)[0]
    if 0x10000<=q<0x80000000 and q%0x1000==0:candidates.add(q)
   found=[]
   for a in sorted(candidates):
    try:
     b=read(a,0x30);base,limit=struct.unpack_from('<II',b,4);selfp=struct.unpack_from('<I',b,0x18)[0];pid,tid=struct.unpack_from('<II',b,0x20)
     if selfp==a and pid==19308 and tid==warning['tid'] and 0x10000<=limit<base<0x80000000 and base-limit<=8388608:found.append(dict(teb=a,stackBase=base,stackLimit=limit))
    except Exception:pass
   res['validatedTeb32']=found
   if len(found)==1:
    import pefile
    p=pefile.PE(m.image);image=p.get_memory_mapped_image();x=found[0];limit=x['stackLimit'];base=x['stackBase'];n=min(base-limit,1048576);stack=read(limit,n);calls=[]
    for i in range(0,len(stack)-4,4):
     v=struct.unpack_from('<I',stack,i)[0];off=v-0x400000
     if 5<=off<len(image) and image[off-5]==0xe8:
      target=v+struct.unpack_from('<i',image,off-4)[0]
      if 0x400000<=target<0x1800000:calls.append(dict(stackAddress=limit+i,returnAddress=v,directCallTarget=target))
    res['stackRange']=dict(address=limit,bytes=n,sha256=hashlib.sha256(stack).hexdigest(),candidateReturnAddresses=calls[:400],totalCandidates=len(calls),truncatedCandidates=len(calls)>400,warning='May contain stale return pointers; not unwind/current EIP proof.')
  finally:k.CloseHandle(th)
except Exception as e:res['captureGap']=type(e).__name__+': '+str(e)
finally:m.close()
res['dialogText']=[x['text']for y in windows if y['className']=='#32770' for x in y['children']if x['className']=='Static' and x['text']]
out=B/'capture-19308.json'
if out.exists():raise ValueError('preserve existing capture')
out.write_text(json.dumps(res,indent=2)+'\n')
print(json.dumps(dict(dialog=res['dialogText'],thread=res.get('threadQuery'),teb=res.get('validatedTeb32'),stackCandidates=res.get('stackRange',{}).get('totalCandidates'),gap=res.get('captureGap'),sha256=hashlib.sha256(out.read_bytes()).hexdigest()),indent=2))
