from pathlib import Path
import hashlib,json,subprocess
root=Path('J:/FM08dev'); repo=root/'reference/OpenFM2007'; out=root/'FmLauncher/data/research/EUROPEAN_CUPS_FM07_GAP_REVIEW_20261110'
old=json.loads((root/'FmLauncher/data/research/OPENFM2007_UEFA_ANALYSIS_20261108/report.json').read_text(encoding='utf-8-sig'))
commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
assert commit==old['commit']
checked={}
for rel,expected in old['source_sha256'].items():
 p=repo/rel; actual=hashlib.sha256(p.read_bytes()).hexdigest(); assert actual==expected.lower(),rel; checked[rel]=actual
assert subprocess.check_output(['git','-C',str(repo),'status','--short'],text=True).strip()==''
manifest=dict(status='analysis_completed_no_implementation',date='2026-11-10',repository=str(repo),commit=commit,repository_clean=True,source_hashes_verified=checked,scope=['UEFA_FM07_implemented_offline_runtime_gaps','FM08_port_prerequisites','minimum_safe_implementation_plan'],upstream_latest_gate=dict(task='T47.1',status='next',source='phase-ends/current/PHASE_PLAN.md:193'),new_runtime_tests=False,new_C_tests=False,prior_97_comparer_tests='existing_20261108_evidence_not_rerun',game_or_database_changes=False,shared_document_changes=False,follow_up='evaluate_user_format_idea_before_implementation')
manifest['artifact_hashes']={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in out.iterdir()if p.is_file() and p.name != 'manifest.json'}
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('PASS review saved; source hashes match prior review; reference unchanged; no game/database mutations')



# Additional read-only sources inspected for the companion contract.
extra_sources=['FmLauncher/src/FmLauncher/CareerIdentity.cs','FmLauncher/src/FmLauncher/GameLeagueDiagnosticsPatch.cs','FmLauncher/src/FmLauncher/LeagueDiagnostics.cs','FmLauncher/src/FmLauncher/LeagueProfileAutomation.cs','FmLauncher/src/FmLauncher/LeagueChanges.cs','FmLauncher/src/FmLauncher/GameLauncher.cs','FmLauncher/src/FmLauncher/SuspendedGameProcess.cs','FmLauncher/tests/FmLauncher.Tests/LeagueDiagnosticsTests.cs','FmLauncher/tests/FmLauncher.Tests/ProfileAutomationTests.cs','FmLauncher/DOCUMENTATION.md','FMExt/fm08_compendium.md','FmLauncher/data/research/GHIDRA_ENGINE_20261107_R5/decompiled/functions/ram_4669a0.c','FmLauncher/data/research/GHIDRA_ENGINE_20261107_R5/decompiled/functions/ram_465210.c','reference/OpenFM2007/mod/src/savearc.c','reference/OpenFM2007/mod/src/savearc.h']
manifest['companion_contract']=dict(status='design_only_no_implementation',document='SAVE_COMPANION_CONTRACT.md',known_save_event_not_proven_final_commit=True,save_path_and_revision_missing=True,old_career_migration_not_implemented=True,new_runtime_tests=False,source_hashes={p:hashlib.sha256((root/p).read_bytes()).hexdigest()for p in extra_sources})
manifest['artifact_hashes']={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in out.iterdir()if p.is_file() and p.name != 'manifest.json'}
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('PASS companion design evidence and artifact hashes recorded')

