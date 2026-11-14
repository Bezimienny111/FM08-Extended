"""Publish documentation and a research map after the independent export audit passes."""
import ast,csv,hashlib,html,json,shutil
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REPO=ROOT/'FM08-Database-Tools';OUT=ROOT/'FmLauncher/data/research/GHIDRA_ENGINE_20261107_R5'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 audit=load(OUT/'audit.json');assert audit['status'] in ['verified','verified_with_decompiler_failures']
 assert not (OUT/'README.md').exists(),'Final notes already exist'
 data=load(OUT/'decompiled/function-index.json');rows=data['functions'];by_entry={r['entry']:r for r in rows}
 with (OUT/'decompiled/function-list.tsv').open('x',encoding='utf-8',newline='') as f:
  w=csv.writer(f,delimiter='\t');w.writerow(['Address','Name','Status','CFile','BodyBytes'])
  for r in rows:w.writerow([r['address'],r['name'],r['status'],r.get('path',''),r['body_bytes']])
 anchors=[
 ('Polska: ustawienia grywalnych poziomow',0xe8ddc0),('Polska: tworzenie rozgrywek',0xe8e950),('Polska: wymagane liczebnosci klubow',0xe8df90),('Konstruktor POL_FIRST',0xe8dfe0),('Konstruktor POL_SECOND',0xe8e320),('Polska: fabryka regul pierwszego poziomu',0xe90740),('Polska: fabryka regul drugiego poziomu',0xe8f660),('Polska: wybor uczestnikow z puli 129560',0xe8ed20),('Rejestracja poziomu w ustawieniach kraju',0xd63c10),('Walidator liczebnosci klubow',0xd35180),('Ogolny odczyt definicji etapow',0xd70cf0),('Parser regul etapu ligowego',0xdd2010),('Tworzenie akcji awansu',0xdc7160),('Tworzenie akcji spadku',0xdc71c0),
 ('Reakcja indywidualna / protesty',0xb6afd0),('Wybor rodzaju reakcji',0xb63b10),('Reakcja grupy zawodnikow',0xb5bb80),('Aktualizacja stanu reakcji +0x108C',0xb30450),('Zrodlo parametru reakcji +0x1118',0xb62c70),('Wyslanie akcji reakcji',0xb64ae0),('Wrapper generatora losowego meczu',0xb48b90),('Odczyt konfiguracji komentarza',0xb06ba0),('Konstruktor obslugi komentarza',0xb08400),('Switch nazw akcji: adres wewnatrz funkcji',0xb2c7a5)]
 lines=['# Mapa punktow badawczych FM08 8.0.2','', 'Adresy dotycza wylacznie EXE o SHA256 '+audit['source_sha256']+'. Opisy pochodza z dotychczasowych audytow Polski i kontrowersji meczowych. Nie sa odzyskanymi nazwami zrodlowymi. Parametry +0x108C/+0x1118 nadal nie maja udowodnionego przypisania do cech osobowosci w bazie.','', '| Zastosowanie | Adres | Funkcja Ghidry | Pseudokod |','|---|---|---|---|'];mapped=[]
 for label,address in anchors:
  direct=by_entry.get('ram:'+format(address,'08x'));candidates=[] if direct else [r for r in rows if any(int(b['start'],16)<=address<=int(b['end'],16) for b in r['body_ranges'] if ':' not in b['start'] and ':' not in b['end'])]
  r=direct or (candidates[0] if len(candidates)==1 else None)
  if r:
   path='decompiled/'+r['path'] if r.get('path') else None
   file_link='[C]('+path+')' if path else r['status'];name=r['name'].replace('|','\\|')
   lines.append('| '+label+' | `0x'+format(address,'08X')+'` | `'+name+'` | '+file_link+' |')
   mapped.append(dict(label=label,research_address=hex(address),function_entry=r['entry'],exact_function_entry=direct is not None,status=r['status'],path=path))
  else:lines.append('| '+label+' | `0x'+format(address,'08X')+'` | brak jednoznacznego wpisu | projekt/ASM |')
 (OUT/'RESEARCH_MAP.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');save(OUT/'research-map.json',mapped)
 native=OUT/'project/FM08_802_FULL_R5.gpr'
 caveat=('\nDekompilator nie wyeksportowal '+str(audit['failed'])+' funkcji. Ich adresy i powody sa jawnie zapisane w audit.json oraz function-index.json; kod maszynowy pozostaje w projekcie.\n') if audit['failed'] else '\nWszystkie rozpoznane funkcje wewnetrzne otrzymaly pseudokod.\n'
 readme='''# FM08 8.0.2 - projekt Ghidry i eksport silnika

Analiza zakonczona bez przekroczenia limitu. Oryginalny fm.exe oraz jego prywatna kopia maja SHA256 **'''+audit['source_sha256']+'''**.

| Wynik | Liczba |
|---|---:|
| Rozpoznane funkcje | '''+str(audit['recognized_functions'])+''' |
| Pliki C z pseudokodem | '''+str(audit['written'])+''' |
| Nieudane dekompilacje | '''+str(audit['failed'])+''' |
| Funkcje zewnetrzne / importy | '''+str(audit['external'])+''' |
| Niepodjete funkcje | 0 |

'''+caveat+'''
## Material do dalszych prac

- [Staly projekt Ghidry](project/FM08_802_FULL_R5.gpr) i towarzyszacy katalog .rep. Otwierac w tej samej Ghidrze 12.1.4. Zachowac oba elementy razem.
- [Mapa punktow badawczych](RESEARCH_MAP.md): Polska, tworzenie rozgrywek, awanse/spadki, komentarze i protesty meczowe.
- [Lista funkcji TSV](decompiled/function-list.tsv): adres, nazwa, status, plik C, rozmiar ciala.
- [Pelny indeks](decompiled/function-index.json) oraz append-only decompiled/export-journal.jsonl.
- Pseudokod: decompiled/functions/*.c. Kazdy plik ma adres, SHA zrodla i hash tresci w naglowku; jego pelny hash znajduje sie w indeksie.
- [Niezalezny audyt](audit.json): zgodnosc wszystkich C, dziennika, indeksu i projektu, liczniki oraz kotwice z poprzednich badan.

To pseudokod Ghidry, nie oryginalne zrodla ani projekt gotowy do ponownego zbudowania gry. Zakres to funkcje rozpoznane w calym EXE, w tym kod silnika, interfejsu i bibliotek. Ghidra moze pozostawiac typy undefined, nazwy FUN/DAT i ostrzezenia o niepewnej interpretacji. Decyzje o zmianach binarnych nalezy weryfikowac w asemblerze i po adresie.

## Jak pracowac dalej

Nie importowac EXE ponownie do analizy tych samych danych. Uzywac istniejacego projektu. Do odczytu skryptowego stosowac analyzeHeadless z tym projektem, -process fm.exe i -noanalysis; do czystego odczytu takze -readOnly. Eksport jest wznowialny przez wykonawce --phase export, ktory sprawdza dziennik i hashe i pomija juz zapisane funkcje. Nie otwierac projektu do edycji podczas odczytu przez inny proces.

Przyklad wyszukiwania regul Polski: `rg -n '129560|0x1fa18' decompiled/functions`. Dla konkretnej funkcji zaczac od RESEARCH_MAP.md lub TSV; pelny JSON moze miec bardzo dlugie linie.

Import mial limit 7200 s (2 godziny); pominietych analizatorow: brak. Eksport pracowal na zapisanym projekcie bez ponownej autoanalizy. Limit pojedynczej dekompilacji: 120 s. Logi import-stdout.log i export-stdout.log zachowano.

Gra nie byla uruchamiana ani patchowana. Bazy danych nie byly modyfikowane. Pliki .c i indeks nie sa deklaracja identycznosci z oryginalnym kodem producenta.
'''
 if audit.get('resume_verification'):readme+='\nWznowienie po kolizji dostepu do pliku postepu: zachowano '+str(audit['resume_verification']['prior_written'])+' wczesniejszych C. Audyt potwierdzil niezmieniony prefiks dziennika i hashe tych plikow; import nie byl powtarzany. Logi pierwotnego eksportu: resume-01/.\n'
 readme+='\nFunkcje z komentarzami WARNING dekompilatora: '+str(audit.get('functions_with_decompiler_warnings',0))+'. Licznik jest osobny od bledow eksportu; kategorie i przyklady sa w audit.json.\n'
 (OUT/'README.md').write_text(readme,encoding='utf-8')
 result={k:audit[k] for k in ['status','source_sha256','recognized_functions','written','failed','external','unattempted','c_bytes','project_bytes','source_unchanged']};result.update(persistent_project=str(native),export_directory=str(OUT/'decompiled'),research_map=str(OUT/'RESEARCH_MAP.md'),audit=str(OUT/'audit.json'),completed_at=datetime.now().astimezone().isoformat(timespec='seconds'));save(OUT/'result.json',result)
 p=REPO/'docs/GHIDRA_ENGINE_R5.md';p.write_text('Wynik: analiza i eksport zakonczone, niezalezny audyt '+audit['status']+'. Rozpoznane funkcje: '+str(audit['recognized_functions'])+', pliki C: '+str(audit['written'])+', bledy: '+str(audit['failed'])+'. [Gotowy material i mapa badan](../../FmLauncher/data/research/GHIDRA_ENGINE_20261107_R5/README.md).\n\n'+p.read_text(encoding='utf-8'),encoding='utf-8')
 entry=REPO/'IMPORTER_AKTUALNY_SCHEMAT_I_ZASADY.md';raw=entry.read_bytes();nl='\r\n' if b'\r\n' in raw else '\n';note='\nWynik Ghidra R5: pelna analiza zakonczona bez timeoutu, '+str(audit['recognized_functions'])+' rozpoznanych funkcji, '+str(audit['written'])+' plikow C, '+str(audit['failed'])+' bledow dekompilatora i '+str(audit['external'])+' funkcji zewnetrznych. Zapisany staly projekt .gpr/.rep, indeks i mapa badan; audyt '+audit['status']+'. Szczegoly w GHIDRA_ENGINE_R5.md i katalogu przebiegu.\n';assert b'Wynik Ghidra R5:' not in raw;entry.write_bytes(raw+note.replace('\n',nl).encode('utf-8'))
 page=OUT/'podglad-ghidra.html'
 if page.exists():
  text=page.read_text(encoding='utf-8');text=text.replace('</html>','<section><h2>Wynik niezaleznego audytu</h2><p>Rozpoznane: '+str(audit['recognized_functions'])+'; C: '+str(audit['written'])+'; bledy: '+str(audit['failed'])+'; importy zewnetrzne: '+str(audit['external'])+'.</p><p><a href="README.md">Gotowy material</a> / <a href="RESEARCH_MAP.md">Mapa badan</a></p></section></html>');page.write_text(text,encoding='utf-8')
 archive=OUT/'final-source-snapshot';archive.mkdir(exist_ok=False);files=[REPO/'scratch/run_ghidra_engine_r5_20261107.py',REPO/'scratch/continue_ghidra_engine_r5_20261107.py',REPO/'scratch/verify_ghidra_engine_r5_20261107.py',Path(__file__),REPO/'docs/GHIDRA_ENGINE_R5.md']+list((OUT/'scripts').glob('*.java'));manifest=[]
 for source in files:
  rel=source.relative_to(REPO) if source.is_relative_to(REPO) else Path('ghidra-scripts')/source.name;dest=archive/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest);manifest.append(dict(path=str(rel),sha256=sha(dest)))
 save(archive/'manifest.json',dict(source_only=True,files=manifest));print(json.dumps(result,ensure_ascii=True))
if __name__=='__main__':main()
