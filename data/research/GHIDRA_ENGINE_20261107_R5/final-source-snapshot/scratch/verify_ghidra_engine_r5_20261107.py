"""Independent audit of the saved Ghidra project and per-function FM08 export."""
import argparse,collections,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
EXPECTED='157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(ok,text):
 if not ok:raise ValueError(text)
def main(out,final):
 progress=read(out/'progress.json')
 if not final:
  data=read(out/'decompiled/export-progress.json') if (out/'decompiled/export-progress.json').exists() else {}
  print(json.dumps(dict(phase=progress['phase'],elapsed_seconds=progress['elapsed_seconds'],state=progress['status'],java=progress.get('java'),last_stack_observation=progress.get('last_stack_observation'),export={k:data.get(k) for k in ['status','selected_functions','written','failed','external','remaining','reused','attempted_in_run','current_function']},pipeline=read(out/'pipeline.json')['status']),ensure_ascii=True));return
 require(not (out/'audit.json').exists(),'Audit exists; refusing overwrite')
 analysis=read(out/'analysis-result.json');imported=read(out/'import-finished.json');exported=read(out/'export-finished.json');pipeline=read(out/'pipeline.json')
 require(analysis['status']=='analysis_complete' and not analysis['analysis_timed_out'],'Auto-analysis did not complete')
 require(imported['exit_code']==0 and imported['source_unchanged'],'Import failed or source changed')
 require(exported['exit_code']==0 and exported['source_unchanged'],'Export failed or source changed')
 require(pipeline['status']=='export_finished_needs_audit','Pipeline not finished')
 require(sha(ROOT/'fm.exe')==sha(out/'input/fm.exe')==EXPECTED,'Source hashes differ')
 require((out/'project/FM08_802_FULL_R5.gpr').is_file() and (out/'project/FM08_802_FULL_R5.rep').is_dir(),'Persistent project missing')
 base=out/'decompiled';index=read(base/'function-index.json');result=read(base/'export-result.json')
 require(result['status'] in ['completed','completed_with_failures'] and result['remaining']==0,'Unattempted functions remain')
 require(index['source_sha256']==result['source_sha256']==analysis['sha256']==EXPECTED,'Provenance digest differs')
 rows=index['functions'];by_entry={r['entry']:r for r in rows};require(len(rows)==len(by_entry)==result['selected_functions']==analysis['function_count'],'Function inventory/count mismatch')
 latest={};raw=(base/'export-journal.jsonl').read_bytes();require(raw.endswith(b'\n'),'Journal has incomplete final line');lines=raw.decode('utf-8').splitlines();header=json.loads(lines[0])
 for line in lines[1:]:
  item=json.loads(line);require(item['record_type']=='function','Unexpected journal record');latest[item['entry']]=item
 require(latest==by_entry,'Journal and final index disagree')
 resume_verification=None
 if (out/'resume-before.json').exists():
  pin=read(out/'resume-before.json');prefix=raw[:pin['journal_prefix_bytes']]
  require(hashlib.sha256(prefix).hexdigest()==pin['journal_prefix_sha256'],'Pre-resume journal prefix changed')
  prior_written=0
  for line in prefix.decode('utf-8').splitlines()[1:]:
   old=json.loads(line)
   if old['status']=='written':
    prior_written+=1;now=by_entry[old['entry']]
    require(now['status']=='written' and now['sha256']==old['sha256'] and now['path']==old['path'],'Pre-resume C changed')
  require(prior_written==pin['written_before_resume'] and result['reused']>=prior_written,'Resume did not account for prior outputs')
  resume_verification=dict(prior_written=prior_written,journal_prefix_unchanged=True,prior_c_hashes_unchanged=True)
 plan=read(out/'export-plan.json');require('-noanalysis' in plan['command'] and '-readOnly' in plan['command'] and '-import' not in plan['command'],'Export did not reuse saved project')
 for key in ['source_sha256','ghidra_version','language','compiler_spec','profile','selected_functions']:require(header[key]==index[key]==result[key],'Header mismatch '+key)
 counts=collections.Counter(r['status'] for r in rows);total_bytes=0;expected_paths=set();failures=[];warning_functions=0;warning_lines=0;warning_kinds=collections.Counter();warning_examples=[]
 for row in rows:
  state=row['status'];require(state in ['written','failed','external'],'Unknown function status')
  if state=='failed':failures.append(row);continue
  if state!='written':continue
  path=base/row['path'];require(path.resolve().is_relative_to((base/'functions').resolve()) and not path.is_symlink(),'Output escapes function directory')
  require(path.is_file() and sha(path)==row['sha256'],'C hash mismatch '+row['entry']);payload=path.read_bytes();first,body=payload.split(b'\n',1)
  pattern=r'/\* FM08_R5 source=([0-9a-f]{64}) entry=(\S+) body=([0-9a-f]{64}) \*/'
  match=re.fullmatch(pattern,first.decode('ascii'));require(match is not None,'Invalid C provenance header')
  require(match[1]==EXPECTED and match[2]==row['entry'] and hashlib.sha256(body).hexdigest()==match[3],'C body provenance mismatch')
  require(bool(body.strip()),'Empty C body '+row['entry']);total_bytes+=len(payload);expected_paths.add(path.resolve())
  warnings=re.findall(r'^\s*(?:/\*|//)\s*WARNING:\s*(.+)',body.decode('utf-8'),re.M)
  if warnings:
   warning_functions+=1;warning_lines+=len(warnings)
   for warning in warnings:warning_kinds[re.sub(r'0x[0-9a-fA-F]+','0xADDR',warning).rstrip(' */')]+=1
   if len(warning_examples)<30:warning_examples.append(dict(entry=row['entry'],path=row['path'],warnings=warnings[:5]))
 actual_paths={p.resolve() for p in (base/'functions').glob('*.c')};require(expected_paths==actual_paths,'Unexpected or omitted C files')
 for key in ['written','failed','external']:require(counts[key]==result[key],key+' count mismatch')
 anchors={}
 for name,address in [('pol_get_settings','00e8ddc0'),('pol_setup_comps','00e8e950'),('individual_dissent','00b6afd0'),('reaction_choice','00b63b10'),('group_reaction','00b5bb80')]:
  row=by_entry.get('ram:'+address);require(row is not None and row['status']=='written','Required anchor lacks pseudocode: '+name)
  anchors[name]=dict(entry=row['entry'],name=row['name'],path=row['path'],sha256=row['sha256'])
 settings=(base/anchors['pol_get_settings']['path']).read_text(encoding='utf-8')
 require(('0x1fa16' in settings.lower() or '129558' in settings) and ('0x1fa17' in settings.lower() or '129559' in settings),'Polish UID constants missing from settings pseudocode')
 project_files=[p for p in (out/'project').rglob('*') if p.is_file()];project_hashes={str(p.relative_to(out/'project')):sha(p) for p in project_files}
 status='verified_with_decompiler_failures' if failures else 'verified'
 report=dict(status=status,source_sha256=EXPECTED,source_unchanged=True,analysis_timed_out=False,recognized_functions=len(rows),written=counts['written'],failed=counts['failed'],external=counts['external'],unattempted=0,c_bytes=total_bytes,c_files_verified=len(expected_paths),journal_and_index_identical=True,resume_verification=resume_verification,export_reused_saved_project=True,body_hashes_verified=True,functions_with_decompiler_warnings=warning_functions,decompiler_warning_lines=warning_lines,decompiler_warning_kinds=dict(warning_kinds),decompiler_warning_examples=warning_examples,anchors=anchors,project_files=len(project_files),project_bytes=sum(p.stat().st_size for p in project_files),project_hashes=project_hashes,failures=failures,original_source_recovered=False,original_exe_modified=False,game_executed=False)
 (out/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:report[k] for k in ['status','recognized_functions','written','failed','external','c_bytes','project_files','project_bytes','source_unchanged']},ensure_ascii=True))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--final',action='store_true');a=p.parse_args();main(a.output.resolve(),a.final)
