using System.Globalization;
using System.Reflection;

namespace FmLauncher;

internal enum AttributeEmphasis { Ordinary, Important, Key }

internal sealed record PositionHighlightRole(string Code, string Polish, string English)
{
    internal string Name(string language) => language == "pl" ? Polish : English;
}

/// <summary>Project display categories derived from the documented external Genie weights.
/// This is not an SI role definition, ability rating or prediction of development.</summary>
internal static class PositionHighlightModel
{
    internal const bool IntegrationReady = true;
    internal const int KeyMinimum = 60;
    internal const int ImportantMinimum = 20;
    internal static IReadOnlyList<PositionHighlightRole> Roles { get; } =
    [
        new("GK", "Bramkarz", "Goalkeeper"),
        new("SW", "Ostatni obrońca", "Sweeper"),
        new("DC", "Środkowy obrońca", "Centre-back"),
        new("DL_DR", "Boczny obrońca", "Full-back"),
        new("WBL_WBR", "Wahadłowy", "Wing-back"),
        new("DM", "Defensywny pomocnik", "Defensive midfielder"),
        new("MC", "Środkowy pomocnik", "Central midfielder"),
        new("AMC", "Ofensywny pomocnik", "Attacking midfielder"),
        new("ML_MR_AML_AMR", "Skrzydłowy", "Wide midfielder / winger"),
        new("FS", "Szybki napastnik", "Fast striker"),
        new("TS", "Napastnik odgrywający", "Target striker")
    ];
    private static readonly HashSet<string> Excluded = new(StringComparer.Ordinal)
    {
        "Scale", "CA", "Normalization_denominator", "LeftFoot", "RightFoot",
        "Consistency", "ImportantMatches", "InjuryProneness", "Dirtiness", "Versatility",
        "Adaptability", "Ambition", "Controversy", "Loyalty", "Pressure", "Professionalism",
        "Sportsmanship", "Temperament"
    };
    private static readonly IReadOnlyDictionary<string, IReadOnlyDictionary<string, int>> Weights = Load();

    internal static bool IsRole(string? role) => role is not null && Roles.Any(value => value.Code == role);
    internal static IReadOnlyCollection<string> VisibleAttributes => Weights.Keys.ToArray();

    internal static AttributeEmphasis Emphasis(string role, string attribute)
    {
        if (!IsRole(role)) throw new ArgumentException("Unknown position role.", nameof(role));
        if (!Weights.TryGetValue(attribute, out var values)) return AttributeEmphasis.Ordinary;
        var weight = values[role];
        return weight >= KeyMinimum ? AttributeEmphasis.Key
            : weight >= ImportantMinimum ? AttributeEmphasis.Important : AttributeEmphasis.Ordinary;
    }

    internal static IReadOnlyDictionary<string, int> AttributeWeights(string attribute) => Weights[attribute];

    private static IReadOnlyDictionary<string, IReadOnlyDictionary<string, int>> Load()
    {
        using var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(
            "FmLauncher.PositionAttributeWeights.csv") ?? throw new InvalidDataException("Missing position weights.");
        using var reader = new StreamReader(stream);
        var header = (reader.ReadLine() ?? throw new InvalidDataException("Missing position header.")).Split(';');
        var roles = header.Skip(2).ToArray();
        if (!roles.Order().SequenceEqual(Roles.Select(value => value.Code).Order()))
            throw new InvalidDataException("Position weight groups differ.");
        var result = new Dictionary<string, IReadOnlyDictionary<string, int>>(StringComparer.Ordinal);
        while (reader.ReadLine() is { } line)
        {
            if (string.IsNullOrWhiteSpace(line)) continue;
            var columns = line.Split(';');
            if (columns.Length != header.Length) throw new InvalidDataException("Position weight column count.");
            if (Excluded.Contains(columns[0])) continue;
            var values = new Dictionary<string, int>(StringComparer.Ordinal);
            for (var index = 0; index < roles.Length; index++)
            {
                var weight = int.Parse(columns[index + 2], CultureInfo.InvariantCulture);
                if (weight is < 0 or > 100) throw new InvalidDataException("Invalid visible attribute weight.");
                values.Add(roles[index], weight);
            }
            result.Add(columns[0], values);
        }
        return result;
    }
}

internal sealed record PlayerProfilePanelOptions(bool PositionHighlightsEnabled = false,
    bool HiddenAttributesEnabled = false, string PositionRole = "DC")
{
    internal static PlayerProfilePanelOptions From(LauncherConfiguration configuration) =>
        new(configuration.PositionHighlightsEnabled, configuration.HiddenAttributesEnabled);

    internal void Validate()
    {
        if (!PositionHighlightModel.IsRole(PositionRole)) throw new LauncherException("InvalidPositionHighlightRole");
    }
}
