"""Verify and archive the SI loan fixture with Fee To Buy disabled."""
import argparse,json,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
from research_buffon_loan_wages_20261106 import ROOT,REPO,read,sha,hashes,save
R=ROOT/'FmLauncher/data/research/LOANS_20261106_BUFFON_FEE_OFF'
BUILD=REPO/'out/loans-20261106-fee-off-r1'

def prepare():
    p=REPO/'scratch/compare_buffon_loan_variant_20261106.py';text=p.read_text(encoding='utf-8-sig')
    old="'fee':dict(folder='TEST_LOAN_FEE',offset=19,width=4,before=5000000,after=7000000)}"
    assert old in text
    text=text.replace(old,"'fee':dict(folder='TEST_LOAN_FEE',offset=19,width=4,before=5000000,after=7000000), 'fee_off':dict(folder='TEST_LOAN_FEE_OFF',offset=19,width=4,before=5000000,after=-1)}")
    p.write_text(text,encoding='utf-8')
    p=REPO/'tests/TestNativeLoans.cs';text=p.read_text(encoding='utf-8-sig')
    assert 'a.Length<=7' in text and 'if(a.Length==7){' in text
    marker='  File.WriteAllText(a[2],';start=text.index('  if(a.Length==7){');end=text.index(marker)
    block=text[start:end];assert block.count('Check(')==4
    extra=block.replace('if(a.Length==7){','if(a.Length==8){').replace('a[6]','a[7]')
    for name in ['Fixture','Pins','People','Server','Loans','Header']:extra=extra.replace('fee'+name,'feeOff'+name)
    extra=extra.replace('7000000','-1').replace('SI buy fee changes from 5000000 to -1','SI disabled buy fee decodes as signed -1').replace('complete SI fee table','complete SI disabled-fee table').replace('fee variant retains','disabled-fee variant retains').replace('fee fixture remains','disabled-fee fixture remains').replace('fee input changed','disabled-fee input changed')
    text=text.replace('a.Length<=7','a.Length<=8').replace('[TEST_LOAN_FEE]]]]','[TEST_LOAN_FEE [TEST_LOAN_FEE_OFF]]]]]').replace('if(a.Length==7){','if(a.Length>=7){').replace(marker,extra+marker)
    p.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8'))
    print('Prepared disabled-fee comparison and four real SI fixture checks.')

def document():
    r=read(R/'report.json');assert r['status']=='controlled_loan_fee_off_verified'
    assert r['loan_after']['raw_fee_to_buy']==-1 and r['loan_after']['raw_options_byte_17']==0
    assert r['main_contract_wages_native']==[79575]*3 and r['inputs_unchanged']
    p=REPO/'docs/NATIVE_LOANS.md';text=p.read_text(encoding='utf-8-sig')
    text=text.replace('| +19 | int32 | 5000000 | Kwota Fee To Buy, little-endian; TEST_LOAN_FEE potwierdza 5000000 → 7000000 |','| +19 | int32 | 5000000 | Kwota Fee To Buy, little-endian; 5000000 → 7000000 potwierdzone; -1 = opcja wyłączona (TEST_LOAN_FEE_OFF) |')
    text=text.replace('[41 kontroli z wariantami odwołania, numeru, udziału płac i wykupu]','[45 kontroli z wariantami odwołania, numeru, udziału płac, kwoty i wyłączenia wykupu]')
    text=text.replace('Kwota dla wyłączonej opcji wykupu nie ma jeszcze potwierdzonej interpretacji.','Zapis wyłączonej opcji wykupu potwierdza osobna próbka TEST_LOAN_FEE_OFF poniżej.')
    old='Następna próba: **TEST_LOAN_FEE_OFF**, od czystej 8.0.2, odtworzyć TEST_LOAN\nz kwotą 5000000 i następnie wyłączyć wyłącznie checkbox Fee To Buy.\nPozostałe warunki jak TEST_LOAN: pensja 50%, brak odwołania i numeru, te same daty.\nNie zakładamy z góry, że brak wykupu zapisuje się jako zero lub -1.'
    assert old in text
    text=text.replace(old,'**TEST_LOAN_FEE_OFF — wykonane:** wyłączenie checkboxa zapisuje -1 w polu kwoty na +19.')
    text+='''

## Wariant TEST_LOAN_FEE_OFF — wynik 2026-11-06

Wyłączenie checkboxa Fee To Buy zastępuje 5000000 wartością **-1** w polu
`int32 little-endian` od +19: `40 4B 4C 00 → FF FF FF FF`.
Cała tabela SI odpowiada dokładnie tej jednej zmianie pola względem TEST_LOAN.
Bajt opcji +17 pozostaje 0; w tej próbce brak wykupu nie wymaga osobnego bitu.
Nie utożsamiać -1 z kwotą 0: zero nie zostało sprawdzone jako wariant wykupu.

Daty, Inter jako klub wypożyczenia, udział płac 50%, niewskazany numer 255,
indeks 6210 i UID 1800000090 pozostają identyczne. Wszystkie 6210 starych wpisów,
całe rekordy Juventusu i Interu oraz główna umowa Buffona są niezmienione.
Płaca natywna pozostaje 79575, numer głównej umowy 1. Ewentualna różnica indeksu
imienia jest sprawdzana w słowniku jako ta sama nazwa i ten sam UID.

Wspólny czytnik zachowuje tę wartość jako `FeeToBuyRaw == -1`.
Dowody: `FmLauncher/data/research/LOANS_20261106_BUFFON_FEE_OFF/report.json`.
Testy odtwarzają całą tabelę w pamięci i sprawdzają zachowanie innych pól
oraz hashe wejść. Nie zapisują baz. Tworzenie nowych wypożyczeń natywnym
wykonawcą i zachowanie gry pozostają niepotwierdzone.

Następna przydatna próba: **TEST_LOAN_WAGES_ZERO**, od czystej 8.0.2 odtworzyć
TEST_LOAN i zmienić tylko udział płac 50% → 0%. Wykup włączony 5000000,
brak odwołania i numeru, te same daty. Surowe 255 nadal ma nieustalone znaczenie.
'''
    p.write_text(text,encoding='utf-8')
    p=REPO/'fm08_compendium.md';text=p.read_text(encoding='utf-8-sig')
    text=text.replace('Wartość przy wyłączonej opcji wykupu wymaga osobnej próby TEST_LOAN_FEE_OFF.','Osobna próba TEST_LOAN_FEE_OFF potwierdza -1 przy wyłączonej opcji wykupu.')
    text+='''

#### Wyłączona opcja wykupu — TEST_LOAN_FEE_OFF

Wyłączenie Fee To Buy w SI zapisuje -1 (FF FF FF FF) jako int32 od +19
rekordu LOAN. Bajt opcji +17 i pozostałe warunki nie zmieniają się.
Cała tabela odpowiada jednej zmianie pola kwoty, a stare wypożyczenia,
główna umowa Buffona i kadry pozostają identyczne. Zero nie jest potwierdzonym
zamiennikiem -1. Szczegóły: [NATIVE_LOANS.md](docs/NATIVE_LOANS.md).
'''
    p.write_text(text,encoding='utf-8')
    print('Documented signed -1 disabled-fee sentinel and unchanged option byte.')

def finalize():
    r=read(R/'report.json');t=read(R/'native-tests.json');m=read(BUILD/'build-manifest.json')
    assert t['status']=='pass' and t['checks']==45
    for path,key in [('baseline','baseline_hashes'),('reference','reference_hashes'),('fixture','fixture_hashes')]:assert hashes(Path(r[path]))==r[key]
    for e in m['Sources']:assert sha(REPO/e['Path'])==e['SHA256']
    for e in m['Outputs']:assert sha(BUILD/e['Path'])==e['SHA256']
    archive=R/'source-snapshot';archive.mkdir(exist_ok=False)
    files={e['Path'] for e in m['Sources']};files.update(['build.ps1','scratch/analyze_buffon_loan_20261106.py','scratch/compare_native_player_tests.py','scratch/compare_buffon_loan_variant_20261106.py','scratch/research_buffon_loan_fee_off_20261106.py','scratch/research_buffon_loan_wages_20261106.py','docs/NATIVE_LOANS.md','fm08_compendium.md'])
    entries=[]
    for rel in sorted(files):
        dest=archive/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(REPO/rel,dest);entries.append(dict(path=rel,SHA256=sha(dest)))
    shutil.copy2(BUILD/'build-manifest.json',R/'build-manifest.json');save(archive/'manifest.json',dict(source_only=True,files=entries,build_manifest_sha256=sha(BUILD/'build-manifest.json')))
    result=dict(status=r['status'],record_offset=19,field_type='int32_little_endian',before=5000000,after=-1,disabled_fee_value=-1,options_byte_unchanged=True,reader_checks_passed=45,prior_loans_preserved=6210,input_databases_unchanged=True,build=str(BUILD),source_files_archived=len(entries),game_behavior='not_tested',native_generated_fixture_SI_acceptance='not_tested',proposed_next_case=dict(name='TEST_LOAN_WAGES_ZERO',baseline=r['baseline'],reference='TEST_LOAN',single_change='Wage contribution 50 to 0 percent; buy fee enabled at 5000000; recall disabled; shirt unspecified'))
    save(R/'result.json',result)
    policy_path=R.parent/'LOAN_RESEARCH_POLICY.json';policy=read(policy_path);policy.update(latest_case=str(R),fee_to_buy_disabled_meaning='disabled_option',confirmed_fee_to_buy_disabled_value=-1);save(policy_path,policy)
    print(json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','document','finalize']);a=p.parse_args();{'prepare':prepare,'document':document,'finalize':finalize}[a.stage]()
