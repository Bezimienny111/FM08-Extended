"""Read-only audit of Poland league activation; writes new research artifacts only."""
import argparse,csv,hashlib,json,re,shutil,struct,sys
from pathlib import Path
import capstone,pefile
sys.dont_write_bytecode=True
from analyze_buffon_loan_20261106 import ROOT,BASE,load,hashes,require,integer
from compare_native_player_tests import occurrences,controlled_club_record_candidate
from create_native_u23_test import language_blocks
EXPECTED='157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d'
REPO=ROOT/'FM08-Database-Tools'
REGIONS=[('pol_get_settings',0xe8ddc0,0xe8def4),('settings_registration',0xd63c10,0xd63c3a),('pol_minimum_teams',0xe8df90,0xe8dfdc),('minimum_limit_semantics',0xd35180,0xd35280),('pol_setup_comps',0xe8e950,0xe8ea44),('second_lower_pool_selection',0xe8ed20,0xe8edc8),('second_main_stage',0xe8ee60,0xe8ef3a),('second_rules_and_fates',0xe8f660,0xe8f7f8)]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def localized(block,uid):
    found=[]
    for a in occurrences(block,struct.pack('<i',uid)):
        pos=a+4;fields=[]
        try:
            for k in range(3):
                n=integer(block,pos);pos+=4;require(0<=n<=1000,'localized length')
                fields.append(block[pos:pos+n*2].decode('utf-16-le'));pos+=n*2
                require(block[pos:pos+2]==bytes(2),'localized terminator');pos+=2
                if k<2:pos+=1
            require(integer(block,pos)==uid+1,'next localized competition identity')
            found.append(fields)
        except (ValueError,UnicodeError,struct.error,IndexError):continue
    require(len(found)==1,'localized competition missing/ambiguous');return found[0]

def comp_record(s,uid,index):
    found=[]
    for a in occurrences(s,struct.pack('<i',uid)):
        start=a-64
        if start>=68 and a+72<=len(s) and s[start]==0 and integer(s,a-4)==index and integer(s,a-72)==index-1 and integer(s,a+64)==index+1:
            found.append((start,s[start:a+4]))
    require(len(found)==1,'native competition footer and adjacent indices');return found[0]

def analyze(output):
    doc=REPO/'docs/POLAND_THIRD_TIER.md'
    require(not output.exists() and not doc.exists(),'output/doc exists; refusing overwrite')
    inputs=[ROOT/'fm.exe',ROOT/'data/comps.efa',ROOT/'data/updates/update-802/data/comps.efa']
    pins={str(p.relative_to(ROOT)):sha(p) for p in inputs}
    require(pins['fm.exe']==EXPECTED,'unsupported executable')
    dbs=[BASE,ROOT/'Dane/db/2627_V25'];dbpins=[hashes(p) for p in dbs]
    policy=json.loads((ROOT/'FmLauncher/data/research/LOAN_RESEARCH_POLICY.json').read_text(encoding='utf-8-sig'))
    require(dbpins[0]==policy['baseline_hashes'],'canonical 8.0.2 source changed')
    raw=inputs[0].read_bytes();pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);checks=[]
    def off(va):return pe.get_offset_from_rva(va-base)
    def u32(va):return struct.unpack_from('<I',raw,off(va))[0]
    def ins(a,b):return list(md.disasm(raw[off(a):off(a)+b-a],a))
    def cstr(va):
        a=off(va);return raw[a:raw.index(b'\0',a)].decode('ascii')
    def check(label,ok):require(ok,label);checks.append(label)
    exports={e.name.decode():base+e.address for e in pe.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
    for n,va in [('pol_get_settings',0xe8ddc0),('pol_get_minimum_division_teams',0xe8df90),('pol_setup_comps',0xe8e950)]:check('export '+n,exports[n]==va)
    def call_args(a,b,target,n):
        pushes=[];found=[]
        for i in ins(a,b):
            if i.mnemonic=='push':pushes.append(i.op_str)
            if i.mnemonic=='call':
                if i.op_str==hex(target):found.append(dict(call=hex(i.address),arguments=list(reversed(pushes[-n:]))))
                pushes=[]
        return found
    registrations=call_args(0xe8ddc0,0xe8def4,0xd63c10,3)
    check('exactly two league settings entries',registrations==[dict(call='0xe8de15',arguments=['0x1fa16','0','0']),dict(call='0xe8de25',arguments=['0x1fa17','1','0'])])
    minimum=call_args(0xe8df90,0xe8dfdc,0xd35180,6)
    check('lower pool minimum 30 and no maximum',minimum[-1]['arguments']==['0x1fa18','0x313','0x1e','-1','0','0'])
    check('first minimum 16',minimum[0]['arguments'][2:4]==['0x10','-2'])
    check('second minimum 18',minimum[1]['arguments'][2:4]==['0x12','-2'])
    setup=ins(0xe8e950,0xe8ea44)
    constructors=[int(i.op_str,16) for i in setup if i.mnemonic=='call' and i.op_str.startswith('0xe8')]
    check('five Polish constructors',constructors==[0xe8dfe0,0xe8e320,0xe8e7f0,0xe8e190,0xe8e400])
    classes=[]
    for va in constructors:
        assigns=[i for i in ins(va,va+0xa0) if i.mnemonic=='mov' and i.op_str.startswith('dword ptr [esi], 0x')]
        require(len(assigns)==1,'constructor primary vtable')
        vt=int(assigns[0].op_str.split(', ')[1],16);col=u32(vt-4);td=u32(col+12)
        classes.append(dict(constructor=hex(va),vtable=hex(vt),rtti=cstr(td+8)))
    check('two league classes, three cups',set(c['rtti'] for c in classes)=={'.?AVPOL_FIRST@@','.?AVPOL_SECOND@@','.?AVPOL_SUPER_CUP@@','.?AVPOL_FA_CUP@@','.?AVPOL_LEAGUE_CUP@@'})
    anchors=[(0xe8edbb,'push','0x1fa18'),(0xe8edc0,'call','0xd7b260'),(0xe8f69d,'mov','word ptr [ebp], 0x12'),(0xe8f7b6,'push','0x1fa16'),(0xe8f7d5,'call','0xdc7160'),(0xe8f7db,'push','4'),(0xe8f7dd,'push','0x1fa18'),(0xe8f7e4,'call','0xdc71c0'),(0xe8eed0,'call','0xdd07f0'),(0xe8eee9,'call','0xd73fc0')]
    for va,mn,op in anchors:
        i=ins(va,va+15)[0];check('native instruction '+hex(va),(i.mnemonic,i.op_str)==(mn,op))
    vslots={hex(v):{hex(slot):hex(u32(v+slot)) for slot in [0x158,0x160,0x164]} for v in [0x162f28c,0x162fa2c]}
    check('Polish rule factories are native overrides',vslots['0x162f28c']['0x160']=='0xe90740' and vslots['0x162fa2c']['0x160']=='0xe8f660')
    archives=[]
    for path in inputs[1:]:
        decoded=bytes(b^255 for b in path.read_bytes())
        ids=re.findall(rb'<properties\s+competition="(\d+)"',decoded)
        check('no Polish ID definition in '+str(path.relative_to(ROOT)),all(str(u).encode() not in decoded for u in [129558,129559,129560]))
        archives.append(dict(path=str(path.relative_to(ROOT)),competition_headers=[int(x) for x in ids],polish_ids_present=False))
    results=[];rows=[]
    for folder in dbs:
        s=load(folder,'server_db.dat');p=load(folder,'people_db.dat');count=integer(p,0)
        blocks=dict(language_blocks((folder/'lang_db.dat').read_bytes()));comps=[]
        for uid,idx in [(129558,139),(129559,140),(129560,141)]:
            at,record=comp_record(s,uid,idx);names={str(lang):localized(blocks[lang],uid) for lang in [8,18]};clubs=[]
            for loc in occurrences(s,struct.pack('<i',idx)):
                candidate=controlled_club_record_candidate(s,loc-7,count)
                if not candidate:continue
                ci,start,end=candidate;ro=start+63+s[start+62]*4;n=struct.unpack_from('<H',s,ro)[0]
                clubs.append(dict(club_index=ci,club_uid=integer(s,end-4),roster_count=n,start=start,end=end))
            check(folder.name+' division '+str(idx)+' club uniqueness',len(clubs)==len({c['club_uid'] for c in clubs})==len({c['club_index'] for c in clubs}))
            check(folder.name+' division '+str(idx)+' expected club count',len(clubs)=={139:16,140:18,141:118}[idx])
            comps.append(dict(uid=uid,index=idx,names=names,record_offset=at,record_hex=record.hex(' '),clubs=clubs,club_count=len(clubs),roster_entries=sum(c['roster_count'] for c in clubs),empty_rosters=sum(c['roster_count']==0 for c in clubs),rosters_below_eleven=sum(c['roster_count']<11 for c in clubs)))
            rows.extend(dict(database=folder.name,competition_uid=uid,competition_index=idx,club_index=c['club_index'],club_uid=c['club_uid'],roster_count=c['roster_count']) for c in clubs)
        results.append(dict(path=str(folder),source_role='canonical_reference' if folder==BASE else 'current_working_database_read_only_comparison',hashes=dbpins[len(results)],competitions=comps))
    check('input file hashes unchanged',pins=={str(p.relative_to(ROOT)):sha(p) for p in inputs})
    check('all database file hashes unchanged',dbpins==[hashes(p) for p in dbs])
    output.mkdir(parents=True)
    report=dict(status='static_poland_third_tier_feasibility_audited',exe_sha256=EXPECTED,input_hashes=pins,checks=checks,settings_registrations=registrations,minimum_team_calls=minimum,constructed_classes=classes,rule_vtable_slots=vslots,competition_archives=archives,databases=results,shared_editor_crosscheck=dict(build='out/staff-20261106-r2',method='ParseNativeClubDivisions',observed_independently_in_read_only_PowerShell=True,counts_match=True),conclusion='UID 129560 is a lower-club pool; the current Polish settings register only levels 0 and 1, and setup constructs only two league classes.',unknowns=['full league-selection UI consumer path','new playable object construction and registration route','new competition creation and native save/load compatibility','correct calendar, participant selection, fate links, and lower-pool boundary','new career and multi-season execution'],game_executed=False,game_patched=False,database_modified=False,inputs_unchanged=True)
    save(output/'report.json',report)
    with (output/'club-membership.csv').open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['database','competition_uid','competition_index','club_index','club_uid','roster_count']);w.writeheader();w.writerows(rows)
    lines=[]
    for label,a,b in REGIONS:
        lines.append('\n'+label+' '+hex(a)+'..'+hex(b));lines.extend('%08X %-8s %s'%(i.address,i.mnemonic,i.op_str) for i in ins(a,b))
    (output/'disassembly.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    doc.write_text('''# Polska: grywalny trzeci poziom - analiza 2026-11-07

## Wynik

UID **129560** istnieje jako **Polish Lower Division / Polska Niższa Liga**,
indeks COMP **141**. W obecnym silniku pełni rolę zbiorczego zaplecza niższych
klubów. Nie znaleziono rejestracji tego UID jako trzeciego grywalnego poziomu.
Istnienie rekordu, przypisanych klubów oraz poziomu w bazie nie tworzy ligi
z terminarzem i możliwością objęcia zespołu.

Analiza kontynuuje ustalenia Status.md z 2026-10-21 i ponownie sprawdza
oryginalny fm.exe o SHA256 157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d.
Bez uruchamiania gry, patchowania EXE i zmian danych wejściowych.

## Dane obu baz

| Baza | UID / rozgrywki | Kluby | Wpisy na listach osób | Puste listy | Listy poniżej 11 |
|---|---|---:|---:|---:|---:|
| Oryginalna 8.0.2 | 129558 / najwyższy poziom | 16 | 818 | 0 | 0 |
| Oryginalna 8.0.2 | 129559 / drugi poziom | 18 | 532 | 0 | 0 |
| Oryginalna 8.0.2 | 129560 / niższe ligi | 118 | 374 | 53 | 108 |
| 2627_V25 | 129558 / najwyższy poziom | 16 | 443 | 0 | 0 |
| 2627_V25 | 129559 / drugi poziom | 18 | 541 | 0 | 0 |
| 2627_V25 | 129560 / niższe ligi | 118 | 552 | 52 | 102 |

Nazwy oryginalnej bazy: 129558 Polish First Division / Polska 1. Liga;
129559 Polish Second Division / Polska 2. Liga. To historyczne nazwy dwóch
najwyższych poziomów, a nie współczesna numeracja lig. Nie ustalano tutaj
rzeczywistego składu ani regulaminu sezonu 2026/27.

Wpisy list osób CLUB nie są liczbą kompletnych pierwszych drużyn ani
zweryfikowanych zawodników: mogą wymagać sprawdzenia rodzaju osoby, rezerw,
kontraktów, emerytur i aktualności. Samo 11 wpisów nie dowodzi gotowości kadry.
Liczebności potwierdzono dwoma sposobami: strukturalnym odczytem Python i
wspólną funkcją edytora ParseNativeClubDivisions z builda staff-20261106-r2.
CSV zawiera indeksy i UID, bez zgadywania nazw klubów starszym parserem.

## Gdzie powstaje ograniczenie

- Eksport pol_get_settings **0x00E8DDC0** rejestruje tylko 129558 / indeks 0
  i 129559 / indeks 1. Wywołania helpera **0x00D63C10** są przy
  **0x00E8DE15** i **0x00E8DE25**. Helper umieszcza rekord w settings+0x30.
  To potwierdzenie zawartości ustawień; całej drogi do kontrolki UI nie prześledzono.
- pol_setup_comps **0x00E8E950** tworzy pięć obiektów: POL_FIRST,
  POL_SECOND, POL_SUPER_CUP, POL_FA_CUP, POL_LEAGUE_CUP. Tożsamości klas
  sprawdzono przez vtable i MSVC RTTI. W tej funkcji brak tworzenia trzeciej ligi.
- POL_FIRST: vtable **0x0162F28C**, fabryka reguł +0x160 -> **0x00E90740**.
  POL_SECOND: vtable **0x0162FA2C**, fabryka reguł -> **0x00E8F660**.
  Reguły Polski są implementowane w kodzie. W obu sprawdzonych comps.efa
  po XOR 0xFF nie występują ID 129558, 129559 i 129560. Nie dowodzi to,
  że dodanie własnej definicji nigdy nie zadziała, ale nie jest gotową metodą aktywacji.
- pol_get_minimum_division_teams **0x00E8DF90** wymaga odpowiednio
  16, 18 i minimum 30 klubów. Trzeci wpis ma maksimum -1, czyli bez górnego
  limitu w helperze **0x00D35180**. To kontrola puli klubów, nie format ligi
  na 30 zespołów ani deklaracja 30 grywalnych miejsc.
- **0x00E8ED20** używa 129560 do selekcji klubów przy **0x00E8EDC0**.
  POL_SECOND w fabryce reguł kieruje spadki do 129560:
  **0x00E8F7DD -> 0x00E8F7E4 / 0x00DC71C0**, cztery miejsca po normalizacji
  parametrów 4/-1. Awans prowadzi do 129558. Kopia drugiej ligi zachowałaby
  niewłaściwe cele oraz pozostałe polskie założenia i powiązania barażowe.

## Dwie drogi do prototypu

1. **Zachować 129560 jako zaplecze i utworzyć osobny rekord trzeciej ligi.**
   Wybrane kluby przenieść do nowego rekordu; reszta pozostaje niżej.
   Dodać poziom 2 do ustawień, tworzenie aktywnego obiektu i etapu, reguły,
   terminarz i połączenia drugiego poziomu z nowym trzecim oraz trzeciego
   z zapleczem 129560. Uczestników pucharów i historyczną selekcję sprawdzić
   osobno. Preferowany wariant projektowy: utrzymuje osobną pulę poniżej ligi.
2. **Przeznaczyć 129560 na grywalny trzeci poziom.** Wybrać jego uczestników,
   utworzyć nowe zaplecze dla pozostałych klubów i przepiąć dotychczasowe
   odwołania wymagające starej puli, w tym minimalną liczebność i selekcję.
   Obecna tożsamość 129560 nie czyni tej drogi prostą ani sprawdzoną.

Obie drogi wymagają zmian silnika i danych. Nie wystarczy zmienić nazwy,
reputacji, jednego nieopisanego bajtu lub dodać wiersza do menu. Nie ma jeszcze
implementacji tworzenia nowej ligi ani dowodu zgodnej serializacji.
Nie udowodniono również, że musi powstać nowa klasa C++: potencjalna droga
przez ogólny ACTUAL_COMP i reguły opisane danymi wymaga osobnego sprawdzenia.
Nie należy zmieniać ID drugiej ligi globalnym zastępowaniem bajtów.

## Zalecany zakres pierwszego eksperymentu

Najpierw ustalić format. Jedna grupa 18 zespołów i dwie rundy (34 kolejki)
jest rozsądną propozycją do technicznego prototypu, a nie przyjętym wymaganiem
ani zweryfikowaną rekonstrukcją sezonu. Najwyższe dwa poziomy zachować
początkowo w formacie obecnego FM08, aby ograniczyć liczbę jednoczesnych zmian.
Jeśli docelowo mają odpowiadać innemu sezonowi, potrzebny będzie osobny zakres
ich rozmiaru, kalendarza, awansów i baraży.

Kolejność prac: ustalić konsumenta ustawień i sposób tworzenia aktywnego
obiektu; przygotować izolowany prototyp z wydzieloną obsadą i zapleczem;
następnie potwierdzić wybór poziomu i klubu, wygenerowany terminarz,
zapis/wczytanie oraz awanse, spadki i kolejny sezon. Import współczesnych
kadr wykonywać dopiero po stabilizacji struktury.

Podstawa eksperymentów pozostaje oryginalna 8.0.2. V25 odczytano tylko dla
porównania, nie jest wyjściem eksperymentu. Wykaz plików i hashe obu baz
sprawdzono przed i po analizie. Aktualny importer zachowuje liczebność lig;
nie używać jego zwykłego CSV jako narzędzia przebudowy piramidy.

## Dowody

Raport: FmLauncher/data/research/POLAND_THIRD_TIER_20261107/report.json.
Obok: club-membership.csv, disassembly.txt i źródła analizy.
Wynik jest analizą statyczną i audytem przypisań, nie zaliczonym pilotem.
''',encoding='utf-8')
    archive=output/'source-snapshot';archive.mkdir()
    files=[Path(__file__),doc]
    archived=[]
    for path in files:
        dest=archive/path.relative_to(REPO);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest);archived.append(dict(path=str(path.relative_to(REPO)),sha256=sha(dest)))
    save(archive/'manifest.json',dict(source_only=True,files=archived))
    save(output/'result.json',dict(status=report['status'],checks_passed=len(checks),canonical_lower_pool_clubs=118,current_lower_pool_clubs=118,polish_playable_levels_registered=2,inputs_unchanged=True,game_executed=False,game_patched=False,database_modified=False))
    print(json.dumps(dict(status=report['status'],checks_passed=len(checks),database_club_counts=[[c['club_count'] for c in db['competitions']] for db in results],inputs_unchanged=True)))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();analyze(args.output)
