using System.Text.Json;
using System.Diagnostics;
using System.Security.Cryptography;
using System.Buffers.Binary;
using System.ComponentModel;
using System.Runtime.InteropServices;
using FmLauncher;

namespace FmLauncher.Tests;

internal static partial class Program
{
    private static int count;
    private static readonly Resolution Hd = new(1920, 1080);

    [STAThread]
    private static int Main(string[] args)
    {
        using (var current = Process.GetCurrentProcess())
        {
            if (current.ProcessName.StartsWith("FmLauncher.TestGame.", StringComparison.Ordinal))
            {
                File.WriteAllText(Path.Combine(AppContext.BaseDirectory, "child-working-directory.txt"), Environment.CurrentDirectory);
                Thread.Sleep(30000);
                return 0;
            }
        }
        Application.SetHighDpiMode(HighDpiMode.PerMonitorV2);
        Application.SetUnhandledExceptionMode(UnhandledExceptionMode.ThrowException);
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        if (args.Length == 2 && args[0] == "--ui-layout")
        {
            var uiDirectory = Path.Combine(Path.GetTempPath(), "FmLauncher.UiLayout." + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(uiDirectory);
            try
            {
                var languagePath = Path.Combine(AppContext.BaseDirectory, "FmLauncher.languages.json");
                using (var form = new MainForm(uiDirectory, new Localizer(languagePath), _ => new[] { Hd }))
                {
                    form.Show();
                    var config = Default();
                    config.Language = "pl";
                    config.LeagueChangesEnabled = true;
                    form.Populate(config, new[] { Hd });
                    Application.DoEvents();
                    Directory.CreateDirectory(args[1]);
                    void Snapshot(string name)
                    {
                        using var image = new Bitmap(form.Width, form.Height);
                        form.DrawToBitmap(image, new Rectangle(Point.Empty, form.Size));
                        image.Save(Path.Combine(args[1], name + ".png"));
                    }
                    Snapshot("home");
                    form.ApplyTheme(true);
                    Snapshot("home-dark");
                    form.ApplyTheme(false);
                    ShowFeature(form, "MatchRulesFeature");
                    Snapshot("details");
                    form.ApplyTheme(true);
                    Snapshot("details-dark");
                    form.ApplyTheme(false);
                    form.Size = form.MinimumSize;
                    Snapshot("minimum");
                    form.Size = new Size(1000, 900);
                    Descendants(form).OfType<TabControl>().Single().SelectTab("SkinGuide");
                    Snapshot("skins");
                    form.ApplyTheme(true);
                    Snapshot("skins-dark");
                    form.Close();
                }
                Run("compact equal-height tiles, aligned details/display controls, persistent graphics options and dark mode",
                    () => TestCompactDarkLayout(uiDirectory, languagePath));
                Run("two tabs, feature toggles/details, centered play, profile status and social links",
                    () => TestFeatureTabs(uiDirectory, languagePath));
                Run("user folder validation, legacy defaults, skin folder selection and independent match-rule switch",
                    () => TestUserDataConfiguration(uiDirectory));
                Run("player mode hides technical tools, preserves active flags, warns and restores advanced access",
                    () => TestAdvancedMode(uiDirectory, languagePath));
                Run("launch autosave preserves folder and disabled rule selections",
                    () => TestLaunchAutosave(uiDirectory, languagePath));
                return 0;
            }
            catch (Exception ex) { Console.Error.WriteLine(ex); return 1; }
            finally { Directory.Delete(uiDirectory, recursive: true); }
        }
        if (args.Length is 1 or 2 && args[0] == "--rule-scope")
        {
            var scopeDirectory = Path.Combine(Path.GetTempPath(), "FmLauncher.RuleScope." + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(scopeDirectory);
            try
            {
                var languagePath = Path.Combine(AppContext.BaseDirectory, "FmLauncher.languages.json");
                Run("rule scope: localized names/types, unknowns, sorting, selection and unchanged configuration",
                    () => TestRuleScope(scopeDirectory, languagePath));
                if (args.Length == 2)
                    Run("rule scope: native assignments, RTTI names and fixture-to-match data flow",
                        () => TestRuleScopeNative(args[1]));
                return 0;
            }
            catch (Exception ex) { Console.Error.WriteLine(ex); return 1; }
            finally { Directory.Delete(scopeDirectory, recursive: true); }
        }
        if (args.Length == 2 && args[0] == "--modern-rules")
        {
            var modernDirectory = Path.Combine(Path.GetTempPath(), "FmLauncher.ModernRules." + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(modernDirectory);
            try
            {
                Run("native aging delay, biennial reputation writer, profiles and change log",
                    () => TestModernRules(modernDirectory, args[1]));
                return 0;
            }
            catch (Exception ex) { Console.Error.WriteLine(ex); return 1; }
            finally
            {
                Directory.Delete(modernDirectory, recursive: true);
            }
        }
        if ((args.Length == 1 && args[0] == "--league-reputation")
            || (args.Length == 3 && args[0] == "--league-live"))
            return RunLeagueTests(args);
        if (args.Length == 2 && args[0] == "--league-diagnostics")
        {
            var diagnosticsDirectory = Path.Combine(Path.GetTempPath(), "FmLauncher.LeagueDiagnostics." + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(diagnosticsDirectory);
            try
            {
                Run("league lifecycle guards, journal persistence, errors and legacy config", () => TestLeagueDiagnostics(diagnosticsDirectory));
                Run("league diagnostics: real x86 execution and suspended FM08 installation",
                    () => TestLeagueDiagnosticNative(diagnosticsDirectory, args[1]));
                return 0;
            }
            catch (Exception ex) { Console.Error.WriteLine(ex); return 1; }
            finally
            {
                foreach (var file in Directory.GetFiles(diagnosticsDirectory)) File.Delete(file);
                Directory.Delete(diagnosticsDirectory);
            }
        }
        if (args.Length == 4 && args[0] == "--install-skins")
        {
            try
            {
                var localizer = new Localizer(Path.Combine(AppContext.BaseDirectory, "FmLauncher.languages.json"));
                localizer.Select(args[3]);
                using var verified = MatchRulePatch.OpenVerifiedGame(args[1]);
                Console.WriteLine("Installed panel overrides; changed files: "
                    + SkinPanelInstaller.Install(args[1], args[2], localizer.Text("PanelFatigueTitle")));
                return 0;
            }
            catch (Exception ex) { Console.Error.WriteLine(ex); return 1; }
        }
        if (args.Length == 2 && args[0] == "--panels")
        {
            var temporary = Path.Combine(Path.GetTempPath(), "FmLauncher.Panels." + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(temporary);
            try
            {
                Run("panel skin XML and localized instructions", () => TestPanelXml(temporary, args[1]));
                Run("read-only panels: actual x86 payload", () => TestPanelsNative(temporary, args[1]));
                Run("suspended FM08 panel installation and opt-out", () => TestPanelsSuspended(args[1]));
                return 0;
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine(ex);
                if (ex is LauncherException error) Console.Error.WriteLine(string.Join(" | ", error.Arguments));
                return 1;
            }
            finally
            {
                foreach (var file in Directory.GetFiles(temporary)) File.Delete(file);
                Directory.Delete(temporary);
            }
        }
        DisplayMode? selectedDisplay = null;
        if (args.Length == 3 && args[0] == "--display-game"
            && Enum.TryParse<DisplayMode>(args[2], out var selection) && Enum.IsDefined(selection))
            selectedDisplay = selection;
        if (args.Length != 0 && !((args.Length == 2 && args[0] is "--game" or "--display-game" or "--pa-analysis")
            || selectedDisplay is not null || (args.Length == 1 && args[0] == "--pa-native")))
        {
            Console.Error.WriteLine("Usage: FmLauncher.Tests [--game|--display-game|--pa-analysis <original fm.exe> [Fullscreen|Window|Borderless]]");
            return 1;
        }
        var gamePath = args.Length >= 2 ? args[1] : null;
        if (selectedDisplay is not null || (args.Length == 2 && args[0] == "--pa-analysis")
            || (args.Length == 1 && args[0] == "--pa-native"))
        {
            try
            {
                if (selectedDisplay is { } selected)
                    Run("FM08 live display: " + selected, () => TestLiveDisplay(gamePath!, selected));
                else if (args[0] == "--pa-analysis")
                    Run("FM08 read-only PA binary contract", () => TestPaContract(gamePath!));
                else
                {
                    var temporary = Path.Combine(Path.GetTempPath(), "FmLauncher.PaTest." + Guid.NewGuid().ToString("N"));
                    Directory.CreateDirectory(temporary);
                    try
                    {
                        Run("PA age/mentality policy, rounding and validation", TestPaPolicy);
                        Run("PA real x86 payload", () => TestPaNative(temporary));
                    }
                    finally
                    {
                        var payload = Path.Combine(temporary, "pa-payload.bin");
                        if (File.Exists(payload)) File.Delete(payload);
                        var entry = Path.Combine(temporary, "pa-event.bin");
                        if (File.Exists(entry)) File.Delete(entry);
                        var factors = Path.Combine(temporary, "pa-model-cases.bin");
                        if (File.Exists(factors)) File.Delete(factors);
                        Directory.Delete(temporary);
                    }
                }
                return 0;
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine(ex);
                if (ex is LauncherException error) Console.Error.WriteLine(string.Join(" | ", error.Arguments));
                return 1;
            }
        }
        var directory = Path.Combine(Path.GetTempPath(), "FmLauncher.Tests." + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        try
        {
            Run("29 independent rules and known originals", () =>
            {
                var config = Default();
                Assert(config.Language == "en" && config.Rules.Count == 29);
                Assert(config.Rules[18].Substitutions == 12 && config.Rules[20].Substitutions == 5);
                Assert(RuleCatalog.Original(1) == (3, 5));
                Assert(RuleCatalog.Original(22) is null && RuleCatalog.Original(28) is null);
                config.Rules[0].Override = true;
                config.Rules[0].Substitutions = 7;
                Assert(!config.Rules[1].Override && config.Rules[1].Substitutions == 3);
                ConfigurationValidator.Validate(config);
            });
            Run("atomic save, reload, PA preservation and override toggle", () =>
            {
                var path = Path.Combine(directory, "config.json");
                var store = new ConfigurationStore(path);
                Assert(store.Load() is null);
                var config = Default();
                config.Language = "pl";
                config.PaEnabled = true;
                config.PaChance = 73;
                config.Rules[4].Override = true;
                config.Rules[4].Substitutions = 6;
                config.Rules[4].BenchOverride = true;
                config.Rules[4].Bench = 11;
                store.Save(config);
                config = store.Load()!;
                config.PaEnabled = false;
                config.Rules[4].Override = false;
                config.Rules[4].BenchOverride = false;
                store.Save(config);
                var restored = store.Load()!;
                Assert(restored.Language == "pl" && !restored.PaEnabled && restored.PaChance == 73);
                Assert(!restored.Rules[4].Override && restored.Rules[4].Substitutions == 6);
                Assert(!restored.Rules[4].BenchOverride && restored.Rules[4].Bench == 11);
                Assert(!Directory.GetFiles(directory, "*.tmp").Any());
            });
            Run("exact rendering thresholds and disconnected displays", () =>
            {
                foreach (var resolution in new[] { new Resolution(1921, 1080), new Resolution(1920, 1081),
                    new Resolution(2560, 720), new Resolution(0, 720), new Resolution(1280, -1) })
                {
                    var config = Default();
                    config.Resolution = resolution;
                    Reject(() => ConfigurationValidator.Validate(config), "InvalidResolution");
                }
                var valid = Default();
                valid.DisplayOverride = true;
                ConfigurationValidator.ValidateDisplay(valid, new[] { Hd });
                Reject(() => ConfigurationValidator.ValidateDisplay(valid, new[] { new Resolution(1280, 720) }),
                    "ResolutionUnavailable");
            });
            Run("PA boundaries, rule codes and numeric storage bounds", () =>
            {
                foreach (var chance in new[] { 0, 100 })
                {
                    var config = Default();
                    config.PaChance = chance;
                    ConfigurationValidator.Validate(config);
                }
                foreach (var chance in new[] { -1, 101 })
                {
                    var config = Default();
                    config.PaChance = chance;
                    Reject(() => ConfigurationValidator.Validate(config), "InvalidPa");
                }
                var duplicate = Default();
                duplicate.Rules[28].Code = 0;
                Reject(() => ConfigurationValidator.Validate(duplicate), "InvalidRules");
                var missing = Default();
                missing.Rules.RemoveAt(0);
                Reject(() => ConfigurationValidator.Validate(missing), "InvalidRules");
                var invalid = Default();
                invalid.Rules[0].Bench = 128;
                Reject(() => ConfigurationValidator.Validate(invalid), "InvalidRuleValue");
                invalid = Default();
                invalid.Rules[0].Substitutions = 127;
                ConfigurationValidator.Validate(invalid);
                invalid.Rules[0].Override = true;
                Reject(() => ConfigurationValidator.Validate(invalid), "InvalidSubstitutionLimit");
                invalid.Rules[0].Substitutions = 12;
                ConfigurationValidator.Validate(invalid);
            });
            Run("legacy JSON leaves bench overrides disabled and preserves limits", () =>
            {
                var path = Path.Combine(directory, "legacy.json");
                var config = Default();
                config.Rules[0].Override = true;
                config.Rules[0].Substitutions = 7;
                config.Rules[0].Bench = 127;
                var json = JsonSerializer.Serialize(config, ConfigurationStore.JsonOptions)
                    .Replace("      \"BenchOverride\": false,\r\n", "")
                    .Replace("      \"BenchOverride\": false,\n", "");
                Assert(!json.Contains("BenchOverride"));
                File.WriteAllText(path, json);
                var restored = new ConfigurationStore(path).Load()!;
                Assert(restored.Rules.All(rule => !rule.BenchOverride));
                Assert(restored.Rules[0].Override && restored.Rules[0].Substitutions == 7 && restored.Rules[0].Bench == 127);
                restored.Rules[0].BenchOverride = true;
                Reject(() => ConfigurationValidator.Validate(restored), "InvalidBenchLimit");
                foreach (var value in new[] { 0, 12 })
                {
                    restored.Rules[0].Bench = value;
                    ConfigurationValidator.Validate(restored);
                }
                restored.Rules[0].Bench = 13;
                Reject(() => ConfigurationValidator.Validate(restored), "InvalidBenchLimit");
            });
            Run("malformed JSON is never overwritten", () =>
            {
                var path = Path.Combine(directory, "broken.json");
                const string content = "{ broken";
                File.WriteAllText(path, content);
                Reject(() => new ConfigurationStore(path).Load(), "ConfigReadError");
                Assert(File.ReadAllText(path) == content);
                var json = JsonSerializer.Serialize(Default(), ConfigurationStore.JsonOptions);
                File.WriteAllText(path, json.Replace("\"PaChance\": 0,", ""));
                Reject(() => new ConfigurationStore(path).Load(), "ConfigReadError");
                File.WriteAllText(path, json.Replace("\"SchemaVersion\": 1", "\"SchemaVersion\": 2"));
                Reject(() => new ConfigurationStore(path).Load(), "UnsupportedVersion");
                File.WriteAllText(path, json.Replace("\"Fullscreen\"", "55"));
                Reject(() => new ConfigurationStore(path).Load(), "ConfigReadError");
            });
            var languageSource = Path.Combine(AppContext.BaseDirectory, "FmLauncher.languages.json");
            var languagePath = Path.Combine(directory, "languages.json");
            File.Copy(languageSource, languagePath);
            Run("two-tab layout, toggles, inline details, social links and bilingual minimum size",
                () => TestFeatureTabs(directory, languagePath));
            Run("user folder validation, skin folder selection and legacy UI configuration",
                () => TestUserDataConfiguration(directory));
            Run("player mode hides technical tools, preserves active flags, warns and restores advanced access",
                () => TestAdvancedMode(directory, languagePath));
            Run("compact equal-height tiles, aligned controls, persistent graphics options and dark mode",
                () => TestCompactDarkLayout(directory, languagePath));
            Run("rule scope names/types, unknowns, sorting, bilingual layout and unchanged settings",
                () => TestRuleScope(directory, languagePath));
            Run("launch automatically saves current edits; cancellation, invalid settings and save failures block startup",
                () => TestLaunchAutosave(directory, languagePath));
            Run("league target formula and annual observation simulation", TestLeagueModel);
            Run("league reports: atomic persistence, failures and legacy configuration", () => TestLeagueReports(directory));
            Run("league native snapshot: strict reads, active partition and stability", TestLeagueMemory);
            Run("league diagnostic persistence and lifecycle guards", () => TestLeagueDiagnostics(directory));
            Run("automatic career profile creation, matching and immutable migration", () => TestProfileAutomation(directory));
            Run("automatic profile failures, save retry and legacy safeguards", () => TestProfileAutomationEdgeCases(directory));
            Run("display defaults, legacy opt-out and active minimum", () =>
            {
                var config = LauncherConfiguration.CreateDefault(Path.Combine(directory, "fm.exe"), Hd);
                Assert(config.DisplayOverride);
                var path = Path.Combine(directory, "legacy-display.json");
                var json = JsonSerializer.Serialize(config, ConfigurationStore.JsonOptions)
                    .Replace("  \"DisplayOverride\": true,\r\n", "")
                    .Replace("  \"DisplayOverride\": true,\n", "");
                Assert(!json.Contains("DisplayOverride"));
                File.WriteAllText(path, json);
                Assert(!new ConfigurationStore(path).Load()!.DisplayOverride);
                config.Resolution = new Resolution(639, 480);
                Reject(() => ConfigurationValidator.ValidateDisplay(config, new[] { config.Resolution }), "InvalidGameResolution");
                config.DisplayOverride = false;
                ConfigurationValidator.ValidateDisplay(config, Array.Empty<Resolution>());
            });
            Run("framed working-area fit, DPI margins and exact rendering cap", () =>
            {
                var candidates = new[] { Hd, new Resolution(1921, 1080), new Resolution(1920, 1081),
                    new Resolution(1904, 1001), new Resolution(1280, 720), new Resolution(640, 480),
                    new Resolution(639, 480), new Resolution(640, 479) };
                var window = DisplayService.FilterForGame(candidates, DisplayMode.Window, new Size(1920, 1040), new Size(16, 39));
                Assert(window.SequenceEqual(new[] { candidates[3], candidates[4], candidates[5] }));
                var highDpi = DisplayService.FilterForGame(candidates, DisplayMode.Window, new Size(1920, 1040), new Size(32, 78));
                Assert(highDpi.SequenceEqual(new[] { candidates[4], candidates[5] }));
                foreach (var mode in new[] { DisplayMode.Fullscreen, DisplayMode.Borderless })
                {
                    var modes = DisplayService.FilterForGame(candidates, mode, new Size(3840, 2120), new Size(16, 39));
                    Assert(modes.SequenceEqual(new[] { Hd, candidates[3], candidates[4], candidates[5] }));
                }
                Reject(() => DisplayService.FilterForGame(candidates, DisplayMode.Window, new Size(640, 440), new Size(16, 39)),
                    "NoSafeResolution");
            });
            Run("display UI applies mode filtering, visible adjustment and saved-selection preservation", () =>
            {
                var small = new Resolution(1280, 720);
                using var form = new MainForm(directory, new Localizer(languagePath),
                    mode => mode == DisplayMode.Window ? new[] { small } : new[] { Hd, small });
                form.Show();
                var config = Default();
                config.DisplayOverride = true;
                form.Populate(config, new[] { Hd, small });
                var mode = Descendants(form).OfType<ComboBox>().Single(control => control.Name == "DisplayMode");
                mode.SelectedIndex = (int)DisplayMode.Window;
                Assert(form.CaptureConfiguration().Resolution == small);
                Assert(Descendants(form).OfType<Label>().Any(label => label.Text.Contains("largest fitting")));
                form.ApplyLanguage("pl");
                Assert(Descendants(form).OfType<Label>().Any(label => label.Text.Contains("największą pasującą")));
                config.DisplayMode = DisplayMode.Window;
                form.Populate(config, new[] { small });
                var captured = form.CaptureConfiguration();
                Assert(captured.DisplayOverride && captured.Resolution == Hd);
                Reject(() => ConfigurationValidator.ValidateDisplay(captured, new[] { small }), "ResolutionUnavailable");
                Descendants(form).OfType<CheckBox>().Single(control => control.Name == "DisplayOverride").Checked = false;
                captured = form.CaptureConfiguration();
                Assert(!captured.DisplayOverride && !mode.Enabled && captured.Resolution == Hd);
                form.Close();
            });
            Run("complete English and Polish translations, UTF-8", () =>
            {
                var file = ReadLanguages(languagePath);
                Assert(file.Languages[0].Texts.Keys.Order().SequenceEqual(file.Languages[1].Texts.Keys.Order()));
                var localizer = new Localizer(languagePath);
                Assert(localizer.Warning is null && localizer.Code == "en");
                foreach (var language in file.Languages)
                {
                    localizer.Select(language.Code);
                    foreach (var key in file.Languages[0].Texts.Keys)
                        Assert(localizer.Text(key, Enumerable.Repeat<object>("test",
                            System.Text.CompositeFormat.Parse(language.Texts[key]).MinimumArgumentCount).ToArray()).Length > 0);
                }
                Assert(localizer.Text("Browse").Contains('ą'));
            });
            Run("third language added through JSON and missing-key fallback", () =>
            {
                var file = ReadLanguages(languagePath);
                file.Languages.Add(new LanguageDefinition
                {
                    Code = "de", Name = "Deutsch",
                    Texts = new Dictionary<string, string> { ["Title"] = "Fußball " + new string('x', 300) }
                });
                File.WriteAllText(languagePath, JsonSerializer.Serialize(file, ConfigurationStore.JsonOptions));
                var localizer = new Localizer(languagePath);
                Assert(localizer.Warning is null && localizer.Languages.Count == 3);
                localizer.Select("de");
                Assert(localizer.Text("Title").Length > 300);
                Assert(localizer.Text("Launch") == "Launch FM08");
            });
            Run("missing/broken language file, duplicate codes and format mismatch", () =>
            {
                Assert(new Localizer(Path.Combine(directory, "absent.json")).Warning is not null);
                var badPath = Path.Combine(directory, "bad-languages.json");
                File.WriteAllText(badPath, "{}");
                var fallback = new Localizer(badPath);
                Assert(fallback.Warning is not null && fallback.Text("Launch") == "Launch FM08");
                Assert(File.ReadAllText(badPath) == "{}");
                var file = ReadLanguages(languageSource);
                file.Languages[1].Code = "en";
                File.WriteAllText(badPath, JsonSerializer.Serialize(file));
                Assert(new Localizer(badPath).Warning is not null);
                file = ReadLanguages(languageSource);
                file.Languages[1].Texts["InvalidGamePath"] = "Invalid {1}";
                File.WriteAllText(badPath, JsonSerializer.Serialize(file));
                Assert(new Localizer(badPath).Warning is not null);
            });
            Run("WinForms language changes preserve all edited settings", () =>
            {
                using var form = new MainForm(directory, new Localizer(languagePath), _ => new[] { Hd });
                form.Show();
                var config = Default();
                config.PaChance = 84;
                config.DisplayMode = DisplayMode.Borderless;
                config.Rules[12].Override = true;
                config.Rules[12].Bench = 11;
                form.Populate(config, new[] { Hd });
                var grid = Descendants(form).OfType<DataGridView>().Single();
                Assert(!grid.Rows[12].Cells["Substitutions"].ReadOnly && grid.Rows[12].Cells["Bench"].ReadOnly);
                Assert(grid.Rows[0].Cells["Substitutions"].ReadOnly && grid.Rows[0].Cells["Bench"].ReadOnly);
                form.ApplyLanguage("pl");
                var polish = form.CaptureConfiguration();
                Assert(polish.Language == "pl" && polish.PaChance == 84 && !polish.PaEnabled);
                Assert(polish.DisplayMode == DisplayMode.Borderless && polish.Resolution == Hd);
                Assert(polish.Rules[12].Override && polish.Rules[12].Bench == 11);
                form.ApplyLanguage("de");
                form.PerformLayout();
                var german = form.CaptureConfiguration();
                Assert(form.Text.Length > 300 && german.GamePath == config.GamePath);
                Assert(german.Rules.Count == 29 && german.Rules[12].Bench == 11);
                Assert(form.IsHandleCreated && form.Visible);
                form.Close();
            });
            Run("spin buttons, numeric sorting and independent override controls", () =>
            {
                using var form = new MainForm(directory, new Localizer(languagePath), _ => new[] { Hd });
                form.Show();
                ShowFeature(form, "MatchRulesFeature");
                var config = Default();
                config.Rules[0].Override = true;
                config.Rules[0].Substitutions = 7;
                config.Rules[18].BenchOverride = true;
                form.Populate(config, new[] { Hd });
                var grid = Descendants(form).OfType<DataGridView>().Single();
                var subs = Descendants(form).OfType<NumericUpDown>().Single(control => control.Name == "SubstitutionsEditor");
                var bench = Descendants(form).OfType<NumericUpDown>().Single(control => control.Name == "BenchEditor");
                grid.CurrentCell = grid.Rows[0].Cells["Substitutions"];
                Assert(subs.Enabled && !bench.Enabled && subs.Value == 7);
                subs.UpButton();
                Assert(form.CaptureConfiguration().Rules[0].Substitutions == 8);
                subs.DownButton();
                Assert(form.CaptureConfiguration().Rules[0].Substitutions == 7);
                grid.CurrentCell = grid.Rows[18].Cells["Bench"];
                Assert(bench.Enabled && !subs.Enabled && bench.Value == 12);
                bench.UpButton();
                Assert(bench.Value == 12);
                bench.DownButton();
                Assert(form.CaptureConfiguration().Rules[18].Bench == 11);
                bench.Value = 0;
                bench.DownButton();
                Assert(bench.Value == 0);
                bench.Value = 11;
                foreach (var column in new[] { "Code", "Substitutions", "Bench" })
                foreach (var direction in new[] { ListSortDirection.Ascending, ListSortDirection.Descending })
                {
                    grid.Sort(grid.Columns[column], direction);
                    var values = grid.Rows.Cast<DataGridViewRow>().Select(row => (int)row.Cells[column].Value).ToList();
                    Assert(values.SequenceEqual(direction == ListSortDirection.Ascending
                        ? values.Order() : values.OrderDescending()));
                    var settings = form.CaptureConfiguration();
                    Assert(settings.Rules.Select(rule => rule.Code).SequenceEqual(Enumerable.Range(0, 29)));
                    Assert(settings.Rules[0].Override && settings.Rules[0].Substitutions == 7 && !settings.Rules[0].BenchOverride);
                    Assert(settings.Rules[18].BenchOverride && settings.Rules[18].Bench == 11 && !settings.Rules[18].Override);
                }
                grid.Sort(grid.Columns["BenchOverride"], ListSortDirection.Descending);
                Assert(grid.Rows[0].Cells["BenchOverride"].Value is true);
                var selected = grid.Rows.Cast<DataGridViewRow>().Single(row => (int)row.Cells["Code"].Value == 18);
                grid.CurrentCell = selected.Cells["Bench"];
                bench.UpButton();
                Assert(form.CaptureConfiguration().Rules[18].Bench == 12);
                form.ApplyLanguage("pl");
                Assert(bench.Value == 12 && bench.Enabled);
                selected.Cells["BenchOverride"].Value = false;
                Assert(!bench.Enabled && selected.Cells["Bench"].ReadOnly);
                Assert(form.CaptureConfiguration().Rules[18].Bench == 12);
                var store = new ConfigurationStore(Path.Combine(directory, "sorted-settings.json"));
                store.Save(form.CaptureConfiguration());
                Assert(store.Load()!.Rules[0].Substitutions == 7 && store.Load()!.Rules[18].Bench == 12);
                var snapshot = Environment.GetEnvironmentVariable("FMLAUNCHER_UI_SNAPSHOT");
                if (!string.IsNullOrWhiteSpace(snapshot))
                {
                    using var image = new Bitmap(form.Width, form.Height);
                    form.DrawToBitmap(image, new Rectangle(Point.Empty, form.Size));
                    image.Save(snapshot);
                }
                form.Close();
            });
            Run("invalid grid edits report errors without reentrant startup or dialogs", () =>
            {
                using var form = new MainForm(directory, new Localizer(languagePath), _ => new[] { Hd });
                form.Show();
                ShowFeature(form, "MatchRulesFeature");
                var config = Default();
                config.Rules[0].Override = true;
                config.Rules[0].Substitutions = 7;
                form.Populate(config, new[] { Hd });
                var grid = Descendants(form).OfType<DataGridView>().Single();
                foreach (var invalid in new[] { "13", "-1", "abc" })
                {
                    grid.CurrentCell = grid.Rows[0].Cells["Substitutions"];
                    grid.Focus();
                    Assert(grid.BeginEdit(true));
                    var editor = grid.EditingControl as TextBox ?? throw new InvalidOperationException("Missing grid editor.");
                    editor.Text = invalid;
                    Assert(!form.ValidateChildren());
                    Assert(!string.IsNullOrWhiteSpace(grid.Rows[0].ErrorText));
                    Application.DoEvents();
                    Assert(grid.Rows.Count == 29 && grid.Rows[0].Cells["Override"].Value is true);
                    Reject(() => form.CaptureConfiguration(), "InvalidGrid");
                    Reject(() => form.LaunchGame(_ => throw new InvalidOperationException("Unexpected confirmation."),
                        _ => throw new InvalidOperationException("Unexpected start.")), "InvalidGrid");
                    Reject(() => form.ApplyLanguage("pl"), "InvalidGrid");
                    grid.CancelEdit();
                    Assert(form.CaptureConfiguration().Rules[0].Substitutions == 7);
                }
                form.ApplyLanguage("pl");
                Assert(form.CaptureConfiguration().Language == "pl");
                form.Close();
            });
            Run("legacy inactive value is shown without clamping and can be corrected", () =>
            {
                using var form = new MainForm(directory, new Localizer(languagePath), _ => new[] { Hd });
                form.Show();
                var config = Default();
                config.Rules[0].Bench = 127;
                form.Populate(config, new[] { Hd });
                var grid = Descendants(form).OfType<DataGridView>().Single();
                grid.CurrentCell = grid.Rows[0].Cells["Bench"];
                var editor = Descendants(form).OfType<NumericUpDown>().Single(control => control.Name == "BenchEditor");
                Assert(editor.Value == 127 && !editor.Enabled);
                Assert(form.CaptureConfiguration().Rules[0].Bench == 127);
                grid.CurrentCell = grid.Rows[0].Cells["BenchOverride"];
                grid.Rows[0].Cells["BenchOverride"].Value = true;
                Reject(() => form.CaptureConfiguration(), "InvalidBenchLimit");
                grid.Rows[0].Cells["Bench"].Value = 11;
                Assert(editor.Enabled && editor.Maximum == 12 && editor.Value == 11);
                Assert(form.CaptureConfiguration().Rules[0].Bench == 11);
                form.Close();
            });
            Run("display detection produces only capped modes", () =>
            {
                var modes = DisplayService.Detect();
                Assert(modes.Count > 0 && modes.Distinct().Count() == modes.Count);
                Assert(modes.All(mode => mode.Width <= 1920 && mode.Height <= 1080));
                Console.WriteLine("  Detected: " + string.Join(", ", modes));
            });
            Run("small, 4K and non-16:9 desktops choose capped native proportions", () =>
            {
                var candidates = new[] { Hd, new Resolution(2560, 1440), new Resolution(1280, 720),
                    new Resolution(1440, 1080), new Resolution(800, 600) };
                Assert(DisplayService.FilterAndOrder(candidates, new Resolution(3840, 2160))[0] == Hd);
                Assert(DisplayService.FilterAndOrder(candidates, new Resolution(1280, 720))[0] == new Resolution(1280, 720));
                Assert(DisplayService.FilterAndOrder(candidates, new Resolution(1600, 1200))[0] == new Resolution(1440, 1080));
                Reject(() => DisplayService.FilterAndOrder(candidates, new Resolution(320, 200)), "NoSafeResolution");
            });
            Run("invalid game path is blocked", () =>
            {
                using var launcher = new GameLauncher();
                Reject(() => launcher.Launch("relative.exe"), "InvalidGamePath");
                Reject(() => launcher.Launch(Path.Combine(directory, "absent.exe")), "InvalidGamePath");
            });
            Run("payload shape, independent overrides and original fallback jump", () =>
            {
                var config = Default();
                config.Rules[0].Override = true;
                config.Rules[0].Substitutions = 7;
                config.Rules[20].Override = true;
                config.Rules[20].Substitutions = 0;
                var payload = MatchRulePatch.BuildPayload(0x10000000, config.Rules, RuleLimit.Substitutions);
                Assert(payload.Length == 96 && payload[0] == 1 && payload[32] == 7);
                Assert(payload[20] == 1 && payload[52] == 0 && payload[1] == 0 && payload[28] == 0);
                Assert(payload.AsSpan(64, 5).SequenceEqual(MatchRulePatch.OriginalEntry));
                var returnOffset = BinaryPrimitives.ReadUInt32LittleEndian(payload.AsSpan(91, 4));
                Assert(unchecked(0x10000000u + 95 + returnOffset) == MatchRulePatch.GetterAddress(RuleLimit.Substitutions) + 5);
                var entry = MatchRulePatch.BuildEntryJump(0x10000040, RuleLimit.Substitutions);
                Assert(unchecked(MatchRulePatch.GetterAddress(RuleLimit.Substitutions) + 5
                    + BinaryPrimitives.ReadUInt32LittleEndian(entry.AsSpan(1))) == 0x10000040);
            });
            Run("PA payload shape, native stamp and validation", () =>
            {
                Assert(GamePaPatch.InitialState(1, 0x11000000).Length == GamePaPatch.StateSize);
                foreach (var chance in new[] { 0, 1, 50, 99, 100 })
                {
                    var payload = GamePaPatch.BuildPayload(0x10001000, 0x10000000, chance, GamePaPatch.OriginalEntry.ToArray());
                    var target = unchecked(0x10001000u + (uint)payload.Length
                        + BinaryPrimitives.ReadUInt32LittleEndian(payload.AsSpan(payload.Length - 4)));
                    Assert(target == GamePaPatch.HookAddress + 5);
                    if (chance == 0) Assert(payload.AsSpan(0, 5).SequenceEqual(GamePaPatch.OriginalEntry));
                    else Assert(payload.AsSpan(0, 8).SequenceEqual(new byte[] { 0x9C, 0x60, 0x8B, 0xC1, 0x87, 0x45, 0x04, 0x3B }));
                }
                foreach (var chance in new[] { -1, 101 })
                    Reject(() => GamePaPatch.BuildPayload(0x10001000, 0x10000000, chance, GamePaPatch.OriginalEntry.ToArray()), "InvalidPa");
                Reject(() => GamePaPatch.BuildPayload(0x10001000, 0x10000000, 50, new byte[5]), "UnexpectedGameMemory");
            });
            Run("PA age/mentality policy, rounding and validation", TestPaPolicy);
            Run("PA real x86 payload", () => TestPaNative(directory));
            Run("PA journal batches, wrap, errors and localized window", () => TestPaJournal(directory));
            Run("bench-only payload is independent of substitution settings", () =>
            {
                var config = Default();
                config.Rules[0].BenchOverride = true;
                config.Rules[0].Bench = 11;
                config.Rules[22].BenchOverride = true;
                config.Rules[22].Bench = 0;
                var bench = MatchRulePatch.BuildPayload(0x10000100, config.Rules, RuleLimit.Bench);
                var subs = MatchRulePatch.BuildPayload(0x10000000, config.Rules, RuleLimit.Substitutions);
                Assert(bench[0] == 1 && bench[32] == 11 && bench[22] == 1 && bench[54] == 0);
                Assert(bench[28] == 0 && subs.Take(29).All(value => value == 0));
                Assert(unchecked(0x10000100u + 95 + BinaryPrimitives.ReadUInt32LittleEndian(bench.AsSpan(91)))
                    == MatchRulePatch.GetterAddress(RuleLimit.Bench) + 5);
            });
            Run("unsupported EXE is rejected before start when overrides are enabled", () =>
            {
                var config = Default();
                config.GamePath = Path.Combine(AppContext.BaseDirectory, "FmLauncher.NativeFixture.exe");
                config.Rules[0].Override = true;
                using var launcher = new GameLauncher();
                Reject(() => launcher.Launch(config), "UnsupportedGame");
                Assert(!launcher.IsRunning);
                config.DisplayOverride = false;
                config.PaEnabled = true;
                config.Rules[0].Override = false;
                foreach (var legacyChance in new[] { 0, 100 })
                {
                    config.PaChance = legacyChance;
                    Reject(() => launcher.Launch(config), "UnsupportedGame");
                    Assert(!launcher.IsRunning);
                }
                config.Rules[0].BenchOverride = true;
                Reject(() => launcher.Launch(config), "UnsupportedGame");
                Assert(!launcher.IsRunning);
                config.Rules[0].BenchOverride = false;
                config.PaEnabled = false;
                config.PanelInformationEnabled = false;
                config.LeagueDiagnosticsEnabled = true;
                Reject(() => launcher.Launch(config), "UnsupportedGame");
                Assert(!launcher.IsRunning && !launcher.LeagueDiagnostics.Installed);
                config.LeagueDiagnosticsEnabled = false;
                config.DisplayOverride = true;
                config.Resolution = DisplayService.Detect()[0];
                Reject(() => launcher.Launch(config), "UnsupportedGame");
                Assert(!launcher.IsRunning);
            });
            Run("real process launch, working directory, duplicate start and cleanup", () =>
            {
                foreach (var source in Directory.GetFiles(AppContext.BaseDirectory))
                    File.Copy(source, Path.Combine(directory, Path.GetFileName(source)), overwrite: true);
                var helperName = "FmLauncher.TestGame." + Guid.NewGuid().ToString("N");
                var helper = Path.Combine(directory, helperName + ".exe");
                File.Copy(Path.Combine(AppContext.BaseDirectory, "FmLauncher.Tests.exe"), helper);
                using var first = new GameLauncher();
                using var second = new GameLauncher();
                Process? child = null;
                try
                {
                    var unmodified = Default();
                    unmodified.GamePath = helper;
                    unmodified.MatchRulesEnabled = false;
                    unmodified.Rules[0].Override = true;
                    unmodified.Rules[0].BenchOverride = true;
                    first.Launch(unmodified);
                    Assert(first.IsRunning);
                    Assert(unmodified.Rules[0].Override && unmodified.Rules[0].BenchOverride);
                    var children = Process.GetProcessesByName(helperName);
                    Assert(children.Length == 1);
                    child = children[0];
                    Reject(() => first.Launch(helper), "AlreadyRunning");
                    Reject(() => second.Launch(helper), "AlreadyRunning");
                    var workingDirectoryFile = Path.Combine(directory, "child-working-directory.txt");
                    Assert(SpinWait.SpinUntil(() => File.Exists(workingDirectoryFile), 5000));
                    Assert(File.ReadAllText(workingDirectoryFile) == directory);
                    first.Dispose();
                    Assert(!child.HasExited);
                    Reject(() => second.Launch(helper), "AlreadyRunning");
                    child.Kill();
                    Assert(child.WaitForExit(5000));
                    second.Launch(helper);
                    child.Dispose();
                    child = Process.GetProcessesByName(helperName).Single();
                    child.Kill();
                    Assert(child.WaitForExit(5000));
                    Assert(second.CheckExited() && !second.IsRunning);
                }
                finally
                {
                    if (child is not null)
                    {
                        if (!child.HasExited)
                        {
                            child.Kill();
                            child.WaitForExit(5000);
                        }
                        child.Dispose();
                    }
                }
            });
            Run("native suspended startup, explicit resume and handle ownership", () =>
            {
                var helper = Directory.GetFiles(directory, "FmLauncher.TestGame.*.exe").Single();
                var marker = Path.Combine(directory, "child-working-directory.txt");
                File.Delete(marker);
                using var suspended = new SuspendedGameProcess(helper);
                using var child = Process.GetProcessById(suspended.ProcessId);
                try
                {
                    Assert(!child.HasExited && !File.Exists(marker));
                    using var managed = suspended.Resume();
                    Assert(managed.Id == child.Id);
                    Assert(SpinWait.SpinUntil(() => File.Exists(marker), 5000));
                    suspended.Dispose();
                    Assert(!child.HasExited);
                }
                finally
                {
                    if (!child.HasExited)
                    {
                        child.Kill();
                        child.WaitForExit(5000);
                    }
                }
            });
            if (gamePath is not null)
            {
                var gameHash = GameFileHash(gamePath);
                Run("exact EXE allowlist, tampered/truncated rejection and verification handle ownership",
                    () => TestGameAllowlist(gamePath, directory));
                Run("real x86 getters: both, mixed, disabled, subs-only and bench-only", () =>
                {
                    using var verified = MatchRulePatch.OpenVerifiedGame(gamePath);
                    for (var variant = 0; variant < 5; variant++)
                    {
                        var config = Default();
                        foreach (var rule in config.Rules)
                        {
                            rule.Override = variant is 0 or 3 || (variant == 1 && rule.Code % 2 == 0);
                            rule.BenchOverride = variant is 0 or 4 || (variant == 1 && rule.Code % 2 == 1);
                            rule.Substitutions = rule.Code % 13;
                            rule.Bench = (28 - rule.Code) % 13;
                        }
                        var payloadFile = Path.Combine(directory, "payload.bin");
                        var subs = MatchRulePatch.BuildPayload(0x10000000, config.Rules, RuleLimit.Substitutions);
                        var bench = MatchRulePatch.BuildPayload(0x10000100, config.Rules, RuleLimit.Bench);
                        File.WriteAllBytes(payloadFile, subs.Concat(bench).ToArray());
                        var start = new ProcessStartInfo(Path.Combine(AppContext.BaseDirectory, "FmLauncher.NativeFixture.exe"))
                        {
                            UseShellExecute = false, RedirectStandardOutput = true, RedirectStandardError = true
                        };
                        start.ArgumentList.Add(gamePath);
                        start.ArgumentList.Add(payloadFile);
                        var originalsFile = Path.Combine(directory, "originals.bin");
                        start.ArgumentList.Add(originalsFile);
                        using var fixture = Process.Start(start)!;
                        try
                        {
                            Assert(fixture.WaitForExit(10000));
                            var output = fixture.StandardOutput.ReadToEnd() + fixture.StandardError.ReadToEnd();
                            Console.Write(output);
                            Assert(fixture.ExitCode == 0);
                            var originals = File.ReadAllBytes(originalsFile);
                            foreach (var rule in config.Rules)
                            {
                                if (RuleCatalog.Original(rule.Code) is { } known)
                                {
                                    Assert(originals[rule.Code * 4] == known.Substitutions
                                        && originals[rule.Code * 4 + 1] == known.Substitutions);
                                    Assert(originals[rule.Code * 4 + 2] == known.Bench
                                        && originals[rule.Code * 4 + 3] == known.Bench);
                                }
                            }
                        }
                        finally
                        {
                            if (!fixture.HasExited)
                            {
                                fixture.Kill();
                                fixture.WaitForExit(5000);
                            }
                        }
                    }
                });
                Run("real FM08 suspended injection, unchanged bench/PA and abort cleanup", () =>
                {
                    var existing = Process.GetProcessesByName(Path.GetFileNameWithoutExtension(gamePath));
                    try { Assert(existing.Length == 0); }
                    finally { foreach (var candidate in existing) candidate.Dispose(); }
                    using var verified = MatchRulePatch.OpenVerifiedGame(gamePath);
                    using var before = SHA256.Create();
                    var hash = Convert.ToHexString(before.ComputeHash(verified));
                    var native = new SuspendedGameProcess(gamePath);
                    using var observer = Process.GetProcessById(native.ProcessId);
                    try
                    {
                        var benchBefore = native.Read(0x00AFE150, 0xB0);
                        var paBefore = native.Read(0x008D3D60, 16);
                        var config = Default();
                        config.Rules[0].Override = true;
                        config.Rules[0].Substitutions = 7;
                        native.ApplyRuleLimits(config.Rules, verified);
                        var entry = native.Read(MatchRulePatch.GetterAddress(RuleLimit.Substitutions), 5);
                        Assert(entry[0] == 0xE9);
                        var cave = unchecked(MatchRulePatch.GetterAddress(RuleLimit.Substitutions) + 5
                            + BinaryPrimitives.ReadUInt32LittleEndian(entry.AsSpan(1)) - 64);
                        Assert(native.Read(cave, 96).SequenceEqual(MatchRulePatch.BuildPayload(cave, config.Rules, RuleLimit.Substitutions)));
                        Assert(native.Read(0x00AFE150, 0xB0).SequenceEqual(benchBefore));
                        Assert(native.Read(0x008D3D60, 16).SequenceEqual(paBefore));
                        Reject(() => native.ApplyRuleLimits(config.Rules, verified), "UnexpectedGameMemory");
                    }
                    finally { native.Dispose(); }
                    Assert(observer.WaitForExit(5000));
                    verified.Position = 0;
                    Assert(Convert.ToHexString(SHA256.HashData(verified)) == hash);
                    Console.WriteLine("  FM08 was created suspended, never resumed, and terminated.");
                });
                Run("FM08 PA analysis: manager/person ABI, weekly scheduler and post-stamp hook", () => TestPaContract(gamePath));
                Run("FM08 PA suspended injection, zero chance and combined integrations", () =>
                {
                    using var verified = MatchRulePatch.OpenVerifiedGame(gamePath);
                    foreach (var chance in new[] { 0, 8, 50, 100 })
                    {
                        using var native = new SuspendedGameProcess(gamePath);
                        using var observer = Process.GetProcessById(native.ProcessId);
                        var before = native.Read(GamePaPatch.HookAddress, 16);
                        var entryBefore = native.Read(0x008D3D60, 16);
                        var getters = Enum.GetValues<RuleLimit>().ToDictionary(limit => limit,
                            limit => native.Read(MatchRulePatch.GetterAddress(limit), 16));
                        var extra = native.Read(0x00AFE080, 0x50);
                        var state = chance == 8 ? native.ApplyPaGrowth(PaGrowthPolicy.Default, verified)
                            : native.ApplyPaGrowth(chance, verified);
                        if (chance == 0)
                        {
                            Assert(state == 0 && native.Read(GamePaPatch.HookAddress, 16).SequenceEqual(before));
                        }
                        else
                        {
                            var jump = native.Read(GamePaPatch.HookAddress, 5);
                            Assert(jump[0] == 0xE9);
                            var cave = unchecked(GamePaPatch.HookAddress + 5 + BinaryPrimitives.ReadUInt32LittleEndian(jump.AsSpan(1)));
                            var payload = GamePaPatch.BuildPayload(cave, state, chance, before.AsSpan(0, 5).ToArray());
                            Assert(native.Read(cave, payload.Length).SequenceEqual(payload));
                            var counters = native.Read(state, GamePaPatch.StateSize);
                            Assert(BinaryPrimitives.ReadUInt32LittleEndian(counters) != 0
                                && counters.AsSpan(4, 28).ToArray().All(value => value == 0));
                            var journal = BinaryPrimitives.ReadUInt32LittleEndian(counters.AsSpan(32));
                            Assert(journal != 0 && native.Read(journal, GamePaPatch.LogEntrySize).All(value => value == 0));
                            Assert(native.Read(GamePaPatch.HookAddress + 5, 11).SequenceEqual(before.Skip(5)));
                            Reject(() => native.ApplyPaGrowth(chance, verified), "UnexpectedGameMemory");
                        }
                        if (chance == 100)
                        {
                            var config = Default();
                            config.Rules[0].Override = config.Rules[0].BenchOverride = true;
                            native.ApplyRuleLimits(config.Rules, verified);
                            native.ApplyDisplay(new DisplayLaunchSettings(DisplayMode.Window, new Resolution(1280, 720),
                                DisplayService.DesktopBounds()), verified);
                            foreach (var limit in Enum.GetValues<RuleLimit>())
                                Assert(native.Read(MatchRulePatch.GetterAddress(limit), 1)[0] == 0xE9);
                        }
                        else
                            foreach (var limit in Enum.GetValues<RuleLimit>())
                                Assert(native.Read(MatchRulePatch.GetterAddress(limit), 16).SequenceEqual(getters[limit]));
                        Assert(native.Read(0x008D3D60, 16).SequenceEqual(entryBefore));
                        Assert(native.Read(0x00AFE080, 0x50).SequenceEqual(extra));
                        native.Dispose();
                        Assert(observer.WaitForExit(5000));
                    }
                    verified.Position = 0;
                    Assert(Convert.ToHexString(SHA256.HashData(verified)) == gameHash);
                });
                Run("FM08 display hooks preserve instructions, return targets and independent match patches", () =>
                {
                    var originals = new Dictionary<uint, byte[]>
                    {
                        [GameDisplayPatch.OpenAddress] = [0x6A, 0xFF, 0x68, 0x9F, 0x0D, 0x1F, 0x01],
                        [GameDisplayPatch.CreatedAddress] = [0xF6, 0x84, 0x24, 0x28, 0x02, 0, 0, 0x02],
                        [GameDisplayPatch.ExitAddress] = [0x8B, 0x8C, 0x24, 0x08, 0x02, 0, 0],
                        [GameDisplayPatch.StyleAddress] = [0x8B, 0x7C, 0x24, 0x14, 0x8B, 0x2D, 0xBC, 0xA3, 0x21, 0x01],
                        [GameDisplayPatch.ResizeAddress] = [0x83, 0xEC, 0x2C, 0x53, 0x55]
                    };
                    using var verified = MatchRulePatch.OpenVerifiedGame(gamePath);
                    foreach (var mode in Enum.GetValues<DisplayMode>())
                    {
                        using var native = new SuspendedGameProcess(gamePath, GameDisplayPatch.Arguments(mode), dpiAware: true);
                        var config = Default();
                        config.Rules[0].Override = config.Rules[0].BenchOverride = true;
                        native.ApplyRuleLimits(config.Rules, verified);
                        var pa = native.Read(0x008D3D60, 16);
                        var extra = native.Read(0x00AFE080, 0x50);
                        foreach (var entry in originals) Assert(native.Read(entry.Key, entry.Value.Length).SequenceEqual(entry.Value));
                        var settings = new DisplayLaunchSettings(mode, new Resolution(1280, 720), DisplayService.DesktopBounds());
                        var state = native.ApplyDisplay(settings, verified);
                        Assert(native.Read(state, GameDisplayPatch.StateSize).All(value => value == 0));
                        foreach (var (site, original) in originals)
                        {
                            var jump = native.Read(site, original.Length);
                            if (site == GameDisplayPatch.StyleAddress && mode != DisplayMode.Window)
                            {
                                Assert(jump.SequenceEqual(original));
                                continue;
                            }
                            Assert(jump[0] == 0xE9 && jump.Skip(5).All(value => value == 0x90));
                            var address = unchecked(site + 5 + BinaryPrimitives.ReadUInt32LittleEndian(jump.AsSpan(1)));
                            var code = site switch
                            {
                                GameDisplayPatch.OpenAddress => GameDisplayPatch.Open(address, state, settings, original),
                                GameDisplayPatch.CreatedAddress => GameDisplayPatch.Created(address, state, settings, original),
                                GameDisplayPatch.ExitAddress => GameDisplayPatch.Exit(address, state, original),
                                GameDisplayPatch.StyleAddress => GameDisplayPatch.Style(address, original),
                                GameDisplayPatch.ResizeAddress => GameDisplayPatch.Resize(address, settings, original),
                                _ => throw new InvalidOperationException()
                            };
                            Assert(native.Read(address, code.Length).SequenceEqual(code));
                            Assert(code.AsSpan(code.Length - 5 - original.Length, original.Length).SequenceEqual(original));
                            Assert(unchecked(address + (uint)code.Length
                                + BinaryPrimitives.ReadUInt32LittleEndian(code.AsSpan(code.Length - 4))) == site + original.Length);
                        }
                        foreach (var limit in Enum.GetValues<RuleLimit>())
                            Assert(native.Read(MatchRulePatch.GetterAddress(limit), 1)[0] == 0xE9);
                        Assert(native.Read(0x008D3D60, 16).SequenceEqual(pa));
                        Assert(native.Read(0x00AFE080, 0x50).SequenceEqual(extra));
                        Reject(() => native.ApplyDisplay(settings, verified), "UnexpectedGameMemory");
                        foreach (var invalid in new[] { new Resolution(1921, 1080), new Resolution(1920, 1081),
                            new Resolution(639, 480), new Resolution(640, 479) })
                            Reject(() => GameDisplayPatch.Resize(0x10000000, settings with { Resolution = invalid },
                                originals[GameDisplayPatch.ResizeAddress]), "InvalidGameResolution");
                    }
                    verified.Position = 0;
                    Assert(Convert.ToHexString(SHA256.HashData(verified)) == gameHash);
                });
                Run("FM08 bench-only, both and disabled patches preserve unrelated code", () =>
                {
                    using var verified = MatchRulePatch.OpenVerifiedGame(gamePath);
                    for (var variant = 0; variant < 3; variant++)
                    {
                        using var native = new SuspendedGameProcess(gamePath);
                        using var observer = Process.GetProcessById(native.ProcessId);
                        var originals = Enum.GetValues<RuleLimit>().ToDictionary(limit => limit,
                            limit => native.Read(MatchRulePatch.GetterAddress(limit), limit == RuleLimit.Substitutions ? 0x80 : 0xB0));
                        var paBefore = native.Read(0x008D3D60, 16);
                        var extraBefore = native.Read(0x00AFE080, 0x50);
                        var config = Default();
                        config.Rules[0].BenchOverride = variant != 2;
                        config.Rules[0].Bench = 11;
                        config.Rules[0].Override = variant == 1;
                        config.Rules[0].Substitutions = 7;
                        native.ApplyRuleLimits(config.Rules, verified);
                        foreach (var limit in Enum.GetValues<RuleLimit>())
                        {
                            var getter = MatchRulePatch.GetterAddress(limit);
                            if (config.Rules.Any(rule => MatchRulePatch.Enabled(rule, limit)))
                            {
                                var entry = native.Read(getter, 5);
                                Assert(entry[0] == 0xE9);
                                var cave = unchecked(getter + 5 + BinaryPrimitives.ReadUInt32LittleEndian(entry.AsSpan(1)) - 64);
                                Assert(native.Read(cave, 96).SequenceEqual(MatchRulePatch.BuildPayload(cave, config.Rules, limit)));
                            }
                            else Assert(native.Read(getter, originals[limit].Length).SequenceEqual(originals[limit]));
                        }
                        Assert(native.Read(0x008D3D60, 16).SequenceEqual(paBefore));
                        Assert(native.Read(0x00AFE080, 0x50).SequenceEqual(extraBefore));
                        native.Dispose();
                        Assert(observer.WaitForExit(5000));
                    }
                    verified.Position = 0;
                    Assert(Convert.ToHexString(SHA256.HashData(verified)) == gameHash);
                });
            }
            if (args.Length == 2 && args[0] == "--display-game")
            {
                foreach (var mode in Enum.GetValues<DisplayMode>())
                    Run("FM08 live display, renderer and desktop restoration: " + mode, () => TestLiveDisplay(gamePath!, mode));
            }
            Console.WriteLine($"PASS: {count} test groups.");
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(ex);
            if (ex is LauncherException error) Console.Error.WriteLine(string.Join(" | ", error.Arguments));
            return 1;
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    private static LauncherConfiguration Default()
    {
        var config = LauncherConfiguration.CreateDefault(Path.Combine(Path.GetTempPath(), "fm.exe"), Hd);
        config.DisplayOverride = false;
        config.PanelInformationEnabled = false;
        return config;
    }

    private static void TestPaNative(string directory)
    {
        var payloadPath = Path.Combine(directory, "pa-payload.bin");
        using (var writer = new BinaryWriter(File.Create(payloadPath)))
        {
            foreach (var chance in new[] { 0, 1, 8, 50, 99, 100 })
            {
                var payload = GamePaPatch.BuildPayload(0x10001000, 0x10000000, chance, GamePaPatch.OriginalEntry.ToArray());
                writer.Write(chance);
                writer.Write(payload.Length);
                writer.Write(payload);
            }
        }
        using (var writer = new BinaryWriter(File.Create(Path.Combine(directory, "pa-model-cases.bin"))))
        {
            foreach (var age in new[] { 13, 14, 18, 19, 21, 22, 24, 25, 27, 28, 30, 31, 33, 34, 100, 101 })
            foreach (var pro in new[] { -1, 0, 1, 10, 20, 21 })
            foreach (var amb in new[] { -1, 0, 1, 12, 20, 21 })
            foreach (var rawDet in new[] { -1, 0, 1, 2, 3, 47, 48, 49, 50, 51, 97, 98, 99, 100, 101 })
            {
                var invalid = age is < 14 or > 100 || pro is < 1 or > 20
                    || amb is < 1 or > 20 || rawDet is < 1 or > 100;
                writer.Write(age);
                writer.Write(pro);
                writer.Write(amb);
                writer.Write(rawDet);
                writer.Write(invalid ? -1 : PaGrowthPolicy.Default.ChanceBasisPoints(age, pro, amb,
                    Math.Clamp((rawDet + 2) / 5, 1, 20)));
            }
        }
        var path = Path.Combine(AppContext.BaseDirectory, "FmLauncher.NativeFixture.exe");
        if (!File.Exists(path)) throw new InvalidOperationException("Missing native fixture: " + path);
        var start = new ProcessStartInfo(path) { UseShellExecute = false, RedirectStandardOutput = true, RedirectStandardError = true };
        start.ArgumentList.Add("--pa");
        start.ArgumentList.Add(payloadPath);
        using var fixture = Process.Start(start) ?? throw new InvalidOperationException("Cannot start native PA fixture.");
        try
        {
            var output = fixture.StandardOutput.ReadToEndAsync();
            var error = fixture.StandardError.ReadToEndAsync();
            if (!fixture.WaitForExit(30000)) throw new InvalidOperationException("Native PA fixture timed out.");
            var text = output.GetAwaiter().GetResult();
            var errors = error.GetAwaiter().GetResult();
            if (fixture.ExitCode != 0) throw new InvalidOperationException(text + errors);
            Console.Write(text);
            var entry = GamePaJournal.Decode(File.ReadAllBytes(Path.Combine(directory, "pa-event.bin")));
            Assert(entry.FirstName == "\u0141ukasz" && entry.LastName == "Kowalski"
                && entry.CurrentAbility == 90 && entry.Before == 90 && entry.After == 91 && entry.PlayerId == 12345
                && entry.Epoch == 4 && !entry.NameIncomplete);
        }
        finally
        {
            if (!fixture.HasExited)
            {
                fixture.Kill();
                fixture.WaitForExit(5000);
            }
        }
    }

    private static void TestPaPolicy()
    {
        var model = PaGrowthPolicy.Default;
        Assert(model.ChanceBasisPoints(18, 20, 20, 20) == 1500);
        Assert(model.ChanceBasisPoints(23, 10, 12, 10) == 800);
        Assert(model.ChanceBasisPoints(29, 10, 12, 10) == 320);
        Assert(model.ChanceBasisPoints(34, 1, 1, 1) == 20);
        Assert(new PaGrowthPolicy { BaseChancePercent = 1 }.ChanceBasisPoints(18, 1, 1, 1) == 63);
        foreach (var (age, multiplier) in new[]
        {
            (14, 125), (18, 125), (19, 110), (21, 110), (22, 100), (24, 100),
            (25, 70), (27, 70), (28, 40), (30, 40), (31, 15), (33, 15), (34, 5), (100, 5)
        })
            Assert(model.ChanceBasisPoints(age, 10, 12, 10) == 8 * multiplier);
        var custom = new PaGrowthPolicy { BaseChancePercent = 100 };
        Assert(custom.ChanceBasisPoints(18, 20, 20, 20) == 10000);
        Reject(() => model.ChanceBasisPoints(13, 10, 10, 10), "InvalidPaInputs");
        Reject(() => model.ChanceBasisPoints(23, 0, 10, 10), "InvalidPaInputs");
        Reject(() => model.ChanceBasisPoints(23, 10, 21, 10), "InvalidPaInputs");
        Reject(() => model.ChanceBasisPoints(23, 10, 10, -1), "InvalidPaInputs");
        Reject(() => new PaGrowthPolicy { AmbitionWeight = 26 }.Validate(), "InvalidPaPolicy");
        Reject(() => new PaGrowthPolicy { MentalityDivisor = 0 }.Validate(), "InvalidPaPolicy");
        Reject(() => new PaGrowthPolicy { AgeBands = new[] { new PaAgeBand(100, 125), new PaAgeBand(18, 5) } }
            .Validate(), "InvalidPaPolicy");
        Assert(new PaGrowthPolicy { BaseChancePercent = 0 }.ChanceBasisPoints(18, 20, 20, 20) == 0);
        var payload = GamePaPatch.BuildPayload(0x10001000, 0x10000000, model, GamePaPatch.OriginalEntry.ToArray());
        Assert(payload.Length < 0xF00);
    }

    private static void TestPaJournal(string directory)
    {
        var eventBytes = File.ReadAllBytes(Path.Combine(directory, "pa-event.bin"));
        var state = GamePaPatch.InitialState(1, 0x11000000);
        var queue = new byte[GamePaPatch.LogCapacity * GamePaPatch.LogEntrySize];
        eventBytes.CopyTo(queue, 0);
        BinaryPrimitives.WriteUInt32LittleEndian(state.AsSpan(20), 1);
        byte[] Read(uint address, int size)
        {
            var bytes = address >= 0x11000000 ? queue : state;
            var offset = address - (address >= 0x11000000 ? 0x11000000u : 0x10000000u);
            return bytes.AsSpan((int)offset, size).ToArray();
        }
        void Write(uint address, byte[] bytes) => bytes.CopyTo(state, (int)(address - 0x10000000));
        var journal = new GamePaJournal();
        journal.Update(0x10000000, Read, Write);
        Assert(journal.Entries.Count == 1 && BinaryPrimitives.ReadUInt32LittleEndian(state.AsSpan(24)) == 1);
        journal.Update(0x10000000, Read, Write);
        Assert(journal.Entries.Count == 1);
        for (var i = 0; i < GamePaPatch.LogCapacity; i++)
            eventBytes.CopyTo(queue, i * GamePaPatch.LogEntrySize);
        BinaryPrimitives.WriteUInt32LittleEndian(state.AsSpan(20), 4097);
        BinaryPrimitives.WriteUInt32LittleEndian(state.AsSpan(28), 3);
        journal.Update(0x10000000, Read, Write);
        Assert(journal.Entries.Count == 4097 && journal.Dropped == 3
            && journal.Entries.All(entry => entry.FirstName == "\u0141ukasz" && entry.After == 91));
        BinaryPrimitives.WriteUInt32LittleEndian(state.AsSpan(20), 4098);
        Reject(() => journal.Update(0x10000000, Read, (_, _) => throw new LauncherException("PaLogInvalid")), "PaLogInvalid");
        Assert(journal.Entries.Count == 4097 && BinaryPrimitives.ReadUInt32LittleEndian(state.AsSpan(24)) == 4097);
        journal.Update(0x10000000, Read, Write);
        Assert(journal.Entries.Count == 4098);
        BinaryPrimitives.WriteUInt32LittleEndian(state.AsSpan(20), 8195);
        Reject(() => journal.Update(0x10000000, Read, Write), "PaLogInvalid");
        Assert(journal.Entries.Count == 4098 && BinaryPrimitives.ReadUInt32LittleEndian(state.AsSpan(24)) == 4098);
        var malformed = eventBytes.ToArray();
        BinaryPrimitives.WriteUInt32LittleEndian(malformed.AsSpan(16), 97);
        Reject(() => GamePaJournal.Decode(malformed), "PaLogInvalid");
        malformed = eventBytes.ToArray();
        BinaryPrimitives.WriteUInt16LittleEndian(malformed.AsSpan(10), 92);
        Reject(() => GamePaJournal.Decode(malformed), "PaLogInvalid");
        malformed = eventBytes.ToArray();
        BinaryPrimitives.WriteUInt32LittleEndian(malformed.AsSpan(28), 85);
        Reject(() => GamePaJournal.Decode(malformed), "PaLogInvalid");
        BinaryPrimitives.WriteUInt32LittleEndian(malformed.AsSpan(28), 91);
        Reject(() => GamePaJournal.Decode(malformed), "PaLogInvalid");
        malformed = eventBytes.ToArray();
        BinaryPrimitives.WriteUInt16LittleEndian(malformed.AsSpan(32), 0xD800);
        Assert(GamePaJournal.Decode(malformed).NameIncomplete);
        malformed = eventBytes.ToArray();
        BinaryPrimitives.WriteUInt16LittleEndian(malformed.AsSpan(32), '\n');
        Assert(GamePaJournal.Decode(malformed).NameIncomplete);
        var localizer = new Localizer(Path.Combine(AppContext.BaseDirectory, "FmLauncher.languages.json"));
        using var window = new PaLogForm(localizer, journal);
        window.Show();
        Application.DoEvents();
        var grid = (DataGridView)window.Controls.Find("PaLogEntries", true).Single();
        Assert(grid.RowCount == 4098 && grid.Rows[0].Cells[2].Value?.ToString() == "\u0141ukasz"
            && grid.Rows[0].Cells[4].Value?.ToString() == "90" && grid.Rows[0].Cells[5].Value?.ToString() == "90"
            && grid.Rows[0].Cells[6].Value?.ToString() == "91");
        localizer.Select("pl");
        window.ApplyLanguage();
        Assert(grid.Columns[2].HeaderText == "Imię" && window.Text.StartsWith("Logi wzrostu PA"));
        journal.Error = new LauncherException("PaLogInvalid");
        Assert(PaLogForm.Status(localizer, journal).Contains("działają nadal"));
        journal.Reset();
        window.RefreshJournal();
        Assert(grid.RowCount == 0 && journal.Dropped == 0 && journal.Error is null);
        window.Close();
        var logConfiguration = Default();
        logConfiguration.AdvancedMode = true;
        new ConfigurationStore(Path.Combine(directory, "FmLauncher.config.json")).Save(logConfiguration);
        using var main = new MainForm(directory, localizer, _ => new[] { Hd });
        main.Show();
        ShowFeature(main, "PaFeature");
        Application.DoEvents();
        var open = Descendants(main).OfType<Button>().Single(button => button.Text == localizer.Text("PaLogOpen"));
        open.PerformClick();
        Application.DoEvents();
        Assert(main.OwnedForms.Single() is PaLogForm);
        main.ApplyLanguage("pl");
        Assert(main.OwnedForms.Single().Text.StartsWith("Logi wzrostu PA"));
        main.OwnedForms.Single().Close();
        open.PerformClick();
        Application.DoEvents();
        Assert(main.OwnedForms.Single() is PaLogForm && !main.IsDisposed);
        main.Close();
    }

    private static void TestPaContract(string path)
    {
        var originalHash = GameFileHash(path);
        using var verified = MatchRulePatch.OpenVerifiedGame(path);
        byte[] Read(uint address, int length)
        {
            verified.Position = address - 0x400000;
            var bytes = new byte[length];
            verified.ReadExactly(bytes);
            return bytes;
        }
        uint Pointer(uint address) => BinaryPrimitives.ReadUInt32LittleEndian(Read(address, 4));
        string NativeType(uint vtable)
        {
            var descriptor = Pointer(Pointer(vtable - 4) + 12);
            return System.Text.Encoding.ASCII.GetString(Read(descriptor + 8, 64)
                .TakeWhile(value => value != 0).ToArray());
        }
        Assert(NativeType(0x0154CE1C) == ".?AVTRAINING_MANAGER@@");
        Assert(NativeType(0x015AB414) == ".?AVACTUAL_PLAYER@@");
        Assert(Read(0x008D3D60, 6).SequenceEqual(new byte[] { 0x83, 0xEC, 0x68, 0x53, 0x8B, 0xD9 }));
        Assert(Read(0x008D3DB0, 6).SequenceEqual(new byte[] { 0x8B, 0x74, 0x24, 0x78, 0x85, 0xF6 }));
        Assert(Read(0x008D3DE2, 14).SequenceEqual(new byte[]
            { 0x8B, 0x16, 0x8B, 0xCE, 0xFF, 0x92, 0xA4, 0x02, 0, 0, 0x8B, 0xF0, 0x85, 0xF6 }));
        Assert(Read(0x008D3E5B, 12).SequenceEqual(new byte[]
            { 0x8B, 0x7B, 0x08, 0x2B, 0x7D, 0x04, 0x89, 0x7C, 0x24, 0x28, 0x75, 0x0F }));
        Assert(Read(0x008D5150, 13).SequenceEqual(new byte[]
            { 0x83, 0xEC, 0x1C, 0x8B, 0x51, 0x08, 0x42, 0x57, 0x33, 0xFF, 0x89, 0x51, 0x08 }));
        Assert(Read(0x008D7CDC, 22).SequenceEqual(new byte[]
            { 0x0F, 0xBF, 0xC6, 0x99, 0xB9, 0x07, 0, 0, 0, 0xF7, 0xF9, 0x85, 0xD2,
              0x75, 0x07, 0x8B, 0xCF, 0xE8, 0x5E, 0xD4, 0xFF, 0xFF }));
        Assert(Read(0x008D3F30, 6).SequenceEqual(new byte[] { 0x8B, 0x4F, 0x08, 0x89, 0x4D, 0x04 }));
        Assert(Read(GamePaPatch.HookAddress, 5).AsSpan().SequenceEqual(GamePaPatch.OriginalEntry));
        foreach (var personVtable in new[] { 0x015AB12Cu, 0x015E9CDCu })
        {
            Assert(Pointer(personVtable + 0x88) == 0x00CBA5B0);
            Assert(Pointer(personVtable + 0x21C) == 0x00CBAB00);
            Assert(Pointer(personVtable + 0x22C) == 0x00CBAB60);
        }
        foreach (var (thunk, target) in new[]
        {
            (0x00CBA5B0u, 0x00C80B80u), (0x00CBAB00u, 0x00C81A30u), (0x00CBAB60u, 0x00C81A60u)
        })
        {
            Assert(Read(thunk, 10).SequenceEqual(new byte[] { 0x2B, 0x49, 0xFC, 0x81, 0xC1, 0x0C, 1, 0, 0, 0xE9 }));
            Assert(unchecked(thunk + 14 + (uint)BinaryPrimitives.ReadInt32LittleEndian(Read(thunk + 10, 4))) == target);
        }
        Assert(Read(0x00C81A30, 12).SequenceEqual(new byte[]
            { 0x8B, 0x41, 0xC0, 0x85, 0xC0, 0x74, 0x05, 0x0F, 0xBE, 0x40, 0x1D, 0xC3 }));
        Assert(Read(0x00C81A60, 12).SequenceEqual(new byte[]
            { 0x8B, 0x41, 0xC0, 0x85, 0xC0, 0x74, 0x05, 0x0F, 0xBE, 0x40, 0x20, 0xC3 }));
        Assert(Read(0x00A63420, 12).SequenceEqual(new byte[]
            { 0x8B, 0x57, 0xFC, 0x8D, 0x4F, 0xFC, 0xFF, 0x92, 0x1C, 2, 0, 0 }));
        Assert(Read(0x00A65AAC, 12).SequenceEqual(new byte[]
            { 0x8B, 0x57, 0xFC, 0x8D, 0x4F, 0xFC, 0xFF, 0x92, 0x2C, 2, 0, 0 }));
        Assert(Read(0x00A74EF4, 3).SequenceEqual(new byte[] { 0x52, 0x6A, 0x1E }));
        Assert(Pointer(0x00CAE760 + 0x1E * 4) == 0x00CAE67B);
        Assert(Read(0x00CAE67B, 13).SequenceEqual(new byte[]
            { 0x8B, 0x01, 0xC7, 0x44, 0x24, 4, 0x4D, 0, 0, 0, 0xFF, 0x60, 0x18 }));
        Assert(Read(0x00CBAB20, 21).SequenceEqual(new byte[]
            { 0x8B, 0x81, 0x14, 0xFF, 0xFF, 0xFF, 0x6A, 0, 0x81, 0xC1, 0x14, 0xFF, 0xFF, 0xFF,
              0x6A, 1, 0x6A, 0x4D, 0xFF, 0x50, 0x18 }));
        Assert(Pointer(0x015AB414 + 0x18) == 0x00CAE280 && Pointer(0x015EA0D4 + 0x18) == 0x00CAE280);
        Assert(Read(0x00CAE29D, 15).SequenceEqual(new byte[]
            { 0x8B, 0x8E, 0xCC, 0, 0, 0, 0x53, 0x83, 0xC1, 0x1C, 0xE8, 0xE4, 0x36, 0xE2, 0xFF }));
        Assert(Read(0x00CAE2AC, 6).SequenceEqual(new byte[] { 0x0F, 0xBE, 0xC0, 0x83, 0xC0, 2 }));
        Assert(BitConverter.ToSingle(Read(0x0129ECD4, 4)) == 0.2f);
        Assert(Pointer(0x015AB12C + 0x90) == 0x00CBA5D0 && Pointer(0x015AB12C + 0x94) == 0x00CBA5E0);
        Assert(Pointer(Pointer(0x015AB12C - 4) + 4) == 0xEC);
        Assert(Read(0x00CBA5D0, 14).SequenceEqual(new byte[]
            { 0x2B, 0x49, 0xFC, 0x81, 0xC1, 0x0C, 0x01, 0, 0, 0xE9, 0x32, 0xDC, 0xFC, 0xFF }));
        Assert(Read(0x00CBA5E0, 14).SequenceEqual(new byte[]
            { 0x2B, 0x49, 0xFC, 0x81, 0xC1, 0x0C, 0x01, 0, 0, 0xE9, 0x42, 0xDC, 0xFC, 0xFF }));
        Assert(Read(0x00C88210, 9).SequenceEqual(new byte[] { 0x8B, 0x81, 0x20, 0xFF, 0xFF, 0xFF, 0xC2, 0x04, 0x00 }));
        Assert(Read(0x00C88230, 9).SequenceEqual(new byte[] { 0x8B, 0x81, 0x24, 0xFF, 0xFF, 0xFF, 0xC2, 0x04, 0x00 }));
        Assert(Pointer(0x015AB12C + 0x2A4) == 0x00CBAD10);
        Assert(Pointer(0x015AB414) == 0x00CBA270);
        Assert(Read(0x00CBA270, 5).SequenceEqual(new byte[] { 0x66, 0x8B, 0x41, 0x14, 0xC3 }));
        Assert(Pointer(0x015AB414 + 4) == 0x00CAE910);
        Assert(Read(0x00CAE910, 23).SequenceEqual(new byte[] {
            0x8A, 0x44, 0x24, 0x04, 0x84, 0xC0, 0x74, 0x08,
            0xE8, 0x63, 0xD5, 0, 0, 0xC2, 0x04, 0,
            0x66, 0x8B, 0x41, 0x16, 0xC2, 0x04, 0 }));
        var caOffset = Read(0x00CBA270 + 3, 1)[0];
        var paOffset = Read(0x00CAE920 + 3, 1)[0];
        Assert(GamePaPatch.CurrentAbilityOffset == caOffset && GamePaPatch.PotentialAbilityOffset == paOffset);
        Assert(Read(0x00CBAD10, 8).SequenceEqual(new byte[] { 0x2B, 0x49, 0xFC, 0xE9, 0x08, 0, 0, 0 }));
        Assert(Read(0x00CBAD20, 7).SequenceEqual(new byte[] { 0x8D, 0x81, 0x14, 0xFF, 0xFF, 0xFF, 0xC3 }));
        var nameAdjustment = BinaryPrimitives.ReadInt32LittleEndian(Read(0x00CBA5D0 + 5, 4));
        var firstOffset = nameAdjustment
            + BinaryPrimitives.ReadInt32LittleEndian(Read(0x00C88210 + 2, 4));
        var lastOffset = nameAdjustment
            + BinaryPrimitives.ReadInt32LittleEndian(Read(0x00C88230 + 2, 4));
        Assert(firstOffset == 0x2C && lastOffset == 0x30
            && GamePaPatch.FirstNameOffset == firstOffset && GamePaPatch.LastNameOffset == lastOffset);
        Assert(Read(0x008D3DF6, 14).SequenceEqual(new byte[]
            { 0x8B, 0x46, 0x04, 0x8B, 0x48, 0x04, 0x8B, 0x54, 0x31, 0x04, 0x8D, 0x4C, 0x31, 0x04 }));
        Assert(Pointer(0x015E9CDC + 0x90) == 0x00CBA5D0
            && Pointer(0x015E9CDC + 0x94) == 0x00CBA5E0
            && Pointer(0x015E9CDC + 0x2A4) == 0x00D2AA10);
        Assert(Read(0x00D2AA10, 11).SequenceEqual(new byte[]
            { 0x2B, 0x49, 0xFC, 0x83, 0xE9, 0x38, 0xE9, 0x05, 0x03, 0xF9, 0xFF }));
        Assert(Read(0x00CBA01F, 13).SequenceEqual(new byte[]
            { 0x8D, 0x8E, 0xEC, 0, 0, 0, 0xC7, 0x46, 0x04, 0x6C, 0xB6, 0x5A, 0x01 }));
        Assert(Read(0x00D2A77F, 13).SequenceEqual(new byte[]
            { 0x8D, 0x8E, 0x24, 0x01, 0, 0, 0xC7, 0x46, 0x04, 0x38, 0xA3, 0x5E, 0x01 }));
        foreach (var (vbtable, personOffset, first, last, uid) in new[]
        {
            (0x015AB66Cu, 0xEC, 0x118, 0x11C, 0x100),
            (0x015EA338u, 0x124, 0x150, 0x154, 0x138)
        })
        {
            Assert(Pointer(vbtable + 4) + 4 == personOffset);
            Assert(personOffset + firstOffset == first && personOffset + lastOffset == last
                && personOffset + Read(0x01096C90 + 2, 1)[0] == uid);
        }
        foreach (var chance in new[] { 1, 50, 100 })
        {
            var code = GamePaPatch.BuildPayload(0x10001000, 0x10000000, chance, GamePaPatch.OriginalEntry.ToArray());
            Assert(code.AsSpan().IndexOf(new byte[]
                { 0x8B, 0x46, 0x04, 0x8B, 0x40, 0x04, 0x8D, 0x6C, 0x06, 0x04, 0x8B, 0x45, 0x14 }) >= 0);
            foreach (var offset in new[] { (byte)firstOffset, (byte)lastOffset })
                Assert(code.AsSpan().IndexOf(new byte[] { 0x8B, 0xD5, 0x2B, 0x52, 0xFC, 0x8B, 0x52, offset }) >= 0);
            Assert(code.AsSpan().IndexOf(new byte[] { 0x8B, 0x96, 0x18, 0x01, 0, 0 }) < 0
                && code.AsSpan().IndexOf(new byte[] { 0x8B, 0x86, 0, 0x01, 0, 0 }) < 0);
            Assert(code.AsSpan().IndexOf(new byte[] { 0x0F, 0xB7, 0x4E, caOffset }) >= 0
                && code.AsSpan().IndexOf(new byte[] { 0x0F, 0xB7, 0x46, paOffset }) >= 0
                && code.AsSpan().IndexOf(new byte[] { 0x66, 0xF0, 0x0F, 0xB1, 0x56, paOffset }) >= 0
                && code.AsSpan().IndexOf(new byte[] { 0x66, 0xF0, 0x0F, 0xB1, 0x56, 0x1E }) < 0);
        }
        Assert(Read(0x00F4F598, 7).SequenceEqual(new byte[] { 0x8B, 0x4F, 0x08, 0x0F, 0xB7, 0x51, 0x04 }));
        Assert(Read(0x00F4F5AC, 7).SequenceEqual(new byte[] { 0x0F, 0xB7, 0x4E, 0x04, 0x8B, 0x56, 0x08 }));
        Assert(Read(0x01096C90, 4).SequenceEqual(new byte[] { 0x8B, 0x41, 0x14, 0xC3 }));
        verified.Position = 0;
        Assert(Convert.ToHexString(SHA256.HashData(verified)) == originalHash);
    }

    private static void TestLiveDisplay(string path, DisplayMode mode)
    {
        var originalHash = GameFileHash(path);
        var desktop = DisplayService.CurrentResolution();
        var savedMode = Marshal.AllocHGlobal(220);
        try
        {
            Marshal.Copy(new byte[220], 0, savedMode, 220);
            Marshal.WriteInt16(savedMode, 68, 220);
            if (!EnumDisplaySettings(null, -1, savedMode)) throw new Win32Exception(Marshal.GetLastWin32Error());
            var config = Default();
            config.GamePath = path;
            config.DisplayOverride = true;
            config.DisplayMode = mode;
            var available = DisplayService.Detect(mode);
            config.Resolution = available.Contains(new Resolution(1280, 720)) ? new Resolution(1280, 720) : available[0];
            config.Rules[0].Override = true;
            config.Rules[0].Substitutions = 7;
            config.Rules[0].BenchOverride = true;
            config.Rules[0].Bench = 11;
            using var launcher = new GameLauncher();
            launcher.Launch(config);
            using var owned = Process.GetProcessById(launcher.GameProcessId);
            try
            {
                Assert(!launcher.IsDisplayReady);
                var startup = Stopwatch.StartNew();
                while (!launcher.IsDisplayReady && startup.Elapsed < TimeSpan.FromSeconds(65))
                {
                    launcher.CheckExited();
                    Assert(launcher.IsRunning);
                    Thread.Sleep(100);
                }
                Assert(launcher.IsDisplayReady && launcher.RenderResolution == config.Resolution);
                var observe = Stopwatch.StartNew();
                while (observe.Elapsed < TimeSpan.FromSeconds(30))
                {
                    if (launcher.CheckExited())
                        throw new InvalidOperationException("FM08 exited during observation, exit code: " + owned.ExitCode);
                    Assert(launcher.IsRunning);
                    Thread.Sleep(200);
                }
                Console.WriteLine($"  PID {owned.Id}, HWND 0x{launcher.GameWindow.ToInt64():X}, render {launcher.RenderResolution}, title: {owned.MainWindowTitle}");
                var snapshotDirectory = Environment.GetEnvironmentVariable("FMLAUNCHER_GAME_SNAPSHOT");
                if (!string.IsNullOrWhiteSpace(snapshotDirectory))
                {
                    using var bitmap = new Bitmap(config.Resolution.Width, config.Resolution.Height);
                    using var graphics = Graphics.FromImage(bitmap);
                    var context = graphics.GetHdc();
                    try
                    {
                        if (!PrintWindow(launcher.GameWindow, context, 1))
                            throw new Win32Exception(Marshal.GetLastWin32Error());
                    }
                    finally { graphics.ReleaseHdc(context); }
                    bitmap.Save(Path.Combine(snapshotDirectory, mode + ".png"));
                }
                ShowWindow(launcher.GameWindow, 6);
                var restored = Stopwatch.StartNew();
                while (DisplayService.CurrentResolution() != desktop && restored.Elapsed < TimeSpan.FromSeconds(5))
                    Thread.Sleep(100);
                Assert(DisplayService.CurrentResolution() == desktop);
                launcher.CheckExited();
                Assert(launcher.IsRunning && launcher.RenderResolution == config.Resolution);
                ShowWindow(launcher.GameWindow, 9);
                Thread.Sleep(1000);
                launcher.CheckExited();
                Assert(launcher.IsRunning && launcher.RenderResolution == config.Resolution);
                launcher.Dispose();
                Assert(!owned.HasExited);
                owned.CloseMainWindow();
                if (!owned.WaitForExit(5000))
                {
                    ShowWindow(owned.MainWindowHandle, 6);
                    owned.Kill();
                    Assert(owned.WaitForExit(5000));
                }
            }
            finally
            {
                if (!owned.HasExited)
                {
                    owned.Kill();
                    Assert(owned.WaitForExit(5000));
                }
            }
        }
        finally
        {
            try
            {
                if (DisplayService.CurrentResolution() != desktop)
                {
                    var result = ChangeDisplaySettings(savedMode, 0);
                    if (result != 0) throw new InvalidOperationException("Could not restore original desktop mode: " + result);
                }
            }
            finally { Marshal.FreeHGlobal(savedMode); }
        }
        using var verified = MatchRulePatch.OpenVerifiedGame(path);
        Assert(Convert.ToHexString(SHA256.HashData(verified)) == originalHash);
    }

    [DllImport("user32.dll", EntryPoint = "EnumDisplaySettingsW", CharSet = CharSet.Unicode, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool EnumDisplaySettings(string? device, int mode, IntPtr settings);
    [DllImport("user32.dll", EntryPoint = "ChangeDisplaySettingsW")]
    private static extern int ChangeDisplaySettings(IntPtr settings, uint flags);
    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool ShowWindow(IntPtr window, int command);
    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool PrintWindow(IntPtr window, IntPtr context, uint flags);
    private static IEnumerable<Control> Descendants(Control parent)
    {
        foreach (Control child in parent.Controls)
        {
            yield return child;
            foreach (var nested in Descendants(child)) yield return nested;
        }
    }
    private static LanguageFile ReadLanguages(string path) =>
        JsonSerializer.Deserialize<LanguageFile>(File.ReadAllText(path), ConfigurationStore.JsonOptions)!;
    private static void Run(string name, Action test)
    {
        test();
        count++;
        Console.WriteLine("PASS: " + name);
    }
    private static void Assert(bool condition)
    {
        if (!condition) throw new InvalidOperationException("Assertion failed.");
    }
    private static void Reject(Action action, string key)
    {
        try { action(); }
        catch (LauncherException ex) when (ex.Key == key) { return; }
        catch (LauncherException ex)
        {
            throw new InvalidOperationException($"Expected {key}, received {ex.Key}: {string.Join(" | ", ex.Arguments)}", ex);
        }
        throw new InvalidOperationException("Expected error: " + key);
    }
}
