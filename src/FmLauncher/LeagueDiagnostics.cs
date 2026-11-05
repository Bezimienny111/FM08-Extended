using System.Buffers.Binary;
using System.Text.Json;

namespace FmLauncher;

internal sealed record LeagueDiagnosticEvent(uint Sequence, LeagueDiagnosticKind Kind, uint ThreadId,
    uint Generation, uint Day, uint Year, uint Context, uint Mode, uint Result, uint ScheduledDay, uint ScheduledYear);

internal sealed class LeagueDiagnostics
{
    private Func<uint, int, byte[]>? read;
    private uint state;
    private uint consumed;
    private Guid id;
    internal bool Installed => read is not null;
    internal uint Generation { get; private set; }
    internal uint ActiveLoads { get; private set; }
    internal uint Dropped { get; private set; }
    internal string Stamp => id != Guid.Empty ? $"{id:N}:{Generation}" : "";
    internal string? LogPath { get; private set; }
    internal LauncherException? Error { get; private set; }
    internal List<LeagueDiagnosticEvent> Events { get; } = [];
    internal bool LoadedCareer => Events.Any(end => end.Generation == Generation
        && end.Kind == LeagueDiagnosticKind.LoadReturn && end.Result == 1
        && Events.Any(begin => begin.Generation == end.Generation && begin.Kind == LeagueDiagnosticKind.LoadBegin
            && begin.Mode == 0 && begin.Context == end.Context && begin.ThreadId == end.ThreadId
            && begin.Sequence < end.Sequence));

    internal LeagueDiagnosticEvent? LastSave(CareerIdentity identity) => Events.LastOrDefault(entry =>
        entry.Generation == Generation && entry.Kind == LeagueDiagnosticKind.SaveCompleted && entry.Result == 1
        && entry.Mode == identity.Token && entry.ScheduledDay == identity.DateWord && entry.ScheduledYear == identity.Marker);

    internal void Reset()
    {
        read = null;
        id = Guid.Empty;
        state = consumed = Generation = ActiveLoads = Dropped = 0;
        LogPath = null;
        Error = null;
        Events.Clear();
    }

    internal void End() => read = null;

    internal void Begin(uint address, Func<uint, int, byte[]> reader, string directory, int processId)
    {
        Reset();
        id = Guid.NewGuid();
        var path = Path.Combine(directory, $"league-diagnostics-{id:N}.jsonl");
        try
        {
            Directory.CreateDirectory(directory);
            using var stream = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.Read);
            WriteLine(stream, new { SchemaVersion = 1, Session = id, ProcessId = processId,
                Started = DateTimeOffset.Now, Purpose = "diagnostics-only-no-reputation-writes" });
            stream.Flush(flushToDisk: true);
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
        {
            throw new LauncherException("LeagueDiagnosticsLogError", path, ex.Message);
        }
        state = address;
        read = reader;
        LogPath = path;
    }

    internal void Update()
    {
        if (read is null || Error is not null) return;
        try
        {
            var before = read(state, GameLeagueDiagnosticsPatch.HeaderSize);
            var count = Word(before, 4);
            if (count > GameLeagueDiagnosticsPatch.Capacity || count < consumed)
                throw new LauncherException("LeagueDiagnosticsInvalid");
            var entries = count == consumed ? [] : read(state + GameLeagueDiagnosticsPatch.HeaderSize
                + consumed * GameLeagueDiagnosticsPatch.EntrySize,
                checked((int)(count - consumed) * GameLeagueDiagnosticsPatch.EntrySize));
            var after = read(state, GameLeagueDiagnosticsPatch.HeaderSize);
            if (!before.SequenceEqual(after) || Word(after, 0) != 0) return;
            Generation = Word(after, 12);
            ActiveLoads = Word(after, 16);
            Dropped = Word(after, 8);
            if (Dropped != 0) throw new LauncherException("LeagueDiagnosticsDropped", Dropped);
            if (ActiveLoads > int.MaxValue) throw new LauncherException("LeagueDiagnosticsInvalid");
            if (count == consumed) return;
            var batch = new List<LeagueDiagnosticEvent>();
            for (var index = 0; index < count - consumed; index++)
            {
                var span = entries.AsSpan(index * GameLeagueDiagnosticsPatch.EntrySize, GameLeagueDiagnosticsPatch.EntrySize);
                var kind = (LeagueDiagnosticKind)Word(span, 0);
                if (!Enum.IsDefined(kind)) throw new LauncherException("LeagueDiagnosticsInvalid");
                batch.Add(new LeagueDiagnosticEvent(consumed + (uint)index + 1, kind,
                    Word(span, 4), Word(span, 8), Word(span, 12), Word(span, 16), Word(span, 20),
                    Word(span, 24), Word(span, 28), Word(span, 32), Word(span, 36)));
            }
            using (var stream = new FileStream(LogPath!, FileMode.Append, FileAccess.Write, FileShare.Read))
            {
                foreach (var entry in batch) WriteLine(stream, entry);
                stream.Flush(flushToDisk: true);
            }
            Events.AddRange(batch);
            consumed = count;
        }
        catch (LauncherException ex) { Error = ex; }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
        {
            Error = new LauncherException("LeagueDiagnosticsLogError", LogPath!, ex.Message);
        }
    }

    internal LeagueSnapshot Capture(Func<LeagueSnapshot> capture)
    {
        if (read is null) return capture();
        var snapshot = CaptureStable(capture);
        return snapshot with { World = snapshot.World + ":load:" + Stamp };
    }

    internal T CaptureStable<T>(Func<T> capture)
    {
        if (read is null) return capture();
        Update();
        if (Error is not null) throw Error;
        var before = read(state, GameLeagueDiagnosticsPatch.HeaderSize);
        if (Word(before, 0) != 0 || Word(before, 16) != 0 || Word(before, 8) != 0)
            throw new LauncherException("LeagueDiagnosticsBusy");
        var snapshot = capture();
        var after = read(state, GameLeagueDiagnosticsPatch.HeaderSize);
        if (!before.SequenceEqual(after) || Word(after, 0) != 0)
            throw new LauncherException("LeagueDiagnosticsBusy");
        Generation = Word(after, 12);
        ActiveLoads = 0;
        return snapshot;
    }

    private static uint Word(ReadOnlySpan<byte> bytes, int offset) =>
        BinaryPrimitives.ReadUInt32LittleEndian(bytes[offset..]);

    private static void WriteLine<T>(Stream stream, T value)
    {
        JsonSerializer.Serialize(stream, value);
        stream.WriteByte((byte)'\n');
    }
}
