namespace FmLauncher;

internal enum RuleHookStatus { Installing, Verified }

internal sealed record LaunchLogEntry(DateTimeOffset Time, string Key, object[] Arguments);

internal sealed class LaunchJournal
{
    private readonly List<LaunchLogEntry> entries = [];
    internal IReadOnlyList<LaunchLogEntry> Entries => entries;
    internal void Reset() => entries.Clear();
    internal void Add(string key, params object[] arguments) =>
        entries.Add(new(DateTimeOffset.Now, key, arguments));
    internal void Begin(IReadOnlyList<RuleSettings>? rules)
    {
        Reset();
        Add("LaunchLogStarting");
        foreach (var limit in Enum.GetValues<RuleLimit>())
        {
            var count = rules?.Count(rule => MatchRulePatch.Enabled(rule, limit)) ?? 0;
            Add(rules is null ? "LaunchLogDisabled" : count == 0 ? "LaunchLogOriginal" : "LaunchLogRequested",
                limit, count);
        }
    }
    internal void Rule(RuleLimit limit, RuleHookStatus status) =>
        Add(status == RuleHookStatus.Installing ? "LaunchLogInstalling" : "LaunchLogVerified", limit);
    internal void Failed(Exception error) => Add("LaunchLogFailed", error);
    internal static string Format(LaunchLogEntry entry, Localizer localizer) =>
        localizer.Text(entry.Key, entry.Arguments.Select(argument => argument switch
        {
            RuleLimit limit => (object)localizer.Text(limit == RuleLimit.Substitutions ? "Substitutions" : "Bench"),
            LauncherException error => localizer.Error(error),
            Exception error => error.Message,
            _ => argument
        }).ToArray());
}
