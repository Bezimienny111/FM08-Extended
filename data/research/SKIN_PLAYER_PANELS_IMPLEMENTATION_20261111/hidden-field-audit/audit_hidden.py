from pathlib import Path
import struct,json,hashlib,csv
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
ROOT=Path('J:/FM08dev');O=ROOT/'FmLauncher/data/research/SKIN_PLAYER_PANELS_IMPLEMENTATION_20261111/hidden-field-audit';O.mkdir(exist_ok=True)
source=ROOT/'fm.exe';data=source.read_bytes();h=hashlib.sha256(data).hexdigest();assert h=='157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d'
pe=pefile.PE(data=data);base=pe.OPTIONAL_HEADER.ImageBase;cs=Cs(CS_ARCH_X86,CS_MODE_32)
def raw(a,n):return data[pe.get_offset_from_rva(a-base):][:n]
def u32(a):return struct.unpack('<I',raw(a,4))[0]
def pin(a,n,why):
 b=raw(a,n);assert len(b)==n
 return dict(address=hex(a),file_offset=pe.get_offset_from_rva(a-base),size=n,purpose=why,bytes=b.hex(),sha256=hashlib.sha256(b).hexdigest(),instructions=[dict(address=hex(i.address),mnemonic=i.mnemonic,operands=i.op_str)for i in cs.disasm(b,a)])
snippets=[pin(0xcae280,0x96,'Generic PLAYER getter, source-order(selector,scaleTo20,clampRaw100), ret0xC; rawreturnAL'),pin(0xcae320,0x75,'Independent native setter scale flag multiplies1..20by5 outside selectors0..24'),pin(0xad15f0,0x20,'Classifier0..24direct1..20; others1..100'),pin(0xad1990,0x28,'Clamp raw0..100 helper, not missing validator'),pin(0x112f26c,0x75,'Native float-to-int correction afterFISTP; not Pythonround'),pin(0xcae480,0x58,'Injury(0) routes selector4A,1,0; nonzero adds conditioning modifier'),pin(0xc81a90,0x10,'Candidate eighth PERSON field, semantics unresolved'),pin(0xcbab90,14,'Virtual PERSON thunk slot238'),pin(0xcbab10,0x26,'PERSONslot220 routes PLAYERselector4D Determination, not controversy')]
names={};proofs={};a=0xd37700;code=raw(a,0xc00)
for i in range(len(code)-35):
 if code[i:i+3]!=b'\x6a\x01\x68':continue
 p=struct.unpack_from('<I',code,i+3)[0]
 if not 0x1140000<=p<0x1700000:continue
 pos=code.find(b'\xc6\x44\x24\x04',i+7,min(i+35,len(code)))
 if pos<0:continue
 call=code.find(b'\xe8',i+7,pos)
 if call<0 or a+call+5+struct.unpack_from('<i',code,call+1)[0]!=0xf4dbf0:continue
 name=raw(p,300).split(b'\0')[0].decode('ascii');sel=code[pos+4];names[sel]=name
 proofs[sel]=dict(name=name,selector=sel,selector_hex=hex(sel),label_address=hex(p),label_bytes=raw(p,len(name)+1).hex(),branch_address=hex(a+i),selector_write_address=hex(a+pos),matcher='0xF4DBF0')
fields=[]
assert u32(0x15ab414+0x18)==0xcae280
for name,custom,sel in [('Consistency','Fh01',0x46),('Important Matches','Fh05',0x49),('Dirtiness','Fh09',0x43),('Injury Proneness','Fh07',0x4a)]:
 assert names[sel]==name
 snippets.append(pin(int(proofs[sel]['branch_address'],16),30,'Exact native name=>selector: '+name))
 fields.append(dict(name=name,custom_property=custom,status='statically_named_selector_and_runtime_ABI_bound',semantic_proof=proofs[sel],PLAYER_vtable='0x15AB414',virtual_slot='0x18',vtable_entry_bytes=raw(0x15ab414+0x18,4).hex(),getter='0xCAE280',raw_runtime_expression='*(validated_PLAYER_core+0xCC)+0x1C+selector',raw_type='signed byte; valid1..100',scale_type='native1..20',raw_call='ECX=PLAYERcore; push0;push0;pushSelector;call[vt+18];movsxEAX,AL',display_call='Only after signedraw1..100 check: push0;push1;pushSelector;call[vt+18];movsxEAX,AL;validate1..20',stack_cleanup='callee ret0xC',missing_policy='null/unreadable pointer or raw<=0 or>100 =>missing; NEVER allow native clamp to turn invalid raw into displayed1/20',scale_proof='CAE280 native (raw+2)*float0.2 ->112F26C ->clamp1..20; independent setterCAE320 multiplies by5 on scaled write',serialized_name_to_runtime_proof='not reconstructed; exact named enum parser and getter/setter are proved separately',runtime_fixture='not run by this agent'))
assert u32(0x15ab12c+0x238)==0xcbab90
contro=dict(name='Controversy',custom_property='Fh12',status='UNRESOLVED_SEMANTIC_NAME_DO_NOT_ENABLE',PERSON_vtable='0x15AB12C',slot='0x238',entry_bytes=raw(0x15ab12c+0x238,4).hex(),thunk='0xCBAB90',getter='0xC81A90',candidate_read='signed byte+0x23 through data pointer at canonical getter this−0x40; null=>0',known='Exact vtable/thunk/getter only; no proof naming this field Controversy',unknown='Need named enum/event or independent serialized personality mapping; neighbor order is insufficient',wrong_alternative='PERSONslot220 is Determination via PLAYERselector4D',virtual_base_policy='Use native RTTI/vbtable; never hardcode ACTUAL_PLAYER+EC')
visible=[]
for idx in range(47):
 entry=0xcae760+idx*4;branch=u32(entry);b=raw(branch,13)
 assert b[:6]==b'\x8b\x01\xc7\x44\x24\x04'and b[10:]==b'\xff\x60\x18'
 sel=struct.unpack_from('<I',b,6)[0]
 visible.append(dict(native_attribute_enum=idx,selector=sel,selector_hex=hex(sel),name=names.get(sel,''),name_proof='named_parser'if sel in names else'not_bound_here',jump_table_entry=hex(entry),branch=hex(branch),branch_bytes=b.hex(),TABLE_row_order_proved=False))
abi=dict(this='validated PLAYERcore inECX',arguments_source_order=['selector','scaleTo20','clampRaw100'],push_order=['clampRaw100','scaleTo20','selector'],callee_cleanup=12,return_width='AL on raw path; sign extend explicitly',factor_address='0x129ECD4',factor_bytes=raw(0x129ecd4,4).hex(),factor=struct.unpack('<f',raw(0x129ecd4,4))[0],invalid_order='raw flags0/0 =>signed1..100 check =>scaled flags1/0 =>1..20 check',allowed_core_classes='ACTUAL_PLAYER/PLAYER_STAFF via native RTTI and allowed class gates')
e=dict(source_binary=str(source),sha256=h,method='Existing R5 plus independent original PE/capstone; no binary upgrade or game mutation',fields=fields,controversy=contro,raw_abi=abi,visible_attribute_remap=visible,snippets=snippets,REA=dict(attempt='open_binary fm.exe provider_id=kuna',result='capability_unavailable; Kuna not configured and does not admit PE here',active_session_created=False,fallback='Existing GHIDRA_ENGINE_20261107_R5 and raw shipped PE; no install/configuration changes'),limits=['No fixture/runtime execution by this agent','No active game attach/pause/hook/injection','No code/XML/config/DB changes','Controversy semantics remain unresolved','No independent full loader/serializer mapping recovered','Enum map0..46 does NOT prove TABLE row order'])
(O/'evidence.json').write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with(O/'visible-attribute-enum-map.csv').open('w',encoding='utf-8-sig',newline='')as f:
 w=csv.DictWriter(f,fieldnames=list(visible[0]));w.writeheader();w.writerows(visible)
report='''# Ukryte cechy — odczyty statyczne, 11 XI 2026

Potwierdzone dokładne nazwy i selektory: **Consistency 0x46; Important Matches 0x49; Dirtiness 0x43**. Osobno tą samą metodą potwierdzono Injury Proneness 0x4A. Controversy nadal nie ma wystarczającego semantycznego dowodu; nie włączać go na podstawie tego raportu.

Oryginalny fm.exe ma SHA256 157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d. Native matcher F4DBF0 porównuje dokładne napisy, a gałąź zapisuje selector: Consistency label1585CCC/writeD37DD1; Important Matches1585CA4/D37E49; Dirtiness1585D08/D37E0D; Injury Proneness1585C90/D37AC5. Pełne bajty, adresy, hashe i instrukcje: evidence.json.

## ABI i skala — obowiązkowa kontrola raw

ACTUAL_PLAYER vtable15AB414, slot18 wskazuje CAE280. __thiscall: ECX=zweryfikowany PLAYERcore, argumenty(selector,scaleTo20,clampRaw100), push w odwrotnej kolejności, callee ret0xC. Raw path zwraca AL; górne bityEAX nie są znormalizowane. Należy użyć signedbyteextension.

AD15F0 odróżnia selektory0..24 o bezpośredniej skali1..20. Cztery badane selektory są poza tym zakresem i mają runtime1..100. Getter flags1/0 liczy (raw+2)*float0.2 przez natywny112F26C i potem clamp1..20. Native setterCAE320 niezależnie pokazuje mnożenie przez5 przy zapisie wartości1..20. Nie zastępować natywnej konwersji Pythonround; helper koryguje wynikFISTP do konwersji całkowitej.

**Najpierw raw flags0/0, signedraw1..100; dopiero następnie flags1/0 i wynik1..20.** Natywny getter sam maskuje raw0 lub>100 przez wynik1/20. Bez prewalidacji byłaby to fałszywa cecha zamiast missing. Null, nieczytelny wskaźnik, wartości ujemne/0/>100 oznaczają brak. Wrapper nie dodaje własnego clamp.

Injury4A może użyć tej samej metody. CAE480(0) dokładnie kieruje do(4A,1,0), a wariant niezerowy uwzględnia dodatkowo kondycję. Żadnego offsetu89B zDB nie przeniesiono wprost do obiektu runtime.

## Controversy pozostaje nieustalone

PERSON vtable15AB12C, slot238 → CBAB90 → C81A90; odczyt signedbyte+23 ze wskaźnika danych względem kanonicznego this−40, null=>0. To dowód pola i ABI, nie nazwy. Nie odtworzono bezpośredniego Controversy→slot238 ani niezależnego mapowania nazwanej cechy z17BrekorduDB do tego pola. Sąsiedztwo siedmiu znanych cech i użycie w zachowaniach społecznych nie wystarcza.

PERSONslot220 jest błędną alternatywą: CBAB10→CBAB20 prowadzi do PLAYERselector4D, czyliDetermination. Native thunk korzysta z vtordisp; nie wolno uniwersalnie dodawać ACTUAL_PLAYER+EC.

## Pomocnicza mapa widocznych atrybutów

CAE4E0 i jumptableCAE760 mapują47wejściowych kodów0..46 na selektoryPLAYER. Wszystkie47gałęzi zapisano w visible-attribute-enum-map.csv, z bajtami i nazwą tam, gdzie dowiódł jej parser. Kod30→4D pozostawiono bez nowego przypisania nazwy w tej mapie; Determination ma osobny dowódroota. Ta mapa NIE dowodzi kolejności wierszyTABLE aniIDetykiet i nie może sama sterować indeksem kontrolki.

## Metoda i granice

Przeczytano reverse-engineer-anything i native-and-artifacts. REA/Kuna odmówiło tegoPE: provider nie jest skonfigurowany i nie obsługujePEw tej rejestracji. Nie instalowano narzędzi. Użyto istniejącego R5 i niezależnego odczytu oryginalnego PE/Capstone; bez nowego projektuGhidra i bez przypisywania nieznanego wejścia do najbliższej wcześniejszej funkcji.

To dowody statyczne. Fixture i rzeczywista integracja pozostają po stronie agenta wdrożenia. Nie odtworzono pełnego niezależnego loadera/serializera: nie należy deklarować takiego wyniku. Nie zmieniono C#, XML, konfiguracji, bazy ani aktywnej gry.
'''
(O/'RAPORT.md').write_text(report,encoding='utf-8')
print(json.dumps({'fields':[(x['name'],x['semantic_proof']['selector_hex'])for x in fields],'controversy':'unresolved','visible_rows':47,'visible_named':sum(bool(x['name'])for x in visible),'out':str(O)},ensure_ascii=True))
