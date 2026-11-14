using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Web.Script.Serialization;
using System.Xml;

public static class NativeStaffTool
{
    static readonly BindingFlags Hidden = BindingFlags.Static | BindingFlags.NonPublic;
    public static byte[] Load(string root, string file) { return (byte[])typeof(FM08_Database_Editor).GetMethod("DecompressFile", Hidden).Invoke(null, new object[] { Path.Combine(root, file) }); }
    public static string Hash(string file) { using (var s = File.OpenRead(file)) using (var h = SHA256.Create()) return BitConverter.ToString(h.ComputeHash(s)).Replace("-", ""); }
    public static Dictionary<string, string> Hashes(string root) { return Directory.GetFiles(root, "*", SearchOption.AllDirectories).ToDictionary(p => p.Substring(root.Length + 1), Hash); }
    static string Csv(object value) { return "\"" + Convert.ToString(value, System.Globalization.CultureInfo.InvariantCulture).Replace("\"", "\"\"") + "\""; }
    public static int Main(string[] a) { try {
        if (a.Length < 3) throw new ArgumentException("--export source output.csv UID... | --validate source changes.csv report.json | --apply source changes.csv NEW-database");
        string source = Path.GetFullPath(a[1]).TrimEnd(Path.DirectorySeparatorChar);
        var pins = Hashes(source); byte[] p = Load(source, "people_db.dat"), s = Load(source, "server_db.dat");
        if (a[0] == "--export") {
            if (a.Length < 4 || File.Exists(a[2]) || Directory.Exists(a[2])) throw new IOException("Provide UID(s) and a new CSV path.");
            var records = a.Skip(3).Select(id => FM08_Database_Editor.ReadNativeStaff(p, s, int.Parse(id))).ToList();
            if (!pins.OrderBy(x => x.Key).SequenceEqual(Hashes(source).OrderBy(x => x.Key))) throw new IOException("Source changed during export.");
            File.WriteAllLines(a[2], new[] { "ID,PersonIndex,FirstName,LastName,ClubIndex,Club,PersonTypeRaw,ClubRoleRaw,WeeklyWage,BirthDate,ContractExpires" }.Concat(records.Select(r => string.Join(",", new object[] { r.Id, r.PersonIndex, r.FirstName, r.LastName, r.ClubIndex, r.Club, r.PersonTypeRaw, r.ClubRoleRaw, r.WeeklyWage, r.BirthDate.Value.ToString("yyyy-MM-dd"), r.ContractExpires.HasValue ? r.ContractExpires.Value.ToString("yyyy-MM-dd") : "" }.Select(Csv)))), new UTF8Encoding(false));
            Console.WriteLine("Exported staff profiles: " + records.Count); return 0;
        }
        if (a.Length != 4 || (a[0] != "--validate" && a[0] != "--apply")) throw new ArgumentException("Unknown mode or argument count.");
        var plan = FM08_Database_Editor.ReadNativeStaffWageCsv(a[2]);
        byte[] edited = FM08_Database_Editor.ApplyNativeStaffWages(p, s, plan);
        foreach (var change in plan) if (FM08_Database_Editor.ReadNativeStaff(edited, s, change.Id).WeeklyWage != change.WeeklyWage) throw new InvalidDataException("Staff readback failed.");
        if (!pins.OrderBy(x => x.Key).SequenceEqual(Hashes(source).OrderBy(x => x.Key))) throw new IOException("Source changed during validation.");
        if (a[0] == "--validate") {
            if (File.Exists(a[3]) || Directory.Exists(a[3])) throw new IOException("Report already exists.");
            File.WriteAllText(a[3], new JavaScriptSerializer { MaxJsonLength = int.MaxValue }.Serialize(new { status = "validated_in_memory", changes = plan.Count, source, source_hashes = pins, database_writes = false }), new UTF8Encoding(false));
            Console.WriteLine("Validated staff wage changes in memory: " + plan.Count); return 0;
        }
        string target = Path.GetFullPath(a[3]).TrimEnd(Path.DirectorySeparatorChar), sep = Path.DirectorySeparatorChar.ToString();
        if (Directory.Exists(target) || File.Exists(target) || target.Equals(source, StringComparison.OrdinalIgnoreCase) || target.StartsWith(source + sep, StringComparison.OrdinalIgnoreCase) || source.StartsWith(target + sep, StringComparison.OrdinalIgnoreCase)) throw new IOException("A separate, new database directory is required.");
        string stage = target + ".staff-staging-" + Guid.NewGuid().ToString("N"); Directory.CreateDirectory(stage);
        foreach (var file in pins.Keys) { string dest = Path.Combine(stage, file); Directory.CreateDirectory(Path.GetDirectoryName(dest)); File.Copy(Path.Combine(source, file), dest, false); }
        byte[] raw = File.ReadAllBytes(Path.Combine(source, "people_db.dat"));
        byte[] compressed = (byte[])typeof(FM08_Database_Editor).GetMethod("CompressFile", Hidden).Invoke(null, new object[] { edited, raw.Take(9).ToArray() });
        File.WriteAllBytes(Path.Combine(stage, "people_db.dat"), compressed);
        if (!Load(stage, "people_db.dat").SequenceEqual(edited)) throw new InvalidDataException("Compressed staff output differs.");
        string[] xml = Directory.GetFiles(stage, "*.xml");
        if (xml.Length != 1) throw new InvalidDataException("Expected one database metadata XML.");
        var metadata = new XmlDocument(); metadata.Load(xml[0]);
        var name = metadata.SelectSingleNode("//string[@id='name']/@value"); if (name == null) throw new InvalidDataException("Database name missing.");
        name.Value = Path.GetFileName(target); string finalXml = Path.Combine(stage, Path.GetFileName(target) + ".xml");
        if (!finalXml.Equals(xml[0], StringComparison.OrdinalIgnoreCase)) { metadata.Save(finalXml); File.Delete(xml[0]); } else metadata.Save(finalXml);
        foreach (var file in pins.Keys.Where(f => f != "people_db.dat" && !f.EndsWith(".xml", StringComparison.OrdinalIgnoreCase))) if (Hash(Path.Combine(stage, file)) != pins[file]) throw new InvalidDataException("Protected file changed: " + file);
        if (!pins.OrderBy(x => x.Key).SequenceEqual(Hashes(source).OrderBy(x => x.Key))) throw new IOException("Source changed during copy.");
        Directory.Move(stage, target); Console.WriteLine("Created staff wage database: " + target); return 0;
    } catch (Exception ex) { Console.Error.WriteLine(ex); return 1; } }
}
