"""Read-only analysis of the SI fixture creating a new unassigned manager."""
import json,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
from analyze_buffon_loan_20261106 import ROOT,BASE,load,hashes,sha,integer,require,name_evidence,loan_rows,club_evidence
from analyze_staff_noclub_20261106 import staff_table
from compare_native_player_tests import occurrences,native_person_table_end
REPO=ROOT/'FM08-Database-Tools';FIXTURE=ROOT/'Dane/db/TEST_STAFF_NEW';OUT=ROOT/'FmLauncher/data/research/STAFF_20261106_NEW_MANAGER'
UID=1394631303

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def layout(p):
    persons,personalities,players,staff=struct.unpack_from('<4i',p);end=native_person_table_end(p)
    personality_start=end+4;player_start=end+8+personalities*17;staff_header=player_start+players*89;staff_start=staff_header+4
    require(integer(p,end)==personalities and integer(p,player_start-4)==players and integer(p,staff_header)==staff,'table count mismatch')
    require(staff_start+staff*49<=len(p),'truncated non-player attribute table')
    require(all(integer(p,staff_start+i*49+41)==i for i in range(staff)),'noncontiguous staff attribute indices')
    return dict(persons=persons,personalities=personalities,players=players,staff=staff,person_end=end,personality_start=personality_start,player_start=player_start,staff_header=staff_header,staff_start=staff_start,staff_end=staff_start+staff*49)
def analyze():
    require(not OUT.exists(),'research output already exists')
    pins=[hashes(p) for p in [BASE,FIXTURE]];policy=read(ROOT/'FmLauncher/data/research/STAFF_RESEARCH_POLICY.json');require(pins[0]==policy['baseline_hashes'],'canonical 802 changed')
    p,q=[load(d,'people_db.dat') for d in [BASE,FIXTURE]];s,t=[load(d,'server_db.dat') for d in [BASE,FIXTURE]];c,d=[load(folder,'client_db.dat') for folder in [BASE,FIXTURE]]
    before,after=layout(p),layout(q)
    require([after[k]-before[k] for k in ['persons','personalities','players','staff']]==[1,1,0,1],'unexpected count changes')
    uid_hits=list(occurrences(q[:after['person_end']],struct.pack('<i',UID)));require(len(uid_hits)==1,'person UID not unique')
    end=uid_hits[0]+4;index=integer(q,end-8);require(index==before['persons'],'unexpected PERSON index')
    starts=list(occurrences(q[max(16,end-4096):end-8],struct.pack('<iB',index,1)));require(len(starts)==1,'new PERSON start ambiguous')
    start=max(16,end-4096)+starts[0];person=q[start:end];require(len(person)==138,'unexpected new staff PERSON size')
    require(integer(person,75)==-1 and person[79]==16 and person[102]==0,'new manager has unexpected club/role/contracts')
    require(struct.unpack_from('<HH',person,80)==(0,1900),'club date sentinel differs')
    require(integer(person,85)==before['personalities'] and integer(person,19)==before['staff'],'incorrect personality/staff references')
    personality=q[after['personality_start']+before['personalities']*17:after['personality_start']+after['personalities']*17]
    staff_attributes=q[after['staff_start']+before['staff']*49:after['staff_end']]
    require(len(personality)==17 and integer(personality,9)==before['personalities'],'incorrect new personality row')
    require(len(staff_attributes)==49 and integer(staff_attributes,41)==before['staff'],'incorrect new staff attribute row')
    require(personality[:9]==bytes(9) and staff_attributes[:41]==bytes(41),'new raw attributes are not defaults')
    require(p[before['personality_start']:before['player_start']-4]==q[after['personality_start']:after['personality_start']+before['personalities']*17],'existing personalities changed')
    require(p[before['player_start']:before['staff_header']]==q[after['player_start']:after['staff_header']],'player attributes changed')
    require(p[before['staff_start']:before['staff_end']]==q[after['staff_start']:after['staff_start']+before['staff']*49],'existing staff attributes changed')
    require(p[before['staff_end']:]==q[after['staff_end']:],'people trailing bytes changed')
    require(after['person_end']-before['person_end']==138 and len(q)-len(p)==204,'unexpected people length changes')
    names=[]
    for word,offset in [('Trener ',29),('Nowy',33)]:
        name_index=integer(person,offset);server_entry=name_evidence(t,word,name_index);client_entry=name_evidence(d,word,name_index)
        require(name_index==0 and server_entry['uid']==client_entry['uid'],'new name differs between server/client')
        names.append(dict(field='first_name' if offset==29 else 'last_name',stored_text=word,server=server_entry,client=client_entry))
    uids=dict(person=UID,personality=integer(personality,13),staff_attributes=integer(staff_attributes,45),first_name=names[0]['server']['uid'],last_name=names[1]['server']['uid'])
    require(len(set(uids.values()))==5,'new record UIDs collide')
    for uid in uids.values():
        require(all(struct.pack('<i',uid) not in buf for buf in [p,s,c]),'new UID already appears in baseline')
    require(integer(person,29)==integer(person,33)==0,'new name references differ')
    require(struct.pack('<i',index) not in t and struct.pack('<i',index) not in d,'new person index referenced in server/client')
    h,n,_,_=staff_table(s);hh,nn,_,_=staff_table(t)
    require(n==nn==8777 and s[h:h+4+n*17]==t[hh:hh+4+nn*17],'club staff relation table changed')
    require(club_evidence(s,995,before['persons'])[1]==club_evidence(t,995,after['persons'])[1],'Juventus record changed')
    loans_before=loan_rows(s,140364)[1];loans_after=loan_rows(t,140364)[1]
    require(loans_before==loans_after and len(loans_before)==6210,'loan table changed')
    history=['non_pl_hist_dt.dat','non_pl_hist_id.dat','non_pl_hist_index.dat','pl_hist_dt.dat','pl_hist_id.dat','pl_hist_index.dat']
    for f in history:require(pins[0][f]==pins[1][f],'history changed: '+f)
    require(pins==[hashes(folder) for folder in [BASE,FIXTURE]],'input changed during analysis')
    report=dict(status='controlled_free_staff_creation_verified',baseline=str(BASE),fixture=str(FIXTURE),baseline_hashes=pins[0],fixture_hashes=pins[1],person_uid=UID,person_index=index,person_type_raw=1,user_reported_role='manager',role_raw=16,club_index=-1,contract_count=0,person_span=[start,end],person_length=138,counts_before={k:before[k] for k in ['persons','personalities','players','staff']},counts_after={k:after[k] for k in ['persons','personalities','players','staff']},new_uids=uids,personality_record_size=17,staff_attribute_record_size=49,person_personality_reference_offset=85,person_staff_attributes_reference_offset=19,personality_index_offset=9,staff_attribute_index_offset=41,new_personality_body_is_zero=True,new_staff_attributes_body_is_zero=True,names=names,first_name_has_trailing_space=True,existing_personalities_identical=True,all_player_attributes_identical=True,existing_staff_attributes_identical=True,people_tail_identical=True,people_size_delta=204,club_staff_relation_table_unchanged=True,club_staff_relation_count=8777,new_person_index_absent_in_server_and_client=True,juventus_record_unchanged=True,loans_preserved=6210,history_files_identical=history,all_unrelated_person_records_compared=False,si_name_table_reordering_not_copied_to_native_writer=True,inputs_unchanged=True,current_staff_reader_free_staff='unsupported',native_staff_creation='not_implemented',game_behavior='not_tested')
    OUT.mkdir(parents=True);save(OUT/'report.json',report)
    for name,row in [('person',person),('personality',personality),('staff-attributes',staff_attributes)]:(OUT/(name+'.hex')).write_text(row.hex(' ')+'\n',encoding='ascii')
    print(json.dumps({k:report[k] for k in ['status','person_uid','person_index','person_length','new_uids','people_size_delta','club_staff_relation_table_unchanged','loans_preserved','inputs_unchanged']}))
    return report
if __name__=='__main__':analyze()
