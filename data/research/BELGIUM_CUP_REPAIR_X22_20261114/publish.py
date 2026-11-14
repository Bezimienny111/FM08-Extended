from pathlib import Path
import json,hashlib,zlib,struct,shutil,zipfile,xml.etree.ElementTree as ET,datetime,sys
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');B=Path(__file__).resolve().parent;NAME='TEST_X22';PUB=ROOT/'Dane/db'/NAME;ZIP=ROOT/'wydania'/f'{NAME}.zip';STAGE=B/'release-ready'/NAME;TMP=B/'release-ready'/f'{NAME}.zip'
rd=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def pins(d):return {str(p.relative_to(d)):sha(p)for p in sorted(d.rglob('*'))if p.is_file()}
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not any(p.exists()for p in[PUB,ZIP,STAGE,TMP,ROOT/'Dane/db/TEST_X22.xml'])
assert sha(B/'native-patch-proof.json')=='0136f51f6a76c5497fab93e790b57e4db2b5c2c0fc36083ca72af8551ef130df'
p=rd(B/'native-patch-proof.json');q=rd(B/'selection-readback.json');f=rd(B/'source-freeze.json');D=Path(p['Private']);F=Path(p['Source']);S=Path(f['source']);before=p['SourceHashes'];after=p['PrivateHashes']
assert p['Status']=='PASS_ONE_CURRENT_INT32_NATIVE_INVERSE_AND_589_SELECTION' and q['Status']=='PASS_589' and len(q['Checks'])==589 and all(x['AfterPassed']for x in q['Checks'])
assert pins(S)==pins(F)==before and pins(D)==after and sha(Path(f['OriginalZIP']))==f['OriginalZIP_SHA256']
old=zlib.decompress((F/'server_db.dat').read_bytes()[9:]);new=zlib.decompress((D/'server_db.dat').read_bytes()[9:]);rec=next(x for x in rd(B/'source-native-structure.json')['records']if x['ClubUID']==3200589);e=p['Edit'];assert e['Offset']==rec['Start']+7 and struct.unpack_from('<iI',old,rec['Footer'])==(rec['TeamIndex'],3200589)
inverse=bytearray(new);assert old[e['Offset']:e['Offset']+4]==bytes.fromhex(e['BeforeHex']) and new[e['Offset']:e['Offset']+4]==bytes.fromhex(e['AfterHex']);inverse[e['Offset']:e['Offset']+4]=bytes.fromhex(e['BeforeHex']);assert bytes(inverse)==old and sum(x!=y for x,y in zip(old,new))==1
assert{k:v for k,v in before.items()if k!='server_db.dat'}=={k:v for k,v in after.items()if k!='server_db.dat'}
STAGE.parent.mkdir();shutil.copytree(D,STAGE);assert pins(STAGE)==after
xml=ET.parse(STAGE/'TEST_X21.xml');xr=xml.getroot();xr.find("string[@id='name']").set('value',NAME);xr.find("string[@id='description']").text='TEST_X22: poprawka obsady Belgii i Pucharu Belgii 2007/08; dane zawodnikow bez zmian.';xml.write(STAGE/f'{NAME}.xml',encoding='utf-8',xml_declaration=True)
assert STAGE.resolve().parent==(B/'release-ready').resolve();(STAGE/'TEST_X21.xml').unlink();(STAGE/'RAPORT_TEST_X21.txt').unlink()
sm=rd(F/'manifest.json');counts=sm['counts'];now=datetime.datetime.now(datetime.timezone.utc).isoformat();native={k:v for k,v in after.items()if k.lower().endswith('.dat')}
manifest=dict(database=NAME,scope=sm['scope'],playable_levels=sm['playable_levels'],source='TEST_X21 after latest SI save',source_career='FAIL_2007_10_05_BEL_CUP',counts=counts,counts_inherited_unchanged=True,native_verified=True,si='PENDING',new_career='PENDING',season='PENDING',EnglandLeagueUpdated=False,repair=dict(ClubUID=3200589,ClubName='RFC Meux',CurrentFromCompetitionUID=4,CurrentToCompetitionUID=2,Fields=1,ActualChangedRawBytes=1,SecondDivision19=True,ThirdGroups=[16,15],CupExpected111=True,GameVerified=False),NativeSHA256=native,ProofSHA256=sha(B/'native-patch-proof.json'),SelectionSHA256=sha(B/'selection-readback.json'),SourceOriginalZIP_SHA256=f['OriginalZIP_SHA256'],UTC=now)
dump(STAGE/'manifest.json',manifest);dump(STAGE/'BELGIUM_PATCH_PROVENANCE.json',dict(Proof=p,Decision=rd(B/'decision.json'),SourceNativeHashes={k:v for k,v in before.items()if k.lower().endswith('.dat')},StaticCodeSHA256=sha(B/'BEL_CUP_eec1c0.asm')))
report='''TEST_X22 - poprawka obsady Belgii\n\nPodstawa: najnowsza TEST_X21 po zapisie SI. X21: awaria5X2007 przy tworzeniu meczu Pucharu Belgii,110 uczestnikow przy wymaganych111.\n\nRFC Meux UID3200589 z trzeciego poziomu grupyB do drugiego poziomu: nastepny uprawniony klub wedlug koncowych tabel25/26 z juz zebranych danych. Drugi poziom19, trzeci grupy16+15, historyczny wyjatek silnika sezonu2007/08. Puchar: przewidywane74+19+18=111uczestnikow.\n\nJedno pole Current int32; jeden zmieniony bajt nieskompresowanego SERVER. Pozostale dane natywne identyczne z koncowym SI X21: zawodnicy,kadry,wypozyczenia,CA/PA,stadiony,rodzice,SugarDaddy.589warunkow selekcji obu form PASS i pelna inwersja SERVER PASS. EXE/launcher bez zmian.\n\nX22:SI,nowa kariera,sezon PENDING. Test: zapisSI,nowa kariera z Belgia do trzeciego poziomu,urlop do1VIII2008 i kontrola Pucharu Belgii oraz kolejnego sezonu. Wymaga NOWEJ KARIERY; nie naprawia juz rozpoczetego zapisuX21. X21/SI/ZIP/save chronione.\n\nAnglia to osobna paczka, nie zostala tu dodana.\n'''
(STAGE/f'RAPORT_{NAME}.txt').write_text(report,encoding='utf-8');(STAGE/'README.md').write_text('# TEST_X22\n\nBelgium data-only correction on latest post-SI X21: RFC Meux to Second Division, restoring first-year19/16/15 allocation and required111cup entrants. One Current field changes; player data and all native files except SERVER preserved.589selection conditions and full inverse PASS.\n\nSI/new career/season tests PENDING. A NEW CAREER is required; existing X21 saves are not repaired. England is not included.\n',encoding='utf-8')
metadata={'TEST_X21.xml','RAPORT_TEST_X21.txt','README.md','manifest.json','SHA256SUMS.txt'}
for rel,h in after.items():
 if rel not in metadata:assert sha(STAGE/rel)==h
assert ET.parse(STAGE/f'{NAME}.xml').find("string[@id='name']").get('value')==NAME
sums={str(x.relative_to(STAGE)).replace('\\','/'):sha(x)for x in sorted(STAGE.rglob('*'))if x.is_file()and x.name!='SHA256SUMS.txt'};(STAGE/'SHA256SUMS.txt').write_text(''.join(f'{h}  {rel}\n'for rel,h in sums.items()),encoding='utf-8');package=pins(STAGE)
with zipfile.ZipFile(TMP,'x',zipfile.ZIP_DEFLATED,compresslevel=1)as z:
 for x in sorted(STAGE.rglob('*')):
  if x.is_file():z.write(x,NAME+'/'+str(x.relative_to(STAGE)).replace('\\','/'))
with zipfile.ZipFile(TMP)as z:
 assert z.testzip()is None and set(z.namelist())=={NAME+'/'+rel.replace('\\','/')for rel in package}
 for rel,h in package.items():assert hashlib.sha256(z.read(NAME+'/'+rel.replace('\\','/'))).hexdigest()==h
assert pins(S)==pins(F)==before and pins(D)==after and sha(Path(f['OriginalZIP']))==f['OriginalZIP_SHA256'];shutil.copytree(STAGE,PUB)
with TMP.open('rb')as src,ZIP.open('xb')as out:shutil.copyfileobj(src,out)
assert pins(PUB)==package and sha(ZIP)==sha(TMP)and pins(S)==before
result=dict(Status='PASS_LOCAL_X22_FOLDER_ZIP_READBACK',Name=NAME,PublicPath=str(PUB),ZIP=str(ZIP),ZipSHA256=sha(ZIP),ZipBytes=ZIP.stat().st_size,Native=True,SI=False,NewCareer=False,Season=False,SourcePreserved=True,SourceHashes=before,PublicHashes=package,Checks=589,Fields=1,ActualChangedBytes=1,Counts=counts,CreatedUTC=now)
dump(B/'publication.json',result);print(json.dumps({k:result[k]for k in ['Status','PublicPath','ZIP','ZipSHA256','ZipBytes']}),flush=True)
