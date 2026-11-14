"""Independent byte audit and source archive of the first native staff wage pilot."""
import json,shutil,struct,sys,xml.etree.ElementTree as ET
from pathlib import Path
sys.dont_write_bytecode=True
from analyze_buffon_loan_20261106 import ROOT,BASE,load,hashes,sha,integer,name_evidence,club_evidence,loan_rows,require
R=ROOT/'FmLauncher/data/research/STAFF_20261106_RANIERI'
REPO=ROOT/'FM08-Database-Tools';BUILD=REPO/'out/staff-20261106-r2'
FIXTURE=ROOT/'Dane/db/TEST_STAFF_WAGE';NATIVE=ROOT/'Dane/db/TEST_STAFF_NATIVE_R1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def staff_span(data):
    needle=struct.pack('<i',4201569);hits=[];pos=data.find(needle)
    while pos>=0:
        footer=pos-4
        if footer>=16 and integer(data,footer)==129460:
            prefix=struct.pack('<iB',129460,1);start=data.rfind(prefix,max(16,footer-4096),footer)
            if start>=16 and pos+4-start==272:hits.append((start,pos+4))
        pos=data.find(needle,pos+1)
    require(len(hits)==1,'independent Ranieri span missing/ambiguous');return hits[0]
def finalize():
    require(not (R/'independent.json').exists(),'independent report already exists')
    tests=read(R/'native-tests-r2.json');require(tests['status']=='pass' and tests['checks']==18,'staff checks failed')
    pins=[hashes(p) for p in [BASE,FIXTURE,NATIVE]]
    require(pins[0]==tests['baseline_hashes'] and pins[1]==tests['fixture_hashes'],'inputs changed since staff test')
    policy=read(ROOT/'FmLauncher/data/research/LOAN_RESEARCH_POLICY.json');require(pins[0]==policy['baseline_hashes'],'canonical 802 source changed')
    people=[load(p,'people_db.dat') for p in [BASE,FIXTURE,NATIVE]]
    servers=[load(p,'server_db.dat') for p in [BASE,FIXTURE,NATIVE]]
    spans=[staff_span(p) for p in people];rows=[p[a:b] for p,(a,b) in zip(people,spans)]
    require([integer(r,138) for r in rows]==[0,12345,12345],'wrong wage values')
    require(all(integer(r,75)==995 and r[79]==16 for r in rows),'club/raw role changed')
    expected=bytearray(people[0]);struct.pack_into('<i',expected,spans[0][0]+138,12345)
    require(people[2]==expected,'native output differs outside the wage int32')
    names=[]
    for word,offset in [('Claudio',29),('Ranieri',33)]:
        entries=[name_evidence(s,word,integer(r,offset)) for s,r in zip(servers,rows)]
        require(len({e['uid'] for e in entries})==1,'name UID changed');names.append(dict(name=word,snapshots=entries))
    normalized=bytearray(rows[1]);normalized[29:37]=rows[0][29:37]
    require(normalized==rows[2],'native PERSON differs from SI beyond resolved name references')
    clubs=[club_evidence(s,995,integer(p,0))[1] for s,p in zip(servers,people)]
    require(clubs[0]==clubs[1]==clubs[2],'Juventus record changed')
    loans=[loan_rows(s,140364)[1] for s in servers];require(loans[0]==loans[1]==loans[2] and len(loans[0])==6210,'loan table changed')
    protected=[]
    for file,value in pins[0].items():
        if file=='people_db.dat' or file.lower().endswith('.xml'):continue
        require(pins[2].get(file)==value,'protected native output file changed: '+file);protected.append(file)
    xml=NATIVE/'TEST_STAFF_NATIVE_R1.xml';require(xml.exists() and ET.parse(xml).getroot().find("string[@id='name']").get('value')==NATIVE.name,'output metadata name mismatch')
    for file in ['non_pl_hist_dt.dat','non_pl_hist_id.dat','non_pl_hist_index.dat','pl_hist_dt.dat','pl_hist_id.dat','pl_hist_index.dat']:
        require(pins[0][file]==pins[1][file]==pins[2][file],'history changed')
    require(pins==[hashes(p) for p in [BASE,FIXTURE,NATIVE]],'database changed during independent audit')
    result=dict(status='native_staff_wage_verified',person_uid=4201569,person_index=129460,person_type=1,staff_name='Claudio Ranieri',baseline=str(BASE),fixture=str(FIXTURE),native_output=str(NATIVE),baseline_hashes=pins[0],fixture_hashes=pins[1],native_output_hashes=pins[2],wage_before=0,wage_after=12345,wage_relative_offset_this_fixture=138,whole_native_people_matches_single_int32_edit=True,whole_person_matches_si_after_name_reference_resolution=True,names=names,juventus_record_identical=True,loans_preserved=6210,protected_files=protected,staff_checks_passed=18,source_and_fixture_unchanged=True,si_acceptance_of_native_output='not_tested',game_behavior='not_tested',gui_smoke='not_tested')
    save(R/'independent.json',result)
    manifest=read(BUILD/'build-manifest.json')
    for e in manifest['Sources']:require(sha(REPO/e['Path'])==e['SHA256'],'source changed since build')
    for e in manifest['Outputs']:require(sha(BUILD/e['Path'])==e['SHA256'],'binary changed since build')
    archive=R/'source-snapshot';archive.mkdir(exist_ok=False)
    files={e['Path'] for e in manifest['Sources']};files.update(['build.ps1','README.md','CSV_SCHEMA.md','IMPORTER_AKTUALNY_SCHEMAT_I_ZASADY.md','fm08_compendium.md','docs/NATIVE_STAFF.md','scratch/build_assignment_r6.ps1','scratch/analyze_buffon_loan_20261106.py','scratch/compare_native_player_tests.py','scratch/prepare_native_staff_20261106.py','scratch/finish_native_staff_20261106.py','scratch/verify_native_staff_20261106.py'])
    entries=[]
    for rel in sorted(files):
        dest=archive/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(REPO/rel,dest);entries.append(dict(path=rel,SHA256=sha(dest)))
    save(archive/'manifest.json',dict(source_only=True,files=entries));shutil.copy2(BUILD/'build-manifest.json',R/'build-manifest.json')
    save(R/'result.json',dict(status=result['status'],build=str(BUILD),staff_checks_passed=18,native_output=str(NATIVE),source_files_archived=len(entries),source_and_fixture_unchanged=True,scope='existing_contracted_type1_staff_read_and_wages_only',si_acceptance_of_native_output='not_tested',game_behavior='not_tested',gui_smoke='not_tested'))
    save(R.parent/'STAFF_RESEARCH_POLICY.json',dict(baseline=str(BASE),baseline_hashes=pins[0],baseline_read_only=True,latest_case=str(R),production_v25_unchanged=True,confirmed_operations=['read_supported_contracted_type1_staff_by_uid','update_existing_staff_weekly_wage'],unsupported_operations=['create_staff','transfer_staff','change_job_role','free_staff','national_team_contracts','combined_player_nonplayer']))
    print(json.dumps({k:result[k] for k in ['status','wage_before','wage_after','whole_native_people_matches_single_int32_edit','loans_preserved','staff_checks_passed','source_and_fixture_unchanged']}))
if __name__=='__main__':finalize()
