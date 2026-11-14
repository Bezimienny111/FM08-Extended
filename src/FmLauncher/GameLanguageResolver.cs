using System.Security;
using System.Xml;
using System.Xml.Linq;

namespace FmLauncher;

internal sealed record GameLanguageSelection(string PreferencePath, string? NativeLanguage,
    string PanelLanguage, bool Fallback, string SourceStatus);

/// <summary>FM08's saved language, independent of launcher UI language. Never writes preferences.</summary>
internal static class GameLanguageResolver
{
    internal static string PreferencePath => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
        "Sports Interactive", "Football Manager 2008", "settings", "Version 800", "current_language.xml");

    internal static GameLanguageSelection Resolve(string? preferencePath = null)
    {
        var path = preferencePath ?? PreferencePath;
        GameLanguageSelection Unknown(string status) => new(path, null, "en", true, status);
        try
        {
            using var stream = new FileStream(path, FileMode.Open, FileAccess.Read,
                FileShare.ReadWrite | FileShare.Delete);
            if (stream.Length > 65536) return Unknown("oversized");
            using var reader = XmlReader.Create(stream, new XmlReaderSettings
            {
                DtdProcessing = DtdProcessing.Prohibit, XmlResolver = null,
                MaxCharactersInDocument = 65536, MaxCharactersFromEntities = 0
            });
            var xml = XDocument.Load(reader);
            if (xml.Root?.Name != "record") return Unknown("invalid-root");
            var values = xml.Root.Elements("string").Where(e => (string?)e.Attribute("id") == "valu").ToArray();
            if (values.Length != 1 || string.IsNullOrWhiteSpace((string?)values[0].Attribute("value")))
                return Unknown("missing-or-ambiguous-value");
            var name = ((string)values[0].Attribute("value")!).Trim();
            return new(path, name, name.Equals("polish", StringComparison.OrdinalIgnoreCase) ? "pl" : "en",
                false, "saved-preference");
        }
        catch (FileNotFoundException) { return Unknown("missing"); }
        catch (DirectoryNotFoundException) { return Unknown("missing"); }
        catch (Exception error) when (error is IOException or UnauthorizedAccessException or XmlException
            or SecurityException or ArgumentException or NotSupportedException)
        {
            return Unknown("unreadable-or-invalid");
        }
    }

    internal static Localizer CreatePanelLocalizer(Localizer? ui = null, string? preferencePath = null)
    {
        var source = ui ?? new Localizer(Path.Combine(AppContext.BaseDirectory, "FmLauncher.languages.json"));
        return source.Fork(Resolve(preferencePath).PanelLanguage);
    }
}
