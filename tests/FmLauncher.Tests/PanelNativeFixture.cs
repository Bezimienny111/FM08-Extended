using System;
using System.IO;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
using Marshal = PanelRemoteMemory;

internal static class NativePanelFixture
{
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    private delegate int PanelRead(IntPtr player, int kind);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    private delegate IntPtr PanelFormat(IntPtr type, IntPtr value);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    private delegate int PanelProperty(IntPtr self, int property, IntPtr value);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    private delegate IntPtr PanelTitle(IntPtr output, int property, int shortName);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    private delegate void PanelTraining(IntPtr panel);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    private delegate int PanelEqual(IntPtr type, IntPtr first, IntPtr second);

    internal static void TestPanels(string gamePath, string path)
    {
        using var remote = new PanelRemoteProcess(gamePath);
        Marshal.Process = remote;
        IntPtr code = AllocatePanel(0x10000000, 8192);
        IntPtr data = AllocatePanel(0x11000000, 65536);
        IntPtr scratch = AllocatePanel(0x12000000, 65536);
        int propertyEntry, titleEntry, trainingEntry, labelEntry, readEntry, formatEntry;
        int[] types = new int[4];
        using (var reader = new BinaryReader(File.OpenRead(path)))
        {
            int length = reader.ReadInt32();
            Marshal.Copy(reader.ReadBytes(length), 0, code, length);
            length = reader.ReadInt32();
            Marshal.Copy(reader.ReadBytes(length), 0, data, length);
            propertyEntry = reader.ReadInt32();
            titleEntry = reader.ReadInt32();
            trainingEntry = reader.ReadInt32();
            labelEntry = reader.ReadInt32();
            readEntry = reader.ReadInt32();
            formatEntry = reader.ReadInt32();
            for (int i = 0; i < types.Length; i++) types[i] = reader.ReadInt32();
        }
        IntPtr player = scratch;
        IntPtr human = IntPtr.Add(scratch, 0x1000);
        IntPtr human2 = IntPtr.Add(scratch, 0x2000);
        IntPtr team = IntPtr.Add(scratch, 0x3000);
        IntPtr reserves = IntPtr.Add(scratch, 0x3100);
        IntPtr foreign = IntPtr.Add(scratch, 0x3200);
        IntPtr club = IntPtr.Add(scratch, 0x3400);
        IntPtr otherClub = IntPtr.Add(scratch, 0x3500);
        IntPtr activeHuman = IntPtr.Add(scratch, 0x3600);
        IntPtr value = IntPtr.Add(scratch, 0x3700);
        IntPtr output = IntPtr.Add(scratch, 0x3800);
        IntPtr panel = IntPtr.Add(scratch, 0x4000);
        IntPtr widget = IntPtr.Add(scratch, 0x5000);
        IntPtr variantCopy = IntPtr.Add(scratch, 0x5400);
        IntPtr integers = IntPtr.Add(scratch, 0x6000);
        IntPtr beforeFx = IntPtr.Add(scratch, 0x7000);
        IntPtr afterFx = IntPtr.Add(scratch, 0x7200);
        InitializePerson(player, 0x015AB414, 0xEC, 0x015AB12C, IntPtr.Add(scratch, 0x8000));
        InitializePerson(human, 0x015AE30C, 0x29C, 0x015AE024, IntPtr.Add(scratch, 0x8100));
        InitializePerson(human2, 0x015AE30C, 0x29C, 0x015AE024, IntPtr.Add(scratch, 0x8200));
        Marshal.WriteInt32(team, 0x38, club.ToInt32());
        Marshal.WriteInt32(reserves, 0x38, club.ToInt32());
        Marshal.WriteInt32(foreign, 0x38, otherClub.ToInt32());
        Marshal.WriteInt32(human, 0x29C + 0x70, team.ToInt32());
        Marshal.WriteInt32(human2, 0x29C + 0x70, foreign.ToInt32());
        Marshal.WriteInt32(player, 0xEC + 0x70, team.ToInt32());
        Marshal.WriteInt32(activeHuman, human.ToInt32());
        Marshal.WriteInt16(player, 0x14, 123);
        Marshal.WriteInt16(player, 0x16, 187);
        // Only the active-human context resolver and native number formatter are mocked.
        // Virtual-base thunks, club getters, RTTI, numeric copying and XML header strings
        // execute the original FM08 machine code in the suspended test process.
        WritePanelCode(0x00C927B0, Join(new byte[] { 0xA1 }, BitConverter.GetBytes(activeHuman.ToInt32()), new byte[] { 0xC3 }));
        IntPtr numberStorage = IntPtr.Add(scratch, 0x9000);
        for (int n = 0; n <= 200; n++)
        {
            IntPtr text = IntPtr.Add(numberStorage, n * 64);
            ImmutableString(text, n.ToString());
            Marshal.WriteInt32(integers, n * 4, text.ToInt32());
        }
        WritePanelCode(0x00F5D4F0, Join(new byte[] { 0x8B, 0x44, 0x24, 0x04, 0x8B, 0, 0x8B, 0x04, 0x85 },
            BitConverter.GetBytes(integers.ToInt32()), new byte[] { 0xC2, 0x08, 0 }));
        PanelRead read = PanelFunction<PanelRead>(0x1200D000, Join(
            new byte[] { 0x8B, 0x4C, 0x24, 0x04, 0x8B, 0x54, 0x24, 0x08, 0xB8 },
            BitConverter.GetBytes(readEntry), new byte[] { 0xFF, 0xD0, 0xC3 }));
        PanelFormat format = PanelFunction<PanelFormat>(0x1200D100, new byte[]
        {
            0x8B, 0x4C, 0x24, 0x04, 0x6A, 0, 0xFF, 0x74, 0x24, 0x0C,
            0x8B, 0x01, 0xFF, 0x50, 0x60, 0xC3
        });
        PanelRead asInteger = PanelFunction<PanelRead>(0x1200D200, new byte[]
        {
            0x8B, 0x4C, 0x24, 0x04, 0xFF, 0x74, 0x24, 0x08, 0x8B, 0x01, 0xFF, 0x50, 0x1C, 0xC3
        });
        PanelProperty property = PanelFunction<PanelProperty>(0x1200D300, Join(new byte[]
        {
            0x8B, 0x4C, 0x24, 0x04, 0xFF, 0x74, 0x24, 0x0C, 0xFF, 0x74, 0x24, 0x0C, 0xB8
        }, BitConverter.GetBytes(propertyEntry), new byte[] { 0xFF, 0xD0, 0xC3 }));
        PanelEqual equal = PanelFunction<PanelEqual>(0x1200D400, new byte[]
        {
            0x8B, 0x4C, 0x24, 0x04, 0xFF, 0x74, 0x24, 0x0C, 0xFF, 0x74, 0x24, 0x0C,
            0x8B, 0x01, 0xFF, 0x50, 0x10, 0xC3
        });
        PanelEqual equalRaw = PanelFunction<PanelEqual>(0x1200D480, new byte[]
        {
            0x8B, 0x4C, 0x24, 0x04, 0xFF, 0x74, 0x24, 0x0C, 0xFF, 0x74, 0x24, 0x0C,
            0x8B, 0x01, 0xFF, 0x50, 0x14, 0xC3
        });
        int[] ids = { 0x466A6164, 0x46636162, 0x46706162, 0x466A6874 };
        for (int kind = 0; kind < 4; kind++)
        {
            Require((property(IntPtr.Add(player, 0x10), ids[kind], value) & 255) == 1, "Property result.");
            Require(Marshal.ReadInt32(value) == player.ToInt32() && Marshal.ReadInt32(value, 4) == types[kind], "Property ABI.");
        }
        byte[] playerBefore = new byte[0x300];
        Marshal.Copy(player, playerBefore, 0, playerBefore.Length);
        int cases = 0;
        for (int j = -1500; j <= 1500; j++)
        {
            Marshal.WriteInt16(player, 0x0C, (short)j);
            Marshal.WriteInt32(value, player.ToInt32());
            Marshal.WriteInt32(value, 4, types[0]);
            Require(read(player, 0) == j, "Signed fatigue at " + j);
            Require(asInteger(new IntPtr(types[0]), value.ToInt32()) == j, "Integer conversion at " + j);
            string expected = j <= 0 ? "Wypoczęty" : j <= 250 ? "Normalne" : j < 375 ? "Narastające"
                : j < 500 ? "Wysokie" : "Bardzo wysokie";
            Require(PanelText(format(new IntPtr(types[0]), value)) == expected, "Fatigue label at " + j);
            int penalty = (Math.Min(Math.Max(j - 250, 0), 250) * 4 + 12) / 25;
            Require(PanelText(format(new IntPtr(types[3]), value)).Contains(penalty + "%"), "Tooltip at " + j);
            cases++;
        }
        Marshal.WriteInt16(player, 0x0C, 375);
        Marshal.Copy(player, playerBefore, 0, playerBefore.Length);
        string detailedHint = PanelText(format(new IntPtr(types[3]), value));
        Require(detailedHint.Split(new[] { "\r\n" }, StringSplitOptions.None).Length == 5
            && detailedHint.Contains("kondycji 100%") && detailedHint.Contains("Poziomy FMExt:")
            && detailedHint.Contains("rotację") && detailedHint.Contains("dłuższy odpoczynek")
            && detailedHint.Contains("nie diagnoza medyczna"), "Detailed Polish training tooltip.");
        Require(read(player, 1) == 123 && read(player, 2) == 187, "CA/PA values.");
        Require(PanelText(format(new IntPtr(types[1]), value)) == "123", "CA formatting.");
        Require(PanelText(format(new IntPtr(types[2]), value)) == "187", "PA formatting.");
        Marshal.WriteInt32(value, 4, types[1]);
        Marshal.Copy(new int[] { player.ToInt32(), types[1] }, 0, variantCopy, 2);
        Require((equal(new IntPtr(types[1]), value, variantCopy) & 255) == 1, "Numeric equality.");
        Marshal.WriteInt32(output, 123);
        Require((equalRaw(new IntPtr(types[1]), value, output) & 255) == 1, "Native raw integer equality ABI.");
        Marshal.WriteInt32(output, 124);
        Require((equalRaw(new IntPtr(types[1]), value, output) & 255) == 0, "Native raw integer inequality ABI.");
        Marshal.WriteInt32(activeHuman, human2.ToInt32());
        for (int kind = 0; kind < 4; kind++)
        {
            Require(read(player, kind) == int.MinValue, "Foreign club access.");
            Require(PanelText(format(new IntPtr(types[kind]), value)) == "----", "Cached value leaked across humans.");
        }
        Marshal.WriteInt32(player, 0xEC + 0x70, foreign.ToInt32());
        Require(read(player, 1) == 123, "Active foreign manager should see their player.");
        Marshal.WriteInt32(activeHuman, human.ToInt32());
        Require(read(player, 1) == int.MinValue, "Outgoing loan should be hidden.");
        Marshal.WriteInt32(player, 0xEC + 0x70, reserves.ToInt32());
        Require(read(player, 1) == 123, "Reserve team / incoming loan should be visible.");
        Marshal.WriteByte(reserves, 0x40, 1);
        Require(read(player, 1) == int.MinValue, "National team should not grant club access.");
        Marshal.WriteByte(reserves, 0x40, 0);
        Marshal.WriteInt32(activeHuman, 0);
        Require(read(player, 0) == int.MinValue, "No active human.");
        Marshal.WriteInt32(activeHuman, human.ToInt32());
        Marshal.WriteInt32(human, 0x29C + 0x70, 0);
        Require(read(player, 1) == int.MinValue, "Unemployed human.");
        Marshal.WriteInt32(human, 0x29C + 0x70, team.ToInt32());
        Marshal.WriteInt32(player, 0xEC + 0x70, team.ToInt32());
        foreach (short invalid in new short[] { -32768, -1501, 1501, 32767 })
        {
            Marshal.WriteInt16(player, 0x0C, invalid);
            Require(read(player, 0) == int.MinValue, "Invalid fatigue.");
        }
        foreach (short invalid in new short[] { -1, 0, 201, 32767 })
        {
            Marshal.WriteInt16(player, 0x14, invalid);
            Require(read(player, 1) == int.MinValue, "Invalid CA.");
        }
        Marshal.WriteInt16(player, 0x14, 123);
        Marshal.WriteInt16(player, 0x0C, 375);
        byte[] playerAfter = new byte[playerBefore.Length];
        Marshal.Copy(player, playerAfter, 0, playerAfter.Length);
        Require(EqualBytes(playerBefore, playerAfter), "Panel reads mutated player data.");

        ImmutableString(output, "");
        Marshal.WriteInt32(new IntPtr(0x01B205E4), Marshal.ReadInt32(output, 8));
        WritePanelCode(0x0102FDE0, new byte[] { 0xC3 });
        PanelTitle title = PanelFunction<PanelTitle>(0x1200D500, Join(new byte[] { 0xB8 },
            BitConverter.GetBytes(titleEntry), new byte[] { 0xFF, 0xE0 }));
        Require(title(output, ids[0], 0) == output && PanelText(output) == "Zmęczenie sezonowe", "Native header Unicode copy.");
        Require(title(output, ids[1], 1) == output && PanelText(output) == "CA", "CA header.");

        // The schedule deliberately points elsewhere: only the native +88 PERSON
        // binding (9B8740) may select the player.
        Marshal.WriteInt32(panel, IntPtr.Add(panel, 0x300).ToInt32());
        Marshal.WriteInt32(panel, 0x88, IntPtr.Add(player, 0xEC).ToInt32());
        Marshal.WriteInt32(panel, 0x1E8, foreign.ToInt32());
        Marshal.WriteInt32(panel, 0x234, 0x13579BDF);
        Marshal.WriteInt32(IntPtr.Add(panel, 0x300), 0xC4, 0x1200D600);
        Marshal.WriteInt32(widget, 0x10, IntPtr.Add(widget, 0x100).ToInt32());
        Marshal.WriteInt32(IntPtr.Add(widget, 0x100), 8, 0x1200D700);
        WritePanelCode(0x1200D600, Join(new byte[] { 0xB8 },
            BitConverter.GetBytes(widget.ToInt32()), new byte[] { 0xC2, 0x18, 0 }));
        ImmutableString(IntPtr.Add(widget, 0x70), "");
        // Suppress repaint scheduling, not LABEL's text setter/string conversion.
        WritePanelCode(0x00F614F0, new byte[] { 0xC2, 0x04, 0 });
        // The suspended main thread has not initialized locale collation.
        // Compare these null-terminated test labels ordinally instead.
        WritePanelCode(0x00FF9400, new byte[]
        {
            0x56, 0x57, 0x8B, 0x74, 0x24, 0x0C, 0x8B, 0x7C, 0x24, 0x10,
            0x0F, 0xB7, 0x06, 0x0F, 0xB7, 0x17, 0x2B, 0xC2, 0x75, 0x0C,
            0x85, 0xD2, 0x74, 0x08, 0x83, 0xC6, 0x02, 0x83, 0xC7, 0x02,
            0xEB, 0xEA, 0x5F, 0x5E, 0xC3
        });
        WritePanelCode(0x1200D700, Join(new byte[]
        {
            0x81, 0x7C, 0x24, 0x04
        }, BitConverter.GetBytes(0x68696E74), new byte[]
        {
            0x74, 0x07, 0xB8
        }, BitConverter.GetBytes(0x00FBBDB0), new byte[]
        {
            0xFF, 0xE0,
            0x56, 0x8B, 0xF1, 0x6A, 0, 0xFF, 0x74, 0x24, 0x10,
            0x8B, 0x04, 0x24, 0x8B, 0x48, 0x04, 0x8B, 0x11, 0xFF, 0x52, 0x60,
            0x89, 0x86, 0xF0, 0x01, 0, 0,
            0xD9, 0xE8, 0x5E, 0xB0, 0x01, 0xC2, 0x08, 0
        }));
        WritePanelCode(0x009B6CE7, new byte[] { 0xC3 });
        var trainingStub = new List<byte>(new byte[] { 0x55, 0x53, 0x56, 0x57,
            0x8B, 0x74, 0x24, 0x14, 0xBF });
        trainingStub.AddRange(BitConverter.GetBytes(0x13579BDF));
        trainingStub.AddRange(new byte[] { 0xBD });
        trainingStub.AddRange(BitConverter.GetBytes(0x2468ACE0));
        trainingStub.AddRange(new byte[] { 0xD9, 0xE8, 0x0F, 0xAE, 0x05 });
        trainingStub.AddRange(BitConverter.GetBytes(beforeFx.ToInt32()));
        trainingStub.Add(0xB8); trainingStub.AddRange(BitConverter.GetBytes(trainingEntry));
        trainingStub.AddRange(new byte[] { 0xFF, 0xD0, 0x0F, 0xAE, 0x05 });
        trainingStub.AddRange(BitConverter.GetBytes(afterFx.ToInt32()));
        trainingStub.AddRange(new byte[] { 0xDD, 0xD8, 0x5F, 0x5E, 0x5B, 0x5D, 0xC3 });
        PanelTraining training = PanelFunction<PanelTraining>(0x1200D800, trainingStub.ToArray());
        training(panel);
        Require(PanelText(IntPtr.Add(widget, 0x70)) == "Wysokie", "Native LABEL text / selected PERSON binding.");
        Require(PanelText(new IntPtr(Marshal.ReadInt32(widget, 0x200))).Contains("20%"), "Training tooltip.");
        byte[] fxBefore = new byte[512], fxAfter = new byte[512];
        Marshal.Copy(beforeFx, fxBefore, 0, fxBefore.Length);
        Marshal.Copy(afterFx, fxAfter, 0, fxAfter.Length);
        Require(EqualBytes(fxBefore, fxAfter), "Training hook changed FPU/SSE state.");
        Marshal.WriteInt32(activeHuman, human2.ToInt32());
        training(panel);
        Require(PanelText(IntPtr.Add(widget, 0x70)) == "----", "Training privacy on human switch.");
        Marshal.WriteInt32(activeHuman, human.ToInt32());
        IntPtr nextPlayer = IntPtr.Add(scratch, 0xC400);
        InitializePerson(nextPlayer, 0x015AB414, 0xEC, 0x015AB12C, IntPtr.Add(scratch, 0xC800));
        Marshal.WriteInt32(nextPlayer, 0xEC + 0x70, team.ToInt32());
        Marshal.WriteInt16(nextPlayer, 0x0C, -5);
        Marshal.WriteInt32(panel, 0x88, IntPtr.Add(nextPlayer, 0xEC).ToInt32());
        training(panel);
        Require(PanelText(IntPtr.Add(widget, 0x70)) == "Wypoczęty", "Training player switching must replace the old label.");
        Marshal.WriteInt32(panel, 0x88, 0);
        Marshal.WriteInt32(panel, 0x1E8, IntPtr.Add(player, 0xEC).ToInt32());
        training(panel);
        Require(PanelText(IntPtr.Add(widget, 0x70)) == "----", "Training null PERSON must not read the schedule.");
        Require(Marshal.ReadInt32(data, 12) == 4, "Training update diagnostic.");
        Marshal.Copy(player, playerAfter, 0, playerAfter.Length);
        Require(EqualBytes(playerBefore, playerAfter), "Training updates mutated the selected player.");

        // The real table wire format deliberately discards our custom type. Exercise
        // native variant serialization and native integer deserialization before LABEL.
        IntPtr wire = IntPtr.Add(scratch, 0xE800);
        IntPtr nativeInteger = IntPtr.Add(wire, 0x180);
        IntPtr wireBytes = IntPtr.Add(wire, 0x200);
        PanelTraining initializeTypes = PanelFunction<PanelTraining>(0x1200DBA0, new byte[]
        {
            0x8B, 0x4C, 0x24, 0x04, 0xB8, 0x80, 0xE0, 0xF5, 0, 0xFF, 0xD0, 0xC3
        });
        initializeTypes(IntPtr.Add(wire, 0x300));
        Marshal.WriteInt32(new IntPtr(0x01B24238), IntPtr.Add(wire, 0x300).ToInt32());
        Marshal.WriteInt32(wire, IntPtr.Add(wire, 0x100).ToInt32());
        Marshal.WriteInt32(wire, 4, IntPtr.Add(wire, 0x140).ToInt32());
        Marshal.WriteInt32(wire, 0x144, 0x1C);
        Marshal.WriteInt32(wire, 0x20, IntPtr.Add(wire, 0x150).ToInt32());
        Marshal.WriteInt32(wire, 0x104, 0x1200DB00);
        Marshal.WriteInt32(wire, 0x108, 0x1200DB40);
        Marshal.WriteInt32(wire, 0x15C, 0x1200DB80);
        Marshal.WriteInt32(nativeInteger, 0x0166DDE4);
        // Only byte transport is a fixture: the variant header, gated conversion,
        // integer serializer/deserializer and LABEL setter are native/production code.
        WritePanelCode(0x1200DB00, new byte[]
        {
            0x56, 0x57, 0x8B, 0xD1, 0x8B, 0x79, 0x40,
            0x8B, 0x74, 0x24, 0x0C, 0x8B, 0x4C, 0x24, 0x10,
            0xF3, 0xA4, 0x89, 0x7A, 0x40, 0x5F, 0x5E, 0xB0, 0x01, 0xC2, 0x08, 0
        });
        WritePanelCode(0x1200DB40, new byte[]
        {
            0x56, 0x57, 0x8B, 0xD1, 0x8B, 0x71, 0x40,
            0x8B, 0x7C, 0x24, 0x0C, 0x8B, 0x4C, 0x24, 0x10,
            0xF3, 0xA4, 0x89, 0x72, 0x40, 0x5F, 0x5E, 0xB0, 0x01, 0xC2, 0x08, 0
        });
        WritePanelCode(0x1200DB80, new byte[] { 0xB8, 1, 0, 0, 0, 0xC3 });
        PanelRead serialize = PanelFunction<PanelRead>(0x1200DA00, new byte[]
        {
            0x8B, 0x4C, 0x24, 0x04, 0xFF, 0x74, 0x24, 0x08,
            0xB8, 0x60, 0xC0, 0xF5, 0, 0xFF, 0xD0, 0xC3
        });
        PanelEqual deserializeInteger = PanelFunction<PanelEqual>(0x1200DA40, new byte[]
        {
            0x8B, 0x4C, 0x24, 0x04, 0xFF, 0x74, 0x24, 0x0C, 0xFF, 0x74, 0x24, 0x0C,
            0x8B, 0x01, 0xFF, 0x50, 0x68, 0xC3
        });
        PanelRead integerValue = PanelFunction<PanelRead>(0x1200DA80, new byte[]
        {
            0x8B, 0x4C, 0x24, 0x04, 0xFF, 0x74, 0x24, 0x08,
            0xB8, 0, 0xE7, 0xF5, 0, 0xFF, 0xD0, 0xC3
        });
        PanelProperty setCell = PanelFunction<PanelProperty>(0x1200DAC0, Join(new byte[]
        {
            0x8B, 0x4C, 0x24, 0x04, 0xFF, 0x74, 0x24, 0x0C, 0xFF, 0x74, 0x24, 0x0C, 0xB8
        }, BitConverter.GetBytes(labelEntry), new byte[] { 0xFF, 0xD0, 0xC3 }));
        IntPtr table = IntPtr.Add(scratch, 0xE000);
        IntPtr columns = IntPtr.Add(scratch, 0xE200);
        IntPtr columnItems = IntPtr.Add(scratch, 0xE220);
        IntPtr definitions = IntPtr.Add(scratch, 0xE240);
        IntPtr layout = IntPtr.Add(scratch, 0xE400);
        IntPtr layoutItems = IntPtr.Add(scratch, 0xE420);
        IntPtr columnEntry = IntPtr.Add(scratch, 0xE440);
        IntPtr sortEntry = IntPtr.Add(scratch, 0xE450);
        IntPtr sortCell = IntPtr.Add(scratch, 0xE700);
        IntPtr sortOutput = IntPtr.Add(scratch, 0xE720);
        Marshal.WriteInt32(table, 0x0156624C);
        Marshal.WriteInt32(table, 0xA0, columns.ToInt32());
        Marshal.WriteInt32(columns, 0x0168CEE0);
        Marshal.WriteInt32(columns, 4, columnItems.ToInt32());
        Marshal.WriteInt32(columns, 8, 3);
        Marshal.WriteInt32(columns, 12, 3);
        for (int kind = 0; kind < 3; kind++)
        {
            Marshal.WriteInt32(columnItems, kind * 4, IntPtr.Add(definitions, kind * 0x44).ToInt32());
            Marshal.WriteInt32(definitions, kind * 0x44, ids[kind]);
        }
        Marshal.WriteInt32(layout, 0x0166A12C);
        Marshal.WriteInt32(layout, 4, layoutItems.ToInt32());
        Marshal.WriteInt32(layout, 8, 2);
        Marshal.WriteInt32(layout, 12, 2);
        Marshal.WriteInt32(layoutItems, columnEntry.ToInt32());
        Marshal.WriteInt32(layoutItems, 4, sortEntry.ToInt32());
        Marshal.WriteInt32(columnEntry, 4, nativeInteger.ToInt32());
        Marshal.WriteInt32(columnEntry, 8, 0x636F6C20);
        Marshal.WriteInt32(sortEntry, 4, nativeInteger.ToInt32());
        Marshal.WriteInt32(sortEntry, 8, 0x7372746F);
        Marshal.WriteInt32(sortCell, 0xC, widget.ToInt32());
        PanelRead getSortValue = PanelFunction<PanelRead>(0x1200DBC0, new byte[]
        {
            0x8B, 0x4C, 0x24, 0x04, 0xFF, 0x74, 0x24, 0x08,
            0xB8, 0xE0, 0x95, 0x03, 0x01, 0xFF, 0xD0, 0xC3
        });
        Marshal.WriteInt32(widget, 4, table.ToInt32());
        Marshal.WriteInt32(widget, 0x3C, layout.ToInt32());
        Marshal.WriteInt32(IntPtr.Add(widget, 0x100), 4, 0x00FBBC90);
        Marshal.WriteInt32(activeHuman, human.ToInt32());
        foreach (int kind in new int[] { 0, 1, 2 })
        {
            // TABLE assigns generated widget IDs. Both the layout lookup and column
            // collection access execute the native code, with no mocked getter.
            int generatedId = unchecked((int)0x800000C5) + kind;
            integerValue(variantCopy, generatedId);
            Require((setCell(IntPtr.Add(widget, 0x10), 0x69642020, variantCopy) & 255) == 1, "Cell ID setter.");
            Require(Marshal.ReadInt32(widget, 0x30) == generatedId, "TABLE-generated cell ID field.");
            Marshal.WriteInt32(columnEntry, kind);
            foreach (int n in new int[] { -1500, -1, 0, 1, 9, 10, 99, 100, 200, 250, 251, 374, 375, 499, 500, 1500 })
            {
                if (kind != 0 && (n < 1 || n > 200)) continue;
                Marshal.WriteInt16(player, kind == 0 ? 0x0C : kind == 1 ? 0x14 : 0x16, (short)n);
                property(IntPtr.Add(player, 0x10), ids[kind], value);
                RoundTripPanelInteger(serialize, deserializeInteger, nativeInteger, wire, wireBytes, value, variantCopy, n);
                Marshal.WriteInt32(sortEntry, n);
                Marshal.WriteByte(sortCell, 0x15, 0);
                byte[] cellBefore = new byte[8], cellAfter = new byte[8];
                Marshal.Copy(variantCopy, cellBefore, 0, 8);
                foreach (int textProperty in new int[] { 0x76616C75, 0x74657874 })
                {
                    Require((setCell(IntPtr.Add(widget, 0x10), textProperty, variantCopy) & 255) == 1, "Cell text setter.");
                    string expected = kind != 0 ? n.ToString() : n <= 0 ? "Wypoczęty" : n <= 250 ? "Normalne"
                        : n < 375 ? "Narastające" : n < 500 ? "Wysokie" : "Bardzo wysokie";
                    Require(PanelText(IntPtr.Add(widget, 0x70)) == expected, "Serialized cell text at " + kind + "/" + n);
                    getSortValue(sortCell, sortOutput.ToInt32());
                    Require(Marshal.ReadInt32(sortOutput) == n
                        && Marshal.ReadInt32(new IntPtr(Marshal.ReadInt32(sortOutput, 4))) == 0x0166DDE4,
                        "Native TABLE_CELL sorting must still read a numeric value.");
                }
                Marshal.Copy(variantCopy, cellAfter, 0, 8);
                Require(EqualBytes(cellBefore, cellAfter), "Display changed the numeric sorting model.");
            }
            Marshal.WriteInt32(activeHuman, human2.ToInt32());
            RoundTripPanelInteger(serialize, deserializeInteger, nativeInteger, wire, wireBytes, value, variantCopy, int.MinValue);
            setCell(IntPtr.Add(widget, 0x10), 0x76616C75, variantCopy);
            Require(PanelText(IntPtr.Add(widget, 0x70)) == "----", "Foreign serialized cell leaked a negative sentinel.");
            Marshal.WriteInt32(activeHuman, human.ToInt32());
        }
        Marshal.WriteInt32(columnEntry, 0);
        Marshal.WriteInt32(definitions, 0x50636162);
        integerValue(variantCopy, 123);
        setCell(IntPtr.Add(widget, 0x10), 0x76616C75, variantCopy);
        Require(PanelText(IntPtr.Add(widget, 0x70)) == "123", "Unrelated native cells changed.");
        Marshal.WriteInt32(definitions, 0x46636162);
        Marshal.WriteInt32(definitions, 0x44, 0x466A6164);
        Marshal.WriteInt32(columnEntry, 1);
        integerValue(variantCopy, 375);
        setCell(IntPtr.Add(widget, 0x10), 0x76616C75, variantCopy);
        Require(PanelText(IntPtr.Add(widget, 0x70)) == "Wysokie", "Reordered native column identity.");
        foreach (int missingColumn in new int[] { -1, 3 })
        {
            Marshal.WriteInt32(columnEntry, missingColumn);
            integerValue(variantCopy, 123);
            setCell(IntPtr.Add(widget, 0x10), 0x76616C75, variantCopy);
            Require(PanelText(IntPtr.Add(widget, 0x70)) == "123", "Invalid column index must preserve native behavior.");
        }
        Console.WriteLine("PASS: actual x86 panel payload; " + cases
            + " fatigue values, own/foreign humans, loans/reserves/national teams, cached variants, native RTTI"
            + ", native Unicode header copying, training row/tooltip, FPU/SSE preservation, serialized numeric cells"
            + ", native LABEL text/missing markers and unchanged sorting values.");
    }

    private static void RoundTripPanelInteger(PanelRead serialize, PanelEqual deserialize, IntPtr integerType,
        IntPtr wire, IntPtr bytes, IntPtr source, IntPtr target, int expected)
    {
        Marshal.WriteInt32(wire, 0x40, bytes.ToInt32());
        Require((serialize(source, wire.ToInt32()) & 255) == 1, "Native variant serialization failed.");
        Require(Marshal.ReadInt32(wire, 0x40) == bytes.ToInt32() + 5, "Native integer wire length.");
        Require((Marshal.ReadInt16(bytes) & 255) == 1, "Native integer wire type.");
        Require(Marshal.ReadInt32(bytes, 1) == expected, "Gated numeric wire value.");
        Marshal.WriteInt32(wire, 0x40, IntPtr.Add(bytes, 1).ToInt32());
        Require((deserialize(integerType, target, wire) & 255) == 1, "Native integer deserialization failed.");
        Require(Marshal.ReadInt32(target) == expected, "Native integer model value.");
        Require(Marshal.ReadInt32(new IntPtr(Marshal.ReadInt32(target, 4))) == 0x0166DDE4,
            "The table must receive an ordinary native integer, not a custom formatter.");
    }

    private static void InitializePerson(IntPtr core, int vtable, int personOffset, int personVtable, IntPtr bases)
    {
        Marshal.WriteInt32(core, vtable);
        Marshal.WriteInt32(core, 4, bases.ToInt32());
        Marshal.WriteInt32(bases, 4, personOffset - 4);
        Marshal.WriteInt32(bases, 8, personOffset - 4);
        Marshal.WriteInt32(core, personOffset, personVtable);
    }
    private static IntPtr AllocatePanel(int address, uint length)
    {
        IntPtr value = Marshal.Process.Allocate(address, length);
        Require(value == new IntPtr(address), "Cannot allocate panel fixture at " + address.ToString("X"));
        return value;
    }
    private static void ImmutableString(IntPtr location, string text)
    {
        Marshal.WriteInt32(location, 0x0166A398);
        Marshal.WriteInt32(location, 4, 0x0166A38C);
        Marshal.WriteInt32(location, 8, IntPtr.Add(location, 12).ToInt32());
        Marshal.WriteInt32(location, 12, 0xFFFF);
        Marshal.WriteInt16(location, 16, (short)text.Length);
        Marshal.WriteInt16(location, 18, (short)(text.Length + 1));
        Marshal.WriteInt32(location, 20, IntPtr.Add(location, 24).ToInt32());
        byte[] textBytes = Encoding.Unicode.GetBytes(text + "\0");
        Marshal.Copy(textBytes, 0, IntPtr.Add(location, 24), textBytes.Length);
    }
    private static string PanelText(IntPtr value)
    {
        Require(value != IntPtr.Zero, "Null formatted string.");
        IntPtr buffer = new IntPtr(Marshal.ReadInt32(value, 8));
        return Marshal.PtrToStringUni(new IntPtr(Marshal.ReadInt32(buffer, 8)), (ushort)Marshal.ReadInt16(buffer, 4));
    }
    private static T PanelFunction<T>(int address, byte[] bytes) where T : class
    {
        WritePanelCode(address, bytes);
        object function;
        if (typeof(T) == typeof(PanelRead))
            function = new PanelRead((a, b) => Marshal.Process.Call(address, a.ToInt32(), b));
        else if (typeof(T) == typeof(PanelFormat))
            function = new PanelFormat((a, b) => new IntPtr(Marshal.Process.Call(address, a.ToInt32(), b.ToInt32())));
        else if (typeof(T) == typeof(PanelProperty))
            function = new PanelProperty((a, b, c) => Marshal.Process.Call(address, a.ToInt32(), b, c.ToInt32()));
        else if (typeof(T) == typeof(PanelTitle))
            function = new PanelTitle((a, b, c) => new IntPtr(Marshal.Process.Call(address, a.ToInt32(), b, c)));
        else if (typeof(T) == typeof(PanelEqual))
            function = new PanelEqual((a, b, c) => Marshal.Process.Call(address, a.ToInt32(), b.ToInt32(), c.ToInt32()));
        else if (typeof(T) == typeof(PanelTraining))
            function = new PanelTraining(a => Marshal.Process.Call(address, a.ToInt32()));
        else throw new InvalidOperationException("Unsupported native fixture delegate.");
        return (T)function;
    }
    private static void WritePanelCode(int address, byte[] bytes)
    {
        Marshal.Copy(bytes, 0, new IntPtr(address), bytes.Length);
    }
    private static byte[] Join(params byte[][] arrays)
    {
        var bytes = new List<byte>();
        foreach (byte[] array in arrays) bytes.AddRange(array);
        return bytes.ToArray();
    }
    private static bool EqualBytes(byte[] first, byte[] second)
    {
        if (first.Length != second.Length) return false;
        for (int i = 0; i < first.Length; i++) if (first[i] != second[i]) return false;
        return true;
    }
    private static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
