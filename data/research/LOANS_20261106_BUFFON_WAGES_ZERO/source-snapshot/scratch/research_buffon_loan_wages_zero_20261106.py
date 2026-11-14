"""Verify the controlled zero-percent loan-wage fixture; never write databases."""
import argparse,json,shutil,sys
sys.dont_write_bytecode=True
from research_buffon_loan_wages_20261106 import ROOT,REPO,read,sha,hashes,save
R=ROOT/'FmLauncher/data/research/LOANS_20261106_BUFFON_WAGES_ZERO'
BUILD=REPO/'out/loans-20261106-wages-zero-r1'

def prepare():
    p=REPO/'scratch/compare_buffon_loan_variant_20261106.py';text=p.read_text(encoding='utf-8-sig')
    old="'fee_off':dict(folder='TEST_LOAN_FEE_OFF',offset=19,width=4,before=5000000,after=-1)}"
    assert old in text
    text=text.replace(old,"'fee_off':dict(folder='TEST_LOAN_FEE_OFF',offset=19,width=4,before=5000000,after=-1), 'wages_zero':dict(folder='TEST_LOAN_WAGES_ZERO',offset=23,before=50,after=0)}")
    p.write_text(text,encoding='utf-8')
    p=REPO/'tests/TestNativeLoans.cs';text=p.read_text(encoding='utf-8-sig')
    assert 'a.Length<=8' in text and 'if(a.Length==8){' in text
    start=text.index('  if(a.Length>=6){');end=text.index('  if(a.Length>=7){',start);block=text[start:end];assert block.count('Check(')==4
    extra=block.replace('if(a.Length>=6){','if(a.Length==9){').replace('a[5]','a[8]')
    for name in ['Fixture','Pins','People','Server','Loans','Header']:extra=extra.replace('wage'+name,'zeroWage'+name)
    extra=extra.replace('75','0').replace('SI wage contribution','SI zero-wage contribution').replace('SI wage table','SI zero-wage table').replace('wage variant retains','zero-wage variant retains').replace('wage fixture remains','zero-wage fixture remains').replace('wage input changed','zero-wage input changed')
    marker='  File.WriteAllText(a[2],';assert marker in text
    text=text.replace('a.Length<=8','a.Length<=9').replace('[TEST_LOAN_FEE_OFF]]]]]','[TEST_LOAN_FEE_OFF [TEST_LOAN_WAGES_ZERO]]]]]]').replace('if(a.Length==8){','if(a.Length>=8){').replace(marker,extra+marker)
    p.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8'))
    print('Prepared one-byte comparison and four zero-percent SI checks.')

def document():
    r=read(R/'report.json');assert r['status']=='controlled_loan_wages_zero_verified'
    assert r['loan_after']['raw_wage_contribution_byte_23']==0
    assert r['main_contract_wages_native']==[79575]*3 and r['inputs_unchanged']
    p=REPO/'docs/NATIVE_LOANS.md';text=p.read_text(encoding='utf-8-sig')
    text=text.replace('| +23 | byte | 50 | Procent pensji pokrywany przez klub wypożyczający; wariant WAGES potwierdza 50 → 75 |','| +23 | byte | 50 | Procent pensji pokrywany przez klub wypożyczający; potwierdzone wartości 0, 50 i 75 |')
    text=text.replace('[45 kontroli z wariantami odwołania, numeru, udziału płac, kwoty i wyłączenia wykupu]','[49 kontroli z wariantami odwołania, numeru, udziału płac (także 0%), kwoty i wyłączenia wykupu]')
    text=text.replace('Zakresy0%/100% i zachowanie w grze pozostają osobnymi próbami.','Wartość 0% potwierdza TEST_LOAN_WAGES_ZERO poniżej; 100% i zachowanie w grze wymagają osobnych prób.')
    old='Następna przydatna próba: **TEST_LOAN_WAGES_ZERO**, od czystej 8.0.2 odtworzyć\nTEST_LOAN i zmienić tylko udział płac 50% → 0%. Wykup włączony 5000000,\nbrak odwołania i numeru, te same daty. Surowe 255 nadal ma nieustalone znaczenie.'
    assert old in text
    text=text.replace(old,'**TEST_LOAN_WAGES_ZERO — wykonane:** udział płac 0% zapisuje się jako bajt 0 na +23.')
    text+='''

## Wariant TEST_LOAN_WAGES_ZERO — wynik 2026-11-06

Zmiana udziału płac 50% → 0% zmienia wyłącznie bajt **+23: 50 → 0**.
Cała tabela SI jest identyczna z TEST_LOAN po zastąpieniu tylko tego bajtu.
Zero jest jawnym udziałem 0%; nie interpretujemy surowego 255 jako zera.

Wszystkie 6210 wcześniejszych wypożyczeń są identyczne. Daty, Inter jako klub
wypożyczenia, wykup 5000000, opcje 0, niewskazany numer 255, indeks 6210
oraz UID 1800000090 pozostają bez zmian. Główna umowa Buffona zachowuje
płacę natywną 79575 i numer 1; udział płac jest osobnym polem LOAN.
Całe rekordy Juventusu i Interu są identyczne. Indeks imienia sprawdzamy
przez odczyt słownika i UID tej samej nazwy.

Dowody: `FmLauncher/data/research/LOANS_20261106_BUFFON_WAGES_ZERO/report.json`.
Czytnik `WageContributionRaw` zachowuje potwierdzoną wartość 0.
Hashe bazy 8.0.2, TEST_LOAN i nowej próbki są niezmienione po analizie.
Nie wykonano prób zachowania w grze ani natywnego tworzenia wypożyczeń.

Następna próba: **TEST_LOAN_WAGES_FULL**, od czystej 8.0.2 odtworzyć TEST_LOAN
ze zmianą wyłącznie udziału płac 50% → 100%. Wykup włączony 5000000,
bez odwołania i numeru, te same daty. Znaczenie 255 pozostaje niepotwierdzone.
'''
    p.write_text(text,encoding='utf-8')
    p=REPO/'fm08_compendium.md';text=p.read_text(encoding='utf-8-sig');text+='''

#### Zerowy udział w pensji — TEST_LOAN_WAGES_ZERO

Próbka SI potwierdza zapis 0% jako 0 na +23 rekordu LOAN (50 → 0).
To jedyna zmiana tabeli względem TEST_LOAN; główna płaca Buffona pozostaje
79575. Stare wypożyczenia i całe rekordy klubów są identyczne.
Nie utożsamiamy surowego 255 z potwierdzonym zerem.
Szczegóły: [NATIVE_LOANS.md](docs/NATIVE_LOANS.md).
''';p.write_text(text,encoding='utf-8')
    print('Documented explicit zero-percent value and preserved main-contract wage.')

def finalize():
    from pathlib import Path
    r=read(R/'report.json');t=read(R/'native-tests.json');m=read(BUILD/'build-manifest.json')
    assert t['status']=='pass' and t['checks']==49
    for path,key in [('baseline','baseline_hashes'),('reference','reference_hashes'),('fixture','fixture_hashes')]:assert hashes(Path(r[path]))==r[key]
    for e in m['Sources']:assert sha(REPO/e['Path'])==e['SHA256']
    for e in m['Outputs']:assert sha(BUILD/e['Path'])==e['SHA256']
    archive=R/'source-snapshot';archive.mkdir(exist_ok=False)
    files={e['Path'] for e in m['Sources']};files.update(['build.ps1','scratch/analyze_buffon_loan_20261106.py','scratch/compare_native_player_tests.py','scratch/compare_buffon_loan_variant_20261106.py','scratch/research_buffon_loan_wages_zero_20261106.py','scratch/research_buffon_loan_wages_20261106.py','docs/NATIVE_LOANS.md','fm08_compendium.md'])
    entries=[]
    for rel in sorted(files):
        dest=archive/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(REPO/rel,dest);entries.append(dict(path=rel,SHA256=sha(dest)))
    shutil.copy2(BUILD/'build-manifest.json',R/'build-manifest.json');save(archive/'manifest.json',dict(source_only=True,files=entries,build_manifest_sha256=sha(BUILD/'build-manifest.json')))
    result=dict(status=r['status'],record_offset=23,before_percent=50,after_percent=0,main_contract_wage_native=79575,reader_checks_passed=49,prior_loans_preserved=6210,input_databases_unchanged=True,build=str(BUILD),source_files_archived=len(entries),game_behavior='not_tested',native_generated_fixture_SI_acceptance='not_tested',proposed_next_case=dict(name='TEST_LOAN_WAGES_FULL',baseline=r['baseline'],reference='TEST_LOAN',single_change='Wage contribution 50 to 100 percent; buy fee enabled at 5000000; recall disabled; shirt unspecified'))
    save(R/'result.json',result)
    policy_path=R.parent/'LOAN_RESEARCH_POLICY.json';policy=read(policy_path);policy.update(latest_case=str(R),confirmed_wage_percentage_values=[0,50,75]);save(policy_path,policy)
    print(json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','document','finalize']);a=p.parse_args();{'prepare':prepare,'document':document,'finalize':finalize}[a.stage]()
