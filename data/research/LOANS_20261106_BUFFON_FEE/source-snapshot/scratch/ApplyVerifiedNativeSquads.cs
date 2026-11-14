using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;

class ApplyVerifiedNativeSquads
{
    static void Main(string[] args)
    {
        bool ab = args.Length >= 5 && args[4] == "--serie-ab";
        bool prem = args.Length >= 5 && args[4] == "--premier-league";
        bool spain = args.Length >= 5 && args[4] == "--spain";
        bool engLower = args.Length >= 5 && args[4] == "--eng-lower";
        bool france = args.Length >= 5 && args[4] == "--france";
        bool portugal = args.Length >= 5 && args[4] == "--portugal";
        bool germany = args.Length >= 5 && args[4] == "--germany";
        bool ger3liga = args.Length >= 5 && args[4] == "--germany-3liga";
        bool polNed = args.Length >= 5 && args[4] == "--poland-netherlands";
        bool bst = args.Length >= 5 && args[4] == "--belgium-scotland-turkey";
        bool cne = args.Length >= 5 && args[4] == "--central-north-europe";
        bool restEuro = args.Length >= 5 && args[4] == "--europe-rest";
        bool mls = args.Length >= 5 && args[4] == "--usa-mls";
        bool americas = args.Length >= 5 && args[4] == "--americas";
        bool asiaOceania = args.Length >= 5 && args[4] == "--asia-oceania";
        bool universal = args.Length >= 5 && args[4] == "--universal";
        bool euroRemain = args.Length >= 5 && args[4] == "--europe-remaining";
        bool southAmerica = args.Length >= 5 && args[4] == "--south-america";
        bool asiaAfrica = args.Length >= 5 && args[4] == "--asia-africa";
        bool fallenGiants = args.Length >= 5 && args[4] == "--fallen-giants";
        bool wonderkids = args.Length >= 5 && args[4] == "--wonderkids";
        bool batchTest = args.Length == 5 && args[4] == "--test-batch";
        bool repair = args.Length == 6 && args[4] == "--repair-contracts";
        if (args.Length != 4 && !(args.Length == 5 && (args[4] == "--verify" || ab || prem || spain || engLower || france || portugal || germany || ger3liga || polNed || bst || cne || restEuro || mls || americas || asiaOceania || universal || euroRemain || southAmerica || asiaAfrica || fallenGiants || wonderkids || batchTest)) &&
            !(args.Length == 6 && (ab || prem || spain || engLower || france || portugal || germany || ger3liga || polNed || bst || cne || restEuro || mls || americas || asiaOceania || universal || euroRemain || southAmerica || asiaAfrica || fallenGiants || wonderkids) && args[5] == "--verify") && !repair)
            throw new ArgumentException("Usage: editor-exe source-db new-output native-squad-csv [--verify | --universal | ...]");
        string editor = Path.GetFullPath(args[0]);
        if (!File.Exists(editor)) throw new FileNotFoundException("Editor assembly not found.", editor);
        var domain = AppDomain.CreateDomain("VerifiedNativeSquads", null,
            new AppDomainSetup { ApplicationBase = Path.GetDirectoryName(editor) });
        try
        {
            var worker = (VerifiedNativeSquadsWorker)domain.CreateInstanceFromAndUnwrap(
                Assembly.GetExecutingAssembly().Location, typeof(VerifiedNativeSquadsWorker).FullName);
            if (repair) worker.RepairContracts(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]),
                new[] { Path.GetFullPath(args[3]), Path.GetFullPath(args[5]) });
            else if (batchTest) worker.TestAbBatch(Path.GetFullPath(args[1]), Path.GetFullPath(args[3]));
            else if (wonderkids) worker.ImportWonderkids(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Path.GetFullPath(args[3]), args.Length == 6);
            else if (fallenGiants) worker.ImportFallenGiants(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Path.GetFullPath(args[3]), args.Length == 6);
            else if (asiaAfrica) worker.ImportAsiaAfrica(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Path.GetFullPath(args[3]), args.Length == 6);
            else if (southAmerica) worker.ImportSouthAmerica(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Path.GetFullPath(args[3]), args.Length == 6);
            else if (euroRemain) worker.ImportEuropeRemaining(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Path.GetFullPath(args[3]), args.Length == 6);
            else if (universal) worker.ImportUniversal(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Path.GetFullPath(args[3]), args.Length == 6);
            else if (asiaOceania) worker.ImportAsiaOceania(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Path.GetFullPath(args[3]), args.Length == 6);

            else if (americas) worker.ImportAmericas(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Path.GetFullPath(args[3]), args.Length == 6);
            else if (mls) worker.ImportUsaMls(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Path.GetFullPath(args[3]), args.Length == 6);
            else if (restEuro) worker.ImportEuropeRest(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Path.GetFullPath(args[3]), args.Length == 6);
            else if (cne) worker.ImportCentralNorthEurope(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Path.GetFullPath(args[3]), args.Length == 6);
            else if (bst) worker.ImportBelgiumScotlandTurkey(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Path.GetFullPath(args[3]), args.Length == 6);
            else if (polNed) worker.ImportPolandAndNetherlands(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Path.GetFullPath(args[3]), args.Length == 6);
            else if (ger3liga) worker.ImportGermany3Liga(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Path.GetFullPath(args[3]), args.Length == 6);
            else if (germany) worker.ImportGermany(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Path.GetFullPath(args[3]), args.Length == 6);
            else if (portugal) worker.ImportPortugal(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Path.GetFullPath(args[3]), args.Length == 6);
            else if (france) worker.ImportFrance(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Path.GetFullPath(args[3]), args.Length == 6);
            else if (spain) worker.ImportSpain(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Path.GetFullPath(args[3]), args.Length == 6);
            else if (engLower) worker.ImportEnglandLower(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Path.GetFullPath(args[3]), args.Length == 6);
            else if (prem) worker.ImportEnglishPremierLeague(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Path.GetFullPath(args[3]), args.Length == 6);
            else if (ab) worker.SerieAb(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Path.GetFullPath(args[3]), args.Length == 6);
            else if (args.Length == 4 && args[3] == "--audit") worker.Audit(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]));
            else if (args.Length == 5) worker.Verify(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Path.GetFullPath(args[3]));
            else worker.Run(Path.GetFullPath(args[1]), Path.GetFullPath(args[2]), Path.GetFullPath(args[3]));
        }
        finally { AppDomain.Unload(domain); }
    }
}

public sealed partial class VerifiedNativeSquadsWorker : MarshalByRefObject
{
    static readonly BindingFlags Private = BindingFlags.NonPublic | BindingFlags.Static;
    static readonly Type Editor = typeof(FM08_Database_Editor);

    static object Call(string name, params object[] args)
    {
        return Editor.GetMethod(name, Private).Invoke(null, args);
    }

    static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidDataException(message);
    }

    static byte[] Load(string directory, string file)
    {
        return (byte[])Call("DecompressFile", Path.Combine(directory, file));
    }

    static int AttributesStart(byte[] people)
    {
        return (int)Call("Find89ByteTable", people) - 81;
    }

    static string Csv(object value)
    {
        return "\"" + Convert.ToString(value, CultureInfo.InvariantCulture).Replace("\"", "\"\"") + "\"";
    }

    public void Audit(string source, string output)
    {
        Require(!Directory.Exists(output), "Audit directory already exists.");
        byte[] people = Load(source, "people_db.dat"), server = Load(source, "server_db.dat");
        var clubs = (Dictionary<int, string>)Call("ParseClubs", server);
        FM08_Database_Editor.ResolveNativeU23ClubNames(server, BitConverter.ToInt32(people, 0), clubs);
        var nations = (Dictionary<int, string>)Call("ParseNations", server);
        var players = ReadPlayers(people, server, clubs, nations);
        Directory.CreateDirectory(output);
        File.WriteAllLines(Path.Combine(output, "nations.csv"), new[] { "NationIndex,Nation" }.Concat(
            nations.OrderBy(e => e.Key).Select(e => Csv(e.Key) + "," + Csv(e.Value))), new UTF8Encoding(false));
        File.WriteAllLines(Path.Combine(output, "clubs.csv"), new[] { "ClubIndex,Club" }.Concat(
            clubs.OrderBy(e => e.Key).Select(e => Csv(e.Key) + "," + Csv(e.Value))), new UTF8Encoding(false));
        File.WriteAllLines(Path.Combine(output, "players.csv"), new[] {
            "ID,PersonIndex,FirstName,LastName,BirthDate,ClubIndex,Club,CA,PA,SquadNumber,Nationality" }.Concat(
            players.Select(p => string.Join(",", new object[] { p.Id, BitConverter.ToInt32(people, p.PersonOffset - 15),
                p.FirstName, p.LastName, p.BirthDate.HasValue ? p.BirthDate.Value.ToString("yyyy-MM-dd") : "",
                p.ClubIdOffset > 0 ? BitConverter.ToInt32(people, p.ClubIdOffset) : -1,
                p.Club, p.CA, p.PA, p.SquadNumber, p.Nationality }.Select(Csv)))), new UTF8Encoding(false));
        Console.WriteLine("Audited native players, clubs and nationalities: " + output);
    }

    static List<FM08_Database_Editor.PlayerRecord> ReadPlayers(byte[] people, byte[] server,
        Dictionary<int, string> clubs, Dictionary<int, string> nations)
    {
        object[] firstArgs = { server, 0, 0 };
        var first = (Dictionary<int, string>)Editor.GetMethod("ParseFirstNames", Private).Invoke(null, firstArgs);
        object[] lastArgs = { server, (int)firstArgs[2], null, 0 };
        var last = (Dictionary<int, string>)Editor.GetMethod("ParseSurnames", Private).Invoke(null, lastArgs);
        var common = (Dictionary<int, string>)Call("ParseCommonNames", server, (int)lastArgs[3]);
        var tags = (Dictionary<int, string[]>)Call("ParseEntityTreeAndTags", server);
        var details = (Dictionary<int, FM08_Database_Editor.PersonDetails>)Call("ParsePersonData", people, first, last, common, clubs);
        return (List<FM08_Database_Editor.PlayerRecord>)Call("BuildPlayerList", people, details, tags, lastArgs[2], clubs, nations);
    }

    static void EqualRange(byte[] a, int offsetA, byte[] b, int offsetB, int count, string label)
    {
        Require(offsetA >= 0 && offsetB >= 0 && count >= 0 &&
            offsetA + (long)count <= a.Length && offsetB + (long)count <= b.Length, "Invalid range: " + label);
        for (int i = 0; i < count; i++)
            if (a[offsetA + i] != b[offsetB + i]) throw new InvalidDataException("Unrelated bytes changed: " + label);
    }

    public void Run(string source, string output, string csv)
    {
        Require(!Directory.Exists(output) && !File.Exists(output), "Output already exists.");
        Require(!output.StartsWith(source.TrimEnd('\\') + "\\", StringComparison.OrdinalIgnoreCase), "Output is inside source.");
        byte[] people = Load(source, "people_db.dat"), server = Load(source, "server_db.dat"), client = Load(source, "client_db.dat");
        byte[] originalPeople = (byte[])people.Clone(), originalServer = (byte[])server.Clone();
        int originalCount = BitConverter.ToInt32(people, 0);
        int originalPersonalities = BitConverter.ToInt32(people, 4), originalPlayers = BitConverter.ToInt32(people, 8);
        int originalAttributes = AttributesStart(people);
        int originalPersonalityHeader = originalAttributes - 8 - originalPersonalities * 17;
        var clubs = (Dictionary<int, string>)Call("ParseClubs", server);
        FM08_Database_Editor.ResolveNativeU23ClubNames(server, originalCount, clubs);
        var nations = (Dictionary<int, string>)Call("ParseNations", server);
        var players = ReadPlayers(people, server, clubs, nations);
        FM08_Database_Editor.ClubsRev.Clear();
        foreach (var entry in clubs) if (!FM08_Database_Editor.ClubsRev.ContainsKey(entry.Value))
            FM08_Database_Editor.ClubsRev.Add(entry.Value, entry.Key);
        FM08_Database_Editor.NationsRev.Clear();
        foreach (var entry in nations) if (!FM08_Database_Editor.NationsRev.ContainsKey(entry.Value))
            FM08_Database_Editor.NationsRev.Add(entry.Value, entry.Key);
        FM08_Database_Editor.InitCsvRegistry();
        var records = FM08_Database_Editor.ParseNativeClubDivisions(server, originalCount);
        var originalLoans = FM08_Database_Editor.ParseNativeLoans(server, originalCount);
        var originalRetirements = FM08_Database_Editor.ParseRetirements(server);
        var byPerson = players.ToDictionary(p => BitConverter.ToInt32(people, p.PersonOffset - 15));

        string[] lines = File.ReadAllLines(csv, Encoding.UTF8);
        string[] headers = (string[])Call("ParseCsvLine", lines[0]);
        Require(headers.Length == headers.Distinct(StringComparer.Ordinal).Count(), "Duplicate CSV header.");
        var incoming = new List<FM08_Database_Editor.PlayerRecord>();
        var targets = new HashSet<int>();
        var targetByPlayer = new Dictionary<FM08_Database_Editor.PlayerRecord, int>();
        var identities = new HashSet<string>();
        for (int line = 1; line < lines.Length; line++)
        {
            string[] values = (string[])Call("ParseCsvLine", lines[line]);
            Require(values.Length == headers.Length, "Malformed squad CSV row.");
            var row = headers.Select((h, i) => new { h, value = values[i] }).ToDictionary(v => v.h, v => v.value);
            int club = int.Parse(row["ClubIndex"], CultureInfo.InvariantCulture);
            Require((club == 1009 || club == 23626) && records.ContainsKey(club) &&
                clubs[club] == row["Club"], "Unverified target club identity.");
            var player = new FM08_Database_Editor.PlayerRecord {
                Id = -1, FirstName = row["FirstName"], LastName = row["LastName"], Club = row["Club"],
                BirthDate = DateTime.ParseExact(row["BirthDate"], "yyyy-MM-dd", CultureInfo.InvariantCulture),
                Nationality = row["Nationality"], ContractExpires = new DateTime(2010, 6, 30),
                ContractExpiresPending = true, ClubAssignmentPending = true
            };
            Require(FM08_Database_Editor.NationsRev.ContainsKey(player.Nationality), "Unknown nationality: " + player.Nationality +
                "; native Congo names: " + string.Join(", ", nations.Values.Where(n => n.IndexOf("ong", StringComparison.OrdinalIgnoreCase) >= 0)));
            Require(identities.Add(club + "|" + player.FullName + "|" + row["BirthDate"]), "Duplicate squad identity.");
            foreach (var entry in row)
            {
                if (new[] { "ClubIndex", "FirstName", "LastName", "BirthDate", "Nationality", "Club" }.Contains(entry.Key)) continue;
                int number = int.Parse(entry.Value, CultureInfo.InvariantCulture);
                var field = typeof(FM08_Database_Editor.PlayerRecord).GetField(entry.Key);
                var property = typeof(FM08_Database_Editor.PlayerRecord).GetProperty(entry.Key);
                Type type = field != null ? field.FieldType : property != null && property.CanWrite ? property.PropertyType : null;
                Require(type == typeof(int) || type == typeof(byte), "Unsupported native model column: " + entry.Key);
                object value;
                if (type == typeof(byte)) value = checked((byte)number);
                else value = number;
                if (field != null) field.SetValue(player, value);
                else property.SetValue(player, value, null);
            }
            Require(player.CA >= 1 && player.PA >= player.CA && player.PA <= 200 && player.WeeklyWage > 0 &&
                player.SquadNumber > 0 && player.SquadNumber <= 99, "Invalid imported profile.");
            player.Position = player.PosGK == 20 ? "GK" : player.PosDC == 20 ? "DC" : player.PosMC == 20 ? "MC" : "ST";
            foreach (var entry in row)
                if (!new[] { "ClubIndex", "FirstName", "LastName", "BirthDate", "Nationality", "Club", "CA", "PA",
                    "WeeklyWage", "Height", "Weight", "SquadNumber" }.Contains(entry.Key))
                    Require(int.Parse(entry.Value, CultureInfo.InvariantCulture) >= 0 &&
                        int.Parse(entry.Value, CultureInfo.InvariantCulture) <= 20, "Invalid attribute/position: " + entry.Key);
            targets.Add(club);
            incoming.Add(player);
            targetByPlayer.Add(player, club);
        }
        Require(targets.SetEquals(new[] { 1009, 23626 }), "This verified stage requires both Novara and Atalanta U23.");
        Require(BitConverter.ToInt32(server, records[23626].Footer + 4) == 1800000089 &&
            BitConverter.ToInt32(server, records[23626].Footer - 14) == 786, "Atalanta U23 UID or parent differs from the verified creation.");
        foreach (int target in targets)
        {
            var squad = incoming.Where(p => targetByPlayer[p] == target).ToList();
            Require(squad.Count >= 18 && squad.Count <= 45 && squad.Count(p => p.PosGK == 20) >= 2 &&
                squad.Select(p => p.SquadNumber).Distinct().Count() == squad.Count, "Incomplete or duplicate-number squad.");
        }

        var departing = new List<FM08_Database_Editor.PlayerRecord>();
        var departingIndices = new HashSet<int>();
        foreach (int target in targets)
        {
            var record = records[target];
            int count = BitConverter.ToUInt16(server, record.RosterOffset);
            for (int i = 0; i < count; i++)
            {
                int index = BitConverter.ToInt32(server, record.RosterOffset + 2 + i * 4);
                FM08_Database_Editor.PlayerRecord player;
                Require(byPerson.TryGetValue(index, out player), "Unsupported departing PERSON index: " + index);
                Require(player.ClubIdOffset > 0 && BitConverter.ToInt32(people, player.ClubIdOffset) == target &&
                    departingIndices.Add(index), "Unsupported or duplicate owned-player relationship.");
                departing.Add(player);
            }
        }
        var removedLoanPeople = new HashSet<int>(departingIndices);
        foreach (var loan in originalLoans) if (targets.Contains(loan.ClubId)) removedLoanPeople.Add(loan.PersonIndex);
        server = FM08_Database_Editor.RemoveNativeLoans(server, originalCount, removedLoanPeople);
        RetireHistoricalDepartures(ref people, ref server, players, departing);
        byte[] releasedPeople = (byte[])people.Clone();
        int releasedPersonalityHeader = AttributesStart(people) - 8 - originalPersonalities * 17;
        int nextIdentity = 1600000000;
        int created = 0;
        foreach (var player in incoming)
        {
            FM08_Database_Editor.AppendNativePlayerWithIdentityCursor(ref people, ref server, ref client, player, players, ref nextIdentity);
            players.Add(player);
            if (++created % 10 == 0) Console.WriteLine("Created native profiles: " + created + "/" + incoming.Count);
        }
        FM08_Database_Editor.SyncClubAssignments(ref people, ref server, incoming);

        int countAfter = BitConverter.ToInt32(people, 0);
        var afterRecords = FM08_Database_Editor.ParseNativeClubDivisions(server, countAfter);
        Require(countAfter == originalCount + incoming.Count && afterRecords.Count == records.Count, "Native entity count mismatch.");
        foreach (var record in records.Values)
        {
            var current = afterRecords[record.ClubIndex];
            Require(record.CurrentDivisionIndex == current.CurrentDivisionIndex &&
                record.PreviousDivisionIndex == current.PreviousDivisionIndex &&
                record.EuropeanCompetitionIndex == current.EuropeanCompetitionIndex, "Competition assignment changed.");
            if (!targets.Contains(record.ClubIndex))
            {
                VerifyClubAfterRelease(originalServer, server, record, current, departingIndices);
            }
        }
        foreach (int target in targets)
        {
            var current = afterRecords[target];
            var expected = new HashSet<int>(incoming.Where(p => targetByPlayer[p] == target)
                .Select(p => BitConverter.ToInt32(people, p.PersonOffset - 15)));
            Require(expected.Count == BitConverter.ToUInt16(server, current.RosterOffset), "Incorrect target roster size.");
            for (int i = 0; i < BitConverter.ToUInt16(server, current.RosterOffset); i++)
                Require(expected.Remove(BitConverter.ToInt32(server, current.RosterOffset + 2 + i * 4)), "Unexpected roster member.");
            Require(expected.Count == 0, "Missing modern roster member.");
        }
        EqualRange(releasedPeople, 16, people, 16, releasedPersonalityHeader - 16, "original PERSON after release");
        VerifyHistoricalDepartures(originalPeople, originalServer, people, server,
            ReadPlayers(originalPeople, originalServer, clubs, nations), players, targets);
        int currentAttributes = AttributesStart(people);
        int currentPersonalityHeader = currentAttributes - 8 - BitConverter.ToInt32(people, 4) * 17;
        EqualRange(originalPeople, originalPersonalityHeader + 4, people, currentPersonalityHeader + 4, originalPersonalities * 17, "original personalities");
        EqualRange(originalPeople, originalAttributes, people, currentAttributes, originalPlayers * 89, "original attributes");
        int oldEnd = originalAttributes + originalPlayers * 89;
        int newEnd = currentAttributes + BitConverter.ToInt32(people, 8) * 89;
        Require(originalPeople.Length - oldEnd == people.Length - newEnd, "Original people suffix size changed.");
        EqualRange(originalPeople, oldEnd, people, newEnd, originalPeople.Length - oldEnd, "original people suffix");
        var retirements = FM08_Database_Editor.ParseRetirements(server);
        foreach (var player in departing) Require(retirements[player.Id] == player.RetirementDate, "Missing retirement.");
        foreach (var entry in originalRetirements) if (!departing.Any(p => p.Id == entry.Key))
            Require(retirements.ContainsKey(entry.Key) && retirements[entry.Key] == entry.Value, "Unrelated retirement changed.");
        var loansAfter = FM08_Database_Editor.ParseNativeLoans(server, countAfter);
        Require(loansAfter.Count == originalLoans.Count(l => !removedLoanPeople.Contains(l.PersonIndex)), "Unexpected loan count.");
        foreach (var player in incoming) Require(!retirements.ContainsKey(player.Id), "Modern player is retired.");
        Console.WriteLine("PASS: " + incoming.Count + " modern players; " + departing.Count + " owned old players retired.");
        Console.WriteLine("PASS: all other CLUB records, original attributes/personalities and unrelated PERSON bytes unchanged.");
        Console.WriteLine("PASS: unrelated contracts preserved; historical players released and retired; incoming loans returned.");

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
            byte[] header = (byte[])Call("GetFileHeader", Path.Combine(source, entry.Key));
            File.WriteAllBytes(Path.Combine(output, entry.Key), (byte[])Call("CompressFile", entry.Value, header));
            EqualRange(entry.Value, 0, Load(output, entry.Key), 0, entry.Value.Length, "persisted " + entry.Key);
        }
        FM08_Database_Editor.WriteDatabaseMetadata(source, output);
        foreach (string path in Directory.GetFiles(source, "*", SearchOption.AllDirectories))
        {
            string relative = path.Substring(source.TrimEnd('\\').Length + 1);
            if (new[] { "people_db.dat", "server_db.dat", "client_db.dat" }.Contains(relative) ||
                (string.IsNullOrEmpty(Path.GetDirectoryName(relative)) && Path.GetExtension(relative).Equals(".xml", StringComparison.OrdinalIgnoreCase))) continue;
            Require(File.ReadAllBytes(path).SequenceEqual(File.ReadAllBytes(Path.Combine(output, relative))), "Unrelated copied file changed.");
        }
        Console.WriteLine("Published: " + output);
        Verify(source, output, csv);
    }

    public void Verify(string source, string output, string csv)
    {
        byte[] people = Load(output, "people_db.dat"), server = Load(output, "server_db.dat");
        var clubs = (Dictionary<int, string>)Call("ParseClubs", server);
        FM08_Database_Editor.ResolveNativeU23ClubNames(server, BitConverter.ToInt32(people, 0), clubs);
        var nations = (Dictionary<int, string>)Call("ParseNations", server);
        var players = ReadPlayers(people, server, clubs, nations);
        var retirements = FM08_Database_Editor.ParseRetirements(server);
        var contractReferences = FM08_Database_Editor.ResolveNativeClubContractReferences(
            server, BitConverter.ToInt32(people, 0), players.Where(p => p.Id >= 1600000000 && p.ClubId > 0).Select(p => p.ClubId));
        string[] lines = File.ReadAllLines(csv, Encoding.UTF8);
        string[] headers = (string[])Call("ParseCsvLine", lines[0]);
        int verified = 0;
        foreach (string line in lines.Skip(1))
        {
            string[] values = (string[])Call("ParseCsvLine", line);
            var row = headers.Select((h, i) => new { h, value = values[i] }).ToDictionary(v => v.h, v => v.value);
            var dob = DateTime.ParseExact(row["BirthDate"], "yyyy-MM-dd", CultureInfo.InvariantCulture);
            var matches = players.Where(p => p.BirthDate == dob &&
                p.FirstName.Equals(row["FirstName"], StringComparison.OrdinalIgnoreCase) &&
                p.LastName.Equals(row["LastName"], StringComparison.OrdinalIgnoreCase) &&
                p.ClubIdOffset > 0 && BitConverter.ToInt32(people, p.ClubIdOffset) == int.Parse(row["ClubIndex"])).ToList();
            Require(matches.Count == 1, "Persisted modern identity missing or duplicated: " + row["FirstName"] + " " + row["LastName"]);
            var player = matches[0];
            foreach (var entry in row)
            {
                if (new[] { "ClubIndex", "FirstName", "LastName", "BirthDate" }.Contains(entry.Key)) continue;
                var field = typeof(FM08_Database_Editor.PlayerRecord).GetField(entry.Key);
                var property = typeof(FM08_Database_Editor.PlayerRecord).GetProperty(entry.Key);
                object actual = field != null ? field.GetValue(player) : property.GetValue(player, null);
                Require(Convert.ToString(actual, CultureInfo.InvariantCulture).Equals(entry.Value, StringComparison.OrdinalIgnoreCase),
                    "Persisted profile field differs: " + player.FullName + " / " + entry.Key +
                    " expected=" + entry.Value + " actual=" + Convert.ToString(actual, CultureInfo.InvariantCulture));
            }
            Require(player.ContractExpires == new DateTime(2010, 6, 30), "Persisted contract date differs.");
            int index = BitConverter.ToInt32(people, player.PersonOffset - 15);
            int contract = player.ClubIdOffset + 28;
            Require(people[contract - 1] == 1 && people[contract + 1] == 1 &&
                BitConverter.ToInt32(people, contract + 31) == contractReferences[int.Parse(row["ClubIndex"])] &&
                BitConverter.ToInt32(people, contract + 26) == index &&
                BitConverter.ToInt32(people, contract + 35) == player.WeeklyWage, "Invalid persisted primary contract.");
            Require(!retirements.ContainsKey(player.Id), "New modern player is retired.");
            if (player.PA == 155) Console.WriteLine("Generic PA155 talent: " + player.FullName);
            verified++;
        }
        Require(verified == 59, "The published stage must contain exactly 59 verified new profiles.");
        byte[] beforeServer = Load(source, "server_db.dat");
        var oldPeople = Load(source, "people_db.dat");
        var beforePlayers = ReadPlayers(oldPeople, beforeServer,
            (Dictionary<int, string>)Call("ParseClubs", beforeServer), (Dictionary<int, string>)Call("ParseNations", beforeServer));
        int retired = beforePlayers.Count(p => p.ClubIdOffset > 0 &&
            new[] { 1009, 23626 }.Contains(BitConverter.ToInt32(oldPeople, p.ClubIdOffset)));
        VerifyHistoricalDepartures(oldPeople, beforeServer, people, server, beforePlayers, players,
            new HashSet<int> { 1009, 23626 });
        Console.WriteLine("PASS: reloaded " + verified + " exact profiles, native contracts, PA/CA/positions/attributes and " + retired + " old retirements.");
    }
}
