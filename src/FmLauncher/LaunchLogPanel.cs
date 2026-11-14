namespace FmLauncher;

internal sealed class LaunchLogPanel : UserControl
{
    private readonly Localizer localizer;
    private readonly Button header = new()
    {
        Name = "LaunchLogExpand", Dock = DockStyle.Top, Height = 32, FlatStyle = FlatStyle.Flat,
        TextAlign = ContentAlignment.MiddleLeft, AutoEllipsis = true
    };
    private readonly Panel content = new() { Dock = DockStyle.Fill };
    private readonly TextBox log = new()
    {
        Name = "LaunchLogEntries", Dock = DockStyle.Fill, Multiline = true, ReadOnly = true,
        ScrollBars = ScrollBars.Vertical, WordWrap = true
    };
    private readonly Label notice = new()
    {
        Name = "LaunchLogEvidence", Dock = DockStyle.Bottom, Height = 55, Padding = new Padding(6, 3, 6, 3)
    };
    private readonly System.Windows.Forms.Timer timer = new() { Interval = 500 };
    private string previous = "";
    internal LaunchJournal Journal { get; }
    private bool expanded;
    internal bool Expanded
    {
        get => expanded;
        set
        {
            expanded = value;
            content.Visible = value;
            Height = (int)Math.Round((value ? 180 : 34) * DeviceDpi / 96f);
            RefreshJournal();
        }
    }

    internal LaunchLogPanel(Localizer localizer, LaunchJournal journal)
    {
        this.localizer = localizer;
        Journal = journal;
        Name = "LaunchLogPanel";
        Dock = DockStyle.Bottom;
        Padding = new Padding(1);
        content.Controls.Add(log);
        content.Controls.Add(notice);
        Controls.Add(content);
        Controls.Add(header);
        header.Click += (_, _) => Expanded = !Expanded;
        timer.Tick += (_, _) => RefreshJournal();
        timer.Start();
        Expanded = false;
        ApplyLanguage();
    }

    internal void ApplyLanguage()
    {
        notice.Text = localizer.Text("LaunchLogPanelEvidence");
        previous = "";
        RefreshJournal();
    }

    internal void RefreshJournal()
    {
        header.Text = (Expanded ? "▼  " : "▶  ") + localizer.Text("LaunchLogPanelHeading", Journal.Entries.Count);
        header.AccessibleName = localizer.Text(Expanded ? "CollapseLaunchLog" : "ExpandLaunchLog");
        var text = Journal.Entries.Count == 0 ? localizer.Text("LaunchLogEmpty")
            : string.Join(Environment.NewLine, Journal.Entries.Select(entry =>
                entry.Time.ToLocalTime().ToString("HH:mm:ss") + "  " + LaunchJournal.Format(entry, localizer)));
        if (previous == text) return;
        previous = text;
        log.Text = text;
        log.SelectionStart = log.TextLength;
        if (Expanded) log.ScrollToCaret();
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing) timer.Dispose();
        base.Dispose(disposing);
    }
}
