"""Verify the single Can Be Recalled change in the user's controlled SI fixture."""
import argparse,json,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
from analyze_buffon_loan_20261106 import BASE,ROOT,require,hashes,sha,load,loan_rows,decode,controlled_player_span,name_evidence,club_evidence,integer

def compare(output):
    require(not output.exists(),'recall report directory already exists')
    policy=json.loads((ROOT/'FmLauncher/data/research/LOAN_RESEARCH_POLICY.json').read_text(encoding='utf-8-sig'))
    before=ROOT/'Dane/db/TEST_LOAN';after=ROOT/'Dane/db/TEST_LOAN_RECALL';dirs=[BASE,before,after];pins=[hashes(p) for p in dirs]
    require(pins[0]==policy['baseline_hashes'],'official 8.0.2 changed')
    initial=ROOT/'FmLauncher/data/research/LOANS_20261106_BUFFON/report.json';first=json.loads(initial.read_text(encoding='utf-8-sig'))
    require(pins[1]==first['fixture_hashes'],'original TEST_LOAN changed')
    servers=[load(p,'server_db.dat') for p in dirs];people=[load(p,'people_db.dat') for p in dirs]
    tables=[loan_rows(s,140364) for s in servers];rows=[x[1] for x in tables];headers=[x[0] for x in tables]
    require([len(x) for x in rows]==[6210,6211,6211],'unexpected loan counts')
    require(rows[0]==rows[1][:-1]==rows[2][:-1],'pre-existing loan rows changed')
    old,new=rows[1][-1],rows[2][-1];changes=[dict(offset=i,before=a,after=b) for i,(a,b) in enumerate(zip(old,new)) if a!=b]
    require(changes==[dict(offset=17,before=0,after=4)],'recall is not the only changed loan byte')
    require(integer(old,1)==integer(new,1)==3474 and integer(old,5)==integer(new,5)==992,'wrong player or club')
    expected=bytearray(struct.pack('<i',6211)+b''.join(rows[1]));expected[4+6210*32+17]|=0x04
    require(expected==servers[2][headers[2]:headers[2]+len(expected)],'bit-only table edit differs from SI')
    records=[p[a:b] for p in people for a,b in [controlled_player_span(p,11133)]]
    require(all(len(r)==472 and integer(r,242)==995 for r in records),'Buffon identity/owner differs')
    names=[name_evidence(s,'Gianluigi',integer(r,196)) for s,r in zip(servers,records)]
    require(len({n['uid'] for n in names})==1,'Buffon name identity changed')
    person_changes=[dict(offset=i,before=a,after=b) for i,(a,b) in enumerate(zip(records[1],records[2])) if a!=b]
    require(all(196<=e['offset']<200 for e in person_changes),'additional Buffon PERSON changes')
    require(records[0][270:]==records[1][270:]==records[2][270:],'main contract/tail changed')
    clubs=[]
    for club in [992,995]:
        evidence=[club_evidence(s,club,integer(p,0)) for s,p in zip(servers,people)]
        require(evidence[0][1]==evidence[1][1]==evidence[2][1],'club record changed')
        clubs.append(dict(club_index=club,all_three_records_identical=True,snapshots=[e[0] for e in evidence]))
    protected_histories=['non_pl_hist_dt.dat','non_pl_hist_id.dat','non_pl_hist_index.dat','pl_hist_dt.dat','pl_hist_id.dat','pl_hist_index.dat']
    for name in protected_histories:require(pins[0][name]==pins[1][name]==pins[2][name],'history file changed')
    require(pins==[hashes(p) for p in dirs],'input changed during comparison')
    report=dict(status='controlled_recall_flag_verified',baseline=str(BASE),no_recall_fixture=str(before),recall_fixture=str(after),baseline_hashes=pins[0],no_recall_hashes=pins[1],recall_hashes=pins[2],original_case_report_sha256=sha(initial),loan_before=decode(old),loan_after=decode(new),loan_byte_changes=changes,options_byte_offset=17,recall_bit_hex='0x04',can_be_recalled_before=False,can_be_recalled_after=True,all_6210_original_loans_unchanged=True,whole_loan_table_matches_single_bit_edit=True,person_byte_changes=person_changes,first_names=names,main_contract_and_tail_identical=True,clubs=clubs,input_directories_unchanged=True,new_career_behavior='not_tested',native_generated_database_SI_acceptance='not_tested')
    output.mkdir(parents=True);(output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (output/'loan-before.hex').write_text(old.hex(' ')+'\n',encoding='ascii');(output/'loan-after.hex').write_text(new.hex(' ')+'\n',encoding='ascii')
    print(json.dumps(dict(status=report['status'],record_byte=17,bit='0x04',before=0,after=4,unchanged_prior_loans=6210,contracts_and_clubs_unchanged=True,input_directories_unchanged=True,output=str(output)),ensure_ascii=False),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();compare(args.output)
