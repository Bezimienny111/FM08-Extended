"""Read-only controlled analysis of Ranieri's removal from Juventus in SI."""
import json,shutil,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
from analyze_buffon_loan_20261106 import ROOT,BASE,load,hashes,sha,integer,require,name_evidence,club_evidence,loan_rows
from compare_native_player_tests import occurrences,native_person_table_end
REPO=ROOT/'FM08-Database-Tools';FIXTURE=ROOT/'Dane/db/Test_staff_noclub';WAGE=ROOT/'Dane/db/TEST_STAFF_WAGE'
OUT=ROOT/'FmLauncher/data/research/STAFF_20261106_RANIERI_NOCLUB'
UID=4201569;INDEX=129460

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def person_span(data):
    end=native_person_table_end(data);hits=[]
    for at in occurrences(data[:end],struct.pack('<i',UID)):
        if at>=4 and integer(data,at-4)==INDEX:
            start=data.rfind(struct.pack('<iB',INDEX,1),max(16,at-4096),at-4)
            if start>=16 and at+4-start in [207,272]:hits.append((start,at+4))
    require(len(hits)==1,'missing or ambiguous staff PERSON');return hits[0]
def staff_table(server):
    found=[]
    for at in occurrences(server,struct.pack('<Bi',0,INDEX)):
        if at+17>len(server):continue
        ordinal=integer(server,at+9);header=at-17*ordinal-4
        if ordinal<0 or header<0:continue
        count=integer(server,header)
        if not 0<=ordinal<count<=334475 or header+4+17*count>len(server):continue
        if all(server[header+4+i*17]==0 and integer(server,header+4+i*17+9)==i and integer(server,header+4+i*17+13)==-1 for i in range(count)):
            found.append((header,count,ordinal,at))
    require(len(found)==1,'missing or ambiguous staff relation table');return found[0]
def compare():
    require(not OUT.exists(),'research output already exists')
    paths=[BASE,WAGE,FIXTURE];pins=[hashes(p) for p in paths]
    previous=read(ROOT/'FmLauncher/data/research/STAFF_20261106_RANIERI/independent.json')
    require(pins[0]==previous['baseline_hashes'] and pins[1]==previous['fixture_hashes'],'original baseline or wage fixture changed')
    people=[load(p,'people_db.dat') for p in paths];servers=[load(p,'server_db.dat') for p in paths];spans=[person_span(p) for p in people];rows=[p[a:b] for p,(a,b) in zip(people,spans)]
    require([len(r) for r in rows]==[272,272,207],'unexpected staff record lengths')
    require(people[0][:16]==people[1][:16]==people[2][:16],'native entity counts changed')
    require([integer(r,75) for r in rows]==[995,995,-1],'unexpected club relation')
    require([r[79] for r in rows]==[16]*3 and [r[102] for r in rows]==[1,1,0],'role/count differ')
    require(struct.unpack_from('<HH',rows[2],80)==(0,1900),'cleared club date sentinel differs')
    names=[]
    for word,offset in [('Claudio',29),('Ranieri',33)]:
        evidence=[name_evidence(s,word,integer(r,offset)) for s,r in zip(servers,rows)]
        require(len({e['uid'] for e in evidence})==1,'name identity changed');names.append(dict(name=word,snapshots=evidence))
    for before in rows[:2]:
        expected=bytearray(before[:103]+before[168:]);expected[29:37]=rows[2][29:37]
        struct.pack_into('<i',expected,75,-1);struct.pack_into('<HH',expected,80,0,1900);expected[102]=0
        require(expected==rows[2],'unexplained change inside Ranieri PERSON')
    clubs=[club_evidence(s,995,integer(p,0)) for s,p in zip(servers,people)]
    require(clubs[0][1]==clubs[1][1],'club differs between original and wage fixture')
    expected_club=bytearray(clubs[0][1]);require(integer(expected_club,23)==INDEX,'manager slot does not point at Ranieri')
    struct.pack_into('<i',expected_club,23,-1);require(expected_club==clubs[2][1],'club changes beyond manager slot')
    memberships=[]
    for server,(meta,_) in zip(servers,clubs):
        pos=meta['start']+63+server[meta['start']+62]*4;count=struct.unpack_from('<H',server,pos)[0]
        members=[integer(server,pos+2+4*i) for i in range(count)];memberships.append(members)
    require(memberships[0]==memberships[1]==memberships[2] and INDEX not in memberships[0],'unexpected roster membership')
    header,count,ordinal,at=staff_table(servers[1]);base_h,base_count,base_ordinal,base_at=staff_table(servers[0])
    require((count,ordinal)==(8777,4501) and (base_count,base_ordinal)==(count,ordinal),'unexpected relation table identity')
    table=servers[1][header:header+4+17*count]
    require(servers[0][base_h:base_h+4+17*count]==table,'relation table changed in wage case')
    expected_table=bytearray(table[:4+ordinal*17]+table[4+(ordinal+1)*17:]);struct.pack_into('<i',expected_table,0,count-1)
    for index in range(ordinal,count-1):struct.pack_into('<i',expected_table,4+index*17+9,index)
    require(servers[2][header:header+len(expected_table)]==expected_table,'other relation table data changed')
    require(integer(servers[2],header)==8776,'incorrect relation count after removal')
    loans=[loan_rows(s,140364)[1] for s in servers];require(loans[0]==loans[1]==loans[2] and len(loans[0])==6210,'loans changed')
    history=['non_pl_hist_dt.dat','non_pl_hist_id.dat','non_pl_hist_index.dat','pl_hist_dt.dat','pl_hist_id.dat','pl_hist_index.dat']
    for name in history:require(pins[0][name]==pins[1][name]==pins[2][name],'history changed: '+name)
    suffixes=[p[native_person_table_end(p):] for p in people]
    tails_same=suffixes[0]==suffixes[1]==suffixes[2]
    require(tails_same,'non-PERSON people tables changed')
    # Quantify residual SI differences instead of calling all bytes outside the operation unchanged.
    expected_people=bytearray(people[1][:spans[1][0]+103]+people[1][spans[1][0]+168:])
    expected_people[spans[1][0]:spans[1][0]+207]=rows[2]
    expected_server=bytearray(servers[1][:at]+servers[1][at+17:]);expected_server[header:header+len(expected_table)]=expected_table
    struct.pack_into('<i',expected_server,clubs[1][0]['start']+23,-1)
    residual={}
    for filename,expected,current in [('people_db.dat',expected_people,people[2]),('server_db.dat',expected_server,servers[2]),('client_db.dat',load(WAGE,'client_db.dat'),load(FIXTURE,'client_db.dat'))]:
        require(len(expected)==len(current),'unexplained decompressed length change: '+filename)
        residual[filename]=sum(x!=y for x,y in zip(expected,current))
    require(pins==[hashes(p) for p in paths],'input changed during comparison')
    OUT.mkdir(parents=True)
    report=dict(status='controlled_staff_club_removal_verified',baseline=str(BASE),wage_reference=str(WAGE),fixture=str(FIXTURE),baseline_hashes=pins[0],wage_reference_hashes=pins[1],fixture_hashes=pins[2],person_uid=UID,person_index=INDEX,person_type=1,person_lengths=[len(r) for r in rows],club_before=995,club_after=-1,club_date_after='1900-01-01',raw_role_before_after=16,contract_count_before=1,contract_count_after=0,removed_contract_bytes=65,person_reconstructed_exactly_after_name_resolution=True,manager_pointer_club_relative_offset=23,manager_pointer_before=INDEX,manager_pointer_after=-1,club_record_reconstructed_exactly=True,juventus_roster_count=len(memberships[0]),ranieri_present_in_player_roster_before=False,player_roster_unchanged=True,relation_table=dict(header=header,count_before=count,count_after=count-1,record_size=17,removed_row_index=ordinal,removed_row_hex=servers[1][at:at+17].hex(' '),index_field_offset=9,complete_table_matches_removal_and_renumbering=True,other_two_short_fields_meaning='not_confirmed'),names=names,loans_preserved=6210,all_nonperson_people_tables_identical=True,history_files_identical=history,residual_si_different_bytes_outside_reconstructed_operation=residual,residual_differences_fully_classified=False,inputs_unchanged=True,native_release_implementation='not_implemented',current_staff_reader_free_staff='unsupported',game_behavior='not_tested')
    save(OUT/'report.json',report)
    for label,row in zip(['original-802','wage-reference','no-club'],rows):(OUT/(label+'.hex')).write_text(row.hex(' ')+'\n',encoding='ascii')
    print(json.dumps({k:report[k] for k in ['status','person_lengths','club_after','removed_contract_bytes','juventus_roster_count','loans_preserved','all_nonperson_people_tables_identical','inputs_unchanged']}))
    return report
if __name__=='__main__':compare()
