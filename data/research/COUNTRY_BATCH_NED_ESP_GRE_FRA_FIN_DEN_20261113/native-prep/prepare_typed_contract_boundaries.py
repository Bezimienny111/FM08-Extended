from pathlib import Path
import json,csv,hashlib,struct,sys,subprocess
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev'); B=Path(__file__).resolve().parent;W=B/'root-structure';P=B/'prepared';sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
from create_italy_structure_i1_20261108 import load,languages,lang_sections,find_table,club
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
source=W/'structure-db';report=read(W/'structure-report.json');assert read(W/'root-independent-verification.json')['status']=='PASS_NATIVE_INVERSE_SCOPE_AND_READBACK_GLOBAL_SELECTION_PENDING'
assert all(sha(source/k)==v.lower()for k,v in report['output_hashes'].items())
cm=rows(W/'club-map.csv');assert len(cm)==602
teams={int(c['TeamIndex'])for c in cm};prov=read(P/'provenance.json');teams.update(int(p['owner_club'])for p in prov)
# Projected teamindices and materialised map are already independently equal. Source owner-only entities remain existing native clubs.
a=load(source,'server_db.dat');client=load(source,'client_db.dat');en,_=lang_sections(dict(languages((source/'lang_db.dat').read_bytes()))[8]);families,_,_=find_table(client,[x['uid']for x in en['club']],club)
world=read(B/'native-world-identities.json');plans={str(x['TMID']):x for x in read(B/'club-plan.json')};byti={}
for x in cm:
 plan=plans[x['TMID']];fi=plan.get('NativeContractFamilyIndex')
 if fi is None:fi=int(x['FamilyIndex'])
 byti[int(x['TeamIndex'])]=dict(FamilyIndex=int(fi))
byti.update({x['TeamIndex']:dict(FamilyIndex=x['TeamTailFamilyIndex'],ClubUID=x['TeamTailFamilyUID'])for x in world if x['TeamIndex']in teams and x['TeamIndex']not in byti})
needed={int(byti[t]['FamilyIndex'])for t in teams};req=[];teamstart=min(r['Start']for r in read(W/'native-structure-after.json')['records'])
for fi in sorted(needed):
 uid=families[fi]['uid'];pat=struct.pack('<iI',fi,uid);positions=[];at=a.find(pat,0,teamstart)
 while at>=0:positions.append(at);at=a.find(pat,at+1,teamstart)
 assert positions,(fi,uid);req.append(dict(FamilyIndex=fi,FamilyUID=uid,Positions=positions))
candidates=P/'typed-family-candidates.json';result=P/'typed-family-boundary-result.json';dump(candidates,dict(TeamStart=teamstart,Teams=sorted(teams),Families=req))
cmd=['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(B/'resolve_typed_contract_boundaries.ps1'),'-Editor',str(B/'tools/FM08_Database_Editor.exe'),'-Source',str(source),'-Candidates',str(candidates),'-Output',str(result)]
z=subprocess.run(cmd,capture_output=True,text=True);(B/'typed-family-boundaries.log').write_text(z.stdout+z.stderr,encoding='utf-8');assert z.returncode==0,z.stdout+z.stderr
actual=read(result);assert {int(k):int(v)for k,v in actual['Resolution'].items()}=={t:int(byti[t]['FamilyIndex'])for t in teams},'Materialised contract FAMILY differs from typed existing tail/projected reserve parent'
dump(P/'native-contract-resolution.json',actual['Resolution']);dump(P/'typed-family-footers.json',actual['TypedOffsets'])
assert all(sha(source/k)==v.lower()for k,v in report['output_hashes'].items())
dump(B/'typed-family-witness-proof.json',dict(status='typed_native_family_footer_unique_for_all_requested_families',source_server_sha256=sha(source/'server_db.dat'),source_client_sha256=sha(source/'client_db.dat'),native_editor_sha256=sha(B/'tools/FM08_Database_Editor.exe'),candidates_sha256=sha(candidates),typed_offsets_sha256=sha(P/'typed-family-footers.json'),source_contract_resolver_sha256=sha(P/'native-contract-resolution.json'),predicate=actual['Predicate'],requested_TEAMs=len(teams),typed_FAMILYs=len(needed),database_modified=False))
print('MATERIALISED',len(teams),'TEAMreferences and',len(needed),'typedFAMILYfootersPASS')
