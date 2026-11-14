"""Live local HTML preview for one REA/Ghidra run. Queries process counters only."""
import argparse,ctypes,html,json,os,time,subprocess
from ctypes import wintypes as w
from datetime import datetime
from pathlib import Path

k=ctypes.WinDLL('kernel32',use_last_error=True);ps=ctypes.WinDLL('psapi',use_last_error=True)
k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
k.CloseHandle.argtypes=[w.HANDLE];k.GetProcessTimes.argtypes=[w.HANDLE,ctypes.POINTER(w.FILETIME),ctypes.POINTER(w.FILETIME),ctypes.POINTER(w.FILETIME),ctypes.POINTER(w.FILETIME)]
class Memory(ctypes.Structure):
    _fields_=[('cb',w.DWORD),('PageFaultCount',w.DWORD)]+[(n,ctypes.c_size_t) for n in ['PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage']]
ps.GetProcessMemoryInfo.argtypes=[w.HANDLE,ctypes.POINTER(Memory),w.DWORD]
def ft(t):return ((t.dwHighDateTime<<32)|t.dwLowDateTime)/10_000_000

def sample(pid):
    h=k.OpenProcess(0x410,False,pid)
    if not h:return None
    try:
        created,ended,kernel,user=(w.FILETIME() for _ in range(4))
        if not k.GetProcessTimes(h,ctypes.byref(created),ctypes.byref(ended),ctypes.byref(kernel),ctypes.byref(user)):return None
        m=Memory();m.cb=ctypes.sizeof(m)
        if not ps.GetProcessMemoryInfo(h,ctypes.byref(m),m.cb):return None
        return dict(pid=pid,created=ft(created),cpu_seconds=ft(kernel)+ft(user),memory_mib=round(m.WorkingSetSize/1048576,1),elapsed_seconds=max(0,int(time.time()-(ft(created)-11644473600))))
    finally:k.CloseHandle(h)

def write(path,data):
    temporary=path.with_suffix(path.suffix+'.tmp');temporary.write_text(data,encoding='utf-8');os.replace(temporary,path)

def main(a):
    out=a.output;out.mkdir(parents=True,exist_ok=True);history=[];previous=None;observed={};began=time.monotonic();latest=None;stage=None;last_stage_probe=0
    while True:
        now=time.monotonic();jvm=sample(a.java_pid);rea=sample(a.rea_pid)
        for kind,item in [('java',jvm),('rea',rea)]:
            if item:
                if kind in observed and observed[kind]!=item['created']:
                    if kind=='java':jvm=None
                    else:rea=None
                else:observed[kind]=item['created']
        if jvm:
            latest=jvm
            if previous:
                jvm['cpu_percent_one_core']=round(max(0,(jvm['cpu_seconds']-previous[1])/(now-previous[0])*100),1)
            else:jvm['cpu_percent_one_core']=None
            previous=(now,jvm['cpu_seconds']);history.append(jvm['cpu_percent_one_core'] or 0);history=history[-100:]
        if jvm and now-last_stage_probe>60:
            last_stage_probe=now
            try:
                command='C:/Users/Bezi/AppData/Local/Programs/REA-Tools/jdk-25.0.5+8/bin/jcmd.exe'
                probe=subprocess.run([command,str(a.java_pid),'Thread.print'],capture_output=True,timeout=8,creationflags=subprocess.CREATE_NO_WINDOW)
                frames=[line.strip() for line in probe.stdout.decode('utf-8',errors='replace').splitlines() if 'ghidra.' in line and ('.added(' in line or '.analyze(' in line or '.analysis.' in line)]
                selected=next((line for line in frames if '.added(' in line),frames[0] if frames else 'Brak nazwanego analizatora w próbce stosu')
                stage=dict(observed_at=datetime.now().astimezone().isoformat(timespec='seconds'),frame=selected)
            except (OSError,subprocess.TimeoutExpired):pass
        sizes={p.name:p.stat().st_size for p in out.glob('*') if p.is_file() and p.name in ['pol_get_settings-r4.json','decompile-r4-stderr.log','fm802-r4.snapshot.json','setup.json','mcp-probe.json']}
        running=rea is not None
        title='Ghidra analizuje fm.exe' if jvm else ('REA przygotowuje wynik' if running else 'Przebieg REA zakończony')
        status=dict(updated_at=datetime.now().astimezone().isoformat(timespec='seconds'),running=running,java=jvm,last_java_sample=latest,rea_process_alive=running,completion_percent=None,last_stack_observation=stage,file_sizes=sizes,progress_source='Windows process counters and output file sizes; Ghidra emits no percentage',history_cpu_one_core=history)
        write(out/'progress.json',json.dumps(status,ensure_ascii=False,indent=2)+'\n')
        shown=jvm or latest or {};elapsed=shown.get('elapsed_seconds',0);duration=f'{elapsed//60} min {elapsed%60:02d} s'
        cpu=shown.get('cpu_percent_one_core');cpu_text='—' if cpu is None else f'{cpu:.1f}%'
        memory=shown.get('memory_mib');mem_text='—' if memory is None else f'{memory:.0f} MiB'
        log=[]
        for path in [out/'decompile-r4-stderr.log',a.runtime/'ghidra.log',a.runtime/'script.log']:
            if path.is_file() and path.stat().st_size:
                for line in path.read_text(encoding='utf-8-sig',errors='replace').splitlines()[-8:]:
                    if not any(word in line.lower() for word in ['token','authorization','secret','bearer']):log.append(line)
        if stage:log.insert(0,'Próbka stosu JVM '+stage['observed_at']+'\n'+stage['frame'])
        log_text='\n'.join(log[-12:]) or 'Ghidra nie opublikowała jeszcze komunikatów w logach. Aktywność jest mierzona na podstawie procesu JVM.'
        bars=''.join(f'<i style="height:{max(2,min(100,x/4)):.1f}%" title="{x:.1f}% jednego rdzenia"></i>' for x in history)
        table=''.join('<tr><td>'+html.escape(n)+'</td><td>'+f'{size:,}'.replace(',',' ')+' B</td></tr>' for n,size in sorted(sizes.items()))
        text='''<!doctype html><html lang="pl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="3"><title>Ghidra — podgląd analizy FM08</title><style>
*{box-sizing:border-box}body{margin:0;background:#101721;color:#e6edf6;font:16px/1.55 system-ui,sans-serif}main{max-width:1050px;margin:45px auto;padding:0 25px}h1{font-size:32px;margin:8px 0}p{color:#a9bbce}.eyebrow{color:#67d5b5;letter-spacing:2px;font-size:12px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:26px 0}.card,section{background:#192331;border:1px solid #2a3a4d;border-radius:14px;padding:22px}.value{font-size:32px;font-weight:650;color:#fff}.label{font-size:13px;color:#a9bbce}.chart{display:flex;align-items:end;height:95px;gap:3px;margin-top:15px}.chart i{background:#67d5b5;flex:1;border-radius:2px 2px 0 0;max-width:12px}section{margin:16px 0}h2{font-size:18px;margin:0 0 12px}pre{white-space:pre-wrap;font:13px/1.5 Consolas,monospace;color:#becfe2}table{width:100%;border-collapse:collapse;font-size:14px}td{padding:8px;border-bottom:1px solid #2a3a4d}td:last-child{text-align:right}footer{font-size:12px;color:#8ea3ba;margin:25px 0}.state{display:inline-block;border:1px solid #67d5b5;color:#67d5b5;border-radius:30px;padding:4px 13px;font-size:12px}@media(max-width:650px){.grid{grid-template-columns:1fr}.value{font-size:25px}}
</style><main><div class="eyebrow">FM08 · REA 6.8.0 / GHIDRA 12.1.4</div><h1>__TITLE__</h1><span class="state">__STATE__</span><p>Cel: odczyt pseudokodu <strong>pol_get_settings · 0x00E8DDC0</strong>.<br>Panel odświeża się co 3 sekundy. Gra nie jest uruchamiana.</p><div class="grid"><div class="card"><div class="label">Czas pracy JVM</div><div class="value">__DURATION__</div></div><div class="card"><div class="label">CPU JVM · 100% = jeden rdzeń</div><div class="value">__CPU__</div></div><div class="card"><div class="label">Pamięć procesu JVM</div><div class="value">__MEMORY__</div></div></div><section><h2>Aktywność CPU</h2><div class="chart">__BARS__</div><p class="label">Kolejne próbki co 3 s; wysokość wykresu do 400%. To pomiar aktywności, nie procent ukończenia.</p></section><section><h2>Komunikaty Ghidry / REA</h2><pre>__LOG__</pre></section><section><h2>Pliki wynikowe</h2><table>__TABLE__</table></section><footer>Ostatnia próbka: __UPDATED__ · Brak dostępnego procentu postępu. Zakończenie procesu wymaga osobnej kontroli wyniku.</footer></main></html>'''
        replacements={'__TITLE__':title,'__STATE__':'W trakcie' if running else 'Proces zakończył pracę','__DURATION__':duration,'__CPU__':cpu_text,'__MEMORY__':mem_text,'__BARS__':bars,'__LOG__':html.escape(log_text),'__TABLE__':table,'__UPDATED__':html.escape(status['updated_at'])}
        for key,value in replacements.items():text=text.replace(key,value)
        try:write(out/'podglad-ghidra.html',text)
        except PermissionError:pass
        if not running or now-began>3600:break
        time.sleep(3)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--java-pid',type=int,required=True);p.add_argument('--rea-pid',type=int,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True);main(p.parse_args())
