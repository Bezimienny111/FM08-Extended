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

public static partial class PolandThirdTierGroupFixR92
{
    public const string ExpectedHash = "157F484BE2EAD4AB27006D1002C2C666A7228197B88B14C8D026E76F31B1D62D";
    public const uint HookAddress = 0x00E8EA41;
    public const uint AllocatorAddress = 0x00C933F0;
    public const uint ConstructorAddress = 0x00D805B0;
    public const uint CompetitionUid = 1800001000;
    public const uint LowerCompetitionUid = 129560;
    public static readonly byte[] OriginalTail = { 0x5E, 0x59, 0xC3, 0xCC, 0xCC };
    // State: status0,calls4,thirdObject8,collection12,before16,after20,UID24,lowerObject28,lowerUID32,phase36.
    // Status 1=added, 2=invalid collection, 3=allocation failed, 4=constructor null,
    // 5=first append failed,6=already seven,7=second allocation null,8=second ctor null,9=second append failed.
    const int StateSize = 96;

    public static int Main(string[] args)
    {
        try
        {
            Require(IntPtr.Size == 4, "Compile and run this tool as x86.");
            if (args.Length == 0 || (args[0] == "--verify" && args.Length <= 2))
            {
                if (args.Length == 2) VerifyExe(Path.GetFullPath(args[1]));
                VerifyNativeAbi();
                VerifyActivationHookFixtures();
                VerifyGroupInitializerFixtures();
                VerifySeasonGateFixtures();
                Console.WriteLine("VERIFIED: x86 ABI, 5->7 append, preserved original entries/registers/flags/stack, guard paths. No FM08 process started.");
                return 0;
            }
            if (args.Length == 2 && args[0] == "--verify-runtime")
            {
                var root = Path.GetFullPath(args[1]); VerifyRuntime(root);
                Console.WriteLine("VERIFIED: isolated R9 runtime/manifest/database layout. No FM08 process started."); return 0;
            }
            if (args.Length == 2 && args[0] == "--launch") return Launch(Path.GetFullPath(args[1]));
            Console.Error.WriteLine("Usage: PolandThirdTierGroupFixR92.exe [--verify [original-fm.exe] | --verify-runtime <runtime-root> | --launch <runtime-root>]");
            return 2;
        }
        catch (Exception ex) { Console.Error.WriteLine(ex.ToString()); return 1; }
    }

    public static byte[] BuildStub(uint address, uint state, uint allocator, uint constructor, uint uid)
    {
        var a = new X86(address);
        a.E(0x9C, 0x60);
        a.E(0xF0, 0xFF, 0x05); a.U(state + 4);
        a.StoreImm(state, 0); a.StoreImm(state + 24, uid); a.StoreImm(state + 32, LowerCompetitionUid); a.StoreImm(state + 36, 0);
        a.E(0x89, 0x35); a.U(state + 12);
        a.E(0x85, 0xF6); a.Jcc(0x84, "bad");
        a.E(0x0F, 0xB6, 0x46, 0x08); a.StoreEax(state + 16); a.StoreEax(state + 20);
        a.E(0x83, 0xF8, 0x07); a.Jcc(0x84, "already");
        a.E(0x83, 0xF8, 0x05); a.Jcc(0x85, "bad");
        a.E(0x8B, 0x16, 0x85, 0xD2); a.Jcc(0x84, "bad");
        a.E(0x83, 0x3A, 0x00); a.Jcc(0x84, "bad");
        // Construct both objects before modifying the original collection of five.
        for (int objectIndex = 0; objectIndex < 2; objectIndex++)
        {
            a.E(0x68); a.U(0x240); a.Call(allocator); a.E(0x83, 0xC4, 0x04);
            a.E(0x85, 0xC0); a.Jcc(0x84, objectIndex == 0 ? "alloc_failed" : "alloc2_failed");
            a.E(0x8B, 0xC8, 0x6A, 0x01, 0x6A, 0x01, 0x68); a.U(objectIndex == 0 ? uid : LowerCompetitionUid);
            a.Call(constructor);
            a.E(0x85, 0xC0); a.Jcc(0x84, objectIndex == 0 ? "ctor_failed" : "ctor2_failed");
            a.StoreEax(state + (objectIndex == 0 ? 8u : 28u));
            a.E(0xC6, 0x80); a.U(0xF4); a.E((byte)(objectIndex + 2));
            a.E(0xC6, 0x80); a.U(0xE9); a.E(0x01);
            a.StoreImm(state + 36, (uint)objectIndex + 1);
        }
        for (int objectIndex = 0; objectIndex < 2; objectIndex++)
        {
            a.E(0xA1); a.U(state + (objectIndex == 0 ? 8u : 28u));
            a.E(0x50, 0x8D, 0x04, 0x24, 0x8B, 0x16, 0x8B, 0xCE, 0x50, 0xFF, 0x12, 0x83, 0xC4, 0x04);
            a.E(0x0F, 0xB6, 0x46, 0x08); a.StoreEax(state + 20);
            a.E(0x83, 0xF8, (byte)(objectIndex + 6)); a.Jcc(0x85, objectIndex == 0 ? "append_failed" : "append2_failed");
            a.StoreImm(state + 36, (uint)objectIndex + 3);
        }
        a.StoreImm(state, 1); a.Jmp("done");
        string[] errors = { "bad", "alloc_failed", "ctor_failed", "append_failed", "already", "alloc2_failed", "ctor2_failed", "append2_failed" };
        uint[] status = { 2, 3, 4, 5, 6, 7, 8, 9 };
        for (int i = 0; i < errors.Length; i++) { a.Label(errors[i]); a.StoreImm(state, status[i]); a.Jmp("done"); }
        a.Label("done"); a.E(0x61, 0x9D, 0x5E, 0x59, 0xC3);
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
            f.Position = 0; var image = new byte[f.Length]; int offset = 0;
            while (offset < image.Length) { int count = f.Read(image, offset, image.Length-offset); Require(count>0,"Truncated EXE."); offset += count; }
            VerifyUpperBoundaryImage(image);
            VerifyGroupImage(image);
            VerifyUpperBoundaryFixture(image);
        }
    }

    public static string VerifyRuntime(string root)
    {
        var runtime = new DirectoryInfo(Path.GetFullPath(root));
        Require(string.Equals(runtime.Name, "runtime", StringComparison.OrdinalIgnoreCase) && runtime.Parent != null,
            "Use the isolated R9 runtime directory, not the original game directory.");
        var pilotRoot = runtime.Parent.FullName;
        var manifestPath = Path.Combine(pilotRoot, "manifest.json");
        Require(File.Exists(manifestPath), "Parent R9 manifest missing.");
        var manifest = File.ReadAllText(manifestPath);
        Require(System.Text.RegularExpressions.Regex.IsMatch(manifest, "\"repair_revision\"\\s*:\\s*\"R9[.]2\""), "Manifest repair revision is not R9.2.");
        Require(System.Text.RegularExpressions.Regex.IsMatch(manifest, "\"revision\"\\s*:\\s*\"R9\""), "Manifest revision is not R9.");
        Require(System.Text.RegularExpressions.Regex.IsMatch(manifest, "\"new_competition_uid\"\\s*:\\s*1800001000(?=\\s*[,}])"), "Unexpected pilot competition UID.");
        var db = Path.Combine(pilotRoot, "user-data", "db", "TEST_POL_3_LEVEL_R9");
        foreach (var name in new[] { "server_db.dat", "client_db.dat", "lang_db.dat", "people_db.dat", "TEST_POL_3_LEVEL_R9.xml" })
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
                ApplyUpperBoundary(File.ReadAllBytes(exe),
                    delegate(uint address, int count) { return Read(pi.Process, address, count); },
                    delegate(uint address, byte[] bytes) { WriteExecutable(pi.Process, address, bytes); });
                InstallActivationHooks(pi.Process, state);
                InstallGroupInitializer(pi.Process, state);
                InstallSeasonGate(pi.Process, state);
                uint siteProtection; Check(VirtualProtectEx(pi.Process, Pointer(HookAddress), (UIntPtr)5, 0x40, out siteProtection), "Protect original tail");
                try { Write(pi.Process, HookAddress, EntryJump(stub)); }
                finally { uint ignored; Check(VirtualProtectEx(pi.Process, Pointer(HookAddress), (UIntPtr)5, siteProtection, out ignored), "Restore tail protection"); }
                Check(FlushInstructionCache(pi.Process, Pointer(HookAddress), (UIntPtr)5), "Flush tail");
                log.WriteLine("{\"event\":\"installed\",\"process_id\":" + pi.ProcessId + ",\"uid\":" + CompetitionUid + ",\"state\":\"0x" + state.ToString("X8") + "\",\"hook\":\"0x00E8EA41\",\"exe_sha256\":\"" + ExpectedHash + "\"}");
                Require(ResumeThread(pi.Thread) == 1, "ResumeThread did not report one suspended state."); resumed = true;
                Console.WriteLine("Pilot started, PID=" + pi.ProcessId + ". Log=" + logPath);
                Console.WriteLine("Only this new process has the hook. Keep this console open to collect state; closing it does not stop FM08.");
                string previous = null, previousGroup = null;
                while (true)
                {
                    uint wait = WaitForSingleObject(pi.Process, 0);
                    if (wait == 0) break;
                    Require(wait == 0x102, "Unexpected process wait result: " + wait);
                    byte[] bytes;
                    try { bytes = Read(pi.Process, state, StateSize); }
                    catch (Win32Exception) { if (WaitForSingleObject(pi.Process, 0) == 0) break; throw; }
                    var line = "{\"event\":\"state\",\"utc\":\"" + DateTime.UtcNow.ToString("o") + "\",\"status\":" + Get(bytes, 0) + ",\"calls\":" + Get(bytes, 4) + ",\"object\":\"0x" + Get(bytes, 8).ToString("X8") + "\",\"collection\":\"0x" + Get(bytes, 12).ToString("X8") + "\",\"before\":" + Get(bytes, 16) + ",\"after\":" + Get(bytes, 20) + ",\"uid\":" + Get(bytes, 24) + ",\"lower_object\":\"0x" + Get(bytes, 28).ToString("X8") + "\",\"lower_uid\":" + Get(bytes, 32) + ",\"phase\":" + Get(bytes, 36) + ",\"lower_activation_a\":" + Get(bytes, 40) + ",\"lower_activation_b\":" + Get(bytes, 44) + "}";
                    var signature = Hex(bytes);
                    if (signature != previous) { log.WriteLine(line); Console.WriteLine(line); previous = signature; }
                    var groupLine = GroupTelemetry(pi.Process, bytes);
                    if (groupLine != previousGroup) { log.WriteLine(groupLine); Console.WriteLine(groupLine); previousGroup = groupLine; }
                    Thread.Sleep(500);
                }
                try { var finalState = Read(pi.Process, state, StateSize); log.WriteLine(GroupTelemetry(pi.Process, finalState)); } catch (Win32Exception) { }
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

    // Run actual x86 payload against fake cdecl allocation, thiscall constructors and Add.
    public static void VerifyNativeAbi()
    {
        IntPtr allocation = VirtualAlloc(IntPtr.Zero, (UIntPtr)0x4000, 0x3000, 0x40); Check(allocation != IntPtr.Zero, "VirtualAlloc fixture");
        try
        {
            uint b = Address(allocation), stub=b, alloc=b+0x1000, ctor=b+0x1100, append=b+0x1200, wrapper=b+0x1300;
            uint vt=b+0x2000, collection=b+0x2100, obj=b+0x2400, lower=b+0x2700, state=b+0x2C00, capture=b+0x2D00, fake=b+0x2E00;
            Copy(stub,BuildStub(stub,state,alloc,ctor,CompetitionUid));
            var a=new X86(alloc);
            a.E(0x8B,0x44,0x24,0x04); a.StoreEax(fake+8); a.E(0xFF,0x05); a.U(fake+12);
            a.E(0xA1); a.U(fake+12); a.E(0x83,0xF8,1); a.Jcc(0x85,"second");
            a.E(0xA1); a.U(fake); a.E(0xC3); a.Label("second"); a.E(0xA1); a.U(fake+4); a.E(0xC3); Copy(alloc,a.Finish());
            a=new X86(ctor); a.E(0xFF,0x05); a.U(fake+32); a.E(0x83,0x3D); a.U(fake+32); a.E(1); a.Jcc(0x85,"second");
            for(int k=0;k<2;k++)
            {
                if(k==1)a.Label("second");
                uint captureAt=fake+(k==0?16u:40u); a.E(0x89,0x0D);a.U(captureAt);
                for(byte i=0;i<3;i++){a.E(0x8B,0x44,0x24,(byte)(4+i*4));a.StoreEax(captureAt+4+(uint)i*4);}
                a.E(0xA1);a.U(fake+(k==0?60u:64u));a.E(0xC2,0x0C,0);
            }
            Copy(ctor,a.Finish());
            a=new X86(append);a.E(0xFF,0x05);a.U(fake+56);a.E(0xA1);a.U(fake+56);a.E(0x3B,0x05);a.U(fake+36);a.Jcc(0x84,"skip");
            a.E(0x8B,0x54,0x24,0x04,0x8B,0x02,0x0F,0xB6,0x51,0x08,0x89,0x44,0x91,0x10,0xFE,0x41,0x08);
            a.Label("skip");a.E(0xC2,4,0);Copy(append,a.Finish());
            a=new X86(wrapper);a.E(0x55,0x8B,0xEC,0x53,0x56,0x57,0x89,0x25);a.U(capture);a.E(0x89,0x2D);a.U(capture+4);
            a.E(0x68);a.AbsLabel("returned");a.E(0x68);a.U(0x55667788);a.E(0x68);a.U(0x11223344);
            a.E(0x8B,0x75,0x08,0xB8);a.U(0x7FA0B123);a.E(0xB9);a.U(0xCAFEBABE);a.E(0xBA);a.U(0x1122ABCD);
            a.E(0xBB);a.U(0xDDEEFF11);a.E(0xBF);a.U(0x99AABBCC);a.E(0x68);a.U(0x246);a.E(0x9D);a.Jmp(stub);
            a.Label("returned");a.StoreEax(capture+8);a.E(0x89,0x0D);a.U(capture+12);a.E(0x89,0x15);a.U(capture+16);
            a.E(0x89,0x1D);a.U(capture+20);a.E(0x89,0x35);a.U(capture+24);a.E(0x89,0x3D);a.U(capture+28);
            a.E(0x89,0x25);a.U(capture+32);a.E(0x89,0x2D);a.U(capture+36);a.E(0x9C,0x58);a.StoreEax(capture+40);
            a.E(0xB8);a.U(1);a.E(0x5F,0x5E,0x5B,0x5D,0xC2,4,0);Copy(wrapper,a.Finish());
            Check(FlushInstructionCache(GetCurrentProcess(),allocation,(UIntPtr)0x4000),"Flush fixture");
            var run=(FixtureEntry)Marshal.GetDelegateForFunctionPointer(Pointer(wrapper),typeof(FixtureEntry));Put(vt,append);
            uint[] statuses={1,2,2,2,3,4,7,8,5,9,2};
            for(int scenario=0;scenario<statuses.Length;scenario++)
            {
                Copy(state,new byte[StateSize]);Copy(fake,new byte[128]);Copy(collection,new byte[128]);Copy(obj,new byte[0x240]);Copy(lower,new byte[0x240]);
                Put(collection,vt);Marshal.WriteByte(Pointer(collection+8),scenario==2?(byte)4:scenario==10?(byte)6:(byte)5);
                for(uint j=0;j<5;j++)Put(collection+0x10+4*j,0xAABB0000+j);
                Put(fake,scenario==4?0:obj);Put(fake+4,scenario==6?0:lower);Put(fake+60,scenario==5?0:obj);Put(fake+64,scenario==7?0:lower);
                if(scenario==3)Put(collection,0);if(scenario==8)Put(fake+36,1);if(scenario==9)Put(fake+36,2);
                Require(run(scenario==1?IntPtr.Zero:Pointer(collection))==1,"Wrapper return.");CheckCapture(capture);
                Require(Read32(state)==statuses[scenario],"Status scenario "+scenario);
                Require(Read32(state+4)==1 && Read32(state+24)==CompetitionUid && Read32(state+32)==LowerCompetitionUid,"State accounting.");
                for(uint j=0;j<5;j++)Require(Read32(collection+0x10+4*j)==0xAABB0000+j,"Original five entries changed.");
                int count=Marshal.ReadByte(Pointer(collection+8));Require(count==(scenario==0?7:scenario==2?4:scenario==9||scenario==10?6:5),"Unexpected append count.");
                if(scenario==0)
                {
                    Require(Read32(collection+0x24)==obj && Read32(collection+0x28)==lower,"Appended object order.");
                    Require(Read32(state+8)==obj && Read32(state+28)==lower && Read32(state+16)==5 && Read32(state+20)==7 && Read32(state+36)==4,"Successful state.");
                    Require(Read32(fake+8)==0x240 && Read32(fake+12)==2 && Read32(fake+32)==2,"Allocation/constructor counts.");
                    Require(Read32(fake+16)==obj && Read32(fake+20)==CompetitionUid && Read32(fake+24)==1 && Read32(fake+28)==1,"First constructor ABI.");
                    Require(Read32(fake+40)==lower && Read32(fake+44)==LowerCompetitionUid && Read32(fake+48)==1 && Read32(fake+52)==1,"Second constructor ABI.");
                    Require(Marshal.ReadByte(Pointer(obj+0xF4))==2 && Marshal.ReadByte(Pointer(lower+0xF4))==3 && Marshal.ReadByte(Pointer(obj+0xE9))==1 && Marshal.ReadByte(Pointer(lower+0xE9))==1,"League levels/types.");
                    run(Pointer(collection));CheckCapture(capture);Require(Read32(state)==6 && Read32(state+4)==2 && Read32(fake+12)==2 && Read32(fake+32)==2,"Repeat count7 allocated.");
                }
                else if(scenario<=3||scenario==10)Require(Read32(fake+12)==0 && Read32(fake+32)==0,"Invalid collection allocated.");
                else if(scenario==4)Require(Read32(fake+12)==1 && Read32(fake+32)==0,"First allocator failure.");
                else if(scenario==5)Require(Read32(fake+12)==1 && Read32(fake+32)==1 && Read32(fake+56)==0,"First constructor failure.");
                else if(scenario==6)Require(Read32(fake+12)==2 && Read32(fake+32)==1 && Read32(fake+56)==0,"Second allocator failure modified collection.");
                else if(scenario==7)Require(Read32(fake+12)==2 && Read32(fake+32)==2 && Read32(fake+56)==0,"Second constructor failure modified collection.");
                Console.WriteLine("R9 ABI scenario "+scenario+" passed (status "+statuses[scenario]+").");
            }
            GC.KeepAlive(run);
        }
        finally{Check(VirtualFree(allocation,UIntPtr.Zero,0x8000),"Free fixture");}
    }

    static void CheckCapture(uint c)
    {
        Require(Read32(c) == Read32(c + 32) && Read32(c + 4) == Read32(c + 36), "ESP/EBP changed.");
        Require(Read32(c + 8) == 0x7FA0B123 && Read32(c + 12) == 0x55667788 && Read32(c + 16) == 0x1122ABCD, "Volatile registers / native ECX pop changed.");
        Require(Read32(c + 20) == 0xDDEEFF11 && Read32(c + 24) == 0x11223344 && Read32(c + 28) == 0x99AABBCC, "Nonvolatile registers / native ESI pop changed.");
        Require((Read32(c + 40) & 0x8D5) == 0x44, "Arithmetic flags changed.");
    }

    public static readonly uint[] ActivationSites={0x00D68DD3,0x00D69AF0};
    public static readonly byte[][] ActivationOriginal={new byte[]{0x3A,0x51,0x11,0x7E,0x0C},new byte[]{0x3A,0xC1,0x8B,0xCE,0x7E,0x0F}};
    public static byte[] BuildActivationA(uint address,uint state,uint active,uint fallback)
    {
        var a=new X86(address);a.E(0x9C,0x81,0x7E,0x14);a.U(LowerCompetitionUid);a.Jcc(0x85,"original");
        a.E(0x80,0x79,0x11,0x02);a.Jcc(0x8C,"original");
        if(state!=0){a.E(0xF0,0xFF,0x05);a.U(state+40);}
        a.E(0x9D,0x3A,0x51,0x11);a.Jmp(active);
        a.Label("original");a.E(0x9D,0x3A,0x51,0x11);a.Jcc(0x8E,"active");a.Jmp(fallback);a.Label("active");a.Jmp(active);
        return a.Finish();
    }
    public static byte[] BuildActivationB(uint address,uint state,uint active,uint fallback)
    {
        var a=new X86(address);a.E(0x9C,0x81,0x7E,0x14);a.U(LowerCompetitionUid);a.Jcc(0x85,"original");
        a.E(0x80,0xF9,0x02);a.Jcc(0x8C,"original");
        if(state!=0){a.E(0xF0,0xFF,0x05);a.U(state+44);}
        a.E(0x9D,0x3A,0xC1,0x8B,0xCE);a.Jmp(active);
        a.Label("original");a.E(0x9D,0x3A,0xC1,0x8B,0xCE);a.Jcc(0x8E,"active");a.Jmp(fallback);a.Label("active");a.Jmp(active);
        return a.Finish();
    }
    static byte[] ActivationJump(uint source,uint destination,int length)
    {
        var bytes=new byte[length];bytes[0]=0xE9;Array.Copy(BitConverter.GetBytes(unchecked(destination-source-5)),0,bytes,1,4);
        for(int i=5;i<length;i++)bytes[i]=0x90;return bytes;
    }
    static void InstallActivationHooks(IntPtr process,uint state)
    {
        for(int i=0;i<ActivationSites.Length;i++)Require(Equal(Read(process,ActivationSites[i],ActivationOriginal[i].Length),ActivationOriginal[i]),"Lower activation preflight failed.");
        for(int i=0;i<ActivationSites.Length;i++)
        {
            var page=VirtualAllocEx(process,IntPtr.Zero,(UIntPtr)4096,0x3000,4);Check(page!=IntPtr.Zero,"Allocate lower activation hook");
            uint address=Address(page);var code=i==0?BuildActivationA(address,state,0x00D68DE4,0x00D68DD8):BuildActivationB(address,state,0x00D69B05,0x00D69AF6);
            Write(process,address,code);uint old;Check(VirtualProtectEx(process,page,(UIntPtr)4096,0x20,out old),"Protect lower activation hook RX");
            Check(FlushInstructionCache(process,page,(UIntPtr)code.Length),"Flush lower activation hook");
            WriteExecutable(process,ActivationSites[i],ActivationJump(ActivationSites[i],address,ActivationOriginal[i].Length));
        }
    }
    static uint CompareByteFlags(byte left,byte right)
    {
        byte result=unchecked((byte)(left-right));uint flags=0;
        if(left<right)flags|=1;if(result==0)flags|=0x40;if((result&0x80)!=0)flags|=0x80;
        if(((left^right^result)&0x10)!=0)flags|=0x10;if(((left^right)&(left^result)&0x80)!=0)flags|=0x800;
        int bits=0;for(int k=0;k<8;k++)bits+=(result>>k)&1;if(bits%2==0)flags|=4;return flags;
    }
    public static void VerifyActivationHookFixtures()
    {
        var allocation=VirtualAlloc(IntPtr.Zero,(UIntPtr)0x4000,0x3000,0x40);Check(allocation!=IntPtr.Zero,"Allocate activation fixture");
        try
        {
            uint b=Address(allocation),hookA=b,hookB=b+0x100,wrapper=b+0x1000,active=b+0x1300,fallback=b+0x1400,done=b+0x1500;
            uint obj=b+0x3000,settings=b+0x3100,capture=b+0x3200,state=b+0x3300;
            Copy(hookA,BuildActivationA(hookA,state,active,fallback));Copy(hookB,BuildActivationB(hookB,state,active,fallback));
            var a=new X86(active);a.StoreImm(capture+44,1);a.Jmp(done);Copy(active,a.Finish());
            a=new X86(fallback);a.StoreImm(capture+44,0);a.Jmp(done);Copy(fallback,a.Finish());
            a=new X86(done);a.StoreEax(capture+8);a.E(0x89,0x0D);a.U(capture+12);a.E(0x89,0x15);a.U(capture+16);
            a.E(0x89,0x1D);a.U(capture+20);a.E(0x89,0x35);a.U(capture+24);a.E(0x89,0x3D);a.U(capture+28);
            a.E(0x89,0x25);a.U(capture+32);a.E(0x89,0x2D);a.U(capture+36);a.E(0x9C,0x58);a.StoreEax(capture+40);
            a.E(0xB8);a.U(1);a.E(0x5F,0x5E,0x5B,0x5D,0xC2,4,0);Copy(done,a.Finish());
            var run=(FixtureEntry)Marshal.GetDelegateForFunctionPointer(Pointer(wrapper),typeof(FixtureEntry));int cases=0;
            foreach(uint uid in new uint[]{LowerCompetitionUid,CompetitionUid,129559})
            for(byte selected=0;selected<=3;selected++)for(byte level=0;level<=3;level++)for(int hook=0;hook<2;hook++)
            {
                Copy(state,new byte[StateSize]);Copy(capture,new byte[64]);Put(obj+0x14,uid);Marshal.WriteByte(Pointer(settings+0x11),selected);
                uint eax=hook==0?0x7FA0B123:0x7FA0B100u+level,ecx=hook==0?settings:0xCAFEBA00+selected,edx=hook==0?0x1122AB00u+level:0x1122ABCD;
                a=new X86(wrapper);a.E(0x55,0x8B,0xEC,0x53,0x56,0x57,0x89,0x25);a.U(capture);a.E(0x89,0x2D);a.U(capture+4);
                a.E(0xB8);a.U(eax);a.E(0xB9);a.U(ecx);a.E(0xBA);a.U(edx);a.E(0xBB);a.U(0xDDEEFF11);a.E(0xBE);a.U(obj);a.E(0xBF);a.U(0x99AABBCC);
                a.E(0x68);a.U(0x246);a.E(0x9D);a.Jmp(hook==0?hookA:hookB);Copy(wrapper,a.Finish());
                Check(FlushInstructionCache(GetCurrentProcess(),allocation,(UIntPtr)0x2000),"Flush activation fixture");Require(run(IntPtr.Zero)==1,"Activation wrapper return.");
                bool forced=uid==LowerCompetitionUid&&selected>=2;bool expected=forced||level<=selected;
                Require(Read32(capture+44)==(expected?1u:0u),"Activation branch selection.");
                Require(Read32(capture)==Read32(capture+32)&&Read32(capture+4)==Read32(capture+36),"Activation ESP/EBP.");
                Require(Read32(capture+8)==eax&&Read32(capture+12)==(hook==0?ecx:obj)&&Read32(capture+16)==edx,"Activation volatile registers.");
                Require(Read32(capture+20)==0xDDEEFF11&&Read32(capture+24)==obj&&Read32(capture+28)==0x99AABBCC,"Activation preserved registers.");
                Require((Read32(capture+40)&0x8D5)==CompareByteFlags(level,selected),"Activation original CMP flags.");
                Require(Read32(state+(hook==0?40u:44u))==(forced?1u:0u),"Activation scope counter.");cases++;
            }
            GC.KeepAlive(run);Console.WriteLine("R9 lower activation fixtures passed: "+cases+" native x86 cases (3 UIDs, selected0..3, levels0..3, both hooks).");
        }
        finally{Check(VirtualFree(allocation,UIntPtr.Zero,0x8000),"Free activation fixture");}
    }

    public sealed class MemoryPatch
    {
        public readonly uint Address; public readonly string Meaning;
        readonly byte[] original, replacement;
        public byte[] Original { get { return (byte[])original.Clone(); } }
        public byte[] Replacement { get { return (byte[])replacement.Clone(); } }
        public MemoryPatch(uint address,string meaning,byte[] original,byte[] replacement)
        { Address=address;Meaning=meaning;this.original=(byte[])original.Clone();this.replacement=(byte[])replacement.Clone(); }
    }
    public static readonly MemoryPatch[] UpperBoundaryPatches={
        new MemoryPatch(0x00E8F761,"POL_SECOND relegation places 4->3",new byte[]{0xC6,0x46,0x17,0x04},new byte[]{0xC6,0x46,0x17,0x03}),
        new MemoryPatch(0x00E8F7DB,"Relegation action count 4->3",new byte[]{0x6A,0x04},new byte[]{0x6A,0x03}),
        new MemoryPatch(0x00E8F7DD,"Relegation target 129560->1800001000",new byte[]{0x68,0x18,0xFA,0x01,0x00},new byte[]{0x68,0xE8,0xD5,0x49,0x6B})
    };
    public static void VerifyUpperBoundaryImage(byte[] image)
    {
        using(var sha=SHA256.Create())Require(Hex(sha.ComputeHash(image))==ExpectedHash,"Unsupported original for R9 boundary.");
        foreach(var patch in UpperBoundaryPatches)Require(Equal(Slice(image,patch.Address,patch.Original.Length),patch.Original),"Unexpected boundary instruction.");
        for(int i=0;i<ActivationSites.Length;i++)Require(Equal(Slice(image,ActivationSites[i],ActivationOriginal[i].Length),ActivationOriginal[i]),"Unexpected lower activation hook bytes.");
        Require(BitConverter.ToUInt32(image,checked((int)(0x0162FA2C+0x160-0x400000)))==0x00E8F660,"POL_SECOND factory vtable differs.");
    }
    static byte[] Slice(byte[] image,uint address,int length){var result=new byte[length];Array.Copy(image,checked((int)(address-0x400000)),result,0,length);return result;}
    public static void ApplyUpperBoundary(byte[] verifiedOriginal,Func<uint,int,byte[]> read,Action<uint,byte[]> write)
    {
        VerifyUpperBoundaryImage(verifiedOriginal);
        Require(Equal(read(0x0162FA2C+0x160,4),Slice(verifiedOriginal,0x0162FA2C+0x160,4)),"Unexpected POL_SECOND factory pointer in memory.");
        Require(Equal(read(0x00E8F660,0x4A0),Slice(verifiedOriginal,0x00E8F660,0x4A0)),"POL_SECOND factory is already modified or unsupported.");
        foreach(var patch in UpperBoundaryPatches)Require(Equal(read(patch.Address,patch.Original.Length),patch.Original),"Boundary preflight failed.");
        var attempted=new List<MemoryPatch>();
        try
        {
            foreach(var patch in UpperBoundaryPatches){attempted.Add(patch);write(patch.Address,patch.Replacement);Require(Equal(read(patch.Address,patch.Replacement.Length),patch.Replacement),"Boundary write verification failed.");}
            var expected=Slice(verifiedOriginal,0x00E8F660,0x4A0);
            foreach(var patch in UpperBoundaryPatches)Array.Copy(patch.Replacement,0,expected,checked((int)(patch.Address-0x00E8F660)),patch.Replacement.Length);
            Require(Equal(read(0x00E8F660,0x4A0),expected),"Unexpected neighbouring factory change.");
        }
        catch(Exception failure)
        {
            var errors=new List<Exception>();errors.Add(failure);
            for(int i=attempted.Count-1;i>=0;i--){var patch=attempted[i];try{write(patch.Address,patch.Original);Require(Equal(read(patch.Address,patch.Original.Length),patch.Original),"Rollback verification failed.");}catch(Exception rollback){errors.Add(rollback);}}
            if(errors.Count>1)throw new AggregateException("Boundary installation failed; never resume this process.",errors);throw;
        }
    }
    static void WriteExecutable(IntPtr process,uint address,byte[] bytes)
    {
        uint old;Check(VirtualProtectEx(process,Pointer(address),(UIntPtr)bytes.Length,0x40,out old),"Protect boundary");
        try{Write(process,address,bytes);}finally{uint ignored;Check(VirtualProtectEx(process,Pointer(address),(UIntPtr)bytes.Length,old,out ignored),"Restore boundary protection");}
        Check(FlushInstructionCache(process,Pointer(address),(UIntPtr)bytes.Length),"Flush boundary");
    }
    static void VerifyUpperBoundaryFixture(byte[] original)
    {
        var memory=(byte[])original.Clone();Func<uint,int,byte[]> read=delegate(uint a,int n){return Slice(memory,a,n);};
        Action<uint,byte[]> write=delegate(uint a,byte[] v){Array.Copy(v,0,memory,checked((int)(a-0x400000)),v.Length);};
        ApplyUpperBoundary(original,read,write);int changed=0;for(int i=0;i<memory.Length;i++)if(memory[i]!=original[i])changed++;
        Require(changed==6,"Boundary fixture changed unexpected number of bytes.");
        foreach(var patch in UpperBoundaryPatches)Require(Equal(read(patch.Address,patch.Replacement.Length),patch.Replacement),"Boundary fixture payload.");
        memory=(byte[])original.Clone();memory[0xE8F761-0x400000]^=1;int writes=0;bool rejected=false;
        try{ApplyUpperBoundary(original,read,delegate(uint a,byte[] v){writes++;write(a,v);});}catch(InvalidOperationException){rejected=true;}
        Require(rejected&&writes==0,"Boundary preflight was not atomic.");
        memory=(byte[])original.Clone();int invocation=0;rejected=false;
        try{ApplyUpperBoundary(original,read,delegate(uint a,byte[] v){write(a,v);invocation++;if(invocation==2)throw new IOException("Injected partial write failure");});}catch(IOException){rejected=true;}
        Require(rejected&&Equal(memory,original),"Boundary rollback failed.");
        Console.WriteLine("R9 upper-boundary fixture passed: three guarded literals, six changed bytes, preflight rejection and rollback.");
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
