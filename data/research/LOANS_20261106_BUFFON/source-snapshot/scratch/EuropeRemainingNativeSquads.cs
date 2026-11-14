using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using Player = FM08_Database_Editor.PlayerRecord;

public sealed partial class VerifiedNativeSquadsWorker
{
    public void ImportEuropeRemaining(string source, string output, string csvPath, bool verifyOnly)
    {
        var rows = AbRows(csvPath);
        if (verifyOnly) { VerifyEuropeRemaining(source, output, rows); return; }

        Require(!Directory.Exists(output) && !File.Exists(output), "Europe Remaining output already exists: " + output);
        Require(!output.StartsWith(source.TrimEnd('\\') + "\\", StringComparison.OrdinalIgnoreCase), "Output is inside source.");

        byte[] people = Load(source, "people_db.dat"), server = Load(source, "server_db.dat"), client = Load(source, "client_db.dat");
        int originalCount = BitConverter.ToInt32(people, 0);

        var clubs = (Dictionary<int, string>)Call("ParseClubs", server);
        FM08_Database_Editor.ResolveNativeU23ClubNames(server, originalCount, clubs);
        if (!clubs.ContainsKey(768) || string.IsNullOrEmpty(clubs[768])) clubs[768] = "Racing Club de Lens";
        if (!clubs.ContainsKey(1288) || string.IsNullOrEmpty(clubs[1288])) clubs[1288] = "Clube de Futebol Estrela da Amadora";
        if (!clubs.ContainsKey(15145) || string.IsNullOrEmpty(clubs[15145])) clubs[15145] = "SSV Jahn Regensburg";
        if (!clubs.ContainsKey(2989) || string.IsNullOrEmpty(clubs[2989])) clubs[2989] = "VfB Stuttgart II";
        if (!clubs.ContainsKey(1280) || string.IsNullOrEmpty(clubs[1280])) clubs[1280] = "Pogon Szczecin";
        if (!clubs.ContainsKey(1819)) clubs[1819] = "Celta Fortuna";
        if (!clubs.ContainsKey(1513)) clubs[1513] = "Real Sociedad B";
        if (!clubs.ContainsKey(512)) clubs[512] = "AFC Bournemouth";
        if (!clubs.ContainsKey(599)) clubs[599] = "Newcastle United";
        if (!clubs.ContainsKey(1459)) clubs[1459] = "U.D. Almería S.A.D.";

        var nations = (Dictionary<int, string>)Call("ParseNations", server);
        var players = ReadPlayers(people, server, clubs, nations);
        var byId = players.ToDictionary(p => p.Id);
        var byPerson = players.ToDictionary(p => BitConverter.ToInt32(people, p.PersonOffset - 15));
        var records = FM08_Database_Editor.ParseNativeClubDivisions(server, originalCount);

        FM08_Database_Editor.ClubsRev.Clear();
        foreach (var item in clubs)
            if (!FM08_Database_Editor.ClubsRev.ContainsKey(item.Value))
                FM08_Database_Editor.ClubsRev.Add(item.Value, item.Key);

        FM08_Database_Editor.NationsRev.Clear();
        foreach (var item in nations)
            if (!FM08_Database_Editor.NationsRev.ContainsKey(item.Value))
                FM08_Database_Editor.NationsRev.Add(item.Value, item.Key);

        FM08_Database_Editor.InitCsvRegistry();

        var targets = new HashSet<int>(rows.Select(r => int.Parse(r["ClubIndex"])));
        Console.WriteLine("Europe Remaining Import: Target clubs count = " + targets.Count + ", incoming players = " + rows.Count);
        ValidateTargetOwnerRosters(people, server, players, targets, records);

        var incoming = new List<Player>();
        var newPlayers = new List<Player>();
        var targetByPlayer = new Dictionary<Player, int>();
        var keys = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var row in rows)
        {
            int club = int.Parse(row["ClubIndex"]);
            if (!clubs.ContainsKey(club)) throw new KeyNotFoundException("Brak klubu w słowniku clubs dla index=" + club + " (" + row["LastName"] + ")");
            Require(clubs[club] == row["Club"] && nations.Values.Contains(row["Nationality"]), "Unverified club/nationality for " + row["LastName"]);
            Require(keys.Add(row["FirstName"] + "|" + row["LastName"] + "|" + row["BirthDate"]), "Duplicate incoming identity: " + row["LastName"]);

            Player player = new Player();
            incoming.Add(player);
            newPlayers.Add(player);
            targetByPlayer.Add(player, club);
        }

        var nonPlayersInRoster = targets.ToDictionary(t => t, t => new HashSet<int>());
        foreach (int club in targets)
        {
            foreach (int index in Roster(server, records[club]))
            {
                if (!byPerson.ContainsKey(index))
                {
                    nonPlayersInRoster[club].Add(index);
                }
            }
        }

        var departing = new List<Player>();
        var departingSet = new HashSet<int>();
        foreach (var player in players)
        {
            if (player.ClubIdOffset <= 0 || player.ClubIdOffset > people.Length - 4) continue;
            int owner = BitConverter.ToInt32(people, player.ClubIdOffset);
            if (targets.Contains(owner))
            {
                int index = BitConverter.ToInt32(people, player.PersonOffset - 15);
                if (departingSet.Add(index))
                {
                    departing.Add(player);
                }
            }
        }

        for (int i = 0; i < incoming.Count; i++) SetProfile(incoming[i], rows[i]);

        foreach (int club in targets)
        {
            var squad = incoming.Where(p => targetByPlayer[p] == club).ToList();
            Require(squad.Count >= 10 && squad.Count <= 45 && squad.Count(p => p.PosGK == 20) >= 1 &&
                squad.Select(p => p.SquadNumber).Distinct().Count() == squad.Count, "Incomplete squad for club index " + club + " (" + clubs[club] + "): count=" + squad.Count);
        }

        var retiredIndices = new HashSet<int>(departing.Select(p => BitConverter.ToInt32(people, p.PersonOffset - 15)));

        var removeLoans = new HashSet<int>(retiredIndices);
        foreach (var loan in FM08_Database_Editor.ParseNativeLoans(server, originalCount))
        {
            if (targets.Contains(loan.ClubId) && loan.PersonIndex >= 0 && loan.PersonIndex < originalCount)
                removeLoans.Add(loan.PersonIndex);
        }
        server = FM08_Database_Editor.RemoveNativeLoans(server, originalCount, removeLoans);

        RetireHistoricalDepartures(ref people, ref server, players, departing);

        FM08_Database_Editor.SyncClubAssignments(ref people, ref server, departing);

        var pool = new IdPool(1626000000, 1635000000, people, server, client);
        AppendBatch(ref people, ref server, ref client, newPlayers, players, targetByPlayer, pool);

        var finalRosters = targets.ToDictionary(c => c,
            c => new HashSet<int>(incoming.Where(p => targetByPlayer[p] == c).Select(p => BitConverter.ToInt32(people, p.PersonOffset - 15))));

        foreach (int club in targets)
        {
            finalRosters[club].UnionWith(nonPlayersInRoster[club]);
        }

        RewriteRosters(ref server, BitConverter.ToInt32(people, 0), finalRosters);

        pool.Verify(people, server, client);
        Console.WriteLine("PASS: Europe Remaining bulk native records and collision-free identities in 1626000000 range.");

        Directory.CreateDirectory(output);
        foreach (string path in Directory.GetFiles(source, "*", SearchOption.AllDirectories))
        {
            string relative = path.Substring(source.TrimEnd('\\').Length + 1);
            if (string.IsNullOrEmpty(Path.GetDirectoryName(relative)) && Path.GetExtension(relative).Equals(".xml", StringComparison.OrdinalIgnoreCase)) continue;
            string destination = Path.Combine(output, relative);
            Directory.CreateDirectory(Path.GetDirectoryName(destination));
            File.Copy(path, destination);
        }

        foreach (var entry in new Dictionary<string, byte[]> { { "people_db.dat", people }, { "server_db.dat", server }, { "client_db.dat", client } })
        {
            File.WriteAllBytes(Path.Combine(output, entry.Key), (byte[])Call("CompressFile", entry.Value,
                (byte[])Call("GetFileHeader", Path.Combine(source, entry.Key))));
        }

        FM08_Database_Editor.WriteDatabaseMetadata(source, output);
        VerifyEuropeRemaining(source, output, rows);
        Console.WriteLine("Published Europe Remaining database: " + output);
    }

    void VerifyEuropeRemaining(string source, string output, List<Dictionary<string, string>> rows)
    {
        byte[] oldPeople = Load(source, "people_db.dat"), oldServer = Load(source, "server_db.dat");
        byte[] people = Load(output, "people_db.dat"), server = Load(output, "server_db.dat");

        var oldClubs = (Dictionary<int, string>)Call("ParseClubs", oldServer);
        var clubs = (Dictionary<int, string>)Call("ParseClubs", server);
        FM08_Database_Editor.ResolveNativeU23ClubNames(server, BitConverter.ToInt32(people, 0), clubs);
        if (!clubs.ContainsKey(768) || string.IsNullOrEmpty(clubs[768])) clubs[768] = "Racing Club de Lens";
        if (!clubs.ContainsKey(1288) || string.IsNullOrEmpty(clubs[1288])) clubs[1288] = "Clube de Futebol Estrela da Amadora";
        if (!clubs.ContainsKey(15145) || string.IsNullOrEmpty(clubs[15145])) clubs[15145] = "SSV Jahn Regensburg";
        if (!clubs.ContainsKey(2989) || string.IsNullOrEmpty(clubs[2989])) clubs[2989] = "VfB Stuttgart II";
        if (!clubs.ContainsKey(1280) || string.IsNullOrEmpty(clubs[1280])) clubs[1280] = "Pogon Szczecin";
        if (!clubs.ContainsKey(1819)) clubs[1819] = "Celta Fortuna";
        if (!clubs.ContainsKey(1513)) clubs[1513] = "Real Sociedad B";
        if (!clubs.ContainsKey(512)) clubs[512] = "AFC Bournemouth";
        if (!clubs.ContainsKey(599)) clubs[599] = "Newcastle United";
        if (!clubs.ContainsKey(1459)) clubs[1459] = "U.D. Almería S.A.D.";

        var before = ReadPlayers(oldPeople, oldServer, oldClubs, (Dictionary<int, string>)Call("ParseNations", oldServer));
        var after = ReadPlayers(people, server, clubs, (Dictionary<int, string>)Call("ParseNations", server));

        var byId = after.ToDictionary(p => p.Id);
        var byIdentity = after.GroupBy(p => p.FirstName + "|" + p.LastName + "|" +
            (p.BirthDate.HasValue ? p.BirthDate.Value.ToString("yyyy-MM-dd") : ""), StringComparer.OrdinalIgnoreCase)
            .ToDictionary(g => g.Key, g => g.ToList(), StringComparer.OrdinalIgnoreCase);

        var targets = new HashSet<int>(rows.Select(r => int.Parse(r["ClubIndex"])));
        var contractReferences = FM08_Database_Editor.ResolveNativeClubContractReferences(
            server, BitConverter.ToInt32(people, 0), targets);
        VerifyHistoricalDepartures(oldPeople, oldServer, people, server, before, after, targets);

        var records = FM08_Database_Editor.ParseNativeClubDivisions(server, BitConverter.ToInt32(people, 0));
        var retirements = FM08_Database_Editor.ParseRetirements(server);

        // Verify protected previous imports are untouched (20,992 modern players)
        int previousModernCount = after.Count(p => p.Id >= 1600000000 && p.Id < 1625000000);
        Require(previousModernCount == 20992, "Protected previous modern profiles modified: " + previousModernCount);

        foreach (var row in rows)
        {
            string key = row["FirstName"] + "|" + row["LastName"] + "|" + row["BirthDate"];
            List<Player> matches;
            Require(byIdentity.TryGetValue(key, out matches), "Modern player identity missing: " + key);
            Player player = matches.FirstOrDefault(p => p.Id >= 1626000000 && p.Id < 1635000000);
            Require(player != null, "Player ID outside Europe Remaining range for " + key);
            int targetClub = int.Parse(row["ClubIndex"]);

            Require(player.Id >= 1626000000 && player.Id < 1635000000, "Player ID outside Europe Remaining range: " + player.Id);
            Require(player.ClubIdOffset > 0 && BitConverter.ToInt32(people, player.ClubIdOffset) == targetClub, "Wrong owner for " + key);
            Require(player.ContractExpires.HasValue && player.ContractExpires.Value.Year == 2010 && player.ContractExpires.Value.Month == 6 &&
                player.ContractExpires.Value.Day == 30, "Wrong expiry date for " + key);
            Require(player.WeeklyWage == int.Parse(row["WeeklyWage"]), "Wrong weekly wage for " + key);

            int personIndex = BitConverter.ToInt32(people, player.PersonOffset - 15);
            int contract = player.ClubIdOffset + 28;
            Require(people[contract - 1] == 1 && people[contract + 1] == 1, "Malformed contract header for " + key);
            int contractClubRef = BitConverter.ToInt32(people, contract + 31);
            Require(contractClubRef == contractReferences[targetClub], "Contract club reference mismatch for " + key + ": got " + contractClubRef + " expected " + contractReferences[targetClub]);
            Require(BitConverter.ToInt32(people, contract + 26) == personIndex, "Contract person index mismatch for " + key);

            Require(player.CA == int.Parse(row["CA"]) && player.PA == int.Parse(row["PA"]), "CA/PA mismatch for " + key);
            Require(player.PosGK == int.Parse(row["PosGK"]) && player.PosST == int.Parse(row["PosST"]), "Position mismatch for " + key);
            Require(player.Finishing == int.Parse(row["Finishing"]) && player.Reflexes == int.Parse(row["Reflexes"]), "Attribute mismatch for " + key);
            Require(player.Determination == int.Parse(row["Determination"]), "Determination mismatch for " + key);

            var roster = Roster(server, records[targetClub]);
            Require(roster.Contains(personIndex), "Player missing from target roster: " + key);
        }

        Console.WriteLine("PASS: Europe Remaining verification of " + rows.Count + " profiles across " + targets.Count + " clubs, all contracts and division assignments verified.");
    }
}
