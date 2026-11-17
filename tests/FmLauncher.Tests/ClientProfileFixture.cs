using System;
using Marshal = PanelRemoteMemory;

internal static partial class NativePanelFixture
{
    private sealed record ClientFixture(IntPtr First, IntPtr Second, IntPtr TeamReferenceList,
        IntPtr TeamPackedRef, IntPtr PersonIndex, IntPtr PersonType, IntPtr Subtype,
        IntPtr Context, IntPtr TeamContext, IntPtr PcteType, IntPtr LookupCount,
        IntPtr Screen, IntPtr ViewerRef, IntPtr SelectedRef, IntPtr ScreenBag);

    private static ClientFixture CreateClientProxies(IntPtr scratch, IntPtr first, IntPtr second,
        IntPtr club, IntPtr otherClub, IntPtr human, IntPtr otherHuman, IntPtr connection)
    {
        IntPtr root = IntPtr.Add(scratch, 0x24000);
        IntPtr types = IntPtr.Add(root, 0x3000), count = IntPtr.Add(root, 0x3200);
        IntPtr firstClient = root, secondClient = IntPtr.Add(root, 0x400);
        IntPtr teamReference = IntPtr.Add(root, 0x800);
        IntPtr table = IntPtr.Add(root, 0x3300), tableVt = IntPtr.Add(root, 0x3400);
        IntPtr records = IntPtr.Add(root, 0x3500);
        PanelTraining initialize = PanelFunction<PanelTraining>(0x1202E000, new byte[]
        {
            0x8B,0x4C,0x24,0x04,0xB8,0x80,0xE0,0xF5,0,0xFF,0xD0,0xC3
        });
        initialize(types);
        Marshal.WriteInt32(new IntPtr(0x01B24238), types.ToInt32());
        Marshal.WriteInt32(new IntPtr(0x01B2424C), 0);
        Marshal.WriteInt32(new IntPtr(0x01B24250), types.ToInt32());

        void Bag(IntPtr list, IntPtr array, int countValue)
        {
            // Actual R2 crash snapshot uses native PROPERTY_LIST and native F4C110.
            Marshal.WriteInt32(list, 0x0166A12C);
            Marshal.WriteInt32(list, 4, array.ToInt32());
            Marshal.WriteInt32(list, 8, countValue);
            Marshal.WriteInt32(list, 12, countValue);
        }
        void Property(IntPtr array, IntPtr props, int index, int tag, int value, int typeOffset)
        {
            IntPtr p = IntPtr.Add(props, index * 16);
            Marshal.WriteInt32(array, index * 4, p.ToInt32());
            Marshal.WriteInt32(p, value);
            Marshal.WriteInt32(p, 4, IntPtr.Add(types, typeOffset).ToInt32());
            Marshal.WriteInt32(p, 8, tag);
        }
        void Client(IntPtr target, int index)
        {
            IntPtr array = IntPtr.Add(target, 0x100), props = IntPtr.Add(target, 0x180);
            Marshal.WriteInt32(target, 0x012776CC);
            Bag(IntPtr.Add(target, 0x10), array, 5);
            // No Pclb; these are the actual PLAYER proxy fields observed live.
            Property(array, props, 0, 0x78787878, 0, 0x10); // optional dcnt
            Property(array, props, 1, 0x64736861, index, 0x10); // dsha
            Property(array, props, 2, 0x64747479, 1, 0x10); // dtty=1
            Property(array, props, 3, 0x50637465, teamReference.ToInt32(), 0x30); // Pcte OBJECT/propertylist
            Property(array, props, 4, 0x64737562, 0x50706C79, 0x14); // dsub=Pply SYMBOL
        }
        Client(firstClient, 0);
        Client(secondClient, 1);
        IntPtr teamArray = IntPtr.Add(root, 0x900), teamProps = IntPtr.Add(root, 0xA00);
        Bag(teamReference, teamArray, 2);
        Property(teamArray, teamProps, 0, 0x78787878, 0, 0x10);
        Property(teamArray, teamProps, 1, 0x64726566, 0x18000000, 0x10); // packed native TEAM dref

        Marshal.WriteInt32(club, 0x015996C4);
        Marshal.WriteInt32(club, 0x14, 9999);
        Marshal.WriteInt32(club, 0x18, 7);
        Marshal.WriteInt32(otherClub, 0x015996C4);
        Marshal.WriteInt32(otherClub, 0x14, 9998);
        Marshal.WriteInt32(otherClub, 0x18, 9);
        Marshal.WriteInt32(first, 0xEC + 0x14, 8074);
        Marshal.WriteInt32(first, 0xEC + 0x18, 0);
        Marshal.WriteInt32(second, 0xEC + 0x14, 8075);
        Marshal.WriteInt32(second, 0xEC + 0x18, 1);

        // Actual dtty1 dispatch C21650 -> PERSON subobject; selected lookup counter
        // is separate from the permitted public TEAM lookup.
        Marshal.WriteInt32(new IntPtr(0x01B1ED08), table.ToInt32());
        Marshal.WriteInt32(table, 0x10, tableVt.ToInt32());
        Marshal.WriteInt32(table, 0x14, records.ToInt32());
        Marshal.WriteInt32(table, 0x18, 4);
        Marshal.WriteInt32(records, IntPtr.Add(first, 0xEC).ToInt32());
        Marshal.WriteInt32(records, 4, IntPtr.Add(second, 0xEC).ToInt32());
        Marshal.WriteInt32(records, 8, IntPtr.Add(human, 0x29C).ToInt32());
        Marshal.WriteInt32(records, 12, IntPtr.Add(otherHuman, 0x29C).ToInt32());
        Marshal.WriteInt32(human, 0x29C + 0x14, 900001);
        Marshal.WriteInt32(human, 0x29C + 0x18, 2);
        Marshal.WriteInt32(otherHuman, 0x29C + 0x14, 900002);
        Marshal.WriteInt32(otherHuman, 0x29C + 0x18, 3);
        WritePanelCode(0x1202E200, Join(new byte[] { 0x8B,0x44,0x24,0x04,0x83,0xF8,0x02,0x73,0x06,0xFF,0x05 },
            BitConverter.GetBytes(count.ToInt32()), new byte[] { 0x8B,0x51,0x04,0x8B,0x04,0x82,0xC2,0x04,0 }));
        Marshal.WriteInt32(tableVt, 0x2C, 0x1202E200);

        IntPtr team = IntPtr.Add(scratch, 0x4000), otherTeam = IntPtr.Add(scratch, 0x4100);
        Marshal.WriteInt32(team, 0x015A9E0C); Marshal.WriteInt32(team, 0x18, 0);
        Marshal.WriteInt32(otherTeam, 0x015A9E0C); Marshal.WriteInt32(otherTeam, 0x18, 1);
        IntPtr teamTable = IntPtr.Add(root, 0x3600), teamRecords = IntPtr.Add(root, 0x3700);
        Marshal.WriteInt32(new IntPtr(0x01B1ED38), teamTable.ToInt32());
        Marshal.WriteInt32(teamTable, 0x10, 0x015506FC);
        Marshal.WriteInt32(teamTable, 0x14, teamRecords.ToInt32());
        Marshal.WriteInt32(teamTable, 0x18, 2);
        Marshal.WriteInt32(teamRecords, team.ToInt32());
        Marshal.WriteInt32(teamRecords, 4, otherTeam.ToInt32());
        IntPtr screen = IntPtr.Add(root, 0x4000), screenBag = IntPtr.Add(root, 0x4100);
        IntPtr screenArray = IntPtr.Add(root, 0x4200), screenProps = IntPtr.Add(root, 0x4300);
        IntPtr humanRef = IntPtr.Add(root, 0x4400), selectedRef = IntPtr.Add(root, 0x4500);
        IntPtr humanRefArray = IntPtr.Add(root, 0x4600), selectedRefArray = IntPtr.Add(root, 0x4700);
        IntPtr humanRefProps = IntPtr.Add(root, 0x4800), selectedRefProps = IntPtr.Add(root, 0x4900);
        Marshal.WriteInt32(connection, 0x012843A4); Marshal.WriteInt32(connection, 0x44, screen.ToInt32());
        Marshal.WriteInt32(screen, 0x012A002C); Marshal.WriteInt32(screen, 0x3C, screenBag.ToInt32());
        Bag(screenBag, screenArray, 2);
        Property(screenArray, screenProps, 0, 0x4868756D, humanRef.ToInt32(), 0x30);
        Property(screenArray, screenProps, 1, 0x64726566, selectedRef.ToInt32(), 0x30);
        Bag(humanRef, humanRefArray, 1); Bag(selectedRef, selectedRefArray, 1);
        Property(humanRefArray, humanRefProps, 0, 0x64726566, 0x01000002, 0x10);
        Property(selectedRefArray, selectedRefProps, 0, 0x64726566, 0x01000000, 0x10);
        Bag(new IntPtr(0x01B1F0F4), IntPtr.Zero, 0); // actual idle SERVER scratch is empty
        int[] colourHandles = { 0x01910D58, 0x01910DF8, 0x01910DC8, 0x01910DA4, 0x01910DE8 };
        int[] palette = { unchecked((int)0xFF112233), unchecked((int)0xFF224466),
            unchecked((int)0xFF448822), unchecked((int)0xFFAA7711), unchecked((int)0xFF777777) };
        for(int i=0;i<colourHandles.Length;i++)
        {
            IntPtr handle = IntPtr.Add(root,0x5000+i*0x100);
            IntPtr bag = IntPtr.Add(handle,0x20), array = IntPtr.Add(handle,0x40), prop = IntPtr.Add(handle,0x50);
            Marshal.WriteInt32(new IntPtr(colourHandles[i]),handle.ToInt32());
            Marshal.WriteInt32(handle,8,bag.ToInt32());
            Bag(bag,array,1);
            Property(array,prop,0,0x636F6C72,palette[i],0x2C);
        }
        return new ClientFixture(firstClient, secondClient, teamReference,
            IntPtr.Add(teamProps, 16), IntPtr.Add(firstClient, 0x190),
            IntPtr.Add(firstClient, 0x1A0), IntPtr.Add(firstClient, 0x1C0),
            IntPtr.Add(firstClient, 0x180), teamProps,
            IntPtr.Add(firstClient, 0x1B4), count, screen, humanRefProps, selectedRefProps, screenBag);
    }
}
