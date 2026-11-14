import runpy,json,struct,sys
from pathlib import Path
q=runpy.run_path(str(Path(__file__).with_name('probe_runtime_readonly.py')))
B=Path(__file__).parent;pid=int(sys.argv[1]);out=B/sys.argv[2];assert not out.exists()
expected=q['readjson'](B/'unique-trait-proof.json')['codec'];layout=q['readjson'](B/'runtime-field-layout.json')
m=q['WindowsMemory'](pid);matches=[];rejected=[];hits=0;typed=0;scanned=0;seen=set()
try:
 needle=struct.pack('<I',8074)
 for start,size in m.regions():
  for offset in range(0,size,1048576-3):
   try:data=m.read(start+offset,min(1048576,size-offset))
   except q['Rejected']:continue
   scanned+=len(data);q['require'](scanned<=1024**3,'byte budget')
   i=0
   while True:
    i=data.find(needle,i)
    if i<0:break
    a=start+offset+i;i+=1
    if a%4:continue
    hits+=1;person=a-0x14
    if person in seen:continue
    seen.add(person)
    try:
     if q['u32'](m,person)!=q['PERSON_VT']:continue
     typed+=1;matches.append(q['validate_selected_person'](m,person,expected,layout))
    except q['Rejected']as e:
     if typed:rejected.append(dict(PERSON=person,error=str(e)))
 result=dict(status='PASS_controlled_runtime8_actual_PLAYER'if len(matches)==1 and matches[0]['All8Match']else'FAIL_ambiguous_absent_or_values_mismatch',pid=pid,identity_selection='Known UID field PERSON+14, native vtable, RTTI, PMD virtual base, DOB; NEVER candidate value',scanned_bytes=scanned,raw_uid_hits=hits,typed_PERSON_hits=typed,matches=matches,rejected=rejected,GUI_profile_link='PENDING_CLIENT_BASE_PERSON_proxy_is_not_ACTUAL_PLAYER; actual identity selected independently',remote_execution=False,process_writes=False,suspended=False)
finally:m.close()
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,ensure_ascii=True,indent=2))
