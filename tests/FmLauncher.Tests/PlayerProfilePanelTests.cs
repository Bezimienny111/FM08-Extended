using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Xml.Linq;
using FmLauncher;

namespace FmLauncher.Tests;

internal static partial class Program
{
    private static void TestProfileHookReadback(string gamePath, bool positions = false)
    {
        var originalHash = GameFileHash(gamePath);
        using var verified = MatchRulePatch.OpenVerifiedGame(gamePath);
        using (var suspended = new SuspendedGameProcess(gamePath))
        {
            var state = suspended.ApplyPanelInformation(verified, PanelLocalizer(),
                new PlayerProfilePanelOptions(positions, true), legacyEnabled: false);
            Assert(suspended.Read(state, GamePanelPatch.StateSize).All(value => value == 0));
            foreach (var (address, expected) in new[]
            {
                (GamePanelPatch.PropertyAddress, GamePanelPatch.PropertyOriginal.ToArray()),
                (GamePanelPatch.TitleAddress, GamePanelPatch.TitleOriginal.ToArray()),
                (GamePanelPatch.TrainingAddress, GamePanelPatch.TrainingOriginal.ToArray()),
                (GamePanelPatch.LabelAddress, GamePanelPatch.LabelOriginal.ToArray()),
                (GamePanelPatch.ProfileSetAddress, GamePanelPatch.ProfileSetOriginal.ToArray()),
                (GamePanelPatch.ProfileEventAddress, GamePanelPatch.ProfileEventOriginal.ToArray()),
                (GamePanelPatch.ProfileInitAddress, GamePanelPatch.ProfileInitOriginal.ToArray())
            })
            {
                verified.Position = address - 0x400000;
                var original = new byte[expected.Length]; verified.ReadExactly(original);
                Assert(original.SequenceEqual(expected));
                var jump = suspended.Read(address, expected.Length);
                Assert(jump[0] == 0xE9);
                var target = unchecked(address + 5 + System.Buffers.Binary.BinaryPrimitives.ReadUInt32LittleEndian(jump.AsSpan(1)));
                Assert(target != 0 && suspended.Read(target, 1).Length == 1);
            }
            if (positions)
            {
                Assert(suspended.PositionBackgroundState != 0);
                var callback = System.Buffers.Binary.BinaryPrimitives.ReadUInt32LittleEndian(
                    suspended.Read(suspended.PositionBackgroundState+(uint)GamePositionBackgroundPatch.RoleSynchronizeOffset,4));
                Assert(callback!=0 && suspended.Read(callback,4).SequenceEqual(new byte[]{0x53,0x55,0x56,0x57}));
                foreach (var (address, expected, opcode) in new[]
                {
                    (GamePositionBackgroundPatch.NumericCreatedAddress,GamePositionBackgroundPatch.NumericCreatedOriginal.ToArray(),0xE8),
                    (GamePositionBackgroundPatch.NameCreatedAddress,GamePositionBackgroundPatch.NameCreatedOriginal.ToArray(),0xE8),
                    (GamePositionBackgroundPatch.DrawAddress,GamePositionBackgroundPatch.DrawOriginal.ToArray(),0xE9),
                    (GamePositionBackgroundPatch.RebuildAddress,GamePositionBackgroundPatch.RebuildOriginal.ToArray(),0xE9),
                    (GamePositionBackgroundPatch.DestructorAddress,GamePositionBackgroundPatch.DestructorOriginal.ToArray(),0xE9),
                    (GamePositionBackgroundPatch.FontCopyAddress,GamePositionBackgroundPatch.FontCopyOriginal.ToArray(),0xE9),
                    (GamePositionBackgroundPatch.PopupCommitAddress,GamePositionBackgroundPatch.PopupCommitOriginal.ToArray(),0xE9)
                })
                {
                    verified.Position=address-0x400000;
                    var original=new byte[expected.Length];verified.ReadExactly(original);
                    Assert(original.SequenceEqual(expected));
                    var installed=suspended.Read(address,expected.Length);Assert(installed[0]==opcode);
                    var target=unchecked(address+5+System.Buffers.Binary.BinaryPrimitives.ReadUInt32LittleEndian(installed.AsSpan(1)));
                    Assert(target!=0 && suspended.Read(target,1).Length==1);
                }
            }
        }
        Assert(GameFileHash(gamePath) == originalHash);
        Console.WriteLine("PASS: all7 profile+existing hooks installed/readback in private suspended fixture; main thread never resumed; original EXE unchanged.");
    }

    private static void TestHiddenPanelsNative(string directory, string gamePath)
    {
        using var verified = MatchRulePatch.OpenVerifiedGame(gamePath);
        var integerVtable = new byte[0x70];
        verified.Position = GamePanelPatch.IntegerVtable - 0x400000;
        verified.ReadExactly(integerVtable);
        foreach (var (enabled, legacy) in new[] { (true, true), (false, true), (true, false) })
        {
            var payload = GamePanelPatch.Build(0x10000000, 0x11000000, integerVtable, PanelLocalizer(),
                new PlayerProfilePanelOptions(false, enabled), legacy);
            var path = Path.Combine(directory, "hidden-" + enabled + "-" + legacy + ".bin");
            using (var writer = new BinaryWriter(File.Create(path)))
            {
                writer.Write(payload.Code.Length); writer.Write(payload.Code);
                writer.Write(payload.Data.Length); writer.Write(payload.Data);
                writer.Write(payload.PropertyEntry); writer.Write(payload.TitleEntry);
                writer.Write(payload.TrainingEntry); writer.Write(payload.LabelEntry);
                writer.Write(payload.ReadEntry); writer.Write(payload.FormatEntry);
                writer.Write(payload.Types.Length);
                foreach (var type in payload.Types) writer.Write(type);
                writer.Write(payload.ProfileSetEntry); writer.Write(payload.ProfileEventEntry);
                writer.Write(payload.ProfileInitEntry); writer.Write(payload.ProfileUpdateEntry);
            }
            NativePanelFixture.TestHiddenPanels(gamePath, path, enabled, legacy);
        }
    }

    private static void TestPlayerProfilePanels(string directory, string gamePath, string output)
    {
        Directory.CreateDirectory(output);
        Assert(PositionHighlightModel.Roles.Count == 11);
        Assert(PositionHighlightModel.Emphasis("DC", "Heading") == AttributeEmphasis.Key);
        Assert(PositionHighlightModel.Emphasis("DC", "Tackling") == AttributeEmphasis.Key);
        Assert(PositionHighlightModel.Emphasis("DC", "Passing") == AttributeEmphasis.Important);
        Assert(PositionHighlightModel.Emphasis("DC", "Finishing") == AttributeEmphasis.Ordinary);
        Assert(PositionHighlightModel.Emphasis("GK", "Reflexes") == AttributeEmphasis.Key);
        Assert(PositionHighlightModel.Emphasis("GK", "Communication") == AttributeEmphasis.Important);
        Assert(PositionHighlightModel.Emphasis("GK", "Finishing") == AttributeEmphasis.Ordinary);
        Assert(PositionHighlightModel.VisibleAttributes.All(value => value is not "CA" and not "Scale"
            and not "Normalization_denominator" and not "Professionalism" and not "Consistency"));
        foreach (var attribute in PositionHighlightModel.VisibleAttributes)
        foreach (var role in PositionHighlightModel.Roles)
        {
            var weight = PositionHighlightModel.AttributeWeights(attribute)[role.Code];
            Assert(PositionHighlightModel.Emphasis(role.Code, attribute) == (weight >= 60
                ? AttributeEmphasis.Key : weight >= 20 ? AttributeEmphasis.Important : AttributeEmphasis.Ordinary));
        }
        var old = JsonSerializer.Serialize(Default(), ConfigurationStore.JsonOptions);
        var json = System.Text.Json.Nodes.JsonNode.Parse(old)!;
        json.AsObject().Remove("PositionHighlightsEnabled");
        json.AsObject().Remove("HiddenAttributesEnabled");
        var previous = JsonSerializer.Deserialize<LauncherConfiguration>(json.ToJsonString(), ConfigurationStore.JsonOptions)!;
        Assert(!previous.PositionHighlightsEnabled && !previous.HiddenAttributesEnabled);
        foreach (var (positions, hidden) in new[] { (false, false), (true, false), (false, true), (true, true) })
        {
            var configuration = Default();
            configuration.PositionHighlightsEnabled = positions;
            configuration.HiddenAttributesEnabled = hidden;
            var roundtrip = JsonSerializer.Deserialize<LauncherConfiguration>(
                JsonSerializer.Serialize(configuration, ConfigurationStore.JsonOptions), ConfigurationStore.JsonOptions)!;
            Assert(roundtrip.PositionHighlightsEnabled == positions && roundtrip.HiddenAttributesEnabled == hidden);
            using var form = new MainForm(directory, PanelLocalizer(), _ => [Hd]);
            form.Populate(configuration, [Hd]);
            Assert(form.CaptureConfiguration().PositionHighlightsEnabled == positions
                && form.CaptureConfiguration().HiddenAttributesEnabled == hidden);
            foreach (var language in new[] { "en", "pl" })
            {
                form.ApplyLanguage(language);
                Assert(form.CaptureConfiguration().PositionHighlightsEnabled == positions
                    && form.CaptureConfiguration().HiddenAttributesEnabled == hidden);
            }
        }
        Console.WriteLine("PASS: all11 role sets, exact60/20 categories, no hidden/normalization fields, old JSON and independent OFF toggles.");

        var actualDirectory = Path.GetDirectoryName(gamePath)!;
        var fixtureGame = Path.Combine(directory, "fixture-game");
        Directory.CreateDirectory(fixtureGame);
        var fixtureExe = Path.Combine(fixtureGame, "SkinPanelFixture.exe");
        File.WriteAllBytes(fixtureExe, [0x4D, 0x5A]);
        foreach (var relative in new[] { "data/panels.fmf", "data/skins.fmf", "data/updates/update-802/data/panels.fmf" })
        {
            var target = Path.Combine(fixtureGame, relative);
            Directory.CreateDirectory(Path.GetDirectoryName(target)!);
            File.Copy(Path.Combine(actualDirectory, relative), target);
        }
        var skins = Path.Combine(directory, "fixture-data", "skins");
        Directory.CreateDirectory(skins);
        var actualSkins = Path.GetFullPath(Path.Combine(actualDirectory, "Dane", "skins"));
        // Actual workspace source chosen explicitly by the fixture caller if the game is installed elsewhere.
        if (!Directory.Exists(Path.Combine(actualSkins, "steklo_black_ext_left")))
            actualSkins = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory,
                "../../../../../../../../Dane/skins"));
        var installedReceiptPath = Path.Combine(Path.GetDirectoryName(actualSkins)!, ".fmext", "player-panels", "installation.json");
        var installedReceipt = File.Exists(installedReceiptPath)
            ? JsonSerializer.Deserialize<SkinPanelReceipt>(File.ReadAllBytes(installedReceiptPath)) : null;
        var owned = installedReceipt?.Files.ToDictionary(file => Path.GetFullPath(file.Path), StringComparer.OrdinalIgnoreCase)
            ?? new Dictionary<string, SkinPanelFileReceipt>(StringComparer.OrdinalIgnoreCase);
        void CopyXmlSkin(string name)
        {
            foreach (var source in Directory.EnumerateFiles(Path.Combine(actualSkins, name), "*.xml", SearchOption.AllDirectories))
            {
                var target = Path.Combine(skins, name, Path.GetRelativePath(Path.Combine(actualSkins, name), source));
                var cleanSource = source;
                // This is a clean-install fixture, not a receipt-upgrade fixture. Reconstruct
                // only owned files from validated originals; never import a managed block
                // without its receipt or relax the production unmanaged-block guard.
                if (owned.TryGetValue(Path.GetFullPath(source), out var receiptFile))
                {
                    Assert(Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(source))) == receiptFile.AfterHash);
                    if (receiptFile.BeforeHash is null) continue;
                    Assert(receiptFile.Backup is not null && Convert.ToHexString(
                        SHA256.HashData(File.ReadAllBytes(receiptFile.Backup))) == receiptFile.BeforeHash);
                    cleanSource = receiptFile.Backup!;
                }
                Directory.CreateDirectory(Path.GetDirectoryName(target)!);
                File.Copy(cleanSource, target);
            }
        }
        foreach (var name in new[] { "fm2008", "steklo", "steklo_black", "steklo_left", "steklo_left_black" }) CopyXmlSkin(name);
        CopyXmlSkin("steklo_black_ext_left");
        var protectedSources = Directory.EnumerateFiles(skins, "*.xml", SearchOption.AllDirectories)
            .Where(path => !path.Contains("steklo_black_ext_left", StringComparison.Ordinal))
            .ToDictionary(path => path, File.ReadAllBytes);
        var localizer = PanelLocalizer();
        var both = new PlayerProfilePanelOptions(false, true);
        try { SkinPanelInstaller.ValidateProfileReadiness(skins, both); throw new InvalidOperationException("Missing installation accepted."); }
        catch (LauncherException error) { Assert(error.Key == "SkinProfileNotReady"); }
        SkinPanelInstaller.InstallExt(fixtureExe, skins, "Zmęczenie sezonowe", both, localizer);
        SkinPanelInstaller.ValidateProfileReadiness(skins, both);
        var profile = Path.Combine(skins, "steklo_black_ext_left", "panels", "player profile.xml");
        var transformed = XDocument.Load(profile);
        Assert(transformed.Descendants("widget").Count(value => (string?)value.Attribute("id") == "Fpos") == 0);
        Assert(transformed.Descendants("container").Count(value => (string?)value.Attribute("id") == "Fhid") == 1);
        foreach (var panel in new[] { "technical", "mental", "physical" })
            Assert(transformed.Descendants("container").Count(value =>
                (string?)value.Attribute("file") == "player profile " + panel + " attributes") == 1);
        foreach (var field in PlayerProfileFields.Hidden)
            Assert(transformed.Descendants("widget").Count(value => (string?)value.Attribute("id") == field.Id) == 1);
        Assert(SkinPanelInstaller.InstallExt(fixtureExe, skins, "Zmęczenie sezonowe", both, localizer) == 0);
        var prototype = Path.Combine(output, "prototype", "steklo_black_ext_left", "player profile.xml");
        Directory.CreateDirectory(Path.GetDirectoryName(prototype)!);
        File.Copy(profile, prototype);
        foreach (var (path, bytes) in protectedSources) Assert(File.ReadAllBytes(path).SequenceEqual(bytes));
        Console.WriteLine("PASS: Steklo Ext Left prototype, real inherited XML, unique native attribute containers and idempotent install.");

        var legacyExt = ExtSkinCatalog.All.Where(value => !value.CreateWhenParentPresent)
            .Select(value => value.DirectoryName).ToArray();
        Assert(legacyExt.Length == 4); // Keep the original four-skin regression independent of optional Noche.
        foreach (var name in legacyExt.Where(value => value != "steklo_black_ext_left")) CopyXmlSkin(name);
        SkinPanelInstaller.InstallExt(fixtureExe, skins, "Zmęczenie sezonowe", both, localizer);
        Assert(SkinPanelInstaller.InstallExt(fixtureExe, skins, "Zmęczenie sezonowe", both, localizer) == 0);
        foreach (var skin in legacyExt)
        {
            var target = Path.Combine(skins, skin, "panels", "player profile.xml");
            XDocument.Load(target);
            var copy = Path.Combine(output, "four-ext", skin, "player profile.xml");
            Directory.CreateDirectory(Path.GetDirectoryName(copy)!);
            File.Copy(target, copy);
        }
        var edited = File.ReadAllBytes(profile);
        File.AppendAllText(profile, "\n<!-- user edit must survive -->\n");
        var changed = File.ReadAllBytes(profile);
        try { SkinPanelInstaller.Uninstall(fixtureExe, skins); throw new InvalidOperationException("Uninstall accepted user edits."); }
        catch (LauncherException error) { Assert(error.Key == "SkinInstallError"); }
        Assert(File.ReadAllBytes(profile).SequenceEqual(changed));
        File.WriteAllBytes(profile, edited);
        Assert(SkinPanelInstaller.Uninstall(fixtureExe, skins) >= 20);
        Assert(SkinPanelInstaller.Uninstall(fixtureExe, skins) == 0);
        foreach (var (path, bytes) in protectedSources) Assert(File.ReadAllBytes(path).SequenceEqual(bytes));
        try
        {
            SkinPanelInstaller.InstallExt(Environment.ProcessPath!, skins, "Zmęczenie sezonowe", both, localizer);
            throw new InvalidOperationException("Installer accepted a running same-name process.");
        }
        catch (LauncherException error) { Assert(error.Key == "AlreadyRunning"); }

        // A real Windows sharing violation on the second target forces a partial-write
        // rollback; it does not mirror the serializer or mock the production file writes.
        var firstTraining = Path.Combine(skins, "fm2008_ext_left", "panels", "player training.xml");
        var lockedSquad = Path.Combine(skins, "fm2008_ext_left", "panels", "team squad.xml");
        var trainingXml = XDocument.Load(firstTraining);
        trainingXml.Descendants("widget").Where(value => (string?)value.Attribute("id") == "Fmjd").Remove();
        trainingXml.Save(firstTraining);
        var squadXml = XDocument.Load(lockedSquad);
        squadXml.Descendants("record").Where(value => (string?)value.Attribute("id") == SkinPanelInstaller.EditViewId).Remove();
        squadXml.Save(lockedSquad);
        Dictionary<string, byte[]> Snapshot() => Directory.EnumerateFiles(skins, "*.xml", SearchOption.AllDirectories)
            .ToDictionary(path => path, File.ReadAllBytes);
        void Same(Dictionary<string, byte[]> snapshot)
        {
            var now = Snapshot();
            Assert(now.Keys.Order().SequenceEqual(snapshot.Keys.Order()));
            foreach (var (path, bytes) in snapshot) Assert(now[path].SequenceEqual(bytes));
        }
        var beforeFailure = Snapshot();
        using (var fileLock = new FileStream(lockedSquad, FileMode.Open, FileAccess.Read, FileShare.Read))
        {
            try
            {
                SkinPanelInstaller.InstallExt(fixtureExe, skins, "Zmęczenie sezonowe", both, localizer);
                throw new InvalidOperationException("Expected actual sharing violation.");
            }
            catch (LauncherException error) { Assert(error.Key == "SkinInstallError"); }
            Same(beforeFailure);
        }
        SkinPanelInstaller.InstallExt(fixtureExe, skins, "Zmęczenie sezonowe", both, localizer);
        var beforeUndoFailure = Snapshot();
        using (var fileLock = new FileStream(lockedSquad, FileMode.Open, FileAccess.Read, FileShare.Read))
        {
            try { SkinPanelInstaller.Uninstall(fixtureExe, skins); throw new InvalidOperationException("Expected undo sharing violation."); }
            catch (LauncherException error) { Assert(error.Key == "SkinInstallError"); }
            Same(beforeUndoFailure);
        }
        SkinPanelInstaller.Uninstall(fixtureExe, skins);
        Same(beforeFailure);
        Console.WriteLine("PASS: readiness, running-process guard, real partial-write rollback and failed-Undo rollback/readback.");
        Console.WriteLine("PASS: all4Ext only, update/idempotency, safe Undo, user-edit conflict and original-parent preservation.");
    }
}
