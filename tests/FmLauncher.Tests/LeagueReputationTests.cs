using System.Buffers.Binary;
using System.Diagnostics;
using System.Text;
using System.Text.Json;
using FmLauncher;

namespace FmLauncher.Tests;

internal static partial class Program
{
    private static void TestLeagueModel()
    {
        Assert(LeagueReputationModel.Target(11, 18.5, 35.033) == 14);
        foreach (var reputation in Enumerable.Range(1, 20))
            Assert(LeagueReputationModel.Target(reputation, 18.5, 18.5) == reputation);
        Assert(LeagueReputationModel.Target(11, 0, Math.Pow((0.5 - 1e-8) / 1.7, 2)) == 11);
        Assert(LeagueReputationModel.Target(11, 0, Math.Pow((0.5 + 1e-8) / 1.7, 2)) == 12);
        Assert(LeagueReputationModel.Target(20, 0, 100000) == 20);
        Assert(LeagueReputationModel.Target(1, 100000, 0) == 1);
        foreach (var value in new[] { -1d, double.NaN, double.PositiveInfinity, double.NegativeInfinity })
        {
            Reject(() => LeagueReputationModel.Target(11, value, 0), "LeagueInvalidData");
            Reject(() => LeagueReputationModel.Target(11, 0, value), "LeagueInvalidData");
        }
        Reject(() => LeagueReputationModel.Target(0, 0, 0), "LeagueInvalidData");
        Reject(() => LeagueReputationModel.Target(21, 0, 0), "LeagueInvalidData");
        var start = LeagueSample();
        var report = LeagueReputationModel.Begin(start);
        Assert(report.Observations[0].Projections[0].Simulated == 11);
        var annual = start with
        {
            Date = new DateOnly(2008, 6, 15),
            Leagues = [start.Leagues[0] with { History = [2, 3, 4, 5, 35, 0] }]
        };
        var next = LeagueReputationModel.Observe(report, annual);
        var row = next.Observations[^1].Projections[0];
        Assert(row.Target == LeagueReputationModel.Target(11, 15, 49) && row.Simulated == 11 && row.Streak == 1);
        var duplicate = LeagueReputationModel.Observe(next, annual);
        Assert(!duplicate.Observations[^1].Annual && duplicate.Observations[^1].Projections[0] == row);
        annual = annual with
        {
            Date = new DateOnly(2009, 6, 15),
            Leagues = [annual.Leagues[0] with { History = [3, 4, 5, 35, 40, 0] }]
        };
        next = LeagueReputationModel.Observe(duplicate, annual);
        row = next.Observations[^1].Projections[0];
        Assert(row.Simulated == 12 && row.Streak == 0 && row.Direction == 0);
        Assert(row.Target == LeagueReputationModel.Target(11, 15, 87));
        Assert(next.Baseline == start && report.Observations.Length == 1);

        var falling = report with
        {
            Observations = [report.Observations[0] with
            {
                Projections = [report.Observations[0].Projections[0] with { Simulated = 19, Direction = 1, Streak = 1 }]
            }]
        };
        var firstYear = duplicate.Observations[1].Snapshot;
        var reversed = LeagueReputationModel.Observe(falling, firstYear);
        row = reversed.Observations[^1].Projections[0];
        Assert(row.Direction == -1 && row.Streak == 1 && row.Simulated == 19);
        var secondFall = annual with { Leagues = [annual.Leagues[0] with { History = [3, 4, 5, 35, 0, 0] }] };
        var alternating = LeagueReputationModel.Observe(reversed, annual).Observations[^1].Projections[0];
        Assert(alternating.Direction == 1 && alternating.Streak == 1 && alternating.Simulated == 19);
        reversed = LeagueReputationModel.Observe(reversed, secondFall);
        Assert(reversed.Observations[^1].Projections[0].Simulated == 18);
        Reject(() => LeagueReputationModel.Observe(report, start with { Date = new DateOnly(2008, 6, 15) }),
            "LeagueHistoryChanged");

        Reject(() => LeagueReputationModel.Observe(report, start with { World = "another-world" }), "LeagueSessionChanged");
        Reject(() => LeagueReputationModel.Observe(next, start), "LeagueSessionChanged");
        Reject(() => LeagueReputationModel.Observe(report, annual), "LeagueSeasonGap");
        Reject(() => LeagueReputationModel.Observe(report, start with
        {
            Leagues = [start.Leagues[0] with { Reputation = 12 }]
        }), "LeagueSessionChanged");
        Reject(() => LeagueReputationModel.Observe(report, start with
        {
            Leagues = [start.Leagues[0] with { History = [2, 3, 4, 5, 35, 0] }]
        }), "LeagueHistoryChanged");
        Reject(() => LeagueReputationModel.Observe(report, firstYear with { Date = new DateOnly(2008, 6, 14) }),
            "LeagueHistoryChanged");
        var ongoing = LeagueReputationModel.Observe(report, start with
        {
            Date = new DateOnly(2008, 6, 14),
            Leagues = [start.Leagues[0] with { History = [1, 2, 3, 4, 5, 99] }]
        });
        Assert(ongoing.Observations[^1].Projections[0].Coefficient == 15
            && ongoing.Observations[^1].Projections[0].Streak == 0);
        foreach (var value in new[] { float.NaN, -1, 101 })
            Reject(() => LeagueReputationModel.Begin(start with
            {
                Leagues = [start.Leagues[0] with { History = [1, 2, 3, 4, value, 0] }]
            }), "LeagueInvalidData");
    }

    private static LeagueSnapshot LeagueSample() => new(new DateOnly(2007, 6, 30), "test-world",
        [new LeagueReading(129558, "Polish league", 1, "Poland", 11, [1, 2, 3, 4, 5, 0])]);

    private static void TestLeagueReports(string directory)
    {
        var observer = new LeagueObserver(directory);
        observer.Capture(LeagueSample(), baseline: true);
        var path = observer.ReportPath!;
        var contents = File.ReadAllBytes(path);
        var saved = JsonSerializer.Deserialize<LeagueReport>(contents, ConfigurationStore.JsonOptions)!;
        Assert(saved.SchemaVersion == 1 && saved.Baseline.Leagues[0].Coefficient == 15
            && saved.Observations.Single().Projections.Single().Simulated == 11);
        using (var locked = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read))
            Reject(() => observer.Capture(LeagueSample(), baseline: false), "LeagueReportError");
        Assert(observer.Report!.Observations.Length == 1 && observer.Error is not null
            && File.ReadAllBytes(path).SequenceEqual(contents) && !Directory.GetFiles(directory, "*.tmp").Any());
        Reject(() => observer.Capture(LeagueSample(), baseline: false), "LeagueRestartRequired");
        observer.Capture(LeagueSample(), baseline: true);
        Assert(observer.ReportPath != path && File.ReadAllBytes(path).SequenceEqual(contents) && observer.Error is null);
        observer.Capture(LeagueSample(), baseline: false);
        Assert(observer.Report!.Observations.Length == 2);
        Assert(JsonSerializer.Deserialize<LeagueReport>(File.ReadAllText(observer.ReportPath!),
            ConfigurationStore.JsonOptions)!.Observations.Length == 2);
        var notDirectory = Path.Combine(directory, "not-a-directory");
        File.WriteAllText(notDirectory, "not a directory");
        var blocked = new LeagueObserver(notDirectory);
        Reject(() => blocked.Capture(LeagueSample(), baseline: true), "LeagueReportError");
        Assert(blocked.Report is null && blocked.ReportPath is null && blocked.Error is not null);
        var configPath = Path.Combine(directory, "legacy-league-config.json");
        var config = Default();
        Assert(!config.LeagueReputationEnabled);
        File.WriteAllText(configPath, JsonSerializer.Serialize(config, ConfigurationStore.JsonOptions)
            .Replace("  \"LeagueReputationEnabled\": false,\r\n", "")
            .Replace("  \"LeagueReputationEnabled\": false,\n", ""));
        var store = new ConfigurationStore(configPath);
        Assert(!store.Load()!.LeagueReputationEnabled);
        config.LeagueReputationEnabled = true;
        store.Save(config);
        Assert(store.Load()!.LeagueReputationEnabled);
    }

    private static void TestLeagueMemory()
    {
        var memory = new Dictionary<uint, byte>();
        void Bytes(uint address, byte[] value)
        {
            for (var index = 0; index < value.Length; index++) memory[address + (uint)index] = value[index];
        }
        void U32(uint address, uint value) => Bytes(address, BitConverter.GetBytes(value));
        void Text(uint address, string value)
        {
            Bytes(address, new byte[12]);
            Bytes(address + 4, BitConverter.GetBytes((ushort)value.Length));
            U32(address + 8, address + 16);
            Bytes(address + 16, Encoding.Unicode.GetBytes(value));
        }
        byte[] Read(uint address, int size) =>
            Enumerable.Range(0, size).Select(index => memory[address + (uint)index]).ToArray();
        Bytes(0x1096C90, [0x8B, 0x41, 0x14, 0xC3]);
        Bytes(0x1B1EE14, [180, 0, 0xD7, 7, 0]);
        U32(0x1B1ECE4, 0x2000000);
        U32(0x2000004, 0x2000100);
        U32(0x2000018, 0);
        U32(0x2000100, 0x2500200);
        U32(0x250022C, 0xF9A0D0);
        U32(0x2000104, 0x2600000);
        U32(0x2000108, (uint)LeagueMemoryReader.TopLeagues.Length);
        U32(0x2500010, 0x1096C90);
        U32(0x250012C, 0xCA8C60);
        for (var index = 0; index < LeagueMemoryReader.TopLeagues.Length; index++)
        {
            var uid = LeagueMemoryReader.TopLeagues[index];
            var offset = (uint)index;
            var obj = 0x2100000 + offset * 0x1000;
            var nation = 0x2200000 + offset * 0x1000;
            var history = 0x2300000 + offset * 0x100;
            var text = 0x2400000 + offset * 0x100;
            Bytes(obj, new byte[0x90]);
            U32(0x2600000 + offset * 4, obj);
            U32(obj, 0x2500000);
            U32(obj + 0x14, uid);
            U32(obj + 0x18, offset);
            U32(obj + 0x3C, text);
            U32(obj + 0x64, nation);
            Bytes(obj + 0x84, BitConverter.GetBytes((short)11));
            Text(text, $"League {uid}");
            Text(text + 0x80, $"Country {uid}");
            U32(nation + 0x14, uid + 100);
            U32(nation + 0x28, text + 0x80);
            U32(nation + 0x1BC, 0x2500100);
            U32(nation + 0x1C0, history);
            Bytes(nation + 0x1C4, [6]);
            for (var year = 0; year < 6; year++) Bytes(history + (uint)year * 4, BitConverter.GetBytes(year == 5 ? 99f : 3f));
        }
        var snapshot = LeagueMemoryReader.Capture(Read);
        Assert(snapshot.Leagues.Length == 42 && snapshot.Date == new DateOnly(2007, 6, 30));
        Assert(snapshot.Leagues.All(league => league.Reputation == 11 && league.Coefficient == 15));
        // Active derived objects use the active partition rather than the full-array slot.
        U32(0x2000018, 1);
        U32(0x2000010, 0x2500200);
        U32(0x2000014, 0x2601000);
        U32(0x2601000, 0x2100000);
        U32(0x2600000, 0);
        Assert(LeagueMemoryReader.Capture(Read).Leagues.Length == 42);
        U32(0x250012C, 0);
        Reject(() => LeagueMemoryReader.Capture(Read), "LeagueInvalidData");
        U32(0x250012C, 0xCA8C60);
        Bytes(0x22001C4, [5]);
        Reject(() => LeagueMemoryReader.Capture(Read), "LeagueInvalidData");
        Bytes(0x22001C4, [6]);
        Bytes(0x2300000, BitConverter.GetBytes(float.NaN));
        Reject(() => LeagueMemoryReader.Capture(Read), "LeagueInvalidData");
        Bytes(0x2300000, BitConverter.GetBytes(3f));
        var dateReads = 0;
        Reject(() => LeagueMemoryReader.Capture((address, size) =>
        {
            var value = Read(address, size);
            if (address == 0x1B1EE14 && ++dateReads >= 3) value[0]++;
            return value;
        }), "LeagueHistoryChanged");
        U32(0x2100014, 999999);
        Reject(() => LeagueMemoryReader.Capture(Read), "LeagueInvalidData");
    }

    private static int RunLeagueTests(string[] args)
    {
        var directory = args.Length == 3 ? args[2]
            : Path.Combine(Path.GetTempPath(), "FmLauncher.LeagueTests." + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        try
        {
            if (args[0] == "--league-live")
            {
                using var process = Process.GetProcessById(int.Parse(args[1], System.Globalization.CultureInfo.InvariantCulture));
                Run("read-only actual FM08 coefficients and persistent baseline", () =>
                {
                    var snapshot = LeagueMemoryReader.Capture(process);
                    var observer = new LeagueObserver(directory);
                    observer.Capture(snapshot, baseline: true);
                    observer.Capture(LeagueMemoryReader.Capture(process), baseline: false);
                    Assert(observer.Report!.Observations[^1].Projections.All(row => row.Actual == row.Target && row.Actual == row.Simulated));
                    foreach (var uid in new uint[] { 11, 67, 32, 129558 })
                    {
                        var row = snapshot.Leagues.Single(league => league.Uid == uid);
                        Console.WriteLine($"{uid}: reputation={row.Reputation}; coefficient={row.Coefficient:F3}; date={snapshot.Date}");
                    }
                    Console.WriteLine("Report: " + observer.ReportPath);
                });
            }
            else
            {
                Run("league target formula and annual observation simulation", TestLeagueModel);
                Run("league reports: atomic persistence, failures and legacy configuration", () => TestLeagueReports(directory));
                Run("league native snapshot: strict reads, active partition and stability", TestLeagueMemory);
            }
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(ex);
            if (ex is LauncherException error) Console.Error.WriteLine(string.Join(" | ", error.Arguments));
            return 1;
        }
        finally
        {
            if (args.Length != 3)
            {
                foreach (var file in Directory.GetFiles(directory)) File.Delete(file);
                Directory.Delete(directory);
            }
        }
    }
}
