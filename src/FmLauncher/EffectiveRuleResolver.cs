namespace FmLauncher;

/// <summary>A copied launch policy for native rule codes, never a per-competition profile.</summary>
internal sealed record EffectiveRuleEntry(int Code, int? SubstitutionsOverride, int? BenchOverride);

internal sealed class EffectiveRulePolicy
{
    private readonly EffectiveRuleEntry[] entries;
    internal IReadOnlyList<EffectiveRuleEntry> Rules { get; }
    internal string ScopeMode => "NativeCodeGlobal";

    internal EffectiveRulePolicy(EffectiveRuleEntry[] source)
    {
        ArgumentNullException.ThrowIfNull(source);
        entries = (EffectiveRuleEntry[])source.Clone();
        if (entries.Length != 29 || entries.Where((entry, index) => entry is null || entry.Code != index).Any())
            throw new LauncherException("InvalidRules");
        foreach (var entry in entries)
        {
            if (entry.SubstitutionsOverride is < 0 or > 12)
                throw new LauncherException("InvalidSubstitutionLimit");
            if (entry.BenchOverride is < 0 or > 12)
                throw new LauncherException("InvalidBenchLimit");
        }
        Rules = Array.AsReadOnly(entries);
    }

    internal int? Override(int code, RuleLimit limit)
    {
        ValidateLimit(limit);
        if (code is < 0 or > 28) return null;
        return limit == RuleLimit.Substitutions ? entries[code].SubstitutionsOverride : entries[code].BenchOverride;
    }

    internal bool HasOverrides(RuleLimit limit)
    {
        ValidateLimit(limit);
        return entries.Any(entry => Override(entry.Code, limit).HasValue);
    }

    /// <summary>Desired compiled values; running-game authority is AppliedRuleSnapshot, not this policy.</summary>
    internal int? Resolve(int code, RuleLimit limit, bool side) =>
        Override(code, limit) ?? EffectiveRuleResolver.NativeFallback(code, limit, side);

    internal static void ValidateLimit(RuleLimit limit)
    {
        if (limit is not RuleLimit.Substitutions and not RuleLimit.Bench)
            throw new ArgumentOutOfRangeException(nameof(limit));
    }
}

internal static class EffectiveRuleResolver
{
    internal static EffectiveRulePolicy Compile(IReadOnlyList<RuleSettings>? rules)
    {
        if (rules is null)
            return new EffectiveRulePolicy(Enumerable.Range(0, 29)
                .Select(code => new EffectiveRuleEntry(code, null, null)).ToArray());
        if (rules.Count != 29 || rules.Any(rule => rule is null || rule.Code is < 0 or > 28)
            || rules.Select(rule => rule.Code).Distinct().Count() != 29)
            throw new LauncherException("InvalidRules");
        var copied = new EffectiveRuleEntry[29];
        foreach (var rule in rules)
        {
            // A disabled value is deliberately absent; storage/editor validation is a separate contract.
            if (rule.Override && rule.Substitutions is < 0 or > 12)
                throw new LauncherException("InvalidSubstitutionLimit");
            if (rule.BenchOverride && rule.Bench is < 0 or > 12)
                throw new LauncherException("InvalidBenchLimit");
            copied[rule.Code] = new EffectiveRuleEntry(rule.Code,
                rule.Override ? rule.Substitutions : null, rule.BenchOverride ? rule.Bench : null);
        }
        return new EffectiveRulePolicy(copied);
    }

    /// <summary>Known vanilla getter result; unknown/signed out-of-range codes must defer to native code.</summary>
    internal static int? NativeFallback(int code, RuleLimit limit, bool side)
    {
        EffectiveRulePolicy.ValidateLimit(limit);
        if (code is < 0 or > 28) return null;
        if (code == 22) return limit == RuleLimit.Substitutions ? 3 : side ? 5 : 7;
        if (code == 28) return side ? 12 : 10;
        var original = RuleCatalog.Original(code)!.Value;
        return limit == RuleLimit.Substitutions ? original.Substitutions : original.Bench;
    }
}
