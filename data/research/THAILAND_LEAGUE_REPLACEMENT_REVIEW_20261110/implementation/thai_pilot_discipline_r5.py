"""Strict preflight for the newly discovered mandatory native discipline handler.
Read-only binary/static evidence. Does not patch EXE, EFA, databases or processes.
"""
import hashlib,json,sys
from pathlib import Path
import pefile
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];OUT=HERE/'package-r5-blocked'
FUNCTIONS=ROOT/'FmLauncher/data/research/GHIDRA_ENGINE_20261107_R5/decompiled/functions'
EXPECTED='157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d'
def readfn(n):return (FUNCTIONS/('ram_'+n+'.c')).read_text(encoding='utf-8')
def check_exports(prefix,exports):return any(n.lower()==prefix.lower()+'_setup_discipline_rules'for n in exports)
def main():
 binary=ROOT/'fm.exe';digest=hashlib.sha256(binary.read_bytes()).hexdigest();assert digest==EXPECTED
 pe=pefile.PE(str(binary));exports={x.name.decode('ascii')for x in pe.DIRECTORY_ENTRY_EXPORT.symbols if x.name}
 assert not check_exports('tha',exports);assert check_exports('sco',exports)
 constructor=readfn('d690a0');setup=readfn('d64730');parse=readfn('d66b00');new=readfn('d69a90');load=readfn('d69770');fixture=readfn('d69530')
 assert 'FUN_00d65300(1)'in constructor
 assert '"_setup_discipline_rules"'in setup and 'Cannot find setup_discipline_rules function for rule group'in setup
 assert 'FUN_00f4c250'not in setup and 'FUN_00f4c2e0'not in setup
 assert 'FUN_00d64730()'in new and 'FUN_00d64730()'in load
 assert 'FUN_00d68eb0'in fixture and '"_setup_fixture_rules"'in fixture
 assert 'FUN_00d63820'in parse and 'FUN_00d65340'in parse and 'FUN_00d638b0'in parse and 'FUN_00d65490'in parse
 proof=[]
 for name in ['d690a0','d65300','d66b00','d64730','d69a90','d69770','d69530','d68eb0','df6d20','ee3b90','d63120','ca6f80','d69200','d9e540','d9daf0','d9dde0']:
  f=FUNCTIONS/('ram_'+name+'.c');lines=f.read_text(encoding='utf-8').splitlines();proof.append({'address':'0x00'+name,'path':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'relevant_lines':[{'line':i+1,'text':x.strip()}for i,x in enumerate(lines)if any(k in x for k in ['_setup_discipline_rules','FUN_00d64730','FUN_00d65300','Cannot find','FUN_00d68eb0','_setup_fixture_rules','FUN_00d63820','FUN_00d65340','FUN_00d638b0','FUN_00d65490','rule_group','FUN_00ca6f80','param_1 + 0x1c'])]})
 OUT.mkdir(exist_ok=False)
 result={'status':'BLOCKED_native_discipline_handler_missing','runtime_X9':'FAILED_warning_before_accepted_start','user_warning':'Cannot find setup_discipline_rules function for rule group','exe_sha256':digest,'nation_uid':140,'nation_code':'THA','native_export_present':False,'default_discipline_sets':1,'XML_settings_parser_has_discipline_fallback':False,'new_career_requires_handler':True,'load_requires_handler':True,'stock_SCO_requires_native_discipline_export':'0x00ee3b90','explicit_XML_module_reuse':'not supported by inspected nation resource/header/settings path','standalone_discipline_rules_XML_key_in_binary':False,'R5_archives_created':False,'EXE_hook_DDL_changes_authorized':False,'constraint':'Keep ThaiUID140/codeTHA, original engine, no hook or native DLL extension','not_fixes':['add ignored discipline_rules XML','discipline_index=-1','zero settings+0x4C','click through warning','THA code changed to SCO/SIN/HKG','borrow another nation without explicit decision'],'minimum_new_native_scope_if_reconsidered':'At least provide the discipline setup entry point and audit native registration/ABI; integration not implemented or authorized.','fallback_existing_country':'Separate donor variant accepts donor native rules and possible identity/AFC compromises; not implemented or accepted.'}
 (OUT/'preflight.json').write_text(json.dumps(result,indent=2),encoding='utf-8');(OUT/'native-evidence.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
 tests={'status':'PASS_blocker_identification_not_runtime_fix','checks':[{'test':'Thai mandatory discipline export missing','passed':not check_exports('tha',exports)},{'test':'Stock SCO positive control has discipline export','passed':check_exports('sco',exports)},{'test':'Default constructor creates one mandatory discipline slot','passed':True},{'test':'Both new game and reload call same mandatory setup','passed':True},{'test':'Discipline has no XML fallback unlike fixture rules','passed':True},{'test':'No new EFA produced for unsupported schema','passed':not list(OUT.rglob('*.efa'))}]}
 (OUT/'scope-tests.json').write_text(json.dumps(tests,indent=2),encoding='utf-8');print(json.dumps({'status':result['status'],'checks':len(tests['checks']),'R5_EFA_created':False}))
if __name__=='__main__':main()
