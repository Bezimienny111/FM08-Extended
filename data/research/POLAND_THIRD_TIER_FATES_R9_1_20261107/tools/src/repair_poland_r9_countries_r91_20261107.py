from pathlib import Path
from datetime import datetime
import csv,hashlib,json,shutil,struct,zlib,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_FATES_R9_20261107'
OUT=ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_FATES_R9_1_20261107'
DB=SOURCE/'user-data/db/TEST_POL_3_LEVEL_R9'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def hashes(p):return {str(x.relative_to(p)):sha(x) for x in p.rglob('*') if x.is_file()}
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
m=json.loads((SOURCE/'manifest.json').read_text(encoding='utf-8'))
assert hashes(DB)==m['database_output_hashes']
audit=json.loads((SOURCE/'diagnostics-selection/country-audit.json').read_text(encoding='utf-8'))
assert audit['clubs_audited']==152 and audit['country_counts']['141']=={'161':57,'-1':43}
fixes=audit['non_polish_country'];assert len(fixes)==43
assert all(x['CountryIndex']==-1 and x['FamilyPosition']==0 and x['CurrentDivisionIndex']==141 for x in fixes)
with (SOURCE/'diagnostics-selection/native-club-selection.csv').open(encoding='utf-8-sig',newline='') as f:teams=list(csv.DictReader(f))
assert len(teams)==23394
secondary=[x for x in teams if int(x['SecondaryDivisionIndex']) in (139,140,141,1332)]
assert not secondary,'Additional validator counts require review'
assert not OUT.exists(),'Refuse overwrite R9.1'
OUT.mkdir();(OUT/'input').mkdir();shutil.copytree(DB,OUT/'input/TEST_POL_3_LEVEL_R9')
shutil.copytree(SOURCE/'diagnostics-selection',OUT/'input/diagnostics-selection')
print(json.dumps({'step':'copy_R9_1','country_fixes':43,'preserve_R9_and_R8':True}),flush=True)
for name in ('runtime','resources','tools','promotion','lower-boundary','upper-boundary'):shutil.copytree(SOURCE/name,OUT/name)
shutil.copy2(SOURCE/'participants.csv',OUT/'participants.csv')
DEST=OUT/'user-data/db/TEST_POL_3_LEVEL_R9';shutil.copytree(DB,DEST)
raw=(DB/'server_db.dat').read_bytes();server=zlib.decompress(raw[9:]);after=bytearray(server);allowed=set()
for row in fixes:
 base=row['BaseStart'];at=row['CountryOffset'];end=row['NameTreeFooter'];marker=row['NameMarker']
 assert at==base+1 and server[base]==0
 assert server[marker:marker+7]==bytes.fromhex('FF00006C070000')
 assert struct.unpack_from('<ii',server,end)==(row['FamilyReference'],row['ClubUID'])
 assert struct.unpack_from('<i',server,at)[0]==-1
 assert struct.unpack_from('<ii',server,row['NativeRecordEnd']-8)==(row['ClubIndex'],row['ClubUID'])
 assert struct.unpack_from('<i',server,row['NativeRecordStart']+7)[0]==141
 struct.pack_into('<i',after,at,161);allowed.update(range(at,at+4))
 assert after[base:end+8]==server[base:at]+struct.pack('<i',161)+server[at+4:end+8]
changed={i for i,(a,b) in enumerate(zip(server,after)) if a!=b}
assert len(after)==len(server) and changed==allowed and len(changed)==172
reverse=bytearray(after)
for row in fixes:struct.pack_into('<i',reverse,row['CountryOffset'],-1)
assert bytes(reverse)==server
(DEST/'server_db.dat').write_bytes(raw[:9]+zlib.compress(after))
assert zlib.decompress((DEST/'server_db.dat').read_bytes()[9:])==after
meta=ET.parse(DEST/'TEST_POL_3_LEVEL_R9.xml');node=meta.getroot()
for x in node.findall('string'):
 if x.get('id')=='name':x.set('value','TEST_POL_3_LEVEL_R9_1 - Polish Promotion and Relegation Pilot')
 elif x.get('id')=='version':x.set('value','0.2.1')
 elif x.get('id')=='description':x.set('value',x.get('value')+' R9.1 restores the Polish country reference for43 existing lower-tier clubs; no change to league rules.')
meta.write(DEST/'TEST_POL_3_LEVEL_R9.xml',encoding='utf-8',xml_declaration=True)
for rel,want in m['database_output_hashes'].items():
 if rel not in ('server_db.dat','TEST_POL_3_LEVEL_R9.xml'):assert sha(DEST/rel)==want
# Internal layout stays R9 for the unchanged verified engine tool; display/package repair is R9.1.
new=dict(m);new.update(revision='R9',repair_revision='R9.1',status='preflight_pending',started_at=datetime.now().astimezone().isoformat(),source_database=str(DB),frozen_input=str(OUT/'input/TEST_POL_3_LEVEL_R9'),source_database_hashes=hashes(DB),runtime=str(OUT/'runtime'),output_database=str(DEST),database_output_hashes=hashes(DEST),game_verified=False,preflight_passed=False,season_rollover_verified=False,country_repairs=43,source_modified=False,pilot_tool_sha256=sha(OUT/'tools/PolandThirdTierFatesR9.exe'),runtime_comp_archive_sha256=sha(OUT/'resources/comps.efa'),repair_reason='43lower clubs haveCountry=-1; effective count57<required100',rules_changed=False,selection_verified_in_game=False)
save(OUT/'manifest.json',new)
report=dict(status='country_correction_structurally_verified',source=str(DB),output=str(DEST),country_before={'Poland':57,'missing':43},country_after={'Poland':100,'missing':0},changes=fixes,changed_decompressed_bytes=172,only_43_country_int32_fields_changed=True,exact_reverse_reconstructs_R9=True,secondary_entries_in_polish_divisions=0,all_club_team_records_unchanged=True,other_dat_files_identical=True,resources_and_engine_tool_identical=True,required_teams_retained=100,rule_changes=0,game_selection_verified=False,season_rollover_verified=False)
save(OUT/'country-correction.json',report)
shutil.copy2(SOURCE/'Start-Pilot.ps1',OUT/'Start-Pilot.ps1');shutil.copy2(SOURCE/'Start-Pilot.cmd',OUT/'Start-Pilot.cmd')
shutil.copy2(Path(__file__),OUT/'tools/src'/Path(__file__).name)
(OUT/'README.md').write_text('''# R9.1 — poprawka wyboru Polski

Poprawka danych R9, z niezmienionymi regułami awansów, spadków i baraży.
43 istniejące kluby zaplecza miały Country=-1. Silnik pomijał je w liczeniu:
57 zamiast wymaganych100 blokowało wybór Polski. Uzupełniono wyłącznie ich
referencję kraju na Polskę (indeks161). Nie obniżono wymogu100.

Uruchom Start-Pilot.cmd z TEGO katalogu i w nowej karierze wybierz bazę
**TEST_POL_3_LEVEL_R9_1 - Polish Promotion and Relegation Pilot**.
Najpierw sprawdź dostępność Polski i wybór trzeciego poziomu. Następnie
pozostaje uzgodniony pilot R9: baraże i zmiana sezonu (3awanse,4–6spadków,
po18klubów na drugim i trzecim poziomie,100klubów zaplecza).

Wewnętrzna nazwa folderu bazy i narzędzie pozostają R9, aby korzystać z tego
samego sprawdzonego kodu silnika. Widoczna nazwa bazy ma R9_1.
Nie zmieniono przypisań ligowych, kadr, osób, pensji, reputacji ani reguł.
W SERVER zmieniły się43pola int32, czyli172bajty danych po dekompresji.
CLIENT,PEOPLE,LANG,historie i inne pliki DAT są identyczne z R9.
R9 i działający R8 zachowano. Raport: country-correction.json;
diagnoza źródłowa: input/diagnostics-selection/validator-trace.md.
Kontrole techniczne nie zastępują ponownego sprawdzenia wyboru kraju w grze.
''',encoding='utf-8')
(OUT/'WZNOWIENIE.md').write_text('''# R9.1 — poprawka Country zaplecza

Status: preflight_pending. Naprawiono43referencjeCountry−1→161 w nowejkopiiR9;
wymóg100został. DotychczasowyR9nieprzeszedłwyboruPolski, boefektywniebyło57.
Dwaindeksykrajów zCOMP i52klubygrywalnychlig były poprawne; brakdotyczyłpuli.
TEAM+47secondaryniezawierażadnejz4polskichlig (23394rekordysprawdzone).

Start-Pilot.cmd wtymkatalogu, wybórnazwyTEST_POL_3_LEVEL_R9_1.
Kod/reguły/runtimeidentycznezR9, wewnętrznydbnameR9(repair_revisionR9.1).
CzekanatywnyeksportC#, ponownyaudyt152krajów iStart-Pilot.ps1 -VerifyOnly,
potemtestwyboruPolski iuzgodnionytestbaraży/przejściasezonu.
Nie zmieniać R8, źródłowej802 ani oryginalnegoEXE.
''',encoding='utf-8')
assert hashes(DB)==m['database_output_hashes']
print(json.dumps({'status':report['status'],'fixed_clubs':43,'changed_server_bytes':172,'required_teams':100,'rules_changed':False,'source_R9_unchanged':True,'output':str(OUT)}),flush=True)
