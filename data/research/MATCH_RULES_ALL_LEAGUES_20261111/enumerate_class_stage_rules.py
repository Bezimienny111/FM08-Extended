"""Pinned native class->COMP registration, stage-method CFG facts and XML subs rules."""
from pathlib import Path
import sys,json,struct,re,collections,bisect,hashlib,xml.etree.ElementTree as ET
import pefile,capstone
sys.dont_write_bytecode=True
ROOT=Path.cwd();B=ROOT/'FmLauncher/data/research/MATCH_RULES_ALL_LEAGUES_20261111'
raw=(ROOT/'fm.exe').read_bytes();assert hashlib.sha256(raw).hexdigest()=='157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d'
pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
def va(p):return base+pe.get_rva_from_offset(p)
def off(a):return pe.get_offset_from_rva(a-base)
def dump(name,value):(B/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
vt=json.loads((B/'rtti-vftables.json').read_text())
primary={v['vftable']:v for v in vt if v['object_offset']==0}
sec=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text');lo=sec.PointerToRawData;hi=lo+sec.SizeOfRawData
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
def inst(a):
 try:return next(md.disasm(raw[off(a):off(a)+16],a),None)
 except (StopIteration,pefile.PEFormatError):return None
bindings=[]
for m in re.finditer(rb'\xe8',raw[lo:hi]):
 p=lo+m.start();target=va(p)+5+struct.unpack_from('<i',raw,p+1)[0]
 if target!=0xd805b0:continue
 call=va(p);chosen=None
 for z in md.disasm(raw[p+5:p+205],call+5):
  if z.mnemonic.startswith('ret'):break
  op=z.operands
  if z.mnemonic=='mov' and len(op)==2 and op[0].type==capstone.x86.X86_OP_MEM and op[0].mem.disp==0 and op[1].type==capstone.x86.X86_OP_IMM and op[1].imm in primary:
   chosen=(z,primary[op[1].imm]);break
 if not chosen:continue
 # A literal push in the argument window must decode continuously through the exact base call.
 pushes=[]
 for pp in range(max(lo,p-48),p):
  if raw[pp]not in[0x68,0x6a,0x50,0x51,0x52,0x53,0x54,0x55,0x56,0x57]:continue
  seq=list(md.disasm(raw[pp:p+5],va(pp)))
  if not seq or seq[0].mnemonic!='push' or not seq[0].operands:continue
  if seq[-1].address!=call or seq[-1].mnemonic!='call':continue
  value=seq[0].operands[0].imm if seq[0].operands[0].type==capstone.x86.X86_OP_IMM else None
  pushes.append((pp,value))
 if not pushes:continue
 pushp,uid=max(pushes,key=lambda q:q[0])
 if uid is None or not 0<uid<0x7fffffff:continue
 z,v=chosen
 bindings.append(dict(native_class=v['name'],competition_uid=uid,base_constructor_call=hex(call),uid_push_address=hex(va(pushp)),root_vtable_write=hex(z.address),vftable=hex(v['vftable']),slot88=hex(v['functions'][88])if len(v['functions'])>88 else None,confidence='derived_literal_constructor_registration'))
# Keep every independent binding; reject contradictory UID registrations for same class.
byclass=collections.defaultdict(list)
for r in bindings:byclass[r['native_class']].append(r)
classes=list({(v['native_class'],v['competition_uid']):v for v in bindings}.values())
dump('multiple-COMP-UID-classes.json',{k:v for k,v in byclass.items()if len({x['competition_uid']for x in v})>1})
factories={int(x['slot88'],16)for x in classes if x['slot88']}
regparts={'eax':['eax','ax','al','ah'],'ebx':['ebx','bx','bl','bh'],'ecx':['ecx','cx','cl','ch'],'edx':['edx','dx','dl','dh'],'esi':['esi','si'],'edi':['edi','di'],'ebp':['ebp','bp'],'esp':['esp','sp']}
alias={r:k for k,vs in regparts.items()for r in vs}
def assign(reg,val,state):
 family=alias.get(reg,reg)
 for r in regparts.get(family,[family]):state.pop(r,None)
 if val is None:return
 state[reg]=val
 if reg in ['eax','ebx','ecx','edx','ax','bx','cx','dx']:state[family[1]+'l']=val&255
def regval(op,state):
 if op.type==capstone.x86.X86_OP_IMM:return op.imm
 if op.type==capstone.x86.X86_OP_REG:return state.get(md.reg_name(op.reg))
 return None
cache={}
def scan(entry):
 if entry in cache:return cache[entry]
 todo=[(entry,{})];seen=set();writes={};calls=set();branches={};unknown=[];count=0
 while todo and count<16000:
  pc,state=todo.pop();tag=(pc,tuple(sorted(state.items())))
  if tag in seen:continue
  seen.add(tag);count+=1
  if pc!=entry and pc in factories:unknown.append(dict(address=hex(pc),reason='tail/delegation_to_other_slot88_method'));continue
  if not entry<=pc<entry+0x18000:unknown.append(dict(address=hex(pc),reason='branch_outside_bounded_method_window'));continue
  z=inst(pc)
  if z is None:unknown.append(dict(address=hex(pc),reason='decode_failed'));continue
  ops=z.operands;nextpc=pc+z.size;new=dict(state)
  if z.mnemonic in ['cmp','test']:branches[pc]=z.mnemonic+' '+z.op_str
  if z.mnemonic=='mov'and len(ops)==2:
   dst,src=ops
   if dst.type==capstone.x86.X86_OP_MEM and dst.mem.base not in [capstone.x86.X86_REG_ESP,capstone.x86.X86_REG_EBP]and 0x2e<=dst.mem.disp<=0x31<dst.mem.disp+dst.size:
    whole=regval(src,state);value=((whole>>((0x31-dst.mem.disp)*8))&255)if whole is not None else None
    key=(pc,value);writes[key]=dict(address=hex(pc),code=value if value is not None and 0<=value<=28 else None,instruction=z.mnemonic+' '+z.op_str,value_status='constant_in_CFG_path'if value is not None else'dynamic_or_unresolved',source_register_value=whole,field_byte_value=value,memory_base=md.reg_name(dst.mem.base),packed_write_size=dst.size)
   if dst.type==capstone.x86.X86_OP_REG:assign(md.reg_name(dst.reg),regval(src,state),new)
  elif z.mnemonic=='xor'and len(ops)==2 and ops[0].type==ops[1].type==capstone.x86.X86_OP_REG and ops[0].reg==ops[1].reg:assign(md.reg_name(ops[0].reg),0,new)
  elif z.mnemonic in ['movzx','movsx','lea','pop','inc','dec','and','or','add','sub','shl','shr','sar','imul','neg','not']and ops and ops[0].type==capstone.x86.X86_OP_REG:
   assign(md.reg_name(ops[0].reg),None,new)
  if z.mnemonic=='call':
   if ops and ops[0].type==capstone.x86.X86_OP_IMM:calls.add(ops[0].imm)
   else:unknown.append(dict(address=hex(pc),reason='indirect_call_semantics_not_expanded'))
   for fam in ['eax','ecx','edx']:
    for rr in regparts[fam]:new.pop(rr,None)
  if z.mnemonic.startswith('ret'):continue
  if z.mnemonic.startswith('j'):
   if ops and ops[0].type==capstone.x86.X86_OP_IMM:
    target=ops[0].imm
    branches[pc]=z.mnemonic+' '+z.op_str
    todo.append((target,new))
   else:unknown.append(dict(address=hex(pc),reason='indirect_jump_or_jump_table_unresolved'))
   if z.mnemonic=='jmp':continue
  todo.append((nextpc,new))
 if todo:unknown.append(dict(reason='CFG_state_budget_exhausted'))
 value=dict(entry=hex(entry),decoded_states=count,writes=list(writes.values()),direct_calls=[hex(x)for x in sorted(calls)],branch_instructions=[dict(address=hex(a),instruction=t)for a,t in sorted(branches.items())],unknowns=unknown,paths_complete_for_direct_CFG=not any('indirect_jump'in x.get('reason','')or'budget'in x.get('reason','')or'decode_failed'in x.get('reason','')for x in unknown))
 cache[entry]=value;return value

# Explicit MSVC class hierarchy coverage includes definitions with parameterised COMP UID.
hierarchy=[]
for v in vt:
 if v['object_offset']!=0:continue
 hp=struct.unpack_from('<I',raw,off(v['locator'])+16)[0]
 sig,attrs,n,arr=struct.unpack_from('<4I',raw,off(hp))
 if n>512:continue
 names=[]
 for j in range(n):
  bc=struct.unpack_from('<I',raw,off(arr)+4*j)[0]
  td=struct.unpack_from('<I',raw,off(bc))[0];p=off(td)+8
  names.append(raw[p:raw.find(b'\0',p)].decode('ascii',errors='replace'))
 if '.?AVCOMP@@'in names:
  hierarchy.append(dict(native_class=v['name'],vftable=hex(v['vftable']),base_types=names,slot88=hex(v['functions'][88])if len(v['functions'])>88 else None))
known={c['native_class']for c in classes}
for h in hierarchy:
 if h['native_class']not in known:
  classes.append(dict(h,competition_uid=None,confidence='RTTI_COMP_subclass_UID_unresolved',base_constructor_call=None,uid_push_address=None,root_vtable_write=None))
dump('COMP-RTTI-hierarchy.json',hierarchy)
factories.update(int(x['slot88'],16)for x in classes if x['slot88'])

for n,c in enumerate(classes):
 c['stage_method']=scan(int(c['slot88'],16))if c['slot88']else None
 if n%100==0:print('CLASS CFG',n,'/',len(classes),flush=True)
enum=[]
anchor=raw.find(struct.pack('<I',0x15f6110))
for p in range(anchor-16,anchor+27*8,8):
 ptr,code=struct.unpack_from('<II',raw,p);s=off(ptr);value=raw[s:raw.find(b'\0',s)].decode('ascii')
 enum.append(dict(code=code,key=value,entry_address=hex(va(p)),key_address=hex(ptr)))
assert {v['code']for v in enum}==set(range(29))
dump('native-subs-enum.json',sorted(enum,key=lambda r:r['code']))
keys={r['key']:r['code']for r in enum}
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'));import pol3_efa_r8_20261107 as efa
members={};resources=[]
for rel in ['data/comps.efa','data/updates/update-802/data/comps.efa']:
 a=efa.parse((ROOT/rel).read_bytes())
 assert a['source_sha256']==efa.EXPECTED_SOURCE_SHA256[rel]
 for path,body in a['members'].items():members[path]=(rel,body)
 for path,body in a['members'].items():resources.append(dict(archive=rel,archive_sha256=a['source_sha256'],member=path,member_sha256=hashlib.sha256(body).hexdigest()))
xmlrows=[]
for member,(archive,body)in members.items():
 try:root=ET.fromstring(body)
 except ET.ParseError:continue
 def walk(node,path,context):
  here=path+'/'+node.tag+('['+','.join(k+'='+v for k,v in node.attrib.items())+']'if node.attrib else'')
  context=context+[dict(tag=node.tag,attributes=node.attrib)]if node.tag=='record'else context
  if node.attrib.get('id')=='subs_rules':
   value=node.attrib.get('value');xmlrows.append(dict(competition_uid=root.attrib.get('competition'),resource=member,archive=archive,path=here,enum_key=value,code=keys.get(value),context=context,evidence_status='explicit_XML_value_plus_native_enum_binding'))
  for ch in node:walk(ch,here,context)
 walk(root,'',[])
dump('competition-class-bindings.json',classes)
dump('stage-method-CFG-cache.json',list(cache.values()))
dump('resource-subs-rules.json',xmlrows)
dump('resource-source-pins.json',resources)
summary=dict(classes=len(classes),unique_slot88_methods=len(cache),classes_with_explicit_code=sum(bool(c['stage_method']and c['stage_method']['writes'])for c in classes),codes_seen=sorted({w['code']for c in classes if c['stage_method']for w in c['stage_method']['writes']if w['code']is not None}),xml_explicit_rows=len(xmlrows),xml_codes=sorted({r['code']for r in xmlrows if r['code']is not None}))
dump('stage-map-summary.json',summary);print(json.dumps(summary))
