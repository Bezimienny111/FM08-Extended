using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using Player = FM08_Database_Editor.PlayerRecord;

public sealed partial class VerifiedNativeSquadsWorker
{
    public void ImportEnglishPremierLeague(string source, string output, string csvPath, bool verifyOnly)
    {
        var rows = AbRows(csvPath);
        if (verifyOnly) { VerifyEnglish(source, output, rows); return; }

        Require(!Directory.Exists(output) && !File.Exists(output), "English output already exists.");
        Require(!output.StartsWith(source.TrimEnd('\\') + "\\", StringComparison.OrdinalIgnoreCase), "Output is inside source.");

        byte[] people = Load(source, "people_db.dat"), server = Load(source, "server_db.dat"), client = Load(source, "client_db.dat");
        int originalCount = BitConverter.ToInt32(people, 0);

        var clubs = (Dictionary<int, string>)Call("ParseClubs", server);
        FM08_Database_Editor.ResolveNativeU23ClubNames(server, originalCount, clubs);
        // Zapewnienie nazw dla licencyjnych klubów Premier League (AFC Bournemouth i Newcastle United):
        if (!clubs.ContainsKey(512)) clubs[512] = "AFC Bournemouth";
        if (!clubs.ContainsKey(599)) clubs[599] = "Newcastle United";
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
        Require(targets.Count == 20, "English Premier League batch must contain exactly 20 clubs.");
        ValidateTargetOwnerRosters(people, server, players, targets, records);

        var incoming = new List<Player>();
        var newPlayers = new List<Player>();
        var targetByPlayer = new Dictionary<Player, int>();
        var keys = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var row in rows)
        {
            int club = int.Parse(row["ClubIndex"]);
            if (!clubs.ContainsKey(club)) throw new KeyNotFoundException("Brak klubu w słowniku clubs dla index=" + club + " (zawodnik: " + row["LastName"] + ")");
            Require(clubs[club] == row["Club"] && nations.Values.Contains(row["Nationality"]), "Unverified club/nationality for " + row["LastName"]);
            Require(keys.Add(row["FirstName"] + "|" + row["LastName"] + "|" + row["BirthDate"]), "Duplicate incoming identity: " + row["LastName"]);

            Player player = new Player();
            incoming.Add(player);
            newPlayers.Add(player);
            targetByPlayer.Add(player, club);
        }

        var oldIndices = new HashSet<int>(targets.SelectMany(t => Roster(server, records[t])));
        var departing = new List<Player>();
        var nonPlayersInRoster = targets.ToDictionary(t => t, t => new HashSet<int>());

        foreach (int club in targets)
        {
            foreach (int index in Roster(server, records[club]))
            {
                Player player;
                if (!byPerson.TryGetValue(index, out player))
                {
                    // Non-player staff member in club roster - preserve them in the club
                    nonPlayersInRoster[club].Add(index);
                    continue;
                }
                if (!IsOwnedRosterPlayer(people, server, player, club, records)) continue;
                departing.Add(player);
            }
        }

        for (int i = 0; i < incoming.Count; i++) SetProfile(incoming[i], rows[i]);

        foreach (int club in targets)
        {
            var squad = incoming.Where(p => targetByPlayer[p] == club).ToList();
            Require(squad.Count >= 17 && squad.Count <= 45 && squad.Count(p => p.PosGK == 20) >= 1 &&
                squad.Select(p => p.SquadNumber).Distinct().Count() == squad.Count, "Incomplete Premier League squad for club index " + club);
        }

        var retiredIndices = new HashSet<int>(departing.Select(p => BitConverter.ToInt32(people, p.PersonOffset - 15)));

        var removeLoans = new HashSet<int>(retiredIndices);
        foreach (var loan in FM08_Database_Editor.ParseNativeLoans(server, originalCount))
        {
            if (targets.Contains(loan.ClubId)) removeLoans.Add(loan.PersonIndex);
        }
        server = FM08_Database_Editor.RemoveNativeLoans(server, originalCount, removeLoans);

        RetireHistoricalDepartures(ref people, ref server, players, departing);

        FM08_Database_Editor.SyncClubAssignments(ref people, ref server, players);

        // Pula identyfikatorów dla Premier League: 1602000000..1603000000
        var pool = new IdPool(1602000000, 1603000000, people, server, client);
        AppendBatch(ref people, ref server, ref client, newPlayers, players, targetByPlayer, pool);

        var finalRosters = targets.ToDictionary(c => c,
            c => new HashSet<int>(incoming.Where(p => targetByPlayer[p] == c).Select(p => BitConverter.ToInt32(people, p.PersonOffset - 15))));

        // Zachowaj sztabowców w ich macierzystych klubach
        foreach (int club in targets)
        {
            finalRosters[club].UnionWith(nonPlayersInRoster[club]);
        }


        RewriteRosters(ref server, BitConverter.ToInt32(people, 0), finalRosters);

        pool.Verify(people, server, client);
        Console.WriteLine("PASS: Premier League bulk native records and collision-free identities in 1602000000 range.");

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
        VerifyEnglish(source, output, rows);
        Console.WriteLine("Published Premier League database: " + output);
    }

    void VerifyEnglish(string source, string output, List<Dictionary<string, string>> rows)
    {
        byte[] oldPeople = Load(source, "people_db.dat"), oldServer = Load(source, "server_db.dat");
        byte[] people = Load(output, "people_db.dat"), server = Load(output, "server_db.dat");

        var oldClubs = (Dictionary<int, string>)Call("ParseClubs", oldServer);
        var clubs = (Dictionary<int, string>)Call("ParseClubs", server);
        FM08_Database_Editor.ResolveNativeU23ClubNames(server, BitConverter.ToInt32(people, 0), clubs);
        if (!clubs.ContainsKey(512)) clubs[512] = "AFC Bournemouth";
        if (!clubs.ContainsKey(599)) clubs[599] = "Newcastle United";

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

        // 1. Weryfikacja ochranianych Włochów
        var italianBefore = before.Where(p => p.Id >= 1601000000 && p.Id < 1602000000).ToList();
        Require(italianBefore.Count == 1103, "Expected 1103 protected Italian players with UID 1601xxxxxx, got " + italianBefore.Count);

        int italianAfter = after.Count(p => p.Id >= 1601000000 && p.Id < 1602000000);
        Require(italianAfter == 1103, "Protected Italian players count changed! Expected 1103, got " + italianAfter);

        foreach (var p in italianBefore)
        {
            Require(byId.ContainsKey(p.Id), "Protected Italian player UID=" + p.Id + " (" + p.FullName + ") missing!");
            Player afterP = byId[p.Id];
            Require(afterP.ClubId == p.ClubId, "Protected Italian player club changed: " + p.FullName + ", expected=" + p.ClubId + ", got=" + afterP.ClubId);
        }

        // Ochrona Carlo Pinsoglio (ID 43006598)
        Require(byId.ContainsKey(43006598), "Carlo Pinsoglio (ID 43006598) missing!");

        // 2. Weryfikacja każdego dodanego gracza Premier League
        foreach (var row in rows)
        {
            string key = row["FirstName"] + "|" + row["LastName"] + "|" + row["BirthDate"];
            List<Player> matches;
            Require(byIdentity.TryGetValue(key, out matches) && matches.Count == 1, "Modern English player identity missing: " + key);
            Player player = matches[0];
            int club = int.Parse(row["ClubIndex"]);

            Require(player.Id >= 1602000000 && player.Id < 1603000000,
                "Modern English player UID out of allocated 1602xxxxxx range: " + player.FullName + ", UID=" + player.Id);

            Require(player.ClubIdOffset > 0 && BitConverter.ToInt32(people, player.ClubIdOffset) == club,
                "Club assignment mismatch for " + player.FullName);

            int pIndex = BitConverter.ToInt32(people, player.PersonOffset - 15);
            int contract = player.ClubIdOffset + 28;

            Require(people[contract - 1] == 1 && people[contract + 1] == 1,
                "Malformed contract header for " + player.FullName);
            Require(BitConverter.ToInt32(people, contract + 31) == contractReferences[club],
                "Club contract reference mismatch in NAME-TREE for " + player.FullName);
            Require(BitConverter.ToInt32(people, contract + 26) == pIndex,
                "Contract person index mismatch for " + player.FullName);
            Require(!retirements.ContainsKey(player.Id),
                "Modern English player marked as retired: " + player.FullName);

            var squad = Roster(server, records[club]);
            Require(squad.Contains(pIndex), "Modern player not in club roster: " + player.FullName);
        }

        foreach (int club in targets)
        {
            var squad = Roster(server, records[club]);
            Require(squad.Count >= 17, "Roster count too low for club index " + club);
        }

        Console.WriteLine("VERIFIED: Premier League 20 clubs (" + rows.Count + " players in UID 1602xxxxxx range) and 1103 protected Italian players (UID 1601xxxxxx) 100% preserved.");
    }
}
