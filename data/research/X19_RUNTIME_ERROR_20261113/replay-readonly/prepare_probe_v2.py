from pathlib import Path
import ast,hashlib,difflib,json
B=Path('J:/FM08dev/FmLauncher/data/research/X19_RUNTIME_ERROR_20261113/replay-readonly');p=B/'probe_dutch_qualification.py';orig=p.read_text(encoding='utf-8-sig');assert hashlib.sha256(p.read_bytes()).hexdigest()=='3f2bdf1a94d04d1f8e2501e1ad39a291bec105e7fa0a556d0d3b2192b03bd658'
s=orig.replace('from pathlib import Path','from pathlib import Path\nimport pefile')
s=s.replace("EXPECTED =", "VERSION = 'V2_PARENT_COMP_AND_CUP_CAPTURE'\nEXPECTED =",1)
s=s.replace("self.before=self.identity();require(self.before['ImageSHA256']==EXPECTED,'unsupported image')", "self.before=self.identity();require(self.before['ImageSHA256']==EXPECTED,'unsupported image')\n        self.pe=pefile.PE(self.before['Image']);self.disk_image=self.pe.get_memory_mapped_image()")
insert='''def method_proof(m,a,slot):
    vt=m.u32(a);target=m.u32(vt+slot);rva=target-0x400000
    require(0<=rva and rva+32<=len(m.disk_image),'native method target outside pinned image')
    require(any(sec.VirtualAddress<=rva<sec.VirtualAddress+max(sec.Misc_VirtualSize,sec.SizeOfRawData) and sec.Characteristics&0x20000000 for sec in m.pe.sections),'native method target not executable')
    actual=m.read(target,32,True);require(actual==m.disk_image[rva:rva+32],'native method bytes differ from pinned image')
    return dict(Slot=slot,Target=target,Entry32Hex=actual.hex(),EntrySHA256=hashlib.sha256(actual).hexdigest(),ExactPinnedPEMatch=True,Invoked=False)

def descriptor_capture(m,header):
    vt=U32(header,0x1b4);data=U32(header,0x1b8);n=I8(header,0x1bc)
    require(0<=n<=64,'additional descriptor count bound')
    out=dict(VectorVTable=vt,Data=data,Count=n,FieldsKnownFromD70770='descriptor+5 and +6 flags, +4 low byte index; record+0 COMP UID comparison',StrideSemantics='UNKNOWN; raw window only, not parsed as pointers or guessed records')
    if n:
        # Header guarantees >=7B per referenced descriptor, but does not prove
        # its stride. Capture a bounded raw window; do not dereference entries.
        target=m.u32(vt+0x2c);rva=target-0x400000;require(0<=rva and rva+48<=len(m.disk_image),'descriptor getter target')
        raw=m.read(target,48,True);require(raw==m.disk_image[rva:rva+48],'descriptor getter not pinned PE')
        out.update(GetterTarget=target,GetterEntry48Hex=raw.hex(),GetterPEMatch=True,RawWindowBytes=n*8,RawWindowHex=m.read(data,n*8,True).hex())
    return out

'''
s=s.replace('def team(m,a):',insert+'def team(m,a):',1)
s=s.replace("CurrentCOMP=m.uid(m.u32(p+0x54)) if m.u32(p+0x54) else None)","CurrentCOMP=m.uid(m.u32(p+0x54)) if m.u32(p+0x54) else None,CurrentCOMPAddress=m.u32(p+0x54),CurrentCOMPClass=m.rtti(m.u32(p+0x54)) if m.u32(p+0x54) else None)")
s=s.replace("    if typ=='.?AVLEAGUE_STAGE@@':", "    out['NativeSlots']=[method_proof(m,a,slot) for slot in (8,0x64,0x68,0x124)]\n    if typ=='.?AVLEAGUE_STAGE@@':",1)
s=s.replace("    else:out['DecodeGap']='OTHER_STAGE raw header only'", """    elif typ=='.?AVCUP_STAGE@@':
        n=I16(b,0x3c);table=U32(b,0x38);require(0<=n<=256,'CUP TEAM count short bound')
        raw=m.read(table,n*8,True) if n else b''
        entries=[]
        for i in range(n):
            q=raw[i*8:i*8+8];ptr=U32(q)
            entries.append(dict(Index=i,RawSlotHex=q.hex(),TEAM=team(m,ptr) if ptr else None))
        out.update(TeamCountShort3C=n,TeamTableAddress38=table,TeamTableEntries=entries,PureStatus=dict(Value=None,Proof='UNKNOWN CUP_STAGE status; no native getter invoked'),FixtureDecodeGap='Existing witness supports TEAM pointer+8B slots only; internal match/fixture offsets not proved, not guessed')
    else:out['DecodeGap']='OTHER_STAGE raw header and guarded methods only'""")
s=s.replace("b=m.read(p,0xd8,True);n=I8(b,0xd4)","b=m.read(p,0x1c0,True);n=I8(b,0xd4)")
s=s.replace("StageCount=n,Stages=[stage(m,a,i,uid) for i,a in enumerate(arr)]))", "StageCount=n,CompletionE0=U32(b,0xe0),CompletionE4Byte=I8(b,0xe4),TierF4=I8(b,0xf4),ParentCOMP10C=U32(b,0x10c),AdditionalDescriptors=descriptor_capture(m,b),NativeSlots=[method_proof(m,p,slot) for slot in (0x68,0x124,0x2c0)],Stages=[stage(m,a,i,uid) for i,a in enumerate(arr)]))")
s=s.replace("m=None;res=dict(Status='FAIL_CAPTURE'", "m=None;res=dict(ProbeVersion=VERSION,PreviousProbeSHA256='3f2bdf1a94d04d1f8e2501e1ad39a291bec105e7fa0a556d0d3b2192b03bd658',Status='FAIL_CAPTURE'")
ast.parse(s);out=B/'probe_dutch_qualification_v2.py';assert not out.exists();out.write_text(s,encoding='utf-8');(B/'probe-v1-v2.diff').write_text(''.join(difflib.unified_diff(orig.splitlines(True),s.splitlines(True),fromfile=p.name,tofile=out.name)),encoding='utf-8')
proof=dict(Status='READY_SYNTAX_AND_OFFLINE_REVIEW_PASS_RUNTIME_NOT_RUN',Script=str(out),ScriptSHA256=hashlib.sha256(out.read_bytes()).hexdigest(),OriginalProbeSHA256=hashlib.sha256(p.read_bytes()).hexdigest(),DiffSHA256=hashlib.sha256((B/'probe-v1-v2.diff').read_bytes()).hexdigest(),NoProcessAccessDuringPreparation=True,NoMutatingProcessAPIs=True,Changes=['COMP raw header D8→1C0, E0/E4/F4/D4/10C fields','Additional descriptor vector1B4/1B8/1BC bounded raw capture; stride UNKNOWN','All stages slots8/64/68/124, COMP68/124/2C0 targets and exact pinned PE bytes','CUP_STAGE signed shortcount3C and 8B TEAM table38 from prior proved witness','FamilyMembers actual CurrentCOMP pointers/RTTI','All V1 session/calendar/readwatch/exclusive-output guards retained'],Gaps=['No fixture game offsets guessed','No status virtual calls','Descriptor stride not guessed'])
(B/'probe-v2-ready.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof,indent=2))
