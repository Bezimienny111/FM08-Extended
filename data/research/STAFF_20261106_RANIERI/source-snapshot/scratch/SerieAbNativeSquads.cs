using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using Player = FM08_Database_Editor.PlayerRecord;

public sealed partial class VerifiedNativeSquadsWorker
{
    static readonly string[] Traits = { "Adaptability", "Ambition", "Controversy", "Loyalty",
        "Pressure", "Professionalism", "Sportsmanship", "Temperament" };

    static object Value(Player player, string name)
    {
        var field = typeof(Player).GetField(name);
        var property = typeof(Player).GetProperty(name);
        Require(field != null || property != null, "Unknown profile field: " + name);
        return field != null ? field.GetValue(player) : property.GetValue(player, null);
    }

    static List<Dictionary<string, string>> AbRows(string csv)
    {
        string[] lines = File.ReadAllLines(csv, Encoding.UTF8);
        Require(lines.Length > 1, "Empty A/B input.");
        var headers = (string[])Call("ParseCsvLine", lines[0]);
        Require(headers.Distinct().Count() == headers.Length, "Duplicate input column.");
        var result = new List<Dictionary<string, string>>();
        foreach (string line in lines.Skip(1))
        {
            var cells = (string[])Call("ParseCsvLine", line);
            Require(cells.Length == headers.Length, "Malformed A/B input.");
            result.Add(headers.Select((h, i) => new { h, v = cells[i] }).ToDictionary(e => e.h, e => e.v));
        }
        return result;
    }

    static void SetProfile(Player player, Dictionary<string, string> row)
    {
        player.FirstName = row["FirstName"];
        player.LastName = row["LastName"];
        player.BirthDate = DateTime.ParseExact(row["BirthDate"], "yyyy-MM-dd", CultureInfo.InvariantCulture);
        player.Club = row["Club"];
        player.Nationality = row["Nationality"];
        foreach (var item in row)
        {
            if (new[] { "ExistingID", "FirstName", "LastName", "BirthDate", "Club", "ClubIndex", "Nationality" }.Contains(item.Key)) continue;
            int number = int.Parse(item.Value, CultureInfo.InvariantCulture);
            var field = typeof(Player).GetField(item.Key);
            var property = typeof(Player).GetProperty(item.Key);
            Type type = field != null ? field.FieldType : property != null && property.CanWrite ? property.PropertyType : null;
            Require(type == typeof(int) || type == typeof(byte), "Invalid native model column: " + item.Key);
            bool attribute = item.Key.StartsWith("Pos", StringComparison.Ordinal) || Traits.Contains(item.Key) ||
                !new[] { "CA", "PA", "WeeklyWage", "Height", "Weight", "SquadNumber" }.Contains(item.Key);
            Require(!attribute || (number >= 0 && number <= 20), "Out-of-range attribute: " + item.Key);
            object value = type == typeof(byte) ? (object)checked((byte)number) : number;
            if (field != null) field.SetValue(player, value);
            else property.SetValue(player, value, null);
        }
        Require(player.CA >= 1 && player.PA >= player.CA && player.PA <= 200 &&
            player.WeeklyWage > 0 && player.Height >= 140 && player.Height <= 220 &&
            player.Weight >= 45 && player.Weight <= 130 && player.SquadNumber >= 1 &&
            player.SquadNumber <= 99, "Invalid profile: " + player.FullName);
        player.ContractExpires = new DateTime(2010, 6, 30);
        player.ContractExpiresPending = true;
        player.ContractDetailsPending = true;
        player.ClubAssignmentPending = true;
    }

    static byte[] Replace(byte[] source, int offset, int removed, byte[] addition)
    {
        Require(offset >= 0 && removed >= 0 && offset + (long)removed <= source.Length, "Invalid replacement.");
        byte[] result = new byte[checked(source.Length - removed + addition.Length)];
        Buffer.BlockCopy(source, 0, result, 0, offset);
        Buffer.BlockCopy(addition, 0, result, offset, addition.Length);
        Buffer.BlockCopy(source, offset + removed, result, offset + addition.Length, source.Length - offset - removed);
        return result;
    }

    sealed class IdPool
    {
        internal readonly int First, Limit;
        readonly HashSet<int> used = new HashSet<int>();
        internal readonly Dictionary<int, int> Allocated = new Dictionary<int, int>();
        int next;

        internal IdPool(int first, int limit, params byte[][] buffers)
        {
            First = first;
            Limit = limit;
            next = first;
            foreach (byte[] buffer in buffers)
                for (int i = 0; i <= buffer.Length - 4; i++)
                {
                    int value = BitConverter.ToInt32(buffer, i);
                    if (value >= First && value < Limit) used.Add(value);
                }
        }

        internal IdPool(params byte[][] buffers) : this(1601000000, 1602000000, buffers)
        {
        }

        internal int Allocate(int copies)
        {
            while (next < Limit && used.Contains(next)) next++;
            Require(next < Limit, "Native batch identity range exhausted.");
            used.Add(next);
            Allocated.Add(next, copies);
            return next++;
        }

        internal void Verify(params byte[][] buffers)
        {
            var counts = Allocated.Keys.ToDictionary(k => k, k => 0);
            foreach (byte[] buffer in buffers)
                for (int i = 0; i <= buffer.Length - 4; i++)
                {
                    int value = BitConverter.ToInt32(buffer, i);
                    if (value >= First && value < Limit && counts.ContainsKey(value)) counts[value]++;
                }
            foreach (var pair in Allocated)
                Require(counts[pair.Key] == pair.Value, "Native identity collision after serialization: " + pair.Key);
        }
    }

    static Dictionary<string, int> BatchNames(ref byte[] server, ref byte[] client,
        IEnumerable<string> requested, bool surname, IdPool pool)
    {
        int anchor = (int)Call("FindNameTableStart", server, 5000000, server.Length - 1000);
        if (surname) anchor = (int)Call("FindNameTableStart", server, anchor + 100000, server.Length - 1000);
        Require(anchor >= 0, "Missing native name table.");
        object[] args = { server, anchor, null, null, 0 };
        var names = (Dictionary<int, string>)Editor.GetMethod("ParseNativeNames", Private).Invoke(null, args);
        int end = (int)args[4], start = end - 4 - names.Values.Sum(s => 22 + s.Length * 2);
        byte[] marker = new byte[64];
        Buffer.BlockCopy(server, start, marker, 0, marker.Length);
        int clientStart = (int)Call("FindNativeBytes", client, marker, 0, -1);
        Require(clientStart >= 0, "Server/client name table mismatch.");
        EqualRange(server, start, client, clientStart, end - start, "initial native name table");
        var needed = requested.GroupBy(s => s, StringComparer.Ordinal).ToDictionary(g => g.Key, g => g.Count());
        var indices = new Dictionary<string, int>(StringComparer.Ordinal);
        int cursor = start + 4;
        for (int i = 0; i < names.Count; i++)
        {
            string value = names[i - 1];
            if (!indices.ContainsKey(value)) indices.Add(value, i);
            int references;
            if (needed.TryGetValue(value, out references))
            {
                int offset = cursor + 7 + value.Length * 2;
                ushort increased = checked((ushort)(BitConverter.ToUInt16(server, offset) + references));
                BitConverter.GetBytes(increased).CopyTo(server, offset);
                BitConverter.GetBytes(increased).CopyTo(client, clientStart + offset - start);
                needed.Remove(value);
            }
            cursor += 22 + value.Length * 2;
        }
        Require(cursor == end, "Native name table boundary mismatch.");
        var rows = new List<byte[]>();
        int count = names.Count;
        foreach (var item in needed)
        {
            Require(!string.IsNullOrWhiteSpace(item.Key) && item.Key.Length <= 120, "Invalid native name.");
            byte[] row = new byte[22 + item.Key.Length * 2];
            BitConverter.GetBytes(item.Key.Length).CopyTo(row, 1);
            Encoding.Unicode.GetBytes(item.Key).CopyTo(row, 5);
            byte[] tail = { 0, 0, 1, 0, 0, 255, 255, 255, 255 };
            Buffer.BlockCopy(tail, 0, row, 5 + item.Key.Length * 2, tail.Length);
            BitConverter.GetBytes(checked((ushort)item.Value)).CopyTo(row, 7 + item.Key.Length * 2);
            BitConverter.GetBytes(count).CopyTo(row, row.Length - 8);
            BitConverter.GetBytes(pool.Allocate(2)).CopyTo(row, row.Length - 4);
            rows.Add(row);
            indices.Add(item.Key, count++);
        }
        byte[] chunk = rows.SelectMany(r => r).ToArray();
        server = Replace(server, end, 0, chunk);
        client = Replace(client, clientStart + end - start, 0, chunk);
        BitConverter.GetBytes(count).CopyTo(server, start);
        BitConverter.GetBytes(count).CopyTo(client, clientStart);
        EqualRange(server, start, client, clientStart, end - start + chunk.Length, "updated native name table");
        return indices;
    }

    static void WriteProfile(Player player, byte[] people, int personalityHeader = -1)
    {
        foreach (var field in FM08_Database_Editor.allCsvFields)
            if (field.Getter != null && field.Setter != null &&
                !new[] { "FirstName", "LastName", "CommonName" }.Contains(field.Key))
                field.Setter(player, people, field.Getter(player));
        FM08_Database_Editor.UpdatePlayerBirthDate(player, people, player.BirthDate.Value);
        FM08_Database_Editor.UpdatePlayerNation(player, people, player.Nationality);
        if (personalityHeader < 0)
            personalityHeader = AttributesStart(people) - 8 - BitConverter.ToInt32(people, 4) * 17;
        int index = BitConverter.ToInt32(people, player.PersonOffset - 15 + 181);
        int personality = personalityHeader + 4 + index * 17;
        Require(people[personality] == 0 && BitConverter.ToInt32(people, personality + 9) == index,
            "Unverified personality record: " + player.FullName);
        for (int i = 0; i < Traits.Length; i++) people[personality + 1 + i] = Convert.ToByte(Value(player, Traits[i]));
    }

    static void AppendBatch(ref byte[] people, ref byte[] server, ref byte[] client,
        List<Player> incoming, List<Player> existing, Dictionary<Player, int> targets, IdPool pool)
    {
        var contractReferences = FM08_Database_Editor.ResolveNativeClubContractReferences(
            server, BitConverter.ToInt32(people, 0), targets.Values);
        var firstNames = BatchNames(ref server, ref client, incoming.Select(p => p.FirstName), false, pool);
        var lastNames = BatchNames(ref server, ref client, incoming.Select(p => p.LastName), true, pool);
        ReadPlayers(people, server, (Dictionary<int, string>)Call("ParseClubs", server),
            (Dictionary<int, string>)Call("ParseNations", server));
        int count = BitConverter.ToInt32(people, 0), personalities = BitConverter.ToInt32(people, 4),
            attributes = BitConverter.ToInt32(people, 8), start = AttributesStart(people);
        int personalityHeader = start - 8 - personalities * 17, attributeHeader = start - 4,
            attributeEnd = start + attributes * 89, n = incoming.Count;
        Require(BitConverter.ToInt32(people, personalityHeader) == personalities &&
            BitConverter.ToInt32(people, attributeHeader) == attributes, "Unverified native table layout.");
        for (int i = 0; i < attributes; i++)
            Require(BitConverter.ToInt32(people, start + i * 89 + 81) == i, "Non-contiguous native attribute table.");
        var personBytes = new byte[checked(n * 299)];
        var personalityBytes = new byte[checked(n * 17)];
        var attributeBytes = new byte[checked(n * 89)];
        for (int i = 0; i < n; i++)
        {
            Player player = incoming[i];
            player.Id = pool.Allocate(1);
            byte[] person = new byte[234];
            person[4] = 2;
            foreach (int offset in new[] { 26, 76, 80, 84, 88, 109, 119, 145, 169, 178, 209, 214, 222 })
                BitConverter.GetBytes((short)1900).CopyTo(person, offset);
            foreach (int offset in new[] { 91, 103, 121, 133, 150, 154, 162, 171, 185, 194, 216 })
                BitConverter.GetBytes(-1).CopyTo(person, offset);
            BitConverter.GetBytes((short)10000).CopyTo(person, 28);
            BitConverter.GetBytes((short)10000).CopyTo(person, 32);
            person[148] = 255; person[175] = 1;
            BitConverter.GetBytes(count + i).CopyTo(person, 0);
            BitConverter.GetBytes(attributes + i).CopyTo(person, 15);
            BitConverter.GetBytes(firstNames[player.FirstName]).CopyTo(person, 125);
            BitConverter.GetBytes(lastNames[player.LastName]).CopyTo(person, 129);
            BitConverter.GetBytes(targets[player]).CopyTo(person, 171);
            BitConverter.GetBytes((ushort)181).CopyTo(person, 176);
            BitConverter.GetBytes((ushort)2007).CopyTo(person, 178);
            BitConverter.GetBytes(personalities + i).CopyTo(person, 181);
            BitConverter.GetBytes(count + i).CopyTo(person, 226);
            BitConverter.GetBytes(player.Id).CopyTo(person, 230);
            byte[] contract = new byte[65];
            contract[1] = 1; contract[25] = 100;
            BitConverter.GetBytes(count + i).CopyTo(contract, 26);
            BitConverter.GetBytes(contractReferences[targets[player]]).CopyTo(contract, 31);
            BitConverter.GetBytes(player.WeeklyWage).CopyTo(contract, 35);
            BitConverter.GetBytes((ushort)(player.ContractExpires.Value.DayOfYear - 1)).CopyTo(contract, 39);
            BitConverter.GetBytes((ushort)2010).CopyTo(contract, 41);
            contract[43] = 2; contract[44] = 255;
            BitConverter.GetBytes((ushort)181).CopyTo(contract, 54);
            BitConverter.GetBytes((ushort)2007).CopyTo(contract, 56);
            contract[59] = 25; contract[60] = player.SquadNumber;
            person[198] = 1;
            person = Replace(person, 199, 0, contract);
            Buffer.BlockCopy(person, 0, personBytes, i * 299, 299);
            int personality = i * 17;
            for (int t = 0; t < Traits.Length; t++)
                personalityBytes[personality + 1 + t] = Convert.ToByte(Value(player, Traits[t]));
            BitConverter.GetBytes(personalities + i).CopyTo(personalityBytes, personality + 9);
            BitConverter.GetBytes(pool.Allocate(1)).CopyTo(personalityBytes, personality + 13);
            BitConverter.GetBytes(attributes + i).CopyTo(attributeBytes, i * 89 + 81);
            BitConverter.GetBytes(pool.Allocate(1)).CopyTo(attributeBytes, i * 89 + 85);
        }
        people = Replace(people, attributeEnd, 0, attributeBytes);
        people = Replace(people, attributeHeader, 0, personalityBytes);
        people = Replace(people, personalityHeader, 0, personBytes);
        BitConverter.GetBytes(count + n).CopyTo(people, 0);
        BitConverter.GetBytes(personalities + n).CopyTo(people, 4);
        BitConverter.GetBytes(attributes + n).CopyTo(people, 8);
        BitConverter.GetBytes(personalities + n).CopyTo(people, personalityHeader + personBytes.Length);
        BitConverter.GetBytes(attributes + n).CopyTo(people, attributeHeader + personBytes.Length + personalityBytes.Length);
        foreach (Player player in existing) player.T89Offset += personBytes.Length + personalityBytes.Length;
        for (int i = 0; i < n; i++)
        {
            Player player = incoming[i];
            int person = personalityHeader + i * 299;
            player.PersonOffset = person + 15;
            player.FirstNameIdOffset = person + 125; player.LastNameIdOffset = person + 129;
            player.CommonNameIdOffset = person + 133; player.BirthDateOffset = person + 145;
            player.NationIdOffset = person + 150; player.ClubIdOffset = person + 171;
            player.ClubId = targets[player]; player.ContractExpiresOffset = person + 240;
            player.T89Offset = attributeEnd + personBytes.Length + personalityBytes.Length + i * 89 - 8;
            WriteProfile(player, people, personalityHeader + personBytes.Length);
            player.ClubAssignmentPending = false;
            player.ContractExpiresPending = false;
            player.ContractDetailsPending = false;
            existing.Add(player);
        }
    }

    static int PersonEnd(byte[] people, Player player)
    {
        byte[] marker = new byte[8];
        BitConverter.GetBytes(BitConverter.ToInt32(people, player.PersonOffset - 15)).CopyTo(marker, 0);
        BitConverter.GetBytes(player.Id).CopyTo(marker, 4);
        int footer = (int)Call("FindNativeBytes", people, marker, player.PersonOffset, 4096);
        Require(footer > player.PersonOffset, "Unverified original PERSON footer.");
        return footer + 8;
    }

    static int OwnedPointer(byte[] people, Player player, int club)
    {
        int start = player.PersonOffset - 15, footer = PersonEnd(people, player) - 8;
        int index = BitConverter.ToInt32(people, start);
        foreach (int candidate in new[] { player.ClubIdOffset, player.NationIdOffset + 21, start + 171 }.Distinct())
            if (candidate > start && candidate + 28 <= footer &&
                BitConverter.ToInt32(people, candidate) == club &&
                (int)Call("GetNativeContractLength", people, candidate + 28, footer, index) >= 0)
                return candidate;
        throw new InvalidDataException("Unverified ownership: UID=" + player.Id + ", expected=" + club +
            ", PERSON-length=" + (footer + 8 - start) + ", nation-relative=" + (player.NationIdOffset - start) +
            ", field171=" + BitConverter.ToInt32(people, start + 171) +
            ", fieldNation21=" + BitConverter.ToInt32(people, player.NationIdOffset + 21));
    }

    static HashSet<int> Roster(byte[] server, FM08_Database_Editor.NativeClubDivisionRecord record)
    {
        var result = new HashSet<int>();
        int count = BitConverter.ToUInt16(server, record.RosterOffset);
        for (int i = 0; i < count; i++)
            Require(result.Add(BitConverter.ToInt32(server, record.RosterOffset + 2 + i * 4)), "Duplicate native roster entry.");
        return result;
    }

    static void VerifyClubAfterRelease(byte[] oldServer, byte[] server,
        FM08_Database_Editor.NativeClubDivisionRecord old, FM08_Database_Editor.NativeClubDivisionRecord current,
        HashSet<int> releasedIndices)
    {
        var expected = Roster(oldServer, old);
        expected.ExceptWith(releasedIndices);
        Require(expected.SetEquals(Roster(server, current)), "Protected CLUB roster changed: " + old.ClubIndex);
        int oldEnd = old.RosterOffset + 2 + BitConverter.ToUInt16(oldServer, old.RosterOffset) * 4;
        int end = current.RosterOffset + 2 + BitConverter.ToUInt16(server, current.RosterOffset) * 4;
        Require(old.RosterOffset - old.Start == current.RosterOffset - current.Start &&
            old.Footer - oldEnd == current.Footer - end, "Protected CLUB structure changed: " + old.ClubIndex);
        EqualRange(oldServer, old.Start, server, current.Start, old.RosterOffset - old.Start, "protected CLUB prefix");
        EqualRange(oldServer, oldEnd, server, end, old.Footer + 8 - oldEnd, "protected CLUB suffix");
    }

    static bool IsOwnedRosterPlayer(byte[] people, byte[] server, Player player, int club,
        Dictionary<int, FM08_Database_Editor.NativeClubDivisionRecord> records)
    {
        Require(player.ClubIdOffset > 0 && player.ClubIdOffset <= people.Length - 4,
            "Unresolved roster ownership: UID=" + player.Id + ", club=" + club);
        int owner = BitConverter.ToInt32(people, player.ClubIdOffset);
        Require(records.ContainsKey(owner), "Missing roster owner: UID=" + player.Id + ", owner=" + owner);
        Require(OwnedPointer(people, player, owner) == player.ClubIdOffset,
            "Unverified roster ownership field: UID=" + player.Id);
        if (owner == club) return true;
        int index = BitConverter.ToInt32(people, player.PersonOffset - 15);
        Require(Roster(server, records[owner]).Contains(index),
            "Borrowed roster player is absent from owner roster: UID=" + player.Id + ", owner=" + owner);
        return false;
    }

    static void ValidateTargetOwnerRosters(byte[] people, byte[] server, List<Player> players, HashSet<int> targets,
        Dictionary<int, FM08_Database_Editor.NativeClubDivisionRecord> records)
    {
        var rosters = targets.ToDictionary(club => club, club => Roster(server, records[club]));
        foreach (Player player in players.Where(p => p.ClubIdOffset > 0))
        {
            int owner = BitConverter.ToInt32(people, player.ClubIdOffset);
            if (!targets.Contains(owner)) continue;
            int index = BitConverter.ToInt32(people, player.PersonOffset - 15);
            Require(rosters[owner].Contains(index),
                "Original player missing from owner roster: UID=" + player.Id + ", club=" + owner);
        }
    }

    static void RetireHistoricalDepartures(ref byte[] people, ref byte[] server, List<Player> players, List<Player> departing)
    {
        Require(departing.Select(p => p.Id).Distinct().Count() == departing.Count &&
            departing.All(p => p.Id > 0 && p.Id < 1600000000), "Duplicate or protected modern retirement UID.");
        if (departing.Count == 0) return;
        FM08_Database_Editor.RetireNativePlayersBulk(ref people, ref server, players,
            new HashSet<int>(departing.Select(p => p.Id)), new DateTime(2007, 7, 30));
    }

    static void VerifyHistoricalDepartures(byte[] oldPeople, byte[] oldServer, byte[] people, byte[] server,
        List<Player> before, List<Player> after, HashSet<int> targets)
    {
        VerifyRetiredPlayers(oldPeople, oldServer, people, server, before.Where(p => p.ClubIdOffset > 0 &&
            targets.Contains(BitConverter.ToInt32(oldPeople, p.ClubIdOffset))).ToList(), after);
    }

    static void VerifyRetiredPlayers(byte[] oldPeople, byte[] oldServer, byte[] people, byte[] server,
        List<Player> retiredBefore, List<Player> after)
    {
        int count = BitConverter.ToInt32(people, 0);
        var records = FM08_Database_Editor.ParseNativeClubDivisions(server, count);
        var rosterPeople = new HashSet<int>(records.Values.SelectMany(r => Roster(server, r)));
        var byUid = after.ToDictionary(p => p.Id);
        var retired = FM08_Database_Editor.ParseRetirements(server);
        var oldRetired = FM08_Database_Editor.ParseRetirements(oldServer);
        var loanPersons = new HashSet<int>(FM08_Database_Editor.ParseNativeLoans(server, count).Select(l => l.PersonIndex));
        foreach (Player old in retiredBefore)
        {
            Player player;
            Require(byUid.TryGetValue(old.Id, out player) && player.ClubIdOffset == 0 && player.ClubId == 0 &&
                !player.ContractExpires.HasValue && player.WeeklyWage == 0 && player.SquadNumber == 0,
                "Historical departure is not free: UID=" + old.Id);
            int index = BitConverter.ToInt32(people, player.PersonOffset - 15);
            DateTime date, expectedDate;
            if (!oldRetired.TryGetValue(old.Id, out expectedDate)) expectedDate = new DateTime(2007, 7, 30);
            Require(!rosterPeople.Contains(index) &&
                retired.TryGetValue(player.Id, out date) && date == expectedDate &&
                !loanPersons.Contains(index), "Historical departure has inconsistent roster/retirement/loan: UID=" + old.Id);
            int start = player.PersonOffset - 15;
            int footer = PersonEnd(people, player) - 8;
            int free = (int)Call("FindNativeFreePlayerClubOffset", people, start, footer, player.NationIdOffset);
            Require(free > 0 && BitConverter.ToInt32(people, free) == -1 && people[free + 27] == 0,
                "Unverified native free-player fields: UID=" + old.Id);
            int oldStart = old.PersonOffset - 15, ownerRelative = old.ClubIdOffset - oldStart;
            int length = (int)Call("GetNativeContractLength", oldPeople, old.ClubIdOffset + 28,
                PersonEnd(oldPeople, old) - 8, BitConverter.ToInt32(oldPeople, oldStart));
            Require(length >= 0, "Unsupported historical source contract: UID=" + old.Id);
            byte[] expected = new byte[PersonEnd(oldPeople, old) - oldStart];
            Buffer.BlockCopy(oldPeople, oldStart, expected, 0, expected.Length);
            expected = Replace(expected, ownerRelative + 28, length, new byte[0]);
            BitConverter.GetBytes(-1).CopyTo(expected, ownerRelative);
            expected[ownerRelative + 5] = expected[ownerRelative + 6] = 0;
            BitConverter.GetBytes((ushort)1900).CopyTo(expected, ownerRelative + 7);
            expected[ownerRelative + 27] = 0;
            Require(expected.Length == footer + 8 - start, "Released PERSON length differs: " + old.Id);
            EqualRange(expected, 0, people, start, expected.Length, "released PERSON " + old.Id);
        }
    }

    static void RewriteRosters(ref byte[] server, int count, Dictionary<int, HashSet<int>> rosters)
    {
        var records = FM08_Database_Editor.ParseNativeClubDivisions(server, count);
        foreach (var record in records.Values.Where(r => rosters.ContainsKey(r.ClubIndex)).OrderByDescending(r => r.RosterOffset))
        {
            int oldCount = BitConverter.ToUInt16(server, record.RosterOffset);
            int[] desired = rosters[record.ClubIndex].OrderBy(i => i).ToArray();
            var bytes = new byte[2 + desired.Length * 4];
            BitConverter.GetBytes(checked((ushort)desired.Length)).CopyTo(bytes, 0);
            for (int i = 0; i < desired.Length; i++) BitConverter.GetBytes(desired[i]).CopyTo(bytes, 2 + i * 4);
            server = Replace(server, record.RosterOffset, 2 + oldCount * 4, bytes);
        }
    }

    static int[] NameCounts(byte[] server)
    {
        var counts = new int[2];
        int anchor = (int)Call("FindNameTableStart", server, 5000000, server.Length - 1000);
        for (int table = 0; table < 2; table++)
        {
            if (table == 1) anchor = (int)Call("FindNameTableStart", server, anchor + 100000, server.Length - 1000);
            object[] args = { server, anchor, null, null, 0 };
            counts[table] = ((Dictionary<int, string>)Editor.GetMethod("ParseNativeNames", Private).Invoke(null, args)).Count;
        }
        return counts;
    }

    static void NormalizeAddedNameIds(byte[] server, byte[] client, int[] originalCounts)
    {
        int anchor = (int)Call("FindNameTableStart", server, 5000000, server.Length - 1000);
        for (int table = 0; table < 2; table++)
        {
            if (table == 1) anchor = (int)Call("FindNameTableStart", server, anchor + 100000, server.Length - 1000);
            object[] args = { server, anchor, null, null, 0 };
            var names = (Dictionary<int, string>)Editor.GetMethod("ParseNativeNames", Private).Invoke(null, args);
            int end = (int)args[4], start = end - 4 - names.Values.Sum(s => 22 + s.Length * 2);
            byte[] marker = new byte[64];
            Buffer.BlockCopy(server, start, marker, 0, marker.Length);
            int clientStart = (int)Call("FindNativeBytes", client, marker, 0, -1), cursor = start + 4;
            Require(clientStart >= 0, "Regression client name table missing.");
            for (int i = 0; i < names.Count; i++)
            {
                int length = 22 + names[i - 1].Length * 2;
                if (i >= originalCounts[table])
                {
                    Array.Clear(server, cursor + length - 4, 4);
                    Array.Clear(client, clientStart + cursor + length - 4 - start, 4);
                }
                cursor += length;
            }
        }
    }

    static void NormalizeAddedPeopleIds(byte[] people, byte[] server, int originalCount, int originalPersonalities, int originalAttributes)
    {
        var players = ReadPlayers(people, server, (Dictionary<int, string>)Call("ParseClubs", server),
            (Dictionary<int, string>)Call("ParseNations", server));
        foreach (Player player in players.Where(p => BitConverter.ToInt32(people, p.PersonOffset - 15) >= originalCount))
            Array.Clear(people, PersonEnd(people, player) - 4, 4);
        int attributes = AttributesStart(people), personalities = attributes - 8 - BitConverter.ToInt32(people, 4) * 17;
        for (int i = originalPersonalities; i < BitConverter.ToInt32(people, 4); i++)
            Array.Clear(people, personalities + 4 + i * 17 + 13, 4);
        for (int i = originalAttributes; i < BitConverter.ToInt32(people, 8); i++)
            Array.Clear(people, attributes + i * 89 + 85, 4);
    }

    public void TestAbBatch(string source, string csv)
    {
        byte[] people = Load(source, "people_db.dat"), server = Load(source, "server_db.dat"), client = Load(source, "client_db.dat");
        int count = BitConverter.ToInt32(people, 0), personalities = BitConverter.ToInt32(people, 4), attributes = BitConverter.ToInt32(people, 8);
        int[] nameCounts = NameCounts(server);
        var clubs = (Dictionary<int, string>)Call("ParseClubs", server);
        var nations = (Dictionary<int, string>)Call("ParseNations", server);
        FM08_Database_Editor.ClubsRev.Clear();
        foreach (var entry in clubs) if (!FM08_Database_Editor.ClubsRev.ContainsKey(entry.Value))
            FM08_Database_Editor.ClubsRev.Add(entry.Value, entry.Key);
        FM08_Database_Editor.NationsRev.Clear();
        foreach (var entry in nations) if (!FM08_Database_Editor.NationsRev.ContainsKey(entry.Value))
            FM08_Database_Editor.NationsRev.Add(entry.Value, entry.Key);
        FM08_Database_Editor.InitCsvRegistry();
        var independentReferences = new Dictionary<int, int> { { 956, 779 }, { 995, 818 }, { 1006, 829 } };
        var rows = AbRows(csv).Where(r => int.Parse(r["ExistingID"]) < 0 &&
            independentReferences.ContainsKey(int.Parse(r["ClubIndex"])))
            .GroupBy(r => r["ClubIndex"]).Select(g => g.First()).ToList();
        Require(rows.Count == 3, "Missing three-club batch contract fixtures.");
        var oldPlayers = ReadPlayers(people, server, clubs, nations);
        var incoming = rows.Select(r => { var p = new Player { Id = -1 }; SetProfile(p, r); return p; }).ToList();
        var targets = incoming.Select((p, i) => new { p, club = int.Parse(rows[i]["ClubIndex"]) }).ToDictionary(e => e.p, e => e.club);
        byte[] bulkPeople = (byte[])people.Clone(), bulkServer = (byte[])server.Clone(), bulkClient = (byte[])client.Clone();
        var pool = new IdPool(bulkPeople, bulkServer, bulkClient);
        AppendBatch(ref bulkPeople, ref bulkServer, ref bulkClient, incoming, oldPlayers, targets, pool);
        foreach (Player player in incoming)
            Require(BitConverter.ToInt32(bulkPeople, player.ClubIdOffset + 28 + 31) == independentReferences[targets[player]],
                "Bulk contract differs from independently established SI club reference.");
        var rosters = FM08_Database_Editor.ParseNativeClubDivisions(bulkServer, count + incoming.Count);
        var desired = targets.Values.Distinct().ToDictionary(c => c, c => Roster(bulkServer, rosters[c]));
        foreach (Player player in incoming) desired[targets[player]].Add(BitConverter.ToInt32(bulkPeople, player.PersonOffset - 15));
        RewriteRosters(ref bulkServer, count + incoming.Count, desired);
        pool.Verify(bulkPeople, bulkServer, bulkClient);
        oldPlayers = ReadPlayers(people, server, clubs, nations);
        var singles = rows.Select(r => { var p = new Player { Id = -1 }; SetProfile(p, r); return p; }).ToList();
        int next = 1601000000;
        foreach (Player player in singles)
        {
            FM08_Database_Editor.AppendNativePlayerWithIdentityCursor(ref people, ref server, ref client, player, oldPlayers, ref next);
            oldPlayers.Add(player);
        }
        FM08_Database_Editor.SyncClubAssignments(ref people, ref server, oldPlayers);
        NormalizeAddedPeopleIds(people, server, count, personalities, attributes);
        NormalizeAddedPeopleIds(bulkPeople, bulkServer, count, personalities, attributes);
        NormalizeAddedNameIds(server, client, nameCounts);
        NormalizeAddedNameIds(bulkServer, bulkClient, nameCounts);
        Require(people.SequenceEqual(bulkPeople) && server.SequenceEqual(bulkServer) && client.SequenceEqual(bulkClient),
            "Bulk serialization differs from verified single-player native writes.");
        Console.WriteLine("PASS: bulk construction exactly matches three verified sequential native writes, except allocated UIDs.");
        Console.WriteLine("PASS: all original bytes, reused/new name reference counts, primary contracts and native rosters match.");
    }

    public void SerieAb(string source, string output, string csv, bool verifyOnly)
    {
        var rows = AbRows(csv);
        if (verifyOnly) { VerifyAb(source, output, rows); return; }
        Require(!Directory.Exists(output) && !File.Exists(output), "A/B output already exists.");
        Require(!output.StartsWith(source.TrimEnd('\\') + "\\", StringComparison.OrdinalIgnoreCase), "Output is inside source.");
        byte[] people = Load(source, "people_db.dat"), server = Load(source, "server_db.dat"), client = Load(source, "client_db.dat");
        int originalCount = BitConverter.ToInt32(people, 0);
        var clubs = (Dictionary<int, string>)Call("ParseClubs", server);
        FM08_Database_Editor.ResolveNativeU23ClubNames(server, originalCount, clubs);
        var nations = (Dictionary<int, string>)Call("ParseNations", server);
        var players = ReadPlayers(people, server, clubs, nations);
        var byId = players.ToDictionary(p => p.Id);
        var byPerson = players.ToDictionary(p => BitConverter.ToInt32(people, p.PersonOffset - 15));
        var records = FM08_Database_Editor.ParseNativeClubDivisions(server, originalCount);
        FM08_Database_Editor.ClubsRev.Clear();
        foreach (var item in clubs) if (!FM08_Database_Editor.ClubsRev.ContainsKey(item.Value))
            FM08_Database_Editor.ClubsRev.Add(item.Value, item.Key);
        FM08_Database_Editor.NationsRev.Clear();
        foreach (var item in nations) if (!FM08_Database_Editor.NationsRev.ContainsKey(item.Value))
            FM08_Database_Editor.NationsRev.Add(item.Value, item.Key);
        FM08_Database_Editor.InitCsvRegistry();
        var targets = new HashSet<int>(rows.Select(r => int.Parse(r["ClubIndex"])));
        var actualAb = new HashSet<int>(records.Values.Where(r => r.CurrentDivisionIndex == 22 || r.CurrentDivisionIndex == 23).Select(r => r.ClubIndex));
        Require(targets.Count == 42 && targets.SetEquals(actualAb), "Input must cover exactly the current 20 A and 22 B clubs.");
        var incoming = new List<Player>();
        var newPlayers = new List<Player>();
        var retained = new HashSet<int>();
        var targetByPlayer = new Dictionary<Player, int>();
        var keys = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var row in rows)
        {
            int club = int.Parse(row["ClubIndex"]), id = int.Parse(row["ExistingID"]);
            Require(clubs[club] == row["Club"] && nations.Values.Contains(row["Nationality"]), "Unverified club/nationality.");
            Require(keys.Add(row["FirstName"] + "|" + row["LastName"] + "|" + row["BirthDate"]), "Duplicate incoming identity.");
            Player player;
            if (id > 0)
            {
                Require(byId.TryGetValue(id, out player) && player.ClubIdOffset > 0 &&
                    BitConverter.ToInt32(people, player.ClubIdOffset) == 992 && retained.Add(id),
                    "Only verified existing modern Inter identities may be reused.");
                player = byId[id];
                Require(player.FirstName == row["FirstName"] && player.LastName == row["LastName"] &&
                    player.BirthDate.Value.ToString("yyyy-MM-dd") == row["BirthDate"], "Reused identity differs.");
            }
            else { player = new Player { Id = -1 }; newPlayers.Add(player); }
            incoming.Add(player);
            targetByPlayer.Add(player, club);
        }
        var departing = new List<Player>();
        var released = new List<Player>();
        ValidateTargetOwnerRosters(people, server, players, targets, records);
        foreach (int club in targets)
            foreach (int index in Roster(server, records[club]))
            {
                Player player;
                Require(byPerson.TryGetValue(index, out player), "Unsupported original roster PERSON=" + index + ", club=" + club);
                if (!IsOwnedRosterPlayer(people, server, player, club, records)) continue;
                if (retained.Contains(player.Id)) continue;
                if (player.Id >= 1600000000)
                {
                    Require(club == 992, "Unexpected modern identity outside Inter.");
                    released.Add(player);
                }
                else departing.Add(player);
            }
        Require(departing.Select(p => p.Id).Distinct().Count() == departing.Count, "Duplicate departing player.");
        foreach (Player player in released) { player.Club = ""; player.ClubAssignmentPending = true; }
        FM08_Database_Editor.SyncClubAssignments(ref people, ref server, players);
        Console.WriteLine("Preflight: " + targets.Count + " clubs, " + incoming.Count + " profiles, " + retained.Count +
            " reused, " + released.Count + " active Inter departures kept unretired.");
        for (int i = 0; i < incoming.Count; i++) SetProfile(incoming[i], rows[i]);
        foreach (int club in targets)
        {
            var squad = incoming.Where(p => targetByPlayer[p] == club).ToList();
            Require(squad.Count >= 17 && squad.Count <= 45 && squad.Count(p => p.PosGK == 20) >= 1 &&
                squad.Select(p => p.SquadNumber).Distinct().Count() == squad.Count, "Incomplete A/B squad.");
        }
        var retiredIndices = new HashSet<int>(departing.Select(p => BitConverter.ToInt32(people, p.PersonOffset - 15)));
        var removeLoans = new HashSet<int>(retiredIndices);
        foreach (var loan in FM08_Database_Editor.ParseNativeLoans(server, originalCount))
            if (targets.Contains(loan.ClubId)) removeLoans.Add(loan.PersonIndex);
        server = FM08_Database_Editor.RemoveNativeLoans(server, originalCount, removeLoans);
        RetireHistoricalDepartures(ref people, ref server, players, departing);
        foreach (Player player in incoming.Where(p => retained.Contains(p.Id))) WriteProfile(player, people);
        FM08_Database_Editor.SyncClubAssignments(ref people, ref server, players);
        var pool = new IdPool(people, server, client);
        AppendBatch(ref people, ref server, ref client, newPlayers, players, targetByPlayer, pool);
        var finalRosters = targets.ToDictionary(c => c,
            c => new HashSet<int>(incoming.Where(p => targetByPlayer[p] == c).Select(p => BitConverter.ToInt32(people, p.PersonOffset - 15))));
        RewriteRosters(ref server, BitConverter.ToInt32(people, 0), finalRosters);
        pool.Verify(people, server, client);
        Console.WriteLine("PASS: bulk native records, matching name references and collision-free identities.");
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
            File.WriteAllBytes(Path.Combine(output, entry.Key), (byte[])Call("CompressFile", entry.Value,
                (byte[])Call("GetFileHeader", Path.Combine(source, entry.Key))));
        FM08_Database_Editor.WriteDatabaseMetadata(source, output);
        VerifyAb(source, output, rows);
        Console.WriteLine("Published A/B database: " + output);
    }

    void VerifyAb(string source, string output, List<Dictionary<string, string>> rows)
    {
        byte[] oldPeople = Load(source, "people_db.dat"), oldServer = Load(source, "server_db.dat");
        byte[] people = Load(output, "people_db.dat"), server = Load(output, "server_db.dat");
        var oldClubs = (Dictionary<int, string>)Call("ParseClubs", oldServer);
        var clubs = (Dictionary<int, string>)Call("ParseClubs", server);
        FM08_Database_Editor.ResolveNativeU23ClubNames(server, BitConverter.ToInt32(people, 0), clubs);
        var before = ReadPlayers(oldPeople, oldServer, oldClubs, (Dictionary<int, string>)Call("ParseNations", oldServer));
        var after = ReadPlayers(people, server, clubs, (Dictionary<int, string>)Call("ParseNations", server));
        var byId = after.ToDictionary(p => p.Id);
        var byIdentity = after.GroupBy(p => p.FirstName + "|" + p.LastName + "|" +
            (p.BirthDate.HasValue ? p.BirthDate.Value.ToString("yyyy-MM-dd") : ""), StringComparer.OrdinalIgnoreCase)
            .ToDictionary(g => g.Key, g => g.ToList(), StringComparer.OrdinalIgnoreCase);
        var retained = new HashSet<int>(rows.Where(r => int.Parse(r["ExistingID"]) > 0).Select(r => int.Parse(r["ExistingID"])));
        var targets = new HashSet<int>(rows.Select(r => int.Parse(r["ClubIndex"])));
        var contractReferences = FM08_Database_Editor.ResolveNativeClubContractReferences(
            server, BitConverter.ToInt32(people, 0), targets);
        var oldRecords = FM08_Database_Editor.ParseNativeClubDivisions(oldServer, BitConverter.ToInt32(oldPeople, 0));
        var records = FM08_Database_Editor.ParseNativeClubDivisions(server, BitConverter.ToInt32(people, 0));
        var retirements = FM08_Database_Editor.ParseRetirements(server);
        var oldRetirements = FM08_Database_Editor.ParseRetirements(oldServer);
        var oldIndices = new HashSet<int>(targets.SelectMany(t => Roster(oldServer, oldRecords[t])));
        var owned = before.Where(p => p.ClubIdOffset > 0 &&
            targets.Contains(BitConverter.ToInt32(oldPeople, p.ClubIdOffset))).ToList();
        var departing = owned.Where(p => oldIndices.Contains(BitConverter.ToInt32(oldPeople, p.PersonOffset - 15)) &&
            !retained.Contains(p.Id) && p.Id < 1600000000).ToList();
        var released = owned.Where(p => oldIndices.Contains(BitConverter.ToInt32(oldPeople, p.PersonOffset - 15)) &&
            !retained.Contains(p.Id) && p.Id >= 1600000000).ToList();
        var retiredIndices = new HashSet<int>(departing.Select(p => BitConverter.ToInt32(oldPeople, p.PersonOffset - 15)));
        var importedIndices = targets.ToDictionary(t => t, t => new HashSet<int>());
        foreach (var row in rows)
        {
            string key = row["FirstName"] + "|" + row["LastName"] + "|" + row["BirthDate"];
            List<Player> matches;
            Require(byIdentity.TryGetValue(key, out matches) && matches.Count == 1, "Persisted identity missing or duplicated: " + key);
            Player player = matches[0];
            if (int.Parse(row["ExistingID"]) > 0) Require(player.Id == int.Parse(row["ExistingID"]), "Existing modern UID not preserved.");
            foreach (var field in row)
            {
                if (new[] { "ExistingID", "ClubIndex", "BirthDate" }.Contains(field.Key)) continue;
                Require(Convert.ToString(Value(player, field.Key), CultureInfo.InvariantCulture).Equals(field.Value, StringComparison.OrdinalIgnoreCase),
                    "Persisted field differs: " + player.FullName + " / " + field.Key);
            }
            int index = BitConverter.ToInt32(people, player.PersonOffset - 15), contract = player.ClubIdOffset + 28;
            Require(player.ClubIdOffset > 0 && BitConverter.ToInt32(people, player.ClubIdOffset) == int.Parse(row["ClubIndex"]) &&
                player.ContractExpires == new DateTime(2010, 6, 30) && people[contract - 1] == 1 &&
                people[contract + 1] == 1 &&
                BitConverter.ToInt32(people, contract + 31) == contractReferences[int.Parse(row["ClubIndex"])] &&
                BitConverter.ToInt32(people, contract + 26) == index &&
                BitConverter.ToInt32(people, contract + 35) == player.WeeklyWage, "Invalid primary contract: " + player.FullName);
            Require(!retirements.ContainsKey(player.Id), "Modern player marked retired.");
            importedIndices[int.Parse(row["ClubIndex"])].Add(index);
        }
        int added = rows.Count - retained.Count;
        for (int i = 0; i < 3; i++)
            Require(BitConverter.ToInt32(people, i * 4) == BitConverter.ToInt32(oldPeople, i * 4) + added, "Native entity count mismatch.");
        Require(records.Count == oldRecords.Count && targets.Count == 42, "Native club count mismatch.");
        foreach (var old in oldRecords.Values)
        {
            var current = records[old.ClubIndex];
            Require(old.CurrentDivisionIndex == current.CurrentDivisionIndex && old.PreviousDivisionIndex == current.PreviousDivisionIndex &&
                old.EuropeanCompetitionIndex == current.EuropeanCompetitionIndex, "Competition changed.");
            if (targets.Contains(old.ClubIndex))
                Require(Roster(server, current).SetEquals(importedIndices[old.ClubIndex]), "Persisted target roster differs.");
            else
            {
                VerifyClubAfterRelease(oldServer, server, old, current, retiredIndices);
            }
        }
        VerifyRetiredPlayers(oldPeople, oldServer, people, server, departing, after);
        foreach (Player player in released)
        {
            Player current = byId[player.Id];
            Require(!retirements.ContainsKey(player.Id) && current.ClubId == 0 && !current.ContractExpires.HasValue,
                "Active modern departure retired or still contracted.");
        }
        var departingIds = new HashSet<int>(departing.Select(p => p.Id));
        foreach (var entry in oldRetirements)
            if (!departingIds.Contains(entry.Key))
                Require(retirements.ContainsKey(entry.Key) && retirements[entry.Key] == entry.Value,
                    "Unrelated earlier retirement changed: " + entry.Key);
        Require(retirements.Count == oldRetirements.Count + departing.Count(p => !oldRetirements.ContainsKey(p.Id)), "Unexpected retirement.");
        var modified = new HashSet<int>(departing.Select(p => p.Id).Concat(released.Select(p => p.Id)).Concat(retained));
        int oldAttributes = AttributesStart(oldPeople), attributes = AttributesStart(people);
        int oldPersonalities = oldAttributes - 8 - BitConverter.ToInt32(oldPeople, 4) * 17;
        int personalities = attributes - 8 - BitConverter.ToInt32(people, 4) * 17;
        int oldCursor = 16, cursor = 16;
        foreach (Player player in before.Where(p => modified.Contains(p.Id)).OrderBy(p => p.PersonOffset))
        {
            Player current = byId[player.Id];
            int oldStart = player.PersonOffset - 15, start = current.PersonOffset - 15;
            Require(oldStart - oldCursor == start - cursor, "Unrelated PERSON prefix shifted unexpectedly.");
            EqualRange(oldPeople, oldCursor, people, cursor, oldStart - oldCursor, "untouched PERSON segment");
            oldCursor = PersonEnd(oldPeople, player); cursor = PersonEnd(people, current);
        }
        Require(oldPersonalities - oldCursor == personalities - added * 299 - cursor, "Unrelated PERSON suffix size changed.");
        EqualRange(oldPeople, oldCursor, people, cursor, oldPersonalities - oldCursor, "untouched PERSON suffix");
        var retainedAttributes = new HashSet<int>(before.Where(p => retained.Contains(p.Id))
            .Select(p => BitConverter.ToInt32(oldPeople, p.PersonOffset)));
        var retainedPersonalities = new HashSet<int>(before.Where(p => retained.Contains(p.Id))
            .Select(p => BitConverter.ToInt32(oldPeople, p.PersonOffset - 15 + 181)));
        for (int i = 0; i < BitConverter.ToInt32(oldPeople, 8); i++)
            EqualRange(oldPeople, oldAttributes + i * 89 + (retainedAttributes.Contains(i) ? 81 : 0),
                people, attributes + i * 89 + (retainedAttributes.Contains(i) ? 81 : 0),
                retainedAttributes.Contains(i) ? 8 : 89, "original attributes " + i);
        for (int i = 0; i < BitConverter.ToInt32(oldPeople, 4); i++)
        {
            int offset = retainedPersonalities.Contains(i) ? 9 : 0;
            EqualRange(oldPeople, oldPersonalities + 4 + i * 17 + offset,
                people, personalities + 4 + i * 17 + offset, 17 - offset, "original personality " + i);
        }
        int oldEnd = oldAttributes + BitConverter.ToInt32(oldPeople, 8) * 89;
        int end = attributes + BitConverter.ToInt32(people, 8) * 89;
        Require(oldPeople.Length - oldEnd == people.Length - end, "Original people suffix size differs.");
        EqualRange(oldPeople, oldEnd, people, end, oldPeople.Length - oldEnd, "untouched people suffix");
        var removedLoans = new HashSet<int>(departing.Select(p => BitConverter.ToInt32(oldPeople, p.PersonOffset - 15)));
        var oldLoans = FM08_Database_Editor.ParseNativeLoans(oldServer, BitConverter.ToInt32(oldPeople, 0));
        foreach (var loan in oldLoans) if (targets.Contains(loan.ClubId)) removedLoans.Add(loan.PersonIndex);
        var expectedLoans = oldLoans.Where(l => !removedLoans.Contains(l.PersonIndex)).Select(l => l.PersonIndex + "|" + l.ClubId).OrderBy(s => s);
        var loans = FM08_Database_Editor.ParseNativeLoans(server, BitConverter.ToInt32(people, 0)).Select(l => l.PersonIndex + "|" + l.ClubId).OrderBy(s => s);
        Require(expectedLoans.SequenceEqual(loans), "Unrelated historical loan changed.");
        foreach (string path in Directory.GetFiles(source, "*", SearchOption.AllDirectories))
        {
            string relative = path.Substring(source.TrimEnd('\\').Length + 1);
            if (new[] { "people_db.dat", "server_db.dat", "client_db.dat" }.Contains(relative) ||
                (string.IsNullOrEmpty(Path.GetDirectoryName(relative)) && Path.GetExtension(relative).Equals(".xml", StringComparison.OrdinalIgnoreCase))) continue;
            Require(File.ReadAllBytes(path).SequenceEqual(File.ReadAllBytes(Path.Combine(output, relative))), "Protected database file changed.");
        }
        File.WriteAllLines(Path.Combine(output, "serie_ab_import_summary.txt"), new[] {
            "Clubs=" + targets.Count, "Players=" + rows.Count, "Created=" + added, "Reused=" + retained.Count,
            "RetiredHistorical=" + departing.Count, "ActiveDeparturesKeptUnretired=" + released.Count,
            "Verification=PASS: exact profiles/contracts/rosters; protected clubs/PERSON/attributes/personality/files unchanged",
            "Source=" + source, "Input=" + Path.GetFileName("italian_ab_import_2026_27.csv"),
            "Acceptance=Not yet opened in official SI editor or tested in a new game",
        }, new UTF8Encoding(false));
        Console.WriteLine("PASS: reloaded " + rows.Count + " exact profiles and contracts across 42 clubs; " +
            departing.Count + " historical retirements; all Serie C/U23 and unrelated data preserved.");
    }
}
