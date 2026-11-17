using System;
using System.IO;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using Marshal = PanelRemoteMemory;

internal static partial class NativePanelFixture
{
    internal static void TestHiddenPanels(string gamePath, string payloadPath, bool hiddenEnabled, bool legacyEnabled)
    {
        using var remote = new PanelRemoteProcess(gamePath);
        Marshal.Process = remote;
        IntPtr code = AllocatePanel(0x10000000, 8192);
        IntPtr data = AllocatePanel(0x11000000, 65536);
        IntPtr scratch = AllocatePanel(0x12000000, 0x40000);
        int propertyEntry, titleEntry, trainingEntry, labelEntry, readEntry, formatEntry;
        int profileSet, profileEvent, profileInit, updateProfile;
        int[] types;
        using (var reader = new BinaryReader(File.OpenRead(payloadPath)))
        {
            int length = reader.ReadInt32(); Marshal.Copy(reader.ReadBytes(length), 0, code, length);
            length = reader.ReadInt32(); Marshal.Copy(reader.ReadBytes(length), 0, data, length);
            propertyEntry = reader.ReadInt32(); titleEntry = reader.ReadInt32();
            trainingEntry = reader.ReadInt32(); labelEntry = reader.ReadInt32();
            readEntry = reader.ReadInt32(); formatEntry = reader.ReadInt32();
            types = new int[reader.ReadInt32()];
            for (int index = 0; index < types.Length; index++) types[index] = reader.ReadInt32();
            profileSet = reader.ReadInt32(); profileEvent = reader.ReadInt32();
            profileInit = reader.ReadInt32(); updateProfile = reader.ReadInt32();
        }
        Require(types.Length == 16, "Four existing properties plus twelve hidden rows.");
        IntPtr player = scratch;
        IntPtr second = IntPtr.Add(scratch, 0x1000);
        IntPtr human = IntPtr.Add(scratch, 0x2000);
        IntPtr otherHuman = IntPtr.Add(scratch, 0x3000);
        IntPtr team = IntPtr.Add(scratch, 0x4000);
        IntPtr otherTeam = IntPtr.Add(scratch, 0x4100);
        IntPtr club = IntPtr.Add(scratch, 0x4200);
        IntPtr otherClub = IntPtr.Add(scratch, 0x4300);
        IntPtr activeHuman = IntPtr.Add(scratch, 0x4400);
        IntPtr selectedConnection = IntPtr.Add(scratch, 0x4500);
        IntPtr connection = IntPtr.Add(scratch, 0x4600);
        IntPtr network = IntPtr.Add(scratch, 0x4700);
        IntPtr block = IntPtr.Add(scratch, 0x4800);
        IntPtr secondBlock = IntPtr.Add(scratch, 0x4900);
        IntPtr personBlock = IntPtr.Add(scratch, 0x4A00);
        IntPtr secondPersonBlock = IntPtr.Add(scratch, 0x4B00);
        IntPtr profile = IntPtr.Add(scratch, 0x5000);
        IntPtr value = IntPtr.Add(scratch, 0x6000);
        IntPtr integers = IntPtr.Add(scratch, 0x7000);
        IntPtr numberStorage = IntPtr.Add(scratch, 0x18000);
        InitializePerson(player, 0x015AB414, 0xEC, 0x015AB12C, IntPtr.Add(scratch, 0x8000));
        InitializePerson(second, 0x015AB414, 0xEC, 0x015AB12C, IntPtr.Add(scratch, 0x8100));
        InitializePerson(human, 0x015AE30C, 0x29C, 0x015AE024, IntPtr.Add(scratch, 0x8200));
        InitializePerson(otherHuman, 0x015AE30C, 0x29C, 0x015AE024, IntPtr.Add(scratch, 0x8300));
        // Separate PLAYER and PERSON attribute blocks; native virtual thunks resolve PERSON.
        Marshal.WriteInt32(player, 0xEC + 0xCC, personBlock.ToInt32());
        Marshal.WriteInt32(second, 0xEC + 0xCC, secondPersonBlock.ToInt32());
        Marshal.WriteInt32(player, 0xCC, block.ToInt32());
        Marshal.WriteInt32(second, 0xCC, secondBlock.ToInt32());
        Marshal.WriteInt32(team, 0x38, club.ToInt32());
        Marshal.WriteInt32(otherTeam, 0x38, otherClub.ToInt32());
        Marshal.WriteInt32(player, 0xEC + 0x70, team.ToInt32());
        Marshal.WriteInt32(second, 0xEC + 0x70, team.ToInt32());
        Marshal.WriteInt32(human, 0x29C + 0x70, team.ToInt32());
        Marshal.WriteInt32(otherHuman, 0x29C + 0x70, otherTeam.ToInt32());
        Marshal.WriteInt32(activeHuman, human.ToInt32());
        Marshal.WriteInt32(selectedConnection, connection.ToInt32());
        Marshal.WriteInt32(connection, 0x64, network.ToInt32());
        Marshal.WriteInt32(network, 0x01672F38);
        Marshal.WriteInt32(new IntPtr(0x01BC1CB8), connection.ToInt32());
        Marshal.WriteByte(new IntPtr(0x0191136A), 0);
        Marshal.WriteInt16(player, 0x14, 123);
        Marshal.WriteInt16(player, 0x16, 187);
        Marshal.WriteInt16(player, 0x0C, 375);
        byte[] originalHumanGetter = new byte[64];
        Marshal.Copy(new IntPtr(0x00C927B0), originalHumanGetter, 0, originalHumanGetter.Length);
        WritePanelCode(0x00C927B0, Join(new byte[] { 0xA1 }, BitConverter.GetBytes(activeHuman.ToInt32()), new byte[] { 0xC3 }));
        WritePanelCode(0x00F9A010, Join(new byte[] { 0xA1 }, BitConverter.GetBytes(selectedConnection.ToInt32()), new byte[] { 0xC3 }));
        for (int number = 0; number <= 200; number++)
        {
            IntPtr text = IntPtr.Add(numberStorage, number * 64);
            ImmutableString(text, number.ToString());
            Marshal.WriteInt32(integers, number * 4, text.ToInt32());
        }
        WritePanelCode(0x00F5D4F0, Join(new byte[] { 0x8B, 0x44, 0x24, 0x04, 0x8B, 0, 0x8B, 0x04, 0x85 },
            BitConverter.GetBytes(integers.ToInt32()), new byte[] { 0xC2, 0x08, 0 }));
        PanelRead read = PanelFunction<PanelRead>(0x1200D000, Join(
            new byte[] { 0x8B, 0x4C, 0x24, 0x04, 0x8B, 0x54, 0x24, 0x08, 0xB8 },
            BitConverter.GetBytes(readEntry), new byte[] { 0xFF, 0xD0, 0xC3 }));
        PanelRead nativePerson = PanelFunction<PanelRead>(0x1200D100, new byte[]
        {
            0x8B, 0x4C, 0x24, 0x04, 0x8B, 0x54, 0x24, 0x08, 0x8B, 0x01,
            0xFF, 0x14, 0x10, 0x0F, 0xBE, 0xC0, 0xC3
        });
        PanelRead nativeScaled = PanelFunction<PanelRead>(0x1200D200, new byte[]
        {
            0x8B, 0x4C, 0x24, 0x04, 0x8B, 0x44, 0x24, 0x08, 0x6A, 0, 0x6A, 1,
            0x50, 0x8B, 0x01, 0xFF, 0x50, 0x18, 0x0F, 0xBE, 0xC0, 0xC3
        });
        int[] slots = { 0x218, 0x21C, 0x224, 0x228, 0x22C, 0x230, 0x234, 0x238 };
        int[] selectors = { 0x46, 0x49, 0x4A, 0x43 };
        int cases = 0;
        for (int index = 0; index < slots.Length; index++)
        {
            for (int number = 1; number <= 20; number++)
            {
                Marshal.WriteByte(personBlock, 0x1C + index, (byte)number);
                int expected = nativePerson(IntPtr.Add(player, 0xEC), slots[index]);
                Require(expected == number, "Independent native PERSON getter.");
                int actualValue = read(player, index < 7 ? index + 4 : 15);
                Require(actualValue == (hiddenEnabled ? expected : int.MinValue), "Production PERSON getter kind " + (index + 4) + " actual=" + actualValue + " expected=" + expected);
                cases++;
            }
            foreach (byte invalid in new byte[] { 0, 21, 127, 128, 255 })
            {
                Marshal.WriteByte(personBlock, 0x1C + index, invalid);
                Require(read(player, index < 7 ? index + 4 : 15) == int.MinValue, "Invalid PERSON value must be unavailable.");
                cases++;
            }
            Marshal.WriteByte(personBlock, 0x1C + index, (byte)(index + 3));
        }
        for (int index = 0; index < selectors.Length; index++)
        {
            foreach (int raw in new int[] { 1, 2, 3, 5, 24, 49, 50, 74, 95, 99, 100 })
            {
                Marshal.WriteByte(block, 0x1C + selectors[index], (byte)raw);
                int expected = nativeScaled(player, selectors[index]);
                Require(expected >= 1 && expected <= 20, "Independent native PLAYER scale.");
                Require(read(player, index + 11) == (hiddenEnabled ? expected : int.MinValue), "Production PLAYER scaling kind " + (index + 11));
                cases++;
            }
            foreach (byte invalid in new byte[] { 0, 101, 127, 128, 255 })
            {
                Marshal.WriteByte(block, 0x1C + selectors[index], invalid);
                Require(read(player, index + 11) == int.MinValue, "Validate raw before native clamp.");
                cases++;
            }
            Marshal.WriteByte(block, 0x1C + selectors[index], 50);
        }
        Require(read(player, 15) == (hiddenEnabled ? 10 : int.MinValue), "Controlled Controversy getter slot238.");
        Require(read(player, 1) == (legacyEnabled ? 123 : int.MinValue), "Legacy CA switch independence.");
        foreach (byte server in new byte[] { 1, 2, 255 })
        {
            Marshal.WriteByte(new IntPtr(0x0191136A), server);
            for (int kind = 4; kind < 16; kind++) Require(read(player, kind) == int.MinValue, "Hosting/unknown server state denied.");
            Require(read(player, 1) == (legacyEnabled ? 123 : int.MinValue), "New network gate must not alter existing CA.");
        }
        Marshal.WriteByte(new IntPtr(0x0191136A), 0);
        foreach (int vtable in new int[] { 0x0168E364, 0x0168C0F0, unchecked((int)0xDEADBEEF), 0 })
        {
            Marshal.WriteInt32(network, vtable);
            for (int kind = 4; kind < 16; kind++) Require(read(player, kind) == int.MinValue, "Remote/closed/unknown connection denied.");
        }
        Marshal.WriteInt32(network, 0x01672F38);
        Marshal.WriteInt32(connection, 0x64, 0);
        Require(read(player, 4) == int.MinValue, "Null network denied.");
        Marshal.WriteInt32(connection, 0x64, network.ToInt32());
        Marshal.WriteInt32(selectedConnection, 0);
        Require(read(player, 4) == int.MinValue, "No selected connection denied.");
        Marshal.WriteInt32(selectedConnection, connection.ToInt32());
        Marshal.WriteInt32(activeHuman, otherHuman.ToInt32());
        for (int kind = 4; kind < 16; kind++) Require(read(player, kind) == int.MinValue, "Foreign active manager denied.");
        Marshal.WriteInt32(activeHuman, human.ToInt32());
        Require(read(player, 4) == (hiddenEnabled ? 3 : int.MinValue), "Local state rechecked after manager/connection change.");
        Require(read(IntPtr.Zero, 4) == int.MinValue, "Null player.");
        Marshal.WriteInt32(second, 0x015EA0D4); // Verified ACTUAL_PLAYER_AND_NON_PLAYER core vtable.
        Require(read(second, 4) == int.MinValue, "Known hybrid PLAYER/STAFF core remains explicitly unsupported.");
        Marshal.WriteInt32(second, 0x015AB414);
        Console.WriteLine("PASS HIDDEN native getters/scales/ranges/network/scope; cases=" + cases + " enabled=" + hiddenEnabled + " legacy=" + legacyEnabled);

        var clients = CreateClientProxies(scratch, player, second, club, otherClub, human, otherHuman, connection);
        WritePanelCode(0x00C927B0, originalHumanGetter);
        PanelRead actualServerHuman = PanelFunction<PanelRead>(0x1200D180,
            new byte[] { 0xB8,0xB0,0x27,0xC9,0,0xFF,0xD0,0xC3 });
        Require(actualServerHuman(IntPtr.Zero, 0) == 0,
            "Actual unmodified C927B0 returns0 for the actual empty SERVER scratch context.");
        for (int index = 0; index < 12; index++)
        {
            int expected = index < 7 ? index + 3 : 10;
            Require(read(clients.First, index + 4) == (hiddenEnabled ? expected : int.MinValue),
                "Native CLIENT proxy conversion field " + index);
        }
        int lookupBefore = Marshal.ReadInt32(clients.LookupCount);
        void Denied(string name)
        {
            int before = Marshal.ReadInt32(clients.LookupCount);
            Require(read(clients.First, 4) == int.MinValue, "Client denied " + name);
            Require(Marshal.ReadInt32(clients.LookupCount) == before, "No selected lookup before denied gate " + name);
        }
        Marshal.WriteInt32(clients.Screen, 0); Denied("unsupported current SCREEN");
        Marshal.WriteInt32(clients.Screen, 0x012A002C);
        Marshal.WriteInt32(connection, 0x44, 0); Denied("no current SCREEN");
        Marshal.WriteInt32(connection, 0x44, clients.Screen.ToInt32());
        Marshal.WriteInt32(connection, 0); Denied("unsupported GAME_SCREEN_CLIENT");
        Marshal.WriteInt32(connection, 0x012843A4);
        Marshal.WriteInt32(clients.Screen, 0x3C, 0); Denied("missing SCREEN property context");
        Marshal.WriteInt32(clients.Screen, 0x3C, clients.ScreenBag.ToInt32());
        foreach(int bad in new[]{unchecked((int)0xFF7FFFFF),0x18000002,0x017FFFFF})
        { Marshal.WriteInt32(clients.ViewerRef,bad); Denied("invalid typed current viewer reference"); }
        Marshal.WriteInt32(clients.ViewerRef, 0x01000002);
        Marshal.WriteInt32(clients.SelectedRef, 0x01000001); Denied("stale CLIENT differs from selected SCREEN reference");
        Marshal.WriteInt32(clients.SelectedRef, 0x01000000);
        IntPtr screenArray = new IntPtr(Marshal.ReadInt32(clients.ScreenBag,4));
        IntPtr viewerProperty = new IntPtr(Marshal.ReadInt32(screenArray));
        int viewerType = Marshal.ReadInt32(viewerProperty,4);
        Marshal.WriteInt32(viewerProperty,4,Marshal.ReadInt32(clients.PersonIndex,4));
        Denied("SCREEN viewer must be native OBJECT/reference, never guessed INTEGER");
        Marshal.WriteInt32(viewerProperty,4,viewerType);
        Marshal.WriteInt32(activeHuman, otherHuman.ToInt32()); Marshal.WriteInt32(clients.ViewerRef, 0x01000003); Denied("foreign human club");
        Marshal.WriteInt32(activeHuman, human.ToInt32()); Marshal.WriteInt32(clients.ViewerRef, 0x01000002);
        foreach (int bad in new[] { -1, 0x18000001, 0x187FFFFF, 0x007FFFFF })
        { Marshal.WriteInt32(clients.TeamPackedRef, bad); Denied("invalid/foreign public TEAM reference"); }
        Marshal.WriteInt32(clients.TeamPackedRef, 0x18000000);
        Marshal.WriteInt32(clients.PersonType, 0); Denied("wrong native PERSON reference table");
        Marshal.WriteInt32(clients.PersonType, 1);
        Marshal.WriteInt32(clients.Subtype, 0x50706C68); Denied("non PLAYER subtype");
        Marshal.WriteInt32(clients.Subtype, 0x50706C79);
        int subtypeType = Marshal.ReadInt32(clients.Subtype, 4);
        Marshal.WriteInt32(clients.Subtype, 4, Marshal.ReadInt32(clients.PersonType, 4));
        Denied("PLAYER subtype must be native SYMBOL");
        Marshal.WriteInt32(clients.Subtype, 4, subtypeType);
        int teamReferenceType = Marshal.ReadInt32(clients.TeamPackedRef, 4);
        Marshal.WriteInt32(clients.TeamPackedRef, 4, subtypeType);
        Denied("packed TEAM dref must be native INTEGER");
        Marshal.WriteInt32(clients.TeamPackedRef, 4, teamReferenceType);

        Marshal.WriteByte(team, 0x40, 1); Denied("national TEAM is not a club");
        Marshal.WriteByte(team, 0x40, 0);
        Marshal.WriteInt32(team, 0); Denied("unsupported native TEAM");
        Marshal.WriteInt32(team, 0x015A9E0C);
        Marshal.WriteInt32(clients.Context,8,0x64636E74);
        Denied("nonlocal CLIENT context is not silently treated as current local SCREEN");
        Marshal.WriteInt32(clients.Context,8,0x78787878);
        Marshal.WriteInt32(clients.TeamContext,8,0x64636E74);
        Denied("TEAM context must match current local CLIENT");
        Marshal.WriteInt32(clients.Context,8,0x64636E74);
        Denied("matching but unsupported nonempty contexts are not local proof");
        Marshal.WriteInt32(clients.Context,8,0x78787878);
        Marshal.WriteInt32(clients.TeamContext,8,0x78787878);
        Require(read(clients.First,4)==(hiddenEnabled?3:int.MinValue),
            "Actual omitted contexts use native canonical missing variant.");
        int metadataType=Marshal.ReadInt32(clients.PersonIndex,4);
        Marshal.WriteInt32(clients.PersonIndex,4,0);Denied("missing dsha INTEGER");
        Marshal.WriteInt32(clients.PersonIndex,4,Marshal.ReadInt32(clients.PcteType));Denied("wrong dsha datatype");
        Marshal.WriteInt32(clients.PersonIndex,4,metadataType);
        int pcteType = Marshal.ReadInt32(clients.PcteType);
        Marshal.WriteInt32(clients.PcteType, 0); Denied("unavailable public TEAM"); Marshal.WriteInt32(clients.PcteType, pcteType);
        foreach (byte server in new byte[] { 1, 2, 255 })
        {
            Marshal.WriteByte(new IntPtr(0x0191136A), server); Denied("server");
        }
        Marshal.WriteByte(new IntPtr(0x0191136A), 0);
        foreach (int bad in new[] { 0, 0x0168E364, 0x0168C0F0, unchecked((int)0xDEADBEEF) })
        {
            Marshal.WriteInt32(network, bad); Denied("network");
        }
        Marshal.WriteInt32(network, 0x01672F38);
        Require(read(clients.First, 4) == (hiddenEnabled ? 3 : int.MinValue), "Client state restored without cache.");
        Require(!hiddenEnabled || Marshal.ReadInt32(clients.LookupCount) > lookupBefore, "Lookup used only for allowed CLIENT.");
        Require(Marshal.ReadInt32(data, 24) == (hiddenEnabled ? 100 : 0),
            "Minimal viewer-stage diagnostics expose success without logging attribute values.");
        Console.WriteLine("PASS CLIENT actual empty SERVER scratch/native Human0, active LOCAL SCREEN viewer/reference, selected identity, native CLUB and guards; rejected states perform zero selected-person lookups.");

        IntPtr emptyString = IntPtr.Add(scratch, 0x6800);
        ImmutableString(emptyString, "");
        Marshal.WriteInt32(new IntPtr(0x01B205E4), Marshal.ReadInt32(emptyString, 8));
        WritePanelCode(0x0102FDE0, new byte[] { 0xC3 });
        // Exercise the production synchronous refresh with native RTTI and LABEL formatter.
        // The lookup/repaint/locale services are fixtures, not the per-player data getters.
        Marshal.WriteInt32(profile, 0x0156A984);
        Marshal.WriteInt32(profile, 0x10, 0x0156A974);
        Marshal.WriteInt32(profile,0x100,16); Marshal.WriteInt32(profile,0x104,11); Marshal.WriteInt32(profile,0x108,6);
        int Palette(int value)
        {
            return value<1||value>20?unchecked((int)0xFF777777):
                value>=Marshal.ReadInt32(profile,0x100)?unchecked((int)0xFFAA7711):
                value>=Marshal.ReadInt32(profile,0x104)?unchecked((int)0xFF448822):
                value>=Marshal.ReadInt32(profile,0x108)?unchecked((int)0xFF224466):unchecked((int)0xFF112233);
        }
        Marshal.WriteInt32(profile, 0x88, clients.First.ToInt32());
        var lookup = new List<byte>();
        for (int index = 0; index < 12; index++)
        {
            int[] ids = { 0x46684164, 0x4668416D, 0x46684C6F, 0x46685072, 0x46685066, 0x46685370,
                0x46685465, 0x4668436F, 0x4668496D, 0x4668496E, 0x46684469, 0x46684374 };
            IntPtr widget = IntPtr.Add(scratch, 0x20000 + index * 0x400);
            IntPtr widgetVtable = IntPtr.Add(widget, 0x300);
            Marshal.WriteInt32(widget, 0x01675554); // actual LABEL class, native FONTcolour at+A8
            Marshal.WriteInt32(widget, 0x10, widgetVtable.ToInt32());
            Marshal.WriteInt32(widgetVtable, 8, 0x00FBBDB0);
            ImmutableString(IntPtr.Add(widget, 0x70), "");
            lookup.AddRange(new byte[] { 0x81, 0x7C, 0x24, 0x04 });
            lookup.AddRange(BitConverter.GetBytes(ids[index]));
            lookup.AddRange(new byte[] { 0x75, 0x08, 0xB8 });
            lookup.AddRange(BitConverter.GetBytes(widget.ToInt32()));
            lookup.AddRange(new byte[] { 0xC2, 0x18, 0 });
        }
        lookup.AddRange(new byte[] { 0x33, 0xC0, 0xC2, 0x18, 0 });
        WritePanelCode(0x1200D400, lookup.ToArray());
        Marshal.WriteInt32(new IntPtr(0x0156A984 + 0xC4), 0x1200D400);
        WritePanelCode(0x00F614F0, new byte[] { 0xC2, 0x04, 0 });
        WritePanelCode(0x00FF9400, new byte[]
        {
            0x56, 0x57, 0x8B, 0x74, 0x24, 0x0C, 0x8B, 0x7C, 0x24, 0x10,
            0x0F, 0xB7, 0x06, 0x0F, 0xB7, 0x17, 0x2B, 0xC2, 0x75, 0x0C,
            0x85, 0xD2, 0x74, 0x08, 0x83, 0xC6, 0x02, 0x83, 0xC7, 0x02,
            0xEB, 0xEA, 0x5F, 0x5E, 0xC3
        });
        PanelTraining refresh = PanelFunction<PanelTraining>(0x1200D800, Join(
            new byte[] { 0x8B, 0x4C, 0x24, 0x04, 0xB8 },
            BitConverter.GetBytes(updateProfile), new byte[] { 0xFF, 0xD0, 0xC3 }));
        for (int index = 0; index < 8; index++) Marshal.WriteByte(secondPersonBlock, 0x1C + index, 19);
        foreach (int selector in selectors) Marshal.WriteByte(secondBlock, 0x1C + selector, 95);
        for (int transition = 0; transition < 100; transition++)
        {
            bool missing = transition % 3 == 2;
            bool next = transition % 3 == 1;
            Marshal.WriteInt32(profile, 0x88, missing ? 0 : (next ? clients.Second : clients.First).ToInt32());
            Marshal.WriteInt32(clients.SelectedRef, next ? 0x01000001 : 0x01000000);
            refresh(profile);
            for (int index = 0; index < 12; index++)
            {
                string actual = PanelText(IntPtr.Add(scratch, 0x20000 + index * 0x400 + 0x70));
                string expected = !hiddenEnabled || missing ? "----"
                    : (next ? 19 : index < 7 ? index + 3 : 10).ToString();
                Require(actual == expected, "No stale profile value at transition " + transition + " field " + index + " actual=" + actual);
                int number = expected=="----"?int.MinValue:int.Parse(expected);
                Require(Marshal.ReadInt32(IntPtr.Add(scratch,0x20000+index*0x400),0xA8)==Palette(number),
                    "Actual native named-palette lookup/COLOUR variant/LABEL colr setter field"+index
                    +" actual="+Marshal.ReadInt32(IntPtr.Add(scratch,0x20000+index*0x400),0xA8).ToString("X8")
                    +" expected="+Palette(number).ToString("X8"));
            }
        }
        Marshal.WriteInt32(profile,0x88,clients.First.ToInt32());
        Marshal.WriteInt32(clients.SelectedRef,0x01000000);
        for(int number=1;number<=20;number++)
        {
            Marshal.WriteByte(personBlock,0x1C,(byte)number);refresh(profile);
            Require(Marshal.ReadInt32(IntPtr.Add(scratch,0x20000),0xA8)==Palette(hiddenEnabled?number:int.MinValue),
                "Native attribute palette boundary"+number);
        }
        Marshal.WriteByte(personBlock,0x1C,3);
        Marshal.WriteInt32(profile,0x100,3); Marshal.WriteInt32(profile,0x104,2); Marshal.WriteInt32(profile,0x108,1);
        refresh(profile);
        Require(Marshal.ReadInt32(IntPtr.Add(scratch,0x20000),0xA8)==Palette(hiddenEnabled?3:int.MinValue),
            "Current profile thresholds override defaults.");
        Marshal.WriteInt32(profile,0x100,16); Marshal.WriteInt32(profile,0x104,11); Marshal.WriteInt32(profile,0x108,6);
        IntPtr lowHandle=new IntPtr(Marshal.ReadInt32(new IntPtr(0x01910D58)));
        IntPtr lowBag=new IntPtr(Marshal.ReadInt32(lowHandle,8));
        IntPtr lowArray=new IntPtr(Marshal.ReadInt32(lowBag,4));
        IntPtr lowProperty=new IntPtr(Marshal.ReadInt32(lowArray));
        Marshal.WriteInt32(lowProperty,unchecked((int)0xFFABCDEF));refresh(profile);
        Require(Marshal.ReadInt32(IntPtr.Add(scratch,0x20000),0xA8)==(hiddenEnabled?unchecked((int)0xFFABCDEF):Palette(int.MinValue)),
            "Skin palette is resolved live; no hardcoded RGB or stale colour cache.");
        Marshal.WriteInt32(lowProperty,unchecked((int)0xFF112233));
        Console.WriteLine("PASS native F46CA0/F46300 named palette, F5EB90 COLOUR and actual LABEL FONT colr setter,1..20/current thresholds/live palette/reset.");
        Marshal.WriteInt32(profile, 0x88, clients.First.ToInt32());
        Marshal.WriteInt32(activeHuman, otherHuman.ToInt32()); Marshal.WriteInt32(clients.ViewerRef, 0x01000003); refresh(profile);
        for (int index = 0; index < 12; index++)
            Require(PanelText(IntPtr.Add(scratch, 0x20000 + index * 0x400 + 0x70)) == "----", "Foreign manager clears every field.");
        Marshal.WriteInt32(activeHuman, human.ToInt32()); Marshal.WriteInt32(clients.ViewerRef, 0x01000002);
        Marshal.WriteByte(new IntPtr(0x0191136A), 1); refresh(profile);
        for (int index = 0; index < 12; index++)
            Require(PanelText(IntPtr.Add(scratch, 0x20000 + index * 0x400 + 0x70)) == "----", "Network state clears every field.");
        // Execute the real Pers=null setter path: the original skips its child refresh,
        // so only our wrapper can invalidate the twelve old labels.
        Marshal.WriteByte(new IntPtr(0x0191136A), 0);
        Marshal.WriteInt32(profile, 0x88, clients.First.ToInt32());
        refresh(profile);
        IntPtr variantTypes = IntPtr.Add(scratch, 0x15000);
        PanelTraining initializeVariantTypes = PanelFunction<PanelTraining>(0x1200DA00, new byte[]
        {
            0x8B, 0x4C, 0x24, 0x04, 0xB8, 0x80, 0xE0, 0xF5, 0, 0xFF, 0xD0, 0xC3
        });
        initializeVariantTypes(variantTypes);
        Marshal.WriteInt32(new IntPtr(0x01B24238), variantTypes.ToInt32());
        PanelRead objectVariant = PanelFunction<PanelRead>(0x1200DA40, new byte[]
        {
            0x8B, 0x4C, 0x24, 0x04, 0xFF, 0x74, 0x24, 0x08,
            0xB8, 0x30, 0xE9, 0xF5, 0, 0xFF, 0xD0, 0xC3
        });
        objectVariant(value, 0);
        PanelProperty setProfile = PanelFunction<PanelProperty>(0x1200DA80, Join(new byte[]
        {
            0x8B, 0x4C, 0x24, 0x04, 0xFF, 0x74, 0x24, 0x0C, 0xFF, 0x74, 0x24, 0x0C, 0xB8
        }, BitConverter.GetBytes(profileSet), new byte[] { 0xFF, 0xD0, 0xC3 }));
        Require((setProfile(IntPtr.Add(profile, 0x10), 0x50657273, value) & 255) == 1, "Actual native Pers=null setter ABI/return.");
        Require(Marshal.ReadInt32(profile, 0x88) == 0, "Native setter null stored at main+88.");
        for (int index = 0; index < 12; index++)
            Require(PanelText(IntPtr.Add(scratch, 0x20000 + index * 0x400 + 0x70)) == "----",
                "Pers=null wrapper must clear label" + index);
        Console.WriteLine("PASS HIDDEN actual native Pers=null setter delegation, this+10 ABI and explicit12-field invalidation.");
        // Keep original displaced instructions, with a controlled tail after the entry:
        // this tests wrapper argument/return ABI without constructing the whole UI event system.
        WritePanelCode(0x009B2735, Join(new byte[] { 0xB8 }, BitConverter.GetBytes(0x12345678),
            new byte[] { 0x5B, 0xC2, 0x08, 0 }));
        PanelProperty dispatch = PanelFunction<PanelProperty>(0x1200DB00, Join(new byte[]
        {
            0x8B, 0x4C, 0x24, 0x04, 0xFF, 0x74, 0x24, 0x0C, 0xFF, 0x74, 0x24, 0x0C, 0xB8
        }, BitConverter.GetBytes(profileEvent), new byte[] { 0xFF, 0xD0, 0xC3 }));
        Marshal.WriteInt32(profile, 0x88, unchecked((int)0xDEADBEEF));
        Require(dispatch(profile, 0x7A7A7A7A, IntPtr.Zero) == 0x12345678,
            "Unknown event must delegate without inspecting a possibly invalidated PERSON.");
        Marshal.WriteInt32(profile, 0x88, clients.First.ToInt32());
        Require(dispatch(profile, 0x6D626368, IntPtr.Zero) == 0x12345678, "Known event preserves original result.");
        Require(PanelText(IntPtr.Add(scratch, 0x20070)) == (hiddenEnabled ? "3" : "----"),
            "Known profile event refreshes current data.");
        WritePanelCode(0x009B21F6, Join(new byte[] { 0x8B, 0xE5, 0x5D, 0xB8 },
            BitConverter.GetBytes(0x76543210), new byte[] { 0xC2, 0x04, 0 }));
        PanelRead initialize = PanelFunction<PanelRead>(0x1200DB80, Join(new byte[]
        {
            0x8B, 0x4C, 0x24, 0x04, 0xFF, 0x74, 0x24, 0x08, 0xB8
        }, BitConverter.GetBytes(profileInit), new byte[] { 0xFF, 0xD0, 0xC3 }));
        Require(initialize(profile, 0) == 0x76543210, "Init thiscall ret4 preserves result and stack.");
        Console.WriteLine("PASS HIDDEN event/init displaced-prefix ABI; unknown events never read invalidated PERSON.");

        Console.WriteLine("PASS HIDDEN native profile refresh100 transitions, null/foreign/network clears all12rows; main game thread never resumed.");
    }
}
