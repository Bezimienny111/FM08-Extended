namespace FmLauncher;

/// <summary>R5-only Rules text adapter. Calls the installed engine getters; never mutates rule/save objects.
/// Active mask is derived from verified applied receipts by the caller, not desired configuration.</summary>
internal static class GameRuleDisplayPatch
{
    internal const uint EntryAddress = 0x00AFDBF0;
    internal const int EntryLength = 7;
    internal const int NativeFormatterLength = 0x28C;
    internal const int TrampolineOffset = 0x180, ActiveCodesOffset = 0x200, PayloadSize = 0x220;
    internal const uint TemplateAddress = 0x01586E70;
    internal const uint NumberFormatAddress = 0x01B205CC;
    internal const uint SetTemplateAddress = 0x00F521C0, SetNumberAddress = 0x00F55BC0;
    internal static ReadOnlySpan<byte> OriginalEntry => [0x56,0x57,0x0F,0xBE,0x7C,0x24,0x0C];

    // AFDBF0 is cdecl(code:int8, caller-owned GameString*, sideFlag:int8).
    // Native F521C0/F55BC0 are thiscall, ret8/ret12. No string is owned by this adapter.
    internal static byte[] BuildPayload(uint address, ReadOnlySpan<byte> activeCodes29)
    {
        if (address < 0x10000 || address > 0x7FFF0000) throw new ArgumentOutOfRangeException(nameof(address));
        if (activeCodes29.Length != 29) throw new ArgumentException("Exactly29 applied code flags required.",nameof(activeCodes29));
        foreach (var value in activeCodes29) if (value > 1) throw new ArgumentException("Applied flags must be0or1.",nameof(activeCodes29));
        var c = new NativeCode(address);
        c.Emit(0x55,0x8B,0xEC,0x53,0x56,0x57); // frame + preserve EBX,ESI,EDI
        c.Emit(0x0F,0xBE,0x7D,0x08,0x83,0xFF,0x1C); // signed native code; unsigned bounds reject negatives
        c.Branch(0x87,"native");
        c.Emit(0x0F,0xB6,0x87); c.Dword(address+ActiveCodesOffset);
        c.Emit(0x85,0xC0); c.Branch(0x84,"native");
        c.Emit(0x8B,0x75,0x0C,0x0F,0xB6,0x5D,0x10); // ESI=original receiver; EBX=original native side byte
        c.Emit(0x6A,0,0x68); c.Dword(TemplateAddress);
        c.Emit(0x8B,0xCE); c.Call(SetTemplateAddress);
        EffectiveNumber(0x00AFE150,1); // bench getter, same native code+side as simulation
        EffectiveNumber(0x00AFE0D0,2); // substitutions getter; untouched dimension falls back natively
        c.Emit(0xB8,1,0,0,0,0x5F,0x5E,0x5B,0x5D,0xC3);
        c.Mark("native");
        c.Emit(0x5F,0x5E,0x5B,0x5D); c.Jump(address+TrampolineOffset);
        var code=c.Finish();
        if(code.Length>TrampolineOffset)throw new InvalidOperationException("Rules display code overlaps trampoline.");
        var payload=new byte[PayloadSize];code.CopyTo(payload,0);
        var original=new NativeCode(address+TrampolineOffset);
        original.Emit(OriginalEntry.ToArray());original.Jump(EntryAddress+EntryLength);
        original.Finish().CopyTo(payload,TrampolineOffset);
        activeCodes29.CopyTo(payload.AsSpan(ActiveCodesOffset,29));
        return payload;

        void EffectiveNumber(uint getter,byte token)
        {
            c.Emit(0x53,0x57);c.Call(getter);c.Emit(0x83,0xC4,8,0x0F,0xB6,0xC0);
            c.Emit(0x68);c.Dword(NumberFormatAddress);c.Emit(0x50,0x6A,token,0x8B,0xCE);c.Call(SetNumberAddress);
        }
    }

    internal static byte[] BuildEntryJump(uint target)
    {
        var c=new NativeCode(EntryAddress);c.Jump(target);c.Emit(0x90,0x90);return c.Finish();
    }
}
