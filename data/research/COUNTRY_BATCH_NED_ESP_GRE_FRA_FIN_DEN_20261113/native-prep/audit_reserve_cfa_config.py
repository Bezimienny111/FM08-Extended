from pathlib import Path
from collections import Counter
import json,sys,struct,csv,hashlib,importlib.util
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8');ROOT=Path('J:/FM08dev');B=ROOT/'FmLauncher/data/research/COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep';O=B/'reserve-cfa-config-review';O.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'));from create_club_stadium_native_n1_20261108 import load
rd=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
W=B/'root-structure';src=B/'input/X17-after-SI';dest=W/'structure-db';report=rd(W/'structure-report.json');assert all(sha(dest/k)==v.lower()for k,v in report['output_hashes'].items())
a=load(dest,'server_db.dat');old=load(src,'server_db.dat');r=rd(W/'native-structure-after.json')['records'];rb={x['ClubUID']:x for x in r};oldr=rd(B/'native-structure.json')['records'];oldrb={x['ClubUID']:x for x in oldr};world=rd(B/'native-world-identities.json');wb={x['ClubUID']:x for x in world};cm=rows(W/'club-map.csv');cmby={int(x['ClubUID']):x for x in cm};tm={x['TMID']:x for x in cm};plan={str(x['TMID']):x for x in rd(W/'club-plan.json')};overlay={x['ProjectedClubUID']:x for x in rd(W/'tools/reserve-kind-overlay.json')['Rows']};add={x['uid']:x for x in report['additions']};cfg=rd(W/'structure-config.json');top={q['index']:q['uid']for q in cfg['requirements']if q['uid']in[16,17,18,145438]};kind={};country={};parent={};names={};tails=[]
sp=importlib.util.spec_from_file_location('common_native_x18',W/'tools/ApplyX18Structure.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
for u,x in wb.items():kind[u]=x['NativeTeamKind'];country[u]=x['TeamCountry'];parent[u]=x['ParentUID'];names[u]=x['Names'][0]if x['Names']else''
for u,x in add.items():
 c=cmby[u];kind[u]=overlay[u]['RequiredNativeReserveKind']if u in overlay else 0;country[u]=int(c['CountryIndex']);parent[u]=int(c['ParentUID'])if c['ParentUID']else None;names[u]=c['ClubName']
for u,x in cmby.items():country[u]=int(x['CountryIndex']);names[u]=x['ClubName']
def record(u):
 z=rb[u];p=parent.get(u);po=rb.get(p);return dict(UID=u,Name=names.get(u),TMID=cmby.get(u,{}).get('TMID'),TEAMIndex=z['TeamIndex'],Kind=kind[u],Country=country.get(u),CurrentIndex=struct.unpack_from('<i',a,z['Start']+7)[0],RegionalIndex=struct.unpack_from('<i',a,z['Start']+47)[0],ParentUID=p,ParentCurrentIndex=po['CurrentDivisionIndex']if po else None,ParentTopCOMP=top.get(po['CurrentDivisionIndex'])if po else None)
direct=[record(x['ClubUID'])for x in r if x['CurrentDivisionIndex']==265];regional=[record(x['ClubUID'])for x in r if struct.unpack_from('<i',a,x['Start']+47)[0]==265 and x['CurrentDivisionIndex']!=265]
for u,x in overlay.items():
 fi,pos,k=m._typed_tail(a,rb[u],24026);header=a[pos-4:pos];assert k==x['RequiredNativeReserveKind'];tails.append(dict(UID=u,TMID=x['TMID'],Country=country[u],Kind=k,HeaderHex=header.hex(),FamilyIndex=fi,ReferenceOffset=pos,ParentUID=parent[u],NativeLoaderCodec='C7D4A0 reads4headerbytes +int32FAMILY+2string/byte+footer'))
stock=[]
for u in [1668,856118,519703,519715]:
 z=oldrb[u];fi,pos,k=m._typed_tail(old,z,23916);stock.append(dict(UID=u,Name=names[u],Kind=k,Country=country[u],HeaderHex=old[pos-4:pos].hex(),FamilyIndex=fi))
frenchnew=[x for x in tails if x['Country']==143]
dump('physical-cfa-and-regional.json',dict(Status='READ_ONLY_PHYSICAL_CLASSIFICATION_NOT_RUNTIME_CANDIDATE_REPLAY',SourceFrenchKinds=dict(Counter(x['NativeTeamKind']for x in world if x['TeamCountry']==143)),TargetDirectCFA53=direct,TargetRegionalOnly19=regional,DirectKinds=dict(Counter(x['Kind']for x in direct)),RegionalParentLevels=dict(Counter(str(x['ParentTopCOMP'])for x in regional)),FrenchNewReserveKinds=dict(Counter(x['Kind']for x in frenchnew)),FrenchNewReserves=frenchnew,StockTailWitnesses=stock,New55TailHeaders=tails))
fp=next(x for x in rd(B.parent/'competition-prep/source-cascade-plan.json')['Plans']if x['Country']=='France');pool=next(x['OrderedCandidatePool']for x in fp['CascadeSteps']if x['Name']=='provisional_CFA_minimum_fill10_from_current_fifth');eligible=[];rejected=[]
for x in pool:
 t=x['TMID'];c=tm.get(t);p=plan.get(t)
 if not c or not p:rejected.append(dict(TMID=t,Reason='not_in_closed602_map'));continue
 u=int(c['ClubUID']);z=record(u);why=None
 if kind[u]!=0 or parent.get(u)or p.get('ParentTMID')or p.get('ReserveTeam'):why='linked_reserve_not_firstTEAM'
 elif z['CurrentIndex']==265:why='already_direct_CFA'
 elif z['CurrentIndex']in top and z['CurrentIndex']!=265:why='already_higher_classic_tier'
 if why:rejected.append(dict(TMID=t,UID=u,Name=x['Name'],Reason=why));continue
 eligible.append(dict(SourceRankOrder=x['CandidateOrder'],TMID=t,UID=u,Name=x['Name'],CurrentIndex=z['CurrentIndex'],Kind=kind[u],ParentUID=parent.get(u),PreviousFacts=x['PreviousFacts'],SourceCompetition=x['SourceCompetition']))
dump('ranked-first-team-feeders.json',dict(Status='SAVED_PREVIOUS_TABLE_ORDER_FILTERED_TYPED_KIND0_NO_PARENT',OrderedEligible=eligible,First6=eligible[:6],Rejected=rejected,Need='At least6 if runtime67 remains; X19 count must prove n>=73 in EB8DE0, not only selector min53. No native change proposed until runtimeUIDset matched.'))
files={str(p):sha(p)for p in [src/'server_db.dat',dest/'server_db.dat',W/'native-structure-after.json',B/'native-world-identities.json',W/'club-plan.json',B.parent/'competition-prep/source-cascade-plan.json',Path(__file__)]};dump('manifest.json',dict(Status='READ_ONLY_BOUNDED_FINDINGS',SourcePins=files,DBWrite=False,NativeRuntimeCause='root/graphics liveproof EB8DE0 FRE_CFA runtimecandidate67 vs18x4 prune requiresn>=73',NoMutation=True));print('DIRECT',len(direct),'REGIONAL',len(regional),'directkinds',dict(Counter(x['Kind']for x in direct)),'NEWFRB',dict(Counter(x['Kind']for x in frenchnew)),'FIRST6',[(x['TMID'],x['UID'],x['Name'])for x in eligible[:6]],flush=True)

