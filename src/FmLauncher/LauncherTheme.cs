using System.Diagnostics;
using System.Runtime.InteropServices;

namespace FmLauncher;

internal static class LauncherTheme
{
    internal static Color Background(bool dark) => dark ? Color.FromArgb(20, 24, 32) : Color.FromArgb(239, 242, 247);
    internal static Color Surface(bool dark) => dark ? Color.FromArgb(28, 34, 44) : Color.White;
    internal static Color Input(bool dark) => dark ? Color.FromArgb(36, 45, 58) : SystemColors.Window;
    internal static Color Text(bool dark) => dark ? Color.FromArgb(220, 229, 240) : SystemColors.ControlText;
    internal static Color Muted(bool dark) => dark ? Color.FromArgb(157, 173, 194) : SystemColors.ControlDarkDark;
    internal static Color Border(bool dark) => dark ? Color.FromArgb(57, 70, 88) : SystemColors.ControlDark;
    internal static Color Hover(bool dark) => dark ? Color.FromArgb(43, 57, 76) : Color.FromArgb(230, 239, 249);
    internal static Color Accent(bool dark) => dark ? Color.FromArgb(135, 186, 250) : Color.FromArgb(32, 99, 180);
    internal static Color Warning(bool dark) => dark ? Color.FromArgb(48, 44, 36) : Color.LemonChiffon;
    internal static Color Success(bool dark) => dark ? Color.FromArgb(30, 66, 49) : Color.Honeydew;
    internal static Color Error(bool dark) => dark ? Color.FromArgb(255, 150, 150) : Color.Firebrick;

    internal static void Apply(Control control, bool dark)
    {
        control.SuspendLayout();
        try
        {
            control.ForeColor = Text(dark);
            control.BackColor = control is Form or TabPage || control.Name == "MainSettingsScroll"
                ? Background(dark)
                : control is FeatureSection || control.Name is "LauncherHeader" or "LauncherActions" or "GamePaths"
                    ? Surface(dark) : control.Parent?.BackColor ?? Surface(dark);
            switch (control)
            {
                case InputFrame frame:
                    frame.DarkMode = dark;
                    frame.Invalidate();
                    break;
                case TextBoxBase:
                case ComboBox:
                case NumericUpDown:
                    control.BackColor = Input(dark);
                    if (control is TextBoxBase textBox && control.Parent is not InputFrame)
                        textBox.BorderStyle = BorderStyle.FixedSingle;
                    if (control is NumericUpDown number) number.BorderStyle = BorderStyle.FixedSingle;
                    if (control is ThemedComboBox combo)
                    {
                        combo.DarkMode = dark;
                        combo.Invalidate();
                    }
                    break;
                case Button button:
                    var borderless = button is SocialLinkButton || button.Name.EndsWith("Details", StringComparison.Ordinal);
                    button.FlatStyle = FlatStyle.Flat;
                    button.UseVisualStyleBackColor = false;
                    button.FlatAppearance.BorderColor = Border(dark);
                    button.FlatAppearance.BorderSize = borderless || button.Name == "Play" ? 0 : 1;
                    button.FlatAppearance.MouseOverBackColor = Hover(dark);
                    button.FlatAppearance.MouseDownBackColor = Input(dark);
                    if (button.Name == "Play")
                    {
                        button.BackColor = Color.FromArgb(42, 111, 203);
                        button.ForeColor = Color.White;
                        button.FlatAppearance.MouseOverBackColor = Color.FromArgb(48, 117, 209);
                        button.FlatAppearance.MouseDownBackColor = Color.FromArgb(35, 95, 178);
                    }
                    else
                    {
                        button.BackColor = borderless ? control.Parent?.BackColor ?? Surface(dark) : Input(dark);
                        button.ForeColor = borderless || button.Name == "ThemeMode" ? Accent(dark) : Text(dark);
                    }
                    break;
                case LinkLabel link:
                    link.LinkColor = link.ActiveLinkColor = link.VisitedLinkColor = Accent(dark);
                    if (link.Name == "CareerProfileBanner")
                    {
                        link.LinkColor = dark ? Text(true) : Accent(false);
                        link.LinkBehavior = LinkBehavior.HoverUnderline;
                    }
                    break;
                case DataGridView grid:
                    grid.BackgroundColor = Input(dark);
                    grid.BorderStyle = BorderStyle.None;
                    grid.EnableHeadersVisualStyles = false;
                    grid.GridColor = dark ? Color.FromArgb(73, 84, 101) : SystemColors.ControlDark;
                    grid.DefaultCellStyle.BackColor = grid.AlternatingRowsDefaultCellStyle.BackColor = Input(dark);
                    grid.DefaultCellStyle.ForeColor = Text(dark);
                    grid.DefaultCellStyle.SelectionBackColor = Color.FromArgb(32, 113, 207);
                    grid.DefaultCellStyle.SelectionForeColor = Color.White;
                    grid.ColumnHeadersDefaultCellStyle.BackColor = Surface(dark);
                    grid.ColumnHeadersDefaultCellStyle.ForeColor = Text(dark);
                    grid.ColumnHeadersDefaultCellStyle.SelectionBackColor = Surface(dark);
                    grid.ColumnHeadersDefaultCellStyle.SelectionForeColor = Text(dark);
                    break;
                case ThemedTabControl tabs:
                    tabs.DarkMode = dark;
                    tabs.Invalidate();
                    break;
                case Label label when label.Name is "LauncherStatus" or "UserDataNotice" or "DisplayNotice" or "DonatePrompt":
                    label.ForeColor = Muted(dark);
                    break;
            }
            foreach (Control child in control.Controls) Apply(child, dark);
            if (control is Form form && form.IsHandleCreated && OperatingSystem.IsWindowsVersionAtLeast(10, 0, 18985))
            {
                var enabled = dark ? 1 : 0;
                var result = DwmSetWindowAttribute(form.Handle, 20, ref enabled, sizeof(int));
                if (result < 0) Trace.TraceWarning("Window title-bar theme unavailable: HRESULT 0x{0:X8}.", result);
            }
        }
        finally { control.ResumeLayout(true); }
    }

    [DllImport("dwmapi.dll")]
    private static extern int DwmSetWindowAttribute(IntPtr window, int attribute, ref int value, int size);
}
