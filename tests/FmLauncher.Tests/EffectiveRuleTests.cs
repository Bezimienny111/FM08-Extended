using FmLauncher;

namespace FmLauncher.Tests;

internal static partial class Program
{
    // Pinned getter expectations from AFE0D0/AFE150, including independent side branches22/28.
    private static void TestEffectiveRules()
    {
        int[] nativeSubs = [3,3,3,3,3,3,3,3,3,7,3,3,3,3,3,3,5,5,12,0,5,4,3,5,6,3,4,3,10];
        int[] nativeBench = [7,5,3,5,7,4,4,6,12,7,9,5,5,5,5,6,8,9,12,0,7,7,7,5,9,11,9,6,10];
        var disabled = EffectiveRuleResolver.Compile(null);
        Assert(disabled.Rules.Count == 29 && disabled.ScopeMode == "NativeCodeGlobal");
        Assert(!disabled.HasOverrides(RuleLimit.Substitutions) && !disabled.HasOverrides(RuleLimit.Bench));
        var rules = EffectiveTestRules();
        foreach (var rule in rules)
        {
            rule.Override = rule.Code % 2 == 0;
            rule.Substitutions = rule.Code % 13;
            rule.BenchOverride = rule.Code % 3 == 0;
            rule.Bench = (rule.Code + 4) % 13;
        }
        var policy = EffectiveRuleResolver.Compile(rules.AsEnumerable().Reverse().ToArray());
        foreach (var code in Enumerable.Range(0, 29))
        foreach (var side in new[] { false, true })
        {
            var subs = code == 28 && side ? 12 : nativeSubs[code];
            var bench = code == 28 && side ? 12 : code == 22 && side ? 5 : nativeBench[code];
            Assert(disabled.Override(code, RuleLimit.Substitutions) is null);
            Assert(disabled.Override(code, RuleLimit.Bench) is null);
            Assert(disabled.Resolve(code, RuleLimit.Substitutions, side) == subs);
            Assert(disabled.Resolve(code, RuleLimit.Bench, side) == bench);
            Assert(policy.Resolve(code, RuleLimit.Substitutions, side) == (rules[code].Override ? rules[code].Substitutions : subs));
            Assert(policy.Resolve(code, RuleLimit.Bench, side) == (rules[code].BenchOverride ? rules[code].Bench : bench));
        }
        foreach (var unknown in new[] { -129, -128, -1, 29, 127, 255, 256 })
        foreach (var limit in Enum.GetValues<RuleLimit>())
        {
            Assert(policy.Override(unknown, limit) is null);
            Assert(policy.Resolve(unknown, limit, false) is null && policy.Resolve(unknown, limit, true) is null);
        }
        EffectiveThrows<LauncherException>(() => EffectiveRuleResolver.Compile([]));
        var duplicate = EffectiveTestRules(); duplicate[28].Code = 0;
        EffectiveThrows<LauncherException>(() => EffectiveRuleResolver.Compile(duplicate));
        var nullRow = EffectiveTestRules(); nullRow[3] = null!;
        EffectiveThrows<LauncherException>(() => EffectiveRuleResolver.Compile(nullRow));
        foreach (var bad in new[] { -1, 13, int.MaxValue })
        {
            var invalid = EffectiveTestRules(); invalid[0].Override = true; invalid[0].Substitutions = bad;
            EffectiveThrows<LauncherException>(() => EffectiveRuleResolver.Compile(invalid));
            invalid[0].Override = false; invalid[0].BenchOverride = true; invalid[0].Bench = bad;
            EffectiveThrows<LauncherException>(() => EffectiveRuleResolver.Compile(invalid));
        }
        var forged = Enumerable.Range(0, 29).Select(code => new EffectiveRuleEntry(code, code == 0 ? 13 : null, null)).ToArray();
        EffectiveThrows<LauncherException>(() => new EffectiveRulePolicy(forged));
        EffectiveThrows<LauncherException>(() => new EffectiveRulePolicy([new EffectiveRuleEntry(0, null, null)]));
        var unsorted = Enumerable.Range(0, 29).Reverse().Select(code => new EffectiveRuleEntry(code, null, null)).ToArray();
        EffectiveThrows<LauncherException>(() => new EffectiveRulePolicy(unsorted));
        var copiedEntries = Enumerable.Range(0, 29).Select(code => new EffectiveRuleEntry(code, code == 0 ? 7 : null, null)).ToArray();
        var copiedPolicy = new EffectiveRulePolicy(copiedEntries); copiedEntries[0] = new EffectiveRuleEntry(0, 1, null);
        Assert(copiedPolicy.Override(0, RuleLimit.Substitutions) == 7);
        var ignored = EffectiveTestRules(); ignored[0].Substitutions = int.MinValue; ignored[0].Bench = int.MaxValue;
        Assert(EffectiveRuleResolver.Compile(ignored).Rules[0] == new EffectiveRuleEntry(0, null, null));
        EffectiveThrows<ArgumentOutOfRangeException>(() => policy.Override(0, (RuleLimit)99));

        // Compilation copies both flags and values. A pending settings edit cannot change engine bytes.
        var payloadBefore = MatchRulePatch.BuildPayload(0x60000000, policy, RuleLimit.Substitutions);
        var benchBefore = MatchRulePatch.BuildPayload(0x60001000, policy, RuleLimit.Bench);
        foreach (var rule in rules) { rule.Code = 99; rule.Override = false; rule.BenchOverride = false; rule.Substitutions = 12; rule.Bench = 12; }
        Assert(MatchRulePatch.BuildPayload(0x60000000, policy, RuleLimit.Substitutions).SequenceEqual(payloadBefore));
        Assert(MatchRulePatch.BuildPayload(0x60001000, policy, RuleLimit.Bench).SequenceEqual(benchBefore));
        EffectiveThrows<NotSupportedException>(() => ((IList<EffectiveRuleEntry>)policy.Rules)[0] = new EffectiveRuleEntry(0, 0, 0));

        // Equal group edits produce exactly the same immutable launch policy and payload.
        var grouped = EffectiveTestRules(); var individual = EffectiveTestRules();
        MatchRuleGroups.Apply(grouped, 0, new GroupRuleChange(GroupRuleAction.Override, 5), new GroupRuleChange(GroupRuleAction.Override, 9));
        foreach (var code in MatchRuleGroups.ForCode(0))
        { individual[code].Override = true; individual[code].Substitutions = 5; individual[code].BenchOverride = true; individual[code].Bench = 9; }
        var groupPolicy = EffectiveRuleResolver.Compile(grouped); var individualPolicy = EffectiveRuleResolver.Compile(individual);
        Assert(groupPolicy.Rules.SequenceEqual(individualPolicy.Rules));
        foreach (var limit in Enum.GetValues<RuleLimit>())
            Assert(MatchRulePatch.BuildPayload(0x60000000, groupPolicy, limit).SequenceEqual(MatchRulePatch.BuildPayload(0x60000000, individualPolicy, limit)));

        // Only verified dimensions activate the running policy; desired Bench12 is not silently applied.
        var requested = EffectiveTestRules(); requested[0].Override = true; requested[0].Substitutions = 7;
        requested[0].BenchOverride = true; requested[0].Bench = 12;
        var runningPolicy = EffectiveRuleResolver.Compile(requested);
        var session = new RuleHookSession(42, DateTime.UtcNow.Ticks, MatchRulePatch.SupportedHash);
        var snapshot = AppliedRuleSnapshot.Begin(session, runningPolicy);
        Assert(snapshot.AppliedRevision == 0 && snapshot.ActiveCodesMask29.All(x => x == 0));
        Assert(snapshot.Status(RuleLimit.Substitutions) == AppliedRuleStatus.Installing && snapshot.Status(RuleLimit.Bench) == AppliedRuleStatus.Installing);
        var memory = new EffectiveRuleMemory();
        var subsReceipt = memory.Install(runningPolicy, RuleLimit.Substitutions, 0x60000000);
        snapshot = snapshot.WithInstalling(RuleLimit.Substitutions).WithVerified(RuleLimit.Substitutions, subsReceipt);
        Assert(snapshot.AppliedOverride(0, RuleLimit.Substitutions) == 7 && snapshot.AppliedOverride(0, RuleLimit.Bench) is null);
        Assert(snapshot.ActiveCodesMask29[0] == 1 && snapshot.ActiveCodesMask29.Skip(1).All(x => x == 0));
        var activeMask = snapshot.ActiveCodesMask29; activeMask[0] = 0; Assert(snapshot.ActiveCodesMask29[0] == 1);
        var revision = snapshot.AppliedRevision;
        requested[0].Substitutions = 1; requested[0].BenchOverride = false;
        Assert(snapshot.AppliedRevision == revision && snapshot.AppliedOverride(0, RuleLimit.Substitutions) == 7);
        var partial = snapshot.WithFailed(RuleLimit.Bench);
        Assert(partial.Status(RuleLimit.Bench) == AppliedRuleStatus.Failed && partial.AppliedOverride(0, RuleLimit.Bench) is null);
        Assert(partial.AppliedOverride(0, RuleLimit.Substitutions) == 7);
        var benchReceipt = memory.Install(runningPolicy, RuleLimit.Bench, 0x60001000);
        snapshot = snapshot.WithInstalling(RuleLimit.Bench).WithVerified(RuleLimit.Bench, benchReceipt);
        Assert(snapshot.Status(RuleLimit.Bench) == AppliedRuleStatus.Verified && snapshot.AppliedOverride(0, RuleLimit.Bench) == 12);
        Assert(snapshot.Revalidate(new RuleHookSession(42, session.StartUtcTicks, session.ImageSha256.ToLowerInvariant()), true, memory.Read) == snapshot);

        // Mutating either original byte arrays or returned copies cannot rewrite the attested receipt.
        var payloadCopy = subsReceipt.CopyPayload(); payloadCopy[0] ^= 1;
        var entryCopy = subsReceipt.CopyEntry(); entryCopy[0] ^= 1;
        Assert(subsReceipt.MatchesFreshRead(memory.Read));
        Assert(subsReceipt.CopyPayload()[0] != payloadCopy[0] && subsReceipt.CopyEntry()[0] != entryCopy[0]);
        var rawPayload = MatchRulePatch.BuildPayload(0x60002000, runningPolicy, RuleLimit.Substitutions);
        var rawJump = MatchRulePatch.BuildEntryJump(0x60002000 + MatchRulePatch.PayloadCodeOffset, RuleLimit.Substitutions);
        var isolated = new EffectiveRuleMemory(); isolated.Put(MatchRulePatch.GetterAddress(RuleLimit.Substitutions), rawJump); isolated.Put(0x60002000, rawPayload);
        var immutableReceipt = RuleInstallationReceipt.CreateVerified(RuleLimit.Substitutions, 0x60002000, rawPayload, rawJump, isolated.Read);
        var pinnedHash = immutableReceipt.PayloadSha256; rawPayload[^1] ^= 1; rawJump[0] ^= 1;
        Assert(immutableReceipt.MatchesFreshRead(isolated.Read) && immutableReceipt.PayloadSha256 == pinnedHash);
        EffectiveThrows<LauncherException>(() => RuleInstallationReceipt.CreateVerified(RuleLimit.Substitutions, 0x60002000, rawPayload, rawJump, isolated.Read));
        var otherRules = EffectiveTestRules(); otherRules[0].Override = true; otherRules[0].Substitutions = 6;
        var otherReceipt = new EffectiveRuleMemory().Install(EffectiveRuleResolver.Compile(otherRules), RuleLimit.Substitutions, 0x60003000);
        EffectiveThrows<LauncherException>(() => AppliedRuleSnapshot.Begin(session, runningPolicy).WithVerified(RuleLimit.Substitutions, otherReceipt));
        EffectiveThrows<LauncherException>(() => AppliedRuleSnapshot.Begin(session, runningPolicy).WithVerified(RuleLimit.Substitutions, benchReceipt));

        memory.Flip(MatchRulePatch.GetterAddress(RuleLimit.Substitutions), 0);
        var changedEntry = snapshot.Revalidate(session, true, memory.Read);
        Assert(changedEntry.Status(RuleLimit.Substitutions) == AppliedRuleStatus.Lost && changedEntry.AppliedOverride(0, RuleLimit.Substitutions) is null);
        Assert(changedEntry.Status(RuleLimit.Bench) == AppliedRuleStatus.Verified && changedEntry.AppliedOverride(0, RuleLimit.Bench) == 12);
        memory.Flip(MatchRulePatch.GetterAddress(RuleLimit.Substitutions), 0);
        Assert(changedEntry.Revalidate(session, true, memory.Read).Status(RuleLimit.Substitutions) == AppliedRuleStatus.Lost);
        memory.Flip(benchReceipt.PayloadAddress, MatchRulePatch.PayloadLength - 1);
        var changedPayload = snapshot.Revalidate(session, true, memory.Read);
        Assert(changedPayload.Status(RuleLimit.Bench) == AppliedRuleStatus.Lost && changedPayload.Status(RuleLimit.Substitutions) == AppliedRuleStatus.Verified);
        var readFailure = snapshot.Revalidate(session, true, (_, _) => throw new IOException("read failed"));
        Assert(!readFailure.HasActiveOverrides && readFailure.ActiveCodesMask29.All(x => x == 0));
        foreach (var mismatch in new[] { new RuleHookSession(43, session.StartUtcTicks, session.ImageSha256), new RuleHookSession(42, session.StartUtcTicks + 1, session.ImageSha256), new RuleHookSession(42, session.StartUtcTicks, new string('A', 64)) })
        {
            var lost = snapshot.Revalidate(mismatch, true, (_, _) => throw new InvalidOperationException("must not read wrong session"));
            Assert(!lost.SessionAlive && !lost.HasActiveOverrides && lost.ActiveCodesMask29.All(x => x == 0));
        }
        var exited = snapshot.Revalidate(session, false, (_, _) => throw new InvalidOperationException("must not read exited process"));
        Assert(!exited.SessionAlive && exited.AppliedRevision > snapshot.AppliedRevision && exited.ActiveCodesMask29.All(x => x == 0));
        EffectiveThrows<InvalidOperationException>(() => exited.WithInstalling(RuleLimit.Substitutions));
        Assert(exited.Revalidate(session, true, memory.Read) == exited);
        Assert(!AppliedRuleSnapshot.Begin(session, disabled).HasActiveOverrides);
        Assert(AppliedRuleSnapshot.Begin(session, disabled).Status(RuleLimit.Bench) == AppliedRuleStatus.Disabled);
        EffectiveThrows<ArgumentException>(() => new RuleHookSession(42, 1, "unverified"));
        EffectiveThrows<ArgumentOutOfRangeException>(() => new RuleHookSession(0, 1, MatchRulePatch.SupportedHash));
    }

    private static List<RuleSettings> EffectiveTestRules() => LauncherConfiguration.CreateDefault("unused", new Resolution(1920,1080)).Rules;
    private static void EffectiveThrows<T>(Action action) where T : Exception
    {
        try { action(); }
        catch (T) { Assert(true); return; }
        throw new InvalidOperationException("Expected " + typeof(T).Name);
    }

    private sealed class EffectiveRuleMemory
    {
        private readonly Dictionary<uint, byte[]> bytes = [];
        internal void Put(uint address, byte[] value) => bytes[address] = (byte[])value.Clone();
        internal byte[] Read(uint address, int size) => bytes.TryGetValue(address, out var value) && value.Length == size
            ? (byte[])value.Clone() : throw new IOException("Unknown or short range");
        internal void Flip(uint address, int offset) => bytes[address][offset] ^= 1;
        internal RuleInstallationReceipt Install(EffectiveRulePolicy policy, RuleLimit limit, uint address)
        {
            var payload = MatchRulePatch.BuildPayload(address, policy, limit);
            var jump = MatchRulePatch.BuildEntryJump(address + MatchRulePatch.PayloadCodeOffset, limit);
            Put(address, payload); Put(MatchRulePatch.GetterAddress(limit), jump);
            return RuleInstallationReceipt.CreateVerified(limit, address, payload, jump, Read);
        }
    }
}
