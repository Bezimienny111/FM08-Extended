using System.Buffers.Binary;
using System.Diagnostics;
using FmLauncher;

namespace FmLauncher.Tests;

internal static partial class Program
{
    private static void TestModernRules(string directory, string gamePath)
    {
        var binaryPath = Path.Combine(directory, "modern-rules.bin");
        using (var verified = MatchRulePatch.OpenVerifiedGame(gamePath))
        using (var output = new BinaryWriter(File.Create(binaryPath)))
        {
            var writer = GameLeagueChangesPatch.Build(0x10100000, 0x10000000, 0x10200000);
            Assert(writer.Length < 4096);
            output.Write(writer.Length); output.Write(writer);
            output.Write(GameAgingPatch.Hooks.Length);
            foreach (var (hook, index) in GameAgingPatch.Hooks.Select((hook, index) => (hook, index)))
            {
                var original = new byte[hook.Original.Length];
                verified.Position = hook.Address - 0x400000;
                verified.ReadExactly(original);
                Assert(original.SequenceEqual(hook.Original));
                Reject(() => GameAgingPatch.Build(0x10400000, hook, new byte[original.Length]), "UnexpectedGameMemory");
                var bytes = GameAgingPatch.Build(0x10400000 + (uint)index * 256, hook, original);
                output.Write(bytes.Length); output.Write(bytes);
                Assert(bytes[^5] == 0xE9 && unchecked(
                    0x10400000u + (uint)index * 256 + (uint)bytes.Length
                    + BinaryPrimitives.ReadUInt32LittleEndian(bytes.AsSpan(bytes.Length - 4)))
                    == hook.Address + original.Length);
            }
            verified.Position = GameAgingPatch.ThresholdAddress - 0x400000;
            var threshold = new byte[2]; verified.ReadExactly(threshold);
            Assert(threshold.SequenceEqual(GameAgingPatch.ThresholdOriginal));
            var annual = GameLeagueDiagnosticsPatch.Build(0x10600000, 0x10200000,
                LeagueDiagnosticKind.AnnualHistory, GameLeagueDiagnosticsPatch.AnnualOriginal, 0x10100000);
            output.Write(annual.Length); output.Write(annual);
            var agingBody = new byte[0xA36458 - 0xA34E00];
            verified.Position = 0xA34E00 - 0x400000;
            verified.ReadExactly(agingBody);
            output.Write(agingBody.Length); output.Write(agingBody);
            foreach (var hook in GameAgingPatch.Hooks)
            {
                output.Write(hook.Address);
                output.Write(hook.Original.Length);
                var payload = GameAgingPatch.Build(0x10800000 + (uint)Array.IndexOf(GameAgingPatch.Hooks, hook) * 256,
                    hook, hook.Original);
                output.Write(payload.Length); output.Write(payload);
            }
        }
        var start = new ProcessStartInfo(Path.Combine(AppContext.BaseDirectory, "FmLauncher.NativeFixture.exe"))
        {
            UseShellExecute = false, RedirectStandardOutput = true, RedirectStandardError = true
        };
        start.ArgumentList.Add("--modern-rules"); start.ArgumentList.Add(binaryPath);
        using (var fixture = Process.Start(start) ?? throw new InvalidOperationException("Cannot start native rules fixture."))
        {
            try
            {
                var stdout = fixture.StandardOutput.ReadToEndAsync();
                var stderr = fixture.StandardError.ReadToEndAsync();
                if (!fixture.WaitForExit(30000)) throw new InvalidOperationException("Native rules fixture timed out.");
                var text = stdout.GetAwaiter().GetResult() + stderr.GetAwaiter().GetResult();
                if (fixture.ExitCode != 0) throw new InvalidOperationException(text);
                Console.Write(text);
            }
            finally { if (!fixture.HasExited) { fixture.Kill(); fixture.WaitForExit(5000); } }
        }
        using (var verified = MatchRulePatch.OpenVerifiedGame(gamePath))
        using (var suspended = new SuspendedGameProcess(gamePath))
        {
            suspended.ApplyAgingDelay(verified);
            var diagnostic = suspended.ApplyLeagueDiagnostics(verified, changes: true);
            Assert(suspended.LeagueChangesState != 0 && diagnostic != 0);
            Assert(suspended.Read(GameLeagueDiagnosticsPatch.SaveAddress, 7)[0] == 0xE9);
            foreach (var hook in GameAgingPatch.Hooks)
                Assert(suspended.Read(hook.Address, hook.Original.Length)[0] == 0xE9);
            Assert(suspended.Read(GameAgingPatch.ThresholdAddress, 2).SequenceEqual(GameAgingPatch.ThresholdDelayed));
            Assert(suspended.Read(GamePaPatch.HookAddress, GamePaPatch.OriginalEntry.Length).AsSpan()
                .SequenceEqual(GamePaPatch.OriginalEntry));
            Assert(suspended.Read(suspended.LeagueChangesState, GameLeagueChangesPatch.StateSize).All(b => b == 0));
        }
        TestLeagueChangesJournal(directory);
        TestProfileAutomation(directory);
        TestProfileAutomationEdgeCases(directory);
    }

    private static void TestLeagueChangesJournal(string directory)
    {
        const uint stateAddress = 0x10000000;
        var state = new byte[GameLeagueChangesPatch.StateSize];
        var diagnosticState = new byte[GameLeagueDiagnosticsPatch.StateSize];
        static void Set(byte[] buffer, int offset, uint value) =>
            BinaryPrimitives.WriteUInt32LittleEndian(buffer.AsSpan(offset), value);
        Set(diagnosticState, 12, 2);
        var diagnostics = new LeagueDiagnostics();
        diagnostics.Begin(0x20000000, (a, n) => diagnosticState.AsSpan((int)(a - 0x20000000), n).ToArray(),
            directory, 99);
        diagnostics.Update();
        var snapshot = new LeagueSnapshot(new DateOnly(2007, 6, 30), "test:load:" + diagnostics.Stamp,
            LeagueMemoryReader.TopLeagues.Select((uid, i) => new LeagueReading(uid, "League " + uid,
                (uint)i + 1, "Nation " + i, 10, [5,5,5,5,5,0])
                { Address = 0x30000000u + (uint)i * 4096, NationAddress = 0x40000000u + (uint)i * 4096, Vtable = 0x50000000 }).ToArray());
        var profile = LeagueCareerProfile.Create(snapshot);
        var path = Path.Combine(directory, "profile.json");
        profile.Save(path);
        Reject(() => profile.Save(path), "LeagueReportError");
        var loaded = LeagueCareerProfile.Load(path);
        Assert(loaded.Id == profile.Id && loaded.Baseline.Leagues.All(l => l.Address == 0));
        var changes = new LeagueChanges();
        changes.Begin(stateAddress, (a, n) => state.AsSpan((int)(a - stateAddress), n).ToArray(),
            (a, b) => b.CopyTo(state, (int)(a - stateAddress)), diagnostics, directory, 99);
        changes.Bind(loaded, snapshot);
        Assert(changes.Armed && BinaryPrimitives.ReadUInt32LittleEndian(state) == 1);
        Assert(BinaryPrimitives.ReadUInt32LittleEndian(state.AsSpan(8)) == 2007);
        Reject(() => changes.Bind(loaded, snapshot with { Date = new DateOnly(2009, 6, 15) }), "LeagueProfileMismatch");
        changes.Bind(loaded, snapshot);
        var offset = GameLeagueChangesPatch.LogOffset;
        Set(state, offset, 2009); Set(state, offset + 4, snapshot.Leagues[0].Uid);
        Set(state, offset + 8, 10); Set(state, offset + 12, 11); Set(state, offset + 16, 15);
        BinaryPrimitives.WriteDoubleLittleEndian(state.AsSpan(offset + 20), 60);
        Set(state, offset + 28, 2); Set(state, 16, 1);
        changes.Update(); changes.Update();
        Assert(changes.Error is null && changes.Events.Count == 1);
        Assert(changes.Events[0].League == snapshot.Leagues[0].Name);
        Assert(File.ReadAllLines(changes.LogPath!).Length == 2);
        using (var localizerFile = new FileStream(Path.Combine(AppContext.BaseDirectory, "FmLauncher.languages.json"),
            FileMode.Open, FileAccess.Read, FileShare.Read))
        {
            var localizer = new Localizer(localizerFile.Name);
            using var log = new LeagueChangeLogForm(localizer, changes);
            log.Show(); Application.DoEvents();
            var grid = log.Controls.OfType<DataGridView>().Single();
            Assert(grid.RowCount == 1 && (string)grid.Rows[0].Cells[2].Value == snapshot.Leagues[0].Name);
            localizer.Select("pl"); log.RefreshJournal(); log.Close();
        }
        Set(diagnosticState, 12, 3); diagnostics.Update(); changes.Update();
        Assert(!changes.Armed && BinaryPrimitives.ReadUInt32LittleEndian(state) == 0);
        Set(state, 20, 1);
        changes.Update();
        Assert(changes.Error?.Key == "LeagueChangesNativeError" && !changes.Armed);
        changes.End();
        diagnostics.End();
        var configPath = Path.Combine(directory, "modern-config.json");
        var store = new ConfigurationStore(configPath);
        var config = Default();
        Assert(!config.AgingDelayEnabled && !config.LeagueChangesEnabled);
        config.AgingDelayEnabled = config.LeagueChangesEnabled = true;
        store.Save(config);
        Assert(store.Load() is { AgingDelayEnabled: true, LeagueChangesEnabled: true });
        var uiDirectory = Path.Combine(directory, "ui");
        Directory.CreateDirectory(uiDirectory);
        try
        {
            var localizer = new Localizer(Path.Combine(AppContext.BaseDirectory, "FmLauncher.languages.json"));
            using var form = new MainForm(uiDirectory, localizer, _ => new[] { Hd });
            form.Show(); form.Populate(config, new[] { Hd });
            foreach (var language in new[] { "pl", "en" })
            {
                form.ApplyLanguage(language);
                var captured = form.CaptureConfiguration();
                Assert(captured.AgingDelayEnabled && captured.LeagueChangesEnabled);
                Assert(Descendants(form).OfType<CheckBox>().Single(c => c.Name == "AgingDelayEnabled").Checked);
                Assert(Descendants(form).OfType<CheckBox>().Single(c => c.Name == "LeagueChangesEnabled").Checked);
                Assert(Descendants(form).OfType<LinkLabel>().Single(c => c.Name == "CareerProfileBanner").Visible);
                Assert(Descendants(form).OfType<Button>().Single(c => c.Name == "LeagueRetryProfile").Text.Length > 0);
            }
            form.Close();
        }
        finally { Directory.Delete(uiDirectory); }
    }
}
