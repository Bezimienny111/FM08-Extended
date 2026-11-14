"""Audit and document three verified supplemental entry points, preserving the baseline export."""
import csv,hashlib,json,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'FmLauncher/data/research/GHIDRA_ENGINE_20261107_R5';REPO=ROOT/'FM08-Database-Tools'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
audit=load(OUT/'audit.json');report=load(OUT/'supplemental/recovery-result.json');assert report['status']=='supplemental_entries_exported' and len(report['entries'])==3
assert sha(ROOT/'fm.exe')==sha(OUT/'input/fm.exe')==report['source_sha256']==audit['source_sha256']
for rel,digest in audit['project_hashes'].items():assert sha(OUT/'project'/rel)==digest,'Baseline project changed'
expected={'00e90740':['0x1fa17'],'00e8f660':['0x1fa16','0x1fa18'],'00dd2010':['0x6e746d73','0x6e726473']}
new=[];warning_functions=0
for row in report['entries']:
 p=OUT/row['path'];assert sha(p)==row['sha256'];text=p.read_text(encoding='utf-8');assert len(text)>500 and row['entry_prefix_verified']
 assert all(token in text.lower() for token in expected[row['address']]),'Expected native rule constants absent'
 if 'WARNING:' in text:warning_functions+=1
 new.append(dict(label=row['label'],research_address=hex(int(row['address'],16)),function_entry='ram:'+row['address'],exact_function_entry=True,status='written',path=row['path'],name=row['name'],origin='explicit_verified_entry_in_separate_project'))
project_files=[p for p in (OUT/'project-research').rglob('*') if p.is_file()]
supplemental_audit=dict(status='verified',source_sha256=report['source_sha256'],new_functions=3,functions_before=report['functions_before'],functions_after=report['functions_after'],original_project_hashes_unchanged=True,entry_prefixes_verified=True,expected_rule_constants_verified=True,functions_with_WARNING_comments=warning_functions,entries=report['entries'],project_hashes={str(p.relative_to(OUT/'project-research')):sha(p) for p in project_files})
save(OUT/'supplemental/audit.json',supplemental_audit)
mapping=load(OUT/'research-map.json');assert len(mapping)==21;mapping.extend(new);save(OUT/'research-map.json',mapping)
p=OUT/'RESEARCH_MAP.md';text=p.read_text(encoding='utf-8')
for row in new:
 address='0x'+format(int(row['research_address'],16),'08X');old='| `'+address+'` | brak jednoznacznego wpisu | projekt/ASM |';replacement='| `'+address+'` | `'+row['name']+'` | [C]('+row['path']+') |';assert old in text;text=text.replace(old,replacement)
text+='\nTrzy funkcje research_* oznaczono jako jawne, wczesniej zweryfikowane punkty wejscia w osobnej kopii projektu project-research/. Ich nazwy sa etykietami badawczymi. Oryginalny projekt i bazowy eksport pozostaly niezmienione; supplemental/audit.json potwierdza bajty poczatkowe, hashe oraz stale regul.\n';p.write_text(text,encoding='utf-8')
index=load(OUT/'decompiled/function-index.json')
with (OUT/'function-list-all.tsv').open('x',encoding='utf-8',newline='') as f:
 w=csv.writer(f,delimiter='\t');w.writerow(['Address','Name','Status','CFile','BodyBytes','Origin'])
 for row in index['functions']:w.writerow([row['address'],row['name'],row['status'],'decompiled/'+row['path'] if row.get('path') else '',row['body_bytes'],'default_analysis'])
 for row in report['entries']:w.writerow([row['address'],row['name'],'written',row['path'],row['body_bytes'],'verified_manual_entry'])
notice='''Aktualny material obejmuje **91 123 pliki C**: 91 120 z bazowego eksportu i 3 dodatkowe, zweryfikowane punkty wejscia. Do dalszych prac zalecany jest [projekt badawczy](project-research/FM08_802_FULL_R5.gpr), ktory zawiera **91 406 funkcji**. [Laczna lista funkcji](function-list-all.tsv) oraz [mapa badawcza](RESEARCH_MAP.md) obejmuja uzupelnienie.

Bazowy, automatycznie przeanalizowany projekt i eksport pozostawiono bez zmian. Ponizsze liczniki dotycza bazowego przebiegu; [dodatkowy audyt](supplemental/audit.json) obejmuje obie polskie fabryki regul (0x00E90740, 0x00E8F660) i parser regul ligowych (0x00DD2010). Adresy poczatkowe sprawdzono wzgledem oryginalnych bajtow EXE. Nazwy research_* sa etykietami badawczymi.

'''
p=OUT/'README.md';text=p.read_text(encoding='utf-8');title,rest=text.split('\n',1);p.write_text(title+'\n\n'+notice+rest,encoding='utf-8')
result=load(OUT/'result.json');result.update(supplemental_functions=3,total_c_files=91123,research_function_count=report['functions_after'],research_project=str(OUT/'project-research/FM08_802_FULL_R5.gpr'),supplemental_audit=str(OUT/'supplemental/audit.json'));save(OUT/'result.json',result)
p=REPO/'docs/GHIDRA_ENGINE_R5.md';p.write_text('Uzupelnienie: 3 jawne punkty wejscia w osobnej kopii projektu. Lacznie 91 123 pliki C oraz 91 406 funkcji w projekcie badawczym. Bajty poczatkowe, stale regul i hashe sprawdzono; bazowy projekt pozostaje niezmieniony. Szczegoly w README katalogu przebiegu i supplemental/audit.json.\n\n'+p.read_text(encoding='utf-8'),encoding='utf-8')
entry=REPO/'IMPORTER_AKTUALNY_SCHEMAT_I_ZASADY.md';raw=entry.read_bytes();nl='\r\n' if b'\r\n' in raw else '\n';note='\nUzupelnienie Ghidra R5: odzyskano tez 3 znane punkty wejscia niewydzielone przez domyslna analize: obie polskie fabryki regul i parser ligowy. Oddzielna kopia `project-research` ma 91 406 funkcji, a caly material 91 123 pliki C. Bazowy projekt i eksport pozostaly bez zmian; dodatkowy audyt w `supplemental/audit.json`.\n';entry.write_bytes(raw+note.replace('\n',nl).encode('utf-8'))
archive=OUT/'supplemental-source-snapshot';archive.mkdir(exist_ok=False);files=[OUT/'scripts/FmRecoverKnownEntriesR5.java',Path(__file__),OUT/'README.md',OUT/'RESEARCH_MAP.md',REPO/'docs/GHIDRA_ENGINE_R5.md'];manifest=[]
for source in files:
 dest=archive/source.name;shutil.copy2(source,dest);manifest.append(dict(path=dest.name,sha256=sha(dest)))
save(archive/'manifest.json',dict(source_only=True,files=manifest))
print(json.dumps(dict(status='verified',total_c_files=91123,research_functions=report['functions_after'],supplemental_functions=3,supplemental_warning_functions=warning_functions,baseline_project_unchanged=True),ensure_ascii=True))
