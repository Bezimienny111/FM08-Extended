using System.Buffers.Binary;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;
using Microsoft.Win32.SafeHandles;

namespace FmLauncher;

internal sealed record LeagueReading(uint Uid, string Name, uint NationUid, string Nation,
    int Reputation, float[] History)
{
    public double Coefficient => History.Take(5).Sum(value => (double)value);
    [System.Text.Json.Serialization.JsonIgnore]
    public uint Address { get; init; }
    [System.Text.Json.Serialization.JsonIgnore]
    public uint NationAddress { get; init; }
    [System.Text.Json.Serialization.JsonIgnore]
    public uint Vtable { get; init; }
}

internal sealed record LeagueSnapshot(DateOnly Date, string World, LeagueReading[] Leagues)
{
    public CareerIdentity? Identity { get; init; }
    public int Season => Date >= new DateOnly(Date.Year, 6, 15) ? Date.Year : Date.Year - 1;
}

internal sealed record LeagueProjection(uint Uid, string Name, string Nation, int Actual,
    int Baseline, double BaselineCoefficient, double Coefficient, int Target, int Simulated, int Direction, int Streak);

internal sealed record LeagueObservation(LeagueSnapshot Snapshot, LeagueProjection[] Projections, bool Annual);
internal sealed record LeagueReport(int SchemaVersion, Guid Id, DateTimeOffset Created,
    LeagueSnapshot Baseline, LeagueObservation[] Observations);

internal static class LeagueReputationModel
{
    internal static int Target(int reputation, double baseline, double current)
    {
        if (reputation is < 1 or > 20 || !double.IsFinite(baseline) || !double.IsFinite(current)
            || baseline < 0 || current < 0)
            throw new LauncherException("LeagueInvalidData");
        return (int)Math.Floor(Math.Clamp(reputation + 1.7 * (Math.Sqrt(current) - Math.Sqrt(baseline)), 1, 20) + 0.5);
    }

    internal static LeagueReport Begin(LeagueSnapshot snapshot)
    {
        Validate(snapshot);
        var rows = snapshot.Leagues.Select(league => new LeagueProjection(league.Uid, league.Name, league.Nation,
            league.Reputation, league.Reputation, league.Coefficient, league.Coefficient, league.Reputation,
            league.Reputation, 0, 0)).ToArray();
        return new LeagueReport(1, Guid.NewGuid(), DateTimeOffset.Now, snapshot,
            [new LeagueObservation(snapshot, rows, false)]);
    }

    internal static LeagueReport Observe(LeagueReport report, LeagueSnapshot snapshot)
    {
        Validate(snapshot);
        var previous = report.Observations[^1];
        if (snapshot.World != report.Baseline.World || snapshot.Date < previous.Snapshot.Date
            || !snapshot.Leagues.Select(league => league.Uid).SequenceEqual(report.Baseline.Leagues.Select(league => league.Uid)))
            throw new LauncherException("LeagueSessionChanged");
        var difference = snapshot.Season - previous.Snapshot.Season;
        if (difference is < 0 or > 1) throw new LauncherException("LeagueSeasonGap");
        if (difference == 1 && snapshot.Leagues.Select((league, index) =>
            league.History.Take(5).SequenceEqual(previous.Snapshot.Leagues[index].History.Take(5))).All(equal => equal))
            throw new LauncherException("LeagueHistoryChanged");
        var rows = new List<LeagueProjection>();
        for (var index = 0; index < snapshot.Leagues.Length; index++)
        {
            var current = snapshot.Leagues[index];
            var start = report.Baseline.Leagues[index];
            var last = previous.Snapshot.Leagues[index];
            var state = previous.Projections[index];
            if (current.NationUid != start.NationUid || current.Reputation != start.Reputation)
                throw new LauncherException("LeagueSessionChanged");
            var historyMatches = difference == 0
                ? current.History.Take(5).SequenceEqual(last.History.Take(5))
                : current.History.Take(4).SequenceEqual(last.History.Skip(1).Take(4));
            if (!historyMatches) throw new LauncherException("LeagueHistoryChanged");
            var target = Target(start.Reputation, start.Coefficient, current.Coefficient);
            var simulated = state.Simulated;
            var direction = state.Direction;
            var streak = state.Streak;
            if (difference == 1)
            {
                var nextDirection = Math.Sign(target - simulated);
                streak = nextDirection == 0 ? 0 : nextDirection == direction ? streak + 1 : 1;
                direction = nextDirection;
                if (streak >= 2)
                {
                    simulated += direction;
                    streak = 0;
                    direction = 0;
                }
            }
            rows.Add(new LeagueProjection(current.Uid, current.Name, current.Nation, current.Reputation,
                start.Reputation, start.Coefficient, current.Coefficient, target, simulated, direction, streak));
        }
        return report with { Observations = [.. report.Observations, new LeagueObservation(snapshot, rows.ToArray(), difference == 1)] };
    }

    internal static void Validate(LeagueSnapshot snapshot)
    {
        if (snapshot.Leagues.Length == 0 || string.IsNullOrWhiteSpace(snapshot.World)
            || snapshot.Leagues.Select(league => league.Uid).Distinct().Count() != snapshot.Leagues.Length)
            throw new LauncherException("LeagueInvalidData");
        foreach (var league in snapshot.Leagues)
        {
            if (league.History.Length != 6 || league.History.Any(value => !float.IsFinite(value) || value is < 0 or > 100)
                || string.IsNullOrWhiteSpace(league.Name) || string.IsNullOrWhiteSpace(league.Nation))
                throw new LauncherException("LeagueInvalidData");
            _ = Target(league.Reputation, league.Coefficient, league.Coefficient);
        }
    }
}

internal sealed class LeagueObserver(string directory)
{
    internal LeagueReport? Report { get; private set; }
    internal string? ReportPath { get; private set; }
    internal LauncherException? Error { get; private set; }

    internal void Capture(LeagueSnapshot snapshot, bool baseline)
    {
        try
        {
            if (!baseline && Error is not null) throw new LauncherException("LeagueRestartRequired");
            var next = baseline ? LeagueReputationModel.Begin(snapshot)
                : LeagueReputationModel.Observe(Report ?? throw new LauncherException("LeagueBaselineRequired"), snapshot);
            var path = Path.Combine(directory, $"league-{next.Id:N}.json");
            Save(path, next);
            Report = next;
            ReportPath = path;
            Error = null;
        }
        catch (LauncherException ex)
        {
            Error = ex;
            throw;
        }
    }

    internal void Fail(LauncherException error) => Error = error;

    internal void CheckDiagnostics(string baselineStamp, LeagueDiagnostics diagnostics)
    {
        if (Report is not null && Error is null
            && (baselineStamp != diagnostics.Stamp || diagnostics.ActiveLoads != 0 || diagnostics.Error is not null))
            Fail(new LauncherException("LeagueLoadDetected"));
    }

    private static void Save(string path, LeagueReport report)
    {
        var temporary = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            using (var stream = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            {
                JsonSerializer.Serialize(stream, report, ConfigurationStore.JsonOptions);
                stream.Flush(flushToDisk: true);
            }
            if (File.Exists(path)) File.Replace(temporary, path, null);
            else File.Move(temporary, path);
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
        {
            throw new LauncherException("LeagueReportError", path, ex.Message);
        }
        finally
        {
            if (File.Exists(temporary)) File.Delete(temporary);
        }
    }
}

internal static class LeagueMemoryReader
{
    internal static readonly uint[] TopLeagues =
    [
        11, 67, 32, 22, 16, 60, 29, 129650, 130286, 1, 5314301, 136543, 7540024,
        129558, 7560276, 7500000, 1300397, 137889, 129120, 129645, 7860000, 45, 7580000,
        7520391, 6, 50, 130486, 132321, 8350942, 131287, 8401073, 129372, 692430,
        5745020, 2300046, 8403697, 59007607, 59007869, 8401070, 7840132, 7483354, 59006196
    ];

    internal static LeagueSnapshot Capture(Process process)
    {
        using var verified = MatchRulePatch.OpenVerifiedGame(process.MainModule?.FileName
            ?? throw new LauncherException("UnexpectedGameMemory"));
        using var handle = OpenProcess(0x410, false, process.Id);
        if (handle.IsInvalid)
            throw new LauncherException("IntegrationError", "OpenProcess (read-only)",
                new Win32Exception(Marshal.GetLastWin32Error()).Message);
        var snapshot = Capture((address, size) => SuspendedGameProcess.ReadMemory(handle, address, size));
        return snapshot with { World = $"{process.Id}:{process.StartTime.ToUniversalTime().Ticks}:{snapshot.World}" };
    }

    internal static LeagueSnapshot Capture(Func<uint, int, byte[]> read)
    {
        var first = ReadSnapshot(read);
        var second = ReadSnapshot(read);
        if (JsonSerializer.Serialize(first) != JsonSerializer.Serialize(second))
            throw new LauncherException("LeagueHistoryChanged");
        return second;
    }

    private static LeagueSnapshot ReadSnapshot(Func<uint, int, byte[]> read)
    {
        uint U32(uint address) => BinaryPrimitives.ReadUInt32LittleEndian(read(address, 4));
        void Require(bool condition)
        {
            if (!condition) throw new LauncherException("LeagueInvalidData");
        }
        string Text(uint buffer)
        {
            Require(buffer != 0);
            var header = read(buffer, 12);
            var count = BinaryPrimitives.ReadUInt16LittleEndian(header.AsSpan(4));
            Require(count is > 0 and <= 1000);
            return Encoding.Unicode.GetString(read(BinaryPrimitives.ReadUInt32LittleEndian(header.AsSpan(8)), count * 2));
        }
        Require(read(0x1096C90, 4).SequenceEqual(new byte[] { 0x8B, 0x41, 0x14, 0xC3 }));
        var dateBytes = read(0x1B1EE14, 5);
        var day = BinaryPrimitives.ReadUInt16LittleEndian(dateBytes);
        var year = BinaryPrimitives.ReadUInt16LittleEndian(dateBytes.AsSpan(2));
        Require(year is >= 1900 and <= 9998 && day < (DateTime.IsLeapYear(year) ? 366 : 365));
        var date = new DateOnly(year, 1, 1).AddDays(day);
        var table = U32(0x1B1ECE4);
        Require(table != 0);
        var collection = U32(table + 4);
        Require(collection != 0 && U32(U32(collection) + 0x2C) == 0xF9A0D0);
        var count = U32(collection + 8);
        Require(count is > 0 and <= 100000);
        var pointers = read(U32(collection + 4), checked((int)count * 4));
        var activeCount = U32(table + 0x18);
        Require(activeCount <= count);
        if (activeCount > 0)
        {
            Require(U32(U32(table + 0x10) + 0x2C) == 0xF9A0D0);
            read(U32(table + 0x14), checked((int)activeCount * 4)).CopyTo(pointers, 0);
        }
        var expected = new HashSet<uint>(TopLeagues);
        var leagues = new Dictionary<uint, LeagueReading>();
        var identity = new StringBuilder($"{table:X8}:{collection:X8}");
        for (var index = 0; index < count; index++)
        {
            var pointer = BinaryPrimitives.ReadUInt32LittleEndian(pointers.AsSpan(index * 4));
            Require(pointer != 0);
            var uid = U32(pointer + 0x14);
            if (!expected.Contains(uid)) continue;
            var data = read(pointer, 0x90);
            var vtable = BinaryPrimitives.ReadUInt32LittleEndian(data);
            Require(U32(vtable + 0x10) == 0x1096C90 && U32(pointer + 0x18) == index && !leagues.ContainsKey(uid));
            var nation = BinaryPrimitives.ReadUInt32LittleEndian(data.AsSpan(0x64));
            Require(nation != 0 && read(nation + 0x1C4, 1)[0] == 6
                && U32(U32(nation + 0x1BC) + 0x2C) == 0xCA8C60);
            var historyBytes = read(U32(nation + 0x1C0), 24);
            var history = Enumerable.Range(0, 6).Select(i =>
                BinaryPrimitives.ReadSingleLittleEndian(historyBytes.AsSpan(i * 4))).ToArray();
            var league = new LeagueReading(uid, Text(U32(pointer + 0x3C)), U32(nation + 0x14),
                Text(U32(nation + 0x28)), BinaryPrimitives.ReadInt16LittleEndian(data.AsSpan(0x84)), history)
                { Address = pointer, NationAddress = nation, Vtable = vtable };
            Require(data.SequenceEqual(read(pointer, 0x90))
                && historyBytes.SequenceEqual(read(U32(nation + 0x1C0), 24)));
            leagues.Add(uid, league);
            identity.Append($":{uid}:{pointer:X8}:{nation:X8}");
        }
        Require(leagues.Count == TopLeagues.Length);
        Require(dateBytes.SequenceEqual(read(0x1B1EE14, 5)) && table == U32(0x1B1ECE4)
            && collection == U32(table + 4) && count == U32(collection + 8));
        var result = new LeagueSnapshot(date, identity.ToString(), TopLeagues.Select(uid => leagues[uid]).ToArray());
        LeagueReputationModel.Validate(result);
        return result;
    }

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern SafeProcessHandle OpenProcess(uint access, [MarshalAs(UnmanagedType.Bool)] bool inherit, int id);
}
