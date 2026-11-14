namespace FmLauncher;

internal static partial class GamePanelPatch
{
    internal const uint ProfileSetAddress = 0x009AF630;
    internal const uint ProfileEventAddress = 0x009B2730;
    internal const uint ProfileInitAddress = 0x009B21F0;
    internal const uint PlayerProfileVtable = 0x0156A984;
    internal const uint RunAsServerAddress = 0x0191136A;
    internal const uint ConnectionManagerAddress = 0x01BC1CB0;
    internal const uint CurrentConnectionGetter = 0x00F9A010;
    internal const uint LocalConnectionVtable = 0x01672F38;
    internal static ReadOnlySpan<byte> ProfileSetOriginal => [0x64, 0xA1, 0, 0, 0, 0];
    internal static ReadOnlySpan<byte> ProfileEventOriginal => [0x53, 0x8B, 0x5C, 0x24, 0x0C];
    internal static ReadOnlySpan<byte> ProfileInitOriginal => [0x55, 0x8B, 0xEC, 0x83, 0xE4, 0xF8];

    private static void AppendProfile(Code code, uint[] types, Func<int, uint> reserve,
        Action<uint, uint> set, Action<uint> setControl, uint positionSetRole)
    {
        var fieldIds = reserve(PlayerProfileFields.Hidden.Count * 4);
        var fieldTypes = reserve(PlayerProfileFields.Hidden.Count * 4);
        for (var index = 0; index < PlayerProfileFields.Hidden.Count; index++)
        {
            set(fieldIds + (uint)(index * 4), PlayerProfileFields.Hidden[index].Property);
            set(fieldTypes + (uint)(index * 4), types[index + 4]);
        }

        // Each wrapper delegates to the original entry with its exact thiscall arguments.
        // No PERSON or widget pointer survives the synchronous call.
        code.Mark("profileSet");
        code.Emit(0x53, 0x8B, 0xD9, 0xFF, 0x74, 0x24, 0x0C, 0xFF, 0x74, 0x24, 0x0C);
        code.Call("profileSetOriginal");
        code.Emit(0x50, 0x81, 0x7C, 0x24, 0x0C); code.Dword(0x50657273); // Pers
        code.Branch(0x85, "profileSetDone");
        code.Emit(0x8D, 0x4B, 0xF0); code.Call("updateProfile"); // property subobject -10 -> main
        code.Mark("profileSetDone");
        code.Emit(0x58, 0x5B, 0xC2, 0x08, 0);
        code.Mark("profileSetOriginal");
        code.Emit(ProfileSetOriginal.ToArray());
        code.Jump(ProfileSetAddress + (uint)ProfileSetOriginal.Length);

        code.Mark("profileEvent");
        code.Emit(0x53, 0x8B, 0xD9, 0xFF, 0x74, 0x24, 0x0C, 0xFF, 0x74, 0x24, 0x0C);
        code.Call("profileEventOriginal");
        code.Emit(0x50);
        // Do not touch the panel after arbitrary/destruction events delegated to the base.
        // Only the three proven native profile refresh routes may read its current PERSON.
        code.Emit(0x81, 0x7C, 0x24, 0x0C); code.Dword(0x696E6974);
        code.Branch(0x84, "profileKnownEvent");
        code.Emit(0x81, 0x7C, 0x24, 0x0C); code.Dword(0x6D626368);
        code.Branch(0x84, "profileKnownEvent");
        code.Emit(0x81, 0x7C, 0x24, 0x0C); code.Dword(0x73737070);
        code.Branch(0x85, "profileEventDone");
        code.Mark("profileKnownEvent");
        code.Emit(0x8B, 0xCB); code.Call("updateProfile");
        code.Mark("profileEventDone");
        code.Emit(0x58, 0x5B, 0xC2, 0x08, 0);
        code.Mark("profileEventOriginal");
        code.Emit(ProfileEventOriginal.ToArray());
        code.Jump(ProfileEventAddress + (uint)ProfileEventOriginal.Length);

        code.Mark("profileInit");
        code.Emit(0x53, 0x8B, 0xD9, 0xFF, 0x74, 0x24, 0x08);
        code.Call("profileInitOriginal");
        code.Emit(0x50, 0x8B, 0xCB); code.Call("updateProfile");
        code.Emit(0x58, 0x5B, 0xC2, 0x04, 0);
        code.Mark("profileInitOriginal");
        code.Emit(ProfileInitOriginal.ToArray());
        code.Jump(ProfileInitAddress + (uint)ProfileInitOriginal.Length);

        code.Mark("updateProfile");
        // Preserve the caller's registers/flags and floating-point state around UI operations.
        code.Emit(0x9C, 0x60, 0x8B, 0xEC, 0x81, 0xEC); code.Dword(528);
        code.Emit(0x83, 0xE4, 0xF0, 0x0F, 0xAE, 0x04, 0x24);
        code.Call("updateProfileCore");
        code.Emit(0x0F, 0xAE, 0x0C, 0x24, 0x8B, 0xE5, 0x61, 0x9D, 0xC3);

        code.Mark("updateProfileCore");
        code.Emit(0x53, 0x55, 0x56, 0x57, 0x83, 0xEC, 0x08, 0x8B, 0xF1);
        code.Emit(0x85, 0xF6); code.Branch(0x84, "profileUpdateDone");
        code.Emit(0x81, 0x3E); code.Dword(PlayerProfileVtable);
        code.Branch(0x85, "profileUpdateDone");
        if (positionSetRole != 0) { code.Emit(0x8B, 0xCE); code.Call("profileRole"); }
        code.Emit(0x33, 0xDB, 0x8B, 0x86); code.Dword(0x88);
        code.Emit(0x85, 0xC0); code.Branch(0x84, "profileFields");
        code.Emit(0x81, 0x38); code.Dword(ClientPersonVtable);
        code.Branch(0x85, "profileServerRecord");
        code.Emit(0x8B, 0xD8); code.Jump("profileFields");
        code.Mark("profileServerRecord");
        code.Emit(0x81, 0x38); code.Dword(0x015AB12C);
        code.Branch(0x85, "profileFields");
        code.Push(0); code.Push(0x018EBF00); code.Push(0x0187FE6C); code.Push(0);
        code.Emit(0x50); code.Call(0x0112FAF8);
        code.Emit(0x83, 0xC4, 0x14, 0x8B, 0xD8);
        code.Mark("profileFields");
        code.Emit(0x33, 0xED);
        code.Mark("profileNextField");
        // Native recursive FindChild takes its16-byte lookup object by value and ret18.
        code.Emit(0x83, 0xEC, 0x10, 0x8B, 0xC4, 0xC7, 0x00); code.Dword(0x01233A10);
        code.Emit(0xC7, 0x40, 0x08); code.Dword(0);
        code.Emit(0xC7, 0x40, 0x0C); code.Dword(0);
        code.Push(0);
        code.Emit(0xFF, 0x34, 0xAD); code.Dword(fieldIds);
        code.Emit(0x8B, 0x06, 0x8B, 0xCE, 0xFF, 0x90); code.Dword(0xC4);
        code.Emit(0x85, 0xC0); code.Branch(0x84, "profileFieldDone");
        code.Emit(0x8B, 0xF8, 0x89, 0x1C, 0x24, 0x8B, 0x04, 0xAD); code.Dword(fieldTypes);
        code.Emit(0x89, 0x44, 0x24, 0x04);
        setControl(0x74657874);
        code.Emit(0x8B, 0xCC, 0x57, 0x8B, 0xD6); code.Call("profileFieldColour");
        code.Mark("profileFieldDone");
        code.Emit(0x45, 0x83, 0xFD, (byte)PlayerProfileFields.Hidden.Count);
        code.Branch(0x8C, "profileNextField");
        code.Mark("profileUpdateDone");
        code.Emit(0x83, 0xC4, 0x08, 0x5F, 0x5E, 0x5D, 0x5B, 0xC3);
        if (positionSetRole != 0) AppendProfileRole(code, positionSetRole);
    }
}
