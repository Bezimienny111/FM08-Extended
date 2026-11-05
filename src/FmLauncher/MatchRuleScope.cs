namespace FmLauncher;

internal sealed record RuleScopeExample(int Code, string NativeClass, string MatchType, uint AssignmentAddress,
    bool Conditional = false);

internal static class MatchRuleScope
{
    // Direct stage+0x31 assignments, linked to competition classes through MSVC RTTI.
    // These are examples from the supported executable, not an exhaustive career-specific mapping.
    internal static IReadOnlyList<RuleScopeExample> Examples { get; } = Array.AsReadOnly<RuleScopeExample>(
    [
        new(0, "ARG_PREMIER", "League", 0x00ED5C8E),
        new(0, "CHN_SUPER", "League", 0x00ECD33F),
        new(0, "GER_REGIONAL_DIVISION", "League", 0x00EDADFC),
        new(0, "MAL_CUP", "Cup", 0x00E5DEC8),
        new(1, "ENG_CONF2_REGION", "League", 0x00F07EEA),
        new(1, "FRE_SECOND", "League", 0x00EBB107),
        new(1, "FRE_NATIONAL", "League", 0x00EBADD7),
        new(1, "ARG_SECOND", "League", 0x00ED4D05),
        new(1, "ESP_SECOND_B_GROUP", "League", 0x00ECB1A6),
        new(1, "SWE_PREM", "League", 0x00EC3774),
        new(1, "NETWORK_LEAGUE", "Network", 0x00F16499),
        new(2, "WAL_PRM", "League", 0x00E76A20),
        new(2, "NIR_FIRST", "League", 0x00EB12F4),
        new(2, "NIR_SECOND", "League", 0x00EB1620),
        new(2, "WAL_LEAGUE_CUP", "Cup", 0x00E77525),
        new(3, "AUT_FIRST", "League", 0x00E8406E),
        new(3, "AUS_CHAL_CUP", "Cup", 0x00E41CE8),
        new(4, "CZE_FIRST", "League", 0x00E8B1D6),
        new(4, "COL_FIRST", "League", 0x00E6D62E),
        new(4, "COL_SECOND", "League", 0x00E6C00E),
        new(4, "AUT_PREM", "League", 0x00E84470),
        new(4, "IRE_ALL_IRELAND", "Cup", 0x00E9621B),
        new(4, "DAN_FIRST", "League", 0x00EBE4B0, true),
        new(5, "DAN_FIRST", "League", 0x00EBE1F2, true),
        new(5, "DAN_SECOND_GROUP", "League", 0x00EBEA36),
        new(6, "BEL_FIRST", "League", 0x00EEA5E5),
        new(6, "BEL_SECOND", "League", 0x00EEAC52),
        new(6, "AUS_NSL", "League", 0x00E413CD),
        new(8, "INTER_EURO_CHAMP", "International", 0x00F2A0AB),
        new(10, "ASI_CHAMPIONS_LEAGUE", "Continental", 0x00F11DF2),
        new(10, "ASI_ASEAN_CLUB_CHAMP", "Continental", 0x00F10C11),
        new(18, "USA_COMBINE", "Trial", 0x00EEF477),
        new(20, "UKR_FIRST", "League", 0x00E652F4),
        new(20, "FIN_LEAGUE_CUP", "Cup", 0x00EE753A),
        new(20, "ISL_UPPER_LEAGUE_CUP", "Cup", 0x00E4ED95),
        new(20, "ISL_LOWER_LEAGUE_CUP", "Cup", 0x00E4F316),
        new(21, "POL_LEAGUE_CUP", "Cup", 0x00E903C0),
        new(21, "RUS_FIRST", "League", 0x00E8CF13),
        new(21, "BLR_HIGHEST", "League", 0x00E54F5E),
        new(21, "ISR_PRM_TOTO_CUP", "Cup", 0x00E7AA5A),
        new(21, "ISR_FIRST_TOTO_CUP", "Cup", 0x00E7AFF7),
        new(25, "INTER_FIFA_CONFED", "International", 0x00F2D2F1),
        new(26, "KOR_LEAGUE", "League", 0x00EE2C6A, true),
        new(27, "KOR_LEAGUE", "League", 0x00EE258B, true),
        new(27, "KOR_LEAGUE_CUP", "Cup", 0x00EE3611)
    ]);

    internal static RuleScopeExample[] ForCode(int code)
    {
        _ = RuleCatalog.Original(code);
        return Examples.Where(example => example.Code == code).ToArray();
    }

    internal static string Summary(int code, Localizer localizer)
    {
        var examples = ForCode(code);
        return examples.Length == 0 ? localizer.Text("RuleScopeUnknown")
            : string.Join("; ", examples.Take(2).Select(example => localizer.Text("Scope_" + example.NativeClass)))
                + (examples.Length > 2 ? localizer.Text("RuleScopeMore", examples.Length - 2) : "");
    }

    internal static string Details(int code, Localizer localizer)
    {
        var examples = ForCode(code);
        return localizer.Text("RuleScopeHeading", code) + Environment.NewLine
            + (examples.Length == 0 ? localizer.Text("RuleScopeUnknownDetails")
                : string.Join(Environment.NewLine, examples.Select(example =>
                    localizer.Text("RuleScopeEntry", localizer.Text("Scope_" + example.NativeClass),
                        localizer.Text("RuleType" + example.MatchType),
                        example.Conditional ? localizer.Text("RuleScopeConditional") : "",
                        example.NativeClass, example.AssignmentAddress.ToString("X8")))));
    }
}
