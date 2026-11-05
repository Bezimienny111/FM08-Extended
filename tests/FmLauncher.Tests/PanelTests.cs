using System.Buffers.Binary;
using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;
using System.Xml.Linq;
using FmLauncher;

namespace FmLauncher.Tests;

internal static partial class Program
{
    private static Localizer PanelLocalizer()
    {
        var localizer = new Localizer(Path.Combine(AppContext.BaseDirectory, "FmLauncher.languages.json"));
        localizer.Select("pl");
        return localizer;
    }

    private static void TestPanelXml(string directory, string gamePath)
    {
        var root = Path.GetDirectoryName(gamePath)!;
        var basePanels = new FmfArchive(Path.Combine(root, "data", "panels.fmf"));
        var patch = new FmfArchive(Path.Combine(root, "data", "updates", "update-802", "data", "panels.fmf"));
        Assert(basePanels.Names.Count() == 410 && patch.Names.Count() == 27);
        foreach (var name in new[] { "player training.xml", "team squad.xml", "tactic person list.xml", "person list table.xml" })
        {
            var source = patch.Names.Contains(name) ? patch.Get(name) : basePanels.Get(name);
            var changed = SkinPanelInstaller.Transform(name, source, "Zmęczenie sezonowe");
            Assert(changed.SequenceEqual(SkinPanelInstaller.Transform(name, changed, "Zmęczenie sezonowe")));
            var xml = XDocument.Parse(Encoding.UTF8.GetString(changed));
            if (name == "player training.xml")
                Assert(xml.Descendants("widget").Count(e => (string?)e.Attribute("id") == "Fmjd") == 1);
            else if (name == "person list table.xml")
            {
                var registry = xml.Descendants("list").Single(e => (string?)e.Attribute("id") == "column_display_properties");
                var original = XDocument.Parse(Encoding.UTF8.GetString(source)).Descendants("list")
                    .Single(e => (string?)e.Attribute("id") == "column_display_properties");
                Assert(registry.Elements("record").Count() == original.Elements("record").Count() + 3);
                foreach (var id in new[] { "Fjad", "Fcab", "Fpab" })
                {
                    var definition = registry.Elements("record").Single(e => e.Elements("flags").Any(
                        flag => (string?)flag.Attribute("id") == "id" && (string?)flag.Attribute("value") == id));
                    Assert(definition.Elements("record").Any(e => (string?)e.Attribute("id") == "column_properties"));
                    Assert(definition.Elements("record").Single(e => (string?)e.Attribute("id") == "column_heading")
                        .Elements("string").Single(e => (string?)e.Attribute("id") == "text").Attribute("value")?.Value
                        == (id == "Fjad" ? "Zmęczenie sezonowe" : id == "Fcab" ? "CA" : "PA"));
                }
                Assert(registry.Elements("record").Take(original.Elements("record").Count())
                    .Select(e => e.ToString()).SequenceEqual(original.Elements("record").Select(e => e.ToString())));
            }
            else
            {
                var target = xml.Descendants("record").Single(e => (string?)e.Attribute("id")
                    == (name == "team squad.xml" ? "sltn" : "posi")).Elements("record")
                    .Single(e => (string?)e.Attribute("id") == "view");
                Assert(target.Elements("record").Count(e => (string?)e.Attribute("id") == "Fjad") == 1);
                if (name == "team squad.xml")
                    Assert(target.Elements("record").Any(e => (string?)e.Attribute("id") == "Fcab")
                        && target.Elements("record").Any(e => (string?)e.Attribute("id") == "Fpab"));
                var edit = xml.Descendants("record").Single(e => (string?)e.Attribute("id") == SkinPanelInstaller.EditViewId);
                Assert(edit.Elements("string").Single().Attribute("value")?.Value == "Edycja");
                var columns = edit.Elements("record").Single(e => (string?)e.Attribute("id") == "view");
                var expected = new[] { "Ppkd", "Pnfo", "Pnam", "Ppos", "Pcon", "Fjad" }
                    .Concat(name == "team squad.xml" ? new[] { "Fcab", "Fpab" } : []);
                Assert(columns.Elements().Select(e => (string?)e.Attribute("id")).Order()
                    .SequenceEqual(expected.Order()));
                Assert(columns.Elements("record").Where(e => ((string?)e.Attribute("id"))?.StartsWith("F", StringComparison.Ordinal) == true)
                    .All(e => (int?)e.Attribute("auto_hide_priority") == 0));
            }
        }
        foreach (var snippet in new[] { SkinPanelInstaller.TrainingFragment, SkinPanelInstaller.SquadFragment,
            SkinPanelInstaller.TacticsFragment, SkinPanelInstaller.ColumnRegistryFragment("Fatigue & recovery") })
            XDocument.Parse("<panel>" + snippet + "</panel>");
        var fixture = Path.Combine(directory, "skins-fixture");
        Directory.CreateDirectory(Path.Combine(fixture, "steklo_black", "panels"));
        try
        {
            File.WriteAllText(Path.Combine(fixture, "steklo_black", "steklo_black.xml"), "<properties/>");
            var existing = Path.Combine(fixture, "steklo_black", "panels", "tactic person list.xml");
            var original = patch.Get("tactic person list.xml");
            File.WriteAllBytes(existing, original);
            var count = SkinPanelInstaller.Install(gamePath, fixture, "Zmęczenie sezonowe");
            Assert(count == 16);
            Assert(File.ReadAllBytes(existing + SkinPanelInstaller.BackupSuffix).SequenceEqual(original));
            Assert(SkinPanelInstaller.Install(gamePath, fixture, "Zmęczenie sezonowe") == 0);
            Assert(File.ReadAllBytes(existing + SkinPanelInstaller.BackupSuffix).SequenceEqual(original));
            Directory.CreateDirectory(Path.Combine(fixture, "steklo_left_black"));
            File.WriteAllText(Path.Combine(fixture, "steklo_left_black", "steklo_left_black.xml"), "<properties/>");
            Directory.CreateDirectory(Path.Combine(fixture, "steklo_left", "panels"));
            var inherited = XDocument.Parse(Encoding.UTF8.GetString(basePanels.Get("team squad.xml")));
            inherited.Root!.SetAttributeValue("title", "Left fixture panel");
            var leftSource = Path.Combine(fixture, "steklo_left", "panels", "team squad.xml");
            inherited.Save(leftSource);
            var parentBytes = File.ReadAllBytes(leftSource);
            Assert(SkinPanelInstaller.Install(gamePath, fixture, "Zmęczenie sezonowe") == 4);
            foreach (var panel in new[] { "team squad.xml", "tactic person list.xml", "person list table.xml" })
            {
                var installed = XDocument.Load(Path.Combine(fixture, "steklo_left_black", "panels", panel));
                if (panel == "person list table.xml")
                    Assert(installed.Descendants("list").Single(e => (string?)e.Attribute("id") == "column_display_properties")
                        .Elements("record").Elements("flags").Count(e =>
                        (string?)e.Attribute("id") == "id" && (string?)e.Attribute("value") == "Fjad") == 1);
                else Assert(installed.Descendants("record").Count(e => (string?)e.Attribute("id") == SkinPanelInstaller.EditViewId) == 1);
                if (panel == "team squad.xml") Assert((string?)installed.Root!.Attribute("title") == "Left fixture panel");
            }
            Assert(File.ReadAllBytes(leftSource).SequenceEqual(parentBytes));
            Assert(SkinPanelInstaller.Install(gamePath, fixture, "Zmęczenie sezonowe") == 0);
            File.Delete(Path.Combine(fixture, "steklo_black", "steklo_black.xml"));
            Assert(SkinPanelInstaller.Install(gamePath, fixture, "Zmęczenie sezonowe") == 0);
        }
        finally { Directory.Delete(fixture, recursive: true); }
        using var form = new MainForm(directory, PanelLocalizer(), _ => [Hd]);
        form.Show();
        var config = Default();
        config.PanelInformationEnabled = true;
        form.Populate(config, [Hd]);
        Assert(form.CaptureConfiguration().PanelInformationEnabled);
        var check = Descendants(form).OfType<CheckBox>().Single(e => e.Name == "PanelInformationEnabled");
        check.Checked = false;
        Assert(!form.CaptureConfiguration().PanelInformationEnabled);
        var tabs = Descendants(form).OfType<TabControl>().Single();
        tabs.SelectTab("SkinGuide");
        var snippets = Descendants(form).OfType<ComboBox>().Single(e => e.Name == "SkinSnippetChoice");
        var code = Descendants(form).OfType<TextBox>().Single(e => e.Name == "SkinSnippet");
        Assert(code.ReadOnly && code.Text.Contains("Fmjd"));
        snippets.SelectedIndex = 1;
        Assert(code.Text.Contains("Fcab") && code.Text.Contains("Fpab"));
        form.ApplyLanguage("pl");
        Assert(code.Text.Contains("Fcab") && snippets.SelectedIndex == 1);
        snippets.SelectedIndex = 2;
        Assert(code.Text.Contains("Fjad") && !code.Text.Contains("Fcab"));
        snippets.SelectedIndex = 3;
        Assert(code.Text.Contains("Fjad") && code.Text.Contains("Fcab") && code.Text.Contains("column_heading"));
        Assert(Descendants(form).OfType<Button>().Any(e => e.Name == "CopySkinSnippet"));
        foreach (var language in new[] { "en", "pl" })
        {
            form.ApplyLanguage(language);
            var instructions = Descendants(form).OfType<TextBox>().Single(e => e.Name == "SkinInstructions");
            Assert(instructions.Text.Contains("Edycja") && instructions.Text.Contains("steklo_left_black"));
            Assert(instructions.Text.StartsWith(language == "pl" ? "UWAGA: odświeżanie widoku."
                : "NOTE: refreshing the view.", StringComparison.Ordinal));
        }
        form.Close();
        Console.WriteLine("PASS: native FMF resources, idempotent Edycja views, Steklo Black/Left installation,"
            + " left-parent precedence, left-only support, backups, module opt-out and both guide languages.");
    }

    private static void TestPanelsNative(string directory, string gamePath)
    {
        using var verified = MatchRulePatch.OpenVerifiedGame(gamePath);
        var integerVtable = new byte[0x70];
        verified.Position = GamePanelPatch.IntegerVtable - 0x400000;
        verified.ReadExactly(integerVtable);
        foreach (var (site, original) in new[]
        {
            (GamePanelPatch.PropertyAddress, GamePanelPatch.PropertyOriginal.ToArray()),
            (GamePanelPatch.TitleAddress, GamePanelPatch.TitleOriginal.ToArray()),
            (GamePanelPatch.TrainingAddress, GamePanelPatch.TrainingOriginal.ToArray()),
            (GamePanelPatch.LabelAddress, GamePanelPatch.LabelOriginal.ToArray())
        })
        {
            verified.Position = site - 0x400000;
            var bytes = new byte[original.Length];
            verified.ReadExactly(bytes);
            Assert(bytes.SequenceEqual(original));
        }
        var localizer = PanelLocalizer();
        foreach (var language in new[] { "en", "pl" })
        {
            localizer.Select(language);
            var localizedPayload = GamePanelPatch.Build(0x10000000, 0x11000000, integerVtable, localizer);
            Assert(localizedPayload.Data.Length <= GamePanelPatch.DataCapacity);
            for (var penalty = 0; penalty <= 40; penalty++)
            {
                var hint = localizer.Text("PanelFatigueHint", penalty);
                Assert(hint.Contains(penalty + "%") && !hint.Contains("{0}"));
                Assert(hint.Split("\r\n").Length == 5 && hint.Contains("100%"));
                for (var level = 0; level < 5; level++)
                    Assert(hint.Contains(localizer.Text("PanelFatigue" + level)));
                Assert(localizedPayload.Data.AsSpan().IndexOf(Encoding.Unicode.GetBytes(hint + "\0")) >= 0);
            }
        }
        var payload = GamePanelPatch.Build(0x10000000, 0x11000000, integerVtable, PanelLocalizer());
        var path = Path.Combine(directory, "panels-payload.bin");
        using (var writer = new BinaryWriter(File.Create(path)))
        {
            writer.Write(payload.Code.Length);
            writer.Write(payload.Code);
            writer.Write(payload.Data.Length);
            writer.Write(payload.Data);
            writer.Write(payload.PropertyEntry);
            writer.Write(payload.TitleEntry);
            writer.Write(payload.TrainingEntry);
            writer.Write(payload.LabelEntry);
            writer.Write(payload.ReadEntry);
            writer.Write(payload.FormatEntry);
            foreach (var type in payload.Types) writer.Write(type);
        }
        NativePanelFixture.TestPanels(gamePath, path);
    }

    private static void TestPanelsSuspended(string gamePath)
    {
        var originalHash = GameFileHash(gamePath);
        using var verified = MatchRulePatch.OpenVerifiedGame(gamePath);
        using (var game = new SuspendedGameProcess(gamePath))
        {
            Assert(game.Read(GamePanelPatch.PropertyAddress, GamePanelPatch.PropertyOriginal.Length)
                .AsSpan().SequenceEqual(GamePanelPatch.PropertyOriginal));
            var pa = game.Read(GamePaPatch.HookAddress, GamePaPatch.OriginalEntry.Length);
            var state = game.ApplyPanelInformation(verified, PanelLocalizer());
            Assert(game.Read(state, GamePanelPatch.StateSize).All(b => b == 0));
            foreach (var address in new[] { GamePanelPatch.PropertyAddress, GamePanelPatch.TitleAddress,
                GamePanelPatch.TrainingAddress, GamePanelPatch.LabelAddress })
            {
                var hook = game.Read(address, 5);
                Assert(hook[0] == 0xE9);
                var target = unchecked(address + 5 + BinaryPrimitives.ReadUInt32LittleEndian(hook.AsSpan(1)));
                Assert(target != 0 && game.Read(target, 1).Length == 1);
            }
            Assert(game.Read(GamePaPatch.HookAddress, pa.Length).SequenceEqual(pa));
            Assert(game.Read(0x00A7665D, 2).SequenceEqual(new byte[] { 0x6A, 1 }));
            var config = Default();
            config.Rules[0].Override = true;
            config.Rules[0].Substitutions = 7;
            game.ApplyRuleLimits(config.Rules, verified);
            game.ApplyPaGrowth(50, verified);
            var display = new DisplayLaunchSettings(DisplayMode.Window, new Resolution(1280, 720), new Rectangle(0, 0, 1920, 1080))
            {
                WorkArea = new Rectangle(0, 0, 1920, 1040)
            };
            game.ApplyDisplay(display, verified);
        }
        verified.Position = 0;
        Assert(Convert.ToHexString(SHA256.HashData(verified)) == originalHash);
        Console.WriteLine("PASS: all panel hooks installed/read back in suspended FM08 alongside match rules,"
            + " display and PA; process never resumed; original Pjad and EXE unchanged.");
    }
}
