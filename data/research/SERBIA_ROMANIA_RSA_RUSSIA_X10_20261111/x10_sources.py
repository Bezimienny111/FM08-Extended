"""X10 consolidation, using existing immutable raw responses and existing fact analyzer."""
from x10_pipeline import *
from collections import Counter
def merge():
 other=R/'RUSSIA_RSA_PREP_X10_20261111'
 assert read(other/'preparation-report.json')['status']=='source_preparation_complete_no_DB_write'
 own=read(B/'source-targets.json');foreign=read(other/'source-targets.json')
 assert len(own)==84 and len(foreign)==70 and not(B/'source-consolidation.json').exists()
 dump(B/'source-targets-before-RU-RSA-merge.json',own)
 copied=[];conflicts=[]
 for f in (other/'sources').rglob('*'):
  if not f.is_file():continue
  dest=S/f.relative_to(other/'sources');dest.parent.mkdir(parents=True,exist_ok=True)
  if dest.exists():
   if dest.read_bytes()==f.read_bytes():continue
   if f.parent.name=='tm-raw':
    a,b=read(dest),read(f)
    if a.get('sha256')==b.get('sha256'):continue
    alt=S/'source-conflicts'/other.name/f.relative_to(other/'sources');alt.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,alt)
    conflicts.append(dict(file=str(dest.relative_to(B)),other=str(alt.relative_to(B)),same_body=False))
    if b.get('fetched_at','')>a.get('fetched_at',''):shutil.copyfile(f,dest)
   else:
    alt=S/'source-conflicts'/other.name/f.relative_to(other/'sources');alt.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,alt);conflicts.append(dict(file=str(dest.relative_to(B)),other=str(alt.relative_to(B))))
  else:shutil.copyfile(f,dest);copied.append(str(dest.relative_to(B)))
 targets=own+[dict(c,SourceBatch=other.name)for c in foreign]
 assert len(targets)==154 and len({c['TMID']for c in targets})==154
 assert all((B/c['ProfileFile']).exists()and (B/c['RosterFile']).exists()for c in targets)
 dump(B/'source-targets.json',targets)
 dump(B/'source-consolidation.json',dict(status='four_country_sources_merged_no_database_changes',clubs=154,country_counts=dict(Counter(c['Country']for c in targets)),copied_files=len(copied),conflicts=conflicts,source_batch=str(other),source_report_sha256=hashlib.sha256((other/'preparation-report.json').read_bytes()).hexdigest()))
 print('MERGED154',Counter(c['Country']for c in targets),'files',len(copied),'conflicts',len(conflicts),flush=True)
def analyze():
 source=R/'RUSSIA_RSA_PREP_X10_20261111/analyze_sources.py'
 s=source.read_text(encoding='utf-8')
 s=s.replace("B=Path.cwd()/'FmLauncher/data/research/RUSSIA_RSA_PREP_X10_20261111';S=B/'sources'","B=Path.cwd()/'FmLauncher/data/research/SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111';S=B/'sources'")
 s=s.replace("len(targets)==70","len(targets)==154")
 # Keep the existing batch identity/acceptance state; source analyzer gets its own manifest filename.
 s=s.replace("manifest=read(B/'manifest.json')","manifest=read(B/'manifest.json')")
 s=s.replace("dump(B/'manifest.json',manifest)","dump(B/'source-preparation-manifest.json',manifest)")
 out=B/'source-analyzer-configured.py';out.write_text(s,encoding='utf-8');exec(compile(s,str(out),'exec'),{'__name__':'__main__','__file__':str(out)})
if __name__=='__main__':
 if sys.argv[1]=='merge':merge()
 elif sys.argv[1]=='analyze':analyze()
 elif sys.argv[1]=='identities':identities_draft()
 else:raise ValueError(sys.argv[1])
