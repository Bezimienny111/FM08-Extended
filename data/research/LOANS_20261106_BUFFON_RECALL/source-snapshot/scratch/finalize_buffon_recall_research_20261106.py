"""Finalize documentation and immutable evidence for the verified Buffon recall flag."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REPO=ROOT/'FM08-Database-Tools'
RESEARCH=ROOT/'FmLauncher/data/research/LOANS_20261106_BUFFON_RECALL'
PRIOR=ROOT/'FmLauncher/data/research/LOANS_20261106_BUFFON'
BUILD=REPO/'out/loans-20261106-recall-r1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def hashes(root):return {str(f.relative_to(root)):sha(f) for f in root.rglob('*') if f.is_file()}
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
r=read(RESEARCH/'report.json');tests=read(RESEARCH/'native-tests.json');manifest=read(BUILD/'build-manifest.json')
assert tests['status']=='pass' and tests['checks']==28
assert hashes(Path(r['baseline']))==r['baseline_hashes']
assert hashes(Path(r['no_recall_fixture']))==r['no_recall_hashes']
assert hashes(Path(r['recall_fixture']))==r['recall_hashes']
for e in manifest['Sources']:assert sha(REPO/e['Path'])==e['SHA256']
for e in manifest['Outputs']:assert sha(BUILD/e['Path'])==e['SHA256']
# Restore the preceding source-only documentation snapshot, then apply the new finding in UTF-8.
p=REPO/'docs/NATIVE_LOANS.md';text=(PRIOR/'source-snapshot/docs/NATIVE_LOANS.md').read_text(encoding='utf-8-sig')
text=text.replace('Próbka utworzenia wypożyczenia przez oficjalny edytor SI.','Próbki utworzenia wypożyczenia i włączenia odwołania przez oficjalny edytor SI.')
text=text.replace('| +17 | byte | 0 | Surowe opcje; bit odwołania jeszcze niepotwierdzony |','| +17 | byte | 0 | Opcje: bit `0x04` = Can Be Recalled, potwierdzony w TEST_LOAN_RECALL |')
text=text.replace('[23 testy](../tests/TestNativeLoans.cs)','[28 kontroli z wariantem odwołania](../tests/TestNativeLoans.cs)')
text=text.replace('1. **TEST_LOAN_RECALL** — zaznaczyć tylko Can Be Recalled. Pozostałe wartości jak w TEST_LOAN.','1. **TEST_LOAN_RECALL — wykonane:** potwierdzono bit 0x04 na +17, patrz poniżej.\n2. **TEST_LOAN_NUMBER — następne:** włączyć tylko Squad Number i wpisać 31; Can Be Recalled wyłączone, pozostałe wartości jak w TEST_LOAN.')
text=text.replace('2. Następnie osobne warianty numeru koszulki, udziału płac oraz włączonej/wyłączonej opcji wykupu.','3. Następnie osobne warianty udziału płac oraz włączonej/wyłączonej opcji wykupu.').replace('3. Dopiero po tych porównaniach:','4. Dopiero po tych porównaniach:')
text+='''
## Wariant TEST_LOAN_RECALL — wynik 2026-11-06

Porównano trzy kopie: oryginalną 8.0.2, TEST_LOAN i TEST_LOAN_RECALL.
**Jedyna zmiana całego 32-bajtowego rekordu wypożyczenia: +17, 0x00 → 0x04.**
UID wpisu pozostaje 1800000090. Daty, klub, nieustawiony numer 255, wykup 5000000,
udział płac 50 i indeks 6210 są identyczne. Wszystkie 6210 wcześniejszych wypożyczeń
pozostają bajtowo identyczne z oryginalną 8.0.2.

Potwierdzona interpretacja: `CanBeRecalled = (OptionsRaw & 0x04) != 0`.
Nie utożsamiamy całego bajtu opcji z pojedynczym boolem; zachowujemy pozostałe bity.
Model `NativeLoanRecord` udostępnia teraz tę właściwość tylko do odczytu.

Całe rekordy klubów Juventusu i Interu są identyczne we wszystkich trzech kopiach.
Rekord PERSON Buffona między TEST_LOAN a TEST_LOAN_RECALL zmienia tylko bajt +196:
indeks imienia 48313 → 48316, ten sam tekst „Gianluigi” i UID nazwy 3803673.
Właściciel i główna umowa nie zmieniają się. Sześć plików historii jest identycznych.
Pozostałych różnic globalnego zapisu SI nie odtwarzamy jako zmiany tej flagi.

Cała tabela wariantu RECALL jest zgodna z tabelą TEST_LOAN po zmianie tego jednego bitu
w pamięci. Nie wygenerowano zmienionej bazy i nie testowano odwołania w nowej karierze.
Dowody: `FmLauncher/data/research/LOANS_20261106_BUFFON_RECALL/report.json`;
skrypt: [compare_buffon_loan_recall_20261106.py](../scratch/compare_buffon_loan_recall_20261106.py).
'''
assert 'niepotwierdzony |' not in text and 'TEST_LOAN_NUMBER' in text
p.write_text(text,encoding='utf-8')
p=REPO/'fm08_compendium.md';text=p.read_text(encoding='utf-8-sig');marker='#### Potwierdzenie flagi Can Be Recalled'
assert text.count(marker)==1
text=text.split(marker)[0].rstrip()+'''

#### Potwierdzenie flagi Can Be Recalled — TEST_LOAN_RECALL

Wariant SI zmienia wyłącznie +17 rekordu LOAN: 0 → 4. Potwierdzony bit odwołania
wynosi 0x04; odczyt `CanBeRecalled` maskuje tylko ten bit. UID 1800000090 i wszystkie
inne pola wypożyczenia są identyczne, podobnie 6210 starszych rekordów i obie kadry.
Umowa Buffona jest niezmieniona; indeks tego samego imienia zmienia 48313 → 48316.
Szczegóły i raport: [NATIVE_LOANS.md](docs/NATIVE_LOANS.md).
'''
p.write_text(text,encoding='utf-8')
archive=RESEARCH/'source-snapshot';archive.mkdir(exist_ok=False)
files={e['Path'] for e in manifest['Sources']}
files.update(['build.ps1','scratch/analyze_buffon_loan_20261106.py','scratch/compare_native_player_tests.py','scratch/compare_buffon_loan_recall_20261106.py','scratch/finalize_buffon_recall_research_20261106.py','docs/NATIVE_LOANS.md','fm08_compendium.md'])
entries=[]
for rel in sorted(files):
    src=REPO/rel;dest=archive/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest);entries.append(dict(path=rel,SHA256=sha(dest)))
shutil.copy2(BUILD/'build-manifest.json',RESEARCH/'build-manifest.json');save(archive/'manifest.json',dict(source_only=True,files=entries,build_manifest_sha256=sha(BUILD/'build-manifest.json')))
result=dict(status='controlled_recall_flag_verified',record_offset=17,mask='0x04',before=0,after=4,can_be_recalled_before=False,can_be_recalled_after=True,prior_loan_rows_preserved=6210,loan_uid=1800000090,main_contract_unchanged=True,club_records_unchanged=True,inputs_unchanged=True,reader_checks_passed=28,build=str(BUILD),report_sha256=sha(RESEARCH/'report.json'),source_files_archived=len(entries),native_generated_database_SI_acceptance='not_tested',new_career_test='not_tested',proposed_next_case=dict(name='TEST_LOAN_NUMBER',baseline=r['baseline'],reference='TEST_LOAN',single_change='Enable Squad Number and set 31; leave Can Be Recalled disabled and every other term unchanged'))
save(RESEARCH/'result.json',result)
policy_path=RESEARCH.parent/'LOAN_RESEARCH_POLICY.json';policy=read(policy_path);policy.update(latest_case=str(RESEARCH),confirmed_recall_mask='0x04',confirmed_recall_record_offset=17);save(policy_path,policy)
print(json.dumps({k:result[k] for k in ['status','mask','reader_checks_passed','inputs_unchanged','source_files_archived']},ensure_ascii=False),flush=True)
