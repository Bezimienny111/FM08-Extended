"""TEST_X11: strictly scoped same-length CA/PA patch; no roster importer or new UID."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import ast,csv,hashlib,json,random,shutil,struct,subprocess,sys,zlib
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=R/'CA_PA_REPAIR_X11_20261111';SOURCE=ROOT/'Dane/db/TEST_X10';FROZEN=B/'input/X10-after-SI';STAGED=B/'output/TEST_X11';PUBLIC=ROOT/'Dane/db/TEST_X11';SCOPE=R/'CA_PA_AUDIT_20261111/R2'
VERSION='legacy-ca-jitter-pa-repair-2026-11-11-v1'
NEIGHBOR_AUDIT={}
sys.dont_write_bytecode=True
assert __debug__,'Run with assertions enabled'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pins(folder):return {str(p.relative_to(folder)):sha(p)for p in sorted(folder.rglob('*'))if p.is_file()}
def js(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rows(p):
 with p.open(encoding='utf-8-sig',newline='')as f:return list(csv.DictReader(f))
def save(p,v):
 with p.open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(v[0]));w.writeheader();w.writerows(v)
def decode(p):
 raw=p.read_bytes();decoder=zlib.decompressobj();data=decoder.decompress(raw[9:])+decoder.flush()
 assert len(raw)>9 and decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail
 return raw[:9],data
def one(data,needle):
 first=data.find(needle);assert first>=0 and data.find(needle,first+1)<0,('nonunique',needle.hex())
 return first
def patch(data,edits):
 out=bytearray(data);end=0
 for at,count,value in sorted(edits):
  assert 0<=end<=at and len(value)==count and at+count<=len(data),'Only bounded non-overlapping same-size edits'
  out[at:at+count]=value;end=at+count
 return bytes(out)
# Extract the already-verified inverse helper without importing historical top-level state.
helper=ROOT/'FM08-Database-Tools/scratch/create_club_stadium_native_n1_20261108.py'
tree=ast.parse(helper.read_text(encoding='utf-8-sig'));fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='apply_verified')
env={'patch':patch,'hashlib':hashlib};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(helper),'exec'),env);apply_verified=env['apply_verified']
def table_bounds(ppl):
 pc,traits,attrs=struct.unpack_from('<iii',ppl,0);assert pc>300000 and traits>0 and attrs>0
 needle=struct.pack('<i',attrs);at=0;found=[]
 while True:
  at=ppl.find(needle,at)
  if at<0:break
  start=at+4
  if start+attrs*89<=len(ppl)and all(struct.unpack_from('<i',ppl,start+k*89+81)[0]==k for k in [0,1,2,3,attrs-1]):
   personend=at-4-traits*17
   if personend>20 and struct.unpack_from('<i',ppl,personend)[0]==traits:found.append((personend,at,start,attrs,traits,pc))
  at+=1
 assert len(found)==1,('attribute table ambiguity',found)
 personend,co,start,attrs,traits,pc=found[0]
 assert all(struct.unpack_from('<i',ppl,start+k*89+81)[0]==k for k in range(attrs))
 traitstart=personend+4
 assert traitstart+traits*17==co
 assert all(struct.unpack_from('<i',ppl,traitstart+k*17+9)[0]==k for k in range(traits))
 return dict(person_end=personend,traits_count=traits,traits_start=traitstart,traits_end=co,attributes_count=attrs,attributes_start=start,attributes_end=start+attrs*89,person_count=pc,all_table_indices_verified=True)
def locate(ppl,record,bounds):
 uid=int(record['ID']);pi=int(record['PersonIndex']);assert 0<pi<bounds['person_count']
 footer=one(ppl,struct.pack('<iI',pi,uid));assert footer<bounds['person_end']
 pattern=struct.pack('<iB',pi,2);start=max(20,footer-4096);candidates=[]
 while True:
  at=ppl.find(pattern,start,footer)
  if at<0:break
  start=at+1
  if at+30>=footer or ppl[at+26:at+30]!=bytes.fromhex('6c071027'):continue
  if at<8:continue
  prevpi,prevuid=struct.unpack_from('<iI',ppl,at-8)
  if not(0<=prevpi<bounds['person_count']and prevuid>0):continue
  prev=NEIGHBOR_AUDIT.get(prevpi)
  if prev is not None and int(prev['ID'])!=prevuid:continue
  nxt=footer+8
  if nxt!=bounds['person_end']:
   if nxt+5>bounds['person_end']:continue
   nextpi,nextkind=struct.unpack_from('<iB',ppl,nxt)
   if not(0<=nextpi<bounds['person_count']and nextkind in range(1,6)):continue
   neighbor=NEIGHBOR_AUDIT.get(nextpi)
   if nextkind==2:
    if neighbor is None:continue
    if ppl[nxt+26:nxt+30]!=bytes.fromhex('6c071027'):continue
    if struct.unpack_from('<hh',ppl,nxt+11)!=(int(neighbor['CA']),int(neighbor['PA'])):continue
    nf=one(ppl,struct.pack('<iI',nextpi,int(neighbor['ID'])))
    if not nxt+200<=nf<=min(nxt+4096,bounds['person_end']-8):continue
  if(struct.unpack_from('<h',ppl,at+11)[0],struct.unpack_from('<h',ppl,at+13)[0])!=(int(record['CA']),int(record['PA'])):continue
  ai=struct.unpack_from('<i',ppl,at+15)[0]
  if not 0<=ai<bounds['attributes_count']:continue
  candidates.append(at)
 assert len(candidates)==1,('PERSON ambiguity/mismatch',uid,pi,candidates)
 return candidates[0],footer
def audit(source,out,log):
 exe=R/'ITALY_DATABASE_2627_IMPORT_I1_20261108/tools-r1/ApplyVerifiedNativeSquads.exe';editor=R/'FOUR_COUNTRY_X7_20261110/tools-r2/FM08_Database_Editor.exe'
 assert not out.exists()
 assert sha(editor)=='884ae78d9d9f72ed90de583f8d586c83984bbc43cb996b9219f42c1aa16f6b4e'
 z=subprocess.run([str(exe),str(editor),str(source),str(out),'--audit'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600)
 log.write_text(z.stdout+z.stderr,encoding='utf-8');assert z.returncode==0,(z.returncode,z.stderr[-500:])
 return dict(wrapper=str(exe),wrapper_sha256=sha(exe),editor=str(editor),editor_sha256=sha(editor))
def validate_plan(v,scope,live):
 u=int(v['uid']);assert u in scope and u in live
 r=live[u];s=scope[u]
 assert s['classification']=='source_proven_project_estimate'and s['source_proven_for_dry_run']=='True'
 assert s['uid_in_stock802']=='False'and u!=1603002695
 assert(r['FirstName']+' '+r['LastName']).strip()==s['name']
 assert(int(r['CA']),int(r['PA']))==(int(s['CA']),int(s['PA']))==(int(v['old_CA']),int(v['old_PA']))
 assert 1<=int(v['new_CA'])<=int(v['new_PA'])<=200 and int(v['new_PA'])>=int(v['old_PA'])
 assert -5<=int(v['CA_draw'])<=5
 assert int(v['new_CA'])==max(1,min(200,int(v['old_CA'])+int(v['CA_draw'])))
 assert int(v['new_PA'])==max(int(v['old_PA']),int(v['R2_target_PA']),int(v['new_CA']))
def freeze():
 assert not PUBLIC.exists()and not FROZEN.exists()and not STAGED.exists()
 B.mkdir(exist_ok=True);before=pins(SOURCE);assert 'people_db.dat'in before and 'TEST_X10.xml'in before
 FROZEN.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(SOURCE,FROZEN)
 frozen=pins(FROZEN);after=pins(SOURCE);assert before==frozen==after,'Source changed during freeze; do not proceed'
 manifest=dict(created_at=datetime.now(timezone.utc).isoformat(),version=VERSION,scope=542,source=str(SOURCE),frozen=str(FROZEN),source_hashes=before,frozen_hashes=frozen,source_stable_during_freeze=True,source_SI='user_confirmed',source_new_career='user_confirmed',source_season='pending',output=str(PUBLIC),native='not_started',SI='pending',new_career='pending',season='pending',source_of_authorization='User explicitly requested PA correction plus small CA randomization; parent scope542legacyTM,±5CA,PA-onlyR2target, no attribute or roster changes')
 dump(B/'manifest.json',manifest)
 tools=audit(FROZEN,B/'audit-X10',B/'audit-X10.log');assert pins(FROZEN)==frozen and pins(SOURCE)==before
 dump(B/'tools.json',tools);print('FROZEN_AND_AUDITED',len(before),'files',flush=True)
def plan_apply():
 m=js(B/'manifest.json');assert pins(FROZEN)==m['frozen_hashes']and pins(SOURCE)==m['source_hashes']
 assert not STAGED.exists()and not PUBLIC.exists()
 scopefile=SCOPE/'source-proven-estimates-dry-run-scope.csv';targetfile=SCOPE/'scenario-PA-only.csv';scope={int(x['uid']):x for x in rows(scopefile)};targets={int(x['uid']):x for x in rows(targetfile)}
 assert len(scope)==len(targets)==542 and set(scope)==set(targets)
 live={int(x['ID']):x for x in rows(B/'audit-X10/players.csv')};NEIGHBOR_AUDIT.update({int(x['PersonIndex']):x for x in live.values()});hdr,ppl=decode(FROZEN/'people_db.dat');bounds=table_bounds(ppl)
 plan=[];edits=[]
 for uid,s in sorted(scope.items()):
  r=live[uid];t=targets[uid];assert (int(r['CA']),int(r['PA']))==(int(t['CA_before']),int(t['PA_before']))
  seedtext=VERSION+'|'+str(uid)+'|ca-jitter';seed=hashlib.sha256(seedtext.encode('ascii')).digest();delta=random.Random(int.from_bytes(seed,'big')).randint(-5,5)
  ca=max(1,min(200,int(r['CA'])+delta));pa=max(int(r['PA']),int(t['PA_after']),ca)
  reason=[]
  if int(t['PA_after'])>int(r['PA']):reason.append('approved_R2_age_margin')
  if ca>max(int(r['PA']),int(t['PA_after'])):reason.append('technical_PA_at_least_new_CA')
  if not reason:reason.append('preserved_existing_PA')
  v=dict(uid=uid,name=s['name'],club=s['club'],country=s['country'],age=int(s['age']),source_dob=s['source_dob'],source_player_id=s['source_player_id'],old_CA=int(r['CA']),new_CA=ca,CA_draw=delta,CA_effective_delta=ca-int(r['CA']),old_PA=int(r['PA']),R2_target_PA=int(t['PA_after']),new_PA=pa,PA_delta=pa-int(r['PA']),PA_reason='|'.join(reason),seed_text=seedtext,seed_sha256=seed.hex(),algorithm='SHA256 key -> random.Random(big-endian digest).randint(-5,5); no talent draw',provenance_class=s['classification'])
  validate_plan(v,scope,live);start,footer=locate(ppl,r,bounds)
  v.update(person_index=int(r['PersonIndex']),person_start=start,person_end=footer+8,CA_offset=start+11,PA_offset=start+13,previous_physical_person_index=struct.unpack_from('<i',ppl,start-8)[0],previous_physical_UID=struct.unpack_from('<I',ppl,start-4)[0],next_physical_person_index=struct.unpack_from('<i',ppl,footer+8)[0]if footer+8<bounds['person_end']else -1,old_record_sha256=hashlib.sha256(ppl[start:footer+8]).hexdigest())
  plan.append(v);edits.extend([(start+11,2,struct.pack('<h',ca)),(start+13,2,struct.pack('<h',pa))])
 assert len({p['uid']for p in plan})==542
 # Native negative guards, entirely in memory and before any output DB exists.
 negatives=[]
 for name,change in [('wrong_old_CA',dict(old_CA=plan[0]['old_CA']+1)),('protected_FC27_UID',dict(uid=1603002695)),('invalid_PA_below_CA',dict(new_PA=1)),('CA_jitter_out_of_bounds',dict(CA_draw=6))]:
  try:validate_plan(dict(plan[0],**change),scope,live)
  except(AssertionError,KeyError):negatives.append(dict(case=name,rejected=True))
  else:raise AssertionError('Negative case accepted:'+name)
 try:apply_verified(ppl,[(11,2,b'AA'),(12,2,b'BB')])
 except AssertionError:negatives.append(dict(case='overlapping_native_edits',rejected=True))
 else:raise AssertionError('Overlapping edits accepted')
 out,evidence=apply_verified(ppl,edits)
 assert len(out)==len(ppl)and out[bounds['person_end']:]==ppl[bounds['person_end']:]
 assert out[bounds['attributes_start']:bounds['attributes_end']]==ppl[bounds['attributes_start']:bounds['attributes_end']]
 inverse=bytearray(out)
 for v in plan:
  struct.pack_into('<hh',inverse,v['CA_offset'],v['old_CA'],v['old_PA'])
 assert bytes(inverse)==ppl,'Full inverse failed'
 STAGED.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(FROZEN,STAGED)
 (STAGED/'people_db.dat').write_bytes(hdr+zlib.compress(out))
 xml=STAGED/'TEST_X10.xml';b=xml.read_bytes();assert b.count(b'TEST_X10')==2;b=b.replace(b'TEST_X10',b'TEST_X11');(STAGED/'TEST_X11.xml').write_bytes(b);xml.unlink()
 (STAGED/'README.md').write_text('TEST_X11\n\nPoprawka ocen542potwierdzonych wcześniejszych profili modelowych TM: PA według audytuR2 i małe, deterministyczne odchylenieCA od-5do+5. Bez nowych zawodników, transferów, klubów i nagród talentu. Atrybuty/osobowości, daty, umowy i rozgrywki zachowane. To korekta szacunków, nie nowe indywidualne oceny skautingowe.\n\nPodstawaTEST_X10: SI i nowa kariera potwierdzone. TEST_X11: native weryfikacja w raporcie; zapisSI/nowa kariera/sezon wymagają osobnego testu.\nRaport: FmLauncher/data/research/CA_PA_REPAIR_X11_20261111/RAPORT.md\n',encoding='utf-8')
 h2,d2=decode(STAGED/'people_db.dat');assert h2==hdr and d2==out
 save(B/'before-after.csv',plan);dump(B/'negative-tests.json',dict(status='PASS',cases=negatives))
 dump(B/'native-patch-evidence.json',dict(status='PASS',bounds=bounds,edits=evidence,entire_PEOPLE_inverse_pass=True,people_uncompressed_size_unchanged=True,people_header9B_unchanged=True,all_bytes_after_PERSON_unchanged=True,entire_89B_attribute_table_unchanged=True,entire_17B_personality_table_unchanged=True,source_people_sha256=sha(FROZEN/'people_db.dat'),output_people_sha256=sha(STAGED/'people_db.dat'),source_unpacked_sha256=hashlib.sha256(ppl).hexdigest(),output_unpacked_sha256=hashlib.sha256(out).hexdigest()))
 m.update(native='patched_pending_independent_readback',staged=str(STAGED),scope_files={str(scopefile):sha(scopefile),str(targetfile):sha(targetfile)},patcher_sha256=sha(Path(__file__)),known_inverse_helper=str(helper),known_inverse_helper_sha256=sha(helper),CA_changed=sum(x['old_CA']!=x['new_CA']for x in plan),PA_changed=sum(x['old_PA']!=x['new_PA']for x in plan),CA_and_PA_changed=sum(x['old_CA']!=x['new_CA']and x['old_PA']!=x['new_PA']for x in plan),CA_delta_counts=dict(Counter(x['CA_draw']for x in plan)),R2_PA_changes=sum(x['old_PA']!=x['R2_target_PA']for x in plan),PA_technical_only=sum(x['old_PA']==x['R2_target_PA']and x['new_PA']>x['old_PA']for x in plan),talent_draws=0,attributes_changed=False,personality_changed=False,new_UIDs=0,transfers=0,staged_hashes=pins(STAGED))
 dump(B/'manifest.json',m);assert pins(SOURCE)==m['source_hashes']and pins(FROZEN)==m['frozen_hashes']
 print('PATCHED',m['CA_changed'],'CA',m['PA_changed'],'PA; audit follows',flush=True)
 audit(STAGED,B/'audit-X11',B/'audit-X11.log')
def verify_publish():
 m=js(B/'manifest.json');assert not PUBLIC.exists()and pins(STAGED)==m['staged_hashes']
 before={int(x['ID']):x for x in rows(B/'audit-X10/players.csv')};after={int(x['ID']):x for x in rows(B/'audit-X11/players.csv')};plan=rows(B/'before-after.csv');allowed={int(x['uid']):x for x in plan}
 assert set(before)==set(after)and len(allowed)==542
 count=0
 for uid,b in before.items():
  a=after[uid]
  if uid in allowed:
   v=allowed[uid];assert(int(a['CA']),int(a['PA']))==(int(v['new_CA']),int(v['new_PA']))
   assert{k:v for k,v in a.items()if k not in ['CA','PA']}=={k:v for k,v in b.items()if k not in ['CA','PA']}
   count+=1
  else:assert a==b,('Unrelated player changed',uid)
 assert count==542 and after[1603002695]==before[1603002695]
 # Independent raw inverse reconstruction from saved before/after; do not invoke writer helper.
 h0,d0=decode(FROZEN/'people_db.dat');h1,d1=decode(STAGED/'people_db.dat');assert h0==h1 and len(d0)==len(d1);undo=bytearray(d1);allowed_positions=set()
 for v in plan:
  u=int(v['uid']);caoff=int(v['CA_offset']);paoff=int(v['PA_offset']);pi=int(v['person_index']);start=int(v['person_start']);end=int(v['person_end'])
  assert d1[end-8:end]==struct.pack('<iI',pi,u)and d1[start:start+5]==struct.pack('<iB',pi,2)
  assert struct.unpack_from('<hh',d1,caoff)==(int(v['new_CA']),int(v['new_PA']))
  undo[caoff:caoff+2]=struct.pack('<h',int(v['old_CA']));undo[paoff:paoff+2]=struct.pack('<h',int(v['old_PA']))
  allowed_positions.update(range(caoff,caoff+2));allowed_positions.update(range(paoff,paoff+2))
 assert bytes(undo)==d0,'Independent entire PEOPLE inverse failed'
 # All other files byte-identical except documented metadata name and README.
 diffs=[]
 for name,digest in m['frozen_hashes'].items():
  if name=='TEST_X10.xml':continue
  if sha(STAGED/name)!=digest:diffs.append(name)
 assert set(diffs)<= {'people_db.dat','README.md'}and'people_db.dat'in diffs
 x0=(FROZEN/'TEST_X10.xml').read_bytes();x1=(STAGED/'TEST_X11.xml').read_bytes();assert x0.replace(b'TEST_X10',b'TEST_X11')==x1
 assert set(pins(STAGED))==(set(m['frozen_hashes'])-{'TEST_X10.xml'})|{'TEST_X11.xml'}
 assert pins(FROZEN)==m['frozen_hashes']and pins(SOURCE)==m['source_hashes']
 proof=dict(status='PASS',all_player_rows_compared=len(before),scoped_UIDs=count,no_new_or_removed_UIDs=True,protected_FC27_Luka_Ilic_unchanged=True,all_other_player_rows_identical=True,subject_rows_identical_except_CA_PA=True,entire_PEOPLE_independent_inverse=True,only_allowed_CA_PA_words_changed=True,all_other_files_identical_except_XML_name_and_README=True,contracts_rosters_loans_dates_attributes_personality_unchanged=True,source_X10_and_frozen_snapshot_unchanged=True,SI='pending',new_career='pending',season='pending')
 dump(B/'independent-verification.json',proof)
 shutil.copytree(STAGED,PUBLIC);assert pins(PUBLIC)==m['staged_hashes']and pins(SOURCE)==m['source_hashes']
 m.update(native='PASS',published_at=datetime.now(timezone.utc).isoformat(),output_hashes=pins(PUBLIC),independent_readback='PASS',SI='pending',new_career='pending',season='pending')
 dump(B/'manifest.json',m)
 report=f"""# TEST_X11 — poprawka CA/PA, 11 XI 2026

**Native PASS.** Nowa baza: J:/FM08dev/Dane/db/TEST_X11. Podstawa TEST_X10 po potwierdzonym zapisie SI i nowej karierze została zamrożona w input/X10-after-SI. X10 i zapis kariery niezmienione. TEST_X11 ma osobne statusy: **SI oczekuje; nowa kariera oczekuje; sezon oczekuje**.

Użytkownik zlecił poprawę PA i niewielką randomizację CA. Zakres to dokładnie542źródłowo potwierdzone wcześniejsze modeleTM z audytuR2. Chroniony Luka Ilić UID1603002695 (FC27), stock i wszystkie pozostałe profile są nietknięte. Nie dodano UID, zawodników, klubów ani transferów.

CA: deterministyczna liczba całkowita−5..+5, klucz VERSION|UID|ca-jitter, SHA256→big-endian integer→random.Random→randint(-5,5); clamp1..200. Wersja: {VERSION}. Zmieniło się **{m['CA_changed']} CA**; zerowe odchylenie jest poprawnym wynikiem. Pełny rozkład delt w manifest.json i każdy seed w before-after.csv.

PA: gotowy cel wariantuR2 (374zmiany) oraz tylko techniczne maksimum max(starePA,celR2,noweCA). Łącznie zmieniło się **{m['PA_changed']} PA**, w tym **{m['PA_technical_only']} dodatkowych przypadków wyłącznie dla PA≥noweCA**. Potencjał nigdy nie maleje. To nie nowa loteria; wykonano0losowań talentów.

CAjitter jest niewielką korektą dawnych szacunków, nie nowym indywidualnym skautingiem. **Atrybutów nie przeliczano.** Dlatego ta zmiana nie jest pełną kalibracją umiejętności ani siły klubów i nie należy tak jej przedstawiać.

## Dowody techniczne

Istniejący parser FM08_Database_Editor zapisuje CA naPersonOffset−4, PA naPersonOffset−2. W zweryfikowanym typie2 PERSON przekłada się to na int16+11/+13 od początku rekordu. Oceny nie leżą w tabeli89B.

Każdy UID powiązano ze świeżym odczytem źródła poSI, dokładnym footerem(PersonIndex,UID), jednoznacznym nagłówkiem typu2, markerem6C071027, granicami sąsiednich rekordów, indeksem atrybutów i oczekiwanymi starymiCA/PA. Całe tabele17B/89B sprawdzono po indeksach i pozostawiono bitowo identyczne. Zastosowano istniejący helper apply_verified, wyodrębniony AST bez historycznych efektów top-level; jego patch dla zmian stałej długości wykorzystuje bytearray, a pełny inverse odzyskuje wszystkie pierwotne bajty.

Niezależny eksport istniejącym narzędziem odczytał **{len(before)} zawodników**. Wszystkie542cele zgadzają się z planem; pozostałe pełne wiersze identyczne. Drugi surowy inverse odtworzył całePEOPLE źródła. SERVER/CLIENT, historie, LNC/EDT i pozostałe pliki identyczne. Jedynymi wyjątkami pozaPEOPLE są nazwaTEST_X11 wXML/nazwa plikuXML orazREADME.

Umowy, wypożyczenia, rostery, daty, atrybuty i osobowości są zachowane dzięki pełnemu inverse i identyczności pozostałych plików. Negatywne walidacje odrzuciły złą wartość starą, chronionyUID,PAponiżejCA,deltaCApoza zakresem i nakładające się zapisy. Nie przebudowywano edytora ani launchera.

## Pliki

before-after.csv: UID, nazwisko, klub, wiek, źródło, stare/noweCA/PA, delta, powódPA i seed. manifest.json: piny wejścia/wyjścia i osobne statusy. native-patch-evidence.json: offsety i inverse. independent-verification.json: pełny readback. negative-tests.json: walidacje. audit-X10 i audit-X11: surowe eksporty.

## Test użytkownika

Otworzyć TEST_X11 w edytorzeSI, zapisać i zamknąć. Następnie utworzyć osobną nową karierę naTEST_X11 i sprawdzić przykładowe poprawione profile. Obecna karieraTEST_X10 nie otrzymuje tych zmian automatycznie. Potwierdzenie sezonu pozostaje osobnym testem.
"""
 (B/'RAPORT.md').write_text(report,encoding='utf-8')
 (B/'WZNOWIENIE.md').write_text('TEST_X11 gotowa: Native PASS; SI/nowa kariera/sezon oczekują.542UIDlegacyTM,±5CA deterministic SHA256 iPAcelR2/max(old,target,newCA); bez nowych UID i bez przeliczania atrybutów/talentów. X10poSI zamrożona i nietknięta. Nie powtarzaćpatchera ani nie nadpisywaćX11. RAPORT.md i manifest.json.\n',encoding='utf-8')
 print('PUBLISHED_NATIVE_PASS',str(PUBLIC),'CA',m['CA_changed'],'PA',m['PA_changed'],'playersCompared',len(before),flush=True)
if __name__=='__main__':
 stage=sys.argv[1]
 {'freeze':freeze,'apply':plan_apply,'verify-publish':verify_publish}[stage]()
