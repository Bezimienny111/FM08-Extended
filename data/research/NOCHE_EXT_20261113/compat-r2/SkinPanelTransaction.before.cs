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
        ["player training.xml", "team squad.xml", "tactic person list.xml", "person list table.xml", "player profile.xml"];
    private static readonly JsonSerializerOptions ReceiptJson = new() { WriteIndented = true };
    private static string Digest(byte[] bytes) => Convert.ToHexString(SHA256.HashData(bytes));
    private static string? FileDigest(string path) => File.Exists(path) ? Digest(File.ReadAllBytes(path)) : null;
    private static string ReceiptRoot(string skinsPath) => Path.Combine(
        Path.GetDirectoryName(Path.GetFullPath(skinsPath))!, ".fmext", "player-panels");
    private static string ReceiptPath(string skinsPath) => Path.Combine(ReceiptRoot(skinsPath), "installation.json");

    internal static int InstallExt(string gamePath, string skinsPath, string fatigueTitle,
        PlayerProfilePanelOptions options, Localizer localizer)
    {
        options.Validate();
        if (options.PositionHighlightsEnabled && !PositionHighlightModel.IntegrationReady)
            throw new LauncherException("PositionHighlightsUnavailable");
        return WithStoppedGame(gamePath, () => InstallExtStopped(gamePath, skinsPath, fatigueTitle, options, localizer));
    }

    // Existing receipts without PanelLanguage migrate through the same checked transaction.
    // This does not create a new installation or bypass changed-file / backup ownership checks.
    internal static int EnsurePanelLanguage(string gamePath, string skinsPath,
        PlayerProfilePanelOptions options, Localizer panelLocalizer) =>
        WithStoppedGame(gamePath, () =>
        {
            var previous = ReadReceipt(skinsPath);
            if (previous is not { Status: "installed" }) return 0;
            ValidateProfileReadiness(skinsPath, options);
            foreach (var file in previous.Files)
                if (FileDigest(file.Path) != file.AfterHash)
                    throw new InvalidDataException("Installed panel changed after installation.");
            if (previous.PanelLanguage == panelLocalizer.Code) return 0;
            // Preserve the previously installed independent feature switches; PLAY's
            // readiness check remains responsible for newly requested options.
            var installed = new PlayerProfilePanelOptions(previous.PositionHighlights, previous.HiddenAttributes);
            return InstallExtStopped(gamePath, skinsPath, panelLocalizer.Text("PanelFatigueTitle"), installed, panelLocalizer);
        });

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
        WithStoppedGame(gamePath, () => UninstallStopped(gamePath, skinsPath));

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

    private static SkinPanelReceipt? ReadReceipt(string skinsPath)
    {
        var path = ReceiptPath(skinsPath);
        if (!File.Exists(path)) return null;
        var receipt = JsonSerializer.Deserialize<SkinPanelReceipt>(File.ReadAllBytes(path), ReceiptJson)
            ?? throw new InvalidDataException("Invalid skin installation receipt.");
        if (receipt.Schema != 2 || !Path.GetFullPath(receipt.SkinsRoot).Equals(
            Path.GetFullPath(skinsPath), StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("Skin installation receipt scope differs.");
        foreach (var file in receipt.Files)
        {
            ValidateDestination(skinsPath, file.Path);
            if (file.Backup is not null && !Path.GetFullPath(file.Backup).StartsWith(
                ReceiptRoot(skinsPath) + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Skin backup is outside the receipt root.");
        }
        // The receipt may come from a checked private clone or a caller using '/'.
        // Canonicalize only after scope/backup validation, before ownership lookup.
        receipt = receipt with { Files = receipt.Files.Select(file => file with
        {
            Path = Path.GetFullPath(file.Path),
            Backup = file.Backup is null ? null : Path.GetFullPath(file.Backup)
        }).ToList() };
        if (receipt.Files.Select(value => value.Path).Distinct(StringComparer.OrdinalIgnoreCase).Count() != receipt.Files.Count)
            throw new InvalidDataException("Duplicate skin receipt target.");
        return receipt;
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
        PlayerProfilePanelOptions options, Localizer localizer)
    {
        if (!Path.IsPathFullyQualified(skinsPath) || !Directory.Exists(skinsPath))
            throw new LauncherException("SkinDirectoryMissing", skinsPath);
        var active = ExtSkinCatalog.All.Where(skin =>
            File.Exists(Path.Combine(skinsPath, skin.DirectoryName, skin.DirectoryName + ".xml"))
            || skin.CreateWhenParentPresent && File.Exists(Path.Combine(skinsPath, skin.Parent!, skin.Parent + ".xml")))
            .ToArray();
        if (active.Length == 0) throw new LauncherException("SkinExtMissing", skinsPath);
        var previous = ReadReceipt(skinsPath);
        if (previous is { Status: "uninstalled" }) previous = null;
        var prior = previous?.Files.ToDictionary(value => value.Path, StringComparer.OrdinalIgnoreCase)
            ?? new Dictionary<string, SkinPanelFileReceipt>(StringComparer.OrdinalIgnoreCase);
        var pendingMetadata = active.Where(skin => skin.CreateWhenParentPresent && !File.Exists(
            Path.Combine(skinsPath, skin.DirectoryName, skin.DirectoryName + ".xml")))
            .ToDictionary(skin => skin.DirectoryName, skin => skin.Descriptor(), StringComparer.OrdinalIgnoreCase);
        var resolver = new SkinResourceResolver(gamePath, skinsPath, pendingMetadata);
        var knownFatigueTitles = localizer.Languages.Select(language => language.Texts.GetValueOrDefault("PanelFatigueTitle"))
            .Where(title => title is not null).Cast<string>().Append(fatigueTitle).Distinct(StringComparer.Ordinal).ToArray();
        var planned = new Dictionary<string, byte[]>(StringComparer.OrdinalIgnoreCase);
        foreach (var definition in active)
        {
            var skin = definition.DirectoryName;
            var metadataPath = Path.GetFullPath(Path.Combine(skinsPath, skin, skin + ".xml"));
            if (pendingMetadata.ContainsKey(skin) || prior.ContainsKey(metadataPath))
            {
                ValidateDestination(skinsPath, metadataPath);
                prior.TryGetValue(metadataPath, out var oldMetadata);
                planned.Add(metadataPath, ReadClean(metadataPath, oldMetadata, definition.Descriptor));
            }
            // Validate each actual parent chain even when a target resource is already local.
            resolver.Chain(skin);
            foreach (var panel in ExtendedPanelNames)
            {
                var destination = Path.GetFullPath(Path.Combine(skinsPath, skin, "panels", panel));
                ValidateDestination(skinsPath, destination);
                prior.TryGetValue(destination, out var old);
                if (panel == "player profile.xml" && !options.PositionHighlightsEnabled
                    && !options.HiddenAttributesEnabled && old is null) continue;
                var source = ReadClean(destination, old, () => resolver.Get(skin, panel, skipFirst: old is not null));
                planned.Add(destination, panel == "player profile.xml"
                    ? PlayerProfileXml.Transform(source, options, localizer) : Transform(panel, source, fatigueTitle, localizer.Code, knownFatigueTitles));
            }
        }
        foreach (var existing in prior.Keys)
            if (!planned.ContainsKey(existing))
                throw new InvalidDataException("An installed Ext skin is missing; restore it before updating.");
        var root = ReceiptRoot(skinsPath);
        Directory.CreateDirectory(Path.Combine(root, "backups"));
        var receiptFiles = new List<SkinPanelFileReceipt>();
        var before = planned.Keys.ToDictionary(path => path,
            path => File.Exists(path) ? File.ReadAllBytes(path) : null, StringComparer.OrdinalIgnoreCase);
        foreach (var (path, bytes) in planned)
        {
            prior.TryGetValue(path, out var old);
            var original = old is null ? before[path] : old.BeforeHash is null ? null : File.ReadAllBytes(old.Backup!);
            var originalHash = original is null ? null : Digest(original);
            var backup = originalHash is null ? null : Path.Combine(root, "backups", originalHash + ".xml");
            if (backup is not null)
            {
                if (File.Exists(backup) && FileDigest(backup) != originalHash)
                    throw new InvalidDataException("Skin backup hash conflict.");
                if (!File.Exists(backup)) AtomicWrite(backup, original!);
            }
            using var stream = new MemoryStream(bytes);
            XDocument.Load(stream);
            receiptFiles.Add(new(path, originalHash, backup, Digest(bytes)));
        }
        var receipt = new SkinPanelReceipt(2, "installed", Path.GetFullPath(skinsPath),
            options.PositionHighlightsEnabled, options.HiddenAttributesEnabled, receiptFiles,
            PanelLanguage: localizer.Code);
        var planPath = Path.Combine(root, "plan-" + Guid.NewGuid().ToString("N") + ".json");
        AtomicWrite(planPath, JsonSerializer.SerializeToUtf8Bytes(receipt, ReceiptJson));
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
            AtomicWrite(ReceiptPath(skinsPath), JsonSerializer.SerializeToUtf8Bytes(receipt, ReceiptJson));
        }
        catch (Exception error)
        {
            Rollback(before, changed, error);
            throw;
        }
        return changed.Count;
    }

    private static void Rollback(Dictionary<string, byte[]?> originals, List<string> changed, Exception error)
    {
        var failures = new List<Exception> { error };
        foreach (var path in changed.AsEnumerable().Reverse())
        {
            try
            {
                if (originals[path] is { } original) AtomicWrite(path, original);
                else File.Delete(path);
            }
            catch (Exception rollback) when (rollback is IOException or UnauthorizedAccessException)
            {
                failures.Add(rollback);
            }
        }
        if (failures.Count > 1)
            throw new LauncherException("SkinInstallError", string.Join(Environment.NewLine, failures.Select(value => value.Message)));
    }

    private static int UninstallStopped(string gamePath, string skinsPath)
    {
        var receipt = ReadReceipt(skinsPath);
        if (receipt is null || receipt.Status == "uninstalled") return 0;
        foreach (var file in receipt.Files)
            if (FileDigest(file.Path) != file.AfterHash
                || file.BeforeHash is not null && (file.Backup is null || FileDigest(file.Backup) != file.BeforeHash))
                throw new InvalidDataException("Uninstall conflict; preserve changed skin file: " + file.Path);
        var originals = receipt.Files.ToDictionary(value => value.Path,
            value => (byte[]?)File.ReadAllBytes(value.Path), StringComparer.OrdinalIgnoreCase);
        var changed = new List<string>();
        EnsureGameStopped(gamePath);
        try
        {
            foreach (var file in receipt.Files)
            {
                if (file.BeforeHash is null) File.Delete(file.Path);
                else AtomicWrite(file.Path, File.ReadAllBytes(file.Backup!));
                changed.Add(file.Path);
            }
            foreach (var file in receipt.Files)
                if (FileDigest(file.Path) != file.BeforeHash)
                    throw new IOException("Skin uninstall readback differs: " + file.Path);
            AtomicWrite(ReceiptPath(skinsPath), JsonSerializer.SerializeToUtf8Bytes(receipt with { Status = "uninstalled" }, ReceiptJson));
        }
        catch (Exception error) { Rollback(originals, changed, error); throw; }
        return changed.Count;
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
            var path = Path.Combine(skinsPath, skin, skin + ".xml");
            byte[] bytes;
            if (File.Exists(path)) bytes = File.ReadAllBytes(path);
            else if (plannedMetadata.TryGetValue(skin, out var planned)) bytes = planned;
            else
            {
                var member = skin + "\\" + skin + ".xml";
                if (!packaged.Names.Contains(member, StringComparer.OrdinalIgnoreCase))
                    throw new InvalidDataException("Missing skin parent metadata: " + skin);
                bytes = packaged.Get(member);
            }
            using var input = new MemoryStream(bytes);
            var xml = XDocument.Load(input);
            var parent = xml.Root?.Elements().Where(value => (string?)value.Attribute("id") == "parent").ToArray() ?? [];
            if (parent.Length > 1) throw new InvalidDataException("Ambiguous skin parent.");
            skin = parent.SingleOrDefault()?.Attribute("value")?.Value ?? "";
        }
        return chain;
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
