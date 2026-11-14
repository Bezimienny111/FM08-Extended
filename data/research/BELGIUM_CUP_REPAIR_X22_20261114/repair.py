from pathlib import Path
from collections import Counter
import sys,json,hashlib,shutil,subprocess,importlib.util,struct,zlib,csv,datetime
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent;N=R/'COUNTRY_BATCH_BLR_BEL_AUT_AUS_ARG_20261114/native-prep';S=ROOT/'Dane/db/TEST_X21';F=B/'input/X21-after-SI';D=B/'private-db';T=N/'tools'
rd=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def pins(p):return {str(x.relative_to(p)):sha(x)for x in sorted(p.rglob('*'))if x.is_file()}
def dump(p,x):
 assert not p.exists(),str(p)
 p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def closed():
 z=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,text=True,encoding='utf-8',errors='replace',check=True)
 names={row[0].lower()for row in csv.reader(z.stdout.splitlines())if row}
 assert 'data editor.exe' not in names and 'fm.exe' not in names,'Close source editor/FM; do not bypass guard'
closed();assert not any(p.exists()for p in[F,D,ROOT/'Dane/db/TEST_X22',ROOT/'wydania/TEST_X22.zip'])
zip21=ROOT/'wydania/TEST_X21.zip';zipsha=sha(zip21);assert zipsha=='31a308c91d1396c208cc456da723f0bc0efd60f0dfcd84443de2a5dd3b680c50'
before=pins(S);shutil.copytree(S,F);assert pins(F)==pins(S)==before;closed()
dump(B/'source-freeze.json',dict(source=str(S),frozen=str(F),hashes=before,OriginalZIP=str(zip21),OriginalZIP_SHA256=zipsha,UserClosedEditor=True,SourceCareer='FAILED_BEL_CUP_2007_10_05',SI='USER_SAVED_AND_CLOSED',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat()))
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'));from create_club_stadium_native_n1_20261108 import load
# Static evidence directly from the pinned original image, no EXE patches.
import pefile,capstone
exe=ROOT/'fm.exe';assert sha(exe)=='157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d'
pe=pefile.PE(str(exe));image=pe.get_memory_mapped_image();md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
assert struct.unpack_from('<I',image,0x1650bac-0x400000+0x160)[0]==0xeec1c0
assert struct.unpack_from('<I',image,0x1650bac-0x400000+0x158)[0]==0xeea0e0
code=list(md.disasm(image[0xeec1c0-0x400000:0xeecb00-0x400000],0xeec1c0));texts={i.address:(i.mnemonic,i.op_str)for i in code}
assert texts[0xeec22b]==('mov','word ptr [eax], 0x6f') and texts[0xeec2a1]==('mov','word ptr [ecx + 8], 0x6f') and texts[0xeec468]==('mov','word ptr [esp + 0x3c], 0x13')
(B/'BEL_CUP_eec1c0.asm').write_text('\n'.join(hex(i.address)+' '+i.mnemonic+' '+i.op_str for i in code)+'\n',encoding='utf-8')
sourcecode=R/'GHIDRA_ENGINE_20261107_R5/decompiled/functions/ram_ee99a0.c';assert 'iVar5 = 0x4a;'in sourcecode.read_text(encoding='utf-8-sig')
# Exact ranking order from already gathered completed25/26 data; no current table.
plan=rd(N/'club-plan-allocated.json');candidates=[x for x in plan if x['Country']=='Belgium'and x.get('DesiredDivision')in[2,3]and x.get('PreviousFacts')and not x.get('ParentTMID')]
def rank(x):
 f=x['PreviousFacts'];m=f['Matches'];return(f['PreviousLevel'],f['FinalPosition'],-f['Points']/m,-f['GoalDifference']/m,-f['Wins']/m,int(x['TMID']))
candidates.sort(key=rank);chosen=candidates[0];assert chosen['NativeClubUID']==3200589 and chosen['TMID']=='11939' and chosen['DesiredDivision']==3
# Reuse verified read-only country selector; fresh source and target exports only.
qpath=R/'COUNTRY_BATCH_CZE_CRO_CHN_CHI_BGR_BRA_20261113/native-prep/qa-root/selection_regression.py';sp=importlib.util.spec_from_file_location('known_selection',qpath);q=importlib.util.module_from_spec(sp);sp.loader.exec_module(q)
old,native,evpins,overlays,summary=q.definitions();new=q.normalize(rd(N.parent/'competition-prep/native-competition-requirements-scoped-r2.json')['requirements']);assert len(old)+len(native)+len(new)==589;relevant={x['uid']for x in old+native+new}
def export(db,file):
 args=[T/'ExportWholeNativeStructure.exe',db,T/'FM08_Database_Editor.exe',file];z=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300);(file.with_suffix('.log')).write_text(z.stdout+z.stderr,encoding='utf-8');assert z.returncode==0,z.stderr[-1200:]
export(F,B/'source-native-structure.json');source=q.add_native_counts(q.x18.profile(F,before,B/'source-native-structure.json',overlays,relevant));records=rd(B/'source-native-structure.json')['records'];by={x['ClubUID']:x for x in records};raw=load(F,'server_db.dat');uid=3200589;z=by[uid];start=z['Start'];tail=source['tailproof'][uid];assert source['raw'][uid]==[4,None,None] and source['countries'][uid]==131 and source['kinds'][uid]==0 and tail['TEAMFamilyUID']==uid
indices={u:i for i,u in enumerate(source['names'])};assert indices[2]==1 and indices[4]==3
assert Counter(v[0]for v in source['raw'].values())[2]==18 and Counter(v[0]for v in source['raw'].values())[4]==16
assert raw[start]==10 and struct.unpack_from('<iI',raw,z['Footer'])==(z['TeamIndex'],uid)
at=start+7;old4=raw[at:at+4];new4=struct.pack('<i',indices[2]);assert struct.unpack('<i',old4)[0]==indices[4]
changed=bytearray(raw);changed[at:at+4]=new4;inverse=bytearray(changed);inverse[at:at+4]=old4;assert bytes(inverse)==raw
assert pins(S)==pins(F)==before;closed();shutil.copytree(F,D);header=(F/'server_db.dat').read_bytes()[:9];(D/'server_db.dat').write_bytes(header+zlib.compress(bytes(changed)));assert load(D,'server_db.dat')==bytes(changed)
after=pins(D);assert{k:v for k,v in before.items()if k!='server_db.dat'}=={k:v for k,v in after.items()if k!='server_db.dat'}
export(D,B/'target-native-structure.json');target=q.add_native_counts(q.x18.profile(D,after,B/'target-native-structure.json',overlays,relevant));assert source['nations']==target['nations'] and source['names']==target['names'] and source['countries']==target['countries'] and source['kinds']==target['kinds']
changes=[dict(UID=u,Slot=i,Before=source['raw'][u][i],After=target['raw'][u][i])for u in source['raw']for i in range(3)if source['raw'][u][i]!=target['raw'][u][i]];assert changes==[dict(UID=uid,Slot=0,Before=4,After=2)]
checks_before=q.x18.checks_for(old,source)+q.native_checks(native+new,source);checks_after=q.x18.checks_for(old,target)+q.native_checks(native+new,target);checks=[dict(a,Before=a['Count'],After=b['Count'],AfterPassed=b['Passed'])for a,b in zip(checks_before,checks_after)];assert len(checks)==589 and all(x['Passed']for x in checks_before) and all(x['Passed']for x in checks_after)
for f in [0,1]:assert target['nativecounts'][f][2]==19 and target['nativecounts'][f][3]==16 and target['nativecounts'][f][4]==15
assert len(source['raw'])==len(target['raw']) and len(records)==len(rd(B/'target-native-structure.json')['records'])
for u,x in by.items():
 y=nextrec=None
# Whole buffer inverse already proves all TEAM/FAMILY/people/contracts/ratings bytes except oneint32 preserved.
assert pins(S)==pins(F)==before and pins(D)==after and sha(zip21)==zipsha and sha(exe)=='157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d'
proof=dict(Status='PASS_ONE_CURRENT_INT32_NATIVE_INVERSE_AND_589_SELECTION',Name='TEST_X22',Source=str(F),Private=str(D),SourceHashes=before,PrivateHashes=after,UID=uid,NameMoved=chosen['Name'],TMID='11939',TEAMStart=start,TEAMFooter=z['Footer'],Family=tail,Edit=dict(Offset=at,BeforeHex=old4.hex(),AfterHex=new4.hex(),CurrentBeforeCOMP=4,CurrentAfterCOMP=2),RawSlotChanges=changes,WholeBufferInverse=True,UncompressedLength=len(raw),ActualChangedBytes=sum(a!=b for a,b in zip(raw,changed)),AllOtherFilesIdentical=True,PreviousAlternateRegionalPreserved=True,CountryKindParentFAMILYRosterAndPeoplePreserved=True,SugarDaddyUntouchedAndInheritedOFF746=True,SelectionChecks=589,NewFailures=[],StaticRequiredCupParticipants2007=111,StaticNewSecondEntrants2007=19,PredictedCupParticipants=74+19+18,GameVerified=False,SI=False,NewCareer=False,Season=False,OriginalZIP_SHA256=zipsha,FixedCareerSave=False)
dump(B/'native-patch-proof.json',proof);dump(B/'selection-readback.json',dict(Status='PASS_589',Checks=checks,Reader=str(qpath),ReaderSHA256=sha(qpath),EvidencePins=evpins))
dump(B/'decision.json',dict(Rule='Restore source-proven first-year Belgian engine counts; completed previous season ranking',Chosen={k:chosen[k]for k in ['TMID','Name','NativeClubUID','PreviousFacts']},CandidateRanking=[{k:x.get(k)for k in ['TMID','Name','NativeClubUID','PreviousFacts']}for x in candidates],NativeData=[dict(COMPUID=2,Before=18,After=19),dict(COMPUID=4,Before=16,After=15)],LowerFeedersUnchanged=True,NoAdditionalPlayerImport=True,StaticProofFile='BEL_CUP_eec1c0.asm',StaticProofSHA256=sha(B/'BEL_CUP_eec1c0.asm'),SourceSelectorFile=str(sourcecode),SourceSelectorSHA256=sha(sourcecode),RepairOnlyAppliesToNewCareer=True))
print('READY_PRIVATE_X22 oneCurrent int32;589checksPASS;Cup111prediction;SI/career/seasonPENDING',flush=True)
