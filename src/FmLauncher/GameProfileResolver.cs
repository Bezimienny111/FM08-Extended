namespace FmLauncher;

internal static partial class GamePanelPatch
{
    internal const uint ClientPersonVtable = 0x012776CC;
    internal const uint ClientClubVtable = 0x01523074;
    internal const uint ClubVtable = 0x015996C4;
    internal const uint ClientPersonResolver = 0x007709D0;

    // Every call revalidates the local session and the public client club BEFORE the
    // selected-person lookup. It returns a borrowed core only for this conversion.
    private static void AppendProfileResolver(Code code, uint diagnosticState)
    {
        code.Mark("profileLocal");
        code.Emit(0x80, 0x3D); code.Dword(RunAsServerAddress); code.Emit(0);
        code.Branch(0x85, "profileLocalNo");
        code.Emit(0x83, 0x3D); code.Dword(ConnectionManagerAddress + 8); code.Emit(0);
        code.Branch(0x84, "profileLocalNo");
        code.Emit(0xB9); code.Dword(ConnectionManagerAddress); code.Call(CurrentConnectionGetter);
        code.Emit(0x85, 0xC0); code.Branch(0x84, "profileLocalNo");
        code.Emit(0x8B, 0x40, 0x64, 0x85, 0xC0); code.Branch(0x84, "profileLocalNo");
        code.Emit(0x81, 0x38); code.Dword(LocalConnectionVtable); code.Branch(0x85, "profileLocalNo");
        code.Emit(0xB8); code.Dword(1); code.Emit(0xC3);
        code.Mark("profileLocalNo"); code.Emit(0x33, 0xC0, 0xC3);

        code.Mark("profileResolve");
        DiagnosticCount(code, diagnosticState, ProfileResolveCallsOffset);
        DiagnosticStage(code, diagnosticState, ProfileResolveStageOffset, 1);
        code.Emit(0x53, 0x55, 0x56, 0x57, 0x83, 0xEC, 0x20, 0x8B, 0xF1);
        code.Emit(0xC7, 0x44, 0x24, 0x1C); code.Dword(0);
        code.Emit(0x85, 0xF6); code.Branch(0x84, "profileResolveDone");
        code.Emit(0x81, 0x3E); code.Dword(ClientPersonVtable); code.Branch(0x85, "profileResolveDone");
        code.Call("profileLocal"); code.Emit(0x85, 0xC0); code.Branch(0x84, "profileResolveDone");
        DiagnosticStage(code, diagnosticState, ProfileResolveStageOffset, 3);
        code.Emit(0x8B, 0xCE); code.Call("profileViewer");
        code.Emit(0x85, 0xC0); code.Branch(0x84, "profileResolveDone");
        code.Emit(0x81, 0x38); code.Dword(HumanVtable); code.Branch(0x85, "profileResolveDone");
        code.Emit(0x89, 0x04, 0x24, 0x8B, 0x48, 0x04, 0x85, 0xC9);
        code.Branch(0x84, "profileResolveDone");
        code.Emit(0x8B, 0x49, 0x04, 0x8D, 0x4C, 0x08, 0x04, 0x8B, 0x11, 0xFF, 0x92); code.Dword(0x110);
        code.Emit(0x85, 0xC0); code.Branch(0x84, "profileResolveDone");
        code.Emit(0x81, 0x38); code.Dword(ClubVtable); code.Branch(0x85, "profileResolveDone");
        code.Emit(0x89, 0x44, 0x24, 0x04, 0x8B, 0x40, 0x18, 0x85, 0xC0);
        code.Branch(0x88, "profileResolveDone");
        code.Emit(0x3D); code.Dword(0x7FFFFF); code.Branch(0x83, "profileResolveDone");
        code.Emit(0x89, 0x44, 0x24, 0x08);


        DiagnosticStage(code, diagnosticState, ProfileResolveStageOffset, 5);
        // Real CLIENT_BASE_PERSON has dtty=1 and dsub=Pply. dsha is its PERSON
        // reference index; type0 is a different native table. Both fields must be typed.
        foreach (var property in new uint[] { 0x64736861, 0x64747479 })
        {
            code.Push(property); code.Emit(0x8D, 0x4E, 0x10); code.Call(0x00F4C200);
            code.Emit(0x85, 0xC0); code.Branch(0x84, "profileResolveDone");
            code.Emit(0x8B, 0x50, 0x04, 0x85, 0xD2); code.Branch(0x84, "profileResolveDone");
            code.Emit(0x81, 0x3A); code.Dword(IntegerVtable); code.Branch(0x85, "profileResolveDone");
        }
        code.Emit(0x8B, 0xCE); code.Call(0x007701A0);
        code.Emit(0x83, 0xF8, 0x01); code.Branch(0x85, "profileResolveDone");
        code.Emit(0x8B, 0xCE); code.Call(0x00770120);
        code.Emit(0x85, 0xC0); code.Branch(0x88, "profileResolveDone");
        code.Emit(0x3D); code.Dword(0x7FFFFF); code.Branch(0x83, "profileResolveDone");
        code.Emit(0x89, 0x44, 0x24, 0x10);
        code.Push(0x64737562); code.Emit(0x8D, 0x4E, 0x10); code.Call(0x00F4C200); // dsub
        code.Emit(0x85, 0xC0); code.Branch(0x84, "profileResolveDone");
        code.Emit(0x8B, 0x50, 0x04, 0x85, 0xD2); code.Branch(0x84, "profileResolveDone");
        code.Emit(0x81, 0x3A); code.Dword(0x0166DE5C); code.Branch(0x85, "profileResolveDone");
        code.Emit(0x81, 0x38); code.Dword(0x50706C79); code.Branch(0x85, "profileResolveDone"); // Pply

        // Pcte is a public TEAM reference, not a CLIENT_CLUB object. Resolve that
        // public TEAM and compare its native club before any selected PERSON lookup.
        DiagnosticStage(code, diagnosticState, ProfileResolveStageOffset, 6);
        code.Emit(0x8B, 0xCE); code.Call("profileTeamClub");
        code.Emit(0x85, 0xC0); code.Branch(0x84, "profileResolveDone");
        code.Emit(0x3B, 0x44, 0x24, 0x04); code.Branch(0x85, "profileResolveDone");
        code.Call("profileLocal"); code.Emit(0x85, 0xC0); code.Branch(0x84, "profileResolveDone");

        DiagnosticStage(code, diagnosticState, ProfileResolveStageOffset, 7);
        code.Emit(0x8B, 0xCE); code.Call(ClientPersonResolver);
        code.Emit(0x85, 0xC0); code.Branch(0x84, "profileResolveDone");
        code.Emit(0x81, 0x38); code.Dword(0x015AB12C); code.Branch(0x85, "profileResolveDone");
        code.Emit(0x83, 0x78, 0x14, 0); code.Branch(0x8E, "profileResolveDone");
        code.Emit(0x8B, 0x50, 0x18, 0x3B, 0x54, 0x24, 0x10); code.Branch(0x85, "profileResolveDone");
        code.Push(0); code.Push(0x018EBF00); code.Push(0x0187FE6C); code.Push(0); code.Emit(0x50);
        code.Call(0x0112FAF8); code.Emit(0x83, 0xC4, 0x14);
        code.Emit(0x85, 0xC0); code.Branch(0x84, "profileResolveDone");
        code.Emit(0x81, 0x38); code.Dword(PlayerVtable); code.Branch(0x85, "profileResolveDone");
        code.Emit(0x8B, 0xE8);
        code.Emit(0x8B, 0xCE); code.Call(0x00770120);
        code.Emit(0x3B, 0x44, 0x24, 0x10); code.Branch(0x85, "profileResolveDone");
        code.Emit(0x8B, 0xCE); code.Call("profileViewer");
        code.Emit(0x3B, 0x04, 0x24); code.Branch(0x85, "profileResolveDone");
        code.Call("profileLocal"); code.Emit(0x85, 0xC0); code.Branch(0x84, "profileResolveDone");
        code.Emit(0x89, 0x6C, 0x24, 0x1C);
        DiagnosticStage(code, diagnosticState, ProfileResolveStageOffset, 100);
        DiagnosticCount(code, diagnosticState, ProfileResolveSuccessOffset);
        code.Mark("profileResolveDone");
        code.Emit(0x8B, 0x44, 0x24, 0x1C, 0x83, 0xC4, 0x20, 0x5F, 0x5E, 0x5D, 0x5B, 0xC3);

        code.Mark("profileTeamClub");
        // thiscall ECXclient -> borrowed CLUB or0. Reference on stack has the
        // original packed dref + borrowed context variant, consumed synchronously.
        code.Emit(0x53, 0x56, 0x57, 0x83, 0xEC, 0x18, 0x8B, 0xF1);
        code.Emit(0xC7, 0x44, 0x24, 0x0C); code.Dword(0);
        code.Push(0x50637465); code.Emit(0x8D, 0x4E, 0x10); code.Call(0x00F4C200); // Pcte
        code.Emit(0x85, 0xC0); code.Branch(0x84, "profileTeamDone");
        code.Emit(0x8B, 0x50, 0x04, 0x85, 0xD2); code.Branch(0x84, "profileTeamDone");
        code.Emit(0x81, 0x3A); code.Dword(0x0166E1A4); code.Branch(0x85, "profileTeamDone");
        code.Emit(0x8B, 0xC8); code.Call(0x00F5BF40); // native PROPERTY_LIST converter
        code.Emit(0x85, 0xC0); code.Branch(0x84, "profileTeamDone");
        code.Emit(0x81, 0x38); code.Dword(0x0166A12C); code.Branch(0x85, "profileTeamDone");
        code.Emit(0x8B, 0xF8);
        code.Push(0x64726566); code.Emit(0x8B, 0xCF); code.Call(0x00F4C200); // dref
        code.Emit(0x85, 0xC0); code.Branch(0x84, "profileTeamDone");
        code.Emit(0x8B, 0x50, 0x04, 0x85, 0xD2); code.Branch(0x84, "profileTeamDone");
        code.Emit(0x81, 0x3A); code.Dword(IntegerVtable); code.Branch(0x85, "profileTeamDone");
        code.Emit(0x8B, 0x00, 0x89, 0x04, 0x24, 0x8B, 0xD0, 0xC1, 0xEA, 0x18);
        code.Emit(0x83, 0xFA, 0x18); code.Branch(0x85, "profileTeamDone");
        code.Emit(0x25); code.Dword(0x00FFFFFF); // reject unsupported reference flag/sentinel bits
        code.Emit(0x3D); code.Dword(0x007FFFFF); code.Branch(0x83, "profileTeamDone");

        // A reference from another context must never cross into the local game.
        // Native F4C250 supplies the same canonical missing variant for both absent.
        code.Push(0x64636E74); code.Emit(0x8D, 0x4E, 0x10); code.Call(0x00F4C250);
        code.Emit(0x85, 0xC0); code.Branch(0x84, "profileTeamDone");
        code.Emit(0x8B, 0xD8);
        code.Push(0x64636E74); code.Emit(0x8B, 0xCF); code.Call(0x00F4C250);
        code.Emit(0x85, 0xC0); code.Branch(0x84, "profileTeamDone");
        code.Emit(0x8B, 0x10, 0x3B, 0x13); code.Branch(0x85, "profileTeamDone");
        code.Emit(0x89, 0x54, 0x24, 0x04);
        code.Emit(0x8B, 0x50, 0x04, 0x3B, 0x53, 0x04); code.Branch(0x85, "profileTeamDone");
        code.Emit(0x89, 0x54, 0x24, 0x08);
        code.Emit(0x8B, 0xC4, 0x50, 0xB9); code.Dword(0x01B1ECD0);
        code.Call(0x00C2F270); // only public type18 TEAM, never selected PERSON
        code.Emit(0x85, 0xC0); code.Branch(0x84, "profileTeamDone");
        code.Emit(0x81, 0x38); code.Dword(0x015A9E0C); code.Branch(0x85, "profileTeamDone");
        code.Emit(0x8B, 0xC8); code.Call(0x00C7C7A0); // original TEAM::club, rejects national TEAM
        code.Emit(0x85, 0xC0); code.Branch(0x84, "profileTeamDone");
        code.Emit(0x81, 0x38); code.Dword(ClubVtable); code.Branch(0x85, "profileTeamDone");
        code.Emit(0x89, 0x44, 0x24, 0x0C);
        code.Mark("profileTeamDone");
        code.Emit(0x8B, 0x44, 0x24, 0x0C, 0x83, 0xC4, 0x18, 0x5F, 0x5E, 0x5B, 0xC3);
        AppendProfileViewer(code, diagnosticState);
        AppendProfileColours(code);
    }
}
