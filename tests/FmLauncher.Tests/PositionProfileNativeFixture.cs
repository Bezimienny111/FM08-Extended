using System;
using System.IO;
using FmLauncher;
using Marshal = PanelRemoteMemory;

internal static partial class NativePanelFixture
{
    internal static void TestPositionProfile(string gamePath)
    {
        using var remote = new PanelRemoteProcess(gamePath);
        Marshal.Process = remote;
        var code = AllocatePanel(0x10000000,8192);
        var data = AllocatePanel(0x11000000,65536);
        var positionCode = AllocatePanel(0x10100000,4096);
        var positionState = AllocatePanel(0x11100000,4096);
        var scratch = AllocatePanel(0x12000000,0x40000);
        var profile=IntPtr.Add(scratch,0x1000);
        var popup=IntPtr.Add(scratch,0x2000);
        var popupProperties=IntPtr.Add(scratch,0x2400);
        var types=IntPtr.Add(scratch,0x3000);
        var menuPointer=IntPtr.Add(scratch,0x4000);
        var classes=new byte[12*47];
        for(int r=0;r<11;r++)for(int a=0;a<47;a++)
            classes[(r+1)*47+a]=(byte)PositionHighlightModel.Emphasis(PositionHighlightModel.Roles[r].Code,
                GamePositionBackgroundPatch.NativeAttributes[a]);
        var pos=GamePositionBackgroundPatch.Build(0x10100000,0x11100000,classes,true);
        Marshal.Copy(pos.Code,0,positionCode,pos.Code.Length);Marshal.Copy(pos.Data,0,positionState,pos.Data.Length);
        byte[] vt=new byte[0x70];
        using(var f=File.OpenRead(gamePath)){f.Position=GamePanelPatch.IntegerVtable-0x400000;f.ReadExactly(vt);}
        var localizer=new Localizer(Path.Combine(AppContext.BaseDirectory,"FmLauncher.languages.json"));localizer.Select("pl");
        var panel=GamePanelPatch.Build(0x10000000,0x11000000,vt,localizer,new(true,false),false,pos.SetRoleEntry);
        Marshal.Copy(panel.Code,0,code,panel.Code.Length);Marshal.Copy(panel.Data,0,data,panel.Data.Length);
        var initTypes=PanelFunction<PanelTraining>(0x1200D000,new byte[]{
            0x8B,0x4C,0x24,0x04,0xB8,0x80,0xE0,0xF5,0,0xFF,0xD0,0xC3});
        initTypes(types);Marshal.WriteInt32(new IntPtr(0x01B24238),types.ToInt32());
        Marshal.WriteInt32(profile,0x0156A984);
        Marshal.WriteInt32(popup,0x10,popupProperties.ToInt32());
        Marshal.WriteInt32(popupProperties,4,0x00FB61E0); // Original POPUP property getter, ret8.
        Marshal.WriteInt32(menuPointer,popup.ToInt32());
        WritePanelCode(0x1200D100,Join(new byte[]{0x81,0x7C,0x24,0x04},
            BitConverter.GetBytes(0x46706F73),new byte[]{0x75,0x08,0xA1},
            BitConverter.GetBytes(menuPointer.ToInt32()),new byte[]{0xC2,0x18,0,0x33,0xC0,0xC2,0x18,0}));
        Marshal.WriteInt32(new IntPtr(0x0156A984+0xC4),0x1200D100);
        var begin=PanelFunction<PanelTraining>(0x1200D200,Join(new byte[]{0x8B,0x4C,0x24,0x04,0xB8},
            BitConverter.GetBytes(pos.BeginGenerationEntry),new byte[]{0xFF,0xD0,0xC3}));
        var refresh=PanelFunction<PanelTraining>(0x1200D300,Join(new byte[]{0x8B,0x4C,0x24,0x04,0xB8},
            BitConverter.GetBytes(panel.ProfileUpdateEntry),new byte[]{0xFF,0xD0,0xC3}));
        Require(panel.ProfileRoleEntry!=0,"Production role callback is exported.");
        Marshal.WriteInt32(positionState,GamePositionBackgroundPatch.RoleSynchronizeOffset,
            unchecked((int)panel.ProfileRoleEntry));
        var postFillRole=PanelFunction<PanelTraining>(0x1200D380,Join(new byte[]{0x8B,0x4C,0x24,0x04,0xB8},
            BitConverter.GetBytes(panel.ProfileRoleEntry),new byte[]{0xFF,0xD0,0xC3}));
        begin(profile);
        Marshal.WriteInt32(popup,0x160,0x46703033);postFillRole(profile);
        Require(Marshal.ReadInt32(positionState,12)==3,"Exported post-Fill callback reads current native popup Fp03.");
        Marshal.WriteInt32(popup,0x160,0x46706E30);postFillRole(profile);
        Require(Marshal.ReadInt32(positionState,12)==0,"Exported callback OFF clears role.");
        Marshal.WriteInt32(menuPointer,0);postFillRole(profile);
        Require(Marshal.ReadInt32(positionState,12)==0,"Exported callback missing menu stays OFF.");
        Marshal.WriteInt32(menuPointer,popup.ToInt32());
        for(int role=1;role<=11;role++)
        {
            string id=PlayerProfileXml.RoleItemId(role-1);
            int tag=(id[0]<<24)|(id[1]<<16)|(id[2]<<8)|id[3];
            Marshal.WriteInt32(popup,0x160,tag);
            refresh(profile);
            Require(Marshal.ReadInt32(positionState,12)==role,"Native popup SYMBOL/slct -> role"+role);
        }
        foreach(int missing in new[]{0x46706E30,0,0x78787878})
        {
            Marshal.WriteInt32(popup,0x160,missing);refresh(profile);
            Require(Marshal.ReadInt32(positionState,12)==0,"Unknown/OFF selection clears role.");
        }
        Marshal.WriteInt32(popup,0x160,0x46703031);refresh(profile);
        Require(Marshal.ReadInt32(positionState,12)==1,"GK selected.");
        Marshal.WriteInt32(menuPointer,0);refresh(profile);
        Require(Marshal.ReadInt32(positionState,12)==0,"Missing Fpos clears previous role.");
        // Reproduce the real first-choice regression through the original native commit:
        // real MENU_ITEM+PROPERTY_LIST and SYMBOL, then installed hook -> production role helper.
        // Only FindChild and repaint notification are headless boundaries, not selection/getter.
        var table=IntPtr.Add(scratch,0x6000);var label=IntPtr.Add(scratch,0x6800);
        var menu=IntPtr.Add(scratch,0x7000);var vector=IntPtr.Add(scratch,0x7100);
        var property=IntPtr.Add(scratch,0x7200);var route=IntPtr.Add(scratch,0x7400);
        var routeVector=IntPtr.Add(scratch,0x7500);var routeProperty=IntPtr.Add(scratch,0x7600);
        Marshal.WriteInt32(table,unchecked((int)GamePositionBackgroundPatch.TableVtable));
        Marshal.WriteInt32(label,unchecked((int)GamePositionBackgroundPatch.LabelVtable));Marshal.WriteInt32(label,4,table.ToInt32());
        Marshal.WriteInt32(profile,0x98,table.ToInt32());
        Marshal.WriteInt32(popup,0x0167466C);Marshal.WriteInt32(popup,4,profile.ToInt32());
        Marshal.WriteInt32(popup,0x30,0x46706F73);Marshal.WriteInt32(popup,0x164,route.ToInt32());
        Marshal.WriteByte(popup,0x17E,1); // fixed caption skips unrelated actual GUI repaint/text factory.
        Marshal.WriteInt32(route,0x0166A12C);Marshal.WriteInt32(route,4,routeVector.ToInt32());
        Marshal.WriteInt32(route,8,1);Marshal.WriteInt32(route,12,4);Marshal.WriteInt32(routeVector,routeProperty.ToInt32());
        Marshal.WriteInt32(routeProperty,0x6D626368);Marshal.WriteInt32(routeProperty,4,IntPtr.Add(types,0x14).ToInt32());
        Marshal.WriteInt32(routeProperty,8,0x65766964);
        Marshal.WriteInt32(menu,0x0168DA44);Marshal.WriteInt32(menu,4,0x0166A12C);
        Marshal.WriteInt32(menu,8,vector.ToInt32());Marshal.WriteInt32(menu,12,1);Marshal.WriteInt32(menu,16,4);
        Marshal.WriteInt32(vector,property.ToInt32());Marshal.WriteInt32(property,0x46703130);
        Marshal.WriteInt32(property,4,IntPtr.Add(types,0x14).ToInt32());Marshal.WriteInt32(property,8,0x69642020);
        WritePanelCode(0x00F61160,new byte[]{0xC3}); // external headless invalidation only
        var register=PanelFunction<PanelTraining>(0x1200D400,Join(new byte[]{0x6A,0,0x6A,13,0x68},
            BitConverter.GetBytes(label.ToInt32()),new byte[]{0x68},BitConverter.GetBytes(table.ToInt32()),
            new byte[]{0x68},BitConverter.GetBytes(profile.ToInt32()),new byte[]{0xB8},
            BitConverter.GetBytes(pos.RegisterEntry),new byte[]{0xFF,0xD0,0xC3}));
        begin(profile);register(profile);Require(Marshal.ReadInt32(positionState,16)==1,"Live production registry entry for commit integration.");
        Marshal.WriteInt32(menuPointer,popup.ToInt32());Marshal.WriteInt32(popup,0x160,0x46703031);refresh(profile);
        Require(Marshal.ReadInt32(positionState,12)==1,"Initial GK role before native first commit.");
        var commit=PanelFunction<PanelTraining>(0x1200D500,Join(new byte[]{0x6A,1,0x68},
            BitConverter.GetBytes(menu.ToInt32()),new byte[]{0xB9},BitConverter.GetBytes(popup.ToInt32()),
            new byte[]{0xB8,0x80,0x49,0xFB,0,0xFF,0xD0,0xC3}));
        commit(profile);
        Require(Marshal.ReadInt32(popup,0x160)==0x46703130 && Marshal.ReadInt32(positionState,12)==1,
            "Original FB4980 first choice commits Fp10 but reproduces stale background GK without the new hook.");
        byte[] original=new byte[GamePositionBackgroundPatch.PopupCommitOriginal.Length];
        Marshal.Copy(new IntPtr(GamePositionBackgroundPatch.PopupCommitAddress),original,0,original.Length);
        Require(original.SequenceEqual(GamePositionBackgroundPatch.PopupCommitOriginal.ToArray()),"Actual popup commit original signature.");
        WritePanelCode(unchecked((int)GamePositionBackgroundPatch.PopupCommitAddress),Join(new byte[]{0xE9},
            BitConverter.GetBytes(unchecked(pos.PopupCommitEntry-(GamePositionBackgroundPatch.PopupCommitAddress+5))),
            new byte[]{0x90,0x90,0x90}));
        Marshal.WriteInt32(popup,0x160,0x46703031); // fixture reset only; next selection uses actual native commit.
        commit(profile);
        Require(Marshal.ReadInt32(popup,0x160)==0x46703130 && Marshal.ReadInt32(positionState,12)==10,
            "First actual FB4980 commit -> production ProfileRoleEntry applies Fp10/Role10 without refresh or a second selection.");
        Console.WriteLine("PASS: integrated first native FB4980 commit -> production role helper; original stale GK reproduced; all11 roles/OFF/unknown/missing; private main never resumed.");
    }
}
