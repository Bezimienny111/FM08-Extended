using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Linq;
using System.Text;
using System.Xml;

public class TestNativeDatabaseWrites
{
    private static void Require(bool condition, string message)
    {
        if (!condition) throw new Exception(message);
    }

    private static object Call(string method, params object[] arguments)
    {
        return typeof(FM08_Database_Editor).GetMethod(method, BindingFlags.NonPublic | BindingFlags.Static).Invoke(null, arguments);
    }

    private static void RejectLeagueChanges(byte[] server, int personCount, params FM08_Database_Editor.ClubLeagueChange[] changes)
    {
        bool rejected = false;
        try { FM08_Database_Editor.ApplyClubLeagueChanges(server, personCount, changes); }
        catch (InvalidDataException) { rejected = true; }
        Require(rejected, "Invalid league mapping must fail explicitly.");
    }

    private static FM08_Database_Editor.ClubLeagueChange LeagueChange(int club, int source, int target)
    {
        return new FM08_Database_Editor.ClubLeagueChange { ClubIndex = club, ExpectedDivisionIndex = source, TargetDivisionIndex = target };
    }

    private static void CheckLeagueAssignments(string sourceDirectory, string referenceDirectory)
    {
        byte[] server = (byte[])Call("DecompressFile", Path.Combine(sourceDirectory, "server_db.dat"));
        byte[] snapshot = (byte[])server.Clone();
        int personCount = BitConverter.ToInt32((byte[])Call("DecompressFile", Path.Combine(sourceDirectory, "people_db.dat")), 0);
        var records = FM08_Database_Editor.ParseNativeClubDivisions(server, personCount);
        Require(records.ContainsKey(992) && records.ContainsKey(968), "Controlled league clubs were not located.");
        Require(records[992].CurrentDivisionIndex == 22 && records[968].CurrentDivisionIndex == 23, "Unexpected controlled source leagues.");
        Require(records.Values.Count(record => record.CurrentDivisionIndex == 22) == 20 &&
            records.Values.Count(record => record.CurrentDivisionIndex == 23) == 22, "Source Serie A/B memberships must be exactly 20/22.");
        string map = Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "data", "club_league_changes_test.csv"));
        var changes = FM08_Database_Editor.ReadClubLeagueCsv(map);
        byte[] updated = FM08_Database_Editor.ApplyClubLeagueChanges(server, personCount, changes);
        byte[] reference = (byte[])Call("DecompressFile", Path.Combine(referenceDirectory, "server_db.dat"));
        var referenceRecords = FM08_Database_Editor.ParseNativeClubDivisions(reference, personCount);
        int changedBytes = 0;
        for (int offset = 0; offset < server.Length; offset++)
        {
            if (server[offset] == updated[offset]) continue;
            changedBytes++;
            Require(changes.Any(change => offset >= records[change.ClubIndex].Start + 7 &&
                offset < records[change.ClubIndex].Start + 11), "League import changed an unrelated server byte.");
        }
        Require(changedBytes == 2 && updated.Length == server.Length, "Controlled swap must change exactly two physical bytes.");
        foreach (var change in changes)
        {
            var original = records[change.ClubIndex];
            var expected = referenceRecords[change.ClubIndex];
            int length = original.Footer + 8 - original.Start;
            Require(length == expected.Footer + 8 - expected.Start, "SI club record size differs.");
            Require(updated.Skip(original.Start).Take(length).SequenceEqual(reference.Skip(expected.Start).Take(length)),
                "Complete imported club record does not match SI: " + change.ClubIndex);
        }
        var after = FM08_Database_Editor.ParseNativeClubDivisions(updated, personCount);
        Require(after.Values.Count(record => record.CurrentDivisionIndex == 22) == 20 &&
            after.Values.Count(record => record.CurrentDivisionIndex == 23) == 22, "Imported Serie A/B memberships changed.");
        Require(FM08_Database_Editor.ApplyClubLeagueChanges(server, personCount, new[] { LeagueChange(992, 22, 22) }).SequenceEqual(server), "No-op mapping changed data.");
        RejectLeagueChanges(server, personCount, LeagueChange(992, 22, 23));
        RejectLeagueChanges(server, personCount, LeagueChange(992, 23, 22));
        RejectLeagueChanges(server, personCount, LeagueChange(992, 22, 23), LeagueChange(992, 22, 23));
        RejectLeagueChanges(server, personCount, LeagueChange(int.MaxValue, 22, 23));
        RejectLeagueChanges(server, personCount, LeagueChange(992, 22, int.MaxValue));
        RejectLeagueChanges(server, personCount, LeagueChange(992, 22, -2));
        RejectLeagueChanges(server, personCount);
        RejectLeagueChanges(new byte[64], personCount, LeagueChange(992, 22, 23));

        var third = records.Values.First(record => record.CurrentDivisionIndex >= 0 &&
            record.CurrentDivisionIndex != 22 && record.CurrentDivisionIndex != 23);
        var cycle = new[] { LeagueChange(992, 22, 23), LeagueChange(968, 23, third.CurrentDivisionIndex),
            LeagueChange(third.ClubIndex, third.CurrentDivisionIndex, 22) };
        var cycled = FM08_Database_Editor.ParseNativeClubDivisions(FM08_Database_Editor.ApplyClubLeagueChanges(server, personCount, cycle), personCount);
        foreach (var group in records.Values.GroupBy(record => record.CurrentDivisionIndex))
            Require(cycled.Values.Count(record => record.CurrentDivisionIndex == group.Key) == group.Count(), "Three-league cycle changed participant counts.");
        Require(cycled[992].CurrentDivisionIndex == 23 && cycled[968].CurrentDivisionIndex == third.CurrentDivisionIndex &&
            cycled[third.ClubIndex].CurrentDivisionIndex == 22, "Three-league cycle destinations are wrong.");
        var unassigned = records.Values.First(record => record.CurrentDivisionIndex == -1);
        byte[] outside = FM08_Database_Editor.ApplyClubLeagueChanges(server, personCount,
            new[] { LeagueChange(992, 22, -1), LeagueChange(unassigned.ClubIndex, -1, 22) });
        Require(BitConverter.ToInt32(outside, records[992].Start + 7) == -1 &&
            BitConverter.ToInt32(outside, unassigned.Start + 7) == 22, "Balanced no-division swap failed.");

        string temporary = Path.Combine(Path.GetTempPath(), "FM08LeagueTests_" + Guid.NewGuid().ToString("N"));
        string source = Path.Combine(temporary, "SOURCE");
        string output = Path.Combine(temporary, "OUTPUT");
        string csv = Path.Combine(temporary, "mapping.csv");
        Directory.CreateDirectory(source);
        Directory.CreateDirectory(output);
        try
        {
            FM08_Database_Editor.ExportClubLeagueCsv(csv, server, personCount,
                new Dictionary<int, string> { { 992, "Inter, \"Milano\"" } });
            var roundTrip = FM08_Database_Editor.ReadClubLeagueCsv(csv);
            Require(roundTrip.Count == records.Count &&
                FM08_Database_Editor.ApplyClubLeagueChanges(server, personCount, roundTrip).SequenceEqual(server),
                "Complete UTF-8 quoted-name export/import did not round-trip.");
            string header = "ClubIndex,ExpectedDivisionIndex,TargetDivisionIndex,ClubName\n";
            foreach (string invalid in new[] {
                "", header, header + "\n", header + "992,22,23,\"Inter\n",
                header + "992,22,23,In\"ter\n", header + "992,22,23,\"Inter\"x\n",
                header + "992,22,23\n", header + "992,22,23,Inter,Extra\n",
                header + "abc,22,23,Inter\n", header + "0,22,23,Inter\n",
                header + "992,22,-2,Inter\n", header + "992,22,23,Inter\n992,22,23,Inter\n",
                "ClubIndex,ExpectedDivisionIndex,TargetDivisionIndex,Typo\n992,22,23,Inter\n",
                "ClubIndex,ClubIndex,TargetDivisionIndex\n992,22,23\n"
            })
            {
                File.WriteAllText(csv, invalid, new UTF8Encoding(true));
                bool rejected = false;
                try { FM08_Database_Editor.ReadClubLeagueCsv(csv); }
                catch (InvalidDataException) { rejected = true; }
                Require(rejected, "Malformed league CSV was accepted: " + invalid);
            }
            File.WriteAllText(csv, "targetdivisionindex,clubindex,expecteddivisionindex\n23,992,22\n22,968,23\n", new UTF8Encoding(true));
            Require(FM08_Database_Editor.ApplyClubLeagueChanges(server, personCount,
                FM08_Database_Editor.ReadClubLeagueCsv(csv)).SequenceEqual(updated), "Reordered case-insensitive CSV failed.");

            string originalXml = Path.Combine(source, "SOURCE.xml");
            File.WriteAllText(originalXml, "<properties version=\"1.0\"><string id=\"name\" value=\"SOURCE\"/><string id=\"author\" value=\"Original Author\"/><string id=\"required_version\" value=\"8.0.2\"/></properties>");
            FM08_Database_Editor.WriteDatabaseMetadata(source, output);
            var metadata = new XmlDocument();
            metadata.Load(Path.Combine(output, "OUTPUT.xml"));
            Require(((XmlElement)metadata.SelectSingleNode("/properties/string[@id='name']")).GetAttribute("value") == "OUTPUT" &&
                ((XmlElement)metadata.SelectSingleNode("/properties/string[@id='author']")).GetAttribute("value") == "Original Author",
                "Output metadata name or preserved author is wrong.");
            Require(File.ReadAllText(originalXml).Contains("value=\"SOURCE\""), "Source metadata was modified.");
        }
        finally
        {
            foreach (string file in Directory.GetFiles(temporary, "*", SearchOption.AllDirectories)) File.Delete(file);
            Directory.Delete(source);
            Directory.Delete(output);
            Directory.Delete(temporary);
        }
        Require(server.SequenceEqual(snapshot), "League validation modified the input buffer.");
        Console.WriteLine("PASS: league CSV/SI exact records, 20/22 membership, multi-league cycle, no-division balance, atomic rejection, no-op, full CSV round-trip and XML metadata.");
    }

    private static FM08_Database_Editor.ClubCompetitionChange EuropeanChange(int club, int source, int target)
    {
        return new FM08_Database_Editor.ClubCompetitionChange { ClubIndex = club, ExpectedCompetitionIndex = source, TargetCompetitionIndex = target };
    }

    private static void CheckEuropeanAssignments(string sourceDirectory, string referenceDirectory)
    {
        byte[] server = (byte[])Call("DecompressFile", Path.Combine(sourceDirectory, "server_db.dat"));
        byte[] snapshot = (byte[])server.Clone();
        int personCount = BitConverter.ToInt32((byte[])Call("DecompressFile", Path.Combine(sourceDirectory, "people_db.dat")), 0);
        var records = FM08_Database_Editor.ParseNativeClubDivisions(server, personCount);
        Require(records[992].EuropeanCompetitionIndex == 519 && records[968].EuropeanCompetitionIndex == -1,
            "Unexpected controlled source European assignments.");
        Require(records.Values.Count(record => record.EuropeanCompetitionIndex == 519) == 76, "Source Champions Cup must contain exactly 76 assigned clubs.");
        string csv = Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "data", "club_european_changes_test.csv"));
        var changes = FM08_Database_Editor.ReadClubEuropeanCsv(csv);
        byte[] updated = FM08_Database_Editor.ApplyClubEuropeanChanges(server, personCount, changes);
        byte[] reference = (byte[])Call("DecompressFile", Path.Combine(referenceDirectory, "server_db.dat"));
        var expectedRecords = FM08_Database_Editor.ParseNativeClubDivisions(reference, personCount);
        int changedBytes = 0;
        for (int i = 0; i < server.Length; i++)
        {
            if (server[i] == updated[i]) continue;
            changedBytes++;
            Require(changes.Any(change => i >= records[change.ClubIndex].Start + 33 &&
                i < records[change.ClubIndex].Start + 37), "European import changed an unrelated byte.");
        }
        Require(changedBytes == 8 && updated.Length == server.Length, "European swap must change exactly eight bytes.");
        foreach (var change in changes)
        {
            var original = records[change.ClubIndex];
            var expected = expectedRecords[change.ClubIndex];
            Require(updated.Skip(original.Start).Take(original.Footer + 8 - original.Start)
                .SequenceEqual(reference.Skip(expected.Start).Take(expected.Footer + 8 - expected.Start)),
                "Complete European club record differs from SI: " + change.ClubIndex);
        }
        var after = FM08_Database_Editor.ParseNativeClubDivisions(updated, personCount);
        Require(after[992].EuropeanCompetitionIndex == -1 && after[968].EuropeanCompetitionIndex == 519 &&
            after.Values.Count(record => record.EuropeanCompetitionIndex == 519) == 76, "European replacement or count is wrong.");
        Require(FM08_Database_Editor.ApplyClubEuropeanChanges(server, personCount,
            new[] { EuropeanChange(992, 519, 519) }).SequenceEqual(server), "European no-op changed data.");
        foreach (var invalid in new[] {
            new[] { EuropeanChange(992, 519, -1) },
            new[] { EuropeanChange(968, -1, 519) },
            new[] { EuropeanChange(992, -1, 519) },
            new[] { EuropeanChange(992, 519, -1), EuropeanChange(992, 519, -1) },
            new[] { EuropeanChange(int.MaxValue, 519, -1) },
            new[] { EuropeanChange(992, 519, int.MaxValue) },
            new[] { EuropeanChange(992, 519, -2) },
            new FM08_Database_Editor.ClubCompetitionChange[0],
            new FM08_Database_Editor.ClubCompetitionChange[] { null }
        })
        {
            bool rejected = false;
            try { FM08_Database_Editor.ApplyClubEuropeanChanges(server, personCount, invalid); }
            catch (InvalidDataException) { rejected = true; }
            Require(rejected, "Invalid European mapping must be rejected atomically.");
        }
        var other = records.Values.First(record => record.EuropeanCompetitionIndex >= 0 &&
            record.EuropeanCompetitionIndex != 519 && record.EuropeanCompetitionIndex < server.Length / 4);
        var crossed = FM08_Database_Editor.ParseNativeClubDivisions(FM08_Database_Editor.ApplyClubEuropeanChanges(server, personCount,
            new[] { EuropeanChange(992, 519, other.EuropeanCompetitionIndex), EuropeanChange(other.ClubIndex, other.EuropeanCompetitionIndex, 519) }), personCount);
        foreach (var group in records.Values.GroupBy(record => record.EuropeanCompetitionIndex))
            Require(crossed.Values.Count(record => record.EuropeanCompetitionIndex == group.Key) == group.Count(), "Cross-cup replacement changed a participant count.");

        string temporary = Path.Combine(Path.GetTempPath(), "FM08EuropeanCsv_" + Guid.NewGuid().ToString("N") + ".csv");
        try
        {
            FM08_Database_Editor.ExportClubEuropeanCsv(temporary, server, personCount,
                new Dictionary<int, string> { { 968, "Bologna, \"FC\"" } });
            var exported = FM08_Database_Editor.ReadClubEuropeanCsv(temporary);
            Require(exported.Count == records.Count &&
                FM08_Database_Editor.ApplyClubEuropeanChanges(server, personCount, exported).SequenceEqual(server),
                "Complete European CSV export/import did not round-trip.");
            foreach (string invalid in new[] {
                "ClubIndex,ExpectedDivisionIndex,TargetDivisionIndex\n992,519,-1\n",
                "ClubIndex,ExpectedEuropeanCompetitionIndex,TargetEuropeanCompetitionIndex\n",
                "ClubIndex,ExpectedEuropeanCompetitionIndex,TargetEuropeanCompetitionIndex\n992,519,\n",
                "ClubIndex,ExpectedEuropeanCompetitionIndex,TargetEuropeanCompetitionIndex\n992,519,-1\n992,519,-1\n"
            })
            {
                File.WriteAllText(temporary, invalid, new UTF8Encoding(true));
                bool rejected = false;
                try { FM08_Database_Editor.ReadClubEuropeanCsv(temporary); }
                catch (InvalidDataException) { rejected = true; }
                Require(rejected, "Invalid European CSV was accepted.");
            }
            File.WriteAllText(temporary, "targeteuropeancompetitionindex,clubindex,expectedeuropeancompetitionindex\n-1,992,519\n519,968,-1\n", new UTF8Encoding(true));
            Require(FM08_Database_Editor.ApplyClubEuropeanChanges(server, personCount,
                FM08_Database_Editor.ReadClubEuropeanCsv(temporary)).SequenceEqual(updated), "Reordered European CSV failed.");
        }
        finally { File.Delete(temporary); }
        var leagueChanges = FM08_Database_Editor.ReadClubLeagueCsv(Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "data", "club_league_changes_test.csv")));
        byte[] combined = FM08_Database_Editor.ApplyClubEuropeanChanges(FM08_Database_Editor.ApplyClubLeagueChanges(server, personCount, leagueChanges), personCount, changes);
        byte[] reversed = FM08_Database_Editor.ApplyClubLeagueChanges(updated, personCount, leagueChanges);
        Require(combined.SequenceEqual(reversed), "League and European maps must be independent and commute.");
        Require(server.SequenceEqual(snapshot), "European validation modified the input buffer.");
        Console.WriteLine("PASS: European CSV/SI exact records, 76 participants, no-op, atomic rejection, cross-cup balance, full CSV round-trip and independent league/European maps.");
    }

    private static void CheckNativeSample(string directory, string outputDirectory)
    {
        byte[] server = (byte[])Call("DecompressFile", Path.Combine(directory, "server_db.dat"));
        byte[] people = (byte[])Call("DecompressFile", Path.Combine(directory, "people_db.dat"));
        object[] firstArguments = { server, 0, 0 };
        var firstNames = (Dictionary<int, string>)Call("ParseFirstNames", firstArguments);
        object[] lastArguments = { server, firstArguments[2], null, 0 };
        var lastNames = (Dictionary<int, string>)Call("ParseSurnames", lastArguments);
        var commonNames = (Dictionary<int, string>)Call("ParseCommonNames", server, lastArguments[3]);
        Require(firstNames[-1] == "Brak" && lastNames[-1] == "Imienia", "Native index-zero names were not read.");
        var clubs = (Dictionary<int, string>)Call("ParseClubs", server);
        var nations = (Dictionary<int, string>)Call("ParseNations", server);
        var details = (Dictionary<int, FM08_Database_Editor.PersonDetails>)Call("ParsePersonData", people, firstNames, lastNames, commonNames, clubs);
        FM08_Database_Editor.PersonDetails created;
        Require(details.TryGetValue(273506, out created), "Native new-player details were not read.");
        Console.WriteLine("Native new details: " + created.FirstName + " " + created.LastName + ", UID=" + created.UniqueId);
        var players = (List<FM08_Database_Editor.PlayerRecord>)Call("BuildPlayerList", people, details, new Dictionary<int, string[]>(), new Dictionary<int, string>(), clubs, nations);
        var added = players.Find(player => player.Id == 1394631309);
        Require(added != null && added.FirstName == "Brak" && added.LastName == "Imienia", "Native new player did not round-trip through the editor reader.");
        var buffon = players.Find(player => player.Id == 11133);
        Console.WriteLine("Buffon UID check: " + (buffon == null ? "missing" : buffon.FullName + ", GK=" + buffon.PosGK + ", offset=" + buffon.PersonOffset));
        foreach (var candidate in players.FindAll(player => player.LastName == "Buffon"))
            Console.WriteLine("Buffon name match: UID=" + candidate.Id + ", name=" + candidate.FullName + ", GK=" + candidate.PosGK);
        Require(buffon != null && buffon.LastName == "Buffon" && buffon.PosGK == 20, "Buffon identity or attributes regressed.");
        Console.WriteLine("PASS: native new player, index-zero names and Buffon identity.");
        byte[] client = (byte[])Call("DecompressFile", Path.Combine(directory, "client_db.dat"));
        int originalCount = BitConverter.ToInt32(people, 8);
        var newPlayer = FM08_Database_Editor.CreateNewPlayer(0);
        newPlayer.FirstName = "NativeProbeFirst";
        newPlayer.LastName = "NativeProbeLast";
        newPlayer.Nationality = "";
        FM08_Database_Editor.AppendNativePlayer(ref people, ref server, ref client, newPlayer, players);
        Require(BitConverter.ToInt32(people, 8) == originalCount + 1, "Creation did not increase the native player count.");
        firstArguments = new object[] { server, 0, 0 };
        firstNames = (Dictionary<int, string>)Call("ParseFirstNames", firstArguments);
        lastArguments = new object[] { server, firstArguments[2], null, 0 };
        lastNames = (Dictionary<int, string>)Call("ParseSurnames", lastArguments);
        commonNames = (Dictionary<int, string>)Call("ParseCommonNames", server, lastArguments[3]);
        details = (Dictionary<int, FM08_Database_Editor.PersonDetails>)Call("ParsePersonData", people, firstNames, lastNames, commonNames, clubs);
        var reopened = (List<FM08_Database_Editor.PlayerRecord>)Call("BuildPlayerList", people, details, new Dictionary<int, string[]>(), new Dictionary<int, string>(), clubs, nations);
        var persisted = reopened.Find(player => player.Id == newPlayer.Id);
        Require(persisted != null && persisted.FirstName == newPlayer.FirstName && persisted.LastName == newPlayer.LastName, "Created native player did not persist.");
        Require(persisted.CA == 90 && persisted.PA == 130 && persisted.PosST == 20 && persisted.RightFoot == 20, "Created player attributes did not persist.");
        Require(reopened.Exists(player => player.Id == 11133 && player.LastName == "Buffon" && player.PosGK == 20), "Creating a player changed Buffon.");
        Require(reopened.Exists(player => player.Id == 1394631309 && player.LastName == "Imienia"), "Creating a player replaced the official sample.");
        Require(reopened.Count == players.Count + 1, "Creation changed the number of unrelated players.");
        var secondPlayer = FM08_Database_Editor.CreateNewPlayer(0);
        secondPlayer.FirstName = "NativeProbeSecond";
        secondPlayer.LastName = "NativeProbeLast";
        secondPlayer.Nationality = "";
        FM08_Database_Editor.AppendNativePlayer(ref people, ref server, ref client, secondPlayer, reopened);
        Require(secondPlayer.Id != newPlayer.Id, "Repeated creation reused a native identity.");
        byte[] surnameBytes = System.Text.Encoding.Unicode.GetBytes(newPlayer.LastName);
        int serverSurname = (int)Call("FindNativeBytes", server, surnameBytes);
        int clientSurname = (int)Call("FindNativeBytes", client, surnameBytes);
        Require(serverSurname >= 0 && clientSurname >= 0, "Shared surname is missing.");
        Require(BitConverter.ToUInt16(server, serverSurname + surnameBytes.Length + 2) == 2, "Shared surname reference count is not two in server data.");
        Require(BitConverter.ToUInt16(client, clientSurname + surnameBytes.Length + 2) == 2, "Shared surname reference count is not two in client data.");
        Require(people[persisted.T89Offset + 31] == 20 && people[reopened.Find(player => player.Id == 11133).T89Offset + 9] == 20, "Repeated creation invalidated existing player offsets.");
        var scheduled = reopened.Find(player => player.Id == 11133);
        scheduled.RetirementDate = new DateTime(2007, 9, 30);
        server = FM08_Database_Editor.SyncRetirements(server, reopened);
        Require(FM08_Database_Editor.ParseRetirements(server)[11133] == scheduled.RetirementDate.Value, "Native fixture retirement did not persist.");
        Console.WriteLine("PASS: native structural creation, new names, persisted CA/PA/positions and preserved existing identities. New UID=" + newPlayer.Id);
        Console.WriteLine("PASS: repeated creation and Buffon retirement in the generated database. Second UID=" + secondPlayer.Id);
        if (!string.IsNullOrEmpty(outputDirectory))
        {
            Require(!Directory.Exists(outputDirectory), "Output directory already exists; refusing to overwrite it.");
            Directory.CreateDirectory(outputDirectory);
            foreach (string sourceFile in Directory.GetFiles(directory))
            {
                string filename = Path.GetFileName(sourceFile);
                if (filename.EndsWith(".xml", StringComparison.OrdinalIgnoreCase)) continue;
                File.Copy(sourceFile, Path.Combine(outputDirectory, filename));
            }
            string[] filenames = { "people_db.dat", "server_db.dat", "client_db.dat" };
            byte[][] buffers = { people, server, client };
            for (int index = 0; index < filenames.Length; index++)
            {
                byte[] original = File.ReadAllBytes(Path.Combine(directory, filenames[index]));
                byte[] compressed = (byte[])Call("CompressFile", buffers[index], original);
                string path = Path.Combine(outputDirectory, filenames[index]);
                File.WriteAllBytes(path, compressed);
                byte[] verified = (byte[])Call("DecompressFile", path);
                Require(verified.Length == buffers[index].Length, "Compressed output length changed.");
                for (int position = 0; position < verified.Length; position++)
                    Require(verified[position] == buffers[index][position], "Compressed output did not round-trip.");
            }
            var metadata = new System.Xml.XmlDocument();
            metadata.LoadXml("<properties version='1.0'><string id='name' value=''/><string id='required_version' value='8.0.2'/></properties>");
            metadata.DocumentElement.FirstChild.Attributes["value"].Value = Path.GetFileName(outputDirectory);
            metadata.Save(Path.Combine(outputDirectory, Path.GetFileName(outputDirectory) + ".xml"));
            Console.WriteLine("PASS: test database written and compressed files verified: " + outputDirectory);
        }
    }

    private static void CheckClubAssignments(string directory)
    {
        byte[] server = (byte[])Call("DecompressFile", Path.Combine(directory, "server_db.dat"));
        byte[] people = (byte[])Call("DecompressFile", Path.Combine(directory, "people_db.dat"));
        object[] firstArguments = { server, 0, 0 };
        var firstNames = (Dictionary<int, string>)Call("ParseFirstNames", firstArguments);
        object[] lastArguments = { server, firstArguments[2], null, 0 };
        var lastNames = (Dictionary<int, string>)Call("ParseSurnames", lastArguments);
        var commonNames = (Dictionary<int, string>)Call("ParseCommonNames", server, lastArguments[3]);
        var clubs = (Dictionary<int, string>)Call("ParseClubs", server);
        var nations = (Dictionary<int, string>)Call("ParseNations", server);
        var details = (Dictionary<int, FM08_Database_Editor.PersonDetails>)Call("ParsePersonData", people, firstNames, lastNames, commonNames, clubs);
        var players = (List<FM08_Database_Editor.PlayerRecord>)Call("BuildPlayerList", people, details, new Dictionary<int, string[]>(), new Dictionary<int, string>(), clubs, nations);
        FM08_Database_Editor.ClubsRev.Clear();
        FM08_Database_Editor.ClubsRev["Juventus"] = 995;
        FM08_Database_Editor.ClubsRev["Test destination"] = 996;
        var knownReferences = new Dictionary<int, int> {
            { 956, 779 }, { 963, 786 }, { 992, 815 }, { 995, 818 }, { 1006, 829 }, { 1011, 834 }
        };
        var references = FM08_Database_Editor.ResolveNativeClubContractReferences(
            server, BitConverter.ToInt32(people, 0), knownReferences.Keys.Concat(new[] { 996 }));
        foreach (var known in knownReferences)
        {
            Require(references[known.Key] == known.Value, "Contract club differs from independent SI reference.");
            var samples = players.Where(p => p.Id < 1600000000 && p.ClubId == known.Key &&
                p.ContractExpiresOffset > 0).Take(2).ToList();
            Require(samples.Count == 2, "Missing independent SI contract samples.");
            foreach (var sample in samples)
                Require(BitConverter.ToInt32(people, sample.ContractExpiresOffset - 10) == known.Value,
                    "Resolver differs from untouched SI main contract: " + sample.FullName);
        }
        var nativeRecords = FM08_Database_Editor.ParseNativeClubDivisions(server, BitConverter.ToInt32(people, 0));
        byte[] corruptServer = (byte[])server.Clone();
        BitConverter.GetBytes(815).CopyTo(corruptServer, nativeRecords[956].Footer - 14);
        bool badReferenceRejected = false;
        try { FM08_Database_Editor.ResolveNativeClubContractReferences(corruptServer, BitConverter.ToInt32(people, 0), new[] { 956 }); }
        catch (InvalidDataException) { badReferenceRejected = true; }
        Require(badReferenceRejected, "A foreign NAME-TREE family must not be accepted for a regular club.");
        Console.WriteLine("PASS: six club references match twelve independent SI contracts; foreign family rejected.");
        var target = players.Find(player => player.Id == 1600000006);
        Require(target != null && target.ClubId == 0, "Expected the second probe to be free in the official control.");
        target.WeeklyWage = 1000;
        target.ContractDetailsPending = true;
        byte[] rejectedPeople = people;
        byte[] rejectedServer = server;
        bool freeWageRejected = false;
        try { FM08_Database_Editor.SyncClubAssignments(ref rejectedPeople, ref rejectedServer, players); }
        catch (InvalidDataException) { freeWageRejected = true; }
        Require(freeWageRejected && object.ReferenceEquals(people, rejectedPeople) && object.ReferenceEquals(server, rejectedServer), "Wages without a club must not silently disappear.");
        target.WeeklyWage = 0;
        target.ContractDetailsPending = false;
        FM08_Database_Editor.ClubsRev["Missing native club"] = int.MaxValue;
        FM08_Database_Editor.UpdatePlayerClub(target, people, "Missing native club");
        byte[] missingPeople = people, missingServer = server;
        bool missingClubRejected = false;
        try { FM08_Database_Editor.SyncClubAssignments(ref missingPeople, ref missingServer, players); }
        catch (InvalidDataException) { missingClubRejected = true; }
        Require(missingClubRejected && object.ReferenceEquals(missingPeople, people) &&
            object.ReferenceEquals(missingServer, server) && target.ClubAssignmentPending,
            "Missing native contract clubs must fail atomically.");
        byte[] sourcePeople = people;
        byte[] sourceServer = server;
        FM08_Database_Editor.csvFieldsByName["Club"].Setter(target, people, "Juventus");
        Require(object.ReferenceEquals(sourcePeople, people) && target.ClubId == 0 && target.ClubAssignmentPending, "Club edits must be staged, not overwrite the old club.");
        byte[] ambiguousServer = (byte[])server.Clone();
        BitConverter.GetBytes(818).CopyTo(ambiguousServer, 16);
        BitConverter.GetBytes(1139).CopyTo(ambiguousServer, 20);
        byte[] ambiguousSnapshot = ambiguousServer, ambiguousPeople = people;
        bool ambiguousRejected = false;
        try { FM08_Database_Editor.SyncClubAssignments(ref ambiguousPeople, ref ambiguousServer, players); }
        catch (InvalidDataException) { ambiguousRejected = true; }
        Require(ambiguousRejected && object.ReferenceEquals(ambiguousPeople, people) &&
            object.ReferenceEquals(ambiguousServer, ambiguousSnapshot) && target.ClubAssignmentPending,
            "Ambiguous NAME-TREE identities must fail atomically.");
        Console.WriteLine("PASS: missing clubs and ambiguous NAME-TREE references reject the whole write atomically.");
        FM08_Database_Editor.SyncClubAssignments(ref people, ref server, players);
        Require(target.ClubId == 995 && !target.ClubAssignmentPending && people.Length == sourcePeople.Length + 65, "Creating the club contract failed.");
        string expected = Path.Combine(Path.GetDirectoryName(directory), "TEST_FMEXT_JUVE_NATIVE");
        byte[] provenPeople = (byte[])Call("DecompressFile", Path.Combine(expected, "people_db.dat"));
        int provenStart = (int)Call("FindNativeBytes", provenPeople, BitConverter.GetBytes(target.Id), 0, -1) + 4 - 299;
        int generatedStart = target.PersonOffset - 15;
        for (int offset = 0; offset < 299; offset++)
            if (offset < 125 || offset >= 137)
            {
                byte expectedByte = offset == 200 ? (byte)1 :
                    offset >= 230 && offset < 234 ? BitConverter.GetBytes(818)[offset - 230] : provenPeople[provenStart + offset];
                Require(people[generatedStart + offset] == expectedByte, "Person differs from the legacy layout with corrected primary type/club at " + offset);
            }
        byte[] provenServer = (byte[])Call("DecompressFile", Path.Combine(expected, "server_db.dat"));
        int roster = (int)Call("FindNativeClubRoster", server, 995, BitConverter.ToInt32(people, 0));
        int provenRoster = (int)Call("FindNativeClubRoster", provenServer, 995, BitConverter.ToInt32(people, 0));
        Require(BitConverter.ToUInt16(server, roster) == BitConverter.ToUInt16(provenServer, provenRoster), "Runtime-proven roster count differs.");
        for (int offset = 0; offset < 2 + BitConverter.ToUInt16(server, roster) * 4; offset++)
            Require(server[roster + offset] == provenServer[provenRoster + offset], "Runtime-proven roster member differs.");
        Console.WriteLine("PASS: primary contract retains the legacy person/roster layout; primary semantics are checked separately against controlled SI B.");
        byte[] legacyPeople = (byte[])people.Clone();
        int legacyPayload = target.ClubIdOffset + 28;
        legacyPeople[legacyPayload + 1] = 5;
        BitConverter.GetBytes(43450).CopyTo(legacyPeople, legacyPayload + 35);
        BitConverter.GetBytes((ushort)181).CopyTo(legacyPeople, legacyPayload + 39);
        BitConverter.GetBytes((ushort)2012).CopyTo(legacyPeople, legacyPayload + 41);
        var legacyDetails = (Dictionary<int, FM08_Database_Editor.PersonDetails>)Call("ParsePersonData", legacyPeople, firstNames, lastNames, commonNames, clubs);
        var legacyDecoded = legacyDetails[BitConverter.ToInt32(legacyPeople, target.PersonOffset)];
        Require(legacyDecoded.ContractExpires == new DateTime(2012, 6, 30) && legacyDecoded.ContractExpiresOffset == legacyPayload + 41 &&
            legacyDecoded.WeeklyWage == 43450 && legacyDecoded.SquadNumber == 255, "A first block with byte 5 must be read as the main contract.");
        var legacyTarget = new FM08_Database_Editor.PlayerRecord {
            Id = target.Id, PersonOffset = target.PersonOffset, ClubIdOffset = target.ClubIdOffset,
            ClubId = 995, Club = "Juventus", ContractDetailsPending = true, WeeklyWage = 10000
        };
        byte[] legacyServer = server;
        var legacyPlayers = new List<FM08_Database_Editor.PlayerRecord> { legacyTarget };
        FM08_Database_Editor.SyncClubAssignments(ref legacyPeople, ref legacyServer, legacyPlayers);
        Require(BitConverter.ToInt32(legacyPeople, legacyPayload + 35) == 10000 &&
            BitConverter.ToUInt16(legacyPeople, legacyPayload + 41) == 2012, "Legacy primary detail edit failed.");
        Console.WriteLine("PASS: first-block byte 5 is decoded and edited as a main contract, not misclassified as ownership.");
        byte[] preservedContract = new byte[65];
        Buffer.BlockCopy(legacyPeople, legacyPayload, preservedContract, 0, 65);
        FM08_Database_Editor.UpdatePlayerClub(legacyTarget, legacyPeople, "Test destination");
        FM08_Database_Editor.SyncClubAssignments(ref legacyPeople, ref legacyServer, legacyPlayers);
        Require(legacyTarget.ClubId == 996 && legacyTarget.ContractExpiresOffset == legacyPayload + 41, "Legacy primary transfer failed.");
        for (int offset = 0; offset < 65; offset++)
            Require(legacyPeople[legacyPayload + offset] == (offset >= 31 && offset < 35 ?
                BitConverter.GetBytes(references[996])[offset - 31] : preservedContract[offset]),
                "Pure transfer changed contract fields other than the main club reference.");
        FM08_Database_Editor.UpdatePlayerClub(legacyTarget, legacyPeople, "CLEAR");
        FM08_Database_Editor.SyncClubAssignments(ref legacyPeople, ref legacyServer, legacyPlayers);
        Require(legacyPeople.Length == sourcePeople.Length && legacyServer.Length == sourceServer.Length, "Legacy primary transfer/release changed unexpected sizes.");
        for (int offset = 0; offset < sourcePeople.Length; offset++) Require(legacyPeople[offset] == sourcePeople[offset], "Legacy primary release changed unrelated person bytes.");
        for (int offset = 0; offset < sourceServer.Length; offset++) Require(legacyServer[offset] == sourceServer[offset], "Legacy primary transfer changed unrelated roster bytes.");
        Console.WriteLine("PASS: legacy-primary transfer changes only the main club reference; release restores person/roster bytes exactly.");
        for (int header = 0; header <= 5; header += 5)
        {
            int contract = target.ClubIdOffset + 28;
            byte[] variantPeople = header == 0 ? (byte[])people.Clone() : (byte[])Call("InsertNativeBytes", people, contract, new byte[] { 0xA1, 0xB2, 0xC3, 0xD4, 0xE5 });
            byte[] variantServer = server;
            var variant = new FM08_Database_Editor.PlayerRecord {
                Id = target.Id, PersonOffset = target.PersonOffset, ClubIdOffset = target.ClubIdOffset,
                ClubId = 995, Club = "Juventus", FirstName = target.FirstName, LastName = target.LastName
            };
            var variantPlayers = new List<FM08_Database_Editor.PlayerRecord> { variant };
            var fieldsForVariant = FM08_Database_Editor.csvFieldsByName;
            fieldsForVariant["WeeklyWage"].Setter(variant, null, "123456");
            fieldsForVariant["SquadNumber"].Setter(variant, null, "23");
            fieldsForVariant["ContractExpires"].Setter(variant, null, "29.02.2028");
            FM08_Database_Editor.SyncClubAssignments(ref variantPeople, ref variantServer, variantPlayers);
            Require(variant.ContractExpiresOffset == contract + header + 41, "Expiry model offset missed the optional header.");
            Require(BitConverter.ToUInt16(variantPeople, variant.ContractExpiresOffset) == 2028, "Post-2025 expiry was not written.");
            Require(BitConverter.ToInt32(variantPeople, contract + header + 35) == 123456 && variantPeople[contract + header + 60] == 23, "Contract detail edits were not written.");
            var variantDetails = (Dictionary<int, FM08_Database_Editor.PersonDetails>)Call("ParsePersonData", variantPeople, firstNames, lastNames, commonNames, clubs);
            var decoded = variantDetails[BitConverter.ToInt32(variantPeople, variant.PersonOffset)];
            Require(decoded.ContractExpires == new DateTime(2028, 2, 29) && decoded.WeeklyWage == 123456 && decoded.SquadNumber == 23, "Native contract fields did not reparse exactly.");
            fieldsForVariant["WeeklyWage"].Setter(variant, null, "0");
            fieldsForVariant["SquadNumber"].Setter(variant, null, "0");
            FM08_Database_Editor.SyncClubAssignments(ref variantPeople, ref variantServer, variantPlayers);
            Require(BitConverter.ToInt32(variantPeople, contract + header + 35) == 0 && variantPeople[contract + header + 60] == 255, "Zero wage or cleared jersey was ignored.");
            Require(variant.ContractExpires == new DateTime(2028, 2, 29), "Detail-only edit changed the expiry.");
            fieldsForVariant["ContractExpires"].Setter(variant, null, "CLEAR");
            FM08_Database_Editor.SyncClubAssignments(ref variantPeople, ref variantServer, variantPlayers);
            Require(BitConverter.ToUInt16(variantPeople, contract + header + 39) == 0 && BitConverter.ToUInt16(variantPeople, variant.ContractExpiresOffset) == 1900, "Cleared expiry lost its native sentinel.");
            byte[] beforeTransfer = new byte[65 + header];
            Buffer.BlockCopy(variantPeople, contract, beforeTransfer, 0, beforeTransfer.Length);
            FM08_Database_Editor.UpdatePlayerClub(variant, variantPeople, "Test destination");
            FM08_Database_Editor.SyncClubAssignments(ref variantPeople, ref variantServer, variantPlayers);
            for (int i = 0; i < beforeTransfer.Length; i++)
                Require(variantPeople[contract + i] == (i >= header + 31 && i < header + 35 ?
                    BitConverter.GetBytes(references[996])[i - header - 31] : beforeTransfer[i]),
                    "Optional-header transfer changed unrelated contract bytes.");
            FM08_Database_Editor.UpdatePlayerClub(variant, variantPeople, "CLEAR");
            FM08_Database_Editor.SyncClubAssignments(ref variantPeople, ref variantServer, variantPlayers);
            Require(variantPeople.Length == sourcePeople.Length && variantServer.Length == sourceServer.Length && variant.SquadNumber == 0, "Release removed the wrong contract length.");
            for (int position = 0; position < sourcePeople.Length; position++) Require(variantPeople[position] == sourcePeople[position], "Variant release changed unrelated person bytes.");
            for (int position = 0; position < sourceServer.Length; position++) Require(variantServer[position] == sourceServer[position], "Variant release changed unrelated roster bytes.");
        }
        Console.WriteLine("PASS: 65-byte and synthetic 70-byte layouts support exact readback, leap-day expiry, wages, jersey clearing and byte-exact release.");
        byte[] malformedPeople = (byte[])people.Clone();
        BitConverter.GetBytes(-123).CopyTo(malformedPeople, target.ClubIdOffset + 28 + 26);
        byte[] malformedSource = malformedPeople;
        byte[] unchangedServer = server;
        target.ContractExpiresPending = true;
        bool malformedRejected = false;
        try { FM08_Database_Editor.SyncClubAssignments(ref malformedPeople, ref unchangedServer, players); }
        catch (InvalidDataException) { malformedRejected = true; }
        Require(malformedRejected && object.ReferenceEquals(malformedPeople, malformedSource) && object.ReferenceEquals(unchangedServer, server) && target.ContractExpiresPending, "Unsupported contract must fail atomically without clearing pending changes.");
        target.ContractExpiresPending = false;
        Console.WriteLine("PASS: unsupported contract owners fail atomically instead of reporting a partial transfer.");
        FM08_Database_Editor.UpdatePlayerClub(target, people, "Test destination");
        FM08_Database_Editor.SyncClubAssignments(ref people, ref server, players);
        Require(target.ClubId == 996 && people.Length == sourcePeople.Length + 65, "Transfer must retain the existing contract block.");
        byte[] bulkPeople = people, bulkServer = server;
        FM08_Database_Editor.ReleaseNativePlayersBulk(ref bulkPeople, ref bulkServer, players, new HashSet<int> { target.Id });
        FM08_Database_Editor.UpdatePlayerClub(target, people, "CLEAR");
        FM08_Database_Editor.SyncClubAssignments(ref people, ref server, players);
        Require(bulkPeople.SequenceEqual(people) && bulkServer.SequenceEqual(server),
            "Bulk release differs from the controlled single-contract release.");
        Require(target.ClubId == 0 && people.Length == sourcePeople.Length && server.Length == sourceServer.Length, "Releasing a player must remove the contract and roster entry.");
        for (int position = 0; position < people.Length; position++) Require(people[position] == sourcePeople[position], "Release failed to restore the free player data.");
        for (int position = 0; position < server.Length; position++) Require(server[position] == sourceServer[position], "Transfer/release changed unrelated roster data.");
        Console.WriteLine("PASS: transfer between club rosters and release restore the original free-player database exactly.");
        var buffon = players.Find(player => player.Id == 11133);
        Console.WriteLine("Existing contract: " + buffon.FullName + ", club=" + buffon.ClubId + ", club offset=" + buffon.ClubIdOffset + ", person=" + buffon.PersonOffset);
        Require(buffon.ClubId == 995, "Buffon club was not read correctly.");
        FM08_Database_Editor.UpdatePlayerClub(buffon, people, "Test destination");
        FM08_Database_Editor.SyncClubAssignments(ref people, ref server, players);
        Require(buffon.ClubId == 996 && people.Length == sourcePeople.Length, "Existing-player transfer changed the record length.");
        Require(people[buffon.T89Offset + 9] == 20, "Transfer changed Buffon's goalkeeper ability.");
        FM08_Database_Editor.UpdatePlayerContract(buffon, people, new DateTime(2012, 6, 30));
        FM08_Database_Editor.SyncClubAssignments(ref people, ref server, players);
        Require(BitConverter.ToUInt16(people, buffon.ContractExpiresOffset) == 2012, "Contract expiry without club change did not persist.");
        Console.WriteLine("PASS: existing Buffon contract transfers safely; expiry-only edits persist without moving the player again.");
        var budan = players.Find(player => player.Id == 104104);
        Require(budan != null && budan.ClubIdOffset > 0, "Native multi-contract reference was not read.");
        int budanContract = budan.ClubIdOffset + 28;
        Require(people[budanContract - 1] == 2, "Budan must have two native contracts, not a boolean presence flag.");
        byte[] ownershipContract = new byte[65];
        Buffer.BlockCopy(people, budanContract + 65, ownershipContract, 0, 65);
        Require(people[budanContract + 1] == 5 && ownershipContract[1] == 1, "Budan must have primary followed by a coownership block, as confirmed by SI removal.");
        Require(budan.ContractExpiresOffset == budanContract + 41 && budan.ContractExpires == new DateTime(2012, 6, 30) && budan.SquadNumber == 20, "Reader differs from Budan's main contract shown in SI.");
        int beforeBudanLength = people.Length;
        FM08_Database_Editor.UpdatePlayerContract(budan, people, new DateTime(2016, 6, 30));
        FM08_Database_Editor.csvFieldsByName["WeeklyWage"].Setter(budan, null, "87654");
        FM08_Database_Editor.csvFieldsByName["SquadNumber"].Setter(budan, null, "17");
        FM08_Database_Editor.SyncClubAssignments(ref people, ref server, players);
        Require(people.Length == beforeBudanLength && BitConverter.ToUInt16(people, budan.ContractExpiresOffset) == 2016, "Editing a multi-contract expiry changed record size or missed the primary contract.");
        for (int offset = 0; offset < 65; offset++) Require(people[budanContract + 65 + offset] == ownershipContract[offset], "Editing the primary contract changed ownership fields.");
        Require(BitConverter.ToInt32(people, budanContract + 35) == 87654 && people[budanContract + 60] == 17, "Primary wage or jersey was written into ownership.");
        FM08_Database_Editor.UpdatePlayerClub(budan, people, "Test destination");
        FM08_Database_Editor.SyncClubAssignments(ref people, ref server, players);
        Require(BitConverter.ToInt32(people, budanContract + 31) == references[996], "Coowned primary transfer retained the old club reference.");
        for (int offset = 0; offset < 65; offset++)
            Require(people[budanContract + 65 + offset] == ownershipContract[offset], "Transfer changed secondary coownership.");
        byte[] beforeBudanRelease = people;
        bulkPeople = people;
        bulkServer = server;
        FM08_Database_Editor.ReleaseNativePlayersBulk(ref bulkPeople, ref bulkServer, players, new HashSet<int> { budan.Id });
        FM08_Database_Editor.UpdatePlayerClub(budan, people, "CLEAR");
        FM08_Database_Editor.SyncClubAssignments(ref people, ref server, players);
        Require(bulkPeople.SequenceEqual(people) && bulkServer.SequenceEqual(server),
            "Bulk release differs from the real two-contract/coownership release.");
        Require(people.Length == beforeBudanLength - 130 && people[budanContract - 1] == 0, "Multi-contract release must remove all counted entries.");
        for (int offset = budanContract; offset < people.Length; offset++) Require(people[offset] == beforeBudanRelease[offset + 130], "Multi-contract release damaged trailing clauses or other records.");
        Console.WriteLine("PASS: real SI Budan two-contract record edits its primary entry only and releases all 130 bytes without damaging its tail.");
        byte[] client = (byte[])Call("DecompressFile", Path.Combine(directory, "client_db.dat"));
        var added = FM08_Database_Editor.CreateNewPlayer(0);
        var fields = FM08_Database_Editor.csvFieldsByName;
        fields["FirstName"].Setter(added, null, "GuiImportProbe");
        fields["LastName"].Setter(added, null, "ClubRetirement");
        fields["Club"].Setter(added, null, "Juventus");
        fields["RetireDate"].Setter(added, null, "30.09.2007");
        fields["ContractExpires"].Setter(added, null, "30.06.2010");
        fields["WeeklyWage"].Setter(added, null, "45000");
        fields["SquadNumber"].Setter(added, null, "17");
        FM08_Database_Editor.AppendNativePlayer(ref people, ref server, ref client, added, players);
        players.Add(added);
        FM08_Database_Editor.SyncClubAssignments(ref people, ref server, players);
        server = FM08_Database_Editor.SyncRetirements(server, players);
        Require(added.ClubId == 995 && BitConverter.ToUInt16(people, added.ContractExpiresOffset) == 2010, "New imported player's club/contract did not persist.");
        Require(BitConverter.ToInt32(people, added.ClubIdOffset + 28 + 35) == 45000 && people[added.ClubIdOffset + 28 + 60] == 17, "Appending a CSV player discarded the imported contract details.");
        Require(people[added.ClubIdOffset + 28 + 1] == 1 &&
            BitConverter.ToInt32(people, added.ClubIdOffset + 28 + 31) == 818,
            "New CSV contract does not reference Juventus's NAME-TREE entry.");
        Require(FM08_Database_Editor.ParseRetirements(server)[added.Id] == new DateTime(2007, 9, 30), "New imported player's retirement did not persist.");
        Require(people[added.T89Offset + 31] == 20 && people[buffon.T89Offset + 9] == 20, "New imported contract invalidated player attribute offsets.");
        Console.WriteLine("PASS: new player created through CSV setters preserves club, contract expiry, retirement, and existing player offsets.");
    }

    private static void CheckControlledContract(string sourceDirectory, string expectedDirectory)
    {
        const int identity = 1800003674;
        byte[] people = (byte[])Call("DecompressFile", Path.Combine(sourceDirectory, "people_db.dat"));
        byte[] server = (byte[])Call("DecompressFile", Path.Combine(sourceDirectory, "server_db.dat"));
        byte[] expectedPeople = (byte[])Call("DecompressFile", Path.Combine(expectedDirectory, "people_db.dat"));
        byte[] expectedServer = (byte[])Call("DecompressFile", Path.Combine(expectedDirectory, "server_db.dat"));
        int expectedEnd = (int)Call("FindNativeBytes", expectedPeople, BitConverter.GetBytes(identity), 0, -1) + 4;
        int expectedStart = expectedEnd - 299;
        Require(expectedStart >= 16 && expectedPeople[expectedStart + 4] == 2 && expectedPeople[expectedStart + 200] == 1 && expectedPeople[expectedStart + 230] == 47, "Expected the independently verified SI primary-contract reference B.");
        int club = BitConverter.ToInt32(expectedPeople, expectedStart + 171);
        object[] firstArguments = { server, 0, 0 };
        var firstNames = (Dictionary<int, string>)Call("ParseFirstNames", firstArguments);
        object[] lastArguments = { server, firstArguments[2], null, 0 };
        var lastNames = (Dictionary<int, string>)Call("ParseSurnames", lastArguments);
        var commonNames = (Dictionary<int, string>)Call("ParseCommonNames", server, lastArguments[3]);
        var clubs = (Dictionary<int, string>)Call("ParseClubs", server);
        var nations = (Dictionary<int, string>)Call("ParseNations", server);
        var details = (Dictionary<int, FM08_Database_Editor.PersonDetails>)Call("ParsePersonData", people, firstNames, lastNames, commonNames, clubs);
        var players = (List<FM08_Database_Editor.PlayerRecord>)Call("BuildPlayerList", people, details, new Dictionary<int, string[]>(), new Dictionary<int, string>(), clubs, nations);
        var target = players.Find(player => player.Id == identity);
        Require(target != null && target.ClubId == 0 && clubs.ContainsKey(club), "Controlled free player A or destination club was not read.");
        FM08_Database_Editor.ClubsRev.Clear();
        FM08_Database_Editor.ClubsRev[clubs[club]] = club;
        byte[] originalPeople = people;
        byte[] originalServer = server;
        int start = target.PersonOffset - 15;
        var fields = FM08_Database_Editor.csvFieldsByName;
        fields["Club"].Setter(target, people, clubs[club]);
        fields["ContractExpires"].Setter(target, people, "30.06.2008");
        fields["WeeklyWage"].Setter(target, people, "10000");
        FM08_Database_Editor.SyncClubAssignments(ref people, ref server, players);
        Require(people.Length == originalPeople.Length + 65 && server.Length == originalServer.Length + 4, "Shared serializer changed unexpected section sizes.");
        for (int offset = 0; offset < 299; offset++)
            Require(people[start + offset] == expectedPeople[expectedStart + offset], "Shared importer differs from confirmed SI B at person byte " + offset);
        for (int offset = 0; offset < start; offset++)
            Require(people[offset] == originalPeople[offset], "Shared importer changed an earlier record.");
        for (int offset = start + 299; offset < people.Length; offset++)
            Require(people[offset] == originalPeople[offset - 65], "Shared importer changed a later record.");
        int roster = (int)Call("FindNativeClubRoster", server, club, BitConverter.ToInt32(people, 0));
        int expectedRoster = (int)Call("FindNativeClubRoster", expectedServer, club, BitConverter.ToInt32(expectedPeople, 0));
        int count = BitConverter.ToUInt16(expectedServer, expectedRoster);
        for (int offset = 0; offset < 2 + count * 4; offset++)
            Require(server[roster + offset] == expectedServer[expectedRoster + offset], "Shared importer roster differs from confirmed SI B.");
        var writtenDetails = (Dictionary<int, FM08_Database_Editor.PersonDetails>)Call("ParsePersonData", people, firstNames, lastNames, commonNames, clubs);
        var written = writtenDetails[BitConverter.ToInt32(people, target.PersonOffset)];
        Require(written.ContractExpires == new DateTime(2008, 6, 30) && written.WeeklyWage == 10000 && written.SquadNumber == 255 && written.ContractExpiresOffset == start + 240, "Shared importer output does not read back as the confirmed primary contract.");
        Console.WriteLine("PASS: actual shared CSV serializer reproduces all 299 SI B person bytes and the complete native roster, preserving all other person records.");
    }

    private static void CheckControlledLoans(string sourceDirectory, string referenceDirectory)
    {
        byte[] people = (byte[])Call("DecompressFile", Path.Combine(sourceDirectory, "people_db.dat"));
        byte[] server = (byte[])Call("DecompressFile", Path.Combine(sourceDirectory, "server_db.dat"));
        byte[] reference = (byte[])Call("DecompressFile", Path.Combine(referenceDirectory, "server_db.dat"));
        int persons = BitConverter.ToInt32(people, 0);
        byte[] identity = new byte[8];
        BitConverter.GetBytes(140364).CopyTo(identity, 0);
        BitConverter.GetBytes(5250624).CopyTo(identity, 4);
        Require((int)Call("FindNativeBytes", people, identity, 0, -1) >= 0, "Controlled Jimenez person identity missing.");
        var loans = FM08_Database_Editor.ParseNativeLoans(server, persons);
        Require(loans.Count == 6210 && loans.FindAll(loan => loan.PersonIndex == 140364 && loan.ClubId == 992).Count == 1,
            "Controlled Jimenez loan was not read.");
        int header = (int)Call("FindNativeLoanTable", server, persons);
        int referenceHeader = (int)Call("FindNativeLoanTable", reference, persons);
        var selected = new HashSet<int> { 140364 };
        byte[] updated = FM08_Database_Editor.RemoveNativeLoans(server, persons, selected);
        Require(updated.Length == server.Length - 32, "Loan cancellation must remove exactly 32 bytes.");
        int length = 4 + (loans.Count - 1) * 32;
        for (int offset = 0; offset < length; offset++)
            Require(updated[header + offset] == reference[referenceHeader + offset],
                "Shared loan serializer differs from independently saved SI B.");
        for (int offset = 0; offset < header; offset++)
            Require(updated[offset] == server[offset], "Loan cancellation changed data before the table.");
        for (int offset = header + length; offset < updated.Length; offset++)
            Require(updated[offset] == server[offset + 32], "Loan cancellation changed data after the table.");
        Require(FM08_Database_Editor.ParseNativeLoans(updated, persons).FindAll(loan => selected.Contains(loan.PersonIndex)).Count == 0,
            "Cancelled loan remains in native table.");
        selected.Add(3461);
        byte[] multiple = FM08_Database_Editor.RemoveNativeLoans(server, persons, selected);
        var retained = FM08_Database_Editor.ParseNativeLoans(multiple, persons);
        int removed = loans.FindAll(loan => selected.Contains(loan.PersonIndex)).Count;
        Require(retained.Count == loans.Count - removed && retained.FindAll(loan => selected.Contains(loan.PersonIndex)).Count == 0,
            "Multiple loan cancellation failed.");
        Require(object.ReferenceEquals(server, FM08_Database_Editor.RemoveNativeLoans(server, persons, new HashSet<int>())),
            "Empty selection must leave the source unchanged.");
        bool rejected = false;
        try { FM08_Database_Editor.RemoveNativeLoans(server, persons, new HashSet<int> { persons }); }
        catch (InvalidDataException) { rejected = true; }
        Require(rejected && FM08_Database_Editor.ParseNativeLoans(server, persons).Count == loans.Count,
            "Invalid loan selection must fail without changing the source.");
        byte[] invalid = (byte[])server.Clone();
        BitConverter.GetBytes(persons).CopyTo(invalid, header + 5);
        rejected = false;
        try { FM08_Database_Editor.ParseNativeLoans(invalid, persons); }
        catch (InvalidDataException) { rejected = true; }
        Require(rejected, "Malformed loan table must not be accepted.");
        Console.WriteLine("PASS: shared native loan serializer exactly reproduces SI B, preserves unrelated bytes, removes multiple selected loans and rejects invalid inputs.");
    }

    private static void CheckCoownershipPrimary(string sourceDirectory, string referenceDirectory)
    {
        foreach (string directory in new string[] { sourceDirectory, referenceDirectory })
        {
            byte[] server = (byte[])Call("DecompressFile", Path.Combine(directory, "server_db.dat"));
            byte[] people = (byte[])Call("DecompressFile", Path.Combine(directory, "people_db.dat"));
            object[] firstArguments = { server, 0, 0 };
            var firstNames = (Dictionary<int, string>)Call("ParseFirstNames", firstArguments);
            object[] lastArguments = { server, firstArguments[2], null, 0 };
            var lastNames = (Dictionary<int, string>)Call("ParseSurnames", lastArguments);
            var commonNames = (Dictionary<int, string>)Call("ParseCommonNames", server, lastArguments[3]);
            var clubs = (Dictionary<int, string>)Call("ParseClubs", server);
            var details = (Dictionary<int, FM08_Database_Editor.PersonDetails>)Call("ParsePersonData", people, firstNames, lastNames, commonNames, clubs);
            FM08_Database_Editor.PersonDetails budan = null;
            foreach (var detail in details.Values)
                if (detail.UniqueId == 104104)
                {
                    Require(budan == null, "Ambiguous Budan identity.");
                    budan = detail;
                }
            Require(budan != null && budan.ContractExpires == new DateTime(2012, 6, 30) &&
                budan.WeeklyWage == 5651 && budan.SquadNumber == 20,
                "Main-contract reader differs from the independent SI coownership A/B samples.");
        }
        Console.WriteLine("PASS: Budan main date, wage and jersey match SI before and after coownership removal.");
    }

    private static void CheckU23LeagueAssignments(string sourceDirectory, string referenceDirectory)
    {
        byte[] source = (byte[])Call("DecompressFile", Path.Combine(sourceDirectory, "server_db.dat"));
        byte[] snapshot = (byte[])source.Clone();
        byte[] reference = (byte[])Call("DecompressFile", Path.Combine(referenceDirectory, "server_db.dat"));
        int personCount = BitConverter.ToInt32((byte[])Call("DecompressFile", Path.Combine(sourceDirectory, "people_db.dat")), 0);
        Require(personCount == BitConverter.ToInt32((byte[])Call("DecompressFile",
            Path.Combine(referenceDirectory, "people_db.dat")), 0), "Person count changed in the U23 league test.");
        Require(source.Length == reference.Length, "U23 league test must preserve server length.");
        var before = FM08_Database_Editor.ParseNativeClubDivisions(source, personCount);
        var saved = FM08_Database_Editor.ParseNativeClubDivisions(reference, personCount);
        Require(before.ContainsKey(23624) && saved.ContainsKey(23624), "Final native U23 club is missing.");
        var team = before[23624];
        Require(BitConverter.ToInt32(source, team.Footer + 4) == 1800000087 &&
            team.Footer + 8 - team.Start == 113, "Controlled U23 identity or length differs.");
        Require(BitConverter.ToInt32(source, team.Start + 87) == 9 &&
            BitConverter.ToInt32(source, team.Start + 91) == 815 &&
            BitConverter.ToUInt16(source, team.RosterOffset) == 0, "U23 type, parent or empty roster differs.");
        Require(before[8207].CurrentDivisionIndex == 26 && team.CurrentDivisionIndex == -1 &&
            saved[8207].CurrentDivisionIndex == -1 && saved[23624].CurrentDivisionIndex == 26,
            "Controlled Canavese/U23 destinations differ.");
        Require(before.Count == saved.Count, "Native club count changed during league assignment.");
        Require(before.Values.Count(record => record.CurrentDivisionIndex == 26) == 18 &&
            saved.Values.Count(record => record.CurrentDivisionIndex == 26) == 18, "C2/A must retain 18 clubs.");
        var expectedMembers = new HashSet<int>(before.Values.Where(record => record.CurrentDivisionIndex == 26)
            .Select(record => record.ClubIndex));
        Require(expectedMembers.Remove(8207) && expectedMembers.Add(23624), "Controlled replacement source differs.");
        Require(expectedMembers.SetEquals(saved.Values.Where(record => record.CurrentDivisionIndex == 26)
            .Select(record => record.ClubIndex)), "SI changed other C2/A participants.");
        byte[] generated = FM08_Database_Editor.ApplyClubLeagueChanges(source, personCount,
            new[] { LeagueChange(8207, 26, -1), LeagueChange(23624, -1, 26) });
        var after = FM08_Database_Editor.ParseNativeClubDivisions(generated, personCount);
        foreach (var record in after.Values)
        {
            FM08_Database_Editor.NativeClubDivisionRecord actual;
            Require(saved.TryGetValue(record.ClubIndex, out actual), "An SI native club identity disappeared.");
            Require(BitConverter.ToInt32(generated, record.Footer + 4) == BitConverter.ToInt32(reference, actual.Footer + 4) &&
                record.CurrentDivisionIndex == actual.CurrentDivisionIndex &&
                record.PreviousDivisionIndex == actual.PreviousDivisionIndex &&
                record.EuropeanCompetitionIndex == actual.EuropeanCompetitionIndex,
                "An SI club UID or competition field differs: " + record.ClubIndex);
        }
        foreach (int club in new[] { 8207, 23624, 992 })
        {
            var original = before[club];
            var expected = saved[club];
            int length = original.Footer + 8 - original.Start;
            Require(length == expected.Footer + 8 - expected.Start, "Controlled CLUB length differs.");
            for (int offset = 0; offset < length; offset++)
                Require(generated[original.Start + offset] == reference[expected.Start + offset],
                    "Complete CLUB record does not match SI: " + club + " at +" + offset);
        }
        Require(BitConverter.ToUInt16(generated, after[992].RosterOffset) == 25 &&
            after[992].CurrentDivisionIndex == 22, "Parent Inter roster or league changed.");
        foreach (var group in before.Values.GroupBy(record => record.CurrentDivisionIndex))
            Require(after.Values.Count(record => record.CurrentDivisionIndex == group.Key) == group.Count(),
                "A participant count changed.");
        int changedBytes = 0;
        for (int offset = 0; offset < source.Length; offset++)
            if (source[offset] != generated[offset])
            {
                changedBytes++;
                Require(new[] { 8207, 23624 }.Any(club => offset >= before[club].Start + 7 &&
                    offset < before[club].Start + 11), "U23 league write changed an unrelated byte.");
            }
        Require(changedBytes == 8, "The exact no-division swap must change eight physical bytes.");
        RejectLeagueChanges(source, personCount, LeagueChange(23624, -1, 26));
        RejectLeagueChanges(source, personCount, LeagueChange(23624, 26, -1), LeagueChange(8207, 26, -1));
        Require(FM08_Database_Editor.ApplyClubLeagueChanges(source, personCount,
            new[] { LeagueChange(23624, -1, -1) }).SequenceEqual(source), "Terminal CLUB no-op changed bytes.");

        int boundary = team.Footer + 8;
        byte[] badTag = (byte[])source.Clone();
        badTag[boundary + 4] = 2;
        Require(!FM08_Database_Editor.ParseNativeClubDivisions(badTag, personCount).ContainsKey(23624),
            "An invalid next-section tag was accepted as a terminal CLUB.");
        RejectLeagueChanges(badTag, personCount, LeagueChange(8207, 26, -1), LeagueChange(23624, -1, 26));
        byte[] badFooter = (byte[])source.Clone();
        int count = BitConverter.ToInt32(source, boundary);
        int cursor = boundary + 4;
        for (int index = 0; index < count; index++)
            cursor += 94 + BitConverter.ToInt32(source, cursor + 1) * 2;
        BitConverter.GetBytes(-1).CopyTo(badFooter, cursor - 8);
        Require(!FM08_Database_Editor.ParseNativeClubDivisions(badFooter, personCount).ContainsKey(23624),
            "A corrupt final next-section footer was not validated.");
        Require(!FM08_Database_Editor.ParseNativeClubDivisions(source.Take(boundary + 100).ToArray(), personCount)
            .ContainsKey(23624), "A truncated next section was accepted as a terminal CLUB.");
        Require(source.SequenceEqual(snapshot), "A test mutated the source sample.");
        Console.WriteLine("PASS: terminal U23 recognized; full Canavese/U23/Inter records match SI.");
        Console.WriteLine("PASS: C2/A 18 -> 18; every division count preserved; exactly 8 current-division bytes changed.");
        Console.WriteLine("PASS: U23 type/parent/empty roster and parent Inter's 25 players preserved.");
        Console.WriteLine("PASS: entire next section validated; corrupt tag/footer and truncation rejected; atomic/no-op checks passed.");
    }

    private static void CheckU23PlayerAssignment(string sourceDirectory, string referenceDirectory, string previousSaveDirectory)
    {
        const int index = 334478, uid = 1800000020;
        byte[][] peopleSamples = new[] { sourceDirectory, referenceDirectory, previousSaveDirectory }
            .Select(directory => (byte[])Call("DecompressFile", Path.Combine(directory, "people_db.dat"))).ToArray();
        int[] starts = new int[3];
        byte[] footerIdentity = BitConverter.GetBytes(index).Concat(BitConverter.GetBytes(uid)).ToArray();
        for (int sample = 0; sample < 3; sample++)
        {
            int footer = (int)Call("FindNativeBytes", peopleSamples[sample], footerIdentity, 0, -1);
            starts[sample] = footer + 8 - 299;
            Require(footer >= 0 && starts[sample] >= 16 &&
                BitConverter.ToInt32(peopleSamples[sample], starts[sample]) == index &&
                peopleSamples[sample][starts[sample] + 4] == 2, "Controlled Lautaro PERSON identity differs.");
            Require(BitConverter.ToInt32(peopleSamples[sample], 0) == BitConverter.ToInt32(peopleSamples[0], 0),
                "Controlled person count changed.");
        }
        byte[] sourcePeople = peopleSamples[0], referencePeople = peopleSamples[1];
        byte[] sourceServer = (byte[])Call("DecompressFile", Path.Combine(sourceDirectory, "server_db.dat"));
        byte[] referenceServer = (byte[])Call("DecompressFile", Path.Combine(referenceDirectory, "server_db.dat"));
        Require(BitConverter.ToInt32(sourcePeople, starts[0] + 171) == 992 &&
            BitConverter.ToInt32(referencePeople, starts[1] + 171) == 23624, "SI did not change the club pointer as expected.");
        var player = new FM08_Database_Editor.PlayerRecord {
            Id = uid, FirstName = "Lautaro", LastName = "Martinez", PersonOffset = starts[0] + 15,
            ClubId = 992, ClubIdOffset = starts[0] + 171, Club = "Inter"
        };
        // These SI-verified aliases are fixture setup, not production name resolution for generated U23 names.
        FM08_Database_Editor.ClubsRev["Inter"] = 992;
        FM08_Database_Editor.ClubsRev["Inter Under 23s"] = 23624;
        var fields = FM08_Database_Editor.csvFieldsByName;
        fields["Club"].Setter(player, sourcePeople, "Inter Under 23s");
        byte[] people = sourcePeople, server = sourceServer;
        FM08_Database_Editor.SyncClubAssignments(ref people, ref server,
            new List<FM08_Database_Editor.PlayerRecord> { player });
        Require(people.Length == sourcePeople.Length && server.Length == sourceServer.Length,
            "The assignment unexpectedly changed total payload lengths.");
        Require(player.ClubId == 23624 && BitConverter.ToInt32(people, starts[0] + 171) == 23624,
            "Native assignment did not persist the child club pointer.");
        int changedPersonBytes = 0;
        for (int offset = 0; offset < sourcePeople.Length; offset++)
            if (sourcePeople[offset] != people[offset])
            {
                changedPersonBytes++;
                Require(offset >= starts[0] + 171 && offset < starts[0] + 175,
                    "Native assignment changed an unrelated PERSON byte.");
            }
        Require(changedPersonBytes == 2, "The controlled club pointer must change exactly two physical PERSON bytes.");
        var priorSaveChanges = new HashSet<int>();
        var extraSiChanges = new HashSet<int>();
        for (int offset = 0; offset < 299; offset++)
        {
            if (peopleSamples[2][starts[2] + offset] != sourcePeople[starts[0] + offset])
                priorSaveChanges.Add(offset);
            if (people[starts[0] + offset] != referencePeople[starts[1] + offset])
                extraSiChanges.Add(offset);
            if (offset >= 199 && offset < 264)
                Require(sourcePeople[starts[0] + offset] == referencePeople[starts[1] + offset],
                    "SI changed the contract payload at +" + offset);
        }
        Require(priorSaveChanges.SetEquals(new[] { 125 }) && extraSiChanges.SetEquals(priorSaveChanges),
            "SI changed a PERSON field beyond the independently observed earlier-save variation.");

        int personCount = BitConverter.ToInt32(people, 0);
        var before = FM08_Database_Editor.ParseNativeClubDivisions(sourceServer, personCount);
        var after = FM08_Database_Editor.ParseNativeClubDivisions(server, personCount);
        var saved = FM08_Database_Editor.ParseNativeClubDivisions(referenceServer, personCount);
        foreach (int club in new[] { 992, 23624 })
        {
            var original = before[club];
            var generated = after[club];
            var expected = saved[club];
            int length = generated.Footer + 8 - generated.Start;
            Require(length == expected.Footer + 8 - expected.Start, "Generated U23/parent CLUB length differs from SI.");
            for (int offset = 0; offset < length; offset++)
                Require(server[generated.Start + offset] == referenceServer[expected.Start + offset],
                    "Generated U23/parent CLUB differs from SI at +" + offset);
            int originalCount = BitConverter.ToUInt16(sourceServer, original.RosterOffset);
            var expectedMembers = new HashSet<int>();
            for (int member = 0; member < originalCount; member++)
                expectedMembers.Add(BitConverter.ToInt32(sourceServer, original.RosterOffset + 2 + member * 4));
            Require(club == 992 ? expectedMembers.Remove(index) : expectedMembers.Add(index),
                "Unexpected source membership for Lautaro.");
            int count = BitConverter.ToUInt16(server, generated.RosterOffset);
            var actualMembers = new HashSet<int>();
            for (int member = 0; member < count; member++)
                actualMembers.Add(BitConverter.ToInt32(server, generated.RosterOffset + 2 + member * 4));
            Require(actualMembers.SetEquals(expectedMembers), "Native roster membership differs.");
        }
        Require(BitConverter.ToUInt16(server, after[992].RosterOffset) == 24 &&
            BitConverter.ToUInt16(server, after[23624].RosterOffset) == 1, "Expected Inter 24 and U23 1 players.");
        int childTail = after[23624].RosterOffset + 2 + 4;
        Require(BitConverter.ToInt32(server, childTail + 22) == 9 &&
            BitConverter.ToInt32(server, childTail + 26) == 815, "U23 type or parent reference changed.");
        foreach (var record in before.Values)
        {
            var current = after[record.ClubIndex];
            Require(record.CurrentDivisionIndex == current.CurrentDivisionIndex &&
                record.PreviousDivisionIndex == current.PreviousDivisionIndex &&
                record.EuropeanCompetitionIndex == current.EuropeanCompetitionIndex,
                "Player assignment changed a competition field.");
        }
        int parentEnd = before[992].Footer + 8, movedParentEnd = after[992].Footer + 8;
        int middleLength = before[23624].Start - parentEnd;
        Require(middleLength == after[23624].Start - movedParentEnd, "Intermediate server section length changed.");
        for (int offset = 0; offset < before[992].Start; offset++)
            Require(sourceServer[offset] == server[offset], "Server prefix changed.");
        for (int offset = 0; offset < middleLength; offset++)
            Require(sourceServer[parentEnd + offset] == server[movedParentEnd + offset], "An intervening server byte changed.");
        Require(before[23624].Footer == after[23624].Footer, "Balanced roster changes shifted the final footer.");
        for (int offset = before[23624].Footer + 8; offset < sourceServer.Length; offset++)
            Require(sourceServer[offset] == server[offset], "Server suffix changed.");
        fields["Club"].Setter(player, people, "Inter");
        FM08_Database_Editor.SyncClubAssignments(ref people, ref server,
            new List<FM08_Database_Editor.PlayerRecord> { player });
        Require(people.SequenceEqual(sourcePeople) && server.SequenceEqual(sourceServer),
            "U23 -> parent return did not restore the exact source payloads.");
        byte[] badServer = (byte[])sourceServer.Clone();
        badServer[before[23624].Footer + 12] = 2;
        byte[] badSnapshot = (byte[])badServer.Clone();
        byte[] failedPeople = sourcePeople, failedServer = badServer;
        fields["Club"].Setter(player, sourcePeople, "Inter Under 23s");
        bool rejected = false;
        try { FM08_Database_Editor.SyncClubAssignments(ref failedPeople, ref failedServer,
            new List<FM08_Database_Editor.PlayerRecord> { player }); }
        catch (InvalidDataException) { rejected = true; }
        Require(rejected && object.ReferenceEquals(failedPeople, sourcePeople) &&
            object.ReferenceEquals(failedServer, badServer) && failedServer.SequenceEqual(badSnapshot) && player.ClubId == 992,
            "A corrupt terminal roster did not fail atomically.");
        Console.WriteLine("PASS: shared CSV/native assignment Inter -> U23 -> Inter; reverse restores exact payloads.");
        Console.WriteLine("PASS: PERSON club pointer changes only 2 bytes; full 65-byte contract payload remains unchanged.");
        Console.WriteLine("PASS: both complete CLUB records match SI; Inter 25 -> 24, U23 0 -> 1; leagues/type/parent preserved.");
        Console.WriteLine("PASS: malformed terminal roster fails without changing either payload or the player.");
        Console.WriteLine("NOTE: SI also changed PERSON +125, independently variable on the previous save; native assignment preserves it.");
        Console.WriteLine("NOTE: U23 display-name aliases are fixture-only; production generated-name resolution is still pending.");
    }

    static void CheckDetermination(string database)
    {
        byte[] server = (byte[])Call("DecompressFile", Path.Combine(database, "server_db.dat"));
        byte[] people = (byte[])Call("DecompressFile", Path.Combine(database, "people_db.dat"));
        byte[] original = (byte[])people.Clone();
        object[] firstArgs = { server, 0, 0 };
        var first = (Dictionary<int, string>)Call("ParseFirstNames", firstArgs);
        object[] lastArgs = { server, firstArgs[2], null, 0 };
        var last = (Dictionary<int, string>)Call("ParseSurnames", lastArgs);
        var common = (Dictionary<int, string>)Call("ParseCommonNames", server, lastArgs[3]);
        var clubs = (Dictionary<int, string>)Call("ParseClubs", server);
        var nations = (Dictionary<int, string>)Call("ParseNations", server);
        var details = (Dictionary<int, FM08_Database_Editor.PersonDetails>)Call("ParsePersonData", people, first, last, common, clubs);
        var players = (List<FM08_Database_Editor.PlayerRecord>)Call("BuildPlayerList", people, details,
            new Dictionary<int, string[]>(), new Dictionary<int, string>(), clubs, nations);
        foreach (var player in players)
            Require(player.Determination == people[player.T89Offset + 86], "Determination was replaced by a placeholder.");
        var subjects = players.Take(3).ToArray();
        Require(subjects.Length == 3, "Missing determination test players.");
        var nationSubject = players.First(p => p.BirthDate.HasValue && p.NationIdOffset > 0);
        var nationModel = new FM08_Database_Editor.PlayerRecord { NationIdOffset = nationSubject.NationIdOffset };
        byte[] zeroNation = (byte[])people.Clone();
        FM08_Database_Editor.NationsRev.Clear();
        foreach (var entry in nations) FM08_Database_Editor.NationsRev[entry.Value] = entry.Key;
        Require(nations[0] == "Algeria", "Unexpected native nation zero.");
        FM08_Database_Editor.UpdatePlayerNation(nationModel, zeroNation, nations[0]);
        Require(BitConverter.ToInt32(zeroNation, nationSubject.NationIdOffset) == 0 && nationModel.NationId == 0,
            "Native nation zero was not written.");
        var zeroDetails = (Dictionary<int, FM08_Database_Editor.PersonDetails>)Call("ParsePersonData", zeroNation, first, last, common, clubs);
        var zeroPlayers = (List<FM08_Database_Editor.PlayerRecord>)Call("BuildPlayerList", zeroNation, zeroDetails,
            new Dictionary<int, string[]>(), new Dictionary<int, string>(), clubs, nations);
        var reloadedNation = zeroPlayers.Single(p => p.Id == nationSubject.Id);
        Require(reloadedNation.Nationality == nations[0] && reloadedNation.BirthDate == nationSubject.BirthDate,
            "Native nation zero lost the nationality or birth date on reload.");
        Console.WriteLine("PASS: native nation zero (Algeria) written and reloaded without losing birth date.");
        string[] aliases = { "Determination_Pers", "Determination", "Determinacja", "DeterminacjaOsobista", "DetPers" };
        var fields = FM08_Database_Editor.csvFieldsByName;
        foreach (string alias in aliases)
        {
            Require(object.ReferenceEquals(fields[alias], fields[aliases[0]]), "Determination alias resolves to a different field.");
            fields[alias].Setter(subjects[0], people, "7");
            Require(people[subjects[0].T89Offset + 86] == 7 && subjects[0].Determination == 7, "Alias did not persist determination.");
        }
        var modelOnly = new FM08_Database_Editor.PlayerRecord();
        fields[aliases[0]].Setter(modelOnly, null, "18");
        Require(modelOnly.Determination == 18, "Model-only CSV import failed.");
        foreach (string invalid in new[] { "-1", "21", "256", "abc", "", "1.5" })
        {
            bool rejected = false;
            try { fields[aliases[0]].Setter(subjects[0], people, invalid); }
            catch (InvalidDataException) { rejected = true; }
            Require(rejected && subjects[0].Determination == 7 &&
                people[subjects[0].T89Offset + 86] == 7, "Invalid determination did not fail atomically.");
        }
        var noRecord = new FM08_Database_Editor.PlayerRecord { Determination = 9 };
        foreach (int offset in new[] { 0, -1, people.Length - 86, int.MaxValue })
        {
            noRecord.T89Offset = offset;
            bool rejected = false;
            try { fields[aliases[0]].Setter(noRecord, people, "10"); }
            catch (InvalidDataException) { rejected = true; }
            Require(rejected && noRecord.Determination == 9, "Invalid determination offset must fail before model changes.");
        }
        int[] values = { 0, 1, 20 };
        var changed = new HashSet<int>();
        for (int i = 0; i < subjects.Length; i++)
        {
            subjects[i].Determination = (byte)values[i];
            fields[aliases[0]].Setter(subjects[i], people, fields[aliases[0]].Getter(subjects[i]));
            changed.Add(subjects[i].T89Offset + 86);
        }
        for (int i = 0; i < people.Length; i++)
            if (!changed.Contains(i)) Require(people[i] == original[i], "Determination changed another field or personality byte.");
        string temporary = Path.GetTempFileName();
        try
        {
            byte[] header = (byte[])Call("GetFileHeader", Path.Combine(database, "people_db.dat"));
            File.WriteAllBytes(temporary, (byte[])Call("CompressFile", people, header));
            byte[] reopened = (byte[])Call("DecompressFile", temporary);
            Require(people.SequenceEqual(reopened), "Determination payload did not survive disk compression.");
            var reloaded = (List<FM08_Database_Editor.PlayerRecord>)Call("BuildPlayerList", reopened, details,
                new Dictionary<int, string[]>(), new Dictionary<int, string>(), clubs, nations);
            for (int i = 0; i < subjects.Length; i++)
                Require(reloaded.Single(p => p.Id == subjects[i].Id).Determination == values[i],
                    "Determination did not survive native save/reload.");
        }
        finally { File.Delete(temporary); }
        Require(original.SequenceEqual((byte[])Call("DecompressFile", Path.Combine(database, "people_db.dat"))),
            "Determination test modified the source database.");
        Console.WriteLine("PASS: native determination read for all players; five CSV aliases; 0/1/20 saved and reloaded.");
        Console.WriteLine("PASS: only the determination bytes changed; invalid values/offsets rejected atomically; source unchanged.");
    }

    static void CheckU23GeneratedNames(string database)
    {
        var type = typeof(FM08_Database_Editor);
        var flags = BindingFlags.NonPublic | BindingFlags.Static;
        byte[] server = (byte[])type.GetMethod("DecompressFile", flags).Invoke(null,
            new object[] { Path.Combine(database, "server_db.dat") });
        byte[] people = (byte[])type.GetMethod("DecompressFile", flags).Invoke(null,
            new object[] { Path.Combine(database, "people_db.dat") });
        var names = (Dictionary<int, string>)type.GetMethod("ParseClubs", flags).Invoke(null, new object[] { server });
        var originalNames = new Dictionary<int, string>(names);
        FM08_Database_Editor.ResolveNativeU23ClubNames(server, BitConverter.ToInt32(people, 0), names);
        foreach (var pair in new[] { new[] { 23624, 992 }, new[] { 23625, 995 }, new[] { 23626, 963 } })
            Require(names[pair[0]] == names[pair[1]] + " Under 23s", "Wrong native U23 parent name.");
        var records = FM08_Database_Editor.ParseNativeClubDivisions(server, BitConverter.ToInt32(people, 0));
        byte[] corrupt = (byte[])server.Clone();
        BitConverter.GetBytes(815).CopyTo(corrupt, records[23626].Footer - 14);
        var invalidNames = new Dictionary<int, string>(originalNames);
        bool rejected = false;
        try { FM08_Database_Editor.ResolveNativeU23ClubNames(corrupt, BitConverter.ToInt32(people, 0), invalidNames); }
        catch (InvalidDataException) { rejected = true; }
        Require(rejected, "Unrelated U23 parent must not produce a guessed name.");
        Require(invalidNames.Count == originalNames.Count &&
            originalNames.All(entry => invalidNames[entry.Key] == entry.Value), "Name resolution failure must be atomic.");
        Console.WriteLine("PASS: generated U23 names, populated terminal team, wrong parent rejection and atomic dictionaries.");
    }

    public static void Main(string[] arguments)
    {
        FM08_Database_Editor.InitCsvRegistry();
        var fields = FM08_Database_Editor.csvFieldsByName;
        var imported = new FM08_Database_Editor.PlayerRecord();
        foreach (var invalid in new string[] { "-1", "abc", "2147483648" })
        {
            bool rejectedWage = false;
            try { fields["WeeklyWage"].Setter(imported, null, invalid); }
            catch (InvalidDataException) { rejectedWage = true; }
            Require(rejectedWage, "Invalid wage must not silently succeed.");
        }
        foreach (var invalid in new string[] { "-1", "100", "abc" })
        {
            bool rejectedNumber = false;
            try { fields["SquadNumber"].Setter(imported, null, invalid); }
            catch (InvalidDataException) { rejectedNumber = true; }
            Require(rejectedNumber, "Invalid jersey must not silently succeed.");
        }
        fields["Emerytura"].Setter(imported, null, "30.09.2007");
        Require(imported.RetirementDate == new DateTime(2007, 9, 30), "CSV retirement date was not imported.");
        fields["RetirementDate"].Setter(imported, null, "CLEAR");
        Require(!imported.RetirementDate.HasValue, "CSV retirement clearing failed.");
        bool invalidDateRejected = false;
        try { fields["RetirementDate"].Setter(imported, null, "31.02.2007"); }
        catch (InvalidDataException) { invalidDateRejected = true; }
        Require(invalidDateRejected, "Invalid CSV retirement must be rejected.");
        byte[] source = new byte[64];
        byte[] signature = { 0x24, 0x00, 0xD8, 0x07, 0x6D, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF };
        Buffer.BlockCopy(signature, 0, source, 7, signature.Length);
        source[23] = 0;
        source[63] = 0xA7;
        var player = new FM08_Database_Editor.PlayerRecord { Id = 11133, RetirementDate = new DateTime(2007, 9, 30) };
        var players = new List<FM08_Database_Editor.PlayerRecord> { player };
        byte[] added = FM08_Database_Editor.SyncRetirements(source, players);
        Require(added.Length == source.Length + 18, "A retirement must add exactly 18 bytes.");
        Require(added[added.Length - 1] == 0xA7 && source[19] == 0, "Source and trailing data must be preserved.");
        Require(FM08_Database_Editor.ParseRetirements(added)[11133] == player.RetirementDate.Value, "Retirement date did not round-trip.");
        BitConverter.GetBytes(1394631301).CopyTo(added, 37);
        player.RetirementDate = new DateTime(2008, 2, 29);
        byte[] updated = FM08_Database_Editor.SyncRetirements(added, players);
        Require(updated.Length == added.Length && BitConverter.ToInt32(updated, 37) == 1394631301, "Native extra field must survive updates.");
        Require(FM08_Database_Editor.ParseRetirements(updated)[11133] == player.RetirementDate.Value, "Leap-day update failed.");
        player.RetirementDate = null;
        byte[] cleared = FM08_Database_Editor.SyncRetirements(updated, players);
        Require(!FM08_Database_Editor.ParseRetirements(cleared).ContainsKey(11133), "Clearing a retirement must deactivate the record.");
        player.RetirementDate = new DateTime(2007, 9, 30);
        byte[] restored = FM08_Database_Editor.SyncRetirements(cleared, players);
        Require(restored.Length == added.Length && FM08_Database_Editor.ParseRetirements(restored).ContainsKey(11133), "Reactivating must reuse the record.");
        bool rejected = false;
        try { FM08_Database_Editor.SyncRetirements(new byte[64], players); }
        catch (InvalidDataException) { rejected = true; }
        Require(rejected, "Missing table must not silently report success.");
        Console.WriteLine("PASS: retirement add, update, native-field preservation, clear, reactivate and invalid-table checks.");
        int next = 0;
        if (arguments.Length > 0 && arguments[0] == "--controlled")
        {
            if (arguments.Length < 3)
                throw new ArgumentException("Usage: --controlled source-A reference-B [--clubs legacy-control] [--loans source reference]");
            CheckControlledContract(arguments[1], arguments[2]);
            next = 3;
        }
        else if (arguments.Length > 0 && arguments[0] != "--clubs" && arguments[0] != "--loans" && arguments[0] != "--coownership" && arguments[0] != "--leagues" && arguments[0] != "--european" && arguments[0] != "--u23-leagues" && arguments[0] != "--u23-player" && arguments[0] != "--u23-names" && arguments[0] != "--determination")
        {
            CheckNativeSample(arguments[0], arguments.Length > 1 ? arguments[1] : null);
            return;
        }
        while (next < arguments.Length)
        {
            if (arguments[next] == "--clubs" && next + 1 < arguments.Length)
            {
                CheckClubAssignments(arguments[next + 1]);
                next += 2;
            }
            else if (arguments[next] == "--loans" && next + 2 < arguments.Length)
            {
                CheckControlledLoans(arguments[next + 1], arguments[next + 2]);
                next += 3;
            }
            else if (arguments[next] == "--coownership" && next + 2 < arguments.Length)
            {
                CheckCoownershipPrimary(arguments[next + 1], arguments[next + 2]);
                next += 3;
            }
            else if (arguments[next] == "--leagues" && next + 2 < arguments.Length)
            {
                CheckLeagueAssignments(arguments[next + 1], arguments[next + 2]);
                next += 3;
            }
            else if (arguments[next] == "--european" && next + 2 < arguments.Length)
            {
                CheckEuropeanAssignments(arguments[next + 1], arguments[next + 2]);
                next += 3;
            }
            else if (arguments[next] == "--u23-leagues" && next + 2 < arguments.Length)
            {
                CheckU23LeagueAssignments(arguments[next + 1], arguments[next + 2]);
                next += 3;
            }
            else if (arguments[next] == "--u23-player" && next + 3 < arguments.Length)
            {
                CheckU23PlayerAssignment(arguments[next + 1], arguments[next + 2], arguments[next + 3]);
                next += 4;
            }
            else if (arguments[next] == "--u23-names" && next + 1 < arguments.Length)
            {
                CheckU23GeneratedNames(arguments[next + 1]);
                next += 2;
            }
            else if (arguments[next] == "--determination" && next + 1 < arguments.Length)
            {
                CheckDetermination(arguments[next + 1]);
                next += 2;
            }
            else throw new ArgumentException("Invalid regression selector: " + arguments[next]);
        }
    }
}
