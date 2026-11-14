"""Verify the configured REA MCP transport without opening or executing a target."""
import argparse,json,os,queue,subprocess,threading,time,tomllib
from pathlib import Path

def main(output):
    config=Path('C:/Users/Bezi/.codex/config.toml')
    current=tomllib.loads(config.read_text(encoding='utf-8-sig'))
    original=tomllib.loads(config.with_name('config.toml.rea.backup').read_text(encoding='utf-8-sig'))
    unchanged=dict(current);unchanged.pop('mcp_servers',None)
    assert unchanged==original,'Unrelated settings differ from the setup backup'
    server=current['mcp_servers']['rea'];env=dict(os.environ);env.update(server.get('env',{}))
    child=subprocess.Popen([server['command']]+server['args'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
    lines=queue.Queue();errors=[]
    def read_out():
        for line in child.stdout:lines.put(line)
        lines.put(None)
    def read_err():
        for line in child.stderr:errors.append(line.decode('utf-8',errors='replace'))
    threading.Thread(target=read_out,daemon=True).start();threading.Thread(target=read_err,daemon=True).start()
    def send(msg):child.stdin.write((json.dumps(msg)+'\n').encode('utf-8'));child.stdin.flush()
    def response(identity):
        deadline=time.monotonic()+30
        while True:
            line=lines.get(timeout=max(0.1,deadline-time.monotonic()))
            if line is None:raise RuntimeError('REA closed before answering')
            msg=json.loads(line)
            if msg.get('id')==identity:
                if 'error' in msg:raise RuntimeError(str(msg['error']))
                return msg['result']
            if time.monotonic()>deadline:raise TimeoutError('REA MCP response deadline')
    try:
        send(dict(jsonrpc='2.0',id=1,method='initialize',params=dict(protocolVersion='2025-03-26',capabilities={},clientInfo=dict(name='fm08-rea-setup-check',version='1.0'))))
        initialized=response(1);send(dict(jsonrpc='2.0',method='notifications/initialized'))
        send(dict(jsonrpc='2.0',id=2,method='tools/list',params={}))
        tools=response(2)['tools'];names=[t['name'] for t in tools]
        required=['open_binary','close_binary','binary_session','procedure_pseudo_code','procedure_references','analyze_function']
        assert all(name in names for name in required),'Required native operations absent from catalog'
        result=dict(status='mcp_transport_verified',server_info=initialized['serverInfo'],protocol_version=initialized['protocolVersion'],tool_count=len(tools),required_tools_present=required,unrelated_codex_settings_preserved=True,configured_command=server['command'],configured_args=server['args'],ghidra_install_dir=server['env']['GHIDRA_INSTALL_DIR'],java_home=server['env']['JAVA_HOME'],active_chat_mcp_tools='requires_client_restart',target_executed=False)
    finally:
        child.stdin.close()
        try:child.wait(timeout=10)
        except subprocess.TimeoutExpired:child.terminate();child.wait(timeout=10)
    result['mcp_process_exit_code']=child.returncode
    assert child.returncode==0,'REA MCP did not close cleanly'
    assert not output.exists(),'Refusing to overwrite probe report'
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=True))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();main(args.output)
