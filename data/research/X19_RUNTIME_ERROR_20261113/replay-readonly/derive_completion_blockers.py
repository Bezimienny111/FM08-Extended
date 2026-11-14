from pathlib import Path
import json,hashlib,struct,pefile,capstone
B=Path('J:/FM08dev/FmLauncher/data/research/X19_RUNTIME_ERROR_20261113/replay-readonly');P=B/'baseline-2009-03-22.json';D=Path('J:/FM08dev/FmLauncher/data/research/GHIDRA_ENGINE_20261107_R5/decompiled/functions/ram_dd3330.c');E=Path('J:/FM08dev/fm.exe');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P)=='18e76a581133b4ef4c1fa63862d311a49adf1ca291f947f4c3442cdf00a5722c';assert sha(E)=='157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d'
d=json.loads(P.read_text(encoding='utf-8-sig'));assert d['Status']=='PASS_STABLE_READ_ONLY_SNAPSHOT';c=next(x for x in d['Competitions'] if x['UID']==30);g=next(x for x in c['Stages'] if 'GROUP_STAGE' in x['RTTI']['Type']);results=[]
def signed8(v):return (v+128)%256-128
for ch in g['Children']:
 s=bytes.fromhex(ch['Settings']['RawHex']);threshold=signed8(s[0x10]);n=signed8(s[0xb]);
 if s[0x12]:threshold=min(threshold,signed8((n-1)*signed8(s[0xa])))
 rowfacts=[dict(Row=r['Row'],UID=r['TEAM']['UID'],Name=r['TEAM'].get('Name'),Games14=signed8(r['Games14']),Threshold=threshold,Flags42=r['Flags42'],BelowThreshold=signed8(r['Games14'])<threshold) for r in ch['Rows']]
 out=dict(PeriodIndex=ch['Index'],StageAddress=ch['Address'],Threshold=threshold,Field20=ch['Field20'],Field21=ch['Field21'],Field50=ch['Field50'],Rows=rowfacts,InsufficientGamesRows=[r for r in rowfacts if r['BelowThreshold']],DerivedValue=None,Status='UNKNOWN',ProofPrefix=[],NoRuntimeCalls=True)
 if ch['Field50']!=0:out.update(DerivedValue=0,Status='PROVED_RETURN0_HEADER50')
 elif ch['Field20']!=0:out.update(DerivedValue=2,Status='PROVED_RETURN2_HEADER20_IGNORING_NONPURE_SIDE_EFFECTS')
 elif signed8(s[0x2f])!=-1 and s[0x2e]==1:out['Status']='UNKNOWN_EARLY_NONPURE_STAGE_TRANSITION'
 else:
  prefix_pure=True
  for r,f in zip(ch['Rows'],rowfacts):
   if f['BelowThreshold']:
    out['FirstCompletionBlocker']=f
    if prefix_pure:out.update(DerivedValue=0,Status='PROVED_RETURN0_INSUFFICIENT_GAMES_BEFORE_ANY_WRITE_OR_CALL')
    else:out['Status']='UNKNOWN_INSufficientGames_AFTER_NONPURE_PREFIX'
    break
   flags=f['Flags42']&255
   if flags&8 and flags&1:prefix_pure=False;out['ProofPrefix'].append(dict(Row=r['Row'],Kind='ROW42_BIT8_CLEAR_WRITE_AT_DD3429'))
   if flags&10:
    out['FirstCompletionBlocker']=dict(f,Kind='RESERVE_DEPENDENCY_GATE_AT_DD3430',DD0B70PriorCallEnabled=bool(ch['Field21'] and not ch['Settings']['FlagsC']&0x100),PrefixBeforeGateReadOnly=prefix_pure)
    members=r['TEAM'].get('FamilyMembers',[]);positions=[i for i,x in enumerate(members) if x['Address']==r['TEAM']['Address']]
    if len(positions)==1 and positions[0]>0:
     out['FirstCompletionBlocker']['C9DCE0CapturedPredecessor']=members[positions[0]-1]
    out['Status']='UNKNOWN_AT_RESERVE_DEPENDENCY_GATE';break
  else:out['Status']='UNKNOWN_AFTER_ALL_ROWS_PASS'
 results.append(out)
report=dict(Status='ANALYSIS_ONLY_BOUNDED_DD3330_PURE_PREFIX',RuntimeMemoryRead=False,DBWrite=False,OriginalCaptureUnchanged=True,InputSHA256=sha(P),StaticSourceSHA256=sha(D),ImageSHA256=sha(E),Method='DD3330 virtual+8 called by E32A70 would receive(0,0); symbolic prefix only, never execute native code',ExactOrder=['DD3337 short50!=0 ->return0','DD3354 byte20!=0 ->return2; possible side effects before return','DD33A3 period-link early transition may write/call and return2','DD33CD threshold=min(signedByte10, signed8((signedByteB-1)*signedByteA)) iff settings12 !=0','DD340D row signedByte14 < threshold ->DD354D return0','DD3429 iff(row42&8)&&(row42&1): clear row42bit8','DD3430 iff row42&0xA: parent/dependency path, possibly DD0B70 if stage21 and !settings100','DD3462 C9DCE0 pure physical predecessor lookup','DD347C parent CurrentCOMP virtual68(1)','DD3493/349D ownerCOMP virtual124 vs parentCOMP virtual124','DD34C9 parent node virtual2C0(0,0,-1,1,1)'],GlobalAnyInsufficientShortcutSafe=False,Reason='An earlier row can enter DD0B70/virtual methods and mutate state before a later insufficient-games test; exact no-write/no-call prefix is required for pure snapshot proof.',DerivedCompletionBlockers=results,Summary=dict(PureStatus0Periods=[x['PeriodIndex'] for x in results if x['DerivedValue']==0],UnknownPeriods=[x['PeriodIndex'] for x in results if x['DerivedValue'] is None],Status0LowerBound=sum(x['DerivedValue']==0 for x in results),Status0UpperBound=sum(x['DerivedValue'] in (0,None) for x in results),ActualMainQuota=8,RetainedFate2=5,RemainingQUALInterval=[8-5-sum(x['DerivedValue'] in (0,None) for x in results),8-5-sum(x['DerivedValue']==0 for x in results)]),RemainingProofGaps=['Five completed-by-games periods enter first reserve-dependency gate, whose parent COMP virtual return values were not captured','No assertion that reserve itself is invalid or source fix is required','Current state is March22, not crash decision April19'])
pe=pefile.PE(str(E));image=pe.get_memory_mapped_image();md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);asm='\n'.join(f'{i.address:08X} {i.bytes.hex():24s} {i.mnemonic} {i.op_str}' for i in md.disasm(image[0xdd3330-0x400000:0xdd3330-0x400000+0x1a5],0xdd3330))+'\n';ap=B/'DD3330-prefix-asm.txt';ap.write_text(asm,encoding='utf-8');report['ASM_SHA256']=sha(ap)
op=B/'baseline-derived-completion-blockers.json';op.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');assert sha(P)==report['InputSHA256'];print(json.dumps(report['Summary']));print('ANALYSIS_SHA256',sha(op))
