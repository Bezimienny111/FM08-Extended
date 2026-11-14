"""One bounded RPM capture of typed frontend HUMAN; no game control."""
import ctypes
from ctypes import wintypes as W
from datetime import datetime,timezone
import hashlib,json,struct,sys
from pathlib import Path
import pefile
from ui_context_reader import frontend_active_human

ROOT=Path(__file__).resolve().parent
BASELINE=ROOT/"captures/pre_confirm_8020_20261112T090331898196Z.json"
SHA="157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d"

def main():
    baseline=json.loads(BASELINE.read_text())
    pid=baseline["process"]["pid"]
    k=ctypes.WinDLL("kernel32",use_last_error=True)
    k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
    k.CloseHandle.argtypes=[W.HANDLE];k.CloseHandle.restype=W.BOOL
    k.ReadProcessMemory.argtypes=[W.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    k.ReadProcessMemory.restype=W.BOOL
    k.QueryFullProcessImageNameW.argtypes=[W.HANDLE,W.DWORD,W.LPWSTR,ctypes.POINTER(W.DWORD)];k.QueryFullProcessImageNameW.restype=W.BOOL
    k.GetProcessTimes.argtypes=[W.HANDLE,ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME)];k.GetProcessTimes.restype=W.BOOL
    h=k.OpenProcess(0x410,False,pid)
    if not h:raise ctypes.WinError(ctypes.get_last_error())
    reads=0;total=0
    def read(a,n):
        nonlocal reads,total
        if not 0x10000<=a<(1<<32) or not 1<=n<=4096 or a+n>(1<<32) or reads>=192 or total+n>8192:
            raise ValueError("bounded RPM guard")
        b=ctypes.create_string_buffer(n);got=ctypes.c_size_t()
        if not k.ReadProcessMemory(h,a,b,n,ctypes.byref(got)) or got.value!=n:
            raise ValueError("incomplete RPM")
        reads+=1;total+=n
        return b.raw
    def u32(a):return struct.unpack("<I",read(a,4))[0]
    try:
        ts=[W.FILETIME() for _ in range(4)]
        if not k.GetProcessTimes(h,*[ctypes.byref(t) for t in ts]):raise ctypes.WinError(ctypes.get_last_error())
        generation=(ts[0].dwHighDateTime<<32)|ts[0].dwLowDateTime
        if generation!=baseline["process"]["creation_filetime"]:raise ValueError("process generation changed")
        size=W.DWORD(32768);buf=ctypes.create_unicode_buffer(size.value)
        if not k.QueryFullProcessImageNameW(h,0,buf,ctypes.byref(size)):raise ctypes.WinError(ctypes.get_last_error())
        path=Path(buf.value);image=path.read_bytes()
        if path.name.lower()!="fm.exe" or hashlib.sha256(image).hexdigest()!=SHA:raise ValueError("EXE identity mismatch")
        pe=pefile.PE(data=image,fast_load=True)
        if pe.OPTIONAL_HEADER.ImageBase!=0x400000 or pe.OPTIONAL_HEADER.DllCharacteristics&0x40:raise ValueError("unsupported image mapping")
        if read(0x400000,64)!=image[:64]:raise ValueError("runtime image mapping mismatch")
        def file_u32(a):return struct.unpack_from("<I",image,pe.get_offset_from_rva(a-0x400000))[0]
        def class_name(a):
            vt=u32(a);col=file_u32(vt-4);td=file_u32(col+12)
            if file_u32(col)!=0 or file_u32(col+4)!=0:raise ValueError("not primary native class")
            off=pe.get_offset_from_rva(td+8-0x400000);end=image.index(0,off,off+256)
            return image[off:end].decode("ascii")
        def capture():
            if read(0x0191136A,1)!=b"\0":raise ValueError("remote/host mode")
            if u32(0x01BC1CB0)!=0x01671FE8:raise ValueError("screen-client manager class")
            cid=u32(0x01BC1C34);array=u32(0x01BC1CB8);vt=u32(array)
            if vt not in {0x01672024,0x01672074,0x016720B0,0x016721A4} or file_u32(vt+0x2C)!=0xF9A0D0:raise ValueError("screen-client array class")
            data,count=struct.unpack("<II",read(array+4,8))
            if not 1<=count<=16:raise ValueError("screen-client array bounds")
            clients=struct.unpack("<"+"I"*count,read(data,count*4))
            selected=[c for c in clients if u32(c+0x40)==cid]
            if len(selected)!=1 or u32(selected[0])!=0x012843A4:raise ValueError("active client identity")
            client=selected[0];connection=u32(client+0x64)
            if u32(connection)!=0x01672F38:raise ValueError("not local connection")
            screen=u32(client+0x44);screen_type=class_name(screen)
            if sys.argv[1:]==["--inspect-person-store"]:
                store=u32(0x01B1ECD0+0x38)
                try:
                    classname=class_name(store)
                except Exception as exc:
                    classname="UNVERIFIED: "+type(exc).__name__+": "+str(exc)
                ivt=u32(store+0x10)
                try:
                    getter=file_u32(ivt+0x2C)
                except Exception as exc:
                    getter="UNVERIFIED: "+type(exc).__name__+": "+str(exc)
                human={"status":"DIAGNOSTIC_ONLY_NOT_ADMITTED",
                    "database":0x01B1ECD0,"store":store,
                    "header_hex":read(store,0x20).hex(),
                    "first_dword":u32(store),"class_result":classname,
                    "inline_array_vtable":ivt,"inline_getter":getter}
            elif not sys.argv[1:]:
                human=frontend_active_human(read,file_u32,class_name)
            else:
                raise ValueError("unsupported diagnostic arguments")
            if u32(0x01BC1C34)!=cid or u32(client+0x44)!=screen:raise ValueError("active UI changed")
            return {"client":client,"client_id":cid,"screen":screen,"screen_class":screen_type,"human":human}
        first=capture();second=capture()
        participants=[t["core_team"]["uid"] for t in baseline["first"]["matches"]["controller_3c"]["teams"]]
        result={"source":"typed frontend HUMAN capture","captured_utc":datetime.now(timezone.utc).isoformat(),
            "process":{"pid":pid,"creation_filetime":generation,"exe":str(path),"sha256":SHA},
            "access":"RPM_ONLY_0x410","first":first,"second":second,"snapshots_equal":first==second,
            "baseline_participants":participants,"matches_saved_participant":first["human"].get("team_uid") in participants,
            "live_match_assumed":False,"read_calls":reads,"read_bytes":total}
        stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        dest=ROOT/"captures"/f"frontend_human_{pid}_{stamp}.json"
        with dest.open("x",encoding="utf-8") as f:json.dump(result,f,indent=2)
        print(json.dumps({"status":"CAPTURED","path":str(dest),"result":result}))
    except Exception as exc:
        failure={"status":"REJECTED","error_type":type(exc).__name__,"reason":str(exc),
            "pid":pid,"read_calls":reads,"read_bytes":total,"game_mutation":False}
        stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        dest=ROOT/"captures"/f"frontend_rejected_{pid}_{stamp}.json"
        with dest.open("x",encoding="utf-8") as f:json.dump(failure,f,indent=2)
        print(json.dumps({"path":str(dest),"result":failure}))
        raise
    finally:k.CloseHandle(h)
if __name__=="__main__":main()
