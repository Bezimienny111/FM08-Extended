"""Exact root-authorized ALT cleanup; fail closed on tuple or any preservation mismatch."""
from pathlib import Path
import sys,json,hashlib,struct,importlib.util
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev');sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
from create_italy_structure_i1_20261108 import load,languages,lang_sections,find_table,club,city
from audit_poland_v25_common_r1_20261108 import Cursor
EXPECTED_SHA='d470f84f6ffce2f0329572aea332eadd836d50f0507423eaa1278e8685fb083a'
EXPECTED=dict(UID=1039388,Slot='Alternate',BeforeUID=5624449,AfterUID=None,SourceCountry=None,TargetCountry=None)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def authorized(item,witness):
 return witness.get('PreservationPASS') is True and witness.get('DecisionSHA256')==EXPECTED_SHA and all(item.get(k)==v for k,v in EXPECTED.items())
def one_profile(folder,export):
 a=load(folder,'server_db.dat');c=load(folder,'client_db.dat');en,_=lang_sections(dict(languages((folder/'lang_db.dat').read_bytes()))[8]);cl,_,_=find_table(c,[v['uid'] for v in en['club']],club);rows=read(export)['records'];r=next(x for x in rows if x['ClubUID']==1039388);assert r['TeamIndex']==9693 and struct.unpack_from('<iI',a,r['Footer'])==(9693,1039388)
 f=next(x for x in cl if x['uid']==1039388);assert f['index']==9470 and f['country_index']==-1;assert f['embedded_full_name']=='Yanjing Beer'
 _,_,co=find_table(a,[v['uid'] for v in en['city']],city);beg=co+4;end=min(x['Start'] for x in rows);span=a[beg:end]
 # Existing pinned typed prefix+forward fields+exact suffix parser, no new disk format.
 modp=folder.parents[1]/'family-region-review/read_family_regions.py'
 if not modp.exists():modp=ROOT/'FmLauncher/data/research/COUNTRY_BATCH_IDN_IND_HKG_20261112/family-region-review/read_family_regions.py'
 sp=importlib.util.spec_from_file_location('regions_scoped',modp);mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod);proof=mod.inspect(a,c,f,cl,beg,span)
 team=a[r['Start']:r['Footer']+8];family=a[proof['FamilyStart']:proof['FamilyEnd']]
 vals=[struct.unpack_from('<i',team,x)[0] for x in [7,15,47]];tail=next(x for x in read(ROOT/'FmLauncher/data/research/COUNTRY_BATCH_IDN_IND_HKG_20261112/native-world-identities.json') if x['ClubUID']==1039388)
 assert tail['NativeTeamKind']==0 and tail['TeamTailFamilyIndex']==9470 and tail['TeamCountry']==-1
 return dict(TEAM=team,FAMILY=family,Fields=vals,Names=[f['embedded_full_name'],f['embedded_short_name']],FamilyProof=proof,TEAMStart=r['Start'],TEAMFooter=r['Footer'])
def verify_and_test(b,w,report):
 decisionp=b/'root-review/YANJING_ALT_CLEANUP_DECISION.json';assert sha(decisionp)==EXPECTED_SHA;d=read(decisionp);assert d['status']=='ROOT_REVIEWED_EXACT_FIELD_CLEANUP' and d['club_uid']==1039388 and d['team_index']==9693 and d['family_index']==9470
 assert d['allowed_change']==dict(slot='Alternate',from_competition_uid=5624449,to_competition_uid=None,source_country=None,target_country=None)
 for p,h in d['evidence_pins'].items():assert sha(ROOT/p)==h
 source=Path(report['source']);target=Path(report['output']);snap={str(folder/name):sha(folder/name) for folder in [source,target] for name in ['server_db.dat','client_db.dat','lang_db.dat','people_db.dat']}
 a=one_profile(source,b/'native-structure.json');z=one_profile(target,w/'native-structure-after.json');assert a['Fields']==[-1,636,-1] and z['Fields']==[-1,-1,-1]
 assert a['TEAM'][:15]==z['TEAM'][:15] and a['TEAM'][19:]==z['TEAM'][19:] and len(a['TEAM'])==len(z['TEAM'])
 assert a['FAMILY']==z['FAMILY'] and a['Names']==z['Names'];assert sha(source/'people_db.dat')==sha(target/'people_db.dat')
 assert snap=={p:sha(Path(p)) for p in snap}
 witness=dict(PreservationPASS=True,DecisionPath=str(decisionp),DecisionSHA256=EXPECTED_SHA,AllowedTuple=EXPECTED,TEAMFieldsBefore=a['Fields'],TEAMFieldsAfter=z['Fields'],OnlyTEAMChangedByteSpan=dict(RecordRelativeOffset=15,Length=4),OtherTEAMBytesUnchanged=True,FamilyBytesUnchanged=True,NamesUnchanged=True,PeopleDBUnchanged=True,SourceTEAMSHA256=hashlib.sha256(a['TEAM']).hexdigest(),TargetTEAMSHA256=hashlib.sha256(z['TEAM']).hexdigest(),FAMILY_SHA256=hashlib.sha256(a['FAMILY']).hexdigest(),SourceFamilyProof=a['FamilyProof'],TargetFamilyProof=z['FamilyProof'],InputPins=snap,HelperSHA256=sha(Path(__file__)))
 assert authorized(EXPECTED,witness)
 cases=[]
 for name,changes in [('wrong_UID',dict(UID=1039389)),('wrong_slot',dict(Slot='Current')),('wrong_before',dict(BeforeUID=5624450)),('wrong_after',dict(AfterUID=1301432)),('wrong_source_country',dict(SourceCountry=56)),('wrong_target_country',dict(TargetCountry=56)),('both_known_country',dict(SourceCountry=56,TargetCountry=56)),('other_unknown_UID',dict(UID=1408))]:
  item={**EXPECTED,**changes};assert not authorized(item,witness);cases.append(dict(Name=name,Rejected=True,Tuple=item))
 for name,change in [('preservation_failed',dict(PreservationPASS=False)),('wrong_decision_pin',dict(DecisionSHA256='0'*64))]:
  assert not authorized(EXPECTED,{**witness,**change});cases.append(dict(Name=name,Rejected=True))
 witness['NegativeCases']=cases
 return witness
