"""Record and test the controlled 50 to 75 percent Buffon loan-wage experiment."""
import argparse,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REPO=ROOT/'FM08-Database-Tools'
R=ROOT/'FmLauncher/data/research/LOANS_20261106_BUFFON_WAGES';BUILD=REPO/'out/loans-20261106-wages-r1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def hashes(p):return {str(f.relative_to(p)):sha(f) for f in p.rglob('*') if f.is_file()}
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def prepare_comparison():
    p=REPO/'scratch/compare_buffon_loan_variant_20261106.py';text=p.read_text(encoding='utf-8-sig');old="'number':dict(folder='TEST_LOAN_NUMBER',offset=18,before=255,after=31)}"
    assert old in text and "'wages':" not in text
    text=text.replace(old,"'number':dict(folder='TEST_LOAN_NUMBER',offset=18,before=255,after=31), 'wages':dict(folder='TEST_LOAN_WAGES',offset=23,before=50,after=75)}")
    text=text.replace('main_contract_shirt_numbers=main_numbers,clubs=clubs','main_contract_shirt_numbers=main_numbers,main_contract_wages_native=[integer(record,305) for record in records],clubs=clubs')
    p.write_text(text,encoding='utf-8')
def prepare_tests():
    r=read(R/'report.json');assert r['status']=='controlled_loan_wages_verified'
    assert r['main_contract_wages_native']==[79575,79575,79575]
    p=REPO/'tests/TestNativeLoans.cs';text=p.read_text(encoding='utf-8-sig')
    assert 'a.Length<=5' in text and 'if(a.Length==5){' in text
    text=text.replace('a.Length<=5','a.Length<=6').replace('report-json [TEST_LOAN_RECALL [TEST_LOAN_NUMBER]]','report-json [TEST_LOAN_RECALL [TEST_LOAN_NUMBER [TEST_LOAN_WAGES]]]').replace('if(a.Length==5){','if(a.Length>=5){')
    marker='  File.WriteAllText(a[2],';assert marker in text
    extra='''  if(a.Length==6){
   string wageFixture=Path.GetFullPath(a[5]);var wagePins=Hashes(wageFixture);byte[] wagePeople=Load(wageFixture,"people_db.dat"),wageServer=Load(wageFixture,"server_db.dat");
   var wageLoans=FM08_Database_Editor.ParseNativeLoans(wageServer,BitConverter.ToInt32(wagePeople,0));var subject=wageLoans.Single(r=>r.PersonIndex==3474);
   Check("SI wage contribution changes from 50 to 75 percent",()=>Require(buffon.WageContributionRaw==50&&subject.WageContributionRaw==75,"percentage interpretation"));
   int wageHeader=Table(wageServer,count);byte[] expected=edited.Skip(after).Take(4+6211*32).ToArray();expected[4+6210*32+23]=75;
   Check("complete SI wage table equals exactly one byte edit",()=>Require(expected.SequenceEqual(wageServer.Skip(wageHeader).Take(expected.Length)),"additional loan edits"));
   Check("wage variant retains club, dates, fee, options, number and UID",()=>Require(subject.ClubId==buffon.ClubId&&subject.StartDate==buffon.StartDate&&subject.EndDate==buffon.EndDate&&subject.FeeToBuyRaw==buffon.FeeToBuyRaw&&subject.OptionsRaw==buffon.OptionsRaw&&subject.SquadNumberRaw==buffon.SquadNumberRaw&&subject.RecordIndex==buffon.RecordIndex&&subject.UniqueId==buffon.UniqueId,"other terms differ"));
   Check("wage fixture remains byte-identical",()=>Require(wagePins.OrderBy(x=>x.Key).SequenceEqual(Hashes(wageFixture).OrderBy(x=>x.Key)),"wage input changed"));
  }
'''
    text=text.replace(marker,extra+marker);p.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8'))
    p=REPO/'docs/NATIVE_LOANS.md';text=p.read_text(encoding='utf-8-sig')
    text=text.replace('| +23 | byte | 50 | Odpowiada udziałowi płac 50%; potrzebny wariant jednej zmiany |','| +23 | byte | 50 | Procent pensji pokrywany przez klub wypożyczający; wariant WAGES potwierdza 50 → 75 |')
    text=text.replace('[33 kontrole z wariantami odwołania i numeru]','[37 kontroli z wariantami odwołania, numeru i udziału płac]')
    text=text.replace('Następna próba: **TEST_LOAN_WAGES**, ponownie od czystej 8.0.2. Ustawienia jak\nw TEST_LOAN (bez odwołania i bez numeru), zmienić wyłącznie udział płac **50% → 75%**.','**TEST_LOAN_WAGES — wykonane:** +23 zmienia 50 → 75; kwota głównej pensji jest niezmieniona.')
    text+='''
## Wariant TEST_LOAN_WAGES — wynik 2026-11-06

**Jedyna zmiana 32-bajtowego rekordu względem TEST_LOAN: +23, 50 → 75.**
To potwierdza procent wynagrodzenia pokrywany przez klub wypożyczający.
Kwota płacy w głównej umowie Buffona pozostaje identyczna (wartość natywna 79575).
Procent udziału jest osobnym polem relacji wypożyczenia, nie nową kwotą głównej umowy.

Daty, klub, wykup 5000000, numer niewskazany255, opcje0, indeks6210 i UID1800000090
są niezmienione. Wszystkie6210 wcześniejszych wypożyczeń i całe rekordy Juventusu
oraz Interu pozostają identyczne. W PERSON zmienia się tylko indeks tego samego
imienia „Gianluigi”:48313→48316, UID nazwy3803673. Główna umowa jest identyczna.

Istniejący odczyt `WageContributionRaw` zwraca potwierdzoną wartość75.
W oryginalnej8.0.2 występuje też surowe255: jego domyślnego znaczenia nie ustalono.
Nie zamieniamy go na0% ani100% i nie dodajemy takiego domyślnego ustawienia.
Zakresy0%/100% i zachowanie w grze pozostają osobnymi próbami.

Dowody: `FmLauncher/data/research/LOANS_20261106_BUFFON_WAGES/report.json`.
Cała tabela SI jest odtwarzana w pamięci przez zmianę jednego bajtu.
Bazy wejściowe nie były zmieniane.

Następna próba: **TEST_LOAN_FEE**, ponownie od czystej8.0.2. Warunki jak
w TEST_LOAN: odwołanie wyłączone, numer niewskazany, pensja50%, daty bez zmian.
Opcja Fee To Buy nadal włączona; zmienić tylko kwotę **5000000 → 7000000**.
'''
    p.write_text(text,encoding='utf-8')
    p=REPO/'fm08_compendium.md';text=p.read_text(encoding='utf-8-sig');text+='''

#### Udział w pensji — TEST_LOAN_WAGES

Wariant SI zmienia tylko +23 rekordu LOAN:50→75. Potwierdza to procent pensji
pokrywany przez klub wypożyczający; kwota głównej umowy Buffona pozostaje79575.
Wszystkie inne warunki,6210 dawnych wypożyczeń i kadry są identyczne.
Surowe255 nie ma jeszcze potwierdzonego znaczenia domyślnego.
Szczegóły: [NATIVE_LOANS.md](docs/NATIVE_LOANS.md).
''';p.write_text(text,encoding='utf-8')
def finalize():
    r=read(R/'report.json');t=read(R/'native-tests.json');m=read(BUILD/'build-manifest.json');assert t['status']=='pass' and t['checks']==37
    for path,key in [('baseline','baseline_hashes'),('reference','reference_hashes'),('fixture','fixture_hashes')]:assert hashes(Path(r[path]))==r[key]
    for e in m['Sources']:assert sha(REPO/e['Path'])==e['SHA256']
    for e in m['Outputs']:assert sha(BUILD/e['Path'])==e['SHA256']
    archive=R/'source-snapshot';archive.mkdir(exist_ok=False)
    files={e['Path'] for e in m['Sources']};files.update(['build.ps1','scratch/analyze_buffon_loan_20261106.py','scratch/compare_native_player_tests.py','scratch/compare_buffon_loan_variant_20261106.py','scratch/research_buffon_loan_wages_20261106.py','docs/NATIVE_LOANS.md','fm08_compendium.md'])
    entries=[]
    for rel in sorted(files):
        dest=archive/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(REPO/rel,dest);entries.append(dict(path=rel,SHA256=sha(dest)))
    shutil.copy2(BUILD/'build-manifest.json',R/'build-manifest.json');save(archive/'manifest.json',dict(source_only=True,files=entries,build_manifest_sha256=sha(BUILD/'build-manifest.json')))
    result=dict(status='controlled_loan_wages_verified',record_byte=23,before_percent=50,after_percent=75,main_contract_wage_native=79575,reader_checks_passed=37,prior_loans_preserved=6210,input_databases_unchanged=True,build=str(BUILD),source_files_archived=len(entries),game_behavior='not_tested',proposed_next_case=dict(name='TEST_LOAN_FEE',baseline=r['baseline'],reference='TEST_LOAN',single_change='Fee To Buy enabled, amount 5000000 to 7000000; wage contribution 50 percent; recall disabled; shirt unspecified'))
    save(R/'result.json',result);policy_path=R.parent/'LOAN_RESEARCH_POLICY.json';policy=read(policy_path);policy.update(latest_case=str(R),confirmed_wage_percentage_record_offset=23,wage_percentage_255_meaning='not_confirmed');save(policy_path,policy)
    print(json.dumps({k:result[k] for k in ['status','after_percent','main_contract_wage_native','reader_checks_passed','input_databases_unchanged']}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['comparison','tests','finalize']);a=p.parse_args();{'comparison':prepare_comparison,'tests':prepare_tests,'finalize':finalize}[a.stage]()
