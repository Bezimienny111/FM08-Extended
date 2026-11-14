using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Web.Script.Serialization;
using Player = FM08_Database_Editor.PlayerRecord;

class RepairPolandU17Assignments
{
    static void Main(string[] args)
    {
        if (args.Length != 4 && args.Length != 5)
            throw new ArgumentException("Expected editor source new-output batch [--verify|--pilot]");
        string editor = Path.GetFullPath(args[0]);
        var domain = AppDomain.CreateDomain("PolandU17Repair", null,
            new AppDomainSetup { ApplicationBase = Path.GetDirectoryName(editor) });
        try
        {
            var worker = (VerifiedNativeSquadsWorker)domain.CreateInstanceFromAndUnwrap(
                Assembly.GetExecutingAssembly().Location, typeof(VerifiedNativeSquadsWorker).FullName);
            worker.RepairPolandU17(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]),
                Path.GetFullPath(args[3]), args.Length == 5 ? args[4] : "");
        }
        finally { AppDomain.Unload(domain); }
    }
}

public sealed partial class VerifiedNativeSquadsWorker
{
    static readonly JavaScriptSerializer RepairJson = new JavaScriptSerializer { MaxJsonLength = int.MaxValue };
    static readonly int[] RetiredPolandUids = { 1646004782, 1646004800 };

    static string RepairHash(string path)
    {
        using (var stream = File.OpenRead(path))
        using (var sha = SHA256.Create())
            return BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", "");
    }

    static Dictionary<string, object> RepairObject(string path)
    {
        return RepairJson.Deserialize<Dictionary<string, object>>(File.ReadAllText(path, Encoding.UTF8));
    }

    static void CheckRepairSource(string source, string batch)
    {
        var manifest = RepairObject(Path.Combine(batch, "manifest.json"));
        Require((string)manifest["source_db"] == source, "Repair source differs from manifest.");
        var pins = (Dictionary<string, object>)manifest["source_hashes"];
        var files = Directory.GetFiles(source, "*", SearchOption.AllDirectories)
            .Select(p => p.Substring(source.TrimEnd('\\').Length + 1)).ToList();
        Require(new HashSet<string>(files).SetEquals(pins.Keys), "Source inventory changed.");
        foreach (var pin in pins)
            Require(RepairHash(Path.Combine(source, pin.Key)) == (string)pin.Value, "Source hash changed: " + pin.Key);
        var report = RepairObject(Path.Combine(batch, "preparation-report.json"));
        Require((string)report["status"] == "prepared_not_applied" &&
            (string)report["plan_sha256"] == RepairHash(Path.Combine(batch, "repair-plan.csv")) &&
            (string)report["manifest_sha256"] == RepairHash(Path.Combine(batch, "manifest.json")),
            "Repair plan or manifest changed.");
        var facts = (Dictionary<string, object>)report["source_facts_hashes"];
        foreach (var fact in facts)
            Require(RepairHash(Path.Combine(batch, "sources", fact.Key)) == (string)fact.Value, "Source fact changed.");
    }

    public void RepairPolandU17(string source, string output, string batch, string option)
    {
        Require(option == "" || option == "--verify" || option == "--pilot", "Unknown repair option.");
        Require(!source.Equals(output, StringComparison.OrdinalIgnoreCase) &&
            !output.StartsWith(source.TrimEnd('\\') + "\\", StringComparison.OrdinalIgnoreCase) &&
            !source.StartsWith(output.TrimEnd('\\') + "\\", StringComparison.OrdinalIgnoreCase),
            "Unsafe repair output path.");
        CheckRepairSource(source, batch);
        var rows = AbRows(Path.Combine(batch, "repair-plan.csv"));
        var approved = new HashSet<int>(Enumerable.Range(0, 21).Select(i => 1646004761 + i * 3)
            .Where(uid => uid != 1646004797));
        Require(rows.Count == 20 && approved.SetEquals(rows.Select(r => int.Parse(r["UID"]))),
            "Repair requires exactly the audited twenty UIDs, excluding Madej.");
        Require(rows.Where(r => r["Action"] == "retire").Select(r => int.Parse(r["UID"]))
            .OrderBy(i => i).SequenceEqual(RetiredPolandUids), "Retirement allowlist differs from approval.");
        if (option == "--pilot")
            rows = rows.Where(r => new[] { "1646004761", "1646004776", "1646004782" }.Contains(r["UID"])).ToList();
        if (option == "--verify")
        {
            VerifyPolandRepair(source, output, batch, rows);
            CheckRepairSource(source, batch);
            return;
        }
        Require(!Directory.Exists(output) && !File.Exists(output), "Repair output already exists.");
        byte[] people = Load(source, "people_db.dat"), server = Load(source, "server_db.dat");
        int count = BitConverter.ToInt32(people, 0);
        var clubs = (Dictionary<int, string>)Call("ParseClubs", server);
        FM08_Database_Editor.ResolveNativeU23ClubNames(server, count, clubs);
        var nations = (Dictionary<int, string>)Call("ParseNations", server);
        var records = FM08_Database_Editor.ParseNativeClubDivisions(server, count);
        var players = ReadPlayers(people, server, clubs, nations);
        var byUid = players.ToDictionary(p => p.Id);
        var retirement = FM08_Database_Editor.ParseRetirements(server);
        var touched = new HashSet<int>();
        FM08_Database_Editor.ClubsRev.Clear();
        foreach (var row in rows)
        {
            int uid = int.Parse(row["UID"]), target = int.Parse(row["TargetClubIndex"]);
            Player player;
            Require(byUid.TryGetValue(uid, out player), "Missing repair UID.");
            int start = player.PersonOffset - 15, person = BitConverter.ToInt32(people, start);
            Require(touched.Add(person) && player.FirstName == row["FirstName"] &&
                player.LastName == row["LastName"] && player.BirthDate.Value.ToString("yyyy-MM-dd") == row["BirthDate"] &&
                player.ClubId == 3853 && !retirement.ContainsKey(uid) &&
                PersonEnd(people, player) - start == 299 && player.ClubIdOffset == start + 171 &&
                BitConverter.ToInt32(people, start + 291) == person &&
                BitConverter.ToInt32(people, start + 295) == uid &&
                Roster(server, records[3853]).Contains(person), "Source identity/owner/layout mismatch: " + uid);
            if (row["Action"] == "retire")
            {
                Require(target == -1, "Retirement must release ownership.");
                continue;
            }
            Require(row["Action"] == "transfer" && target != 3853 && records.ContainsKey(target) &&
                BitConverter.ToInt32(server, records[target].Footer + 4) == int.Parse(row["TargetClubUID"]),
                "Unverified repair destination UID: " + uid);
            string name;
            if (clubs.TryGetValue(target, out name) && !string.IsNullOrEmpty(name))
                Require(name == row["TargetClub"], "Destination name conflict.");
            Require(!Roster(server, records[target]).Contains(person), "Person already in destination roster.");
            FM08_Database_Editor.ClubsRev[row["TargetClub"]] = target;
            player.Club = row["TargetClub"];
            player.ClubAssignmentPending = true;
            player.SquadNumber = byte.Parse(row["SquadNumber"], CultureInfo.InvariantCulture);
            Require(player.SquadNumber >= 1 && player.SquadNumber <= 99, "Invalid destination shirt number.");
            Require(!players.Any(p => p.ClubId == target && p.SquadNumber == player.SquadNumber),
                "Destination shirt number already occupied.");
            player.ContractDetailsPending = true;
        }
        Require(!FM08_Database_Editor.ParseNativeLoans(server, count).Any(l => touched.Contains(l.PersonIndex)),
            "Repair player has a loan; explicit handling is required.");
        FM08_Database_Editor.SyncClubAssignments(ref people, ref server, players);
        var retired = new HashSet<int>(rows.Where(r => r["Action"] == "retire").Select(r => int.Parse(r["UID"])));
        FM08_Database_Editor.RetireNativePlayersBulk(ref people, ref server, players, retired, new DateTime(2007, 7, 30));
        CheckRepairSource(source, batch);
        Directory.CreateDirectory(output);
        foreach (string path in Directory.GetFiles(source, "*", SearchOption.AllDirectories))
        {
            string relative = path.Substring(source.TrimEnd('\\').Length + 1);
            if (string.IsNullOrEmpty(Path.GetDirectoryName(relative)) && Path.GetExtension(relative) == ".xml") continue;
            string destination = Path.Combine(output, relative);
            Directory.CreateDirectory(Path.GetDirectoryName(destination));
            File.Copy(path, destination);
        }
        foreach (var entry in new Dictionary<string, byte[]> { { "people_db.dat", people }, { "server_db.dat", server } })
            File.WriteAllBytes(Path.Combine(output, entry.Key), (byte[])Call("CompressFile", entry.Value,
                (byte[])Call("GetFileHeader", Path.Combine(source, entry.Key))));
        FM08_Database_Editor.WriteDatabaseMetadata(source, output);
        VerifyPolandRepair(source, output, batch, rows);
        CheckRepairSource(source, batch);
    }

    sealed class RepairSpan
    {
        internal int Offset, Length;
        internal RepairSpan(int offset, int length) { Offset = offset; Length = length; }
    }

    static byte[] WithoutRepairSpans(byte[] bytes, IEnumerable<RepairSpan> spans)
    {
        using (var stream = new MemoryStream())
        {
            int cursor = 0;
            foreach (var span in spans.OrderBy(s => s.Offset))
            {
                Require(span.Offset >= cursor && span.Length >= 0 &&
                    span.Offset + (long)span.Length <= bytes.Length, "Overlapping/invalid verification ranges.");
                stream.Write(bytes, cursor, span.Offset - cursor);
                cursor = span.Offset + span.Length;
            }
            stream.Write(bytes, cursor, bytes.Length - cursor);
            return stream.ToArray();
        }
    }

    void VerifyPolandRepair(string source, string output, string batch, List<Dictionary<string, string>> rows)
    {
        byte[] oldPeople = Load(source, "people_db.dat"), oldServer = Load(source, "server_db.dat");
        byte[] people = Load(output, "people_db.dat"), server = Load(output, "server_db.dat");
        var oldClubs = (Dictionary<int, string>)Call("ParseClubs", oldServer);
        var clubs = (Dictionary<int, string>)Call("ParseClubs", server);
        var before = ReadPlayers(oldPeople, oldServer, oldClubs, (Dictionary<int, string>)Call("ParseNations", oldServer));
        var after = ReadPlayers(people, server, clubs, (Dictionary<int, string>)Call("ParseNations", server));
        Require(before.Count == after.Count && new HashSet<int>(before.Select(p => p.Id)).SetEquals(after.Select(p => p.Id)),
            "Player identity inventory changed.");
        var byUid = before.ToDictionary(p => p.Id);
        var afterUid = after.ToDictionary(p => p.Id);
        int count = BitConverter.ToInt32(people, 0);
        Require(count == BitConverter.ToInt32(oldPeople, 0), "PERSON count changed.");
        var oldRecords = FM08_Database_Editor.ParseNativeClubDivisions(oldServer, count);
        var records = FM08_Database_Editor.ParseNativeClubDivisions(server, count);
        Require(new HashSet<int>(oldRecords.Keys).SetEquals(records.Keys), "Club inventory changed.");
        var destinations = new HashSet<int>(rows.Where(r => r["Action"] == "transfer")
            .Select(r => int.Parse(r["TargetClubIndex"])));
        var references = FM08_Database_Editor.ResolveNativeClubContractReferences(oldServer, count, destinations);
        var desired = oldRecords.ToDictionary(r => r.Key, r => Roster(oldServer, r.Value));
        byte[] expectedPeople = (byte[])oldPeople.Clone();
        var removedContracts = new List<RepairSpan>();
        var evidence = new List<object>();
        foreach (var row in rows)
        {
            int uid = int.Parse(row["UID"]), target = int.Parse(row["TargetClubIndex"]);
            Player original = byUid[uid], current = afterUid[uid];
            int start = original.PersonOffset - 15, person = BitConverter.ToInt32(oldPeople, start);
            int owner = start + 171, contract = start + 199;
            Require(PersonEnd(oldPeople, original) - start == 299 && oldPeople[start + 4] == 2 &&
                oldPeople[start + 198] == 1 && original.ClubId == 3853, "Unsupported independent PERSON control.");
            BitConverter.GetBytes(target).CopyTo(expectedPeople, owner);
            Require(desired[3853].Remove(person), "Expected PSM membership missing.");
            if (target >= 0)
            {
                Require(BitConverter.ToInt32(oldServer, oldRecords[target].Footer + 4) ==
                    int.Parse(row["TargetClubUID"]), "Destination UID changed.");
                Require(desired[target].Add(person), "Duplicate destination membership.");
                BitConverter.GetBytes((ushort)181).CopyTo(expectedPeople, owner + 5);
                BitConverter.GetBytes((ushort)2007).CopyTo(expectedPeople, owner + 7);
                BitConverter.GetBytes(references[target]).CopyTo(expectedPeople, contract + 31);
                expectedPeople[contract + 60] = byte.Parse(row["SquadNumber"], CultureInfo.InvariantCulture);
                Require(current.ClubId == target && current.SquadNumber == int.Parse(row["SquadNumber"]) &&
                    current.WeeklyWage == original.WeeklyWage, "Reloaded transfer differs.");
            }
            else
            {
                Array.Clear(expectedPeople, owner + 5, 2);
                BitConverter.GetBytes((ushort)1900).CopyTo(expectedPeople, owner + 7);
                expectedPeople[owner + 27] = 0;
                removedContracts.Add(new RepairSpan(contract, 65));
                Require(current.ClubIdOffset == 0 && current.WeeklyWage == 0 && current.SquadNumber == 0 &&
                    !current.ContractExpires.HasValue, "Retired player retains club contract.");
            }
            Require(current.BirthDate == original.BirthDate && current.CA == original.CA && current.PA == original.PA,
                "DOB or ratings changed.");
            evidence.Add(new { uid, person, source_start = start, target, action = row["Action"],
                source_club = row["SourceClub"], dob_status = row["DOBStatus"],
                contract_reference = target >= 0 ? references[target] : -1,
                squad_number = int.Parse(row["SquadNumber"]) });
        }
        expectedPeople = WithoutRepairSpans(expectedPeople, removedContracts);
        Require(expectedPeople.Length == people.Length, "Unexpected PERSON size change.");
        EqualRange(expectedPeople, 0, people, 0, people.Length, "entire PERSON file outside approved owner/contracts");
        var oldSpans = new List<RepairSpan>();
        var newSpans = new List<RepairSpan>();
        foreach (int club in records.Keys)
        {
            var oldRecord = oldRecords[club];
            var record = records[club];
            Require(desired[club].SetEquals(Roster(server, record)), "Unexpected roster change: " + club);
            oldSpans.Add(new RepairSpan(oldRecord.RosterOffset, 2 + BitConverter.ToUInt16(oldServer, oldRecord.RosterOffset) * 4));
            newSpans.Add(new RepairSpan(record.RosterOffset, 2 + BitConverter.ToUInt16(server, record.RosterOffset) * 4));
        }
        foreach (int club in destinations)
        {
            var numbers = after.Where(p => p.ClubId == club && p.SquadNumber > 0 && p.SquadNumber < 100)
                .GroupBy(p => p.SquadNumber);
            Require(numbers.All(g => g.Count() == 1), "Duplicate destination shirt numbers.");
        }
        var retiredRows = rows.Where(r => r["Action"] == "retire").ToList();
        int oldTable = (int)Call("FindRetirementTable", oldServer), newTable = (int)Call("FindRetirementTable", server);
        Require(oldTable >= 0 && newTable >= 0, "Retirement table missing.");
        int oldCount = BitConverter.ToInt32(oldServer, oldTable + 12), newCount = BitConverter.ToInt32(server, newTable + 12);
        Require(newCount == oldCount + retiredRows.Count, "Unexpected retirement count.");
        EqualRange(oldServer, oldTable, server, newTable, 12, "retirement header");
        Require(oldServer[oldTable + 16] == server[newTable + 16], "Retirement flag changed.");
        EqualRange(oldServer, oldTable + 17, server, newTable + 17, oldCount * 18, "all prior retirement records");
        for (int i = 0; i < retiredRows.Count; i++)
        {
            int uid = int.Parse(retiredRows[i]["UID"]), offset = newTable + 17 + (oldCount + i) * 18;
            Require(BitConverter.ToInt32(server, offset) == uid &&
                BitConverter.ToUInt16(server, offset + 4) == 210 &&
                BitConverter.ToUInt16(server, offset + 6) == 2007 && server[offset + 8] == 1 &&
                BitConverter.ToInt32(server, offset + 9) == oldCount + i &&
                BitConverter.ToInt32(server, offset + 13) == -1 && server[offset + 17] == 0,
                "Incorrect technical retirement record.");
        }
        oldSpans.Add(new RepairSpan(oldTable, 17 + oldCount * 18));
        newSpans.Add(new RepairSpan(newTable, 17 + newCount * 18));
        var oldProtected = WithoutRepairSpans(oldServer, oldSpans);
        var newProtected = WithoutRepairSpans(server, newSpans);
        Require(oldProtected.Length == newProtected.Length, "Unrelated SERVER structure changed.");
        EqualRange(oldProtected, 0, newProtected, 0, oldProtected.Length, "all SERVER bytes except rosters and retirement table");
        foreach (string path in Directory.GetFiles(source, "*", SearchOption.AllDirectories))
        {
            string relative = path.Substring(source.TrimEnd('\\').Length + 1);
            if (new[] { "people_db.dat", "server_db.dat", "README.md" }.Contains(relative) ||
                (string.IsNullOrEmpty(Path.GetDirectoryName(relative)) && Path.GetExtension(relative) == ".xml")) continue;
            Require(RepairHash(path) == RepairHash(Path.Combine(output, relative)), "Protected file changed: " + relative);
        }
        string reportPath = Path.Combine(batch, Path.GetFileName(output) + "-verification.json");
        File.WriteAllText(reportPath, RepairJson.Serialize(new {
            status = "native_verified", source, output, players = rows.Count,
            transfers = rows.Count(r => r["Action"] == "transfer"), retirements = retiredRows.Count,
            all_person_bytes_checked = true, all_clubs_checked = records.Count,
            server_outside_rosters_and_retirements_identical = true,
            attributes_and_personality_identical = true,
            source_person_count = count, new_profiles = 0,
            si_acceptance = "not_tested", new_career_acceptance = "not_tested", evidence
        }) + Environment.NewLine, new UTF8Encoding(false));
        Console.WriteLine("Verified repair: " + rows.Count + " profiles; all PERSON bytes and " + records.Count + " clubs checked.");
    }
}
