namespace FmLauncher;

internal sealed class LeagueProfileAutomation(string directory, string? legacyDirectory = null)
{
    private string? stamp;
    private CareerIdentity? identity;
    private DateOnly date;
    private uint saveSequence;
    private bool loadedCareer;
    private LeagueSnapshot? pendingBaseline;
    internal string StatusKey { get; private set; } = "LeagueAutoWaiting";
    internal LauncherException? Error { get; private set; }
    internal LeagueCareerProfile? Selected { get; private set; }
    internal string? ProfilePath { get; private set; }
    internal string DirectoryPath => directory;

    internal void Reset()
    {
        stamp = null;
        identity = null;
        pendingBaseline = null;
        saveSequence = 0;
        loadedCareer = false;
        Selected = null;
        ProfilePath = null;
        Error = null;
        StatusKey = "LeagueAutoWaiting";
    }

    internal void Update(LeagueDiagnostics diagnostics, LeagueChanges changes,
        Func<(CareerIdentity Identity, DateOnly Date)> current, Func<LeagueSnapshot> capture)
    {
        if (diagnostics.Error is not null || changes.Error is not null)
        {
            changes.Disarm();
            Error = diagnostics.Error ?? changes.Error;
            StatusKey = "LeagueAutoStopped";
            return;
        }
        if (diagnostics.ActiveLoads != 0)
        {
            changes.Disarm();
            Reset();
            return;
        }
        (CareerIdentity Identity, DateOnly Date) context;
        try { context = current(); }
        catch (LauncherException ex)
        {
            changes.Disarm();
            Reset();
            Error = ex;
            return;
        }
        var saved = diagnostics.LastSave(context.Identity);
        var waitingForSave = StatusKey is "LeagueAutoFirstSave" or "LeagueAutoSaveRetry";
        if (stamp == diagnostics.Stamp && identity == context.Identity
            && !(StatusKey == "LeagueAutoDate" && date != context.Date)
            && (!waitingForSave || saveSequence == (saved?.Sequence ?? 0)
                && date == context.Date && loadedCareer == diagnostics.LoadedCareer))
        {
            if (StatusKey == "LeagueAutoActive" && !changes.Armed) StatusKey = "LeagueAutoStopped";
            return;
        }
        changes.Disarm();
        if (stamp != diagnostics.Stamp || identity != context.Identity) pendingBaseline = null;
        stamp = diagnostics.Stamp;
        identity = context.Identity;
        date = context.Date;
        saveSequence = saved?.Sequence ?? 0;
        loadedCareer = diagnostics.LoadedCareer;
        Selected = null;
        ProfilePath = null;
        Error = null;
        if (date.Month == 6 && date.Day == 15)
        {
            StatusKey = "LeagueAutoDate";
            return;
        }
        LeagueSnapshot snapshot;
        try
        {
            snapshot = capture();
            if (snapshot.Identity != identity) throw new LauncherException("LeagueHistoryChanged");
        }
        catch (LauncherException ex)
        {
            changes.Disarm();
            Error = ex;
            StatusKey = "LeagueAutoWaiting";
            stamp = null;
            return;
        }
        try
        {
            var profiles = ReadProfiles();
            var matches = profiles.Where(entry => entry.Profile.Identity == identity).ToArray();
            if (matches.Length > 1)
            {
                StatusKey = "LeagueAutoConflict";
                return;
            }
            if (matches.Length == 0)
            {
                if (profiles.Any(entry => entry.Profile.Identity is null))
                {
                    StatusKey = "LeagueAutoLegacy";
                    return;
                }
                if (!loadedCareer && saved is null)
                {
                    pendingBaseline = snapshot;
                    StatusKey = "LeagueAutoFirstSave";
                    return;
                }
                var baseline = snapshot;
                if (!loadedCareer && saved is not null)
                {
                    if (saved.Year is < 1900 or > 9998
                        || saved.Day >= (DateTime.IsLeapYear((int)saved.Year) ? 366 : 365))
                        throw new LauncherException("LeagueDiagnosticsInvalid");
                    var savedDate = new DateOnly((int)saved.Year, 1, 1).AddDays((int)saved.Day);
                    if (pendingBaseline is { } pending && pending.Date <= savedDate)
                        baseline = pending;
                    else if (snapshot.Date > savedDate)
                    {
                        pendingBaseline = snapshot;
                        StatusKey = "LeagueAutoSaveRetry";
                        return;
                    }
                }
                Remember(LeagueCareerProfile.Create(baseline), snapshot, diagnostics.Stamp, changes);
                pendingBaseline = null;
                return;
            }
            Activate(matches[0].Profile, matches[0].Path, snapshot, diagnostics.Stamp, changes);
        }
        catch (LauncherException ex)
        {
            changes.Disarm();
            Error = ex;
            StatusKey = "LeagueAutoStopped";
            if (ex.Key is "LeagueDiagnosticsBusy" or "LeagueHistoryChanged") stamp = null;
        }
    }

    internal void Create(LeagueSnapshot snapshot, string currentStamp, LeagueChanges changes)
    {
        var key = snapshot.Identity ?? throw new LauncherException("LeagueInvalidData");
        if (ReadProfiles().Any(entry => entry.Profile.Identity == key)) throw new LauncherException("LeagueAutoExists");
        Remember(LeagueCareerProfile.Create(snapshot), snapshot, currentStamp, changes);
    }

    internal void Remember(LeagueCareerProfile profile, LeagueSnapshot snapshot, string currentStamp, LeagueChanges changes)
    {
        changes.Disarm();
        var key = snapshot.Identity ?? throw new LauncherException("LeagueInvalidData");
        if (profile.Identity is not null && profile.Identity != key)
            throw new LauncherException("LeagueProfileMismatch");
        profile = profile with { Identity = key };
        profile.ValidateFor(snapshot);
        var path = Path.Combine(directory, profile.Id.ToString("N") + ".json");
        try
        {
            Directory.CreateDirectory(directory);
            if (File.Exists(path))
            {
                var existing = LeagueCareerProfile.Load(path);
                if (existing.Identity is null && Equal(existing with { Identity = key }, profile))
                    path = Path.Combine(directory, profile.Id.ToString("N") + ".bound.json");
            }
            if (File.Exists(path))
            {
                var existing = LeagueCareerProfile.Load(path);
                if (!Equal(existing, profile))
                    throw new LauncherException("LeagueAutoConflict");
            }
            else profile.Save(path);
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
        {
            throw new LauncherException("LeagueReportError", path, ex.Message);
        }
        Activate(profile, path, snapshot, currentStamp, changes);
    }

    private void Activate(LeagueCareerProfile profile, string path, LeagueSnapshot snapshot,
        string currentStamp, LeagueChanges changes)
    {
        changes.Bind(profile, snapshot);
        Selected = profile;
        ProfilePath = path;
        identity = snapshot.Identity;
        stamp = currentStamp;
        date = snapshot.Date;
        Error = null;
        StatusKey = "LeagueAutoActive";
    }

    private (string Path, LeagueCareerProfile Profile)[] ReadProfiles()
    {
        (string Path, LeagueCareerProfile Profile)[] legacy = [];
        try
        {
            legacy = Migrate();
            string[] paths;
            try { paths = System.IO.Directory.GetFiles(directory, "*.json"); }
            catch (DirectoryNotFoundException) when (!File.Exists(directory)) { return legacy; }
            return paths
                .Select(path => (Path: path, Profile: LeagueCareerProfile.Load(path))).Concat(legacy).ToArray();
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
        {
            throw new LauncherException("LeagueReportError", directory, ex.Message);
        }
    }

    private static bool Equal(LeagueCareerProfile first, LeagueCareerProfile second) =>
        System.Text.Json.JsonSerializer.Serialize(first, ConfigurationStore.JsonOptions)
            == System.Text.Json.JsonSerializer.Serialize(second, ConfigurationStore.JsonOptions);

    private (string Path, LeagueCareerProfile Profile)[] Migrate()
    {
        if (legacyDirectory is null) return [];
        string[] paths;
        try { paths = Directory.GetFiles(legacyDirectory, "*.json"); }
        catch (DirectoryNotFoundException) when (!File.Exists(legacyDirectory)) { return []; }
        var unbound = new List<(string Path, LeagueCareerProfile Profile)>();
        foreach (var source in paths)
        {
            var profile = LeagueCareerProfile.Load(source);
            if (profile.Identity is null)
            {
                unbound.Add((source, profile));
                continue;
            }
            Directory.CreateDirectory(directory);
            var target = Path.Combine(directory, profile.Id.ToString("N") + ".json");
            if (File.Exists(target))
            {
                if (!Equal(LeagueCareerProfile.Load(target), profile))
                    throw new LauncherException("LeagueAutoConflict");
                continue;
            }
            var temporary = target + "." + Guid.NewGuid().ToString("N") + ".tmp";
            try
            {
                using (var input = File.OpenRead(source))
                using (var output = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
                {
                    input.CopyTo(output);
                    output.Flush(true);
                }
                File.Move(temporary, target);
            }
            finally { if (File.Exists(temporary)) File.Delete(temporary); }
        }
        return unbound.ToArray();
    }
}
