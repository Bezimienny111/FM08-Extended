namespace FmLauncher;

internal static partial class GamePanelPatch
{
    private static void AppendProfileRole(Code code, uint setRole)
    {
        code.Mark("profileRole");
        code.Emit(0x53,0x55,0x56,0x57,0x83,0xEC,0x08,0x8B,0xF1,0x33,0xDB);
        code.Emit(0x83,0xEC,0x10,0x8B,0xC4,0xC7,0);
        code.Dword(0x01233A10);
        code.Emit(0xC7,0x40,0x08);code.Dword(0);code.Emit(0xC7,0x40,0x0C);code.Dword(0);
        code.Push(0);code.Push(0x46706F73); // Fpos
        code.Emit(0x8B,0x06,0x8B,0xCE,0xFF,0x90);code.Dword(0xC4);
        code.Emit(0x85,0xC0);code.Branch(0x84,"profileRoleApply");
        code.Emit(0x8B,0xF8,0x8B,0xCC);code.Call(0x00F5E670);
        code.Emit(0x8B,0xC4,0x50);code.Push(0x736C6374); // selection/slct, NOT select_event/sele
        code.Emit(0x8D,0x4F,0x10,0x8B,0x01,0xFF,0x50,0x04);
        code.Emit(0x84,0xC0);code.Branch(0x84,"profileRoleDispose");
        code.Emit(0x8B,0xCC);code.Call(0x00F5BDA0); // native SYMBOL -> FourCC
        for(var i=0;i<PositionHighlightModel.Roles.Count;i++)
        {
            var text=PlayerProfileXml.RoleItemId(i);
            uint id=((uint)text[0]<<24)|((uint)text[1]<<16)|((uint)text[2]<<8)|text[3];
            code.Emit(0x3D);code.Dword(id);code.Branch(0x85,"profileRoleNext"+i);
            code.Emit(0xBB);code.Dword((uint)i+1);code.Jump("profileRoleDispose");
            code.Mark("profileRoleNext"+i);
        }
        code.Mark("profileRoleDispose");
        code.Emit(0x8B,0xCC);code.Call(0x00F5BC90);
        code.Mark("profileRoleApply");
        code.Emit(0x53,0x8B,0xCE);code.Call(setRole);
        code.Emit(0x83,0xC4,0x08,0x5F,0x5E,0x5D,0x5B,0xC3);
    }
}
