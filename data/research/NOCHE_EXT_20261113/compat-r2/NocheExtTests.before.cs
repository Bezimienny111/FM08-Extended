using System.Security.Cryptography;
using System.Text.Json;
using System.Xml.Linq;
using FmLauncher;

namespace FmLauncher.Tests;

internal static partial class Program
{
    // Disk/XML fixture only. No game process is started, attached to, suspended or patched.
    private static void TestNocheExt(string gamePath, string actualSkins, string output)
    {
        Assert(!Directory.Exists(output));
        Directory.CreateDirectory(output);
        var game = Path.Combine(output, "private-game");
        Directory.CreateDirectory(game);
        var exe = Path.Combine(game, "NocheSkinFixture.exe");
        File.WriteAllBytes(exe, [0x4D, 0x5A]);
        foreach (var relative in new[] { "data/panels.fmf", "data/skins.fmf", "data/updates/update-802/data/panels.fmf" })
        {
            var target = Path.Combine(game, relative);
            Directory.CreateDirectory(Path.GetDirectoryName(target)!);
            File.Copy(Path.Combine(Path.GetDirectoryName(gamePath)!, relative), target);
        }
        string Hash(string path) => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path)));
        Dictionary<string,string> Snapshot(string root, string pattern = "*") => Directory.EnumerateFiles(root, pattern, SearchOption.AllDirectories)
            .ToDictionary(path => Path.GetRelativePath(root, path), Hash);
        void Same(string root, Dictionary<string,string> before, string pattern = "*")
        {
            var after = Snapshot(root, pattern);
            Assert(before.Count == after.Count && before.All(p => after.GetValueOrDefault(p.Key) == p.Value));
        }
        void CloneXml(string source, string target)
        {
            foreach (var file in Directory.EnumerateFiles(source, "*.xml", SearchOption.AllDirectories))
            {
                var to = Path.Combine(target, Path.GetRelativePath(source, file));
                Directory.CreateDirectory(Path.GetDirectoryName(to)!); File.Copy(file, to);
            }
        }
        var live = Snapshot(actualSkins);
        var skins = Path.Combine(output, "noche-only", "skins");
        CloneXml(Path.Combine(actualSkins, "noche"), Path.Combine(skins, "noche"));
        var original = Snapshot(Path.Combine(skins, "noche"));
        var ui = PanelLocalizer(); ui.Select("en");
        var options = new PlayerProfilePanelOptions(true, true);
        Assert(ExtSkinCatalog.All.Count == 5 && SkinPanelInstaller.ExtSkins.Contains("NocheExt"));
        Assert(SkinPanelInstaller.InstallExt(exe, skins, "Zmęczenie sezonowe", options, PanelLocalizer()) == 6);
        var descriptor = Path.Combine(skins, "NocheExt", "NocheExt.xml");
        var xml = XDocument.Load(descriptor);
        Assert(xml.Root!.Elements().Single(e => (string?)e.Attribute("id") == "name").Attribute("value")!.Value == "NocheExt");
        Assert(xml.Root.Elements().Single(e => (string?)e.Attribute("id") == "parent").Attribute("value")!.Value == "noche");
        var resolver = new SkinResourceResolver(exe, skins);
        Assert(resolver.Chain("NocheExt").SequenceEqual(new[] { "NocheExt", "noche" }));
        Assert(resolver.Get("NocheExt", "player profile personal details.xml").SequenceEqual(
            File.ReadAllBytes(Path.Combine(skins, "noche", "panels", "player profile personal details.xml"))));
        void Profile(string root, PlayerProfilePanelOptions expected, Localizer locale)
        {
            var profile = XDocument.Load(Path.Combine(root, "NocheExt", "panels", "player profile.xml"));
            Assert(profile.Descendants("widget").Count(e => (string?)e.Attribute("id") == "Fpos") == (expected.PositionHighlightsEnabled ? 1 : 0));
            foreach (var field in PlayerProfileFields.Hidden)
                Assert(profile.Descendants("widget").Count(e => (string?)e.Attribute("id") == field.Id) == (expected.HiddenAttributesEnabled ? 1 : 0));
            foreach (var name in new[] { "technical", "mental", "physical" })
                Assert(profile.Descendants("container").Count(e => (string?)e.Attribute("file") == "player profile " + name + " attributes") == 1);
            if (expected.PositionHighlightsEnabled)
            {
                var popup = profile.Descendants("widget").Single(e => (string?)e.Attribute("id") == "Fpos");
                Assert(popup.Descendants("record").Count(e => ((string?)e.Attribute("id"))?.StartsWith("Fp", StringComparison.Ordinal) == true) == 12);
                for (var i = 0; i < 11; i++)
                    Assert(PanelXmlText(popup.Descendants("record").Single(e => (string?)e.Attribute("id") == PlayerProfileXml.RoleItemId(i)), "name") == PositionHighlightModel.Roles[i].Name(locale.Code));
            }
            if (expected.HiddenAttributesEnabled)
            {
                var hidden = profile.Descendants("container").Single(e => (string?)e.Attribute("id") == "Fhid");
                foreach (var field in PlayerProfileFields.Hidden)
                    Assert(hidden.Descendants("widget").Count(e => PanelXmlText(e, "text") == (locale.Code == "pl" ? field.Polish : field.English)) == 1);
            }
            var training = XDocument.Load(Path.Combine(root, "NocheExt", "panels", "player training.xml"));
            Assert(training.Descendants("widget").Count(e => (string?)e.Attribute("id") == "Fmjd") == 1);
            var registry = XDocument.Load(Path.Combine(root, "NocheExt", "panels", "person list table.xml"));
            foreach (var id in new[] { "Fjad", "Fcab", "Fpab" })
                Assert(registry.Descendants("record").Count(e => e.Elements("flags").Any(f => (string?)f.Attribute("id") == "id" && (string?)f.Attribute("value") == id)) == 1);
            SkinPanelInstaller.ValidateProfileReadiness(root, expected);
        }
        var pl = PanelLocalizer(); pl.Select("pl");
        Profile(skins, options, pl);
        Assert(SkinPanelInstaller.InstallExt(exe, skins, pl.Text("PanelFatigueTitle"), options, pl) == 0);
        foreach (var (positions, hidden) in new[] { (true,false), (false,true), (false,false), (true,true) })
        {
            var requested = new PlayerProfilePanelOptions(positions, hidden);
            SkinPanelInstaller.InstallExt(exe, skins, pl.Text("PanelFatigueTitle"), requested, pl);
            Profile(skins, requested, pl);
            Assert(SkinPanelInstaller.InstallExt(exe, skins, pl.Text("PanelFatigueTitle"), requested, pl) == 0);
        }
        var preference = Path.Combine(output, "private-current_language.xml");
        foreach (var (native, code) in new[] { ("english","en"), ("polish","pl"), ("german","en"), ("polish","pl") })
        {
            File.WriteAllText(preference, "<record><string id='valu' value='" + native + "'/></record>");
            var locale = GameLanguageResolver.CreatePanelLocalizer(ui, preference);
            Assert(locale.Code == code && ui.Code == "en");
            SkinPanelInstaller.EnsurePanelLanguage(exe, skins, options, locale);
            Profile(skins, options, locale);
            Assert(SkinPanelInstaller.EnsurePanelLanguage(exe, skins, options, locale) == 0);
        }
        var profilePath = Path.Combine(skins, "NocheExt", "panels", "player profile.xml");
        var saved = File.ReadAllBytes(profilePath);
        File.AppendAllText(profilePath, "\n<!-- preserve user change -->\n");
        var edited = Snapshot(skins);
        try { SkinPanelInstaller.InstallExt(exe, skins, pl.Text("PanelFatigueTitle"), options, pl); throw new InvalidOperationException("User edit accepted"); }
        catch (LauncherException e) { Assert(e.Key == "SkinInstallError"); }
        Same(skins, edited);
        try { SkinPanelInstaller.Uninstall(exe, skins); throw new InvalidOperationException("Edited Undo accepted"); }
        catch (LauncherException e) { Assert(e.Key == "SkinInstallError"); }
        Same(skins, edited); File.WriteAllBytes(profilePath, saved);
        var guarded = Snapshot(skins);
        try { SkinPanelInstaller.InstallExt(Environment.ProcessPath!, skins, pl.Text("PanelFatigueTitle"), options, pl); throw new InvalidOperationException("Running process accepted"); }
        catch (LauncherException e) { Assert(e.Key == "AlreadyRunning"); }
        Same(skins, guarded);
        Assert(SkinPanelInstaller.Uninstall(exe, skins) == 6 && !File.Exists(descriptor));
        Assert(SkinPanelInstaller.Uninstall(exe, skins) == 0);
        Same(Path.Combine(skins, "noche"), original);
        // Actual sharing violation after descriptor and first panel commit proves metadata participates in rollback.
        var squad = Path.Combine(skins, "NocheExt", "panels", "team squad.xml");
        Directory.CreateDirectory(Path.GetDirectoryName(squad)!);
        File.WriteAllBytes(squad, resolver.Get("noche", "team squad.xml"));
        var beforeFailure = Snapshot(skins);
        using (var locked = new FileStream(squad, FileMode.Open, FileAccess.Read, FileShare.Read))
        {
            try { SkinPanelInstaller.InstallExt(exe, skins, pl.Text("PanelFatigueTitle"), options, pl); throw new InvalidOperationException("Sharing violation expected"); }
            catch (LauncherException e) { Assert(e.Key == "SkinInstallError"); }
            Same(skins, beforeFailure); Assert(!File.Exists(descriptor));
        }
        File.Delete(squad);
        // Source-parent cycle fails before a child or panel is committed.
        var parentPath = Path.Combine(skins, "noche", "noche.xml");
        var parent = File.ReadAllBytes(parentPath);
        var cycle = XDocument.Load(parentPath);cycle.Root!.Add(new XElement("flags",new XAttribute("id","parent"),new XAttribute("value","NocheExt")));cycle.Save(parentPath);
        var cycleBefore = Snapshot(skins);
        try { SkinPanelInstaller.InstallExt(exe, skins, pl.Text("PanelFatigueTitle"), options, pl); throw new InvalidOperationException("Cycle accepted"); }
        catch (LauncherException e) { Assert(e.Key == "SkinInstallError"); }
        Same(skins, cycleBefore); File.WriteAllBytes(parentPath, parent);
        // Clone the actual four-skin receipt, append Noche without resetting any backup ownership.
        var allData = Path.Combine(output, "private-user");
        var allSkins = Path.Combine(allData, "skins");CloneXml(actualSkins, allSkins);
        var liveReceipt = Path.Combine(Path.GetDirectoryName(actualSkins)!, ".fmext", "player-panels");
        var receiptRoot = Path.Combine(allData, ".fmext", "player-panels");
        if (Directory.Exists(liveReceipt))
        {
            foreach (var file in Directory.EnumerateFiles(liveReceipt, "*", SearchOption.AllDirectories))
            {
                var to=Path.Combine(receiptRoot,Path.GetRelativePath(liveReceipt,file));Directory.CreateDirectory(Path.GetDirectoryName(to)!);File.Copy(file,to);
            }
            var receiptPath=Path.Combine(receiptRoot,"installation.json");
            var old=JsonSerializer.Deserialize<SkinPanelReceipt>(File.ReadAllBytes(receiptPath))!;
            var moved=old with { SkinsRoot=allSkins, Files=old.Files.Select(f=>f with
            {
                Path=Path.Combine(allSkins,Path.GetRelativePath(actualSkins,f.Path)),
                Backup=f.Backup is null?null:Path.Combine(receiptRoot,Path.GetRelativePath(liveReceipt,f.Backup))
            }).ToList()};File.WriteAllBytes(receiptPath,JsonSerializer.SerializeToUtf8Bytes(moved));
        }
        var localeNow=GameLanguageResolver.CreatePanelLocalizer(ui);
        SkinPanelInstaller.InstallExt(exe,allSkins,localeNow.Text("PanelFatigueTitle"),options,localeNow);
        Assert(SkinPanelInstaller.InstallExt(exe,allSkins,localeNow.Text("PanelFatigueTitle"),options,localeNow)==0);
        SkinPanelInstaller.ValidateProfileReadiness(allSkins,options);Profile(allSkins,options,localeNow);
        var installed=JsonSerializer.Deserialize<SkinPanelReceipt>(File.ReadAllBytes(Path.Combine(receiptRoot,"installation.json")))!;
        Assert(installed.Files.Count(f=>Path.GetFileName(f.Path)=="player profile.xml")==5);
        foreach(var f in installed.Files)if(f.Backup is not null)Assert(Hash(f.Backup)==f.BeforeHash);
        var candidate=Path.Combine(output,"candidate-skin","NocheExt");CloneXml(Path.Combine(allSkins,"NocheExt"),candidate);
        Assert(Directory.EnumerateFiles(candidate,"*",SearchOption.AllDirectories).Count()==6);
        var report=new { Status="PASS_NOCHE_EXT_OFFLINE", Skin="NocheExt", Parent="noche", ParentHasImplicitBaseFallback=true,
            ActiveProfiles=5, HiddenFields=12, Roles=11, NativeAttributeContainers=3, PanelLanguage=localeNow.Code,
            Idempotent=true, IndependentOptions=true, PLGameElseEN=true, OriginalNocheUnchanged=true,
            ExistingFourUpgradeBackupsPreserved=true, UserEditsRejected=true, RunningGameGuardPreserved=true,
            ActualPartialWriteMetadataRollback=true, CyclicParentRejected=true, ArtworkCopiedToChild=false,
            ActualFMStarted=false, ActualFMAttached=false, LiveSkinsWritten=false, RuntimeVisualAcceptance="PENDING_AFTER_USER_CLOSES_FM",
            CandidateSkin=candidate, FixtureSkins=allSkins, FixtureGame=exe };
        File.WriteAllText(Path.Combine(output,"offline-result.json"),JsonSerializer.Serialize(report,new JsonSerializerOptions{WriteIndented=true}));
        Same(actualSkins,live);Same(Path.Combine(skins,"noche"),original);
        Console.WriteLine("PASS: NocheExt + four existing profiles; 12 hidden / 11 roles; PL-game else EN; transactions, Undo, guard, metadata rollback and original Noche preserved. No real FM started/attached.");
    }
}
