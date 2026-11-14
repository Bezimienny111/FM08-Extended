using System;
using System.IO;
using Marshal = PanelRemoteMemory;

internal static partial class NativePanelFixture
{
    internal static void TestClientBridgeNative(string gamePath)
    {
        using var remote = new PanelRemoteProcess(gamePath);
        Marshal.Process = remote;
        IntPtr scratch = AllocatePanel(0x12000000, 0x40000);
        IntPtr client = scratch, types = IntPtr.Add(scratch, 0x1000);
        IntPtr listVt = IntPtr.Add(scratch, 0x1100), array = IntPtr.Add(scratch, 0x1200);
        IntPtr properties = IntPtr.Add(scratch, 0x1400), person = IntPtr.Add(scratch, 0x2000);
        IntPtr table = IntPtr.Add(scratch, 0x3000), tableVt = IntPtr.Add(scratch, 0x3100);
        IntPtr records = IntPtr.Add(scratch, 0x3200);
        PanelTraining initTypes = PanelFunction<PanelTraining>(0x1200D000, new byte[]
        {
            0x8B,0x4C,0x24,0x04,0xB8,0x80,0xE0,0xF5,0,0xFF,0xD0,0xC3
        });
        initTypes(types);
        Marshal.WriteInt32(new IntPtr(0x01B24238), types.ToInt32());
        Marshal.WriteInt32(client, 0x012776CC);
        Marshal.WriteInt32(client, 0x10, listVt.ToInt32());
        Marshal.WriteInt32(client, 0x14, array.ToInt32());
        Marshal.WriteInt32(client, 0x18, 3);
        WritePanelCode(0x1200D100, new byte[]
        {
            0x8B,0x44,0x24,0x04,0x8B,0x51,0x04,0x8D,0x04,0x82,0xC2,0x04,0
        });
        Marshal.WriteInt32(listVt, 0x28, 0x1200D100);
        int[] ids = { 0x64636E74, 0x64736861, 0x64747479 }; // dcnt,dsha,dtty
        for (int i = 0; i < 3; i++)
        {
            IntPtr item = IntPtr.Add(properties, i * 16);
            Marshal.WriteInt32(array, i * 4, item.ToInt32());
            Marshal.WriteInt32(item, 0, 0);
            Marshal.WriteInt32(item, 4, IntPtr.Add(types, 0x10).ToInt32());
            Marshal.WriteInt32(item, 8, ids[i]);
        }
        Marshal.WriteInt32(IntPtr.Add(properties, 32), 1); // actual dtty1 PERSON dispatch
        Marshal.WriteInt32(person, 0x015AB12C);
        Marshal.WriteInt32(person, 0x14, 8074);
        Marshal.WriteInt32(new IntPtr(0x01B1ED08), table.ToInt32());
        Marshal.WriteInt32(table, 0x10, tableVt.ToInt32());
        Marshal.WriteInt32(table, 0x14, records.ToInt32());
        Marshal.WriteInt32(table, 0x18, 1);
        Marshal.WriteInt32(records, person.ToInt32());
        WritePanelCode(0x1200D200, new byte[]
        {
            0x8B,0x44,0x24,0x04,0x8B,0x51,0x04,0x8B,0x04,0x82,0xC2,0x04,0
        });
        Marshal.WriteInt32(tableVt, 0x2C, 0x1200D200);
        PanelRead resolve = PanelFunction<PanelRead>(0x1200D300, new byte[]
        {
            0x8B,0x4C,0x24,0x04,0x8B,0x01,0xFF,0x50,0x18,0xC3
        });
        int result = resolve(client, 0);
        Require(result == person.ToInt32(), "Actual CLIENT resolver18->7709D0->C2F270->C21650 result; got " + result.ToString("X8"));
        Require(Marshal.ReadInt32(new IntPtr(result), 0x14) == 8074, "Native resolved record UID.");
        Marshal.WriteInt32(IntPtr.Add(properties, 16), -1);
        Require(resolve(client, 0) == 0, "Native missing reference sentinel.");
        Marshal.WriteInt32(IntPtr.Add(properties, 16), 0);
        Require(resolve(client, 0) == person.ToInt32(), "Reference changes re-read, no cached record.");
        Console.WriteLine("PASS: actual shipped CLIENT_BASE_PERSON resolver, native property conversion, typed reference, indexed PERSON lookup and sentinel; private suspended main never resumed.");
    }
}
