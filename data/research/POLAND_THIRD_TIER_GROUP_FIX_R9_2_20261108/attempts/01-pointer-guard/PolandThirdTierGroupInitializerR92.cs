// R9.2: scoped GROUP_STAGE initialization at the generic factory call site.
// Native ownership/ABI evidence: R5 E3A560, E3A6E0, E29940, E29270, E62230, E3A720.
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;

public static partial class PolandThirdTierGroupFixR92
{
    const uint GroupHookSite = 0x00D7C9C9;
    const uint GroupContinuation = 0x00D7C9CF;
    const uint GroupVtable = 0x0160F90C;
    const uint GroupConstructor = 0x00E3A560;
    const uint GroupXmlInitializer = 0x00E29270;
    static readonly byte[] GroupOriginal = {0x89,0x7E,0x30,0xFF,0x52,0x78};

    // Entry is a JMP with the original XML/list arguments still on the stack.
    // State48=successful copies,52=stage,56=input count,60=copied count,64=index,68=status.
    // Status: 1=initialized, 2=unexpected nonempty default, 3=invalid input count.
    public static byte[] BuildGroupInitializer(uint address,uint state,uint constructor,uint xmlInitializer,uint continuation)
    {
        var a=new X86(address);
        a.E(0x89,0x7E,0x30,0x9C,0x60); // original owner assignment; save flags/all registers
        a.E(0x85,0xFF); a.Jcc(0x84,"fallback");
        a.E(0x81,0x7F,0x14); a.U(LowerCompetitionUid); a.Jcc(0x85,"fallback");
        a.E(0x3B,0x3D); a.U(state+28); a.Jcc(0x85,"fallback"); // exact object made by our pilot
        a.E(0x81,0x3E); a.U(GroupVtable); a.Jcc(0x85,"fallback");
        a.E(0x89,0x35); a.U(state+52);
        foreach(byte offset in new byte[]{0x08,0x28,0x34,0x38,0x44})
        { a.E(0x83,0x7E,offset,0); a.Jcc(0x85,"nonempty"); }
        a.E(0x66,0x83,0x7E,0x3C,0); a.Jcc(0x85,"nonempty");
        a.E(0x80,0x7E,0x48,0); a.Jcc(0x85,"nonempty");
        // After pushfd/pushad: original XML at+36, list at+40.
        a.E(0x8B,0x44,0x24,0x28,0x0F,0xBF,0x48,0x08,0x89,0x0D); a.U(state+56);
        a.E(0x85,0xC9); a.Jcc(0x8E,"badcount");
        // E3A560(this=ESI, index=0, list, groupBytes=NULL, flag=1), native ret16.
        a.E(0x6A,1,0x6A,0,0x50,0x6A,0,0x8B,0xCE); a.Call(constructor);
        a.E(0x89,0x7E,0x30); // base constructor reset owner; restore it before XML/setup
        a.E(0x55,0x8B,0xCE); a.Call(xmlInitializer); // E29270(this,XML), ret4
        a.E(0x0F,0xBF,0x46,0x3C); a.StoreEax(state+60);
        a.E(0x0F,0xBE,0x46,0x18); a.StoreEax(state+64);
        a.StoreImm(state+68,1); a.E(0xF0,0xFF,0x05); a.U(state+48);
        a.E(0x61,0x9D,0x8D,0x64,0x24,8); a.Jmp(continuation); // discard original two args
        a.Label("nonempty"); a.StoreImm(state+68,2); a.Jmp("fallback");
        a.Label("badcount"); a.StoreImm(state+68,3);
        a.Label("fallback"); a.E(0x61,0x9D,0xFF,0x52,0x78); a.Jmp(continuation);
        return a.Finish();
    }

    static void VerifyGroupImage(byte[] image)
    {
        Require(Equal(Slice(image,GroupHookSite,GroupOriginal.Length),GroupOriginal),"Generic stage initializer call site changed.");
        Require(Equal(Slice(image,GroupConstructor+0x111,3),new byte[]{0xC2,0x10,0}),"Group constructor ABI changed.");
        Require(Equal(Slice(image,GroupXmlInitializer+0x6D,3),new byte[]{0xC2,4,0}),"Stage XML initializer ABI changed.");
        Require(BitConverter.ToUInt32(Slice(image,GroupVtable+0x78,4),0)==0x00431040,"Group virtual initializer changed.");
    }

    static void InstallGroupInitializer(IntPtr process,uint state)
    {
        Require(Equal(Read(process,GroupHookSite,GroupOriginal.Length),GroupOriginal),"Unexpected group initializer in private process.");
        var page=VirtualAllocEx(process,IntPtr.Zero,(UIntPtr)4096,0x3000,4); Check(page!=IntPtr.Zero,"Allocate group initializer");
        uint address=Address(page); var code=BuildGroupInitializer(address,state,GroupConstructor,GroupXmlInitializer,GroupContinuation);
        Require(code.Length<4096,"Group initializer exceeds page."); Write(process,address,code);
        uint previous; Check(VirtualProtectEx(process,page,(UIntPtr)4096,0x20,out previous),"Protect group initializer RX");
        Check(FlushInstructionCache(process,page,(UIntPtr)code.Length),"Flush group initializer");
        WriteExecutable(process,GroupHookSite,ActivationJump(GroupHookSite,address,GroupOriginal.Length));
        Require(Equal(Read(process,GroupHookSite,GroupOriginal.Length),ActivationJump(GroupHookSite,address,GroupOriginal.Length)),"Group hook readback failed.");
    }

    static string GroupTelemetry(IntPtr process,byte[] state)
    {
        uint stage=Get(state,52);
        if(stage==0)return "{\"event\":\"group\",\"status\":\"waiting\"}";
        var b=new StringBuilder("{\"event\":\"group\",\"stage\":\"0x"+stage.ToString("X8")+"\",\"initializer_calls\":"+Get(state,48)+",\"initializer_status\":"+Get(state,68)+",\"input_count\":"+Get(state,56)+",\"copied_count\":"+Get(state,60)+",\"xml_index\":"+Get(state,64));
        try
        {
            var group=Read(process,stage,0x50); uint list=Get(group,0x44); int count=group[0x48];
            b.Append(",\"group_team_count\":"+BitConverter.ToInt16(group,0x3C)+",\"group_count\":"+count+",\"leagues\":[");
            bool four=count==4 && list!=0 && Get(group,0)==GroupVtable && Get(group,0x30)==Get(state,28) && Get(state,68)==1;
            if(count>=0 && count<=16 && list!=0)
            {
                var pointers=Read(process,list,count*4);
                for(int i=0;i<count;i++)
                {
                    if(i>0)b.Append(','); uint league=Get(pointers,i*4);
                    if(league==0){b.Append("null");four=false;continue;}
                    var row=Read(process,league,0x40); int teams=(sbyte)row[0x38];uint table=Get(row,0x34);
                    b.Append("{\"object\":\"0x"+league.ToString("X8")+"\",\"team_count\":"+teams+",\"table\":\"0x"+table.ToString("X8")+"\"}");
                    four &= teams==25 && table!=0;
                }
            }
            b.Append("],\"four_tables_of_25\":"+(four?"true":"false"));
        }
        catch(Win32Exception ex){b.Append(",\"snapshot_unavailable\":"+ex.NativeErrorCode);}
        return b.Append('}').ToString();
    }

    // Execute the exact emitted x86 payload, including fallback call and native-style ret16/ret4.
    public static void VerifyGroupInitializerFixtures()
    {
        var mem=VirtualAlloc(IntPtr.Zero,(UIntPtr)0x10000,0x3000,0x40); Check(mem!=IntPtr.Zero,"Allocate group ABI fixture");
        try
        {
            uint b=Address(mem),hook=b,ctor=b+0x1000,xmlInit=b+0x1400,wrapper=b+0x1800,returned=b+0x1C00;
            uint fallback=b+0x2000,vt=b+0x3000,state=b+0x3200,stage=b+0x3400,owner=b+0x3500;
            uint list=b+0x3800,xml=b+0x3C00,records=b+0x4000,capture=b+0x5000,calls=b+0x5100,teams=b+0x6000;
            Copy(hook,BuildGroupInitializer(hook,state,ctor,xmlInit,returned)); Put(vt+0x78,fallback);
            // Fake constructor captures ABI, independently copies each team into a 16-byte record,
            // deliberately resets owner as the native base constructor does.
            var a=new X86(ctor); a.E(0x53,0x56,0x57,0x8B,0xF1);
            a.E(0xFF,0x05);a.U(calls);a.E(0x89,0x35);a.U(calls+4);
            for(byte k=0;k<4;k++){a.E(0x8B,0x44,0x24,(byte)(16+k*4));a.StoreEax(calls+8+(uint)k*4);}
            a.E(0xC7,0x46,0x30);a.U(0);
            a.E(0x8B,0x5C,0x24,20,0x0F,0xBF,0x4B,8,0x66,0x89,0x4E,0x3C,0xC7,0x46,0x38);a.U(records);
            a.E(0x8B,0x5B,4,0xBF);a.U(records);a.Label("copy");
            a.E(0x8B,0x03,0x89,0x47,8,0x83,0xC3,4,0x83,0xC7,16,0x49);a.Jcc(0x85,"copy");
            a.E(0x8B,0xC6,0x5F,0x5E,0x5B,0xC2,16,0);Copy(ctor,a.Finish());
            a=new X86(xmlInit);a.E(0xFF,0x05);a.U(calls+24);a.E(0x8B,0x44,0x24,4);a.StoreEax(calls+28);
            a.E(0x8B,0x41,0x30);a.StoreEax(calls+32);a.E(0xC6,0x41,0x18,7,0xC7,0x41,0x1C);a.U(0x67726F75);a.E(0xC2,4,0);Copy(xmlInit,a.Finish());
            a=new X86(fallback);a.E(0xFF,0x05);a.U(calls+36);a.E(0x89,0x0D);a.U(calls+40);
            for(byte k=0;k<2;k++){a.E(0x8B,0x44,0x24,(byte)(4+k*4));a.StoreEax(calls+44+(uint)k*4);}
            a.E(0x68);a.U(0x246);a.E(0x9D,0xC2,8,0);Copy(fallback,a.Finish());
            a=new X86(wrapper);a.E(0x55,0x8B,0xEC,0x53,0x56,0x57,0x89,0x25);a.U(capture);
            a.E(0xBE);a.U(stage);a.E(0xBF);a.U(owner);a.E(0xBD);a.U(xml);a.E(0xBB);a.U(0xDDEEFF11);
            a.E(0xBA);a.U(vt);a.E(0xB9);a.U(stage);a.E(0x68);a.U(list);a.E(0x55,0xB8);a.U(0x1234ABCD);
            a.E(0x68);a.U(0x246);a.E(0x9D);a.Jmp(hook);Copy(wrapper,a.Finish());
            a=new X86(returned);a.E(0x89,0x25);a.U(capture+4);a.E(0x89,0x35);a.U(capture+8);a.E(0x89,0x3D);a.U(capture+12);
            a.E(0x89,0x2D);a.U(capture+16);a.E(0x89,0x1D);a.U(capture+20);a.E(0x9C,0x58);a.StoreEax(capture+24);
            a.E(0xB8);a.U(1);a.E(0x5F,0x5E,0x5B,0x5D,0xC2,4,0);Copy(returned,a.Finish());
            var run=(FixtureEntry)Marshal.GetDelegateForFunctionPointer(Pointer(wrapper),typeof(FixtureEntry));
            int checkedCases=0;
            // Scoped success with 100 teams and guard cases for every owned pointer/count.
            for(int scenario=0;scenario<13;scenario++)
            {
                Copy(state,new byte[80]);Copy(stage,new byte[0x50]);Copy(owner,new byte[0x100]);Copy(calls,new byte[64]);Copy(records,new byte[1600]);
                Put(state+28,owner);Put(stage,GroupVtable);Put(owner+0x14,LowerCompetitionUid);Put(list+4,teams);Put(list+8,100);
                for(int i=0;i<100;i++)Put(teams+(uint)i*4,0x10000000+(uint)i*0x100);
                if(scenario==1)Put(owner+0x14,129559);
                if(scenario==2)Put(stage,vt);
                if(scenario==3)Put(state+28,owner+4);
                if(scenario>=4 && scenario<=8)Put(stage+new uint[]{8,0x28,0x34,0x38,0x44}[scenario-4],1);
                if(scenario==9)Put(stage+0x3C,1);
                if(scenario==10)Put(stage+0x48,1);
                if(scenario==11)Put(list+8,0);
                if(scenario==12)Put(list+8,0xFFFF);
                // Hook fallback dereferences EDX (saved native vtable), so the fixture substitutes
                // an independent fake vtable there while the object retains its checked identity.
                Check(FlushInstructionCache(GetCurrentProcess(),mem,(UIntPtr)0x10000),"Flush group fixture");
                Require(run(IntPtr.Zero)==1,"Group fixture did not return.");
                Require(Read32(capture)==Read32(capture+4),"Group hook stack imbalance.");
                Require(Read32(capture+8)==stage && Read32(capture+12)==owner && Read32(capture+16)==xml && Read32(capture+20)==0xDDEEFF11,"Group hook clobbered nonvolatile register.");
                Require((Read32(capture+24)&0x8D5)==0x44,"Group hook changed arithmetic flags.");
                Require(Read32(stage+0x30)==owner,"Group owner lost.");
                if(scenario==0)
                {
                    Require(Read32(calls)==1 && Read32(calls+4)==stage && Read32(calls+8)==0 && Read32(calls+12)==list && Read32(calls+16)==0 && Read32(calls+20)==1,"Native constructor ABI mismatch.");
                    Require(Read32(calls+24)==1 && Read32(calls+28)==xml && Read32(calls+32)==owner,"XML initializer ABI or owner ordering mismatch.");
                    Require(Read32(state+48)==1 && Read32(state+56)==100 && Read32(state+60)==100 && Read32(state+64)==7 && Read32(state+68)==1,"Group diagnostics mismatch.");
                    Copy(teams,new byte[400]); // temporary input lifetime ends
                    for(int i=0;i<100;i++)Require(Read32(records+(uint)i*16+8)==0x10000000+(uint)i*0x100,"Group retained temporary list or lost a team.");
                }
                else
                {
                    Require(Read32(calls)==0 && Read32(calls+24)==0 && Read32(calls+36)==1,"Guard called constructor or lost original dispatch.");
                    Require(Read32(calls+40)==stage && Read32(calls+44)==xml && Read32(calls+48)==list,"Fallback virtual initializer ABI mismatch.");
                    Require(Read32(state+48)==0,"Guard reported successful initialization.");
                }
                checkedCases++;
            }
            Console.WriteLine("VERIFIED: "+checkedCases+" GROUP_STAGE x86 cases; native constructor/XML ABI, 100 independent team records, owner, guards, stack and flags.");
            GC.KeepAlive(run);
        }
        finally{Check(VirtualFree(mem,UIntPtr.Zero,0x8000),"Free group fixture");}
    }
}
