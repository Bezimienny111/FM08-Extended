using System.ComponentModel;
using System.Diagnostics;

namespace FmLauncher;

internal sealed class LeagueReputationPage : UserControl
{
    private readonly Localizer localizer;
    private readonly Func<string> gamePath;
    private readonly Action<Action> execute;
    private readonly LeagueObserver observer;
    private readonly GameLauncher launcher;
    private readonly Func<bool> isDarkMode;
    private readonly ToggleSwitch enabled = new() { Name = "LeagueReputationEnabled" };
    private readonly ToggleSwitch diagnostics = new() { Name = "LeagueDiagnosticsEnabled" };
    private readonly Label diagnosticNotice = new() { AutoSize = true, Dock = DockStyle.Top };
    private readonly Label diagnosticStatus = new() { Name = "LeagueDiagnosticsStatus", AutoSize = true, Dock = DockStyle.Top };
    private readonly Button diagnosticOpen = new() { Name = "LeagueDiagnosticsOpen", AutoSize = true };
    private string baselineStamp = "";
    private readonly Label notice = new() { AutoSize = true, Dock = DockStyle.Top };
    private readonly Label status = new() { Name = "LeagueReputationStatus", AutoSize = true, Dock = DockStyle.Top };
    private readonly Button baseline = new() { Name = "LeagueBaseline", AutoSize = true };
    private readonly Button capture = new() { Name = "LeagueCapture", AutoSize = true };
    private readonly Button report = new() { Name = "LeagueReport", AutoSize = true };
    private readonly Button open = new() { Name = "LeagueReportOpen", AutoSize = true };
    private Form? reportWindow;
    private DataGridView? reportGrid;
    private readonly ToggleSwitch changes = new() { Name = "LeagueChangesEnabled" };
    private readonly FeatureSection changesSection;
    private readonly FeatureSection observationSection;
    private readonly FeatureSection diagnosticSection;
    private readonly Label changesNotice = new() { AutoSize = true, Dock = DockStyle.Top };
    private readonly Label changesStatus = new() { Name = "LeagueChangesStatus", AutoSize = true, Dock = DockStyle.Top };
    private readonly Button newProfile = new() { Name = "LeagueNewProfile", AutoSize = true };
    private readonly Button loadProfile = new() { Name = "LeagueLoadProfile", AutoSize = true };
    private readonly Button changeLog = new() { Name = "LeagueChangeLog", AutoSize = true };
    private LeagueChangeLogForm? changeWindow;
    private readonly LeagueProfileAutomation profiles;
    private readonly Button retryProfile = new() { Name = "LeagueRetryProfile", AutoSize = true };
    internal event Action? ProfileStatusChanged;
    internal event Action? AdvancedToolsChanged;
    internal string ProfileStatusText => changesStatus.Text;
    internal Color ProfileStatusColor => changesStatus.BackColor;

    internal bool ChangesEnabled
    {
        get => changes.Checked;
        set => changes.Checked = value;
    }

    internal bool ObservationEnabled
    {
        get => enabled.Checked;
        set => enabled.Checked = value;
    }

    internal bool DiagnosticsEnabled
    {
        get => diagnostics.Checked;
        set => diagnostics.Checked = value;
    }

    internal LeagueReputationPage(Localizer localizer, Func<string> gamePath, Action<Action> execute, string directory,
        GameLauncher launcher, Func<bool>? isDarkMode = null)
    {
        this.localizer = localizer;
        this.gamePath = gamePath;
        this.execute = execute;
        this.launcher = launcher;
        this.isDarkMode = isDarkMode ?? (() => false);
        profiles = new LeagueProfileAutomation(Path.Combine(directory, "profils"),
            Path.Combine(directory, "league-profiles"));
        observer = new LeagueObserver(Path.Combine(directory, "league-observations"));
        Name = "LeagueReputation";
        Dock = DockStyle.Top;
        AutoSize = true;
        AutoSizeMode = AutoSizeMode.GrowAndShrink;
        Margin = Padding.Empty;
        var content = new TableLayoutPanel
        {
            Dock = DockStyle.Top, AutoSize = true, AutoSizeMode = AutoSizeMode.GrowAndShrink,
            ColumnCount = 1, Margin = Padding.Empty
        };
        content.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        var buttons = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Top };
        buttons.Controls.AddRange([baseline, capture, report, open]);
        var changeButtons = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Top };
        changeButtons.Controls.AddRange([newProfile, loadProfile, retryProfile, changeLog]);
        changesStatus.Padding = new Padding(10);
        changesStatus.BorderStyle = BorderStyle.FixedSingle;
        static TableLayoutPanel Details(params Control[] controls)
        {
            var panel = new TableLayoutPanel
            {
                Dock = DockStyle.Top, AutoSize = true, AutoSizeMode = AutoSizeMode.GrowAndShrink,
                ColumnCount = 1, Margin = Padding.Empty
            };
            panel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
            panel.Controls.AddRange(controls);
            return panel;
        }
        changesSection = new FeatureSection("LeagueChangesFeature", changes,
            Details(changesNotice, changeButtons, changesStatus), localizer);
        observationSection = new FeatureSection("LeagueObservationFeature", enabled,
            Details(notice, buttons, status), localizer);
        diagnosticSection = new FeatureSection("LeagueDiagnosticsFeature", diagnostics,
            Details(diagnosticNotice, diagnosticOpen, diagnosticStatus), localizer);
        content.Controls.AddRange([changesSection, observationSection, diagnosticSection]);
        Controls.Add(content);
        SizeChanged += (_, _) =>
        {
            notice.MaximumSize = status.MaximumSize = new Size(Math.Max(200, Width - 50), 0);
            diagnosticNotice.MaximumSize = diagnosticStatus.MaximumSize = notice.MaximumSize;
            changesNotice.MaximumSize = changesStatus.MaximumSize = notice.MaximumSize;
        };
        enabled.CheckedChanged += (_, _) =>
        {
            if (!enabled.Checked) observer.Fail(new LauncherException("LeagueRestartRequired"));
            RefreshLanguage();
            AdvancedToolsChanged?.Invoke();
        };
        diagnostics.CheckedChanged += (_, _) => AdvancedToolsChanged?.Invoke();
        baseline.Click += (_, _) => execute(() => Read(baseline: true));
        capture.Click += (_, _) => execute(() => Read(baseline: false));
        report.Click += (_, _) => ShowReport();
        open.Click += (_, _) => execute(() =>
        {
            try
            {
                Process.Start(new ProcessStartInfo
                {
                    FileName = observer.ReportPath ?? throw new LauncherException("LeagueBaselineRequired"),
                    UseShellExecute = true
                });
            }
            catch (Exception ex) when (ex is Win32Exception or InvalidOperationException)
            {
                throw new LauncherException("LeagueOpenError", ex.Message);
            }
        });
        diagnosticOpen.Click += (_, _) => execute(() =>
        {
            try
            {
                Process.Start(new ProcessStartInfo
                {
                    FileName = launcher.LeagueDiagnostics.LogPath ?? throw new LauncherException("LeagueDiagnosticsNotStarted"),
                    UseShellExecute = true
                });
            }
            catch (Exception ex) when (ex is Win32Exception or InvalidOperationException)
            {
                throw new LauncherException("LeagueOpenError", ex.Message);
            }
        });
        changes.CheckedChanged += (_, _) => execute(() =>
        {
            if (!changes.Checked) launcher.LeagueChanges.Disarm();
            profiles.Reset();
            RefreshLanguage();
        });
        newProfile.Click += (_, _) => execute(() => BindChanges(create: true));
        loadProfile.Click += (_, _) => execute(() => BindChanges(create: false));
        retryProfile.Click += (_, _) => execute(() =>
        {
            profiles.Reset();
            UpdateRuntime();
        });
        changeLog.Click += (_, _) =>
        {
            if (changeWindow is null || changeWindow.IsDisposed)
            {
                changeWindow = new LeagueChangeLogForm(localizer, launcher.LeagueChanges);
                changeWindow.Show(FindForm());
                LauncherTheme.Apply(changeWindow, this.isDarkMode());
            }
            changeWindow.RefreshJournal();
            if (changeWindow.WindowState == FormWindowState.Minimized) changeWindow.WindowState = FormWindowState.Normal;
            changeWindow.Activate();
        };
        RefreshLanguage();
    }

    internal void ShowChanges() => changesSection.Expanded = true;

    internal void SetAdvancedMode(bool advanced)
    {
        observationSection.Visible = diagnosticSection.Visible = changeLog.Visible = advanced;
        if (!advanced)
        {
            observationSection.Expanded = diagnosticSection.Expanded = false;
            if (reportWindow is { IsDisposed: false }) reportWindow.Close();
            if (changeWindow is { IsDisposed: false }) changeWindow.Close();
        }
    }

    private void BindChanges(bool create)
    {
        if (!changes.Checked || !launcher.LeagueChanges.Installed || !launcher.IsRunning)
            throw new LauncherException("LeagueChangesRestart");
        if (MessageBox.Show(this, localizer.Text("LeagueProfileConfirm"), localizer.Text("WarningTitle"),
            MessageBoxButtons.OKCancel, MessageBoxIcon.Warning, MessageBoxDefaultButton.Button2) != DialogResult.OK) return;
        launcher.LeagueChanges.Disarm();
        if (create)
            profiles.Create(launcher.CaptureCurrentLeagueSnapshot(), launcher.LeagueDiagnostics.Stamp, launcher.LeagueChanges);
        else
        {
            using var dialog = new OpenFileDialog { CheckFileExists = true, Filter = "JSON (*.json)|*.json",
                InitialDirectory = Directory.Exists(profiles.DirectoryPath) ? profiles.DirectoryPath : AppContext.BaseDirectory };
            if (dialog.ShowDialog(this) != DialogResult.OK) return;
            profiles.Remember(LeagueCareerProfile.Load(dialog.FileName), launcher.CaptureCurrentLeagueSnapshot(),
                launcher.LeagueDiagnostics.Stamp, launcher.LeagueChanges);
        }
        RefreshLanguage();
    }

    private void Read(bool baseline)
    {
        if (!enabled.Checked) throw new LauncherException("LeagueDisabled");
        if (MessageBox.Show(this, localizer.Text(baseline ? "LeagueBaselineConfirm" : "LeagueCaptureConfirm"),
            localizer.Text("WarningTitle"), MessageBoxButtons.OKCancel, MessageBoxIcon.Warning,
            MessageBoxDefaultButton.Button2) != DialogResult.OK) return;
        try
        {
            var path = gamePath();
            using var verified = MatchRulePatch.OpenVerifiedGame(path);
            var candidates = Process.GetProcessesByName(Path.GetFileNameWithoutExtension(path));
            try
            {
                if (candidates.Length != 1 || candidates[0].HasExited)
                    throw new LauncherException("LeagueGameRequired");
                if (!string.Equals(candidates[0].MainModule?.FileName, Path.GetFullPath(path), StringComparison.OrdinalIgnoreCase))
                    throw new LauncherException("LeagueGameRequired");
                UpdateRuntime();
                observer.Capture(launcher.CaptureLeagueSnapshot(candidates[0]), baseline);
                baselineStamp = launcher.LeagueDiagnostics.Stamp;
            }
            finally
            {
                foreach (var candidate in candidates) candidate.Dispose();
            }
        }
        catch (Exception ex) when (ex is Win32Exception or InvalidOperationException)
        {
            var error = new LauncherException("LeagueReadError", ex.Message);
            observer.Fail(error);
            throw error;
        }
        catch (LauncherException ex)
        {
            observer.Fail(ex);
            throw;
        }
        finally { RefreshLanguage(); }
        ShowReport();
    }

    internal void RefreshLanguage()
    {
        changesSection.RefreshLanguage();
        observationSection.RefreshLanguage();
        diagnosticSection.RefreshLanguage();
        Text = localizer.Text("LeagueTab");
        changes.Text = localizer.Text("LeagueChangesEnabled");
        changesNotice.Text = localizer.Text("LeagueChangesNotice");
        newProfile.Text = localizer.Text("LeagueNewProfile");
        loadProfile.Text = localizer.Text("LeagueLoadProfile");
        changeLog.Text = localizer.Text("LeagueChangeLog");
        retryProfile.Text = localizer.Text("LeagueAutoRetry");
        newProfile.Enabled = loadProfile.Enabled = changes.Checked && launcher.IsRunning && launcher.LeagueChanges.Installed;
        retryProfile.Enabled = newProfile.Enabled;
        var profileText = profiles.Selected is { } selected && profiles.ProfilePath is { } selectedPath
            ? localizer.Text(profiles.StatusKey, Path.GetFileName(selectedPath),
                selected.Baseline.Date, launcher.LeagueChanges.Events.Count)
            : localizer.Text(profiles.StatusKey);
        changesStatus.Text = launcher.LeagueChanges.Error is { } changeError ? localizer.Error(changeError)
            : profiles.Error is { } profileError ? profileText + Environment.NewLine + localizer.Error(profileError)
            : profileText;
        changesStatus.BackColor = !changes.Checked ? LauncherTheme.Surface(isDarkMode())
            : launcher.LeagueChanges.Armed ? LauncherTheme.Success(isDarkMode()) : LauncherTheme.Warning(isDarkMode());
        ProfileStatusChanged?.Invoke();
        if (changeWindow is not null && !changeWindow.IsDisposed) changeWindow.RefreshJournal();
        enabled.Text = localizer.Text("LeagueEnabled");
        notice.Text = localizer.Text("LeagueNotice");
        baseline.Text = localizer.Text("LeagueBaseline");
        capture.Text = localizer.Text("LeagueCapture");
        report.Text = localizer.Text("LeagueReport");
        open.Text = localizer.Text("LeagueReportOpen");
        diagnostics.Text = localizer.Text("LeagueDiagnosticsEnabled");
        diagnosticNotice.Text = localizer.Text("LeagueDiagnosticsNotice");
        diagnosticOpen.Text = localizer.Text("LeagueDiagnosticsOpen");
        var runtime = launcher.LeagueDiagnostics;
        diagnosticOpen.Enabled = runtime.LogPath is not null;
        diagnosticStatus.Text = runtime.Error is { } diagnosticError ? localizer.Error(diagnosticError)
            : runtime.LogPath is not null
                ? localizer.Text(runtime.Installed ? "LeagueDiagnosticsStatus" : "LeagueDiagnosticsFinished",
                    runtime.Events.Count, runtime.Generation, runtime.ActiveLoads, runtime.LogPath)
                : localizer.Text("LeagueDiagnosticsNotStarted");
        baseline.Enabled = enabled.Checked;
        capture.Enabled = enabled.Checked && observer.Report is not null && observer.Error is null;
        report.Enabled = open.Enabled = observer.Report is not null;
        status.Text = observer.Error is { } error && enabled.Checked
            ? localizer.Error(error)
            : observer.Report is { } current
                ? localizer.Text("LeagueStatus", current.Observations[^1].Snapshot.Date,
                    current.Observations.Length, observer.ReportPath!)
                : localizer.Text("LeagueNoBaseline");
        if (reportWindow is not null && !reportWindow.IsDisposed) UpdateReport();
    }

    internal void UpdateRuntime()
    {
        observer.CheckDiagnostics(baselineStamp, launcher.LeagueDiagnostics);
        if (changes.Checked && launcher.IsRunning && launcher.LeagueChanges.Installed)
            profiles.Update(launcher.LeagueDiagnostics, launcher.LeagueChanges,
                launcher.CaptureCurrentCareer, launcher.CaptureCurrentLeagueSnapshot);
        else profiles.Reset();
        RefreshLanguage();
    }

    private void ShowReport()
    {
        if (observer.Report is null) return;
        if (reportWindow is null || reportWindow.IsDisposed)
        {
            reportWindow = new Form
            {
                Size = new Size(1250, 650), MinimumSize = new Size(750, 400),
                StartPosition = FormStartPosition.CenterParent, Font = Font
            };
            reportGrid = new DataGridView
            {
                Dock = DockStyle.Fill, ReadOnly = true, AllowUserToAddRows = false,
                AllowUserToDeleteRows = false, RowHeadersVisible = false,
                AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.DisplayedCells,
                AutoGenerateColumns = false
            };
            foreach (var key in new[] { "LeagueCountry", "LeagueName", "LeagueActual", "LeagueStart",
                "LeagueCoefficientStart", "LeagueCoefficient", "LeagueTarget", "LeagueSimulated", "LeagueStreak" })
                reportGrid.Columns.Add(new DataGridViewTextBoxColumn { Name = key, SortMode = DataGridViewColumnSortMode.Automatic });
            reportWindow.Controls.Add(reportGrid);
            reportWindow.Show(FindForm());
            LauncherTheme.Apply(reportWindow, isDarkMode());
        }
        UpdateReport();
        if (reportWindow.WindowState == FormWindowState.Minimized) reportWindow.WindowState = FormWindowState.Normal;
        reportWindow.Activate();
    }

    private void UpdateReport()
    {
        if (reportWindow is null || reportGrid is null || observer.Report is null) return;
        reportWindow.Text = localizer.Text("LeagueReport") + " - " + observer.Report.Observations[^1].Snapshot.Date;
        foreach (DataGridViewColumn column in reportGrid.Columns) column.HeaderText = localizer.Text(column.Name);
        reportGrid.Rows.Clear();
        foreach (var row in observer.Report.Observations[^1].Projections)
            reportGrid.Rows.Add(row.Nation, row.Name, row.Actual, row.Baseline,
                row.BaselineCoefficient, row.Coefficient, row.Target, row.Simulated, row.Streak);
        reportGrid.Columns["LeagueCoefficientStart"].DefaultCellStyle.Format = "F3";
        reportGrid.Columns["LeagueCoefficient"].DefaultCellStyle.Format = "F3";
    }
}
