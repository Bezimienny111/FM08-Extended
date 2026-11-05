using System.Diagnostics;
using System.IO.Compression;
using System.Text;
using System.Xml;
using System.Xml.Linq;

namespace FmLauncher;

internal static class SkinPanelInstaller
{
    internal const string BackupSuffix = ".before-fmext-panels";
    internal const string EditViewId = "Fmed";
    internal const string EditViewName = "Edycja";
    internal const string TrainingFragment = """
        <widget class="label" text="Zmęczenie sezonowe" col="0" row="7" auto_size="vertical"/>
        <widget class="label" id="Fmjd" col="2" row="7" auto_size="vertical" text="----"/>
        """;
    internal const string SquadFragment = """
        <record id="Fjad" width="132" minimum_width="115" auto_hide_priority="950"/>
        <record id="Fcab" width="44" minimum_width="32" auto_hide_priority="900"/>
        <record id="Fpab" width="44" minimum_width="32" auto_hide_priority="900"/>
        """;
    internal const string TacticsFragment = """
        <record id="Fjad" width="132" minimum_width="115" auto_hide_priority="950"/>
        """;
    internal static string ColumnRegistryFragment(string fatigueTitle) =>
        string.Join(Environment.NewLine, ColumnDefinitions(fatigueTitle).Select(column => column.ToString()));

    private static IEnumerable<XElement> ColumnDefinitions(string fatigueTitle)
    {
        foreach (var (id, title, width, minimum, priority) in new[]
        {
            ("Fjad", fatigueTitle, 132, 115, 950),
            ("Fcab", "CA", 44, 32, 900),
            ("Fpab", "PA", 44, 32, 900)
        })
            yield return new XElement("record",
                new XElement("flags", new XAttribute("id", "id"), new XAttribute("value", id)),
                new XElement("flags", new XAttribute("id", "width"), new XAttribute("value", width)),
                new XElement("integer", new XAttribute("id", "minimum_width"), new XAttribute("value", minimum)),
                new XElement("boolean", new XAttribute("id", "sort_ascending"), new XAttribute("value", "false")),
                new XElement("integer", new XAttribute("id", "auto_hide_priority"), new XAttribute("value", priority)),
                new XElement("record", new XAttribute("id", "column_properties"),
                    new XElement("flags", new XAttribute("id", "alignment"), new XAttribute("value", "centre"))),
                new XElement("record", new XAttribute("id", "column_heading"),
                    new XElement("flags", new XAttribute("id", "alignment"), new XAttribute("value", "centre")),
                    new XElement("string", new XAttribute("id", "text"), new XAttribute("value", title)),
                    new XElement("string", new XAttribute("id", "hint"), new XAttribute("value", title))));
    }

    internal static int Install(string gamePath, string skinsPath, string fatigueTitle)
    {
        using var launchLock = new Mutex(false, @"Local\FmLauncher.GameStart");
        bool acquired;
        try { acquired = launchLock.WaitOne(0); }
        catch (AbandonedMutexException) { acquired = true; }
        if (!acquired) throw new LauncherException("AlreadyRunning");
        try
        {
            var candidates = Process.GetProcessesByName(Path.GetFileNameWithoutExtension(gamePath));
            try
            {
                if (candidates.Any(candidate => !candidate.HasExited))
                    throw new LauncherException("SkinGameRunning");
            }
            finally { foreach (var candidate in candidates) candidate.Dispose(); }
            return InstallStopped(gamePath, skinsPath, fatigueTitle);
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or XmlException
            or InvalidDataException or OverflowException or ArgumentException)
        {
            throw new LauncherException("SkinInstallError", ex.Message);
        }
        finally { launchLock.ReleaseMutex(); }
    }

    private static int InstallStopped(string gamePath, string skinsPath, string fatigueTitle)
    {
        if (!Path.IsPathFullyQualified(gamePath) || !File.Exists(gamePath))
            throw new LauncherException("InvalidGamePath", gamePath);
        if (!Path.IsPathFullyQualified(skinsPath) || !Directory.Exists(skinsPath))
            throw new LauncherException("SkinDirectoryMissing", skinsPath);
        var blackSkins = new[] { "steklo_black", "steklo_left_black" }
            .Where(skin => File.Exists(Path.Combine(skinsPath, skin, skin + ".xml"))).ToArray();
        if (blackSkins.Length == 0)
            throw new LauncherException("SkinBlackMissing", skinsPath);
        var gameDirectory = Path.GetDirectoryName(gamePath)!;
        var panels = new FmfArchive(Path.Combine(gameDirectory, "data", "panels.fmf"));
        var patch = new FmfArchive(Path.Combine(gameDirectory, "data", "updates", "update-802", "data", "panels.fmf"));
        var skins = new FmfArchive(Path.Combine(gameDirectory, "data", "skins.fmf"));
        var plans = new Dictionary<string, byte[]>(StringComparer.OrdinalIgnoreCase);
        foreach (var name in skins.Names.Where(name => name.StartsWith(@"fm2008\", StringComparison.OrdinalIgnoreCase)))
        {
            var destination = Path.Combine(skinsPath, name);
            if (!File.Exists(destination)) plans.Add(destination, skins.Get(name));
        }
        foreach (var skin in new[] { "fm2008" }.Concat(blackSkins))
        foreach (var name in new[] { "player training.xml", "team squad.xml", "tactic person list.xml", "person list table.xml" })
        {
            var destination = Path.Combine(skinsPath, skin, "panels", name);
            var ancestors = skin switch
            {
                "steklo_left_black" => new[] { skin, "steklo_left", "steklo" },
                "steklo_black" => new[] { skin, "steklo" },
                _ => new[] { skin }
            };
            var inherited = ancestors.Select(ancestor => Path.Combine(skinsPath, ancestor, "panels", name))
                .FirstOrDefault(File.Exists);
            var source = inherited is not null ? File.ReadAllBytes(inherited)
                : patch.Names.Contains(name, StringComparer.OrdinalIgnoreCase) ? patch.Get(name) : panels.Get(name);
            plans[destination] = Transform(name, source, fatigueTitle);
        }
        var originals = plans.Keys.ToDictionary(path => path,
            path => File.Exists(path) ? File.ReadAllBytes(path) : null, StringComparer.OrdinalIgnoreCase);
        var changed = new List<string>();
        try
        {
            foreach (var (path, bytes) in plans)
            {
                var previous = originals[path];
                if (previous is not null && previous.AsSpan().SequenceEqual(bytes)) continue;
                Directory.CreateDirectory(Path.GetDirectoryName(path)!);
                if (previous is not null && !File.Exists(path + BackupSuffix))
                    File.Copy(path, path + BackupSuffix, overwrite: false);
                AtomicWrite(path, bytes);
                changed.Add(path);
            }
        }
        catch (Exception error) when (error is IOException or UnauthorizedAccessException)
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
            throw new LauncherException("SkinInstallError", string.Join(Environment.NewLine, failures.Select(e => e.Message)));
        }
        return changed.Count;
    }

    private static void AtomicWrite(string path, byte[] bytes)
    {
        var temporary = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
        try
        {
            File.WriteAllBytes(temporary, bytes);
            File.Move(temporary, path, overwrite: true);
        }
        finally { if (File.Exists(temporary)) File.Delete(temporary); }
    }

    internal static byte[] Transform(string name, byte[] original, string fatigueTitle)
    {
        using var stream = new MemoryStream(original);
        var xml = XDocument.Load(stream, LoadOptions.PreserveWhitespace);
        if (name == "player training.xml")
        {
            var table = xml.Descendants("widget").SingleOrDefault(e => (string?)e.Attribute("id") == "phpb")
                ?? throw new InvalidDataException("Missing training table phpb.");
            var value = table.Elements("widget").SingleOrDefault(e => (string?)e.Attribute("id") == "Fmjd");
            if (value is null)
            {
                var rows = table.Elements("widget").Select(e => (int?)e.Attribute("row") ?? -1);
                var row = rows.DefaultIfEmpty(-1).Max() + 1;
                table.Add(new XText("\n\t\t\t\t\t"));
                table.Add(new XElement("widget", new XAttribute("class", "label"),
                    new XAttribute("text", fatigueTitle), new XAttribute("col", "0"),
                    new XAttribute("row", row), new XAttribute("auto_size", "vertical")));
                table.Add(new XText("\n\t\t\t\t\t"));
                table.Add(new XElement("widget", new XAttribute("class", "label"),
                    new XAttribute("id", "Fmjd"), new XAttribute("col", "2"),
                    new XAttribute("row", row), new XAttribute("auto_size", "vertical"),
                    new XAttribute("text", "\u2014")));
                table.Add(new XText("\n\t\t\t\t"));
            }
        }
        else if (name == "person list table.xml")
        {
            var registry = xml.Descendants("list").SingleOrDefault(e =>
                (string?)e.Attribute("id") == "column_display_properties")
                ?? throw new InvalidDataException("Missing column_display_properties registry.");
            foreach (var definition in ColumnDefinitions(fatigueTitle))
            {
                var id = definition.Elements("flags").Single(e => (string?)e.Attribute("id") == "id")
                    .Attribute("value")!.Value;
                var existing = registry.Elements("record").Where(e => e.Elements("flags").Any(
                    flag => (string?)flag.Attribute("id") == "id" && (string?)flag.Attribute("value") == id)).ToArray();
                if (existing.Length > 1) throw new InvalidDataException("Duplicate FMExt column definition " + id + ".");
                if (existing.Length == 1) existing[0].ReplaceWith(definition);
                else registry.Add(new XText("\n"), definition, new XText("\n"));
            }
        }
        else
        {
            var viewId = name == "team squad.xml" ? "sltn" : name == "tactic person list.xml" ? "posi"
                : throw new ArgumentException("Unsupported panel.", nameof(name));
            var view = xml.Descendants("record").SingleOrDefault(e => (string?)e.Attribute("id") == viewId)
                ?.Elements("record").SingleOrDefault(e => (string?)e.Attribute("id") == "view")
                ?? throw new InvalidDataException("Missing list view " + viewId + ".");
            AddColumn(view, "Fjad", "Pcon", 132, 115, 950);
            if (viewId == "sltn")
            {
                foreach (var id in new[] { "PCAB", "PPAB" })
                    foreach (var entry in view.Elements().Where(e => (string?)e.Attribute("id") == id).ToArray())
                        entry.Remove();
                AddColumn(view, "Fcab", null, 44, 32, 900);
                AddColumn(view, "Fpab", null, 44, 32, 900);
            }
            AddEditView(view, viewId == "sltn");
        }
        using var output = new MemoryStream();
        using (var writer = XmlWriter.Create(output, new XmlWriterSettings
        {
            Encoding = new UTF8Encoding(false), Indent = false, OmitXmlDeclaration = xml.Declaration is null
        })) xml.Save(writer);
        return output.ToArray();
    }

    private static void AddEditView(XElement view, bool squad)
    {
        var template = view.Parent ?? throw new InvalidDataException("Missing view definition.");
        var menu = template.Parent ?? throw new InvalidDataException("Missing views menu.");
        if (menu.Name != "list" || (string?)menu.Attribute("id") != "items")
            throw new InvalidDataException("Unexpected views menu.");
        if (menu.Elements("record").Any(e => (string?)e.Attribute("id") == EditViewId)) return;
        var edit = new XElement(template);
        edit.SetAttributeValue("id", EditViewId);
        foreach (var text in edit.Nodes().OfType<XText>().Where(t => !string.IsNullOrWhiteSpace(t.Value)).ToArray())
            text.Remove();
        var caption = edit.Elements("string")
            .Single(e => (string?)e.Attribute("id") is "name" or "text");
        caption.SetAttributeValue("value", EditViewName);
        var columns = edit.Elements("record").Single(e => (string?)e.Attribute("id") == "view");
        var keep = new HashSet<string> { "Ppkd", "Pnfo", "Pnam", "Ppos", "Pcon", "Fjad" };
        if (squad) keep.UnionWith(["Fcab", "Fpab"]);
        foreach (var column in columns.Elements().ToArray())
        {
            var id = (string?)column.Attribute("id");
            if (id is null || !keep.Contains(id)) column.Remove();
            else if (id is "Fjad" or "Fcab" or "Fpab")
                column.SetAttributeValue("auto_hide_priority", 0);
        }
        template.AddAfterSelf(new XText("\n"), edit);
    }

    private static void AddColumn(XElement view, string id, string? after, int width, int minimum, int priority)
    {
        var existing = view.Elements().Where(e => (string?)e.Attribute("id") == id).ToArray();
        if (existing.Length > 1) throw new InvalidDataException("Duplicate FMExt column " + id + ".");
        if (existing.Length == 1) return;
        var column = new XElement("record", new XAttribute("id", id), new XAttribute("width", width),
            new XAttribute("minimum_width", minimum), new XAttribute("auto_hide_priority", priority));
        var previous = after is null ? null : view.Elements().LastOrDefault(e => (string?)e.Attribute("id") == after);
        if (previous is null) view.Add(new XText("\n\t\t\t\t\t\t\t\t"), column, new XText("\n"));
        else previous.AddAfterSelf(new XText("\n\t\t\t\t\t\t\t\t"), column);
    }
}

internal sealed class FmfArchive
{
    private readonly byte[] data;
    private readonly Dictionary<string, (uint Offset, uint Stored, uint Length)> entries = new(StringComparer.OrdinalIgnoreCase);
    internal IEnumerable<string> Names => entries.Keys;

    internal FmfArchive(string path)
    {
        data = File.ReadAllBytes(path);
        if (data.Length < 18 || !data.AsSpan(0, 6).SequenceEqual(new byte[] { 2, 1, 0x66, 0x6D, 0x66, 0x2E }))
            throw new InvalidDataException("Invalid FMF: " + path);
        var offset = checked((int)System.Buffers.Binary.BinaryPrimitives.ReadUInt32LittleEndian(data.AsSpan(9)) + 18);
        if (offset >= data.Length) throw new InvalidDataException("Invalid FMF directory offset: " + path);
        using var compressed = new MemoryStream(data, offset, data.Length - offset, writable: false);
        using var inflate = new ZLibStream(compressed, CompressionMode.Decompress);
        using var toc = new MemoryStream();
        inflate.CopyTo(toc);
        if (toc.Length is < 4 or > 16 * 1024 * 1024) throw new InvalidDataException("Invalid FMF directory length.");
        toc.Position = 4;
        using var reader = new BinaryReader(toc, Encoding.Unicode, leaveOpen: true);
        ReadNode("", 0);
        if (toc.Position != toc.Length) throw new InvalidDataException("Unexpected FMF directory trailer.");

        string Text()
        {
            var count = reader.ReadUInt32();
            if (count > 4096) throw new InvalidDataException("Invalid FMF name length.");
            var bytes = reader.ReadBytes(checked((int)count * 2));
            if (bytes.Length != count * 2 || reader.ReadUInt16() != 0) throw new InvalidDataException("Invalid FMF name.");
            return Encoding.Unicode.GetString(bytes);
        }
        void ReadNode(string prefix, int depth)
        {
            if (depth > 32) throw new InvalidDataException("Invalid FMF directory nesting.");
            var files = reader.ReadUInt16();
            for (var i = 0; i < files; i++)
            {
                var name = prefix + Text() + Text();
                if (Path.IsPathRooted(name) || name.Split('\\').Any(part => part is "." or ".."))
                    throw new InvalidDataException("Invalid FMF resource path.");
                if (!entries.TryAdd(name, (reader.ReadUInt32(), reader.ReadUInt32(), reader.ReadUInt32())))
                    throw new InvalidDataException("Duplicate FMF resource.");
            }
            var directories = reader.ReadUInt16();
            for (var i = 0; i < directories; i++) ReadNode(prefix + Text() + "\\", depth + 1);
        }
    }

    internal byte[] Get(string name)
    {
        if (!entries.TryGetValue(name, out var entry)) throw new InvalidDataException("FMF resource not found: " + name);
        var offset = checked((int)entry.Offset + 9);
        var stored = checked((int)entry.Stored);
        if (entry.Length > 8 * 1024 * 1024 || offset > data.Length - stored)
            throw new InvalidDataException("Invalid FMF resource length: " + name);
        using var source = new MemoryStream(data, offset, stored, writable: false);
        if (entry.Stored == entry.Length) return data.AsSpan(offset, stored).ToArray();
        using var inflate = new ZLibStream(source, CompressionMode.Decompress);
        using var output = new MemoryStream();
        inflate.CopyTo(output);
        if (output.Length != entry.Length) throw new InvalidDataException("Incomplete FMF resource: " + name);
        return output.ToArray();
    }
}
