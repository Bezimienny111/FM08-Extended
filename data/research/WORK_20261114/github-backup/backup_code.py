from pathlib import Path
from datetime import datetime,timezone
import subprocess,json,hashlib,re,os,shutil,zipfile
ROOT=Path('J:/FM08dev');OUT=Path(__file__).resolve().parent;R=ROOT/'FmLauncher/data/research';N=R/'COUNTRY_BATCH_ENGLAND_20261114/native-prep'
rd=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def git(cwd,*args):
 z=subprocess.run(['git']+list(args),cwd=cwd,capture_output=True,text=True,encoding='utf-8',errors='replace',env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='Never'),timeout=240)
 assert z.returncode==0,('git_failed',args,z.stderr[-1200:]);return z.stdout.strip()
publication=rd(N/'publication-TEST_X23.json');assert publication['Status']=='PASS_PUBLIC_FOLDER_ZIP_ALL_MEMBERS_READBACK';assert sha(Path(publication['ZipPath']))==publication['ZipSHA256'];assert rd(OUT.parent/'GITHUB_AUTH_CHECK.json')['Status']=='AUTH_OK'
secret=re.compile(r"""(?i)(?:api[_-]?key|api[_-]?token|access[_-]?token|x-apisports-key|password|client[_-]?secret)["']?\s*[:=]\s*["']([^"'\r\n]{16,})["']""")
provider=re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,}|sk-proj-[A-Za-z0-9_-]{30,})')
selected={}
for x in rd(OUT/'source-selection.json')['Files']:
 f=Path(x['Source']);assert f.is_file();selected[(x['Repository'],x['Relative'])]=f
skip={'tools-deps','tools-python','__pycache__','bin','obj','.git','source-before','proposed','rollback','backups','references','reference','decompiled','openfm2007','source-archive','source-cache'}
for base,dirs,files in os.walk(R):
 dirs[:]=[d for d in dirs if d.lower()not in skip]
 for name in files:
  f=Path(base)/name
  if f.suffix.lower()in ['.py','.cs','.ps1']:selected[('FmLauncher',f.relative_to(ROOT/'FmLauncher').as_posix())]=f
f=ROOT/'FM08-Database-Tools/operations/database-update-policy-v1.json'
if f.exists():selected[('FM08-Database-Tools',f.relative_to(ROOT/'FM08-Database-Tools').as_posix())]=f
for rel in ['model-configuration.json','club-UID-projection.json','reserve-kind-overlay.json','club-plan.json','foreign-owner-plan.json','foreign-owner-aliases.json','root-structure/structure-config.json','source-authorization.json','source-freeze.json','tools/build-manifest.json']:
 f=N/rel
 if f.exists():selected[('FmLauncher',f.relative_to(ROOT/'FmLauncher').as_posix())]=f
findings=[];inventory=[]
for(repo,rel),f in sorted(selected.items()):
 raw=f.read_bytes();s=raw.decode('utf-16'if raw.startswith((b'\xff\xfe',b'\xfe\xff'))else'utf-8-sig',errors='replace')
 if secret.search(s)or provider.search(s):findings.append(dict(Repository=repo,File=rel))
 inventory.append(dict(Repository=repo,Relative=rel,Source=str(f),Bytes=len(raw),SHA256=hashlib.sha256(raw).hexdigest()))
dump(OUT/'reviewed-inventory.json',dict(Status='PASS_NO_LITERAL_SECRETS'if not findings else'REVIEW_REQUIRED',Files=inventory,Findings=findings,Excluded='raw caches, original FM binaries, saves/crashes, external graphics, personal launcher config'))
assert not findings,('possible_secret_files_only',findings)
branch='backup/modern-2627-england-20261114';workspace=ROOT/'backups/github-20261114';workspace.mkdir(parents=True,exist_ok=True);results=[]
for repo in ['FmLauncher','FM08-Database-Tools']:
 source=ROOT/repo;dest=workspace/repo;assert not dest.exists();state=git(source,'status','--porcelain=v1','--untracked-files=normal');head=git(source,'rev-parse','HEAD');originalbranch=git(source,'branch','--show-current');remote=git(source,'remote','get-url','origin')
 assert remote in ['https://github.com/Bezimienny111/FM08-Extended.git','https://github.com/Bezimienny111/FM08-Database-Tools.git']
 assert not git(source,'ls-remote','--heads','origin','refs/heads/'+branch),'Remote backup branch already exists'
 git(source,'worktree','add','-b',branch,str(dest),head);files=[]
 for x in inventory:
  if x['Repository']!=repo:continue
  f=Path(x['Source']);assert sha(f)==x['SHA256'];target=dest/x['Relative'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target);assert sha(target)==x['SHA256'];files.append(x['Relative'])
 notes='Backup 14 November 2026. Current first-party source and actual database helpers; original dirty main worktrees preserved. TEST_X23 native verified; SI/new-career/season pending. X22 long test in progress. Raw datasets, API credentials, original FM binaries, saves and external graphics excluded. Scripts may require separately owned local FM08 data and SI proof fixtures; no claim of a standalone universal importer. Launcher binary is verified dev R12; current source archived separately without claiming a fresh build.\n'
 (dest/'BACKUP_20261114.md').write_text(notes,encoding='utf-8');files.append('BACKUP_20261114.md')
 if repo=='FmLauncher':
  runtime=ROOT/'Launcher_0.1.3_R12';sub=dest/'backup/launcher-0.1.3-r12';sub.mkdir(parents=True);members=[]
  for f in sorted(runtime.iterdir()):
   if not f.is_file()or f.name in ['FmLauncher.config.json','FmLauncher.pdb']:continue
   assert f.suffix.lower()in ['.exe','.dll','.json','.txt'];target=sub/f.name;shutil.copy2(f,target);assert sha(target)==sha(f);members.append(dict(Name=f.name,SHA256=sha(f)));files.append(target.relative_to(dest).as_posix())
  dump(sub/'BACKUP_MANIFEST.json',dict(LauncherVersion='0.1.3_R12',Files=members,PersonalConfigurationExcluded=True,PdbExcluded=True));files.append((sub/'BACKUP_MANIFEST.json').relative_to(dest).as_posix())
  launcherzip=OUT/'FmLauncher-0.1.3-R12-backup.zip';assert not launcherzip.exists()
  with zipfile.ZipFile(launcherzip,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
   for f in sorted(sub.iterdir()):z.write(f,'Launcher_0.1.3_R12/'+f.name)
  with zipfile.ZipFile(launcherzip)as z:
   for f in sub.iterdir():assert hashlib.sha256(z.read('Launcher_0.1.3_R12/'+f.name)).hexdigest()==sha(f)
 for at in range(0,len(files),30):git(dest,'-c','core.autocrlf=false','add','-f','--',*files[at:at+30])
 assert git(dest,'diff','--cached','--name-only')
 git(dest,'commit','-m','Back up modern 2026/27 launcher and database workflow after TEST_X23 England')
 commit=git(dest,'rev-parse','HEAD');git(dest,'push','origin','HEAD:refs/heads/'+branch);assert git(dest,'ls-remote','--heads','origin','refs/heads/'+branch).split()[0]==commit
 assert git(source,'rev-parse','HEAD')==head and git(source,'branch','--show-current')==originalbranch and git(source,'status','--porcelain=v1','--untracked-files=normal')==state,'Original dirty worktree changed'
 row=dict(Repository=repo,Remote=remote,Branch=branch,Commit=commit,FilesCopied=len(files),OriginalBranch=originalbranch,OriginalHEAD=head,OriginalDirtyWorktreePreserved=True,Worktree=str(dest),URL=remote.removesuffix('.git')+'/tree/'+branch);results.append(row);dump(OUT/('branch-'+repo+'.json'),row);print('PUSHED',repo,commit,flush=True)
dump(OUT/'code-backup-result.json',dict(Status='PASS_TWO_SEPARATE_BACKUP_BRANCHES_REMOTE_HEAD_VERIFIED',Branches=results,SourceFiles=len(inventory),SecretScan='PASS_NO_LITERAL_SECRETS',LauncherZIP=str(OUT/'FmLauncher-0.1.3-R12-backup.zip'),LauncherZIPSHA256=sha(OUT/'FmLauncher-0.1.3-R12-backup.zip'),DatabaseZIP=publication['ZipPath'],DatabaseZIPSHA256=publication['ZipSHA256'],RecordedAt=datetime.now(timezone.utc).isoformat()))
print('CODE_BACKUP_COMPLETE',flush=True)
