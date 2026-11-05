using System.Buffers.Binary;
using System.Text;

namespace FmLauncher;

internal sealed record PanelPayload(byte[] Code, byte[] Data, uint PropertyEntry, uint TitleEntry,
    uint TrainingEntry, uint LabelEntry, uint ReadEntry, uint FormatEntry, uint[] Types);

internal static class GamePanelPatch
{
    internal const uint PropertyAddress = 0x00A73FB0;
    internal const uint TitleAddress = 0x00C8A030;
    internal const uint TrainingAddress = 0x009B6CE1;
    internal const uint LabelAddress = 0x00FBBDB0;
    internal const uint IntegerVtable = 0x0166DDE4;
    internal const uint PlayerVtable = 0x015AB414;
    internal const uint HumanVtable = 0x015AE30C;
    internal const uint PersonTableVtable = 0x0156624C;
    internal const uint FatigueProperty = 0x466A6164; // Fjad
    internal const uint CaProperty = 0x46636162; // Fcab
    internal const uint PaProperty = 0x46706162; // Fpab
    internal const uint HintProperty = 0x466A6874; // Fjht
    internal const int Missing = int.MinValue;
    internal const int StateSize = 16;
    internal const int CodeCapacity = 8192;
    internal const int DataCapacity = 65536;
    internal static ReadOnlySpan<byte> PropertyOriginal => [0x55, 0x8B, 0xEC, 0x83, 0xE4, 0xF8];
    internal static ReadOnlySpan<byte> TitleOriginal => [0x6A, 0xFF, 0x68, 0x51, 0xB4, 0x1B, 0x01];
    internal static ReadOnlySpan<byte> TrainingOriginal => [0x39, 0xBE, 0x34, 0x02, 0, 0];
    internal static ReadOnlySpan<byte> LabelOriginal => [0x64, 0xA1, 0, 0, 0, 0];

    internal static PanelPayload Build(uint address, uint dataAddress, byte[] integerVtable, Localizer localizer)
    {
        if (integerVtable.Length != 0x70) throw new LauncherException("UnexpectedGameMemory");
        var data = new List<byte>(new byte[StateSize]);
        var code = new Code(address);
        uint Reserve(int size)
        {
            while (data.Count % 4 != 0) data.Add(0);
            var result = dataAddress + (uint)data.Count;
            data.AddRange(new byte[size]);
            return result;
        }
        void Set(uint at, uint value) => Put(data, checked((int)(at - dataAddress)), value);
        uint Text(string text)
        {
            var result = Reserve(24);
            var utf16 = Encoding.Unicode.GetBytes(text + "\0");
            if (text.Length >= ushort.MaxValue) throw new ArgumentOutOfRangeException(nameof(text));
            var characters = Reserve(utf16.Length);
            utf16.CopyTo(System.Runtime.InteropServices.CollectionsMarshal.AsSpan(data)
                .Slice(checked((int)(characters - dataAddress)), utf16.Length));
            Set(result, 0x0166A398);
            Set(result + 4, 0x0166A38C);
            Set(result + 8, result + 12);
            // Native SI_STRING buffers with refcount FFFF are immutable and never freed.
            Set(result + 12, 0x0000FFFF);
            Set(result + 16, (uint)text.Length | ((uint)(text.Length + 1) << 16));
            Set(result + 20, characters);
            return result;
        }
        var dash = Text("----");
        var stringType = Reserve(4);
        Set(stringType, 0x0166DC7C);
        var labels = Enumerable.Range(0, 5).Select(i => Text(localizer.Text("PanelFatigue" + i))).ToArray();
        var hints = Enumerable.Range(0, 41).Select(i => Text(localizer.Text("PanelFatigueHint", i))).ToArray();
        var titles = new[]
        {
            Text(localizer.Text("PanelFatigueTitle")), Text("CA"), Text("PA"),
            Text(localizer.Text("PanelFatigueTitle"))
        };
        var vtable = Reserve(0x70);
        integerVtable.CopyTo(System.Runtime.InteropServices.CollectionsMarshal.AsSpan(data)
            .Slice(checked((int)(vtable - dataAddress)), integerVtable.Length));
        var types = Enumerable.Range(0, 4).Select(_ => Reserve(8)).ToArray();
        for (var kind = 0; kind < types.Length; kind++)
        {
            Set(types[kind], vtable);
            Set(types[kind] + 4, (uint)kind);
        }

        code.Mark("property");
        code.Emit(0x8B, 0x44, 0x24, 0x04);
        Identify("property", "propertyOriginal");
        code.Mark("propertyCustom");
        code.Emit(0x56, 0x57, 0x8D, 0x71, 0xF0, 0x8B, 0x7C, 0x24, 0x10,
            0x8B, 0xCA, 0x51, 0x8B, 0xCF);
        code.Call(0x00F5BC90);
        code.Emit(0x59, 0x89, 0x37, 0x89, 0x4F, 0x04, 0x5F, 0x5E, 0xB0, 0x01, 0xC2, 0x08, 0);
        code.Mark("propertyOriginal");
        code.Emit(PropertyOriginal.ToArray());
        code.Jump(PropertyAddress + (uint)PropertyOriginal.Length);

        code.Mark("title");
        code.Emit(0x8B, 0x44, 0x24, 0x08);
        Identify("title", "titleOriginal");
        code.Mark("titleCustom");
        code.Emit(0x8B, 0x4C, 0x24, 0x04, 0x52);
        code.Call(0x00F4F3C0);
        code.Emit(0xC3);
        code.Mark("titleOriginal");
        code.Emit(TitleOriginal.ToArray());
        code.Jump(TitleAddress + (uint)TitleOriginal.Length);

        // Server-side variants recheck the active human on conversion, including
        // serialization. Client tables receive gated integers, not player references.
        code.Mark("read");
        code.Emit(0x53, 0x55, 0x56, 0x57, 0x8B, 0xD9, 0x8B, 0xEA);
        code.Emit(0xF0, 0xFF, 0x05); code.Dword(dataAddress);
        code.Emit(0x85, 0xDB); code.Branch(0x84, "hidden");
        code.Emit(0x81, 0x3B); code.Dword(PlayerVtable); code.Branch(0x85, "invalid");
        code.Emit(0x8B, 0x4B, 0x04, 0x85, 0xC9); code.Branch(0x84, "invalid");
        code.Emit(0x8B, 0x49, 0x04, 0x8D, 0x4C, 0x0B, 0x04, 0x8B, 0x01, 0xFF, 0x90);
        code.Dword(0x110);
        code.Emit(0x8B, 0xF0, 0x85, 0xF6); code.Branch(0x84, "hidden");
        code.Call(0x00C927B0);
        code.Emit(0x85, 0xC0); code.Branch(0x84, "hidden");
        code.Emit(0x81, 0x38); code.Dword(HumanVtable); code.Branch(0x85, "invalid");
        code.Emit(0x8B, 0x48, 0x04, 0x85, 0xC9); code.Branch(0x84, "invalid");
        code.Emit(0x8B, 0x49, 0x04, 0x8D, 0x4C, 0x08, 0x04, 0x8B, 0x11, 0xFF, 0x92);
        code.Dword(0x110);
        code.Emit(0x85, 0xC0); code.Branch(0x84, "hidden");
        code.Emit(0x3B, 0xC6); code.Branch(0x85, "hidden");
        code.Emit(0x83, 0xFD, 0x01); code.Branch(0x84, "readCa");
        code.Emit(0x83, 0xFD, 0x02); code.Branch(0x84, "readPa");
        code.Emit(0x0F, 0xBF, 0x43, 0x0C, 0x3D); code.Dword(unchecked((uint)-1500));
        code.Branch(0x8C, "invalid");
        code.Emit(0x3D); code.Dword(1500); code.Branch(0x8F, "invalid");
        code.Jump("readDone");
        code.Mark("readCa");
        code.Emit(0x0F, 0xBF, 0x43, 0x14); code.Jump("abilityBounds");
        code.Mark("readPa");
        code.Emit(0x0F, 0xBF, 0x43, 0x16);
        code.Mark("abilityBounds");
        code.Emit(0x83, 0xF8, 0x01); code.Branch(0x8C, "invalid");
        code.Emit(0x3D); code.Dword(200); code.Branch(0x8F, "invalid");
        code.Jump("readDone");
        code.Mark("invalid");
        code.Emit(0xF0, 0xFF, 0x05); code.Dword(dataAddress + 8); code.Jump("missing");
        code.Mark("hidden");
        code.Emit(0xF0, 0xFF, 0x05); code.Dword(dataAddress + 4);
        code.Mark("missing");
        code.Emit(0xB8); code.Dword(unchecked((uint)Missing));
        code.Mark("readDone");
        code.Emit(0x5F, 0x5E, 0x5D, 0x5B, 0xC3);

        code.Mark("integer");
        code.Emit(0x8B, 0x51, 0x04, 0x8B, 0x44, 0x24, 0x04, 0x8B, 0x08);
        code.Call("read");
        code.Emit(0xC2, 0x04, 0);
        code.Mark("boolean");
        code.Emit(0xFF, 0x74, 0x24, 0x04); code.Call("integer");
        code.Emit(0x3D); code.Dword(unchecked((uint)Missing));
        code.Branch(0x84, "booleanMissing");
        code.Emit(0x85, 0xC0, 0x0F, 0x95, 0xC0, 0xC2, 0x04, 0);
        code.Mark("booleanMissing");
        code.Emit(0x33, 0xC0, 0xC2, 0x04, 0);
        code.Mark("long");
        code.Emit(0xFF, 0x74, 0x24, 0x04); code.Call("integer");
        code.Emit(0x99, 0xC2, 0x04, 0);
        code.Mark("double");
        code.Emit(0xFF, 0x74, 0x24, 0x04); code.Call("integer");
        code.Emit(0x50, 0xDB, 0x04, 0x24, 0x83, 0xC4, 0x04, 0xC2, 0x04, 0);
        code.Mark("symbol");
        code.Emit(0xFF, 0x74, 0x24, 0x08); code.Call("integer");
        code.Emit(0x8B, 0x4C, 0x24, 0x04, 0x89, 0x01, 0x8B, 0xC1, 0xC2, 0x08, 0);
        code.Mark("equal");
        code.Emit(0x56, 0x8B, 0x44, 0x24, 0x08, 0x8B, 0x48, 0x04, 0x8B, 0x11, 0x50,
            0xFF, 0x52, 0x1C, 0x8B, 0xF0, 0x8B, 0x44, 0x24, 0x0C,
            0x8B, 0x48, 0x04, 0x85, 0xC9);
        code.Branch(0x84, "equalEmpty");
        code.Emit(0x8B, 0x11, 0x50, 0xFF, 0x52, 0x1C, 0x3B, 0xC6, 0x0F, 0x94, 0xC0,
            0x5E, 0xC2, 0x08, 0);
        code.Mark("equalEmpty");
        code.Emit(0x33, 0xC0, 0x5E, 0xC2, 0x08, 0);
        code.Mark("equalRaw");
        code.Emit(0xFF, 0x74, 0x24, 0x04); code.Call("integer");
        code.Emit(0x8B, 0x54, 0x24, 0x08, 0x3B, 0x02, 0x0F, 0x94, 0xC0, 0xC2, 0x08, 0);

        code.Mark("format");
        code.Emit(0x53, 0x8B, 0x59, 0x04, 0xFF, 0x74, 0x24, 0x08); code.Call("integer");
        code.Emit(0x3D); code.Dword(unchecked((uint)Missing)); code.Branch(0x84, "formatDash");
        code.Emit(0x83, 0xFB, 0x03); code.Branch(0x84, "formatHint");
        code.Emit(0x85, 0xDB); code.Branch(0x85, "formatNumber");
        code.Call("fatigueText");
        code.Emit(0x5B, 0xC2, 0x08, 0);
        code.Mark("formatHint");
        code.Emit(0x2D); code.Dword(250);
        code.Branch(0x8E, "hint0");
        code.Emit(0x3D); code.Dword(250); code.Branch(0x8F, "hint40");
        code.Emit(0x6B, 0xC0, 0x04, 0x83, 0xC0, 0x0C, 0x33, 0xD2, 0xB9); code.Dword(25);
        code.Emit(0xF7, 0xF1, 0x8B, 0x04, 0x85);
        var hintTable = Reserve(hints.Length * 4);
        for (var i = 0; i < hints.Length; i++) Set(hintTable + (uint)(4 * i), hints[i]);
        code.Dword(hintTable);
        code.Emit(0x5B, 0xC2, 0x08, 0);
        ReturnText(hints[0], "hint0");
        ReturnText(hints[40], "hint40");
        ReturnText(dash, "formatDash");
        code.Mark("formatNumber");
        code.Emit(0x83, 0xEC, 0x08, 0x89, 0x04, 0x24, 0x6A, 0x00, 0x8D, 0x44, 0x24, 0x04, 0x50);
        code.Call(0x00F5D4F0);
        code.Emit(0x83, 0xC4, 0x08, 0x5B, 0xC2, 0x08, 0);

        code.Mark("fatigueText");
        foreach (var (threshold, index) in new[] { (0, 0), (250, 1), (374, 2), (499, 3) })
        {
            code.Emit(0x3D); code.Dword((uint)threshold); code.Branch(0x8E, "label" + index);
        }
        for (var i = 4; i >= 0; i--)
        {
            code.Mark("label" + i);
            code.Emit(0xB8); code.Dword(labels[i]); code.Emit(0xC3);
        }

        // TABLE replaces child IDs with generated IDs. Resolve those cells through
        // their native column position and the parent PERSON_LIST_TABLE's registry.
        code.Mark("label");
        code.Emit(0x8B, 0x44, 0x24, 0x04, 0x3D); code.Dword(0x74657874);
        code.Branch(0x84, "cellIdentity");
        code.Emit(0x3D); code.Dword(0x76616C75); code.Branch(0x85, "labelOriginal");
        code.Mark("cellIdentity");
        code.Emit(0x8B, 0x41, 0x20, 0x85, 0xC0); code.Branch(0x89, "cellIdentify");
        code.Emit(0x51); code.Call("cellColumn"); code.Emit(0x59);
        code.Mark("cellIdentify");
        code.Emit(0x3D); code.Dword(FatigueProperty);
        code.Branch(0x84, "cellProperty");
        code.Emit(0x3D); code.Dword(CaProperty); code.Branch(0x84, "cellProperty");
        code.Emit(0x3D); code.Dword(PaProperty); code.Branch(0x85, "labelOriginal");
        code.Mark("cellProperty");
        code.Emit(0x8B, 0xD0);
        code.Emit(0x8B, 0x44, 0x24, 0x08, 0x8B, 0x40, 0x04, 0x85, 0xC0);
        code.Branch(0x84, "labelOriginal");
        code.Emit(0x81, 0x38); code.Dword(IntegerVtable); code.Branch(0x85, "labelOriginal");
        code.Emit(0x53, 0x56, 0x8B, 0xD9, 0x8B, 0xF2, 0x8B, 0x4C, 0x24, 0x10);
        code.Call(0x00F5BD20);
        code.Emit(0x3D); code.Dword(unchecked((uint)Missing)); code.Branch(0x84, "cellDash");
        code.Emit(0x81, 0xFE); code.Dword(FatigueProperty); code.Branch(0x85, "cellUnchanged");
        code.Emit(0x3D); code.Dword(unchecked((uint)-1500)); code.Branch(0x8C, "cellInvalid");
        code.Emit(0x3D); code.Dword(1500); code.Branch(0x8F, "cellInvalid");
        code.Call("fatigueText"); code.Jump("cellDisplay");
        code.Mark("cellInvalid");
        code.Emit(0xF0, 0xFF, 0x05); code.Dword(dataAddress + 8);
        code.Mark("cellDash");
        code.Emit(0xB8); code.Dword(dash);
        code.Mark("cellDisplay");
        // Borrow an immutable SI_STRING for this synchronous native setter call.
        code.Emit(0x83, 0xEC, 0x08, 0x89, 0x04, 0x24, 0xC7, 0x44, 0x24, 0x04);
        code.Dword(stringType);
        code.Emit(0x8B, 0xC4, 0x50, 0xFF, 0x74, 0x24, 0x18, 0x8B, 0xCB);
        code.Call("labelOriginal");
        code.Emit(0x83, 0xC4, 0x08, 0x5E, 0x5B, 0xC2, 0x08, 0);
        code.Mark("cellUnchanged");
        code.Emit(0x8B, 0xCB, 0x5E, 0x5B);
        code.Mark("labelOriginal");
        code.Emit(LabelOriginal.ToArray());
        code.Jump(LabelAddress + (uint)LabelOriginal.Length);

        code.Mark("cellColumn");
        code.Emit(0x53, 0x56, 0x8B, 0x59, 0xF4, 0x85, 0xDB);
        code.Branch(0x84, "columnUnavailable");
        code.Emit(0x81, 0x3B); code.Dword(PersonTableVtable);
        code.Branch(0x85, "columnUnavailable");
        code.Emit(0x83, 0xEC, 0x08, 0x33, 0xC0, 0x89, 0x04, 0x24, 0x89, 0x44, 0x24, 0x04,
            0x8B, 0xC4, 0x50);
        code.Push(0x636F6C20); // Native WIDGET layout property "col ".
        code.Emit(0x8B, 0x11, 0xFF, 0x52, 0x04, 0x84, 0xC0);
        code.Branch(0x84, "columnGetterFailed");
        code.Emit(0x8B, 0xCC); code.Call(0x00F5BD20);
        code.Emit(0x8B, 0xF0, 0x8B, 0xCC); code.Call(0x00F5BC90);
        code.Emit(0x83, 0xC4, 0x08, 0x85, 0xF6); code.Branch(0x88, "columnUnavailable");
        code.Emit(0x8B, 0x8B); code.Dword(0xA0);
        code.Emit(0x85, 0xC9); code.Branch(0x84, "columnUnavailable");
        code.Emit(0x3B, 0x71, 0x08); code.Branch(0x8D, "columnUnavailable");
        code.Emit(0x8B, 0x01, 0x56, 0xFF, 0x50, 0x2C, 0x85, 0xC0);
        code.Branch(0x84, "columnUnavailable");
        code.Emit(0x8B, 0x00, 0x5E, 0x5B, 0xC3);
        code.Mark("columnGetterFailed");
        code.Emit(0x8B, 0xCC); code.Call(0x00F5BC90);
        code.Emit(0x83, 0xC4, 0x08);
        code.Mark("columnUnavailable");
        code.Emit(0x33, 0xC0, 0x5E, 0x5B, 0xC3);

        code.Mark("write");
        code.Emit(0xFF, 0x74, 0x24, 0x04); code.Call("integer");
        code.Emit(0x8B, 0x4C, 0x24, 0x08, 0x50); code.Call(0x00F451F0);
        code.Emit(0xC2, 0x08, 0);

        code.Mark("readSerialized");
        code.Emit(0x56, 0x83, 0xEC, 0x04, 0x8B, 0x74, 0x24, 0x0C,
            0x8B, 0x4C, 0x24, 0x10, 0x8B, 0xC4, 0x50);
        code.Call(0x00F44D30);
        code.Emit(0x84, 0xC0); code.Branch(0x84, "serializedDone");
        code.Emit(0x8B, 0xCE); code.Call(0x00F5BC90);
        code.Emit(0xFF, 0x34, 0x24, 0x8B, 0xCE); code.Call(0x00F5E700);
        code.Emit(0xB0, 0x01);
        code.Mark("serializedDone");
        code.Emit(0x83, 0xC4, 0x04, 0x5E, 0xC2, 0x08, 0);

        code.Mark("training");
        code.Emit(0x9C, 0x60, 0x8B, 0xEC, 0x81, 0xEC); code.Dword(528);
        code.Emit(0x83, 0xE4, 0xF0, 0x0F, 0xAE, 0x04, 0x24, 0x8B, 0xCE);
        code.Call("updateTraining");
        code.Emit(0x0F, 0xAE, 0x0C, 0x24, 0x8B, 0xE5, 0x61, 0x9D);
        code.Emit(TrainingOriginal.ToArray());
        code.Jump(TrainingAddress + (uint)TrainingOriginal.Length);
        code.Mark("updateTraining");
        code.Emit(0x53, 0x55, 0x56, 0x57, 0x83, 0xEC, 0x08, 0x8B, 0xF1, 0x33, 0xDB);
        // Native setter 9B8740 stores the selected PERSON at +88;
        // +1E8 belongs to the serialized training schedule, not the player.
        code.Emit(0x8B, 0x86); code.Dword(0x88);
        code.Emit(0x85, 0xC0); code.Branch(0x84, "trainingFind");
        code.Push(0); code.Push(0x018EBF00); code.Push(0x0187FE6C); code.Push(0);
        code.Emit(0x50); code.Call(0x0112FAF8);
        code.Emit(0x83, 0xC4, 0x14, 0x8B, 0xD8);
        code.Emit(0x85, 0xDB); code.Branch(0x85, "trainingFind");
        code.Emit(0xF0, 0xFF, 0x05); code.Dword(dataAddress + 8);
        code.Mark("trainingFind");
        code.Emit(0x83, 0xEC, 0x10, 0x8B, 0xC4, 0xC7, 0x00); code.Dword(0x01233A10);
        code.Emit(0xC7, 0x40, 0x08); code.Dword(0);
        code.Emit(0xC7, 0x40, 0x0C); code.Dword(0);
        code.Push(0); code.Push(0x466D6A64); // Fmjd control, not a database property
        code.Emit(0x8B, 0x06, 0x8B, 0xCE, 0xFF, 0x90); code.Dword(0xC4);
        code.Emit(0x85, 0xC0); code.Branch(0x84, "trainingDone");
        code.Emit(0x8B, 0xF8, 0x89, 0x1C, 0x24, 0xC7, 0x44, 0x24, 0x04); code.Dword(types[0]);
        SetControl(0x74657874);
        code.Emit(0xC7, 0x44, 0x24, 0x04); code.Dword(types[3]);
        SetControl(0x68696E74);
        code.Emit(0xF0, 0xFF, 0x05); code.Dword(dataAddress + 12);
        code.Mark("trainingDone");
        code.Emit(0x83, 0xC4, 0x08, 0x5F, 0x5E, 0x5D, 0x5B, 0xC3);

        foreach (var (slot, label) in new (int, string)[]
        {
            (0x10, "equal"), (0x14, "equalRaw"), (0x18, "boolean"), (0x1C, "integer"),
            (0x20, "integer"), (0x24, "long"), (0x28, "long"), (0x2C, "double"),
            (0x34, "symbol"), (0x60, "format"), (0x64, "write"), (0x68, "readSerialized")
        }) Set(vtable + (uint)slot, code.At(label));
        if (code.Length > CodeCapacity || data.Count > DataCapacity)
            throw new LauncherException("UnexpectedGameMemory");
        return new PanelPayload(code.Finish(), data.ToArray(), code.At("property"), code.At("title"),
            code.At("training"), code.At("label"), code.At("read"), code.At("format"), types);

        void Identify(string prefix, string otherwise)
        {
            var ids = new[] { FatigueProperty, CaProperty, PaProperty, HintProperty };
            for (var i = 0; i < ids.Length; i++)
            {
                code.Emit(0x3D); code.Dword(ids[i]); code.Branch(0x84, prefix + i);
            }
            code.Jump(otherwise);
            for (var i = 0; i < ids.Length; i++)
            {
                code.Mark(prefix + i);
                code.Emit(0xBA); code.Dword(prefix == "property" ? types[i] : titles[i]);
                code.Jump(prefix + "Custom");
            }
        }
        void ReturnText(uint text, string label)
        {
            code.Mark(label);
            code.Emit(0xB8); code.Dword(text);
            code.Emit(0x5B, 0xC2, 0x08, 0);
        }
        void SetControl(uint property)
        {
            code.Emit(0x8B, 0xC4, 0x50); code.Push(property);
            code.Emit(0x8D, 0x4F, 0x10, 0x8B, 0x11, 0xFF, 0x52, 0x08);
        }
    }

    private static void Put(List<byte> bytes, int offset, uint value) =>
        BinaryPrimitives.WriteUInt32LittleEndian(
            System.Runtime.InteropServices.CollectionsMarshal.AsSpan(bytes).Slice(offset, 4), value);

    private sealed class Code(uint address)
    {
        private readonly List<byte> bytes = [];
        private readonly Dictionary<string, int> labels = [];
        private readonly List<(int Offset, string Label)> fixups = [];
        internal int Length => bytes.Count;
        internal uint At(string label) => address + (uint)labels[label];
        internal void Mark(string label) => labels.Add(label, bytes.Count);
        internal void Emit(params byte[] value) => bytes.AddRange(value);
        internal void Dword(uint value)
        {
            var start = bytes.Count;
            bytes.AddRange(new byte[4]);
            Put(bytes, start, value);
        }
        internal void Push(uint value) { Emit(0x68); Dword(value); }
        internal void Call(uint destination) { Emit(0xE8); Relative(destination); }
        internal void Jump(uint destination) { Emit(0xE9); Relative(destination); }
        internal void Call(string label) { Emit(0xE8); Reference(label); }
        internal void Jump(string label) { Emit(0xE9); Reference(label); }
        internal void Branch(byte condition, string label) { Emit(0x0F, condition); Reference(label); }
        private void Reference(string label)
        {
            fixups.Add((bytes.Count, label));
            Dword(0);
        }
        private void Relative(uint destination) =>
            Dword(unchecked(destination - (address + (uint)bytes.Count + 4)));
        internal byte[] Finish()
        {
            foreach (var (offset, label) in fixups)
                Put(bytes, offset, unchecked((uint)(labels[label] - offset - 4)));
            return bytes.ToArray();
        }
    }
}
