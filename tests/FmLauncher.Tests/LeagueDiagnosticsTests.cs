using System.Buffers.Binary;
using System.Diagnostics;
using System.Security.Cryptography;
using System.Text.Json;
using FmLauncher;

namespace FmLauncher.Tests;

internal static partial class Program
{
    private static void TestLeagueDiagnostics(string directory)
    {
        var state = new byte[GameLeagueDiagnosticsPatch.StateSize];
        const uint address = 0x10000000;
        byte[] Read(uint location, int length) => state.AsSpan(checked((int)(location - address)), length).ToArray();
        void Set(int offset, uint value) => BinaryPrimitives.WriteUInt32LittleEndian(state.AsSpan(offset), value);
        var journal = new LeagueDiagnostics();
        journal.Begin(address, Read, directory, 42);
        var originalStamp = journal.Stamp;
        var observer = new LeagueObserver(directory);
        observer.Capture(LeagueSample(), baseline: true);
        observer.CheckDiagnostics(originalStamp, journal);
        Assert(observer.Error is null);
        var baseline = journal.Capture(LeagueSample);
        Assert(baseline.World.EndsWith(originalStamp, StringComparison.Ordinal));
        Set(12, 1);
        Set(16, 1);
        Set(4, 1);
        Set(20, (uint)LeagueDiagnosticKind.LoadBegin);
        Set(28, 1);
        Set(32, 164);
        Set(36, 2008);
        journal.Update();
        Assert(journal.Error is null && journal.Events.Count == 1 && journal.Generation == 1
            && journal.ActiveLoads == 1 && journal.Stamp != originalStamp);
        observer.CheckDiagnostics(originalStamp, journal);
        Assert(observer.Error?.Key == "LeagueLoadDetected");
        Reject(() => journal.Capture(LeagueSample), "LeagueDiagnosticsBusy");
        Set(16, 0);
        Set(4, 2);
        Set(60, (uint)LeagueDiagnosticKind.LoadReturn);
        Set(68, 1);
        journal.Update();
        journal.Update();
        Assert(journal.Events.Count == 2 && journal.ActiveLoads == 0);
        var lines = File.ReadAllLines(journal.LogPath!);
        Assert(lines.Length == 3 && JsonDocument.Parse(lines[0]).RootElement.GetProperty("SchemaVersion").GetInt32() == 1);
        Assert(JsonSerializer.Deserialize<LeagueDiagnosticEvent>(lines[1])!.Kind == LeagueDiagnosticKind.LoadBegin);
        Assert(journal.Capture(LeagueSample).World != baseline.World);
        observer.Capture(LeagueSample(), baseline: true);
        observer.CheckDiagnostics(journal.Stamp, journal);
        Assert(observer.Error is null);
        Reject(() => journal.Capture(() => { Set(12, 2); return LeagueSample(); }), "LeagueDiagnosticsBusy");
        Set(8, 1);
        journal.Update();
        Assert(journal.Error?.Key == "LeagueDiagnosticsDropped");
        observer.CheckDiagnostics(journal.Stamp, journal);
        Assert(observer.Error?.Key == "LeagueLoadDetected");
        Reject(() => journal.Capture(LeagueSample), "LeagueDiagnosticsDropped");
        journal.End();
        Assert(!journal.Installed && journal.LogPath is not null);
        journal.Reset();
        Assert(journal.Events.Count == 0 && journal.Error is null && journal.Stamp == "");
        Assert(journal.Capture(LeagueSample).World == "test-world");

        Array.Clear(state);
        journal.Begin(address, Read, directory, 43);
        Set(0, 1);
        Set(4, 1);
        Set(20, (uint)LeagueDiagnosticKind.AnnualHistory);
        journal.Update();
        Assert(journal.Events.Count == 0 && journal.Error is null);
        Set(0, 0);
        using (var locked = new FileStream(journal.LogPath!, FileMode.Open, FileAccess.Read, FileShare.Read))
            journal.Update();
        Assert(journal.Error?.Key == "LeagueDiagnosticsLogError" && journal.Events.Count == 0);
        Reject(() => journal.Capture(LeagueSample), "LeagueDiagnosticsLogError");

        Array.Clear(state);
        journal.Begin(address, Read, directory, 44);
        Set(4, GameLeagueDiagnosticsPatch.Capacity + 1);
        journal.Update();
        Assert(journal.Error?.Key == "LeagueDiagnosticsInvalid");
        Array.Clear(state);
        journal.Begin(address, Read, directory, 45);
        Set(4, 1);
        Set(20, 999);
        journal.Update();
        Assert(journal.Error?.Key == "LeagueDiagnosticsInvalid");
        Array.Clear(state);
        journal.Begin(address, Read, directory, 46);
        Set(16, uint.MaxValue);
        journal.Update();
        Assert(journal.Error?.Key == "LeagueDiagnosticsInvalid");

        Array.Clear(state);
        journal.Begin(address, Read, directory, 47);
        Set(12, 3);
        var count = 0;
        void Add(LeagueDiagnosticKind kind, uint mode = uint.MaxValue, uint result = uint.MaxValue,
            uint context = 100, uint thread = 7, uint generation = 3,
            uint scheduledDay = uint.MaxValue, uint scheduledYear = uint.MaxValue)
        {
            var values = new[] { (uint)kind, thread, generation, 242u, 2013u, context, mode, result, scheduledDay, scheduledYear };
            for (var i = 0; i < values.Length; i++) Set(20 + count * 40 + i * 4, values[i]);
            Set(4, (uint)++count);
            journal.Update();
            Assert(journal.Error is null);
        }
        Add(LeagueDiagnosticKind.LoadBegin, mode: 1);
        Add(LeagueDiagnosticKind.LoadReturn, result: 1);
        Assert(!journal.LoadedCareer);
        Add(LeagueDiagnosticKind.LoadBegin, mode: 0, context: 200);
        Add(LeagueDiagnosticKind.LoadReturn, result: 0, context: 200);
        Add(LeagueDiagnosticKind.LoadReturn, result: 1, context: 201);
        Add(LeagueDiagnosticKind.LoadReturn, result: 1, context: 200, thread: 8);
        Assert(!journal.LoadedCareer);
        Add(LeagueDiagnosticKind.LoadReturn, result: 1, context: 200);
        Assert(journal.LoadedCareer);
        var identity = new CareerIdentity(3191021, 136, 2026, 51);
        Add(LeagueDiagnosticKind.SaveCompleted, mode: identity.Token, result: 0,
            scheduledDay: identity.DateWord, scheduledYear: identity.Marker);
        Assert(journal.LastSave(identity) is null);
        Add(LeagueDiagnosticKind.SaveCompleted, mode: identity.Token + 1, result: 1,
            scheduledDay: identity.DateWord, scheduledYear: identity.Marker);
        Add(LeagueDiagnosticKind.SaveCompleted, mode: identity.Token, result: 1,
            scheduledDay: identity.DateWord + 1, scheduledYear: identity.Marker);
        Add(LeagueDiagnosticKind.SaveCompleted, mode: identity.Token, result: 1,
            scheduledDay: identity.DateWord, scheduledYear: (uint)identity.Marker + 1);
        Add(LeagueDiagnosticKind.SaveCompleted, mode: identity.Token, result: 1, generation: 2,
            scheduledDay: identity.DateWord, scheduledYear: identity.Marker);
        Assert(journal.LastSave(identity) is null);
        Add(LeagueDiagnosticKind.SaveCompleted, mode: identity.Token, result: 1,
            scheduledDay: identity.DateWord, scheduledYear: identity.Marker);
        Assert(journal.LastSave(identity)?.Sequence == (uint)count);
        Set(12, 4);
        journal.Update();
        Assert(!journal.LoadedCareer && journal.LastSave(identity) is null);
        journal.End();

        var configPath = Path.Combine(directory, "diagnostics-legacy.json");
        File.WriteAllText(configPath, JsonSerializer.Serialize(Default(), ConfigurationStore.JsonOptions)
            .Replace("  \"LeagueDiagnosticsEnabled\": false,\r\n", "")
            .Replace("  \"LeagueDiagnosticsEnabled\": false,\n", ""));
        var store = new ConfigurationStore(configPath);
        Assert(!store.Load()!.LeagueDiagnosticsEnabled);
        var config = store.Load()!;
        config.LeagueDiagnosticsEnabled = true;
        store.Save(config);
        Assert(store.Load()!.LeagueDiagnosticsEnabled);
    }

    private static void TestLeagueDiagnosticNative(string directory, string gamePath)
    {
        var originalHash = GameFileHash(gamePath);
        using var verified = MatchRulePatch.OpenVerifiedGame(gamePath);
        var path = Path.Combine(directory, "league-native.bin");
        using (var writer = new BinaryWriter(File.Create(path)))
        {
            foreach (var (address, expected) in new[]
            {
                (GameLeagueDiagnosticsPatch.SaveAddress, new byte[] {
                    0x8B,0x8C,0x24,0xEC,2,0,0,0x5F,0x5E,0xB0,1,0x64,0x89,0x0D,0,0,0,0,0x5B,0x8B,0xE5,0x5D,0xC2,0x0C,0 }),
                (0x00467C76u, new byte[] {
                    0x32,0xC0,0x8B,0x8C,0x24,0xEC,2,0,0,0x64,0x89,0x0D,0,0,0,0,0x5F,0x5E,0x5B,0x8B,0xE5,0x5D,0xC2,0x0C,0 })
            })
            {
                var bytes = new byte[expected.Length];
                verified.Position = address - 0x400000;
                verified.ReadExactly(bytes);
                Assert(bytes.SequenceEqual(expected));
                writer.Write(bytes.Length);
                writer.Write(bytes);
            }
            foreach (var (site, kind, expected) in new[]
            {
                (GameLeagueDiagnosticsPatch.AnnualAddress, LeagueDiagnosticKind.AnnualHistory, GameLeagueDiagnosticsPatch.AnnualOriginal),
                (GameLeagueDiagnosticsPatch.LoadAddress, LeagueDiagnosticKind.LoadBegin, GameLeagueDiagnosticsPatch.LoadOriginal),
                (GameLeagueDiagnosticsPatch.ReturnAddress, LeagueDiagnosticKind.LoadReturn, GameLeagueDiagnosticsPatch.ReturnOriginal),
                (GameLeagueDiagnosticsPatch.SaveAddress, LeagueDiagnosticKind.SaveCompleted, GameLeagueDiagnosticsPatch.SaveOriginal)
            })
            {
                var original = new byte[7];
                verified.Position = site - 0x400000;
                verified.ReadExactly(original);
                Assert(original.SequenceEqual(expected));
                Reject(() => GameLeagueDiagnosticsPatch.Build(0x10010000, 0x10000000, kind, new byte[7]),
                    "UnexpectedGameMemory");
                var code = GameLeagueDiagnosticsPatch.Build(0x10100000 + (uint)((int)kind - 1) * 4096,
                    0x10000000, kind, original);
                Assert(code.Length < 4096);
                writer.Write(code.Length);
                writer.Write(code);
            }
        }
        var start = new ProcessStartInfo(Path.Combine(AppContext.BaseDirectory, "FmLauncher.NativeFixture.exe"))
        {
            UseShellExecute = false, RedirectStandardOutput = true, RedirectStandardError = true
        };
        start.ArgumentList.Add("--league");
        start.ArgumentList.Add(path);
        using var fixture = Process.Start(start) ?? throw new InvalidOperationException("Cannot start league fixture.");
        try
        {
            var output = fixture.StandardOutput.ReadToEndAsync();
            var errors = fixture.StandardError.ReadToEndAsync();
            if (!fixture.WaitForExit(30000)) throw new InvalidOperationException("League fixture timed out.");
            var text = output.GetAwaiter().GetResult();
            var error = errors.GetAwaiter().GetResult();
            if (fixture.ExitCode != 0) throw new InvalidOperationException(text + error);
            Console.Write(text);
        }
        finally
        {
            if (!fixture.HasExited) { fixture.Kill(); fixture.WaitForExit(5000); }
        }
        using var suspended = new SuspendedGameProcess(gamePath);
        var unrelated = suspended.Read(GamePaPatch.HookAddress, GamePaPatch.OriginalEntry.Length);
        var saveBefore = suspended.Read(GameLeagueDiagnosticsPatch.SaveAddress, 25);
        var failureBefore = suspended.Read(0x00467C76, 25);
        var state = suspended.ApplyLeagueDiagnostics(verified);
        Assert(suspended.Read(state, GameLeagueDiagnosticsPatch.StateSize).All(value => value == 0));
        foreach (var site in new[] { GameLeagueDiagnosticsPatch.AnnualAddress, GameLeagueDiagnosticsPatch.LoadAddress,
            GameLeagueDiagnosticsPatch.ReturnAddress })
            Assert(suspended.Read(site, 7)[0] == 0xE9);
        Assert(suspended.Read(GamePaPatch.HookAddress, unrelated.Length).SequenceEqual(unrelated));
        Assert(suspended.Read(GameLeagueDiagnosticsPatch.SaveAddress, 25).SequenceEqual(saveBefore));
        Assert(suspended.Read(0x00467C76, 25).SequenceEqual(failureBefore));
        Reject(() => suspended.ApplyLeagueDiagnostics(verified), "UnexpectedGameMemory");
        verified.Position = 0;
        Assert(Convert.ToHexString(SHA256.HashData(verified)) == originalHash);
    }
}
