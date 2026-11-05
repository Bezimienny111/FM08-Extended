using System.Buffers.Binary;
using System.Text.Json;
using FmLauncher;

namespace FmLauncher.Tests;

internal static partial class Program
{
    private static void TestProfileAutomation(string directory)
    {
        var root = Path.Combine(directory, "automatic-profiles");
        var native = new byte[GameLeagueChangesPatch.StateSize];
        var lifecycle = new byte[GameLeagueDiagnosticsPatch.HeaderSize];
        void Generation(uint value) => BinaryPrimitives.WriteUInt32LittleEndian(lifecycle.AsSpan(12), value);
        Generation(2);
        var diagnostics = new LeagueDiagnostics();
        diagnostics.Begin(0x20000000, (_, n) => lifecycle.AsSpan(0, n).ToArray(), directory, 77);
        diagnostics.Update();
        var changes = new LeagueChanges();
        changes.Begin(0x10000000, (a, n) => native.AsSpan((int)(a - 0x10000000), n).ToArray(),
            (a, bytes) => bytes.CopyTo(native, (int)(a - 0x10000000)), diagnostics, directory, 77);
        var identity = new CareerIdentity(3191021, 136, 2026, 51);
        var snapshot = new LeagueSnapshot(new DateOnly(2013, 8, 31), "fixture:load:" + diagnostics.Stamp,
            LeagueMemoryReader.TopLeagues.Select((uid, i) => new LeagueReading(uid, "League " + uid,
                (uint)i + 1, "Nation " + i, 10, [5,5,5,5,5,0])
                { Address = 0x30000000u + (uint)i * 4096, NationAddress = 0x40000000u + (uint)i * 4096,
                    Vtable = 0x50000000 }).ToArray()) { Identity = identity };
        var automation = new LeagueProfileAutomation(root);
        void Update() => automation.Update(diagnostics, changes, () => (snapshot.Identity!, snapshot.Date), () => snapshot);
        void Loaded()
        {
            diagnostics.Events.Add(new LeagueDiagnosticEvent(10, LeagueDiagnosticKind.LoadBegin, 1,
                diagnostics.Generation, 242, 2013, 100, 0, uint.MaxValue, uint.MaxValue, uint.MaxValue));
            diagnostics.Events.Add(new LeagueDiagnosticEvent(11, LeagueDiagnosticKind.LoadReturn, 1,
                diagnostics.Generation, 242, 2013, 100, uint.MaxValue, 1, uint.MaxValue, uint.MaxValue));
        }
        Update();
        Assert(automation.StatusKey == "LeagueAutoFirstSave" && !changes.Armed && !Directory.Exists(root));
        diagnostics.Events.Add(new LeagueDiagnosticEvent(1, LeagueDiagnosticKind.SaveCompleted, 1, 2,
            242, 2013, 100, identity.Token, 0, identity.DateWord, identity.Marker));
        Update();
        Assert(!Directory.Exists(root) && !changes.Armed);
        diagnostics.Events.Add(new LeagueDiagnosticEvent(2, LeagueDiagnosticKind.SaveCompleted, 1, 2,
            242, 2013, 100, identity.Token, 1, identity.DateWord, identity.Marker));
        snapshot = snapshot with { Date = snapshot.Date.AddDays(1) };
        Update();
        Assert(changes.Armed && automation.StatusKey == "LeagueAutoActive");
        var path = automation.ProfilePath!;
        var original = File.ReadAllBytes(path);
        Assert(BinaryPrimitives.ReadUInt32LittleEndian(native.AsSpan(3000)) == identity.Token);
        Assert(BinaryPrimitives.ReadUInt32LittleEndian(native.AsSpan(3004)) == identity.DateWord);
        Assert(BinaryPrimitives.ReadUInt32LittleEndian(native.AsSpan(3008)) == identity.Marker);
        Assert(BinaryPrimitives.ReadUInt32LittleEndian(native.AsSpan(3012)) == 1);
        Reject(() => automation.Create(snapshot, diagnostics.Stamp, changes), "LeagueAutoExists");
        var profile = LeagueCareerProfile.Load(path);
        Assert(profile.Identity == identity && profile.Baseline.Identity == identity);
        snapshot = snapshot with { Date = snapshot.Date.AddDays(7) };
        Generation(3); diagnostics.Update(); changes.Update();
        Loaded();
        snapshot = snapshot with { World = "fixture:load:" + diagnostics.Stamp };
        Update();
        Assert(changes.Armed && File.ReadAllBytes(path).SequenceEqual(original));
        automation = new LeagueProfileAutomation(root);
        automation.Update(diagnostics, changes, () => (snapshot.Identity!, snapshot.Date),
            () => throw new LauncherException("LeagueInvalidData"));
        Assert(!changes.Armed && automation.StatusKey == "LeagueAutoWaiting" && automation.Error is not null);
        Update();
        Assert(changes.Armed && automation.Selected?.Id == profile.Id && automation.Error is null);
        var first = snapshot;
        snapshot = snapshot with { Identity = identity with { Token = identity.Token + 1 } };
        Generation(4); diagnostics.Update(); changes.Update();
        Loaded();
        snapshot = snapshot with { World = "fixture:load:" + diagnostics.Stamp };
        Update();
        Assert(changes.Armed && automation.StatusKey == "LeagueAutoActive" && automation.Selected?.Id != profile.Id);
        Reject(() => automation.Remember(profile, snapshot, diagnostics.Stamp, changes), "LeagueProfileMismatch");
        snapshot = first with { Identity = identity with { Marker = 52 }, World = snapshot.World };
        Update();
        Assert(changes.Armed && automation.Selected?.Identity == snapshot.Identity);
        snapshot = first with { Identity = identity with { Year = 2025 }, World = snapshot.World };
        Update();
        Assert(changes.Armed && automation.Selected?.Identity == snapshot.Identity);
        snapshot = first with { World = snapshot.World };
        Update();
        Assert(changes.Armed);
        var duplicate = profile with { Id = Guid.NewGuid() };
        duplicate.Save(Path.Combine(root, duplicate.Id.ToString("N") + ".json"));
        automation.Reset(); Update();
        Assert(!changes.Armed && automation.StatusKey == "LeagueAutoConflict");
        automation.Remember(profile, snapshot, diagnostics.Stamp, changes);
        Update();
        Assert(changes.Armed && automation.Selected?.Id == profile.Id);
        File.Delete(Path.Combine(root, duplicate.Id.ToString("N") + ".json"));
        snapshot = snapshot with { Date = new DateOnly(2015, 6, 15) };
        automation.Reset(); Update();
        Assert(!changes.Armed && automation.StatusKey == "LeagueAutoDate");
        snapshot = snapshot with { Date = snapshot.Date.AddDays(1) };
        Update();
        Assert(changes.Armed);
        snapshot = snapshot with { Date = new DateOnly(2012, 1, 1) };
        automation.Reset(); Update();
        Assert(!changes.Armed && automation.Error?.Key == "LeagueProfileMismatch");
        snapshot = first with { World = snapshot.World };
        File.WriteAllText(Path.Combine(root, "broken.json"), "{");
        automation.Reset(); Update();
        Assert(!changes.Armed && automation.Error?.Key == "LeagueReportError");
        File.Delete(Path.Combine(root, "broken.json"));
        var legacy = profile with { Id = Guid.NewGuid(), Identity = null,
            Baseline = profile.Baseline with { Identity = null } };
        var legacyPath = Path.Combine(directory, "external-legacy-profile.json");
        legacy.Save(legacyPath);
        var legacyOriginal = File.ReadAllBytes(legacyPath);
        automation.Remember(LeagueCareerProfile.Load(legacyPath), snapshot, diagnostics.Stamp, changes);
        Assert(automation.Selected?.Identity == identity && automation.Selected?.Baseline.Date == legacy.Baseline.Date);
        Assert(File.ReadAllBytes(legacyPath).SequenceEqual(legacyOriginal));
        var migrationSource = Path.Combine(directory, "profile-migration-source");
        var migrationTarget = Path.Combine(directory, "profils");
        Directory.CreateDirectory(migrationSource);
        var sourcePath = Path.Combine(migrationSource, "old-profile.json");
        File.Copy(path, sourcePath);
        automation = new LeagueProfileAutomation(migrationTarget, migrationSource);
        Update();
        Assert(changes.Armed && automation.Selected?.Id == profile.Id);
        var migratedPath = automation.ProfilePath!;
        Assert(File.ReadAllBytes(migratedPath).SequenceEqual(original));
        Assert(File.ReadAllBytes(sourcePath).SequenceEqual(original));
        File.WriteAllText(sourcePath, JsonSerializer.Serialize(profile with { Created = profile.Created.AddMinutes(1) },
            ConfigurationStore.JsonOptions));
        automation.Reset(); Update();
        Assert(!changes.Armed && automation.Error?.Key == "LeagueAutoConflict");
        Assert(File.ReadAllBytes(migratedPath).SequenceEqual(original));
        changes.End(); diagnostics.End();

        var frame = new byte[20];
        BinaryPrimitives.WriteUInt32LittleEndian(frame, identity.Token);
        BinaryPrimitives.WriteUInt32LittleEndian(frame.AsSpan(4), 0x121A5BC);
        BinaryPrimitives.WriteUInt32LittleEndian(frame.AsSpan(8), identity.DateWord);
        frame[12] = identity.Marker;
        BinaryPrimitives.WriteUInt32LittleEndian(frame.AsSpan(16), 117931);
        Assert(CareerIdentity.Read((address, n) =>
        {
            Assert(address == 0x1911160 && n == 20);
            return frame;
        }) == identity);
        frame[4] = 0;
        Reject(() => CareerIdentity.Read((_, _) => frame), "LeagueInvalidData");
        Reject(() => (identity with { Token = 10000000 }).Validate(), "LeagueProfileInvalid");
        Reject(() => (identity with { Year = 0 }).Validate(), "LeagueProfileInvalid");
        Assert(JsonSerializer.Deserialize<CareerIdentity>(JsonSerializer.Serialize(identity)) == identity);
        Console.WriteLine("PASS: first successful save, missing-profile load, immutable migration, restart/reload, collisions, legacy import, dates and identity.");
    }

    private static void TestProfileAutomationEdgeCases(string directory)
    {
        var state = new byte[GameLeagueChangesPatch.StateSize];
        var lifecycle = new byte[GameLeagueDiagnosticsPatch.HeaderSize];
        var diagnostics = new LeagueDiagnostics();
        var changes = new LeagueChanges();
        var identity = new CareerIdentity(3191021, 136, 2026, 51);
        var initial = new LeagueSnapshot(new DateOnly(2013, 8, 31), "fixture",
            LeagueMemoryReader.TopLeagues.Select((uid, i) => new LeagueReading(uid, "League " + uid,
                (uint)i + 1, "Nation " + i, 10, [5,5,5,5,5,0])
                { Address = 0x30000000u + (uint)i * 4096, NationAddress = 0x40000000u + (uint)i * 4096,
                    Vtable = 0x50000000 }).ToArray()) { Identity = identity };
        var snapshot = initial;
        var root = "";
        var automation = new LeagueProfileAutomation(directory);
        void Begin(string name, bool loaded = false)
        {
            changes.End();
            Array.Clear(state);
            Array.Clear(lifecycle);
            BinaryPrimitives.WriteUInt32LittleEndian(lifecycle.AsSpan(12), 1);
            diagnostics.Begin(0x20000000, (_, n) => lifecycle.AsSpan(0, n).ToArray(), directory, 77);
            diagnostics.Update();
            changes.Begin(0x10000000, (a, n) => state.AsSpan((int)(a - 0x10000000), n).ToArray(),
                (a, bytes) => bytes.CopyTo(state, (int)(a - 0x10000000)), diagnostics, directory, 77);
            root = Path.Combine(directory, name);
            snapshot = initial with { World = "fixture:load:" + diagnostics.Stamp };
            automation = new LeagueProfileAutomation(root);
            if (loaded)
            {
                diagnostics.Events.Add(new(1, LeagueDiagnosticKind.LoadBegin, 7, 1, 242, 2013, 100,
                    0, uint.MaxValue, uint.MaxValue, uint.MaxValue));
                diagnostics.Events.Add(new(2, LeagueDiagnosticKind.LoadReturn, 7, 1, 242, 2013, 100,
                    uint.MaxValue, 1, uint.MaxValue, uint.MaxValue));
            }
        }
        void Tick() => automation.Update(diagnostics, changes, () => (snapshot.Identity!, snapshot.Date), () => snapshot);
        void Saved(uint sequence, DateOnly date, CareerIdentity? key = null, uint result = 1, uint generation = 1)
        {
            key ??= identity;
            diagnostics.Events.Add(new(sequence, LeagueDiagnosticKind.SaveCompleted, 7, generation,
                (uint)date.DayOfYear - 1, (uint)date.Year, 100, key.Token, result, key.DateWord, key.Marker));
        }

        Begin("first-save-rejections");
        Saved(1, snapshot.Date, result: 0);
        Saved(2, snapshot.Date, identity with { Token = identity.Token + 1 });
        Saved(3, snapshot.Date, generation: 0);
        Tick();
        Assert(automation.StatusKey == "LeagueAutoFirstSave" && !Directory.Exists(root) && !changes.Armed);
        BinaryPrimitives.WriteUInt32LittleEndian(lifecycle.AsSpan(16), 1);
        diagnostics.Update();
        Saved(4, snapshot.Date);
        automation.Update(diagnostics, changes, () => throw new InvalidOperationException("Read during load"),
            () => throw new InvalidOperationException("Capture during load"));
        Assert(!changes.Armed && !Directory.Exists(root));

        Begin("missed-save-retry");
        snapshot = snapshot with { Date = initial.Date.AddDays(1) };
        Saved(1, initial.Date);
        Tick();
        Assert(automation.StatusKey == "LeagueAutoSaveRetry" && !Directory.Exists(root) && !changes.Armed);
        var pendingDate = snapshot.Date;
        snapshot = snapshot with { Date = snapshot.Date.AddDays(1) };
        Saved(2, snapshot.Date);
        Tick();
        Assert(changes.Armed && automation.Selected!.Baseline.Date == pendingDate);
        var immutable = File.ReadAllBytes(automation.ProfilePath!);
        Saved(3, snapshot.Date);
        Tick();
        Assert(File.ReadAllBytes(automation.ProfilePath!).SequenceEqual(immutable));

        Begin("different-unsaved-world");
        Tick();
        snapshot = snapshot with { Identity = identity with { Token = identity.Token + 1 }, Date = initial.Date.AddDays(10) };
        Saved(1, initial.Date.AddDays(1), snapshot.Identity);
        Tick();
        Assert(automation.StatusKey == "LeagueAutoSaveRetry" && !changes.Armed && !Directory.Exists(root));

        Begin("missing-loaded-profile", loaded: true);
        Tick();
        Assert(changes.Armed && automation.Selected?.Baseline.Date == snapshot.Date
            && Directory.GetFiles(root, "*.json").Length == 1);
        immutable = File.ReadAllBytes(automation.ProfilePath!);
        snapshot = snapshot with { Date = snapshot.Date.AddDays(7) };
        Saved(3, snapshot.Date);
        automation.Reset();
        Tick();
        Assert(changes.Armed && File.ReadAllBytes(automation.ProfilePath!).SequenceEqual(immutable));

        Begin("invalid-profile-import");
        var invalidDate = LeagueCareerProfile.Create(snapshot with { Date = snapshot.Date.AddDays(1), Identity = null });
        Reject(() => automation.Remember(invalidDate, snapshot, diagnostics.Stamp, changes), "LeagueProfileMismatch");
        Assert(!Directory.Exists(root) && !changes.Armed);
        var invalidLeagues = LeagueCareerProfile.Create(snapshot with { Identity = null,
            Leagues = snapshot.Leagues.Select((league, i) => i == 0 ? league with { NationUid = 999 } : league).ToArray() });
        Reject(() => automation.Remember(invalidLeagues, snapshot, diagnostics.Stamp, changes), "LeagueProfileMismatch");
        Assert(!Directory.Exists(root) && !changes.Armed);

        Begin("blocked-profile-directory", loaded: true);
        File.WriteAllText(root, "do not replace");
        Tick();
        Assert(!changes.Armed && automation.Error?.Key == "LeagueReportError" && File.ReadAllText(root) == "do not replace");

        Begin("blocked-legacy-directory", loaded: true);
        File.WriteAllText(root + "-old", "do not replace");
        automation = new LeagueProfileAutomation(root, root + "-old");
        Tick();
        Assert(!changes.Armed && automation.Error?.Key == "LeagueReportError" && !Directory.Exists(root));

        Begin("unbound-managed-profile", loaded: true);
        Directory.CreateDirectory(root);
        var legacy = LeagueCareerProfile.Create(snapshot with { Identity = null });
        var path = Path.Combine(root, legacy.Id.ToString("N") + ".json");
        legacy.Save(path);
        immutable = File.ReadAllBytes(path);
        Tick();
        Assert(!changes.Armed && automation.StatusKey == "LeagueAutoLegacy");
        automation.Remember(legacy, snapshot, diagnostics.Stamp, changes);
        Assert(changes.Armed && automation.ProfilePath!.EndsWith(".bound.json", StringComparison.Ordinal)
            && File.ReadAllBytes(path).SequenceEqual(immutable));
        automation.Reset(); Tick();
        Assert(changes.Armed && automation.Selected!.Id == legacy.Id && File.ReadAllBytes(path).SequenceEqual(immutable));

        Begin("unbound-legacy-migration", loaded: true);
        var oldDirectory = root + "-old";
        Directory.CreateDirectory(oldDirectory);
        path = Path.Combine(oldDirectory, legacy.Id.ToString("N") + ".json");
        legacy.Save(path);
        immutable = File.ReadAllBytes(path);
        automation = new LeagueProfileAutomation(root, oldDirectory);
        Tick();
        Assert(!changes.Armed && automation.StatusKey == "LeagueAutoLegacy" && !Directory.Exists(root));
        automation.Remember(legacy, snapshot, diagnostics.Stamp, changes);
        automation.Reset(); Tick();
        Assert(changes.Armed && automation.Selected!.Id == legacy.Id && File.ReadAllBytes(path).SequenceEqual(immutable));
        Assert(Directory.GetFiles(root, "*.json").Length == 1 && !Directory.GetFiles(root, "*.tmp").Any());
        using (var locked = new FileStream(automation.ProfilePath!, FileMode.Open, FileAccess.Read, FileShare.None))
        {
            automation.Reset(); Tick();
            Assert(!changes.Armed && automation.Error?.Key == "LeagueReportError");
        }
        automation.Reset(); Tick();
        Assert(changes.Armed);
        changes.End();
        diagnostics.End();
        Console.WriteLine("PASS: failed/foreign/stale saves, busy loads, missed-save retry, identity changes, immutable reload, invalid imports, disk/lock errors and unbound legacy profiles.");
    }
}
