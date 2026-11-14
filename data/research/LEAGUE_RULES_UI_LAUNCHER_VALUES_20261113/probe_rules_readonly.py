from pathlib import Path
import sys,importlib.util,struct,json,hashlib,datetime
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent
P=B.parent/'CONTROVERSY_CONTROL_8074_20261111/probe_runtime_readonly.py'
spec=importlib.util.spec_from_file_location('existing_rpm',P);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
m=mod.WindowsMemory(11056)
u=lambda a:struct.unpack('<I',m.read(a,4))[0]
result=dict(status='PENDING',pid=11056,image=m.image,access='0x410 QUERY_INFORMATION|VM_READ',writes=False,remote_calls=False,debug_attach=False,paused=False,scan_budget=268435456,raw_dumps=False,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
try:
 result['getters']={}
 for key,addr in [('subs',0xafe0d0),('bench',0xafe150)]:
  raw=m.read(addr,5);rec=dict(address=addr,entry_hex=raw.hex(),entry_kind='original' if raw==bytes.fromhex('0fbe442404') else 'unknown')
  if raw[0]==0xe9:
   target=addr+5+struct.unpack_from('<i',raw,1)[0];rec.update(entry_kind='jump',target=target)
   try:
    payload=m.read(target-64,96)
    rec.update(candidate_payload_sha256=hashlib.sha256(payload).hexdigest(),code0_enabled=payload[0],code0_value=payload[32],all_enabled=list(payload[:29]),values=list(payload[32:61]))
   except Exception as e:rec['payload_error']=str(e)
  result['getters'][key]=rec
 result['formatter_AFDBF0_entry']=m.read(0xafdbf0,16).hex()
 found=[];seen=0;needle=struct.pack('<I',0x156daf4);budget=result['scan_budget']
 for start,size in m.regions():
  for off in range(0,size,524285):
   n=min(524288,size-off,budget-seen)
   if n<4:break
   try:data=m.read(start+off,n)
   except Exception:continue
   seen+=n;pos=0
   while True:
    pos=data.find(needle,pos)
    if pos<0:break
    p=start+off+pos;pos+=1
    if p%4:continue
    try:
     r=mod.col(m,p)
     if r['name']!='.?AVRULES_PANEL@@' or r['complete']!=p:continue
     if [u(p+x) for x in [16,20,24]]!=[0x156dae0,0x156dab8,0x156daac]:continue
     comp=u(p+0x88);cr=mod.col(m,comp);db=mod.resolve_base(m,cr['complete'],cr['hierarchy'],'.?AVDATABASE_RECORD@@');uid=u(db['address']+0x14)
     count=struct.unpack('<H',m.read(p+0x9c,2))[0];cap=struct.unpack('<H',m.read(p+0xa0,2))[0];ptr=u(p+0x98)
     if uid!=32 or not 0<count<=cap<=256 or u(p+0x94)!=0x128114c:continue
     rows=[]
     for i in range(count):
      row=u(ptr+4*i);b=m.read(row,0x648);typ=b[0]
      if typ>37:raise ValueError('unexpected row type')
      v=dict(index=i,address=row,type=typ,sha256=hashlib.sha256(b).hexdigest())
      if typ==8:v.update(rule_code=b[0x28+0x1b9],payload_flags=struct.unpack_from('<I',b,0x28+8)[0],restriction_count=struct.unpack_from('<I',b,0x28+0x1b0)[0])
      if typ in [1,2,3,4,5,6,7,34,35,36,37]:v['number']=struct.unpack_from('<b',b,0x20)[0]
      if typ==16:v['match_count_bytes']=list(b[0x609:0x60d])
      rows.append(v)
     stable=u(p+0x88)==comp and u(p+0x98)==ptr and struct.unpack('<H',m.read(p+0x9c,2))[0]==count and all(hashlib.sha256(m.read(v['address'],0x648)).hexdigest()==v['sha256']for v in rows)
     found.append(dict(panel=p,selected_comp_pointer=comp,competition_uid=uid,competition_rtti=cr,stage_context_bytes=list(m.read(p+0x8c,2)),count=count,rows=rows,stable=stable))
    except Exception:continue
   if found or seen>=budget:break
  if found or seen>=budget:break
 result.update(scanned_bytes=seen,matches=found,status='PASS_readonly_panel_snapshot'if len(found)==1 and found[0]['stable'] else 'UNKNOWN_panel_not_unique_or_not_found')
except Exception as e:result.update(status='UNKNOWN_readonly_probe',reason=type(e).__name__+': '+str(e))
finally:m.close()
out=B/'runtime-readonly.json'
if out.exists():raise RuntimeError('preserve existing evidence')
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=result['status'],scanned_bytes=result.get('scanned_bytes'),panels=len(result.get('matches',[])),getters=result.get('getters')),indent=2))
