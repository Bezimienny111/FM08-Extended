namespace FmLauncher;

internal sealed class PaLogForm : Form
{
    private readonly Localizer localizer;
    private readonly GamePaJournal journal;
    private readonly DataGridView grid = new()
    {
        Name = "PaLogEntries", Dock = DockStyle.Fill, ReadOnly = true, VirtualMode = true,
        AllowUserToAddRows = false, AllowUserToDeleteRows = false, RowHeadersVisible = false,
        AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
        SelectionMode = DataGridViewSelectionMode.FullRowSelect
    };
    private readonly Label status = new() { AutoSize = true, Dock = DockStyle.Bottom, Padding = new Padding(8) };

    internal PaLogForm(Localizer localizer, GamePaJournal journal)
    {
        this.localizer = localizer;
        this.journal = journal;
        Name = "PaLogWindow";
        Font = new Font("Segoe UI", 10);
        AutoScaleMode = AutoScaleMode.Dpi;
        Size = new Size(1050, 500);
        MinimumSize = new Size(700, 300);
        StartPosition = FormStartPosition.CenterParent;
        foreach (var key in new[] { "PaLogId", "PaLogEpoch", "PaLogFirst", "PaLogLast",
            "PaLogCa", "PaLogBefore", "PaLogAfter", "PaLogNameStatus" })
            grid.Columns.Add(new DataGridViewTextBoxColumn { Name = key, SortMode = DataGridViewColumnSortMode.NotSortable });
        grid.CellValueNeeded += (_, e) =>
        {
            if (e.RowIndex >= journal.Entries.Count) return;
            var entry = journal.Entries[e.RowIndex];
            e.Value = e.ColumnIndex switch
            {
                0 => entry.PlayerId,
                1 => entry.Epoch,
                2 => entry.FirstName,
                3 => entry.LastName,
                4 => entry.CurrentAbility,
                5 => entry.Before,
                6 => entry.After,
                _ => entry.NameIncomplete ? localizer.Text("PaLogNameIncomplete") : ""
            };
        };
        Controls.Add(grid);
        Controls.Add(status);
        ApplyLanguage();
    }

    internal void ApplyLanguage()
    {
        Text = localizer.Text("PaLogTitle");
        foreach (DataGridViewColumn column in grid.Columns) column.HeaderText = localizer.Text(column.Name);
        grid.Invalidate();
        RefreshJournal();
    }

    internal static string Status(Localizer localizer, GamePaJournal journal)
    {
        var text = localizer.Text(journal.Entries.Count == 0 ? "PaLogEmpty" : "PaLogSummary", journal.Entries.Count);
        if (journal.Dropped != 0) text += " " + localizer.Text("PaLogDropped", journal.Dropped);
        if (journal.Error is { } error) text += " " + localizer.Text("PaLogReadError", localizer.Error(error));
        return text;
    }

    internal void RefreshJournal()
    {
        var following = grid.RowCount == 0 || grid.FirstDisplayedScrollingRowIndex < 0
            || grid.FirstDisplayedScrollingRowIndex + grid.DisplayedRowCount(false) >= grid.RowCount;
        if (grid.RowCount != journal.Entries.Count)
        {
            grid.RowCount = journal.Entries.Count;
            if (following && grid.RowCount != 0) grid.FirstDisplayedScrollingRowIndex = grid.RowCount - 1;
        }
        status.MaximumSize = new Size(Math.Max(200, ClientSize.Width - 20), 0);
        status.Text = Status(localizer, journal);
    }
}
