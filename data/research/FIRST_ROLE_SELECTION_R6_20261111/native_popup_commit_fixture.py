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
res={'status':'STARTED','source_sha256':hashlib.sha256(EXE.read_bytes()).hexdigest(),'never_resumed_main_thread':True,'user_process_touched':False,'cases':[],'boundary_doubles':['controlled actual MENU_ITEM/POPUP/PL/TYPE storage; original FB4980 getters and commit execute','native silent=1 excludes full UI event dispatcher; postcommit wrapper is common to both native silent modes','native epilogue boundary for controlled lifecycle changes and old-popup NOACCESS proof','callback current-popup lookup and small rolemap controlled; native getter and SYMBOL conversion retained'],'real_native':['FB4980 full original body/SEH and native MENU_ITEM F4C250 F5BDA0 selection commit','nativeTYPE bootstrap F5E080; POPUPslctFB61E0/SYMBOLF5BDA0','kernel32 VirtualProtect via original EXE IAT in private process only']}
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

 # Actual native MENU_ITEM -> SYMBOL -> POPUP commit. No newselection direct data assignment.
 popup=0x1200B400;replacement=0x1200E000;menu=0x1200D400;event=0x1200D700;eventvec=0x1200D780;eventprop=0x1200D7C0
 variant=0x1200D900;lookup=0x1200E800;callbackcount=0x1200E804;callback=0x1200C000;epilogue=0x1200C800
 call(0xF5E080,0x1200DA00);write(0x1B24238,pack(0x1200DA00))
 for pop in [popup,replacement]:
  write(pop,pack(0x167466C));write(pop+4,pack(profile));write(pop+0x10,pack(0x167465C));write(pop+0x30,pack(0x46706F73));write(pop+0x160,pack(0x46703031));write(pop+0x164,pack(event));write(pop+0x17E,b'\1')
 write(event,pack(0x166A12C)+pack(eventvec)+pack(1)+pack(4));write(eventvec,pack(eventprop))
 call(0xF5E800,variant,(0x6D626368,));write(eventprop,read(variant,8)+pack(0x65766964)+pack(0));call(0xF5BC90,variant)
 write(menu,pack(0x168DA44)+pack(0x166A12C)+pack(0x1200D500)+pack(1)+pack(4));write(0x1200D500,pack(0x1200D600))
 def menu_item(tag):
  call(0xF5E800,variant,(tag,));write(0x1200D600,read(variant,8)+pack(0x69642020)+pack(0));call(0xF5BC90,variant)
 # Callback native popup getter/decoder; popup lookup boundary is current pointer, never old this.
 def callback_for(setrole):
  z=bytearray(b'\x56\x57\x8B\xF1\xFF\x05'+pack(callbackcount)+b'\x83\xEC\x08\x8B\xCC')
  def cc(a):z.extend(b'\xE8'+pack(a-(callback+len(z)+5)))
  cc(0xF5E670);z.extend(b'\x8B\xC4\x50\x68'+pack(0x736C6374)+b'\x8B\x0D'+pack(lookup)+b'\x83\xC1\x10');cc(0xFB61E0);z.extend(b'\x8B\xCC');cc(0xF5BDA0)
  z.extend(b'\xBF'+pack(0)+b'\x3D'+pack(0x46703130)+b'\x75\x07\xBF'+pack(10)+b'\xEB\x1A'+b'\x3D'+pack(0x46703031)+b'\x75\x07\xBF'+pack(1)+b'\xEB\x0C'+b'\x3D'+pack(0x46703033)+b'\x75\x05\xBF'+pack(3))
  z.extend(b'\x57\x8B\xCE');cc(setrole);z.extend(b'\x8B\xCC');cc(0xF5BC90);z.extend(b'\x83\xC4\x08\x5F\x5E\xC3');write(callback,z)
 write(lookup,pack(popup));menu_item(0x46703130)
 oldr=R.parent/'ROLE_SELECTION_REPAINT_R5_20261111';old=json.loads((oldr/'position-payload.json').read_text())
 write(0x12020000,(oldr/'position-code.bin').read_bytes());write(state,(oldr/'position-data.bin').read_bytes());callback_for(old['SetRoleEntry']);write(state+40,pack(callback))
 call(old['BeginGenerationEntry'],profile);call(old['RegisterEntry'],args=(profile,table,label,13,5));call(old['SetRoleEntry'],profile,(1,))
 native_result=call(0xFB4980,popup,(menu,1))
 require(rd(popup+0x160)==0x46703130 and rd(state+12)==1 and rd(callbackcount)==0,'R5 actual native FB4980 commit Fp01toFp10 leaves oldRole1, regression reproduced')
 write(0x12020000,(R/'position-code.bin').read_bytes());write(state,(R/'position-data.bin').read_bytes());callback_for(P['SetRoleEntry']);write(state+40,pack(callback))
 original=read(0xFB4980,8);require(original==bytes.fromhex('6aff64a100000000'),'original actual popup8B SEH entry boundary')
 patch(0xFB4980,b'\xE9'+pack(P['PopupCommitEntry']-(0xFB4980+5))+b'\x90'*3)
 def ready(pr=profile):
  write(popup,pack(0x167466C));write(popup+4,pack(pr));write(popup+0x30,pack(0x46706F73));write(popup+0x160,pack(0x46703031));write(eventprop,pack(0x6D626368));write(lookup,pack(popup));write(callbackcount,pack(0));write(state,pack(1));write(state+40,pack(callback));begin();register(13);role(1)
 ready();got=call(0xFB4980,popup,(menu,1))
 res['first_R6_observation']={'selection':hex(rd(popup+0x160)),'role':rd(state+12),'count':rd(state+16),'callbacks':rd(callbackcount),'event':[hex(rd(event+k)) for k in range(0,16,4)],'prop':[hex(rd(eventprop+k)) for k in range(0,12,4)]};print(res['first_R6_observation'],flush=True)
 require(rd(popup+0x160)==0x46703130 and rd(state+12)==10 and rd(callbackcount)==1,'R6 actual first native Fp01toFp10 commit synchronizesRole10 without second event')
 require(got==native_result,'popup wrapper preserves actual nativeEAX return')
 for name,change in [('foreignowner',lambda:write(popup+4,pack(otherprofile))),('nonFpos',lambda:write(popup+0x30,pack(0x61747476))),('wrongclass',lambda:write(popup,pack(0x1675554))),('nonmbch',lambda:write(eventprop,pack(0x78787878))),('disabled',lambda:write(state,pack(0))),('callback0',lambda:write(state+40,pack(0)))]:
  ready();change();call(0xFB4980,popup,(menu,1));require(rd(popup+0x160)==0x46703130 and rd(callbackcount)==0 and rd(state+12)==1,'scope '+name+' delegates original native commit without background change')
 ready();write(state+64,pack(0));call(0xFB4980,popup,(menu,1))
 require(rd(state+16)==1 and rd(callbackcount)==0 and rd(state+12)==1,'positiveCount but all registry widgets dead does not synchronize')
 # Native epilogue boundary: emulate synchronous UI destruction/replacement AFTER actual commit.
 # Protect OLD popup page NOACCESS before returning to our wrapper. No old-popup read is allowed.
 native_epilogue=read(0xFB4BB5,5);assert native_epilogue==bytes.fromhex('8b4c242c5f')
 def protect_epilogue(invalidate=False,replace=False,switch=False,regenerate=False):
  z=bytearray(b'\x9C\x60')
  def cc(a):z.extend(b'\xE8'+pack(a-(epilogue+len(z)+5)))
  if invalidate:z.extend(b'\xB9'+pack(label));cc(P['InvalidateLabelEntry'])
  if replace:z.extend(b'\xC7\x05'+pack(lookup)+pack(replacement))
  if switch:z.extend(b'\xC7\x05'+pack(state+4)+pack(otherprofile))
  if regenerate:z.extend(b'\xFF\x05'+pack(state+8))
  z.extend(b'\x68'+pack(0x1200EF00)+b'\x6A\x01\x68'+pack(0x1000)+b'\x68'+pack(0x1200B000)+b'\xFF\x15'+pack(0x121A08C)+b'\x61\x9D'+native_epilogue)
  z.extend(b'\xE9'+pack(0xFB4BBA-(epilogue+len(z)+5)));write(epilogue,z);patch(0xFB4BB5,b'\xE9'+pack(epilogue-(0xFB4BB5+5)))
 def restore_popup_page():
  oldprot=W.DWORD();ck(K.VirtualProtectEx(p.hProcess,C.c_void_p(0x1200B000),0x1000,0x40,C.byref(oldprot)));assert oldprot.value==1
 for name,options,expect in [('all-dead',{'invalidate':True},0),('profile-switch',{'switch':True},0),('generation-change',{'regenerate':True},0),('replacement-current-popup',{'replace':True},1)]:
  ready();write(replacement+0x160,pack(0x46703033));protect_epilogue(**options)
  call(0xFB4980,popup,(menu,1));require(rd(callbackcount)==expect,'NOACCESS old popup after original '+name+' callback guard')
  if name=='replacement-current-popup':require(rd(state+12)==3,'replacement current Fpos read instead of old inaccessible popup')
  restore_popup_page();patch(0xFB4BB5,native_epilogue)
 # Repeated switches/actual commits plus OFF; test exact popup native path, not direct selected stores.
 for n in range(20):
  ready();call(0xFB4980,popup,(menu,1));assert rd(state+12)==10
 require(rd(callbackcount)==1,'20 actual native commits each apply first selection exactly once')
 menu_item(0x46706E30);ready();call(0xFB4980,popup,(menu,1));require(rd(state+12)==0,'native OFF commit removes role in same callback')
 menu_item(0x46703130);ready()
 # FP/SIMD preservation across actual native popup body + postcommit callback.
 fx=0x12030000;fx2=fx+0x200;entry=0x1200CC00;write(fx+0x800,bytes.fromhex('00112233445566778899aabbccddeeff'))
 stub=b'\xDB\xE3\xF3\x0F\x6F\x05'+pack(fx+0x800)+b'\x0F\xAE\x05'+pack(fx)+b'\x6A\x01\x68'+pack(menu)+b'\xB9'+pack(popup)+b'\xB8'+pack(0xFB4980)+b'\xFF\xD0\x0F\xAE\x05'+pack(fx2)+b'\xC3';write(entry,stub);call(entry)
 aa=read(fx,512);bb=read(fx2,512);require(aa[:28]==bb[:28] and aa[32:160]==bb[32:160] and aa[160:288]==bb[160:288],'actual popup native commit and callback preserve FP/SIMD')
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
