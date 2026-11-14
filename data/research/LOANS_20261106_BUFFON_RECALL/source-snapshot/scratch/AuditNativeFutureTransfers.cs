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

public static class AuditNativeFutureTransfers
{
    const int RecordSize = 35;
    const BindingFlags Private = BindingFlags.Static | BindingFlags.NonPublic;

    public sealed class Transfer
    {
        public int RecordId, Offset, PersonIndex, ClubIndex;
        public DateTime Date;
    }

    sealed class Identity
    {
        internal int Uid;
        internal string Name;
    }

    static bool PersonHeader(byte[] people, int offset, int end, int count)
    {
        if (offset < 16 || offset + 5 > end) return false;
        int index = BitConverter.ToInt32(people, offset);
        return index >= 0 && index < count && people[offset + 4] >= 1 && people[offset + 4] <= 5;
    }

    static Identity ResolveOtherPerson(byte[] people, int index, int end, int count,
        Dictionary<int, string[]> names)
    {
        Identity found = null;
        for (int start = 16; start + 5 <= end; start++)
        {
            if (people[start + 4] != 3 || BitConverter.ToInt32(people, start) != index) continue;
            for (int footer = start + 5; footer <= Math.Min(end - 8, start + 4096); footer++)
            {
                if (BitConverter.ToInt32(people, footer) != index) continue;
                int uid = BitConverter.ToInt32(people, footer + 4);
                if (uid <= 0) continue;
                int next = footer + 8;
                bool boundary = next == end || PersonHeader(people, next, end, count) ||
                    (next + 2 <= end && PersonHeader(people, next + 2, end, count));
                if (!boundary) continue;
                Require(found == null, "Ambiguous type-3 PERSON identity: " + index);
                string[] name;
                bool named = names.TryGetValue(uid, out name) && name.Length >= 2;
                found = new Identity { Uid = uid,
                    Name = named ? name[0] + " " + name[1] : "UNRESOLVED_NAME_UID_" + uid };
            }
        }
        Require(found != null, "Unresolved transfer PERSON identity: " + index);
        return found;
    }

    static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidDataException(message);
    }

    static bool ValidDate(byte[] data, int offset)
    {
        int day = BitConverter.ToUInt16(data, offset), year = BitConverter.ToUInt16(data, offset + 2);
        return year >= 1900 && year <= 2100 && day < (DateTime.IsLeapYear(year) ? 366 : 365);
    }

    public static List<Transfer> Parse(byte[] server, int personCount, HashSet<int> clubIndices, out int header)
    {
        Require(server != null && personCount > 0 && clubIndices != null && clubIndices.Count > 0,
            "Invalid future-transfer parser inputs.");
        header = -1;
        for (int position = 0; position <= server.Length - 4 - RecordSize; position++)
        {
            if (server[position + 4] != 0 ||
                BitConverter.ToInt32(server, position + 31) != 0 ||
                BitConverter.ToInt32(server, position + 35) != -1) continue;
            int count = BitConverter.ToInt32(server, position);
            if (count <= 0 || count > personCount || position + 4L + count * (long)RecordSize > server.Length)
                continue;
            bool valid = true;
            for (int index = 0; index < count; index++)
            {
                int row = position + 4 + index * RecordSize;
                int person = BitConverter.ToInt32(server, row + 1);
                if (server[row] != 0 || person < 0 || person >= personCount ||
                    !clubIndices.Contains(BitConverter.ToInt32(server, row + 5)) ||
                    !ValidDate(server, row + 9) ||
                    BitConverter.ToInt32(server, row + 27) != index ||
                    BitConverter.ToInt32(server, row + 31) != -1)
                {
                    valid = false;
                    break;
                }
            }
            if (!valid) continue;
            Require(header < 0, "Ambiguous native future-transfer table.");
            header = position;
        }
        Require(header >= 0, "Unsupported, malformed, empty or missing native future-transfer table; not a clean audit.");
        int total = BitConverter.ToInt32(server, header);
        var result = new List<Transfer>();
        for (int index = 0; index < total; index++)
        {
            int row = header + 4 + index * RecordSize;
            int day = BitConverter.ToUInt16(server, row + 9), year = BitConverter.ToUInt16(server, row + 11);
            result.Add(new Transfer {
                RecordId = index, Offset = row, PersonIndex = BitConverter.ToInt32(server, row + 1),
                ClubIndex = BitConverter.ToInt32(server, row + 5), Date = new DateTime(year, 1, 1).AddDays(day)
            });
        }
        return result;
    }

    public static string Classify(DateTime? retirement, DateTime transfer, DateTime careerStart)
    {
        if (!retirement.HasValue) return "no_active_retirement";
        if (transfer < careerStart) return "transfer_before_career_start";
        if (retirement.Value < transfer) return "transfer_after_retirement";
        if (retirement.Value == transfer) return "transfer_on_retirement";
        return "transfer_before_retirement";
    }

    static object Call(string method, params object[] args)
    {
        var info = typeof(FM08_Database_Editor).GetMethod(method, Private);
        if (info == null) throw new MissingMethodException(method);
        return info.Invoke(null, args);
    }

    static string Hash(string path)
    {
        using (var hash = SHA256.Create())
            return BitConverter.ToString(hash.ComputeHash(File.ReadAllBytes(path))).Replace("-", "");
    }

    static SortedDictionary<string, string> Hashes(string directory)
    {
        var result = new SortedDictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        string prefix = directory.TrimEnd('\\') + "\\";
        foreach (string file in Directory.GetFiles(directory, "*", SearchOption.AllDirectories))
            result.Add(file.Substring(prefix.Length), Hash(file));
        return result;
    }

    static string Csv(object value)
    {
        return "\"" + Convert.ToString(value, CultureInfo.InvariantCulture).Replace("\"", "\"\"") + "\"";
    }

    static void WriteNew(string path, IEnumerable<string> lines)
    {
        using (var writer = new StreamWriter(new FileStream(path, FileMode.CreateNew, FileAccess.Write), new UTF8Encoding(false)))
            foreach (string line in lines) writer.WriteLine(line);
    }

    static string Date(DateTime value) { return value.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture); }

    static void Audit(string source, string report, DateTime careerStart)
    {
        source = Path.GetFullPath(source).TrimEnd('\\');
        report = Path.GetFullPath(report).TrimEnd('\\');
        Require(Directory.Exists(source), "Source database does not exist.");
        Require(!report.Equals(source, StringComparison.OrdinalIgnoreCase) &&
            !report.StartsWith(source + "\\", StringComparison.OrdinalIgnoreCase), "Report must be outside the database.");
        Require(!Directory.Exists(report) && !File.Exists(report), "Report output already exists; refusing overwrite.");
        var before = Hashes(source);
        byte[] people = (byte[])Call("DecompressFile", Path.Combine(source, "people_db.dat"));
        byte[] server = (byte[])Call("DecompressFile", Path.Combine(source, "server_db.dat"));
        int personCount = BitConverter.ToInt32(people, 0);
        var clubs = (Dictionary<int, string>)Call("ParseClubs", server);
        FM08_Database_Editor.ResolveNativeU23ClubNames(server, personCount, clubs);
        var nations = (Dictionary<int, string>)Call("ParseNations", server);
        var players = (List<Player>)typeof(VerifiedNativeSquadsWorker).GetMethod("ReadPlayers", Private)
            .Invoke(null, new object[] { people, server, clubs, nations });
        var byIndex = players.ToDictionary(p => BitConverter.ToInt32(people, p.PersonOffset - 15));
        var byUid = players.ToDictionary(p => p.Id);
        var records = FM08_Database_Editor.ParseNativeClubDivisions(server, personCount);
        var byClubIndex = records.Values.ToDictionary(r => r.ClubIndex);
        int header;
        var transfers = Parse(server, personCount, new HashSet<int>(byClubIndex.Keys), out header);
        var otherPeople = new Dictionary<int, Identity>();
        var missingIndices = transfers.Select(t => t.PersonIndex).Distinct().Where(i => !byIndex.ContainsKey(i)).ToList();
        if (missingIndices.Count > 0)
        {
            var names = (Dictionary<int, string[]>)Call("ParseEntityTreeAndTags", server);
            int personEnd = (int)Call("Find89ByteTable", people) - 81 - 8 - BitConverter.ToInt32(people, 4) * 17;
            foreach (int index in missingIndices)
                otherPeople.Add(index, ResolveOtherPerson(people, index, personEnd, personCount, names));
        }
        var retirements = FM08_Database_Editor.ParseRetirements(server);
        int retirementHeader = (int)Call("FindRetirementTable", server);
        Require(retirementHeader >= 0, "Missing retirement table.");
        int retirementCount = BitConverter.ToInt32(server, retirementHeader + 12);
        var activeUids = new HashSet<int>();
        var retirementIssues = new List<string> { "RecordId,RowOffset,UID,Issue,RawRecord" };
        for (int i = 0; i < retirementCount; i++)
        {
            int row = retirementHeader + 17 + i * 18;
            Require(BitConverter.ToInt32(server, row + 9) == i &&
                BitConverter.ToInt32(server, row + 13) == -1 && server[row + 17] == 0 &&
                server[row + 8] <= 1, "Unsupported retirement record: " + i);
            if (server[row + 8] != 1) continue;
            int uid = BitConverter.ToInt32(server, row);
            if (uid <= 0)
            {
                retirementIssues.Add(string.Join(",", new object[] {
                    i, "0x" + row.ToString("X"), uid, "active_row_has_no_positive_uid",
                    BitConverter.ToString(server, row, 18)
                }.Select(Csv).ToArray()));
                continue;
            }
            Require(ValidDate(server, row + 4) && activeUids.Add(uid),
                "Invalid or duplicate active retirement: " + uid);
            Require(retirements.ContainsKey(uid), "Active retirement omitted by reader: " + uid);
        }

        var loans = new HashSet<int>(FM08_Database_Editor.ParseNativeLoans(server, personCount).Select(l => l.PersonIndex));
        var rosterCounts = new Dictionary<int, int>();
        foreach (var record in records.Values)
        {
            int count = BitConverter.ToUInt16(server, record.RosterOffset);
            for (int i = 0; i < count; i++)
            {
                int person = BitConverter.ToInt32(server, record.RosterOffset + 2 + i * 4), current;
                rosterCounts.TryGetValue(person, out current);
                rosterCounts[person] = current + 1;
            }
        }
        string heading = "RecordId,RowOffset,PersonIndex,UID,Name,PersonCoverage,CurrentClubIndex,CurrentClubUID,DestinationClubIndex,DestinationClubUID,DestinationClub,TransferDate,RetirementDate,Classification,CA,PA,ContractExpiry,LoanPresent,RosterEntries,RawRecord";
        var all = new List<string> { heading };
        var retiring = new List<string> { heading };
        var conflicts = new List<string> { heading };
        var counts = new SortedDictionary<string, int>();
        var unresolvedClubNames = new HashSet<int>();
        foreach (var transfer in transfers)
        {
            Player player;
            byIndex.TryGetValue(transfer.PersonIndex, out player);
            int uid = player != null ? player.Id : otherPeople[transfer.PersonIndex].Uid;
            string name = player != null ? player.FullName : otherPeople[transfer.PersonIndex].Name;
            var club = byClubIndex[transfer.ClubIndex];
            int clubUid = BitConverter.ToInt32(server, club.Footer + 4);
            string destinationName;
            if (!clubs.TryGetValue(transfer.ClubIndex, out destinationName))
            {
                unresolvedClubNames.Add(transfer.ClubIndex);
                destinationName = "UNRESOLVED_NAME_CLUB_INDEX_" + transfer.ClubIndex;
            }
            string currentClubUid = "";
            if (player != null && player.ClubIdOffset > 0)
            {
                Require(byClubIndex.ContainsKey(player.ClubId), "Unresolved current owner CLUB index: " + player.ClubId);
                currentClubUid = BitConverter.ToInt32(server, byClubIndex[player.ClubId].Footer + 4)
                    .ToString(CultureInfo.InvariantCulture);
            }
            DateTime date;
            DateTime? retirement = retirements.TryGetValue(uid, out date) ? (DateTime?)date : null;
            string category = Classify(retirement, transfer.Date, careerStart);
            if (!counts.ContainsKey(category)) counts.Add(category, 0);
            counts[category]++;
            int rosterCount;
            rosterCounts.TryGetValue(transfer.PersonIndex, out rosterCount);
            string line = string.Join(",", new object[] {
                transfer.RecordId, "0x" + transfer.Offset.ToString("X"), transfer.PersonIndex, uid, name,
                player != null ? "type_2_player" : "type_3_identity_only",
                player != null && player.ClubIdOffset > 0 ? player.ClubId.ToString(CultureInfo.InvariantCulture) : "",
                currentClubUid, transfer.ClubIndex, clubUid,
                destinationName, Date(transfer.Date),
                retirement.HasValue ? Date(retirement.Value) : "", category,
                player != null ? player.CA.ToString(CultureInfo.InvariantCulture) : "",
                player != null ? player.PA.ToString(CultureInfo.InvariantCulture) : "",
                player != null && player.ContractExpires.HasValue ? Date(player.ContractExpires.Value) : "",
                loans.Contains(transfer.PersonIndex), rosterCount, BitConverter.ToString(server, transfer.Offset, RecordSize)
            }.Select(Csv).ToArray());
            all.Add(line);
            if (retirement.HasValue) retiring.Add(line);
            if (category == "transfer_after_retirement" || category == "transfer_on_retirement") conflicts.Add(line);
            if (uid == 830762)
                Console.WriteLine("CACIA: PERSON={0}, destination={1} (UID={2}, CLUB_INDEX={3}), transfer={4}, retirement={5}, classification={6}",
                    transfer.PersonIndex, destinationName, clubUid, transfer.ClubIndex, Date(transfer.Date),
                    retirement.HasValue ? Date(retirement.Value) : "NONE", category);
        }
        var after = Hashes(source);
        Require(before.Count == after.Count && before.All(p => after.ContainsKey(p.Key) && after[p.Key] == p.Value),
            "Source files changed during audit; report is not valid.");
        Directory.CreateDirectory(report);
        WriteNew(Path.Combine(report, "all_future_transfers.csv"), all);
        WriteNew(Path.Combine(report, "retirement_future_transfers.csv"), retiring);
        WriteNew(Path.Combine(report, "retirement_transfer_conflicts.csv"), conflicts);
        WriteNew(Path.Combine(report, "retirement_table_issues.csv"), retirementIssues);
        var summary = new {
            source = source, careerStart = Date(careerStart), mode = "read-only database audit",
            tableHeader = "0x" + header.ToString("X"), recordSize = RecordSize,
            totalTransfers = transfers.Count, withActiveRetirement = retiring.Count - 1,
            conflictsAtOrAfterRetirement = conflicts.Count - 1, classifications = counts,
            parsedPlayerCount = byUid.Count, activeRetirementRows = activeUids.Count,
            otherPersonIdentities = otherPeople.Count,
            otherPersonNamesUnresolved = otherPeople.Values.Count(p => p.Name.StartsWith("UNRESOLVED_NAME_UID_", StringComparison.Ordinal)),
            destinationClubNamesUnresolved = unresolvedClubNames.OrderBy(i => i).ToArray(),
            activeRetirementRowsWithoutPositiveUid = retirementIssues.Count - 1,
            sourceHashesBefore = before, sourceHashesAfter = after, sourceUnchanged = true,
            limitations = new[] {
                "A scheduled transfer at/after retirement is a data conflict/risk, not proof of the engine's exact cancellation or reactivation path.",
                "Only the validated 35-byte native future-transfer layout is supported; an absent, empty, ambiguous or malformed table fails explicitly.",
                "Unknown transfer payload fields are retained in RawRecord, not assigned guessed meanings.",
                "Club UIDs come from validated CLUB records; names unavailable to the existing name reader are explicitly marked UNRESOLVED_NAME_CLUB_INDEX.",
                "For type-3 PERSON subjects only UID is resolved using a unique bounded header/footer and next-record boundary; names absent from the existing name reader are explicitly marked UNRESOLVED_NAME_UID. Player-only contract/CA/PA fields are unavailable.",
                "No running game or save was inspected and no database was written.",
                "Rows are not deduplicated by person: every scheduled transfer is reported separately."
            }
        };
        WriteNew(Path.Combine(report, "summary.json"), new[] { new JavaScriptSerializer().Serialize(summary) });
        Console.WriteLine("Future transfers: {0}; with active retirement: {1}; at/after retirement: {2}",
            transfers.Count, retiring.Count - 1, conflicts.Count - 1);
        foreach (var count in counts) Console.WriteLine(count.Key + ": " + count.Value);
        if (retirementIssues.Count > 1)
            Console.WriteLine("WARNING: " + (retirementIssues.Count - 1) +
                " active retirement rows have no positive UID; exported separately, not treated as player retirements.");
        if (otherPeople.Count > 0)
            Console.WriteLine("WARNING: " + otherPeople.Count +
                " type-3 PERSON subjects have identity-only coverage; " +
                otherPeople.Values.Count(p => p.Name.StartsWith("UNRESOLVED_NAME_UID_", StringComparison.Ordinal)) +
                " names unresolved, explicitly marked in CSV.");
        if (unresolvedClubNames.Count > 0)
            Console.WriteLine("WARNING: " + unresolvedClubNames.Count +
                " destination club names unresolved; their native CLUB indices and UIDs are resolved and exported.");
        Console.WriteLine("PASS: all " + before.Count + " source file hashes unchanged.");
        Console.WriteLine("Report: " + report);
    }

    static byte[] Fixture()
    {
        var data = new byte[4 + RecordSize * 2];
        BitConverter.GetBytes(2).CopyTo(data, 0);
        for (int i = 0; i < 2; i++)
        {
            int row = 4 + i * RecordSize;
            BitConverter.GetBytes(i + 1).CopyTo(data, row + 1);
            BitConverter.GetBytes(7).CopyTo(data, row + 5);
            BitConverter.GetBytes((ushort)(i == 0 ? 1 : 365)).CopyTo(data, row + 9);
            BitConverter.GetBytes((ushort)2008).CopyTo(data, row + 11);
            BitConverter.GetBytes(i).CopyTo(data, row + 27);
            BitConverter.GetBytes(-1).CopyTo(data, row + 31);
        }
        return data;
    }

    static void Reject(byte[] data, string label)
    {
        int header;
        bool rejected = false;
        try { Parse(data, 10, new HashSet<int> { 7 }, out header); }
        catch (InvalidDataException) { rejected = true; }
        Require(rejected, "Self-test failed to reject " + label);
    }

    static void SelfTest()
    {
        int header;
        var original = Fixture();
        var rows = Parse(original, 10, new HashSet<int> { 7 }, out header);
        Require(header == 0 && rows.Count == 2 && rows[0].PersonIndex == 1 &&
            rows[0].Date == new DateTime(2008, 1, 2) && rows[1].Date == new DateTime(2008, 12, 31),
            "Self-test decoded wrong fields or dates.");
        var embedded = new byte[original.Length + 19];
        Buffer.BlockCopy(original, 0, embedded, 11, original.Length);
        Parse(embedded, 10, new HashSet<int> { 7 }, out header);
        Require(header == 11, "Embedded header not found.");
        foreach (int offset in new[] { 0, 4, 5, 9, 16, 31, 35, 39, 66, 70 })
        {
            var malformed = (byte[])original.Clone();
            malformed[offset] ^= 255;
            Reject(malformed, "field offset " + offset);
        }
        Reject(original.Take(original.Length - 1).ToArray(), "truncated last record");
        var duplicate = original.Concat(original).ToArray();
        Reject(duplicate, "ambiguous tables");
        Reject(new byte[64], "missing/empty table");
        var badDate = (byte[])original.Clone();
        BitConverter.GetBytes((ushort)2007).CopyTo(badDate, 4 + RecordSize + 11);
        Reject(badDate, "day 365 in a non-leap year");
        var start = new DateTime(2007, 6, 30);
        var retirement = new DateTime(2007, 7, 30);
        Require(Classify(retirement, new DateTime(2008, 1, 2), start) == "transfer_after_retirement" &&
            Classify(retirement, retirement, start) == "transfer_on_retirement" &&
            Classify(retirement, retirement.AddDays(-1), start) == "transfer_before_retirement" &&
            Classify(retirement, start.AddDays(-1), start) == "transfer_before_career_start" &&
            Classify(null, retirement, start) == "no_active_retirement", "Classification boundaries failed.");
        Require(original.SequenceEqual(Fixture()), "Parser mutated input.");
        var person = new byte[160];
        BitConverter.GetBytes(3).CopyTo(person, 16);
        person[20] = 3;
        BitConverter.GetBytes(3).CopyTo(person, 40);
        BitConverter.GetBytes(99).CopyTo(person, 44);
        person[48] = 20;
        BitConverter.GetBytes(4).CopyTo(person, 50);
        person[54] = 2;
        var names = new Dictionary<int, string[]> { { 99, new[] { "Test", "Person" } } };
        var identity = ResolveOtherPerson(person, 3, person.Length, 10, names);
        Require(identity.Uid == 99 && identity.Name == "Test Person", "Type-3 identity boundary failed.");
        identity = ResolveOtherPerson(person, 3, person.Length, 10, new Dictionary<int, string[]>());
        Require(identity.Name == "UNRESOLVED_NAME_UID_99", "Missing name was not surfaced.");
        BitConverter.GetBytes(3).CopyTo(person, 80);
        person[84] = 3;
        BitConverter.GetBytes(3).CopyTo(person, 100);
        BitConverter.GetBytes(99).CopyTo(person, 104);
        BitConverter.GetBytes(5).CopyTo(person, 110);
        person[114] = 2;
        bool rejected = false;
        try { ResolveOtherPerson(person, 3, person.Length, 10, names); }
        catch (InvalidDataException) { rejected = true; }
        Require(rejected, "Ambiguous type-3 identity was not rejected.");
        Console.WriteLine("PASS: native transfer layout, embedded/ambiguous/malformed/truncated tables, dates, classification, type-3 identities and read-only parsing.");
    }

    public static void Main(string[] args)
    {
        if (args.Length == 1 && args[0] == "--self-test") { SelfTest(); return; }
        if (args.Length != 3)
            throw new ArgumentException("Usage: AuditNativeFutureTransfers.exe source-db new-report-directory career-start-yyyy-MM-dd | --self-test");
        Audit(args[0], args[1], DateTime.ParseExact(args[2], "yyyy-MM-dd", CultureInfo.InvariantCulture));
    }
}
