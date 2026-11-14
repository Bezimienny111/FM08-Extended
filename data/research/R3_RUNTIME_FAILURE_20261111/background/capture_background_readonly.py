from pathlib import Path
import ctypes as C,ctypes.wintypes as W,struct,json,hashlib,datetime
R=Path(__file__).resolve().parent;PID=2052
K=C.WinDLL('kernel32',use_last_error=True)
K.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];K.OpenProcess.restype=W.HANDLE
K.ReadProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)];K.ReadProcessMemory.restype=W.BOOL
K.CloseHandle.argtypes=[W.HANDLE];K.CloseHandle.restype=W.BOOL
p=K.OpenProcess(0x410,False,PID)
if not p:raise C.WinError(C.get_last_error())
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
 hook=read(0x9B0992,5);assert hook[0]==0xE8
 code=0x9B0997+struct.unpack_from('<i',hook,1)[0]
 template=json.loads(Path('FmLauncher/data/research/POSITION_BACKGROUND_RESEARCH_20261111/implementation-r3/position-payload.json').read_text())
 begin=code+(template['BeginGenerationEntry']-0x12020000);prefix=read(begin,6);assert prefix[:2]==b'\x89\x0D'
 state=struct.unpack_from('<I',prefix,2)[0]-4;before=read(state,64);profile=U(before,4)
 obj=read(profile,0x110);nodes=[];todo=[(profile,0)];seen=set()
 while todo and len(seen)<2048:
  a,depth=todo.pop()
  if a in seen or depth>30:continue
  seen.add(a);vt=u(a);ident=u(a+0x30)
  node={'address':hex(a),'parent':hex(u(a+4)),'vtable':hex(vt),'id':tag(ident),'depth':depth}
  if ident in [0x706C7474,0x706C6D74,0x706C7074]:
   rows=u(a+0xA4);node['rows']=u(rows+8);node['header_rows']=u(a+0xC0);node['attribute_rows']=node['rows']-node['header_rows'];node['flags']=hex(u(a+0x28));node['class']=class_name(vt)
  if ident==0x46706F73:
   node['class']=class_name(vt);node['selection_symbol']=tag(u(a+0x160));node['selection_raw']=hex(u(a+0x160));node['items_property_list']=hex(u(a+0x15C))
  nodes.append(node)
  # Proven native CONTAINER methods identify +70 child ARRAY; LABEL+70 is text, never walk it.
  if u(vt+0xBC)==0xF77C70 and u(vt+0xC0)==0xF77C40:
   arr=u(a+0x70);n=u(arr+8);items=u(arr+4)
   if 0<n<2048:
    bb=read(items,n*4)
    if bb:
     for k in range(n):
      child=U(bb,k*4)
      if child and child!=0xFFFFFFFF:todo.append((child,depth+1))
 after=read(state,64)
 names=['Enabled','ActiveProfile','Generation','Role','Count','Overflow','Registered','Rendered','LastAttribute','LastEmphasis']
 result={'status':'READ_ONLY_STABLE_PROFILE_BACKGROUND_TRIAGE','pid':PID,'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'process_access':'QUERY_INFORMATION|VM_READ','writes_to_process':False,'suspension':False,'remote_execution':False,'code':hex(code),'state':hex(state),'state_before':{k:hex(U(before,i*4)) if k=='ActiveProfile' else U(before,i*4) for i,k in enumerate(names)},'state_after':{k:hex(U(after,i*4)) if k=='ActiveProfile' else U(after,i*4) for i,k in enumerate(names)},'state_header_stable':before==after,'profile':hex(profile),'profile_vtable':hex(U(obj,0)),'profile_class':class_name(U(obj,0)),'profile_cache':{hex(k):hex(U(obj,k)) for k in range(0x90,0xB0,4)},'profile_properties':props(U(obj,0x3C)),'nodes':nodes,'read_errors':errors}
 (R/'live-background.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 (R/'position-state-before.bin').write_bytes(before);(R/'position-state-after.bin').write_bytes(after);(R/'profile.bin').write_bytes(obj)
 print(json.dumps({'state':result['state_after'],'stable':result['state_header_stable'],'nodes':len(nodes),'targets':[n for n in nodes if n['id'] in ['pltt','plmt','plpt','Fpos']],'properties':[x['key'] for x in result['profile_properties']],'errors':len(errors)},indent=2))
finally:K.CloseHandle(p)
