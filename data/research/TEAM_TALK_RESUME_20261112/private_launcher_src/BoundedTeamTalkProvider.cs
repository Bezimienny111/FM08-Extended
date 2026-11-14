using System.Buffers.Binary;
using System.Text.Json;

namespace FmLauncher;

// A verified process-memory backend supplies both identity and immutable image data.
// This traversal has no process enumeration, native calls or write capability.
internal interface ITeamTalkReadMemory : IDisposable
{
    TeamTalkProcess ReadIdentity();
    byte[] Read(uint address, int bytes);
    uint VerifiedFileU32(uint address);
}
internal sealed class BoundedTeamTalkProvider(Func<TeamTalkReadRequest, ITeamTalkReadMemory> open) : ITeamTalkObservationProvider
{
    private sealed class Reader(ITeamTalkReadMemory memory)
    {
        internal int Calls { get; private set; }
        internal int Bytes { get; private set; }
        internal byte[] Read(uint a, int n)
        {
            if (a < 0x10000 || n < 1 || n > 4096 || (ulong)a + (uint)n > 0x100000000UL ||
                Calls >= 768 || Bytes + n > 32768)
                throw new InvalidDataException("Bounded RPM budget/range rejected.");
            Calls++; Bytes += n;
            var b = memory.Read(a,n);
            if (b.Length != n) throw new InvalidDataException("Incomplete read.");
            return b;
        }
        internal uint U32(uint a) => BinaryPrimitives.ReadUInt32LittleEndian(Read(a,4));
        internal int I32(uint a) => BinaryPrimitives.ReadInt32LittleEndian(Read(a,4));
        internal byte Byte(uint a) => Read(a,1)[0];
        internal short I16(uint a) => BinaryPrimitives.ReadInt16LittleEndian(Read(a,2));
        internal void Vt(uint a, uint vt)
        {
            if (U32(a)!=vt) throw new InvalidDataException("Native class guard rejected.");
        }
        internal void Getter(uint vt, uint expected)
        {
            if(memory.VerifiedFileU32(vt+0x2c)!=expected)
                throw new InvalidDataException("Native array getter rejected.");
        }
        internal uint[] Pointers(uint data,int count)
        {
            if(count==0)return [];
            var raw=Read(data,checked(count*4));
            return Enumerable.Range(0,count).Select(i=>BinaryPrimitives.ReadUInt32LittleEndian(raw.AsSpan(i*4,4))).ToArray();
        }
    }
    private sealed record NativeSnapshot(uint Selected, uint FrontendList, uint Person, uint Team, uint Club,
        uint Client, uint Screen, uint Controller, uint Match, uint MatchTeam, uint Manager, uint Talk,
        int Tick, int Phase, int StoredPhase, int Counter, uint Status, uint TeamUid, uint HumanUid,
        TeamTalkPlayer[] Entries, byte Fence, int? EventTimestamp);

    private static NativeSnapshot Collect(Reader r)
    {
        uint selected=r.U32(0x01915234), mode=r.U32(0x01915238), listing=r.U32(0x01915230);
        if(selected==0 || listing==0 || (mode&1)!=0)throw new InvalidDataException("No local frontend HUMAN.");
        r.Vt(listing,0x01294cd4);r.Getter(0x01294cd4,0x00913d30);
        int humans=r.I16(listing+8);
        if(humans is <1 or >16)throw new InvalidDataException("HUMAN list bounds.");
        if(r.Pointers(r.U32(listing+4),humans).Count(v=>v==selected)!=1)
            throw new InvalidDataException("Ambiguous HUMAN member.");
        uint index=r.U32(selected), table=r.U32(0x01b1ecd0+0x38);
        if(index>=0x7fffff)throw new InvalidDataException("PERSON index bounds.");
        r.Vt(table,0x01595ed4);
        uint array=index<r.U32(table+0x18)?table+0x10:r.U32(table+4);
        uint avt=r.U32(array);
        if(avt is not (0x012942dc or 0x01597e68))throw new InvalidDataException("PERSON array class.");
        r.Getter(avt,0x00f9a0d0);
        uint count=r.U32(array+8);
        if(index>=count || count>4000000)throw new InvalidDataException("PERSON array bounds.");
        uint person=r.U32(checked(r.U32(array+4)+index*4));
        r.Vt(person,0x015ae024);
        if(r.U32(person+0x18)!=index || r.I32(person+0x14)<=0)
            throw new InvalidDataException("HUMAN PERSON identity.");
        r.Vt(checked(person-0x29c),0x015ae30c);
        long adjusted=(long)person-r.I32(person-4)+0x10c;
        if(adjusted<0x10000 || adjusted>uint.MaxValue)throw new InvalidDataException("HUMAN this adjustment.");
        uint team=r.U32(checked((uint)adjusted-0x9c));
        r.Vt(team,0x015aa00c);
        if(r.Byte(team+0x40)!=0)throw new InvalidDataException("HUMAN is not a club TEAM.");
        uint club=r.U32(team+0x38);r.Vt(club,0x015996c4);
        if(r.Byte(0x0191136a)!=0)throw new InvalidDataException("Host mode not admitted.");
        r.Vt(0x01bc1cb0,0x01671fe8);
        uint current=r.U32(0x01bc1c34), clients=r.U32(0x01bc1cb0+8);
        if(current==0)throw new InvalidDataException("No current screen client.");
        uint cvt=r.U32(clients);
        if(cvt is not (0x01672024 or 0x01672074 or 0x016720b0 or 0x016721a4))
            throw new InvalidDataException("Screen client array class.");
        r.Getter(cvt,0x00f9a0d0);
        uint clientCount=r.U32(clients+8);
        if(clientCount is <1 or >16)throw new InvalidDataException("Screen client count.");
        var candidates=r.Pointers(r.U32(clients+4),(int)clientCount).Where(p=>r.U32(p+0x40)==current).ToArray();
        if(candidates.Length!=1)throw new InvalidDataException("Current client ambiguous.");
        uint client=candidates[0];r.Vt(client,0x012843a4);
        r.Vt(r.U32(client+0x64),0x01672f38);
        uint screen=r.U32(client+0x44);r.Vt(screen,0x0151860c);
        uint controller=r.U32(screen+0x2a0);r.Vt(controller,0x01512134);
        if(r.U32(controller+0x2700)!=screen)throw new InvalidDataException("Controller backlink.");
        uint match=r.U32(controller+0x3c);
        if(match==0 || r.U32(controller+0x2648)!=match || r.U32(screen+0x2a4)!=0)
            throw new InvalidDataException("Live MATCH identity is ambiguous.");
        r.Vt(match,0x015869b8);
        uint[] participants=[r.U32(match+0x5f2d4),r.U32(match+0x5f2d8)];
        foreach(uint participant in participants)r.Vt(participant,0x01510610);
        var own=participants.Where(p=>r.U32(p+0x59c)==team).ToArray();
        if(own.Length!=1)throw new InvalidDataException("Active HUMAN TEAM is not unique MATCH participant.");
        uint matchTeam=own[0],manager=r.U32(matchTeam+0x530);
        r.Vt(manager,0x01510364);
        if(r.U32(manager+0x74)!=match || r.U32(manager+0x78)!=matchTeam)
            throw new InvalidDataException("Manager backlinks.");
        uint history=manager+0xaf4;r.Vt(history,0x015102c8);r.Getter(0x015102c8,0x00f9a0d0);
        int counter=checked((int)r.U32(manager+0xb04));
        uint talkCount=r.U32(history+8);
        if(counter<0 || counter>talkCount || talkCount is <1 or >5)
            throw new InvalidDataException("Talk history bounds.");
        uint talk=r.U32(checked(r.U32(history+4)+(uint)Math.Max(0,counter-1)*4));
        r.Vt(talk,0x0150f6e0);
        uint evt=r.U32(talk+8);
        if(evt is not (0x0150f338 or 0x0150f3e4 or 0x0150f5e4 or 0x0150f698))
            throw new InvalidDataException("Inline entry array class.");
        r.Getter(evt,0x0050e1a0);
        int entryCount=r.Byte(talk+0x10);
        if(entryCount>64)throw new InvalidDataException("Entry count.");
        var entries=new List<TeamTalkPlayer>();
        foreach(uint pointer in r.Pointers(r.U32(talk+0xc),entryCount))
        {
            var raw=r.Read(pointer,0x2b);
            if(BinaryPrimitives.ReadUInt32LittleEndian(raw)!=0x01588780)
                throw new InvalidDataException("Player entry class.");
            entries.Add(new(BinaryPrimitives.ReadUInt32LittleEndian(raw.AsSpan(8)),
                BinaryPrimitives.ReadUInt64LittleEndian(raw.AsSpan(0x18)),
                BinaryPrimitives.ReadUInt64LittleEndian(raw.AsSpan(0x10)),
                BinaryPrimitives.ReadUInt64LittleEndian(raw.AsSpan(0x20))));
        }
        if(entries.Any(e=>e.Uid is 0 or uint.MaxValue) || entries.Select(e=>e.Uid).Distinct().Count()!=entries.Count)
            throw new InvalidDataException("Invalid own player UID.");
        if(r.U32(0x01915234)!=selected || r.U32(0x01915230)!=listing || r.U32(0x01915238)!=mode ||
            r.U32(selected)!=index || r.U32(0x01bc1c34)!=current || r.U32(client+0x44)!=screen)
            throw new InvalidDataException("Frontend root changed.");
        byte fence=r.Byte(match+0x5f22c);
        if(fence>1)throw new InvalidDataException("Unknown native engine fence.");
        uint queue=match+0xc00,qvt=r.U32(queue);
        if(qvt is not (0x0150f218 or 0x0150f420 or 0x0150f5ac or 0x015867a4 or 0x015868a0 or 0x01586914))
            throw new InvalidDataException("Tactical queue class.");
        r.Getter(qvt,0x00913d30);
        int qcount=r.I16(queue+8);
        if(qcount is <0 or >4096)throw new InvalidDataException("Tactical queue count.");
        int? eventTimestamp=null;
        if(qcount<=32)
        {
            var matches=new List<int>();
            foreach(uint ep in r.Pointers(r.U32(queue+4),qcount))
            {
                if(r.Byte(ep+8)!=7 || r.Byte(ep+9)!=(byte)Array.IndexOf(participants,matchTeam))continue;
                r.Vt(ep,0x0150f700);uint payload=ep+0xc;r.Vt(payload,0x0150f6e0);
                if(r.Byte(payload+0x30)!=r.Byte(talk+0x30))continue;
                uint pvt=r.U32(payload+8);
                if(pvt is not (0x0150f338 or 0x0150f3e4 or 0x0150f5e4 or 0x0150f698))
                    throw new InvalidDataException("Event entry array class.");
                r.Getter(pvt,0x0050e1a0);
                int ec=r.Byte(payload+0x10);
                if(ec>64)throw new InvalidDataException("Event entry count.");
                var fingerprint=new List<(uint Uid,ulong Action,ulong Context)>();
                foreach(uint e in r.Pointers(r.U32(payload+0xc),ec))
                {
                    var raw=r.Read(e,0x2b);
                    if(BinaryPrimitives.ReadUInt32LittleEndian(raw)!=0x01588780)
                        throw new InvalidDataException("Event player entry class.");
                    fingerprint.Add((BinaryPrimitives.ReadUInt32LittleEndian(raw.AsSpan(8)),
                        BinaryPrimitives.ReadUInt64LittleEndian(raw.AsSpan(0x10)),
                        BinaryPrimitives.ReadUInt64LittleEndian(raw.AsSpan(0x20))));
                }
                var expected=entries.Select(e=>(e.Uid,e.RawAction,e.RawContext)).OrderBy(e=>e.Uid).ToArray();
                if(fingerprint.Count>0 && fingerprint.Select(e=>e.Uid).Distinct().Count()==fingerprint.Count &&
                    fingerprint.OrderBy(e=>e.Uid).SequenceEqual(expected))
                    matches.Add(checked((int)r.U32(ep+4)));
            }
            if(matches.Count==1)eventTimestamp=matches[0];
        }
        return new(selected,listing,person,team,club,client,screen,controller,match,matchTeam,manager,talk,
            checked((int)r.U32(match+0x5f2fc)),r.Byte(match+0x5f30c),r.Byte(talk+0x30),counter,
            r.U32(match+0x5fc54),r.U32(team+0x18),r.U32(person+0x14),entries.ToArray(),fence,eventTimestamp);
    }
    public Task<TeamTalkObservation> ReadAsync(TeamTalkReadRequest request,CancellationToken token)
    {
        token.ThrowIfCancellationRequested();
        using var memory=open(request);
        if(memory.ReadIdentity()!=request.Process)throw new InvalidDataException("Process identity rejected.");
        var reader=new Reader(memory);
        var first=Collect(reader);
        token.ThrowIfCancellationRequested();
        var second=Collect(reader);
        if(JsonSerializer.Serialize(first)!=JsonSerializer.Serialize(second) || memory.ReadIdentity()!=request.Process)
            throw new InvalidDataException("Torn coherent HUMAN+MATCH snapshot.");
        return Task.FromResult(new TeamTalkObservation("COHERENT BOUNDED READ / diagnostic only",request.Process,
            second.Phase switch {0=>"prematch",1=>"halftime",_=>"unsupported"},second.Phase,second.Tick,
            second.Counter,second.StoredPhase,second.TeamUid,second.HumanUid,
            TeamTalkWindow.IsCurrent(second.Status,second.Phase,second.StoredPhase,second.Counter) && second.Entries.Length>0,
            true,second.Entries,
            TeamTalkWindow.IsCurrent(second.Status,second.Phase,second.StoredPhase,second.Counter) &&
                second.Fence==1 && second.EventTimestamp is int stamp && stamp>=0 && second.Tick>stamp,
            second.Fence,second.EventTimestamp));
    }
}
