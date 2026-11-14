using System.Security.Cryptography;

namespace FmLauncher;

internal enum AppliedRuleStatus { Disabled, Installing, Verified, Failed, Lost }

internal sealed record RuleHookSession
{
    internal int ProcessId { get; }
    internal long StartUtcTicks { get; }
    internal string ImageSha256 { get; }

    internal RuleHookSession(int processId, long startUtcTicks, string imageSha256)
    {
        if (processId <= 0) throw new ArgumentOutOfRangeException(nameof(processId));
        if (startUtcTicks <= 0 || startUtcTicks > DateTime.MaxValue.Ticks)
            throw new ArgumentOutOfRangeException(nameof(startUtcTicks));
        if (imageSha256 is null || imageSha256.Length != 64 || !imageSha256.All(Uri.IsHexDigit))
            throw new ArgumentException("A pinned SHA256 is required.", nameof(imageSha256));
        ProcessId = processId;
        StartUtcTicks = startUtcTicks;
        ImageSha256 = imageSha256.ToUpperInvariant();
    }
}

/// <summary>Immutable evidence of readback for the entire entry and payload, not merely an arbitrary JMP.</summary>
internal sealed class RuleInstallationReceipt
{
    private readonly byte[] payload;
    private readonly byte[] entry;
    internal RuleLimit Limit { get; }
    internal uint PayloadAddress { get; }
    internal uint EntryAddress => MatchRulePatch.GetterAddress(Limit);
    internal string PayloadSha256 { get; }
    internal string EntrySha256 { get; }
    internal long VerifiedUtcTicks { get; }
    internal byte[] CopyPayload() => (byte[])payload.Clone();
    internal byte[] CopyEntry() => (byte[])entry.Clone();

    private RuleInstallationReceipt(RuleLimit limit, uint payloadAddress, byte[] installedPayload, byte[] jump)
    {
        Limit = limit;
        PayloadAddress = payloadAddress;
        payload = (byte[])installedPayload.Clone();
        entry = (byte[])jump.Clone();
        PayloadSha256 = Convert.ToHexString(SHA256.HashData(payload));
        EntrySha256 = Convert.ToHexString(SHA256.HashData(entry));
        VerifiedUtcTicks = DateTime.UtcNow.Ticks;
    }

    internal static RuleInstallationReceipt CreateVerified(RuleLimit limit, uint payloadAddress,
        byte[] payload, byte[] jump, Func<uint, int, byte[]> read)
    {
        ArgumentNullException.ThrowIfNull(payload);
        ArgumentNullException.ThrowIfNull(jump);
        ArgumentNullException.ThrowIfNull(read);
        EffectiveRulePolicy.ValidateLimit(limit);
        if (payloadAddress == 0 || payloadAddress > uint.MaxValue - MatchRulePatch.PayloadLength
            || payload.Length != MatchRulePatch.PayloadLength
            || !jump.AsSpan().SequenceEqual(MatchRulePatch.BuildEntryJump(
                checked(payloadAddress + MatchRulePatch.PayloadCodeOffset), limit)))
            throw new LauncherException("UnexpectedGameMemory");
        // Copy before external reads so later caller mutations cannot change the attested bytes.
        var receipt = new RuleInstallationReceipt(limit, payloadAddress, payload, jump);
        if (!receipt.MatchesFreshRead(read)) throw new LauncherException("UnexpectedGameMemory");
        return receipt;
    }

    internal bool MatchesFreshRead(Func<uint, int, byte[]> read)
    {
        ArgumentNullException.ThrowIfNull(read);
        try
        {
            var actualEntry = read(EntryAddress, entry.Length);
            var actualPayload = read(PayloadAddress, payload.Length);
            return actualEntry is not null && actualPayload is not null
                && actualEntry.AsSpan().SequenceEqual(entry) && actualPayload.AsSpan().SequenceEqual(payload);
        }
        catch (Exception) { return false; } // Read failure or exited session invalidates evidence; no writes/retries.
    }
}

/// <summary>Immutable installed-state authority. Configuration changes cannot mutate a running snapshot.</summary>
internal sealed class AppliedRuleSnapshot
{
    private sealed record LimitState(AppliedRuleStatus Status, RuleInstallationReceipt? Receipt);
    private readonly LimitState substitutions;
    private readonly LimitState bench;
    internal RuleHookSession Session { get; }
    internal EffectiveRulePolicy Policy { get; }
    internal long AppliedRevision { get; }
    internal bool SessionAlive { get; }
    internal string ScopeMode => "NativeCodeGlobal";
    internal bool HasActiveOverrides => SessionAlive &&
        (substitutions.Status == AppliedRuleStatus.Verified || bench.Status == AppliedRuleStatus.Verified);

    private AppliedRuleSnapshot(RuleHookSession session, EffectiveRulePolicy policy, long revision,
        bool sessionAlive, LimitState substitutions, LimitState bench)
    {
        Session = session;
        Policy = policy;
        AppliedRevision = revision;
        SessionAlive = sessionAlive;
        this.substitutions = substitutions;
        this.bench = bench;
    }

    internal static AppliedRuleSnapshot Begin(RuleHookSession session, EffectiveRulePolicy policy)
    {
        ArgumentNullException.ThrowIfNull(session);
        ArgumentNullException.ThrowIfNull(policy);
        LimitState Initial(RuleLimit limit) => new(policy.HasOverrides(limit)
            ? AppliedRuleStatus.Installing : AppliedRuleStatus.Disabled, null);
        return new AppliedRuleSnapshot(session, policy, 0, true,
            Initial(RuleLimit.Substitutions), Initial(RuleLimit.Bench));
    }

    private LimitState State(RuleLimit limit) => limit switch
    {
        RuleLimit.Substitutions => substitutions,
        RuleLimit.Bench => bench,
        _ => throw new ArgumentOutOfRangeException(nameof(limit))
    };
    internal AppliedRuleStatus Status(RuleLimit limit) => State(limit).Status;
    internal RuleInstallationReceipt? Receipt(RuleLimit limit) => State(limit).Receipt;
    internal int? AppliedOverride(int code, RuleLimit limit) => SessionAlive
        && Status(limit) == AppliedRuleStatus.Verified ? Policy.Override(code, limit) : null;

    internal byte[] ActiveCodesMask29 => Enumerable.Range(0, 29).Select(code =>
        (byte)(AppliedOverride(code, RuleLimit.Substitutions).HasValue
            || AppliedOverride(code, RuleLimit.Bench).HasValue ? 1 : 0)).ToArray();

    private AppliedRuleSnapshot Replace(RuleLimit limit, LimitState state)
    {
        _ = State(limit);
        return new AppliedRuleSnapshot(Session, Policy, checked(AppliedRevision + 1), SessionAlive,
            limit == RuleLimit.Substitutions ? state : substitutions,
            limit == RuleLimit.Bench ? state : bench);
    }

    internal AppliedRuleSnapshot WithInstalling(RuleLimit limit)
    {
        if (!SessionAlive || !Policy.HasOverrides(limit))
            throw new InvalidOperationException("A live enabled policy is required for installation.");
        return Replace(limit, new LimitState(AppliedRuleStatus.Installing, null));
    }

    internal AppliedRuleSnapshot WithVerified(RuleLimit limit, RuleInstallationReceipt receipt)
    {
        ArgumentNullException.ThrowIfNull(receipt);
        if (!SessionAlive || Status(limit) != AppliedRuleStatus.Installing || !Policy.HasOverrides(limit)
            || receipt.Limit != limit
            || !receipt.CopyPayload().AsSpan().SequenceEqual(MatchRulePatch.BuildPayload(receipt.PayloadAddress, Policy, limit))
            || !receipt.CopyEntry().AsSpan().SequenceEqual(MatchRulePatch.BuildEntryJump(
                checked(receipt.PayloadAddress + MatchRulePatch.PayloadCodeOffset), limit)))
            throw new LauncherException("UnexpectedGameMemory");
        return Replace(limit, new LimitState(AppliedRuleStatus.Verified, receipt));
    }

    internal AppliedRuleSnapshot WithFailed(RuleLimit limit) =>
        Replace(limit, new LimitState(Policy.HasOverrides(limit) ? AppliedRuleStatus.Failed : AppliedRuleStatus.Disabled, null));

    internal AppliedRuleSnapshot WithLost(RuleLimit limit) =>
        Replace(limit, new LimitState(Policy.HasOverrides(limit) ? AppliedRuleStatus.Lost : AppliedRuleStatus.Disabled,
            State(limit).Receipt));

    internal AppliedRuleSnapshot WithSessionLost()
    {
        if (!SessionAlive) return this;
        LimitState Lost(RuleLimit limit) => new(Policy.HasOverrides(limit)
            ? AppliedRuleStatus.Lost : AppliedRuleStatus.Disabled, State(limit).Receipt);
        return new AppliedRuleSnapshot(Session, Policy, checked(AppliedRevision + 1), false,
            Lost(RuleLimit.Substitutions), Lost(RuleLimit.Bench));
    }

    /// <summary>Fresh read-only check. A changed PID/start/hash or exited process loses both dimensions.</summary>
    internal AppliedRuleSnapshot Revalidate(RuleHookSession? actualSession, bool sessionAlive,
        Func<uint, int, byte[]> read)
    {
        ArgumentNullException.ThrowIfNull(read);
        if (!SessionAlive) return this;
        if (!sessionAlive || actualSession != Session) return WithSessionLost();
        var result = this;
        foreach (var limit in Enum.GetValues<RuleLimit>())
            if (result.Status(limit) == AppliedRuleStatus.Verified
                && result.Receipt(limit)?.MatchesFreshRead(read) != true)
                result = result.WithLost(limit);
        return result;
    }
}
