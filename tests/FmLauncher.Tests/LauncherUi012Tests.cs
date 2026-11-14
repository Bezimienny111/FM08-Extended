using System.Text.Json;
using FmLauncher;

namespace FmLauncher.Tests;

internal static partial class Program
{
    private static void TestUi012(string directory, string? artifacts = null)
    {
        var localizer = new Localizer(Path.Combine(AppContext.BaseDirectory, "FmLauncher.languages.json"));
        using var form = new MainForm(directory, localizer, _ => new[] { Hd });
        form.Show();
        form.Populate(Default(), new[] { Hd });
        ShowFeature(form, "MatchRulesFeature");
        var before = JsonSerializer.Serialize(form.CaptureConfiguration().Rules);
        var footer = Descendants(form).Single(control => control.Name == "LauncherActions");
        var social = Descendants(form).Single(control => control.Name == "FooterLinks");
        var log = Descendants(form).OfType<LaunchLogPanel>().Single();
        var view = Descendants(form).OfType<ComboBox>().Single(control => control.Name == "RuleEditView");
        var tabs = Descendants(form).OfType<TabControl>().Single();
        var grid = Descendants(form).OfType<DataGridView>().Single();
        var groups = Descendants(form).OfType<ListView>().Single();
        Assert(Descendants(form).Single(control => control.Name == "LauncherVersion").Text == "v0.1.2");
        Assert(!log.Expanded);
        log.Journal.Begin(Default().Rules);
        log.RefreshJournal();
        var initialCount = log.Journal.Entries.Count;
        log.Journal.Add("LaunchLogStarting");
        log.RefreshJournal();
        Assert(log.Journal.Entries.Count == initialCount + 1);
        var messages = Descendants(log).OfType<TextBox>().Single();
        var collapsedText = messages.Text;
        log.Expanded = true;
        Assert(messages.Text == collapsedText);
        log.Expanded = false;
        foreach (var language in new[] { "en", "pl" })
        foreach (var size in new[] { new Size(1000, 900), form.MinimumSize })
        foreach (var dark in new[] { false, true })
        foreach (var index in new[] { 0, 1 })
        foreach (var expanded in new[] { false, true })
        {
            form.ApplyLanguage(language);
            form.Size = size;
            form.ApplyTheme(dark);
            view.SelectedIndex = index;
            log.Expanded = expanded;
            Application.DoEvents();
            Assert(form.ClientRectangle.Contains(log.Bounds));
            Assert(log.Bottom == form.ClientSize.Height && footer.Bottom <= log.Top && tabs.Bottom <= footer.Top);
            var socialBottom = form.PointToClient(social.PointToScreen(new Point(0, social.Height))).Y;
            Assert(socialBottom <= log.Top);
            Assert(log.Visible && messages.Visible == expanded);
            Assert(grid.Visible == (index == 0) && groups.Visible == (index == 1));
            Assert(tabs.Height > 50);
            Assert(JsonSerializer.Serialize(form.CaptureConfiguration().Rules) == before);
            Assert(log.Journal.Entries.Count == initialCount + 1);
            Assert(log.Controls.OfType<Button>().Single().Text.Contains((initialCount + 1).ToString()));
            foreach (var section in Descendants(form).OfType<FeatureSection>())
            {
                Assert(section.DarkMode == dark && LauncherTheme.SectionBorder(dark) != LauncherTheme.Surface(dark));
                using var image = new Bitmap(section.Width, section.Height);
                section.DrawToBitmap(image, section.ClientRectangle);
                var edge = image.GetPixel(1, section.Height / 2);
                var wanted = LauncherTheme.SectionBorder(dark);
                Assert(Math.Abs(edge.R - wanted.R) <= 2 && Math.Abs(edge.G - wanted.G) <= 2 && Math.Abs(edge.B - wanted.B) <= 2);
            }
            Assert(form.OwnedForms.Length == 0);
        }
        if (artifacts is not null)
        {
            Directory.CreateDirectory(artifacts);
            void Capture(string name)
            {
                Application.DoEvents();
                using var image = new Bitmap(form.Width, form.Height);
                form.DrawToBitmap(image, new Rectangle(Point.Empty, form.Size));
                image.Save(Path.Combine(artifacts, name + ".png"));
            }
            form.ApplyLanguage("pl");
            form.Size = new Size(1000, 900);
            form.ApplyTheme(false);
            log.Expanded = false;
            foreach (var section in Descendants(form).OfType<FeatureSection>()) section.Expanded = false;
            Capture("home-light");
            ShowFeature(form, "MatchRulesFeature");
            view.SelectedIndex = 0;
            Capture("individual-light");
            view.SelectedIndex = 1;
            log.Expanded = true;
            Capture("grouped-light-log");
            form.ApplyTheme(true);
            Capture("grouped-dark-log");
            form.Size = form.MinimumSize;
            Capture("minimum-expanded");
            log.Expanded = false;
            Capture("minimum-collapsed");
        }
        form.Close();
    }
}
