using System.Diagnostics;
using System.Security.Cryptography;
using System.Text.Json;
using System.Xml.Linq;

namespace FmLauncher;

internal sealed record SkinPanelFileReceipt(string Path, string? BeforeHash, string? Backup, string AfterHash);
internal sealed record SkinPanelReceipt(int Schema, string Status, string SkinsRoot,
    bool PositionHighlights, bool HiddenAttributes, List<SkinPanelFileReceipt> Files, string ModuleVersion = "0.1.3",
    string? PanelLanguage = null);

internal static partial class SkinPanelInstaller
{
    internal static IReadOnlyList<string> ExtSkins { get; } =
        ExtSkinCatalog.All.Select(skin => skin.DirectoryName).ToArray();
    private static readonly string[] ExtendedPanelNames =
        ["player training.xml", "team squad.xml", "tactic person list.xml", "person list table.xml", "player profile.xml",
            "match team stats short.xml","global panels.xml"];
    private static readonly JsonSerializerOptions ReceiptJson = new() { WriteIndented = true };
    private static string Digest(byte[] bytes) => Convert.ToHexString(SHA256.HashData(bytes));
    private static string? FileDigest(string path) => File.Exists(path) ? Digest(File.ReadAllBytes(path)) : null;
    private static string ReceiptRoot(string skinsPath, bool noche = false) => Path.Combine(
        Path.GetDirectoryName(Path.GetFullPath(skinsPath))!, ".fmext", noche ? "player-panels-noche" : "player-panels");
    private static string ReceiptPath(string skinsPath, bool noche = false) => Path.Combine(ReceiptRoot(skinsPath, noche), "installation.json");
    private static bool IsNoche(string skinsPath, string path) => Path.GetFullPath(path).StartsWith(
        Path.GetFullPath(Path.Combine(skinsPath, "NocheExt")) + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase);

    internal static int InstallExt(string gamePath, string skinsPath, string fatigueTitle,
        PlayerProfilePanelOptions options, Localizer localizer)
    {
        options.Validate();
        if (options.PositionHighlightsEnabled && !PositionHighlightModel.IntegrationReady)
            throw new LauncherException("PositionHighlightsUnavailable");
        return WithStoppedGame(gamePath, () =>
        {
            using var verified=MatchRulePatch.OpenVerifiedGame(gamePath);
            return InstallExtStopped(gamePath,skinsPath,fatigueTitle,options,localizer);
        });
    }

    // Launch is strictly read-only. Only Skins > Basic may update installed XML.
    internal static void ValidatePanelLanguage(string skinsPath, Localizer panelLocalizer)
    {
        try
        {
            var previous=ReadReceipt(skinsPath);
            if(previous is not { Status: "installed" } || previous.Files.Count==0)
                throw new InvalidDataException("No installed Ext panel receipt.");
            foreach(var file in previous.Files)
                if(FileDigest(file.Path)!=file.AfterHash)
                    throw new InvalidDataException("Installed panel changed after installation.");
            if(previous.PanelLanguage!=panelLocalizer.Code)
                throw new InvalidDataException("Installed panel language differs from the game language.");
        }
        catch(Exception error) when(error is IOException or UnauthorizedAccessException or System.Text.Json.JsonException
            or InvalidDataException or ArgumentException)
        {
            throw new LauncherException("SkinPanelsNotReady",skinsPath,error.Message);
        }
    }

    internal static void ValidateProfileReadiness(string skinsPath, PlayerProfilePanelOptions options)
    {
        if (!options.HiddenAttributesEnabled && !options.PositionHighlightsEnabled) return;
        try
        {
            var receipt = ReadReceipt(skinsPath);
            if (receipt is not { Status: "installed" } || options.HiddenAttributesEnabled && !receipt.HiddenAttributes
                || options.PositionHighlightsEnabled && !receipt.PositionHighlights)
                throw new InvalidDataException("No installed hidden profile receipt.");
            foreach (var file in receipt.Files)
                if (FileDigest(file.Path) != file.AfterHash)
                    throw new InvalidDataException("Installed panel changed after installation.");
            var profiles = receipt.Files.Where(file => Path.GetFileName(file.Path) == "player profile.xml").ToArray();
            if (profiles.Length == 0) throw new InvalidDataException("No supported Ext profile installed.");
            foreach (var profile in profiles)
            {
                var xml = XDocument.Load(profile.Path);
                if (options.HiddenAttributesEnabled)
                    foreach (var field in PlayerProfileFields.Hidden)
                        if (xml.Descendants("widget").Count(value => (string?)value.Attribute("id") == field.Id) != 1)
                            throw new InvalidDataException("Installed hidden profile version differs.");
                if (options.PositionHighlightsEnabled && xml.Descendants("widget").Count(
                    value => (string?)value.Attribute("id") == PlayerProfileXml.RoleWidgetId
                        && (string?)value.Attribute("selection") == PlayerProfileXml.NoRoleId) != 1)
                    throw new InvalidDataException("Installed position selector version differs.");
            }
        }
        catch (Exception error) when (error is IOException or UnauthorizedAccessException
            or System.Xml.XmlException or InvalidDataException or JsonException or ArgumentException)
        {
            throw new LauncherException("SkinProfileNotReady", skinsPath, error.Message);
        }
    }

    internal static int Uninstall(string gamePath, string skinsPath) =>
        throw new LauncherException("SkinRemovalDisabled");

    private static int WithStoppedGame(string gamePath, Func<int> operation)
    {
        if (!Path.IsPathFullyQualified(gamePath) || !File.Exists(gamePath))
            throw new LauncherException("InvalidGamePath", gamePath);
        using var launchLock = new Mutex(false, @"Local\FmLauncher.GameStart");
        bool acquired;
        try { acquired = launchLock.WaitOne(0); }
        catch (AbandonedMutexException) { acquired = true; }
        if (!acquired) throw new LauncherException("AlreadyRunning");
        try
        {
            EnsureGameStopped(gamePath);
            return operation();
        }
        catch (LauncherException) { throw; }
        catch (Exception error) when (error is IOException or UnauthorizedAccessException
            or System.Xml.XmlException or InvalidDataException or OverflowException or ArgumentException or JsonException)
        {
            throw new LauncherException("SkinInstallError", error.Message);
        }
        finally { launchLock.ReleaseMutex(); }
    }

    private static void EnsureGameStopped(string gamePath)
    {
        var candidates = Process.GetProcessesByName(Path.GetFileNameWithoutExtension(gamePath));
        try
        {
            if (candidates.Any(candidate => !candidate.HasExited)) throw new LauncherException("AlreadyRunning");
        }
        finally { foreach (var candidate in candidates) candidate.Dispose(); }
    }

    private static List<(bool Noche, SkinPanelReceipt Receipt)> ReadReceiptParts(string skinsPath)
    {
        var parts = new List<(bool, SkinPanelReceipt)>();
        // Noche support withdrawn in R13. Its separate receipts are intentionally left unread.
        foreach (var noche in new[] { false })
        {
            var path = ReceiptPath(skinsPath, noche);
            if (!File.Exists(path)) continue;
            var receipt = JsonSerializer.Deserialize<SkinPanelReceipt>(File.ReadAllBytes(path), ReceiptJson)
                ?? throw new InvalidDataException("Invalid skin installation receipt.");
            if (receipt.Schema != 2 || receipt.Status is not ("installed" or "uninstalled") || !Path.GetFullPath(receipt.SkinsRoot).Equals(
                Path.GetFullPath(skinsPath), StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Skin installation receipt scope differs.");
            foreach (var file in receipt.Files)
            {
                ValidateDestination(skinsPath, file.Path);
                if (IsNoche(skinsPath, file.Path) != noche)
                    throw new InvalidDataException("Skin receipt crosses legacy/Noche ownership scopes.");
                if (file.Backup is not null && !Path.GetFullPath(file.Backup).StartsWith(
                    ReceiptRoot(skinsPath, noche) + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase))
                    throw new InvalidDataException("Skin backup is outside its receipt root.");
            }
            receipt = receipt with { Files = receipt.Files.Select(file => file with
            {
                Path = Path.GetFullPath(file.Path), Backup = file.Backup is null ? null : Path.GetFullPath(file.Backup)
            }).ToList() };
            if (receipt.Files.Select(file => file.Path).Distinct(StringComparer.OrdinalIgnoreCase).Count() != receipt.Files.Count)
                throw new InvalidDataException("Duplicate skin receipt target.");
            parts.Add((noche, receipt));
        }
        return parts;
    }

    private static SkinPanelReceipt? ReadReceipt(string skinsPath)
    {
        var parts = ReadReceiptParts(skinsPath);
        var installed = parts.Where(part => part.Receipt.Status == "installed").Select(part => part.Receipt).ToArray();
        if (installed.Length == 0) return parts.Count == 0 ? null : parts[0].Receipt with { Status = "uninstalled", Files = [] };
        var files = installed.SelectMany(part => part.Files).ToList();
        if (files.Select(file => file.Path).Distinct(StringComparer.OrdinalIgnoreCase).Count() != files.Count)
            throw new InvalidDataException("Duplicate skin target across receipts.");
        var languages = installed.Select(part => part.PanelLanguage).Distinct(StringComparer.Ordinal).ToArray();
        return new SkinPanelReceipt(2, "installed", Path.GetFullPath(skinsPath),
            installed.All(part => part.PositionHighlights), installed.All(part => part.HiddenAttributes), files,
            PanelLanguage: languages.Length == 1 ? languages[0] : null);
    }

    private static void ValidateDestination(string skinsPath, string path)
    {
        var full = Path.GetFullPath(path);
        var permitted = ExtSkins.Any(skin => ExtendedPanelNames.Any(panel =>
            full.Equals(Path.GetFullPath(Path.Combine(skinsPath, skin, "panels", panel)),
                StringComparison.OrdinalIgnoreCase)));
        permitted |= ExtSkinCatalog.All.Any(skin => skin.CreateWhenParentPresent && full.Equals(
            Path.GetFullPath(Path.Combine(skinsPath, skin.DirectoryName, skin.DirectoryName + ".xml")),
            StringComparison.OrdinalIgnoreCase));
        if (!permitted) throw new InvalidDataException("Skin write outside catalogued Ext scopes.");
        for (var directory = new DirectoryInfo(Path.GetDirectoryName(full)!);
            directory is not null && directory.FullName.StartsWith(Path.GetFullPath(skinsPath), StringComparison.OrdinalIgnoreCase);
            directory = directory.Parent)
            if (directory.Exists && (directory.Attributes & FileAttributes.ReparsePoint) != 0)
                throw new InvalidDataException("Linked Ext panel destinations are not supported.");

    }

    private static byte[] ReadClean(string destination, SkinPanelFileReceipt? previous, Func<byte[]> inherited)
    {
        if (previous is null) return File.Exists(destination) ? File.ReadAllBytes(destination) : inherited();
        if (FileDigest(destination) != previous.AfterHash)
            throw new InvalidDataException("Skin panel changed since installation; preserve user edits: " + destination);
        if (previous.BeforeHash is null) return inherited();
        if (previous.Backup is null || !File.Exists(previous.Backup)
            || FileDigest(previous.Backup) != previous.BeforeHash)
            throw new InvalidDataException("Missing or changed original skin backup.");
        return File.ReadAllBytes(previous.Backup);
    }

    private static int InstallExtStopped(string gamePath, string skinsPath, string fatigueTitle,
        PlayerProfilePanelOptions options, Localizer localizer,
        IReadOnlyDictionary<string, PlayerProfilePanelOptions>? perSkinOptions = null)
    {
        if (!Path.IsPathFullyQualified(skinsPath))
            throw new LauncherException("SkinDirectoryMissing", skinsPath);
        var sourceResolver=new SkinResourceResolver(gamePath,skinsPath);
        var active = ExtSkinCatalog.All.Where(skin =>
            sourceResolver.HasMetadata(skin.DirectoryName)
            || skin.CreateWhenParentPresent && sourceResolver.HasMetadata(skin.Parent!))
            .ToArray();
        if (active.Length == 0) throw new LauncherException("SkinExtMissing", skinsPath);
        var previous = ReadReceipt(skinsPath);
        if (previous is { Status: "uninstalled" }) previous = null;
        var prior = previous?.Files.ToDictionary(value => value.Path, StringComparer.OrdinalIgnoreCase)
            ?? new Dictionary<string, SkinPanelFileReceipt>(StringComparer.OrdinalIgnoreCase);
        var pendingMetadata = active.Where(skin => skin.CreateWhenParentPresent && !File.Exists(
            Path.Combine(skinsPath, skin.DirectoryName, skin.DirectoryName + ".xml")))
            .ToDictionary(skin => skin.DirectoryName, skin => skin.Descriptor(sourceResolver.Metadata(skin.Parent!)), StringComparer.OrdinalIgnoreCase);
        var resolver = new SkinResourceResolver(gamePath, skinsPath, pendingMetadata);
        var knownFatigueTitles = localizer.Languages.Select(language => language.Texts.GetValueOrDefault("PanelFatigueTitle"))
            .Where(title => title is not null).Cast<string>().Append(fatigueTitle).Distinct(StringComparer.Ordinal).ToArray();
        var planned = new Dictionary<string, byte[]>(StringComparer.OrdinalIgnoreCase);
        var rollbackDefaults=new Dictionary<string,byte[]>(StringComparer.OrdinalIgnoreCase);
        foreach (var definition in active)
        {
            var skin = definition.DirectoryName;
            var skinOptions = perSkinOptions?.GetValueOrDefault(skin) ?? options;
            var metadataPath = Path.GetFullPath(Path.Combine(skinsPath, skin, skin + ".xml"));
            if (pendingMetadata.ContainsKey(skin) || prior.ContainsKey(metadataPath))
            {
                ValidateDestination(skinsPath, metadataPath);
                prior.TryGetValue(metadataPath, out var oldMetadata);
                planned.Add(metadataPath, ReadClean(metadataPath, oldMetadata, ()=>definition.Descriptor(sourceResolver.Metadata(definition.Parent!))));
                rollbackDefaults[metadataPath]=planned[metadataPath];
            }
            // Validate each actual parent chain even when a target resource is already local.
            var chain=resolver.Chain(skin);
            if(chain.Count<2 || !chain[1].Equals(definition.Parent,StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Unexpected Ext parent; preserve changed descriptor: "+skin);
            foreach (var panel in ExtendedPanelNames)
            {
                var destination = Path.GetFullPath(Path.Combine(skinsPath, skin, "panels", panel));
                if(panel=="global panels.xml" && (definition.LeftMenu is null ||
                    !pendingMetadata.ContainsKey(skin) && !prior.ContainsKey(destination)))continue;
                ValidateDestination(skinsPath, destination);
                prior.TryGetValue(destination, out var old);
                if (panel == "player profile.xml" && !skinOptions.PositionHighlightsEnabled
                    && !skinOptions.HiddenAttributesEnabled && old is null) continue;
                var source = ReadClean(destination, old, () => resolver.Get(skin, panel, skipFirst: old is not null));
                rollbackDefaults[destination]=source;
                planned.Add(destination, panel switch
                {
                    "player profile.xml"=>PlayerProfileXml.Transform(source,skinOptions,localizer),
                    "match team stats short.xml"=>TeamTalkSkinInstaller.Transform(source),
                    "global panels.xml"=>BaseMenuLayout(source,definition.LeftMenu!.Value),
                    _=>Transform(panel,source,fatigueTitle,localizer.Code,knownFatigueTitles)
                });
            }
        }
        foreach (var existing in prior.Keys)
            if (!planned.ContainsKey(existing))
                throw new InvalidDataException("An installed Ext skin is missing; restore it before updating.");
        var receiptFiles = new List<SkinPanelFileReceipt>();
        var before = planned.Keys.ToDictionary(path => path,
            path => File.Exists(path) ? File.ReadAllBytes(path) : null, StringComparer.OrdinalIgnoreCase);
        foreach (var (path, bytes) in planned)
        {
            prior.TryGetValue(path, out var old);
            var original = old is null ? before[path] : old.BeforeHash is null ? null : File.ReadAllBytes(old.Backup!);
            var originalHash = original is null ? null : Digest(original);
            var backup = originalHash is null ? null : Path.Combine(ReceiptRoot(skinsPath, IsNoche(skinsPath, path)), "backups", originalHash + ".xml");
            if (backup is not null)
            {
                if (File.Exists(backup) && FileDigest(backup) != originalHash)
                    throw new InvalidDataException("Skin backup hash conflict.");
                if (!File.Exists(backup))
                {
                    Directory.CreateDirectory(Path.GetDirectoryName(backup)!);
                    AtomicWrite(backup, original!);
                }
            }
            using var stream = new MemoryStream(bytes);
            XDocument.Load(stream);
            receiptFiles.Add(new(path, originalHash, backup, Digest(bytes)));
        }
        var receiptWrites = new Dictionary<string, byte[]>(StringComparer.OrdinalIgnoreCase);
        foreach (var group in receiptFiles.GroupBy(file => IsNoche(skinsPath, file.Path)))
        {
            var definition = active.First(skin => (skin.DirectoryName == "NocheExt") == group.Key);
            var partOptions = perSkinOptions?.GetValueOrDefault(definition.DirectoryName) ?? options;
            var receipt = new SkinPanelReceipt(2, "installed", Path.GetFullPath(skinsPath),
                partOptions.PositionHighlightsEnabled, partOptions.HiddenAttributesEnabled, group.ToList(), PanelLanguage: localizer.Code);
            var bytes = JsonSerializer.SerializeToUtf8Bytes(receipt, ReceiptJson);
            var groupRoot = ReceiptRoot(skinsPath, group.Key);
            Directory.CreateDirectory(groupRoot);
            AtomicWrite(Path.Combine(groupRoot, "plan-" + Guid.NewGuid().ToString("N") + ".json"), bytes);
            var receiptPath = ReceiptPath(skinsPath, group.Key);
            receiptWrites.Add(receiptPath, bytes);
            before.Add(receiptPath, File.Exists(receiptPath) ? File.ReadAllBytes(receiptPath) : null);
            rollbackDefaults[receiptPath]=JsonSerializer.SerializeToUtf8Bytes(receipt with{Status="uninstalled",Files=[]},ReceiptJson);
        }
        EnsureGameStopped(gamePath); // Recheck immediately before the first target mutation.
        foreach (var (path, original) in before)
            if (FileDigest(path) != (original is null ? null : Digest(original)))
                throw new InvalidDataException("Concurrent skin panel change before commit.");
        var changed = new List<string>();
        try
        {
            foreach (var (path, bytes) in planned)
            {
                if (before[path] is { } old && old.AsSpan().SequenceEqual(bytes)) continue;
                Directory.CreateDirectory(Path.GetDirectoryName(path)!);
                AtomicWrite(path, bytes);
                changed.Add(path);
            }
            foreach (var (path, bytes) in planned)
                if (FileDigest(path) != Digest(bytes)) throw new IOException("Skin panel readback differs: " + path);
            foreach (var (path, bytes) in receiptWrites)
            {
                AtomicWrite(path, bytes);
                changed.Add(path);
            }
            foreach (var (path, bytes) in receiptWrites)
                if (FileDigest(path) != Digest(bytes)) throw new IOException("Skin receipt readback differs: " + path);
        }
        catch (Exception error)
        {
            Rollback(before, changed, error,rollbackDefaults);
            throw;
        }
        return changed.Count(path => planned.ContainsKey(path));
    }

    private static byte[] BaseMenuLayout(byte[] source,bool left)
    {
        using var input=new MemoryStream(source);var xml=XDocument.Load(input);
        var main=xml.Descendants("container").Single(x=>(string?)x.Attribute("id")=="main");
        var layout=main.Elements("layout").Single(x=>(string?)x.Attribute("class")=="arrange_horizontal_attachment");
        layout.SetAttributeValue("alignment",left?"left, extend":"right, extend");
        return System.Text.Encoding.UTF8.GetBytes(xml.ToString());
    }

    private static void Rollback(Dictionary<string, byte[]?> originals, List<string> changed, Exception error,
        IReadOnlyDictionary<string,byte[]> defaults)
    {
        var failures = new List<Exception> { error };
        foreach (var path in changed.AsEnumerable().Reverse())
        {
            try
            {
                if (originals[path] is { } original) AtomicWrite(path, original);
                else if(defaults.TryGetValue(path,out var inherited))AtomicWrite(path,inherited);
                // A newly-created descriptor/pending artifact remains on disk.
                // Never emulate restoring absence by deleting a file.
            }
            catch (Exception rollback) when (rollback is IOException or UnauthorizedAccessException)
            {
                failures.Add(rollback);
            }
        }
        if (failures.Count > 1)
            throw new LauncherException("SkinInstallError", string.Join(Environment.NewLine, failures.Select(value => value.Message)));
    }

}

internal sealed class SkinResourceResolver
{
    private readonly string skinsPath;
    private readonly FmfArchive panels;
    private readonly FmfArchive patch;
    private readonly FmfArchive packaged;
    private readonly IReadOnlyDictionary<string, byte[]> plannedMetadata;
    internal SkinResourceResolver(string gamePath, string skinsPath,
        IReadOnlyDictionary<string, byte[]>? plannedMetadata = null)
    {
        this.skinsPath = skinsPath;
        this.plannedMetadata = plannedMetadata ?? new Dictionary<string, byte[]>(StringComparer.OrdinalIgnoreCase);
        var directory = Path.GetDirectoryName(gamePath)!;
        panels = new(Path.Combine(directory, "data", "panels.fmf"));
        patch = new(Path.Combine(directory, "data", "updates", "update-802", "data", "panels.fmf"));
        packaged = new(Path.Combine(directory, "data", "skins.fmf"));
    }

    internal IReadOnlyList<string> Chain(string skin)
    {
        var chain = new List<string>();
        while (!string.IsNullOrEmpty(skin))
        {
            if (chain.Count >= 16 || chain.Contains(skin, StringComparer.OrdinalIgnoreCase)
                || skin.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0 || skin is "." or "..")
                throw new InvalidDataException("Invalid or cyclic skin inheritance.");
            chain.Add(skin);
            byte[] bytes=Metadata(skin);
            using var input = new MemoryStream(bytes);
            var xml = XDocument.Load(input);
            var parent = xml.Root?.Elements().Where(value => (string?)value.Attribute("id") == "parent").ToArray() ?? [];
            if (parent.Length > 1) throw new InvalidDataException("Ambiguous skin parent.");
            skin = parent.SingleOrDefault()?.Attribute("value")?.Value ?? "";
        }
        return chain;
    }

    internal bool HasMetadata(string skin)=>File.Exists(Path.Combine(skinsPath,skin,skin+".xml"))
        || plannedMetadata.ContainsKey(skin) || packaged.Names.Contains(skin+"\\"+skin+".xml",StringComparer.OrdinalIgnoreCase);

    internal byte[] Metadata(string skin)
    {
        if(skin.IndexOfAny(Path.GetInvalidFileNameChars())>=0 || skin is "." or "..")throw new InvalidDataException("Invalid skin name.");
        var path=Path.Combine(skinsPath,skin,skin+".xml");
        if(File.Exists(path))return File.ReadAllBytes(path);
        if(plannedMetadata.TryGetValue(skin,out var bytes))return bytes;
        var member=skin+"\\"+skin+".xml";
        if(!packaged.Names.Contains(member,StringComparer.OrdinalIgnoreCase))throw new InvalidDataException("Missing skin parent metadata: "+skin);
        return packaged.Get(member);
    }

    internal byte[] Get(string skin, string panel, bool skipFirst = false)
    {
        foreach (var ancestor in Chain(skin).Skip(skipFirst ? 1 : 0))
        {
            var path = Path.Combine(skinsPath, ancestor, "panels", panel);
            if (File.Exists(path)) return File.ReadAllBytes(path);
            var member = ancestor + "\\panels\\" + panel;
            if (packaged.Names.Contains(member, StringComparer.OrdinalIgnoreCase)) return packaged.Get(member);
        }
        if (patch.Names.Contains(panel, StringComparer.OrdinalIgnoreCase)) return patch.Get(panel);
        return panels.Get(panel);
    }
}
