import runpy,json,hashlib
from pathlib import Path
B=Path(__file__).parent
m=runpy.run_path(str(B/'offline_reader.py'))['OfflineMemory']()
q=runpy.run_path('FmLauncher/data/research/CONTROVERSY_CONTROL_8074_20261111/probe_runtime_readonly.py')
def get(rows,tag):return next(x for x in rows if x['tag']==tag)
def lookup(off,index):
 t=m.u(0x1b1ecd0+off);a=t+0x10 if index<m.u(t+0x18) else m.u(t+4)
 assert 0<=index<m.u(a+8) and m.u(m.u(a)+0x2c)==0xf9a0d0
 return m.u(m.u(a+4)+4*index)
assert m.read(0xc7c7a0,14)==bytes.fromhex('8a414084c0740333c0c38b4138c3')
props=m.bag(0x202b4350);ref=get(m.bag(get(props,'Pcte')['value']),'dref')
assert get(props,'Pcte')['vtable']==0x166e1a4 and ref['vtable']==0x166dde4 and ref['value']>>24==0x18
team=lookup(0x68,ref['value']&0x7fffff);assert m.u(team)==0x15a9e0c
assert m.read(team+0x40,1)==b'\0';club=m.u(team+0x38);assert m.u(club)==0x15996c4
hhum=get(m.bag(0x1b1f0f4),'Hhum');hr=get(m.bag(hhum['value']),'dref')['value'];assert hr>>24==1
hp=lookup(0x38,hr&0x7fffff);human=q['col'](m,hp);assert human['name']=='.?AVHUMAN_NON_PLAYER@@' and m.u(human['complete'])==0x15ae30c
ht=m.u(hp-m.i(hp-4)+0x10c-0x9c);assert m.u(ht)==0x15a9e0c and m.read(ht+0x40,1)==b'\0' and m.u(ht+0x38)==club
assert get(props,'dtty')['value']==1 and get(props,'dsub')['value']==0x50706c79
p=lookup(0x38,get(props,'dsha')['value'])
c=Path('FmLauncher/data/research/CONTROVERSY_CONTROL_8074_20261111')
player=q['validate_selected_person'](m,p,q['readjson'](c/'unique-trait-proof.json')['codec'],q['readjson'](c/'runtime-field-layout.json'))
r=dict(status='PASS_ACTUAL_SNAPSHOT_PUBLIC_TEAM_OWNER_IDENTITY8',offline_only=True,source_pid=10940,process_access=False,remote_execution=False,production_scan=False,proxy=0x202b4340,public_ref=ref,TEAM=team,CLUB=club,club_UID=m.u(club+0x14),HUMAN=human,HUMAN_PERSON=hp,HUMAN_TEAM=ht,ownclub_before_PLAYER_lookup=True,PLAYER=player,GUI_acceptance='PENDING_R3; R2 remains FAIL',R3source_sha256=hashlib.sha256(Path('FmLauncher/src/FmLauncher/GameProfileResolver.cs').read_bytes()).hexdigest())
(B/'actual-snapshot-witness.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
print(r['status'],'UID',player['UID'],'DOB',player['DOB'],'clubUID',r['club_UID'],'8traits',[(x['Name'],x['Value'])for x in player['Fields']])
