"""Bounded intraprocedural CFG check; not a universal executor completion proof."""
import hashlib,json,struct
from pathlib import Path
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_GRP_JUMP, CS_GRP_RET
from capstone.x86 import X86_OP_IMM
ROOT=Path(__file__).parent
EXE=ROOT.parents[3]/"fm.exe"
# Resolve from workspace explicitly; source may be opened read-only.
EXE=Path("fm.exe")
HASH="157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d"
def run():
 raw=EXE.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=HASH:raise ValueError("EXE hash mismatch")
 pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase
 def data(a,n):return pe.get_data(a-base,n)
 idx=json.loads(Path("FmLauncher/data/research/GHIDRA_ENGINE_20261107_R5/decompiled/function-index.json").read_text("utf-8"))
 record=next(f for f in idx["functions"] if f["address"]=="00aef770")
 cs=Cs(CS_ARCH_X86,CS_MODE_32);cs.detail=True
 instructions={}
 body=b""
 for r in record["body_ranges"]:
  start,end=int(r["start"],16),int(r["end"],16)
  block=data(start,end-start+1);body+=block
  parsed=list(cs.disasm(block,start))
  if sum(i.size for i in parsed)!=len(block):raise ValueError("incomplete body disassembly")
  instructions.update((i.address,i) for i in parsed)
 tables={0xaefa55:tuple(struct.unpack("<5I",data(0xaf83d4,20))),
         0xaf3ed9:tuple(struct.unpack("<5I",data(0xaf83e8,20)))}
 edges={};unknown=[]
 for a,i in instructions.items():
  after=a+i.size;targets=[]
  if i.group(CS_GRP_RET) or i.mnemonic in ("int3","ud2","hlt"): pass
  elif i.group(CS_GRP_JUMP):
   if i.operands[0].type==X86_OP_IMM:targets=[i.operands[0].imm]
   elif a in tables:targets=list(tables[a])
   else:unknown.append(hex(a))
   if i.mnemonic!="jmp" and after in instructions:targets.append(after)
  elif after in instructions:targets=[after]
  edges[a]=targets
 outside=[(hex(a),hex(b)) for a,ts in edges.items() for b in ts if b not in instructions]
 if unknown or outside:raise ValueError(("unresolved CFG",unknown,outside))
 calls=[a for a,i in instructions.items() if i.mnemonic=="call" and i.operands[0].type==X86_OP_IMM and i.operands[0].imm==0xaecae0]
 writes=[0xaf0608,0xaf8286]
 def reachable(start,stop,blocked):
  todo=[start];seen=set()
  while todo:
   a=todo.pop()
   if a in blocked or a in seen:continue
   if a==stop:return True
   seen.add(a);todo+=edges[a]
  return False
 queries=[]
 for start in (0xaef770,0xaf07f6):
  for stop in writes:
   queries.append({"start":hex(start),"tick_writer":hex(stop),
     "reachable":reachable(start,stop,set()),
     "reachable_without_any_dispatcher":reachable(start,stop,set(calls)),
     "reachable_without_main_dispatcher":reachable(start,stop,{0xaf0c8b})})
 return {"source_sha256":HASH,"source_function":"AEF770","body_sha256":hashlib.sha256(body).hexdigest(),
  "instruction_count":len(instructions),"dispatcher_calls":[hex(a) for a in calls],
  "jump_tables":{hex(a):[hex(t) for t in ts] for a,ts in tables.items()},
  "unresolved_indirect_jumps":unknown,"outside_edges":outside,"queries":queries,
  "claim":"AF0C8B dominates both tick writers only from main live-step entry AF07F6. Whole AEF770 has bypass paths.",
  "limits":["Calls modeled as returning to the next instruction.",
            "Intraprocedural CFG does not admit the correct runtime branch by itself.",
            "No persistent alias/callee effects proof. Not a publication-ready completion gate."]}
if __name__=="__main__":
 result=run();out=ROOT/"tick-order-verification.json"
 out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(result,indent=2))
