"""Record the controlled Buffon loan buy-fee experiment without database writes."""
import argparse,json,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
from research_buffon_loan_wages_20261106 import ROOT,REPO,read,sha,hashes,save
R=ROOT/'FmLauncher/data/research/LOANS_20261106_BUFFON_FEE'
BUILD=REPO/'out/loans-20261106-fee-r1'

def prepare():
    p=REPO/'scratch/compare_buffon_loan_variant_20261106.py';text=p.read_text(encoding='utf-8-sig')
    old="'wages':dict(folder='TEST_LOAN_WAGES',offset=23,before=50,after=75)}"
    assert old in text
    text=text.replace(old,"'wages':dict(folder='TEST_LOAN_WAGES',offset=23,before=50,after=75), 'fee':dict(folder='TEST_LOAN_FEE',offset=19,width=4,before=5000000,after=7000000)}")
    old="    require(changes==[dict(offset=case['offset'],before=case['before'],after=case['after'])],'more than the controlled loan field changed')\n    expected=bytearray(struct.pack('<i',6211)+b''.join(rows[1]));expected[4+6210*32+case['offset']]=case['after']"
    assert old in text
    new="""    width=case.get('width',1);offset=case['offset'];fmt='<i' if width==4 else '<B'
    old_field=struct.pack(fmt,case['before']);new_field=struct.pack(fmt,case['after'])
    require(a[offset:offset+width]==old_field and b[offset:offset+width]==new_field,'controlled field values differ')
    expected_changes=[dict(offset=offset+i,before=x,after=y) for i,(x,y) in enumerate(zip(old_field,new_field)) if x!=y]
    require(changes==expected_changes,'more than the controlled loan field changed')
    expected=bytearray(struct.pack('<i',6211)+b''.join(rows[1]));start=4+6210*32+offset;expected[start:start+width]=new_field"""
    text=text.replace(old,new).replace('complete loan table differs from single-byte edit','complete loan table differs from controlled field edit').replace('whole_table_matches_single_byte_edit=True','whole_table_matches_single_byte_edit=(len(changes)==1),whole_table_matches_controlled_field_edit=True,controlled_field_width=width')
    p.write_text(text,encoding='utf-8')
    p=REPO/'tests/TestNativeLoans.cs';text=p.read_text(encoding='utf-8-sig')
    assert 'a.Length<=6' in text and 'if(a.Length==6){' in text
    text=text.replace('a.Length<=6','a.Length<=7').replace('report-json [TEST_LOAN_RECALL [TEST_LOAN_NUMBER [TEST_LOAN_WAGES]]]','report-json [TEST_LOAN_RECALL [TEST_LOAN_NUMBER [TEST_LOAN_WAGES [TEST_LOAN_FEE]]]]').replace('if(a.Length==6){','if(a.Length>=6){')
    marker='  File.WriteAllText(a[2],';assert marker in text
    extra='''  if(a.Length==7){
   string feeFixture=Path.GetFullPath(a[6]);var feePins=Hashes(feeFixture);byte[] feePeople=Load(feeFixture,"people_db.dat"),feeServer=Load(feeFixture,"server_db.dat");
   var feeLoans=FM08_Database_Editor.ParseNativeLoans(feeServer,BitConverter.ToInt32(feePeople,0));var subject=feeLoans.Single(r=>r.PersonIndex==3474);
   Check("SI buy fee changes from 5000000 to 7000000",()=>Require(buffon.FeeToBuyRaw==5000000&&subject.FeeToBuyRaw==7000000,"buy fee interpretation"));
   int feeHeader=Table(feeServer,count);byte[] expected=edited.Skip(after).Take(4+6211*32).ToArray();BitConverter.GetBytes(7000000).CopyTo(expected,4+6210*32+19);
   Check("complete SI fee table equals exactly one int32 edit",()=>Require(expected.SequenceEqual(feeServer.Skip(feeHeader).Take(expected.Length)),"additional loan edits"));
   Check("fee variant retains club, dates, wages, options, number and UID",()=>Require(subject.ClubId==buffon.ClubId&&subject.StartDate==buffon.StartDate&&subject.EndDate==buffon.EndDate&&subject.WageContributionRaw==buffon.WageContributionRaw&&subject.OptionsRaw==buffon.OptionsRaw&&subject.SquadNumberRaw==buffon.SquadNumberRaw&&subject.RecordIndex==buffon.RecordIndex&&subject.UniqueId==buffon.UniqueId,"other terms differ"));
   Check("fee fixture remains byte-identical",()=>Require(feePins.OrderBy(x=>x.Key).SequenceEqual(Hashes(feeFixture).OrderBy(x=>x.Key)),"fee input changed"));
  }
'''
    text=text.replace(marker,extra+marker);p.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8'))
    print('Prepared width-aware comparator and four real SI fee checks; no database writes.')

def document():
    r=read(R/'report.json');assert r['status']=='controlled_loan_fee_verified'
    assert r['loan_before']['raw_fee_to_buy']==5000000 and r['loan_after']['raw_fee_to_buy']==7000000
    assert r['main_contract_wages_native']==[79575]*3 and r['inputs_unchanged']
    p=REPO/'docs/NATIVE_LOANS.md';text=p.read_text(encoding='utf-8-sig')
    text=text.replace('| +19 | int32 | 5000000 | Odpowiada kwocie Fee To Buy ze zrzutu; potrzebny wariant jednej zmiany |','| +19 | int32 | 5000000 | Kwota Fee To Buy, little-endian; TEST_LOAN_FEE potwierdza 5000000 → 7000000 |')
    text=text.replace('[37 kontroli z wariantami odwołania, numeru i udziału płac]','[41 kontroli z wariantami odwołania, numeru, udziału płac i wykupu]')
    old='Następna próba: **TEST_LOAN_FEE**, ponownie od czystej8.0.2. Warunki jak\nw TEST_LOAN: odwołanie wyłączone, numer niewskazany, pensja50%, daty bez zmian.\nOpcja Fee To Buy nadal włączona; zmienić tylko kwotę **5000000 → 7000000**.'
    assert old in text
    text=text.replace(old,'**TEST_LOAN_FEE — wykonane:** pole int32 od +19 zmienia 5000000 → 7000000.')
    text+='''

## Wariant TEST_LOAN_FEE — wynik 2026-11-06

Pole `int32 little-endian` na **+19..+22** zawiera kwotę Fee To Buy.
Zmiana 5000000 → 7000000 zmienia trzy bajty: +19 `40 → C0`, +20 `4B → CF`,
+21 `4C → 6A`; +22 pozostaje `00`. Jest to jedno pole czterobajtowe.
Cała tabela SI jest identyczna z odtworzoną w pamięci tabelą TEST_LOAN po
zastąpieniu wyłącznie tego int32. Nie zmieniają się flagi opcji na +17.

Wszystkie 6210 dawnych wpisów i całe rekordy Juventusu oraz Interu są identyczne.
Właściciel Buffona, jego główna umowa, numer 1 i płaca natywna 79575 pozostają
niezmienione. Odczyt imienia w słowniku potwierdza tę samą tożsamość nazwy.
Daty, udział płac 50%, niewskazany numer 255, brak odwołania, indeks i UID
wypożyczenia pozostają identyczne z TEST_LOAN.

Dowody: `FmLauncher/data/research/LOANS_20261106_BUFFON_FEE/report.json`.
Wspólny czytnik `FeeToBuyRaw` odczytuje 7000000. Nie dodano zapisu nowych
wypożyczeń. Wejściowe bazy są nietknięte; zachowanie gry pozostaje niesprawdzone.
Kwota dla wyłączonej opcji wykupu nie ma jeszcze potwierdzonej interpretacji.

Następna próba: **TEST_LOAN_FEE_OFF**, od czystej 8.0.2, odtworzyć TEST_LOAN
z kwotą 5000000 i następnie wyłączyć wyłącznie checkbox Fee To Buy.
Pozostałe warunki jak TEST_LOAN: pensja 50%, brak odwołania i numeru, te same daty.
Nie zakładamy z góry, że brak wykupu zapisuje się jako zero lub -1.
'''
    p.write_text(text,encoding='utf-8')
    p=REPO/'fm08_compendium.md';text=p.read_text(encoding='utf-8-sig');text+='''

#### Kwota wykupu — TEST_LOAN_FEE

Próbka SI potwierdza kwotę Fee To Buy jako int32 little-endian od +19 rekordu
LOAN: 5000000 → 7000000. Zmieniają się trzy bajty tego jednego pola; opcje +17,
pozostałe warunki, stare wypożyczenia, główna umowa Buffona i kadry są identyczne.
Wartość przy wyłączonej opcji wykupu wymaga osobnej próby TEST_LOAN_FEE_OFF.
Szczegóły: [NATIVE_LOANS.md](docs/NATIVE_LOANS.md).
''';p.write_text(text,encoding='utf-8')
    print('Documented confirmed fee field and separate pending disabled-option experiment.')

def finalize():
    r=read(R/'report.json');t=read(R/'native-tests.json');m=read(BUILD/'build-manifest.json')
    assert t['status']=='pass' and t['checks']==41
    for path,key in [('baseline','baseline_hashes'),('reference','reference_hashes'),('fixture','fixture_hashes')]:assert hashes(Path(r[path]))==r[key]
    for e in m['Sources']:assert sha(REPO/e['Path'])==e['SHA256']
    for e in m['Outputs']:assert sha(BUILD/e['Path'])==e['SHA256']
    archive=R/'source-snapshot';archive.mkdir(exist_ok=False)
    files={e['Path'] for e in m['Sources']};files.update(['build.ps1','scratch/analyze_buffon_loan_20261106.py','scratch/compare_native_player_tests.py','scratch/compare_buffon_loan_variant_20261106.py','scratch/research_buffon_loan_fee_20261106.py','scratch/research_buffon_loan_wages_20261106.py','docs/NATIVE_LOANS.md','fm08_compendium.md'])
    entries=[]
    for rel in sorted(files):
        dest=archive/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(REPO/rel,dest);entries.append(dict(path=rel,SHA256=sha(dest)))
    shutil.copy2(BUILD/'build-manifest.json',R/'build-manifest.json');save(archive/'manifest.json',dict(source_only=True,files=entries,build_manifest_sha256=sha(BUILD/'build-manifest.json')))
    result=dict(status=r['status'],record_offset=19,field_type='int32_little_endian',before=5000000,after=7000000,reader_checks_passed=41,prior_loans_preserved=6210,input_databases_unchanged=True,build=str(BUILD),source_files_archived=len(entries),game_behavior='not_tested',native_generated_fixture_SI_acceptance='not_tested',proposed_next_case=dict(name='TEST_LOAN_FEE_OFF',baseline=r['baseline'],reference='TEST_LOAN',single_change='Disable Fee To Buy checkbox, previously 5000000; wages 50 percent; recall disabled; shirt unspecified'))
    save(R/'result.json',result)
    policy_path=R.parent/'LOAN_RESEARCH_POLICY.json';policy=read(policy_path);policy.update(latest_case=str(R),confirmed_fee_to_buy_record_offset=19,confirmed_fee_to_buy_type='int32_little_endian',fee_to_buy_disabled_meaning='not_confirmed');save(policy_path,policy)
    print(json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','document','finalize']);a=p.parse_args();{'prepare':prepare,'document':document,'finalize':finalize}[a.stage]()
