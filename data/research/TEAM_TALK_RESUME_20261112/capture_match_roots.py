"""Bounded RPM-only capture rooted in the active local MATCH_SCREEN.

No process enumeration, remote execution, writes, debugger, suspend or shutdown.
Captures diagnostic raw state; never publishes player reactions as ready.
"""
import argparse
import ctypes
from ctypes import wintypes as W
import hashlib
import json
from pathlib import Path
import struct
from datetime import datetime, timezone
import pefile
from ui_context_reader import active_human, ContextUnavailable

SOURCE_SHA = "157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d"
MANAGER = 0x01BC1CB0
CURRENT_ID = 0x01BC1C34
RUN_AS_SERVER = 0x0191136A
ARRAY_VTABLES = {0x01672024, 0x01672074, 0x016720B0, 0x016721A4}
ROOT_CLASSES = {MANAGER: 0x01671FE8}
SCREEN_CLIENT = 0x012843A4
MATCH_SCREEN = 0x0151860C
CONTROLLER = 0x01512134
MATCH = 0x015869B8
LOCAL_CONNECTION = 0x01672F38

class CaptureError(RuntimeError): pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", required=True, type=int)
    parser.add_argument("--baseline")
    parser.add_argument("--tag", required=True, choices=["pre_confirm","post_confirm","running_half","halftime","second_half","fulltime","diagnostic"])
    args = parser.parse_args()
    k=ctypes.WinDLL("kernel32",use_last_error=True)
    k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD]; k.OpenProcess.restype=W.HANDLE
    k.CloseHandle.argtypes=[W.HANDLE];k.CloseHandle.restype=W.BOOL
    k.ReadProcessMemory.argtypes=[W.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    k.ReadProcessMemory.restype=W.BOOL
    k.QueryFullProcessImageNameW.argtypes=[W.HANDLE,W.DWORD,W.LPWSTR,ctypes.POINTER(W.DWORD)]
    k.QueryFullProcessImageNameW.restype=W.BOOL
    k.GetProcessTimes.argtypes=[W.HANDLE,ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME)]
    k.GetProcessTimes.restype=W.BOOL
    handle=k.OpenProcess(0x410,False,args.pid)
    if not handle: raise ctypes.WinError(ctypes.get_last_error())
    reads=0; total=0
    def read(address,count):
        nonlocal reads,total
        if not 0x10000 <= address < (1<<32) or count<1 or count>4096 or address+count>(1<<32):
            raise CaptureError("read outside bounded x86 range")
        if reads>=768 or total+count>32768: raise CaptureError("capture budget exceeded")
        buf=ctypes.create_string_buffer(count);got=ctypes.c_size_t()
        if not k.ReadProcessMemory(handle,address,buf,count,ctypes.byref(got)) or got.value!=count:
            raise CaptureError("incomplete RPM at "+hex(address))
        reads+=1;total+=count
        return buf.raw
    def u32(address):return struct.unpack("<I",read(address,4))[0]
    def byte(address):return read(address,1)[0]
    try:
        size=W.DWORD(32768);pathbuf=ctypes.create_unicode_buffer(size.value)
        if not k.QueryFullProcessImageNameW(handle,0,pathbuf,ctypes.byref(size)):
            raise ctypes.WinError(ctypes.get_last_error())
        exe_path=Path(pathbuf.value)
        if exe_path.name.lower()!="fm.exe":raise CaptureError("target is not fm.exe")
        image=exe_path.read_bytes()
        if hashlib.sha256(image).hexdigest()!=SOURCE_SHA:raise CaptureError("unsupported executable hash")
        pe=pefile.PE(data=image,fast_load=True)
        if pe.OPTIONAL_HEADER.ImageBase!=0x400000:raise CaptureError("unsupported preferred image base")
        if pe.OPTIONAL_HEADER.DllCharacteristics & 0x40:raise CaptureError("ASLR profile not admitted")
        if read(0x400000,64)!=image[:64]:raise CaptureError("image mapping mismatch")
        times=[W.FILETIME() for _ in range(4)]
        if not k.GetProcessTimes(handle,*[ctypes.byref(t) for t in times]):raise ctypes.WinError(ctypes.get_last_error())
        creation=(times[0].dwHighDateTime<<32)|times[0].dwLowDateTime
        def file_u32(va):
            offset=pe.get_offset_from_rva(va-0x400000)
            return struct.unpack_from("<I",image,offset)[0]
        def object_info(address,expected=None,allow_secondary=False):
            vt=u32(address)
            if expected is not None and vt!=expected:raise CaptureError("unexpected vtable at "+hex(address)+": "+hex(vt))
            try:
                col=file_u32(vt-4)
                if file_u32(col)!=0 or (file_u32(col+4)!=0 and not allow_secondary):raise CaptureError("not an admitted MSVC class")
                td=file_u32(col+12)
                offset=pe.get_offset_from_rva(td+8-0x400000)
                end=image.index(0,offset,offset+256)
                name=image[offset:end].decode("ascii")
            except (ValueError,struct.error,pefile.PEFormatError) as exc:
                raise CaptureError("class metadata is not in verified image") from exc
            return {"address":address,"vtable":vt,"class":name,"col_offset":file_u32(col+4)}
        def match_info(address):
            obj=object_info(address,MATCH)
            block=read(address+0x5F2C8,0x68)
            get=lambda off:struct.unpack_from("<I",block,off-0x5F2C8)[0]
            obj.update({"tick":get(0x5F2FC),"phase":block[0x5F30C-0x5F2C8],
                "status":u32(address+0x5FC54),"match_view":get(0x5F2DC),
                "fixture_area_hex":read(address+0x5F298,0x30).hex(),
                "queue_count":struct.unpack("<h",read(address+0xC08,2))[0],
                "teams":[]})
            qarray=address+0xC00
            qvt=u32(qarray)
            if qvt not in {0x0150F218,0x0150F420,0x0150F5AC,0x015867A4,0x015868A0,0x01586914} or file_u32(qvt+0x2C)!=0x00913D30:
                raise CaptureError("unexpected embedded tactical queue")
            qdata=u32(qarray+4)
            qcount=obj["queue_count"]
            if not 0<=qcount<=4096:
                raise CaptureError("tactical queue count invalid")
            obj["queue_coverage"]={"total":qcount,"first_entries":min(qcount,32)}
            obj["queue_events"]=[]
            qptrs=struct.unpack("<"+"I"*min(qcount,32),read(qdata,min(qcount,32)*4)) if qcount else ()
            for event_address in qptrs:
                header=read(event_address,12)
                evt,timestamp,event_type,side=struct.unpack_from("<IIBb",header)
                event={"address":event_address,"vtable":evt,"timestamp":timestamp,"type":event_type,"side":side}
                if event_type==7:
                    if evt!=0x0150F700:
                        raise CaptureError("team-talk event class mismatch")
                    payload=read(event_address+0xC,0x34)
                    if struct.unpack_from("<I",payload)[0]!=0x0150F6E0:
                        raise CaptureError("event TEAM_TALK payload class mismatch")
                    evt_array=struct.unpack_from("<I",payload,8)[0]
                    evt_data=struct.unpack_from("<I",payload,0xC)[0]
                    evt_count=payload[0x10]
                    if evt_array not in {0x0150F338,0x0150F3E4,0x0150F5E4,0x0150F698} or file_u32(evt_array+0x2C)!=0x0050E1A0 or evt_count>64:
                        raise CaptureError("event entry array layout mismatch")
                    event["payload_phase"]=payload[0x30]
                    event["raw_identity_2c"]=struct.unpack_from("<I",payload,0x2C)[0]
                    event["entry_count"]=evt_count
                    event["entries"]=[]
                    pointers=struct.unpack("<"+"I"*evt_count,read(evt_data,evt_count*4)) if evt_count else ()
                    for ep in pointers:
                        raw=read(ep,0x2B)
                        if struct.unpack_from("<I",raw)[0]!=0x01588780:
                            raise CaptureError("event player-entry class mismatch")
                        action,effect,context=struct.unpack_from("<QQQ",raw,0x10)
                        event["entries"].append({"uid":struct.unpack_from("<I",raw,8)[0],
                            "action":action,"effect":effect,"context":context})
                obj["queue_events"].append(event)
            for team_address in (get(0x5F2D4),get(0x5F2D8)):
                team=object_info(team_address)
                if team["class"] != ".?AVGAME_MATCH_TEAM@@":
                    raise CaptureError("unexpected match team")
                core_address = u32(team_address + 0x59C)
                core = object_info(core_address)
                if core["class"] != ".?AVTEAM@@":
                    raise CaptureError("unexpected core TEAM")
                core["uid"] = u32(core_address + 0x18)
                team["core_team"] = core
                manager_address = u32(team_address + 0x530)
                manager = object_info(manager_address)
                if manager["class"] != ".?AVGAME_MATCH_MANAGER@@":
                    raise CaptureError("unexpected match manager")
                manager.update({"raw_identity_0c":u32(manager_address+0xC),
                    "match_backlink":u32(manager_address+0x74),
                    "team_backlink":u32(manager_address+0x78),
                    "control_flags":u32(manager_address+0xA40),
                    "talk_counter":u32(manager_address+0xB04)})
                if manager["match_backlink"] != address or manager["team_backlink"] != team_address:
                    raise CaptureError("match manager backlinks mismatch")
                array_address = manager_address+0xAF4
                array = {"address":array_address, "vtable":u32(array_address),
                         "layout_status":"UNVERIFIED_NO_TRAVERSAL"}
                array["header_hex"] = read(array_address,16).hex()
                array["getter"] = file_u32(array["vtable"]+0x2C)
                getter_offset = pe.get_offset_from_rva(array["getter"]-0x400000)
                array["getter_code_32_hex"] = image[getter_offset:getter_offset+32].hex()
                if array["vtable"] != 0x015102C8 or array["getter"] != 0x00F9A0D0:
                    raise CaptureError("unverified TEAM_TALK_HISTORY")
                data, count = struct.unpack("<II", read(array_address+4,8))
                if not 0 <= manager["talk_counter"] <= count <= 5:
                    raise CaptureError("talk history/count bounds")
                array["layout_status"] = "INLINE_NATIVE_GETTER_VERIFIED"
                index = max(0,manager["talk_counter"]-1)
                talk_address = u32(data+index*4)
                talk = object_info(talk_address,0x0150F6E0)
                header=read(talk_address,0x34)
                entry_vtable=struct.unpack_from("<I",header,8)[0]
                entry_data=struct.unpack_from("<I",header,0xC)[0]
                entry_count=header[0x10]
                if entry_vtable not in {0x0150F338,0x0150F3E4,0x0150F5E4,0x0150F698}:
                    raise CaptureError("unexpected embedded player-entry array")
                if file_u32(entry_vtable+0x2C)!=0x0050E1A0 or entry_count>64:
                    raise CaptureError("unexpected entry getter/count")
                talk.update({"slot":index,"executed_slot":manager["talk_counter"]>0,
                    "phase":header[0x30],"raw_identity_2c":struct.unpack_from("<I",header,0x2C)[0],
                    "entry_count":entry_count,"entries":[]})
                pointers=struct.unpack("<"+"I"*entry_count,read(entry_data,entry_count*4)) if entry_count else ()
                for entry_address in pointers:
                    raw=read(entry_address,0x2B)
                    if struct.unpack_from("<I",raw)[0]!=0x01588780:
                        raise CaptureError("unexpected PLAYER_TEAM_TALK_ENTRY")
                    uid=struct.unpack_from("<I",raw,8)[0]
                    action,effect,context=struct.unpack_from("<QQQ",raw,0x10)
                    talk["entries"].append({"address":entry_address,"uid":uid,
                        "action":action,"effect":effect,"context":context,
                        "position":struct.unpack_from("<h",raw,0x28)[0],"index":raw[0x2A]})
                manager["talk_array"] = array
                manager["last_or_staged_talk"] = talk
                team["manager"] = manager
                obj["teams"].append(team)
            return obj
        def snapshot():
            if byte(RUN_AS_SERVER)!=0:raise CaptureError("hosting/remote mode not admitted")
            object_info(MANAGER,0x01671FE8)
            current=u32(CURRENT_ID)
            if current==0:raise CaptureError("no current screen client")
            array=u32(MANAGER+8);vt=u32(array)
            if vt not in ARRAY_VTABLES:raise CaptureError("unsupported screen-client array "+hex(vt))
            if file_u32(vt+0x2C)!=0xF9A0D0:raise CaptureError("unexpected native array getter")
            raw=read(array+4,8);data,count=struct.unpack("<II",raw)
            if not 1<=count<=16:raise CaptureError("screen-client count out of bounds")
            items=struct.unpack("<"+"I"*count,read(data,count*4))
            matches=[p for p in items if u32(p+0x40)==current]
            if len(matches)!=1:raise CaptureError("ambiguous current screen client")
            client=object_info(matches[0],SCREEN_CLIENT)
            local=u32(matches[0]+0x64)
            object_info(local,LOCAL_CONNECTION)
            screen_address=u32(matches[0]+0x44)
            screen=object_info(screen_address,MATCH_SCREEN)
            controller_address=u32(screen_address+0x2A0)
            controller=object_info(controller_address,CONTROLLER)
            if u32(controller_address+0x2700)!=screen_address:raise CaptureError("controller/screen backlink mismatch")
            controller.update({"screen_backlink":screen_address,
                "screen_stage_mask":u32(controller_address+0x2620),
                "controlled_side":byte(controller_address+0x29D2),
                "view_cursor":u32(controller_address+0x394),
                "live_flag_raw":byte(controller_address+0x2643)})
            slots={"controller_3c":u32(controller_address+0x3C),
                   "controller_2648":u32(controller_address+0x2648),
                   "screen_2a4":u32(screen_address+0x2A4)}
            roots={}
            match_cache={}
            for slot,address in slots.items():
                if address and address not in match_cache:
                    match_cache[address]=match_info(address)
                roots[slot]=None if not address else match_cache[address]
            try:
                human_context=active_human(read,file_u32,screen_address,
                    lambda p:object_info(p)["class"])
                own_sides=[i for i,t in enumerate(roots["controller_3c"]["teams"])
                           if t["core_team"]["address"]==human_context["team"]]
                if len(own_sides)!=1:
                    raise ContextUnavailable("active human team not uniquely in this match")
                human_context["own_side"]=own_sides[0]
                human_context["control_flag_human"]=bool(roots["controller_3c"]["teams"][own_sides[0]]["manager"]["control_flags"]&1)
                if not human_context["control_flag_human"]:
                    raise ContextUnavailable("active human club not manually controlled")
            except ContextUnavailable as exc:
                human_context={"status":"UNVERIFIED","reason":str(exc)}
            # Revalidate root chain before returning a snapshot.
            if u32(CURRENT_ID)!=current or u32(client["address"]+0x44)!=screen_address or u32(screen_address+0x2A0)!=controller_address:
                raise CaptureError("UI changed during capture")
            return {"current_client_id":current,"client":client,"screen":screen,
                "controller":controller,"active_human":human_context,"match_slots":slots,"matches":roots,
                "scratch_screen":u32(0x01B24260)}
        baseline=json.loads(Path(args.baseline).read_text()) if args.baseline else None
        if args.tag!="pre_confirm" and baseline is None:
            raise CaptureError("post-talk capture requires a pinned baseline")
        if baseline and (baseline["process"]["pid"]!=args.pid or baseline["process"]["creation_filetime"]!=creation):
            raise CaptureError("process generation differs from baseline")
        first=snapshot()
        second=snapshot()
        baseline_compare=None
        if baseline:
            b=baseline["first"];m=first["matches"]["controller_3c"];bm=b["matches"]["controller_3c"]
            baseline_compare={"same_client":first["client"]["address"]==b["client"]["address"],
                "same_screen":first["screen"]["address"]==b["screen"]["address"],
                "same_controller":first["controller"]["address"]==b["controller"]["address"],
                "same_match":m["address"]==bm["address"],
                "same_team_uids":[t["core_team"]["uid"] for t in m["teams"]]==[t["core_team"]["uid"] for t in bm["teams"]],
                "previous_tick":bm["tick"],"current_tick":m["tick"]}
        result={"tag":args.tag,"captured_utc":datetime.now(timezone.utc).isoformat(),
            "process":{"pid":args.pid,"creation_filetime":creation,"exe":str(exe_path),"sha256":SOURCE_SHA},
            "access":"RPM_ONLY_0x410","publication_ready":False,
            "capture_tool_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "native_completion_gate":"UNVERIFIED","native_edit_lock_gate":"UNVERIFIED",
            "snapshots_equal":first==second,"baseline_comparison":baseline_compare,"first":first,"second":second,
            "read_calls":reads,"read_bytes":total}
        output=Path(__file__).resolve().parent/"captures"
        output.mkdir(exist_ok=True)
        stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        target=output/f"{args.tag}_{args.pid}_{stamp}.json"
        with target.open("x",encoding="utf-8") as f:json.dump(result,f,indent=2)
        print(json.dumps({"status":"CAPTURED","path":str(target),"pid":args.pid,
                          "creation_filetime":creation,"snapshots_equal":first==second,
                          "root":first,"read_bytes":total}))
    finally:
        k.CloseHandle(handle)

if __name__=="__main__":
    main()

