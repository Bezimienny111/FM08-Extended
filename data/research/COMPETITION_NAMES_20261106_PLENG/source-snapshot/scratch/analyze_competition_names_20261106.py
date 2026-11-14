"""Verify UID-based EN/PL competition names in the indexed language archive."""
import json,struct,sys,zlib
from pathlib import Path
sys.dont_write_bytecode=True
from analyze_buffon_loan_20261106 import ROOT,BASE,load,hashes,sha,integer,require,loan_rows
from compare_native_player_tests import occurrences,native_person_table_end
from create_native_u23_test import language_blocks,assemble_languages
REPO=ROOT/'FM08-Database-Tools';FIXTURE=ROOT/'Dane/db/TEST_NAMEL_PLENG'
OUT=ROOT/'FmLauncher/data/research/COMPETITION_NAMES_20261106_PLENG'
UID=129558

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def name_record(block,uid=UID):
    found=[]
    for start in occurrences(block,struct.pack('<i',uid)):
        at=start+4;fields=[]
        try:
            for i in range(3):
                length_at=at;n=integer(block,at);at+=4
                require(0<=n<=1000 and at+n*2+2<=len(block),'invalid localized name length')
                value=block[at:at+n*2].decode('utf-16-le');at+=n*2
                require(block[at:at+2]==bytes(2),'missing UTF-16 NUL');at+=2
                field=dict(text=value,utf16_units=n,length_offset=length_at,encoded_end=at)
                if i<2:field['suffix_byte']=block[at];at+=1
                fields.append(field)
            require(integer(block,at)==129559,'following competition UID mismatch')
            found.append(dict(start=start,end=at,uid=uid,fields=fields))
        except (ValueError,UnicodeError,struct.error,IndexError):continue
    require(len(found)==1,'missing or ambiguous localized competition record');return found[0]
def replace_full_name(block,expected,new):
    record=name_record(block);field=record['fields'][0]
    require(field['text']==expected,'old full-name precondition failed')
    encoded=new.encode('utf-16-le');replacement=struct.pack('<I',len(encoded)//2)+encoded+bytes(2)
    return block[:field['length_offset']]+replacement+block[field['encoded_end']:]
def competition_record(server):
    found=[]
    for at in occurrences(server,struct.pack('<i',UID)):
        start=at-64
        if start>=68 and at+72<=len(server) and server[start]==0 and integer(server,at-4)==139 and integer(server,at-72)==138 and integer(server,at-68)>0 and integer(server,at+64)==140 and integer(server,at+68)==129559:
            found.append((start,server[start:at+4]))
    require(len(found)==1,'missing or ambiguous native competition record');return found[0]
def analyze():
    require(not OUT.exists(),'research directory exists')
    refs=[ROOT/'Dane/db/TEST_STAFF_WAGE',ROOT/'Dane/db/TEST_LOAN'];paths=[BASE,FIXTURE]+refs;pins=[hashes(p) for p in paths]
    policy=read(ROOT/'FmLauncher/data/research/LOAN_RESEARCH_POLICY.json');require(pins[0]==policy['baseline_hashes'],'canonical baseline changed')
    wage=read(ROOT/'FmLauncher/data/research/STAFF_20261106_RANIERI/independent.json');loan=read(ROOT/'FmLauncher/data/research/LOANS_20261106_BUFFON/report.json')
    require(pins[2]==wage['fixture_hashes'] and pins[3]==loan['fixture_hashes'],'SI control fixture changed')
    raw=[(p/'lang_db.dat').read_bytes() for p in paths];blocks=[language_blocks(r) for r in raw]
    ids=[i for i,b in blocks[0]];require(all([i for i,b in bs]==ids for bs in blocks),'language-ID sequence changed')
    require(blocks[2]==blocks[3],'independent SI controls have different language data')
    expected_name='PKO Bank Polski Ekstraklasa';languages=[];changed=[];patched=[]
    for (lang,base),(_,target),(_,reference) in zip(blocks[0],blocks[1],blocks[2]):
        original,current,control=[name_record(b) for b in [base,target,reference]]
        old_fields=[f['text'] for f in original['fields']];new_fields=[f['text'] for f in current['fields']]
        require(old_fields==[f['text'] for f in control['fields']],'control already changed target league name')
        require(original['fields'][0].get('suffix_byte')==current['fields'][0].get('suffix_byte') and original['fields'][1].get('suffix_byte')==current['fields'][1].get('suffix_byte'),'name suffix flags changed')
        if lang in [8,18]:
            require(new_fields==[expected_name]+old_fields[1:],'short name/abbreviation also changed')
            updated=replace_full_name(reference,old_fields[0],expected_name);changed.append(lang)
        else:
            require(old_fields==new_fields,'another language changed target league names');updated=reference
        require(updated==target,'language changes extend beyond the selected full-name field in normalized SI control')
        patched.append((lang,updated))
        languages.append(dict(language_id=lang,language_label={8:'English',18:'Polish'}.get(lang),before=original,after=current,old_full_name=old_fields[0],new_full_name=new_fields[0],short_name=new_fields[1],abbreviation=new_fields[2],record_changed=old_fields!=new_fields,whole_block_identical_to_si_control=reference==target,baseline_block_length=len(base),fixture_block_length=len(target),si_control_block_length=len(reference),full_name_only_reconstruction_matches_si=True))
    require(changed==[8,18],'unexpected edited languages')
    rebuilt=assemble_languages(raw[2],[(lang,zlib.compress(b)) for lang,b in patched]);require(language_blocks(rebuilt)==blocks[1],'indexed language repack roundtrip differs from SI')
    p,q=[load(folder,'people_db.dat') for folder in [BASE,FIXTURE]];s,t=[load(folder,'server_db.dat') for folder in [BASE,FIXTURE]]
    before_comp,after_comp=[competition_record(buf) for buf in [s,t]]
    require(before_comp[1]==after_comp[1],'competition native record changed')
    require(p[:16]==q[:16],'native people counts changed')
    require(p[native_person_table_end(p):]==q[native_person_table_end(q):],'native people attribute tables changed')
    loans=[loan_rows(buf,140364)[1] for buf in [s,t]];require(loans[0]==loans[1] and len(loans[0])==6210,'loan table changed')
    history=['non_pl_hist_dt.dat','non_pl_hist_id.dat','non_pl_hist_index.dat','pl_hist_dt.dat','pl_hist_id.dat','pl_hist_index.dat']
    for f in history:require(pins[0][f]==pins[1][f],'history changed')
    moved=[];missing=[]
    for file,value in pins[0].items():
        if file.lower().startswith('lnc') and file not in pins[1]:
            matches=[candidate for candidate,digest in pins[1].items() if digest==value]
            if len(matches)==1:moved.append(dict(before=file,after=matches[0],content_unchanged=True))
            else:missing.append(file)
    require(pins==[hashes(p) for p in paths],'input changed during analysis')
    OUT.mkdir(parents=True)
    result=dict(status='controlled_competition_localized_names_verified',competition_uid=UID,competition_index=139,baseline=str(BASE),fixture=str(FIXTURE),baseline_hashes=pins[0],fixture_hashes=pins[1],si_controls=[dict(path=str(p),hashes=pin) for p,pin in zip(refs,pins[2:])],archive_language_count=len(ids),english_language_id=8,polish_language_id=18,changed_language_ids=changed,languages=languages,native_competition_record_size=68,native_competition_record_before_offset=before_comp[0],native_competition_record_after_offset=after_comp[0],native_competition_record_identical=True,entire_language_archive_matches_two_full_name_edits_to_both_si_controls=True,indexed_zlib_repack_roundtrip_passed=True,all_unedited_language_blocks_equal_si_controls=True,people_counts_and_attribute_tables_identical=True,loans_preserved=6210,history_files_identical=history,lnc_file_relocations=moved,lnc_source_files_missing_in_fixture=missing,si_normalization_beyond_requested_operation=True,all_people_and_server_differences_fully_classified=False,inputs_unchanged=True,native_renamed_database_generated=False,si_acceptance_of_native_output='not_tested',game_behavior='not_tested',empty_translation_fallback='not_tested')
    save(OUT/'report.json',result)
    for item in languages:
        if item['language_id'] in [8,18]:
            i=ids.index(item['language_id'])
            for label,block,record in [('before',blocks[0][i][1],item['before']),('after',blocks[1][i][1],item['after'])]:
                (OUT/('language-'+str(item['language_id'])+'-'+label+'.hex')).write_text(block[record['start']:record['end']].hex(' ')+'\n',encoding='ascii')
    print(json.dumps(dict(status=result['status'],changed_language_ids=changed,full_name=expected_name,all_twenty_blocks_reconstructed=True,native_competition_record_identical=True,inputs_unchanged=True)))
if __name__=='__main__':analyze()

