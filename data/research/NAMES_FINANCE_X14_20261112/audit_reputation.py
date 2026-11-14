"""Read-only reputation candidate inventory; no database or process mutation."""
from pathlib import Path
import csv,hashlib,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(r"J:\FM08dev")
sys.path.insert(0,str(ROOT/"FM08-Database-Tools/scratch"))
from create_club_stadium_native_n1_20261108 import load
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
import pefile
B=ROOT/"FmLauncher/data/research/COUNTRY_BATCH_GER_MEX_MAS_20261112"
OUT=ROOT/"FmLauncher/data/research/NAMES_FINANCE_X14_20261112/reputation"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def main():
    assert __debug__ and not OUT.exists()
    freeze=read(B/"source-freeze.json");source=Path(freeze["frozen"])
    inputs=[source/"server_db.dat",B/"native-structure.json",B/"native-world-identities.json",ROOT/"fm.exe"]
    pins={str(p):sha(p) for p in inputs}
    assert pins[str(inputs[0])]==freeze["hashes"]["server_db.dat"].lower()
    assert pins[str(ROOT/"fm.exe")]=="157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d"
    world=read(B/"native-world-identities.json")
    assert len({x["ClubUID"] for x in world})==len(world)
    world={x["ClubUID"]:x for x in world}
    records=read(B/"native-structure.json")["records"];server=load(source,"server_db.dat")
    rows=[]
    shortlist={602,630,676,679,868,907,915,1135,1139,1708}
    for record in records:
        start,end=record["Start"],record["Footer"]
        uid,ti=record["ClubUID"],record["TeamIndex"];identity=world[uid]
        assert 0<=start<end<=len(server)-8 and server[start]==10
        assert struct.unpack_from("<iI",server,end)==(ti,uid)
        assert identity["TeamIndex"]==ti
        assert struct.unpack_from("<i",server,start+7)[0]==record["CurrentDivisionIndex"]
        values=struct.unpack_from("<hh",server,start+3)
        rows.append(dict(club_uid=uid,team_index=ti,family_uid=identity["FamilyUID"],
            name=next(iter(identity["Names"]), ""),country_index=identity["Country"],
            dat_team_start=start,raw_s16_at3=values[0],raw_s16_at5=values[1],
            native_field="TEAM_runtime_0x70_candidate_reputation",
            si_label_single_field_verified=False,shortlisted=int(uid in shortlist)))
    pe=pefile.PE(str(ROOT/"fm.exe"),fast_load=True)
    md=Cs(CS_ARCH_X86,CS_MODE_32)
    evidence={}
    for va,size in [(0xCA0340,0x190),(0xC9DCA0,0x40),(0xC9CFA0,0x10)]:
        code=pe.get_data(va-pe.OPTIONAL_HEADER.ImageBase,size)
        evidence[hex(va)]=dict(bytes_hex=code.hex(),sha256=hashlib.sha256(code).hexdigest(),
            instructions=[dict(address=hex(i.address),mnemonic=i.mnemonic,operands=i.op_str)
                          for i in md.disasm(code,va)])
    setter=evidence[hex(0xC9CFA0)]["instructions"]
    assert any(i["mnemonic"]=="mov" and "[ecx + 0x70]" in i["operands"] for i in setter)
    assert pins=={str(p):sha(p) for p in inputs}
    OUT.mkdir()
    for name,items in [("team-field-inventory.csv",rows),("shortlist-existing-values.csv",[r for r in rows if r["shortlisted"]])]:
        with (OUT/name).open("x",encoding="utf-8-sig",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(items[0]));w.writeheader();w.writerows(items)
    result=dict(status="READ_ONLY_FIELD_INVENTORY_NOT_A_REPUTATION_PATCH",source_pins=pins,
        team_records=len(rows),blank_name_rows=sum(not r["name"] for r in rows),raw_at3_min=min(r["raw_s16_at3"] for r in rows),
        raw_at3_max=max(r["raw_s16_at3"] for r in rows),shortlist_count=sum(r["shortlisted"] for r in rows),
        field_serialization_verified=True,si_label_single_field_verified=False,
        new_values_assigned=False,database_modified=False,native_evidence=evidence)
    (OUT/"evidence.json").write_text(json.dumps(result,ensure_ascii=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in ("native_evidence","source_pins")},ensure_ascii=True))
if __name__=="__main__":main()
