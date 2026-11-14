from pathlib import Path
import re,json,hashlib,xml.etree.ElementTree as ET
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
BASE=(ROOT/'Dane/graphics/pictures/logos').resolve()
def h(b):return hashlib.sha256(b).hexdigest()
uids=set(json.loads((OUT/'logo-uids.json').read_text(encoding='utf-8')))
def istarget(node):
 m=re.fullmatch(r'graphics/pictures/club/(\d+)/(logo|icon)',node.get('to',''))
 return bool(m and int(m[1]) in uids)
def attrs(blob,exclude=False):
 root=ET.fromstring(blob)
 return [tuple(sorted(n.attrib.items())) for n in root.iter('record') if n.get('to') and (not exclude or not istarget(n))]
def prepare():
 entries=[];untouched={};alltargets=0
 for path in sorted(BASE.rglob('config.xml')):
  if 'modern_2627' in path.parts:continue
  assert path.resolve().is_relative_to(BASE)
  old=path.read_bytes();tree=ET.fromstring(old)
  selected=[n for n in tree.iter('record') if istarget(n)]
  if not selected:untouched[str(path)]=h(old);continue
  spans=[]
  for match in re.finditer(rb'<record\b[^>]*?/\s*>',old):
   node=ET.fromstring(match.group(0))
   if istarget(node):spans.append((match.start(),match.end()))
  assert len(spans)==len(selected),(path,len(spans),len(selected))
  new=old
  for a,b in reversed(spans):new=new[:a]+new[b:]
  after=ET.fromstring(new)
  assert not any(istarget(n) for n in after.iter('record'))
  assert attrs(old,True)==attrs(new,True)
  rel=path.relative_to(BASE)
  backup=OUT/'legacy-config-backups'/rel
  entries.append(dict(path=str(path),backup=str(backup),before_sha256=h(old),after_sha256=h(new),removed=len(selected),removed_maps=[n.attrib for n in selected],old=old,new=new))
  alltargets+=len(selected)
 modern=[ROOT/'Dane/graphics/pictures/faces/normal/modern_2627/config.xml',BASE/'clubs/normal/modern_2627/config.xml',BASE/'clubs/small/modern_2627/config.xml',ROOT/'Dane/graphics/pictures/kits/2d/modern_2627/config.xml']
 protected={str(p):h(p.read_bytes()) for p in modern}
 return entries,untouched,protected,alltargets
def main():
 entries,untouched,protected,total=prepare()
 plan=dict(status='planned_prevalidated',target_uids=sorted(uids),files=len(entries),removed_maps=total,entries=[{k:v for k,v in e.items() if k not in ['old','new']} for e in entries],untouched_configs=untouched,protected_modern_configs=protected,legacy_png_modified=False)
 (OUT/'legacy-logo-neutralization-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
 written=[];prepared=[]
 try:
  for entry in entries:
   path=Path(entry['path']);backup=Path(entry['backup']);backup.parent.mkdir(parents=True,exist_ok=True)
   if backup.exists():assert backup.read_bytes()==entry['old']
   else:backup.write_bytes(entry['old'])
   tmp=path.with_name('config.xml.modern2627.tmp')
   assert not tmp.exists(),tmp
   tmp.write_bytes(entry['new']);ET.parse(tmp)
   prepared.append((entry,tmp))
  for entry,tmp in prepared:
   path=Path(entry['path'])
   assert h(path.read_bytes())==entry['before_sha256'],path
   tmp.replace(path);written.append(entry)
  for entry in entries:
   actual=Path(entry['path']).read_bytes()
   assert h(actual)==entry['after_sha256']
   assert attrs(entry['old'],True)==attrs(actual,True)
   assert not any(istarget(n) for n in ET.fromstring(actual).iter('record'))
  for path,pin in untouched.items():assert h(Path(path).read_bytes())==pin
  for path,pin in protected.items():assert h(Path(path).read_bytes())==pin
 except Exception as error:
  rollback=[]
  for entry in reversed(written):
   path=Path(entry['path'])
   if h(path.read_bytes())==entry['after_sha256']:
    tmp=path.with_name('config.xml.modern2627.rollback')
    tmp.write_bytes(Path(entry['backup']).read_bytes());tmp.replace(path)
    rollback.append(dict(path=str(path),restored_sha256=h(path.read_bytes())))
   else:rollback.append(dict(path=str(path),blocked='concurrent_change_preserved'))
  for _,tmp in prepared:
   if tmp.exists():tmp.unlink()
  (OUT/'legacy-logo-neutralization-result.json').write_text(json.dumps(dict(status='failed_rolled_back',error=str(error),rollback=rollback),ensure_ascii=False,indent=2),encoding='utf-8')
  raise
 result=dict(status='verified',files_changed=len(entries),old_logo_icon_mappings_removed=total,verified_modern_uids=len(uids),non_target_maps_identical=True,untouched_xml_pins_identical=True,modern_configs_pins_identical=True,old_png_unchanged_by_operation=True,all_xml_parse=True,backups_outside_loader=str(OUT/'legacy-config-backups'),finished_utc=datetime.now(timezone.utc).isoformat())
 (OUT/'legacy-logo-neutralization-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(result),flush=True)
if __name__=='__main__':main()
