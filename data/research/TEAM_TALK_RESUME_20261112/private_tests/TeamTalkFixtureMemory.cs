using System.Buffers.Binary;
using FmLauncher;

internal sealed class TeamTalkFixtureMemory : ITeamTalkReadMemory
{
    private readonly Dictionary<uint, byte> bytes = [];
    private readonly Dictionary<uint, uint> file = [];
    internal Func<uint, int, byte[]?>? Override;
    internal int Reads;
    internal Func<int, TeamTalkProcess>? IdentityOverride;
    private int identityReads;
    internal int TotalBytes;
    internal readonly TeamTalkProcess Identity;
    internal TeamTalkFixtureMemory(TeamTalkProcess identity)
    {
        Identity=identity;
        U(0x01915234,0x500000);U(0x01915238,0);U(0x01915230,0x510000);
        U(0x510000,0x01294cd4);U(0x510004,0x511000);S(0x510008,1);U(0x511000,0x500000);
        U(0x500000,7);U(0x01b1ed08,0x600000);U(0x600000,0x01595ed4);U(0x600018,0);
        U(0x600004,0x600100);U(0x600100,0x01597e68);U(0x600104,0x600200);U(0x600108,8);U(0x60021c,0x100000);
        U(0x100000,0x015ae024);U(0x100018,7);U(0x100014,12345);U(0x100000-0x29c,0x015ae30c);
        U(0x0ffffc,0);U(0x100070,0x200000);
        U(0x200000,0x015aa00c);B(0x200040,0);U(0x200038,0x300000);U(0x200018,902);
        U(0x300000,0x015996c4);B(0x0191136a,0);
        U(0x01bc1cb0,0x01671fe8);U(0x01bc1c34,123);U(0x01bc1cb8,0x520000);
        U(0x520000,0x01672024);U(0x520004,0x521000);U(0x520008,1);U(0x521000,0x530000);
        U(0x530040,123);U(0x530000,0x012843a4);U(0x530064,0x540000);U(0x540000,0x01672f38);
        U(0x530044,0x550000);U(0x550000,0x0151860c);U(0x5502a0,0x560000);U(0x5502a4,0);
        U(0x560000,0x01512134);U(0x562700,0x550000);U(0x56003c,0x900000);U(0x562648,0x900000);
        U(0x900000,0x015869b8);U(0x95f2d4,0x710000);U(0x95f2d8,0x720000);
        U(0x710000,0x01510610);U(0x720000,0x01510610);U(0x71059c,0x200000);U(0x72059c,0x210000);
        U(0x710530,0xa00000);U(0xa00000,0x01510364);U(0xa00074,0x900000);U(0xa00078,0x710000);
        U(0xa00af4,0x015102c8);U(0xa00af8,0xa10000);U(0xa00afc,5);U(0xa00b04,2);U(0xa10004,0xa20000);
        U(0xa20000,0x0150f6e0);U(0xa20008,0x0150f338);U(0xa2000c,0xb00000);B(0xa20010,1);B(0xa20030,1);
        U(0xb00000,0xb10000);
        for(uint i=0;i<0x2b;i++)B(0xb10000+i,0);
        U(0xb10000,0x01588780);U(0xb10008,7788);U(0xb10010,64);U(0xb10018,0x2011);
        U(0x95f2fc,19887);B(0x95f30c,1);U(0x95fc54,0x220290);
        B(0x95f22c,1);U(0x900c00,0x0150f218);U(0x900c04,0xb30000);S(0x900c08,1);U(0xb30000,0xb40000);
        U(0xb40000,0x0150f700);U(0xb40004,19886);B(0xb40008,7);B(0xb40009,0);
        U(0xb4000c,0x0150f6e0);U(0xb40014,0x0150f338);U(0xb40018,0xb50000);B(0xb4001c,1);B(0xb4003c,1);
        U(0xb50000,0xb20000);
        for(uint i=0;i<0x2b;i++)B(0xb20000+i,0);
        U(0xb20000,0x01588780);U(0xb20008,7788);U(0xb20010,64);
        file[0x0150f218+0x2c]=0x00913d30;

        foreach(uint vt in new uint[]{0x01294cd4})file[vt+0x2c]=0x913d30;
        foreach(uint vt in new uint[]{0x01597e68,0x01672024,0x015102c8})file[vt+0x2c]=0xf9a0d0;
        file[0x0150f338+0x2c]=0x50e1a0;
    }
    internal void B(uint a, byte b)=>bytes[a]=b;
    internal void U(uint a, uint n)
    {
        Span<byte> b=stackalloc byte[4];BinaryPrimitives.WriteUInt32LittleEndian(b,n);
        for(uint i=0;i<4;i++)bytes[a+i]=b[(int)i];
    }
    private void S(uint a,short n)
    {
        Span<byte>b=stackalloc byte[2];BinaryPrimitives.WriteInt16LittleEndian(b,n);
        for(uint i=0;i<2;i++)bytes[a+i]=b[(int)i];
    }
    public TeamTalkProcess ReadIdentity()=>IdentityOverride?.Invoke(++identityReads) ?? Identity;
    public byte[] Read(uint address,int count)
    {
        Reads++;TotalBytes+=count;
        var alternate=Override?.Invoke(address,count);
        if(alternate!=null)return alternate;
        var output=new byte[count];
        for(int i=0;i<count;i++)
            output[i]=bytes.TryGetValue(address+(uint)i,out var value)?value:throw new InvalidDataException($"Unmapped fixture address {address+(uint)i:X}");
        return output;
    }
    public uint VerifiedFileU32(uint address)=>file.TryGetValue(address,out var v)?v:throw new InvalidDataException("Missing verified getter.");
    public void Dispose(){}
}
