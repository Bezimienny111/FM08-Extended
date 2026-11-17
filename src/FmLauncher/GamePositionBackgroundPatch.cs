using System.Buffers.Binary;

namespace FmLauncher;

internal sealed record PositionBackgroundPayload(byte[] Code, byte[] Data, uint State,
    uint NativeNameCreatedEntry, uint LabelDrawEntry, uint BeginGenerationHookEntry,
    uint LabelDestructorEntry, uint BeginGenerationEntry, uint SetRoleEntry, uint RegisterEntry,
    uint RenderEntry, uint InvalidateLabelEntry, uint FontCopyEntry, uint PopupCommitEntry = 0, uint NativeValueCreatedEntry = 0, uint RegisterValueEntry = 0);

/// <summary>Native attribute-cell underlays. No PERSON values or table replacement; native number font/colour stays unchanged.
/// Source: POSITION_BACKGROUND_RESEARCH_20261111, original EXE SHA157f484b... .
/// Native profile UI acceptance remains separate from isolated ABI/render fixtures.</summary>
internal static class GamePositionBackgroundPatch
{
    internal const uint NameCreatedAddress = 0x009B0992;
    internal const uint NumericCreatedAddress = 0x009B0948;
    internal const uint DrawAddress = 0x00FC251F;
    internal const uint RebuildAddress = 0x009AFCE0;
    internal const uint DestructorAddress = 0x004C6020;
    internal const uint FontCopyAddress = 0x00FC7D48;
    internal const uint PopupCommitAddress = 0x00FB4980;
    internal const uint LabelVtable = 0x0150C5E4;
    internal const uint TableVtable = 0x0166F4A4;
    internal const uint ProfileVtable = 0x0156A984;
    internal const int Capacity = 96, HeaderSize = 64, EntrySize = 28, DataSize = 4096;
    internal const int CellColumnOffset = 24;
    internal const int EnabledOffset = 0, ProfileOffset = 4, GenerationOffset = 8,
        RoleOffset = 12, CountOffset = 16, OverflowOffset = 20, RegisteredOffset = 24,
        RenderedOffset = 28, LastAttributeOffset = 32, LastEmphasisOffset = 36, RoleSynchronizeOffset = 40;
    internal static ReadOnlySpan<byte> PopupCommitOriginal => [0x6A, 0xFF, 0x64, 0xA1, 0, 0, 0, 0];
    internal static ReadOnlySpan<byte> NumericCreatedOriginal => [0xE8, 0x23, 0x96, 0x5B, 0];
    internal static ReadOnlySpan<byte> NameCreatedOriginal => [0xE8, 0xD9, 0x95, 0x5B, 0];
    internal static ReadOnlySpan<byte> DrawOriginal => [0x8A, 0x86, 0x08, 0x01, 0, 0];
    internal static ReadOnlySpan<byte> RebuildOriginal => [0x55, 0x8B, 0xEC, 0x83, 0xE4, 0xF8];
    internal static ReadOnlySpan<byte> FontCopyOriginal => [0x8A, 0x46, 0x45, 0x84, 0xC0];
    internal static ReadOnlySpan<byte> DestructorOriginal => [0x6A, 0xFF, 0x68, 0x8E, 0xED, 0x14, 0x01];

    // CAE4E0 native enums; aliases reflect FM08 names, not row order or translated labels.
    internal static IReadOnlyList<string> NativeAttributes { get; } = new[] {
        "AerialAbility", "CommandOfArea", "Communication", "Eccentricity", "Handling", "Kicking",
        "Reflexes", "RushingOut", "TendencyToPunch", "Throwing", "OneOnOnes", "Crossing", "Dribbling",
        "Finishing", "Heading", "LongShots", "LongThrows", "Marking", "Passing", "Penalties", "FreeKicks",
        "Tackling", "Technique", "FirstTouch", "Corners", "Aggression", "Anticipation", "Bravery",
        "Creativity", "Decisions", "Determination", "Flair", "Influence", "OffTheBall", "Positioning",
        "Teamwork", "WorkRate", "Composure", "Concentration", "Acceleration", "Agility", "Balance",
        "Pace", "Stamina", "Strength", "Jumping", "NaturalFitness" };

    /// <param name="roleEmphasis">12x47 classes: first row OFF, then agreed eleven roles;0 ordinary,1 important,2 key.</param>
    internal static PositionBackgroundPayload Build(uint address, uint state, byte[] roleEmphasis, bool enabled)
    {
        if (roleEmphasis.Length != 12 * 47 || roleEmphasis.Any(v => v > 2)
            || roleEmphasis.Take(47).Any(v => v != 0)) throw new ArgumentException("Invalid role classes.");
        var data = new byte[DataSize];
        void Set(int offset, uint value) => BinaryPrimitives.WriteUInt32LittleEndian(data.AsSpan(offset, 4), value);
        Set(0, enabled ? 1u : 0u);
        // Muted green/gold underlays. Alpha is independent from native packed-colour high byte.
        Set(44, 0xFF4B8A66); Set(48, 0xFFB79D52); Set(52, 88); Set(56, 38);
        var entries = state + HeaderSize;
        var weights = entries + Capacity * EntrySize;
        roleEmphasis.CopyTo(data, checked((int)(weights - state)));
        var c = new NativeCode(address);
        void LoadState(byte opcode, int offset) { c.Emit(opcode); c.Dword(state + (uint)offset); }
        void StoreEax(int offset) { c.Emit(0xA3); c.Dword(state + (uint)offset); }
        void StoreImm(int offset, uint value) { c.Emit(0xC7, 0x05); c.Dword(state + (uint)offset); c.Dword(value); }
        void GuardEnabled(string done) { c.Emit(0x83, 0x3D); c.Dword(state); c.Emit(0); c.Branch(0x84, done); }
        void GuardProfileTable(string done)
        {
            // ESI=profile, EBX=TABLE, valid only at the synchronous native name-creation callsite.
            c.Emit(0x85, 0xF6); c.Branch(0x84, done);
            c.Emit(0x81, 0x3E); c.Dword(ProfileVtable); c.Branch(0x85, done);
            c.Emit(0x81, 0x3B); c.Dword(TableVtable); c.Branch(0x85, done);
            c.Emit(0x3B, 0x9E); c.Dword(0x98); c.Branch(0x84, "registerTableOk");
            c.Emit(0x3B, 0x9E); c.Dword(0x9C); c.Branch(0x84, "registerTableOk");
            c.Emit(0x3B, 0x9E); c.Dword(0xA0); c.Branch(0x85, done);
            c.Mark("registerTableOk");
        }

        // Hook only the native CALL at9B0992, retaining its original return site9B0997.
        c.Mark("nameCreated");
        for (int n = 0; n < 5; n++) c.Emit(0xFF, 0x74, 0x24, 0x14);
        c.Call(0x00F69F70); // native five arguments, ret14
        c.Emit(0x9C, 0x60, 0x8B, 0xEC, 0x81, 0xEC); c.Dword(528);
        c.Emit(0x83, 0xE4, 0xF0, 0x0F, 0xAE, 0x04, 0x24);
        // pushad frame EBP: savedESI+4, EBX+16, EAX+28; nativeenum at callerbase+38=S+50.
        c.Emit(0x83, 0x7D, 0x28, 0); c.Branch(0x85, "nameRegistrationDone");
        c.Emit(0xFF, 0x75, 0x2C, 0x0F, 0xBE, 0x45, 0x74, 0x50); // row [S+8]=EBP+2C, enum[S+50]=EBP+74
        c.Emit(0xFF, 0x75, 0x1C, 0xFF, 0x75, 0x10, 0xFF, 0x75, 0x04);
        c.Call("register");
        c.Mark("nameRegistrationDone");
        c.Emit(0x0F, 0xAE, 0x0C, 0x24, 0x8B, 0xE5, 0x61, 0x9D, 0xC2, 0x14, 0);

        // The numeric STANDARD_COLUMN_LABEL creation precedes the name creation.
        // At9B0948 EBX is NOT the proven TABLE yet (it is reloaded at9B094D).
        // Read TABLE from native callerESP+44, which is savedFrameEBP+80 here.
        c.Mark("valueCreated");
        for (int n = 0; n < 5; n++) c.Emit(0xFF, 0x74, 0x24, 0x14);
        c.Call(0x00F69F70);
        c.Emit(0x9C, 0x60, 0x8B, 0xEC, 0x81, 0xEC); c.Dword(528);
        c.Emit(0x83, 0xE4, 0xF0, 0x0F, 0xAE, 0x04, 0x24);
        c.Emit(0x83, 0x7D, 0x28, 1); c.Branch(0x85, "valueRegistrationDone");
        c.Emit(0xFF, 0x75, 0x2C, 0x0F, 0xBE, 0x45, 0x74, 0x50);
        c.Emit(0xFF, 0x75, 0x1C, 0xFF, 0xB5); c.Dword(0x80);
        c.Emit(0xFF, 0x75, 0x04); c.Call("registerValue");
        c.Mark("valueRegistrationDone");
        c.Emit(0x0F, 0xAE, 0x0C, 0x24, 0x8B, 0xE5, 0x61, 0x9D, 0xC2, 0x14, 0);

        // Rebuild may also be called outside the profile setter/event wrappers. Clear the
        // previous registry before native Fill, then read the CURRENT popup after all new cells exist.
        // Never carry the old role merely because the profile pointer happens to be reused.
        c.Mark("beginHook");
        c.Emit(0x53, 0x8B, 0xD9, 0x9C, 0x60); c.Call("begin"); c.Emit(0x61, 0x9D);
        c.Call("rebuildOriginal");
        c.Emit(0x9C, 0x60, 0x8B, 0xEC, 0x81, 0xEC); c.Dword(528);
        c.Emit(0x83, 0xE4, 0xF0, 0x0F, 0xAE, 0x04, 0x24);
        c.Emit(0x3B, 0x1D); c.Dword(state + ProfileOffset); c.Branch(0x85, "rebuildSyncDone");
        c.Emit(0x81, 0x3B); c.Dword(ProfileVtable); c.Branch(0x85, "rebuildSyncDone");
        LoadState(0xA1, RoleSynchronizeOffset); c.Emit(0x85, 0xC0); c.Branch(0x84, "rebuildSyncDone");
        c.Emit(0x8B, 0xCB, 0xFF, 0xD0);
        c.Mark("rebuildSyncDone");
        c.Emit(0x0F, 0xAE, 0x0C, 0x24, 0x8B, 0xE5, 0x61, 0x9D, 0x5B, 0xC3);
        c.Mark("rebuildOriginal");
        c.Emit(RebuildOriginal.ToArray()); c.Jump(RebuildAddress + (uint)RebuildOriginal.Length);
        c.Mark("destructorHook");
        c.Emit(0x9C, 0x60); c.Call("invalidateLabel"); c.Emit(0x61, 0x9D);
        c.Emit(DestructorOriginal.ToArray()); c.Jump(DestructorAddress + (uint)DestructorOriginal.Length);

        c.Mark("begin"); // thiscall ECXprofile, no args; invalidate before native rebuild destroys labels
        c.Emit(0x89, 0x0D); c.Dword(state + 4);
        c.Emit(0xFF, 0x05); c.Dword(state + 8);
        StoreImm(12, 0); StoreImm(16, 0); StoreImm(20, 0); c.Emit(0xC3);

        c.Mark("setRole"); // thiscall ECXprofile, DWORDrole0..11; ret4
        c.Emit(0x53, 0x56, 0x57, 0x8B, 0xF1);
        c.Emit(0x3B, 0x35); c.Dword(state + 4); c.Branch(0x85, "setDone");
        c.Emit(0x8B, 0x44, 0x24, 0x10, 0x83, 0xF8, 0x0B); c.Branch(0x86, "setValid");
        c.Emit(0x33, 0xC0); c.Mark("setValid");
        c.Emit(0x3B, 0x05); c.Dword(state + 12); c.Branch(0x84, "setDone"); StoreEax(12);
        // Repaint only live, generation-bound TABLE owners already proved at registration.
        // Native profile caches may still be -1 during lazy initialization; NEVER dereference them here.
        LoadState(0xA1, 16); c.Emit(0x85, 0xC0); c.Branch(0x84, "setDone");
        c.Emit(0x83, 0xF8, Capacity); c.Branch(0x87, "setDone");
        c.Emit(0x8B, 0xD8, 0xBF); c.Dword(entries);
        c.Mark("setRepaint");
        c.Emit(0x8B, 0x17, 0x85, 0xD2); c.Branch(0x84, "setNextTable");
        LoadState(0xA1, 8); c.Emit(0x39, 0x47, 0x0C); c.Branch(0x85, "setNextTable");
        c.Emit(0x8B, 0x4F, 0x04, 0x85, 0xC9); c.Branch(0x84, "setNextTable");
        c.Emit(0x83, 0xF9, 0xFF); c.Branch(0x84, "setNextTable"); // reject explicit native -1 sentinel
        c.Emit(0x39, 0x4A, 0x04); c.Branch(0x85, "setNextTable"); // current live LABEL parent
        c.Emit(0x81, 0x39); c.Dword(TableVtable); c.Branch(0x85, "setNextTable");
        c.Call(0x00F61160);
        c.Mark("setNextTable"); c.Emit(0x83, 0xC7, EntrySize, 0x4B); c.Branch(0x85, "setRepaint");
        c.Mark("setDone"); c.Emit(0x5F, 0x5E, 0x5B, 0xC2, 0x04, 0);

        // Keep the existing five-argument name ABI; column is explicit in the private core.
        c.Mark("register"); // stdcall(profile,table,label,attribute,row)
        c.Emit(0x6A, 0);
        for (int n = 0; n < 5; n++) c.Emit(0xFF, 0x74, 0x24, 0x18);
        c.Call("registerCore"); c.Emit(0xC2, 0x14, 0);
        c.Mark("registerValue"); // same five arguments, numeric column1 only
        c.Emit(0x6A, 1);
        for (int n = 0; n < 5; n++) c.Emit(0xFF, 0x74, 0x24, 0x18);
        c.Call("registerCore"); c.Emit(0xC2, 0x14, 0);
        c.Mark("registerCore"); // stdcall(profile,table,label,attribute,row,column0or1)
        c.Emit(0x55, 0x8B, 0xEC, 0x53, 0x56, 0x57);
        GuardEnabled("registerDone");
        c.Emit(0x83, 0x3D); c.Dword(state + 20); c.Emit(0); c.Branch(0x85, "registerDone");
        c.Emit(0x8B, 0x75, 0x08, 0x8B, 0x5D, 0x0C, 0x8B, 0x7D, 0x10);
        c.Emit(0x3B, 0x35); c.Dword(state + 4); c.Branch(0x85, "registerDone");
        c.Emit(0x85, 0xDB); c.Branch(0x84, "registerDone"); GuardProfileTable("registerDone");
        c.Emit(0x85, 0xFF); c.Branch(0x84, "registerDone");
        c.Emit(0x81, 0x3F); c.Dword(LabelVtable); c.Branch(0x85, "registerDone");
        c.Emit(0x39, 0x5F, 0x04); c.Branch(0x85, "registerDone");
        c.Emit(0x83, 0x7D, 0x14, 46); c.Branch(0x87, "registerDone");
        c.Emit(0x83, 0x7D, 0x18, 0); c.Branch(0x8C, "registerDone");
        c.Emit(0x83, 0x7D, 0x1C, 1); c.Branch(0x87, "registerDone");
        LoadState(0xA1, 16); c.Emit(0x83, 0xF8, Capacity); c.Branch(0x83, "registerOverflow");
        c.Emit(0x6B, 0xC0, EntrySize, 0x05); c.Dword(entries); c.Emit(0x8B, 0xD0);
        c.Emit(0x89, 0x3A, 0x89, 0x5A, 0x04, 0x8B, 0x45, 0x14, 0x89, 0x42, 0x08);
        LoadState(0xA1, 8); c.Emit(0x89, 0x42, 0x0C, 0x8B, 0x45, 0x18, 0x89, 0x42, 0x10, 0x89, 0x72, 0x14);
        c.Emit(0x8B, 0x45, 0x1C, 0x89, 0x42, CellColumnOffset);
        c.Emit(0xFF, 0x05); c.Dword(state + 16); c.Emit(0xFF, 0x05); c.Dword(state + 24); c.Jump("registerDone");
        c.Mark("registerOverflow"); StoreImm(16, 0); StoreImm(20, 1); StoreImm(12, 0);
        c.Mark("registerDone"); c.Emit(0x5F, 0x5E, 0x5B, 0x5D, 0xC2, 0x18, 0);

        c.Mark("invalidateLabel"); // called before native STANDARD_COLUMN_LABEL destruction; never dereferences stale profile
        c.Emit(0x53, 0x56, 0x8B, 0xD9, 0xBE); c.Dword(entries);
        LoadState(0xA1, 16); c.Emit(0x83, 0xF8, Capacity); c.Branch(0x87, "invalidateDone");
        c.Emit(0x8B, 0xD0, 0x85, 0xD2); c.Branch(0x84, "invalidateDone");
        c.Mark("invalidateNext"); c.Emit(0x39, 0x1E); c.Branch(0x85, "invalidateSkip");
        c.Emit(0xC7, 0x06); c.Dword(0);
        c.Mark("invalidateSkip"); c.Emit(0x83, 0xC6, EntrySize, 0x4A); c.Branch(0x85, "invalidateNext");
        c.Mark("invalidateDone"); c.Emit(0x5E, 0x5B, 0xC3);

        c.Mark("render"); // ECX registered STANDARD_COLUMN_LABEL*, EDX surface* or0 for classification only
        c.Emit(0x53, 0x55, 0x56, 0x57, 0x83, 0xEC, 0x10, 0x8B, 0xF1, 0x8B, 0xEA);
        GuardEnabled("renderNone");
        LoadState(0xA1, 12); c.Emit(0x48, 0x83, 0xF8, 10); c.Branch(0x87, "renderNone"); c.Emit(0x40, 0x6B, 0xD8, 47);
        LoadState(0xA1, 16); c.Emit(0x85, 0xC0); c.Branch(0x84, "renderNone");
        c.Emit(0x83, 0xF8, Capacity); c.Branch(0x87, "renderNone"); c.Emit(0x8B, 0xD0, 0xBF); c.Dword(entries);
        c.Mark("renderFind"); c.Emit(0x39, 0x37); c.Branch(0x84, "renderFound");
        c.Emit(0x83, 0xC7, EntrySize, 0x4A); c.Branch(0x85, "renderFind"); c.Jump("renderNone");
        c.Mark("renderFound");
        // Classification without a surface is used only by the bold-font hook.
        // Numeric column1 receives its underlay but NEVER a font/cache/colour change.
        c.Emit(0x85, 0xED); c.Branch(0x85, "renderCellFontOk");
        c.Emit(0x83, 0x7F, CellColumnOffset, 0); c.Branch(0x85, "renderNone");
        c.Mark("renderCellFontOk");
        c.Emit(0x89, 0x7C, 0x24, 0x08); // current entry, outside the stack-local8Brectangle
        c.Emit(0x81, 0x3E); c.Dword(LabelVtable); c.Branch(0x85, "renderNone");
        LoadState(0xA1, 8); c.Emit(0x39, 0x47, 0x0C); c.Branch(0x85, "renderNone");
        c.Emit(0x8B, 0x46, 0x04, 0x3B, 0x47, 0x04); c.Branch(0x85, "renderNone");
        c.Emit(0x85, 0xC0); c.Branch(0x84, "renderNone"); c.Emit(0x81, 0x38); c.Dword(TableVtable); c.Branch(0x85, "renderNone");
        c.Emit(0x8B, 0x47, 0x08, 0x83, 0xF8, 46); c.Branch(0x87, "renderNone"); StoreEax(32);
        c.Emit(0x03, 0xC3, 0x0F, 0xB6, 0x80); c.Dword(weights); c.Emit(0x85, 0xC0); c.Branch(0x84, "renderNone");
        StoreEax(36); c.Emit(0x8B, 0xF8, 0x85, 0xED); c.Branch(0x84, "renderClass");
        c.Emit(0x8B, 0x4C, 0x24, 0x08, 0x8B, 0xD4); c.Call("bandRect");
        c.Emit(0x85, 0xC0); c.Branch(0x84, "renderClass");
        c.Emit(0x83, 0xFF, 2); c.Branch(0x85, "renderImportant"); // EDI retains emphasis; EAX is bandRect success
        c.Emit(0xFF, 0x35); c.Dword(state + 52); c.Emit(0xFF, 0x35); c.Dword(state + 44); c.Jump("renderFill");
        c.Mark("renderImportant"); c.Emit(0xFF, 0x35); c.Dword(state + 56); c.Emit(0xFF, 0x35); c.Dword(state + 48);
        c.Mark("renderFill"); c.Emit(0x8D, 0x44, 0x24, 0x08, 0x50, 0x8B, 0xCD); c.Call(0x00F94D30);
        c.Emit(0xFF, 0x05); c.Dword(state + 28); c.Mark("renderClass"); c.Emit(0x8B, 0xC7); c.Jump("renderDone");
        c.Mark("renderNone"); c.Emit(0x33, 0xC0);
        c.Mark("renderDone"); c.Emit(0x83, 0xC4, 0x10, 0x5F, 0x5E, 0x5D, 0x5B, 0xC3);

        // Construct two DISJOINT parts of one row band from live native geometry.
        // Actual NameRECT contains the inset numberRECT, so painting both old rects blends twice.
        // ECX=current registryentry, EDX=out8Brect; return1=paint,0=fail closed.
        c.Mark("bandRect");
        c.Emit(0x53, 0x55, 0x56, 0x57, 0x83, 0xEC, 0x18, 0x8B, 0xD9, 0x8B, 0xEA);
        c.Emit(0x8B, 0x03, 0x8B, 0x48, 0x34, 0x89, 0x4D, 0, 0x8B, 0x48, 0x38, 0x89, 0x4D, 0x04);
        LoadState(0xA1, CountOffset); c.Emit(0x85, 0xC0); c.Branch(0x84, "bandFallback");
        c.Emit(0x83, 0xF8, Capacity); c.Branch(0x87, "bandFallback");
        c.Emit(0x8B, 0xD0, 0xBE); c.Dword(entries);
        c.Mark("bandFind");
        c.Emit(0x8B, 0x43, CellColumnOffset, 0x83, 0xF0, 1, 0x39, 0x46, CellColumnOffset); c.Branch(0x85, "bandNext");
        // Exact same TABLE, nativeenum, generation, nativerow, profile.
        foreach (byte offset in new byte[] { 4, 8, 12, 16, 20 })
        { c.Emit(0x8B, 0x43, offset, 0x39, 0x46, offset); c.Branch(0x85, "bandNext"); }
        c.Emit(0x8B, 0x3E, 0x85, 0xFF); c.Branch(0x84, "bandNext");
        c.Emit(0x83, 0xFF, 0xFF); c.Branch(0x84, "bandNext");
        c.Emit(0x81, 0x3F); c.Dword(LabelVtable); c.Branch(0x85, "bandNext");
        c.Emit(0x8B, 0x43, 0x04, 0x39, 0x47, 0x04); c.Branch(0x85, "bandNext");
        c.Emit(0x8B, 0x33, 0x83, 0x7B, CellColumnOffset, 0); c.Branch(0x84, "bandGeometry");
        c.Emit(0x87, 0xFE); // ESI=name widget, EDI=value widget
        c.Jump("bandGeometry");
        c.Mark("bandNext"); c.Emit(0x83, 0xC6, EntrySize, 0x4A); c.Branch(0x85, "bandFind"); c.Jump("bandFallback");
        c.Mark("bandGeometry");
        // Positive native dimensions; signed coordinates, widened arithmetic before short output.
        c.Emit(0x0F, 0xBF, 0x46, 0x38, 0x85, 0xC0); c.Branch(0x8E, "bandFallback");
        c.Emit(0x0F, 0xBF, 0x4E, 0x34, 0x03, 0xC1, 0x89, 0x04, 0x24); // nameRight
        c.Emit(0x0F, 0xBF, 0x46, 0x36, 0x89, 0x44, 0x24, 0x08);
        c.Emit(0x0F, 0xBF, 0x4E, 0x3A, 0x85, 0xC9); c.Branch(0x8E, "bandFallback");
        c.Emit(0x03, 0xC8, 0x89, 0x4C, 0x24, 0x0C); // rowBottom
        c.Emit(0x0F, 0xBF, 0x47, 0x36, 0x3B, 0x44, 0x24, 0x08); c.Branch(0x8C, "bandFallback");
        c.Emit(0x0F, 0xBF, 0x4F, 0x3A, 0x85, 0xC9); c.Branch(0x8E, "bandFallback");
        c.Emit(0x03, 0xC1, 0x3B, 0x44, 0x24, 0x0C); c.Branch(0x8F, "bandFallback");
        c.Emit(0x0F, 0xBF, 0x47, 0x34, 0x89, 0x44, 0x24, 0x10); // split=valueX
        c.Emit(0x0F, 0xBF, 0x4E, 0x34, 0x3B, 0xC1); c.Branch(0x8E, "bandFallback");
        c.Emit(0x0F, 0xBF, 0x57, 0x38, 0x85, 0xD2); c.Branch(0x8E, "bandFallback");
        c.Emit(0x03, 0xD0, 0x3B, 0x14, 0x24); c.Branch(0x8D, "bandRightReady");
        c.Emit(0x8B, 0x14, 0x24);
        c.Mark("bandRightReady"); c.Emit(0x81, 0xFA); c.Dword(32767); c.Branch(0x8F, "bandFallback");
        c.Emit(0x83, 0x7B, CellColumnOffset, 0); c.Branch(0x85, "bandValuePart");
        c.Emit(0x8B, 0xD0, 0x2B, 0xD1, 0x8B, 0xC1); c.Jump("bandWidthReady"); // nameX..valueX
        c.Mark("bandValuePart"); c.Emit(0x2B, 0xD0); // valueX..maxRight
        c.Mark("bandWidthReady"); c.Emit(0x85, 0xD2); c.Branch(0x8E, "bandFallback");
        c.Emit(0x81, 0xFA); c.Dword(32767); c.Branch(0x8F, "bandFallback");
        c.Emit(0x66, 0x89, 0x45, 0, 0x66, 0x89, 0x55, 0x04);
        c.Emit(0x66, 0x8B, 0x46, 0x36, 0x66, 0x89, 0x45, 0x02, 0x66, 0x8B, 0x46, 0x3A, 0x66, 0x89, 0x45, 0x06);
        c.Emit(0xB8); c.Dword(1); c.Jump("bandDone");
        c.Mark("bandFallback");
        // A surviving name retains its own native rect; a number without a live pair paints nothing.
        c.Emit(0x33, 0xC0, 0x83, 0x7B, CellColumnOffset, 0); c.Branch(0x85, "bandDone");
        c.Emit(0x40);
        c.Mark("bandDone"); c.Emit(0x83, 0xC4, 0x18, 0x5F, 0x5E, 0x5D, 0x5B, 0xC3);

        // Actual COLUMN_LABEL inherits COMPOSITE_BUTTON, not LABEL. Inline hook after
        // native BOX appearance (FC251A), before original text virtual call (FC252E).
        c.Mark("draw"); // ESI=widget, EBX=surface; retain every register, flag and FP/SIMD value
        c.Emit(0x9C, 0x60, 0x8B, 0xEC, 0x81, 0xEC); c.Dword(528);
        c.Emit(0x83, 0xE4, 0xF0, 0x0F, 0xAE, 0x04, 0x24);
        c.Emit(0x80, 0xBE); c.Dword(0x108); c.Emit(0); c.Branch(0x85, "drawDone");
        c.Emit(0x8B, 0xCE, 0x8B, 0xD3); c.Call("render");
        c.Mark("drawDone");
        c.Emit(0x0F, 0xAE, 0x0C, 0x24, 0x8B, 0xE5, 0x61, 0x9D);
        c.Emit(DrawOriginal.ToArray()); c.Jump(DrawAddress + (uint)DrawOriginal.Length);

        c.Mark("fontCopy"); // after actual native FBC080 copied FONT_SPEC to the native stack frame
        c.Emit(0x9C, 0x60, 0x8B, 0xEC, 0x81, 0xEC); c.Dword(528);
        c.Emit(0x83, 0xE4, 0xF0, 0x0F, 0xAE, 0x04, 0x24, 0x8D, 0x8E); c.Dword(0xFFFFFF58); c.Emit(0x33, 0xD2); c.Call("render");
        c.Emit(0x83, 0xF8, 2); c.Branch(0x85, "fontCopyDone");
        // ESI is TEXT component=widget+A8. Saved frameEBP=nativeESP-36.
        // Actual native localFONT begins nativeESP+2C: flags+10 =>EBP+60, ref+4 =>EBP+54.
        // Only the local copy changes; source component and numeric column remain untouched.
        c.Emit(0x83, 0x4D, 0x60, 2, 0x6A, 0, 0x8D, 0x4D, 0x54); c.Call(0x00FAC5D0);
        c.Mark("fontCopyDone");
        c.Emit(0x0F, 0xAE, 0x0C, 0x24, 0x8B, 0xE5, 0x61, 0x9D);
        c.Emit(FontCopyOriginal.ToArray()); c.Jump(FontCopyAddress + (uint)FontCopyOriginal.Length);

        // Actual popup commit entry. Capture scope BEFORE the original dispatch; never
        // dereference that popup again afterwards (a select event can destroy its widgets).
        c.Mark("popupCommit"); // thiscall(pMENU_ITEM,silent), ret8
        c.Emit(0x53, 0x56, 0x57, 0x8B, 0xF1);
        c.Call("popupOwner"); c.Emit(0x8B, 0xF8, 0x8B, 0x1D); c.Dword(state + GenerationOffset);
        c.Emit(0xFF, 0x74, 0x24, 0x14, 0xFF, 0x74, 0x24, 0x14, 0x8B, 0xCE);
        c.Call("popupOriginal");
        c.Emit(0x9C, 0x60, 0x8B, 0xEC, 0x81, 0xEC); c.Dword(528);
        c.Emit(0x83, 0xE4, 0xF0, 0x0F, 0xAE, 0x04, 0x24);
        c.Emit(0x85, 0xFF); c.Branch(0x84, "popupDone");
        c.Emit(0x3B, 0x3D); c.Dword(state + ProfileOffset); c.Branch(0x85, "popupDone");
        c.Emit(0x3B, 0x1D); c.Dword(state + GenerationOffset); c.Branch(0x85, "popupDone");
        LoadState(0xA1, CountOffset); c.Emit(0x85, 0xC0); c.Branch(0x84, "popupDone");
        c.Emit(0x83, 0xF8, Capacity); c.Branch(0x87, "popupDone");
        c.Emit(0x8B, 0xD0, 0xBE); c.Dword(entries);
        c.Mark("popupLiveNext");
        c.Emit(0x39, 0x5E, 0x0C); c.Branch(0x85, "popupLiveSkip");
        c.Emit(0x39, 0x7E, 0x14); c.Branch(0x85, "popupLiveSkip");
        c.Emit(0x8B, 0x06, 0x85, 0xC0); c.Branch(0x84, "popupLiveSkip");
        c.Emit(0x83, 0xF8, 0xFF); c.Branch(0x84, "popupLiveSkip");
        c.Emit(0x81, 0x38); c.Dword(LabelVtable); c.Branch(0x85, "popupLiveSkip");
        c.Emit(0x8B, 0x4E, 0x04, 0x85, 0xC9); c.Branch(0x84, "popupLiveSkip");
        c.Emit(0x83, 0xF9, 0xFF); c.Branch(0x84, "popupLiveSkip");
        c.Emit(0x39, 0x48, 0x04); c.Branch(0x85, "popupLiveSkip");
        c.Emit(0x81, 0x39); c.Dword(TableVtable); c.Branch(0x85, "popupLiveSkip");
        c.Jump("popupLiveOwner");
        c.Mark("popupLiveSkip"); c.Emit(0x83, 0xC6, EntrySize, 0x4A); c.Branch(0x85, "popupLiveNext"); c.Jump("popupDone");
        c.Mark("popupLiveOwner");
        c.Emit(0x81, 0x3F); c.Dword(ProfileVtable); c.Branch(0x85, "popupDone");
        LoadState(0xA1, RoleSynchronizeOffset); c.Emit(0x85, 0xC0); c.Branch(0x84, "popupDone");
        c.Emit(0x8B, 0xCF, 0xFF, 0xD0); // existing helper finds CURRENT Fpos; no stale popup use
        c.Mark("popupDone");
        c.Emit(0x0F, 0xAE, 0x0C, 0x24, 0x8B, 0xE5, 0x61, 0x9D, 0x5F, 0x5E, 0x5B, 0xC2, 0x08, 0);
        c.Mark("popupOriginal"); c.Emit(PopupCommitOriginal.ToArray()); c.Jump(PopupCommitAddress + (uint)PopupCommitOriginal.Length);

        c.Mark("popupOwner"); // ECX=still-live complete popup, returns current owner or0
        c.Emit(0x53, 0x56, 0x57, 0x8B, 0xF1);
        GuardEnabled("popupOwnerNone");
        c.Emit(0x81, 0x3E); c.Dword(0x0167466C); c.Branch(0x85, "popupOwnerNone");
        c.Emit(0x81, 0x7E, 0x30); c.Dword(0x46706F73); c.Branch(0x85, "popupOwnerNone");
        // Managed Fpos must still have the known native select_event -> mbch route.
        c.Emit(0x8B, 0x96); c.Dword(0x164); c.Emit(0x85, 0xD2); c.Branch(0x84, "popupOwnerNone");
        c.Emit(0x83, 0xFA, 0xFF); c.Branch(0x84, "popupOwnerNone");
        c.Emit(0x81, 0x3A); c.Dword(0x0166A12C); c.Branch(0x85, "popupOwnerNone");
        c.Emit(0x8B, 0x4A, 0x08, 0x85, 0xC9); c.Branch(0x84, "popupOwnerNone");
        c.Emit(0x83, 0xF9, 32); c.Branch(0x87, "popupOwnerNone");
        c.Emit(0x8B, 0x52, 0x04, 0x85, 0xD2); c.Branch(0x84, "popupOwnerNone");
        c.Mark("popupRouteNext");
        c.Emit(0x8B, 0x02, 0x85, 0xC0); c.Branch(0x84, "popupRouteSkip");
        c.Emit(0x83, 0xF8, 0xFF); c.Branch(0x84, "popupRouteSkip");
        c.Emit(0x81, 0x78, 0x08); c.Dword(0x65766964); c.Branch(0x85, "popupRouteSkip");
        c.Emit(0x81, 0x38); c.Dword(0x6D626368); c.Branch(0x85, "popupOwnerNone");
        c.Jump("popupRouteOk");
        c.Mark("popupRouteSkip"); c.Emit(0x83, 0xC2, 4, 0x49); c.Branch(0x85, "popupRouteNext"); c.Jump("popupOwnerNone");
        c.Mark("popupRouteOk"); c.Emit(0x8B, 0x7E, 0x04, 0xB9); c.Dword(32);
        c.Mark("popupParentNext");
        c.Emit(0x85, 0xFF); c.Branch(0x84, "popupOwnerNone");
        c.Emit(0x83, 0xFF, 0xFF); c.Branch(0x84, "popupOwnerNone");
        c.Emit(0x81, 0x3F); c.Dword(ProfileVtable); c.Branch(0x84, "popupParentFound");
        c.Emit(0x8B, 0x7F, 0x04, 0x49); c.Branch(0x85, "popupParentNext"); c.Jump("popupOwnerNone");
        c.Mark("popupParentFound");
        c.Emit(0x3B, 0x3D); c.Dword(state + ProfileOffset); c.Branch(0x85, "popupOwnerNone");
        c.Emit(0x8B, 0xC7); c.Jump("popupOwnerDone");
        c.Mark("popupOwnerNone"); c.Emit(0x33, 0xC0);
        c.Mark("popupOwnerDone"); c.Emit(0x5F, 0x5E, 0x5B, 0xC3);

        return new(c.Finish(), data, state, c.At("nameCreated"), c.At("draw"), c.At("beginHook"),
            c.At("destructorHook"), c.At("begin"), c.At("setRole"), c.At("register"), c.At("render"), c.At("invalidateLabel"), c.At("fontCopy"), c.At("popupCommit"), c.At("valueCreated"), c.At("registerValue"));
    }

    private sealed class NativeCode(uint address)
    {
        private readonly List<byte> bytes = [];
        private readonly Dictionary<string, int> labels = [];
        private readonly List<(int Offset, string Label)> fixups = [];
        internal uint At(string label) => address + (uint)labels[label];
        internal void Mark(string label) => labels.Add(label, bytes.Count);
        internal void Emit(params byte[] value) => bytes.AddRange(value);
        internal void Dword(uint value) { bytes.AddRange(BitConverter.GetBytes(value)); }
        internal void Call(uint target) { Emit(0xE8); Relative(target); }
        internal void Jump(uint target) { Emit(0xE9); Relative(target); }
        internal void Call(string label) { Emit(0xE8); Reference(label); }
        internal void Jump(string label) { Emit(0xE9); Reference(label); }
        internal void Branch(byte condition, string label) { Emit(0x0F, condition); Reference(label); }
        private void Reference(string label) { fixups.Add((bytes.Count, label)); Dword(0); }
        private void Relative(uint target) => Dword(unchecked(target - address - (uint)bytes.Count - 4));
        internal byte[] Finish()
        {
            var result = bytes.ToArray();
            foreach (var (offset, label) in fixups)
                BinaryPrimitives.WriteUInt32LittleEndian(result.AsSpan(offset, 4), unchecked((uint)(labels[label] - offset - 4)));
            return result;
        }
    }
}
