from pathlib import Path
import ctypes as C,ctypes.wintypes as W,struct,json,hashlib,datetime
R=Path(__file__).resolve().parent;PID=19332
K=C.WinDLL('kernel32',use_last_error=True)
K.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];K.OpenProcess.restype=W.HANDLE
K.ReadProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)];K.ReadProcessMemory.restype=W.BOOL
K.CloseHandle.argtypes=[W.HANDLE];K.CloseHandle.restype=W.BOOL
p=K.OpenProcess(0x410,False,PID)
if not p:raise C.WinError(C.get_last_error())
K.QueryFullProcessImageNameW.argtypes=[W.HANDLE,W.DWORD,W.LPWSTR,C.POINTER(W.DWORD)];K.QueryFullProcessImageNameW.restype=W.BOOL
name=C.create_unicode_buffer(32768);count=W.DWORD(len(name));assert K.QueryFullProcessImageNameW(p,0,name,C.byref(count));image=Path(name.value)
assert image.name.lower()=='fm.exe'
assert hashlib.sha256(image.read_bytes()).hexdigest()=='157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d'
errors=[]
def read(a,n):
 if a<=0 or a==0xFFFFFFFF:return b''
 b=C.create_string_buffer(n);got=C.c_size_t()
 if not K.ReadProcessMemory(p,C.c_void_p(a),b,n,C.byref(got)) or got.value!=n:
  errors.append({'address':hex(a),'bytes':n,'winerror':C.get_last_error()});return b''
 return b.raw
def u(a):
 b=read(a,4);return struct.unpack('<I',b)[0] if b else 0
U=lambda b,k:struct.unpack_from('<I',b,k)[0]
def tag(n):return n.to_bytes(4,'big').decode('ascii','replace')
def class_name(vt):
 col=u(vt-4);td=u(col+12);b=read(td+8,100);return b.split(b'\0')[0].decode('ascii','replace') if b else ''
def props(bag):
 n=u(bag+8);arr=u(bag+4)
 if n>512:return []
 o=[]
 for k in range(n):
  v=u(arr+k*4)
  o.append({'address':hex(v),'key':tag(u(v+8)),'data':hex(u(v)),'type':hex(u(v+4))})
 return o
try:
 popup=0x11183F10;assert u(popup)==0x167466C and u(popup+0x30)==0x46706F73
 items=u(popup+0x15C);txt=u(popup+0xB4);ln=int.from_bytes(read(txt+4,2),'little');caption=read(u(txt+8),ln*2).decode('utf-16le')
 ip=props(items+4);arr=0x0C368730;assert u(arr)==0x1670190 and u(arr+8)==12
 vec=u(arr+4);records=[]
 for k in range(12):
  ptr=u(vec+k*4);vt=u(ptr);bag=ptr+4 if u(ptr+4)==0x166A12C else ptr
  records.append({'index':k,'record':hex(ptr),'vtable':hex(vt),'header':read(ptr,64).hex(),'properties':props(bag) if u(bag)==0x166A12C else []})
 result={'pid':PID,'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'popup':hex(popup),'selection':tag(u(popup+0x160)),'caption':caption,'caption_native_UTF16_length':ln,'items_wrapper_properties':ip,'array':hex(arr),'array_count':12,'records':records}
 (R/'menu-records.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
 print(json.dumps(result,indent=2,ensure_ascii=True))
finally:K.CloseHandle(p)
