using System.Runtime.InteropServices;
using System.Security;

namespace FmLauncher;

internal sealed class SkinGuidePage : TabPage
{
    private readonly Localizer localizer;
    private readonly Func<bool> isDarkMode;
    private readonly Label heading = new() { AutoSize = true, Dock = DockStyle.Top };
    private readonly TextBox instructions = new()
    {
        Name = "SkinInstructions", Multiline = true, ReadOnly = true, ScrollBars = ScrollBars.Vertical,
        Dock = DockStyle.Top, Height = 190, BackColor = SystemColors.Window
    };
    private readonly Label runtime = new() { Name = "PanelRuntimeStatus", AutoSize = true, Dock = DockStyle.Top };
    private readonly ComboBox snippets = new ThemedComboBox { Name = "SkinSnippetChoice", DropDownStyle = ComboBoxStyle.DropDownList, Width = 350 };
    private readonly TextBox xml = new()
    {
        Name = "SkinSnippet", Multiline = true, ReadOnly = true, WordWrap = false, ScrollBars = ScrollBars.Both,
        Dock = DockStyle.Fill, Font = new Font("Consolas", 10), BackColor = SystemColors.Window
    };
    private readonly Button copy = new() { Name = "CopySkinSnippet", AutoSize = true };
    private readonly Button install = new() { Name = "InstallSkinPanels", AutoSize = true };
    private readonly Label result = new() { AutoSize = true, Dock = DockStyle.Bottom };
    private PanelStatistics? statistics;
    private bool running;

    internal SkinGuidePage(Localizer localizer, Func<string> gamePath, Func<string> userDataPath, Action<Action> execute,
        Func<bool>? isDarkMode = null)
    {
        this.localizer = localizer;
        this.isDarkMode = isDarkMode ?? (() => false);
        Name = "SkinGuide";
        Padding = new Padding(12);
        var actions = new FlowLayoutPanel { Dock = DockStyle.Top, AutoSize = true, WrapContents = true };
        actions.Controls.AddRange([snippets, copy, install]);
        Controls.Add(xml);
        Controls.Add(result);
        Controls.Add(actions);
        Controls.Add(runtime);
        Controls.Add(instructions);
        Controls.Add(heading);
        snippets.Items.AddRange(["", "", "", ""]);
        snippets.SelectedIndex = 0;
        snippets.SelectedIndexChanged += (_, _) => UpdateSnippet();
        copy.Click += (_, _) => execute(() =>
        {
            try { Clipboard.SetText(xml.Text); }
            catch (ExternalException error) { throw new LauncherException("SkinClipboardError", error.Message); }
            result.Text = localizer.Text("SkinCopied");
        });
        install.Click += (_, _) => execute(() =>
        {
            using var dialog = new FolderBrowserDialog
            {
                Description = localizer.Text("SkinChooseDirectory"),
                InitialDirectory = InitialSkinDirectory(gamePath(), userDataPath()),
                ShowNewFolderButton = false
            };
            if (dialog.ShowDialog(this) != DialogResult.OK) return;
            using var verified = MatchRulePatch.OpenVerifiedGame(gamePath());
            var count = SkinPanelInstaller.Install(gamePath(), dialog.SelectedPath, localizer.Text("PanelFatigueTitle"));
            result.Text = localizer.Text("SkinInstalled", count, dialog.SelectedPath);
        });
        SizeChanged += (_, _) =>
        {
            runtime.MaximumSize = result.MaximumSize = new Size(Math.Max(200, ClientSize.Width - 30), 0);
        };
        ApplyLanguage();
    }

    internal static string InitialSkinDirectory(string gamePath, string userDataPath)
    {
        var candidate = string.IsNullOrWhiteSpace(userDataPath)
            ? Path.Combine(Path.GetDirectoryName(gamePath) ?? "", "Dane", "skins")
            : Path.Combine(userDataPath, "skins");
        if (Directory.Exists(candidate)) return candidate;
        if (!string.IsNullOrWhiteSpace(userDataPath) && Directory.Exists(userDataPath)) return userDataPath;
        return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),
            "Sports Interactive", "Football Manager 2008", "skins");
    }

    internal void ApplyLanguage()
    {
        Text = localizer.Text("SkinTab");
        heading.Text = localizer.Text("SkinHeading");
        instructions.Text = localizer.Text("SkinRefreshNotice") + Environment.NewLine + Environment.NewLine
            + localizer.Text("SkinInstructions") + Environment.NewLine + Environment.NewLine
            + localizer.Text("SkinEditViews") + Environment.NewLine + Environment.NewLine
            + localizer.Text("SkinColumnRegistryInstructions");
        copy.Text = localizer.Text("SkinCopy");
        install.Text = localizer.Text("SkinInstall");
        var selected = snippets.SelectedIndex;
        for (var i = 0; i < snippets.Items.Count; i++) snippets.Items[i] = localizer.Text("SkinSnippet" + i);
        snippets.SelectedIndex = selected;
        result.Text = "";
        UpdateSnippet();
        UpdateRuntime(statistics, running);
    }

    private void UpdateSnippet() => xml.Text = snippets.SelectedIndex switch
    {
        0 => SkinPanelInstaller.TrainingFragment.Replace("Zmęczenie sezonowe",
            SecurityElement.Escape(localizer.Text("PanelFatigueTitle")), StringComparison.Ordinal),
        1 => SkinPanelInstaller.SquadFragment,
        2 => SkinPanelInstaller.TacticsFragment,
        3 => SkinPanelInstaller.ColumnRegistryFragment(localizer.Text("PanelFatigueTitle")),
        _ => throw new InvalidOperationException("No skin snippet selected.")
    };

    internal void UpdateRuntime(PanelStatistics? value, bool isRunning)
    {
        statistics = value;
        running = isRunning;
        install.Enabled = !running;
        runtime.Text = value is null ? localizer.Text(running ? "PanelNotActive" : "PanelNotRunning")
            : localizer.Text("PanelStatistics", value.Reads, value.Hidden, value.Invalid, value.TrainingUpdates);
        runtime.ForeColor = value is { Invalid: > 0 } ? LauncherTheme.Error(isDarkMode()) : LauncherTheme.Text(isDarkMode());
    }
}
