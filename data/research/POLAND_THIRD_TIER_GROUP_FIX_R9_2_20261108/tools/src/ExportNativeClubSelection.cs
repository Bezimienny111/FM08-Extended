using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Xml;

class ExportNativeClubSelection
{
    static void Main(string[] args)
    {
        if (args.Length != 3 && args.Length != 4)
            throw new ArgumentException("Usage: source-db editor-exe output-csv [verified-name-corrections.xml]");
        string editor = Path.GetFullPath(args[1]);
        if (!File.Exists(editor)) throw new FileNotFoundException("Editor assembly not found.", editor);
        var domain = AppDomain.CreateDomain("NativeClubSnapshot", null,
            new AppDomainSetup { ApplicationBase = Path.GetDirectoryName(editor) });
        try
        {
            var worker = (NativeClubSelectionWorker)domain.CreateInstanceFromAndUnwrap(
                Assembly.GetExecutingAssembly().Location, typeof(NativeClubSelectionWorker).FullName);
            worker.Run(Path.GetFullPath(args[0]), Path.GetFullPath(args[2]), args.Length == 4 ? Path.GetFullPath(args[3]) : null);
        }
        finally { AppDomain.Unload(domain); }
    }

    static string Csv(object value)
    {
        return "\"" + Convert.ToString(value).Replace("\"", "\"\"") + "\"";
    }

    internal static void Run(string source, string output, string corrections)
    {
        if (File.Exists(output)) throw new IOException("Refusing to overwrite snapshot: " + output);
        var type = typeof(FM08_Database_Editor);
        var flags = BindingFlags.NonPublic | BindingFlags.Static;
        var decompress = type.GetMethod("DecompressFile", flags);
        byte[] server = (byte[])decompress.Invoke(null, new object[] { Path.Combine(source, "server_db.dat") });
        byte[] people = (byte[])decompress.Invoke(null, new object[] { Path.Combine(source, "people_db.dat") });
        var clubs = (Dictionary<int, string>)type.GetMethod("ParseClubs", flags).Invoke(null, new object[] { server });
        FM08_Database_Editor.ResolveNativeU23ClubNames(server, BitConverter.ToInt32(people, 0), clubs);
        var records = FM08_Database_Editor.ParseNativeClubDivisions(server, BitConverter.ToInt32(people, 0));
        string digest;
        using (var hash = SHA256.Create())
            digest = BitConverter.ToString(hash.ComputeHash(File.ReadAllBytes(Path.Combine(source, "server_db.dat")))).Replace("-", "").ToLowerInvariant();
        if (corrections != null)
            ApplyVerifiedNames(corrections, digest, server, records, clubs);
        var rows = new List<string> {
            "ClubIndex,ClubUID,ClubName,CurrentDivisionIndex,PreviousDivisionIndex,EuropeanCompetitionIndex,RosterSize,SourceServerSHA256,NativeRecordStart,NativeRecordFooter,SecondaryDivisionIndex"
        };
        int missingNames = 0;
        foreach (var record in records.Values.OrderBy(record => record.ClubIndex))
        {
            string name;
            if (!clubs.TryGetValue(record.ClubIndex, out name)) { name = ""; missingNames++; }
            rows.Add(string.Join(",", new object[] {
                record.ClubIndex, BitConverter.ToInt32(server, record.Footer + 4), name,
                record.CurrentDivisionIndex, record.PreviousDivisionIndex,
                record.EuropeanCompetitionIndex, BitConverter.ToUInt16(server, record.RosterOffset), digest, record.Start, record.Footer, BitConverter.ToInt32(server, record.Start + 47)
            }.Select(Csv).ToArray()));
        }

        File.WriteAllLines(output, rows.ToArray(), new UTF8Encoding(false));
        Console.WriteLine("Exported structurally verified clubs: " + records.Count);
        Console.WriteLine("Names unavailable in legacy parser: " + missingNames + " (empty cells, not guessed)");
        Console.WriteLine("Source server SHA256: " + digest);
        Console.WriteLine(output);
    }

    static void ApplyVerifiedNames(string path, string digest, byte[] server,
        Dictionary<int, FM08_Database_Editor.NativeClubDivisionRecord> records, Dictionary<int, string> clubs)
    {
        var document = new XmlDocument { XmlResolver = null };
        document.Load(path);
        var root = document.DocumentElement;
        if (root == null || root.Name != "ClubNameCorrections" || root.GetAttribute("sourceServerSHA256") != digest)
            throw new InvalidDataException("Name correction profile does not match the source server.");
        var seen = new HashSet<int>();
        foreach (XmlNode node in root.ChildNodes)
        {
            var entry = node as XmlElement;
            if (entry == null) continue;
            if (entry.Name != "Club") throw new InvalidDataException("Unexpected name correction element.");
            int index = int.Parse(entry.GetAttribute("index"));
            int uid = int.Parse(entry.GetAttribute("uid"));
            int nameOffset = int.Parse(entry.GetAttribute("nameOffset"));
            int footer = int.Parse(entry.GetAttribute("treeFooterOffset"));
            int treeIndex = int.Parse(entry.GetAttribute("treeIndex"));
            string name = entry.GetAttribute("name");
            FM08_Database_Editor.NativeClubDivisionRecord record;
            if (!seen.Add(index) || !records.TryGetValue(index, out record) ||
                BitConverter.ToInt32(server, record.Footer + 4) != uid ||
                nameOffset < 13 || name.Length == 0 || nameOffset + (long)name.Length * 2 + 2 > server.Length ||
                footer < nameOffset + name.Length * 2 + 2 || footer + 13 > server.Length)
                throw new InvalidDataException("Invalid native name correction identity or bounds: " + index);
            byte[] marker = { 255, 0, 0, 108, 7, 0, 0, 0, 0 };
            if (!server.Skip(nameOffset - 13).Take(marker.Length).SequenceEqual(marker) ||
                BitConverter.ToInt32(server, nameOffset - 4) != name.Length ||
                Encoding.Unicode.GetString(server, nameOffset, name.Length * 2) != name ||
                BitConverter.ToUInt16(server, nameOffset + name.Length * 2) != 0 ||
                BitConverter.ToInt32(server, footer) != treeIndex ||
                BitConverter.ToInt32(server, footer + 4) != uid ||
                !server.Skip(footer + 8).Take(5).SequenceEqual(new byte[] { 0, 150, 0, 0, 0 }))
                throw new InvalidDataException("Serialized name evidence differs: " + index);
            string previous;
            if (clubs.TryGetValue(index, out previous) && previous != name)
                throw new InvalidDataException("Name correction conflicts with parsed name: " + index);
            clubs[index] = name;
        }
        Console.WriteLine("Verified UID-anchored name corrections: " + seen.Count);
    }
}

public sealed class NativeClubSelectionWorker : MarshalByRefObject
{
    public void Run(string source, string output, string corrections)
    {
        ExportNativeClubSelection.Run(source, output, corrections);
    }
}
