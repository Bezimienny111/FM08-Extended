namespace FmLauncher;

/// <summary>Bulk editing only: native codes, scope and JSON schema remain independent.</summary>
internal enum GroupRuleAction { Unchanged, Original, Override }
internal sealed record GroupRuleChange(GroupRuleAction Action, int Value);

internal static class MatchRuleGroups
{
    internal static int[] ForCode(int code)
    {
        var original = RuleCatalog.Original(code);
        // Two dynamic/unknown getters are not evidence of equivalent behavior.
        return original is null ? [code] : Enumerable.Range(0, 29)
            .Where(candidate => RuleCatalog.Original(candidate) == original).ToArray();
    }

    internal static void CopyFrom(IReadOnlyList<RuleSettings> rules, int sourceCode)
    {
        if (rules.Count != 29 || rules.Any(rule => rule is null || rule.Code is < 0 or > 28)
            || rules.Select(rule => rule.Code).Distinct().Count() != 29)
            throw new LauncherException("InvalidRules");
        var source = rules.Single(rule => rule.Code == sourceCode);
        // Validate before touching any destination, including independently disabled values.
        if (source.Substitutions is < 0 or > 127 || source.Bench is < 0 or > 127)
            throw new LauncherException("InvalidRuleValue", source.Code);
        if (source.Override && source.Substitutions > 12)
            throw new LauncherException("InvalidSubstitutionLimit");
        if (source.BenchOverride && source.Bench > 12)
            throw new LauncherException("InvalidBenchLimit");
        var group = ForCode(sourceCode);
        foreach (var target in rules.Where(rule => group.Contains(rule.Code)))
        {
            target.Override = source.Override;
            target.Substitutions = source.Substitutions;
            target.BenchOverride = source.BenchOverride;
            target.Bench = source.Bench;
        }
    }

    internal static void Apply(IReadOnlyList<RuleSettings> rules, int representative,
        GroupRuleChange substitutions, GroupRuleChange bench)
    {
        if (rules.Count != 29 || rules.Any(rule => rule is null || rule.Code is < 0 or > 28)
            || rules.Select(rule => rule.Code).Distinct().Count() != 29)
            throw new LauncherException("InvalidRules");
        var codes = ForCode(representative);
        Validate(substitutions, "InvalidSubstitutionLimit");
        Validate(bench, "InvalidBenchLimit");
        foreach (var rule in rules.Where(rule => codes.Contains(rule.Code)))
        {
            if (substitutions.Action != GroupRuleAction.Unchanged)
            {
                rule.Override = substitutions.Action == GroupRuleAction.Override;
                if (rule.Override) rule.Substitutions = substitutions.Value;
            }
            if (bench.Action != GroupRuleAction.Unchanged)
            {
                rule.BenchOverride = bench.Action == GroupRuleAction.Override;
                if (rule.BenchOverride) rule.Bench = bench.Value;
            }
        }

        static void Validate(GroupRuleChange change, string key)
        {
            if (!Enum.IsDefined(change.Action)) throw new LauncherException("InvalidRules");
            if (change.Action == GroupRuleAction.Override && change.Value is < 0 or > 12)
                throw new LauncherException(key);
        }
    }

    internal static bool Mixed(IEnumerable<RuleSettings> rules) =>
        rules.Select(rule => (rule.Override, rule.Substitutions, rule.BenchOverride, rule.Bench))
            .Distinct().Skip(1).Any();
}
