using System.Drawing.Drawing2D;

namespace FmLauncher;

internal sealed class ToggleSwitch : CheckBox
{
    internal ToggleSwitch()
    {
        AutoSize = true;
        MinimumSize = new Size(130, 30);
        Cursor = Cursors.Hand;
        SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint
            | ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw, true);
    }

    public override Size GetPreferredSize(Size proposedSize)
    {
        var offset = (int)Math.Round(72 * DeviceDpi / 96f);
        var width = MaximumSize.Width > 0 ? MaximumSize.Width : (int)Math.Round(600 * DeviceDpi / 96f);
        if (proposedSize.Width > 0) width = Math.Min(width, proposedSize.Width);
        var text = TextRenderer.MeasureText(Text, Font, Size.Empty,
            TextFormatFlags.SingleLine | TextFormatFlags.NoPadding);
        return new Size(Math.Max(MinimumSize.Width, Math.Min(width, text.Width + offset)),
            Math.Max((int)Math.Round(30 * DeviceDpi / 96f), text.Height + 6));
    }

    protected override void OnCheckedChanged(EventArgs e)
    {
        base.OnCheckedChanged(e);
        Invalidate();
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        e.Graphics.Clear(BackColor);
        e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
        var scale = DeviceDpi / 96f;
        var y = (Height - 26 * scale) / 2;
        using var shape = new GraphicsPath();
        shape.AddArc(2 * scale, y, 26 * scale, 26 * scale, 90, 180);
        shape.AddArc(34 * scale, y, 26 * scale, 26 * scale, 270, 180);
        shape.CloseFigure();
        var color = !Enabled ? SystemColors.GrayText : Checked ? Color.FromArgb(32, 113, 207) : Color.FromArgb(108, 119, 134);
        using var track = new SolidBrush(color);
        using var thumb = new SolidBrush(Color.White);
        e.Graphics.FillPath(track, shape);
        e.Graphics.FillEllipse(thumb, (Checked ? 36 : 5) * scale, y + 3 * scale, 20 * scale, 20 * scale);
        using var font = new Font(Font.FontFamily, 7, FontStyle.Bold);
        TextRenderer.DrawText(e.Graphics, Checked ? "ON" : "OFF", font,
            Rectangle.Round(new RectangleF((Checked ? 3 : 24) * scale, y, 31 * scale, 26 * scale)), Color.White,
            TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPadding);
        var offset = (int)Math.Round(72 * scale);
        var textBounds = new Rectangle(offset, 0, Math.Max(0, Width - offset), Height);
        TextRenderer.DrawText(e.Graphics, Text, Font, textBounds, Enabled ? ForeColor : SystemColors.GrayText,
            TextFormatFlags.SingleLine | TextFormatFlags.EndEllipsis | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPadding);
        if (Focused && ShowFocusCues) ControlPaint.DrawFocusRectangle(e.Graphics, textBounds);
    }
}

internal sealed class FeatureSection : UserControl
{
    private readonly Localizer localizer;
    private readonly Button details = new()
    {
        AutoSize = false, Anchor = AnchorStyles.Left | AnchorStyles.Right, Size = new Size(148, 30),
        FlatStyle = FlatStyle.Flat, TextAlign = ContentAlignment.MiddleRight
    };
    private readonly Control content;
    private readonly ToggleSwitch toggle;
    private bool expanded;
    internal bool Expanded
    {
        get => expanded;
        set
        {
            expanded = value;
            content.Visible = value;
            RefreshLanguage();
        }
    }

    internal FeatureSection(string name, ToggleSwitch toggle, Control content, Localizer localizer,
        bool expanded = false, Control? alwaysVisible = null)
    {
        this.localizer = localizer;
        this.content = content;
        this.toggle = toggle;
        Name = name;
        AutoSize = true;
        AutoSizeMode = AutoSizeMode.GrowAndShrink;
        Dock = DockStyle.Top;
        Padding = new Padding(10, 4, 10, 4);
        Margin = new Padding(0, 2, 0, 2);
        BackColor = Color.White;
        var stack = new TableLayoutPanel
        {
            Dock = DockStyle.Top, AutoSize = true, AutoSizeMode = AutoSizeMode.GrowAndShrink,
            ColumnCount = 1, Margin = Padding.Empty
        };
        stack.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        var header = new TableLayoutPanel
        {
            Dock = DockStyle.Top, AutoSize = true, AutoSizeMode = AutoSizeMode.GrowAndShrink,
            ColumnCount = 2, Margin = Padding.Empty
        };
        header.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        header.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 148));
        header.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        toggle.Dock = DockStyle.Fill;
        toggle.Margin = new Padding(0);
        details.Name = name + "Details";
        details.ForeColor = Color.FromArgb(32, 99, 180);
        details.FlatAppearance.BorderSize = 0;
        details.Margin = Padding.Empty;
        details.Click += (_, _) => Expanded = !Expanded;
        header.Controls.Add(toggle, 0, 0);
        header.Controls.Add(details, 1, 0);
        content.Dock = DockStyle.Top;
        content.Margin = new Padding(0, 4, 0, 0);
        stack.Controls.Add(header);
        stack.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        if (alwaysVisible is not null)
        {
            alwaysVisible.Dock = DockStyle.Top;
            alwaysVisible.Margin = new Padding(0, 4, 0, 0);
            stack.Controls.Add(alwaysVisible);
            stack.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        }
        stack.Controls.Add(content);
        stack.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        Controls.Add(stack);
        Expanded = expanded;
    }

    internal void RefreshLanguage()
    {
        details.Text = localizer.Text(expanded ? "HideDetails" : "Details");
        details.AccessibleName = details.Text + ": " + toggle.Text;
    }
}

internal sealed class InputFrame : Panel
{
    private readonly TextBox input;
    internal bool DarkMode { get; set; }

    internal InputFrame(TextBox input)
    {
        this.input = input;
        AutoSize = true;
        AutoSizeMode = AutoSizeMode.GrowAndShrink;
        Dock = DockStyle.Fill;
        Padding = new Padding(8, 5, 8, 5);
        DoubleBuffered = true;
        input.BorderStyle = BorderStyle.None;
        input.Dock = DockStyle.Fill;
        input.Margin = Padding.Empty;
        input.GotFocus += (_, _) => Invalidate();
        input.LostFocus += (_, _) => Invalidate();
        Controls.Add(input);
    }

    public override Size GetPreferredSize(Size proposedSize) =>
        new(input.GetPreferredSize(proposedSize).Width + Padding.Horizontal, input.PreferredHeight + Padding.Vertical);

    protected override void OnMouseDown(MouseEventArgs e)
    {
        base.OnMouseDown(e);
        input.Focus();
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        var radius = 4 * DeviceDpi / 96f;
        var bounds = new RectangleF(0.5f, 0.5f, Width - 1, Height - 1);
        DrawInput(e.Graphics, bounds, radius, DarkMode, ContainsFocus);
    }

    internal static void DrawInput(Graphics graphics, RectangleF bounds, float radius, bool dark, bool focused)
    {
        if (bounds.Width < radius * 2 || bounds.Height < radius * 2) return;
        using var shape = new GraphicsPath();
        shape.AddArc(bounds.Left, bounds.Top, radius * 2, radius * 2, 180, 90);
        shape.AddArc(bounds.Right - radius * 2, bounds.Top, radius * 2, radius * 2, 270, 90);
        shape.AddArc(bounds.Right - radius * 2, bounds.Bottom - radius * 2, radius * 2, radius * 2, 0, 90);
        shape.AddArc(bounds.Left, bounds.Bottom - radius * 2, radius * 2, radius * 2, 90, 90);
        shape.CloseFigure();
        graphics.SmoothingMode = SmoothingMode.AntiAlias;
        using var fill = new SolidBrush(LauncherTheme.Input(dark));
        using var pen = new Pen(focused ? LauncherTheme.Accent(dark) : LauncherTheme.Border(dark));
        graphics.FillPath(fill, shape);
        graphics.DrawPath(pen, shape);
    }
}

internal sealed class ThemedTabControl : TabControl
{
    internal ThemedTabControl() => DrawMode = TabDrawMode.OwnerDrawFixed;
    internal bool DarkMode { get; set; }

    protected override void OnDrawItem(DrawItemEventArgs e)
    {
        DrawTab(e.Graphics, e.Index, e.Bounds);
        if ((e.State & DrawItemState.Focus) != 0) ControlPaint.DrawFocusRectangle(e.Graphics, e.Bounds);
    }

    private void DrawTab(Graphics graphics, int index, Rectangle bounds)
    {
        var selected = index == SelectedIndex;
        using var brush = new SolidBrush(selected ? LauncherTheme.Surface(DarkMode) : LauncherTheme.Background(DarkMode));
        graphics.FillRectangle(brush, bounds);
        TextRenderer.DrawText(graphics, TabPages[index].Text, Font, bounds,
            selected ? LauncherTheme.Text(DarkMode) : LauncherTheme.Muted(DarkMode),
            TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter);
        if (selected)
        {
            using var accent = new SolidBrush(LauncherTheme.Accent(DarkMode));
            var thickness = Math.Max(2, 2 * DeviceDpi / 96);
            graphics.FillRectangle(accent, bounds.Left + 5, bounds.Bottom - thickness, Math.Max(0, bounds.Width - 10), thickness);
        }
    }

    protected override void WndProc(ref Message m)
    {
        base.WndProc(ref m);
        // OwnerDrawFixed does not cover the native tab frame or unused strip.
        if (DarkMode && TabCount > 0 && m.Msg is 0x000F or 0x0317 or 0x0318)
        {
            using var graphics = m.Msg == 0x000F ? Graphics.FromHwnd(Handle) : Graphics.FromHdc(m.WParam);
            using var brush = new SolidBrush(LauncherTheme.Background(true));
            var page = DisplayRectangle;
            graphics.FillRectangle(brush, 0, 0, ClientSize.Width, page.Top);
            graphics.FillRectangle(brush, 0, page.Top, page.Left, Math.Max(0, ClientSize.Height - page.Top));
            graphics.FillRectangle(brush, page.Right, page.Top, Math.Max(0, ClientSize.Width - page.Right), Math.Max(0, ClientSize.Height - page.Top));
            graphics.FillRectangle(brush, 0, page.Bottom, ClientSize.Width, Math.Max(0, ClientSize.Height - page.Bottom));
            for (var index = 0; index < TabCount; index++) DrawTab(graphics, index, GetTabRect(index));
        }
    }
}

internal sealed class ThemedComboBox : ComboBox
{
    internal bool DarkMode { get; set; }
    internal ThemedComboBox()
    {
        DrawMode = DrawMode.OwnerDrawFixed;
        FlatStyle = FlatStyle.Flat;
        UpdateItemHeight();
    }

    protected override void OnFontChanged(EventArgs e)
    {
        base.OnFontChanged(e);
        UpdateItemHeight();
    }

    private void UpdateItemHeight() => ItemHeight = Font.Height + Math.Max(2, 4 * DeviceDpi / 96);

    private void DrawClosed(Graphics graphics)
    {
        var scale = DeviceDpi / 96f;
        using var surface = new SolidBrush(Parent?.BackColor ?? LauncherTheme.Surface(true));
        graphics.FillRectangle(surface, ClientRectangle);
        InputFrame.DrawInput(graphics, new RectangleF(0.5f, 0.5f, Width - 1, Height - 1),
            4 * scale, true, ContainsFocus);
        var arrowWidth = (int)Math.Round(28 * scale);
        var textBounds = new Rectangle((int)Math.Round(8 * scale), 0, Math.Max(0, Width - arrowWidth - 8), Height);
        TextRenderer.DrawText(graphics, Text, Font, textBounds, Enabled ? LauncherTheme.Text(true) : LauncherTheme.Muted(true),
            TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.EndEllipsis | TextFormatFlags.NoPadding);
        using var pen = new Pen(LauncherTheme.Muted(true), 1.5f * scale);
        var x = Width - 14 * scale;
        var y = Height / 2f - scale;
        graphics.DrawLines(pen, new PointF[] { new(x - 4 * scale, y), new(x, y + 4 * scale), new(x + 4 * scale, y) });
    }

    protected override void WndProc(ref Message m)
    {
        base.WndProc(ref m);
        if (DarkMode && DropDownStyle == ComboBoxStyle.DropDownList && m.Msg is 0x000F or 0x0317 or 0x0318)
        {
            using var graphics = m.Msg == 0x000F ? Graphics.FromHwnd(Handle) : Graphics.FromHdc(m.WParam);
            DrawClosed(graphics);
        }
    }

    protected override void OnDrawItem(DrawItemEventArgs e)
    {
        if (DarkMode && (e.State & DrawItemState.ComboBoxEdit) != 0)
        {
            DrawClosed(e.Graphics);
            return;
        }
        var selected = (e.State & DrawItemState.Selected) != 0 && (e.State & DrawItemState.ComboBoxEdit) == 0;
        using var brush = new SolidBrush(selected ? Color.FromArgb(32, 113, 207) : LauncherTheme.Input(DarkMode));
        e.Graphics.FillRectangle(brush, e.Bounds);
        var text = e.Index >= 0 ? GetItemText(Items[e.Index]) : Text;
        TextRenderer.DrawText(e.Graphics, text, Font, e.Bounds, selected ? Color.White : LauncherTheme.Text(DarkMode),
            TextFormatFlags.Left | TextFormatFlags.VerticalCenter | TextFormatFlags.EndEllipsis);
        e.DrawFocusRectangle();
    }
}

internal sealed class SocialLinkButton : Button
{
    internal SocialLinkButton(string name)
    {
        Name = name;
        Size = name == "DonateLink" ? new Size(60, 48) : new Size(44, 36);
        FlatStyle = FlatStyle.Flat;
        FlatAppearance.BorderSize = 0;
        Cursor = Cursors.Hand;
        Margin = name == "DonateLink" ? Padding.Empty : new Padding(4, 0, 4, 0);
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        var g = e.Graphics;
        g.SmoothingMode = SmoothingMode.AntiAlias;
        var state = g.Save();
        var scale = DeviceDpi / 96f * (Name == "DonateLink" ? 1.5f : 1);
        g.TranslateTransform((Width - 24 * scale) / 2f, (Height - 24 * scale) / 2f);
        g.ScaleTransform(scale, scale);
        var color = !Enabled ? Color.FromArgb(150, 158, 170) : Name switch
        {
            "YouTubeLink" => Color.FromArgb(210, 35, 40),
            "DiscordLink" => Color.FromArgb(88, 101, 242),
            "DonateLink" => Color.FromArgb(195, 72, 81),
            _ => Color.FromArgb(52, 65, 81)
        };
        using var pen = new Pen(color, 2) { LineJoin = LineJoin.Round };
        using var brush = new SolidBrush(color);
        switch (Name)
        {
            case "GitLink":
                g.DrawPolygon(pen, new Point[] { new(12, 1), new(23, 12), new(12, 23), new(1, 12) });
                g.DrawLines(pen, new Point[] { new(8, 6), new(12, 10), new(12, 18) });
                g.DrawLine(pen, 12, 10, 18, 12);
                foreach (var point in new[] { new Point(8, 6), new Point(12, 18), new Point(18, 12) })
                    g.FillEllipse(brush, point.X - 2, point.Y - 2, 4, 4);
                break;
            case "YouTubeLink":
                g.FillRectangle(brush, 1, 5, 22, 15);
                using (var play = new SolidBrush(Color.White))
                    g.FillPolygon(play, new Point[] { new(10, 8), new(10, 17), new(17, 12) });
                break;
            case "DiscordLink":
                g.DrawPolygon(pen, new Point[] { new(5, 5), new(19, 5), new(23, 19), new(17, 21),
                    new(15, 18), new(9, 18), new(7, 21), new(1, 19) });
                g.FillEllipse(brush, 6, 10, 4, 5);
                g.FillEllipse(brush, 14, 10, 4, 5);
                break;
            case "DonateLink":
                g.DrawLines(pen, new Point[] { new(2, 5), new(2, 19), new(17, 19), new(17, 5), new(2, 5) });
                g.DrawArc(pen, 14, 6, 9, 10, 270, 180);
                g.DrawLine(pen, 1, 23, 19, 23);
                g.FillPolygon(brush, new Point[] { new(5, 10), new(8, 8), new(10, 10), new(12, 8),
                    new(15, 10), new(10, 16) });
                break;
        }
        g.Restore(state);
    }
}
