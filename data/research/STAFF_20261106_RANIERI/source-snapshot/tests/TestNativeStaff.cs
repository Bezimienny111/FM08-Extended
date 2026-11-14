using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Collections.Generic;
using System.Web.Script.Serialization;
using Staff = FM08_Database_Editor;
class TestNativeStaff
{
    static int passed;
    static void Check(bool ok, string name) { if (!ok) throw new InvalidDataException(name); passed++; Console.WriteLine("PASS: " + name); }
    static void Reject(Action action, string name) { try { action(); } catch (InvalidDataException) { Check(true, name); return; } throw new Exception("Accepted invalid plan: " + name); }
    static Staff.NativeStaffWageChange Change(int oldWage, int wage) { return new Staff.NativeStaffWageChange { Id = 4201569, ExpectedClubIndex = 995, ExpectedWeeklyWage = oldWage, WeeklyWage = wage }; }
    static int Main(string[] a) { try {
        if (a.Length != 3 || File.Exists(a[2])) throw new ArgumentException("official-802 TEST_STAFF_WAGE NEW-report.json");
        string baseline = Path.GetFullPath(a[0]), fixture = Path.GetFullPath(a[1]);
        var pins = NativeStaffTool.Hashes(baseline); var fixturePins = NativeStaffTool.Hashes(fixture);
        byte[] p = NativeStaffTool.Load(baseline, "people_db.dat"), s = NativeStaffTool.Load(baseline, "server_db.dat"), q = NativeStaffTool.Load(fixture, "people_db.dat"), t = NativeStaffTool.Load(fixture, "server_db.dat");
        var before = Staff.ReadNativeStaff(p, s, 4201569); var after = Staff.ReadNativeStaff(q, t, 4201569);
        Check(before.PersonIndex == 129460 && after.PersonIndex == 129460 && before.PersonTypeRaw == 1 && before.RecordLength == 272 && after.RecordLength == 272, "Ranieri native identity and structural boundaries");
        Check(before.FirstName == "Claudio" && before.LastName == "Ranieri" && after.FirstName == before.FirstName && after.LastName == before.LastName, "Name dictionaries resolve identity before and after SI");
        Check(before.ClubIndex == 995 && after.ClubIndex == 995 && before.ClubRoleRaw == after.ClubRoleRaw && before.BirthDate == after.BirthDate && before.ContractExpires == after.ContractExpires, "Club, raw role, birth date and expiry preserved");
        Check(before.WeeklyWage == 0 && after.WeeklyWage == 12345, "SI wage 0 to 12345 decoded without conversion");
        var change = Change(0, 12345); byte[] edited = Staff.ApplyNativeStaffWages(p, s, new[] { change });
        var expected = (byte[])p.Clone(); BitConverter.GetBytes(12345).CopyTo(expected, before.WageOffset);
        Check(edited.SequenceEqual(expected) && !object.ReferenceEquals(p, edited), "Native update changes only the selected wage int32");
        Check(Staff.ReadNativeStaff(edited, s, 4201569).WeeklyWage == 12345, "Updated staff reads back with new wage");
        byte[] normalized = q.Skip(after.PersonOffset).Take(after.RecordLength).ToArray();
        Buffer.BlockCopy(p, before.PersonOffset + 29, normalized, 29, 8);
        Check(edited.Skip(before.PersonOffset).Take(before.RecordLength).SequenceEqual(normalized), "Whole staff PERSON matches SI except resolved name indices");
        Check(Staff.ApplyNativeStaffWages(edited, s, new[] { Change(12345, 0) }).SequenceEqual(p), "Returning wage to zero restores every source byte");
        Reject(() => Staff.ApplyNativeStaffWages(p, s, new[] { Change(1, 2) }), "Stale expected wage rejected");
        var wrongClub = Change(0, 1); wrongClub.ExpectedClubIndex = 992;
        Reject(() => Staff.ApplyNativeStaffWages(p, s, new[] { wrongClub }), "Stale expected club rejected");
        Reject(() => Staff.ApplyNativeStaffWages(p, s, new[] { change, change }), "Duplicate staff UID rejected before any mutation");
        Reject(() => Staff.ApplyNativeStaffWages(p, s, new[] { Change(0, -1) }), "Negative wage rejected");
        Reject(() => Staff.ReadNativeStaff(p, s, 11133), "Player UID rejected by staff reader");
        Reject(() => Staff.ReadNativeStaff(p, s, 1), "UID-like bytes inside a later payload rejected");
        Reject(() => Staff.ReadNativeStaff(p, s, 1900000999), "Missing staff UID rejected");
        var broken = (byte[])p.Clone(); BitConverter.GetBytes(-3).CopyTo(broken, before.WageOffset);
        Reject(() => Staff.ReadNativeStaff(broken, s, 4201569), "Malformed native wage rejected");
        Check(object.ReferenceEquals(p, Staff.ApplyNativeStaffWages(p, s, new Staff.NativeStaffWageChange[0])), "Empty plan is a no-op");
        Check(pins.OrderBy(x => x.Key).SequenceEqual(NativeStaffTool.Hashes(baseline).OrderBy(x => x.Key)) && fixturePins.OrderBy(x => x.Key).SequenceEqual(NativeStaffTool.Hashes(fixture).OrderBy(x => x.Key)), "All source and SI fixture hashes unchanged");
        File.WriteAllText(a[2], new JavaScriptSerializer { MaxJsonLength = int.MaxValue }.Serialize(new { status = "pass", checks = passed, baseline, fixture, baseline_hashes = pins, fixture_hashes = fixturePins, before, after, database_writes = false, si_acceptance_of_native_output = "not_tested", game_behavior = "not_tested" }), new UTF8Encoding(false));
        Console.WriteLine("PASS: " + passed + " staff checks; no database writes."); return 0;
    } catch (Exception ex) { Console.Error.WriteLine(ex); return 1; } }
}
