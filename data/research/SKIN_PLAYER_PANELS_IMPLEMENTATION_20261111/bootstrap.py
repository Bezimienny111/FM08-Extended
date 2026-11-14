from pathlib import Path,PureWindowsPath
import json,hashlib,csv,struct,zlib,subprocess
ROOT=Path('J:/FM08dev');B=ROOT/'FmLauncher/data/research/SKIN_PLAYER_PANELS_IMPLEMENTATION_20261111'
B.mkdir(exist_ok=True);S=B/'source-before';S.mkdir(exist_ok=True)
files=['Configuration.cs','MainForm.cs','SkinGuidePage.cs','GamePanelPatch.cs','GameLauncher.cs','SuspendedGameProcess.cs','SkinPanelInstaller.cs','FmLauncher.languages.json']
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pinned={}
for name in files:
 p=ROOT/'FmLauncher/src/FmLauncher'/name;target=S/name
 if not target.exists():target.write_bytes(p.read_bytes())
 pinned[str(p)]=h(target)
for name in ['Program.cs','PanelTests.cs','PanelNativeFixture.cs']:
 p=ROOT/'FmLauncher/tests/FmLauncher.Tests'/name;target=S/('test-'+name)
 if not target.exists():target.write_bytes(p.read_bytes())
 pinned[str(p)]=h(target)
skins=['fm2008','steklo','steklo_left','steklo_black','steklo_left_black','fm2008_ext_left','fm2008_ext_right','steklo_black_ext_left','steklo_black_ext_right']
skinpins={str(p):h(p)for name in skins for p in (ROOT/'Dane/skins'/name).rglob('*.xml')}
(B/'source-pins-before.json').write_text(json.dumps(dict(code=pinned,skins=skinpins),indent=2),encoding='utf-8')
z=subprocess.run(['git','status','--short'],cwd=ROOT/'FmLauncher',capture_output=True,text=True);(B/'git-status-before.txt').write_text(z.stdout,encoding='utf-8')
def archive(path):
 data=path.read_bytes();assert data[:6]==bytes([2,1,0x66,0x6d,0x66,0x2e])
 offset=struct.unpack_from('<I',data,9)[0]+18;assert offset<len(data)
 toc=zlib.decompress(data[offset:]);assert len(toc)<=16*1024*1024;at=4;entries={}
 def num(fmt):
  nonlocal at
  size=struct.calcsize(fmt);assert at+size<=len(toc);v=struct.unpack_from(fmt,toc,at)[0];at+=size;return v
 def text():
  nonlocal at
  n=num('<I');assert n<=4096;assert at+n*2<=len(toc);v=toc[at:at+n*2].decode('utf-16-le');at+=n*2;assert num('<H')==0;return v
 def node(prefix='',depth=0):
  assert depth<=32
  for _ in range(num('<H')):
   name=prefix+text()+text();assert not PureWindowsPath(name).is_absolute()and not PureWindowsPath(name).drive and'..'not in name.split('\\')and name not in entries
   entries[name]=(num('<I'),num('<I'),num('<I'))
  for _ in range(num('<H')):node(prefix+text()+'\\',depth+1)
 node();assert at==len(toc)
 def get(name):
  offset,stored,length=entries[name];offset+=9;assert length<=8*1024*1024 and offset<=len(data)-stored
  raw=data[offset:offset+stored];raw=zlib.decompress(raw)if stored!=length else raw;assert len(raw)==length;return raw
 return entries,get
resources={}
for label,arch in [('base',ROOT/'data/panels.fmf'),('802',ROOT/'data/updates/update-802/data/panels.fmf')]:
 names,get=archive(arch)
 for name in names:
  if name.startswith('player profile')or 'attribute' in name or name in ['player personal.xml']:
   raw=get(name);dest=B/'stock-panels'/label/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);resources[label+'/'+name]=dict(archive=str(arch),archive_sha256=h(arch),resource=name,output=str(dest),sha256=h(dest))
(B/'stock-resources.json').write_text(json.dumps(resources,ensure_ascii=False,indent=2),encoding='utf-8')
weights=ROOT/'FMExt/recovery/steklo-dev-20261106/genie-positional-weights.csv';rows=list(csv.DictReader(weights.open(encoding='utf-8-sig'),delimiter=';'));groups=list(rows[0])[2:];exclude={'Scale','CA','LeftFoot','RightFoot','Consistency','ImportantMatches','InjuryProneness','Dirtiness','Versatility','Adaptability','Ambition','Controversy','Loyalty','Pressure','Professionalism','Sportsmanship','Temperament'}
result={}
for g in groups:result[g]=dict(key=[r['Attribute']for r in rows if r['Attribute']not in exclude and int(r[g])>=60],important=[r['Attribute']for r in rows if r['Attribute']not in exclude and 20<=int(r[g])<60])
(B/'position-threshold-proposal.json').write_text(json.dumps(dict(status='project_proposal_for_review_not_SI_fact',key_minimum=60,important_minimum=20,source=str(weights),source_sha256=h(weights),groups=result),indent=2),encoding='utf-8')
print('EVIDENCE SNAPSHOT',len(pinned),'codefiles',len(skinpins),'skinXML',len(resources),'stockresources',len(groups),'positiongroups')
