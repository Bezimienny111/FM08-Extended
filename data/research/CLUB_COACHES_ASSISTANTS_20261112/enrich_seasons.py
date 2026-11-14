from pathlib import Path
import re,json,collections,datetime
import collect_staff as b
B=b.B;R=b.R;ROOT=b.ROOT

def main():
 profiles={};targets={};menus={};extra={}
 for p in R.glob('*/sources/tm-clubs/*profile.json'):
  try:
   v=b.read(p)
   if str(v.get('updated_at',''))>=profiles.get(str(v.get('id','')),{}).get('updated_at',''):profiles[str(v.get('id',''))]=v
  except Exception:pass
 for p in R.glob('*/source-targets.json'):
  try:
   a=b.read(p)
   if isinstance(a,list):
    for x in a:
     if x.get('TMID') and x.get('APISeason') and x.get('RealSeason'):targets[str(x['TMID'])]=(x,p)
  except Exception:pass
 for p in R.glob('*/sources/tm-competitions/*seasons*.json'):
  try:
   a=b.read(p)
   for s in a.get('seasons',[]):menus[(str(a.get('id')),str(s.get('id')))]=(s,p)
  except Exception:pass
 pagecache={};evidence={};fields=None
 for file in ['staff-report.csv','staff-current.csv','staff-candidates.csv']:
  rows=b.rows(B/file)
  for r in rows:
   p=ROOT/r['source_file'];r['actual_page_season_id']='';r['displayed_page_season_label']='';r['real_season_label']='';r['season_evidence_file']='';r['season_evidence_sha256']='';r['season_alignment']='UNKNOWN_REAL_SEASON_LABEL';r['season_request_parameters']='No season parameter supplied; current staff page request' if 'staff-pages' in p.parts else 'See sourceURL'
   if r['source_role'].startswith('90minut'):
    r['displayed_page_season_label']=r['source_season'];r['real_season_label']=r['source_season'];r['season_alignment']='CURRENT_REAL_LABEL_CONFIRMED_2026_27' if r['source_season']=='2026/27' else 'UNKNOWN_REAL_SEASON_LABEL';continue
   if 'staff-pages' not in p.parts:continue
   if str(p) not in pagecache:
    raw=p.read_text(encoding='utf-8',errors='replace');m=re.search(r'<tm-subnavigation\b[^>]*?\bseason="([^"]+)"',raw,re.S);pagecache[str(p)]=m[1] if m else ''
   apiid=pagecache[str(p)];r['actual_page_season_id']=apiid
   league=str((profiles.get(r['TMID'],{}).get('league') or {}).get('id',''));meta=menus.get((league,apiid));proof=None
   if meta:
    s,proof=meta;label=s['name'];r['season_label_provenance']='Provider available-seasons label matched by exact competition ID and page internal season ID'
   elif r['TMID'] in targets and targets[r['TMID']][0]['APISeason']==apiid:
    target,proof=targets[r['TMID']];label=target['RealSeason'];r['season_label_provenance']='Existing resolved canonical source target APISeason→RealSeason mapping'
   else:label='';r['season_label_provenance']='Internal ID only; no verified human season label found'
   if proof:
    r['real_season_label']=label;r['season_evidence_file']=str(proof.relative_to(ROOT));r['season_evidence_sha256']=b.sha(proof);extra[str(proof.relative_to(ROOT))]=b.sha(proof)
    labelnorm=str(label).replace(' ','');r['season_alignment']='CURRENT_REAL_LABEL_CONFIRMED' if labelnorm in ['2026','26/27','2026/27','2026/2027'] else 'ACTUAL_SEASON_LABEL_REVIEW_REQUIRED'
   evidence[r['TMID']]=dict(TMID=r['TMID'],club=r['club'],country=r['country'],actual_page_season_id=apiid,displayed_page_season_label=r['displayed_page_season_label'],real_season_label=r['real_season_label'],season_evidence_file=r['season_evidence_file'],season_evidence_sha256=r['season_evidence_sha256'],season_alignment=r['season_alignment'],sourceURL=r['sourceURL'])
  fields=list(dict.fromkeys(k for r in rows for k in r));b.write(file,rows,fields)
 b.write('season-evidence.csv',list(evidence.values()));pins=b.read(B/'all-evidence-pins.json');pins.update(extra);b.dump('all-evidence-pins.json',pins)
 summary=b.read(B/'summary.json');cur=b.rows(B/'staff-current.csv');summary['season_label_coverage_current_rows']=dict(collections.Counter(r['season_alignment'] for r in cur));summary['season_policy']='Internal provider season_id2025 is not human season2025. Actual page ID and verified human label have separate columns. Unknown label is not called stale by assumption.';b.dump('summary.json',summary);print('SEASON_ALIGNMENT',summary['season_label_coverage_current_rows'],flush=True)
if __name__=='__main__':main()
