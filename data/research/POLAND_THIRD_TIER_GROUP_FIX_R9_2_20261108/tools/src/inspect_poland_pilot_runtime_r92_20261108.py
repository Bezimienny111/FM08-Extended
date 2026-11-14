"""Read-only snapshots of the explicitly launched R9.2 process; optional local JSON output."""
from pathlib import Path
from datetime import datetime,timezone,date,timedelta
import argparse,ctypes,hashlib,json,struct,csv
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'FmLauncher/data/research/POLAND_THIRD_TIER_GROUP_FIX_R9_2_20261108'

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output');args=parser.parse_args()
 log=max((OUT/'pilot-logs').glob('*.jsonl'),key=lambda p:p.stat().st_mtime)
 installed=json.loads(log.read_text(encoding='utf-8-sig').splitlines()[0])
 assert installed['event']=='installed' and installed['exe_sha256']=='157F484BE2EAD4AB27006D1002C2C666A7228197B88B14C8D026E76F31B1D62D'
 k=ctypes.WinDLL('kernel32',use_last_error=True)
 k.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32];k.OpenProcess.restype=ctypes.c_void_p
 k.ReadProcessMemory.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.ReadProcessMemory.restype=ctypes.c_int
 k.CloseHandle.argtypes=[ctypes.c_void_p]
 handle=k.OpenProcess(0x10,False,installed['process_id']);assert handle,ctypes.get_last_error()
 def read(address,count):
  assert 0x10000<=address<0x80000000 and 0<count<=0x10000
  buf=ctypes.create_string_buffer(count);got=ctypes.c_size_t()
  assert k.ReadProcessMemory(handle,address,buf,count,ctypes.byref(got)) and got.value==count,(hex(address),ctypes.get_last_error())
  return buf.raw
 u=lambda b,o=0:struct.unpack_from('<I',b,o)[0]
 short=lambda b,o=0:struct.unpack_from('<h',b,o)[0]
 def uid_at(ptr):return u(read(ptr+0x14,4)) if ptr else None
 try:
  state=read(int(installed['state'],16),96);collection=read(u(state,12),16)
  assert u(collection)==0x015F4AD4 and collection[8]==7,'Original Poland collection no longer valid'
  objects=read(u(collection,4),collection[8]*4)
  today=read(0x01B1EE14,6);year=short(today,2);day=short(today,0)
  assert 2007<=year<=2100 and 0<=day<=366
  result=dict(captured_at=datetime.now(timezone.utc).isoformat(),process_id=installed['process_id'],log=str(log.relative_to(OUT)),game_date=(date(year,1,1)+timedelta(days=day)).isoformat(),game_year=year,game_day_of_year_zero_based=day,read_only=True,competitions=[])
  union=set()
  for i in range(collection[8]):
   address=u(objects,i*4);comp=read(address,0x160);uid=u(comp,0x14)
   if uid not in (129559,1800001000,129560):continue
   count=comp[0xD4];assert 0<count<16
   stage_array=read(u(comp,0xD0),count*4);stages=[];league_addresses=[]
   for j in range(count):
    stage_address=u(stage_array,j*4);stage=read(stage_address,0x50)
    stage_id=u(stage,0x1C).to_bytes(4,'big').decode('ascii',errors='replace')
    stages.append(dict(index=stage[0x18],id=stage_id,vtable=hex(u(stage)),address=hex(stage_address)))
    if j==0:
     if u(stage)==0x0160F90C:
      assert stage[0x48]==4;league_addresses=list(struct.unpack('<4I',read(u(stage,0x44),16)))
     else:league_addresses=[stage_address]
   clubs=[];leagues=[]
   for index,league_address in enumerate(league_addresses):
    head=read(league_address,0x70);assert u(head)==0x015FF21C
    n=head[0x38];assert n in (18,25)
    rows=read(u(head,0x34),n*0x50);uids=[];assignments=[]
    for rank in range(n):
     team=u(rows,rank*0x50);data=read(team,0x60);club=u(data,0x14);uids.append(club)
     assignments.append(dict(club_uid=club,current_division_uid=uid_at(u(data,0x54)),next_division_uid=uid_at(u(data,0x58))))
    assert len(set(uids))==n
    clubs+=uids;leagues.append(dict(group=index,club_count=n,club_uids=uids,assignments=assignments,fixtures_generated=bool(head[0x6D])))
   assert len(set(clubs))==len(clubs) and not union.intersection(clubs),'Competition memberships overlap'
   union.update(clubs)
   result['competitions'].append(dict(uid=uid,season_year=short(comp,0xD8),stage_count=count,stages=stages,club_count=len(clubs),club_uids=sorted(clubs),club_uid_set_sha256=hashlib.sha256(struct.pack('<'+'I'*len(clubs),*sorted(clubs))).hexdigest(),leagues=leagues))
  assert {x['uid']:x['club_count'] for x in result['competitions']}=={129559:18,1800001000:18,129560:100}
  result['total_unique_clubs']=len(union);assert len(union)==136
  if args.output:
   target=(OUT/'runtime-snapshots'/args.output).resolve();base=(OUT/'runtime-snapshots').resolve()
   assert target.is_relative_to(base) and target.suffix=='.json'
   target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists(),'Refuse overwrite snapshot'
   target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  print(json.dumps(dict(game_date=result['game_date'],process_id=result['process_id'],total_unique_clubs=result['total_unique_clubs'],competitions=[{k:x[k] for k in ['uid','season_year','stage_count','club_count','club_uid_set_sha256']} for x in result['competitions']],snapshot=args.output),indent=2))
 finally:k.CloseHandle(handle)

if __name__=='__main__':main()
