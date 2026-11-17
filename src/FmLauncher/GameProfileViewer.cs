namespace FmLauncher;

internal static partial class GamePanelPatch
{
    internal const uint GameScreenClientVtable = 0x012843A4;
    internal const uint PersonScreenVtable = 0x012A002C;

    private static void AppendProfileViewer(Code code, uint diagnosticState)
    {
        // Borrow a native typed local PERSON reference from a SCREEN property.
        // Unknown/nonlocal reference contexts are fail-closed; never use server scratch Hhum.
        code.Mark("profileUiReference");
        code.Emit(0x53,0x56,0x57,0x83,0xEC,0x04,0x8B,0xF1);
        code.Emit(0xC7,0x04,0x24);code.Dword(0xFF7FFFFF);
        code.Emit(0x85,0xF6);code.Branch(0x84,"profileUiReferenceDone");
        code.Emit(0x81,0x3E);code.Dword(0x0166A12C);code.Branch(0x85,"profileUiReferenceDone");
        code.Emit(0x81,0x7E,0x08);code.Dword(512);code.Branch(0x87,"profileUiReferenceDone");
        code.Emit(0x52,0x8B,0xCE);code.Call(0x00F4C200);
        code.Emit(0x85,0xC0);code.Branch(0x84,"profileUiReferenceDone");
        code.Emit(0x8B,0x48,0x04,0x85,0xC9);code.Branch(0x84,"profileUiReferenceDone");
        code.Emit(0x81,0x39);code.Dword(0x0166E1A4);code.Branch(0x85,"profileUiReferenceDone");
        code.Emit(0x8B,0xC8);code.Call(0x00F5BF40);
        code.Emit(0x85,0xC0);code.Branch(0x84,"profileUiReferenceDone");
        code.Emit(0x81,0x38);code.Dword(0x0166A12C);code.Branch(0x85,"profileUiReferenceDone");
        code.Emit(0x8B,0xF8);
        code.Push(0x64726566);code.Emit(0x8B,0xCF);code.Call(0x00F4C200);
        code.Emit(0x85,0xC0);code.Branch(0x84,"profileUiReferenceDone");
        code.Emit(0x8B,0x48,0x04,0x85,0xC9);code.Branch(0x84,"profileUiReferenceDone");
        code.Emit(0x81,0x39);code.Dword(IntegerVtable);code.Branch(0x85,"profileUiReferenceDone");
        code.Emit(0x8B,0x18,0x8B,0xC3,0xC1,0xE8,0x18,0x83,0xF8,0x01);
        code.Branch(0x85,"profileUiReferenceDone");
        code.Emit(0x8B,0xC3,0x25);code.Dword(0x00FFFFFF);
        code.Emit(0x3D);code.Dword(0x007FFFFF);code.Branch(0x83,"profileUiReferenceDone");
        code.Push(0x64636E74);code.Emit(0x8B,0xCF);code.Call(0x00F4C250);
        code.Emit(0x85,0xC0);code.Branch(0x84,"profileUiReferenceDone");
        code.Emit(0x8B,0x10,0x3B,0x15);code.Dword(0x01B2424C);code.Branch(0x85,"profileUiReferenceDone");
        code.Emit(0x8B,0x50,0x04,0x3B,0x15);code.Dword(0x01B24250);code.Branch(0x85,"profileUiReferenceDone");
        code.Emit(0x89,0x1C,0x24);
        code.Mark("profileUiReferenceDone");
        code.Emit(0x8B,0x04,0x24,0x83,0xC4,0x04,0x5F,0x5E,0x5B,0xC3);

        code.Mark("profileViewer");
        DiagnosticCount(code, diagnosticState, ProfileViewerCallsOffset);
        DiagnosticStage(code, diagnosticState, ProfileViewerStageOffset, 1);
        code.Emit(0x53,0x55,0x56,0x57,0x83,0xEC,0x24,0x8B,0xF1);
        code.Emit(0xC7,0x44,0x24,0x1C);code.Dword(0);
        code.Emit(0x85,0xF6);code.Branch(0x84,"profileViewerDone");
        code.Emit(0x81,0x3E);code.Dword(ClientPersonVtable);code.Branch(0x85,"profileViewerDone");
        DiagnosticStage(code, diagnosticState, ProfileViewerStageOffset, 2);
        code.Call("profileLocal");code.Emit(0x85,0xC0);code.Branch(0x84,"profileViewerDone");
        DiagnosticStage(code, diagnosticState, ProfileViewerStageOffset, 3);
        code.Emit(0xB9);code.Dword(ConnectionManagerAddress);code.Call(CurrentConnectionGetter);
        code.Emit(0x85,0xC0);code.Branch(0x84,"profileViewerDone");
        code.Emit(0x81,0x38);code.Dword(GameScreenClientVtable);code.Branch(0x85,"profileViewerDone");
        code.Emit(0x89,0x44,0x24,0x0C,0x8B,0x78,0x44,0x85,0xFF);
        code.Branch(0x84,"profileViewerDone");
        code.Emit(0x81,0x3F);code.Dword(PersonScreenVtable);code.Branch(0x85,"profileViewerDone");
        code.Emit(0x89,0x7C,0x24,0x10,0x8B,0x5F,0x3C,0x85,0xDB);
        code.Branch(0x84,"profileViewerDone");
        DiagnosticStage(code, diagnosticState, ProfileViewerStageOffset, 4);
        foreach(var property in new uint[]{0x64736861,0x64747479})
        {
            code.Push(property);code.Emit(0x8D,0x4E,0x10);code.Call(0x00F4C200);
            code.Emit(0x85,0xC0);code.Branch(0x84,"profileViewerDone");
            code.Emit(0x8B,0x48,0x04,0x85,0xC9);code.Branch(0x84,"profileViewerDone");
            code.Emit(0x81,0x39);code.Dword(IntegerVtable);code.Branch(0x85,"profileViewerDone");
        }
        code.Push(0x64636E74);code.Emit(0x8D,0x4E,0x10);code.Call(0x00F4C250);
        code.Emit(0x85,0xC0);code.Branch(0x84,"profileViewerDone");
        code.Emit(0x8B,0x10,0x3B,0x15);code.Dword(0x01B2424C);code.Branch(0x85,"profileViewerDone");
        code.Emit(0x8B,0x50,0x04,0x3B,0x15);code.Dword(0x01B24250);code.Branch(0x85,"profileViewerDone");
        code.Emit(0x8B,0xCE);code.Call(0x007701A0);
        code.Emit(0x83,0xF8,0x01);code.Branch(0x85,"profileViewerDone");
        code.Emit(0x8B,0xCE);code.Call(0x00770120);
        code.Emit(0x3D);code.Dword(0x007FFFFF);code.Branch(0x83,"profileViewerDone");
        code.Emit(0x0D);code.Dword(0x01000000);code.Emit(0x89,0x44,0x24,0x14);
        DiagnosticStage(code, diagnosticState, ProfileViewerStageOffset, 5);
        code.Emit(0x8B,0xCB,0xBA);code.Dword(0x64726566);code.Call("profileUiReference");
        code.Emit(0x3B,0x44,0x24,0x14);code.Branch(0x85,"profileViewerDone");
        DiagnosticStage(code, diagnosticState, ProfileViewerStageOffset, 6);
        code.Emit(0x8B,0xCB,0xBA);code.Dword(0x4868756D);code.Call("profileUiReference");
        code.Emit(0x3D);code.Dword(0xFF7FFFFF);code.Branch(0x84,"profileViewerDone");
        code.Emit(0x89,0x04,0x24,0x89,0x44,0x24,0x18);
        code.Emit(0xA1);code.Dword(0x01B2424C);code.Emit(0x89,0x44,0x24,0x04);
        code.Emit(0xA1);code.Dword(0x01B24250);code.Emit(0x89,0x44,0x24,0x08);
        DiagnosticStage(code, diagnosticState, ProfileViewerStageOffset, 7);
        code.Emit(0x8B,0xC4,0x50,0xB9);code.Dword(0x01B1ECD0);code.Call(0x00C2F270);
        code.Emit(0x85,0xC0);code.Branch(0x84,"profileViewerDone");
        code.Emit(0x81,0x38);code.Dword(0x015AE024);code.Branch(0x85,"profileViewerDone");
        code.Emit(0x83,0x78,0x14,0);code.Branch(0x8E,"profileViewerDone");
        code.Emit(0x8B,0x54,0x24,0x18,0x81,0xE2);code.Dword(0x007FFFFF);
        code.Emit(0x3B,0x50,0x18);code.Branch(0x85,"profileViewerDone");
        code.Push(0);code.Push(0x018BDFC4);code.Push(0x0187FE6C);code.Push(0);code.Emit(0x50);
        code.Call(0x0112FAF8);code.Emit(0x83,0xC4,0x14,0x85,0xC0);code.Branch(0x84,"profileViewerDone");
        code.Emit(0x81,0x38);code.Dword(HumanVtable);code.Branch(0x85,"profileViewerDone");
        code.Emit(0x8B,0xE8);
        DiagnosticStage(code, diagnosticState, ProfileViewerStageOffset, 9);
        code.Call("profileLocal");code.Emit(0x85,0xC0);code.Branch(0x84,"profileViewerDone");
        code.Emit(0xB9);code.Dword(ConnectionManagerAddress);code.Call(CurrentConnectionGetter);
        code.Emit(0x3B,0x44,0x24,0x0C);code.Branch(0x85,"profileViewerDone");
        code.Emit(0x8B,0x40,0x44,0x3B,0x44,0x24,0x10);code.Branch(0x85,"profileViewerDone");
        code.Emit(0x8B,0x58,0x3C,0x8B,0xCB,0xBA);code.Dword(0x4868756D);code.Call("profileUiReference");
        code.Emit(0x3B,0x44,0x24,0x18);code.Branch(0x85,"profileViewerDone");
        code.Emit(0x8B,0xCB,0xBA);code.Dword(0x64726566);code.Call("profileUiReference");
        code.Emit(0x3B,0x44,0x24,0x14);code.Branch(0x85,"profileViewerDone");
        code.Emit(0x89,0x6C,0x24,0x1C);
        DiagnosticStage(code, diagnosticState, ProfileViewerStageOffset, 100);
        DiagnosticCount(code, diagnosticState, ProfileViewerSuccessOffset);
        code.Mark("profileViewerDone");
        code.Emit(0x8B,0x44,0x24,0x1C,0x83,0xC4,0x24,0x5F,0x5E,0x5D,0x5B,0xC3);
    }
    private static void DiagnosticStage(Code code, uint state, int offset, uint stage)
    {
        code.Emit(0xC7, 0x05); code.Dword(state + (uint)offset); code.Dword(stage);
    }
    private static void DiagnosticCount(Code code, uint state, int offset)
    {
        code.Emit(0xF0, 0xFF, 0x05); code.Dword(state + (uint)offset);
    }
}
