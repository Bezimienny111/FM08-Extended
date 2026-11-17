using System.Buffers.Binary;
using System.Text;

namespace FmLauncher;

internal sealed record TeamTalkUiPayload(byte[] Code,byte[] Data,uint TitleEntry,uint HintEntry,
    uint CreateEntry,uint CellEntry,uint LookupEntry);

// Only the extra Frtt column is intercepted. Existing match statistics delegate
// to their original entry. Published text is immutable; every lookup rechecks
// live match/owner/talk/entry and a frame sequence, including during reload.
internal static class GameTeamTalkPatch
{
    internal const uint Column=0x46727474; // Frtt
    internal const uint TitleAddress=0x007282c0,HintAddress=0x00728360,
        CreateAddress=0x00728b00,CellAddress=0x00728400;
    internal static ReadOnlySpan<byte> TitleOriginal=>[0x8b,0x54,0x24,0x04,0x52];
    internal static ReadOnlySpan<byte> HintOriginal=>[0x8b,0x54,0x24,0x04,0x52];
    internal static ReadOnlySpan<byte> CreateOriginal=>[0x6a,0xff,0x68,0x08,0x5f,0x17,0x01];
    internal static ReadOnlySpan<byte> CellOriginal=>[0x55,0x8b,0xec,0x83,0xe4,0xf8];
    internal const int CodeSize=8192,FrameSize=0x500,Rows=0x100,RowSize=16,
        Pool=0x1000,SlotSize=2048,Slots=256,DataSize=Pool+SlotSize*Slots;
    internal const int Sequence=0,Count=4,Selected=8,FrontendList=12,Client=16,
        Screen=20,Controller=24,Match=28,MatchTeam=32,Manager=36,Talk=40,
        Team=44,TeamUid=48,HumanUid=52,Phase=56,Counter=60,Tick=64,
        Person=68,Club=72,EventTimestamp=76,PersonIndex=80,StringType=0x98;

    internal static uint StringAddress(uint data,int slot)=>checked(data+(uint)(Pool+slot*SlotSize));
    internal static byte[] StringBytes(uint address,string value)
    {
        if(value.Length>900)throw new InvalidDataException("Team-talk caption is too long.");
        var bytes=new byte[SlotSize];
        void U(int at,uint n)=>BinaryPrimitives.WriteUInt32LittleEndian(bytes.AsSpan(at,4),n);
        U(0,0x0166a398);U(4,0x0166a38c);U(8,address+12);U(12,0xffff);
        U(16,(uint)value.Length|((uint)(value.Length+1)<<16));U(20,address+24);
        Encoding.Unicode.GetBytes(value+"\0").CopyTo(bytes,24);
        return bytes;
    }

    internal static TeamTalkUiPayload Build(uint address,uint data,bool polish)
    {
        var initial=new byte[DataSize];
        BinaryPrimitives.WriteUInt32LittleEndian(initial.AsSpan(StringType,4),0x0166dc7c);
        string[] fixedText=["—",polish?"Reakcja na rozmowę":"Team-talk reaction",
            polish?"Reakcja na zatwierdzoną rozmowę w bieżącej połowie":"Reaction to the executed team talk for this half",
            polish?"Złożona reakcja":"Complex reaction"];
        for(int i=0;i<fixedText.Length;i++)StringBytes(StringAddress(data,i),fixedText[i]).CopyTo(initial,Pool+i*SlotSize);
        var c=new NativeCode(address);
        void Header(string name,uint original,ReadOnlySpan<byte> entry,int slot)
        {
            c.Mark(name);c.Emit(0x81,0x7c,0x24,0x04);c.Dword(Column);c.Branch(0x85,name+"Original");
            c.Emit(0x8b,0x4c,0x24,0x08,0x68);c.Dword(StringAddress(data,slot));
            c.Call(0x00f4e870);c.Emit(0xb0,0x01,0xc2,0x08,0);
            c.Mark(name+"Original");c.Emit(entry.ToArray());c.Jump(original+(uint)entry.Length);
        }
        Header("title",TitleAddress,TitleOriginal,1);Header("hint",HintAddress,HintOriginal,2);
        c.Mark("create");c.Emit(0x81,0x7c,0x24,0x04);c.Dword(Column);c.Branch(0x85,"createOriginal");
        // The native squad-number path creates the same text-capable numeric label.
        // Only the local by-value argument changes; registry ID remains Frtt.
        c.Emit(0xc7,0x44,0x24,0x04);c.Dword(0x4d5f736e);
        c.Mark("createOriginal");c.Emit(CreateOriginal.ToArray());c.Jump(CreateAddress+(uint)CreateOriginal.Length);
        c.Mark("cell");c.Emit(0x81,0x7c,0x24,0x04);c.Dword(Column);c.Branch(0x85,"cellOriginal");
        c.Emit(0x9c,0x60,0x8b,0xec,0x81,0xec);c.Dword(528);
        c.Emit(0x83,0xe4,0xf0,0x0f,0xae,0x04,0x24);c.Call("cellCore");
        c.Emit(0x0f,0xae,0x0c,0x24,0x8b,0xe5,0x61,0x9d,0xc2,0x20,0);
        c.Mark("cellOriginal");c.Emit(CellOriginal.ToArray());c.Jump(CellAddress+(uint)CellOriginal.Length);
        c.Mark("cellCore");
        // EBP points at pushad: original widget/stat arguments are +44/+48.
        c.Emit(0x8b,0x7d,0x2c,0x85,0xff);c.Branch(0x84,"cellDone");
        c.Emit(0x8b,0x45,0x30,0x85,0xc0);c.Branch(0x84,"cellEmpty");
        c.Emit(0x8b,0x40,0x08);c.Call("lookup");c.Jump("cellText");
        c.Mark("cellEmpty");c.Emit(0xb8);c.Dword(StringAddress(data,0));
        c.Mark("cellText");c.Emit(0x83,0xec,0x08,0x89,0x04,0x24,0xc7,0x44,0x24,0x04);c.Dword(data+StringType);
        foreach(uint property in new uint[]{0x76616c75,0x68696e74})
        {
            c.Emit(0x8b,0xc4,0x50,0x68);c.Dword(property);
            c.Emit(0x8d,0x4f,0x10,0x8b,0x11,0xff,0x52,0x08);
        }
        c.Emit(0x83,0xc4,0x08);c.Mark("cellDone");c.Emit(0xc3);

        c.Mark("lookup"); // EAX=PERSON table index. Returns a borrowed immutable SI_STRING.
        c.Emit(0x53,0x56,0x57,0x55,0x83,0xec,0x14,0x89,0x04,0x24,0xbf);c.Dword(data);
        c.Emit(0x8b,0x1f,0x85,0xdb);c.Branch(0x84,"missing");
        c.Emit(0xf6,0xc3,0x01);c.Branch(0x85,"missing");
        c.Emit(0x83,0x7f,Count,0x01);c.Branch(0x8c,"missing");
        c.Emit(0x83,0x7f,Count,0x40);c.Branch(0x8f,"missing");
        c.Emit(0x80,0x3d);c.Dword(0x0191136a);c.Emit(0);c.Branch(0x85,"missing");
        c.Emit(0xa1);c.Dword(0x01915238);c.Emit(0xa8,0x01);c.Branch(0x85,"missing");
        c.Emit(0xa1);c.Dword(0x01915230);c.Emit(0x3b,0x47,FrontendList);c.Branch(0x85,"missing");
        c.Emit(0xa1);c.Dword(0x01915234);c.Emit(0x85,0xc0);c.Branch(0x84,"missing");
        c.Emit(0x3b,0x47,Selected);c.Branch(0x85,"missing");
        c.Emit(0x8b,0x00,0x3b,0x47,PersonIndex);c.Branch(0x85,"missing");
        c.Emit(0x8b,0x15);c.Dword(0x01b1ed08);c.Emit(0x85,0xd2);c.Branch(0x84,"missing");
        c.Emit(0x81,0x3a);c.Dword(0x01595ed4);c.Branch(0x85,"missing");
        // Resolve current HUMAN afresh through the native read-only PERSON lookup.
        c.Emit(0x50,0xb9);c.Dword(0x01b1ecd0);c.Call(0x00c21650);
        c.Emit(0x85,0xc0);c.Branch(0x84,"missing");
        c.Emit(0x81,0x38);c.Dword(0x015ae024);c.Branch(0x85,"missing");
        c.Emit(0x8b,0x50,0x14,0x3b,0x57,HumanUid);c.Branch(0x85,"missing");
        c.Emit(0x2b,0x40,0xfc,0x8b,0x40,0x70,0x3b,0x47,Team);c.Branch(0x85,"missing");
        c.Emit(0x81,0x38);c.Dword(0x015a9e0c);c.Branch(0x85,"missing");
        c.Emit(0x8b,0x50,0x18,0x3b,0x57,TeamUid);c.Branch(0x85,"missing");
        // Active local client; reject replay/other screens before reading cached model addresses.
        c.Emit(0xa1);c.Dword(0x01bc1cb8);c.Emit(0x85,0xc0);c.Branch(0x84,"missing");
        c.Emit(0x8b,0x10);
        foreach(uint vt in new uint[]{0x01672024,0x01672074,0x016720b0,0x016721a4})
        {c.Emit(0x81,0xfa);c.Dword(vt);c.Branch(0x84,"clientArray");}
        c.Jump("missing");c.Mark("clientArray");
        c.Emit(0x83,0x78,0x08,0x01);c.Branch(0x8c,"missing");
        c.Emit(0x83,0x78,0x08,0x10);c.Branch(0x8f,"missing");
        c.Emit(0xb9);c.Dword(0x01bc1cb0);c.Call(0x00f9a010);
        c.Emit(0x85,0xc0);c.Branch(0x84,"missing");
        c.Emit(0x3b,0x47,Client);c.Branch(0x85,"missing");
        c.Emit(0x81,0x38);c.Dword(0x012843a4);c.Branch(0x85,"missing");
        c.Emit(0x8b,0x50,0x64,0x85,0xd2);c.Branch(0x84,"missing");
        c.Emit(0x81,0x3a);c.Dword(0x01672f38);c.Branch(0x85,"missing");
        c.Emit(0x8b,0x40,0x44,0x3b,0x47,Screen);c.Branch(0x85,"missing");
        c.Emit(0x85,0xc0);c.Branch(0x84,"missing");
        c.Emit(0x81,0x38);c.Dword(0x0151860c);c.Branch(0x85,"missing");
        c.Emit(0x83,0xb8);c.Dword(0x2a4);c.Emit(0);c.Branch(0x85,"missing");
        c.Emit(0x8b,0x80);c.Dword(0x2a0);c.Emit(0x3b,0x47,Controller);c.Branch(0x85,"missing");
        c.Emit(0x81,0x38);c.Dword(0x01512134);c.Branch(0x85,"missing");
        c.Emit(0x8b,0x70,0x3c,0x3b,0x77,Match);c.Branch(0x85,"missing");
        c.Emit(0x3b,0xb0);c.Dword(0x2648);c.Branch(0x85,"missing");
        c.Emit(0x81,0x3e);c.Dword(0x015869b8);c.Branch(0x85,"missing");
        c.Emit(0x89,0x74,0x24,0x04); // actual MATCH for final fence check
        c.Emit(0x80,0xbe);c.Dword(0x5f22c);c.Emit(1);c.Branch(0x85,"missing");
        c.Emit(0x0f,0xb6,0x86);c.Dword(0x5f30c);c.Emit(0x3b,0x47,Phase);c.Branch(0x85,"missing");
        c.Emit(0x83,0xf8,0x01);c.Branch(0x87,"missing");
        c.Emit(0x8b,0x86);c.Dword(0x5f2fc);c.Emit(0x3b,0x47,Tick);c.Branch(0x8c,"missing");
        c.Emit(0x8b,0x86);c.Dword(0x5fc54);
        c.Emit(0xa9);c.Dword(0x1800000d);c.Branch(0x85,"missing");
        c.Emit(0x8b,0xd0,0x81,0xe2);c.Dword(0x20010);c.Emit(0x81,0xfa);c.Dword(0x20010);c.Branch(0x85,"missing");
        c.Emit(0xc1,0xe8,0x06,0x83,0xe0,0x01,0x33,0x47,Phase,0x83,0xf8,0x01);c.Branch(0x85,"missing");
        c.Emit(0x8b,0x6f,MatchTeam,0x3b,0xae);c.Dword(0x5f2d4);c.Branch(0x84,"participant");
        c.Emit(0x3b,0xae);c.Dword(0x5f2d8);c.Branch(0x85,"missing");
        c.Mark("participant");c.Emit(0x81,0x7d,0);c.Dword(0x01510610);c.Branch(0x85,"missing");
        c.Emit(0x8b,0x85);c.Dword(0x59c);c.Emit(0x3b,0x47,Team);c.Branch(0x85,"missing");
        c.Emit(0x8b,0x85);c.Dword(0x530);c.Emit(0x3b,0x47,Manager);c.Branch(0x85,"missing");
        c.Emit(0x81,0x38);c.Dword(0x01510364);c.Branch(0x85,"missing");
        c.Emit(0x3b,0x70,0x74);c.Branch(0x85,"missing");
        c.Emit(0x3b,0x68,0x78);c.Branch(0x85,"missing");
        c.Emit(0x8b,0xe8,0x89,0x6c,0x24,0x08); // current manager
        c.Emit(0x81,0xbd);c.Dword(0xaf4);c.Dword(0x015102c8);c.Branch(0x85,"missing");
        c.Emit(0x83,0xbd);c.Dword(0xafc);c.Emit(5);c.Branch(0x87,"missing");
        c.Emit(0x8b,0x85);c.Dword(0xb04);c.Emit(0x3b,0x47,Counter);c.Branch(0x85,"missing");
        c.Emit(0x8b,0x57,Phase,0x42,0x3b,0xc2);c.Branch(0x85,"missing");
        c.Emit(0x3b,0x85);c.Dword(0xafc);c.Branch(0x87,"missing");
        c.Emit(0x8b,0x95);c.Dword(0xaf8);c.Emit(0x85,0xd2);c.Branch(0x84,"missing");
        c.Emit(0x8b,0x74,0x82,0xfc,0x3b,0x77,Talk);c.Branch(0x85,"missing");
        c.Emit(0x81,0x3e);c.Dword(0x0150f6e0);c.Branch(0x85,"missing");
        c.Emit(0x0f,0xb6,0x46,0x30,0x3b,0x47,Phase);c.Branch(0x85,"missing");
        c.Emit(0x0f,0xb6,0x46,0x10,0x3b,0x47,Count);c.Branch(0x85,"missing");
        c.Emit(0x8b,0x56,0x08);
        foreach(uint vt in new uint[]{0x0150f338,0x0150f3e4,0x0150f5e4,0x0150f698})
        {c.Emit(0x81,0xfa);c.Dword(vt);c.Branch(0x84,"entryArray");}
        c.Jump("missing");c.Mark("entryArray");
        c.Emit(0x8b,0x76,0x0c,0x85,0xf6);c.Branch(0x84,"missing");
        c.Emit(0x89,0x74,0x24,0x0c); // current entry pointer array
        c.Emit(0x8b,0x04,0x24,0x85,0xc0);c.Branch(0x88,"missing");
        c.Emit(0x50,0xb9);c.Dword(0x01b1ecd0);c.Call(0x00c21650);
        c.Emit(0x85,0xc0);c.Branch(0x84,"missing");
        c.Emit(0x81,0x38);c.Dword(0x015ab12c);c.Branch(0x85,"missing");
        c.Emit(0x8b,0x40,0x14,0x89,0x04,0x24,0x8b,0x4f,Count,0x8d,0x97);c.Dword(Rows);
        c.Mark("cacheNext");c.Emit(0x3b,0x02);c.Branch(0x84,"cacheFound");
        c.Emit(0x83,0xc2,RowSize,0x49);c.Branch(0x85,"cacheNext");c.Jump("missing");
        c.Mark("cacheFound");c.Emit(0x89,0x54,0x24,0x10,0x8b,0x4f,Count,0x33,0xed);
        c.Mark("entryNext");c.Emit(0x8b,0x16,0x85,0xd2);c.Branch(0x84,"missing");
        c.Emit(0x81,0x3a);c.Dword(0x01588780);c.Branch(0x85,"missing");
        c.Emit(0x8b,0x04,0x24,0x3b,0x42,0x08);c.Branch(0x85,"entrySkip");
        c.Emit(0x45,0x83,0xfd,0x01);c.Branch(0x85,"missing");
        c.Emit(0x8b,0x44,0x24,0x10,0x8b,0x50,0x04,0x8b,0x06,0x3b,0x50,0x18);c.Branch(0x85,"missing");
        c.Emit(0x8b,0x54,0x24,0x10,0x8b,0x52,0x08,0x3b,0x50,0x1c);c.Branch(0x85,"missing");
        c.Mark("entrySkip");c.Emit(0x83,0xc6,0x04,0x49);c.Branch(0x85,"entryNext");
        c.Emit(0x83,0xfd,0x01);c.Branch(0x85,"missing");
        c.Emit(0x3b,0x1f);c.Branch(0x85,"missing");
        c.Emit(0x8b,0x74,0x24,0x04,0x80,0xbe);c.Dword(0x5f22c);c.Emit(1);c.Branch(0x85,"missing");
        c.Emit(0x0f,0xb6,0x86);c.Dword(0x5f30c);c.Emit(0x3b,0x47,Phase);c.Branch(0x85,"missing");
        c.Emit(0x8b,0x44,0x24,0x10,0x8b,0x40,0x0c);c.Jump("lookupDone");
        c.Mark("missing");c.Emit(0xb8);c.Dword(StringAddress(data,0));
        c.Mark("lookupDone");c.Emit(0x83,0xc4,0x14,0x5d,0x5f,0x5e,0x5b,0xc3);
        var code=c.Finish();if(code.Length>CodeSize)throw new InvalidDataException("Team-talk hook exceeds budget.");
        return new(code,initial,c.At("title"),c.At("hint"),c.At("create"),c.At("cell"),c.At("lookup"));
    }
}
