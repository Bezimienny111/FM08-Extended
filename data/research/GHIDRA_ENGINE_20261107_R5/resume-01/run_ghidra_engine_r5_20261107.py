"""Run one persistent Ghidra project phase, with live counters and a real log preview."""
import argparse,hashlib,html,json,os,subprocess,sys,time
from collections import Counter
from datetime import datetime
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
from watch_rea_analysis_20261107 import sample
TOOLS=Path('C:/Users/Bezi/AppData/Local/Programs/REA-Tools')
EXPECTED='157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,s):
 t=p.with_name(p.name+'.tmp');t.write_text(s,encoding='utf-8');os.replace(t,p)
def save(p,x):write(p,json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ps(code):
 r=subprocess.run(['powershell.exe','-NoProfile','-Command',code],capture_output=True,timeout=12,creationflags=subprocess.CREATE_NO_WINDOW)
 if r.returncode:return []
 raw=r.stdout.decode('utf-8',errors='replace').strip()
 if not raw:return []
 d=json.loads(raw);return d if isinstance(d,list) else [d]
def main(a):
 out=a.output.resolve();phase=a.phase;exe=ROOT/'fm.exe';private=out/'input/fm.exe'
 assert sha(exe)==EXPECTED,'Original EXE changed'
 if not private.exists():
  import shutil;shutil.copy2(exe,private)
 assert sha(private)==EXPECTED,'Private EXE changed'
 env=dict(os.environ);env['JAVA_HOME']=str(TOOLS/'jdk-25.0.5+8');env['GHIDRA_HEADLESS_MAXMEM']='2G'
 env['PATH']=str(TOOLS/'jdk-25.0.5+8/bin')+os.pathsep+env.get('PATH','')
 for key in ['REA_GHIDRA_DISABLED_ANALYZERS','GHIDRA_JAVA_OPTIONS','GHIDRA_HEADLESS_JAVA_OPTIONS','JAVA_TOOL_OPTIONS','_JAVA_OPTIONS','JDK_JAVA_OPTIONS']:env.pop(key,None)
 launcher=TOOLS/'ghidra_12.1.4_PUBLIC/support/analyzeHeadless.bat'
 args=['cmd.exe','/d','/c',str(launcher),str(out/'project'),'FM08_802_FULL_R5']
 if phase=='import':args+=['-import',str(private),'-analysisTimeoutPerFile','7200','-postScript','FmAnalysisCheckpointR5.java',str(out),EXPECTED]
 else:
  analysis=load(out/'analysis-result.json');assert analysis['status']=='analysis_complete','Analysis incomplete'
  assert (out/'project/FM08_802_FULL_R5.gpr').exists(),'Persistent project missing'
  args+=['-process','fm.exe','-noanalysis','-readOnly','-postScript','FmExportEngineR5.java',str(out/'decompiled'),EXPECTED,'120']
 args+=['-scriptPath',str(out/'scripts'),'-log',str(out/(phase+'-ghidra.log')),'-scriptlog',str(out/(phase+'-script.log'))]
 plan=dict(phase=phase,source=str(exe),private_input=str(private),source_sha256=EXPECTED,command=args,analysis_timeout_seconds=7200,per_function_timeout_seconds=120,disabled_analyzers=[],persistent_project=str(out/'project/FM08_802_FULL_R5.gpr'),started_at=datetime.now().astimezone().isoformat(timespec='seconds'))
 save(out/(phase+'-plan.json'),plan)
 with (out/(phase+'-stdout.log')).open('wb') as stdout,(out/(phase+'-stderr.log')).open('wb') as stderr:
  child=subprocess.Popen(args,stdout=stdout,stderr=stderr,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
  save(out/(phase+'-process.json'),dict(runner_pid=os.getpid(),root_pid=child.pid,phase=phase))
  began=time.monotonic();java_pid=None;stage=None;probe_at=0;discover_at=0;previous=None;history=[];last=None
  while True:
   now=time.monotonic()
   if now-discover_at>15:
    discover_at=now
    try:
     rows=ps("Get-CimInstance Win32_Process -Filter \"Name='java.exe'\" | Where-Object { $_.CommandLine -like '*FM08_802_FULL_R5*' -and $_.CommandLine -like '*ghidra*' -and $_.CommandLine -notlike '*LaunchSupport*' } | Select-Object ProcessId | ConvertTo-Json -Compress")
     java_pid=int(rows[0]['ProcessId']) if len(rows)==1 else None
    except (OSError,ValueError,subprocess.TimeoutExpired):pass
   jvm=sample(java_pid) if java_pid else None
   if jvm:
    if previous:jvm['cpu_percent_one_core']=round(max(0,(jvm['cpu_seconds']-previous[1])/(now-previous[0])*100),1)
    else:jvm['cpu_percent_one_core']=None
    previous=(now,jvm['cpu_seconds']);history.append(jvm['cpu_percent_one_core'] or 0);history=history[-120:];last=jvm
   if jvm and now-probe_at>60:
    probe_at=now
    try:
     p=subprocess.run([str(TOOLS/'jdk-25.0.5+8/bin/jcmd.exe'),str(java_pid),'Thread.print'],capture_output=True,timeout=8,creationflags=subprocess.CREATE_NO_WINDOW)
     frames=[l.strip() for l in p.stdout.decode('utf-8',errors='replace').splitlines() if 'ghidra.' in l and ('.added(' in l or '.analysis.' in l or 'decompileFunction(' in l)]
     selected=next((l for l in frames if '.added(' in l),frames[0] if frames else 'No named analyzer in this JVM stack sample')
     stage=dict(observed_at=datetime.now().astimezone().isoformat(timespec='seconds'),frame=selected)
    except (OSError,subprocess.TimeoutExpired):pass
   counts={}
   progress=out/'decompiled/export-progress.json'
   if progress.exists():
    try:counts=load(progress)
    except (OSError,ValueError):pass
   alive=child.poll() is None
   state=dict(status='running' if alive else 'phase_finished',phase=phase,updated_at=datetime.now().astimezone().isoformat(timespec='seconds'),elapsed_seconds=int(now-began),root_pid=child.pid,java=jvm,last_java_sample=last,last_stack_observation=stage,exit_code=child.poll(),export=counts,percent_complete=None)
   save(out/'progress.json',state)
   log=out/(phase+'-stdout.log');tail=[]
   if log.exists():
    with log.open('rb') as f:f.seek(max(0,log.stat().st_size-6500));tail=f.read().decode('utf-8',errors='replace').splitlines()[-18:]
   tail=[l for l in tail if not any(x in l.lower() for x in ['bearer','authorization','secret','token='])]
   elapsed=state['elapsed_seconds'];shown=jvm or last or {};cpu=shown.get('cpu_percent_one_core');mem=shown.get('memory_mib')
   cards=[('Czas przebiegu',f'{elapsed//60} min {elapsed%60:02d} s'),('CPU JVM / jeden rdzen','--' if cpu is None else f'{cpu:.1f}%'),('Pamiec JVM','--' if mem is None else f'{mem:.0f} MiB')]
   table=''.join('<div class="card"><small>'+html.escape(k)+'</small><strong>'+html.escape(v)+'</strong></div>' for k,v in cards)
   stage_text=html.escape(json.dumps(stage,ensure_ascii=False,indent=2)) if stage else 'Oczekiwanie na pierwsza probke stosu JVM.'
   refresh='<meta http-equiv="refresh" content="5">' if alive else ''
   page='''<!doctype html><html lang="pl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'''+refresh+'''<title>FM08 - Ghidra: analiza i eksport silnika</title><style>body{background:#101721;color:#e5edf5;font:16px/1.6 system-ui;margin:35px auto;max-width:1100px;padding:0 24px}h1{font-size:30px}.cards{display:flex;gap:16px;flex-wrap:wrap}.card,section{background:#192331;border:1px solid #2a3a4d;border-radius:12px;padding:20px}.card{flex:1;min-width:190px}small{color:#a8bbcf}strong{display:block;font-size:29px}section{margin:18px 0}pre{white-space:pre-wrap;font:13px/1.55 Consolas,monospace}h2{font-size:18px;color:#67d5b5}footer{color:#a8bbcf;font-size:13px}</style><h1>Ghidra - staly projekt i pseudokod FM08</h1><p>Etap: <b>'''+html.escape(phase)+'''</b> | Stan: '''+html.escape(state['status'])+'''<br>Pelna analiza bez pomijania analizatorow; limit importu 2 godziny.</p><div class="cards">'''+table+'''</div><section><h2>Ostatnia probka stosu JVM (co 60 s)</h2><pre>'''+stage_text+'''</pre></section><section><h2>Postep eksportu funkcji</h2><pre>'''+html.escape(json.dumps(counts,ensure_ascii=False,indent=2))+'''</pre></section><section><h2>Ostatnie komunikaty Ghidry</h2><pre>'''+html.escape('\n'.join(tail))+'''</pre></section><footer>Odswiezanie co 5 s. Brak procentu ukonczenia importu. Gra nie jest uruchamiana. Probka: '''+html.escape(state['updated_at'])+'''</footer></html>'''
   write(out/'podglad-ghidra.html',page)
   if not alive:break
   time.sleep(5)
 assert sha(exe)==EXPECTED and sha(private)==EXPECTED,'EXE hash changed'
 result=dict(phase=phase,exit_code=child.returncode,source_unchanged=True,finished_at=datetime.now().astimezone().isoformat(timespec='seconds'))
 if phase=='import' and (out/'analysis-result.json').exists():result['analysis']=load(out/'analysis-result.json')
 if phase=='export' and (out/'decompiled/export-result.json').exists():result['export']=load(out/'decompiled/export-result.json')
 save(out/(phase+'-finished.json'),result);print(json.dumps(result));return child.returncode
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--phase',choices=['import','export'],required=True);sys.exit(main(p.parse_args()))
