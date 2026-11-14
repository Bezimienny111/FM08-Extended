"""Verify actual TEAM references independently of same-UID NAME records."""
from pathlib import Path
import csv,hashlib,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(r"J:\FM08dev")
sys.path.insert(0,str(ROOT/"FM08-Database-Tools/scratch"))
from audit_poland_v25_common_r1_20261108 import Cursor,lang_sections,find_table,club
from create_native_u23_test import language_blocks
from create_club_stadium_native_n1_20261108 import load
from apply_native_finance_templates import finance
B=ROOT/"FmLauncher/data/research/COUNTRY_BATCH_GER_MEX_MAS_20261112"
AUDIT=ROOT/"FmLauncher/data/research/NAMES_FINANCE_X14_20261112"
OUT=AUDIT/"team-reference-verified"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def main():
 assert __debug__ and not OUT.exists()
 freeze=read(B/"source-freeze.json");source=Path(freeze["frozen"])
 def pins():return {str(p.relative_to(source)):sha(p) for p in source.rglob("*") if p.is_file()}
 expected={k:v.lower() for k,v in freeze["hashes"].items()};assert pins()==expected
 baseline_manifest=read(AUDIT/"manifest.json")
 oldpath=AUDIT/"club-finance-raw.csv"
 assert sha(oldpath)==baseline_manifest["artifacts"]["club-finance-raw.csv"]
 with oldpath.open(encoding="utf-8-sig",newline="") as f:old=list(csv.DictReader(f))
 assert len(old)==1250 and len({x["club_uid"] for x in old})==1250
 records={r["ClubUID"]:r for r in read(B/"native-structure.json")["records"]}
 en,_=lang_sections(dict(language_blocks((source/"lang_db.dat").read_bytes()))[8])
 client=load(source,"client_db.dat");server=load(source,"server_db.dat")
 clubs,_,_=find_table(client,[r["uid"] for r in en["club"]],club)
 existing={int(r["family_index"]):r for r in old}
 moneykeys=["payload_offset","sugar_daddy","raw_f04_s32","raw_f10_s32","raw_d18_hex","raw_f20_s32","raw_f14_s32","raw_f3c_s32","payload_sha256","finance_kind"]
 result=[];corrections=[]
 for oldrow in old:
  uid=int(oldrow["club_uid"]);r=records[uid]
  assert server[r["Start"]]==10 and struct.unpack_from("<iI",server,r["Footer"])==(r["TeamIndex"],uid)
  start=r["RosterOffset"]+2+4*struct.unpack_from("<H",server,r["RosterOffset"])[0]
  assert r["Start"]<start<r["Footer"]
  hits=[]
  for pos in range(start+4,r["Footer"]-13):
   if server[pos-3]!=0:continue  # TEAM_BASE club discriminator, not arbitrary flag bytes
   fi=struct.unpack_from("<i",server,pos)[0]
   if not 0<=fi<len(clubs):continue
   cur=Cursor(server,pos+4)
   try:
    cur.string();cur.byte();cur.string();cur.byte()
    if cur.p!=r["Footer"]:continue
   except (AssertionError,UnicodeError,struct.error):continue
   hits.append((fi,pos,server[pos-4]))
  assert len(hits)==1,("Ambiguous/missing TEAM family tail",uid,hits)
  fi,offset,kind=hits[0];family_uid=clubs[fi]["uid"]
  row=dict(oldrow);row.update(name_audit_family_index=oldrow["family_index"],
    name_audit_family_uid=oldrow["finance_family_uid"],family_index=fi,finance_family_uid=family_uid,
    shared_family_finance=int(family_uid!=uid),team_family_reference_offset=offset,team_kind_byte=kind)
  if fi!=int(oldrow["family_index"]):
   cached=existing.get(fi)
   if cached:
    assert int(cached["finance_family_uid"])==family_uid
    row.update({k:cached[k] for k in moneykeys})
    at=int(row["payload_offset"])
    assert hashlib.sha256(server[at:at+45]).hexdigest()==row["payload_sha256"]
   else:
    at,payload=finance(server,client,clubs,fi,family_uid)
    row.update(payload_offset=at,sugar_daddy=payload[4],finance_kind=0,
      raw_f04_s32=struct.unpack_from("<i",payload,0)[0],raw_f10_s32=struct.unpack_from("<i",payload,5)[0],
      raw_d18_hex=payload[9:13].hex(),raw_f20_s32=struct.unpack_from("<i",payload,13)[0],
      raw_f14_s32=struct.unpack_from("<i",payload,19)[0],raw_f3c_s32=struct.unpack_from("<i",payload,23)[0],
      payload_sha256=hashlib.sha256(payload).hexdigest())
   corrections.append(dict(club_uid=uid,club=row["club"],name_family=int(oldrow["family_index"]),
    actual_team_family=fi,actual_family_uid=family_uid,reference_offset=offset,kind=kind))
  result.append(row)
 assert pins()==expected
 summary=dict(status="ACTUAL_TEAM_FAMILY_REFERENCE_VERIFIED",database_modified=False,
    clubs=len(result),distinct_finance_families=len({r["family_index"] for r in result}),
    teams_with_parent_finance=sum(r["shared_family_finance"] for r in result),
    same_UID_NAME_assumptions_corrected=len(corrections),
    sugar_daddy_on=[int(r["club_uid"]) for r in result if int(r["sugar_daddy"])==1],
    source_hashes_unchanged=True,old_NAME_inventory_preserved=True,
    TEAM_base_flags_proof="C7D4A0 reads four header bytes and FAMILY int32; club discriminator zero, other flags remain raw; unique FAMILY+two strings+suffixes+exact identity footer required",
    financial_units_verified=False,source_hashes=expected)
 OUT.mkdir()
 with (OUT/"club-finance-raw.csv").open("x",encoding="utf-8-sig",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(result[0]));w.writeheader();w.writerows(result)
 for name,data in [("summary.json",summary),("reference-corrections.json",corrections)]:
  (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 manifest=dict(status=summary["status"],script_sha256=sha(Path(__file__)),
    baseline_manifest_sha256=sha(AUDIT/"manifest.json"),
    inputs={"native-structure.json":sha(B/"native-structure.json")},
    artifacts={p.name:sha(p) for p in OUT.iterdir() if p.is_file()})
 (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({k:v for k,v in summary.items() if k!="source_hashes"},ensure_ascii=True))
if __name__=="__main__":main()
