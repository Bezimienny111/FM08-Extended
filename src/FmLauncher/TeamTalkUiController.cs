using System.Buffers.Binary;
using System.Diagnostics;
using System.Text.Json;

namespace FmLauncher;

internal static class TeamTalkUiFrameBuilder
{
    internal static byte[] Build(TeamTalkObservation observation,TeamTalkProviderEvidence evidence,
        uint data,Func<ulong,uint> caption)
    {
        if(!evidence.SnapshotsEqual || !evidence.ProcessIdentityEqual ||
            evidence.CompletionProof is not ("matching-current-event" or "same-talk-execution-receipt") ||
            evidence.AttestedEventTimestamp!=observation.EventTimestamp || !observation.Relevant ||
            !observation.SimultaneousHumanMatch || !observation.CompletionCandidate ||
            observation.RawPhase is not (0 or 1) || observation.StoredPhase!=observation.RawPhase ||
            observation.Counter!=observation.RawPhase+1 || observation.ExecutionFence!=1 ||
            observation.EventTimestamp is not int stamp || stamp<0 || observation.Tick<=stamp ||
            observation.Players.Count is <1 or >64 || observation.Players.Any(p=>p.Uid is 0 or uint.MaxValue) ||
            observation.Players.Select(p=>p.Uid).Distinct().Count()!=observation.Players.Count)
            throw new InvalidDataException("Team-talk UI frame is not admitted.");
        var snapshot=evidence.Second;
        if(evidence.First.GetRawText()!=snapshot.GetRawText() ||
            snapshot.GetProperty("HumanUid").GetUInt32()!=observation.HumanUid ||
            snapshot.GetProperty("TeamUid").GetUInt32()!=observation.TeamUid ||
            snapshot.GetProperty("Phase").GetInt32()!=observation.RawPhase ||
            snapshot.GetProperty("Counter").GetInt32()!=observation.Counter ||
            snapshot.GetProperty("Tick").GetInt32()!=observation.Tick ||
            !(snapshot.GetProperty("Entries").Deserialize<TeamTalkPlayer[]>()??[]).SequenceEqual(observation.Players))
            throw new InvalidDataException("Team-talk UI context mismatch.");
        var result=new byte[GameTeamTalkPatch.FrameSize];
        void U(int field,uint value)=>BinaryPrimitives.WriteUInt32LittleEndian(result.AsSpan(field,4),value);
        foreach(var (field,name) in new (int,string)[]{
            (GameTeamTalkPatch.Selected,"Selected"),(GameTeamTalkPatch.FrontendList,"FrontendList"),
            (GameTeamTalkPatch.Client,"Client"),(GameTeamTalkPatch.Screen,"Screen"),
            (GameTeamTalkPatch.Controller,"Controller"),(GameTeamTalkPatch.Match,"Match"),
            (GameTeamTalkPatch.MatchTeam,"MatchTeam"),(GameTeamTalkPatch.Manager,"Manager"),
            (GameTeamTalkPatch.Talk,"Talk"),(GameTeamTalkPatch.Team,"Team"),
            (GameTeamTalkPatch.Person,"Person"),(GameTeamTalkPatch.Club,"Club")})
        {
            uint pointer=snapshot.GetProperty(name).GetUInt32();
            if(pointer<0x10000 || (pointer&3)!=0)throw new InvalidDataException("Unbounded native context.");
            U(field,pointer);
        }
        uint personIndex=snapshot.GetProperty("PersonIndex").GetUInt32();
        if(personIndex>=0x7fffff)throw new InvalidDataException("HUMAN index rejected.");
        U(GameTeamTalkPatch.PersonIndex,personIndex);U(GameTeamTalkPatch.TeamUid,observation.TeamUid);
        U(GameTeamTalkPatch.HumanUid,observation.HumanUid);U(GameTeamTalkPatch.Phase,(uint)observation.RawPhase);
        U(GameTeamTalkPatch.Counter,(uint)observation.Counter);U(GameTeamTalkPatch.Tick,(uint)observation.Tick);
        U(GameTeamTalkPatch.EventTimestamp,(uint)stamp);U(GameTeamTalkPatch.Count,(uint)observation.Players.Count);
        U(GameTeamTalkPatch.StringType,0x0166dc7c);
        for(int i=0;i<observation.Players.Count;i++)
        {
            var player=observation.Players[i];uint text=caption(player.RawEffect);
            if(text<data+GameTeamTalkPatch.Pool || text>=data+GameTeamTalkPatch.DataSize ||
                (text-data-GameTeamTalkPatch.Pool)%GameTeamTalkPatch.SlotSize!=0)
                throw new InvalidDataException("Caption is outside immutable string slots.");
            int row=GameTeamTalkPatch.Rows+i*GameTeamTalkPatch.RowSize;
            U(row,player.Uid);U(row+4,(uint)player.RawEffect);U(row+8,(uint)(player.RawEffect>>32));U(row+12,text);
        }
        return result;
    }
}

// Owns only the launcher's allocated UI data block. Does not write players,
// match effects, saves or preferences. Native lookup independently revalidates
// current owner/match/talk and the actual effect before returning any caption.
internal sealed class TeamTalkUiController : IDisposable
{
    private readonly object gate=new();
    private readonly Process process;
    private readonly uint data;
    private readonly bool polish;
    private readonly TeamTalkReadRequest request;
    private readonly TeamTalkReactionSession session;
    private readonly Dictionary<ulong,uint> captions=[];
    private TeamTalkProviderEvidence? evidence;
    private Task? pending;
    private bool disposed;
    private uint sequence=2;
    private string state="waiting";
    private int rows;
    private string? error;
    internal (string State,int Rows,string? Error) Status {get{lock(gate)return(state,rows,error);}}

    internal TeamTalkUiController(Process process,uint data,bool polish)
    {
        this.process=process;this.data=data;this.polish=polish;
        var pin=new TeamTalkProcess(process.Id,process.StartTime.ToUniversalTime().ToFileTimeUtc(),
            "157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d");
        request=new(pin,"","");
        var provider=new BoundedTeamTalkProvider(r=>new VerifiedTeamTalkProcessMemory(r),e=>evidence=e);
        session=new(provider,pin);
    }
    internal void Update()
    {
        lock(gate)
        {
            if(disposed || pending is {IsCompleted:false})return;
            pending=Task.Run(Refresh);
        }
    }
    private async Task Refresh()
    {
        try
        {
            evidence=null;await session.RefreshAsync(request,CancellationToken.None);
            var frame=session.Frame;
            lock(gate)
            {
                if(disposed)return;
                if(frame.Current is null || evidence is null)
                {Clear();state="waiting";rows=0;error=frame.Error;return;}
                uint Caption(ulong mask)
                {
                    if(captions.TryGetValue(mask,out uint known))return known;
                    int slot=4+captions.Count;
                    if(slot>=GameTeamTalkPatch.Slots)return GameTeamTalkPatch.StringAddress(data,3);
                    uint address=GameTeamTalkPatch.StringAddress(data,slot);
                    Write(address,GameTeamTalkPatch.StringBytes(address,TeamTalkReactionText.Format(mask,polish)));
                    captions.Add(mask,address);return address;
                }
                byte[] packet=TeamTalkUiFrameBuilder.Build(frame.Current,evidence,data,Caption);
                if(sequence>=uint.MaxValue-4)sequence=2;
                Write(data,BitConverter.GetBytes(sequence|1));
                Write(data+4,packet.AsSpan(4).ToArray());
                Write(data,BitConverter.GetBytes(sequence));sequence+=2;
                state="current";rows=frame.Current.Players.Count;error=null;
            }
        }
        catch(Exception exception) when(exception is not OutOfMemoryException)
        {
            lock(gate)
            {
                if(disposed)return;
                try{Clear();}catch(Exception clearError) when(clearError is not OutOfMemoryException){/* Process may already have exited. */}
                state="unavailable";rows=0;error=exception.GetType().Name+": "+exception.Message;
            }
        }
    }
    private void Write(uint address,byte[] bytes)
    {
        if(address<data || bytes.Length<1 || (ulong)address+(uint)bytes.Length>(ulong)data+GameTeamTalkPatch.DataSize)
            throw new InvalidDataException("Team-talk UI write outside its own allocation.");
        SuspendedGameProcess.WriteMemory(process.SafeHandle,address,bytes);
    }
    private void Clear()=>Write(data,new byte[4]);
    public void Dispose()
    {
        lock(gate)
        {
            if(disposed)return;
            disposed=true;session.Invalidate("controller-stopped");
            try{Clear();}catch(Exception exception) when(exception is not OutOfMemoryException){/* Exited process. */}
        }
    }
}
