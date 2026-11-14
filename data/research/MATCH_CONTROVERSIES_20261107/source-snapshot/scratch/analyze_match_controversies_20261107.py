"""Static FM08 commentary/dissent audit. Never runs or patches the game."""
import argparse,hashlib,json,re,shutil,struct,sys
from pathlib import Path
import capstone,pefile
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];REPO=ROOT/'FM08-Database-Tools'
EXPECTED='157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d'
EVENTS=[408,409,429,733,736]+list(range(893,921))+[957]
REGIONS=[('config_event_id_parse',0xb0762e,0xb07740),('action_debug_name_switch',0xb2c7a5,0xb2c827),('group_reaction',0xb5bb80,0xb5bde6),('individual_reaction',0xb6afd0,0xb6b4e9),('reaction_choice',0xb63b10,0xb63d38),('effective_parameter_source',0xb62c70,0xb62e30),('runtime_state_update',0xb30450,0xb30546),('dissent_action_dispatch',0xb64ae0,0xb64c21),('random_wrapper',0xb48b90,0xb48b9e),('distance_helper',0xad40b0,0xad4140)]

def require(ok,label):
    if not ok:raise ValueError(label)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def analyze(output):
    require(not output.exists(),'output exists; use a new directory')
    source_paths=[ROOT/'fm.exe',ROOT/'data/match events/events.cfg',ROOT/'data/languages/polish.ltc',ROOT/'data/updates/update-802/data/languages/changes/polish.ltc']
    pins={str(p.relative_to(ROOT)):sha(p) for p in source_paths};require(pins['fm.exe']==EXPECTED,'unsupported EXE hash')
    data=source_paths[0].read_bytes();pe=pefile.PE(data=data);base=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    def offset(va):return pe.get_offset_from_rva(va-base)
    def u32(va):return struct.unpack_from('<I',data,offset(va))[0]
    def instructions(start,end):return list(md.disasm(data[offset(start):offset(start)+end-start],start))
    def literal(va):
        start=offset(va);end=data.index(b'\0',start);return data[start:end].decode('ascii')
    checks=[]
    def check(name,ok):require(ok,name);checks.append(name)
    anchors=[(0xb2c7f7,'push','0x158d70c'),(0xb6b3d3,'push','0x76d'),(0xb6b434,'push','0x76d'),(0xb6b4b0,'push','0x76d'),(0xb6b4bc,'call','0xb64ae0'),(0xb63d1e,'call','0xb48b90'),(0xb48b99,'jmp','0xf56800'),(0xb30468,'mov','ecx, dword ptr [esi + 0x1118]'),(0xb3047b,'mov','dword ptr [esi + 0x108c], eax'),(0xb3053b,'mov','dword ptr [esi + 0x108c], eax'),(0xb62db3,'mov','dword ptr [ecx + 0x1118], edx'),(0xb5bd0d,'call','0xad40b0'),(0xb5bd5e,'call','0xb6afd0')]
    for va,mn,op in anchors:
        ins=instructions(va,va+15)[0];check('native anchor '+hex(va),(ins.mnemonic,ins.op_str)==(mn,op))
    check('native ME_DISSENT debug name',literal(0x158d70c)=='ME_DISSENT')
    action_map={}
    for action in range(0x708,0x7d1):
        table_index=data[offset(0xb2ce9c+action-0x708)]
        if table_index>13:continue
        target=u32(0xb2ce60+4*table_index)
        if target not in [0xb2c7e9,0xb2c7f0,0xb2c7f7,0xb2c7fe,0xb2c805,0xb2c80c,0xb2c813]:continue
        ins=instructions(target,target+5)[0];check('action name case '+hex(action),ins.mnemonic=='push' and ins.operands[0].type==capstone.x86.X86_OP_IMM)
        action_map[hex(action)]=dict(name=literal(ins.operands[0].imm),switch_target=hex(target))
    check('ME_DISSENT action selector resolved',action_map['0x76d']['name']=='ME_DISSENT')
    text=source_paths[1].read_text(encoding='utf-16');starts=list(re.finditer(r'^# (EVENT_[^\r\n]*)',text,re.M));records={}
    for i,match in enumerate(starts):
        end=starts[i+1].start() if i+1<len(starts) else len(text);block=text[match.start():end]
        config=re.search(r'^=\s*(\d+)[^\r\n]*',block,re.M)
        if not config:continue
        event=int(config.group(1))
        if event not in EVENTS:continue
        records[event]=dict(id=event,symbol=match.group(1).strip(),line=text.count('\n',0,match.start())+1,config=config.group(0),polish=[l.split(': ',1)[1] for l in block.splitlines() if l.startswith('INGAME POLISH: ')],english=[l.split(': ',1)[1] for l in block.splitlines() if l.startswith('INGAME ENGLISH: ')])
    check('requested event categories present',all(e in records for e in [409,429,733,894,896,898,900,916,919,957]))
    check('quoted cannot-believe text belongs to goal-stand protest',any('własnym oczom' in s for s in records[894]['polish']))
    check('surrounding-referee phrase exists',any('otaczają sędziego' in s for s in records[409]['polish']))
    check('reaction-choice cases match six-way jump table',[u32(0xb63d38+4*i) for i in range(6)]==[0xb63bda,0xb63c33,0xb63c95,0xb63cb8,0xb63cd7,0xb63cf6])
    check('runtime upper clamp is 100',instructions(0xb30532,0xb30537)[0].op_str=='eax, 0x64')
    disassembly=[]
    for label,start,end in REGIONS:
        disassembly.append('\n'+label+' '+hex(start)+'..'+hex(end))
        disassembly.extend('%08X %-8s %s'%(i.address,i.mnemonic,i.op_str) for i in instructions(start,end))
    media=[]
    for m in re.finditer(rb'OFFICIAL_REACTION_TO_MANAGER_COMPLAINING_ABOUT_REFEREE_NEWS',data):
        start=data.rfind(b'\0',max(0,m.start()-1500),m.start())+1;end=data.find(b'\0',m.start());s=data[start:end].decode('ascii',errors='replace')
        if 'disallowed' in s and 'replays' in s:media.append(dict(va=hex(base+pe.get_rva_from_offset(start)),text=s))
    source_unchanged=pins=={str(p.relative_to(ROOT)):sha(p) for p in source_paths};check('all audited game files unchanged',source_unchanged)
    output.mkdir(parents=True)
    report=dict(status='static_commentary_and_dissent_paths_audited',exe_sha256=EXPECTED,input_hashes=pins,checks=checks,commentary_events=[records[e] for e in sorted(records)],native_actions=action_map,native_reaction_function='0x00B6AFD0',native_reaction_chooser='0x00B63B10',native_group_reaction='0x00B5BB80',runtime_state=dict(offset='0x108C',upper_bound=100,official_attribute_name='not_identified',interpretation='dynamic reaction intensity; semantic inference'),effective_parameter=dict(offset='0x1118',direct_source_offset='0x444',raw_database_attribute='not_identified'),native_confirmed=['ME_DISSENT action 0x76D resolved by named debug switch','conditional reaction branches select dissent or other referee-related actions','reaction chooser calls match RNG','group reaction includes coordinate differences and distance computation','runtime reaction state is updated, bounded and used in choice gates'],media_replay_correctness_variants=media,unresolved=['exact goal award/disallow decision probability','mapping the raw database personality attributes to the effective parameter','full native-to-commentary mapping for event 894','which branch produces event 916 versus 919','live-match execution and frequency measurements'],numeric_collision_warning=dict(event_id=409,unrelated_native_return_function='0x007CEC30',rtti_class='MEDIA_PLAYER_MORALE_NEWS',meaning='Do not equate a matching small integer with a commentary event; RTTI disproved this candidate.'),game_executed=False,game_patched=False,inputs_unchanged=True)
    save(output/'report.json',report);(output/'disassembly.txt').write_text('\n'.join(disassembly)+'\n',encoding='utf-8')
    save(output/'events.json',report['commentary_events'])
    print(json.dumps(dict(status=report['status'],checks_passed=len(checks),events_identified=len(records),dissent_action='0x76D',inputs_unchanged=True,game_executed=False)))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();analyze(a.output)
