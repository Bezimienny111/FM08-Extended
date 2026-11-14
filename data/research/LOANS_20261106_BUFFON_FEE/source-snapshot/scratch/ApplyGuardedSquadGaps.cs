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

class ApplyGuardedSquadGaps
{
    static void Main(string[] args)
    {
        if (args.Length < 4 || args.Length > 5)
            throw new ArgumentException("Expected editor source new-output prepared-directory [--verify|--pilot=club,...]");
        string editor = Path.GetFullPath(args[0]);
        var domain = AppDomain.CreateDomain("GuardedSquadGaps", null,
            new AppDomainSetup { ApplicationBase = Path.GetDirectoryName(editor) });
        try
        {
            var worker = (VerifiedNativeSquadsWorker)domain.CreateInstanceFromAndUnwrap(
                Assembly.GetExecutingAssembly().Location, typeof(VerifiedNativeSquadsWorker).FullName);
            worker.GuardedSquadGaps(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]),
                Path.GetFullPath(args[3]), args.Length == 5 ? args[4] : "");
        }
        finally { AppDomain.Unload(domain); }
    }
}

public sealed partial class VerifiedNativeSquadsWorker
{
    static string GuardHash(string path)
    {
        using (var stream = File.OpenRead(path))
        using (var hash = SHA256.Create())
            return BitConverter.ToString(hash.ComputeHash(stream)).Replace("-", "");
    }

    static void GuardSource(string source, string prepared)
    {
        var pins = AbRows(Path.Combine(prepared, "source_hashes.csv"));
        var expected = new HashSet<string>(pins.Select(r => r["RelativePath"]), StringComparer.OrdinalIgnoreCase);
        var actual = new HashSet<string>(Directory.GetFiles(source, "*", SearchOption.AllDirectories)
            .Select(p => p.Substring(source.TrimEnd('\\').Length + 1)), StringComparer.OrdinalIgnoreCase);
        Require(expected.SetEquals(actual), "Accepted source file inventory changed.");
        foreach (var pin in pins)
            Require(GuardHash(Path.Combine(source, pin["RelativePath"])) == pin["SHA256"],
                "Accepted source hash changed: " + pin["RelativePath"]);
    }

    public void GuardedSquadGaps(string source, string output, string prepared, string option)
    {
        Require(option == "" || option == "--verify" || option.StartsWith("--pilot="), "Unknown guarded option.");
        Require(!source.Equals(output, StringComparison.OrdinalIgnoreCase) &&
            !output.StartsWith(source.TrimEnd('\\') + "\\", StringComparison.OrdinalIgnoreCase), "Unsafe output path.");
        GuardSource(source, prepared);
        var serializer = new JavaScriptSerializer { MaxJsonLength = int.MaxValue };
        var plan = serializer.Deserialize<Dictionary<string, object>>(
            File.ReadAllText(Path.Combine(prepared, "preparation-report.json"), Encoding.UTF8));
        Require((string)plan["status"] == "prepared_not_imported", "Prepared plan has unresolved blockers.");
        Require((string)plan["native_csv_sha256"] == GuardHash(Path.Combine(prepared, "native_players.csv")),
            "Prepared native CSV changed.");
        Require((string)plan["club_map_sha256"] == GuardHash(Path.Combine(prepared, "club_identity_map.csv")) &&
            (string)plan["source_hashes_csv_sha256"] == GuardHash(Path.Combine(prepared, "source_hashes.csv")),
            "Prepared identity map or source pins changed.");
        var rows = AbRows(Path.Combine(prepared, "native_players.csv"));
        var identities = AbRows(Path.Combine(prepared, "club_identity_map.csv"));
        if (option.StartsWith("--pilot="))
        {
            var selected = new HashSet<int>(option.Substring(8).Split(',').Select(int.Parse));
            Require(selected.Count >= 3, "Pilot requires at least three clubs.");
            rows = rows.Where(r => selected.Contains(int.Parse(r["ClubIndex"]))).ToList();
            identities = identities.Where(r => selected.Contains(int.Parse(r["club_index"]))).ToList();
            Require(identities.Count == selected.Count, "Unknown pilot club.");
        }
        else Require(identities.Count == 171, "Full import must cover the approved 171 clubs.");
        if (option == "--verify")
        {
            VerifyGuardedGaps(source, output, prepared, rows, identities);
            GuardSource(source, prepared);
            return;
        }
        Require(!Directory.Exists(output) && !File.Exists(output), "Guarded output already exists.");
        byte[] people = Load(source, "people_db.dat"), server = Load(source, "server_db.dat"),
            client = Load(source, "client_db.dat");
        var clubs = (Dictionary<int, string>)Call("ParseClubs", server);
        FM08_Database_Editor.ResolveNativeU23ClubNames(server, BitConverter.ToInt32(people, 0), clubs);
        var nations = (Dictionary<int, string>)Call("ParseNations", server);
        var records = FM08_Database_Editor.ParseNativeClubDivisions(server, BitConverter.ToInt32(people, 0));
        foreach (var identity in identities)
        {
            int club = int.Parse(identity["club_index"]);
            Require(records.ContainsKey(club) &&
                BitConverter.ToInt32(server, records[club].Footer + 4) == int.Parse(identity["club_uid"]) &&
                records[club].CurrentDivisionIndex == int.Parse(identity["target_division"]),
                "Target UID/division changed: " + club);
            if (!clubs.ContainsKey(club) || string.IsNullOrEmpty(clubs[club]))
            {
                Require(identity["name_evidence"] == "approved_membership_UID_display_alias",
                    "Unverified missing native display name: " + club);
                clubs[club] = identity["native_name"];
            }
            else Require(clubs[club] == identity["native_name"], "Native target name differs: " + club);
        }
        var players = ReadPlayers(people, server, clubs, nations);
        var byUid = players.ToDictionary(p => p.Id);
        var byPerson = players.ToDictionary(p => BitConverter.ToInt32(people, p.PersonOffset - 15));
        var targets = new HashSet<int>(identities.Select(r => int.Parse(r["club_index"])));
        Require(targets.SetEquals(rows.Select(r => int.Parse(r["ClubIndex"]))), "CSV target set differs from approved plan.");
        ValidateTargetOwnerRosters(people, server, players, targets, records);
        FM08_Database_Editor.ClubsRev.Clear();
        foreach (var club in clubs)
            if (!FM08_Database_Editor.ClubsRev.ContainsKey(club.Value))
                FM08_Database_Editor.ClubsRev.Add(club.Value, club.Key);
        Require(identities.Select(r => r["native_name"]).Distinct(StringComparer.OrdinalIgnoreCase).Count() ==
            identities.Count, "Target display names are ambiguous; cannot use the name-based assignment helper.");
        foreach (var identity in identities)
            FM08_Database_Editor.ClubsRev[identity["native_name"]] = int.Parse(identity["club_index"]);
        FM08_Database_Editor.NationsRev.Clear();
        foreach (var nation in nations)
            if (!FM08_Database_Editor.NationsRev.ContainsKey(nation.Value))
                FM08_Database_Editor.NationsRev.Add(nation.Value, nation.Key);
        FM08_Database_Editor.InitCsvRegistry();
        var reused = new HashSet<int>();
        var keys = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var row in rows)
        {
            int club = int.Parse(row["ClubIndex"]), uid = int.Parse(row["ExistingID"]);
            Require(clubs[club] == row["Club"] && nations.Values.Contains(row["Nationality"]), "Invalid club/nation.");
            Require(keys.Add(row["FirstName"] + "|" + row["LastName"] + "|" + row["BirthDate"]), "Duplicate incoming identity.");
            SetProfile(new Player(), row);
            if (uid > 0)
            {
                Player old;
                Require(byUid.TryGetValue(uid, out old) && reused.Add(uid) &&
                    old.FirstName == row["FirstName"] && old.LastName == row["LastName"] &&
                    old.BirthDate.HasValue && old.BirthDate.Value.ToString("yyyy-MM-dd") == row["BirthDate"],
                    "Unverified reused identity: " + uid);
                foreach (var field in row.Where(f => !new[] {
                    "ExistingID", "ClubIndex", "Club", "SquadNumber", "BirthDate" }.Contains(f.Key)))
                    Require(Convert.ToString(Value(old, field.Key), CultureInfo.InvariantCulture) == field.Value,
                        "Existing profile must be preserved: " + uid + " / " + field.Key);
            }
            else Require(uid == -1, "Invalid new identity sentinel.");
        }
        foreach (int club in targets)
        {
            var squad = rows.Where(r => int.Parse(r["ClubIndex"]) == club).ToList();
            Require(squad.Count >= 17 && squad.Count <= 45 &&
                squad.Any(r => r["PosGK"] == "20") &&
                squad.Select(r => r["SquadNumber"]).Distinct().Count() == squad.Count, "Invalid squad: " + club);
        }
        var nonPlayers = targets.ToDictionary(c => c,
            c => new HashSet<int>(Roster(server, records[c]).Where(i => !byPerson.ContainsKey(i))));
        var departing = players.Where(p => p.ClubIdOffset > 0 &&
            targets.Contains(BitConverter.ToInt32(people, p.ClubIdOffset)) && !reused.Contains(p.Id)).ToList();
        Require(departing.All(p => p.Id < 1600000000), "Unaccounted protected modern player in target club.");
        var removeLoans = new HashSet<int>(departing.Concat(players.Where(p => reused.Contains(p.Id)))
            .Select(p => BitConverter.ToInt32(people, p.PersonOffset - 15)));
        foreach (var loan in FM08_Database_Editor.ParseNativeLoans(server, BitConverter.ToInt32(people, 0)))
            if (targets.Contains(loan.ClubId)) removeLoans.Add(loan.PersonIndex);
        server = FM08_Database_Editor.RemoveNativeLoans(server, BitConverter.ToInt32(people, 0), removeLoans);
        RetireHistoricalDepartures(ref people, ref server, players, departing);
        var incoming = new List<Player>();
        var added = new List<Player>();
        var targetByPlayer = new Dictionary<Player, int>();
        foreach (var row in rows)
        {
            int uid = int.Parse(row["ExistingID"]);
            Player player = uid > 0 ? byUid[uid] : new Player { Id = -1 };
            SetProfile(player, row);
            incoming.Add(player);
            targetByPlayer.Add(player, int.Parse(row["ClubIndex"]));
            if (uid < 0) added.Add(player);
            else WriteProfile(player, people);
        }
        FM08_Database_Editor.SyncClubAssignments(ref people, ref server, incoming.Where(p => p.Id > 0).ToList());
        var pool = new IdPool(1660000000, 1661000000, people, server, client);
        AppendBatch(ref people, ref server, ref client, added, players, targetByPlayer, pool);
        var rosters = targets.ToDictionary(c => c, c => new HashSet<int>(incoming
            .Where(p => targetByPlayer[p] == c).Select(p => BitConverter.ToInt32(people, p.PersonOffset - 15))));
        foreach (int club in targets) rosters[club].UnionWith(nonPlayers[club]);
        RewriteRosters(ref server, BitConverter.ToInt32(people, 0), rosters);
        pool.Verify(people, server, client);
        GuardSource(source, prepared);
        Directory.CreateDirectory(output);
        foreach (string path in Directory.GetFiles(source, "*", SearchOption.AllDirectories))
        {
            string relative = path.Substring(source.TrimEnd('\\').Length + 1);
            if (string.IsNullOrEmpty(Path.GetDirectoryName(relative)) &&
                Path.GetExtension(relative).Equals(".xml", StringComparison.OrdinalIgnoreCase)) continue;
            string destination = Path.Combine(output, relative);
            Directory.CreateDirectory(Path.GetDirectoryName(destination));
            File.Copy(path, destination);
        }
        foreach (var entry in new Dictionary<string, byte[]> {
            { "people_db.dat", people }, { "server_db.dat", server }, { "client_db.dat", client } })
            File.WriteAllBytes(Path.Combine(output, entry.Key), (byte[])Call("CompressFile", entry.Value,
                (byte[])Call("GetFileHeader", Path.Combine(source, entry.Key))));
        FM08_Database_Editor.WriteDatabaseMetadata(source, output);
        VerifyGuardedGaps(source, output, prepared, rows, identities);
        GuardSource(source, prepared);
    }

    void VerifyGuardedGaps(string source, string output, string prepared,
        List<Dictionary<string, string>> rows, List<Dictionary<string, string>> identities)
    {
        byte[] oldPeople = Load(source, "people_db.dat"), oldServer = Load(source, "server_db.dat");
        byte[] people = Load(output, "people_db.dat"), server = Load(output, "server_db.dat");
        var oldClubs = (Dictionary<int, string>)Call("ParseClubs", oldServer);
        var clubs = (Dictionary<int, string>)Call("ParseClubs", server);
        FM08_Database_Editor.ResolveNativeU23ClubNames(oldServer, BitConverter.ToInt32(oldPeople, 0), oldClubs);
        FM08_Database_Editor.ResolveNativeU23ClubNames(server, BitConverter.ToInt32(people, 0), clubs);
        foreach (var identity in identities.Where(r => r["name_evidence"] == "approved_membership_UID_display_alias"))
        {
            int club = int.Parse(identity["club_index"]);
            if (!oldClubs.ContainsKey(club) || string.IsNullOrEmpty(oldClubs[club])) oldClubs[club] = identity["native_name"];
            if (!clubs.ContainsKey(club) || string.IsNullOrEmpty(clubs[club])) clubs[club] = identity["native_name"];
        }
        var before = ReadPlayers(oldPeople, oldServer, oldClubs, (Dictionary<int, string>)Call("ParseNations", oldServer));
        var after = ReadPlayers(people, server, clubs, (Dictionary<int, string>)Call("ParseNations", server));
        var byUid = after.ToDictionary(p => p.Id);
        var byIdentity = after.GroupBy(p => p.FirstName + "|" + p.LastName + "|" +
            (p.BirthDate.HasValue ? p.BirthDate.Value.ToString("yyyy-MM-dd") : ""))
            .ToDictionary(g => g.Key, g => g.ToList());
        var targets = new HashSet<int>(identities.Select(r => int.Parse(r["club_index"])));
        var reused = new HashSet<int>(rows.Where(r => int.Parse(r["ExistingID"]) > 0).Select(r => int.Parse(r["ExistingID"])));
        var departing = before.Where(p => p.ClubIdOffset > 0 &&
            targets.Contains(BitConverter.ToInt32(oldPeople, p.ClubIdOffset)) && !reused.Contains(p.Id)).ToList();
        Require(departing.All(p => p.Id < 1600000000), "Unexpected modern retirement.");
        var oldRecords = FM08_Database_Editor.ParseNativeClubDivisions(oldServer, BitConverter.ToInt32(oldPeople, 0));
        var records = FM08_Database_Editor.ParseNativeClubDivisions(server, BitConverter.ToInt32(people, 0));
        var refs = FM08_Database_Editor.ResolveNativeClubContractReferences(server, BitConverter.ToInt32(people, 0), targets);
        var expectedRosters = targets.ToDictionary(c => c, c => new HashSet<int>());
        var beforePersons = new HashSet<int>(before.Select(p => BitConverter.ToInt32(oldPeople, p.PersonOffset - 15)));
        foreach (int club in targets)
            expectedRosters[club].UnionWith(Roster(oldServer, oldRecords[club]).Where(i => !beforePersons.Contains(i)));
        var retirements = FM08_Database_Editor.ParseRetirements(server);
        foreach (var row in rows)
        {
            int uid = int.Parse(row["ExistingID"]), club = int.Parse(row["ClubIndex"]);
            Player player;
            if (uid > 0)
            {
                Require(byUid.ContainsKey(uid), "Existing UID missing after reload.");
                player = byUid[uid];
            }
            else
            {
                string key = row["FirstName"] + "|" + row["LastName"] + "|" + row["BirthDate"];
                List<Player> matches;
                Require(byIdentity.TryGetValue(key, out matches), "New identity missing: " + key);
                matches = matches.Where(p => p.Id >= 1660000000 && p.Id < 1661000000).ToList();
                Require(matches.Count == 1, "New identity duplicated: " + key);
                player = matches[0];
            }
            Require(player.BirthDate.Value.ToString("yyyy-MM-dd") == row["BirthDate"], "Birth date differs.");
            foreach (var field in row.Where(f => !new[] { "ExistingID", "ClubIndex", "BirthDate" }.Contains(f.Key)))
                Require(Convert.ToString(Value(player, field.Key), CultureInfo.InvariantCulture) == field.Value,
                    "Reloaded field differs: " + player.Id + " / " + field.Key);
            int index = BitConverter.ToInt32(people, player.PersonOffset - 15);
            int contract = player.ClubIdOffset + 28;
            Require(player.ClubIdOffset > 0 && BitConverter.ToInt32(people, player.ClubIdOffset) == club &&
                people[contract - 1] == 1 && BitConverter.ToInt32(people, contract + 26) == index &&
                BitConverter.ToInt32(people, contract + 31) == refs[club] &&
                BitConverter.ToInt32(people, contract + 35) == player.WeeklyWage &&
                people[contract + 60] == player.SquadNumber &&
                BitConverter.ToUInt16(people, contract + 39) == 180 &&
                BitConverter.ToUInt16(people, contract + 41) == 2010 &&
                player.ContractExpires == new DateTime(2010, 6, 30) &&
                !retirements.ContainsKey(player.Id), "Reloaded primary contract/retirement differs: " + player.Id);
            expectedRosters[club].Add(index);
        }
        int added = rows.Count - reused.Count;
        for (int i = 0; i < 3; i++)
            Require(BitConverter.ToInt32(people, i * 4) == BitConverter.ToInt32(oldPeople, i * 4) + added,
                "Native table count mismatch.");
        var removedIndices = new HashSet<int>(departing.Concat(before.Where(p => reused.Contains(p.Id)))
            .Select(p => BitConverter.ToInt32(oldPeople, p.PersonOffset - 15)));
        Require(records.Count == oldRecords.Count, "Club count changed.");
        foreach (var old in oldRecords.Values)
        {
            var current = records[old.ClubIndex];
            Require(old.CurrentDivisionIndex == current.CurrentDivisionIndex &&
                old.PreviousDivisionIndex == current.PreviousDivisionIndex &&
                old.EuropeanCompetitionIndex == current.EuropeanCompetitionIndex, "Competition assignment changed.");
            if (targets.Contains(old.ClubIndex))
            {
                Require(Roster(server, current).SetEquals(expectedRosters[old.ClubIndex]), "Target roster differs.");
                int oldEnd = old.RosterOffset + 2 + BitConverter.ToUInt16(oldServer, old.RosterOffset) * 4;
                int end = current.RosterOffset + 2 + BitConverter.ToUInt16(server, current.RosterOffset) * 4;
                EqualRange(oldServer, old.Start, server, current.Start, old.RosterOffset - old.Start, "target prefix");
                EqualRange(oldServer, oldEnd, server, end, old.Footer + 8 - oldEnd, "target suffix");
            }
            else VerifyClubAfterRelease(oldServer, server, old, current, removedIndices);
        }
        VerifyRetiredPlayers(oldPeople, oldServer, people, server, departing, after);
        var oldRetirements = FM08_Database_Editor.ParseRetirements(oldServer);
        var departureIds = new HashSet<int>(departing.Select(p => p.Id));
        foreach (var entry in oldRetirements)
            Require(retirements.ContainsKey(entry.Key) && retirements[entry.Key] == entry.Value, "Earlier retirement changed.");
        Require(retirements.Count == oldRetirements.Count + departing.Count(p => !oldRetirements.ContainsKey(p.Id)),
            "Unexpected retirement additions.");
        int oldAttributes = AttributesStart(oldPeople), attributes = AttributesStart(people);
        int oldPersonalities = oldAttributes - 8 - BitConverter.ToInt32(oldPeople, 4) * 17;
        int personalities = attributes - 8 - BitConverter.ToInt32(people, 4) * 17;
        EqualRange(oldPeople, oldAttributes, people, attributes, BitConverter.ToInt32(oldPeople, 8) * 89,
            "ALL existing attributes, including reused players");
        EqualRange(oldPeople, oldPersonalities + 4, people, personalities + 4,
            BitConverter.ToInt32(oldPeople, 4) * 17, "ALL existing personalities");
        var modified = new HashSet<int>(departureIds.Concat(reused));
        int oldCursor = 16, cursor = 16;
        foreach (var old in before.Where(p => modified.Contains(p.Id)).OrderBy(p => p.PersonOffset))
        {
            var current = byUid[old.Id];
            int oldStart = old.PersonOffset - 15, start = current.PersonOffset - 15;
            Require(oldStart - oldCursor == start - cursor, "Unrelated PERSON gap size changed.");
            EqualRange(oldPeople, oldCursor, people, cursor, oldStart - oldCursor, "protected PERSON gap");
            oldCursor = PersonEnd(oldPeople, old);
            cursor = PersonEnd(people, current);
        }
        Require(oldPersonalities - oldCursor == personalities - added * 299 - cursor, "PERSON suffix size changed.");
        EqualRange(oldPeople, oldCursor, people, cursor, oldPersonalities - oldCursor, "protected PERSON suffix");
        int oldEndPeople = oldAttributes + BitConverter.ToInt32(oldPeople, 8) * 89;
        int endPeople = attributes + BitConverter.ToInt32(people, 8) * 89;
        Require(oldPeople.Length - oldEndPeople == people.Length - endPeople, "People suffix size changed.");
        EqualRange(oldPeople, oldEndPeople, people, endPeople, oldPeople.Length - oldEndPeople, "people suffix");
        var oldLoans = FM08_Database_Editor.ParseNativeLoans(oldServer, BitConverter.ToInt32(oldPeople, 0));
        var removedLoans = new HashSet<int>(removedIndices);
        foreach (var loan in oldLoans) if (targets.Contains(loan.ClubId)) removedLoans.Add(loan.PersonIndex);
        var expectedLoans = oldLoans.Where(l => !removedLoans.Contains(l.PersonIndex)).Select(l => l.PersonIndex + "|" + l.ClubId).OrderBy(s => s);
        var actualLoans = FM08_Database_Editor.ParseNativeLoans(server, BitConverter.ToInt32(people, 0))
            .Select(l => l.PersonIndex + "|" + l.ClubId).OrderBy(s => s);
        Require(expectedLoans.SequenceEqual(actualLoans), "Unrelated loan changed.");
        foreach (string path in Directory.GetFiles(source, "*", SearchOption.AllDirectories))
        {
            string relative = path.Substring(source.TrimEnd('\\').Length + 1);
            if (new[] { "people_db.dat", "server_db.dat", "client_db.dat" }.Contains(relative) ||
                (string.IsNullOrEmpty(Path.GetDirectoryName(relative)) &&
                 Path.GetExtension(relative).Equals(".xml", StringComparison.OrdinalIgnoreCase))) continue;
            Require(GuardHash(path) == GuardHash(Path.Combine(output, relative)), "Protected file changed: " + relative);
        }
        var report = new {
            status = "native_verified_not_SI_or_game_tested", clubs = targets.Count, players = rows.Count,
            created = added, reused = reused.Count, retired_historical = departing.Count,
            existing_attributes_and_personalities = "all bytes preserved",
            protected_clubs = "preserved except explicitly approved outgoing identities",
            nonplayer_target_roster_entries = expectedRosters.Sum(e => e.Value.Count) - rows.Count,
            source = source, output = output, input_sha256 = GuardHash(Path.Combine(prepared, "native_players.csv"))
        };
        File.WriteAllText(Path.Combine(prepared, Path.GetFileName(output) + "-verification.json"),
            new JavaScriptSerializer().Serialize(report), new UTF8Encoding(false));
        Console.WriteLine(new JavaScriptSerializer().Serialize(report));
    }
}
