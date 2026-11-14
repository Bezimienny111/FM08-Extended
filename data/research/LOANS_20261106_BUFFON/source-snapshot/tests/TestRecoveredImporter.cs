using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using Player = FM08_Database_Editor.PlayerRecord;
using Club = FM08_Database_Editor.NativeClubDivisionRecord;

class TestRecoveredImporter
{
    static int passed;

    static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }

    static void Invoke(string name, params object[] args)
    {
        var method = typeof(VerifiedNativeSquadsWorker).GetMethod(name,
            BindingFlags.NonPublic | BindingFlags.Static);
        Require(method != null, "Missing importer method: " + name);
        method.Invoke(null, args);
    }

    static void Check(string name, Action action)
    {
        action();
        passed++;
        Console.WriteLine("PASS: " + name);
    }

    static void Reject(string name, Action action)
    {
        Check(name, delegate {
            try { action(); }
            catch (TargetInvocationException error)
            {
                if (!(error.InnerException is InvalidDataException)) throw;
                return;
            }
            throw new InvalidOperationException("Invalid input accepted: " + name);
        });
    }

    static Club Record(int footer)
    {
        return new Club { ClubIndex = 100, Start = 2, RosterOffset = 10, Footer = footer };
    }

    static byte[] OldRoster()
    {
        byte[] data = Enumerable.Range(0, 80).Select(i => (byte)(i + 1)).ToArray();
        BitConverter.GetBytes((ushort)3).CopyTo(data, 10);
        BitConverter.GetBytes(10).CopyTo(data, 12);
        BitConverter.GetBytes(20).CopyTo(data, 16);
        BitConverter.GetBytes(30).CopyTo(data, 20);
        return data;
    }

    static byte[] ReleasedRoster(byte[] old)
    {
        byte[] data = new byte[old.Length - 4];
        Buffer.BlockCopy(old, 0, data, 0, 20);
        BitConverter.GetBytes((ushort)2).CopyTo(data, 10);
        BitConverter.GetBytes(30).CopyTo(data, 16);
        Buffer.BlockCopy(old, 24, data, 20, old.Length - 24);
        return data;
    }

    static void CheckProtectedClubs()
    {
        byte[] old = OldRoster(), current = ReleasedRoster(old);
        var released = new HashSet<int> { 20 };
        Check("protected roster permits only approved removal and preserves raw prefix/suffix",
            () => Invoke("VerifyClubAfterRelease", old, current, Record(39), Record(35), released));
        Check("unchanged protected club is accepted",
            () => Invoke("VerifyClubAfterRelease", old, (byte[])old.Clone(), Record(39), Record(39), new HashSet<int>()));
        Reject("unapproved protected roster removal", () =>
            Invoke("VerifyClubAfterRelease", old, current, Record(39), Record(35), new HashSet<int>()));
        Reject("approved retirement still present in roster", () =>
            Invoke("VerifyClubAfterRelease", old, old, Record(39), Record(39), released));
        byte[] changed = (byte[])current.Clone();
        changed[2] ^= 1;
        Reject("protected CLUB prefix mutation", () =>
            Invoke("VerifyClubAfterRelease", old, changed, Record(39), Record(35), released));
        changed = (byte[])current.Clone();
        changed[25] ^= 1;
        Reject("protected CLUB suffix mutation", () =>
            Invoke("VerifyClubAfterRelease", old, changed, Record(39), Record(35), released));
        changed = (byte[])current.Clone();
        BitConverter.GetBytes(10).CopyTo(changed, 16);
        Reject("duplicate protected roster PERSON", () =>
            Invoke("VerifyClubAfterRelease", old, changed, Record(39), Record(35), released));
        Reject("protected CLUB structural length mismatch", () =>
            Invoke("VerifyClubAfterRelease", old, current, Record(39), Record(36), released));
        byte[] snapshot = OldRoster();
        Require(old.SequenceEqual(snapshot), "Verifier modified source CLUB bytes.");
    }

    static void CheckRetirementGuards()
    {
        foreach (int[] ids in new[] { new[] { 1600000000 }, new[] { 0 }, new[] { -1 }, new[] { 55, 55 } })
        {
            byte[] people = { 1, 2, 3 }, server = { 4, 5, 6 };
            var departing = ids.Select(id => new Player { Id = id }).ToList();
            object[] arguments = { people, server, new List<Player>(), departing };
            Reject("retirement rejects UID set " + string.Join(",", ids), () =>
                Invoke("RetireHistoricalDepartures", arguments));
            Require(object.ReferenceEquals(arguments[0], people) && object.ReferenceEquals(arguments[1], server) &&
                people.SequenceEqual(new byte[] { 1, 2, 3 }) && server.SequenceEqual(new byte[] { 4, 5, 6 }),
                "Rejected retirement changed buffers.");
        }
        Check("empty retirement selection is an unchanged no-op", delegate {
            byte[] people = { 1 }, server = { 2 };
            object[] args = { people, server, new List<Player>(), new List<Player>() };
            Invoke("RetireHistoricalDepartures", args);
            Require(object.ReferenceEquals(args[0], people) && object.ReferenceEquals(args[1], server),
                "Empty retirement replaced buffers.");
        });
    }

    static Dictionary<string, string> Profile()
    {
        return new Dictionary<string, string> {
            { "FirstName", "Test" }, { "LastName", "\u0141\u00f3d\u017a" },
            { "BirthDate", "1980-02-29" }, { "Club", "Test Club" }, { "Nationality", "Algeria" },
            { "CA", "1" }, { "PA", "1" }, { "WeeklyWage", "1" },
            { "Height", "140" }, { "Weight", "45" }, { "SquadNumber", "1" },
            { "PosGK", "20" }, { "Determination", "0" }
        };
    }

    static void CheckProfiles()
    {
        Check("profile lower bounds, leap-day DOB, Unicode and determination zero", delegate {
            var player = new Player();
            Invoke("SetProfile", player, Profile());
            Require(player.CA == 1 && player.PA == 1 && player.Determination == 0 &&
                player.PosGK == 20 && player.LastName == "\u0141\u00f3d\u017a" &&
                player.BirthDate == new DateTime(1980, 2, 29) &&
                player.ContractExpires == new DateTime(2010, 6, 30), "Profile did not round-trip.");
        });
        Check("profile upper bounds", delegate {
            var row = Profile();
            foreach (var pair in new Dictionary<string, string> {
                { "CA", "200" }, { "PA", "200" }, { "Height", "220" },
                { "Weight", "130" }, { "SquadNumber", "99" }, { "Determination", "20" }
            }) row[pair.Key] = pair.Value;
            Invoke("SetProfile", new Player(), row);
        });
        foreach (var pair in new Dictionary<string, string> {
            { "CA", "0" }, { "PA", "201" }, { "WeeklyWage", "0" },
            { "Height", "139" }, { "Weight", "131" }, { "SquadNumber", "100" },
            { "PosGK", "21" }, { "Determination", "-1" }, { "UnknownColumn", "1" }
        })
        {
            var row = Profile();
            row[pair.Key] = pair.Value;
            Reject("invalid profile field " + pair.Key + "=" + pair.Value, () =>
                Invoke("SetProfile", new Player(), row));
        }
        var invalid = Profile();
        invalid["CA"] = "100";
        invalid["PA"] = "99";
        Reject("PA below CA", () => Invoke("SetProfile", new Player(), invalid));
    }

    static void Main()
    {
        CheckProtectedClubs();
        CheckRetirementGuards();
        CheckProfiles();
        Console.WriteLine("PASS: " + passed + " direct rebuilt-importer checks; no database writes.");
    }
}
