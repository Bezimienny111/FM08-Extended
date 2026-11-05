using System.Buffers.Binary;
using System.Text.Json;

namespace FmLauncher;

internal sealed record LeagueCareerProfile(int SchemaVersion, Guid Id, DateTimeOffset Created, LeagueSnapshot Baseline)
{
    public CareerIdentity? Identity { get; init; }
    internal static LeagueCareerProfile Create(LeagueSnapshot snapshot)
    {
        ValidateSnapshot(snapshot);
        if (snapshot.Date.Month == 6 && snapshot.Date.Day == 15)
            throw new LauncherException("LeagueProfileMismatch");
        return new(1, Guid.NewGuid(), DateTimeOffset.Now, snapshot) { Identity = snapshot.Identity };
    }

    internal void Validate()
    {
        if (SchemaVersion != 1 || Id == Guid.Empty || Baseline is null || Baseline.Leagues is null
            || Baseline.Date.Year is < 1900 or > 9998 || Baseline.Date.Month == 6 && Baseline.Date.Day == 15
            || Baseline.Leagues.Any(l => l is null || l.History is null))
            throw new LauncherException("LeagueProfileInvalid");
        ValidateSnapshot(Baseline);
        Identity?.Validate();
        if (Baseline.Identity is not null && Baseline.Identity != Identity)
            throw new LauncherException("LeagueProfileInvalid");
    }

    internal void ValidateFor(LeagueSnapshot snapshot)
    {
        Validate();
        LeagueReputationModel.Validate(snapshot);
        if (Identity is not null && Identity != snapshot.Identity
            || snapshot.Date < Baseline.Date || snapshot.Date.Month == 6 && snapshot.Date.Day == 15
            || !snapshot.Leagues.Select(l => (l.Uid, l.NationUid)).SequenceEqual(
                Baseline.Leagues.Select(l => (l.Uid, l.NationUid))))
            throw new LauncherException("LeagueProfileMismatch");
    }

    private static void ValidateSnapshot(LeagueSnapshot snapshot)
    {
        LeagueReputationModel.Validate(snapshot);
        if (!snapshot.Leagues.Select(row => row.Uid).SequenceEqual(LeagueMemoryReader.TopLeagues))
            throw new LauncherException("LeagueProfileInvalid");
    }

    internal void Save(string path)
    {
        Validate();
        var temporary = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
        try
        {
            using (var stream = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            {
                JsonSerializer.Serialize(stream, this, ConfigurationStore.JsonOptions);
                stream.Flush(true);
            }
            File.Move(temporary, path);
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
        {
            throw new LauncherException("LeagueReportError", path, ex.Message);
        }
        finally { if (File.Exists(temporary)) File.Delete(temporary); }
    }

    internal static LeagueCareerProfile Load(string path)
    {
        try
        {
            var profile = JsonSerializer.Deserialize<LeagueCareerProfile>(File.ReadAllText(path),
                ConfigurationStore.JsonOptions) ?? throw new JsonException("Missing profile.");
            profile.Validate();
            return profile;
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or JsonException)
        {
            throw new LauncherException("LeagueReportError", path, ex.Message);
        }
    }
}

internal sealed record LeagueChange(DateTimeOffset Recorded, Guid Profile, DateOnly Date, uint Uid,
    string League, string Nation, int Previous, int Current, int Target, double Coefficient, uint Generation);

internal sealed class LeagueChanges
{
    private uint state, consumed;
    private Func<uint, int, byte[]>? read;
    private Action<uint, byte[]>? write;
    private LeagueDiagnostics? diagnostics;
    private LeagueCareerProfile? profile;
    internal bool Installed => read is not null;
    internal bool Armed { get; private set; }
    internal LauncherException? Error { get; private set; }
    internal string? LogPath { get; private set; }
    internal List<LeagueChange> Events { get; } = [];

    internal void Begin(uint address, Func<uint, int, byte[]> reader, Action<uint, byte[]> writer,
        LeagueDiagnostics lifecycle, string directory, int processId)
    {
        End();
        Error = null;
        Events.Clear();
        profile = null;
        consumed = 0;
        state = address;
        diagnostics = lifecycle;
        LogPath = Path.Combine(directory, $"league-changes-{Guid.NewGuid():N}.jsonl");
        try
        {
            Directory.CreateDirectory(directory);
            using var stream = new FileStream(LogPath, FileMode.CreateNew, FileAccess.Write, FileShare.Read);
            WriteLine(stream, new { SchemaVersion = 1, ProcessId = processId, Purpose = "actual-league-reputation-changes" });
            stream.Flush(true);
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
        {
            throw new LauncherException("LeagueReportError", LogPath, ex.Message);
        }
        read = reader;
        write = writer;
    }

    internal void End(bool disarm = true)
    {
        if (disarm && write is not null) Disarm();
        read = null;
        write = null;
        Armed = false;
    }

    internal void Disarm()
    {
        write?.Invoke(state, new byte[4]);
        Armed = false;
    }

    internal void Bind(LeagueCareerProfile selected, LeagueSnapshot snapshot)
    {
        if (read is null || write is null || diagnostics is null)
            throw new LauncherException("LeagueChangesRestart");
        Disarm();
        Update();
        if (Error is not null) throw Error;
        selected.ValidateFor(snapshot);
        diagnostics.Update();
        if (diagnostics.Error is not null) throw diagnostics.Error;
        if (diagnostics.ActiveLoads != 0 || diagnostics.Dropped != 0
            || U32(read(state, 32), 28) != 0)
            throw new LauncherException("LeagueDiagnosticsBusy");
        var generation = diagnostics.Generation;
        if (!snapshot.World.EndsWith(":load:" + diagnostics.Stamp, StringComparison.Ordinal))
            throw new LauncherException("LeagueLoadDetected");
        var rows = new byte[LeagueMemoryReader.TopLeagues.Length * GameLeagueChangesPatch.RowSize];
        for (var index = 0; index < snapshot.Leagues.Length; index++)
        {
            var current = snapshot.Leagues[index];
            var baseline = selected.Baseline.Leagues[index];
            if (current.Address == 0 || current.NationAddress == 0 || current.Vtable == 0)
                throw new LauncherException("LeagueInvalidData");
            var row = rows.AsSpan(index * GameLeagueChangesPatch.RowSize);
            Put(row, 0, current.Uid); Put(row, 4, current.NationUid);
            Put(row, 8, current.Address); Put(row, 12, current.NationAddress);
            BinaryPrimitives.WriteDoubleLittleEndian(row[16..], Math.Sqrt(baseline.Coefficient));
            Put(row, 24, (uint)baseline.Reputation); Put(row, 28, current.Vtable);
        }
        write(state + GameLeagueChangesPatch.HeaderSize, rows);
        var header = new byte[12];
        Put(header, 0, generation);
        Put(header, 4, (uint)selected.Baseline.Season);
        Put(header, 8, (uint)snapshot.Season);
        write(state + 4, header);
        var constants = new byte[32];
        foreach (var (offset, number) in new[] { (0, 1.7), (8, 0.5), (16, 100.0), (24, 0.0) })
            BinaryPrimitives.WriteDoubleLittleEndian(constants.AsSpan(offset), number);
        write(state + 32, constants);
        var identityGuard = new byte[16];
        if (selected.Identity is { } identity)
        {
            Put(identityGuard, 0, identity.Token);
            Put(identityGuard, 4, identity.DateWord);
            Put(identityGuard, 8, identity.Marker);
            Put(identityGuard, 12, 1);
        }
        write(state + GameLeagueChangesPatch.IdentityOffset, identityGuard);
        diagnostics.Update();
        if (generation != diagnostics.Generation || diagnostics.ActiveLoads != 0 || diagnostics.Error is not null)
            throw new LauncherException("LeagueLoadDetected");
        profile = selected;
        write(state, BitConverter.GetBytes(1u));
        Armed = true;
    }

    internal void Update()
    {
        if (read is null || diagnostics is null || Error is not null) return;
        try
        {
            var header = read(state, 32);
            if (U32(header, 28) != 0) return;
            Armed = U32(header, 0) == 1 && U32(header, 4) == diagnostics!.Generation
                && diagnostics.ActiveLoads == 0 && diagnostics.Error is null;
            if (!Armed && U32(header, 0) != 0) Disarm();
            var count = U32(header, 16);
            if (count < consumed || count > GameLeagueChangesPatch.Capacity)
                throw new LauncherException("LeagueDiagnosticsInvalid");
            var bytes = count == consumed ? [] : read(
                state + GameLeagueChangesPatch.LogOffset + consumed * GameLeagueChangesPatch.LogEntrySize,
                checked((int)(count - consumed) * GameLeagueChangesPatch.LogEntrySize));
            if (!header.SequenceEqual(read(state, 32))) return;
            var batch = new List<LeagueChange>();
            for (var index = 0; index < count - consumed; index++)
            {
                var span = bytes.AsSpan(index * GameLeagueChangesPatch.LogEntrySize);
                var uid = U32(span, 4);
                var league = profile?.Baseline.Leagues.SingleOrDefault(l => l.Uid == uid)
                    ?? throw new LauncherException("LeagueDiagnosticsInvalid");
                var oldValue = checked((int)U32(span, 8));
                var newValue = checked((int)U32(span, 12));
                var target = checked((int)U32(span, 16));
                var coefficient = BinaryPrimitives.ReadDoubleLittleEndian(span[20..]);
                var year = U32(span, 0);
                if (oldValue is < 1 or > 20 || newValue is < 1 or > 20 || target is < 1 or > 20
                    || Math.Abs(newValue - oldValue) != 1 || year is < 1900 or > 9998
                    || !double.IsFinite(coefficient) || coefficient is < 0 or > 500)
                    throw new LauncherException("LeagueDiagnosticsInvalid");
                batch.Add(new(DateTimeOffset.Now, profile!.Id, new DateOnly((int)year, 6, 15),
                    uid, league.Name, league.Nation, oldValue, newValue, target, coefficient, U32(span, 28)));
            }
            if (batch.Count > 0)
            {
                using var stream = new FileStream(LogPath!, FileMode.Append, FileAccess.Write, FileShare.Read);
                foreach (var entry in batch) WriteLine(stream, entry);
                stream.Flush(true);
                Events.AddRange(batch);
                consumed = count;
            }
            if (U32(header, 20) != 0) throw new LauncherException("LeagueChangesNativeError", U32(header, 20));
            if (diagnostics.Error is not null) throw diagnostics.Error;
        }
        catch (LauncherException ex) { Error = ex; Disarm(); }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
        {
            Error = new LauncherException("LeagueReportError", LogPath!, ex.Message);
            Disarm();
        }
    }

    private static uint U32(ReadOnlySpan<byte> bytes, int offset) =>
        BinaryPrimitives.ReadUInt32LittleEndian(bytes[offset..]);
    private static void Put(Span<byte> bytes, int offset, uint value) =>
        BinaryPrimitives.WriteUInt32LittleEndian(bytes[offset..], value);
    private static void WriteLine<T>(Stream stream, T value)
    {
        JsonSerializer.Serialize(stream, value);
        stream.WriteByte((byte)'\n');
    }
}
