using System.Text.Json;
using System.Text.Json.Serialization;

namespace FmLauncher;

public enum DisplayMode { Fullscreen, Window, Borderless }

public sealed record Resolution(int Width, int Height)
{
    public override string ToString() => $"{Width} x {Height}";
}

public sealed class RuleSettings
{
    public required int Code { get; set; }
    public required bool Override { get; set; }
    public bool BenchOverride { get; set; }
    public required int Substitutions { get; set; }
    public required int Bench { get; set; }
}

public sealed class LauncherConfiguration
{
    public required int SchemaVersion { get; set; }
    public required string Language { get; set; }
    public required string GamePath { get; set; }
    public string UserDataPath { get; set; } = "";
    public bool MatchRulesEnabled { get; set; } = true;
    public bool DarkMode { get; set; }
    public bool AdvancedMode { get; set; }
    public required DisplayMode DisplayMode { get; set; }
    public bool DisplayOverride { get; set; }
    public required Resolution Resolution { get; set; }
    public required bool PaEnabled { get; set; }
    // Schema 1 compatibility only; preserved on save, ignored by the current PA model.
    public required int PaChance { get; set; }
    public bool PanelInformationEnabled { get; set; } = true;
    public bool LeagueReputationEnabled { get; set; }
    public bool LeagueDiagnosticsEnabled { get; set; }
    public bool AgingDelayEnabled { get; set; }
    public bool LeagueChangesEnabled { get; set; }
    public required List<RuleSettings> Rules { get; set; }

    public static LauncherConfiguration CreateDefault(string gamePath, Resolution resolution) => new()
    {
        SchemaVersion = 1, Language = "en", GamePath = gamePath,
        DisplayMode = DisplayMode.Fullscreen, DisplayOverride = true, Resolution = resolution,
        PaEnabled = false, PaChance = 0,
        Rules = Enumerable.Range(0, 29).Select(code => new RuleSettings
        {
            Code = code, Override = false,
            Substitutions = RuleCatalog.Original(code)?.Substitutions ?? (code == 28 ? 10 : 3),
            Bench = RuleCatalog.Original(code)?.Bench ?? (code == 28 ? 10 : 5)
        }).ToList()
    };
}

public static class RuleCatalog
{
    // Decoded from the two getters in the hash-verified FM08 8.0.2 executable.
    public static (int Substitutions, int Bench)? Original(int code) => code switch
    {
        0 or 4 => (3, 7),
        1 or 3 or 11 or 12 or 13 or 14 => (3, 5),
        2 => (3, 3),
        5 or 6 => (3, 4),
        7 or 15 or 27 => (3, 6),
        8 => (3, 12),
        9 => (7, 7),
        10 => (3, 9),
        16 => (5, 8),
        17 => (5, 9),
        18 => (12, 12),
        19 => (0, 0),
        20 => (5, 7),
        21 => (4, 7),
        23 => (5, 5),
        24 => (6, 9),
        25 => (3, 11),
        26 => (4, 9),
        22 or 28 => null,
        _ => throw new ArgumentOutOfRangeException(nameof(code))
    };
}

public sealed class LauncherException(string key, params object[] arguments) : Exception(key)
{
    public string Key { get; } = key;
    public object[] Arguments { get; } = arguments;
}

public static class ConfigurationValidator
{
    public static void Validate(LauncherConfiguration config)
    {
        if (config.SchemaVersion != 1)
            throw new LauncherException("UnsupportedVersion", config.SchemaVersion);
        if (string.IsNullOrWhiteSpace(config.Language) || string.IsNullOrWhiteSpace(config.GamePath))
            throw new LauncherException("RequiredFields");
        if (config.UserDataPath is null || config.UserDataPath.Length > 0
            && (!Path.IsPathFullyQualified(config.UserDataPath)
                || config.UserDataPath.IndexOfAny(Path.GetInvalidPathChars()) >= 0 || File.Exists(config.UserDataPath)))
            throw new LauncherException("InvalidUserDataPath");
        if (!Enum.IsDefined(config.DisplayMode))
            throw new LauncherException("InvalidDisplayMode");
        if (config.Resolution is null || config.Resolution.Width <= 0 || config.Resolution.Height <= 0
            || config.Resolution.Width > 1920 || config.Resolution.Height > 1080)
            throw new LauncherException("InvalidResolution");
        if (config.PaChance is < 0 or > 100)
            throw new LauncherException("InvalidPa");
        if (config.Rules is null || config.Rules.Count != 29
            || config.Rules.Any(rule => rule is null || rule.Code is < 0 or > 28)
            || config.Rules.Select(rule => rule.Code).Distinct().Count() != 29)
            throw new LauncherException("InvalidRules");
        foreach (var rule in config.Rules)
        {
            // Storage range only, NOT a verified safe engine limit.
            if (rule.Substitutions is < 0 or > 127 || rule.Bench is < 0 or > 127)
                throw new LauncherException("InvalidRuleValue", rule.Code);
            if (rule.Override && rule.Substitutions > 12)
                throw new LauncherException("InvalidSubstitutionLimit");
            if (rule.BenchOverride && rule.Bench > 12)
                throw new LauncherException("InvalidBenchLimit");
        }
    }

    public static void ValidateDisplay(LauncherConfiguration config, IReadOnlyList<Resolution> available)
    {
        Validate(config);
        if (config.DisplayOverride && (config.Resolution.Width < 640 || config.Resolution.Height < 480))
            throw new LauncherException("InvalidGameResolution");
        if (config.DisplayOverride && !available.Contains(config.Resolution))
            throw new LauncherException("ResolutionUnavailable", config.Resolution);
    }
}

public sealed class ConfigurationStore(string path)
{
    internal static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow,
        Converters = { new JsonStringEnumConverter<DisplayMode>(allowIntegerValues: false) }
    };

    public LauncherConfiguration? Load()
    {
        try
        {
            if (!File.Exists(path)) return null;
            var config = JsonSerializer.Deserialize<LauncherConfiguration>(File.ReadAllText(path), JsonOptions)
                ?? throw new JsonException("Configuration must be an object.");
            ConfigurationValidator.Validate(config);
            return config;
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or JsonException)
        {
            throw new LauncherException("ConfigReadError", path, ex.Message);
        }
    }

    public void Save(LauncherConfiguration config)
    {
        ConfigurationValidator.Validate(config);
        var temporary = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
        try
        {
            using (var stream = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            {
                JsonSerializer.Serialize(stream, config, JsonOptions);
                stream.Flush(flushToDisk: true);
            }
            if (File.Exists(path)) File.Replace(temporary, path, null);
            else File.Move(temporary, path);
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
        {
            throw new LauncherException("ConfigSaveError", path, ex.Message);
        }
        finally
        {
            if (File.Exists(temporary)) File.Delete(temporary);
        }
    }
}
