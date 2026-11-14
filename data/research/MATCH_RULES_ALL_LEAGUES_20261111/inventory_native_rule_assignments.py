"""Static RTTI/stage-byte assignment inventory. Never executes target or writes DB/EXE."""
from pathlib import Path
import struct,re,json,csv,bisect,hashlib,collections
import pefile,capstone
ROOT=Path.cwd();B=ROOT/'FmLauncher/data/research/MATCH_RULES_ALL_LEAGUES_20261111';B.mkdir(parents=True,exist_ok=True)
exe=ROOT/'fm.exe';raw=exe.read_bytes();sha=hashlib.sha256(raw).hexdigest();assert sha=='157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d'
pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
def va(off):return base+pe.get_rva_from_offset(off)
def off(addr):return pe.get_offset_from_rva(addr-base)
def u32at(p):return struct.unpack_from('<I',raw,p)[0]
rdata=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.rdata');rs=rdata.PointerToRawData;re_=rs+rdata.SizeOfRawData
text=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text');ts=text.PointerToRawData;te=ts+text.SizeOfRawData
textlo=base+text.VirtualAddress;texthi=textlo+text.SizeOfRawData
types={}
for m in re.finditer(rb'\.\?AV([A-Z][A-Z0-9_]+)@@\0',raw):types[va(m.start()-8)]=m.group(1).decode()
cols={}
for p in range(rs,re_-20,4):
 td=u32at(p)
 if td not in types:continue
 s=p-12
 if s<rs:continue
 sig,objoffset,ctoroffset,td2,hier=struct.unpack_from('<5I',raw,s)
 if sig==0 and objoffset<0x10000 and ctoroffset<0x10000 and base+rdata.VirtualAddress<=hier<base+rdata.VirtualAddress+rdata.SizeOfRawData:
  cols[va(s)]=dict(name=types[td],object_offset=objoffset,locator=va(s))
vtables=[];fnclasses=collections.defaultdict(set)
for p in range(rs,re_-8,4):
 col=u32at(p)
 if col not in cols:continue
 pos=p+4;fns=[]
 while pos+4<=re_ and len(fns)<256:
  f=u32at(pos)
  if not(textlo<=f<texthi):break
  fns.append(f);fnclasses[f].add(cols[col]['name']);pos+=4
 if fns:vtables.append(dict(cols[col],vftable=va(p+4),functions=fns))
lst=ROOT/'FmLauncher/data/research/GHIDRA_ENGINE_20261107_R5/function-list-all.tsv'
with lst.open(encoding='utf-8-sig')as f:funcs=list(csv.DictReader(f,delimiter='\t'))
funcs=[v for v in funcs if chr(58) not in v[chr(65)+chr(100)+chr(100)+chr(114)+chr(101)+chr(115)+chr(115)]]
funcs.sort(key=lambda x:int(x['Address'],16));entries=[int(x['Address'],16)for x in funcs]
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.skipdata=True
matches=[]
for m in re.finditer(rb'\xc6[\x40-\x47]\x31[\x00-\x1c]',raw[ts:te]):
 pos=ts+m.start();address=va(pos);idx=bisect.bisect_right(entries,address)-1
 if idx<0:continue
 f=funcs[idx];start=int(f['Address'],16)
 # Re-disassemble from known function start, not from arbitrary matching byte.
 begin=off(start);insn=None
 for z in md.disasm(raw[begin:pos+16],start):
  if z.address==address:insn=z;break
  if z.address>address:break
 if not insn or insn.mnemonic!='mov' or 'byte ptr'not in insn.op_str:continue
 classes=sorted(fnclasses.get(start,[]))
 cfile=ROOT/'FmLauncher/data/research/GHIDRA_ENGINE_20261107_R5'/f['CFile']
 matches.append(dict(code=raw[pos+3],assignment_address=hex(address),instruction=insn.mnemonic+' '+insn.op_str,function_address=hex(start),function_classes=classes,cfile=str(cfile.relative_to(ROOT)),body_bytes=int(f['BodyBytes'])if f['BodyBytes'].isdigit()else f['BodyBytes']))
(B/'rtti-vftables.json').write_text(json.dumps(vtables,indent=2),encoding='utf-8')
(B/'direct-byte31-writes.json').write_text(json.dumps(matches,indent=2),encoding='utf-8')
summary=dict(source_sha256=sha,types=len(types),locators=len(cols),vtables=len(vtables),direct_byte31_writes=len(matches),by_code=dict(collections.Counter(x['code']for x in matches)),writes_with_rtti_class=sum(bool(x['function_classes'])for x in matches),rtti_writes=[x for x in matches if x['function_classes']])
(B/'inventory-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items()if k!='rtti_writes'}))
