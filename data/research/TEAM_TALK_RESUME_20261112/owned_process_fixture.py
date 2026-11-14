"""Owned-process RPM test. Never accepts or enumerates an external PID.

This validates memory transport and entry decoding on a synthetic Python child.
It does NOT run FM, replay native match code, or prove either publication gate.
"""
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import struct
import subprocess
import sys
from team_talk_model import ENTRY_BYTES, InvalidRead, read_stable_entry, decode_effect

VTABLE = 0x01588780
UID = 8074

def kernel_api():
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.VirtualAlloc.argtypes = [ctypes.c_void_p, ctypes.c_size_t, wintypes.DWORD, wintypes.DWORD]
    k.VirtualAlloc.restype = ctypes.c_void_p
    k.VirtualFree.argtypes = [ctypes.c_void_p, ctypes.c_size_t, wintypes.DWORD]
    k.VirtualFree.restype = wintypes.BOOL
    k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k.OpenProcess.restype = wintypes.HANDLE
    k.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                   ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    k.ReadProcessMemory.restype = wintypes.BOOL
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    k.CloseHandle.restype = wintypes.BOOL
    return k

def child():
    k = kernel_api()
    address = None
    for candidate in (0x20000000, 0x28000000, 0x30000000):
        address = k.VirtualAlloc(candidate, 0x1000, 0x3000, 0x04)
        if address:
            break
    if not address or address >= 1 << 32:
        raise RuntimeError("fixture could not allocate a low x86 address")
    def write(effect, uid=UID, vtable=VTABLE):
        raw = bytearray(ENTRY_BYTES)
        struct.pack_into("<I", raw, 0, vtable)
        struct.pack_into("<I", raw, 8, uid)
        struct.pack_into("<QQQhB", raw, 0x10, 0x8000, effect, 0xFEDCBA9876543210, -1, 0x7F)
        ctypes.memmove(address, bytes(raw), len(raw))  # self-owned child buffer only
    write(1)
    print(json.dumps({"kind": "owned_team_talk_fixture", "address": address, "uid": UID}), flush=True)
    try:
        for line in sys.stdin:
            command = json.loads(line)
            if command["op"] == "exit":
                break
            if command["op"] != "set":
                raise ValueError("unsupported fixture command")
            write(command["effect"], command.get("uid", UID), command.get("vtable", VTABLE))
            print("ok", flush=True)
    finally:
        k.VirtualFree(address, 0, 0x8000)

class OwnedMemory:
    def __init__(self, kernel, handle):
        self.kernel, self.handle = kernel, handle
        self.reads = 0
    def read(self, address, count):
        if count != ENTRY_BYTES:
            raise ValueError("fixture reader admits one entry only")
        buffer = ctypes.create_string_buffer(count)
        read = ctypes.c_size_t()
        ok = self.kernel.ReadProcessMemory(self.handle, address, buffer, count, ctypes.byref(read))
        if not ok or read.value != count:
            raise InvalidRead("incomplete RPM")
        self.reads += 1
        return buffer.raw

def parent():
    k = kernel_api()
    script = str(Path(__file__).resolve())
    proc = subprocess.Popen([sys.executable, "-B", script, "--owned-child"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, creationflags=0x08000000)
    handle = None
    passed = []
    try:
        hello = json.loads(proc.stdout.readline())
        assert hello["kind"] == "owned_team_talk_fixture"
        # The PID is exclusively the Popen child just created here.
        handle = k.OpenProcess(0x410, False, proc.pid)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        memory = OwnedMemory(k, handle)
        def read():
            return read_stable_entry(memory, hello["address"], UID, frozenset({VTABLE}))
        def command(**fields):
            proc.stdin.write(json.dumps({"op": "set", **fields}) + "\n")
            proc.stdin.flush()
            assert proc.stdout.readline().strip() == "ok"
        assert read().effect == 1
        passed.append("owned_child_readonly_rpm")
        command(effect=1 | 0x400 | 0x10000)
        assert decode_effect(read().effect).names == ("motivate", "unhappy", "ignore")
        passed.append("mixed_reaction_preserved")
        command(effect=1 << 63)
        assert decode_effect(read().effect).unknown_bits == 1 << 63
        passed.append("unknown_high_bits_retained")
        command(effect=0)
        assert read().effect == 0
        passed.append("zero_entry_distinct_from_missing")
        command(effect=1, uid=111)
        try:
            read()
        except InvalidRead:
            passed.append("identity_mismatch_rejected")
        else:
            raise AssertionError("foreign UID accepted")
        command(effect=1, uid=UID, vtable=0)
        try:
            read()
        except InvalidRead:
            passed.append("class_mismatch_rejected")
        else:
            raise AssertionError("foreign class accepted")
        print(json.dumps({"status": "PASS", "cases": passed, "rpm_reads": memory.reads,
                          "target": "synthetic_owned_python_child",
                          "game_process_access": False, "cross_process_writes": False,
                          "native_match_validation": False}))
    finally:
        if handle:
            k.CloseHandle(handle)
        if proc.poll() is None:
            try:
                proc.stdin.write('{"op":"exit"}\n')
                proc.stdin.flush()
                proc.wait(timeout=5)
            except (BrokenPipeError, subprocess.TimeoutExpired):
                proc.terminate()  # only the Popen fixture owned by this invocation
                proc.wait(timeout=5)
        if proc.returncode:
            error = proc.stderr.read()
            raise RuntimeError("fixture child failed: " + error)

if __name__ == "__main__":
    if sys.argv[1:] == ["--owned-child"]:
        child()
    elif not sys.argv[1:]:
        parent()
    else:
        raise SystemExit("No external process or PID arguments are accepted")
