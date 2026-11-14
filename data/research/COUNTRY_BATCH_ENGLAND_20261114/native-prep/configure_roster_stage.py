from pathlib import Path
import json,sys,hashlib,shutil,subprocess
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=Path(__file__).resolve().parent;OLD=R/'COUNTRY_BATCH_BLR_BEL_AUT_AUS_ARG_20261114/native-prep';T=B/'tools';rd=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# Keep all byte-layout/native contract code unchanged; configure only the strict batch scope.
s=(OLD/'tools/ApplyRosterBatch-Scope.cs').read_text(encoding='utf-8-sig').replace('blr5201','eng164').replace('x10?201:','x10?164:').replace('blr-bel-aut-aus-arg-20261114','england-20261114').replace('new[]{132,131,129,177,180,187}','new[]{139,175}').replace('current five-country','current England')
old='((cp["Country"]=="Belarus"&&ci==132)||(cp["Country"]=="Belgium"&&ci==131)||(cp["Country"]=="Austria"&&ci==129)||(cp["Country"]=="Australia"&&(ci==177||ci==180))||(cp["Country"]=="Argentina"&&ci==187))'
new='(cp["Country"]=="England"&&(ci==139||ci==175))'
assert s.count(old)==1;s=s.replace(old,new).replace('x10?1712000000:','x10?1714000000:').replace('x10?1714000000:','x10?1716000000:',1)
# Explicit isolated ID ranges; replace declaration after bounded scope edits.
s=s.replace('new IdPool(x10?1716000000:','new IdPool(x10?1714000000:').replace(':1681000000,x10?1714000000:',':1681000000,x10?1716000000:')
s=s.replace('x10?1819000000:','x10?1820000000:').replace(':1801000000,x10?1820000000:',':1801000000,x10?1821000000:')
(T/'ApplyRosterBatch-Scope.cs').write_text(s,encoding='utf-8')
s=(OLD/'tools/ApplyBatchRoster.cs').read_text(encoding='utf-8-sig').replace('blr5201','eng164');(T/'ApplyBatchRoster.cs').write_text(s,encoding='utf-8')
previous=rd(OLD/'tools/build-manifest.json');previous['Sources']=previous['CoreSourcePins'];seed=previous;args=[]
for v in seed['Arguments']:
 if v.startswith('/out:'):args.append('/out:'+str(T/'ApplyBatchRoster-Current.exe'))
 elif v.startswith('/r:') and v.endswith('FM08_Database_Editor.exe'):args.append('/r:'+str(T/'FM08_Database_Editor.exe'))
 elif v.endswith('.cs') and Path(v).name in ['ApplyRosterBatch-Scope.cs','ApplyBatchRoster.cs']:args.append(str(T/Path(v).name))
 else:
  if v.endswith('.cs'):assert sha(Path(v))==previous['Sources'][v],('core source drift',v)
  args.append(v)
assert not(T/'ApplyBatchRoster-Current.exe').exists();z=subprocess.run([seed['Compiler']]+args,capture_output=True,text=True);(T/'build.log').write_text(z.stdout+z.stderr,encoding='utf-8');assert z.returncode==0,z.stdout+z.stderr
(T/'build-manifest.json').write_text(json.dumps(dict(Status='STRICT_COUNTRY_SCOPE_CONFIGURED_CORE_UNCHANGED',Compiler=seed['Compiler'],Arguments=args,CoreSourcePins={v:sha(Path(v))for v in args if v.endswith('.cs')},OutputSHA256=sha(T/'ApplyBatchRoster-Current.exe'),MainEditorRebuilt=False),indent=2)+'\n',encoding='utf-8')

s=(OLD/'integrate_stage.py').read_text(encoding='utf-8-sig').replace('target_country_indices=[132,131,129,177,180,187]','target_country_indices=[139,175]').replace('immutable_X20','immutable_X22');(B/'integrate_stage.py').write_text(s,encoding='utf-8')
for fn in ['verify_roster.py','apply_rosters.py','apply_legacy_ratings.py']:
 s=(OLD/fn).read_text(encoding='utf-8-sig').replace('Wrong current five-country set','Wrong current England set').replace('COUNTRY_BATCH_CZE_CRO_CHN_CHI_BGR_BRA_20261113/native-prep','COUNTRY_BATCH_BLR_BEL_AUT_AUS_ARG_20261114/native-prep')
 (B/fn).write_text(s,encoding='utf-8')
print('England164 strict scope worker built; common byte-layout unchanged; no main editor rebuild',flush=True)
