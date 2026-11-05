using System.Text.Json;
using System.Reflection;
using FmLauncher;

namespace FmLauncher.Tests;

internal static partial class Program
{
    private static void TestFeatureTabs(string directory, string languagePath)
    {
        var localizer = new Localizer(languagePath);
        using var form = new MainForm(directory, localizer, _ => new[] { Hd });
        form.Show();
        form.Populate(Default(), new[] { Hd });
        var tabs = Descendants(form).OfType<TabControl>().Single();
        var footer = Descendants(form).Single(control => control.Name == "LauncherActions");
        var names = new[] { "Settings", "SkinGuide" };
        var captions = new[] { "SettingsTab", "SkinTab" };
        Assert(tabs.TabPages.Cast<TabPage>().Select(page => page.Name).SequenceEqual(names));
        var home = tabs.TabPages["Settings"]!;
        Assert(Descendants(home).OfType<DataGridView>().Count() == 1);
        Assert(Descendants(home).Any(control => control.Name == "DisplayOverride"));
        Assert(Descendants(home).Any(control => control.Name == "UserDataPath"));
        Assert(Descendants(home).Any(control => control.Name == "PaStatistics"));
        Assert(Descendants(home).OfType<Label>()
            .Any(label => label.Text == localizer.Text("PaCalculation")));
        Assert(Descendants(home).OfType<ToggleSwitch>().Count() == 9);
        Assert(Descendants(home).OfType<CheckBox>().All(control => control is ToggleSwitch));
        var diagnosticToggle = Descendants(home).OfType<CheckBox>()
            .Single(control => control.Name == "LeagueDiagnosticsEnabled");
        Assert(!diagnosticToggle.Checked && !form.CaptureConfiguration().LeagueDiagnosticsEnabled);
        var languageChoice = Descendants(form).Single(control => control.Name == "LauncherLanguage");
        var play = Descendants(footer).Single(control => control.Name == "Play");
        var banner = Descendants(footer).Single(control => control.Name == "CareerProfileBanner");
        var changes = Descendants(home).OfType<ToggleSwitch>().Single(control => control.Name == "LeagueChangesEnabled");
        var links = Descendants(footer).OfType<SocialLinkButton>().ToArray();
        var support = Descendants(footer).Single(control => control.Name == "ProjectSupport");
        var prompt = Descendants(support).Single(control => control.Name == "DonatePrompt");
        var linkRow = Descendants(footer).Single(control => control.Name == "FooterLinks");
        var social = Descendants(footer).Single(control => control.Name == "SocialLinks");
        Assert(typeof(MainForm).Assembly.GetCustomAttribute<AssemblyTitleAttribute>()?.Title == "FM08 Extended");
        Assert(typeof(MainForm).Assembly.GetCustomAttribute<AssemblyProductAttribute>()?.Product == "FM08 Extended");
        Assert(links.Select(button => button.Name).SequenceEqual(new[] { "GitLink", "YouTubeLink", "DiscordLink", "DonateLink" }));
        Assert(!links[0].Enabled && links[0].Tag is null);
        Assert((string)links[1].Tag! == "https://www.youtube.com/@Bezimienny111");
        Assert((string)links[2].Tag! == "https://discord.gg/hP2g4MQS5T");
        Assert((string)links[3].Tag! == "https://ko-fi.com/ericaaurora");
        foreach (var language in new[] { "en", "pl" })
        foreach (var size in new[] { new Size(1000, 900), form.MinimumSize })
        foreach (var dark in new[] { false, true })
        foreach (var advanced in new[] { false, true })
        {
            form.Size = size;
            form.ApplyLanguage(language);
            form.ApplyTheme(dark);
            Descendants(form).OfType<ToggleSwitch>().Single(control => control.Name == "AdvancedMode").Checked = advanced;
            for (var index = 0; index < names.Length; index++)
            {
                tabs.SelectedIndex = index;
                Application.DoEvents();
                Assert(tabs.TabPages[index].Text == localizer.Text(captions[index]));
                Assert(form.Text == "FM08 Extended" && Descendants(form).Single(control => control.Name == "BrandTitle").Text == "FM08 Extended");
                Assert(footer.Visible && footer.Bottom <= form.ClientSize.Height && tabs.Bottom <= footer.Top);
                var buttons = Descendants(footer).OfType<Button>().ToArray();
                Assert(buttons.Length == 7 && buttons.Count(button => button.Visible) == (advanced ? 7 : 5));
                Assert(buttons.Where(button => button.Name is "Save" or "Reload").All(button => button.Visible == advanced));
                Assert(buttons.Where(button => button.Visible).All(button => footer.RectangleToScreen(footer.ClientRectangle)
                    .Contains(button.RectangleToScreen(button.ClientRectangle))));
                var center = form.PointToClient(play.PointToScreen(new Point(play.Width / 2, 0))).X;
                Assert(Math.Abs(center - form.ClientSize.Width / 2) <= 3);
                var languageRight = form.PointToClient(languageChoice.PointToScreen(new Point(languageChoice.Width, 0))).X;
                Assert(form.ClientSize.Width - languageRight <= 30);
                Assert(!banner.Visible);
                Assert(form.CaptureConfiguration().Language == language);
                Assert(diagnosticToggle.Text == localizer.Text("LeagueDiagnosticsEnabled"));
                Assert(links.All(button => button.AccessibleName == localizer.Text(button.Name)));
                Assert(links[3].AccessibleDescription == localizer.Text("DonateTooltip")
                    && links[3].AccessibleDescription!.Contains("\"FM08Extended\""));
                Assert(prompt.Text == localizer.Text("DonatePrompt") && prompt.Visible);
                var supportRight = footer.PointToClient(support.PointToScreen(new Point(support.Width, 0))).X;
                Assert(Math.Abs(supportRight - (footer.ClientSize.Width - footer.Padding.Right)) <= 1);
                Assert(links[3].Right == support.ClientSize.Width && links[3].Width > links[0].Width);
                Assert(prompt.Right < links[3].Left && prompt.Height <= support.Height);
                Assert(prompt.PointToScreen(Point.Empty).X >= social.PointToScreen(new Point(social.Width, 0)).X);
                Assert(Math.Abs(social.PointToScreen(new Point(social.Width / 2, 0)).X
                    - linkRow.PointToScreen(new Point(linkRow.Width / 2, 0)).X) <= 1);
                using var icon = new Bitmap(links[3].Width, links[3].Height);
                links[3].DrawToBitmap(icon, links[3].ClientRectangle);
                var firstIconRow = icon.Height;
                var lastIconRow = -1;
                for (var y = 0; y < icon.Height; y++)
                {
                    for (var x = 0; x < icon.Width; x++)
                    {
                        var pixel = icon.GetPixel(x, y);
                        if (pixel.R < 150 || pixel.R <= pixel.G * 1.5 || pixel.R <= pixel.B * 1.5) continue;
                        firstIconRow = Math.Min(firstIconRow, y);
                        lastIconRow = y;
                        break;
                    }
                }
                var iconHeight = lastIconRow - firstIconRow + 1;
                if (iconHeight < 28 * form.DeviceDpi / 96f)
                    throw new InvalidOperationException($"Ko-fi icon too small: {iconHeight}px at {form.DeviceDpi} DPI; {language}/{size}/{dark}");
            }
            tabs.SelectedIndex = 0;
            changes.Checked = true;
            Application.DoEvents();
            Assert(banner.Visible && banner.Bottom <= play.Parent!.Top);
            changes.Checked = false;
            var before = JsonSerializer.Serialize(form.CaptureConfiguration());
            foreach (var feature in Descendants(home).OfType<FeatureSection>().Where(feature => feature.Visible).ToArray())
            {
                feature.Expanded = false;
                var button = Descendants(feature).OfType<Button>().Single(control => control.Name == feature.Name + "Details");
                button.PerformClick();
                Application.DoEvents();
                Assert(feature.Expanded && button.Text == localizer.Text("HideDetails"));
                var toggle = Descendants(feature).OfType<ToggleSwitch>().Single();
                Assert(button.Right <= button.Parent!.ClientSize.Width && toggle.Right <= button.Left);
                Assert(feature.Width <= home.ClientSize.Width);
                button.PerformClick();
                Assert(!feature.Expanded);
            }
            Assert(JsonSerializer.Serialize(form.CaptureConfiguration()) == before);
        }
        form.Close();
    }

    private static void ShowFeature(MainForm form, string name)
    {
        Descendants(form).OfType<TabControl>().Single().SelectTab("Settings");
        var feature = Descendants(form).OfType<FeatureSection>().Single(control => control.Name == name);
        feature.Expanded = true;
        var scroll = Descendants(form).OfType<Panel>().Single(control => control.Name == "MainSettingsScroll");
        scroll.ScrollControlIntoView(feature);
        Application.DoEvents();
    }

    private static void TestCompactDarkLayout(string directory, string languagePath)
    {
        var localizer = new Localizer(languagePath);
        using var form = new MainForm(directory, localizer, _ => new[] { Hd });
        form.Show();
        var config = Default();
        config.DisplayOverride = true;
        form.Populate(config, new[] { Hd });
        var sections = Descendants(form).OfType<FeatureSection>().ToArray();
        var graphics = sections.Single(section => section.Name == "GraphicsFeature");
        var mode = Descendants(form).OfType<ComboBox>().Single(control => control.Name == "DisplayMode");
        var resolution = Descendants(form).OfType<ComboBox>().Single(control => control.Name == "Resolution");
        var refresh = Descendants(form).OfType<Button>().Single(control => control.Name == "RefreshDisplay");
        var theme = Descendants(form).OfType<Button>().Single(control => control.Name == "ThemeMode");
        static double Luminance(Color color)
        {
            static double Linear(byte value)
            {
                var channel = value / 255.0;
                return channel <= 0.04045 ? channel / 12.92 : Math.Pow((channel + 0.055) / 1.055, 2.4);
            }
            return 0.2126 * Linear(color.R) + 0.7152 * Linear(color.G) + 0.0722 * Linear(color.B);
        }
        static double Contrast(Color first, Color second)
        {
            var a = Luminance(first);
            var b = Luminance(second);
            return (Math.Max(a, b) + 0.05) / (Math.Min(a, b) + 0.05);
        }
        foreach (var language in new[] { "en", "pl" })
        foreach (var size in new[] { new Size(1000, 900), form.MinimumSize })
        foreach (var dark in new[] { false, true })
        foreach (var advanced in new[] { false, true })
        {
            form.Size = size;
            form.ApplyLanguage(language);
            form.ApplyTheme(dark);
            Descendants(form).OfType<ToggleSwitch>().Single(control => control.Name == "AdvancedMode").Checked = advanced;
            foreach (var section in sections) section.Expanded = false;
            Application.DoEvents();
            var scale = form.DeviceDpi / 96f;
            var collapsed = sections.Where(section => section != graphics && section.Visible).ToArray();
            if (collapsed.Any(section => section.Height > 48 * scale))
                throw new InvalidOperationException("Oversized tiles: " + string.Join("; ", collapsed.Select(section =>
                    $"{section.Name}={section.Height}, preferred={section.PreferredSize.Height}, children="
                    + string.Join("/", section.Controls.Cast<Control>().Select(control => control.Size.ToString())))));
            Assert(collapsed.Max(section => section.Height) - collapsed.Min(section => section.Height) <= 1);
            var rightEdges = sections.Where(section => section.Visible).Select(section =>
            {
                var button = Descendants(section).OfType<Button>().Single(control => control.Name == section.Name + "Details");
                return button.PointToScreen(new Point(button.Width, 0)).X;
            }).ToArray();
            Assert(rightEdges.Max() - rightEdges.Min() <= 1);
            Assert(mode.Visible && resolution.Visible && refresh.Visible);
            var description = Descendants(graphics).OfType<Label>().Single(label => label.Text == localizer.Text("DisplayNotice"));
            Assert(!description.Visible);
            graphics.Expanded = true;
            Application.DoEvents();
            Assert(description.Visible && mode.Visible && resolution.Visible && refresh.Visible);
            graphics.Expanded = false;
            Application.DoEvents();
            var centers = new[] { mode, resolution }.Select(control =>
                control.PointToScreen(new Point(0, control.Height / 2)).Y).Append(
                    refresh.PointToScreen(new Point(0, refresh.Height / 2)).Y).ToArray();
            if (centers.Max() - centers.Min() > 1)
                throw new InvalidOperationException($"Graphics alignment {language}/{size}/{dark}: {string.Join(",", centers)}; "
                    + $"mode={mode.Bounds}, resolution={resolution.Bounds}, refresh={refresh.Bounds}");
            Assert(mode.BackColor == LauncherTheme.Input(dark) && resolution.BackColor == LauncherTheme.Input(dark));
            Assert(form.BackColor == LauncherTheme.Background(dark));
            Assert(theme.Text == localizer.Text(dark ? "LightMode" : "DarkMode"));
            Assert(form.CaptureConfiguration().DarkMode == dark);
            Assert(Contrast(LauncherTheme.Text(dark), LauncherTheme.Input(dark)) >= 4.5);
            Assert(Contrast(LauncherTheme.Muted(dark), LauncherTheme.Surface(dark)) >= 4.5);
            Assert(Contrast(LauncherTheme.Accent(dark), LauncherTheme.Surface(dark)) >= 4.5);
            var play = Descendants(form).OfType<Button>().Single(button => button.Name == "Play");
            Assert(Contrast(play.ForeColor, play.BackColor) >= 4.5
                && Contrast(play.ForeColor, play.FlatAppearance.MouseOverBackColor) >= 4.5);
            if (dark)
            {
                foreach (var control in new Control[] { mode, resolution }.Concat(Descendants(form).OfType<InputFrame>()))
                {
                    using var image = new Bitmap(control.Width, control.Height);
                    control.DrawToBitmap(image, control.ClientRectangle);
                    foreach (var point in new[] { new Point(0, control.Height / 2), new Point(control.Width - 1, control.Height / 2) })
                    {
                        var pixel = image.GetPixel(point.X, point.Y);
                        Assert(pixel.R < 220 || pixel.G < 220 || pixel.B < 220);
                    }
                }
                var tabs = Descendants(form).OfType<TabControl>().Single();
                using var frame = new Bitmap(tabs.Width, tabs.Height);
                tabs.DrawToBitmap(frame, tabs.ClientRectangle);
                Assert(frame.GetPixel(0, tabs.DisplayRectangle.Top + 10).ToArgb() == LauncherTheme.Background(true).ToArgb());
            }
        }
        form.ApplyTheme(false);
        var before = JsonSerializer.Serialize(form.CaptureConfiguration());
        theme.PerformClick();
        var captured = form.CaptureConfiguration();
        Assert(captured.DarkMode);
        var store = new ConfigurationStore(Path.Combine(directory, "dark-theme.json"));
        store.Save(captured);
        Assert(store.Load()!.DarkMode);
        captured.DarkMode = false;
        Assert(JsonSerializer.Serialize(captured) == before);
        theme.PerformClick();
        Assert(!form.CaptureConfiguration().DarkMode);
        form.ApplyTheme(true);
        ShowFeature(form, "PaFeature");
        Descendants(form).OfType<Button>().Single(button => button.Text == localizer.Text("PaLogOpen")).PerformClick();
        Application.DoEvents();
        var log = form.OwnedForms.Single();
        Assert(log.BackColor == LauncherTheme.Background(true));
        form.ApplyTheme(false);
        Assert(log.BackColor == LauncherTheme.Background(false));
        log.Close();
        form.Close();
    }

    private static void TestUserDataConfiguration(string directory)
    {
        var config = Default();
        var legacy = System.Text.Json.Nodes.JsonNode.Parse(JsonSerializer.Serialize(config, ConfigurationStore.JsonOptions))!.AsObject();
        legacy.Remove("UserDataPath");
        legacy.Remove("MatchRulesEnabled");
        legacy.Remove("DarkMode");
        legacy.Remove("AdvancedMode");
        var loaded = JsonSerializer.Deserialize<LauncherConfiguration>(legacy.ToJsonString(), ConfigurationStore.JsonOptions)!;
        ConfigurationValidator.Validate(loaded);
        Assert(loaded.UserDataPath == "" && loaded.MatchRulesEnabled && !loaded.DarkMode && !loaded.AdvancedMode);
        config.UserDataPath = "relative-folder";
        Reject(() => ConfigurationValidator.Validate(config), "InvalidUserDataPath");
        config.UserDataPath = Path.Combine(directory, "bad\0path");
        Reject(() => ConfigurationValidator.Validate(config), "InvalidUserDataPath");
        config.UserDataPath = Path.Combine(directory, "not-a-folder.txt");
        File.WriteAllText(config.UserDataPath, "unchanged");
        Reject(() => ConfigurationValidator.Validate(config), "InvalidUserDataPath");
        config.UserDataPath = Path.Combine(directory, "user-data");
        Directory.CreateDirectory(config.UserDataPath);
        Assert(SkinGuidePage.InitialSkinDirectory(config.GamePath, config.UserDataPath) == config.UserDataPath);
        Directory.CreateDirectory(Path.Combine(config.UserDataPath, "skins"));
        Assert(SkinGuidePage.InitialSkinDirectory(config.GamePath, config.UserDataPath) == Path.Combine(config.UserDataPath, "skins"));
        config.MatchRulesEnabled = false;
        config.Rules[0].Override = true;
        config.Rules[0].BenchOverride = true;
        var store = new ConfigurationStore(Path.Combine(directory, "user-data-config.json"));
        store.Save(config);
        loaded = store.Load()!;
        Assert(loaded.UserDataPath == config.UserDataPath && !loaded.MatchRulesEnabled
            && loaded.Rules[0].Override && loaded.Rules[0].BenchOverride);
        Assert(File.ReadAllText(Path.Combine(directory, "not-a-folder.txt")) == "unchanged");
    }

    private static void TestAdvancedMode(string directory, string languagePath)
    {
        var localizer = new Localizer(languagePath);
        using var form = new MainForm(directory, localizer, _ => new[] { Hd });
        form.Show();
        var config = Default();
        config.PaEnabled = true;
        config.LeagueChangesEnabled = true;
        config.LeagueReputationEnabled = true;
        config.LeagueDiagnosticsEnabled = true;
        config.MatchRulesEnabled = false;
        config.Rules[0].Override = true;
        config.Rules[0].Substitutions = 5;
        form.Populate(config, new[] { Hd });
        var advanced = Descendants(form).OfType<ToggleSwitch>().Single(control => control.Name == "AdvancedMode");
        var notice = Descendants(form).Single(control => control.Name == "AdvancedActiveTools");
        var league = Descendants(form).Single(control => control.Name == "LeagueReputation");
        var hiddenNames = new[] { "LeagueObservationFeature", "LeagueDiagnosticsFeature", "PaStatistics", "PaLogOpen", "PaLogStatus", "LeagueChangeLog",
            "ConfigurationActions", "Save", "Reload" };
        var hidden = hiddenNames.Select(name => Descendants(form).Single(control => control.Name == name)).ToArray();
        Assert(!advanced.Checked && hidden.All(control => !control.Visible));
        foreach (var language in new[] { "en", "pl" })
        foreach (var dark in new[] { false, true })
        foreach (var size in new[] { new Size(1000, 900), form.MinimumSize })
        {
            form.ApplyLanguage(language);
            form.ApplyTheme(dark);
            form.Size = size;
            ShowFeature(form, "PaFeature");
            ShowFeature(form, "LeagueChangesFeature");
            Assert(advanced.Text == localizer.Text("AdvancedMode"));
            Assert(notice.Visible && notice.Text == localizer.Text("AdvancedActiveTools",
                string.Join(", ", localizer.Text("LeagueEnabled"), localizer.Text("LeagueDiagnosticsEnabled"))));
            Assert(hidden.All(control => !control.Visible));
            var before = JsonSerializer.Serialize(form.CaptureConfiguration());
            var normalHeight = league.Height;
            advanced.Checked = true;
            Application.DoEvents();
            Assert(hidden.All(control => control.Visible) && !notice.Visible && league.Height > normalHeight);
            ShowFeature(form, "LeagueObservationFeature");
            ShowFeature(form, "LeagueDiagnosticsFeature");
            Assert(Descendants(form).Single(control => control.Name == "LeagueBaseline").Visible);
            Assert(Descendants(form).Single(control => control.Name == "LeagueDiagnosticsOpen").Visible);
            var captured = form.CaptureConfiguration();
            Assert(captured.AdvancedMode && captured.LeagueReputationEnabled && captured.LeagueDiagnosticsEnabled);
            var store = new ConfigurationStore(Path.Combine(directory, "advanced-mode.json"));
            store.Save(captured);
            var loaded = store.Load()!;
            Assert(loaded.AdvancedMode);
            form.Populate(loaded, new[] { Hd });
            Assert(advanced.Checked && hidden.All(control => control.Visible));
            Descendants(form).OfType<Button>().Single(button => button.Name == "Save").PerformClick();
            var manuallySaved = new ConfigurationStore(Path.Combine(directory, "FmLauncher.config.json")).Load()!;
            Assert(JsonSerializer.Serialize(manuallySaved) == JsonSerializer.Serialize(form.CaptureConfiguration()));
            Descendants(form).OfType<TextBox>().Single(control => control.Name == "GamePath").Text = Path.Combine(directory, "unsaved.exe");
            Descendants(form).OfType<Button>().Single(button => button.Name == "Reload").PerformClick();
            Assert(JsonSerializer.Serialize(form.CaptureConfiguration()) == JsonSerializer.Serialize(manuallySaved));
            ShowFeature(form, "PaFeature");
            Descendants(form).OfType<Button>().Single(button => button.Name == "PaLogOpen").PerformClick();
            ShowFeature(form, "LeagueChangesFeature");
            Descendants(form).OfType<Button>().Single(button => button.Name == "LeagueChangeLog").PerformClick();
            Assert(form.OwnedForms.Length == 2);
            advanced.Checked = false;
            Application.DoEvents();
            Assert(hidden.All(control => !control.Visible) && notice.Visible && form.OwnedForms.Length == 0);
            Assert(JsonSerializer.Serialize(form.CaptureConfiguration()) == before);
            var observation = Descendants(form).OfType<ToggleSwitch>().Single(control => control.Name == "LeagueReputationEnabled");
            var diagnostics = Descendants(form).OfType<ToggleSwitch>().Single(control => control.Name == "LeagueDiagnosticsEnabled");
            observation.Checked = diagnostics.Checked = false;
            Assert(!notice.Visible);
            observation.Checked = true;
            Assert(notice.Visible && notice.Text.Contains(localizer.Text("LeagueEnabled")));
            diagnostics.Checked = true;
        }
        config = form.CaptureConfiguration();
        new ConfigurationStore(Path.Combine(directory, "advanced-mode.json")).Save(config);
        Assert(!new ConfigurationStore(Path.Combine(directory, "advanced-mode.json")).Load()!.AdvancedMode);
        Descendants(form).OfType<TabControl>().Single().SelectTab("SkinGuide");
        Assert(Descendants(form).Single(control => control.Name == "SkinSnippet").Visible);
        Assert(Descendants(form).Single(control => control.Name == "SkinInstructions").Visible);
        form.Close();
    }

    private static void TestLaunchAutosave(string directory, string languagePath)
    {
        using var form = new MainForm(directory, new Localizer(languagePath), _ => new[] { Hd });
        form.Show();
        var config = Default();
        config.Language = "pl";
        config.PaEnabled = true;
        config.PaChance = 83;
        config.UserDataPath = Path.Combine(directory, "User data");
        config.MatchRulesEnabled = false;
        config.PanelInformationEnabled = true;
        config.LeagueReputationEnabled = true;
        config.LeagueDiagnosticsEnabled = true;
        config.DisplayOverride = true;
        config.DisplayMode = DisplayMode.Borderless;
        config.Rules[0].Override = true;
        config.Rules[18].BenchOverride = true;
        config.Rules[18].Bench = 11;
        form.Populate(config, new[] { Hd });
        Assert(!Descendants(form).Single(control => control.Name == "ConfigurationActions").Visible);
        ShowFeature(form, "MatchRulesFeature");
        var grid = Descendants(form).OfType<DataGridView>().Single();
        grid.Sort(grid.Columns["Code"], System.ComponentModel.ListSortDirection.Descending);
        grid.CurrentCell = grid.Rows.Cast<DataGridViewRow>().Single(row => (int)row.Cells["Code"].Value == 0)
            .Cells["Substitutions"];
        grid.Focus();
        Assert(grid.BeginEdit(true));
        var editor = grid.EditingControl as TextBox ?? throw new InvalidOperationException("Missing grid editor.");
        editor.Text = "9";
        var path = Path.Combine(directory, "FmLauncher.config.json");
        var store = new ConfigurationStore(path);
        var starts = 0;
        form.LaunchGame(confirmation =>
        {
            Assert(confirmation.Contains("stała baza 8%") && !confirmation.Contains("83%"));
            Assert(confirmation.Contains("trzy tymczasowe hooki"));
            Assert(confirmation.Contains("Zmiany i rezerwowi: OFF"));
            return DialogResult.OK;
        }, selected =>
        {
            var saved = store.Load()!;
            Assert(JsonSerializer.Serialize(saved) == JsonSerializer.Serialize(selected));
            Assert(saved.Language == "pl" && saved.PaEnabled && saved.PaChance == 83 && saved.PanelInformationEnabled);
            Assert(saved.LeagueReputationEnabled && saved.LeagueDiagnosticsEnabled);
            Assert(saved.UserDataPath == config.UserDataPath && !saved.MatchRulesEnabled);
            Assert(saved.DisplayOverride && saved.DisplayMode == DisplayMode.Borderless && saved.Resolution == Hd);
            Assert(saved.Rules[0].Override && saved.Rules[0].Substitutions == 9);
            Assert(saved.Rules[18].BenchOverride && saved.Rules[18].Bench == 11);
            starts++;
        });
        Assert(starts == 1);
        config.PaChance = 0;
        form.Populate(config, new[] { Hd });
        form.LaunchGame(confirmation =>
        {
            Assert(confirmation.Contains("stała baza 8%"));
            return DialogResult.Cancel;
        }, _ => starts++);
        Assert(starts == 1);
        var before = File.ReadAllBytes(path);
        config.PaChance = 42;
        form.Populate(config, new[] { Hd });
        form.LaunchGame(_ => DialogResult.Cancel, _ => starts++);
        Assert(starts == 1 && File.ReadAllBytes(path).SequenceEqual(before));

        using (var locked = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read))
            Reject(() => form.LaunchGame(_ => DialogResult.OK, _ => starts++), "ConfigSaveError");
        Assert(starts == 1 && File.ReadAllBytes(path).SequenceEqual(before));
        Assert(!Directory.GetFiles(directory, "*.tmp").Any());

        config.Resolution = new Resolution(1280, 720);
        form.Populate(config, new[] { Hd });
        var confirmed = false;
        Reject(() => form.LaunchGame(_ => { confirmed = true; return DialogResult.OK; }, _ => starts++),
            "ResolutionUnavailable");
        Assert(!confirmed && starts == 1 && File.ReadAllBytes(path).SequenceEqual(before));
        form.Close();
    }
}
