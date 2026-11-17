using FmLauncher;

namespace FmLauncher.Tests;

internal static partial class Program
{
    private static void TestRuleDisplayStartup(string gamePath)
    {
        using var verified = MatchRulePatch.OpenVerifiedGame(gamePath, out var imageHash);
        Assert(imageHash == MatchRulePatch.SupportedHash);
        using var isolated = new SuspendedGameProcess(gamePath);
        var session = isolated.CreateRuleSession(imageHash);
        var originalFormatter = isolated.Read(GameRuleDisplayPatch.EntryAddress, GameRuleDisplayPatch.NativeFormatterLength);
        var disabled = AppliedRuleSnapshot.Begin(session, EffectiveRuleResolver.Compile(null));
        Assert(isolated.ApplyRuleDisplay(disabled, verified, imageHash) is null);
        Assert(isolated.Read(GameRuleDisplayPatch.EntryAddress, originalFormatter.Length).SequenceEqual(originalFormatter));
        var rules = Default().Rules;
        rules[0].Override = true; rules[0].Substitutions = 5;
        rules[0].BenchOverride = true; rules[0].Bench = 9;
        var policy = EffectiveRuleResolver.Compile(rules);
        var snapshot = isolated.ApplyRuleLimits(policy, verified, session);
        Assert(snapshot.Status(RuleLimit.Substitutions) == AppliedRuleStatus.Verified
            && snapshot.Status(RuleLimit.Bench) == AppliedRuleStatus.Verified);
        // Unsupported formatter images must keep native descriptions without undoing verified engine limits.
        Assert(isolated.ApplyRuleDisplay(snapshot, verified, MatchRulePatch.AlternateSupportedHash) is null);
        Assert(isolated.Read(GameRuleDisplayPatch.EntryAddress, originalFormatter.Length).SequenceEqual(originalFormatter));
        var display = isolated.ApplyRuleDisplay(snapshot, verified, imageHash);
        Assert(display is not null && display.MatchesFreshRead(isolated.Read));
        Assert(snapshot.Revalidate(session, true, isolated.Read).ActiveCodesMask29.SequenceEqual(snapshot.ActiveCodesMask29));
        Reject(() => isolated.ApplyRuleDisplay(snapshot, verified, imageHash), "UnexpectedGameMemory");
        Assert(display!.MatchesFreshRead(isolated.Read));
        Console.WriteLine("PASS: actual suspended startup installers, original/unsupported display fallback, verified getter snapshot and display payload; no main-thread resume.");
    }

    private static void TestRuleDisplayAppliedState()
    {
        var rules = EffectiveTestRules();
        rules[0].Override = true; rules[0].Substitutions = 5;
        rules[0].BenchOverride = true; rules[0].Bench = 9;
        var policy = EffectiveRuleResolver.Compile(rules);
        var session = new RuleHookSession(42, DateTime.UtcNow.Ticks, MatchRulePatch.SupportedHash);
        var memory = new EffectiveRuleMemory();
        var snapshot = AppliedRuleSnapshot.Begin(session, policy);
        Assert(!RuleDisplayInstallation.SupportsAppliedState(snapshot));
        snapshot = snapshot.WithVerified(RuleLimit.Substitutions, memory.Install(policy, RuleLimit.Substitutions, 0x60000000));
        Assert(!RuleDisplayInstallation.SupportsAppliedState(snapshot)); // bench still Installing
        snapshot = snapshot.WithVerified(RuleLimit.Bench, memory.Install(policy, RuleLimit.Bench, 0x60001000));
        Assert(RuleDisplayInstallation.SupportsAppliedState(snapshot));
        memory.Flip(MatchRulePatch.GetterAddress(RuleLimit.Substitutions), 0);
        var lost = snapshot.Revalidate(session, true, memory.Read);
        // Both limits share code0. Its union mask remains1 even though one getter is lost.
        Assert(lost.ActiveCodesMask29.SequenceEqual(snapshot.ActiveCodesMask29));
        Assert(!ReferenceEquals(snapshot, lost) && !RuleDisplayInstallation.SupportsAppliedState(lost));
        Assert(!RuleDisplayInstallation.SupportsAppliedState(snapshot.WithFailed(RuleLimit.Bench)));
        Assert(!RuleDisplayInstallation.SupportsAppliedState(snapshot.WithSessionLost()));
        rules[0].BenchOverride = false;
        var onePolicy = EffectiveRuleResolver.Compile(rules);
        var one = AppliedRuleSnapshot.Begin(session, onePolicy).WithVerified(RuleLimit.Substitutions,
            new EffectiveRuleMemory().Install(onePolicy, RuleLimit.Substitutions, 0x60002000));
        Assert(RuleDisplayInstallation.SupportsAppliedState(one)); // intentional independent disabled dimension
    }

    private static void TestRuleDisplayReceipt()
    {
        const uint address = 0x10003000;
        var flags = new byte[29]; flags[0] = 1;
        var payload = GameRuleDisplayPatch.BuildPayload(address, flags);
        var entry = GameRuleDisplayPatch.BuildEntryJump(address);
        var installedPayload = payload.ToArray();
        var installedEntry = entry.ToArray();
        byte[] Read(uint site, int size) => (site == address ? installedPayload : installedEntry).Take(size).ToArray();
        var receipt = new RuleDisplayInstallation(address, payload, entry);
        Assert(receipt.MatchesFreshRead(Read));
        // A saved/editor buffer mutation cannot replace the evidence of what was installed.
        payload[GameRuleDisplayPatch.ActiveCodesOffset] = 0;
        entry[0] = 0;
        Assert(receipt.MatchesFreshRead(Read));
        installedPayload[GameRuleDisplayPatch.ActiveCodesOffset] = 0;
        Assert(!receipt.MatchesFreshRead(Read));
        installedPayload[GameRuleDisplayPatch.ActiveCodesOffset] = 1;
        installedEntry[1] ^= 1;
        Assert(!receipt.MatchesFreshRead(Read));
        Assert(!receipt.MatchesFreshRead((_, _) => []));
        var badFlags = new byte[29]; badFlags[0] = 2;
        bool rejected = false;
        try { GameRuleDisplayPatch.BuildPayload(address, badFlags); }
        catch (ArgumentException) { rejected = true; }
        Assert(rejected);
    }
}
