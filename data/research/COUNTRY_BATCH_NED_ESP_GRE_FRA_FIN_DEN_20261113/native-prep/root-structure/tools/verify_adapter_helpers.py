"""Focused pre-apply adapter helper verification on existing pinned fixtures; no database writes."""
from pathlib import Path
import importlib.util,json,hashlib,struct,sys
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8');ROOT=Path('J:/FM08dev');O=Path(__file__).resolve().parent;sp=importlib.util.spec_from_file_location('common_adapter',O/'ApplyX18Structure.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();B=O.parents[1];S=B/'input/X17-after-SI';a=m.load(S,'server_db.dat');c=m.load(S,'client_db.dat');en,_=m.lang_sections(dict(m.languages((S/'lang_db.dat').read_bytes()))[8]);cl,_,_=m.find_table(c,[r['uid']for r in en['club']],m.club);cf={r['uid']:r for r in cl};rr=m.read(B/'native-structure.json')['records'];r=next(r for r in rr if r['ClubUID']==2121)
protected=[('TEAM_2121',r['Start'],r['Footer']+8,a[r['Start']:r['Footer']+8])];source_family={}
for uid in [2121,928820]:
 f=cf[uid];fi=f['index'];st=m.unique(a,struct.pack('<iI',fi-1,cl[fi-1]['uid']))+8;end=m.unique(a,struct.pack('<iI',fi,uid))+8;protected.append(('FAMILY_'+str(uid),st,end,a[st:end]));source_family[uid]=(f,st,end)
ed=[];ce=[];receipt=m._queue_namefix(S,a,c,ed,ce);assert len(ed)==len(ce)==6;m._guard_edits(ed,protected);sa,spv=m.apply_verified(a,ed);sc,cpv=m.apply_verified(c,ce);keep=m._verify_preserved(sa,ed,protected)
for e in receipt:
 d=sa if e['File']=='server_db.dat'else sc;edits=ed if e['File']=='server_db.dat'else ce;cu=m.Cursor(d,m._rebase(e['Offset'],edits));assert cu.string()==e['AfterUTF16']
newcl,_,_=m.find_table(sc,[r['uid']for r in en['club']],m.club);ncf={r['uid']:r for r in newcl}
for e in receipt:
 if e['File']=='client_db.dat':assert ncf[e['UID']]['embedded_full_name'if e['Field']=='EmbeddedFull'else'embedded_short_name']==e['AfterUTF16']
negative=[]
for name,start,end,_ in protected:
 try:m._guard_edits([(start+1,1,bytes([a[start+1]^1]))],protected);raise RuntimeError('failed negative preservation guard')
 except AssertionError:negative.append('reject_'+name)
# Replay >one new reserve under new first family using unchanged SI fixture.
tplproof=m.read(m.R/'CLUB_STADIUM_CREATION_R1_20261108/si-fixtures.json')['native_N1'];tpl=Path(tplproof['frozen_after_SI']);assert m.pins(tpl)==tplproof['after_SI_hashes'];ta=m.load(tpl,'server_db.dat');te=m.unique(ta,struct.pack('<iI',23394,1800001004))+8;tree=ta[te-216:te];v=m._members(tree,0,len(tree),23394,1800001004,'','');assert v['Members']==[23624]
two=m._append_new_family(tree,23394,1800001004,[23624],60000);three=m._append_new_family(two,23394,1800001004,[23624,60000],60001);assert m._members(three,0,len(three),23394,1800001004,'','')['Members']==[23624,60000,60001]
# Aggregate two appends to one old-family vector, so common apply sees one source edit.
f,st,end=source_family[928820];v=m._members(a,st,end,8540,928820,f['embedded_full_name'],f['embedded_short_name']);assert v['Members']==[8763,1846];members_ed=[];state={};m._queue_member_edit(members_ed,state,928820,v,60000,st,end,8540);m._queue_member_edit(members_ed,state,928820,v,60001,st,end,8540);assert len(members_ed)==1
# Utility-only private fixture: never included in common Kolding-protected write.
fixture=a[st:end];off,n,new=members_ed[0];local=[(off-st,n,new)];updated,_=m.apply_verified(fixture,local);assert m._members(updated,0,len(updated),8540,928820,f['embedded_full_name'],f['embedded_short_name'])['Members']==[8763,1846,60000,60001]
assert m._rebase_end(100,[(100,0,b'xx')])==100 and m._rebase(100,[(100,0,b'xx')])==102
out=dict(Status='PASS_FOCUSED_HELPERS_MAIN_NOT_EXECUTED',WriterSHA256=sha(O/'ApplyX18Structure.py'),NamefixPlanSHA256=m.NAMEFIX_SHA256,NamefixPhysicalEdits=len(receipt),NamefixIndependentSERVERCLIENTStringReadback=True,NamefixCLIENTFullTableReload=True,NamefixWholeInverse=True,PreservedKolding=keep,ProtectedNegativeCases=negative,SI_witness_template='native_N1 family23394/UID1800001004',MultipleNewParentReserves=dict(StartingMembers=1,FinalMembers=3,TypedSuffixPASS=True),MultipleOldParentReserves=dict(StartingMembers=2,FinalMembers=4,SourceEditsAggregated=1,UtilityFixtureOnly=True,TypedSuffixPASS=True),HalfOpenRangeInsertionBoundaryPASS=True,SourceUnchanged=all(sha(S/k)==v for k,v in m.read(B/'source-freeze.json')['hashes'].items()),NativeDatabaseWritten=False,MainExecuted=False,FullCommonPreflight='PENDING_ROOT_CONFIG_PLANS_PROJECTION',FrozenSIHashesVerified=True)
(O/'focused-verification.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(out['Status']);print('writerSHA',out['WriterSHA256']);print('checks:12namefix,two multi-reserve variants,3 protectednegative,SI-N1pinnedfixture; mainNOTRUN')
