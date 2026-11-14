using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Windows.Forms;
using System.Drawing;

public partial class FM08_Database_Editor
{
    public sealed class NativeStaffRecord
    {
        public int Id, PersonIndex, PersonOffset, RecordLength, ClubIndex, WageOffset, WeeklyWage;
        public byte PersonTypeRaw, ClubRoleRaw;
        public string FirstName, LastName, Club;
        public DateTime? BirthDate, ContractExpires;
    }
    public sealed class NativeStaffWageChange
    {
        public int Id, ExpectedClubIndex, ExpectedWeeklyWage, WeeklyWage;
    }

    private static bool IsNativeStaffBoundary(byte[] people, int at, int end, int total)
    {
        if (at == end) return true;
        if (at < 16 || at > end - 19) return false;
        int index = BitConverter.ToInt32(people, at); byte kind = people[at + 4];
        if (index < 0 || index >= total || kind < 1 || kind > 5) return false;
        if (kind <= 3) for (int o = 5; o <= 13; o += 2) {
            int value = BitConverter.ToInt16(people, at + o); if (value < -10 || value > 200) return false;
        }
        return true;
    }

    // Existing contracted non-player PERSONs only. No player attribute table writes.
    public static NativeStaffRecord ReadNativeStaff(byte[] people, byte[] server, int uid)
    {
        if (people == null || server == null) throw new ArgumentNullException("Native database buffers are required.");
        if (uid <= 0 || people.Length < 16) throw new InvalidDataException("A positive staff UID is required.");
        int attributeStart = Find89ByteTable(people) - 81;
        long boundary = attributeStart - 8L - BitConverter.ToInt32(people, 4) * 17L;
        int total = BitConverter.ToInt32(people, 0);
        if (boundary < 16 || boundary > people.Length || total <= 0) throw new InvalidDataException("Unverified PERSON table boundary.");
        int end = (int)boundary, fnStart, snStart, cnStart;
        var first = ParseFirstNames(server, out fnStart, out snStart);
        Dictionary<int, string> ignored;
        var last = ParseSurnames(server, snStart, out ignored, out cnStart);
        var clubs = ParseClubs(server);
        var found = new List<NativeStaffRecord>();
        byte[] identity = BitConverter.GetBytes(uid);
        int identityAt = FindNativeBytes(people, identity, 16, end - 16);
        while (identityAt >= 0 && identityAt < end)
        {
            int footer = identityAt - 4;
            int index = footer >= 16 ? BitConverter.ToInt32(people, footer) : -1;
            if (index >= 0 && index < total && (IsNativeStaffBoundary(people, identityAt + 4, end, total) || IsNativeStaffBoundary(people, identityAt + 6, end, total)))
            {
                byte[] prefix = new byte[5]; BitConverter.GetBytes(index).CopyTo(prefix, 0); prefix[4] = 1;
                int lower = Math.Max(16, footer - 16384);
                int start = FindNativeBytes(people, prefix, lower, footer - lower);
                while (start >= 0 && start <= footer - 120)
                {
                    string fn = null, sn = null;
                    int firstRef = BitConverter.ToInt32(people, start + 29), lastRef = BitConverter.ToInt32(people, start + 33);
                    bool names = first.TryGetValue(firstRef - 1, out fn) && last.TryGetValue(lastRef - 1, out sn);
                    bool ratings = true;
                    for (int o = 5; o <= 13; o += 2) { int v = BitConverter.ToInt16(people, start + o); if (v < -10 || v > 200) ratings = false; }
                    // A matching UID inside a later person's payload cannot extend this PERSON.
                    int earlier = FindNativeBytes(people, BitConverter.GetBytes(index), start + 120, footer - start - 120);
                    bool earlierEnd = false;
                    while (earlier >= 0 && earlier < footer) {
                        if (BitConverter.ToInt32(people, earlier + 4) > 0 &&
                            (IsNativeStaffBoundary(people, earlier + 8, end, total) || IsNativeStaffBoundary(people, earlier + 10, end, total))) { earlierEnd = true; break; }
                        earlier = FindNativeBytes(people, BitConverter.GetBytes(index), earlier + 1, footer - earlier - 1);
                    }
                    if (names && ratings && !earlierEnd)
                    {
                        for (int yearAt = start + 45; yearAt <= Math.Min(start + 550, footer - 100); yearAt++)
                        {
                            int year = BitConverter.ToUInt16(people, yearAt), day = BitConverter.ToUInt16(people, yearAt - 2);
                            if (year < 1850 || year > 2007 || day >= (DateTime.IsLeapYear(year) ? 366 : 365)) continue;
                            int clubAt = yearAt + 26;
                            int club = BitConverter.ToInt32(people, clubAt);
                            if (!clubs.ContainsKey(club) || BitConverter.ToUInt16(people, clubAt - 2) != 1900 || people[clubAt + 27] != 1) continue;
                            int length = GetNativeContractLength(people, clubAt + 28, footer, index);
                            int contract = length > 0 ? GetNativeClubContractOffset(people, clubAt + 28, footer, index) : -1;
                            if (contract < 0 || length < 65) continue;
                            int wage = BitConverter.ToInt32(people, contract + 35);
                            int expYear = BitConverter.ToUInt16(people, contract + 41), expDay = BitConverter.ToUInt16(people, contract + 39);
                            if (wage < 0 || expYear < 1900 || expYear > 9999 || expDay >= (DateTime.IsLeapYear(expYear) ? 366 : 365)) continue;
                            found.Add(new NativeStaffRecord {
                                Id = uid, PersonIndex = index, PersonOffset = start, RecordLength = footer + 8 - start,
                                PersonTypeRaw = 1, FirstName = fn, LastName = sn, BirthDate = new DateTime(year, 1, 1).AddDays(day),
                                ClubIndex = club, Club = clubs[club], ClubRoleRaw = people[clubAt + 4],
                                WageOffset = contract + 35, WeeklyWage = wage,
                                ContractExpires = expYear == 1900 && expDay == 0 ? (DateTime?)null : new DateTime(expYear, 1, 1).AddDays(expDay)
                            });
                        }
                    }
                    int next = start + 1;
                    start = next < footer ? FindNativeBytes(people, prefix, next, footer - next) : -1;
                }
            }
            int nextIdentity = identityAt + 1;
            identityAt = nextIdentity < end ? FindNativeBytes(people, identity, nextIdentity, end - nextIdentity) : -1;
        }
        if (found.Count != 1) throw new InvalidDataException(found.Count == 0 ?
            "Unsupported or missing contracted non-player UID " + uid + ". Combined player/staff and free staff are not supported yet." :
            "Ambiguous staff record for UID " + uid);
        return found[0];
    }

    public static byte[] ApplyNativeStaffWages(byte[] people, byte[] server, IEnumerable<NativeStaffWageChange> changes)
    {
        if (changes == null) throw new ArgumentNullException("changes");
        var plan = changes.ToList(); var ids = new HashSet<int>();
        var edits = new List<KeyValuePair<NativeStaffRecord, NativeStaffWageChange>>();
        foreach (var change in plan)
        {
            if (change == null || !ids.Add(change.Id) || change.WeeklyWage < 0) throw new InvalidDataException("Duplicate, missing or negative staff wage change.");
            var record = ReadNativeStaff(people, server, change.Id);
            if (record.ClubIndex != change.ExpectedClubIndex || record.WeeklyWage != change.ExpectedWeeklyWage)
                throw new InvalidDataException("Staff club/wage precondition failed for UID " + change.Id);
            edits.Add(new KeyValuePair<NativeStaffRecord, NativeStaffWageChange>(record, change));
        }
        if (edits.Count == 0) return people;
        byte[] result = (byte[])people.Clone();
        foreach (var edit in edits) BitConverter.GetBytes(edit.Value.WeeklyWage).CopyTo(result, edit.Key.WageOffset);
        return result;
    }

    public static List<NativeStaffWageChange> ReadNativeStaffWageCsv(string path)
    {
        string[] lines = File.ReadAllLines(path, System.Text.Encoding.UTF8);
        string[] required = { "ID", "ExpectedClubIndex", "ExpectedWeeklyWage", "WeeklyWage" };
        if (lines.Length == 0 || !ParseCsvLine(lines[0].TrimStart('\uFEFF')).SequenceEqual(required))
            throw new InvalidDataException("Expected CSV header: " + string.Join(",", required));
        var result = new List<NativeStaffWageChange>();
        for (int n = 1; n < lines.Length; n++)
        {
            if (string.IsNullOrWhiteSpace(lines[n])) continue;
            string[] fields = ParseCsvLine(lines[n]); int[] values = new int[4];
            if (fields.Length != 4) throw new InvalidDataException("Invalid staff CSV row " + (n + 1));
            for (int c = 0; c < 4; c++) if (!int.TryParse(fields[c], NumberStyles.Integer, CultureInfo.InvariantCulture, out values[c]))
                throw new InvalidDataException("Invalid staff CSV integer on row " + (n + 1));
            result.Add(new NativeStaffWageChange { Id = values[0], ExpectedClubIndex = values[1], ExpectedWeeklyWage = values[2], WeeklyWage = values[3] });
        }
        if (result.Count == 0) throw new InvalidDataException("Staff CSV contains no changes.");
        return result;
    }

    private void OpenNativeStaffEditor()
    {
        if (loadedPeopleDbRaw == null || loadedServerDbRaw == null) { MessageBox.Show("Najpierw wczytaj bazę."); return; }
        using (var dialog = new Form { Text = "Sztab — pensja pracownika", Size = new Size(600, 270), StartPosition = FormStartPosition.CenterParent, MinimizeBox = false, MaximizeBox = false })
        {
            var uid = new TextBox { Left = 100, Top = 15, Width = 150 };
            var read = new Button { Text = "Odczytaj", Left = 265, Top = 13, Width = 100 };
            var info = new Label { Left = 15, Top = 55, Width = 550, Height = 70 };
            var wage = new NumericUpDown { Left = 160, Top = 130, Width = 160, Maximum = int.MaxValue, Enabled = false };
            var apply = new Button { Text = "Zastosuj", Left = 335, Top = 128, Width = 100, Enabled = false };
            NativeStaffRecord selected = null;
            read.Click += (s, e) => { try {
                selected = null; apply.Enabled = wage.Enabled = false; int id;
                if (!int.TryParse(uid.Text, out id)) throw new InvalidDataException("Podaj UID pracownika.");
                selected = ReadNativeStaff(loadedPeopleDbRaw, loadedServerDbRaw, id);
                info.Text = selected.FirstName + " " + selected.LastName + "\n" + selected.Club + "\nUmowa do: " + (selected.ContractExpires.HasValue ? selected.ContractExpires.Value.ToString("dd.MM.yyyy") : "brak daty");
                wage.Value = selected.WeeklyWage; wage.Enabled = apply.Enabled = true;
            } catch (Exception ex) { info.Text = ex.Message; } };
            apply.Click += (s, e) => { try {
                loadedPeopleDbRaw = ApplyNativeStaffWages(loadedPeopleDbRaw, loadedServerDbRaw, new[] { new NativeStaffWageChange {
                    Id = selected.Id, ExpectedClubIndex = selected.ClubIndex, ExpectedWeeklyWage = selected.WeeklyWage, WeeklyWage = (int)wage.Value } });
                hasUnsavedChanges = true; btnSaveDb.Enabled = true; selected.WeeklyWage = (int)wage.Value;
                lblStatus.Text = "Zmieniono pensję pracownika. Użyj Zapisz bazę, aby zapisać wynik.";
            } catch (Exception ex) { MessageBox.Show(ex.Message); } };
            var import = new Button { Text = "Import pensji CSV...", Left = 15, Top = 175, Width = 180 };
            import.Click += (s, e) => { using (var file = new OpenFileDialog { Filter = "CSV|*.csv" }) { if (file.ShowDialog(dialog) != DialogResult.OK) return; try {
                var changes = ReadNativeStaffWageCsv(file.FileName);
                loadedPeopleDbRaw = ApplyNativeStaffWages(loadedPeopleDbRaw, loadedServerDbRaw, changes);
                hasUnsavedChanges = true; btnSaveDb.Enabled = true; selected = null; apply.Enabled = wage.Enabled = false;
                info.Text = "Zastosowano zmiany pensji: " + changes.Count + ". Zapisz bazę w nowym folderze.";
            } catch (Exception ex) { MessageBox.Show(ex.Message); } } };
            dialog.Controls.AddRange(new Control[] { new Label { Text = "UID osoby", Left = 15, Top = 18 }, uid, read, info,
                new Label { Text = "Pensja tygodniowa", Left = 15, Top = 133, Width = 140 }, wage, apply, import });
            dialog.ShowDialog(this);
        }
    }
}
