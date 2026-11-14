from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,zipfile,xml.etree.ElementTree as ET,sys
sys.stdout.reconfigure(encoding='utf-8');ROOT=Path('J:/FM08dev');B=Path(__file__).resolve().parent
rd=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def pins(p):return{str(f.relative_to(p)):sha(f)for f in sorted(p.rglob('*'))if f.is_file()}
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
ready=rd(B/'native-ready-for-root-review.json');assert ready['native'] and not ready['SI']and not ready['new_career']and not ready['season'];assert rd(B/'selection-readback.json')['Evaluations']==621
for name,h in rd(B/'final-artifact-pins.json').items():assert sha(B/name)==h,name
src=Path(ready['private_output']);assert pins(src)==ready['output_hashes'];freeze=rd(B/'source-freeze.json');assert pins(Path(freeze['source']))==freeze['hashes']
assert rd(B/'source-authorization.json')['UserExplicitlyAuthorizedPrepareEnglandOnX22'] is True
number=23
while(ROOT/'Dane/db'/('TEST_X'+str(number))).exists()or(ROOT/'wydania'/('TEST_X'+str(number)+'.zip')).exists():number+=1
name='TEST_X'+str(number);stage=B/'release-ready'/name;public=ROOT/'Dane/db'/name;archive=ROOT/'wydania'/(name+'.zip');assert not stage.exists()and not public.exists()and not archive.exists();stage.mkdir(parents=True)
# Copy only native game/support files; replace inherited version-specific metadata.
gamefiles={rel:h for rel,h in pins(src).items()if Path(rel).suffix.lower()=='.dat' or Path(rel).parts[0].lower()in['edt','lnc']};assert all(k in gamefiles for k in ['people_db.dat','server_db.dat','client_db.dat','lang_db.dat'])
for rel,h in gamefiles.items():
 out=stage/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src/rel,out);assert sha(out)==h
xmls=list(Path(freeze['frozen']).glob('TEST_X22.xml'));assert len(xmls)==1;tree=ET.parse(xmls[0]);props=tree.getroot();names=props.findall("string[@id='name']");assert len(names)==1;names[0].set('value',name);descs=props.findall("string[@id='description']");assert len(descs)==1;descs[0].text=name;descs[0].attrib.pop('value',None);tree.write(stage/(name+'.xml'),encoding='utf-8',xml_declaration=True)
counts=ready['counts'];report=(B/'RAPORT.md').read_text(encoding='utf-8');report='# '+name+'\n\n'+report;report+='\nTest: zapis w edytorze SI, zamkniecie edytora, nowa kariera z Anglia (wszystkie6poziomow,7grup). Potem osobny test przejscia sezonow. Test X22 trwa nadal i nie jest testem nowej wersji.\n';(stage/('RAPORT_'+name+'.txt')).write_text(report,encoding='utf-8')
meta=dict(database=name,scope=['England'],playable_levels=6,playable_groups=7,source='TEST_X22-after-SI',source_season='IN_PROGRESS_TARGET_2010',counts=counts,native_verified=True,si='PENDING',new_career='PENDING',season='PENDING',EnglandLeagueUpdated=True,SourceReadySHA256=sha(B/'native-ready-for-root-review.json'),FinalReadbackSHA256=sha(B/'final-readback.json'),GameFileSHA256=gamefiles)
dump(stage/'manifest.json',meta)
(stage/'SHA256SUMS.txt').write_text(''.join(sha(f)+'  '+f.relative_to(stage).as_posix()+'\n'for f in sorted(stage.rglob('*'))if f.is_file()),encoding='utf-8')
assert ET.parse(stage/(name+'.xml')).find("string[@id='name']").get('value')==name and ET.parse(stage/(name+'.xml')).find("string[@id='description']").text==name
expected=pins(stage);shutil.copytree(stage,public);assert pins(public)==expected
archive.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for f in sorted(stage.rglob('*')):
  if f.is_file():z.write(f,name+'/'+f.relative_to(stage).as_posix())
with zipfile.ZipFile(archive)as z:
 assert len(z.namelist())==len(expected)
 for rel,h in expected.items():assert hashlib.sha256(z.read(name+'/'+Path(rel).as_posix())).hexdigest()==h,rel
assert pins(Path(freeze['source']))==freeze['hashes'] and pins(src)==ready['output_hashes']
proof=dict(Status='PASS_PUBLIC_FOLDER_ZIP_ALL_MEMBERS_READBACK',Database=name,PublicPath=str(public),ZipPath=str(archive),ZipBytes=archive.stat().st_size,ZipSHA256=sha(archive),PublicFiles=expected,NativeGameFilesIdenticalToRated=gamefiles,Native=True,SI=False,NewCareer=False,Season=False,SourceX22Season='IN_PROGRESS_TARGET_2010',SourceX22Unchanged=True,NativeReadySHA256=sha(B/'native-ready-for-root-review.json'),Counts=counts,RecordedAt=datetime.now(timezone.utc).isoformat())
dump(B/('publication-'+name+'.json'),proof);print(json.dumps({k:proof[k]for k in ['Status','Database','PublicPath','ZipPath','ZipBytes','ZipSHA256']}),flush=True)
