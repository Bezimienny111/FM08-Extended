import hashlib,json,os,pathlib,pefile,struct,subprocess
root=pathlib.Path('J:/FM08dev'); out=root/'FmLauncher/data/research/POLAND_THIRD_TIER_R6_20261107'; r=root/'FmLauncher/data/research/GHIDRA_ENGINE_20261107_R5'
project=r/'project-research'; expected=json.loads((r/'result.json').read_text())['source_sha256']; raw=(root/'fm.exe').read_bytes();assert hashlib.sha256(raw).hexdigest()==expected
pe=pefile.PE(data=raw); base=pe.OPTIONAL_HEADER.ImageBase
address=0xf08c60;prefix=raw[pe.get_offset_from_rva(address-base):][:16].hex()
assert struct.unpack_from('<I',raw,pe.get_offset_from_rva(0x165a0ec+0x160-base))[0]==address
assert not (out/'known-entry-prefixes.json').exists()
(out/'known-entry-prefixes.json').write_text(json.dumps([dict(label='ENG_FIRST_rules',address=hex(address),prefix=prefix)],indent=2)+'\n')
def pins():return {str(p.relative_to(project)):hashlib.sha256(p.read_bytes()).hexdigest() for p in project.rglob('*') if p.is_file() and not p.name.endswith('.lock')}
before=pins();(out/'research-project-before.json').write_text(json.dumps(before,indent=2)+'\n')
tools=pathlib.Path('C:/Users/Bezi/AppData/Local/Programs/REA-Tools'); env=dict(os.environ); env['JAVA_HOME']=str(tools/'jdk-25.0.5+8');env['GHIDRA_HEADLESS_MAXMEM']='2G';env['PATH']=str(tools/'jdk-25.0.5+8/bin')+os.pathsep+env.get('PATH','')
args=['cmd.exe','/d','/c',str(tools/'ghidra_12.1.4_PUBLIC/support/analyzeHeadless.bat'),str(project),'FM08_802_FULL_R5','-process','fm.exe','-noanalysis','-readOnly','-postScript','FmRecoverKnownEntriesR5.java',str(out),expected,'-scriptPath',str(r/'scripts'),'-log',str(out/'targeted-ghidra.log'),'-scriptlog',str(out/'targeted-script.log')]
(out/'targeted-plan.json').write_text(json.dumps(dict(command=args,read_only=True,autoanalysis=False),indent=2)+'\n')
with (out/'targeted-stdout.log').open('wb') as so,(out/'targeted-stderr.log').open('wb') as se:
 p=subprocess.run(args,stdout=so,stderr=se,env=env,creationflags=subprocess.CREATE_NO_WINDOW,timeout=900)
assert p.returncode==0, 'Headless failed'
f=out/'supplemental/recovery-result.json';assert f.exists(), 'Native exit zero does not prove script succeeded; missing result'
manifest=json.loads(f.read_text()); assert manifest['status']=='supplemental_entries_exported' and len(manifest['entries'])==1
assert pins()==before, 'Research project changed'
assert hashlib.sha256((root/'fm.exe').read_bytes()).hexdigest()==expected
(out/'targeted-audit.json').write_text(json.dumps(dict(status='verified',entries=manifest['entries'],read_only=True,project_unchanged=True,original_exe_unchanged=True),indent=2)+'\n')
print(json.dumps(dict(status='verified',new_pseudocode=manifest['entries'][0]['path'],project_unchanged=True)))
