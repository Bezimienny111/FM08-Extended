using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using Player = FM08_Database_Editor.PlayerRecord;

public sealed partial class VerifiedNativeSquadsWorker
{
    public void ImportWonderkids(string source, string output, string csvPath, bool verifyOnly)
    {
        var rows = AbRows(csvPath);
        if (verifyOnly) { VerifyWonderkids(source, output, rows); return; }

        Require(!Directory.Exists(output) && !File.Exists(output), "Wonderkids output already exists: " + output);
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
        var byPerson = players.ToDictionary(p => BitConverter.ToInt32(people, p.PersonOffset - 15));
        var byId = players.ToDictionary(p => p.Id);
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

        // 1. Apply PA Boosts to existing wonderkids
        string boostCsvPath = Path.Combine(Path.GetDirectoryName(csvPath), "pa_boosts.csv");
        int boostCount = 0;
        if (File.Exists(boostCsvPath))
        {
            var boostRows = AbRows(boostCsvPath);
            foreach (var b in boostRows)
            {
                int uid = int.Parse(b["UID"]);
                short targetPa = short.Parse(b["TargetPA"]);

                if (byId.ContainsKey(uid))
                {
                    var p = byId[uid];
                    int paOffset = p.PersonOffset - 2;
                    people[paOffset] = (byte)(targetPa & 0xFF);
                    people[paOffset + 1] = (byte)((targetPa >> 8) & 0xFF);
                    p.PA = targetPa;
                    boostCount++;
                }
            }
            Console.WriteLine(string.Format("PASS: Successfully boosted PA for {0} existing modern wonderkids in people_db.dat.", boostCount));
        }

        // 2. Prepare incoming 398 new wonderkids
        var targets = new HashSet<int>(rows.Select(r => int.Parse(r["ClubIndex"])));
        Console.WriteLine(string.Format("Incoming Wonderkids: {0} players across {1} clubs.", rows.Count, targets.Count));

        var incoming = new List<Player>();
        var newPlayers = new List<Player>();
        var targetByPlayer = new Dictionary<Player, int>();
        var keys = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var row in rows)
        {
            int club = int.Parse(row["ClubIndex"]);
            Require(clubs.ContainsKey(club), "Brak klubu w słowniku clubs dla index=" + club + " (" + row["LastName"] + ")");
            Require(nations.Values.Contains(row["Nationality"]), "Unverified nationality for " + row["LastName"] + ": " + row["Nationality"]);
            Require(keys.Add(row["FirstName"] + "|" + row["LastName"] + "|" + row["BirthDate"]), "Duplicate incoming identity: " + row["LastName"]);

            Player player = new Player();
            incoming.Add(player);
            targetByPlayer[player] = club;
            newPlayers.Add(player);
        }

        for (int i = 0; i < incoming.Count; i++) SetProfile(incoming[i], rows[i]);

        // Capture existing rosters of target clubs so we add to them rather than replacing
        var existingRosters = targets.ToDictionary(c => c, c => new HashSet<int>(Roster(server, records[c])));

        // 3. Append modern wonderkids using pool 1657000000 - 1658000000
        var pool = new IdPool(1657000000, 1658000000, people, server, client);
        AppendBatch(ref people, ref server, ref client, newPlayers, players, targetByPlayer, pool);

        // 4. Update rosters: existing + new wonderkids
        var finalRosters = new Dictionary<int, HashSet<int>>();
        foreach (int club in targets)
        {
            var roster = new HashSet<int>(existingRosters[club]);
            var newPlayerIndices = incoming.Where(p => targetByPlayer[p] == club)
                .Select(p => BitConverter.ToInt32(people, p.PersonOffset - 15));
            roster.UnionWith(newPlayerIndices);
            finalRosters[club] = roster;
        }

        RewriteRosters(ref server, BitConverter.ToInt32(people, 0), finalRosters);

        pool.Verify(people, server, client);
        Console.WriteLine("PASS: Wonderkids bulk native records and collision-free identities in 1657000000 range.");

        // Restore all cancelled retirement decisions (flip flag back to 1)
        byte[] sig = new byte[] { 0x24, 0x00, 0xD8, 0x07, 0x6D, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF };
        int sigPos = -1;
        for (int i = 0x01DA0000; i <= server.Length - sig.Length; i++)
        {
            bool match = true;
            for (int j = 0; j < sig.Length; j++) if (server[i + j] != sig[j]) { match = false; break; }
            if (match) { sigPos = i; break; }
        }
        if (sigPos >= 0)
        {
            int countPos = sigPos + sig.Length;
            int retCount = BitConverter.ToInt32(server, countPos);
            int startPos = countPos + 5;
            int restoredRetirements = 0;
            for (int i = 0; i < retCount; i++)
            {
                int off = startPos + i * 18;
                if (server[off + 8] == 0)
                {
                    server[off + 8] = 0x01;
                    restoredRetirements++;
                }
            }
            Console.WriteLine(string.Format("PASS: Restored {0} cancelled retirement decisions in server_db.dat (total active: {1}).",
                restoredRetirements, retCount));
        }

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
        VerifyWonderkids(source, output, rows);
        Console.WriteLine("Published Wonderkids Overhaul database: " + output);
    }

    public void VerifyWonderkids(string source, string output, List<Dictionary<string, string>> rows)
    {
        byte[] oldPeople = Load(source, "people_db.dat"), oldServer = Load(source, "server_db.dat");
        byte[] people = Load(output, "people_db.dat"), server = Load(output, "server_db.dat");

        var oldClubs = (Dictionary<int, string>)Call("ParseClubs", oldServer);
        var clubs = (Dictionary<int, string>)Call("ParseClubs", server);
        FM08_Database_Editor.ResolveNativeU23ClubNames(server, BitConverter.ToInt32(people, 0), clubs);

        var before = ReadPlayers(oldPeople, oldServer, oldClubs, (Dictionary<int, string>)Call("ParseNations", oldServer));
        var after = ReadPlayers(people, server, clubs, (Dictionary<int, string>)Call("ParseNations", server));

        var byIdentity = after.GroupBy(p => p.FirstName + "|" + p.LastName + "|" +
            (p.BirthDate.HasValue ? p.BirthDate.Value.ToString("yyyy-MM-dd") : ""), StringComparer.OrdinalIgnoreCase)
            .ToDictionary(g => g.Key, g => g.ToList(), StringComparer.OrdinalIgnoreCase);

        var targets = new HashSet<int>(rows.Select(r => int.Parse(r["ClubIndex"])));
        var contractReferences = FM08_Database_Editor.ResolveNativeClubContractReferences(
            server, BitConverter.ToInt32(people, 0), targets);

        var records = FM08_Database_Editor.ParseNativeClubDivisions(server, BitConverter.ToInt32(people, 0));

        // Verify protected previous imports (29,061 modern players)
        int previousModernCount = after.Count(p => p.Id >= 1600000000 && p.Id < 1657000000);
        Require(previousModernCount == 29061, "Protected previous modern profiles modified: " + previousModernCount + " (expected 29061)");

        // Verify the 382 PA boosts
        string boostCsvPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, @"..\data\imports\WONDERKIDS_EXPANSION_2627_V20\pa_boosts.csv");
        if (!File.Exists(boostCsvPath)) boostCsvPath = @"D:\Gry\FM08\FMExt\data\imports\WONDERKIDS_EXPANSION_2627_V20\pa_boosts.csv";
        if (File.Exists(boostCsvPath))
        {
            var boostRows = AbRows(boostCsvPath);
            int verifiedBoosts = 0;
            foreach (var b in boostRows)
            {
                int uid = int.Parse(b["UID"]);
                short targetPa = short.Parse(b["TargetPA"]);
                var bp = after.FirstOrDefault(p => p.Id == uid);
                if (bp != null)
                {
                    Require(bp.PA >= targetPa, string.Format("Player UID {0} ({1} {2}) PA {3} is lower than target {4}", uid, bp.FirstName, bp.LastName, bp.PA, targetPa));
                    verifiedBoosts++;
                }
            }
            Console.WriteLine(string.Format("PASS: Verified PA boosts for {0} modern players.", verifiedBoosts));
        }

        foreach (var row in rows)
        {
            string key = row["FirstName"] + "|" + row["LastName"] + "|" + row["BirthDate"];
            List<Player> matches;
            Require(byIdentity.TryGetValue(key, out matches), "Wonderkid identity missing: " + key);
            Player player = matches.FirstOrDefault(p => p.Id >= 1657000000 && p.Id < 1658000000);
            Require(player != null, "Player ID outside Wonderkids range for " + key);
            int targetClub = int.Parse(row["ClubIndex"]);

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
            Require(player.Determination == int.Parse(row["Determination"]), "Determination mismatch for " + key);

            var roster = Roster(server, records[targetClub]);
            Require(roster.Contains(personIndex), "Player missing from target roster: " + key);
        }

        // Verify active retirements
        byte[] sig = new byte[] { 0x24, 0x00, 0xD8, 0x07, 0x6D, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF };
        int sigPos = -1;
        for (int i = 0x01DA0000; i <= server.Length - sig.Length; i++)
        {
            bool match = true;
            for (int j = 0; j < sig.Length; j++) if (server[i + j] != sig[j]) { match = false; break; }
            if (match) { sigPos = i; break; }
        }
        if (sigPos >= 0)
        {
            int countPos = sigPos + sig.Length;
            int retCount = BitConverter.ToInt32(server, countPos);
            int startPos = countPos + 5;
            int inactRetirements = 0;
            for (int i = 0; i < retCount; i++)
            {
                int off = startPos + i * 18;
                if (server[off + 8] == 0) inactRetirements++;
            }
            Require(inactRetirements == 0, "Found inactive retirement decisions: " + inactRetirements);
            Console.WriteLine(string.Format("PASS: Verified 100% active retirement table ({0} active legacy retirements, 0 inactive).", retCount));
        }

        Console.WriteLine("PASS: Wonderkids verification of " + rows.Count + " new profiles across " + targets.Count + " clubs, all contracts and PA boosts verified.");
    }
}
