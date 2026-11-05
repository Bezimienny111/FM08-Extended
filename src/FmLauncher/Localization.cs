using System.Globalization;
using System.Reflection;
using System.Text;
using System.Text.Json;

namespace FmLauncher;

public sealed class LanguageDefinition
{
    public required string Code { get; set; }
    public required string Name { get; set; }
    public required Dictionary<string, string> Texts { get; set; }
    public override string ToString() => Name;
}

public sealed class LanguageFile
{
    public required int SchemaVersion { get; set; }
    public required List<LanguageDefinition> Languages { get; set; }
}

public sealed class Localizer
{
    private readonly LanguageDefinition fallback;
    public IReadOnlyList<LanguageDefinition> Languages { get; }
    public string Code { get; private set; } = "en";
    public LauncherException? Warning { get; }

    public Localizer(string path)
    {
        using var stream = Assembly.GetExecutingAssembly()
            .GetManifestResourceStream("FmLauncher.FmLauncher.languages.json")
            ?? throw new InvalidOperationException("Embedded translations are missing.");
        var builtIn = JsonSerializer.Deserialize<LanguageFile>(stream, ConfigurationStore.JsonOptions)
            ?? throw new InvalidOperationException("Embedded translations are invalid.");
        fallback = builtIn.Languages.Single(language => language.Code == "en");
        Validate(builtIn, fallback);
        Languages = builtIn.Languages;
        try
        {
            var file = JsonSerializer.Deserialize<LanguageFile>(File.ReadAllText(path), ConfigurationStore.JsonOptions)
                ?? throw new JsonException("Language file must be an object.");
            Validate(file, fallback);
            Languages = file.Languages;
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or JsonException or FormatException)
        {
            Warning = new LauncherException("LanguageFileWarning", ex.Message);
        }
    }

    private static void Validate(LanguageFile file, LanguageDefinition fallback)
    {
        if (file.SchemaVersion != 1 || file.Languages is null || file.Languages.Count == 0
            || file.Languages.Any(language => language is null || string.IsNullOrWhiteSpace(language.Code)
                || string.IsNullOrWhiteSpace(language.Name) || language.Texts is null)
            || file.Languages.Select(language => language.Code).Distinct(StringComparer.OrdinalIgnoreCase).Count() != file.Languages.Count
            || !file.Languages.Any(language => language.Code == "en"))
            throw new JsonException("Invalid language file structure; an 'en' language is required.");
        foreach (var language in file.Languages)
        foreach (var pair in language.Texts)
        {
            if (pair.Value is null) throw new JsonException($"Null translation: {pair.Key}");
            var format = CompositeFormat.Parse(pair.Value);
            if (fallback.Texts.TryGetValue(pair.Key, out var original)
                && format.MinimumArgumentCount != CompositeFormat.Parse(original).MinimumArgumentCount)
                throw new JsonException($"Incompatible placeholders: {language.Code}/{pair.Key}");
        }
    }

    public void Select(string code)
    {
        if (!Languages.Any(language => language.Code == code))
            throw new LauncherException("UnknownLanguage", code);
        Code = code;
    }

    public string Text(string key, params object[] arguments)
    {
        var selected = Languages.Single(language => language.Code == Code);
        var value = selected.Texts.TryGetValue(key, out var translated) ? translated : fallback.Texts[key];
        return string.Format(CultureInfo.CurrentCulture, value, arguments);
    }

    public string Error(LauncherException error) => Text(error.Key, error.Arguments);
}
