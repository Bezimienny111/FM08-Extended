from pathlib import Path
r=Path('FM08-Database-Tools')
p=r/'NativeStaff.cs';t=p.read_text(encoding='utf-8-sig')
marker='    // Existing contracted non-player PERSONs only.'
extra='''    private static bool IsNativeStaffBoundary(byte[] people, int at, int end, int total)
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

'''
assert marker in t;t=t.replace(marker,extra+marker,1)
t=t.replace('if (index >= 0 && index < total)','if (index >= 0 && index < total && (IsNativeStaffBoundary(people, identityAt + 4, end, total) || IsNativeStaffBoundary(people, identityAt + 6, end, total)))',1)
old='                    if (names && ratings)\n                    {'
new='''                    // A matching UID inside a later person's payload cannot extend this PERSON.
                    int earlier = FindNativeBytes(people, BitConverter.GetBytes(index), start + 120, footer - start - 120);
                    bool earlierEnd = false;
                    while (earlier >= 0 && earlier < footer) {
                        if (BitConverter.ToInt32(people, earlier + 4) > 0 &&
                            (IsNativeStaffBoundary(people, earlier + 8, end, total) || IsNativeStaffBoundary(people, earlier + 10, end, total))) { earlierEnd = true; break; }
                        earlier = FindNativeBytes(people, BitConverter.GetBytes(index), earlier + 1, footer - earlier - 1);
                    }
                    if (names && ratings && !earlierEnd)
                    {'''
assert old in t;t=t.replace(old,new,1);p.write_text(t.rstrip()+'\n',encoding='utf-8')
p=r/'tests/TestNativeStaff.cs';t=p.read_text(encoding='utf-8-sig')
t=t.replace('"Missing staff UID rejected"','"UID-like bytes inside a later payload rejected"')
marker='        var broken = (byte[])p.Clone();';assert marker in t
t=t.replace(marker,'        Reject(() => Staff.ReadNativeStaff(p, s, 1900000999), "Missing staff UID rejected");\n'+marker,1)
p.write_text(t.rstrip()+'\n',encoding='utf-8')
p=r/'build.ps1';p.write_text(p.read_text(encoding='utf-8-sig').rstrip()+'\n',encoding='utf-8')
p=r/'scratch/build_assignment_r6.ps1';t=p.read_text(encoding='utf-8-sig');old=r'@("$root\FM08_Database_Editor.cs","$root\build.ps1"';new=r'@("$root\FM08_Database_Editor.cs","$root\NativeStaff.cs","$root\build.ps1"';assert old in t;t=t.replace(old,new,1);p.write_text(t,encoding='utf-8')
p=r/'README.md';t=p.read_text(encoding='utf-8-sig');t+='\n## Sztab\n\n[Obsługa sztabu i CSV pensji](docs/NATIVE_STAFF.md): odczyt istniejącego pracownika\npo UID, pensje w GUI i importerze, zakres potwierdzony próbką SI Ranieriego.\nEdytor kompilujemy z `FM08_Database_Editor.cs` i `NativeStaff.cs` przez `build.ps1`.\n';p.write_text(t,encoding='utf-8')
p=r/'IMPORTER_AKTUALNY_SCHEMAT_I_ZASADY.md';t=p.read_text(encoding='utf-8-sig');t+='''

## 18. Sztab — pierwszy zakres 2026-11-06

[Moduł sztabu](NativeStaff.cs), [narzędzie CLI](scratch/NativeStaffTool.cs)
i [dokładny zakres](docs/NATIVE_STAFF.md) dodają odczyt istniejącego pracownika
po UID oraz zmianę jego pensji. Jest osobny model sztabu i CSV z warunkami
wstępnymi; nie zamieniamy pracownika w PlayerRecord ani nie edytujemy tabeli89.
GUI ma przycisk Sztab. CLI wykonuje eksport, walidację w pamięci lub zapis do
nowej kopii. Potwierdzona próbka SI: TEST_STAFF_WAGE, Claudio Ranieri,
UID4201569, pensja0→12345. Tworzenie osób, zmiana ról i transfery sztabu
oraz wariant zawodnik/pracownik nie są jeszcze zaimplementowane.
Nie zmieniono zakresu modernizacji V25; żadnego współczesnego sztabu do niej
nie zaimportowano. Oryginalna8.0.2 pozostaje bazą odniesienia badań.
''';p.write_text(t,encoding='utf-8')
p=r/'CSV_SCHEMA.md';t=p.read_text(encoding='utf-8-sig');t+='''

## Sztab: osobny CSV pensji

To osobny tryb `NativeStaffTool`, nie CSV zawodników GUI.
Nagłówek: `ID,ExpectedClubIndex,ExpectedWeeklyWage,WeeklyWage`.
Znaczenie, ograniczenia i polecenia: [NATIVE_STAFF.md](docs/NATIVE_STAFF.md).
''';p.write_text(t,encoding='utf-8')
p=r/'fm08_compendium.md';t=p.read_text(encoding='utf-8-sig');t+='''

### Sztab — próbka Ranieriego i pensja, 2026-11-06

TEST_STAFF_WAGE względem czystej8.0.2 potwierdza pensję0→12345 bez przeliczenia.
Ranieri: UID4201569, PERSON index129460, typ1, rekord272B. W tej konkretnej
próbce klub995 leży na+75, kontrakt zaczyna się+103, a pensja na+138
(kontrakt+35). Są to offsety próbki, nie stałe dla wszystkich pracowników.
Imię i nazwisko zachowują UID nazw mimo przesunięcia indeksów po zapisie SI.
Natywny zapis zmienia wyłącznie int32 pensji. Role i inne pola pozostają surowe
lub chronione; GUI ról zawodników nie jest implementacją sztabu.
Szczegóły: [NATIVE_STAFF.md](docs/NATIVE_STAFF.md).
''';p.write_text(t,encoding='utf-8')
print('Strengthened PERSON identity boundaries and documented staff scope.')

