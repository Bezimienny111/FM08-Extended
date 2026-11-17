namespace FmLauncher;

internal sealed record CommunityLink(string Title, string Url, bool TranslateTitle = false);

internal sealed class CommunityLinksPage : TabPage
{
    internal static IReadOnlyList<CommunityLink> Community { get; } =
    [
        new("Football Manager 2008 Extended", "https://www.facebook.com/groups/2303383967120548/"),
        new("FMCTH Football Manager Classic Thailand", "https://www.facebook.com/groups/611597612294409/"),
        new("Football Manager 2008", "https://www.facebook.com/groups/1910495955822317/"),
        new("Football manager 2008", "https://www.facebook.com/groups/1199831617320703/"),
        new("FM07HD - display mod for Football Manager 2007 (7.0.2)", "https://github.com/paokkerkir/FM07-HD")
    ];
    private readonly Localizer localizer;
    private readonly GroupBox community = new() { Name = "CommunityGroups", Dock = DockStyle.Top, AutoSize = true, Padding = new Padding(8) };
    private readonly GroupBox project = new() { Name = "CommunityProjectLinks", Dock = DockStyle.Top, AutoSize = true, Padding = new Padding(8) };
    private readonly Label notice = new() { Name = "CommunityLinksNotice", Dock = DockStyle.Top, AutoSize = true, Margin = new Padding(3, 4, 3, 12) };
    private readonly List<(LinkLabel Label, CommunityLink Link)> links = [];
    private readonly List<Label> destinations = [];

    internal CommunityLinksPage(Localizer localizer, IReadOnlyList<CommunityLink> footer, Action<string> open)
    {
        this.localizer = localizer;
        Name = "CommunityLinks";
        var scroll = new Panel { Name = "CommunityLinksScroll", Dock = DockStyle.Fill, AutoScroll = true, Padding = new Padding(12) };
        var columns = new TableLayoutPanel { Name = "CommunityLinksColumns", ColumnCount = 2, Dock = DockStyle.Top, AutoSize = true };
        columns.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
        columns.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
        community.Controls.Add(Build(Community, open));
        project.Controls.Add(Build(footer, open));
        columns.Controls.Add(community, 0, 0);
        columns.Controls.Add(project, 1, 0);
        var stack = new TableLayoutPanel { ColumnCount = 1, Dock = DockStyle.Top, AutoSize = true };
        stack.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        stack.Controls.Add(notice);
        stack.Controls.Add(columns);
        scroll.Controls.Add(stack);
        Controls.Add(scroll);
        SizeChanged += (_, _) => UpdateWidths();
        ApplyLanguage();
    }

    private Control Build(IReadOnlyList<CommunityLink> definitions, Action<string> open)
    {
        var rows = new TableLayoutPanel { Dock = DockStyle.Top, AutoSize = true, ColumnCount = 1, Padding = new Padding(0, 4, 0, 0) };
        rows.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        foreach (var definition in definitions)
        {
            var uri = new Uri(definition.Url, UriKind.Absolute);
            if (uri.Scheme != Uri.UriSchemeHttps) throw new ArgumentException("Community links require HTTPS.");
            var card = new TableLayoutPanel
            {
                Dock = DockStyle.Top, AutoSize = true, ColumnCount = 1, BorderStyle = BorderStyle.FixedSingle,
                Padding = new Padding(9, 7, 9, 7), Margin = new Padding(3, 4, 3, 7)
            };
            card.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
            var title = new LinkLabel
            {
                Name = "CommunityLink" + links.Count, AutoSize = true, Dock = DockStyle.Top,
                LinkBehavior = LinkBehavior.HoverUnderline, Tag = definition.Url,
                Margin = new Padding(0, 0, 0, 5)
            };
            title.LinkClicked += (_, _) => open(definition.Url);
            var destination = new Label
            {
                Name = "CommunityDestination" + links.Count, AutoSize = true, Dock = DockStyle.Top,
                Text = uri.Host + uri.AbsolutePath, Font = new Font("Segoe UI", 9),
                Margin = Padding.Empty
            };
            links.Add((title, definition)); destinations.Add(destination);
            card.Controls.Add(title); card.Controls.Add(destination); rows.Controls.Add(card);
        }
        return rows;
    }

    internal void ApplyLanguage()
    {
        Text = localizer.Text("CommunityLinksTab");
        community.Text = localizer.Text("CommunityGroupsTitle");
        project.Text = localizer.Text("CommunityProjectTitle");
        notice.Text = localizer.Text("CommunityLinksNotice");
        foreach (var (label, link) in links)
        {
            label.Text = link.TranslateTitle ? localizer.Text("Community" + link.Title) : link.Title;
            label.AccessibleName = label.Text;
            label.AccessibleDescription = link.Url;
        }
        UpdateWidths();
    }

    private void UpdateWidths()
    {
        var width = Math.Max(210, (ClientSize.Width - 100) / 2);
        foreach (var (label, _) in links) label.MaximumSize = new Size(width, 0);
        foreach (var destination in destinations) destination.MaximumSize = new Size(width, 0);
        notice.MaximumSize = new Size(Math.Max(300, ClientSize.Width - 65), 0);
    }
}
