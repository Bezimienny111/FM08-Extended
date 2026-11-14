// Isolated Poland level-three pilot. Memory-only hook; default mode never starts FM08.
// Build with .NET Framework csc /platform:x86. No reference to the main launcher assembly.
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Threading;

public static class PolandThirdTierPilotR8
{
    public const string ExpectedHash = "157F484BE2EAD4AB27006D1002C2C666A7228197B88B14C8D026E76F31B1D62D";
    public const uint HookAddress = 0x00E8EA41;
    public const uint AllocatorAddress = 0x00C933F0;
    public const uint ConstructorAddress = 0x00D805B0;
    public const uint CompetitionUid = 1800001000;
    public static readonly byte[] OriginalTail = { 0x5E, 0x59, 0xC3, 0xCC, 0xCC };
    // State: status, calls, object, collection, count-before, count-after, UID, reserved.
    // Status 1=added, 2=invalid collection, 3=allocation failed, 4=constructor null,
    // 5=append did not produce six entries, 6=already six (no allocation).
    const int StateSize = 32;

    public static int Main(string[] args)
    {
        try
        {
            Require(IntPtr.Size == 4, "Compile and run this tool as x86.");
            if (args.Length == 0 || (args[0] == "--verify" && args.Length <= 2))
            {
                if (args.Length == 2) VerifyExe(Path.GetFullPath(args[1]));
                VerifyNativeAbi();
                Console.WriteLine("VERIFIED: x86 ABI, 5->6 append, preserved original entries/registers/flags/stack, guard paths. No FM08 process started.");
                return 0;
            }
            if (args.Length == 2 && args[0] == "--verify-runtime")
            {
                var root = Path.GetFullPath(args[1]); VerifyRuntime(root);
                Console.WriteLine("VERIFIED: isolated R8 runtime/manifest/database layout. No FM08 process started."); return 0;
            }
            if (args.Length == 2 && args[0] == "--launch") return Launch(Path.GetFullPath(args[1]));
            Console.Error.WriteLine("Usage: PolandThirdTierPilotR8.exe [--verify [original-fm.exe] | --verify-runtime <runtime-root> | --launch <runtime-root>]");
            return 2;
        }
        catch (Exception ex) { Console.Error.WriteLine(ex.ToString()); return 1; }
    }

    public static byte[] BuildStub(uint address, uint state, uint allocator, uint constructor, uint uid)
    {
        var a = new X86(address);
        a.E(0x9C, 0x60); // preserve flags and all GPRs; original saved ESI/local ECX remain underneath.
        a.E(0xF0, 0xFF, 0x05); a.U(state + 4);
        a.StoreImm(state, 0); a.StoreImm(state + 24, uid);
        a.E(0x89, 0x35); a.U(state + 12); // collection = ESI
        a.E(0x85, 0xF6); a.Jcc(0x84, "bad");
        a.E(0x0F, 0xB6, 0x46, 0x08); a.StoreEax(state + 16); a.StoreEax(state + 20);
        a.E(0x83, 0xF8, 0x06); a.Jcc(0x84, "already");
        a.E(0x83, 0xF8, 0x05); a.Jcc(0x85, "bad");
        a.E(0x8B, 0x16, 0x85, 0xD2); a.Jcc(0x84, "bad");
        a.E(0x83, 0x3A, 0x00); a.Jcc(0x84, "bad");
        a.E(0x68); a.U(0x240); a.Call(allocator); a.E(0x83, 0xC4, 0x04);
        a.E(0x85, 0xC0); a.Jcc(0x84, "alloc_failed");
        a.E(0x8B, 0xC8, 0x6A, 0x01, 0x6A, 0x01, 0x68); a.U(uid);
        a.Call(constructor); // ECX=this; callee removes UID/type/flag (ret 0x0c).
        a.E(0x85, 0xC0); a.Jcc(0x84, "ctor_failed");
        a.StoreEax(state + 8);
        a.E(0xC6, 0x80); a.U(0xF4); a.E(0x02); // division level 2 (third tier)
        a.E(0xC6, 0x80); a.U(0xE9); a.E(0x01); // league competition type
        // Collection.Add(&localObject); same thiscall convention as the five native objects.
        a.E(0x50, 0x8D, 0x04, 0x24, 0x8B, 0x16, 0x8B, 0xCE, 0x50, 0xFF, 0x12, 0x83, 0xC4, 0x04);
        a.E(0x0F, 0xB6, 0x46, 0x08); a.StoreEax(state + 20);
        a.E(0x83, 0xF8, 0x06); a.Jcc(0x85, "append_failed");
        a.StoreImm(state, 1); a.Jmp("done");
        a.Label("bad"); a.StoreImm(state, 2); a.Jmp("done");
        a.Label("alloc_failed"); a.StoreImm(state, 3); a.Jmp("done");
        a.Label("ctor_failed"); a.StoreImm(state, 4); a.Jmp("done");
        a.Label("append_failed"); a.StoreImm(state, 5); a.Jmp("done");
        a.Label("already"); a.StoreImm(state, 6);
        a.Label("done"); a.E(0x61, 0x9D, 0x5E, 0x59, 0xC3); // native epilogue, unchanged return convention
        return a.Finish();
    }

    public static byte[] EntryJump(uint destination)
    {
        var a = new X86(HookAddress); a.E(0xE9); a.U(unchecked(destination - HookAddress - 5)); return a.Finish();
    }

    static void VerifyExe(string path)
    {
        using (var f = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read))
        {
            using (var sha = SHA256.Create()) Require(Hex(sha.ComputeHash(f)) == ExpectedHash, "Unsupported executable hash: " + path);
            Require(f.Length == 22242560, "Unexpected executable size.");
            f.Position = HookAddress - 0x400000;
            var tail = new byte[OriginalTail.Length]; Require(f.Read(tail, 0, tail.Length) == tail.Length && Equal(tail, OriginalTail), "Original setup tail differs.");
            f.Position = 0xD8095D - 0x400000; Require(f.ReadByte() == 0xC2 && f.ReadByte() == 0x0C && f.ReadByte() == 0, "Constructor no longer returns with ret 0x0c.");
        }
    }

    public static string VerifyRuntime(string root)
    {
        var runtime = new DirectoryInfo(Path.GetFullPath(root));
        Require(string.Equals(runtime.Name, "runtime", StringComparison.OrdinalIgnoreCase) && runtime.Parent != null,
            "Use the isolated R8 runtime directory, not the original game directory.");
        var pilotRoot = runtime.Parent.FullName;
        var manifestPath = Path.Combine(pilotRoot, "manifest.json");
        Require(File.Exists(manifestPath), "Parent R8 manifest missing.");
        var manifest = File.ReadAllText(manifestPath);
        Require(System.Text.RegularExpressions.Regex.IsMatch(manifest, "\"revision\"\\s*:\\s*\"R8\""), "Manifest revision is not R8.");
        Require(System.Text.RegularExpressions.Regex.IsMatch(manifest, "\"new_competition_uid_candidate\"\\s*:\\s*1800001000(?=\\s*[,}])"), "Unexpected pilot competition UID.");
        var db = Path.Combine(pilotRoot, "user-data", "db", "TEST_POL_3_LEVEL_R8");
        foreach (var name in new[] { "server_db.dat", "client_db.dat", "lang_db.dat", "people_db.dat", "TEST_POL_3_LEVEL_R8.xml" })
            Require(File.Exists(Path.Combine(db, name)), "Pilot database file missing: " + name);
        Require(Directory.Exists(Path.Combine(root, "data")), "Runtime data directory missing.");
        VerifyExe(Path.Combine(root, "fm.exe"));
        return pilotRoot;
    }

    static int Launch(string root)
    {
        var pilotRoot = VerifyRuntime(root);
        var exe = Path.Combine(root, "fm.exe");
        // Only prevent another start; never attach to or terminate an existing FM08 process.
        var candidates = Process.GetProcessesByName("fm");
        try { foreach (var p in candidates) Require(p.HasExited, "An FM08 process is already running. Close it before starting the isolated pilot."); }
        finally { foreach (var p in candidates) p.Dispose(); }
        var userData = Path.Combine(pilotRoot, "user-data");
        var logDir = Path.Combine(pilotRoot, "pilot-logs"); Directory.CreateDirectory(logDir);
        var logPath = Path.Combine(logDir, "pilot-" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff") + ".jsonl");
        using (var sourceLock = new FileStream(exe, FileMode.Open, FileAccess.Read, FileShare.Read))
        using (var log = new StreamWriter(new FileStream(logPath, FileMode.CreateNew, FileAccess.Write, FileShare.Read), new UTF8Encoding(false)))
        {
            // Recheck after the non-writable/non-delete share lock is held, before creating the process.
            VerifyExe(exe);
            log.AutoFlush = true;
            var startup = new StartupInfo(); startup.Size = Marshal.SizeOf(typeof(StartupInfo));
            ProcessInformation pi;
            var command = new StringBuilder(Quote(exe) + " --user_data_location=" + Quote(userData) + " --windowed --small_screen");
            Check(CreateProcess(exe, command, IntPtr.Zero, IntPtr.Zero, false, 4, IntPtr.Zero, root, ref startup, out pi), "CreateProcess suspended");
            bool resumed = false;
            try
            {
                Require(Equal(Read(pi.Process, HookAddress, OriginalTail.Length), OriginalTail), "Unexpected original tail in private process memory.");
                var statePtr = VirtualAllocEx(pi.Process, IntPtr.Zero, (UIntPtr)4096, 0x3000, 4); Check(statePtr != IntPtr.Zero, "VirtualAllocEx state");
                var stubPtr = VirtualAllocEx(pi.Process, IntPtr.Zero, (UIntPtr)4096, 0x3000, 4); Check(stubPtr != IntPtr.Zero, "VirtualAllocEx stub");
                uint state = Address(statePtr), stub = Address(stubPtr);
                Write(pi.Process, state, new byte[StateSize]);
                var code = BuildStub(stub, state, AllocatorAddress, ConstructorAddress, CompetitionUid);
                Require(code.Length <= 4096, "Stub exceeds allocated page."); Write(pi.Process, stub, code);
                uint old; Check(VirtualProtectEx(pi.Process, stubPtr, (UIntPtr)4096, 0x20, out old), "Protect stub RX");
                Check(FlushInstructionCache(pi.Process, stubPtr, (UIntPtr)code.Length), "Flush stub");
                uint siteProtection; Check(VirtualProtectEx(pi.Process, Pointer(HookAddress), (UIntPtr)5, 0x40, out siteProtection), "Protect original tail");
                try { Write(pi.Process, HookAddress, EntryJump(stub)); }
                finally { uint ignored; Check(VirtualProtectEx(pi.Process, Pointer(HookAddress), (UIntPtr)5, siteProtection, out ignored), "Restore tail protection"); }
                Check(FlushInstructionCache(pi.Process, Pointer(HookAddress), (UIntPtr)5), "Flush tail");
                log.WriteLine("{\"event\":\"installed\",\"process_id\":" + pi.ProcessId + ",\"uid\":" + CompetitionUid + ",\"state\":\"0x" + state.ToString("X8") + "\",\"hook\":\"0x00E8EA41\",\"exe_sha256\":\"" + ExpectedHash + "\"}");
                Require(ResumeThread(pi.Thread) == 1, "ResumeThread did not report one suspended state."); resumed = true;
                Console.WriteLine("Pilot started, PID=" + pi.ProcessId + ". Log=" + logPath);
                Console.WriteLine("Only this new process has the hook. Keep this console open to collect state; closing it does not stop FM08.");
                string previous = null;
                while (true)
                {
                    uint wait = WaitForSingleObject(pi.Process, 0);
                    if (wait == 0) break;
                    Require(wait == 0x102, "Unexpected process wait result: " + wait);
                    byte[] bytes;
                    try { bytes = Read(pi.Process, state, StateSize); }
                    catch (Win32Exception) { if (WaitForSingleObject(pi.Process, 0) == 0) break; throw; }
                    var line = "{\"event\":\"state\",\"utc\":\"" + DateTime.UtcNow.ToString("o") + "\",\"status\":" + Get(bytes, 0) + ",\"calls\":" + Get(bytes, 4) + ",\"object\":\"0x" + Get(bytes, 8).ToString("X8") + "\",\"collection\":\"0x" + Get(bytes, 12).ToString("X8") + "\",\"before\":" + Get(bytes, 16) + ",\"after\":" + Get(bytes, 20) + ",\"uid\":" + Get(bytes, 24) + "}";
                    var signature = Hex(bytes);
                    if (signature != previous) { log.WriteLine(line); Console.WriteLine(line); previous = signature; }
                    Thread.Sleep(500);
                }
                uint exit; Check(GetExitCodeProcess(pi.Process, out exit), "GetExitCodeProcess"); log.WriteLine("{\"event\":\"exited\",\"code\":" + exit + "}");
                Console.WriteLine("FM08 exited: " + exit); return unchecked((int)exit);
            }
            finally
            {
                try
                {
                    if (!resumed && WaitForSingleObject(pi.Process, 0) == 0x102)
                    {
                        Check(TerminateProcess(pi.Process, 1), "Terminate only the owned suspended process");
                        Require(WaitForSingleObject(pi.Process, 5000) == 0, "Owned process cleanup timed out.");
                    }
                }
                finally { CloseHandle(pi.Thread); CloseHandle(pi.Process); }
            }
        }
    }

    // Execute the actual emitted x86 stub in this process, against small native fakes.
    // This validates ABI/guards without loading or executing FM08.
    public static void VerifyNativeAbi()
    {
        IntPtr allocation = VirtualAlloc(IntPtr.Zero, (UIntPtr)0x4000, 0x3000, 0x40); Check(allocation != IntPtr.Zero, "VirtualAlloc fixture");
        try
        {
            uint b = Address(allocation), stub = b, alloc = b + 0x1000, ctor = b + 0x1100, append = b + 0x1200, wrapper = b + 0x1300;
            uint vt = b + 0x2000, collection = b + 0x2100, obj = b + 0x2400, state = b + 0x2800, capture = b + 0x2900, fake = b + 0x2A00;
            Copy(stub, BuildStub(stub, state, alloc, ctor, CompetitionUid));
            var a = new X86(alloc);
            a.E(0x8B, 0x44, 0x24, 0x04); a.StoreEax(fake + 8); a.E(0xFF, 0x05); a.U(fake + 12); a.E(0xA1); a.U(fake); a.E(0xC3); Copy(alloc, a.Finish());
            a = new X86(ctor);
            a.E(0x89, 0x0D); a.U(fake + 16);
            for (byte i = 0; i < 3; i++) { a.E(0x8B, 0x44, 0x24, (byte)(4 + i * 4)); a.StoreEax(fake + 20 + (uint)i * 4); }
            a.E(0xFF, 0x05); a.U(fake + 32); a.E(0xA1); a.U(fake + 4); a.E(0xC2, 0x0C, 0x00); Copy(ctor, a.Finish());
            a = new X86(append);
            a.E(0x83, 0x3D); a.U(fake + 36); a.E(0); a.Jcc(0x85, "no_append");
            a.E(0x8B, 0x54, 0x24, 0x04, 0x8B, 0x02, 0x0F, 0xB6, 0x51, 0x08, 0x89, 0x44, 0x91, 0x10, 0xFE, 0x41, 0x08);
            a.Label("no_append"); a.E(0xC2, 0x04, 0x00); Copy(append, a.Finish());
            a = new X86(wrapper);
            a.E(0x55, 0x8B, 0xEC, 0x53, 0x56, 0x57, 0x89, 0x25); a.U(capture); a.E(0x89, 0x2D); a.U(capture + 4);
            a.E(0x68); a.AbsLabel("returned"); a.E(0x68); a.U(0x55667788); a.E(0x68); a.U(0x11223344);
            a.E(0x8B, 0x75, 0x08, 0xB8); a.U(0x7FA0B123); a.E(0xB9); a.U(0xCAFEBABE); a.E(0xBA); a.U(0x1122ABCD);
            a.E(0xBB); a.U(0xDDEEFF11); a.E(0xBF); a.U(0x99AABBCC); a.E(0x68); a.U(0x246); a.E(0x9D); a.Jmp(stub);
            a.Label("returned");
            a.StoreEax(capture + 8); a.E(0x89, 0x0D); a.U(capture + 12); a.E(0x89, 0x15); a.U(capture + 16);
            a.E(0x89, 0x1D); a.U(capture + 20); a.E(0x89, 0x35); a.U(capture + 24); a.E(0x89, 0x3D); a.U(capture + 28);
            a.E(0x89, 0x25); a.U(capture + 32); a.E(0x89, 0x2D); a.U(capture + 36); a.E(0x9C, 0x58); a.StoreEax(capture + 40);
            a.E(0xB8); a.U(1); a.E(0x5F, 0x5E, 0x5B, 0x5D, 0xC2, 0x04, 0x00); Copy(wrapper, a.Finish());
            Check(FlushInstructionCache(GetCurrentProcess(), allocation, (UIntPtr)0x4000), "Flush fixture");
            var run = (FixtureEntry)Marshal.GetDelegateForFunctionPointer(Pointer(wrapper), typeof(FixtureEntry));
            Put(vt, append);
            for (int scenario = 0; scenario < 7; scenario++)
            {
                Copy(state, new byte[StateSize]); Copy(fake, new byte[64]); Copy(collection, new byte[128]); Copy(obj, new byte[0x240]);
                Put(collection, vt); Marshal.WriteByte(Pointer(collection + 8), scenario == 2 ? (byte)4 : (byte)5);
                for (uint j = 0; j < 5; j++) Put(collection + 0x10 + 4 * j, 0xAABB0000 + j);
                Put(fake, scenario == 4 ? 0 : obj); Put(fake + 4, scenario == 5 ? 0 : obj);
                if (scenario == 3) Put(collection, 0);
                if (scenario == 6) Put(fake + 36, 1);
                Require(run(scenario == 1 ? IntPtr.Zero : Pointer(collection)) == 1, "Wrapper return.");
                CheckCapture(capture);
                uint wanted = scenario == 0 ? 1u : scenario <= 3 ? 2u : scenario == 4 ? 3u : scenario == 5 ? 4u : 5u;
                Require(Read32(state) == wanted, "Unexpected fixture status in scenario " + scenario);
                Require(Read32(state + 4) == 1 && Read32(state + 24) == CompetitionUid, "State accounting.");
                for (uint j = 0; j < 5; j++) Require(Read32(collection + 0x10 + 4 * j) == 0xAABB0000 + j, "Original five entries changed.");
                if (scenario == 0)
                {
                    Require(Marshal.ReadByte(Pointer(collection + 8)) == 6 && Read32(collection + 0x24) == obj, "Sixth object append.");
                    Require(Read32(state + 8) == obj && Read32(state + 16) == 5 && Read32(state + 20) == 6, "Success snapshots.");
                    Require(Read32(fake + 8) == 0x240 && Read32(fake + 12) == 1 && Read32(fake + 16) == obj, "Allocator/thiscall this.");
                    Require(Read32(fake + 20) == CompetitionUid && Read32(fake + 24) == 1 && Read32(fake + 28) == 1 && Read32(fake + 32) == 1, "Constructor arguments / cleanup.");
                    Require(Marshal.ReadByte(Pointer(obj + 0xF4)) == 2 && Marshal.ReadByte(Pointer(obj + 0xE9)) == 1, "Competition level/type.");
                    run(Pointer(collection)); CheckCapture(capture);
                    Require(Read32(state) == 6 && Read32(state + 4) == 2 && Read32(fake + 12) == 1 && Read32(fake + 32) == 1, "Repeated six-entry collection must not allocate.");
                }
                else
                {
                    Require(Marshal.ReadByte(Pointer(collection + 8)) == (scenario == 2 ? 4 : 5), "Failure changed original count.");
                    if (scenario <= 3) Require(Read32(fake + 12) == 0 && Read32(fake + 32) == 0, "Invalid collection allocated an object.");
                    if (scenario == 4) Require(Read32(fake + 12) == 1 && Read32(fake + 32) == 0, "Allocation failure called constructor.");
                }
                Console.WriteLine("ABI scenario " + scenario + " passed (status " + wanted + ").");
            }
            GC.KeepAlive(run);
        }
        finally { Check(VirtualFree(allocation, UIntPtr.Zero, 0x8000), "Free fixture"); }
    }

    static void CheckCapture(uint c)
    {
        Require(Read32(c) == Read32(c + 32) && Read32(c + 4) == Read32(c + 36), "ESP/EBP changed.");
        Require(Read32(c + 8) == 0x7FA0B123 && Read32(c + 12) == 0x55667788 && Read32(c + 16) == 0x1122ABCD, "Volatile registers / native ECX pop changed.");
        Require(Read32(c + 20) == 0xDDEEFF11 && Read32(c + 24) == 0x11223344 && Read32(c + 28) == 0x99AABBCC, "Nonvolatile registers / native ESI pop changed.");
        Require((Read32(c + 40) & 0x8D5) == 0x44, "Arithmetic flags changed.");
    }

    sealed class X86
    {
        readonly uint address; readonly List<byte> code = new List<byte>();
        readonly Dictionary<string,int> labels = new Dictionary<string,int>();
        readonly List<Tuple<int,string,bool>> fixups = new List<Tuple<int,string,bool>>();
        public X86(uint address) { this.address = address; }
        public void E(params byte[] bytes) { code.AddRange(bytes); }
        public void U(uint value) { E(BitConverter.GetBytes(value)); }
        public void StoreImm(uint target, uint value) { E(0xC7,0x05); U(target); U(value); }
        public void StoreEax(uint target) { E(0xA3); U(target); }
        public void Label(string name) { labels.Add(name,code.Count); }
        void Ref(string name,bool absolute) { fixups.Add(Tuple.Create(code.Count,name,absolute)); U(0); }
        public void AbsLabel(string name) { Ref(name,true); }
        public void Jcc(byte condition,string name) { E(0x0F,condition); Ref(name,false); }
        public void Jmp(string name) { E(0xE9); Ref(name,false); }
        public void Jmp(uint target) { E(0xE9); U(unchecked(target-address-(uint)code.Count-4)); }
        public void Call(uint target) { E(0xE8); U(unchecked(target-address-(uint)code.Count-4)); }
        public byte[] Finish()
        {
            var result=code.ToArray();
            foreach(var x in fixups) { int target; Require(labels.TryGetValue(x.Item2,out target),"Unknown label."); uint value=x.Item3 ? address+(uint)target : unchecked((uint)(target-x.Item1-4)); Array.Copy(BitConverter.GetBytes(value),0,result,x.Item1,4); }
            return result;
        }
    }

    [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate int FixtureEntry(IntPtr collection);
    static uint Address(IntPtr p) { return unchecked((uint)p.ToInt32()); }
    static IntPtr Pointer(uint p) { return new IntPtr(unchecked((int)p)); }
    static uint Read32(uint p) { return unchecked((uint)Marshal.ReadInt32(Pointer(p))); }
    static void Put(uint p,uint value) { Marshal.WriteInt32(Pointer(p),unchecked((int)value)); }
    static void Copy(uint p,byte[] bytes) { Marshal.Copy(bytes,0,Pointer(p),bytes.Length); }
    static uint Get(byte[] data,int offset) { return BitConverter.ToUInt32(data,offset); }
    static string Hex(byte[] bytes) { return BitConverter.ToString(bytes).Replace("-",""); }
    static bool Equal(byte[] a,byte[] b) { if(a.Length!=b.Length)return false;for(int i=0;i<a.Length;i++)if(a[i]!=b[i])return false;return true; }
    static void Require(bool ok,string message) { if(!ok)throw new InvalidOperationException(message); }
    static void Check(bool ok,string action) { if(!ok)throw new Win32Exception(Marshal.GetLastWin32Error(),action); }
    static string Quote(string path) { Require(path.IndexOf('"')<0,"Quote in path."); return "\""+path+"\""; }
    static byte[] Read(IntPtr process,uint address,int count)
    {
        var bytes=new byte[count];UIntPtr read;Check(ReadProcessMemory(process,Pointer(address),bytes,(UIntPtr)count,out read),"ReadProcessMemory");Require(read.ToUInt32()==count,"Short read.");return bytes;
    }
    static void Write(IntPtr process,uint address,byte[] bytes)
    {
        UIntPtr written;Check(WriteProcessMemory(process,Pointer(address),bytes,(UIntPtr)bytes.Length,out written),"WriteProcessMemory");Require(written.ToUInt32()==bytes.Length,"Short write.");Require(Equal(Read(process,address,bytes.Length),bytes),"Write verification.");
    }
    [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)] struct StartupInfo
    {
        public int Size;public IntPtr Reserved,Desktop,Title;public uint X,Y,XSize,YSize,XCountChars,YCountChars,FillAttribute,Flags;public ushort ShowWindow,ReservedSize;public IntPtr ReservedBytes,StandardInput,StandardOutput,StandardError;
    }
    [StructLayout(LayoutKind.Sequential)] struct ProcessInformation { public IntPtr Process,Thread; public uint ProcessId,ThreadId; }
    [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool CreateProcess(string application,StringBuilder commandLine,IntPtr processAttributes,IntPtr threadAttributes,bool inheritHandles,uint flags,IntPtr environment,string directory,ref StartupInfo startup,out ProcessInformation information);
    [DllImport("kernel32.dll",SetLastError=true)] static extern IntPtr VirtualAllocEx(IntPtr process,IntPtr address,UIntPtr size,uint type,uint protection);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool VirtualProtectEx(IntPtr process,IntPtr address,UIntPtr size,uint protection,out uint previous);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool ReadProcessMemory(IntPtr process,IntPtr address,byte[] buffer,UIntPtr size,out UIntPtr read);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool WriteProcessMemory(IntPtr process,IntPtr address,byte[] buffer,UIntPtr size,out UIntPtr written);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool FlushInstructionCache(IntPtr process,IntPtr address,UIntPtr size);
    [DllImport("kernel32.dll",SetLastError=true)] static extern uint ResumeThread(IntPtr thread);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool TerminateProcess(IntPtr process,uint exitCode);
    [DllImport("kernel32.dll",SetLastError=true)] static extern uint WaitForSingleObject(IntPtr process,uint milliseconds);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetExitCodeProcess(IntPtr process,out uint exitCode);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool CloseHandle(IntPtr handle);
    [DllImport("kernel32.dll",SetLastError=true)] static extern IntPtr VirtualAlloc(IntPtr address,UIntPtr size,uint type,uint protection);
    [DllImport("kernel32.dll",SetLastError=true)] static extern bool VirtualFree(IntPtr address,UIntPtr size,uint type);
    [DllImport("kernel32.dll")] static extern IntPtr GetCurrentProcess();
}
