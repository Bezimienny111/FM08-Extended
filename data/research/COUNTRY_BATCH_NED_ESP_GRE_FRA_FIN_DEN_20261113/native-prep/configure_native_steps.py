from pathlib import Path
import json,csv,hashlib,ast
B=Path(__file__).resolve().parent;OLD=B.parents[1]/'COUNTRY_BATCH_IDN_IND_HKG_20261112';P=B/'prepared'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def edit(s,a,b):
 assert a in s,a
 return s.replace(a,b)
for filename in ['club-plan.json','club-UID-projection.json']:
 obj=read(B/filename)
 if isinstance(obj,list):
  for x in obj:
   if str(x.get('TMID'))=='7393':x['NativeCountryIndex']=158
 else:
  # Projection has maps/counters; edit only exact projected entity, never a UID/index.
  def fix(v):
   if isinstance(v,list):
    for a in v:fix(a)
   elif isinstance(v,dict):
    if str(v.get('TMID'))=='7393':v['NativeCountryIndex']=158;v['CountryIndex']=158
    for a in list(v.values()):fix(a)
  fix(obj)
 dump(B/filename,obj)
for path in [B/'club-map.csv',P/'club_map.csv']:
 with path.open(encoding='utf-8-sig',newline='')as f:rs=list(csv.DictReader(f));fields=list(rs[0])
 r=next(x for x in rs if x['TMID']=='7393');assert r['ClubUID']=='1800220090'and r['TeamIndex']=='24285';r['CountryIndex']='158'
 with path.open('w',encoding='utf-8-sig',newline='')as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rs)
m=read(P/'manifest.json');m['prepared_hashes']['club_map.csv']=h(P/'club_map.csv');dump(P/'manifest.json',m)
receipt=read(B/'prepared-csv-ready.json');receipt['Files']['club_map.csv']=h(P/'club_map.csv');receipt['Files']['manifest.json']=h(P/'manifest.json');receipt['RootApprovedCountryMetadata7393']=158;dump(B/'prepared-csv-ready.json',receipt)
s=(OLD/'prepare_typed_contract_boundaries.py').read_text(encoding='utf-8')
s=edit(s,"W=B/'structure-root-r2'","W=B/'root-structure'");s=edit(s,"=='PASS_PRIVATE_NATIVE_STRUCTURE_NOT_SI_OR_RUNTIME'","=='PASS_NATIVE_INVERSE_SCOPE_AND_READBACK_GLOBAL_SELECTION_PENDING'");s=edit(s,'len(cm)==133','len(cm)==602')
a="world=read(B/'native-world-identities.json');byti={int(x['TeamIndex']):x for x in cm};byti.update({x['TeamIndex']:dict(FamilyIndex=x['TeamTailFamilyIndex'],ClubUID=x['TeamTailFamilyUID'])for x in world if x['TeamIndex']in teams and x['TeamIndex']not in byti})"
b="""world=read(B/'native-world-identities.json');plans={str(x['TMID']):x for x in read(B/'club-plan.json')};byti={}
for x in cm:
 plan=plans[x['TMID']];fi=plan.get('NativeContractFamilyIndex')
 if fi is None:fi=int(x['FamilyIndex'])
 byti[int(x['TeamIndex'])]=dict(FamilyIndex=int(fi))
byti.update({x['TeamIndex']:dict(FamilyIndex=x['TeamTailFamilyIndex'],ClubUID=x['TeamTailFamilyUID'])for x in world if x['TeamIndex']in teams and x['TeamIndex']not in byti})"""
s=edit(s,a,b);s=s.replace("'Materialised contract FAMILY differs from reviewed ownfirstfamily'","'Materialised contract FAMILY differs from typed existing tail/projected reserve parent'")
(B/'prepare_typed_contract_boundaries.py').write_text(s,encoding='utf-8')
s=(OLD/'integrate_stage.py').read_text(encoding='utf-8');s=edit(s,"W=B/'structure-root-r2'","W=B/'root-structure'")
s=s.replace("['ClubUID','TeamIndex','FamilyIndex','CountryIndex','DivisionIndex','ParentUID']","['ClubUID','TeamIndex','FamilyIndex','CountryIndex','ParentUID']")
start=s.index(' exceptions=[]');end=s.index(' # Keep every CSV row schema explicit.',start)
s=s[:start]+''' exceptions=[]
 from create_italy_structure_i1_20261108 import load,languages,lang_sections,find_table,club
 client=load(source,'client_db.dat');en,_=lang_sections(dict(languages((source/'lang_db.dat').read_bytes()))[8]);families,_,_=find_table(client,[x['uid']for x in en['club']],club)
 plans={x['TMID']:x for x in read(B/'club-plan.json')}
 for row in core:
  fi=resolution[str(row['TeamIndex'])];plan=plans[row['TMID']];expected=plan.get('NativeContractFamilyIndex')
  if expected is None:expected=int(row['FamilyIndex'])
  assert fi==int(expected),('Contract actual typed family differs',row['TMID'],fi,expected)
  row['OwnFamilyIndex']=row['FamilyIndex'];row['ContractFamilyUID']=str(families[fi]['uid']);row['ContractFamilyIndex']=str(fi)
  if fi!=int(row['FamilyIndex']):exceptions.append(dict(ClubUID=int(row['ClubUID']),OwnFamilyIndex=int(row['FamilyIndex']),ContractFamilyIndex=fi,ContractFamilyUID=families[fi]['uid'],Source='source typed TEAMtail + actual native resolver + unique materialized typed FAMILY boundary'))
  row['FamilyIndex']=str(fi)
 dump(B/'contract-family-exceptions.json',exceptions)
''' +s[end:]
s=s.replace("source_reference_date='2026-11-12'","source_reference_date='2026-11-13'").replace('target_country_indices=[58,57,56]','target_country_indices=[138,142,143,146,158,170,127]').replace('source_player_audit_from_immutable_X16_people_byte_identical','source_player_audit_from_immutable_X17_people_byte_identical').replace('PASS_PRIVATE_NATIVE_STRUCTURE_NOT_SI_OR_RUNTIME','PASS_NATIVE_INVERSE_SCOPE_AND_READBACK_GLOBAL_SELECTION_PENDING')
# Actual owner-only refs also require tail FAMILY UID for foreign references.
s=s.replace("FamilyIndex=w['FamilyIndex'],ParentUID=w['ParentUID']or''","FamilyIndex=w['TeamTailFamilyIndex'],ParentUID=w['TeamTailFamilyUID']")
# Materialization map has final assignments; rows use actual parent witness above.
(B/'integrate_stage.py').write_text(s,encoding='utf-8')
s=(OLD/'finalize_native_package.py').read_text(encoding='utf-8');s=s.replace("B/'independent-selection-qa-r2/regression.json'","B/'root-structure/qa/regression.json'").replace("B/'structure-root-r2/","B/'root-structure/")
s=s.replace('==233','==325').replace('==3555','==14170').replace('==18 and','==92 and').replace('==101 and','==535 and').replace('==408 and','==921 and').replace('==232','==1157')
s=s.replace("for country in ['Indonesia','India','Hong Kong']:","for country in ['Netherlands','Spain','Greece','France','Finland','Denmark']:")
s=s.replace("=='PASS_PRIVATE_NATIVE_STRUCTURE_NOT_SI_OR_RUNTIME'","=='PASS_NATIVE_INVERSE_SCOPE_AND_READBACK_GLOBAL_SELECTION_PENDING'")
s=s.replace("venuegaps=len(sr['venue_gaps']);assert venuegaps==69","venuegaps=len(sr['venue_gaps'])")
start=s.index('# Unsupported old release');end=s.index('meta=dict(',start)
s=s[:start]+"legacyproof=dict(Status='No unsupported source participant bypass; frozen source actor contracts covered by10091 pinned N4 records',SourcePreflightComposite=read(B/'N4-source-contract-composite.json'))\n"+s[end:]
s=s.replace('source_collection_gaps=184,source_cards=3787,source_candidates=3603,source_loans=103,new_clubs=60,new_stadiums=97','source_collection_gaps=739,source_cards=15400,source_candidates=14661,source_loans=608,new_clubs=165,new_stadiums=len(sr.get(\'new_stadiums\',[]))')
s=s.replace('source_X16','source_X17').replace('frozen_X16','frozen_X17').replace('TEST_X17','TEST_X18').replace('inherited X16','inherited X17')
start=s.index("text='# TEST_X18");end=s.index("(B/'RAPORT.md').write_text",start)
s=s[:start]+"text='# TEST_X18 — Netherlands, Spain, Greece, France, Finland, Denmark\\n\\nNative PASS; SI, new career and season PENDING. Accepted frozen X17 preserved.\\n\\n'+json.dumps(meta,ensure_ascii=False,indent=2)+'\\n\\nStrict whole-file inverse, raw names/attributes/personality/DOB/contracts, actor UID ledger and typed CA/PA repair readbacks are pinned. Missing people remain explicit source gaps. Three verified X17 embedded club-name corrections included by root common structural writer. No EXE/rule change.\\n'\n"+s[end:]
s=s.replace(",B/'legacy-format-preserve23042954.json'",",B/'N4-source-contract-composite.json'")
s=s.replace("metadata='Verified private DAT; root replaces inherited X17 XML and metadata when publishing X17.'","metadata='Verified private DAT; root replaces inherited X17 XML and metadata when publishing X18.'")
(B/'finalize_native_package.py').write_text(s,encoding='utf-8')
for f in ['prepare_typed_contract_boundaries.py','integrate_stage.py','apply_rosters.py','verify_roster.py','apply_legacy_ratings.py','finalize_native_package.py']:ast.parse((B/f).read_text(encoding='utf-8'))
# Clean typo only in own handoff text.
p=B/'WZNOWIENIE.md';s=p.read_text(encoding='utf-8');s=s.replace('168? rzeczywistecountzraportu;niezgadywac','strukturę według rzeczywistych liczników raportu');p.write_text(s,encoding='utf-8')
print('X18 typed materialize-proof/integrate/pilot-full/ratings/finalizer adapters syntax PASS; no DATread or write',flush=True)
