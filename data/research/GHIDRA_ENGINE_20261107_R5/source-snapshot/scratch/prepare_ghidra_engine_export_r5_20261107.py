from pathlib import Path
import json,tomllib
config=Path('C:/Users/Bezi/.codex/config.toml');before=config.read_bytes();data=tomllib.loads(before.decode('utf-8-sig'))
server=data['mcp_servers']['rea'];assert server['tool_timeout_sec']==1020 and server['env']['REA_GHIDRA_STARTUP_TIMEOUT_MS']=='900000','Configuration changed; inspect before editing'
backup=config.with_name('config.toml.rea-long-analysis-20261107.backup');assert not backup.exists(),'Backup exists';backup.write_bytes(before)
text=before.decode('utf-8-sig').replace('tool_timeout_sec = 1020','tool_timeout_sec = 7500').replace('REA_GHIDRA_STARTUP_TIMEOUT_MS = "900000"','REA_GHIDRA_STARTUP_TIMEOUT_MS = "7200000"')
assert 'REA_GHIDRA_DECOMPILE_TIMEOUT_SECONDS' not in text;text+='\nREA_GHIDRA_DECOMPILE_TIMEOUT_SECONDS = "120"\n'
after=tomllib.loads(text);expected=dict(data['mcp_servers']['rea']);expected['env']=dict(server['env']);expected['tool_timeout_sec']=7500;expected['env']['REA_GHIDRA_STARTUP_TIMEOUT_MS']='7200000';expected['env']['REA_GHIDRA_DECOMPILE_TIMEOUT_SECONDS']='120'
assert after['mcp_servers']['rea']==expected
remaining=dict(after);remaining['mcp_servers']=dict(after['mcp_servers']);remaining['mcp_servers']['rea']=data['mcp_servers']['rea'];assert remaining==data
config.write_text(text,encoding='utf-8')
root=Path('FmLauncher/data/research/GHIDRA_ENGINE_20261107_R5');(root/'mcp-timeout-update.json').write_text(json.dumps({'provider_startup_ms':7200000,'tool_timeout_sec':7500,'per_function_timeout_sec':120,'backup':str(backup),'other_settings_preserved':True},indent=2)+'\n',encoding='utf-8')
# Compile both Ghidra scripts against the installed, matching distribution before export.
tools=Path('C:/Users/Bezi/AppData/Local/Programs/REA-Tools');jars=list((tools/'ghidra_12.1.4_PUBLIC/Ghidra').rglob('*.jar'))
compiled=root/'script-compile-check';compiled.mkdir(exist_ok=False)
arguments=['-encoding','UTF-8','-classpath',';'.join(str(p) for p in jars),'-d',str(compiled.resolve())]+[str(p.resolve()) for p in (root/'scripts').glob('*.java')]
argfile=root/'javac-arguments.txt';argfile.write_text('\n'.join('"'+s.replace('\\','/').replace('"','\\"')+'"' for s in arguments)+'\n',encoding='utf-8')
import subprocess
r=subprocess.run([str(tools/'jdk-25.0.5+8/bin/javac.exe'),'@'+str(argfile.resolve())],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
(root/'javac-stdout.log').write_bytes(r.stdout);(root/'javac-stderr.log').write_bytes(r.stderr)
print(json.dumps({'configuration_updated':True,'scripts_compile_exit_code':r.returncode,'java_sources':[p.name for p in (root/'scripts').glob('*.java')]}))
if r.returncode:print(r.stderr.decode('utf-8',errors='replace'));raise SystemExit(r.returncode)
