namespace FmLauncher;

internal sealed class LeagueChangeLogForm : Form
{
    private readonly Localizer localizer;
    private readonly LeagueChanges journal;
    private readonly DataGridView grid = new()
    {
        Name = "LeagueChangeEntries", Dock = DockStyle.Fill, ReadOnly = true,
        AllowUserToAddRows = false, AllowUserToDeleteRows = false, RowHeadersVisible = false,
        AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.DisplayedCells
    };
    private readonly Label status = new() { Dock = DockStyle.Bottom, AutoSize = true, Padding = new Padding(8) };
    private int displayed = -1;

    internal LeagueChangeLogForm(Localizer localizer, LeagueChanges journal)
    {
        this.localizer = localizer;
        this.journal = journal;
        Name = "LeagueChangeLogWindow";
        Font = new Font("Segoe UI", 10);
        AutoScaleMode = AutoScaleMode.Dpi;
        Size = new Size(1100, 500);
        MinimumSize = new Size(750, 350);
        StartPosition = FormStartPosition.CenterParent;
        foreach (var key in new[] { "LeagueChangeDate", "LeagueCountry", "LeagueName", "LeagueChangeBefore",
            "LeagueChangeAfter", "LeagueTarget", "LeagueCoefficient" })
            grid.Columns.Add(new DataGridViewTextBoxColumn
            {
                Name = key, SortMode = DataGridViewColumnSortMode.Automatic
            });
        Controls.Add(grid);
        Controls.Add(status);
        RefreshJournal();
    }

    internal void RefreshJournal()
    {
        Text = localizer.Text("LeagueChangeLog");
        foreach (DataGridViewColumn column in grid.Columns) column.HeaderText = localizer.Text(column.Name);
        if (displayed != journal.Events.Count)
        {
            grid.Rows.Clear();
            foreach (var entry in journal.Events)
                grid.Rows.Add(entry.Date, entry.Nation, entry.League, entry.Previous,
                    entry.Current, entry.Target, entry.Coefficient);
            displayed = journal.Events.Count;
        }
        grid.Columns["LeagueChangeDate"].DefaultCellStyle.Format = "yyyy-MM-dd";
        grid.Columns["LeagueCoefficient"].DefaultCellStyle.Format = "F3";
        status.MaximumSize = new Size(Math.Max(200, ClientSize.Width - 20), 0);
        status.Text = journal.Error is { } error ? localizer.Error(error)
            : localizer.Text("LeagueChangeSummary", journal.Events.Count, journal.LogPath ?? "");
    }
}
