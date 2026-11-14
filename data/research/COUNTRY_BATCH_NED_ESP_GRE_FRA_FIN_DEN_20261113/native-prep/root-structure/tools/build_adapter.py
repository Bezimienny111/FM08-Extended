"""Generate X18 common structural writer from exact frozen X17 seed. Does not run writer."""
from pathlib import Path
import hashlib,json,datetime,sys
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev');O=ROOT/'FmLauncher/data/research/COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep/root-structure/tools';O.mkdir(parents=True,exist_ok=True)
SEED=ROOT/'FmLauncher/data/research/COUNTRY_BATCH_IDN_IND_HKG_20261112/structure-root-r2/tools/ApplyX14Structure.py';EXPECTED='a5a524d7a5cbeee5ac9846ce9f203cb443ba994bb343404b3a5ad9491f4b255d';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(SEED)==EXPECTED
s=SEED.read_text(encoding='utf-8-sig')
def replace(a,b):
 global s
 assert s.count(a)==1,('seed_shape_changed',a[:100],s.count(a));s=s.replace(a,b,1)
replace('sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding=\'utf-8\')',"sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')\nROOT=Path('J:/FM08dev')\nsys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))\nimport json,hashlib")
replace("ROOT=Path(__file__).resolve().parents[2];R=ROOT/'FmLauncher/data/research';B=R/'COUNTRY_BATCH_IDN_IND_HKG_20261112/structure-root-r2';H=R/'HUNGARY_DATABASE_2627_H1_20261109';IT=R/'ITALY_DATABASE_2627_IMPORT_I1_20261108'","R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parents[1];H=R/'HUNGARY_DATABASE_2627_H1_20261109';IT=R/'ITALY_DATABASE_2627_IMPORT_I1_20261108'")
replace('1800210001+len(venueadd)','1800230001+len(venueadd)')
helpers='''
NAMEFIX_PLAN=R/'CLUB_NAME_LOOKUP_FIX_20261113/patch-plan.json'
NAMEFIX_SHA256='d0024b012e4ec305cf45fa5a4b0dbd2ba3670ba46dd4f535157bc25f28f743be'
PROTECTED_KOLDING_UID=2121

def _hash(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def _pure_string(s):return struct.pack('<i',len(s))+s.encode('utf-16-le')+(bytes(2)if s else b'')
def _members(data,start,end,fi,uid,full,short):
 # Existing FM08 TEAM_CONTAINER suffix schema: three flags, strings, five-colour kits,
 # member vector, l70, l8c,17flags,l7c, exact family index/UID footer.
 blob=data[start:end];needle=_pure_string(full)+_pure_string(short);found=[];off=0
 while True:
  off=blob.find(needle,off)
  if off<0:break
  at=off-3;off+=1
  if at<0:continue
  try:
   q=Cursor(blob,at);q.take(3);assert q.string()==full and q.string()==short
   nk=q.byte();assert nk<64;q.take(nk*11);ma=q.p;n=q.byte();members=[q.integer()for _ in range(n)];assert len(set(members))==n and all(0<=t<100000 for t in members)
   count=q.byte();q.take(count*8);count=q.num('<h');assert 0<=count<=4096;q.take(count*14);q.take(17);count=q.byte();q.take(count*20)
   assert q.identity()==(fi,uid)and q.p==len(blob);found.append(dict(Offset=start+ma,Count=n,Members=members,Before=data[start+ma:start+ma+1+4*n],SuffixStart=start+at))
  except(AssertionError,ValueError,UnicodeError,struct.error,IndexError):continue
 assert len(found)==1,('typed_family_member_suffix_not_unique',fi,uid,len(found));return found[0]

def _typed_tail(data,r,nfamilies):
 end=r['RosterOffset']+2+4*struct.unpack_from('<H',data,r['RosterOffset'])[0];hits=[]
 for pos in range(end+4,r['Footer']-13):
  if data[pos-3]!=0:continue
  fi=struct.unpack_from('<i',data,pos)[0]
  if not 0<=fi<nfamilies:continue
  try:
   q=Cursor(data,pos+4);q.string();q.byte();q.string();q.byte();assert q.p==r['Footer'];hits.append((fi,pos,data[pos-4]))
  except(AssertionError,ValueError,UnicodeError,struct.error,IndexError):continue
 assert len(hits)==1,('typed_TEAM_tail_not_unique',r['TeamIndex'],len(hits));return hits[0]

def _existing_reference(data,r,cl,x,plannedparents):
 fi,pos,nativekind=_typed_tail(data,r,len(cl));f=cl[fi];u=x['NativeClubUID'];actualparent=f['uid']if f['uid']!=u else None
 expectedfi=x.get('NativeContractFamilyIndex')
 if expectedfi is not None:assert int(expectedfi)==fi,('declared_contract_family_mismatch',u,expectedfi,fi)
 expectedparent=x.get('ExistingParentUID')or x.get('NativeParentUID')or None
 if actualparent:
  assert nativekind!=0 and expectedparent is not None and int(expectedparent)==actualparent,('existing_reserve_parent_mismatch',u,expectedparent,actualparent,nativekind)
  if x.get('ParentTMID')in plannedparents:assert plannedparents[x['ParentTMID']]['ClubUID']==actualparent,('planned_parent_differs_from_native',u)
  role='existing_linked_reserve'
 else:
  assert nativekind==0 and expectedparent is None,('unsupported_existing_team_role',u,nativekind,expectedparent);role='existing_first_team'
 return f,role,actualparent,dict(ClubUID=u,TeamIndex=r['TeamIndex'],TypedTailFamily=fi,TypedTailFamilyUID=f['uid'],TypedTailOffset=pos,NativeKind=nativekind,NativeParentUID=actualparent,DeclaredParentTMID=x.get('ParentTMID'),SourceParentTMID=x.get('SourceParentTMID'),ParentUpdatedInBatch=bool(x.get('ParentTMID')in plannedparents),SourceContractCountry=f['country_index'],WriterKind=role)

def _append_new_family(bb,fi,uid,existing_members,ti):
 assert struct.unpack_from('<iI',bb,len(bb)-8)==(fi,uid)
 # New first families use the existing SI-witnessed empty-name fixture; no fixed member count.
 v=_members(bb,0,len(bb),fi,uid,'','');assert v['Members']==existing_members and ti not in existing_members and len(existing_members)<255
 after=existing_members+[ti];at=v['Offset'];out=bb[:at]+bytes([len(after)])+struct.pack('<'+'i'*len(after),*after)+bb[at+len(v['Before']):]
 assert _members(out,0,len(out),fi,uid,'','')['Members']==after;return bytearray(out)

def _queue_member_edit(edits,state,pu,v,ti,start,end,fi):
 assert ti not in v['Members'];key=str(pu)
 if key not in state:state[key]=dict(source_members=v['Members'],added_members=[],source_offset=v['Offset'],source_size=len(v['Before']),family_start=start,family_end=end,family_index=fi,new_family=False)
 z=state[key];assert z['source_members']==v['Members']and ti not in z['added_members'];z['added_members'].append(ti);members=z['source_members']+z['added_members'];assert len(members)<256
 replacement=(v['Offset'],len(v['Before']),bytes([len(members)])+struct.pack('<'+'i'*len(members),*members))
 hit=[i for i,e in enumerate(edits)if e[0]==v['Offset']]
 if hit:assert len(hit)==1 and edits[hit[0]][1]==len(v['Before']);edits[hit[0]]=replacement
 else:edits.append(replacement)

def _queue_namefix(src,a,c,edits,cedits):
 assert _hash(NAMEFIX_PLAN)==NAMEFIX_SHA256,'namefix_plan_changed';p=read(NAMEFIX_PLAN)
 for f,h in p['SourceHashes'].items():assert _hash(src/f)==h,('namefix_source_changed',f)
 assert p['AllowedUIDs']==[1800200042,1800200058,1800200060]and p['LogicalFields']==6 and p['PhysicalStringEdits']==12
 receipt=[]
 for x in p['Patches']:
  data=a if x['File']=='server_db.dat'else c;out=edits if x['File']=='server_db.dat'else cedits
  old=bytes.fromhex(x['BeforeHex']);new=bytes.fromhex(x['AfterHex']);at=x['Offset'];assert old==bytes(4)and data[at:at+4]==old;assert x['UID']in p['AllowedUIDs']and x['Field']in ['EmbeddedFull','EmbeddedShort']
  assert hashlib.sha256(data[x['RecordStart']:x['RecordEndBefore']]).hexdigest()==x['RecordSHA256Before'];out.append((at,4,new));receipt.append(dict(x))
 return receipt

def _guard_edits(edits,protected):
 ordered=sorted(edits,key=lambda e:e[0]);assert all(x[0]+x[1]<=y[0]for x,y in zip(ordered,ordered[1:])), 'overlapping_source_edits'
 for name,start,end,raw in protected:
  for off,n,new in edits:assert not(start<=off<end or n and off<start<off+n),('protected_Kolding_source_edit',name,off,n)

def _rebase(at,edits):return at+sum(len(new)-n for off,n,new in edits if off+n<=at)
def _rebase_end(at,edits):return at+sum(len(new)-n for off,n,new in edits if off+n<at or n>0 and off+n==at)
def _verify_preserved(result,edits,protected):
 receipt=[]
 for name,start,end,old in protected:
  ns=_rebase(start,edits);ne=_rebase_end(end,edits);assert result[ns:ne]==old,('protected_Kolding_bitwise_changed',name)
  receipt.append(dict(Name=name,SourceStart=start,SourceEnd=end,TargetStart=ns,TargetEnd=ne,Bytes=len(old),SHA256=hashlib.sha256(old).hexdigest(),BitwisePASS=True))
 return receipt
'''
replace('def main():',helpers+'\ndef main():')
# Bind source-preserved Kolding records from typed source CLIENT/FAMILY/TEAM boundaries.
replace("cf={x['uid']:x for x in cl};tplproof=", """cf={x['uid']:x for x in cl}
 kolding=byuid[2121];assert kolding['TeamIndex']==1846 and kolding['CurrentDivisionIndex']==566
 assert a[kolding['Start']+87]==3 and struct.unpack_from('<i',a,kolding['Start']+91)[0]==8540
 assert struct.unpack_from('<iI',a,kolding['Footer'])==(1846,2121)
 protected=[('TEAM_2121_kind3_div566',kolding['Start'],kolding['Footer']+8,a[kolding['Start']:kolding['Footer']+8])]
 for ku in [2121,928820]:
  kf=cf[ku];ks=footer(kf['index']-1,cl[kf['index']-1]['uid']);ke=footer(kf['index'],ku);protected.append(('FAMILY_'+str(ku),ks,ke,a[ks:ke]))
 tplproof=""")
replace("plan=read(B/'club-plan.json')+read(B/'foreign-owner-plan.json');country.update({x['Country']:x['NativeCountryIndex']for x in plan});", "plan=read(B/'club-plan.json')+read(B/'foreign-owner-plan.json');assert all(int(x.get('NativeClubUID')or 0)!=2121 for x in plan),'Kolding_is_deferred_not_importable';country.update({x['Country']:x['NativeCountryIndex']for x in plan});")
replace("parent_edits={};retirement_repairs=[]", "parent_edits={};retirement_repairs=[];source_contract_references=[];namefix_receipt=_queue_namefix(src,a,c,edits,cedits)")
replace("ni=fi-oldName;bb=bytearray(names[ni]);assert bb[182]==1 and struct.unpack_from('<i',bb,183)[0]==pi;bb[182]=2;bb[187:187]=struct.pack('<i',ti);names[ni]=bytes(bb)", """ni=fi-oldName;bb=bytearray(names[ni]);existing=[v['TeamIndex']for v in bytm.values()if v['FamilyIndex']==fi];assert pi in existing
    bb=_append_new_family(bb,fi,pu,existing,ti);names[ni]=bytes(bb)
    key=str(pu)
    if key not in parent_edits:parent_edits[key]=dict(source_members=[pi],added_members=[],family_index=fi,new_family=True)
    parent_edits[key]['added_members'].append(ti)""")
start="""low=footer(fi-1,cl[fi-1]['uid']);end=footer(fi,pu);members=[]
    for r0 in records:
     rend=r0['RosterOffset']+2+4*struct.unpack_from('<H',a,r0['RosterOffset'])[0];ref=struct.unpack_from('<i',a,r0['Footer']-14)[0]
     if not(0<=ref<=100000):
      for pos in range(rend,r0['Footer']-6):
       if a[pos:pos+3]==bytes([0,0,255]):
        value=struct.unpack_from('<i',a,pos+3)[0]
        if 0<value<100000:ref=value;break
     if ref==fi:members.append(r0['TeamIndex'])
    assert pi in members and 0<len(members)<255;count=len(members);hits=[]
    for at in range(low,end-8-4*count):
     if a[at]!=count:continue
     found=list(struct.unpack_from('<'+'i'*count,a,at+1))
     if len(set(found))==count and set(found)==set(members):hits.append((at,found))
    assert len(hits)==1,('parent_member_vector_not_unique',pu,members,hits);at,found=hits[0];edits.append((at,1+4*count,bytes([count+1])+struct.pack('<'+'i'*(count+1),*(found+[ti]))));parent_edits[pu]=dict(source_members=found,new_member=ti,source_offset=at)"""
replace(start,"""low=footer(fi-1,cl[fi-1]['uid']);end=footer(fi,pu);sourcef=cf[pu]
    vector=_members(a,low,end,fi,pu,sourcef['embedded_full_name'],sourcef['embedded_short_name']);assert pi in vector['Members']
    for mt in vector['Members']:assert mt in byteam and _typed_tail(a,byteam[mt],len(cl))[0]==fi,('source_member_tail_family_mismatch',pu,mt)
    _queue_member_edit(edits,parent_edits,pu,vector,ti,low,end,fi)""")
replace("for uid in [x['uid']for x in additions]+[x['uid']for x in venueadd]:", "generateduids=[x['uid']for x in additions]+[x['uid']for x in venueadd];assert len(set(generateduids))==len(generateduids),'cross_generated_UID_collision'\n for uid in generateduids:")
replace("s,proofs=apply_verified(a,edits);cc,cproofs=apply_verified(c,cedits);generated=[];langproof=[];", """_guard_edits(edits,protected);_guard_edits(cedits,[]);s,proofs=apply_verified(a,edits);cc,cproofs=apply_verified(c,cedits);preserved_kolding=_verify_preserved(s,edits,protected)
 for ne in namefix_receipt:
  buf=s if ne['File']=='server_db.dat'else cc;ee=edits if ne['File']=='server_db.dat'else cedits;cur=Cursor(buf,_rebase(ne['Offset'],ee));assert cur.string()==ne['AfterUTF16'],('independent_namefix_readback_failed',ne['UID'],ne['File'],ne['Field'])
 generated=[];langproof=[];""")
# Typing/readback after fresh native export. Source namefix expected strings checked in fresh CLIENT.
replace("for old in records:\n  new=rb[old['TeamIndex']];", "assert rb[1846]['ClubUID']==2121 and rb[1846]['CurrentDivisionIndex']==566 and s[rb[1846]['Start']+87]==3 and struct.unpack_from('<i',s,rb[1846]['Start']+91)[0]==8540\n for old in records:\n  new=rb[old['TeamIndex']];")
replace("en2,_=lang_sections(dict(languages((dest/'lang_db.dat').read_bytes()))[8]);families,_,_=find_table(cc,[x['uid']for x in en2['club']],club);", """en2,_=lang_sections(dict(languages((dest/'lang_db.dat').read_bytes()))[8]);families,_,_=find_table(cc,[x['uid']for x in en2['club']],club)
 freshcf={f['uid']:f for f in families}
 for e in namefix_receipt:
  if e['File']=='client_db.dat':
   f=freshcf[e['UID']];assert f['index']==e['FamilyIndex'];assert f['embedded_full_name']if False else True
   assert f['embedded_full_name'if e['Field']=='EmbeddedFull'else'embedded_short_name']==e['AfterUTF16']
 for pu,z in parent_edits.items():
  pu=int(pu);f=freshcf[pu];st=_rebase(z['family_start'],edits)if not z['new_family']else None;en=_rebase_end(z['family_end'],edits)if not z['new_family']else None
  if z['new_family']:
   source_identity=struct.pack('<iI',f['index'],pu);en=unique(s,source_identity)+8;prevf=families[f['index']-1];st=unique(s,struct.pack('<iI',prevf['index'],prevf['uid']))+8
  got=_members(s,st,en,f['index'],pu,f['embedded_full_name'],f['embedded_short_name']);assert got['Members']==z['source_members']+z['added_members'],('target_parent_member_vector_differs',pu)
  for mt in got['Members']:assert mt in rb and _typed_tail(s,rb[mt],len(families))[0]==f['index'],('target_member_tail_family_mismatch',pu,mt)
 ;""")
# Remove generated accidental standalone semicolon introduced solely to retain following seed chain.
s=s.replace("\n ;_,_,co=find_table", "\n _,_,co=find_table")
s=s.replace(";assert f['embedded_full_name']if False else True","")
replace("parent_member_edits=parent_edits,additions=additions,", "parent_member_edits=parent_edits,namefix_plan_sha256=NAMEFIX_SHA256,namefix_edits=namefix_receipt,preserved_kolding=preserved_kolding,additions=additions,")

replace("""if x.get('ParentTMID'):
   assert x['ParentTMID']in bytm;parent=bytm[x['ParentTMID']]
   if u:assert x['ExistingParentUID']==parent['ClubUID']""", """parent_uid=None
  if not u and x.get('ParentTMID'):
   assert x['ParentTMID']in bytm,('new_reserve_parent_not_prepared',x['TMID'],x['ParentTMID']);parent=bytm[x['ParentTMID']];parent_uid=parent['ClubUID']""")
replace("r=byuid[u];f=cf[parent['ClubUID']if parent else u];ti=r['TeamIndex'];fi=f['index'];assert f['country_index']==x['SourceCountryIndex'];kind='existing_linked_reserve'if parent else'existing_first_team'", "r=byuid[u];f,kind,parent_uid,refproof=_existing_reference(a,r,cl,x,bytm);source_contract_references.append(refproof);ti=r['TeamIndex'];fi=f['index'];assert f['country_index']==x['SourceCountryIndex'],('source_contract_country_mismatch',u,f['country_index'],x['SourceCountryIndex'])")
replace("ParentUID=parent['ClubUID']if parent else''", "ParentUID=parent_uid or''")
replace("namefix_edits=namefix_receipt,preserved_kolding=preserved_kolding,additions=additions,", "namefix_edits=namefix_receipt,preserved_kolding=preserved_kolding,source_contract_references=source_contract_references,additions=additions,")
replace("inverse_all_buffers=True,people_identical=True,new_stadiums=ns,", "inverse_all_buffers=True,people_identical=True,preserved_kolding=preserved_kolding,namefix_logical_fields=6,namefix_physical_edits=12,typed_parent_member_readback=True,new_stadiums=ns,")
replace("actual_deltas={str(d):expected_counts[d]-sum(r['CurrentDivisionIndex']==d for r in records)for d in expected_counts if expected_counts[d]!=sum(r['CurrentDivisionIndex']==d for r in records)}", "before_counts=Counter(r['CurrentDivisionIndex']for r in records)\n actual_deltas={str(d):expected_counts[d]-before_counts[d]for d in set(expected_counts)|set(before_counts)if expected_counts[d]!=before_counts[d]}")
replace("print('PASS X7 structure teams'", "print('PASS X18 common structure teams'")
replace("def main():\n m=read(B/'manifest.json');", "def main():\n raise RuntimeError('DRAFT_LOCKED_NOT_ROOT_REVIEWED: finish explicit new reserve kinds and final configuration preflight before any DAT write')\n m=read(B/'manifest.json');")
compile(s,str(O/'ApplyX18Structure.py'),'exec');out=O/'ApplyX18Structure.py';out.write_text(s,encoding='utf-8')
meta=dict(Status='DRAFT_LOCKED_NOT_ROOT_REVIEWED_NO_DATABASE_WRITES',CreatedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),Seed=str(SEED),SeedSHA256=EXPECTED,Writer=str(out),WriterSHA256=sha(out),NamefixPlan=str(ROOT/'FmLauncher/data/research/CLUB_NAME_LOOKUP_FIX_20261113/patch-plan.json'),NamefixSHA256='d0024b012e4ec305cf45fa5a4b0dbd2ba3670ba46dd4f535157bc25f28f743be',KoldingConversionApplied=False,ProtectedKolding=['TEAM1846/UID2121 exactincludingkind3/div566','ownFAMILY1648','historicalFAMILY8540'],VenueUIDStart=1800230001,Schema='X17 unchanged manifest/club-plan/foreign-owner-plan/structure-config/new-clubs-sugar-daddy-audit.csv/audit/nations.csv',AddedChecks=['12source-namefix edits before one apply','multiple new reserves per new/old parent typed aggregation','preserved Kolding source-range overlap and target bitwise proof','allgenerated cross UID uniqueness','fresh parent member vector readback'],NativeApply='LOCKED_NO_MAIN_EXECUTION',Remaining=['explicit new reserve kind3/16 per final plan, AlmereU23 confirmation','root final602+extras/config/ALT/rawcountpreflight','full adapter review and target readback before accepted nativePASS'])
(O/'adapter-pins.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8');print('COMPILE PASS',meta['WriterSHA256']);print('bytes',len(s));print('main NOT EXECUTED')
