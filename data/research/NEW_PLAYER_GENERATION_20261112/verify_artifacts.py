from pathlib import Path
import hashlib,json,re
root=Path(__file__).resolve().parent
m=json.loads((root/"manifest.json").read_text(encoding="utf-8"))
checked=0
for row in m["files"]:
 p=root/row["path"]
 assert p.is_file(),str(p)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==row["sha256"],str(p)
 checked+=1
for f in json.loads((root/"findings.json").read_text(encoding="utf-8"))["claims"]:
 for p in f["evidence"]:
  assert (root/p).is_file(),p
for link in re.findall(r"\]\(([^)]+)\)",(root/"RAPORT.md").read_text(encoding="utf-8")):
 if "://" not in link:
  assert (root/link).exists(),link
print(json.dumps({"status":"PASS","files":checked,"claims":len(json.loads((root/"findings.json").read_text(encoding="utf-8"))["claims"])}))
