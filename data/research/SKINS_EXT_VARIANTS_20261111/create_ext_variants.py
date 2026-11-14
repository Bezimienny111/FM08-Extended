"""Create only four new inactive Ext skins; originals and game settings are read-only."""
from pathlib import Path, PureWindowsPath
import hashlib,json,struct,zlib,xml.etree.ElementTree as ET
ROOT=Path('J:/FM08dev')
SK=ROOT/'Dane/skins'
OUT=ROOT/'FmLauncher/data/research/SKINS_EXT_VARIANTS_20261111'
ARCH=Path('J:/FM08/data/skins.fmf')
SPEC=[
 ('fm2008_ext_left','Base Ext (Left)','fm2008','left',['fm2008']),
 ('fm2008_ext_right','Base Ext (Right)','fm2008','right',['fm2008']),
 ('steklo_black_ext_left','Steklo Black Ext (Left)','steklo_left_black','left',['steklo','steklo_left','steklo_left_black']),
 ('steklo_black_ext_right','Steklo Black Ext (Right)','steklo_black','right',['steklo','steklo_black'])]
assert all(not (SK/n).exists() for n,*_ in SPEC),'Do not overwrite an existing Ext skin'
def sha(b):return hashlib.sha256(b).hexdigest()
def filehash(p):return sha(p.read_bytes())
source_skins=['fm2008','steklo','steklo_black','steklo_left','steklo_left_black']
protected=sorted({p for n in source_skins for p in (SK/n).rglob('*.xml')})
protected += [ARCH,ROOT/'FmLauncher/PLAN_PANELI_ZAWODNIKA.md',ROOT/'FMExt/SKIN_ARCHITECTURE_FM08.md',ROOT/'FmLauncher/src/FmLauncher/SkinPanelInstaller.cs']
before={str(p):filehash(p) for p in protected}
data=ARCH.read_bytes()
assert len(data)>=18 and data[:6]==bytes([2,1,0x66,0x6d,0x66,0x2e])
toc_offset=struct.unpack_from('<I',data,9)[0]+18
assert toc_offset<len(data)
toc=zlib.decompress(data[toc_offset:])
assert 4<=len(toc)<=16*1024*1024
cursor=4;entries={};case_names=set()
def num(fmt):
 global cursor
 size=struct.calcsize(fmt);assert cursor+size<=len(toc)
 value=struct.unpack_from(fmt,toc,cursor)[0];cursor+=size;return value
def text():
 global cursor
 count=num('<I');assert count<=4096
 length=count*2;assert cursor+length<=len(toc)
 value=toc[cursor:cursor+length].decode('utf-16le');cursor+=length
 assert num('<H')==0
 return value
def readnode(prefix='',depth=0):
 assert depth<=32
 for _ in range(num('<H')):
  name=prefix+text()+text()
  assert not PureWindowsPath(name).is_absolute() and not PureWindowsPath(name).drive
  assert not any(p in ['.','..'] for p in name.split('\\'))
  assert name.casefold() not in case_names
  case_names.add(name.casefold())
  entries[name]=(num('<I'),num('<I'),num('<I'))
 for _ in range(num('<H')):readnode(prefix+text()+'\\',depth+1)
readnode();assert cursor==len(toc)
def getmember(name):
 offset,stored,length=entries[name];offset+=9
 assert length<=8*1024*1024 and offset<=len(data)-stored
 result=data[offset:offset+stored]
 if stored!=length:result=zlib.decompress(result)
 assert len(result)==length
 return result
official_right={name:getmember(name) for name in entries if name.startswith('fm2008_r\\')}
assert len(official_right)==3
for raw in official_right.values():ET.fromstring(raw)
OUT.mkdir(parents=True,exist_ok=True)
def writejson(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
copies=[];validation=[];result_skins=[]
features=['person list table.xml','player training.xml','team squad.xml','tactic person list.xml']
for name,label,parent,side,chain in SPEC:
 dest=SK/name
 # Resolve only normal resource XML. Parent artwork remains inherited.
 winning={}
 for srcname in chain:
  for category in ['panels','settings','screens']:
   folder=SK/srcname/category
   if folder.exists():
    for src in sorted(folder.rglob('*.xml')):
     if ' - Copy' in src.name or src.name.endswith('.bak.xml'):continue
     winning[src.relative_to(SK/srcname).as_posix()]=(src.read_bytes(),str(src))
 if name=='fm2008_ext_right':
  for member,raw in official_right.items():
   if '\\panels\\' in member:
    winning[member.split('\\',1)[1].replace('\\','/')]=(raw,str(ARCH)+'::'+member)
 dest.mkdir()
 for rel,(raw,origin) in winning.items():
  ET.fromstring(raw)
  target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
  copies.append({'skin':name,'target':str(target),'source':origin,'sha256':sha(raw),'byte_identical':True})
 # Clone metadata so its font and visual declarations remain local.
 original=SK/parent/(parent+'.xml')
 meta=ET.parse(original).getroot()
 def setting(tag,key,value):
  el=next((e for e in meta if e.attrib.get('id')==key),None)
  if el is None:el=ET.SubElement(meta,tag,{'id':key})
  el.set('value',value)
 setting('string','name',label)
 setting('string','author',('Sports Interactive' if parent=='fm2008' else 'TomDixon77')+' / FMExt')
 setting('string','description','FMExt '+side+' variant; independent panels; original artwork inherited.')
 setting('string','version','0.1.2')
 setting('string','required_version','8.0.2')
 setting('flags','parent',parent)
 payload=b'<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(meta,encoding='utf-8')+b'\n'
 (dest/(name+'.xml')).write_bytes(payload)
 globalxml=ET.parse(dest/'panels/global panels.xml').getroot()
 if name.startswith('fm2008'):
  proof=next(e.attrib for e in globalxml.findall(".//*[@id='main']/layout") if e.attrib.get('class')=='arrange_horizontal_attachment')
 else:
  proof=next(e.attrib for e in globalxml.findall(".//*[@id='sect']/layout") if e.attrib.get('class')=='stick_to_sides_attachment' and e.attrib.get('alignment') in ['left','right'])
 assert proof['alignment'].split(',')[0].strip()==side,(name,proof)
 # Resolve parent graph from actual metadata, not assumed folder names.
 hierarchy=[name];cur=parent
 while cur:
  assert cur not in hierarchy,'Skin inheritance cycle'
  hierarchy.append(cur)
  m=ET.parse(SK/cur/(cur+'.xml')).getroot()
  parents=[e.attrib['value'] for e in m if e.attrib.get('id')=='parent']
  assert len(parents)<=1
  cur=parents[0] if parents else None
 parsed=0
 for p in dest.rglob('*.xml'):ET.parse(p);parsed+=1
 for filename in features:
  assert (dest/'panels'/filename).exists()
 assert b'Fmjd' in (dest/'panels/player training.xml').read_bytes()
 assert b'Fjad' in (dest/'panels/team squad.xml').read_bytes()
 assert b'Fcab' in (dest/'panels/team squad.xml').read_bytes()
 assert b'Fpab' in (dest/'panels/team squad.xml').read_bytes()
 assert not any(b'Fh01' in p.read_bytes() for p in (dest/'panels').rglob('*.xml'))
 info={'folder':str(dest),'name':label,'id':name,'version':'0.1.2','required_version':'8.0.2','parent_chain':hierarchy,'side':side,'orientation_xml':str(dest/'panels/global panels.xml'),'orientation_element':proof,'local_xml_files':parsed,'runtime':'NOT_TESTED','active_skin_unchanged':True}
 validation.append(info);result_skins.append(info)
after={str(p):filehash(p) for p in protected}
assert before==after,'Unexpected source mutation'
writejson(OUT/'source-hashes-before-after.json',{'all_equal':before==after,'files':before})
writejson(OUT/'resource-copy-provenance.json',copies)
writejson(OUT/'static-validation.json',{'status':'PASS','skins':validation,'original_source_xml_and_archives_unchanged':True,'source_files_checked':len(before),'no_game_start_or_preferences_changes':True,'no_hooks_added':True,'experimental_dev_not_used':True,'xml_parser':'Python ElementTree; no DTD fetch'})
writejson(OUT/'official-fmf-index.json',{'path':str(ARCH),'sha256':filehash(ARCH),'reader_origin':'SkinPanelInstaller.cs FmfArchive, TOC+18, data+9, UTF-16LE, zlib','toc_offset':toc_offset,'entries':[{'name':k,'offset':v[0],'stored':v[1],'length':v[2]} for k,v in entries.items()],'right_members_sha256':{k:sha(v) for k,v in official_right.items()}})
report="""# Cztery skórki Ext — 11.11.2026

Utworzono cztery osobne, nieaktywowane skórki w wersji 0.1.2 dla FM 8.0.2. Statyczna walidacja XML, metadanych, dziedziczenia, orientacji i kopii paneli: PASS. Wybór i wygląd w działającej grze: NIE TESTOWANO. Nie zmieniono ustawień gry, cache ani wybranej skórki. Nie uruchamiano instalatora paneli ani nowych hooków.

| Folder w Dane/skins | Nazwa w grze | Rodzic / orientacja |
|---|---|---|
| fm2008_ext_left | Base Ext (Left) | fm2008; lewa |
| fm2008_ext_right | Base Ext (Right) | fm2008; prawa z oficjalnego fm2008_r |
| steklo_black_ext_left | Steklo Black Ext (Left) | steklo_left_black → steklo_left → steklo; lewa |
| steklo_black_ext_right | Steklo Black Ext (Right) | steklo_black → steklo; prawa |

Każdy folder zawiera własne XML paneli, ustawień i ekranów, które występują w jego efektywnym łańcuchu źródeł; późniejsze nadpisania rodzica mają pierwszeństwo. Grafika, fonty i zasoby spoza lokalnych XML dziedziczą dotychczasowe skórki. Oryginalne foldery rodziców muszą pozostać dostępne. Przyszłe zmiany paneli wykonujemy w folderach Ext. Nie kopiowano eksperymentalnego steklo_black_dev ani backupów „settings - Copy”.

## Pochodzenie i dowód Left/Right

Base Left: lokalne fm2008, 11 paneli, w global panels.xml kontener main ma arrange_horizontal_attachment alignment=\"left, extend\". Base Right: te same lokalne panele z dwiema oryginalnymi nadpisującymi definicjami global panels.xml oraz sections.xml z J:/FM08/data/skins.fmf, gałąź fm2008_r. Oficjalne metadane tej gałęzi potwierdzają parent=fm2008 i „Right sided version”; układ main ma alignment=\"right, extend\". Nie odgadywano układu ani nie zmieniano samodzielnie pojedynczego atrybutu.

Steklo Right: skuteczny łańcuch steklo → steklo_black; kontener sect w global panels.xml ma stick_to_sides_attachment alignment=\"right\". Left: steklo → steklo_left → steklo_left_black; ten sam kontener ma alignment=\"left\". Skopiowano też właściwe nadpisania screens/match.xml i paneli nagłówka/sterowania, zachowując pozostałą grafikę przez dziedziczenie.

Odczyt FMF odwzorowuje istniejący FmfArchive w SkinPanelInstaller.cs: sygnatura, TOC na uint32[9]+18, dane na offset+9, UTF-16LE z terminatorem, zlib, granice, unikalność ścieżek i zakaz traversal. Odczytano 12 członków archiwum, w tym trzy fm2008_r. Nie uruchamiano starego prototypu parse_fmf.py ani nie przepakowywano archiwum.

SHA-256 źródeł i niezmienność oryginalnych XML zawiera source-hashes-before-after.json; źródło i hash każdej kopii wskazuje resource-copy-provenance.json. static-validation.json zawiera konkretne elementy XML potwierdzające orientację. manifest.json wylicza pliki nowych skórek.

## Elementy do skórek: stan i dalszy plan

| Element | Rzeczywisty stan | Co przygotowano w Ext / dalszy krok |
|---|---|---|
| Zmęczenie sezonowe (jadedness), trening | Istnieją kod GamePanelPatch i kontrolka Fmjd. Użytkownik potwierdził tekst w treningu. Tooltip Fjht opisuje poziomy oraz karę do jednego mnożnika treningu. | Zachowano bieżący panel, bez nowego odczytu. Działa przez istniejący moduł launchera, samo XML go nie włącza. |
| Zmęczenie w składzie i taktyce | Istnieją właściwość Fjad, rejestr kolumn i formatter. Użytkownik potwierdził teksty; niektóre odświeżenia składu pokazują jeszcze surową liczbę. Zaakceptowany obejściowy krok: zmienić widok i wrócić. | Własne kopie team squad.xml, tactic person list.xml i person list table.xml. Pełna pewność każdego odświeżenia nadal nieosiągnięta; nowych czterech skórek nie testowano wizualnie. |
| Surowe CA/PA | Istnieją Fcab/Fpab. Moduł udostępnia dane wyłącznie dla aktualnego klubu aktywnego ludzkiego menedżera; obejmuje własne rezerwy wspólnego CLUB i wypożyczonych do nas, nie osobne afiliacje ani wypożyczonych od nas. Brak dostępu daje ----. | Zachowane istniejące kolumny i widok Edycja. Nie rozszerzano zakresu dostępu; asystenckie oceny i natywne Pcab/Ppab nie są równoznaczne z surowym CA/PA. |
| Pozycja: wyróżnianie atrybutów | PLAN w PLAN_PANELI_ZAWODNIKA.md. Wybór roli/pozycji i wyróżnianie etykiet/tła, bez podmiany kolorów wartości i bez oceny 0–100. | Nie wdrożono. Przyszły wspólny projekt na czterech Ext, wymagający implementacji i testów odświeżania. |
| Ukryte cechy w profilu zawodnika | PLAN: m.in. regularność, ważne mecze, podatność na kontuzje, profesjonalizm i cechy osobowości. Stary Dev zawiera wyłącznie prototyp układu, nie gotowe odczyty. | Nie kopiowano Fh01–Fh12 ani eksperymentalnych paneli. Potrzebne rozstrzygnięcie pól PERSON/PLAYER, uprawnień, braków i unieważniania danych przy zmianie gracza. |
| Reakcja na rozmowę motywacyjną | ODŁOŻONE decyzją użytkownika 10.11.2026. Docelowo po zatwierdzeniu i faktycznym przetworzeniu rozmowy, gdy połowa trwa i rozmowa jest zablokowana: pozytywna/neutralna/negatywna, zależnie od udowodnionych flag. Brak odczytu nie oznacza reakcji neutralnej. | Brak wdrożenia UI/parsera/hooka. Nie odblokowano tego zadania. Reakcja nie jest gwarancją późniejszego występu; rzeczywista liczba stanów wymaga osobnego rozstrzygnięcia. |
| Efektywność treningu teff / maksymalny bezpieczny workload mswl | HISTORYCZNY KONCEPT z wcześniejszej architektury. Nie ma gotowych właściwości danych, a dodanie widgetu nie tworzy danych. Kara J 0–40% dotyczy pojedynczego mnożnika, nie całkowitej efektywności. | Nie dodano atrap ani nowych wartości. Osobna analiza silnika oraz implementacja i testy byłyby konieczne. |

Dokumenty źródłowe przeczytane: FmLauncher/PLAN_PANELI_ZAWODNIKA.md, FMExt/SKIN_ARCHITECTURE_FM08.md (w szczególności aktualizacje 13–14), SkinPanelInstaller.cs oraz rzeczywiste XML lokalnych skórek i archiwum SI. Historyczne ścieżki D: w starszych dokumentach nie są bieżącym miejscem instalacji.

## Test w grze do wykonania osobno

Po ukończeniu bieżącego testu gry można wybrać każdą z czterech nazw w Preferencjach → skórka. Jeżeli lista jest zcache'owana, odświeżyć ją zgodnie z dotychczasową instrukcją FM08, dopiero gdy użytkownik zdecyduje się na ten test. Sprawdzić stronę menu, nagłówek, ekran meczu, trening, skład i taktykę, a także poprawne wyświetlanie grafik rodzica. Dla istniejących danych rozszerzonych użyć startu launchera z włączonym modułem paneli i własnego klubu; obcy klub ma nadal pokazywać brak dostępu. Nie traktować poprawnego XML jako potwierdzenia wizualnego.

Zadanie nie zmienia silnika, launcherowych ustawień, aktualnej bazy ani aktywnej kariery. Runtime wszystkich czterech wariantów pozostaje NOT_TESTED.
"""
(OUT/'RAPORT.md').write_text(report,encoding='utf-8')
(OUT/'WZNOWIENIE.md').write_text("""# Wznowienie — skórki Ext 11.11.2026
Utworzone: Dane/skins/fm2008_ext_left, fm2008_ext_right, steklo_black_ext_left, steklo_black_ext_right. Każda ma metadata0.1.2, required_version8.0.2, własne XML paneli oraz odpowiednie lokalne screens/settings dostępne w źródłach. Base Right pochodzi z oficjalnego fm2008_r w skins.fmf. Grafika dziedziczona; oryginalne parenty pozostawić.
Statycznie PASS; w grze NOT_TESTED. Nie przełączano skórki, nie resetowano cache, nie uruchamiano instalatora/hooków. Oryginalne źródła niezmienione.
W RAPORT.md osobny backlog: istniejące fatigue/CA/PA, plan Pozycja i hidden attributes, ODŁOŻONE rozmowy motywacyjne, teff/mswl tylko dawny koncept. Nie kopiować paneli Dev jako gotowych funkcji.
Dalszy krok: użytkownik osobno wybiera i sprawdza4 nazwy w grze; przyszłe zmiany tylko w nowych Ext. Manifest/proweniencja i static-validation zawierają ślad.
""",encoding='utf-8')
manifest={'date':'2026-11-11','scope':'Four separate inactive skin variants only','version':'0.1.2','runtime':'NOT_TESTED','skins':result_skins,'files':[]}
for name,*_ in SPEC:
 for p in sorted((SK/name).rglob('*')):
  if p.is_file():manifest['files'].append({'path':str(p),'size':p.stat().st_size,'sha256':filehash(p)})
writejson(OUT/'manifest.json',manifest)
print(json.dumps({'status':'PASS','new_skins':[(s['id'],s['local_xml_files']) for s in result_skins],'original_sources_unchanged':len(before),'new_files':len(manifest['files']),'report':str(OUT/'RAPORT.md')},ensure_ascii=False))
