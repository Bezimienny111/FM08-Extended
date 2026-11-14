namespace FmLauncher;

internal sealed class TeamTalkDiagnosticsPage : TabPage
{
    private readonly TextBox status = new() { Multiline = true, ReadOnly = true, Dock = DockStyle.Top, Height = 150 };
    private readonly DataGridView rows = new() { Dock = DockStyle.Fill, ReadOnly = true,
        AllowUserToAddRows = false, AllowUserToDeleteRows = false, AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill };
    private readonly ITeamTalkObservationProvider provider = new OfflineTeamTalkProvider();
    private readonly Button load = new() { Text = "Load frozen capture", AutoSize = true };
    internal TeamTalkDiagnosticsPage()
    {
        Text = "Team talks DEV";
        var notice = new Label { Text = "OFFLINE DIAGNOSTIC ONLY. No game memory access. Reaction publication in FM is BLOCKED.",
            Dock = DockStyle.Top, Height = 60, Padding = new Padding(8), ForeColor = Color.DarkRed };
        var buttons = new FlowLayoutPanel { Dock = DockStyle.Top, Height = 42 };
        buttons.Controls.Add(load);
        Controls.Add(rows); Controls.Add(status); Controls.Add(buttons); Controls.Add(notice);
        status.Text = "Select a MATCH capture, then the separately captured frontend HUMAN. " +
            "Later HUMAN correlation is not simultaneous own-scope proof. Completion and full-time boundary remain unverified.";
        load.Click += async (_, _) => await LoadCapture();
    }
    private async Task LoadCapture()
    {
        rows.DataSource = null; // Every failed/changed context invalidates the previous result.
        status.Text = "No current observation.";
        using var picker = new OpenFileDialog { Filter = "JSON capture|*.json", Title = "Select frozen MATCH capture" };
        if (picker.ShowDialog(this) != DialogResult.OK) return;
        string match = picker.FileName;
        picker.Title = "Select frozen frontend HUMAN capture";
        if (picker.ShowDialog(this) != DialogResult.OK) return;
        load.Enabled = false;
        try
        {
            var pinned = new TeamTalkProcess(8020, 134389467680297377,
                "157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d");
            var result = await provider.ReadAsync(new(pinned, match, picker.FileName), CancellationToken.None);
            status.Text = $"{result.Source}\r\nKind: {result.Kind}; raw phase: {result.RawPhase}; tick: {result.Tick}; " +
                $"stored phase: {result.StoredPhase}; counter: {result.Counter}\r\n" +
                $"HUMAN {result.HumanUid}; TEAM {result.TeamUid}; current phase relevance: {result.Relevant}\r\n" +
                "Completion: UNVERIFIED. Own scope: later correlation only. Publication in FM: BLOCKED.";
            rows.DataSource = result.Players.Select(p => new { UID = p.Uid, RawEffect = $"0x{p.RawEffect:X}",
                Context = result.Relevant ? "current phase diagnostic" : "stored prior/staged talk; not current reaction" }).ToArray();
        }
        catch (Exception error) when (error is IOException or System.Text.Json.JsonException or InvalidOperationException or KeyNotFoundException)
        {
            rows.DataSource = null;
            status.Text = "REJECTED; previous observation cleared. " + error.Message;
        }
        finally { load.Enabled = true; }
    }
}
