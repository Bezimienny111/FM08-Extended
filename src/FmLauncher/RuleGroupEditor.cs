namespace FmLauncher;

/// <summary>Groups only the two editable limits; other native behavior remains independent.</summary>
internal sealed class RuleGroupEditor : UserControl
{
    private readonly Localizer localizer;
    private readonly ListView groups = new ThemedListView()
    {
        Name = "RuleGroups", Dock = DockStyle.Top, Height = 230, View = View.Details,
        FullRowSelect = true, MultiSelect = false, HideSelection = false, HeaderStyle = ColumnHeaderStyle.Nonclickable
    };
    private readonly ComboBox substitutionsAction = Choice("GroupSubstitutionsAction");
    private readonly ComboBox benchAction = Choice("GroupBenchAction");
    private readonly NumericUpDown substitutionsValue = Number("GroupSubstitutionsValue");
    private readonly NumericUpDown benchValue = Number("GroupBenchValue");
    private readonly Button apply = new() { Name = "ApplyGroupedChanges", AutoSize = true, Anchor = AnchorStyles.Right };
    private readonly Label selection = new() { Name = "SelectedRuleGroup", AutoSize = true, Dock = DockStyle.Top };
    private readonly Label hint = new() { Name = "GroupedRulesNotice", AutoSize = true, Dock = DockStyle.Top };
    private readonly Label substitutionsLabel = new() { AutoSize = true, Anchor = AnchorStyles.Left };
    private readonly Label benchLabel = new() { AutoSize = true, Anchor = AnchorStyles.Left };
    private readonly Dictionary<int, RuleSettings> rules = [];
    private bool updating;
    internal event Action? SelectionChanged;
    internal event Action<int, GroupRuleChange, GroupRuleChange>? ApplyRequested;
    internal int[] SelectedCodes => groups.SelectedItems.Count == 0 ? []
        : (int[])groups.SelectedItems[0].Tag!;

    internal RuleGroupEditor(Localizer localizer)
    {
        this.localizer = localizer;
        Name = "GroupedRulesView";
        Dock = DockStyle.Top;
        AutoSize = true;
        AutoSizeMode = AutoSizeMode.GrowAndShrink;
        foreach (var key in new[] { "Original", "GroupCodes", "Substitutions", "Bench" })
            groups.Columns.Add(new ColumnHeader { Name = key });
        var stack = new TableLayoutPanel
        {
            ColumnCount = 1, Dock = DockStyle.Top, AutoSize = true, AutoSizeMode = AutoSizeMode.GrowAndShrink,
            Margin = Padding.Empty
        };
        stack.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        stack.Controls.Add(groups);
        stack.Controls.Add(selection);
        var editors = new TableLayoutPanel
        {
            Name = "GroupedRuleEditors", Dock = DockStyle.Top, AutoSize = true, ColumnCount = 4
        };
        editors.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
        editors.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        editors.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 85));
        editors.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
        editors.Controls.Add(substitutionsLabel, 0, 0);
        editors.Controls.Add(substitutionsAction, 1, 0);
        editors.Controls.Add(substitutionsValue, 2, 0);
        editors.Controls.Add(benchLabel, 0, 1);
        editors.Controls.Add(benchAction, 1, 1);
        editors.Controls.Add(benchValue, 2, 1);
        editors.Controls.Add(apply, 3, 1);
        stack.Controls.Add(editors);
        stack.Controls.Add(hint);
        Controls.Add(stack);
        groups.SelectedIndexChanged += (_, _) =>
        {
            if (updating) return;
            ResetEditors();
            SelectionChanged?.Invoke();
        };
        groups.SizeChanged += (_, _) => SizeColumns();
        substitutionsAction.SelectedIndexChanged += (_, _) => UpdateActions();
        benchAction.SelectedIndexChanged += (_, _) => UpdateActions();
        apply.Click += (_, _) =>
        {
            if (SelectedCodes.Length == 0) return;
            ApplyRequested?.Invoke(SelectedCodes[0],
                new((GroupRuleAction)substitutionsAction.SelectedIndex, (int)substitutionsValue.Value),
                new((GroupRuleAction)benchAction.SelectedIndex, (int)benchValue.Value));
        };
        SizeChanged += (_, _) => hint.MaximumSize = new Size(Math.Max(200, ClientSize.Width - 10), 0);
        ApplyLanguage();
    }

    private static ComboBox Choice(string name) => new ThemedComboBox
    {
        Name = name, DropDownStyle = ComboBoxStyle.DropDownList, Dock = DockStyle.Fill,
        MinimumSize = new Size(140, 0)
    };
    private static NumericUpDown Number(string name) => new()
    {
        Name = name, Minimum = 0, Maximum = 12, Width = 74, Enabled = false, Anchor = AnchorStyles.Left
    };

    internal void ApplyLanguage()
    {
        updating = true;
        try
        {
            foreach (ColumnHeader column in groups.Columns) column.Text = localizer.Text(column.Name!);
            foreach (var choice in new[] { substitutionsAction, benchAction })
            {
                var index = Math.Max(0, choice.SelectedIndex);
                choice.Items.Clear();
                choice.Items.AddRange(new object[] { localizer.Text("GroupActionUnchanged"),
                    localizer.Text("GroupActionOriginal"), localizer.Text("GroupActionOverride") });
                choice.SelectedIndex = index;
            }
            substitutionsLabel.Text = localizer.Text("Substitutions");
            benchLabel.Text = localizer.Text("Bench");
            apply.Text = localizer.Text("ApplyGroupedChanges");
            hint.Text = localizer.Text("GroupedRulesNotice");
            RefreshRows();
            UpdateSelectionText();
        }
        finally { updating = false; }
        UpdateActions();
        SizeColumns();
    }

    internal void Populate(IReadOnlyList<RuleSettings> values)
    {
        var previous = SelectedCodes.FirstOrDefault(-1);
        updating = true;
        try
        {
            rules.Clear();
            foreach (var rule in values) rules.Add(rule.Code, rule);
            groups.BeginUpdate();
            groups.Items.Clear();
            foreach (var code in Enumerable.Range(0, 29).Where(code => MatchRuleGroups.ForCode(code)[0] == code))
            {
                var codes = MatchRuleGroups.ForCode(code);
                var item = new ListViewItem("") { Tag = codes };
                item.SubItems.AddRange(new[] { string.Join(", ", codes), "", "" });
                groups.Items.Add(item);
                if (codes.Contains(previous)) item.Selected = true;
            }
            RefreshRows();
            if (groups.SelectedItems.Count == 0 && groups.Items.Count > 0)
                groups.Items[0].Selected = true;
        }
        finally
        {
            groups.EndUpdate();
            updating = false;
        }
        ResetEditors();
        SelectionChanged?.Invoke();
    }

    private void RefreshRows()
    {
        foreach (ListViewItem item in groups.Items)
        {
            var codes = (int[])item.Tag!;
            var original = RuleCatalog.Original(codes[0]);
            item.Text = original is { } value ? $"{value.Substitutions} / {value.Bench}"
                : localizer.Text(codes[0] == 22 ? "OriginalRule22" : "OriginalRule28");
            var members = codes.Where(rules.ContainsKey).Select(code => rules[code]).ToArray();
            item.SubItems[2].Text = Summary(members, RuleLimit.Substitutions);
            item.SubItems[3].Text = Summary(members, RuleLimit.Bench);
        }
    }

    private string Summary(RuleSettings[] members, RuleLimit limit)
    {
        if (members.Length == 0) return "";
        var values = members.Select(rule => (Enabled: MatchRulePatch.Enabled(rule, limit),
            Value: limit == RuleLimit.Substitutions ? rule.Substitutions : rule.Bench)).Distinct().ToArray();
        return values.Length > 1 ? localizer.Text("GroupMixed")
            : values[0].Enabled ? localizer.Text("GroupValue", values[0].Value) : localizer.Text("GroupOriginal");
    }

    private void ResetEditors()
    {
        updating = true;
        try
        {
            substitutionsAction.SelectedIndex = benchAction.SelectedIndex = 0;
            var code = SelectedCodes.FirstOrDefault(-1);
            var original = code >= 0 ? RuleCatalog.Original(code) : null;
            substitutionsValue.Value = original?.Substitutions ?? 3;
            benchValue.Value = original?.Bench ?? 7;
            UpdateSelectionText();
        }
        finally { updating = false; }
        UpdateActions();
    }

    private void UpdateSelectionText() => selection.Text = localizer.Text("RuleGroupSummary", string.Join(", ", SelectedCodes));

    private void UpdateActions()
    {
        if (updating) return;
        substitutionsValue.Enabled = substitutionsAction.SelectedIndex == (int)GroupRuleAction.Override;
        benchValue.Enabled = benchAction.SelectedIndex == (int)GroupRuleAction.Override;
        apply.Enabled = SelectedCodes.Length > 0
            && (substitutionsAction.SelectedIndex > 0 || benchAction.SelectedIndex > 0);
    }

    private void SizeColumns()
    {
        var width = Math.Max(300, groups.ClientSize.Width - SystemInformation.VerticalScrollBarWidth - 5);
        groups.Columns[0].Width = Math.Max(100, width * 21 / 100);
        groups.Columns[1].Width = Math.Max(125, width * 29 / 100);
        groups.Columns[2].Width = width * 25 / 100;
        groups.Columns[3].Width = width - groups.Columns[0].Width - groups.Columns[1].Width - groups.Columns[2].Width;
    }
}
