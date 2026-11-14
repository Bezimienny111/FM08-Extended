"""Prepare and archive the confirmed loan shirt-number reader and fixtures."""
import argparse,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REPO=ROOT/'FM08-Database-Tools'
R=ROOT/'FmLauncher/data/research/LOANS_20261106_BUFFON_NUMBER';BUILD=REPO/'out/loans-20261106-number-r1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def hashes(p):return {str(f.relative_to(p)):sha(f) for f in p.rglob('*') if f.is_file()}
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def cswrite(p,text):p.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8'))
def prepare():
    r=read(R/'report.json');assert r['status']=='controlled_loan_number_verified'
    p=REPO/'FM08_Database_Editor.cs';text=p.read_text(encoding='utf-8-sig');old='\t\tpublic byte SquadNumberRaw;'
    assert text.count(old)==1 and 'public int? SquadNumber {' not in text
    text=text.replace(old,old+'\n\t\tpublic int? SquadNumber { get { return SquadNumberRaw == 255 ? (int?)null : SquadNumberRaw; } }');cswrite(p,text)
    p=REPO/'tests/TestNativeLoans.cs';text=p.read_text(encoding='utf-8-sig')
    text=text.replace('a.Length==3||a.Length==4','a.Length>=3&&a.Length<=5').replace('report-json [TEST_LOAN_RECALL]','report-json [TEST_LOAN_RECALL [TEST_LOAN_NUMBER]]').replace('if(a.Length==4){','if(a.Length>=4){')
    marker='  File.WriteAllText(a[2],';assert marker in text
    extra='''  if(a.Length==5){
   string numberFixture=Path.GetFullPath(a[4]);var numberPins=Hashes(numberFixture);byte[] numberPeople=Load(numberFixture,"people_db.dat"),numberServer=Load(numberFixture,"server_db.dat");
   var numberLoans=FM08_Database_Editor.ParseNativeLoans(numberServer,BitConverter.ToInt32(numberPeople,0));var subject=numberLoans.Single(r=>r.PersonIndex==3474);
   Check("SI loan shirt changes from unspecified to 31",()=>Require(!buffon.SquadNumber.HasValue&&subject.SquadNumber==31&&buffon.SquadNumberRaw==255&&subject.SquadNumberRaw==31,"shirt-number interpretation"));
   Check("only sentinel 255 is interpreted as unspecified",()=>{var r=new FM08_Database_Editor.NativeLoanRecord{SquadNumberRaw=0};Require(r.SquadNumber==0&&r.SquadNumberRaw==0,"zero raw value collapsed");r.SquadNumberRaw=99;Require(r.SquadNumber==99,"numeric value lost");r.SquadNumberRaw=255;Require(!r.SquadNumber.HasValue,"unset sentinel lost");});
   int numberHeader=Table(numberServer,count);byte[] expected=edited.Skip(after).Take(4+6211*32).ToArray();expected[4+6210*32+18]=31;
   Check("complete SI number table equals exactly one byte edit",()=>Require(expected.SequenceEqual(numberServer.Skip(numberHeader).Take(expected.Length)),"additional loan edits"));
   Check("number variant retains recall, dates, fee, wages and loan UID",()=>Require(subject.OptionsRaw==buffon.OptionsRaw&&!subject.CanBeRecalled&&subject.StartDate==buffon.StartDate&&subject.EndDate==buffon.EndDate&&subject.ClubId==buffon.ClubId&&subject.FeeToBuyRaw==buffon.FeeToBuyRaw&&subject.WageContributionRaw==buffon.WageContributionRaw&&subject.UniqueId==buffon.UniqueId,"other terms differ"));
   Check("number fixture remains byte-identical",()=>Require(numberPins.OrderBy(x=>x.Key).SequenceEqual(Hashes(numberFixture).OrderBy(x=>x.Key)),"number input changed"));
  }
'''
    text=text.replace(marker,extra+marker);cswrite(p,text)
    p=REPO/'docs/NATIVE_LOANS.md';text=p.read_text(encoding='utf-8-sig')
    text=text.replace('| +18 | byte | 255 | Koreluje z wyłączonym numerem; wymaga próby z numerem |','| +18 | byte | 255 | Numer wypożyczenia; 255 = niewskazany, TEST_LOAN_NUMBER potwierdza 31 |')
    text=text.replace('[28 kontroli z wariantem odwołania]','[33 kontrole z wariantami odwołania i numeru]')
    text=text.replace('**TEST_LOAN_NUMBER — następne:** włączyć tylko Squad Number i wpisać 31; Can Be Recalled wyłączone, pozostałe wartości jak w TEST_LOAN.','**TEST_LOAN_NUMBER — wykonane:** +18 zmienia 255 → 31, umowa główna zachowuje numer 1.')
    text+='''
## Wariant TEST_LOAN_NUMBER — wynik 2026-11-06

**Jedyna zmiana 32-bajtowego rekordu względem TEST_LOAN: +18, 255 → 31.**
Bit odwołania pozostaje wyłączony. UID, daty, klub, wykup i udział płac są identyczne.
Wszystkie 6210 wcześniejszych wypożyczeń i całe rekordy obu klubów są niezmienione.

Numer wypożyczenia jest osobnym polem od numeru umowy głównej. W oryginale,
TEST_LOAN i TEST_LOAN_NUMBER główna umowa Buffona nadal ma numer **1**,
podczas gdy wpis LOAN w ostatniej próbce wskazuje **31**. Główna umowa i cały
ogon PERSON są identyczne; zmienia się tylko indeks tej samej nazwy „Gianluigi”
48313 → 48314 (UID nazwy 3803673).

Model `NativeLoanRecord.SquadNumber` zwraca liczbę lub `null` dla surowego255.
`SquadNumberRaw` zachowuje oryginalny bajt. Innych surowych wartości nie składamy
w ten znacznik; nie jest to walidator dopuszczalnych numerów dla przyszłego writera.

Dowody: `FmLauncher/data/research/LOANS_20261106_BUFFON_NUMBER/report.json`;
skrypt: [compare_buffon_loan_variant_20261106.py](../scratch/compare_buffon_loan_variant_20261106.py).
Porównanie w pamięci odtwarza całą tabelę SI przez zmianę jednego bajtu.
Nie testowano jeszcze zachowania numerów wypożyczenia w nowej karierze.

Następna próba: **TEST_LOAN_WAGES**, ponownie od czystej 8.0.2. Ustawienia jak
w TEST_LOAN (bez odwołania i bez numeru), zmienić wyłącznie udział płac **50% → 75%**.
'''
    p.write_text(text,encoding='utf-8')
    p=REPO/'fm08_compendium.md';text=p.read_text(encoding='utf-8-sig');text+='''

#### Numer wypożyczenia — TEST_LOAN_NUMBER

Wariant SI zmienia tylko +18 rekordu LOAN: 255 → 31. Główna umowa Buffona nadal
ma numer1. Pozostałe warunki,6210 wcześniejszych wypożyczeń i całe kadry są identyczne.
Model LOAN udostępnia `SquadNumber` jako liczbę lub null dla255, zachowując surowy bajt.
Szczegóły: [NATIVE_LOANS.md](docs/NATIVE_LOANS.md).
''';p.write_text(text,encoding='utf-8')
def finalize():
    r=read(R/'report.json');t=read(R/'native-tests.json');m=read(BUILD/'build-manifest.json');assert t['status']=='pass' and t['checks']==33
    for path,key in [('baseline','baseline_hashes'),('reference','reference_hashes'),('fixture','fixture_hashes')]:assert hashes(Path(r[path]))==r[key]
    for e in m['Sources']:assert sha(REPO/e['Path'])==e['SHA256']
    for e in m['Outputs']:assert sha(BUILD/e['Path'])==e['SHA256']
    archive=R/'source-snapshot';archive.mkdir(exist_ok=False)
    files={e['Path'] for e in m['Sources']};files.update(['build.ps1','scratch/analyze_buffon_loan_20261106.py','scratch/compare_native_player_tests.py','scratch/compare_buffon_loan_variant_20261106.py','scratch/research_buffon_loan_number_20261106.py','docs/NATIVE_LOANS.md','fm08_compendium.md'])
    entries=[]
    for rel in sorted(files):
        dest=archive/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(REPO/rel,dest);entries.append(dict(path=rel,SHA256=sha(dest)))
    shutil.copy2(BUILD/'build-manifest.json',R/'build-manifest.json');save(archive/'manifest.json',dict(source_only=True,files=entries,build_manifest_sha256=sha(BUILD/'build-manifest.json')))
    result=dict(status='controlled_loan_number_verified',record_byte=18,unset_value=255,loan_number=31,main_contract_number=1,reader_checks_passed=33,prior_loans_preserved=6210,input_databases_unchanged=True,build=str(BUILD),source_files_archived=len(entries),game_behavior='not_tested',proposed_next_case=dict(name='TEST_LOAN_WAGES',baseline=r['baseline'],reference='TEST_LOAN',single_change='Wage contribution 50 to 75 percent; recall disabled, loan squad number unspecified; all other terms unchanged'))
    save(R/'result.json',result);policy_path=R.parent/'LOAN_RESEARCH_POLICY.json';policy=read(policy_path);policy.update(latest_case=str(R),confirmed_loan_number_record_offset=18,confirmed_loan_number_unset_value=255);save(policy_path,policy)
    print(json.dumps({k:result[k] for k in ['status','loan_number','main_contract_number','reader_checks_passed','input_databases_unchanged']}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','finalize']);a=p.parse_args();prepare() if a.stage=='prepare' else finalize()
