using System.ComponentModel;
using System.Text;
using System.Text.Json;
using FmLauncher;

namespace FmLauncher.Tests;

internal static partial class Program
{
    private static void TestRuleScope(string directory, string languagePath)
    {
        var localizer = new Localizer(languagePath);
        Assert(MatchRuleScope.Examples.Count == 45);
        Assert(MatchRuleScope.Examples.Select(example => example.AssignmentAddress).Distinct().Count() == 45);
        Assert(MatchRuleScope.ForCode(21).Any(example => example.NativeClass == "POL_LEAGUE_CUP"));
        Assert(MatchRuleScope.ForCode(1).Any(example => example.NativeClass == "ENG_CONF2_REGION"));
        Assert(MatchRuleScope.ForCode(18).Single().MatchType == "Trial");
        Assert(MatchRuleScope.ForCode(4).Any(example => example.NativeClass == "DAN_FIRST" && example.Conditional));
        Assert(MatchRuleScope.ForCode(5).Any(example => example.NativeClass == "DAN_FIRST" && example.Conditional));
        using var form = new MainForm(directory, localizer, _ => new[] { Hd });
        form.Show();
        form.Populate(Default(), new[] { Hd });
        var tabs = Descendants(form).OfType<TabControl>().Single();
        ShowFeature(form, "MatchRulesFeature");
        var grid = Descendants(form).OfType<DataGridView>().Single();
        var details = Descendants(form).OfType<TextBox>().Single(control => control.Name == "RuleScopeDetails");
        Assert(grid.Columns["RuleScope"].ReadOnly && details.ReadOnly && details.Multiline);
        var before = JsonSerializer.Serialize(form.CaptureConfiguration().Rules);
        foreach (var language in new[] { "en", "pl" })
        {
            form.ApplyLanguage(language);
            foreach (var direction in new[] { ListSortDirection.Ascending, ListSortDirection.Descending })
            {
                grid.Sort(grid.Columns["RuleScope"], direction);
                foreach (var code in Enumerable.Range(0, 29))
                {
                    var row = grid.Rows.Cast<DataGridViewRow>().Single(r => (int)r.Cells["Code"].Value == code);
                    grid.CurrentCell = row.Cells["RuleScope"];
                    Application.DoEvents();
                    Assert((string)row.Cells["RuleScope"].Value == MatchRuleScope.Summary(code, localizer));
                    Assert(details.Text == MatchRuleScope.Details(code, localizer));
                    Assert(row.Cells["RuleScope"].ToolTipText == details.Text);
                    foreach (var example in MatchRuleScope.ForCode(code))
                    {
                        Assert(details.Text.Contains(localizer.Text("Scope_" + example.NativeClass)));
                        Assert(details.Text.Contains(localizer.Text("RuleType" + example.MatchType)));
                        Assert(details.Text.Contains(example.NativeClass));
                        Assert(details.Text.Contains(example.AssignmentAddress.ToString("X8")));
                    }
                    if (MatchRuleScope.ForCode(code).Length == 0)
                    {
                        Assert((string)row.Cells["RuleScope"].Value == localizer.Text("RuleScopeUnknown"));
                        Assert(details.Text.Contains(localizer.Text("RuleScopeUnknownDetails")));
                    }
                }
                Assert(JsonSerializer.Serialize(form.CaptureConfiguration().Rules) == before);
            }
            foreach (var size in new[] { new Size(1000, 900), form.MinimumSize })
            {
                form.Size = size;
                Application.DoEvents();
                Assert(details.Width > 200 && details.Height >= 100);
                Assert(details.Parent!.Width <= tabs.TabPages["Settings"]!.ClientSize.Width);
                Assert(Descendants(form).OfType<Label>().Any(label => label.Text == localizer.Text("RuleScopeNotice")));
            }
        }
        form.Close();
    }

    private static void TestRuleScopeNative(string gamePath)
    {
        using var verified = MatchRulePatch.OpenVerifiedGame(gamePath);
        using var buffer = new MemoryStream();
        verified.CopyTo(buffer);
        var bytes = buffer.ToArray();
        foreach (var example in MatchRuleScope.Examples)
        {
            var offset = checked((int)example.AssignmentAddress - 0x400000);
            Assert(bytes[offset] == 0xC6 && (bytes[offset + 1] & 0xF8) == 0x40
                && bytes[offset + 2] == 0x31 && bytes[offset + 3] == example.Code);
            Assert(bytes.AsSpan().IndexOf(Encoding.ASCII.GetBytes(".?AV" + example.NativeClass + "@@\0")) >= 0);
        }
        // Stage+0x31 -> fixture+0x70 -> match+0x5F278; getters consume that same code.
        Assert(bytes.AsSpan(0xDBF60E - 0x400000, 6).SequenceEqual(new byte[] { 0x8A, 0x48, 0x31, 0x88, 0x4F, 0x70 }));
        Assert(bytes.AsSpan(0x6D8FCA - 0x400000, 11)
            .SequenceEqual(new byte[] { 0x8A, 0x47, 0x70, 0x6A, 0, 0x88, 0x86, 0x78, 0xF2, 5, 0 }));
    }
}
