"""Exact Kolding source-space edits. Never writes DAT, allocates UID or changes shared staging.
Root-reviewed complete typed owner/contract guard is mandatory for public prepare().
"""
from pathlib import Path
import hashlib,json,struct,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent
PLAN_SHA256="8a4f2fccfa9f6a0bd40d5401f9e2e06e5b348504a15dd1454074e4e61e2af870"
SERVER_RAW_SHA256="e4c39751f2a216bedf6779d216b6f484f115766a616f772dace81c7a657ec64e"
def _read_plan():
 p=O/'conversion-plan.json';raw=p.read_bytes()
 assert hashlib.sha256(raw).hexdigest()==PLAN_SHA256,'conversion_plan_hash_changed'
 return json.loads(raw.decode('utf-8-sig'))
def _layout(server):
 """Private layout dryrun only. Returns edits and whole-buffer inverse proof."""
 p=_read_plan();assert hashlib.sha256(server).hexdigest()==SERVER_RAW_SHA256,'wrong_or_already_mutated_source_buffer'
 ident=p['Identity'];assert ident['PreserveClubUID']==2121 and ident['PreserveTEAMIndex']==1846 and ident['PreserveOwnFAMILY']==1648 and ident['PreserveHistoricalClubUID']==928820 and ident['BeforeTailFamily']==8540 and ident['AfterTailFamily']==1648
 edits=[]
 for e in p['Edits']:
  off=e['Offset'];old=bytes.fromhex(e['BeforeHex']);new=bytes.fromhex(e['AfterHex']);assert server[off:off+len(old)]==old,'source_slot_changed';edits.append((off,len(old),new))
 assert len(edits)==4 and len({e[0]for e in edits})==4
 edits.sort();assert all(a[0]+a[1]<=b[0]for a,b in zip(edits,edits[1:]))
 q=server
 for off,n,new in reversed(edits):q=q[:off]+new+q[off+n:]
 shift=0;inv=[]
 for e,(off,n,new)in zip(sorted(p['Edits'],key=lambda r:r['Offset']),edits):
  at=off+shift;assert q[at:at+len(new)]==new;inv.append((at,len(new),bytes.fromhex(e['BeforeHex'])));shift+=len(new)-n
 assert shift==0 and len(q)==len(server);restored=q
 for off,n,old in reversed(inv):restored=restored[:off]+old+restored[off+n:]
 assert restored==server,'whole_buffer_inverse_failed'
 return edits,dict(SourcePlanSHA256=PLAN_SHA256,SourceSERVERDecompressedSHA256=SERVER_RAW_SHA256,Edits=4,NewUIDs=0,NewTEAMs=0,NewFAMILies=0,WholeBufferInverse=True,ApplySpace='UNMODIFIED_SOURCE_OFFSETS',DataBaseWritten=False)
def prepare(server,owner_guard_path,expected_owner_guard_sha256):
 """Returns four (sourceOffset,oldSize,newBytes) edits for common writer after all guards.
 The caller must merge with all other edits against the SAME unmodified source buffer.
 No DB write happens here. Do not apply returned offsets after any prior variable-size edit.
 """
 p=_read_plan();guardraw=Path(owner_guard_path).read_bytes();assert hashlib.sha256(guardraw).hexdigest()==expected_owner_guard_sha256,'owner_guard_not_reviewed_pin';g=json.loads(guardraw.decode('utf-8-sig'))
 assert g['Status']=='PASS','typed_owner_guard_not_pass'
 assert g['SourceHashes']==p['SourceHashes'],'guard_source_mismatch'
 assert g['Scope']==dict(TEAM=1846,OwnFamily=1648,HistoricalFamily=8540),'guard_scope_mismatch'
 assert g['CompleteTypedOwnerAndContractCoverage']is True,'incomplete_typed_owner_contract_coverage'
 assert g['OwnerTEAM1846Rows']==[],'existing_owner_actor_requires_explicit_contract_plan'
 assert g['UnresolvedReferences']==[]and g['ActorMigrations']==[],'unresolved_or_unauthorized_actor_changes'
 assert g['Historical8540ContractsPreserved']is True,'historical_club_actor_protection_missing'
 ed,proof=_layout(server);proof['OwnerGuardSHA256']=expected_owner_guard_sha256;proof['Status']='READY_SOURCE_EDITS_NO_WRITE';return ed,proof
