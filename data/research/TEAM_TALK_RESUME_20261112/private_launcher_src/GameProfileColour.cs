namespace FmLauncher;

internal static partial class GamePanelPatch
{
    // These are the native named-setting handles selected by9B0358..9B038E.
    // F46CA0 resolves the current skin/user palette; no packed RGB is baked in.
    internal const uint AttributeLowColour = 0x01910D58;
    internal const uint AttributeNormalColour = 0x01910DF8;
    internal const uint AttributeGoodColour = 0x01910DC8;
    internal const uint AttributeExcellentColour = 0x01910DA4;
    internal const uint AttributeUnknownColour = 0x01910DE8;

    private static void AppendProfileColours(Code code)
    {
        code.Mark("profileFieldColour");
        // ECXborrowedfieldVARIANT, EDXprofile, stackLABEL*,ret4.
        // Preserve all callee registers; colour VARIANT is local and disposed.
        code.Emit(0x53,0x55,0x56,0x57,0x83,0xEC,0x10,0x8B,0xD9,0x8B,0xF2,0x8B,0x7C,0x24,0x24);
        code.Emit(0x85,0xFF);code.Branch(0x84,"profileColourDone");
        code.Emit(0x81,0x3F);code.Dword(0x01675554);code.Branch(0x85,"profileColourDone");
        code.Emit(0x85,0xF6);code.Branch(0x84,"profileColourDone");
        code.Emit(0x81,0x3E);code.Dword(PlayerProfileVtable);code.Branch(0x85,"profileColourDone");
        code.Emit(0x8B,0xCB);code.Call(0x00F5BD20); // preserves the field's own scope/range checks
        code.Emit(0xBD);code.Dword(AttributeUnknownColour);
        code.Emit(0x83,0xF8,0x01);code.Branch(0x8C,"profileColourSelected");
        code.Emit(0x83,0xF8,0x14);code.Branch(0x8F,"profileColourSelected");
        code.Emit(0xBD);code.Dword(AttributeExcellentColour);
        code.Emit(0x3B,0x86);code.Dword(0x100);code.Branch(0x8D,"profileColourSelected");
        code.Emit(0xBD);code.Dword(AttributeGoodColour);
        code.Emit(0x3B,0x86);code.Dword(0x104);code.Branch(0x8D,"profileColourSelected");
        code.Emit(0xBD);code.Dword(AttributeNormalColour);
        code.Emit(0x3B,0x86);code.Dword(0x108);code.Branch(0x8D,"profileColourSelected");
        code.Emit(0xBD);code.Dword(AttributeLowColour);
        code.Mark("profileColourSelected");
        code.Emit(0x55,0x8D,0x4C,0x24,0x0C);code.Call(0x00F46CA0); // DWORDcolour at local+8,ret4
        code.Emit(0x8D,0x44,0x24,0x08,0x50,0x8D,0x4C,0x24,0x04);code.Call(0x00F5EB90);
        code.Emit(0x8B,0xC4,0x50);code.Push(0x636F6C72); // native colour VARIANT -> colr
        code.Emit(0x8D,0x4F,0x10,0x8B,0x01,0xFF,0x50,0x08);
        code.Emit(0x8B,0xCC);code.Call(0x00F5BC90);
        code.Mark("profileColourDone");
        code.Emit(0x83,0xC4,0x10,0x5F,0x5E,0x5D,0x5B,0xC2,0x04,0);
    }
}
