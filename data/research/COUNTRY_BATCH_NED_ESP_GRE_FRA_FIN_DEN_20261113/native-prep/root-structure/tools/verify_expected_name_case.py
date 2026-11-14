from pathlib import Path
import json,hashlib,struct,sys,importlib.util
sys.dont_write_bytecode=True;O=Path('J:/FM08dev/FmLauncher/data/research/COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep/root-structure/tools');sp=importlib.util.spec_from_file_location('fixed',O/'ApplyX18Structure.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);spec=next(x for x in m.read(O.parent/'club-plan.json')if x['ProjectedClubUID']==1800220021);pf=m.read(Path(spec['ProfileFile']));fi=spec['ProjectedFamilyIndex'];uid=spec['ProjectedClubUID'];ti=spec['ProjectedTeamIndex'];name=spec['Name'];short=pf.get('short_name')or name
fix=m.read(m.R/'CLUB_STADIUM_CREATION_R1_20261108/si-fixtures.json')['native_N1'];tpl=Path(fix['frozen_after_SI']);assert m.pins(tpl)==fix['after_SI_hashes'];a=m.load(tpl,'server_db.dat');c=m.load(tpl,'client_db.dat');te=m.unique(a,struct.pack('<iI',23394,1800001004))+8;ce=m.unique(c,struct.pack('<iI',23394,1800001004))+8;bb=m.identity(a[te-216:te],fi,uid);bc=m.identity(c[ce-43:ce],fi,uid)
for q in [bb,bc]:struct.pack_into('<i',q,1,spec['NativeCountryIndex']);struct.pack_into('<H',q,17,int(spec.get('YearFounded') or 0))
bb[52]=0;assert bb[47]==0;struct.pack_into('<i',bb,183,ti);nb,nc=m._fill_new_embedded(bb,bc,fi,uid,name,short);generic=None
try:m._members(nb,0,len(nb),fi,uid);raise RuntimeError('expected two-candidate negative case not reproduced')
except AssertionError as e:generic=e.args[0];assert generic[-1]==2,generic
v=m._members(nb,0,len(nb),fi,uid,name,short);assert v['Members']==[ti]
try:m._members(nb,0,len(nb),fi,uid,name+' wrong',short);raise RuntimeError('wrong expected name not rejected')
except AssertionError:pass
# Actual named family also retains unambiguous selection after two appends.
t1=65000;t2=65001;nb=m._append_new_family(nb,fi,uid,[ti],t1,name,short);nb=m._append_new_family(nb,fi,uid,[ti,t1],t2,name,short);assert m._members(nb,0,len(nb),fi,uid,name,short)['Members']==[ti,t1,t2]
p=dict(Status='PASS_ACTUAL_1800220021_TWO_CANDIDATE_REGRESSION',UID=uid,FamilyIndex=fi,TeamIndex=ti,Full=name,Short=short,UnconstrainedCandidateCount=generic[-1],ExpectedNamesMatchCount=1,WrongExpectedNamesRejected=True,TwoAppendsWithSameConstructorNamesPASS=True,SourceFixturePinsVerified=True,WriterSHA256=hashlib.sha256((O/'ApplyX18Structure.py').read_bytes()).hexdigest(),DatabaseWritten=False,MainExecuted=False)
(O/'expected-name-regression.json').write_text(json.dumps(p,ensure_ascii=True,indent=2)+'\n',encoding='utf-8');print('ACTUAL_CID_REGRESSION_PASS',uid,'generic2/exact1/wrong0/twoappends');print('CODE',p['WriterSHA256'])
