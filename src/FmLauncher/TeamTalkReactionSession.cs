namespace FmLauncher;

internal sealed record TeamTalkReactionFrame(long Revision, string State,
    TeamTalkObservation? Current, string? Error)
{
    internal int RowCount => Current?.Players.Count ?? 0;
}

// Shared refresh policy for the future view. No retained native pointers or
// fallback to an earlier successful observation; publication in FM stays off.
internal sealed class TeamTalkReactionSession(ITeamTalkObservationProvider provider,
    TeamTalkProcess expected)
{
    private readonly object gate=new();
    private long revision;
    private TeamTalkReactionFrame frame=new(0,"empty",null,null);
    internal TeamTalkReactionFrame Frame {get {lock(gate)return frame;}}

    internal void Invalidate(string reason)
    {
        lock(gate)frame=new(++revision,reason,null,null);
    }

    internal async Task RefreshAsync(TeamTalkReadRequest request,CancellationToken token)
    {
        long attempt;
        lock(gate){attempt=++revision;frame=new(attempt,"refreshing",null,null);}
        try
        {
            if(request.Process!=expected)throw new InvalidDataException("Session process pin changed.");
            var observation=await provider.ReadAsync(request,token);
            token.ThrowIfCancellationRequested();
            if(observation.Process!=expected)throw new InvalidDataException("Observation process pin changed.");
            bool current=observation.Relevant && observation.SimultaneousHumanMatch &&
                observation.CompletionCandidate && observation.Players.Count>0 &&
                observation.RawPhase is 0 or 1 && observation.StoredPhase==observation.RawPhase &&
                observation.Counter==observation.RawPhase+1 && observation.ExecutionFence==1 &&
                observation.EventTimestamp is int stamp && stamp>=0 && observation.Tick>stamp;
            lock(gate)
            {
                if(revision!=attempt)return; // An invalidation/new refresh superseded this result.
                frame=new(attempt,current?"current-diagnostic":"no-current-talk",current?observation:null,null);
            }
        }
        catch(Exception error) when(error is not OutOfMemoryException)
        {
            lock(gate)
            {
                if(revision!=attempt)return;
                frame=new(attempt,error is OperationCanceledException?"cancelled":"unavailable",null,
                    error.GetType().Name+": "+error.Message);
            }
        }
    }
}
