"""Read-only local region snapshot; no debugger, suspension, VM writes or execution."""
import ctypes as c,ctypes.wintypes as w,json,zlib,hashlib,time,shutil
from pathlib import Path
PID=2052
OUT=Path('J:/FM08dev/FmLauncher/data/research/R3_RUNTIME_FAILURE_20261111/root-readonly/memory-regions')
assert not OUT.exists()
OUT.mkdir();assert shutil.disk_usage(OUT).free>1073741824
k=c.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
k.ReadProcessMemory.argtypes=[w.HANDLE,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)]
class MBI(c.Structure):
 _fields_=[('BaseAddress',c.c_void_p),('AllocationBase',c.c_void_p),('AllocationProtect',w.DWORD),('RegionSize',c.c_size_t),('State',w.DWORD),('Protect',w.DWORD),('Type',w.DWORD)]
k.VirtualQueryEx.argtypes=[w.HANDLE,c.c_void_p,c.POINTER(MBI),c.c_size_t];k.VirtualQueryEx.restype=c.c_size_t
h=k.OpenProcess(0x410,False,PID);assert h
records=[];pos=0;total=0;stored=0;started=time.monotonic();complete=True
while pos<0x100000000:
 m=MBI()
 if not k.VirtualQueryEx(h,pos,c.byref(m),c.sizeof(m)):break
 base=int(m.BaseAddress or 0);size=int(m.RegionSize)
 if size<=0 or base+size<=pos:break
 pos=base+size
 if m.State!=0x1000 or m.Protect&0x100 or m.Protect&255 not in [2,4,8,16,32,64,128]:continue
 for at in range(base,base+size,8388608):
  n=min(8388608,base+size-at);buf=c.create_string_buffer(n);got=c.c_size_t();k.ReadProcessMemory(h,at,buf,n,c.byref(got));raw=buf.raw[:got.value]
  if not raw:continue
  name=hex(at)+'-'+str(len(raw))+'.zlib';packed=zlib.compress(raw,1);(OUT/name).write_bytes(packed)
  records.append(dict(base=at,size=len(raw),requested=n,region_base=base,region_size=size,protect=int(m.Protect),type=int(m.Type),file=name,sha256=hashlib.sha256(raw).hexdigest(),compressed_bytes=len(packed)))
  total+=len(raw);stored+=len(packed)
  if total>1073741824 or time.monotonic()-started>75:complete=False;break
 if not complete:break
meta=dict(status='READ_ONLY_REGION_SNAPSHOT',pid=PID,complete=complete,records=records,raw_bytes=total,compressed_bytes=stored,elapsed_seconds=round(time.monotonic()-started,2),process_writes=False,remote_execution=False,thread_suspension=False,debugger_attach=False,limitations=['Not an atomic OS minidump; memory read while fatal dialog was open','Saved access-violation record/context captured separately in exception-snapshot.json'])
(OUT/'index.json').write_text(json.dumps(meta,indent=2),encoding='utf-8');k.CloseHandle(h)
print(json.dumps({key:value for key,value in meta.items()if key!='records'},indent=2));print('chunks',len(records),flush=True)