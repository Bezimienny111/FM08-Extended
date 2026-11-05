using System;
using System.IO;
using System.Collections.Generic;
using System.Runtime.InteropServices;

internal static partial class NativeFixture
{
    private static void TestModernRules(string path)
    {
        const int state = 0x10000000, code = 0x10100000, diagnostic = 0x10200000;
        const int objects = 0x10300000, aging = 0x10400000, scratch = 0x10500000;
        foreach (int address in new int[] { state, code, diagnostic, objects, aging, scratch, 0x10600000, 0x10700000, 0x10800000 })
            if (VirtualAlloc(new IntPtr(address), new UIntPtr(0x10000), 0x3000, 0x40) != new IntPtr(address))
                throw new InvalidOperationException("Cannot allocate modern native fixture.");
        Action<int, byte[]> put = (address, value) => Marshal.Copy(value, 0, new IntPtr(address), value.Length);
        Action<int, int> integer = (address, value) => Marshal.WriteInt32(new IntPtr(address), value);
        Func<int, int> word = address => Marshal.ReadInt32(new IntPtr(address));
        using (var input = new BinaryReader(File.OpenRead(path)))
        {
            byte[] writer = input.ReadBytes(input.ReadInt32());
            int calendarReferences = 0;
            for (int i = 0; i <= writer.Length - 4; i++)
                if (BitConverter.ToInt32(writer, i) == 0x1B1EE16)
                {
                    Array.Copy(BitConverter.GetBytes(scratch + 0x202), 0, writer, i, 4);
                    calendarReferences++;
                    i += 3;
                }
            if (calendarReferences != 1) throw new InvalidOperationException("Writer calendar relocation.");
            int identityReferences = 0;
            for (int i = 0; i <= writer.Length - 4; i++)
            {
                int source = BitConverter.ToInt32(writer, i);
                int offset = source == 0x1911160 ? 0 : source == 0x1911168 ? 4 : source == 0x191116C ? 8 : -1;
                if (offset < 0) continue;
                Array.Copy(BitConverter.GetBytes(scratch + 0x600 + offset), 0, writer, i, 4);
                identityReferences++;
                i += 3;
            }
            if (identityReferences != 6) throw new InvalidOperationException("Writer identity relocation.");
            put(code, writer);
            int count = input.ReadInt32();
            if (count != 8) throw new InvalidOperationException("Aging hook count.");
            for (int i = 0; i < count; i++)
            {
                byte[] hook = input.ReadBytes(input.ReadInt32());
                TestAgingHook(i, aging + i * 256, hook, code + 0x4000 + i * 512, scratch);
            }
            byte[] annual = input.ReadBytes(input.ReadInt32());
            for(int i=0;i<=annual.Length-4;i++)
            {
                int value=BitConverter.ToInt32(annual,i);
                if(value!=0x1B1EE14 && value!=0x1B1EE16) continue;
                Array.Copy(BitConverter.GetBytes(scratch+0x200+value-0x1B1EE14),0,annual,i,4);
                i+=3;
            }
            int calls=0;
            for(int i=0;i<=annual.Length-5;i++)
            {
                if(annual[i]!=0xE8 && annual[i]!=0xE9) continue;
                int next=0x10600000+i+5, target=unchecked(next+BitConverter.ToInt32(annual,i+1));
                int destination=target==0xE23440?scratch+0x1000:target==0xE2611A?scratch+0x1100:0;
                if(destination==0) continue;
                Array.Copy(BitConverter.GetBytes(unchecked(destination-next)),0,annual,i+1,4);
                calls++; i+=4;
            }
            if(calls!=2) throw new InvalidOperationException("Integrated annual relocation.");
            put(0x10600000,annual);
            TestAgingControlFlow(input, count, scratch);
        }
        integer(diagnostic + 12, 2);
        Action reset = () =>
        {
            put(state, new byte[36864]);
            integer(state, 1); integer(state + 4, 2); integer(state + 8, 2007); integer(state + 12, 2007);
            put(state + 32, BitConverter.GetBytes(1.7)); put(state + 40, BitConverter.GetBytes(0.5));
            put(state + 48, BitConverter.GetBytes(100.0));
            integer(diagnostic + 12, 2); integer(diagnostic + 16, 0); integer(diagnostic + 8, 0);
            Marshal.WriteInt16(new IntPtr(scratch + 0x202), 2009);
            for (int i = 0; i < 42; i++)
            {
                int row = state + 64 + i * 48, comp = objects + i * 1024, nation = comp + 256;
                integer(row, i + 1); integer(row + 4, i + 100);
                integer(row + 8, comp); integer(row + 12, nation);
                put(row + 16, BitConverter.GetBytes(5.0));
                integer(row + 24, 10); integer(row + 28, 0x12345678);
                integer(comp, 0x12345678); integer(comp + 0x14, i + 1); integer(comp + 0x64, nation);
                Marshal.WriteInt16(new IntPtr(comp + 0x84), 10);
                integer(nation + 0x14, i + 100); integer(nation + 0x1C0, comp + 768);
                Marshal.WriteByte(new IntPtr(nation + 0x1C4), 6);
                for (int j = 0; j < 6; j++) put(comp + 768 + j * 4, BitConverter.GetBytes(i == 0 ? 0f : 20f));
            }
        };
        var call = (Getter)Marshal.GetDelegateForFunctionPointer(new IntPtr(code), typeof(Getter));
        Action<int, int> expect = (before, delta) =>
        {
            for (int i = 0; i < 42; i++)
                if (Marshal.ReadInt16(new IntPtr(objects + i * 1024 + 0x84)) != before + (i == 0 ? -delta : delta))
                    throw new InvalidOperationException("Native reputation mismatch " + i);
        };
        for (int mismatch = 0; mismatch < 4; mismatch++)
        {
            reset();
            integer(state + 3012, 1);
            foreach (int[] field in new int[][] {
                new int[] {0,3191021}, new int[] {4,(2026 << 16) | 136}, new int[] {8,51}
            })
            {
                integer(state + 3000 + field[0], field[1]);
                integer(scratch + 0x600 + field[0], field[1] + (mismatch == field[0] / 4 ? 1 : 0));
            }
            call(0,0);
            expect(10, mismatch == 3 ? 1 : 0);
            if (mismatch != 3 && (word(state) != 0 || word(state + 16) != 0))
                throw new InvalidOperationException("Wrong career was not blocked natively.");
        }
        Console.WriteLine("Native career token/date/marker guards passed.");
        reset(); integer(state, 0); call(0,0); expect(10,0);
        reset(); Marshal.WriteInt16(new IntPtr(scratch + 0x202), 2008); call(0,0);
        expect(10,0);
        if (word(state + 16) != 0) throw new InvalidOperationException("Writer ran in off-year.");
        reset(); call(0,0); expect(10,1);
        if (word(state + 16) != 42 || word(state + 12) != 2009 || word(state + 20) != 0)
            throw new InvalidOperationException("Native biennial writer counters.");
        for (int i = 0; i < 42; i++)
        {
            int entry = state + 4096 + i * 32;
            if (word(entry) != 2009 || word(entry + 4) != i + 1 || word(entry + 8) != 10
                || word(entry + 12) != (i == 0 ? 9 : 11) || word(entry + 16) != (i == 0 ? 2 : 19)
                || Marshal.PtrToStructure<double>(new IntPtr(entry + 20)) != (i == 0 ? 0 : 100))
                throw new InvalidOperationException("Native league change journal mismatch " + i);
        }
        call(0,0); expect(10,1);
        if (word(state + 16) != 42) throw new InvalidOperationException("Duplicate annual application.");
        Marshal.WriteInt16(new IntPtr(scratch + 0x202), 2011); call(0,0); expect(10,2);
        integer(diagnostic + 12, 3);
        Marshal.WriteInt16(new IntPtr(scratch + 0x202), 2013); call(0,0); expect(10,2);
        if (word(state) != 0 || word(state + 16) != 84) throw new InvalidOperationException("Load did not disarm writer.");
        reset(); Marshal.WriteByte(new IntPtr(objects + 41 * 1024 + 256 + 0x1C4), 5); call(0,0);
        expect(10,0);
        if (word(state + 20) != 1 || word(state + 16) != 0) throw new InvalidOperationException("Partial invalid batch.");
        reset(); put(objects + 41 * 1024 + 768, BitConverter.GetBytes(float.NaN)); call(0,0); expect(10,0);
        if (word(state + 20) != 1) throw new InvalidOperationException("NaN was accepted.");
        reset(); integer(state + 16, 1024 - 41); call(0,0); expect(10,0);
        if (word(state + 20) != 2) throw new InvalidOperationException("Journal capacity not guarded.");
        for (int pass = 0; pass < 6; pass++)
        {
            reset();
            int changed = 0;
            for (int i = 0; i < 42; i++)
            {
                int baseline = 1 + (i + pass) % 20;
                int actual = 1 + (i * 3 + pass) % 20;
                double baselineCoefficient = (i + pass) % 7 == 0 ? 0 : (i + pass) * 0.75;
                float component = pass == 0 ? 0 : pass == 1 ? 100 : (i + pass) * 0.375f;
                int row = state + 64 + i * 48;
                integer(row + 24, baseline);
                put(row + 16, BitConverter.GetBytes(Math.Sqrt(baselineCoefficient)));
                Marshal.WriteInt16(new IntPtr(objects + i * 1024 + 0x84), (short)actual);
                for (int j=0;j<5;j++) put(objects+i*1024+768+j*4, BitConverter.GetBytes(component));
                int target = (int)Math.Floor(Math.Max(1,Math.Min(20,
                    baseline+1.7*(Math.Sqrt(5*(double)component)-Math.Sqrt(baselineCoefficient))))+0.5);
                integer(scratch + 0x400 + i*8, actual + Math.Sign(target-actual));
                integer(scratch + 0x404 + i*8, target);
                if(target!=actual) changed++;
            }
            call(0,0);
            if(word(state+16)!=changed || word(state+20)!=0)
                throw new InvalidOperationException("Native target matrix count.");
            for(int i=0;i<42;i++)
                if(Marshal.ReadInt16(new IntPtr(objects+i*1024+0x84))!=word(scratch+0x400+i*8)
                    || word(state+64+i*48+36)!=word(scratch+0x404+i*8))
                    throw new InvalidOperationException("Native target formula mismatch.");
        }
        reset(); call(0,0);
        integer(diagnostic+12,3); call(0,0);
        for(int i=0;i<42;i++) Marshal.WriteInt16(new IntPtr(objects+i*1024+0x84),10);
        call(0,0); expect(10,0);
        integer(state+4,3); integer(state+12,2008); integer(state,1);
        call(0,0); expect(10,1);
        if(word(state+16)!=84) throw new InvalidOperationException("Rollback/rearm did not apply once.");
        reset();
        put(scratch+0x1000,new byte[]{0xC3}); put(scratch+0x1100,new byte[]{0xC3});
        Marshal.WriteInt16(new IntPtr(scratch+0x200),165);
        Marshal.WriteInt16(new IntPtr(scratch+0x1C),165);
        Marshal.WriteInt16(new IntPtr(scratch+0x1E),2009);
        var annualDriver=new List<byte>(new byte[]{0x56,0xBE});
        annualDriver.AddRange(BitConverter.GetBytes(scratch));
        annualDriver.Add(0xE8);
        annualDriver.AddRange(BitConverter.GetBytes(unchecked(0x10600000-(code+0x3000+annualDriver.Count+4))));
        annualDriver.AddRange(new byte[]{0x5E,0xC3});
        put(code+0x3000,annualDriver.ToArray());
        ((Getter)Marshal.GetDelegateForFunctionPointer(new IntPtr(code+0x3000),typeof(Getter)))(0,0);
        expect(10,1);
        if(word(diagnostic+4)!=1 || word(diagnostic+20)!=1 || word(state+16)!=42)
            throw new InvalidOperationException("Integrated annual hook did not execute reputation writer.");
        reset();
        TestWriterRegisters(code, code + 0x2000, scratch);
        Console.WriteLine("PASS: native x86 aging hooks; biennial +/-1, rollback generations, no duplicates, atomic preflight, NaN/capacity guards, register/flags/FPU/SSE preservation.");
    }

    private static void TestAgingHook(int index, int cave, byte[] hook, int driver, int scratch)
    {
        var stub = new List<byte>();
        Action<int> dword = value => stub.AddRange(BitConverter.GetBytes(value));
        stub.AddRange(new byte[] { 0x53,0x55,0x56,0x57,0x81,0xEC }); dword(128);
        foreach (int[] local in new int[][] { new int[] {0x13,35}, new int[] {0x1F,29}, new int[] {0x22,2} })
            stub.AddRange(new byte[] { 0xC6,0x44,0x24,(byte)local[0],(byte)local[1] });
        foreach (int[] local in new int[][] { new int[] {0x2C,29}, new int[] {0x40,40} })
        { stub.AddRange(new byte[] {0xC7,0x44,0x24,(byte)local[0]}); dword(local[1]); }
        foreach (int[] register in new int[][] { new int[] {0xB8,5},new int[] {0xBB,29},new int[] {0xB9,77},
            new int[] {0xBA,99},new int[] {0xBD,40},new int[] {0xBF,29} })
        { stub.Add((byte)register[0]); dword(register[1]); }
        stub.Add(0xE9); dword(unchecked(cave - (driver + stub.Count + 4)));
        int continuation = driver + stub.Count;
        Array.Copy(BitConverter.GetBytes(unchecked(continuation - (cave + hook.Length))), 0, hook, hook.Length - 4, 4);
        if (index == 5 || index == 7)
        { stub.AddRange(new byte[] { 0x8F,0x05 }); dword(scratch + 0x180); }
        foreach (byte operand in new byte[] { 0x05,0x1D,0x0D,0x15,0x2D,0x3D })
        {
            stub.AddRange(new byte[] {0x89,operand});
            dword(scratch + 0x100 + Array.IndexOf(new byte[] {0x05,0x1D,0x0D,0x15,0x2D,0x3D}, operand) * 4);
        }
        stub.AddRange(new byte[] {0x81,0xC4}); dword(128);
        stub.AddRange(new byte[] {0x5F,0x5E,0x5D,0x5B,0xC3});
        Marshal.Copy(stub.ToArray(),0,new IntPtr(driver),stub.Count);
        Marshal.Copy(hook,0,new IntPtr(cave),hook.Length);
        ((Getter)Marshal.GetDelegateForFunctionPointer(new IntPtr(driver),typeof(Getter)))(0,0);
        int[][] expected = {
            new int[] {5,32,35,99,40,29}, new int[] {5,29,77,34,40,29},
            new int[] {32,29,77,32,40,29},
            new int[] {37,29,77,99,40,29}, new int[] {5,29,35,99,40,29},
            new int[] {5,29,77,99,8,29}, new int[] {5,29,77,33,40,32},
            new int[] {37,29,77,99,40,40}
        };
        for (int i=0;i<6;i++)
            if (Marshal.ReadInt32(new IntPtr(scratch + 0x100 + i*4)) != expected[index][i])
                throw new InvalidOperationException("Aging hook register mismatch " + index + "/" + i);
        if ((index == 5 || index == 7) && Marshal.ReadInt32(new IntPtr(scratch + 0x180)) != (index == 5 ? 8 : 37))
            throw new InvalidOperationException("Aging displaced push mismatch.");
    }

    private static void TestAgingControlFlow(BinaryReader input, int count, int scratch)
    {
        const int original = 0xA34E00, bodyAddress = 0x10700000, caves = 0x10800000;
        byte[] body = input.ReadBytes(input.ReadInt32());
        var addresses = new int[count];
        var lengths = new int[count];
        var payloads = new byte[count][];
        for (int i = 0; i < count; i++)
        {
            addresses[i] = input.ReadInt32();
            lengths[i] = input.ReadInt32();
            payloads[i] = input.ReadBytes(input.ReadInt32());
            int cave = caves + i * 256;
            byte[] payload = payloads[i];
            int tail = payload.Length - 5;
            int continuation = addresses[i] + lengths[i];
            Array.Copy(BitConverter.GetBytes(bodyAddress + continuation - original - (cave + payload.Length)),
                0, payload, tail + 1, 4);
            if (addresses[i] == 0xA35630)
            {
                if (payload[10] != 0x0F || payload[11] != 0x8E)
                    throw new InvalidOperationException("Aging conditional relocation.");
                Array.Copy(BitConverter.GetBytes(bodyAddress + 0xA3565A - original - (cave + 16)),
                    0, payload, 12, 4);
            }
        }
        foreach (int target in new int[] {0xA3563E, 0xA359C1})
            for (int i = 0; i < count; i++)
                if (addresses[i] < target && target < addresses[i] + lengths[i])
                    throw new InvalidOperationException("Aging branch enters an overwritten instruction.");
        // Execute original branch bytes and shared entries, not only isolated replacement bodies.
        int[][] cases = {
            new int[] {0xA355E7,0xA35643,35,29,35,2,29},
            new int[] {0xA35630,0xA35643,33,29,32,2,29},
            new int[] {0xA35630,0xA3565A,32,29,99,77,29},
            new int[] {0xA35630,0xA3565A,31,29,99,77,29},
            new int[] {0xA35948,0xA359C6,28,29,33,35,32},
            new int[] {0xA35948,0xA359C6,35,29,33,35,32},
            new int[] {0xA35948,0xA3594F,36,29,99,35,29},
            new int[] {0xA359BD,0xA359C6,28,99,33,77,32}
        };
        for (int test = 0; test < cases.Length; test++)
        {
            int[] item = cases[test];
            Marshal.Copy(body, 0, new IntPtr(bodyAddress), body.Length);
            for (int i = 0; i < count; i++)
            {
                int site = bodyAddress + addresses[i] - original, cave = caves + i * 256;
                var jump = new byte[lengths[i]];
                for (int j = 0; j < jump.Length; j++) jump[j] = 0x90;
                jump[0] = 0xE9;
                Array.Copy(BitConverter.GetBytes(cave - site - 5), 0, jump, 1, 4);
                Marshal.Copy(jump, 0, new IntPtr(site), jump.Length);
                Marshal.Copy(payloads[i], 0, new IntPtr(cave), payloads[i].Length);
            }
            int driver = scratch + 0x2000;
            var stub = new List<byte>(new byte[] {0x53,0x55,0x56,0x57,0x81,0xEC});
            Action<int> dword = value => stub.AddRange(BitConverter.GetBytes(value));
            dword(128);
            foreach (int[] local in new int[][] {
                new int[] {0x13,item[2]}, new int[] {0x1F,29}, new int[] {0x20,35}, new int[] {0x22,2}
            })
                stub.AddRange(new byte[] {0xC6,0x44,0x24,(byte)local[0],(byte)local[1]});
            stub.AddRange(new byte[] {0xC7,0x44,0x24,0x2C}); dword(29);
            foreach (int[] register in new int[][] {
                new int[] {0xB8,5}, new int[] {0xB9,77}, new int[] {0xBA,99},
                new int[] {0xBD,item[2]}, new int[] {0xBF,item[3]}
            })
            { stub.Add((byte)register[0]); dword(register[1]); }
            stub.Add(0xE9);
            dword(bodyAddress + item[0] - original - (driver + stub.Count + 4));
            int continuation = driver + stub.Count;
            byte[] finish = new byte[5]; finish[0] = 0xE9;
            int stop = bodyAddress + item[1] - original;
            Array.Copy(BitConverter.GetBytes(continuation - stop - 5), 0, finish, 1, 4);
            Marshal.Copy(finish, 0, new IntPtr(stop), finish.Length);
            foreach (byte operand in new byte[] {0x15,0x0D,0x3D})
            {
                stub.AddRange(new byte[] {0x89,operand});
                dword(scratch + 0x300 + Array.IndexOf(new byte[] {0x15,0x0D,0x3D}, operand) * 4);
            }
            stub.AddRange(new byte[] {0x81,0xC4}); dword(128);
            stub.AddRange(new byte[] {0x5F,0x5E,0x5D,0x5B,0xC3});
            Marshal.Copy(stub.ToArray(), 0, new IntPtr(driver), stub.Count);
            ((Getter)Marshal.GetDelegateForFunctionPointer(new IntPtr(driver), typeof(Getter)))(0,0);
            for (int i = 0; i < 3; i++)
                if (Marshal.ReadInt32(new IntPtr(scratch + 0x300 + i * 4)) != item[i + 4])
                    throw new InvalidOperationException("Original aging control-flow mismatch " + test + "/" + i);
        }
        Console.WriteLine("Original aging shared-entry control flow: 8 cases passed.");
    }

    private static void TestWriterRegisters(int writer, int driver, int scratch)
    {
        var bytes = new List<byte>(new byte[] {0x53,0x55,0x56,0x57,0x89,0x25});
        Action<int> dword = value => bytes.AddRange(BitConverter.GetBytes(value));
        dword(scratch + 0x140);
        int[] values = {0x11223344,0x22334455,0x33445566,0x44556677,0x55667788,0x66778899,0x778899AA};
        byte[] codes = {0xB8,0xBB,0xB9,0xBA,0xBE,0xBF,0xBD};
        for(int i=0;i<codes.Length;i++) {bytes.Add(codes[i]); dword(values[i]);}
        bytes.AddRange(new byte[] {0xD9,0xE8,0xF2,0x0F,0x10,0x05}); dword(scratch + 0x40);
        bytes.AddRange(new byte[] {0x3B,0xD2,0xE8}); dword(unchecked(writer - (driver + bytes.Count + 4)));
        byte[] operands = {0x05,0x1D,0x0D,0x15,0x35,0x3D,0x2D,0x25};
        for(int i=0;i<operands.Length;i++) {bytes.AddRange(new byte[] {0x89,operands[i]}); dword(scratch+0x100+i*4);}
        bytes.AddRange(new byte[] {0x9C,0x8F,0x05}); dword(scratch+0x120);
        bytes.AddRange(new byte[] {0xDD,0x1D}); dword(scratch+0x128);
        bytes.AddRange(new byte[] {0xF2,0x0F,0x11,0x05}); dword(scratch+0x130);
        bytes.AddRange(new byte[] {0x5F,0x5E,0x5D,0x5B,0xC3});
        Marshal.Copy(BitConverter.GetBytes(3.25),0,new IntPtr(scratch+0x40),8);
        Marshal.Copy(bytes.ToArray(),0,new IntPtr(driver),bytes.Count);
        ((Getter)Marshal.GetDelegateForFunctionPointer(new IntPtr(driver),typeof(Getter)))(0,0);
        for(int i=0;i<values.Length;i++)
            if(Marshal.ReadInt32(new IntPtr(scratch+0x100+i*4))!=values[i])
                throw new InvalidOperationException("Writer register preservation " + i);
        if(Marshal.ReadInt32(new IntPtr(scratch+0x11C))!=Marshal.ReadInt32(new IntPtr(scratch+0x140))
            || (Marshal.ReadInt32(new IntPtr(scratch+0x120)) & 0x8D5)!=0x44
            || Marshal.PtrToStructure<double>(new IntPtr(scratch+0x128))!=1
            || Marshal.PtrToStructure<double>(new IntPtr(scratch+0x130))!=3.25)
            throw new InvalidOperationException("Writer stack/flags/FPU/SSE preservation.");
    }
}
