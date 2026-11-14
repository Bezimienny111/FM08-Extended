from pathlib import Path
import sys,json,csv,hashlib
sys.dont_write_bytecode=True
sys.path.insert(0,'J:/FM08dev/FM08-Database-Tools/scratch')
from create_italy_structure_i1_20261108 import load,languages,lang_sections,find_table,club
B=Path(__file__).resolve().parent.parent;OUT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
source=B/'structure-root-r2/structure-db';public=Path('J:/FM08dev/Dane/db/TEST_X17')
inputs=[source/'lang_db.dat',source/'client_db.dat',public/'lang_db.dat',public/'client_db.dat',B/'prepared/club_map.csv']
before={str(p):sha(p)for p in inputs}
slots=[r for r in rows(B/'prepared/club_map.csv')if r['Country']=='Indonesia' or r['Country']=='India' and int(r['DivisionIndex'])==643]
assert len(slots)==86 and len({r['ClubUID']for r in slots})==86
result=[];snapshot=[]
for tag,folder in [('private_R2',source),('public_X17_after_SI',public)]:
 blocks=dict(languages((folder/'lang_db.dat').read_bytes()));alllangs={}
 for lang,data in blocks.items():
  sec,_=lang_sections(data);alllangs[lang]={x['uid']:x['names']for x in sec['club']}
 families,_,_=find_table(load(folder,'client_db.dat'),list(alllangs[8]),club);byuid={x['uid']:x for x in families}
 for r in slots:
  uid=int(r['ClubUID']);f=byuid[uid];en=alllangs[8].get(uid);pl=alllangs[18].get(uid)
  vals={str(k):v.get(uid)for k,v in alllangs.items()}
  missing=[k for k,v in vals.items()if not v or not v[0].strip() or not v[1].strip()]
  result.append(dict(Snapshot=tag,UID=uid,TMID=r['TMID'],ExpectedClub=r['ClubName'],Country=r['Country'],DivisionIndex=int(r['DivisionIndex']),FamilyIndex=f['index'],English=en,Polish=pl,EmbeddedFull=f['embedded_full_name'],EmbeddedShort=f['embedded_short_name'],MissingFullOrShortLanguages=missing,AllLanguages=vals,PL_or_EN_blank=any(not v or not v[0].strip() or not v[1].strip()for v in [en,pl])))
 snapshot.append(dict(Snapshot=tag,Path=str(folder),LANGSHA=sha(folder/'lang_db.dat'),CLIENTSHA=sha(folder/'client_db.dat'),LanguageCount=len(alllangs)))
after={str(p):sha(p)for p in inputs};assert before==after,'Source changed during narrow read'
dump(OUT/'all-86-slots.json',result)
findings=[r for r in result if r['PL_or_EN_blank']]
dump(OUT/'initial-findings.json',dict(Status='READ_ONLY_86_SLOT_NAME_AUDIT_COMPLETE',SnapshotPins=snapshot,InputsBefore=before,InputsAfter=after,ScopedSlots=86,Findings=findings,PublicDatabaseMutated=False,GameOrProcessAccess=False))
print(json.dumps(dict(Snapshots=snapshot,Findings=[{k:r[k]for k in ['Snapshot','UID','TMID','ExpectedClub','Country','DivisionIndex','English','Polish','EmbeddedFull','EmbeddedShort']}for r in findings]),ensure_ascii=True))