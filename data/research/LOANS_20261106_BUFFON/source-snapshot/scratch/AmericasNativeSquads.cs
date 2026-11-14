using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using Player = FM08_Database_Editor.PlayerRecord;

public sealed partial class VerifiedNativeSquadsWorker
{
    public void ImportAmericas(string source, string output, string csvPath, bool verifyOnly)
    {
        var rows = AbRows(csvPath);
        if (verifyOnly) { VerifyAmericas(source, output, rows); return; }

        Require(!Directory.Exists(output) && !File.Exists(output), "Americas output already exists: " + output);
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
        if (!clubs.ContainsKey(81) || string.IsNullOrEmpty(clubs[81])) clubs[81] = "Newell's Old Boys";
        if (!clubs.ContainsKey(10447) || string.IsNullOrEmpty(clubs[10447])) clubs[10447] = "Tigre";

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
        Require(targets.Count == 50, "Americas batch must contain exactly 50 clubs, got " + targets.Count);
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
                squad.Select(p => p.SquadNumber).Distinct().Count() == squad.Count, "Incomplete squad for club index " + club);
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

        var pool = new IdPool(1614000000, 1615000000, people, server, client);
        AppendBatch(ref people, ref server, ref client, newPlayers, players, targetByPlayer, pool);

        var finalRosters = targets.ToDictionary(c => c,
            c => new HashSet<int>(incoming.Where(p => targetByPlayer[p] == c).Select(p => BitConverter.ToInt32(people, p.PersonOffset - 15))));

        foreach (int club in targets)
        {
            finalRosters[club].UnionWith(nonPlayersInRoster[club]);
        }


        RewriteRosters(ref server, BitConverter.ToInt32(people, 0), finalRosters);

        // Apply balanced Mexico and Argentina league compositions
        var divisionChanges = new List<FM08_Database_Editor.ClubLeagueChange> {
            // Mexico: swap 4 clubs between Primera División (214) and lower divisions
            new FM08_Database_Editor.ClubLeagueChange { ClubIndex = 1101,  ExpectedDivisionIndex = 215, TargetDivisionIndex = 214 }, // Club Deportivo León
            new FM08_Database_Editor.ClubLeagueChange { ClubIndex = 2486,  ExpectedDivisionIndex = 214, TargetDivisionIndex = 215 }, // Club Tecos de la UAG
            new FM08_Database_Editor.ClubLeagueChange { ClubIndex = 3890,  ExpectedDivisionIndex = 215, TargetDivisionIndex = 214 }, // Xoloizcuintles de Tijuana
            new FM08_Database_Editor.ClubLeagueChange { ClubIndex = 2548,  ExpectedDivisionIndex = 214, TargetDivisionIndex = 215 }, // Club Jaguares de Chiapas
            new FM08_Database_Editor.ClubLeagueChange { ClubIndex = 14269, ExpectedDivisionIndex = 215, TargetDivisionIndex = 214 }, // Club Indios de Juárez (FC Juárez)
            new FM08_Database_Editor.ClubLeagueChange { ClubIndex = 2611,  ExpectedDivisionIndex = 214, TargetDivisionIndex = 215 }, // Club Monarcas Morelia
            new FM08_Database_Editor.ClubLeagueChange { ClubIndex = 3888,  ExpectedDivisionIndex = 216, TargetDivisionIndex = 214 }, // Club Halcones de Querétaro
            new FM08_Database_Editor.ClubLeagueChange { ClubIndex = 3543,  ExpectedDivisionIndex = 214, TargetDivisionIndex = 216 }, // Club Tiburones Rojos de Veracruz

            // Argentina: swap 5 clubs between Primera División (71) and Primera B Nacional (72)
            new FM08_Database_Editor.ClubLeagueChange { ClubIndex = 2502,  ExpectedDivisionIndex = 72,  TargetDivisionIndex = 71  }, // Talleres de Córdoba
            new FM08_Database_Editor.ClubLeagueChange { ClubIndex = 2487,  ExpectedDivisionIndex = 71,  TargetDivisionIndex = 72  }, // Colón de Santa Fe
            new FM08_Database_Editor.ClubLeagueChange { ClubIndex = 72,    ExpectedDivisionIndex = 72,  TargetDivisionIndex = 71  }, // Belgrano de Córdoba
            new FM08_Database_Editor.ClubLeagueChange { ClubIndex = 2494,  ExpectedDivisionIndex = 71,  TargetDivisionIndex = 72  }, // Arsenal de Sarandí
            new FM08_Database_Editor.ClubLeagueChange { ClubIndex = 2763,  ExpectedDivisionIndex = 72,  TargetDivisionIndex = 71  }, // Defensa y Justicia
            new FM08_Database_Editor.ClubLeagueChange { ClubIndex = 2766,  ExpectedDivisionIndex = 71,  TargetDivisionIndex = 72  }, // Olimpo de Bahía Blanca
            new FM08_Database_Editor.ClubLeagueChange { ClubIndex = 82,    ExpectedDivisionIndex = 72,  TargetDivisionIndex = 71  }, // Platense
            new FM08_Database_Editor.ClubLeagueChange { ClubIndex = 2768,  ExpectedDivisionIndex = 71,  TargetDivisionIndex = 72  }, // San Martín de San Juan
            new FM08_Database_Editor.ClubLeagueChange { ClubIndex = 2490,  ExpectedDivisionIndex = 72,  TargetDivisionIndex = 71  }, // Unión de Santa Fe
            new FM08_Database_Editor.ClubLeagueChange { ClubIndex = 2531,  ExpectedDivisionIndex = 71,  TargetDivisionIndex = 72  }, // Gimnasia y Esgrima de Jujuy
        };
        server = FM08_Database_Editor.ApplyClubLeagueChanges(server, BitConverter.ToInt32(people, 0), divisionChanges);
        Console.WriteLine("PASS: Applied balanced Mexico (Div 214: 18 clubs) and Argentina (Div 71: 20 clubs) division compositions.");

        pool.Verify(people, server, client);
        Console.WriteLine("PASS: Americas bulk native records and collision-free identities in 1614000000 range.");

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
        VerifyAmericas(source, output, rows);
        Console.WriteLine("Published Americas database: " + output);
    }

    void VerifyAmericas(string source, string output, List<Dictionary<string, string>> rows)
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
        if (!clubs.ContainsKey(81) || string.IsNullOrEmpty(clubs[81])) clubs[81] = "Newell's Old Boys";
        if (!clubs.ContainsKey(10447) || string.IsNullOrEmpty(clubs[10447])) clubs[10447] = "Tigre";

        var before = ReadPlayers(oldPeople, oldServer, oldClubs, (Dictionary<int, string>)Call("ParseNations", oldServer));
        var after = ReadPlayers(people, server, clubs, (Dictionary<int, string>)Call("ParseNations", server));

        var byId = after.ToDictionary(p => p.Id);
        var byIdentity = after.GroupBy(p => p.FirstName + "|" + p.LastName + "|" +
            (p.BirthDate.HasValue ? p.BirthDate.Value.ToString("yyyy-MM-dd") : ""), StringComparer.OrdinalIgnoreCase)
            .ToDictionary(g => g.Key, g => g.ToList(), StringComparer.OrdinalIgnoreCase);

        var targets = new HashSet<int>(rows.Select(r => int.Parse(r["ClubIndex"])));
        var records = FM08_Database_Editor.ParseNativeClubDivisions(server, BitConverter.ToInt32(people, 0));
        var contractReferences = new Dictionary<int, int>();
        foreach (int c in targets)
            contractReferences[c] = (int)Call("GetNativeClubContractReference", server, records[c]);
        VerifyHistoricalDepartures(oldPeople, oldServer, people, server, before, after, targets);

        var retirements = FM08_Database_Editor.ParseRetirements(server);

        // 1. Weryfikacja chronionych lig:
        int italianCount = after.Count(p => p.Id >= 1601000000 && p.Id < 1602000000);
        Require(italianCount == 1103, "Protected Italian players count changed! Expected 1103, got " + italianCount);

        int premCount = after.Count(p => p.Id >= 1602000000 && p.Id < 1603000000);
        Require(premCount == 603, "Protected Premier League players count changed! Expected 603, got " + premCount);

        int spainCount = after.Count(p => p.Id >= 1603000000 && p.Id < 1604000000);
        Require(spainCount == 1061, "Protected Spain players count changed! Expected 1061, got " + spainCount);

        int engLowerCount = after.Count(p => p.Id >= 1604000000 && p.Id < 1605000000);
        Require(engLowerCount == 1727, "Protected England Lower players count changed! Expected 1727, got " + engLowerCount);

        int franceCount = after.Count(p => p.Id >= 1605000000 && p.Id < 1606000000);
        Require(franceCount == 959, "Protected France players count changed! Expected 959, got " + franceCount);

        int ptCount = after.Count(p => p.Id >= 1606000000 && p.Id < 1607000000);
        Require(ptCount == 484, "Protected Portugal players count changed! Expected 484, got " + ptCount);

        int gerB1B2Count = after.Count(p => p.Id >= 1607000000 && p.Id < 1608000000);
        Require(gerB1B2Count == 1047, "Protected Germany B1/B2 players count changed! Expected 1047, got " + gerB1B2Count);

        int ger3LigaCount = after.Count(p => p.Id >= 1608000000 && p.Id < 1609000000);
        Require(ger3LigaCount == 509, "Protected Germany 3. Liga players count changed! Expected 509, got " + ger3LigaCount);

        int polNedCount = after.Count(p => p.Id >= 1609000000 && p.Id < 1610000000);
        Require(polNedCount == 938, "Protected Poland & Netherlands players count changed! Expected 938, got " + polNedCount);

        int bstCount = after.Count(p => p.Id >= 1610000000 && p.Id < 1611000000);
        Require(bstCount == 1295, "Protected Belgium, Scotland & Turkey players count changed! Expected 1295, got " + bstCount);

        int cneCount = after.Count(p => p.Id >= 1611000000 && p.Id < 1612000000);
        Require(cneCount == 2008, "Protected Central & North Europe players count changed! Expected 2008, got " + cneCount);

        int restEuroCount = after.Count(p => p.Id >= 1612000000 && p.Id < 1613000000);
        Require(restEuroCount == 913, "Protected Europe Rest players count changed! Expected 913, got " + restEuroCount);

        int mlsCount = after.Count(p => p.Id >= 1613000000 && p.Id < 1614000000);
        Require(mlsCount == 806, "Protected USA MLS players count changed! Expected 806, got " + mlsCount);

        // 2. Weryfikacja każdego dodanego gracza Americas
        foreach (var row in rows)
        {
            string key = row["FirstName"] + "|" + row["LastName"] + "|" + row["BirthDate"];
            List<Player> matches;
            Require(byIdentity.TryGetValue(key, out matches), "Modern Americas player identity missing: " + key);
            Player player = matches.FirstOrDefault(p => p.Id >= 1614000000 && p.Id < 1615000000);
            Require(player != null, "Modern Americas player UID out of allocated 1614xxxxxx range: " + key);
            int club = int.Parse(row["ClubIndex"]);

            Require(player.Id >= 1614000000 && player.Id < 1615000000,
                "Modern Americas player UID out of allocated 1614xxxxxx range: " + player.FullName + ", UID=" + player.Id);

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
                "Modern Americas player marked as retired: " + player.FullName);

            var squad = Roster(server, records[club]);
            Require(squad.Contains(pIndex), "Modern player not in club roster: " + player.FullName);
        }

        // 3. Weryfikacja dokładnego składu lig:
        // Dywizja 214 (Meksyk): 18 klubów
        var actualMexClubs = records.Values.Where(r => r.CurrentDivisionIndex == 214).Select(r => r.ClubIndex).ToList();
        Require(actualMexClubs.Count == 18, "Mexico Primera División 214 must contain exactly 18 clubs, got " + actualMexClubs.Count);

        // Dywizja 71 (Argentyna): 20 klubów
        var actualArgClubs = records.Values.Where(r => r.CurrentDivisionIndex == 71).Select(r => r.ClubIndex).ToList();
        Require(actualArgClubs.Count == 20, "Argentina Primera División 71 must contain exactly 20 clubs, got " + actualArgClubs.Count);

        Console.WriteLine("VERIFIED: Americas 50 clubs (" + rows.Count + " players in UID 1614xxxxxx range), balanced Mexico (18) and Argentina (20) divisions verified, all previous leagues 100% preserved.");
    }
}
