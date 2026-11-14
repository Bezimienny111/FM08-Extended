"""ReadProcessMemory only. No attach, writes, thread suspension or remote execution."""
import ctypes as c,ctypes.wintypes as w,struct,json,time
from pathlib import Path
PID=10940
OUT=Path('J:/FM08dev/FmLauncher/data/research/R2_RUNTIME_FAILURE_20261111/root-readonly')
OUT.mkdir(parents=True,exist_ok=True)
assert not(OUT/'exception-snapshot.json').exists()
k=c.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
k.ReadProcessMemory.argtypes=[w.HANDLE,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)];k.ReadProcessMemory.restype=w.BOOL
class MBI(c.Structure):
 _fields_=[('BaseAddress',c.c_void_p),('AllocationBase',c.c_void_p),('AllocationProtect',w.DWORD),('RegionSize',c.c_size_t),('State',w.DWORD),('Protect',w.DWORD),('Type',w.DWORD)]
k.VirtualQueryEx.argtypes=[w.HANDLE,c.c_void_p,c.POINTER(MBI),c.c_size_t];k.VirtualQueryEx.restype=c.c_size_t
h=k.OpenProcess(0x410,False,PID)
assert h,('OpenProcess',c.get_last_error())
def rd(a,n):
 b=c.create_string_buffer(n);got=c.c_size_t();k.ReadProcessMemory(h,a,b,n,c.byref(got));return b.raw[:got.value]
def u32(b,o=0):return struct.unpack_from('<I',b,o)[0]
regions=[];pos=0
while pos<0x100000000:
 m=MBI()
 if not k.VirtualQueryEx(h,pos,c.byref(m),c.sizeof(m)):break
 base=int(m.BaseAddress or 0);size=int(m.RegionSize)
 if size<=0 or base+size<=pos:break
 if m.State==0x1000 and not(m.Protect&0x100)and(m.Protect&255)in [2,4,8,16,32,64,128]:regions.append(dict(base=base,size=size,protect=int(m.Protect),type=int(m.Type),allocation=int(m.AllocationBase or 0)))
 pos=base+size
execute=[(r['base'],r['base']+r['size'])for r in regions if r['protect']&255 in [16,32,64,128]]
def execaddr(a):return any(x<=a<y for x,y in execute)
def chunks():
 for r in regions:
  for at in range(r['base'],r['base']+r['size'],1048576):
   v=rd(at,min(1048576,r['base']+r['size']-at))
   if v:yield at,v
started=time.monotonic();records=[];scanned=0
for at,b in chunks():
 scanned+=len(b);p=0
 while True:
  i=b.find(b'\x05\x00\x00\xc0',p)
  if i<0:break
  p=i+4
  if i+80>len(b):continue
  code,flags,nextrec,eip,num=struct.unpack_from('<IIIII',b,i)
  access,address=struct.unpack_from('<II',b,i+20)
  if flags<=3 and num==2 and access in [0,1,8]and execaddr(eip):records.append(dict(address=at+i,code=hex(code),flags=flags,next=nextrec,eip=eip,access=access,target=address,record_hex=b[i:i+80].hex()))
 if time.monotonic()-started>40:break
print('Read-only exception record scan',scanned,'bytes;',len(records),'candidates',flush=True)
contexts=[];seen=set();recs={x['eip']for x in records}
if recs:
 for at,b in chunks():
  for eip in recs:
   p=0;needle=struct.pack('<I',eip)
   while True:
    i=b.find(needle,p)
    if i<0:break
    p=i+4;start=i-184
    if start<0 or start+204>len(b):continue
    flags=u32(b,start);cs=u32(b,start+188);ef=u32(b,start+192);esp=u32(b,start+196);ss=u32(b,start+200)
    if flags&0xffff0000!=0x10000 or not(flags&1)or cs not in [0x1b,0x23]or ss not in [0x23,0x2b]or not(ef&2)or not(0x10000<=esp<0x7fff0000):continue
    ca=at+start
    if ca in seen:continue
    seen.add(ca);blob=rd(ca,716)
    names={'edi':156,'esi':160,'ebx':164,'edx':168,'ecx':172,'eax':176,'ebp':180,'eip':184,'eflags':192,'esp':196}
    regs={n:u32(b,start+off)for n,off in names.items()}
    stack=rd(esp,16384);(OUT/('context-'+hex(ca)+'.bin')).write_bytes(blob);(OUT/('stack-'+hex(ca)+'.bin')).write_bytes(stack)
    code=rd(max(0,eip-64),192);(OUT/('code-'+hex(ca)+'.bin')).write_bytes(code)
    contexts.append(dict(address=ca,flags=flags,cs=cs,ss=ss,registers=regs,stack_bytes=len(stack),stack_first_words=[hex(x)for x in struct.unpack('<'+'I'*(min(len(stack),128)//4),stack[:min(len(stack),128)//4*4])],code_start=max(0,eip-64),code_hex=code.hex()))
  if time.monotonic()-started>85:break
for i,r in enumerate(records):
 (OUT/('record-'+str(i)+'.bin')).write_bytes(bytes.fromhex(r['record_hex']))
result=dict(pid=PID,status='READ_ONLY_EXCEPTION_SCAN_COMPLETE',process_access='VM_READ|QUERY_INFORMATION',regions=regions,scanned_bytes=scanned,exception_records=records,contexts=contexts,elapsed_seconds=round(time.monotonic()-started,2),process_writes=False,remote_execution=False,thread_suspension=False,debugger_attach=False,limitations=['Read while application remains in error dialog; non-atomic live snapshot','Only preserved access-violation records and matching x86 contexts selected; absence is not proof of no exception'])
(OUT/'exception-snapshot.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items()if k not in ['regions']},indent=2))
k.CloseHandle(h)