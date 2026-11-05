using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Collections.Generic;
using System.Threading;

internal static partial class NativeFixture
{
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    private delegate int Getter(int code, int extra);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    private delegate void Training(IntPtr player, IntPtr profile, uint epoch);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr VirtualAlloc(IntPtr address, UIntPtr size, uint type, uint protection);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool VirtualProtect(IntPtr address, UIntPtr size, uint protection, out uint old);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool FlushInstructionCache(IntPtr process, IntPtr address, UIntPtr size);
    [DllImport("kernel32.dll")]
    private static extern IntPtr GetCurrentProcess();

    private static int Main(string[] args)
    {
        try
        {
            if (args[0] == "--pa")
            {
                TestPa(args[1]);
                return 0;
            }
            if (args[0] == "--league")
            {
                TestLeague(args[1]);
                return 0;
            }
            if (args[0] == "--modern-rules")
            {
                TestModernRules(args[1]);
                return 0;
            }
            byte[] game = File.ReadAllBytes(args[0]);
            byte[] payloads = File.ReadAllBytes(args[1]);
            byte[] payload = new byte[96];
            byte[] benchPayload = new byte[96];
            Array.Copy(payloads, 0, payload, 0, 96);
            Array.Copy(payloads, 96, benchPayload, 0, 96);
            IntPtr original = VirtualAlloc(IntPtr.Zero, new UIntPtr(4096), 0x3000, 0x40);
            IntPtr cave = VirtualAlloc(new IntPtr(0x10000000), new UIntPtr(4096), 0x3000, 0x40);
            if (original == IntPtr.Zero || cave != new IntPtr(0x10000000))
                throw new InvalidOperationException("Cannot allocate x86 fixture memory: original="
                    + original.ToString("X") + ", cave=" + cave.ToString("X"));
            byte[] getters = new byte[0x200];
            Array.Copy(game, 0x006FE000, getters, 0, getters.Length);
            int relocation = unchecked(original.ToInt32() - 0x00AFE000);
            // Relocate the original absolute lookup pointers and their jump-table entries.
            foreach (int offset in new int[] { 0xDD, 0xE4, 0x15D, 0x164 })
                Relocate(getters, offset, relocation);
            for (int index = 0; index < 8; index++) Relocate(getters, 0x10C + index * 4, relocation);
            for (int index = 0; index < 12; index++) Relocate(getters, 0x1A4 + index * 4, relocation);
            Marshal.Copy(getters, 0, original, getters.Length);
            IntPtr substitutionAddress = IntPtr.Add(original, 0xD0);
            Getter substitutions = (Getter)Marshal.GetDelegateForFunctionPointer(substitutionAddress, typeof(Getter));
            IntPtr benchAddress = IntPtr.Add(original, 0x150);
            Getter bench = (Getter)Marshal.GetDelegateForFunctionPointer(benchAddress, typeof(Getter));
            int[] extras = { 0, 1, 2, 255 };
            int[,] originalSubs = new int[256, 4];
            int[,] originalBench = new int[256, 4];
            for (int code = 0; code < 256; code++)
            for (int extra = 0; extra < extras.Length; extra++)
            {
                originalSubs[code, extra] = substitutions(code, extras[extra]) & 255;
                originalBench[code, extra] = bench(code, extras[extra]) & 255;
            }
            if (originalSubs[28, 0] != 10 || originalSubs[28, 1] != 12
                || originalBench[22, 0] != 7 || originalBench[22, 1] != 5)
                throw new InvalidOperationException("Unexpected conditional rules.");
            byte[] originals = new byte[29 * 4];
            for (int code = 0; code < 29; code++)
            {
                originals[code * 4] = (byte)originalSubs[code, 0];
                originals[code * 4 + 1] = (byte)originalSubs[code, 1];
                originals[code * 4 + 2] = (byte)originalBench[code, 0];
                originals[code * 4 + 3] = (byte)originalBench[code, 1];
            }
            File.WriteAllBytes(args[2], originals);
            Relocate(payload, 91, relocation);
            Marshal.Copy(payload, 0, cave, payload.Length);
            byte[] jump = { 0xE9, 0, 0, 0, 0 };
            Array.Copy(BitConverter.GetBytes(unchecked(0x10000040 - (substitutionAddress.ToInt32() + 5))), 0, jump, 1, 4);
            Marshal.Copy(jump, 0, substitutionAddress, jump.Length);
            Relocate(benchPayload, 91, relocation);
            Marshal.Copy(benchPayload, 0, IntPtr.Add(cave, 0x100), benchPayload.Length);
            Array.Copy(BitConverter.GetBytes(unchecked(0x10000140 - (benchAddress.ToInt32() + 5))), 0, jump, 1, 4);
            Marshal.Copy(jump, 0, benchAddress, jump.Length);
            for (int code = 0; code < 256; code++)
            for (int extra = 0; extra < extras.Length; extra++)
            {
                int expected = code <= 28 && payload[code] != 0 ? payload[32 + code] : originalSubs[code, extra];
                if ((substitutions(code, extras[extra]) & 255) != expected)
                    throw new InvalidOperationException("Substitutions mismatch at code " + code + ", extra " + extras[extra]);
                int expectedBench = code <= 28 && benchPayload[code] != 0 ? benchPayload[32 + code] : originalBench[code, extra];
                if ((bench(code, extras[extra]) & 255) != expectedBench)
                    throw new InvalidOperationException("Bench mismatch at code " + code + ", extra " + extras[extra]);
            }
            Console.WriteLine("PASS: actual x86 execution; 1024 substitution and 1024 bench cases.");
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine(error);
            return 1;
        }
    }

    private static void TestLeague(string path)
    {
        const int state = 0x10000000, code = 0x10100000, scratch = 0x10200000;
        foreach (int[] range in new int[][] {
            new int[] { state, 0x40000 }, new int[] { code, 0x10000 }, new int[] { scratch, 0x10000 } })
            if (VirtualAlloc(new IntPtr(range[0]), new UIntPtr((uint)range[1]), 0x3000, 0x40) != new IntPtr(range[0]))
                throw new InvalidOperationException("Cannot allocate league fixture " + range[0].ToString("X"));
        byte[] saveSuccess, saveFailure;
        using (var reader = new BinaryReader(File.OpenRead(path)))
        {
            saveSuccess = reader.ReadBytes(reader.ReadInt32());
            saveFailure = reader.ReadBytes(reader.ReadInt32());
            for (int i = 0; i < 4; i++)
            {
                int length = reader.ReadInt32();
                byte[] payload = reader.ReadBytes(length);
                int relocated = 0;
                // The managed fixture can already occupy FM's calendar addresses.
                for (int offset = 0; offset <= payload.Length - 4; offset++)
                {
                    int value = BitConverter.ToInt32(payload, offset);
                    if (value != 0x1B1EE14 && value != 0x1B1EE16) continue;
                    Array.Copy(BitConverter.GetBytes(scratch + 0x200 + value - 0x1B1EE14), 0, payload, offset, 4);
                    relocated++;
                    offset += 3;
                }
                if (relocated != 2) throw new InvalidOperationException("Unexpected calendar relocation count.");
                int identityReferences = 0;
                for (int offset = 0; offset <= payload.Length - 4; offset++)
                {
                    int source = BitConverter.ToInt32(payload, offset);
                    int field = source == 0x1911160 ? 0 : source == 0x1911168 ? 4 : source == 0x191116C ? 8 : -1;
                    if (field < 0) continue;
                    Array.Copy(BitConverter.GetBytes(scratch + 0x220 + field), 0, payload, offset, 4);
                    identityReferences++; offset += 3;
                }
                if (identityReferences != (i == 3 ? 3 : 0))
                    throw new InvalidOperationException("Unexpected save identity relocation.");
                int relocatedBranches = 0;
                for (int offset = 0; offset <= payload.Length - 5; offset++)
                {
                    if (payload[offset] != 0xE8 && payload[offset] != 0xE9) continue;
                    int next = code + i * 4096 + offset + 5;
                    int target = unchecked(next + BitConverter.ToInt32(payload, offset + 1));
                    int destination = target == 0xE23440 ? scratch + 0x1000 :
                        target == 0xE2611A ? scratch + 0x1100 :
                        target == 0x465217 ? scratch + 0x1200 :
                        target == 0x46697F ? scratch + 0x1300 :
                        target == 0x467F2A ? scratch + 0x1400 : 0;
                    if (destination == 0) continue;
                    Array.Copy(BitConverter.GetBytes(unchecked(destination - next)), 0, payload, offset + 1, 4);
                    relocatedBranches++;
                    offset += 4;
                }
                if (relocatedBranches != (i == 0 ? 2 : 1))
                    throw new InvalidOperationException("Unexpected native continuation/call target.");
                Marshal.Copy(payload, 0, new IntPtr(code + i * 4096), length);
            }
        }
        Action<int, byte[]> put = (address, bytes) => Marshal.Copy(bytes, 0, new IntPtr(address), bytes.Length);
        put(scratch + 0x1100, new byte[] { 0xC3 });
        put(scratch + 0x1200, new byte[] { 0x8D, 0x64, 0x24, 8, 0xC3 });
        put(scratch + 0x1300, new byte[] { 0xC3 });
        put(scratch + 0x1400, new byte[] { 0xC3 });
        Marshal.WriteInt32(new IntPtr(scratch + 0x220), 3191021);
        Marshal.WriteInt32(new IntPtr(scratch + 0x224), (2026 << 16) | 136);
        Marshal.WriteInt32(new IntPtr(scratch + 0x228), 51);
        var callee = new List<byte>(new byte[] { 0x89, 0x0D });
        callee.AddRange(BitConverter.GetBytes(scratch + 0x80));
        callee.Add(0xC3);
        put(scratch + 0x1000, callee.ToArray());
        Marshal.WriteInt16(new IntPtr(scratch + 0x200), 164);
        Marshal.WriteInt16(new IntPtr(scratch + 0x202), 2008);
        Marshal.WriteInt16(new IntPtr(scratch + 0x1C), 164);
        Marshal.WriteInt16(new IntPtr(scratch + 0x1E), 2008);
        var drivers = new Getter[7];
        for (int variant = 0; variant < drivers.Length; variant++)
        {
            int kind = variant == 0 ? 1 : variant <= 2 ? 2 : variant <= 4 ? 3 : 4;
            int frame = kind == 3 ? 0xC4C : kind == 4 ? 0x2EC : 0;
            var stub = new List<byte>(new byte[] { 0x53, 0x55, 0x56, 0x57, 0x89, 0x25 });
            Action<int> integer = value => stub.AddRange(BitConverter.GetBytes(value));
            integer(scratch + 0x140);
            if (kind == 2) stub.AddRange(new byte[] { 0x6A, 0, 0x6A, (byte)(variant - 1), 0x6A, 0 });
            if (frame != 0)
            {
                stub.AddRange(new byte[] { 0x81, 0xEC }); integer(frame);
                stub.AddRange(new byte[] { 0xC7, 0x84, 0x24 }); integer(frame - 4); integer(0x66778899);
            }
            stub.Add(0xB8); integer(variant == 3 || variant == 6 ? 0x13572400 : 0x13572401);
            stub.Add(0xBB); integer(0x13579BDF);
            stub.Add(0xBD); integer(0x2468ACE0);
            stub.Add(0xB9); integer(0x12345678);
            stub.Add(0xBA); integer(0x55667788);
            stub.Add(0xBE); integer(scratch);
            stub.Add(0xBF); integer(0x11223344);
            stub.AddRange(new byte[] { 0xD9, 0xE8, 0x3B, 0xD2, 0xE8 });
            integer(unchecked(code + (kind - 1) * 4096 - (code + 0x4000 + variant * 512 + stub.Count + 4)));
            if (kind == 2) stub.AddRange(new byte[] { 0x8D, 0x64, 0x24, 12 });
            if (frame != 0) { stub.AddRange(new byte[] { 0x8D, 0xA4, 0x24 }); integer(frame); }
            foreach (byte operand in new byte[] { 0x05, 0x1D, 0x0D, 0x15, 0x35, 0x3D, 0x2D, 0x25 })
            {
                stub.AddRange(new byte[] { 0x89, operand });
                integer(scratch + 0x100 + Array.IndexOf(new byte[] { 0x05, 0x1D, 0x0D, 0x15, 0x35, 0x3D, 0x2D, 0x25 }, operand) * 4);
            }
            stub.AddRange(new byte[] { 0x9C, 0x8F, 0x05 }); integer(scratch + 0x120);
            stub.AddRange(new byte[] { 0xDD, 0x1D }); integer(scratch + 0x128);
            stub.AddRange(new byte[] { 0x5F, 0x5E, 0x5D, 0x5B, 0xC3 });
            int driver = code + 0x4000 + variant * 512;
            put(driver, stub.ToArray());
            drivers[variant] = (Getter)Marshal.GetDelegateForFunctionPointer(new IntPtr(driver), typeof(Getter));
        }
        Action<int> run = variant =>
        {
            drivers[variant](0, 0);
            int[] expected = { variant == 3 || variant == 6 ? 0x13572400 : 0x13572401, 0x13579BDF,
                variant == 0 ? scratch : variant >= 3 ? 0x66778899 : 0x12345678,
                0x55667788, scratch, 0x11223344, 0x2468ACE0 };
            for (int i = 0; i < expected.Length; i++)
                if (Marshal.ReadInt32(new IntPtr(scratch + 0x100 + i * 4)) != expected[i])
                    throw new InvalidOperationException("League register mismatch " + variant + "/" + i);
            if (Marshal.ReadInt32(new IntPtr(scratch + 0x11C)) != Marshal.ReadInt32(new IntPtr(scratch + 0x140))
                || (Marshal.ReadInt32(new IntPtr(scratch + 0x120)) & 0x8D5) != 0x44
                || Marshal.PtrToStructure<double>(new IntPtr(scratch + 0x128)) != 1)
                throw new InvalidOperationException("League stack/flags/FPU mismatch.");
        };
        Action reset = () => Marshal.Copy(new byte[20 + 4096 * 40], 0, new IntPtr(state), 20 + 4096 * 40);
        run(0); run(1); run(4); run(2); run(3);
        run(5); run(6);
        if (Marshal.ReadInt32(new IntPtr(state + 4)) != 7 || Marshal.ReadInt32(new IntPtr(state + 12)) != 2
            || Marshal.ReadInt32(new IntPtr(state + 16)) != 0 || Marshal.ReadInt32(new IntPtr(scratch + 0x80)) != scratch)
            throw new InvalidOperationException("League counters/call relocation mismatch.");
        int[] kinds = { 1, 2, 3, 2, 3, 4, 4 };
        for (int i = 0; i < kinds.Length; i++)
        {
            IntPtr entry = new IntPtr(state + 20 + i * 40);
            if (Marshal.ReadInt32(entry) != kinds[i] || Marshal.ReadInt32(entry, 4) == 0
                || Marshal.ReadInt32(entry, 12) != 164 || Marshal.ReadInt32(entry, 16) != 2008)
                throw new InvalidOperationException("League event mismatch " + i);
        }
        if (Marshal.ReadInt32(new IntPtr(state + 20 + 24)) != -1
            || Marshal.ReadInt32(new IntPtr(state + 20 + 32)) != 164
            || Marshal.ReadInt32(new IntPtr(state + 20 + 36)) != 2008
            || Marshal.ReadInt32(new IntPtr(state + 20 + 40 + 24)) != 0
            || Marshal.ReadInt32(new IntPtr(state + 20 + 120 + 24)) != 1
            || Marshal.ReadInt32(new IntPtr(state + 20 + 80 + 28)) != 1
            || Marshal.ReadInt32(new IntPtr(state + 20 + 160 + 28)) != 0)
            throw new InvalidOperationException("League mode/result/schedule mismatch.");
        for (int i = 5; i < 7; i++)
        {
            int entry = state + 20 + i * 40;
            if (Marshal.ReadInt32(new IntPtr(entry + 20)) != 0x11223344
                || Marshal.ReadInt32(new IntPtr(entry + 24)) != 3191021
                || Marshal.ReadInt32(new IntPtr(entry + 28)) != 1
                || Marshal.ReadInt32(new IntPtr(entry + 32)) != ((2026 << 16) | 136)
                || Marshal.ReadInt32(new IntPtr(entry + 36)) != 51)
                throw new InvalidOperationException("Successful save identity mismatch.");
        }
        reset();
        byte[] successTail = new byte[saveSuccess.Length - 7];
        Array.Copy(saveSuccess, 7, successTail, 0, successTail.Length);
        put(scratch + 0x1400, successTail);
        put(scratch + 0x2000, saveFailure);
        for (int variant = 0; variant < 2; variant++)
        {
            int bodyAddress = scratch + 0x3000 + variant * 128;
            var body = new List<byte>(new byte[] {
                0x55,0x8B,0xEC,0x81,0xEC,0xEC,2,0,0,0x64,0xA1,0,0,0,0,
                0x89,0x45,0xF4,0x53,0x56,0x57,0xB8,0x44,0x33,0x22,0x11,0xE9 });
            body.AddRange(BitConverter.GetBytes(unchecked((variant == 0 ? code + 0x3000 : scratch + 0x2000)
                - (bodyAddress + body.Count + 4))));
            put(bodyAddress, body.ToArray());
            int driverAddress = scratch + 0x3200 + variant * 128;
            var driver = new List<byte>(new byte[] { 0x6A,0,0x6A,0,0x6A,0,0xE8 });
            driver.AddRange(BitConverter.GetBytes(unchecked(bodyAddress - (driverAddress + driver.Count + 4))));
            driver.Add(0xC3);
            put(driverAddress, driver.ToArray());
            var invoke = (Getter)Marshal.GetDelegateForFunctionPointer(new IntPtr(driverAddress), typeof(Getter));
            int result = invoke(0, 0);
            if (result != (variant == 0 ? 0x11223301 : 0x11223300)
                || Marshal.ReadInt32(new IntPtr(state + 4)) != 1)
                throw new InvalidOperationException("Original save success/failure epilogue or cleanup mismatch.");
        }
        reset();
        Marshal.WriteInt32(new IntPtr(state), 1);
        run(1);
        if (Marshal.ReadInt32(new IntPtr(state)) != 1 || Marshal.ReadInt32(new IntPtr(state + 8)) != 1
            || Marshal.ReadInt32(new IntPtr(state + 12)) != 1 || Marshal.ReadInt32(new IntPtr(state + 16)) != 1)
            throw new InvalidOperationException("League contention must fail closed without releasing another owner's lock.");
        reset();
        for (int i = 0; i < 4096; i++) run(0);
        run(0);
        if (Marshal.ReadInt32(new IntPtr(state)) != 0 || Marshal.ReadInt32(new IntPtr(state + 4)) != 4096
            || Marshal.ReadInt32(new IntPtr(state + 8)) != 1)
            throw new InvalidOperationException("League capacity handling mismatch.");
        reset();
        run(1);
        if (Marshal.ReadInt32(new IntPtr(state + 16)) != 1)
            throw new InvalidOperationException("Unmatched/exceptional load must remain blocked.");
        Console.WriteLine("PASS: league x86 load/annual/save, original success/failure epilogues and SEH/stack cleanup, ABI/FPU, contention, capacity and unmatched load.");
    }

    private static void Relocate(byte[] bytes, int offset, int relocation)
    {
        Array.Copy(BitConverter.GetBytes(unchecked(BitConverter.ToInt32(bytes, offset) + relocation)),
            0, bytes, offset, 4);
    }

    private static void TestPa(string path)
    {
        IntPtr memory = VirtualAlloc(new IntPtr(0x10000000), new UIntPtr(12288), 0x3000, 0x04);
        if (memory != new IntPtr(0x10000000)) throw new InvalidOperationException("Cannot allocate PA fixture.");
        IntPtr log = VirtualAlloc(new IntPtr(0x11000000), new UIntPtr(4096 * 416), 0x3000, 0x04);
        if (log != new IntPtr(0x11000000)) throw new InvalidOperationException("Cannot allocate PA journal fixture.");
        Action<uint> resetState = seed =>
        {
            Marshal.Copy(new byte[36], 0, memory, 36);
            Marshal.WriteInt32(memory, unchecked((int)seed));
            Marshal.WriteInt32(memory, 32, log.ToInt32());
        };
        IntPtr player = IntPtr.Add(memory, 0x200);
        IntPtr profile = IntPtr.Add(memory, 0x400);
        IntPtr snapshot = IntPtr.Add(memory, 0x600);
        IntPtr code = IntPtr.Add(memory, 0x1000);
        IntPtr continuation = IntPtr.Add(memory, 0x1F00);
        IntPtr stubAddress = IntPtr.Add(memory, 0x2000);
        var stub = new List<byte>();
        Action<byte[]> emit = bytes => stub.AddRange(bytes);
        Action<int> integer = value => emit(BitConverter.GetBytes(value));
        Action<byte, int> store = (operand, offset) =>
        {
            emit(new byte[] { 0x89, operand });
            integer(snapshot.ToInt32() + offset);
        };
        emit(new byte[] { 0x55, 0x53, 0x56, 0x57, 0x8B, 0x74, 0x24, 0x14,
            0x8B, 0x6C, 0x24, 0x18, 0x8B, 0x4C, 0x24, 0x1C, 0xB8 });
        integer(0x12345678);
        emit(new byte[] { 0xBB }); integer(0x13579BDF);
        emit(new byte[] { 0xBF }); integer(0x2468ACE0);
        emit(new byte[] { 0xBA }); integer(0x11223344);
        emit(new byte[] { 0xD9, 0xE8, 0x3B, 0xD2, 0x9C, 0x8F, 0x05 });
        integer(snapshot.ToInt32());
        emit(new byte[] { 0xE8 });
        integer(unchecked(code.ToInt32() - (stubAddress.ToInt32() + stub.Count + 4)));
        emit(new byte[] { 0x9C, 0x8F, 0x05 }); integer(snapshot.ToInt32() + 4);
        store(0x05, 8); store(0x1D, 12); store(0x0D, 16);
        store(0x35, 20); store(0x3D, 24); store(0x2D, 28); store(0x15, 32);
        emit(new byte[] { 0xDD, 0x1D }); integer(snapshot.ToInt32() + 40);
        emit(new byte[] { 0x5F, 0x5E, 0x5B, 0x5D, 0xC3 });
        // The native age virtual has one callee-cleaned date argument. No calls into FM in this fixture.
        while (stub.Count < 0x200) emit(new byte[] { 0x90 });
        emit(new byte[] { 0xA1 }); integer(memory.ToInt32() + 0x100);
        emit(new byte[] { 0xC2, 0x04, 0 });
        Marshal.Copy(stub.ToArray(), 0, stubAddress, stub.Count);
        MakeExecutable(stubAddress);
        Training training = (Training)Marshal.GetDelegateForFunctionPointer(stubAddress, typeof(Training));
        var playerBytes = new byte[512];
        var profileBytes = new byte[128];
        for (int i = 0; i < playerBytes.Length; i++) playerBytes[i] = 0xA5;
        for (int i = 0; i < profileBytes.Length; i++) profileBytes[i] = 0xB6;
        Array.Copy(BitConverter.GetBytes(0x015AB414), playerBytes, 4);
        Array.Copy(BitConverter.GetBytes(memory.ToInt32() + 0xB00), 0, playerBytes, 4, 4);
        Marshal.WriteInt32(memory, 0xB04, 0xE8);
        Array.Copy(BitConverter.GetBytes(0), 0, playerBytes, 0xE8, 4);
        Array.Copy(BitConverter.GetBytes(memory.ToInt32() + 0xE00), 0, playerBytes, 0xEC, 4);
        Array.Copy(BitConverter.GetBytes(memory.ToInt32() + 0xC00), 0, playerBytes, 0x1B8, 4);
        Array.Copy(BitConverter.GetBytes(memory.ToInt32() + 0xD00), 0, playerBytes, 0xCC, 4);
        Marshal.WriteInt32(memory, 0xE88, memory.ToInt32() + 0x2200);
        Action<int, int, int, int> setFactors = (age, pro, amb, rawDet) =>
        {
            Marshal.WriteInt32(memory, 0x100, age);
            Marshal.WriteByte(memory, 0xC20, unchecked((byte)pro));
            Marshal.WriteByte(memory, 0xC1D, unchecked((byte)amb));
            Marshal.WriteByte(memory, 0xD69, unchecked((byte)rawDet));
        };
        setFactors(23, 10, 12, 50);
        Array.Copy(BitConverter.GetBytes(12345), 0, playerBytes, 0x100, 4);
        // Use the real actor layout, independently of the payload builder's constants.
        Array.Copy(BitConverter.GetBytes(memory.ToInt32() + 0x800), 0, playerBytes, 0x118, 4);
        Array.Copy(BitConverter.GetBytes(memory.ToInt32() + 0x840), 0, playerBytes, 0x11C, 4);
        Array.Copy(BitConverter.GetBytes(1), 0, playerBytes, 0x2C, 4);
        Array.Copy(BitConverter.GetBytes(1), 0, playerBytes, 0x30, 4);
        string firstName = "\u0141ukasz";
        string lastName = "Kowalski";
        Action<int, int, int, string> setName = (nameOffset, bufferOffset, textOffset, text) =>
        {
            Marshal.WriteInt32(memory, nameOffset + 0x24, memory.ToInt32() + bufferOffset);
            Marshal.WriteInt16(memory, bufferOffset + 4, (short)text.Length);
            Marshal.WriteInt32(memory, bufferOffset + 8, memory.ToInt32() + textOffset);
            byte[] bytes = System.Text.Encoding.Unicode.GetBytes(text);
            Marshal.Copy(bytes, 0, IntPtr.Add(memory, textOffset), bytes.Length);
        };
        setName(0x800, 0x880, 0x900, firstName);
        setName(0x840, 0x8A0, 0xA00, lastName);
        Action<IntPtr, uint, int, int> checkLog = (entry, epoch, ca, before) =>
        {
            if (Marshal.ReadInt32(entry) != 12345 || unchecked((uint)Marshal.ReadInt32(entry, 4)) != epoch
                || Marshal.ReadInt16(entry, 8) != before || Marshal.ReadInt16(entry, 10) != before + 1
                || Marshal.ReadInt32(entry, 12) != 0 || Marshal.ReadInt32(entry, 16) != firstName.Length
                || Marshal.ReadInt32(entry, 20) != lastName.Length || Marshal.ReadInt32(entry, 24) != player.ToInt32()
                || Marshal.ReadInt32(entry, 28) != ca
                || Marshal.PtrToStringUni(IntPtr.Add(entry, 32), firstName.Length) != firstName
                || Marshal.PtrToStringUni(IntPtr.Add(entry, 224), lastName.Length) != lastName)
                throw new InvalidOperationException("Incorrect named PA journal record.");
        };
        Action<short, short, uint> reset = (ca, pa, oldEpoch) =>
        {
            Array.Copy(BitConverter.GetBytes(ca), 0, playerBytes, 0x14, 2);
            Array.Copy(BitConverter.GetBytes(pa), 0, playerBytes, 0x16, 2);
            // The old implementation confused real PA with CA and wrote this unrelated field.
            Array.Copy(BitConverter.GetBytes((short)195), 0, playerBytes, 0x1E, 2);
            Array.Copy(BitConverter.GetBytes(oldEpoch), 0, profileBytes, 4, 4);
            Marshal.Copy(playerBytes, 0, player, playerBytes.Length);
            Marshal.Copy(profileBytes, 0, profile, profileBytes.Length);
        };
        Action<uint> checkRegisters = epoch =>
        {
            if (Marshal.ReadInt32(snapshot) != Marshal.ReadInt32(snapshot, 4)
                || Marshal.ReadInt32(snapshot, 8) != 0x12345678
                || Marshal.ReadInt32(snapshot, 12) != 0x13579BDF
                || unchecked((uint)Marshal.ReadInt32(snapshot, 16)) != epoch
                || Marshal.ReadInt32(snapshot, 20) != player.ToInt32()
                || Marshal.ReadInt32(snapshot, 24) != 0x2468ACE0
                || Marshal.ReadInt32(snapshot, 28) != profile.ToInt32()
                || Marshal.ReadInt32(snapshot, 32) != 0x015AB414
                || BitConverter.Int64BitsToDouble(Marshal.ReadInt64(snapshot, 40)) != 1.0)
                throw new InvalidOperationException("PA hook changed registers, flags or FPU.");
        };
        int cases = 0;
        using (var reader = new BinaryReader(File.OpenRead(path)))
        while (reader.BaseStream.Position < reader.BaseStream.Length)
        {
            int chance = reader.ReadInt32();
            int length = reader.ReadInt32();
            byte[] payload = reader.ReadBytes(length);
            if (payload.Length != length) throw new InvalidOperationException("Truncated PA payload.");
            Array.Copy(BitConverter.GetBytes(unchecked(continuation.ToInt32() - (code.ToInt32() + length))),
                0, payload, length - 4, 4);
            uint old;
            if (!VirtualProtect(code, new UIntPtr(4096), 0x04, out old))
                throw new InvalidOperationException("Cannot write PA fixture code.");
            Marshal.Copy(payload, 0, code, payload.Length);
            Marshal.WriteByte(continuation, 0xC3);
            MakeExecutable(code);
            foreach (short ca in new short[] { -1, 0, 1, 50, 190, 199, 200, 201 })
            foreach (short pa in new short[] { -10, 0, 1, 50, 189, 190, 194, 195, 199, 200, 201 })
            foreach (uint oldEpoch in new uint[] { 0, 1, 100, uint.MaxValue })
            foreach (uint epoch in new uint[] { 0, 1, 2, 101, uint.MaxValue })
            {
                resetState(1);
                reset(ca, pa, oldEpoch);
                uint seed = 1;
                bool invalid = ca < 1 || ca > 200 || pa < 1 || pa > 200;
                bool eligible = epoch > oldEpoch && !invalid && pa < 200 && pa >= ca && pa - ca < 5;
                bool increased = chance > 0 && eligible && NextRoll(ref seed) < chance * 100;
                training(player, profile, epoch);
                checkRegisters(epoch);
                if (Marshal.ReadInt16(player, 0x16) != pa + (increased ? 1 : 0)
                    || unchecked((uint)Marshal.ReadInt32(profile, 4)) != epoch
                    || Marshal.ReadInt32(memory, 4) != (chance > 0 && eligible ? 1 : 0)
                    || Marshal.ReadInt32(memory, 8) != (increased ? 1 : 0)
                    || Marshal.ReadInt32(memory, 12) != (chance > 0 && epoch > oldEpoch && invalid ? 1 : 0))
                    throw new InvalidOperationException("PA mismatch: chance=" + chance + ", CA=" + ca
                        + ", PA=" + pa + ", epoch=" + epoch + ", old=" + oldEpoch);
                if (Marshal.ReadInt32(memory, 16) != 0 || Marshal.ReadInt32(memory, 20) != (increased ? 1 : 0)
                    || Marshal.ReadInt32(memory, 24) != 0 || Marshal.ReadInt32(memory, 28) != 0)
                    throw new InvalidOperationException("Incorrect PA journal counters.");
                if (increased) checkLog(log, epoch, ca, pa);
                var actualPlayer = new byte[playerBytes.Length];
                var actualProfile = new byte[128];
                Marshal.Copy(player, actualPlayer, 0, actualPlayer.Length);
                Marshal.Copy(profile, actualProfile, 0, 128);
                for (int i = 0; i < actualPlayer.Length; i++)
                {
                    if (i != 0x16 && i != 0x17 && actualPlayer[i] != playerBytes[i])
                        throw new InvalidOperationException("PA hook changed another player field.");
                    if (i < actualProfile.Length && (i < 4 || i >= 8) && actualProfile[i] != profileBytes[i])
                        throw new InvalidOperationException("PA hook changed another training field.");
                }
                cases++;
            }
            foreach (uint initialSeed in new uint[] { 1, 0x12345678, SeedForOutput(0xFFFFFFFE) })
            {
                resetState(initialSeed);
                uint seed = initialSeed;
                int expected = 0;
                for (uint epoch = 1; epoch <= 1000; epoch++)
                {
                    reset(50, 50, epoch - 1);
                    bool increasedNow = chance > 0 && NextRoll(ref seed) < chance * 100;
                    if (increasedNow) expected++;
                    training(player, profile, epoch);
                    checkRegisters(epoch);
                    if (Marshal.ReadInt16(player, 0x16) != 50 + (increasedNow ? 1 : 0)
                        || Marshal.ReadInt16(player, 0x14) != 50 || Marshal.ReadInt16(player, 0x1E) != 195)
                        throw new InvalidOperationException("Invalid per-roll PA.");
                    int rolls = Marshal.ReadInt32(memory, 4);
                    int growth = Marshal.ReadInt32(memory, 8);
                    if (rolls != (chance > 0 ? epoch : 0) || growth != expected)
                        throw new InvalidOperationException("PA RNG does not match reference sequence.");
                    training(player, profile, epoch);
                    if (Marshal.ReadInt32(memory, 4) != rolls || Marshal.ReadInt32(memory, 8) != growth)
                        throw new InvalidOperationException("Repeated epoch generated another PA roll.");
                }
                if (chance > 0 && unchecked((uint)Marshal.ReadInt32(memory)) != seed)
                    throw new InvalidOperationException("Unexpected final RNG seed.");
            }
            if (chance == 8)
            {
                using (var factors = new BinaryReader(File.OpenRead(
                    Path.Combine(Path.GetDirectoryName(path), "pa-model-cases.bin"))))
                while (factors.BaseStream.Position < factors.BaseStream.Length)
                {
                    int age = factors.ReadInt32(), pro = factors.ReadInt32(), amb = factors.ReadInt32();
                    int rawDet = factors.ReadInt32(), basisPoints = factors.ReadInt32();
                    foreach (int roll in new int[] { Math.Max(0, basisPoints - 1), Math.Max(0, basisPoints), 9999 })
                    {
                        uint seed = SeedForOutput((uint)roll + 1);
                        resetState(seed);
                        reset(90, 90, 0);
                        setFactors(age, pro, amb, rawDet);
                        training(player, profile, 1);
                        checkRegisters(1);
                        bool valid = basisPoints >= 0;
                        bool success = valid && roll < basisPoints;
                        if (Marshal.ReadInt16(player, 0x16) != (success ? 91 : 90)
                            || Marshal.ReadInt32(memory, 4) != (valid ? 1 : 0)
                            || Marshal.ReadInt32(memory, 12) != (valid ? 0 : 1)
                            || Marshal.ReadInt32(memory, 8) != (success ? 1 : 0)
                            || (!valid && unchecked((uint)Marshal.ReadInt32(memory)) != seed))
                            throw new InvalidOperationException("PA factor/threshold mismatch: age=" + age
                                + ", pro=" + pro + ", amb=" + amb + ", rawDet=" + rawDet
                                + ", bp=" + basisPoints + ", roll=" + roll);
                        if (success) checkLog(log, 1, 90, 90);
                        cases++;
                    }
                }
                setFactors(23, 10, 12, 50);
                foreach (int missingOffset in new int[] { 0xCC, 0x1B8 })
                {
                    resetState(1);
                    reset(90, 90, 0);
                    Marshal.WriteInt32(player, missingOffset, 0);
                    training(player, profile, 1);
                    checkRegisters(1);
                    if (Marshal.ReadInt16(player, 0x16) != 90 || Marshal.ReadInt32(memory, 4) != 0
                        || Marshal.ReadInt32(memory, 12) != 1 || Marshal.ReadInt32(memory) != 1)
                        throw new InvalidOperationException("Missing PA model source was not reported.");
                }
                reset(90, 90, 0);
                resetState(1);
                setFactors(18, 20, 20, 100);
                for (uint epoch = 1; epoch <= 1000 && Marshal.ReadInt16(player, 0x16) < 200; epoch++)
                {
                    short pa = Marshal.ReadInt16(player, 0x16);
                    reset(pa, pa, epoch - 1);
                    training(player, profile, epoch);
                }
                if (Marshal.ReadInt32(memory, 8) <= 5)
                    throw new InvalidOperationException("Unexpected seasonal growth cap.");
                setFactors(23, 10, 12, 50);
            }
            if (chance == 100)
            {
                resetState(1);
                reset(199, 199, 0);
                for (uint epoch = 1; epoch <= 100; epoch++) training(player, profile, epoch);
                if (Marshal.ReadInt16(player, 0x16) != 200 || Marshal.ReadInt32(memory, 8) != 1)
                    throw new InvalidOperationException("PA cap failed.");
                reset(190, 190, 0);
                resetState(1);
                var threads = new Thread[16];
                for (int i = 0; i < threads.Length; i++)
                {
                    threads[i] = new Thread(() => training(player, profile, 1));
                    threads[i].Start();
                }
                foreach (var thread in threads) thread.Join();
                if (Marshal.ReadInt16(player, 0x16) != 191 || Marshal.ReadInt32(memory, 4) != 1
                    || Marshal.ReadInt32(memory, 8) != 1)
                    throw new InvalidOperationException("Concurrent epoch generated extra growth.");
                checkLog(log, 1, 190, 190);
                resetState(1);
                for (uint epoch = 1; epoch <= 4100; epoch++)
                {
                    reset(50, 50, epoch - 1);
                    training(player, profile, epoch);
                    if (Marshal.ReadInt16(player, 0x16) != 51)
                        throw new InvalidOperationException("Journal overflow prevented PA growth.");
                }
                if (Marshal.ReadInt32(memory, 20) != 4096 || Marshal.ReadInt32(memory, 28) != 4
                    || Marshal.ReadInt32(memory, 8) != 4100 || Marshal.ReadInt32(memory, 16) != 0)
                    throw new InvalidOperationException("Journal overflow was not reported.");
                for (int i = 0; i < 4096; i++) checkLog(IntPtr.Add(log, i * 416), (uint)i + 1, 50, 50);
                Marshal.WriteInt32(memory, 24, 4096);
                reset(60, 60, 4100);
                training(player, profile, 4101);
                checkLog(log, 4101, 60, 60);
                if (Marshal.ReadInt32(memory, 20) != 4097 || Marshal.ReadInt32(memory, 28) != 4)
                    throw new InvalidOperationException("Journal did not wrap after acknowledgement.");
                resetState(1);
                Marshal.WriteInt32(memory, 16, 1);
                reset(70, 70, 0);
                training(player, profile, 1);
                if (Marshal.ReadInt16(player, 0x16) != 71 || Marshal.ReadInt32(memory, 20) != 0
                    || Marshal.ReadInt32(memory, 28) != 1 || Marshal.ReadInt32(memory, 16) != 1)
                    throw new InvalidOperationException("Contended journal lock blocked or was overwritten.");
                resetState(1);
                // ACTUAL_PLAYER_AND_NON_PLAYER: PERSON +0x124, not +0xEC.
                // Replay the crash's low value in the old, unrelated name field.
                var ordinaryPlayer = (byte[])playerBytes.Clone();
                Marshal.WriteInt32(memory, 0xB04, 0x120);
                Array.Copy(BitConverter.GetBytes(0x015EA0D4), playerBytes, 4);
                Array.Copy(BitConverter.GetBytes(0), 0, playerBytes, 0x120, 4);
                Array.Copy(BitConverter.GetBytes(memory.ToInt32() + 0xE00), 0, playerBytes, 0x124, 4);
                Array.Copy(BitConverter.GetBytes(memory.ToInt32() + 0xC00), 0, playerBytes, 0x1F0, 4);
                Array.Copy(BitConverter.GetBytes(12345), 0, playerBytes, 0x138, 4);
                Array.Copy(BitConverter.GetBytes(memory.ToInt32() + 0x800), 0, playerBytes, 0x150, 4);
                Array.Copy(BitConverter.GetBytes(memory.ToInt32() + 0x840), 0, playerBytes, 0x154, 4);
                Array.Copy(BitConverter.GetBytes(0x10), 0, playerBytes, 0x118, 4);
                Array.Copy(BitConverter.GetBytes(1), 0, playerBytes, 0x11C, 4);
                Array.Copy(BitConverter.GetBytes(-999), 0, playerBytes, 0x100, 4);
                reset(80, 80, 0);
                training(player, profile, 1);
                checkLog(log, 1, 80, 80);
                if (Marshal.ReadInt16(player, 0x16) != 81 || Marshal.ReadInt32(memory, 16) != 0
                    || Marshal.ReadInt32(snapshot, 28) != profile.ToInt32()
                    || Marshal.ReadInt32(snapshot, 32) != 0x015EA0D4)
                    throw new InvalidOperationException("Combined player/staff PA crash regression.");
                // A nonzero vtordisp must affect names, but not the PERSON UID.
                resetState(1);
                Array.Copy(BitConverter.GetBytes(8), 0, playerBytes, 0x120, 4);
                Array.Copy(BitConverter.GetBytes(memory.ToInt32() + 0xC00), 0, playerBytes, 0x1E8, 4);
                Array.Copy(BitConverter.GetBytes(memory.ToInt32() + 0x800), 0, playerBytes, 0x148, 4);
                Array.Copy(BitConverter.GetBytes(memory.ToInt32() + 0x840), 0, playerBytes, 0x14C, 4);
                Array.Copy(BitConverter.GetBytes(0x10), 0, playerBytes, 0x150, 4);
                reset(80, 80, 1);
                training(player, profile, 2);
                checkLog(log, 2, 80, 80);
                playerBytes = ordinaryPlayer;
                Marshal.WriteInt32(memory, 0xB04, 0xE8);
                resetState(1);
                reset(80, 80, 0);
                training(player, profile, 1);
                setName(0x800, 0x880, 0x900, "Changed");
                checkLog(log, 1, 80, 80);
                resetState(1);
                reset(80, 80, 1);
                Marshal.WriteInt32(player, 0x118, 0);
                training(player, profile, 2);
                if (Marshal.ReadInt32(log, 12) != 1 || Marshal.ReadInt32(log, 16) != 0
                    || Marshal.PtrToStringUni(IntPtr.Add(log, 224), lastName.Length) != lastName)
                    throw new InvalidOperationException("Missing name was not reported.");
                resetState(1);
                reset(80, 80, 1);
                Marshal.WriteInt32(player, 0x11C, 0);
                training(player, profile, 2);
                if (Marshal.ReadInt32(log, 12) != 1 || Marshal.ReadInt32(log, 20) != 0
                    || Marshal.ReadInt16(player, 0x16) != 81)
                    throw new InvalidOperationException("Missing surname prevented growth or was not reported.");
                resetState(1);
                setName(0x800, 0x880, 0x900, new string('A', 100));
                reset(90, 90, 2);
                training(player, profile, 3);
                if (Marshal.ReadInt32(log, 12) != 2 || Marshal.ReadInt32(log, 16) != 96
                    || Marshal.PtrToStringUni(IntPtr.Add(log, 32), 96) != new string('A', 96))
                    throw new InvalidOperationException("Long name was not bounded and reported.");
                setName(0x800, 0x880, 0x900, firstName);
                resetState(1);
                reset(132, 193, 0);
                training(player, profile, 1);
                checkRegisters(1);
                if (Marshal.ReadInt16(player, 0x14) != 132 || Marshal.ReadInt16(player, 0x16) != 193
                    || Marshal.ReadInt16(player, 0x1E) != 195 || Marshal.ReadInt32(memory, 4) != 0
                    || Marshal.ReadInt32(memory, 8) != 0 || Marshal.ReadInt32(memory, 20) != 0)
                    throw new InvalidOperationException("Yontcha regression: an ineligible player changed.");
                resetState(1);
                reset(189, 193, 0);
                training(player, profile, 1);
                checkRegisters(1);
                checkLog(log, 1, 189, 193);
                if (Marshal.ReadInt16(player, 0x14) != 189 || Marshal.ReadInt16(player, 0x16) != 194
                    || Marshal.ReadInt16(player, 0x1E) != 195)
                    throw new InvalidOperationException("Eligible growth modified the wrong ability field.");
                resetState(1);
                reset(90, 90, 3);
                training(player, profile, 4);
                checkLog(log, 4, 90, 90);
                byte[] result = new byte[416];
                Marshal.Copy(log, result, 0, result.Length);
                File.WriteAllBytes(Path.Combine(Path.GetDirectoryName(path), "pa-event.bin"), result);
            }
        }
        Console.WriteLine("PASS: actual x86 PA; " + cases + " boundary cases, RNG, epochs, cap, ABI, concurrency, dynamic PERSON layout, combined player/staff crash replay, vtordisp, named snapshots, overflow and wrap.");
    }

    private static void MakeExecutable(IntPtr address)
    {
        uint old;
        if (!VirtualProtect(address, new UIntPtr(4096), 0x20, out old)
            || !FlushInstructionCache(GetCurrentProcess(), address, new UIntPtr(4096)))
            throw new InvalidOperationException("Cannot protect/flush PA fixture code.");
    }

    private static int NextRoll(ref uint seed)
    {
        while (true)
        {
            seed ^= seed << 13;
            seed ^= seed >> 17;
            seed ^= seed << 5;
            uint value = unchecked(seed - 1);
            if (value < 4294960000) return (int)(value % 10000);
        }
    }

    private static uint SeedForOutput(uint value)
    {
        uint result = 0;
        for (int bit = 0; bit < 32; bit++)
            result |= (((value >> bit) & 1) ^ (bit >= 5 ? (result >> (bit - 5)) & 1 : 0)) << bit;
        value = result;
        result = 0;
        for (int bit = 31; bit >= 0; bit--)
            result |= (((value >> bit) & 1) ^ (bit + 17 < 32 ? (result >> (bit + 17)) & 1 : 0)) << bit;
        value = result;
        result = 0;
        for (int bit = 0; bit < 32; bit++)
            result |= (((value >> bit) & 1) ^ (bit >= 13 ? (result >> (bit - 13)) & 1 : 0)) << bit;
        return result;
    }
}
