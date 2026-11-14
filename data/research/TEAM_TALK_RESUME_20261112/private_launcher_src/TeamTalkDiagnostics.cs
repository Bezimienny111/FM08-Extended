using System.Text.Json;

namespace FmLauncher;

internal sealed record TeamTalkProcess(int Pid, long CreationFiletime, string Sha256);
internal sealed record TeamTalkPlayer(uint Uid, ulong RawEffect, ulong RawAction = 0, ulong RawContext = 0);
internal sealed record TeamTalkObservation(string Source, TeamTalkProcess Process, string Kind,
    int RawPhase, int Tick, int Counter, int StoredPhase, uint TeamUid, uint HumanUid,
    bool Relevant, bool SimultaneousHumanMatch, IReadOnlyList<TeamTalkPlayer> Players,
    bool CompletionCandidate = false, byte? ExecutionFence = null, int? EventTimestamp = null)
{
    // No provider can accidentally promote these diagnostics into the game panel.
    internal bool PublicationReady => false;
}
internal sealed record TeamTalkReadRequest(TeamTalkProcess Process, string MatchFile, string HumanFile);
internal interface ITeamTalkObservationProvider
{
    Task<TeamTalkObservation> ReadAsync(TeamTalkReadRequest request, CancellationToken cancellationToken);
}
internal sealed class OfflineTeamTalkProvider : ITeamTalkObservationProvider
{
    private const long MaximumFileBytes = 256 * 1024;
    private static async Task<JsonDocument> Load(string path, CancellationToken token)
    {
        var info = new FileInfo(path);
        if (!info.Exists || info.Length <= 0 || info.Length > MaximumFileBytes)
            throw new InvalidDataException("Missing or oversized capture.");
        await using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read);
        if (stream.Length <= 0 || stream.Length > MaximumFileBytes) throw new InvalidDataException("Oversized opened capture.");
        return await JsonDocument.ParseAsync(stream, new JsonDocumentOptions { MaxDepth = 32 }, token);
    }
    private static JsonElement Coherent(JsonElement root)
    {
        if (!root.GetProperty("snapshots_equal").GetBoolean())
            throw new InvalidDataException("Capture is not coherent.");
        var first = root.GetProperty("first");
        if (first.GetRawText() != root.GetProperty("second").GetRawText())
            throw new InvalidDataException("The two snapshots differ.");
        return first;
    }
    private static TeamTalkProcess Identity(JsonElement root)
    {
        var p = root.GetProperty("process");
        return new(p.GetProperty("pid").GetInt32(), p.GetProperty("creation_filetime").GetInt64(),
            p.GetProperty("sha256").GetString() ?? "");
    }
    public async Task<TeamTalkObservation> ReadAsync(TeamTalkReadRequest request, CancellationToken token)
    {
        using var matchDoc = await Load(request.MatchFile, token);
        using var humanDoc = await Load(request.HumanFile, token);
        var root = matchDoc.RootElement;
        var humanRoot = humanDoc.RootElement;
        if (Identity(root) != request.Process || Identity(humanRoot) != request.Process)
            throw new InvalidDataException("Process generation or EXE hash changed.");
        var s = Coherent(root);
        var h = Coherent(humanRoot).GetProperty("human");
        if (h.GetProperty("status").GetString() != "VERIFIED_FRONTEND_HUMAN_MEMBER")
            throw new InvalidDataException("Frontend HUMAN is not verified.");
        var slots = s.GetProperty("match_slots");
        uint address = slots.GetProperty("controller_3c").GetUInt32();
        if (address == 0 || slots.GetProperty("controller_2648").GetUInt32() != address)
            throw new InvalidDataException("Ambiguous MATCH.");
        var m = s.GetProperty("matches").GetProperty("controller_3c");
        if (m.GetProperty("address").GetUInt32() != address)
            throw new InvalidDataException("MATCH identity mismatch.");
        var teams = m.GetProperty("teams").EnumerateArray().Where(t =>
            t.GetProperty("core_team").GetProperty("address").GetUInt32() == h.GetProperty("team").GetUInt32()
            && t.GetProperty("core_team").GetProperty("uid").GetUInt32() == h.GetProperty("team_uid").GetUInt32()).ToArray();
        if (teams.Length != 1) throw new InvalidDataException("HUMAN TEAM is not a unique participant.");
        var team = teams[0];
        var manager = team.GetProperty("manager");
        if (manager.GetProperty("match_backlink").GetUInt32() != address ||
            manager.GetProperty("team_backlink").GetUInt32() != team.GetProperty("address").GetUInt32())
            throw new InvalidDataException("Manager backlink mismatch.");
        var talk = manager.GetProperty("last_or_staged_talk");
        var rawEntries = talk.GetProperty("entries");
        if (rawEntries.GetArrayLength() > 64 || rawEntries.GetArrayLength() != talk.GetProperty("entry_count").GetInt32())
            throw new InvalidDataException("Entry count mismatch.");
        var players = rawEntries.EnumerateArray().Select(e =>
            new TeamTalkPlayer(e.GetProperty("uid").GetUInt32(), e.GetProperty("effect").GetUInt64())).ToArray();
        if (players.Any(p => p.Uid == 0 || p.Uid == uint.MaxValue) || players.Select(p => p.Uid).Distinct().Count() != players.Length)
            throw new InvalidDataException("Invalid or duplicate player UID.");
        int phase = m.GetProperty("phase").GetInt32();
        int counter = manager.GetProperty("talk_counter").GetInt32();
        int stored = talk.GetProperty("phase").GetInt32();
        return new("OFFLINE CAPTURE / later HUMAN correlation only", request.Process,
            phase switch { 0 => "prematch", 1 => "halftime", _ => "unsupported" },
            phase, m.GetProperty("tick").GetInt32(), counter, stored, h.GetProperty("team_uid").GetUInt32(),
            h.GetProperty("person_uid").GetUInt32(), TeamTalkWindow.IsCurrent(m.GetProperty("status").GetUInt32(),phase,stored,counter) && players.Length > 0,
            false, players);
    }
}
