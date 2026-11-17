using System.ComponentModel;
using System.Text.Json;
using FmLauncher;

namespace FmLauncher.Tests;

internal static partial class Program
{
    private static void TestRuleGroups()
    {
        var config = Default();
        Assert(MatchRuleGroups.ForCode(1).SequenceEqual(new[] { 1, 3, 11, 12, 13, 14 }));
        Assert(MatchRuleGroups.ForCode(0).SequenceEqual(new[] { 0, 4 }));
        Assert(MatchRuleGroups.ForCode(7).SequenceEqual(new[] { 7, 15, 27 }));
        Assert(MatchRuleGroups.ForCode(22).SequenceEqual(new[] { 22 }));
        Assert(MatchRuleGroups.ForCode(28).SequenceEqual(new[] { 28 }));
        var source = config.Rules.Single(rule => rule.Code == 1);
        source.Override = true; source.Substitutions = 5;
        source.BenchOverride = false; source.Bench = 7;
        var unrelated = JsonSerializer.Serialize(config.Rules.Where(rule => !MatchRuleGroups.ForCode(1).Contains(rule.Code)));
        Assert(MatchRuleGroups.Mixed(config.Rules.Where(rule => MatchRuleGroups.ForCode(1).Contains(rule.Code))));
        MatchRuleGroups.CopyFrom(config.Rules, 1);
        Assert(!MatchRuleGroups.Mixed(config.Rules.Where(rule => MatchRuleGroups.ForCode(1).Contains(rule.Code))));
        Assert(config.Rules.Where(rule => MatchRuleGroups.ForCode(1).Contains(rule.Code))
            .All(rule => rule.Override && rule.Substitutions == 5 && !rule.BenchOverride && rule.Bench == 7));
        Assert(JsonSerializer.Serialize(config.Rules.Where(rule => !MatchRuleGroups.ForCode(1).Contains(rule.Code))) == unrelated);
        ConfigurationValidator.Validate(config);
        var payload = MatchRulePatch.BuildPayload(0x10000000, config.Rules, RuleLimit.Substitutions);
        var bench = MatchRulePatch.BuildPayload(0x10001000, config.Rules, RuleLimit.Bench);
        foreach (var code in Enumerable.Range(0, 29))
        {
            Assert(payload[code] == (MatchRuleGroups.ForCode(1).Contains(code) ? 1 : 0));
            Assert(bench[code] == 0);
        }
        var scope = MatchRuleScope.ForCode(1).Select(example => example.NativeClass).ToArray();
        Assert(scope.Contains("ENG_CONF2_REGION") && !scope.Contains("AUT_FIRST"));
        Assert(MatchRuleScope.ForCode(3).Any(example => example.NativeClass == "AUT_FIRST"));
        source.BenchOverride = true; source.Bench = 13;
        var before = JsonSerializer.Serialize(config.Rules);
        Reject(() => MatchRuleGroups.CopyFrom(config.Rules, 1), "InvalidBenchLimit");
        Assert(before == JsonSerializer.Serialize(config.Rules));
        Reject(() => MatchRuleGroups.CopyFrom(config.Rules.Take(28).ToArray(), 1), "InvalidRules");
    }

    private static void TestLaunchJournal(string directory)
    {
        var localizer = new Localizer(Path.Combine(AppContext.BaseDirectory, "FmLauncher.languages.json"));
        var journal = new LaunchJournal();
        journal.Begin(null);
        Assert(journal.Entries.Count(entry => entry.Key == "LaunchLogDisabled") == 2);
        var config = Default();
        config.Rules[4].BenchOverride = true;
        config.Rules[4].Bench = 9;
        journal.Begin(config.Rules);
        Assert(journal.Entries.Any(entry => entry.Key == "LaunchLogOriginal" && (RuleLimit)entry.Arguments[0] == RuleLimit.Substitutions));
        Assert(journal.Entries.Any(entry => entry.Key == "LaunchLogRequested" && (RuleLimit)entry.Arguments[0] == RuleLimit.Bench));
        journal.Rule(RuleLimit.Bench, RuleHookStatus.Installing);
        Assert(!journal.Entries.Any(entry => entry.Key == "LaunchLogVerified"));
        var address = 0x10001000u;
        var payload = MatchRulePatch.BuildPayload(address, config.Rules, RuleLimit.Bench);
        var jump = MatchRulePatch.BuildEntryJump(address + 64, RuleLimit.Bench);
        byte[] Read(uint site, int size) => (site == address ? payload : jump).Take(size).ToArray();
        SuspendedGameProcess.VerifyRuleInstallation(address, payload, jump, RuleLimit.Bench, Read);
        Reject(() => SuspendedGameProcess.VerifyRuleInstallation(address, payload, jump, RuleLimit.Bench,
            (site, size) => new byte[size]), "UnexpectedGameMemory");
        Reject(() => SuspendedGameProcess.VerifyRuleInstallation(address, payload, jump, RuleLimit.Bench,
            (site, size) => site == address ? new byte[size] : jump), "UnexpectedGameMemory");
        journal.Rule(RuleLimit.Bench, RuleHookStatus.Verified);
        journal.Failed(new LauncherException("UnexpectedGameMemory"));
        using var window = new Form { Size = new Size(700, 360) };
        using var panel = new LaunchLogPanel(localizer, journal) { Expanded = true };
        window.Controls.Add(panel);
        window.Show();
        foreach (var language in new[] { "en", "pl" })
        {
            localizer.Select(language);
            panel.ApplyLanguage();
            Application.DoEvents();
            var text = Descendants(window).OfType<TextBox>().Single();
            Assert(text.ReadOnly && text.Multiline);
            Assert(text.Text.Contains(localizer.Text("Bench")));
            Assert(text.Text.Contains(localizer.Text("Substitutions")));
            Assert(text.Text.Contains(localizer.Text("LaunchLogFailed", localizer.Text("UnexpectedGameMemory"))));
            Assert(Descendants(window).OfType<Label>().Any(label => label.Text == localizer.Text("LaunchLogPanelEvidence")));
        }
        window.Close();
        using var launcher = new GameLauncher();
        config.GamePath = Path.Combine(directory, "nonexistent.exe");
        config.DisplayOverride = false;
        config.PanelInformationEnabled = false;
        Reject(() => launcher.Launch(config), "InvalidGamePath");
        Assert(launcher.LaunchJournal.Entries.Last().Key == "LaunchLogFailed" && !launcher.IsRunning);
        Assert(!launcher.LaunchJournal.Entries.Any(entry => entry.Key == "LaunchLogVerified"));
    }

    private static void TestRuleGroupUi(string directory)
    {
        var localizer = new Localizer(Path.Combine(AppContext.BaseDirectory, "FmLauncher.languages.json"));
        using var form = new MainForm(directory, localizer, _ => new[] { Hd });
        form.Show();
        var config = Default();
        config.Rules[1].Override = true;
        config.Rules[1].Substitutions = 5;
        config.Rules[1].BenchOverride = true;
        config.Rules[1].Bench = 9;
        config.Rules[3].Override = true;
        config.Rules[3].Substitutions = 4;
        var before = JsonSerializer.Serialize(config.Rules);
        form.Populate(config, new[] { Hd });
        ShowFeature(form, "MatchRulesFeature");
        var grid = Descendants(form).OfType<DataGridView>().Single();
        var view = Descendants(form).OfType<ComboBox>().Single(control => control.Name == "RuleEditView");
        var groups = Descendants(form).OfType<ListView>().Single(control => control.Name == "RuleGroups");
        var subAction = Descendants(form).OfType<ComboBox>().Single(control => control.Name == "GroupSubstitutionsAction");
        var benchAction = Descendants(form).OfType<ComboBox>().Single(control => control.Name == "GroupBenchAction");
        var benchValue = Descendants(form).OfType<NumericUpDown>().Single(control => control.Name == "GroupBenchValue");
        var apply = Descendants(form).OfType<Button>().Single(button => button.Name == "ApplyGroupedChanges");
        grid.Sort(grid.Columns["Code"], ListSortDirection.Descending);
        foreach (var language in new[] { "en", "pl" })
        {
            form.ApplyLanguage(language);
            foreach (var index in new[] { 1, 0, 1 })
            {
                view.SelectedIndex = index;
                Application.DoEvents();
                Assert(JsonSerializer.Serialize(form.CaptureConfiguration().Rules) == before);
                Assert(grid.Visible == (index == 0) && groups.Visible == (index == 1));
                if (index == 1)
                    Assert(Descendants(form).OfType<TextBox>().Single(control => control.Name == "RuleScopeDetails")
                        .Text.Contains(localizer.Text("Scope_ARG_PREMIER")));
            }
        }
        Assert(groups.Items.Count == 20);
        Assert(groups.Items.Cast<ListViewItem>().SelectMany(item => (int[])item.Tag!).Order()
            .SequenceEqual(Enumerable.Range(0, 29)));
        var selected = groups.Items.Cast<ListViewItem>().Single(item => ((int[])item.Tag!).Contains(1));
        selected.Selected = true;
        Application.DoEvents();
        Assert(selected.SubItems[2].Text == localizer.Text("GroupMixed"));
        Assert(!apply.Enabled && subAction.SelectedIndex == 0 && benchAction.SelectedIndex == 0);
        var scope = Descendants(form).OfType<TextBox>().Single(control => control.Name == "RuleScopeDetails");
        Assert(scope.Text.Contains("ENG_CONF2_REGION") && scope.Text.Contains("AUT_FIRST"));
        benchAction.SelectedIndex = (int)GroupRuleAction.Override;
        benchValue.Value = 11;
        Assert(apply.Enabled);
        apply.PerformClick();
        var result = form.CaptureConfiguration();
        Assert(result.Rules.Count == 29);
        Assert(result.Rules.Where(rule => MatchRuleGroups.ForCode(1).Contains(rule.Code))
            .All(rule => rule.BenchOverride && rule.Bench == 11));
        Assert(result.Rules[1].Override && result.Rules[1].Substitutions == 5);
        Assert(result.Rules[3].Override && result.Rules[3].Substitutions == 4);
        Assert(!result.Rules[11].Override && result.Rules[11].Substitutions == 3);
        Assert(!result.Rules[0].BenchOverride);
        var isolated = groups.Items.Cast<ListViewItem>().Single(item => ((int[])item.Tag!).Contains(22));
        Assert(((int[])isolated.Tag!).Length == 1);
        Assert(((int[])groups.Items.Cast<ListViewItem>().Single(item => ((int[])item.Tag!).Contains(28)).Tag!).Length == 1);
        var store = new ConfigurationStore(Path.Combine(directory, "group-roundtrip.json"));
        store.Save(result);
        Assert(JsonSerializer.Serialize(store.Load()!.Rules) == JsonSerializer.Serialize(result.Rules));
        var frozen = JsonSerializer.Serialize(result.Rules);
        Reject(() => MatchRuleGroups.Apply(result.Rules, 1, new(GroupRuleAction.Original, 0),
            new(GroupRuleAction.Override, 13)), "InvalidBenchLimit");
        Assert(frozen == JsonSerializer.Serialize(result.Rules));
        MatchRuleGroups.Apply(result.Rules, 1, new(GroupRuleAction.Original, 0), new(GroupRuleAction.Unchanged, 0));
        Assert(result.Rules[1].Substitutions == 5 && !result.Rules[1].Override && result.Rules[1].Bench == 11);
        form.Close();
    }
}
