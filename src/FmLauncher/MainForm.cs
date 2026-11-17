using System.Globalization;
using System.ComponentModel;
using System.Diagnostics;

namespace FmLauncher;

internal sealed partial class MainForm : Form
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
    private readonly Button themeMode = new()
    {
        Name="ThemeMode",AutoSize=false,Size=new Size(150,44),FlatStyle=FlatStyle.Flat,
        Anchor=AnchorStyles.Top|AnchorStyles.Right,Margin=Padding.Empty,
        Font=new Font("Segoe UI",10,FontStyle.Bold)
    };
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
    private readonly ToggleSwitch positionHighlights = new() { Name = "PositionHighlightsEnabled", Dock = DockStyle.Top };
    private readonly ToggleSwitch hiddenAttributes = new() { Name = "HiddenAttributesEnabled", Dock = DockStyle.Top };
    private readonly ToggleSwitch teamTalkReactions = new() { Name = "TeamTalkReactionsEnabled" };
    private readonly SkinGuidePage skinGuide;
    private readonly CommunityLinksPage communityLinks;
    private readonly LeagueReputationPage leagueReputation;
    private int legacyPaChance;
    private readonly Label paStatistics = new() { Name = "PaStatistics", AutoSize = true, Dock = DockStyle.Top };
    private readonly Label paLogStatus = new() { Name = "PaLogStatus", AutoSize = true, Dock = DockStyle.Top };
    private PaLogForm? paLogWindow;
    private readonly LaunchLogPanel launchLog;
    private readonly ComboBox ruleView = Choice();
    private readonly Control individualRulesView;
    private readonly RuleGroupEditor groupedRules;
    private int activeRuleView;
    private bool changingRuleView;
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
        Name = "IndividualRules", Dock = DockStyle.Fill, Height = 300, AutoGenerateColumns = false,
        AllowUserToAddRows = false, AllowUserToDeleteRows = false,
        AllowUserToOrderColumns = false, RowHeadersVisible = false,
        AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
        ColumnHeadersHeightSizeMode = DataGridViewColumnHeadersHeightSizeMode.AutoSize,
        SelectionMode = DataGridViewSelectionMode.FullRowSelect, MultiSelect = true
    };
    private readonly Button retryConfiguration = new() { Name = "RetryConfiguration", AutoSize = true, Visible = false };
    private bool configurationLoaded;
    private string? lastSavedConfiguration;
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
        MinimumSize = new Size(1024, 720);
        Size = new Size(1280, 960);
        StartPosition = FormStartPosition.CenterScreen;
        SuspendLayout();
        var tabs = new ThemedTabControl
        {
            Name = "FeatureTabs", Dock = DockStyle.Fill, Alignment = TabAlignment.Left,
            SizeMode = TabSizeMode.Fixed, Multiline = true, ItemSize = new Size(54, 185), Padding = new Point(12, 8)
        };
        var body = settingsContent = AddSettingsTab(tabs, "Settings", "FeaturesTab");
        var graphicsBody = AddSettingsTab(tabs, "Graphics", "GraphicsTab");
        var preferencesPage = new TabPage { Name = "Preferences", Padding = new Padding(12) };
        captions.Add(preferencesPage, "PreferencesTab");
        var preferencesScroll = new Panel { Name = "PreferencesScroll", Dock = DockStyle.Fill, AutoScroll = true };
        var preferencesBody = Stack();
        preferencesScroll.Controls.Add(preferencesBody);
        preferencesPage.Controls.Add(preferencesScroll);
        body.SuspendLayout();
        leagueReputation = new LeagueReputationPage(localizer, () => gamePath.Text.Trim(), Execute, directory, launcher,
            () => darkMode);
        skinGuide = new SkinGuidePage(localizer, () => gamePath.Text.Trim(), () => userDataPath.Text.Trim(), Execute,
            () => darkMode, () => new PlayerProfilePanelOptions(positionHighlights.Checked, hiddenAttributes.Checked));
        tabs.TabPages.Add(skinGuide);
        Controls.Add(tabs);
        profileBanner.Click += (_, _) =>
        {
            tabs.SelectedTab=tabs.TabPages.Cast<TabPage>().Single(page=>page.Name=="Settings");
            leagueReputation.ShowChanges();
            if (body.Parent is ScrollableControl scroll) scroll.ScrollControlIntoView(sharedDetails);
        };
        leagueReputation.ProfileStatusChanged += () =>
        {
            profileBanner.Visible = leagueReputation.ChangesEnabled;
            profileBanner.Text = leagueReputation.ProfileStatusText;
            profileBanner.BackColor = leagueReputation.ProfileStatusColor;
        };
        ClientSizeChanged += (_, _) => profileBanner.MaximumSize = new Size(Math.Max(200, (profileBanner.Parent?.ClientSize.Width??ClientSize.Width) - 12), 0);

        languages.Name = "LauncherLanguage";
        languages.Width = 160;
        languages.Items.AddRange(localizer.Languages.Cast<object>().ToArray());
        var header = new TableLayoutPanel
        {
            Name = "LauncherHeader", Dock = DockStyle.Top, Height = 76, ColumnCount = 3,
            Padding = new Padding(12, 8, 12, 8), BackColor = Color.White
        };
        header.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 325));
        header.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        header.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 325));
        header.RowCount = 1;
        header.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        var title = CaptionLabel("Title");
        title.Name = "BrandTitle";
        title.Font = new Font(Font.FontFamily, 17, FontStyle.Bold);
        title.AutoSize = false;
        title.Dock = DockStyle.Fill;
        title.TextAlign = ContentAlignment.MiddleCenter;
        title.Height = 33;
        title.Margin = Padding.Empty;
        var version = new Label
        {
            Name = "LauncherVersion", Dock = DockStyle.Fill, Height = 22,
            Text = "v" + typeof(MainForm).Assembly.GetName().Version!.ToString(3) + " R23",
            TextAlign = ContentAlignment.MiddleCenter, Margin = Padding.Empty
        };
        var brandRow = new TableLayoutPanel { Name = "BrandHeading", Dock = DockStyle.Fill, ColumnCount = 1, RowCount = 2, Margin = Padding.Empty };
        brandRow.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        brandRow.RowStyles.Add(new RowStyle(SizeType.Percent, 65));
        brandRow.RowStyles.Add(new RowStyle(SizeType.Percent, 35));
        brandRow.Controls.Add(title, 0, 0);
        brandRow.Controls.Add(version, 0, 1);
        header.Controls.Add(brandRow, 1, 0);
        themeMode.Click += (_, _) => ApplyTheme(!darkMode);
        var languageFrame=new FramedPanel
        {
            Name="LanguageControls",Size=new Size(310,46),Anchor=AnchorStyles.Top|AnchorStyles.Left,
            Padding=new Padding(10,5,10,5),Margin=Padding.Empty
        };
        var languageRow=new TableLayoutPanel{Dock=DockStyle.Fill,ColumnCount=2,RowCount=1,Margin=Padding.Empty};
        languageRow.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,144));
        languageRow.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
        var languageLabel=CaptionLabel("Language");languageLabel.Name="LanguageHeading";
        languageLabel.AutoSize=false;languageLabel.Dock=DockStyle.Fill;languageLabel.Margin=Padding.Empty;
        languageLabel.TextAlign=ContentAlignment.MiddleLeft;languageLabel.Font=new Font(Font,FontStyle.Bold);
        languages.Dock=DockStyle.Fill;languages.Margin=new Padding(3,3,0,0);
        languageRow.Controls.Add(languageLabel,0,0);languageRow.Controls.Add(languages,1,0);
        languageFrame.Controls.Add(languageRow);
        header.Controls.Add(languageFrame,0,0);
        header.Controls.Add(themeMode,2,0);
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
        var pathsBox = new SectionBox { Name = "PathsSection", Dock = DockStyle.Top, AutoSize = true, Padding = new Padding(10, 25, 10, 10) };
        captions.Add(pathsBox, "PathsTitle");
        pathsBox.Controls.Add(pathRow);
        preferencesBody.Controls.Add(pathsBox);

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
        rulePanel.Controls.Add(CreateBulkRulesEditor());
        rulePanel.Controls.Add(Notice("RulesViewNotice"));
        ruleView.Name = "RuleEditView";
        ruleView.Width = 300;
        ruleView.SelectedIndexChanged += (_, _) => Execute(SwitchRuleView);
        rulePanel.Controls.Add(Row(CaptionLabel("RuleEditView"), ruleView));
        var individualPanel = Stack();
        individualRulesView = individualPanel;
        individualRulesView.Name = "IndividualRulesView";
        individualPanel.Controls.Add(Notice("RulesNotice"));
        var gridContainer = new FramedPanel { Name = "IndividualRulesFrame", Dock = DockStyle.Top, Height = 260, Padding = new Padding(3) };
        gridContainer.Controls.Add(rules);
        individualPanel.Controls.Add(gridContainer);
        individualPanel.Controls.Add(Row(selectedRule, CaptionLabel("Substitutions"), substitutionsEditor,
            CaptionLabel("Bench"), benchEditor));
        rulePanel.Controls.Add(individualRulesView);
        groupedRules = new RuleGroupEditor(localizer) { Visible = false };
        groupedRules.SelectionChanged += UpdateRuleScope;
        groupedRules.ApplyRequested += (code, substitutions, bench) =>
            Execute(() => ApplyGroupedChanges(code, substitutions, bench));
        rulePanel.Controls.Add(groupedRules);
        rulePanel.Controls.Add(Notice("RuleScopeNotice"));
        var scopeContainer = new FramedPanel { Name = "RuleScopeFrame", Dock = DockStyle.Top, Height = 155, Padding = new Padding(3) };
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
        var graphicsSection = new SectionBox { Name = "GraphicsSection", Dock = DockStyle.Top, AutoSize = true, Padding = new Padding(12, 25, 12, 12) };
        captions.Add(graphicsSection, "GraphicsTab");
        var graphicsContents = Stack();
        graphicsContents.Controls.Add(displayEnabled);
        graphicsContents.Controls.Add(displayPanel);
        graphicsContents.Controls.Add(displayOptions);
        graphicsSection.Controls.Add(graphicsContents);
        graphicsBody.Controls.Add(graphicsSection);
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
        captions.Add(agingDelay, "AgingFeatureTitle");
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
        captions.Add(panelInformation, "PlayerPanelsFeatureTitle");
        panelInformationSection.Controls.Add(Notice("PanelInformationNotice"));
        panelInformationSection.Controls.Add(Notice("PanelSkinGuideNotice"));
        captions.Add(positionHighlights, "PositionHighlightsEnabled");
        positionHighlights.Enabled = PositionHighlightModel.IntegrationReady;
        captions.Add(hiddenAttributes, "HiddenAttributesEnabled");
        panelInformationSection.Controls.Add(positionHighlights);
        panelInformationSection.Controls.Add(Notice("PositionHighlightsNotice"));
        panelInformationSection.Controls.Add(hiddenAttributes);
        panelInformationSection.Controls.Add(Notice("HiddenAttributesNotice"));
        body.Controls.Add(Feature("PanelsFeature", panelInformation, panelInformationSection));
        var talks = Stack();
        captions.Add(teamTalkReactions,"TeamTalkReactionsTitle");
        talks.Controls.Add(Notice("TeamTalkReactionsNotice"));
        void OpenSkinsBasic()
        {
            tabs.SelectedTab=skinGuide;
            skinGuide.ShowBasic();
        }
        var openTalkSkins=Button("OpenSkinsBasic",OpenSkinsBasic);
        openTalkSkins.Name="TeamTalkOpenSkins";
        talks.Controls.Add(openTalkSkins);
        var openPlayerSkins=Button("OpenSkinsBasic",OpenSkinsBasic);
        openPlayerSkins.Name="PlayerPanelsOpenSkins";
        panelInformationSection.Controls.Add(openPlayerSkins);
        body.Controls.Add(Feature("TeamTalkFeature",teamTalkReactions,talks));
        body.Controls.Add(leagueReputation);
        BuildFeatureWorkspace(body);
        captions.Add(advancedMode, "AdvancedMode");
        preferencesBody.Controls.Add(advancedMode);
        advancedNotice = new Label
        {
            Name = "AdvancedActiveTools", AutoSize = true, Dock = DockStyle.Top,
            Margin = new Padding(3, 7, 8, 3)
        };
        wrappingLabels.Add(advancedNotice);
        preferencesBody.Controls.Add(advancedNotice);
        preferencesBody.Controls.Add(Notice("IniSettingsNotice"));
        preferencesBody.Controls.Add(Notice("AutomaticSaveHint"));
        captions.Add(retryConfiguration,"RetryConfiguration");
        retryConfiguration.Click+=(_,_)=>Execute(LoadConfiguration);
        preferencesBody.Controls.Add(retryConfiguration);
        advancedMode.CheckedChanged += (_, _) => ApplyAdvancedMode();
        leagueReputation.AdvancedToolsChanged += UpdateAdvancedNotice;
        ApplyAdvancedMode();
        captions.Add(launch, "Play");
        launch.Click += (_, _) => Execute(LaunchGame);
        var footer = new TableLayoutPanel
        {
            Name="LauncherActions",Dock=DockStyle.Bottom,AutoSize=true,ColumnCount=2,
            Padding=new Padding(8,4,8,4),Margin=Padding.Empty
        };
        footer.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,188));
        footer.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
        footer.Paint += (_, args) =>
        {
            using var pen = new Pen(LauncherTheme.SectionBorder(darkMode), 2);
            args.Graphics.DrawLine(pen, 0, 0, footer.Width, 0);
        };
        var playArea=new Panel{Name="PlayArea",Dock=DockStyle.Fill,Padding=new Padding(4,8,12,4),MinimumSize=new Size(0,58),Margin=Padding.Empty};
        launch.Dock=DockStyle.Top;launch.Height=42;launch.Margin=Padding.Empty;
        playArea.Controls.Add(launch);footer.Controls.Add(playArea,0,0);
        var footerContents=Stack();footerContents.Name="FooterContents";footerContents.Margin=Padding.Empty;
        footerContents.SizeChanged+=(_,_)=>profileBanner.MaximumSize=new Size(Math.Max(160,footerContents.ClientSize.Width-8),0);
        footer.Controls.Add(footerContents,1,0);
        status.AutoSize=false;status.AutoEllipsis=true;status.TextAlign=ContentAlignment.MiddleLeft;status.Height=30;status.Margin=Padding.Empty;
        profileBanner.Padding=new Padding(5,3,5,3);profileBanner.Margin=Padding.Empty;
        profileBanner.Font=new Font(Font.FontFamily,9);
        var links = new FlowLayoutPanel { Name = "SocialLinks", AutoSize = true, Anchor = AnchorStyles.None, WrapContents = false };
        AddSocialLink(links, "GitLink", "https://github.com/Bezimienny111/FM08-Extended");
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
        communityLinks = new CommunityLinksPage(localizer,
            socialLinks.Select(button => new CommunityLink(button.Name, (string)button.Tag!, true)).ToArray(),
            url => Execute(() =>
            {
                try { Process.Start(new ProcessStartInfo(url) { UseShellExecute = true }); }
                catch (Exception error) when (error is Win32Exception or InvalidOperationException)
                { throw new LauncherException("LinkOpenError", error.Message); }
            }));
        tabs.TabPages.Add(communityLinks);
        tabs.TabPages.Add(preferencesPage);
        var featurePage=tabs.TabPages.Cast<TabPage>().Single(page=>page.Name=="Settings");
        var graphicsPage=tabs.TabPages.Cast<TabPage>().Single(page=>page.Name=="Graphics");
        tabs.TabPages.Clear();
        tabs.TabPages.AddRange([preferencesPage,graphicsPage,skinGuide,featurePage,communityLinks]);
        tabs.SelectedTab=preferencesPage;
        var linkRow = new TableLayoutPanel
        {
            Name = "FooterLinks", Dock = DockStyle.Top, AutoSize = true,
            ColumnCount = 3, Margin = Padding.Empty
        };
        linkRow.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        linkRow.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
        linkRow.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
        linkRow.Controls.Add(status,0,0);
        linkRow.Controls.Add(links, 1, 0);
        linkRow.Controls.Add(support, 2, 0);
        foreach(var social in socialLinks){social.Size=social.Name=="DonateLink"?new Size(40,32):new Size(32,30);social.Margin=new Padding(2,0,2,0);}
        footerContents.Controls.Add(linkRow);
        footerContents.Controls.Add(profileBanner);
        launchLog = new LaunchLogPanel(localizer, launcher.LaunchJournal);
        launchLog.Dock = DockStyle.Top;
        launchLog.Margin = new Padding(0,2,0,0);
        footerContents.Controls.Add(launchLog);
        Controls.Add(footer);
        Controls.Add(header);
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
        FormClosing += (_, args) =>
        {
            try{SaveConfigurationOnClose();}
            catch(LauncherException error){args.Cancel=true;ShowError(error);return;}
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
        paLogOpen.Visible = paStatistics.Visible = paLogStatus.Visible = advanced;
        leagueReputation.SetAdvancedMode(advanced);
        UpdateFeatureSelectorLayout();
        if (!advanced && selectedFeature?.Name is "LeagueObservationFeature" or "LeagueDiagnosticsFeature")
            ShowFeatureDetails(features.Single(feature => feature.Name == "MatchRulesFeature"));
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
            label.MaximumSize = new Size(Math.Max(160, (label.Parent?.ClientSize.Width ?? ClientSize.Width) - 34), 0);
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
        foreach (var feature in featureContents.Keys) feature.RefreshAppearance();
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
            RefreshFeatureWorkspaceLanguage();
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
            var ruleViewIndex = Math.Max(0, ruleView.SelectedIndex);
            ruleView.Items.Clear();
            ruleView.Items.AddRange(new object[] { localizer.Text("IndividualRuleView"), localizer.Text("GroupedRuleView") });
            ruleView.SelectedIndex = ruleViewIndex;
            groupedRules.ApplyLanguage();
            launchLog.ApplyLanguage();
            skinGuide.ApplyLanguage();
            communityLinks.ApplyLanguage();
            leagueReputation.RefreshLanguage();
            sharedDetails.Text = selectedFeature?.FeatureTitle ?? localizer.Text("Details");
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
        UpdateRuleScope();
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
            if (activeRuleView == 0)
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

    private void SwitchRuleView()
    {
        if (updating || changingRuleView) return;
        changingRuleView = true;
        try
        {
            if (!ValidateChildren() || !rules.EndEdit())
            {
                ruleView.SelectedIndex = activeRuleView;
                throw new LauncherException("InvalidGrid");
            }
            activeRuleView = Math.Max(0, ruleView.SelectedIndex);
            individualRulesView.Visible = activeRuleView == 0;
            groupedRules.Visible = activeRuleView == 1;
            if (activeRuleView == 1) groupedRules.Populate(ReadRuleSettings());
            UpdateRuleScope();
        }
        finally { changingRuleView = false; }
    }

    private void UpdateRuleScope()
    {
        if (activeRuleView == 1)
            ruleScope.Text = string.Join(Environment.NewLine + Environment.NewLine,
                groupedRules.SelectedCodes.Select(code => MatchRuleScope.Details(code, localizer)));
        else SyncEditors();
    }

    private List<RuleSettings> ReadRuleSettings() =>
        rules.Rows.Cast<DataGridViewRow>().Select(row => new RuleSettings
        {
            Code = (int)row.Cells["Code"].Value, Override = (bool)row.Cells["Override"].Value,
            BenchOverride = (bool)row.Cells["BenchOverride"].Value,
            Substitutions = Convert.ToInt32(row.Cells["Substitutions"].Value, CultureInfo.InvariantCulture),
            Bench = Convert.ToInt32(row.Cells["Bench"].Value, CultureInfo.InvariantCulture)
        }).OrderBy(rule => rule.Code).ToList();

    internal void ApplyGroupedChanges(int code, GroupRuleChange substitutions, GroupRuleChange bench)
    {
        var config = CaptureConfiguration();
        MatchRuleGroups.Apply(config.Rules, code, substitutions, bench);
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
        SetStatus("RuleGroupApplied", string.Join(", ", MatchRuleGroups.ForCode(code)));
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
        configurationLoaded=true;
        lastSavedConfiguration=ConfigurationFingerprint(CaptureConfiguration());
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
        positionHighlights.Checked = config.PositionHighlightsEnabled;
        hiddenAttributes.Checked = config.HiddenAttributesEnabled;
        teamTalkReactions.Checked = config.TeamTalkReactionsEnabled;
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
        groupedRules.Populate(ReadRuleSettings());
        SyncEditors();
        UpdateRuleScope();
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
            PositionHighlightsEnabled = positionHighlights.Checked,
            HiddenAttributesEnabled = hiddenAttributes.Checked,
            TeamTalkReactionsEnabled = teamTalkReactions.Checked,
            LeagueReputationEnabled = leagueReputation.ObservationEnabled,
            LeagueDiagnosticsEnabled = leagueReputation.DiagnosticsEnabled,
            LeagueChangesEnabled = leagueReputation.ChangesEnabled,
            Rules = ReadRuleSettings()
        };
        ConfigurationValidator.Validate(config);
        return config;
    }

    private static string ConfigurationFingerprint(LauncherConfiguration config) =>
        System.Text.Json.JsonSerializer.Serialize(config,ConfigurationStore.JsonOptions)+"\n"+config.TeamTalkReactionsEnabled;

    private void PersistConfiguration(LauncherConfiguration config)
    {
        store.Save(config);
        lastSavedConfiguration=ConfigurationFingerprint(config);
    }

    internal void SaveConfigurationOnClose()
    {
        // Never replace an unreadable/newer configuration with model defaults.
        if(!configurationLoaded || configurationBlocked)return;
        var config=CaptureConfiguration();
        if(ConfigurationFingerprint(config)!=lastSavedConfiguration)PersistConfiguration(config);
    }

    private void LaunchGame() => LaunchGame(
        config =>
        {
            try { launcher.Launch(config, localizer); }
            finally { launchLog.RefreshJournal(); }
        });

    internal void LaunchGame(Action<LauncherConfiguration> start)
    {
        if (configurationBlocked) throw new LauncherException("ConfigBlocked");
        var config = CaptureConfiguration();
        ConfigurationValidator.ValidateDisplay(config, DetectSelectedDisplay());
        PersistConfiguration(config);
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
        retryConfiguration.Visible=configurationBlocked;
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
