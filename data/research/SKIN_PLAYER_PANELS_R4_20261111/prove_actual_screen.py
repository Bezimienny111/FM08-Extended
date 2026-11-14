import runpy,json,hashlib
from pathlib import Path
B=Path(__file__).parent;S=Path('FmLauncher/data/research/R3_RUNTIME_FAILURE_20261111/root-readonly/memory-regions')
q=runpy.run_path('FmLauncher/data/research/SKIN_PLAYER_PANELS_R3_20261111/offline_reader.py');C=q['OfflineMemory'];C.__init__.__globals__['BASE']=S;m=C()
a=runpy.run_path('FmLauncher/data/research/CONTROVERSY_CONTROL_8074_20261111/probe_runtime_readonly.py')
get=lambda rows,key:next(x for x in rows if x['tag']==key)
def ref(rows,key):
 x=get(rows,key);assert x['vtable']==0x166e1a4;r=m.bag(x['value']);d=get(r,'dref');assert d['vtable']==0x166dde4
 assert not any(y['tag']=='dcnt'for y in r);packed=d['value'];assert packed>>24==1 and (packed&0xffffff)<0x7fffff;return packed
def lookup(off,index):
 t=m.u(0x1b1ecd0+off);p=t+0x10 if index<m.u(t+0x18) else m.u(t+4);assert 0<=index<m.u(p+8)and m.u(m.u(p)+0x2c)==0xf9a0d0;return m.u(m.u(p+4)+4*index)
def club(p):
 t=m.u(p-m.i(p-4)+0x70);assert m.u(t)==0x15a9e0c and m.read(t+0x40,1)==bytes([0]);c=m.u(t+0x38);assert m.u(c)==0x15996c4;return c
lst=m.u(0x1bc1cb8);assert 0<m.u(lst+8)<=32;connections=[m.u(m.u(lst+4)+4*i)for i in range(m.u(lst+8))]
conn=next(x for x in connections if m.u(x+0x40)==m.u(0x1bc1c34));assert m.u(conn)==0x12843a4 and m.u(m.u(conn+0x64))==0x1672f38 and m.read(0x191136a,1)==bytes([0])
screen=m.u(conn+0x44);assert m.u(screen)==0x12a002c;sp=m.bag(m.u(screen+0x3c));selected=ref(sp,'dref');viewer=ref(sp,'Hhum')
profile=m.u(0x1c40004);chain=[];walk=profile
while walk and walk not in chain and len(chain)<32:chain.append(walk);walk=m.u(walk+4)
assert screen in chain
proxy=m.u(profile+0x88);assert m.u(proxy)==0x12776cc;cp=m.bag(proxy+0x10);assert get(cp,'dtty')['value']==1 and get(cp,'dsha')['value']==selected&0x7fffff and get(cp,'dsub')['value']==0x50706c79 and not any(x['tag']=='dcnt'for x in cp)
hp=lookup(0x38,viewer&0x7fffff);hr=a['col'](m,hp);assert m.u(hp)==0x15ae024 and hr['name']=='.?AVHUMAN_NON_PLAYER@@' and m.u(hr['complete'])==0x15ae30c and m.u(hp+0x18)==viewer&0x7fffff
hc=club(hp)
tr=get(m.bag(get(cp,'Pcte')['value']),'dref')['value'];assert tr>>24==0x18;t=lookup(0x68,tr&0x7fffff);assert m.u(t)==0x15a9e0c and m.read(t+0x40,1)==bytes([0]) and m.u(t+0x38)==hc
pp=lookup(0x38,selected&0x7fffff);c=Path('FmLauncher/data/research/CONTROVERSY_CONTROL_8074_20261111');player=a['validate_selected_person'](m,pp,a['readjson'](c/'unique-trait-proof.json')['codec'],a['readjson'](c/'runtime-field-layout.json'));assert club(pp)==hc
assert m.bag(0x1b1f0f4)==[]
r=dict(status='PASS_ACTUAL_R3_SNAPSHOT_SCREEN_VIEWER_SCOPE_IDENTITY8',snapshot_index_sha256=hashlib.sha256((S/'index.json').read_bytes()).hexdigest(),snapshot_description='R3 stable display failure; no crash/context exception. Root corrected description only, chunks unchanged.',server_scratch_Hhum=None,server_C927B0_semantic_result=0,connection=hex(conn),connectionType='GAME_SCREEN_CLIENT',screen=hex(screen),screenType='PERSON_SCREEN',profile=hex(profile),ancestor_chain=[hex(x)for x in chain],proxy=hex(proxy),SCREEN_selected_ref=hex(selected),SCREEN_Hhum_ref=hex(viewer),actual_screen_Hhum_and_selected_variant_type='OBJECT_DATA_TYPE 0166E1A4 -> PROPERTY_LIST -> native INTEGER dref',HUMAN_PERSON=hex(hp),HUMAN_RTTI=hr,CLUB=hex(hc),publicTEAM_matches_HUMAN_before_selected_lookup=True,PLAYER=player,process_access=False,remote_execution=False,snapshot_modified=False,production_heap_scan=False,GUI_acceptance='PENDING_R4; R3 FAIL remains')
(B/'actual-screen-viewer-witness.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
print(r['status'],'UID',player['UID'],'DOB',player['DOB'],'8traits',[x['Value']for x in player['Fields']])
