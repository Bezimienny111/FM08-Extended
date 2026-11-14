"""Read-only analysis of the SI Buffon loan fixture against the official 8.0.2 database."""
import argparse,collections,hashlib,json,struct,sys,xml.etree.ElementTree as ET,zlib
from datetime import date,timedelta
from pathlib import Path
sys.dont_write_bytecode=True
from compare_native_player_tests import controlled_player_span,controlled_loan_table,controlled_club_span,occurrences
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'data/updates/update-802/db/802'
TEST=ROOT/'Dane/db/TEST_LOAN'
def require(value,message):
    if not value:raise ValueError(message)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def hashes(p):return {str(f.relative_to(p)):sha(f) for f in p.rglob('*') if f.is_file()}
def load(p,n):
    raw=(p/n).read_bytes();require(len(raw)>15,'truncated DAT')
    d=zlib.decompressobj();result=d.decompress(raw[9:])+d.flush()
    require(d.eof and not d.unused_data and not d.unconsumed_tail,'invalid compressed DAT '+n);return result
def integer(b,p):return struct.unpack_from('<i',b,p)[0]
def native_date(b,p):
    day,year=struct.unpack_from('<HH',b,p);value=date(year,1,1)+timedelta(days=day)
    require(value.year==year,'date overflow');return value.isoformat()
def loan_rows(s,person):
    header,count=controlled_loan_table(s,person)
    return header,[s[header+4+j*32:header+4+(j+1)*32] for j in range(count)]
def decode(row):
    require(len(row)==32 and row[0]==0,'unsupported loan row')
    return dict(record_flag=row[0],person_index=integer(row,1),loan_club_index=integer(row,5),start_date=native_date(row,9),end_date=native_date(row,13),raw_options_byte_17=row[17],raw_squad_number_byte_18=row[18],raw_fee_to_buy=integer(row,19),raw_wage_contribution_byte_23=row[23],record_index=integer(row,24),uid=integer(row,28),hex=row.hex(' '))
def name_evidence(server,name,index):
    needle=struct.pack('<Bi',0,len(name))+name.encode('utf-16-le');found=[]
    for p in occurrences(server,needle):
        footer=p+14+len(name)*2
        if integer(server,footer)==index:found.append(dict(index=index,uid=integer(server,footer+4),name=name,offset=p))
    require(len(found)==1,'name reference not independently resolved');return found[0]
def club_evidence(server,club,person_count):
    a,b=controlled_club_span(server,club,person_count);r=a+63+server[a+62]*4;n=struct.unpack_from('<H',server,r)[0]
    members=[integer(server,r+2+j*4) for j in range(n)]
    return dict(club_index=club,club_uid=integer(server,b-4),start=a,end=b,roster_count=n,buffon_in_roster=3474 in members),server[a:b]
def analyze(output):
    require(not output.exists(),'research output exists; choose a new directory')
    require(ET.parse(BASE/'802.xml').getroot().find("string[@id='version']").get('value')=='8.0.2','wrong baseline version')
    pins=[hashes(p) for p in [BASE,TEST]]
    people=[load(p,'people_db.dat') for p in [BASE,TEST]];servers=[load(p,'server_db.dat') for p in [BASE,TEST]];clients=[load(p,'client_db.dat') for p in [BASE,TEST]]
    spans=[controlled_player_span(p,11133) for p in people];records=[p[a:b] for p,(a,b) in zip(people,spans)]
    require([len(r) for r in records]==[472,472] and [integer(r,0) for r in records]==[3474,3474],'Buffon PERSON identity/layout differs')
    require(people[0][:16]==people[1][:16],'native entity counts changed')
    diffs=[dict(offset=j,before=x,after=y) for j,(x,y) in enumerate(zip(*records)) if x!=y]
    require(diffs==[dict(offset=196,before=183,after=185)],'unexpected controlled PERSON difference')
    name_before=name_evidence(servers[0],'Gianluigi',integer(records[0],196));name_after=name_evidence(servers[1],'Gianluigi',integer(records[1],196))
    require(name_before['uid']==name_after['uid'],'first-name identity changed')
    require(integer(records[0],242)==integer(records[1],242)==995,'Buffon no longer owned by Juventus')
    require(records[0][270:]==records[1][270:],'Buffon main contract or tail changed')
    tables=[loan_rows(s,140364) for s in servers];headers=[x[0] for x in tables];loans=[x[1] for x in tables]
    require(len(loans[0])==6210 and len(loans[1])==6211,'unexpected loan counts')
    require(loans[0]==loans[1][:-1],'pre-existing loan records changed')
    added=decode(loans[1][-1]);require(added['person_index']==3474 and added['loan_club_index']==992 and added['record_index']==6210,'wrong added loan subject/index')
    require(added['start_date']=='2007-07-01' and added['end_date']=='2008-06-30','date mismatch')
    require(added['raw_options_byte_17']==0 and added['raw_squad_number_byte_18']==255 and added['raw_fee_to_buy']==5000000 and added['raw_wage_contribution_byte_23']==50,'loan does not match supplied SI screenshot')
    require(added['uid']==1800000090,'fixture loan UID differs')
    clubs=[]
    for club in [992,995]:
        before,raw_before=club_evidence(servers[0],club,integer(people[0],0));after,raw_after=club_evidence(servers[1],club,integer(people[1],0))
        require(raw_before==raw_after,'controlled club record changed')
        clubs.append(dict(before=before,after=after,entire_club_record_identical=True))
    expected_table=struct.pack('<i',6211)+b''.join(loans[0])+loans[1][-1]
    require(expected_table==servers[1][headers[1]:headers[1]+len(expected_table)],'minimal loan table reconstruction differs from SI')
    known_files=['people_db.dat','server_db.dat','client_db.dat'];raw=[people,servers,clients];file_differences={}
    for name,pair in zip(known_files,raw):
        a,b=pair;file_differences[name]=dict(before_size=len(a),after_size=len(b),aligned_different_bytes=sum(x!=y for x,y in zip(a,b)) if len(a)==len(b) else None)
    for name in ['non_pl_hist_dt.dat','non_pl_hist_id.dat','non_pl_hist_index.dat','pl_hist_dt.dat','pl_hist_id.dat','pl_hist_index.dat']:require(pins[0][name]==pins[1][name],'history file changed')
    require(pins==[hashes(p) for p in [BASE,TEST]],'analysis changed or raced with an input file')
    screenshot=dict(person='Gianluigi Buffon',owner='Juventus',loan_club='Inter',start='2007-07-01',end='2008-06-30',can_be_recalled=False,squad_number_enabled=False,fee_to_buy_enabled=True,fee_to_buy=5000000,wages_paid_by_loaning_club_percent=50)
    report=dict(status='controlled_loan_creation_analyzed',baseline=str(BASE),si_fixture=str(TEST),baseline_hashes=pins[0],fixture_hashes=pins[1],screenshot=screenshot,person_uid=11133,person_index=3474,person_spans=spans,person_length=472,person_changed_bytes=diffs,first_name_before=name_before,first_name_after=name_after,owner_club_index=995,owner_relative_offset=242,main_contract_relative_offset=270,main_contract_and_tail_identical=True,loan_table_before=dict(offset=headers[0],count=6210),loan_table_after=dict(offset=headers[1],count=6211),existing_loan_rows_byte_identical=6210,added_loan=added,clubs=clubs,file_differences=file_differences,in_memory_loan_table_reconstruction_matches_SI=True,new_uid_occurrences_in_baseline={n:pair[0].count(struct.pack('<i',added['uid'])) for n,pair in zip(known_files,raw)},inputs_unchanged=True,confidence=dict(dates_person_club_index_uid='verified against native anchors and SI fixture',fee_and_wage_offsets='match supplied screenshot; independent one-field variants still required',options_byte_17='raw value 0; original database has values 0 and 4; recall bit is not yet proven',squad_number_byte_18='raw value 255 with unchecked SI option; numbered variant still required'),not_tested=['native creation writer accepted by SI','recall enabled bit','specified loan shirt number','zero/disabled buy option','alternate wage contribution','new-career return after loan end'])
    output.mkdir(parents=True);(output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (output/'loan-record.hex').write_text(added['hex']+'\n',encoding='ascii')
    print(json.dumps(dict(status=report['status'],baseline=str(BASE),si_fixture=str(TEST),person_uid=11133,loan_uid=added['uid'],loans_before=6210,loans_after=6211,all_prior_loans_identical=True,both_club_records_identical=True,main_contract_unchanged=True,output=str(output)),ensure_ascii=False),flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();analyze(args.output)
