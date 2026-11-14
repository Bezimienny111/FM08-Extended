"""Continue the same persistent Ghidra project into export after a verified import."""
import argparse,json,subprocess,sys,time
from datetime import datetime
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main(out):
    finish=out/'import-finished.json'
    state=dict(status='waiting_for_persistent_import',supervisor_pid=__import__('os').getpid(),started_at=datetime.now().astimezone().isoformat(timespec='seconds'))
    save(out/'pipeline.json',state)
    while not finish.exists():
        if (out/'PAUSE_REQUESTED').exists():
            state['status']='paused_by_user';save(out/'pipeline.json',state);return
        time.sleep(5)
    imported=load(finish)
    if imported['exit_code']!=0 or imported.get('analysis',{}).get('status')!='analysis_complete':
        state.update(status='import_needs_review',import_result=imported);save(out/'pipeline.json',state);return
    if (out/'PAUSE_REQUESTED').exists():
        state['status']='paused_by_user';save(out/'pipeline.json',state);return
    assert (out/'project/FM08_802_FULL_R5.gpr').exists(),'Saved native project absent'
    state['status']='exporting_from_saved_project';save(out/'pipeline.json',state)
    with (out/'runner-export.log').open('wb') as stdout,(out/'runner-export-stderr.log').open('wb') as stderr:
        p=subprocess.Popen([sys.executable,str(ROOT/'FM08-Database-Tools/scratch/run_ghidra_engine_r5_20261107.py'),'--output',str(out),'--phase','export'],stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
        state['export_runner_pid']=p.pid;save(out/'pipeline.json',state);exit_code=p.wait()
    state.update(status='export_finished_needs_audit',export_runner_exit_code=exit_code,finished_at=datetime.now().astimezone().isoformat(timespec='seconds'))
    if (out/'export-finished.json').exists():state['export_result']=load(out/'export-finished.json')
    save(out/'pipeline.json',state)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();main(args.output.resolve())
