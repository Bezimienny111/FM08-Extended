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
    public bool PositionHighlightsEnabled { get; set; }
    public bool HiddenAttributesEnabled { get; set; }
    // INI-only optional key: older launchers reject unknown JSON members.
    // Keep the schema1 JSON mirror readable by those releases.
    [JsonIgnore]
    public bool TeamTalkReactionsEnabled { get; set; }
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
    public string IniPath => Path.GetFileName(path).Equals("FmLauncher.config.json", StringComparison.OrdinalIgnoreCase)
        ? Path.Combine(Path.GetDirectoryName(path)!, "FmLauncher.ini") : Path.ChangeExtension(path, ".ini");
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
            if (File.Exists(IniPath)) return IniConfiguration.Read(File.ReadAllText(IniPath));
            if (!File.Exists(path)) return null;
            var config = JsonSerializer.Deserialize<LauncherConfiguration>(File.ReadAllText(path), JsonOptions)
                ?? throw new JsonException("Configuration must be an object.");
            ConfigurationValidator.Validate(config);
            return config;
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or JsonException or FormatException)
        {
            throw new LauncherException("ConfigReadError", path, ex.Message);
        }
    }

    public void Save(LauncherConfiguration config)
    {
        ConfigurationValidator.Validate(config);
        var temporary = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
        var iniTemporary = IniPath + "." + Guid.NewGuid().ToString("N") + ".tmp";
        try
        {
            var iniText = IniConfiguration.Write(config, File.Exists(IniPath) ? File.ReadAllText(IniPath) : "");
            using (var stream = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            {
                JsonSerializer.Serialize(stream, config, JsonOptions);
                stream.Flush(flushToDisk: true);
            }
            using (var stream = new FileStream(iniTemporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            {
                var bytes = System.Text.Encoding.UTF8.GetBytes(iniText);
                stream.Write(bytes);
                stream.Flush(flushToDisk: true);
            }
            // Atomic replacement retains the previous configuration in a unique backup.
            // Failed pending files remain for inspection; no cleanup removes files.
            string? jsonBackup = File.Exists(path) ? path + "." + Guid.NewGuid().ToString("N") + ".bak" : null;
            if (jsonBackup is not null) File.Replace(temporary, path, jsonBackup);
            else File.Move(temporary, path);
            try
            {
                if (File.Exists(IniPath)) File.Replace(iniTemporary, IniPath, IniPath + "." + Guid.NewGuid().ToString("N") + ".bak");
                else File.Move(iniTemporary, IniPath);
            }
            catch (Exception error) when (error is IOException or UnauthorizedAccessException)
            {
                // INI is authoritative. Restore the existing JSON mirror if INI commit fails.
                // Preserve the pending INI and every backup; never delete files for rollback.
                if (jsonBackup is not null) File.Copy(jsonBackup, path, overwrite: true);
                throw;
            }
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or FormatException or JsonException)
        {
            throw new LauncherException("ConfigSaveError", path, ex.Message);
        }
    }
}

// INI schema1 is a stable public contract. Existing JSON remains a backward-compatible
// mirror. Missing optional INI keys use model defaults; unknown keys/comments survive Save.
internal static class IniConfiguration
{
    private static Dictionary<string, string> Parse(string text)
    {
        var values = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        var section = "Launcher";
        foreach (var original in text.Split('\n'))
        {
            var line = original.Trim();
            if (line.Length == 0 || line.StartsWith(';') || line.StartsWith('#')) continue;
            if (line.StartsWith('[') && line.EndsWith(']')) { section = line[1..^1].Trim(); continue; }
            var equals = line.IndexOf('=');
            if (equals <= 0) throw new FormatException("Invalid INI line: " + line);
            var key = section + "." + line[..equals].Trim();
            var value = line[(equals + 1)..].Trim();
            if (value.StartsWith('"')) value = JsonSerializer.Deserialize<string>(value) ?? "";
            if (!values.TryAdd(key, value)) throw new FormatException("Duplicate INI key: " + key);
        }
        if (values.TryGetValue("Launcher.SchemaVersion", out var version) && version != "1")
            throw new FormatException("Unsupported INI schema: " + version + ". File preserved.");
        return values;
    }

    internal static LauncherConfiguration Read(string text)
    {
        var values = Parse(text);
        var config = LauncherConfiguration.CreateDefault("", new Resolution(1920, 1080));
        string S(string section, string key, string fallback) => values.GetValueOrDefault(section + "." + key, fallback);
        bool B(string section, string key, bool fallback) => bool.TryParse(S(section, key, fallback.ToString()), out var result)
            ? result : throw new FormatException("Invalid INI boolean: " + section + "." + key);
        int I(string section, string key, int fallback) => int.TryParse(S(section, key, fallback.ToString(System.Globalization.CultureInfo.InvariantCulture)),
            System.Globalization.NumberStyles.Integer, System.Globalization.CultureInfo.InvariantCulture, out var result)
            ? result : throw new FormatException("Invalid INI integer: " + section + "." + key);
        config.Language = S("Launcher", "Language", config.Language);
        config.GamePath = S("Launcher", "GamePath", config.GamePath);
        config.UserDataPath = S("Launcher", "UserDataPath", config.UserDataPath);
        config.DarkMode = B("Launcher", "DarkMode", config.DarkMode);
        config.AdvancedMode = B("Launcher", "AdvancedMode", config.AdvancedMode);
        if (!Enum.TryParse<DisplayMode>(S("Display", "Mode", config.DisplayMode.ToString()), true, out var mode) || !Enum.IsDefined(mode))
            throw new FormatException("Invalid INI display mode.");
        config.DisplayMode = mode;
        config.DisplayOverride = B("Display", "Override", config.DisplayOverride);
        config.Resolution = new Resolution(I("Display", "Width", config.Resolution.Width), I("Display", "Height", config.Resolution.Height));
        config.MatchRulesEnabled = B("Features", "MatchRulesEnabled", config.MatchRulesEnabled);
        config.PaEnabled = B("Features", "PaEnabled", config.PaEnabled);
        config.PaChance = I("Features", "PaChance", config.PaChance);
        config.PanelInformationEnabled = B("Features", "PanelInformationEnabled", config.PanelInformationEnabled);
        config.PositionHighlightsEnabled = B("Features", "PositionHighlightsEnabled", config.PositionHighlightsEnabled);
        config.HiddenAttributesEnabled = B("Features", "HiddenAttributesEnabled", config.HiddenAttributesEnabled);
        config.TeamTalkReactionsEnabled = B("Features", "TeamTalkReactionsEnabled", config.TeamTalkReactionsEnabled);
        config.LeagueReputationEnabled = B("Features", "LeagueReputationEnabled", config.LeagueReputationEnabled);
        config.LeagueDiagnosticsEnabled = B("Features", "LeagueDiagnosticsEnabled", config.LeagueDiagnosticsEnabled);
        config.AgingDelayEnabled = B("Features", "AgingDelayEnabled", config.AgingDelayEnabled);
        config.LeagueChangesEnabled = B("Features", "LeagueChangesEnabled", config.LeagueChangesEnabled);
        foreach (var rule in config.Rules)
        {
            var section = "Rule." + rule.Code;
            rule.Override = B(section, "Override", rule.Override);
            rule.BenchOverride = B(section, "BenchOverride", rule.BenchOverride);
            rule.Substitutions = I(section, "Substitutions", rule.Substitutions);
            rule.Bench = I(section, "Bench", rule.Bench);
        }
        ConfigurationValidator.Validate(config);
        return config;
    }

    internal static string Write(LauncherConfiguration config, string previous)
    {
        _ = Parse(previous); // Reject malformed/newer schema before writing either format.
        var sections = new Dictionary<string, Dictionary<string, string>>(StringComparer.OrdinalIgnoreCase);
        void Add(string section, string key, object value)
        {
            if (!sections.TryGetValue(section, out var keys)) sections.Add(section, keys = new(StringComparer.OrdinalIgnoreCase));
            keys.Add(key, value is string text ? JsonSerializer.Serialize(text) : value is bool boolean ? boolean.ToString().ToLowerInvariant()
                : Convert.ToString(value, System.Globalization.CultureInfo.InvariantCulture)!);
        }
        Add("Launcher", "SchemaVersion", 1); Add("Launcher", "Language", config.Language); Add("Launcher", "GamePath", config.GamePath);
        Add("Launcher", "UserDataPath", config.UserDataPath); Add("Launcher", "DarkMode", config.DarkMode); Add("Launcher", "AdvancedMode", config.AdvancedMode);
        Add("Display", "Mode", config.DisplayMode.ToString()); Add("Display", "Override", config.DisplayOverride);
        Add("Display", "Width", config.Resolution.Width); Add("Display", "Height", config.Resolution.Height);
        foreach (var property in typeof(LauncherConfiguration).GetProperties().Where(property => property.PropertyType == typeof(bool)
            && property.Name is not ("DarkMode" or "AdvancedMode" or "DisplayOverride"))) Add("Features", property.Name, property.GetValue(config)!);
        Add("Features", "PaChance", config.PaChance);
        foreach (var rule in config.Rules.OrderBy(rule => rule.Code))
        {
            var section = "Rule." + rule.Code; Add(section, "Override", rule.Override); Add(section, "BenchOverride", rule.BenchOverride);
            Add(section, "Substitutions", rule.Substitutions); Add(section, "Bench", rule.Bench);
        }
        var output = new List<string>(); var current = "Launcher";
        foreach (var raw in previous.Replace("\r\n", "\n").Split('\n'))
        {
            var line = raw.Trim();
            if (line.StartsWith('[') && line.EndsWith(']')) current = line[1..^1].Trim();
            var equals = line.IndexOf('=');
            if (!line.StartsWith(';') && !line.StartsWith('#') && equals > 0 && sections.TryGetValue(current, out var keys)
                && keys.Remove(line[..equals].Trim(), out var value)) output.Add(line[..equals].Trim() + "=" + value);
            else if (previous.Length > 0) output.Add(raw);
        }
        if (previous.Length == 0) output.Add("; FM08 Extended - INI schema1. Unknown keys and comments are preserved.");
        foreach (var section in sections.Where(section => section.Value.Count > 0))
        {
            output.Add(""); output.Add("[" + section.Key + "]");
            output.AddRange(section.Value.Select(pair => pair.Key + "=" + pair.Value));
        }
        return string.Join(Environment.NewLine, output) + Environment.NewLine;
    }
}
