"""Compare a one-control Buffon SI loan variant with TEST_LOAN and official 8.0.2."""
import argparse,json,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
from analyze_buffon_loan_20261106 import BASE,ROOT,require,hashes,sha,load,loan_rows,decode,controlled_player_span,name_evidence,club_evidence,integer
CASES={'recall':dict(folder='TEST_LOAN_RECALL',offset=17,before=0,after=4), 'number':dict(folder='TEST_LOAN_NUMBER',offset=18,before=255,after=31), 'wages':dict(folder='TEST_LOAN_WAGES',offset=23,before=50,after=75), 'fee':dict(folder='TEST_LOAN_FEE',offset=19,width=4,before=5000000,after=7000000), 'fee_off':dict(folder='TEST_LOAN_FEE_OFF',offset=19,width=4,before=5000000,after=-1), 'wages_zero':dict(folder='TEST_LOAN_WAGES_ZERO',offset=23,before=50,after=0)}
def compare(variant,output):
    require(not output.exists(),'variant report already exists')
    case=CASES[variant];before=ROOT/'Dane/db/TEST_LOAN';after=ROOT/'Dane/db'/case['folder'];dirs=[BASE,before,after]
    pins=[hashes(p) for p in dirs];policy=json.loads((ROOT/'FmLauncher/data/research/LOAN_RESEARCH_POLICY.json').read_text(encoding='utf-8-sig'))
    first_path=ROOT/'FmLauncher/data/research/LOANS_20261106_BUFFON/report.json';first=json.loads(first_path.read_text(encoding='utf-8-sig'))
    require(pins[0]==policy['baseline_hashes'],'official baseline changed');require(pins[1]==first['fixture_hashes'],'reference TEST_LOAN changed')
    servers=[load(p,'server_db.dat') for p in dirs];people=[load(p,'people_db.dat') for p in dirs]
    require(people[0][:16]==people[1][:16]==people[2][:16],'native counts changed')
    tables=[loan_rows(s,140364) for s in servers];headers=[x[0] for x in tables];rows=[x[1] for x in tables]
    require([len(rs) for rs in rows]==[6210,6211,6211] and rows[0]==rows[1][:-1]==rows[2][:-1],'original loans changed')
    a,b=rows[1][-1],rows[2][-1];changes=[dict(offset=i,before=x,after=y) for i,(x,y) in enumerate(zip(a,b)) if x!=y]
    width=case.get('width',1);offset=case['offset'];fmt='<i' if width==4 else '<B'
    old_field=struct.pack(fmt,case['before']);new_field=struct.pack(fmt,case['after'])
    require(a[offset:offset+width]==old_field and b[offset:offset+width]==new_field,'controlled field values differ')
    expected_changes=[dict(offset=offset+i,before=x,after=y) for i,(x,y) in enumerate(zip(old_field,new_field)) if x!=y]
    require(changes==expected_changes,'more than the controlled loan field changed')
    expected=bytearray(struct.pack('<i',6211)+b''.join(rows[1]));start=4+6210*32+offset;expected[start:start+width]=new_field
    require(expected==servers[2][headers[2]:headers[2]+len(expected)],'complete loan table differs from controlled field edit')
    records=[p[s:e] for p in people for s,e in [controlled_player_span(p,11133)]]
    require(all(len(r)==472 and integer(r,0)==3474 and integer(r,242)==995 for r in records),'Buffon identity/owner changed')
    names=[name_evidence(s,'Gianluigi',integer(r,196)) for s,r in zip(servers,records)];require(len({n['uid'] for n in names})==1,'Buffon name identity changed')
    person_changes=[dict(offset=i,before=x,after=y) for i,(x,y) in enumerate(zip(records[1],records[2])) if x!=y]
    require(all(196<=c['offset']<200 for c in person_changes),'additional Buffon PERSON changes')
    require(records[0][270:]==records[1][270:]==records[2][270:],'main contract/tail changed')
    main_numbers=[r[330] for r in records];require(main_numbers==[1,1,1],'main contract shirt number changed')
    clubs=[]
    for club in [992,995]:
        evidence=[club_evidence(s,club,integer(p,0)) for s,p in zip(servers,people)]
        require(evidence[0][1]==evidence[1][1]==evidence[2][1],'club roster/record changed')
        clubs.append(dict(club_index=club,all_records_identical=True,snapshots=[e[0] for e in evidence]))
    for name in ['non_pl_hist_dt.dat','non_pl_hist_id.dat','non_pl_hist_index.dat','pl_hist_dt.dat','pl_hist_id.dat','pl_hist_index.dat']:require(pins[0][name]==pins[1][name]==pins[2][name],'history changed')
    require(pins==[hashes(p) for p in dirs],'input changed during analysis')
    result=dict(status='controlled_loan_'+variant+'_verified',variant=variant,baseline=str(BASE),reference=str(before),fixture=str(after),baseline_hashes=pins[0],reference_hashes=pins[1],fixture_hashes=pins[2],loan_before=decode(a),loan_after=decode(b),loan_byte_changes=changes,whole_table_matches_single_byte_edit=(len(changes)==1),whole_table_matches_controlled_field_edit=True,controlled_field_width=width,prior_loans_preserved=6210,person_changes=person_changes,names=names,main_contract_identical=True,main_contract_shirt_numbers=main_numbers,main_contract_wages_native=[integer(record,305) for record in records],clubs=clubs,inputs_unchanged=True,game_behavior='not_tested',native_generated_fixture_SI_acceptance='not_tested')
    output.mkdir(parents=True);(output/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for name,row in [('loan-before.hex',a),('loan-after.hex',b)]:(output/name).write_text(row.hex(' ')+'\n',encoding='ascii')
    print(json.dumps(dict(status=result['status'],record_byte=case['offset'],before=case['before'],after=case['after'],main_contract_shirt_number=1,prior_loans_preserved=6210,inputs_unchanged=True)),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--variant',choices=CASES,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();compare(a.variant,a.output)
