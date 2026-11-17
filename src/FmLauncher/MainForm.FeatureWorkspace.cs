using System.Globalization;

namespace FmLauncher;

internal sealed partial class MainForm
{
    private readonly Dictionary<FeatureSection, Control> featureContents = [];
    private readonly SectionBox sharedDetails = new() { Name = "SharedFeatureDetails", Dock = DockStyle.Fill, Padding = new Padding(10, 27, 10, 10) };
    private readonly Panel detailsScroll = new() { Name = "FeatureDetailsScroll", Dock = DockStyle.Fill, AutoScroll = true };
    private readonly TableLayoutPanel detailsContents = Stack();
    private TableLayoutPanel? featureSelectors;
    private TableLayoutPanel? featureWorkspace;
    private FeatureSection? selectedFeature;
    private bool arrangingDetails;
    private readonly ComboBox bulkSubstitutionsAction = Choice();
    private readonly ComboBox bulkBenchAction = Choice();
    private readonly NumericUpDown bulkSubstitutions = new() { Name = "BulkSubstitutionsValue", Minimum = 0, Maximum = 12, Value = 5, Width = 65 };
    private readonly NumericUpDown bulkBench = new() { Name = "BulkBenchValue", Minimum = 0, Maximum = 12, Value = 9, Width = 65 };

    private Control CreateBulkRulesEditor()
    {
        var box = new SectionBox { Name = "BulkRules", Dock = DockStyle.Top, AutoSize = true, Padding = new Padding(10, 25, 10, 10), Margin = new Padding(0, 4, 0, 12) };
        captions.Add(box, "BulkRulesTitle");
        var body = Stack();
        bulkSubstitutionsAction.Name = "BulkSubstitutionsAction";
        bulkBenchAction.Name = "BulkBenchAction";
        bulkSubstitutionsAction.Width = bulkBenchAction.Width = 150;
        bulkSubstitutionsAction.SelectedIndexChanged += (_, _) => bulkSubstitutions.Enabled = bulkSubstitutionsAction.SelectedIndex == 2;
        bulkBenchAction.SelectedIndexChanged += (_, _) => bulkBench.Enabled = bulkBenchAction.SelectedIndex == 2;
        body.Controls.Add(Row(CaptionLabel("Substitutions"), bulkSubstitutionsAction, bulkSubstitutions,
            CaptionLabel("Bench"), bulkBenchAction, bulkBench));
        var all = Button("BulkApplyAll", () => ApplyBulkChanges(true));
        all.Name = "BulkApplyAll";
        var selected = Button("BulkApplySelected", () => ApplyBulkChanges(false));
        selected.Name = "BulkApplySelected";
        body.Controls.Add(Row(all, selected));
        body.Controls.Add(Notice("BulkRulesNotice"));
        box.Controls.Add(body);
        return box;
    }

    private void BuildFeatureWorkspace(TableLayoutPanel body)
    {
        static IEnumerable<FeatureSection> Find(Control parent) => parent.Controls.Cast<Control>()
            .SelectMany(child => child is FeatureSection section ? new[] { section } : Find(child));
        var all = features.Concat(Find(leagueReputation)).ToArray();
        var selectors = new TableLayoutPanel
        {
            Name = "FeatureSelectors", Dock = DockStyle.Top, AutoSize = true,
            ColumnCount = 2, Margin = new Padding(0, 3, 0, 8)
        };
        selectors.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
        selectors.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
        featureSelectors = selectors;
        featureWorkspace = body;
        var navigation = new SectionBox
        {
            Name = "FeatureNavigation", Dock = DockStyle.Fill,
            Padding = new Padding(10, 27, 10, 8), Margin = new Padding(0, 0, 0, 10)
        };
        captions.Add(navigation, "FeaturesTitle");
        var selectorScroll = new Panel { Name = "FeatureSelectorsScroll", Dock = DockStyle.Fill, AutoScroll = true };
        selectorScroll.Controls.Add(selectors);
        selectorScroll.SizeChanged += (_, _) => UpdateFeatureSelectorLayout();
        detailsContents.Name = "FeatureDetailsContents";
        detailsScroll.Controls.Add(detailsContents);
        detailsScroll.SizeChanged+=(_,_)=>UpdateDetailsLayout();
        sharedDetails.Controls.Add(detailsScroll);
        for (var index = 0; index < all.Length; index++)
        {
            var feature = all[index];
            var content = feature.UseSharedDetails(ShowFeatureDetails);
            content.Visible = false;
            featureContents.Add(feature, content);
            detailsContents.Controls.Add(content);
            selectors.Controls.Add(feature, index % 2, index / 2);
        }
        body.Controls.Clear();
        body.AutoSize = false;
        body.Dock = DockStyle.Fill;
        body.RowCount = 2;
        body.Padding = Padding.Empty;
        body.RowStyles.Clear();
        body.RowStyles.Add(new RowStyle(SizeType.Absolute, 205));
        body.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        if (body.Parent is Panel parent) parent.AutoScroll = false;
        navigation.Controls.Add(selectorScroll);
        body.Controls.Add(navigation, 0, 0);
        body.Controls.Add(sharedDetails, 0, 1);
        ShowFeatureDetails(all.Single(feature => feature.Name == "MatchRulesFeature"));
        UpdateFeatureSelectorLayout();
    }

    private void UpdateFeatureSelectorLayout()
    {
        if (featureSelectors is null || featureWorkspace is null) return;
        var columns = featureWorkspace.ClientSize.Width >= 1100 ? 3 : 2;
        var cards = featureContents.Keys.Where(feature => advancedMode.Checked || feature.Name is not ("LeagueObservationFeature" or "LeagueDiagnosticsFeature")).ToArray();
        featureSelectors.SuspendLayout();
        featureSelectors.ColumnCount = columns;
        featureSelectors.ColumnStyles.Clear();
        for (var i = 0; i < columns; i++) featureSelectors.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100f / columns));
        for (var i = 0; i < cards.Length; i++) featureSelectors.SetCellPosition(cards[i], new TableLayoutPanelCellPosition(i % columns, i / columns));
        featureSelectors.ResumeLayout(true);
        var rows = (cards.Length + columns - 1) / columns;
        var wanted = rows * 58 + 46;
        featureWorkspace.RowStyles[0].Height = Math.Min(wanted, Math.Max(130, featureWorkspace.ClientSize.Height * .43f));
    }

    private void ShowFeatureDetails(FeatureSection feature)
    {
        sharedDetails.SuspendLayout();
        foreach (var pair in featureContents)
        {
            pair.Value.Visible = pair.Key == feature;
            pair.Key.MarkSelected(pair.Key == feature);
        }
        selectedFeature = feature;
        sharedDetails.Text = feature.FeatureTitle;
        detailsScroll.AutoScrollPosition = Point.Empty;
        sharedDetails.ResumeLayout(true);
        UpdateDetailsLayout();
    }

    private void UpdateDetailsLayout()
    {
        if(arrangingDetails || detailsScroll.ClientSize.Width<=0)return;
        arrangingDetails=true;
        try
        {
            // Hidden descriptions were measured at the default200px width.
            // Reflow against the visible viewport each time details are selected.
            detailsContents.Width=detailsScroll.ClientSize.Width;
            detailsContents.PerformLayout();
            foreach(var content in featureContents.Values.Where(c=>c.Visible))content.PerformLayout();
            UpdateNoticeWidths();
            detailsContents.PerformLayout();
        }
        finally{arrangingDetails=false;}
    }

    private void RefreshFeatureWorkspaceLanguage()
    {
        foreach (var feature in featureContents.Keys) feature.RefreshLanguage();
        sharedDetails.Text = selectedFeature?.FeatureTitle ?? localizer.Text("Details");
        foreach (var combo in new[] { bulkSubstitutionsAction, bulkBenchAction })
        {
            var index = combo.SelectedIndex < 0 ? 2 : combo.SelectedIndex;
            combo.Items.Clear();
            combo.Items.AddRange(new object[] { localizer.Text("GroupActionUnchanged"), localizer.Text("GroupActionOriginal"), localizer.Text("GroupActionOverride") });
            combo.SelectedIndex = index;
        }
    }

    internal void ApplyBulkChanges(bool all)
    {
        if (!ValidateChildren() || !rules.EndEdit()) throw new LauncherException("InvalidGrid");
        var codes = all ? Enumerable.Range(0, 29).ToArray()
            : activeRuleView == 1 ? groupedRules.SelectedCodes.ToArray()
            : rules.SelectedRows.Cast<DataGridViewRow>().Select(row => (int)row.Cells["Code"].Value).ToArray();
        if (codes.Length == 0) { SetStatus("BulkNothingSelected"); return; }
        var substitutions = new GroupRuleChange((GroupRuleAction)bulkSubstitutionsAction.SelectedIndex, (int)bulkSubstitutions.Value);
        var bench = new GroupRuleChange((GroupRuleAction)bulkBenchAction.SelectedIndex, (int)bulkBench.Value);
        var config = CaptureConfiguration();
        MatchRuleGroups.ApplyCodes(config.Rules, codes, substitutions, bench);
        updating = true;
        try
        {
            foreach (DataGridViewRow row in rules.Rows)
            {
                var value = config.Rules.Single(rule => rule.Code == (int)row.Cells["Code"].Value);
                row.Cells["Override"].Value = value.Override;
                row.Cells["Substitutions"].Value = value.Substitutions;
                row.Cells["BenchOverride"].Value = value.BenchOverride;
                row.Cells["Bench"].Value = value.Bench;
                UpdateRuleEditing(row);
            }
        }
        finally { updating = false; }
        groupedRules.Populate(config.Rules);
        SyncEditors();
        UpdateRuleScope();
        SetStatus(matchRulesEnabled.Checked ? "BulkApplied" : "BulkAppliedDisabled", codes.Length);
    }
}
