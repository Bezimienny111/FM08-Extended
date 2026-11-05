using System.Globalization;
using System.ComponentModel;
using System.Diagnostics;

namespace FmLauncher;

internal sealed class MainForm : Form
{
    private readonly Localizer localizer;
    private readonly ConfigurationStore store;
    private readonly Func<DisplayMode, IReadOnlyList<Resolution>> detectDisplay;
    private readonly GameLauncher launcher = new();
    private readonly System.Windows.Forms.Timer timer = new() { Interval = 1000 };
    private readonly Dictionary<Control, string> captions = new();
    private readonly List<Label> wrappingLabels = new();
    private readonly ComboBox languages = Choice();
    private readonly TextBox gamePath = new() { Dock = DockStyle.Fill };
    private readonly TextBox userDataPath = new() { Name = "UserDataPath", Dock = DockStyle.Fill };
    private readonly ToolTip tooltips = new();
    private readonly List<FeatureSection> features = [];
    private readonly List<SocialLinkButton> socialLinks = [];
    private readonly Button themeMode = new() { Name = "ThemeMode", AutoSize = true, FlatStyle = FlatStyle.Flat };
    private bool darkMode;
    private readonly ToggleSwitch advancedMode = new()
    {
        Name = "AdvancedMode", Dock = DockStyle.Top, Margin = new Padding(13, 4, 10, 4)
    };
    private readonly Button paLogOpen;
    private readonly Label advancedNotice;
    private readonly TableLayoutPanel settingsContent;
    private readonly ToggleSwitch matchRulesEnabled = new() { Name = "MatchRulesEnabled" };
    private readonly ComboBox modes = Choice();
    private readonly ComboBox resolutions = Choice();
    private readonly ToggleSwitch displayEnabled = new() { Name = "DisplayOverride" };
    private readonly ToggleSwitch paEnabled = new() { Name = "PaEnabled" };
    private readonly ToggleSwitch agingDelay = new() { Name = "AgingDelayEnabled" };
    private readonly ToggleSwitch panelInformation = new() { Name = "PanelInformationEnabled" };
    private readonly SkinGuidePage skinGuide;
    private readonly LeagueReputationPage leagueReputation;
    private int legacyPaChance;
    private readonly Label paStatistics = new() { Name = "PaStatistics", AutoSize = true, Dock = DockStyle.Top };
    private readonly Label paLogStatus = new() { Name = "PaLogStatus", AutoSize = true, Dock = DockStyle.Top };
    private PaLogForm? paLogWindow;
    private readonly NumericUpDown substitutionsEditor = new()
    {
        Name = "SubstitutionsEditor", Minimum = 0, Maximum = 12, Width = 80, Enabled = false
    };
    private readonly NumericUpDown benchEditor = new()
    {
        Name = "BenchEditor", Minimum = 0, Maximum = 12, Width = 80, Enabled = false
    };
    private readonly Label selectedRule = new() { AutoSize = true, Margin = new Padding(3, 7, 8, 3) };
    private readonly TextBox ruleScope = new()
    {
        Name = "RuleScopeDetails", ReadOnly = true, Multiline = true, ScrollBars = ScrollBars.Vertical,
        Dock = DockStyle.Fill, BackColor = SystemColors.Window
    };
    private readonly DataGridView rules = new()
    {
        Dock = DockStyle.Fill, Height = 300, AutoGenerateColumns = false,
        AllowUserToAddRows = false, AllowUserToDeleteRows = false,
        AllowUserToOrderColumns = false, RowHeadersVisible = false,
        AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
        ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.AutoSize,
        SelectionMode = DataGridViewSelectionMode.CellSelect
    };
    private readonly Button save = new() { Name = "Save", AutoSize = true };
    private readonly FlowLayoutPanel configurationActions = Row();
    private readonly Button launch = new()
    {
        Name = "Play", Size = new Size(180, 44), FlatStyle = FlatStyle.Flat,
        BackColor = Color.FromArgb(32, 113, 207), ForeColor = Color.White,
        Anchor = AnchorStyles.None
    };
    private readonly Label status = new() { Name = "LauncherStatus", AutoSize = true, Dock = DockStyle.Top, TextAlign = ContentAlignment.MiddleCenter };
    private readonly LinkLabel profileBanner = new()
    {
        Name = "CareerProfileBanner", AutoSize = true, Dock = DockStyle.Top,
        Padding = new Padding(10, 7, 10, 7), Visible = false
    };
    private bool updating;
    private bool syncingEditors;
    private bool configurationBlocked;
    private string statusKey = "Ready";
    private object[] statusArguments = [];

    public MainForm(string directory, Localizer localizer, Func<DisplayMode, IReadOnlyList<Resolution>> detectDisplay)
    {
        this.localizer = localizer;
        this.detectDisplay = detectDisplay;
        store = new ConfigurationStore(Path.Combine(directory, "FmLauncher.config.json"));
        AutoScaleMode = AutoScaleMode.Dpi;
        Font = new Font("Segoe UI", 10);
        BackColor = Color.FromArgb(239, 242, 247);
        MinimumSize = new Size(720, 540);
        Size = new Size(1000, 900);
        StartPosition = FormStartPosition.CenterScreen;
        SuspendLayout();
        var tabs = new ThemedTabControl { Name = "FeatureTabs", Dock = DockStyle.Fill, ItemSize = new Size(150, 32) };
        var body = settingsContent = AddSettingsTab(tabs, "Settings", "SettingsTab");
        body.SuspendLayout();
        leagueReputation = new LeagueReputationPage(localizer, () => gamePath.Text.Trim(), Execute, directory, launcher,
            () => darkMode);
        skinGuide = new SkinGuidePage(localizer, () => gamePath.Text.Trim(), () => userDataPath.Text.Trim(), Execute,
            () => darkMode);
        tabs.TabPages.Add(skinGuide);
        Controls.Add(tabs);
        profileBanner.Click += (_, _) =>
        {
            tabs.SelectedIndex = 0;
            leagueReputation.ShowChanges();
            if (body.Parent is ScrollableControl scroll) scroll.ScrollControlIntoView(leagueReputation);
        };
        leagueReputation.ProfileStatusChanged += () =>
        {
            profileBanner.Visible = leagueReputation.ChangesEnabled;
            profileBanner.Text = leagueReputation.ProfileStatusText;
            profileBanner.BackColor = leagueReputation.ProfileStatusColor;
        };
        ClientSizeChanged += (_, _) => profileBanner.MaximumSize = new Size(Math.Max(200, ClientSize.Width - 36), 0);

        languages.Name = "LauncherLanguage";
        languages.Width = 160;
        languages.Items.AddRange(localizer.Languages.Cast<object>().ToArray());
        var header = new TableLayoutPanel
        {
            Name = "LauncherHeader", Dock = DockStyle.Top, AutoSize = true, ColumnCount = 2,
            Padding = new Padding(12, 8, 12, 8), BackColor = Color.White
        };
        header.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        header.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
        var title = CaptionLabel("Title");
        title.Name = "BrandTitle";
        title.Font = new Font(Font.FontFamily, 15, FontStyle.Bold);
        header.Controls.Add(title, 0, 0);
        themeMode.Click += (_, _) => ApplyTheme(!darkMode);
        var languageRow = Row(themeMode, CaptionLabel("Language"), languages);
        languageRow.WrapContents = false;
        languageRow.Anchor = AnchorStyles.Right;
        header.Controls.Add(languageRow, 1, 0);
        var browse = Button("Browse", () =>
        {
            using var dialog = new OpenFileDialog { Filter = localizer.Text("ExecutableFilter"), CheckFileExists = true };
            if (dialog.ShowDialog(this) == DialogResult.OK) gamePath.Text = dialog.FileName;
        });
        gamePath.Name = "GamePath";
        var pathRow = new TableLayoutPanel { Name = "GamePaths", AutoSize = true, Dock = DockStyle.Top, ColumnCount = 3, BackColor = Color.White, Padding = new Padding(10) };
        pathRow.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
        pathRow.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        pathRow.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
        pathRow.Controls.Add(CaptionLabel("GamePath"), 0, 0);
        pathRow.Controls.Add(new InputFrame(gamePath), 1, 0);
        pathRow.Controls.Add(browse, 2, 0);
        pathRow.Controls.Add(CaptionLabel("UserDataPath"), 0, 1);
        pathRow.Controls.Add(new InputFrame(userDataPath), 1, 1);
        pathRow.Controls.Add(Button("Browse", () =>
        {
            using var dialog = new FolderBrowserDialog
            {
                Description = localizer.Text("UserDataChoose"), ShowNewFolderButton = false,
                InitialDirectory = Directory.Exists(userDataPath.Text.Trim()) ? userDataPath.Text.Trim()
                    : Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments)
            };
            if (dialog.ShowDialog(this) == DialogResult.OK) userDataPath.Text = dialog.SelectedPath;
        }), 2, 1);
        var dataNotice = Notice("UserDataNotice");
        pathRow.Controls.Add(dataNotice, 0, 2);
        pathRow.SetColumnSpan(dataNotice, 3);
        body.Controls.Add(pathRow);

        rules.Columns.Add(new DataGridViewTextBoxColumn { Name = "Code", ValueType = typeof(int), ReadOnly = true, FillWeight = 55 });
        rules.Columns.Add(new DataGridViewTextBoxColumn { Name = "Original", ReadOnly = true, FillWeight = 140 });
        rules.Columns.Add(new DataGridViewCheckBoxColumn { Name = "Override", FillWeight = 70 });
        rules.Columns.Add(new DataGridViewTextBoxColumn { Name = "Substitutions", ValueType = typeof(int) });
        rules.Columns.Add(new DataGridViewCheckBoxColumn { Name = "BenchOverride", FillWeight = 70 });
        rules.Columns.Add(new DataGridViewTextBoxColumn { Name = "Bench", ValueType = typeof(int) });
        rules.Columns.Add(new DataGridViewTextBoxColumn
        {
            Name = "RuleScope", ReadOnly = true, FillWeight = 230, MinimumWidth = 180
        });
        foreach (DataGridViewColumn column in rules.Columns)
            column.SortMode = DataGridViewColumnSortMode.Automatic;
        rules.CellValidating += (_, args) =>
        {
            if (rules.Columns[args.ColumnIndex].Name is not ("Substitutions" or "Bench")) return;
            if (rules.Rows[args.RowIndex].Cells[args.ColumnIndex].ReadOnly) return;
            if (!int.TryParse(Convert.ToString(args.FormattedValue, CultureInfo.InvariantCulture),
                NumberStyles.Integer, CultureInfo.InvariantCulture, out var value) || value < 0
                || value > 12)
            {
                args.Cancel = true;
                rules.Rows[args.RowIndex].ErrorText = localizer.Text("InvalidGrid");
                SetStatus("InvalidGrid");
            }
            else rules.Rows[args.RowIndex].ErrorText = "";
        };
        rules.DataError += (_, args) =>
        {
            args.ThrowException = false;
            args.Cancel = true;
            if (args.RowIndex >= 0) rules.Rows[args.RowIndex].ErrorText = localizer.Text("InvalidGrid");
            SetStatus("InvalidGrid");
        };
        rules.CellEndEdit += (_, args) =>
        {
            rules.Rows[args.RowIndex].ErrorText = "";
            if (statusKey == "InvalidGrid") SetStatus(launcher.IsRunning ? "Running" : "Ready");
        };
        rules.CurrentCellDirtyStateChanged += (_, _) =>
        {
            if (rules.CurrentCell is DataGridViewCheckBoxCell && rules.IsCurrentCellDirty)
                rules.CommitEdit(DataGridViewDataErrorContexts.Commit);
        };
        rules.CellValueChanged += (_, args) =>
        {
            if (updating || args.RowIndex < 0) return;
            var row = rules.Rows[args.RowIndex];
            if (rules.Columns[args.ColumnIndex].Name is "Override" or "BenchOverride")
                UpdateRuleEditing(row);
            if (row == rules.CurrentRow) SyncEditors();
        };
        rules.CurrentCellChanged += (_, _) => SyncEditors();
        rules.Sorted += (_, _) => SyncEditors();
        substitutionsEditor.ValueChanged += (_, _) =>
            Execute(() => UpdateFromEditor(substitutionsEditor, "Substitutions"));
        benchEditor.ValueChanged += (_, _) => Execute(() => UpdateFromEditor(benchEditor, "Bench"));
        var rulePanel = Stack();
        rulePanel.Controls.Add(Notice("RulesNotice"));
        var gridContainer = new Panel { Dock = DockStyle.Top, Height = 260 };
        gridContainer.Controls.Add(rules);
        rulePanel.Controls.Add(gridContainer);
        rulePanel.Controls.Add(Row(selectedRule, CaptionLabel("Substitutions"), substitutionsEditor,
            CaptionLabel("Bench"), benchEditor));
        rulePanel.Controls.Add(Notice("RuleScopeNotice"));
        var scopeContainer = new Panel { Dock = DockStyle.Top, Height = 170 };
        scopeContainer.Controls.Add(ruleScope);
        rulePanel.Controls.Add(scopeContainer);
        captions.Add(matchRulesEnabled, "MatchRulesEnabled");
        rulePanel.Controls.Add(Notice("MatchRulesToggleNotice"));

        modes.Width = 220;
        modes.Name = "DisplayMode";
        resolutions.Width = 170;
        resolutions.Name = "Resolution";
        var displayPanel = Stack();
        captions.Add(displayEnabled, "DisplayEnabled");
        displayPanel.Controls.Add(Notice("DisplayNotice"));
        var displayOptions = new TableLayoutPanel
        {
            Name = "GraphicsOptions", Dock = DockStyle.Top, AutoSize = true,
            AutoSizeMode = AutoSizeMode.GrowAndShrink, ColumnCount = 3, Margin = Padding.Empty
        };
        displayOptions.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
        displayOptions.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
        displayOptions.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
        displayOptions.Controls.Add(CaptionLabel("DisplayMode"), 0, 0);
        displayOptions.Controls.Add(CaptionLabel("Resolution"), 1, 0);
        modes.Dock = resolutions.Dock = DockStyle.Fill;
        modes.Margin = resolutions.Margin = new Padding(3, 0, 10, 0);
        displayOptions.Controls.Add(ComboSlot(modes), 0, 1);
        displayOptions.Controls.Add(ComboSlot(resolutions), 1, 1);
        var refreshDisplay = Button("RefreshDisplay", RefreshDisplay);
        refreshDisplay.Name = "RefreshDisplay";
        refreshDisplay.Anchor = AnchorStyles.Right;
        refreshDisplay.Margin = new Padding(3, 0, 3, 0);
        displayOptions.Controls.Add(refreshDisplay, 2, 1);
        body.Controls.Add(Feature("GraphicsFeature", displayEnabled, displayPanel, alwaysVisible: displayOptions));
        body.Controls.Add(Feature("MatchRulesFeature", matchRulesEnabled, rulePanel));
        displayEnabled.CheckedChanged += (_, _) =>
        {
            modes.Enabled = resolutions.Enabled = displayEnabled.Checked;
            if (!updating) Execute(ChangeDisplayMode);
        };
        modes.SelectedIndexChanged += (_, _) =>
        {
            if (!updating) Execute(ChangeDisplayMode);
        };
        var paPanel = Stack();
        captions.Add(paEnabled, "PaEnabled");
        captions.Add(agingDelay, "AgingDelayEnabled");
        paPanel.Controls.Add(Notice("PaNotice"));
        paPanel.Controls.Add(Notice("PaCalculation"));
        paPanel.Controls.Add(paStatistics);
        paLogOpen = Button("PaLogOpen", OpenPaLog);
        paLogOpen.Name = "PaLogOpen";
        paPanel.Controls.Add(paLogOpen);
        paPanel.Controls.Add(paLogStatus);
        wrappingLabels.Add(paStatistics);
        wrappingLabels.Add(paLogStatus);
        body.Controls.Add(Feature("PaFeature", paEnabled, paPanel));
        var agingPanel = Stack();
        agingPanel.Controls.Add(Notice("AgingDelayNotice"));
        body.Controls.Add(Feature("AgingFeature", agingDelay, agingPanel));
        var panelInformationSection = Stack();
        captions.Add(panelInformation, "PanelInformationEnabled");
        panelInformationSection.Controls.Add(Notice("PanelInformationNotice"));
        panelInformationSection.Controls.Add(Notice("PanelSkinGuideNotice"));
        body.Controls.Add(Feature("PanelsFeature", panelInformation, panelInformationSection));
        body.Controls.Add(leagueReputation);
        captions.Add(advancedMode, "AdvancedMode");
        body.Controls.Add(advancedMode);
        advancedNotice = new Label
        {
            Name = "AdvancedActiveTools", AutoSize = true, Dock = DockStyle.Top,
            Margin = new Padding(3, 7, 8, 3)
        };
        wrappingLabels.Add(advancedNotice);
        body.Controls.Add(advancedNotice);
        advancedMode.CheckedChanged += (_, _) => ApplyAdvancedMode();
        leagueReputation.AdvancedToolsChanged += UpdateAdvancedNotice;
        ApplyAdvancedMode();
        captions.Add(save, "Save");
        captions.Add(launch, "Play");
        save.Click += (_, _) => Execute(SaveConfiguration);
        launch.Click += (_, _) => Execute(LaunchGame);
        var footer = Stack();
        footer.Name = "LauncherActions";
        footer.Dock = DockStyle.Bottom;
        footer.BackColor = Color.White;
        footer.Padding = new Padding(12, 4, 12, 6);
        footer.Controls.Add(status);
        footer.Controls.Add(profileBanner);
        var playRow = new TableLayoutPanel { Dock = DockStyle.Top, AutoSize = true, ColumnCount = 3 };
        playRow.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
        playRow.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
        playRow.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
        configurationActions.Name = "ConfigurationActions";
        var reload = Button("Reload", LoadConfiguration);
        reload.Name = "Reload";
        configurationActions.Controls.AddRange([save, reload]);
        playRow.Controls.Add(configurationActions, 0, 0);
        playRow.Controls.Add(launch, 1, 0);
        footer.Controls.Add(playRow);
        var links = new FlowLayoutPanel { Name = "SocialLinks", AutoSize = true, Anchor = AnchorStyles.None, WrapContents = false };
        AddSocialLink(links, "GitLink", null);
        AddSocialLink(links, "YouTubeLink", "https://www.youtube.com/@Bezimienny111");
        AddSocialLink(links, "DiscordLink", "https://discord.gg/hP2g4MQS5T");
        var support = new FlowLayoutPanel
        {
            Name = "ProjectSupport", AutoSize = true, AutoSizeMode = AutoSizeMode.GrowAndShrink,
            Anchor = AnchorStyles.Right, WrapContents = false, Margin = Padding.Empty
        };
        var donatePrompt = CaptionLabel("DonatePrompt");
        donatePrompt.Name = "DonatePrompt";
        donatePrompt.Anchor = AnchorStyles.None;
        donatePrompt.Margin = new Padding(0, 0, 8, 0);
        support.Controls.Add(donatePrompt);
        AddSocialLink(support, "DonateLink", "https://ko-fi.com/ericaaurora");
        var linkRow = new TableLayoutPanel
        {
            Name = "FooterLinks", Dock = DockStyle.Top, AutoSize = true,
            ColumnCount = 3, Margin = Padding.Empty
        };
        linkRow.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
        linkRow.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
        linkRow.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
        linkRow.Controls.Add(links, 1, 0);
        linkRow.Controls.Add(support, 2, 0);
        footer.Controls.Add(linkRow);
        Controls.Add(footer);
        Controls.Add(header);
        wrappingLabels.Add(status);
        ClientSizeChanged += (_, _) => UpdateNoticeWidths();
        languages.SelectedIndexChanged += (_, _) =>
        {
            if (!updating && languages.SelectedItem is LanguageDefinition language)
                Execute(() => ApplyLanguage(language.Code));
        };
        timer.Tick += (_, _) => Execute(() =>
        {
            if (launcher.CheckExited())
            {
                SetStatus("Exited");
                UpdateActions();
            }
            else if (launcher.IsRunning && statusKey is "Running" or "PreparingDisplay")
                SetStatus(launcher.IsDisplayReady ? "Running" : "PreparingDisplay");
            UpdatePaStatistics();
            skinGuide.UpdateRuntime(launcher.PanelStatistics, launcher.IsRunning);
            leagueReputation.UpdateRuntime();
        });
        FormClosing += (_, _) =>
        {
            timer.Stop();
            launcher.Dispose();
        };
        body.ResumeLayout(true);
        ResumeLayout(true);
        ApplyLanguage("en");
        Load += (_, _) =>
        {
            if (localizer.Warning is not null)
                MessageBox.Show(this, localizer.Error(localizer.Warning), localizer.Text("WarningTitle"),
                    MessageBoxButtons.OK, MessageBoxIcon.Warning);
            Execute(LoadConfiguration);
        };
    }

    private static ComboBox Choice() => new ThemedComboBox { DropDownStyle = ComboBoxStyle.DropDownList };
    private void ApplyAdvancedMode()
    {
        var advanced = advancedMode.Checked;
        configurationActions.Visible = advanced;
        paLogOpen.Visible = paStatistics.Visible = paLogStatus.Visible = advanced;
        leagueReputation.SetAdvancedMode(advanced);
        if (!advanced) paLogWindow?.Close();
        UpdateAdvancedNotice();
    }

    private void UpdateAdvancedNotice()
    {
        var active = new List<string>();
        if (leagueReputation.ObservationEnabled) active.Add(localizer.Text("LeagueEnabled"));
        if (leagueReputation.DiagnosticsEnabled) active.Add(localizer.Text("LeagueDiagnosticsEnabled"));
        advancedNotice.Visible = !advancedMode.Checked && active.Count > 0;
        advancedNotice.Text = localizer.Text("AdvancedActiveTools", string.Join(", ", active));
    }

    private static Panel ComboSlot(ComboBox combo)
    {
        var slot = new Panel
        {
            Name = combo.Name + "Slot", Height = combo.Height, Width = combo.Width,
            Anchor = AnchorStyles.Left | AnchorStyles.Right, Margin = combo.Margin
        };
        combo.Margin = Padding.Empty;
        combo.Dock = DockStyle.Fill;
        slot.Controls.Add(combo);
        combo.SizeChanged += (_, _) => slot.Height = combo.Height;
        return slot;
    }

    private void UpdateNoticeWidths()
    {
        foreach (var label in wrappingLabels)
            label.MaximumSize = new Size(Math.Max(200, ClientSize.Width - 115), 0);
    }
    private FeatureSection Feature(string name, ToggleSwitch toggle, Control content, bool expanded = false,
        Control? alwaysVisible = null)
    {
        var feature = new FeatureSection(name, toggle, content, localizer, expanded, alwaysVisible);
        features.Add(feature);
        return feature;
    }

    internal void ApplyTheme(bool dark)
    {
        darkMode = dark;
        themeMode.Text = localizer.Text(dark ? "LightMode" : "DarkMode");
        themeMode.AccessibleName = themeMode.Text;
        LauncherTheme.Apply(this, dark);
        foreach (var window in OwnedForms) LauncherTheme.Apply(window, dark);
        foreach (DataGridViewRow row in rules.Rows) UpdateRuleEditing(row);
        leagueReputation.RefreshLanguage();
        UpdateAdvancedNotice();
        skinGuide.UpdateRuntime(launcher.PanelStatistics, launcher.IsRunning);
    }

    private void AddSocialLink(Control parent, string name, string? url)
    {
        var button = new SocialLinkButton(name) { Enabled = url is not null, Tag = url };
        socialLinks.Add(button);
        button.Click += (_, _) => Execute(() =>
        {
            if (url is null) return;
            try { Process.Start(new ProcessStartInfo(url) { UseShellExecute = true }); }
            catch (Exception ex) when (ex is Win32Exception or InvalidOperationException)
            {
                throw new LauncherException("LinkOpenError", ex.Message);
            }
        });
        parent.Controls.Add(button);
    }
    private TableLayoutPanel AddSettingsTab(TabControl tabs, string name, string caption)
    {
        var page = new TabPage { Name = name, BackColor = BackColor };
        captions.Add(page, caption);
        var scroll = new Panel { Name = "MainSettingsScroll", Dock = DockStyle.Fill, AutoScroll = true, Padding = new Padding(12) };
        var content = Stack();
        scroll.Controls.Add(content);
        page.Controls.Add(scroll);
        tabs.TabPages.Add(page);
        return content;
    }
    private static TableLayoutPanel Stack() => new()
    {
        ColumnCount = 1, AutoSize = true, AutoSizeMode = AutoSizeMode.GrowAndShrink,
        Dock = DockStyle.Top, Padding = new Padding(0, 3, 0, 3),
        ColumnStyles = { new ColumnStyle(SizeType.Percent, 100) }
    };
    private static FlowLayoutPanel Row(params Control[] controls)
    {
        var panel = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Top, WrapContents = true };
        panel.Controls.AddRange(controls);
        return panel;
    }
    private Label CaptionLabel(string key)
    {
        var label = new Label { AutoSize = true, Margin = new Padding(3, 7, 8, 3) };
        captions.Add(label, key);
        return label;
    }
    private Label Notice(string key)
    {
        var label = CaptionLabel(key);
        label.Name = key;
        label.Dock = DockStyle.Top;
        wrappingLabels.Add(label);
        return label;
    }
    private Button Button(string key, Action action)
    {
        var button = new Button { AutoSize = true };
        captions.Add(button, key);
        button.Click += (_, _) => Execute(action);
        return button;
    }

    internal void ApplyLanguage(string code)
    {
        if (rules.IsCurrentCellInEditMode && (!ValidateChildren() || !rules.EndEdit()))
            throw new LauncherException("InvalidGrid");
        var selectedMode = modes.SelectedItem is ModeChoice choice ? choice.Mode : DisplayMode.Fullscreen;
        updating = true;
        SuspendLayout();
        settingsContent.SuspendLayout();
        try
        {
            localizer.Select(code);
            languages.SelectedItem = localizer.Languages.Single(language => language.Code == code);
            Text = localizer.Text("Title");
            foreach (var caption in captions) caption.Key.Text = localizer.Text(caption.Value);
            foreach (var feature in features) feature.RefreshLanguage();
            foreach (var button in socialLinks)
            {
                button.AccessibleName = localizer.Text(button.Name);
                button.AccessibleDescription = localizer.Text(button.Name == "DonateLink" ? "DonateTooltip" : button.Name);
                tooltips.SetToolTip(button, button.AccessibleDescription);
            }
            tooltips.SetToolTip(launch, localizer.Text("AutoSaveNotice"));
            foreach (DataGridViewColumn column in rules.Columns) column.HeaderText = localizer.Text(column.Name);
            foreach (DataGridViewRow row in rules.Rows) UpdateOriginal(row);
            modes.Items.Clear();
            modes.Items.AddRange(Enum.GetValues<DisplayMode>()
                .Select(mode => new ModeChoice(mode, localizer.Text(mode.ToString()))).Cast<object>().ToArray());
            modes.SelectedIndex = (int)selectedMode;
            SetStatus(statusKey, statusArguments);
            UpdatePaStatistics();
            paLogWindow?.ApplyLanguage();
            skinGuide.ApplyLanguage();
            leagueReputation.RefreshLanguage();
            UpdateAdvancedNotice();
            themeMode.Text = localizer.Text(darkMode ? "LightMode" : "DarkMode");
            themeMode.AccessibleName = themeMode.Text;
            UpdateNoticeWidths();
        }
        finally
        {
            updating = false;
            settingsContent.ResumeLayout(true);
            ResumeLayout(true);
        }
        SyncEditors();
    }

    private void UpdateOriginal(DataGridViewRow row)
    {
        var original = RuleCatalog.Original((int)row.Cells[0].Value);
        row.Cells[1].Value = original is { } value
            ? $"{value.Substitutions} / {value.Bench}"
            : localizer.Text((int)row.Cells[0].Value == 22 ? "OriginalRule22" : "OriginalRule28");
        row.Cells["RuleScope"].Value = MatchRuleScope.Summary((int)row.Cells["Code"].Value, localizer);
        row.Cells["RuleScope"].ToolTipText = MatchRuleScope.Details((int)row.Cells["Code"].Value, localizer);
    }
    private void UpdateRuleEditing(DataGridViewRow row)
    {
        foreach (var (valueColumn, overrideColumn) in new[]
            { ("Substitutions", "Override"), ("Bench", "BenchOverride") })
        {
            var editable = row.Cells[overrideColumn].Value is true;
            row.Cells[valueColumn].ReadOnly = !editable;
            row.Cells[valueColumn].Style.BackColor = editable ? LauncherTheme.Input(darkMode) : LauncherTheme.Surface(darkMode);
        }
    }

    private void SyncEditors()
    {
        if (updating || syncingEditors) return;
        syncingEditors = true;
        try
        {
            var row = rules.CurrentRow;
            selectedRule.Text = row is null ? localizer.Text("NoSelectedRule")
                : localizer.Text("SelectedRule", row.Cells["Code"].Value);
            ruleScope.Text = row is null ? localizer.Text("NoSelectedRule")
                : MatchRuleScope.Details((int)row.Cells["Code"].Value, localizer);
            SyncEditor(substitutionsEditor, row, "Substitutions", "Override");
            SyncEditor(benchEditor, row, "Bench", "BenchOverride");
        }
        finally { syncingEditors = false; }
    }

    private static void SyncEditor(NumericUpDown editor, DataGridViewRow? row, string valueColumn, string overrideColumn)
    {
        var value = row is null ? 0 : Convert.ToInt32(row.Cells[valueColumn].Value, CultureInfo.InvariantCulture);
        // Keep legacy inactive values visible without clamping or applying them.
        editor.Maximum = Math.Max(12, value);
        editor.Value = value;
        editor.Enabled = row?.Cells[overrideColumn].Value is true && value <= 12;
    }

    private void UpdateFromEditor(NumericUpDown editor, string column)
    {
        if (syncingEditors || updating || rules.CurrentRow is not { } row) return;
        if (!ValidateChildren() || !rules.EndEdit())
        {
            SyncEditors();
            throw new LauncherException("InvalidGrid");
        }
        row.Cells[column].Value = (int)editor.Value;
    }

    internal void LoadConfiguration()
    {
        configurationBlocked = true;
        UpdateActions();
        SetStatus("ConfigBlocked");
        var config = store.Load();
        var available = detectDisplay(config is { DisplayOverride: true } ? config.DisplayMode : DisplayMode.Fullscreen);
        config ??= LauncherConfiguration.CreateDefault(FindGamePath(), available[0]);
        if (!localizer.Languages.Any(language => language.Code == config.Language))
        {
            MessageBox.Show(this, localizer.Error(new LauncherException("UnknownLanguage", config.Language)),
                localizer.Text("WarningTitle"), MessageBoxButtons.OK, MessageBoxIcon.Warning);
            config.Language = "en";
        }
        Populate(config, available);
        configurationBlocked = false;
        SetStatus(launcher.IsRunning ? "Running" : "Ready");
        UpdateActions();
    }

    internal void Populate(LauncherConfiguration config, IReadOnlyList<Resolution> available)
    {
        ConfigurationValidator.Validate(config);
        gamePath.Text = config.GamePath;
        userDataPath.Text = config.UserDataPath;
        matchRulesEnabled.Checked = config.MatchRulesEnabled;
        ApplyLanguage(config.Language);
        paEnabled.Checked = config.PaEnabled;
        agingDelay.Checked = config.AgingDelayEnabled;
        legacyPaChance = config.PaChance;
        panelInformation.Checked = config.PanelInformationEnabled;
        leagueReputation.ObservationEnabled = config.LeagueReputationEnabled;
        leagueReputation.DiagnosticsEnabled = config.LeagueDiagnosticsEnabled;
        leagueReputation.ChangesEnabled = config.LeagueChangesEnabled;
        advancedMode.Checked = config.AdvancedMode;
        ApplyAdvancedMode();
        updating = true;
        try
        {
            modes.SelectedIndex = (int)config.DisplayMode;
            displayEnabled.Checked = config.DisplayOverride;
            modes.Enabled = resolutions.Enabled = config.DisplayOverride;
            SetResolutions(available, config.Resolution);
            rules.Rows.Clear();
            foreach (var rule in config.Rules.OrderBy(rule => rule.Code))
            {
                var index = rules.Rows.Add(rule.Code, "", rule.Override, rule.Substitutions, rule.BenchOverride, rule.Bench);
                UpdateOriginal(rules.Rows[index]);
                UpdateRuleEditing(rules.Rows[index]);
            }
        }
        finally { updating = false; }
        SyncEditors();
        ApplyTheme(config.DarkMode);
    }

    private static string FindGamePath()
    {
        for (var directory = new DirectoryInfo(AppContext.BaseDirectory); directory is not null; directory = directory.Parent)
        {
            var candidate = Path.Combine(directory.FullName, "fm.exe");
            if (File.Exists(candidate)) return candidate;
        }
        return Path.Combine(AppContext.BaseDirectory, "fm.exe");
    }

    private void SetResolutions(IReadOnlyList<Resolution> available, Resolution? selected)
    {
        resolutions.Items.Clear();
        resolutions.Items.AddRange(available.Cast<object>().ToArray());
        // Preserve unavailable saved selections so validation requires an explicit user choice.
        if (selected is not null && !available.Contains(selected)) resolutions.Items.Add(selected);
        resolutions.SelectedItem = selected ?? available[0];
    }

    private void RefreshDisplay()
    {
        var selected = resolutions.SelectedItem as Resolution;
        var available = DetectSelectedDisplay();
        SetResolutions(available, selected);
        if (selected is not null && !available.Contains(selected))
            throw new LauncherException("ResolutionUnavailable", selected);
    }

    private DisplayMode SelectedDisplayMode() => modes.SelectedItem is ModeChoice choice
        ? choice.Mode : throw new LauncherException("InvalidDisplayMode");

    private IReadOnlyList<Resolution> DetectSelectedDisplay() =>
        detectDisplay(displayEnabled.Checked ? SelectedDisplayMode() : DisplayMode.Fullscreen);

    private void ChangeDisplayMode()
    {
        var available = DetectSelectedDisplay();
        var selected = resolutions.SelectedItem as Resolution;
        if (selected is not null && !available.Contains(selected))
        {
            var replacement = available.OrderByDescending(value => (long)value.Width * value.Height).First();
            SetResolutions(available, replacement);
            SetStatus("ResolutionAdjusted", selected, replacement);
        }
        else SetResolutions(available, selected);
    }

    internal LauncherConfiguration CaptureConfiguration()
    {
        if (!ValidateChildren() || !rules.EndEdit()) throw new LauncherException("InvalidGrid");
        var config = new LauncherConfiguration
        {
            SchemaVersion = 1, Language = localizer.Code, GamePath = gamePath.Text.Trim(),
            UserDataPath = userDataPath.Text.Trim(), MatchRulesEnabled = matchRulesEnabled.Checked,
            DarkMode = darkMode, AdvancedMode = advancedMode.Checked,
            DisplayOverride = displayEnabled.Checked,
            DisplayMode = modes.SelectedItem is ModeChoice choice ? choice.Mode : throw new LauncherException("InvalidDisplayMode"),
            Resolution = resolutions.SelectedItem as Resolution ?? throw new LauncherException("InvalidResolution"),
            PaEnabled = paEnabled.Checked, PaChance = legacyPaChance,
            AgingDelayEnabled = agingDelay.Checked,
            PanelInformationEnabled = panelInformation.Checked,
            LeagueReputationEnabled = leagueReputation.ObservationEnabled,
            LeagueDiagnosticsEnabled = leagueReputation.DiagnosticsEnabled,
            LeagueChangesEnabled = leagueReputation.ChangesEnabled,
            Rules = rules.Rows.Cast<DataGridViewRow>().Select(row => new RuleSettings
            {
                Code = (int)row.Cells["Code"].Value, Override = (bool)row.Cells["Override"].Value,
                BenchOverride = (bool)row.Cells["BenchOverride"].Value,
                Substitutions = Convert.ToInt32(row.Cells["Substitutions"].Value, CultureInfo.InvariantCulture),
                Bench = Convert.ToInt32(row.Cells["Bench"].Value, CultureInfo.InvariantCulture)
            }).OrderBy(rule => rule.Code).ToList()
        };
        ConfigurationValidator.Validate(config);
        return config;
    }

    private void SaveConfiguration()
    {
        if (configurationBlocked) throw new LauncherException("ConfigBlocked");
        var config = CaptureConfiguration();
        ConfigurationValidator.ValidateDisplay(config, DetectSelectedDisplay());
        store.Save(config);
        SetStatus(launcher.IsRunning ? "Running" : "Saved");
    }

    private void LaunchGame() => LaunchGame(
        confirmation => MessageBox.Show(this, confirmation, localizer.Text("WarningTitle"),
            MessageBoxButtons.OKCancel, MessageBoxIcon.Warning, MessageBoxDefaultButton.Button2),
        config => launcher.Launch(config, localizer));

    internal void LaunchGame(Func<string, DialogResult> confirm, Action<LauncherConfiguration> start)
    {
        if (configurationBlocked) throw new LauncherException("ConfigBlocked");
        var config = CaptureConfiguration();
        ConfigurationValidator.ValidateDisplay(config, DetectSelectedDisplay());
        var confirmation = localizer.Text("LaunchConfirmation") + "\n\n"
            + localizer.Text(config.DisplayOverride ? "DisplayLaunchConfirmation" : "DisplayDisabledConfirmation") + "\n\n"
            + (config.PaEnabled
                ? localizer.Text("PaLaunchConfirmation", PaGrowthPolicy.Default.BaseChancePercent)
                : localizer.Text("PaDisabledConfirmation"))
            + "\n\n" + localizer.Text(config.PanelInformationEnabled ? "PanelLaunchConfirmation" : "PanelDisabledConfirmation")
            + "\n\n" + localizer.Text(config.LeagueChangesEnabled ? "LeagueChangesNotice"
                : config.LeagueReputationEnabled ? "LeagueLaunchConfirmation" : "LeagueDisabledConfirmation");
        if (config.LeagueDiagnosticsEnabled)
            confirmation += "\n\n" + localizer.Text("LeagueDiagnosticsLaunchConfirmation");
        if (config.AgingDelayEnabled)
            confirmation += "\n\n" + localizer.Text("AgingDelayNotice");
        if (!config.MatchRulesEnabled)
            confirmation += "\n\n" + localizer.Text("MatchRulesDisabledConfirmation");
        if (confirm(confirmation) != DialogResult.OK) return;
        store.Save(config);
        start(config);
        leagueReputation.UpdateRuntime();
        skinGuide.UpdateRuntime(launcher.PanelStatistics, launcher.IsRunning);
        SetStatus(launcher.IsDisplayReady ? "Running" : "PreparingDisplay");
        UpdatePaStatistics();
        UpdateActions();
        timer.Start();
    }

    private void SetStatus(string key, params object[] arguments)
    {
        statusKey = key;
        statusArguments = arguments;
        status.Text = localizer.Text(key, arguments);
    }
    private void UpdatePaStatistics()
    {
        paStatistics.Text = launcher.PaStatistics is { } statistics
            ? localizer.Text("PaStatistics", statistics.Rolls, statistics.Increases, statistics.InvalidFields)
            : localizer.Text("PaStatisticsEmpty");
        paLogStatus.Text = PaLogForm.Status(localizer, launcher.PaJournal);
        paLogWindow?.RefreshJournal();
    }
    private void OpenPaLog()
    {
        if (paLogWindow is null || paLogWindow.IsDisposed)
        {
            paLogWindow = new PaLogForm(localizer, launcher.PaJournal);
            paLogWindow.FormClosed += (_, _) => paLogWindow = null;
            paLogWindow.Show(this);
            LauncherTheme.Apply(paLogWindow, darkMode);
        }
        else
        {
            if (paLogWindow.WindowState == FormWindowState.Minimized) paLogWindow.WindowState = FormWindowState.Normal;
            paLogWindow.Activate();
        }
    }
    private void UpdateActions()
    {
        save.Enabled = !configurationBlocked;
        launch.Enabled = !configurationBlocked && !launcher.IsRunning;
    }
    private void ShowError(LauncherException error) =>
        MessageBox.Show(this, localizer.Error(error), localizer.Text("ErrorTitle"), MessageBoxButtons.OK, MessageBoxIcon.Error);
    private void Execute(Action action)
    {
        try { action(); }
        catch (LauncherException ex)
        {
            UpdateActions();
            if (!launcher.IsRunning && statusKey is "Running" or "PreparingDisplay") SetStatus("IntegrationFailed");
            ShowError(ex);
        }
    }
    protected override void Dispose(bool disposing)
    {
        if (disposing)
        {
            timer.Dispose();
            tooltips.Dispose();
            launcher.Dispose();
        }
        base.Dispose(disposing);
    }
    private sealed record ModeChoice(DisplayMode Mode, string Caption)
    {
        public override string ToString() => Caption;
    }
}
