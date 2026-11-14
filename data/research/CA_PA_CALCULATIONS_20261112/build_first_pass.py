from pathlib import Path
import json,hashlib,shutil,re,struct,math
import pefile,capstone
from fractions import Fraction as F
root=Path('J:/FM08dev')
out=root/'FmLauncher/data/research/CA_PA_CALCULATIONS_20261112'
assert not (out/'manifest.json').exists(), 'Do not replace existing report'
out.mkdir(parents=True,exist_ok=True)
(out/'evidence').mkdir(exist_ok=True)
exe=root/'fm.exe'; data=exe.read_bytes(); sha=lambda b:hashlib.sha256(b).hexdigest()
expected='157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d'
assert sha(data)==expected
pe=pefile.PE(data=data);base=pe.OPTIONAL_HEADER.ImageBase
assert base==0x400000
r5=root/'FmLauncher/data/research/GHIDRA_ENGINE_20261107_R5/decompiled'
idx=json.loads((r5/'function-index.json').read_text())
functions={int(x['address'],16):x for x in idx['functions'] if x.get('path')}
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
def raw(a,n):
 rva=a-base
 for s in pe.sections:
  if s.VirtualAddress<=rva and rva+n<=s.VirtualAddress+s.SizeOfRawData:
   offset=s.PointerToRawData+rva-s.VirtualAddress
   return data[offset:offset+n],offset
 raise ValueError('Not raw backed '+hex(a))
def savej(name,obj): (out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
pins=[]
selected=[0xad2630,0xad15f0,0xad1990,0xad1040,0xad1120,0xad13c0,0xad1560,0xd23aa0,0xd23ae0,0xd23f00,0xa7a860,0xcae280,0xcae320,0xcae3a0,0x1142b20,0x1142b40,0xad02a0,0xcb1840,0xcb1350,0xc80440,0xcb3000,0xd24120,0x881bc0,0xa34e00,0x85bc40,0x8d3d60]
for a in selected:
 f=functions[a];source=r5/f['path']; c=source.read_bytes();assert sha(c)==f['sha256']
 name='ram_'+format(a,'x');(out/'evidence'/f'{name}.c').write_bytes(c)
 chunks=[];asm=[];ranges=[]
 for rr in f['body_ranges']:
  start=int(rr['start'],16);end=int(rr['end'],16)+1;b,off=raw(start,end-start);chunks.append(b)
  ranges.append({'va':hex(start),'end_exclusive':hex(end),'file_offset':off,'bytes':len(b),'sha256':sha(b)})
  asm+=['%08x  %-24s %s %s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str) for i in md.disasm(b,start)]
 body=b''.join(chunks);(out/'evidence'/f'{name}.bin').write_bytes(body);(out/'evidence'/f'{name}.asm').write_text('\n'.join(asm)+'\n',encoding='utf-8')
 declared=re.search(rb'body=([0-9a-f]{64})',c).group(1).decode() # R5 opaque body tag is not a raw-code SHA256
 pins.append({'va':hex(a),'source':str(source.relative_to(root)).replace('\\','/'),'c_sha256':sha(c),'body_sha256':sha(body),'r5_opaque_body_tag':declared,'ranges':ranges})
# This parser is a genuine gap in R5 function recovery. Preserve its explicit bounded ASM separately.
a=0xd379d0;b,off=raw(a,0xd382f7-a)
(out/'evidence/native_weight_parser_d379d0.bin').write_bytes(b)
ins=list(md.disasm(b,a));(out/'evidence/native_weight_parser_d379d0.asm').write_text('\n'.join('%08x  %-24s %s %s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str) for i in ins)+'\n',encoding='utf-8')
pins.append({'va':hex(a),'status':'ASM_ONLY_R5_GAP_NO_FALSE_FUNCTION_ASSIGNMENT','end_exclusive':'0xd382f7','file_offset':off,'bytes':len(b),'sha256':sha(b)})
last=None;named=[]
for i in ins:
 if i.mnemonic=='push' and i.op_str.startswith('0x'):
  v=int(i.op_str,16)
  if 0x1200000<v<0x1900000:
   try:
    bb,_=raw(v,100);ss=bb.split(bytes([0]),1)[0]
    if len(ss)<80:last=(ss.decode('latin1'),v)
   except ValueError:pass
 if i.mnemonic=='mov' and i.op_str.startswith('byte ptr [esp + 4],') and last:
  val=int(i.op_str.split(', ')[1],0)
  if i.address<0xd38044:named.append({'internal_index':val,'index_hex':hex(val),'name_literal':last[0],'string_va':hex(last[1]),'assignment_va':hex(i.address),'native_CA_weight':None,'status':'NAME_INDEX_PROVEN_WEIGHT_UNKNOWN'})
savej('native-attribute-map.json',named)
constants={}
for a,t in [(0x121ab80,'d'),(0x157aff0,'d'),(0x121ab58,'d'),(0x152e900,'d'),(0x1429318,'d'),(0x1230a70,'d'),(0x18c96c0,'d'),(0x129ecd4,'f')]:
 b,off=raw(a,struct.calcsize(t));constants[hex(a)]={'type':t,'value':struct.unpack('<'+t,b)[0],'raw_hex':b.hex(),'file_offset':off}
savej('source-pins.json',{'exe':str(exe),'exe_bytes':len(data),'exe_sha256':expected,'base':hex(base),'functions':pins,'constants':constants,'runtime_access':False})
formulas={
 'status':'FIRST_STATIC_PASS_COMPLETE_SCOPE_PARTIAL',
 'stored_CA':{'offset_from_PLAYER':'0x14','type':'signed16','distinct_from_derived_attribute_score':True},
 'stored_PA':{'offset_from_PLAYER':'0x16','type':'signed16','not_a_consumed_points_pool':True},
 'generation_scale':{'function':'0xad2630','formula':'x[j] *= 5 for j=25..79; indices0..24 unchanged','reads_CA':False,'status':'PROVEN_ASM'},
 'display':{'function':'0xcae280','scaled_indices':'25..79','formula':'clamp(trunc((clamp(raw,0,100)+2)*float32(0.2)),1,20)','status':'PROVEN_ASM'},
 'position_blend':{'function':'0xd23ae0','positions_internal_indices':[0,1,12,13,14,15,16,17,18,19,20,21,22,23,24], 'p_r':'clamped position proficiency0..100; normal valid position range1..20','t_r':'max(p_r-10,0)','S':'sum(t_r)','raw_table_object':'0x1b1ee84','raw_table_values':None,'w_j':'sum(t_r*B_rj)/max(10,S)','v_j':'w_j*(w_j+1)/2 if w_j>1 else0','u_j':'w_j*w_j if w_j>1 else0','foot_override':'when table B=0: index50 ->5 unless x50==100 and x51<100; index51 ->5 unless x51==100','status':'STRUCTURE_PROVEN_ASM_RAW_TABLE_UNKNOWN'},
 'attribute_score':{'function':'0xd23f00','flag0':'sum(x_j*v_j)/sum(v_j), zero for nonpositive denominator','nonzero_flags':'denominator includes every v_j before numerator filtering; do not recompute denominator after filtering','status':'PROVEN_ASM'},
 'normalization':{'function':'0xa7a860','target':'T=5*(6+0.05*clamp(CA,1,200))=30+CA/4','sum_v':'W=sum(v_j)','tolerance':'h=3.75*W/count(nonzero v_j)','q_j':'0.2*v_j*(x_j-T)','soft':'soft(q,h)=max(q-h,0)+min(q+h,0)','score':'Q=(sum(v_j*x_j)+3.75*sum(soft(q_j,h)))/W','initial_step':'round_away_from_zero(T-Q), clamp to +/- clamp(5-trunc(iteration/10),1,5)','later_step':'oscillation damping and deterministic subset selection; not yet full executable port','mutates':'attribute bytes only; observed body has no CA/PA write','max_iterations':1000,'status':'FPU_SCORE_RECOVERED_ASM_FULL_ITERATOR_PARTIAL'},
 'native_cost_warning':'v_j and piecewise Q are native score coefficients, not integer CA points for every displayed stat; not Genie weights',
 'zero_cost':'For fixed positions/feet, v_j=0 is zero direct contribution in D23F00/A7A860. Personality bytes outside80-element payload not read in these routines. Universal named zero-cost list not established.',
 'PA_negative':{'ranges_upper_exclusive':{'-10':[170,200],'-9':[150,180],'-8':[130,160],'-7':[110,140],'-6':[90,120],'-5':[70,100],'-4':[50,80],'-3':[30,60],'-2':[10,40],'-1':[1,20]},'raise_lower_base_to_CA':True,'helper_sorts_endpoints':True,'minus10':'reroll once when first>=190','finalizer':'PA=clamp(max(PA,CA),1,200)'},
 'redistribution':{'feasible_design':True,'implemented':False,'exact_for_all_players':False,'must_preserve':['stored CA','stored PA','fixed positions and foot configuration','native score Q at same target','valid units/ranges','provenance new-generated-only'],'linear_sum_alone_insufficient':True}
}
savej('formula-candidates.json',formulas)
# Minimal arithmetic verification, strictly offline; no DLL/native function calls, emulation or game access.
f32=struct.unpack('<f',struct.pack('<f',0.2))[0]
def display(x):return max(1,min(20,math.trunc((max(0,min(100,x))+2)*f32)))
assert all(display(5*d)==d for d in range(1,21))
assert display(1)==display(6)==1 and display(2)==display(7)==1
assert all(display(x+5)==display(x)+1 for x in range(3,93))
def score(x,v,T):
 W=sum(v);h=F(15,4)*W/sum(z!=0 for z in v)
 soft=lambda q:max(q-h,0)+min(q+h,0)
 return (sum(a*b for a,b in zip(x,v))+F(15,4)*sum(soft(F(1,5)*b*(a-T)) for a,b in zip(x,v)))/W
v=[F(15),F(55)];x=[F(10),F(100)];y=[F(21),F(97)]
assert sum(a*b for a,b in zip(x,v))==sum(a*b for a,b in zip(y,v))
assert score(x,v,F(55))!=score(y,v,F(55))
assert F(5)*15/55==F(15,11)
assert F(10,30)*F(10,30)==F(1,9)
savej('offline-verification.json',{'status':'PASS','scope':'Arithmetic and static byte identities only, no game/runtime execution','exe_pin':expected,'r5_functions_pinned':len(selected),'named_indices':len(named),'display_all_100_raw_values':[display(x) for x in range(1,101)],'setter_display_roundtrip_all20':True,'raw_plus5_exception_at1_and2':True,'nonlinear_counterexample':{'synthetic_not_native_weights':True,'v':[15,55],'target':55,'x':[10,100],'y':[21,97],'same_linear_numerator':5650,'Q_x':str(score(x,v,F(55))),'Q_y':str(score(y,v,F(55)))},'integer_compensation_counterexample':'For synthetic v=[15,55], +5 raw on first requires -15/11 raw on second; no exact integer solution using that second trait alone','minus10_probability_190plus_CA_le170':'1/9'})
savej('unresolved.json',[
 {'id':'U01','priority':1,'topic':'Full native B[15][80] values and initialization','known':'Object0x1B1EE84, getter1142B20, config parserD379D0 keys posi/attr/weig; raw BSS cannot be read as EXE table','next':'Find source configuration and default initializer; offline extract with source pins, do not substitute Genie'},
 {'id':'U02','priority':1,'topic':'Full A7A860 iterator model','known':'FPUscore recovered; clamps/halfstep/subset/1000 limit evidenced','next':'Independent FPU stack witness and complete deterministic iterator port, then differential isolated tests'},
 {'id':'U03','priority':1,'topic':'Feet and complete canonical enum mapping','known':'Foot overrides indices50/51; names of51 other attributes from native parser','next':'Prove named foot getter chain and DAT/runtime mapping, include dominant100 threshold changes'},
 {'id':'U04','priority':2,'topic':'Universal zero-cost named traits','known':'v<=0 implies zero direct score; personality separatepayload not read','next':'Recover all native table rows; do not infer zero CA from role irrelevance'},
 {'id':'U05','priority':2,'topic':'RCA integer conversion and every normalization caller','known':'D23F00 mean and D23AA0 target, creationCB3541 and monthlyA3608A callers','next':'Close monthlycallers and position-change paths; no general automatic-correction theorem'},
 {'id':'U06','priority':2,'topic':'New-player-only integration and persistence','known':'Factorylate882523 candidate afterinitialtraining; generator/finalizer sharedwithothercontexts','next':'Prove contexts and idempotency; future isolated career save/reload/training test, not requested now'},
 {'id':'U07','priority':3,'topic':'PA mutability allnativepaths','known':'Creation clamping and monthlyCA<=PA, these setters noPAwrites','next':'Do not claim global immutability solely from these routines; own DynamicPA separate'}])
(out/'ERRATA.md').write_text('''# Errata do raportu generatora 12 XI 2026

Wycofane twierdzenie G13 z NEW_PLAYER_GENERATION_20261112/findings.json oraz zdanie o końcowym normalizowaniu doCA przez0xAD2630.

Całe ciało0xAD2630:0xAD2630..0xAD2651,34bajty, zachowano w evidence/ram_ad2630.bin/.asm. Nie ma odczytu CA, argumentu stosowego, tabel wag ani wartości atrybutów innych niż aktualny bajt. Pętla0..79 mnoży tylko indeksy25..79 przez5. Ret8 jedynie usuwa8bajtów argumentów.

D29BBA..D29BC6 pobieraCA przez PLAYERslot0 i odkładaargument, lecz ECX przedCALL jestpayload+1C. OdbiorcaCA go nie czyta. Kontrprzykład: identyczne80bajtów i inneCA dają identyczne80bajtów wyniku tejfunkcji. To konwersja skali.

Prawdziwy dalszy normalizator to0xA7A860, callsiteCB3541 poD24120 oraz A3608A po miesięcznejzmianieCA. Jego arytmetyka jest opisana osobno w RAPORT.md. Nie zmieniono zamrożonego starszegoraportu ani jego manifestu.
''',encoding='utf-8')
(out/'RAPORT.md').write_text('''# CA i PA FM08: pierwszy przebieg obliczeń — 12 XI 2026

Stan: zakończony pierwszy przebieg statyczny, zakres częściowy. Jest już rzeczywisty model mieszania pozycji, funkcja oceny atrybutów oraz odtworzona arytmetyka normalizatora. Nie ma jeszcze pełnej tabeli liczbowych wag15×80. Nie wdrożono patcha ani polityki ocen.

Pomysł losowych+1/+2 i kompensacji jest wykonalny jako projekt, ale nie można zagwarantować zachowania natywnego bilansu przez odejmowanie tylu samych punktów ani przez wagiGenie. Potrzebne są odzyskane wagi silnika, poprawne jednostki oraz uwzględnienie nieliniowości. Niekiedy dla konkretnego żądanego bonusu i dozwolonej puli odejmowanych cech nie istnieje dokładne rozwiązanie całkowitoliczbowe. Wtedy trzeba odrzucić tę propozycję, zmienić jej losowanie albo szukać innej kombinacji; nie zmieniaćCA/PA, żeby ukryć błąd.

## Źródła i granice

Oryginalny J:/FM08dev/fm.exe, SHA256157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d, base0x400000. Użyto istniejącego eksportu GhidraR5 oraz statycznego ASM Capstone z dokładnie tych bajtów.26funkcji mają sprawdzone hashe C, zakresy ciał i hashe kodu; parserwag zachowano osobno, ponieważ R5 nie odzyskał jego granicy. Source-pins zawiera offsety plikowe i stałe. Nie czytano pamięci gry, nie uruchamiano ani nie zamykanoFM, nie wywoływano natywnych funkcji i nie zmienianoDB, EXE, launchera lub skórek.

Punktem startu był raport NEW_PLAYER_GENERATION_20261112. [ERRATA.md](ERRATA.md) wycofuje jego błędną etykietę0xAD2630 jako normalizacjiCA. Ten helper tylko mnoży skalowane cechy przez5. Prawdziwa normalizacja następuje później w0xA7A860. Stary manifest pozostaje niezmieniony.

## Zapisane CA, PA i rzeczywiste atrybuty

CA i PA są osobnymi polami signed16 względem bazy PLAYER:+0x14 i+0x16. Nie są sumami wyświetlanych atrybutów. PERSON i PLAYER to różne bazy obiektu. Wpisanie wartości atrybutu przez0xCAE320 lub0xCAE3A0 samo nie zapisujeCA aniPA. Tak samo0xA7A860 koryguje atrybuty, nie zapisaneCA/PA.

Łańcuch tworzenia:881BC0→CB1840(CA)/CB1350(PA)→CB3000→D24120(profil pozycji i cechy)→AD2630(skala)→A7A860(dopasowanie doCA). Callsite ostatnich dwóch etapów:D29BC6 iCB3541. Fabryka wykonuje następnie początkowy trening i wraca; późny kandydat integracji882523 jest po tym treningu. To kandydat statyczny, bez wdrożenia.

Dodatkowy rzeczywisty caller normalizacji jest w miesięcznej aktualizacjiA34E00: podA3605F następujeCA+=delta, ograniczenie do0..PA, a podA3608A wywołanieA7A860. To dowód korekty w tej ścieżce, nie gwarancja, że każda ręczna zmiana zostanie natychmiast albo zawsze skorygowana. Sam tygodniowy trening8D3D60 i cała miesięczna aktualizacja to osobne operacje. Harmonogram i każdy caller przy nauce pozycji pozostają częściowo do zamknięcia.

## Jednostki, zaokrąglenia i zakresy

Payload atrybutów jest pod*(PLAYER+CC), tablica odpayload+1C,80bajtów. Indeksy0..24 to pozycje/strony w skali1..20; indeksy25..79 mają wewnętrzną skalę1..100. To nie jest enum47cechUI ani offset89-bajtowego rekorduDAT.

AD2630 mnoży indeksy25..79 przez5 bez kontroliCA i bezclamp; prawidłowe wejście generacyjne1..20 daje5..100. Przekazanie tam już skalowanego payloadu byłoby błędem i może przepełnić bajt. GetterCAE280 w trybie wyświetlania najpierw ogranicza surową wartość do0..100 przezAD1990, następnie liczy clamp(trunc((raw+2)*float32(0.2)),1,20). SetterCAE320 z flagą skali mnoży żądaną widoczną wartość przez5 i ogranicza do1..100. SetterprzyrostowyCAE3A0 wykonuje clamp po dodaniu.

+1surowego bajtu zwykle nie oznacza+1widocznego punktu. +5surowych jednostek daje+1widoczny punkt dla zwykłego wnętrza skali, ale1→6 oraz2→7 nadal wyświetlają1. Zapisanie visible+1 setterem daje poprawny wynik, lecz może zmienić ukrytą resztę zaokrąglenia. Bilans trzeba liczyć z dokładnych wartości wewnętrznych, nie ze zrzutuUI. Pełne odwzorowanieDAT↔runtime dla wszystkich cech nie zostało tu dowiedzione.

## Mieszanie natywnych wag przez pozycje

D23AE0 buduje80wierszy po3double. AD1040 mapuje15wierszy pozycji na indeksy [0,1,12,13,14,15,16,17,18,19,20,21,22,23,24]. Dla znajomości pozycji p_r używa wkładu t_r=max(p_r−10,0). ASM dopuszcza porównanie>=10, lecz przy10wkład jestzerowy. Nie wybiera wyłącznie jednej pozycji naturalnej20.

Przy S=Σt_r i surowej natywnej tabeli B_rj:

```
w_j = Σ(t_r*B_rj) / max(10,S)
v_j = w_j*(w_j+1)/2, gdy w_j>1; inaczej0
u_j = w_j*w_j, gdy w_j>1; inaczej0
```

Pierwszy współczynnik jest używany również przy generacji; drugi v jest wagą oceny i normalizacji; trzeciego nie należy z nimi utożsamiać. Dla jednej pozycji20,w=B. Druga pozycja15dodaje połowę wkładu20 przed normalizacją mieszanki. Potem następuje transformacja trójkątna; średnia gotowychv dla dwóchpozycji nie jest tąsamąoperacją.

B jest pobierane przez1142B20 z globalnego obiektu1B1EE84. ParserD379D0 czyta klucze posi/attr/weig i przypisuje m.in.GK,SW,DC,D RL,WB RL,DM C,M C,AM C,M RL,AM RL,ST. Nie odzyskano jeszcze źródła kompletnej konfiguracji/defaultów ani liczbowychwartości B. Obiekt leży w niezainicjalizowanej pamięci, więc nie odczytano go jako surowej tabeli zplikuEXE. Nie podstawiono w jego miejsce GenieCSV.

[native-attribute-map.json](native-attribute-map.json) ma51nazw i indeksów dowiedzionych w parserze, m.in.Finishing0x1B,Passing0x20,Positioning0x2E,Acceleration0x3C,Pace0x40,Jumping0x41,Reflexes0x2F,Handling0x24. Brak liczbowejwagi nie podważa mapy nazw, ale uniemożliwia podanie np.„+1Finishing kosztujeXCA”.

Szczególne gałęzie indeksów50/51 przy zerowym B podstawiają5, z wyjątkami zależnymi od wartości100obu tychpól. To istotny trop kosztu słabszejnogi. Dopóki nie zostanie domknięty nazwany getter obu nóg i DAT↔runtime, dokładna etykieta każdego ztychdwóchindeksów pozostaje osobnym zadaniem. Zmiana poziomu nogi może zmienić samąwagę przez próg100; dlatego model kompensacji nie powinien teraz zmieniać nóg ani pozycji.

## Funkcja oceny atrybutów i właściwa normalizacja

D23F00 przy fladze0 liczy M=Σ(v_j*x_j)/Σv_j z surowychbajtów, a dla niepozytywnego mianownika zwraca0. Przy innych flagach wagi do mianownika są dodawane przed ewentualnym pominięciem licznika. Nie wolno opisywać tego jako ponownej średniej tylko po przefiltrowanych cechach.

D23AA0 zwraca6+0.05*CA. A7A860 mnoży to przez5, zatem jego cel w jednostkach wewnętrznych to:

```
T = 30 + clamp(CA,1,200)/4
```

PrzykładyCA1/100/200 dająT30.25/55/80. To cel funkcji oceny, nie nakaz równej wartości każdej cechy i nie ograniczenie pojedynczejcechy do16widocznych punktów.

Dekompilator zgubił ciałoFPU istotnych pętliA7A860. Odtworzone z ASM A7A91B..A7AA59 równanie, dla W=Σv_j i nliczby niezerowychv:

```
h = 3.75*W/n
q_j = 0.2*v_j*(x_j-T)
soft(q,h) = max(q-h,0) + min(q+h,0)
Q = [Σ(v_j*x_j) + 3.75*Σsoft(q_j,h)] / W
```

To dodatkowa korekta skrajności, więc zachowanie samej Σ(v*x) nie gwarantuje zachowaniaQ. Odtworzenie ma status statyczny ASM; pełny port iteratora z różnicową weryfikacją jeszcze niepowstał. W sąsiednich obszarach obowiązuje inny koszt krańcowy: poza pasmem soft współczynnik względem surowego x wynosi1.75*v/W, wśrodku v/W; przy przekroczeniu progu trzeba policzyć pełnąróżnicę. To jednostki wynikuQ, nie wprost całkowitepunktyCA.

Normalizator zaokrągla różnicęT−Q z połówkami odzera, ogranicza krok początkowo do±5jednostekwewnętrznych, później do±1. Ma wygaszanie oscylacji i wybór podzbioru, limit1000iteracji,clampzmienianych atrybutów1..100. Dla przecięcia predykatówAD13C0 iAD1560 krok jest dzielony całkowitoliczbowo przez2; dowiedzione indeksyto0x25,0x3C,0x40,0x44,0x48. Są toAerialAbility,Acceleration,Pace,Balance,Agility wedługmapyparsera. Przy kroku±1 taki półkrok daje0. Jest to tempo korekty, nie osobna „połowawagiCA”.

Nie ma gwarancji dokładnieQ=T po każdymprzebiegu: istnieje zaokrąglonykrok0,clampy,oscylacje i limit. Warunek pracy na tym samymCA/PA jest mocniejszy od zachowania dwóch pól w pamięci: trzeba też sprawdzić, czy kolejna normalizacja nie zmienia nowegoprofilu.

## Cechy bez bezpośredniego kosztu

Dla danej, zamrożonej konfiguracji pozycji/nóg:v_j=0 oznacza zerowy wkład w D23F00 i A7A860; obejmuje to także w_j<=1, ponieważ drugi współczynnik pozostaje0. Ten fakt nie daje jeszcze globalnej listy nazwbez kosztu, bo brakujeB. Indeksy0..24 mają w tym modelu0wag, ale pośrednio sterują wszystkimi innymi wagami, więc nie są darmowym źródłemkompensacji.

Ambicja,Profesjonalizm i pozostała osobowośćPERSON są w osobnym payloadzie; omawiane funkcjeoceny/normalizacji ich nieczytają. To brak bezpośredniegokosztu w tychfunkcjach, nie brak wpływu na dalszyrozwój. Determinacja jest innym polem PLAYER0x4D; nie wolno zaliczać jejdoosobowości beztegodystynkcji ani twierdzić,że ma0koszt, dopókibazaB niejestsprawdzona. RównieżConsistencymożebyćukryta, lecz parsermajejindeks; „ukryte” niejestdowodem zerowejwagi.

Obniżenie cechy nieistotnej dlaGenie/roli, lecz natywnie bezkosztowej, niepłaci zaFinishing lubPace. ZmniejszanieProfesjonalizmu zmieniałobyrozwój, zamiastrozliczaćtenbudżet.

## PA oraz pochodzenie początkowegoCA

CB1840 nadaje początkoweCA z przedziałów klubowychC63F90,PA i RNG, z dolnymzabezpieczeniem1. Istnieje bramkaPA>=151 lubR(250)<PA²/200 prowadząca do innejgałęzi. Nie jest to wyliczenieCA zjużgotowych atrybutów. JakośćklubuC63E90 czyta reputację pierwszegoTEAM iCLUB+E1/+E0; nie liczybezpośredniobudżetusalda. Szczegółowe zależne odtrybu przedziały zachowano w evidence, nieuproszczonodo„jednaformułaligi”.

CB1350 respektuje prawidłowe istniejącePA, przy brakach wybiera nowewartości, z klubem przezC64270; kraj/tryb i jakośćklubutworzą kontekst losowania. Wiekwpływana profilegeneracyjne i dalszyrozwój; niezamknięto jednejuniwersalnejformułyPA z wieku,reputacji i kraju. WynikPA niejestzużywanym podczasrozwoju portfelem.

C80440 rozwija kategorie:−10→[170,200),−9→[150,180),−8→[130,160),−7→[110,140),−6→[90,120),−5→[70,100),−4→[50,80),−3→[30,60),−2→[10,40),−1→[1,20), jeśliCA niepodnosi dolnejgranicy. Górna granica jest wyłączona:helperR(n) daje0..n−1. Helperprzedziałowy sortujekońce, zatemnietypoweCA ponadgórnymkońcem wymaga rozpatrzeniadalszejfinalizacji.

Dla−10pierwszywynik>=190powoduje dokładniejednoponowienielosowania; niepętlędoPA<190. PrzyCA<=170prawdopodobieństwokońcowego190..199wynosi1/9. WCB3000PAjestpodnoszonedoCA iograniczonedo1..200;warunkowe2×/3×CA mająnadalniepotwierdzoneetykietyopcji. MiesięcznaaktualizacjaograniczaCAdoPA, a nieodejmujePA za wzrostCA. NieudowodnionoglobalnejniezmiennościPAwewszystkichścieżkach; naszDynamicPAlaunchera jest osobną, jawnie zmieniającąPAregułą, nieoryginalnymkosztematrybutu.

## Konsekwencje dla losowych+1/+2

Genie PositionAttributeWeights.csv może wybieraćpreferowanecechy wedługzaakceptowanychprogów>=60 i20..59, ale niepłacićnimi zanatywnybudżet. Scale,CA,Normalization_denominator to metadane. Pola21−attribute mająodwrotnykierunekpreferencji; niekażda ważnacecha powinnadostawaćdodatnibonusliczbowy.

Przyszłypolicy powinien braćnowąosobępopełnejgeneracji/początkowymtreningu,zachowaćCA,PA,pozycje,nogi iresztętożsamości,losowaćpreferencje ipróbowaćrozwiązaćbilansQ. Dla+1/+2widocznychpunktównajpierw przeliczyćdokładnązmianęsurowychwartości włączniezzaokrągleniem.Nietworzyćklonów przezjednakowecele;stosowaćodtwarzalnyprywatnyseed iodrzucanieniewykonalnychpropozycji.Zerowekosztyniepokrywajądodatnichkosztów.

Nawetprzyznanychvprosta dwustatowawymianamożenieistnieć:przykładowe,syntetycznev15 i55 wymagająza+5rawpierwszejcechy−15/11rawdrugiej.Wagiwtymprzykładziesątestowymkontrprzykładem,nieustaleniemoFinishing/Pace wFM08.Nieliniowytestweryfikacyjny pokazujeteżdwaprofile z identycznąΣ(v*x), lecz innymQ.

Przedwdrożeniemwymagane:pełneB iźródłowebajty;domkniętyportFPU/iteratora;różnicowetestycałejskaliCA,pojedynczych iwielupozycji,GK/pole,obu nóg,brzegów1/20/100,zerowychwag i progówsoft;zachowanieresztypayloadu iCA/PA;jednorazowośćtylko nowejosoby;osobnytestzapis/odczyt ikolejnanormalizacja/treningnaizolowanejkarierze. Żadnegointerfejsu/hooka/patchaniezainstalowano.

[offline-verification.json](offline-verification.json):PASSdla26pinówkoduiarytmetykiskali/zaokrągleń,20roundtripówsettera,kontrprzykładówkompensacji iujemnegoPA−10. To niejesttestwykonaniakoduFM,pełnykalkulatorCA aniakceptacjasezonu.Listaniewiadomychw[unresolved.json](unresolved.json).
''',encoding='utf-8')
(out/'WZNOWIENIE.md').write_text('''# Wznowienie CA/PA — 12 XI 2026

Czytaj RAPORT.md,ERRATA.md,formula-candidates.json iunresolved.json. Pierwszyprzebiegstatycznyzakończony,pełnatabelaB iportnormalizatoraniegotowe.Bezpatcha/runtime/zmianbazy.

Dowiedzione:AD2630tylko×5indeksów25..79;CA/PAosobnepola;D23AE0mieszanie15pozycji itrójkątne wagi;D23F00(flag0)ważonaśrednia;D23AA0=6+0.05CA;A7A860 cel30+CA/4 idodatkowysoftthresholdwFPU;calleryCB3541iA3608A.Dokładnykontraktiteracyjnyjestczęściowy.KompensacjaΣ(v*x)=0samaniemawystarczyć.Atrybutywewnętrzne1..100,UI1..20,zaokrąglenia i wyjątekraw1/2+5.

NastępnykrokU01:znaleźćinicjalizację/configźródłonatywnejB wglobalnymobiekcie1B1EE84;parserASM D379D0 czytapos i/attr/weig,nazwy51cechipmapaindeksówzachowane. NiepodstawiaćGenieCSV inieczytaćBSSzsurowegoEXE.U02domknąćpełnyFPUmodelA7A860 i niezależnyfixture.Ograniczyćnogipozycjejakostałe ażzamkniętaweryfikacjanazw/DAT.

fm.exeSHA256157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d,base400000;26C/ASM/binpiny i parserASM.Bezświeżejpełnejanalizy,attach,RPM,WPM,nativecalls,uruchamianiagry.NietykaćX17,R10,bazzaakceptowanych,SI,rootcheckpointów.AnalizapłacSTOP.
''',encoding='utf-8')
files=[]
for p in sorted(out.rglob('*')):
 if p.is_file():files.append({'path':str(p.relative_to(out)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())})
savej('manifest.json',{'schema':1,'status':'FIRST_STATIC_PASS_COMPLETE_SCOPE_PARTIAL','date':'2026-11-12','exe_sha256':expected,'imagebase':hex(base),'native_functions_pinned':len(selected),'native_named_indices':len(named),'runtime':'NOT_RUN','patch_implemented':False,'database_changed':False,'files':files})
print(json.dumps({'output':str(out),'files':len(files)+1,'functions':len(selected),'named_indices':len(named),'status':'PASS'},ensure_ascii=False))

