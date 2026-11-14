from pathlib import Path
import json,sys,hashlib,shutil,subprocess
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent;OLD=R/'COUNTRY_BATCH_CZE_CRO_CHN_CHI_BGR_BRA_20261113/native-prep';T=B/'tools';rd=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# Keep all byte-layout/native contract code unchanged; configure only the strict batch scope.
s=(OLD/'tools/ApplyRosterBatch-Scope-r2.cs').read_text(encoding='utf-8-sig').replace('cze6338','blr5201').replace('x10?338:','x10?201:').replace('cze-cro-chn-chi-bgr-bra','blr-bel-aut-aus-arg-20261114').replace('new[]{137,135,55,190,134,189}','new[]{132,131,129,177,180,187}').replace('current six-country','current five-country')
old='((cp["Country"]=="Czech Republic"&&ci==137)||(cp["Country"]=="Croatia"&&ci==135)||(cp["Country"]=="China"&&ci==55)||(cp["Country"]=="Chile"&&ci==190)||(cp["Country"]=="Bulgaria"&&ci==134)||(cp["Country"]=="Brazil"&&ci==189))'
new='((cp["Country"]=="Belarus"&&ci==132)||(cp["Country"]=="Belgium"&&ci==131)||(cp["Country"]=="Austria"&&ci==129)||(cp["Country"]=="Australia"&&(ci==177||ci==180))||(cp["Country"]=="Argentina"&&ci==187))'
assert s.count(old)==1;s=s.replace(old,new);(T/'ApplyRosterBatch-Scope.cs').write_text(s,encoding='utf-8')
s=(OLD/'tools/ApplyBatchRoster.cs').read_text(encoding='utf-8-sig').replace('cze6338','blr5201');(T/'ApplyBatchRoster.cs').write_text(s,encoding='utf-8')
previous=rd(OLD/'tools/current-roster-build-r2.json');seed=rd(OLD/'tools/current-roster-build-manifest.json');args=[]
for v in seed['Arguments']:
 if v.startswith('/out:'):args.append('/out:'+str(T/'ApplyBatchRoster-Current.exe'))
 elif v.startswith('/r:') and v.endswith('FM08_Database_Editor.exe'):args.append('/r:'+str(T/'FM08_Database_Editor.exe'))
 elif v.endswith('.cs') and Path(v).name in ['ApplyRosterBatch-Scope.cs','ApplyBatchRoster.cs']:args.append(str(T/Path(v).name))
 else:
  if v.endswith('.cs'):assert sha(Path(v))==previous['Sources'][v],('core source drift',v)
  args.append(v)
assert not(T/'ApplyBatchRoster-Current.exe').exists();z=subprocess.run([seed['Compiler']]+args,capture_output=True,text=True);(T/'build.log').write_text(z.stdout+z.stderr,encoding='utf-8');assert z.returncode==0,z.stdout+z.stderr
(T/'build-manifest.json').write_text(json.dumps(dict(Status='STRICT_COUNTRY_SCOPE_CONFIGURED_CORE_UNCHANGED',Compiler=seed['Compiler'],Arguments=args,CoreSourcePins={v:sha(Path(v))for v in args if v.endswith('.cs')},OutputSHA256=sha(T/'ApplyBatchRoster-Current.exe'),MainEditorRebuilt=False),indent=2)+'\n',encoding='utf-8')
s=(OLD/'close_prepared_csv.py').read_text(encoding='utf-8-sig').replace('len(cm)==338','len(cm)==201').replace('==8318','==5174').replace('==6278','==4081').replace("'2026-11-13'","'2026-11-14'").replace("scope_id='cze-cro-chn-chi-bgr-bra'","scope_id='blr-bel-aut-aus-arg-20261114'").replace('N4Covered6278','N4Covered4081').replace('SourceFrozen24Unchanged','SourceFrozen21Unchanged').replace('Projection338Unchanged','Projection201Unchanged').replace('CountryAllocation338Complete','CountryAllocation201Complete').replace('SingleN4Read6278','SingleN4Read4081')
(B/'close_prepared_csv.py').write_text(s,encoding='utf-8')
s=(OLD/'prepare_typed_contract_boundaries.py').read_text(encoding='utf-8-sig').replace('len(cm)==338','len(cm)==201');(B/'prepare_typed_contract_boundaries.py').write_text(s,encoding='utf-8');shutil.copy2(OLD/'resolve_typed_contract_boundaries.ps1',B/'resolve_typed_contract_boundaries.ps1')
s=(OLD/'integrate_stage.py').read_text(encoding='utf-8-sig').replace("source_reference_date='2026-11-13'","source_reference_date='2026-11-14'").replace('target_country_indices=[137,135,55,190,134,189]','target_country_indices=[132,131,129,177,180,187]').replace('immutable_X19','immutable_X20');(B/'integrate_stage.py').write_text(s,encoding='utf-8')
for fn in ['close_prepared_csv.py','prepare_typed_contract_boundaries.py','integrate_stage.py']:compile((B/fn).read_text(encoding='utf-8'),str(B/fn),'exec')
print('Existing roster worker scoped201 clubs/5countries+NZ; main editor/core unchanged. Prepared close and native contract resolver reused.',flush=True)
