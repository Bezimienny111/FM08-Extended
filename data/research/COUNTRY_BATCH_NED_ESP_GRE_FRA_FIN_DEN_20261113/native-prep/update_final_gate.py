from pathlib import Path
import ast
B=Path('J:/FM08dev/FmLauncher/data/research/COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep');p=B/'finalize_native_package.py';s=p.read_text(encoding='utf-8')
a="assert qa['Status']=='NUMERIC_SELECTION_REGRESSION_PASS' and len(qa['Checks'])==325 and not qa['NewRegressions'] and not qa['CurrentBatchFailures']"
b=a+"\ncurrent_checks=qa['CurrentBatchChecks'];assert (len(current_checks)if isinstance(current_checks,list)else int(current_checks))==92\nif isinstance(current_checks,list):assert all(x.get('passed',x.get('Passed',False))for x in current_checks)"
assert a in s;s=s.replace(a,b)
a="structure=read(B/'root-structure/root-independent-verification.json');assert structure['status']=='PASS_NATIVE_INVERSE_SCOPE_AND_READBACK_GLOBAL_SELECTION_PENDING' and len(structure['both_forms'])==92 and all(r['passed']for r in structure['both_forms'])"
b="structure=read(B/'root-structure/root-independent-verification.json');assert structure['status']=='PASS_NATIVE_INVERSE_SCOPE_AND_READBACK_GLOBAL_SELECTION_PENDING' and structure['inverse_SERVER_CLIENT_all_languages'] and structure['UID_TEAM_family_projection_exact'] and structure['unrelated_TEAM_bytes_previous_regional_preserved'] and structure['people_and_other_files_identical'] and structure['source_unchanged']"
assert a in s;s=s.replace(a,b).replace("new_stadiums=len(sr.get('new_stadiums',[]))","new_stadiums=int(sr['new_stadiums'])").replace('project_families_SugarDaddy_OFF=522',"project_families_SugarDaddy_OFF=structure['project_families_SugarDaddy_OFF']")
ast.parse(s);p.write_text(s,encoding='utf-8');print('FINALGATE: root inverse/scope + actualQA325/92; no duplicated forms required')
