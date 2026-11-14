using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using Player = FM08_Database_Editor.PlayerRecord;

public sealed partial class VerifiedNativeSquadsWorker
{
    static string ProfileKey(Player player)
    {
        return player.FirstName + "|" + player.LastName + "|" +
            (player.BirthDate.HasValue ? player.BirthDate.Value.ToString("yyyy-MM-dd") : "");
    }

    static string FileHash(string path)
    {
        using (var stream = File.OpenRead(path))
        using (var sha = SHA256.Create())
            return BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", "");
    }

    public void RepairContracts(string source, string output, string[] inputs)
    {
        Require(!Directory.Exists(output) && !File.Exists(output), "Repair output already exists.");
        Require(!output.StartsWith(source.TrimEnd('\\') + "\\", StringComparison.OrdinalIgnoreCase),
            "Repair output is inside source.");
        var hashes = Directory.GetFiles(source, "*", SearchOption.AllDirectories)
            .ToDictionary(p => p.Substring(source.TrimEnd('\\').Length + 1), FileHash);
        byte[] people = Load(source, "people_db.dat"), server = Load(source, "server_db.dat");
        var clubs = (Dictionary<int, string>)Call("ParseClubs", server);
        var nations = (Dictionary<int, string>)Call("ParseNations", server);
        var players = ReadPlayers(people, server, clubs, nations);
        var identities = players.GroupBy(ProfileKey, StringComparer.OrdinalIgnoreCase)
            .ToDictionary(g => g.Key, g => g.ToList(), StringComparer.OrdinalIgnoreCase);
        var retirements = FM08_Database_Editor.ParseRetirements(server);
        var selected = new List<Player>();
        foreach (string input in inputs)
        {
            string[] lines = File.ReadAllLines(input, Encoding.UTF8);
            string[] header = (string[])Call("ParseCsvLine", lines[0]);
            foreach (string line in lines.Skip(1))
            {
                string[] values = (string[])Call("ParseCsvLine", line);
                Require(values.Length == header.Length, "Invalid repair identity CSV.");
                var row = header.Select((h, i) => new { h, v = values[i] }).ToDictionary(e => e.h, e => e.v);
                string key = row["FirstName"] + "|" + row["LastName"] + "|" + row["BirthDate"];
                List<Player> matches;
                Require(identities.TryGetValue(key, out matches) && matches.Count == 1,
                    "Missing or ambiguous imported identity: " + key);
                Player player = matches[0];
                Require(player.Id >= 1600000000 && player.ClubIdOffset > 0 && !retirements.ContainsKey(player.Id),
                    "Repair identity is not an active owned modern player: " + key);
                if (row.ContainsKey("ExistingID") && int.Parse(row["ExistingID"]) > 0)
                    Require(player.Id == int.Parse(row["ExistingID"]), "Retained identity UID differs: " + key);
                Require(BitConverter.ToInt32(people, player.ClubIdOffset) == int.Parse(row["ClubIndex"]),
                    "Imported player's current owner differs: " + key);
                selected.Add(player);
            }
        }
        Require(selected.Count > 0 && selected.Select(p => p.Id).Distinct().Count() == selected.Count,
            "Missing or duplicated repair profiles.");
        var references = FM08_Database_Editor.ResolveNativeClubContractReferences(
            server, BitConverter.ToInt32(people, 0), selected.Select(p => p.ClubId));
        byte[] repaired = (byte[])people.Clone();
        var permitted = new HashSet<int>();
        var rows = new List<string> { "UID,FirstName,LastName,ClubIndex,PreviousContractClub,CorrectContractClub,Changed" };
        int changed = 0;
        foreach (Player player in selected)
        {
            int person = BitConverter.ToInt32(people, player.PersonOffset - 15);
            int footer = PersonEnd(people, player) - 8, contract = player.ClubIdOffset + 28;
            int payload = (int)Call("GetNativeClubContractOffset", people, contract, footer, person);
            Require(people[contract - 1] == 1 && payload >= 0, "Unsupported imported main contract: " + player.Id);
            int offset = payload + 31, before = BitConverter.ToInt32(people, offset), target = references[player.ClubId];
            for (int i = 0; i < 4; i++) Require(permitted.Add(offset + i), "Overlapping contract repair.");
            BitConverter.GetBytes(target).CopyTo(repaired, offset);
            if (before != target) changed++;
            rows.Add(string.Join(",", new object[] { player.Id, player.FirstName, player.LastName,
                player.ClubId, before, target, before != target }.Select(Csv)));
        }
        int bytesChanged = 0;
        for (int i = 0; i < people.Length; i++)
            if (people[i] != repaired[i])
            {
                Require(permitted.Contains(i), "Repair changed unrelated PERSON data.");
                bytesChanged++;
            }
        var reloaded = ReadPlayers(repaired, server, clubs, nations).ToDictionary(p => p.Id);
        foreach (Player player in selected)
        {
            Player actual = reloaded[player.Id];
            int payload = (int)Call("GetNativeClubContractOffset", repaired, actual.ClubIdOffset + 28,
                PersonEnd(repaired, actual) - 8, BitConverter.ToInt32(repaired, actual.PersonOffset - 15));
            Require(actual.ClubId == player.ClubId && actual.ContractExpires == player.ContractExpires &&
                actual.WeeklyWage == player.WeeklyWage && actual.SquadNumber == player.SquadNumber &&
                BitConverter.ToInt32(repaired, payload + 31) == references[player.ClubId],
                "Contract repair did not reparse correctly: " + player.Id);
        }
        foreach (var hash in hashes)
            Require(FileHash(Path.Combine(source, hash.Key)) == hash.Value, "Source changed during repair.");
        Directory.CreateDirectory(output);
        foreach (var hash in hashes)
        {
            string relative = hash.Key;
            if (relative == "people_db.dat" ||
                (string.IsNullOrEmpty(Path.GetDirectoryName(relative)) &&
                Path.GetExtension(relative).Equals(".xml", StringComparison.OrdinalIgnoreCase))) continue;
            string destination = Path.Combine(output, relative);
            Directory.CreateDirectory(Path.GetDirectoryName(destination));
            File.Copy(Path.Combine(source, relative), destination);
            Require(FileHash(destination) == hash.Value, "Copied source file differs: " + relative);
        }
        byte[] fileHeader = (byte[])Call("GetFileHeader", Path.Combine(source, "people_db.dat"));
        File.WriteAllBytes(Path.Combine(output, "people_db.dat"), (byte[])Call("CompressFile", repaired, fileHeader));
        byte[] persisted = Load(output, "people_db.dat");
        Require(persisted.Length == repaired.Length, "Persisted repair size differs.");
        EqualRange(repaired, 0, persisted, 0, repaired.Length, "persisted repaired PERSON table");
        FM08_Database_Editor.WriteDatabaseMetadata(source, output);
        foreach (var hash in hashes)
            Require(FileHash(Path.Combine(source, hash.Key)) == hash.Value, "Repair changed a source file.");
        File.WriteAllLines(Path.Combine(output, "contract_repair.csv"), rows, new UTF8Encoding(false));
        string report = "CONTRACT REFERENCES REPAIRED\nSource: " + source +
            "\nVerified imported profiles: " + selected.Count + "\nChanged contract references: " + changed +
            "\nAlready correct: " + (selected.Count - changed) + "\nChanged PERSON bytes: " + bytesChanged +
            "\nOnly the four-byte primary-contract club reference was eligible for modification." +
            "\nAll source file hashes were preserved. Other copied database files are byte-identical." +
            "\nServer, European cups, rosters, wages, dates, shirts, attributes and secondary contracts unchanged." +
            "\nEarlier import-summary files describe the old import, not this repair." +
            "\nReload verified with the native reader; official SI editor/game acceptance still requires testing.\n";
        File.WriteAllText(Path.Combine(output, "contract_repair_summary.txt"), report, new UTF8Encoding(false));
        Console.WriteLine(report + "Published: " + output);
    }
}
