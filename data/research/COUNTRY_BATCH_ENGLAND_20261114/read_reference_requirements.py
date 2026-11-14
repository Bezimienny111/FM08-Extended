from pathlib import Path
import json,hashlib,datetime,re,struct,sys,collections
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');B=Path(__file__).resolve().parent;P=B/'competition-prep';R=ROOT/'FmLauncher/data/research';REF=R/'COUNTRY_BATCH_BLR_BEL_AUT_AUS_ARG_20261114/native-prep';D=R/'GHIDRA_ENGINE_20261107_R5/decompiled/functions';sys.path.insert(0,str(ROOT/'FM08-Database-Tools/scratch'))
from create_italy_structure_i1_20261108 import load
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
comps={r['uid']:r for r in read(REF/'competition-catalog.json')};nation=next(r for r in read(REF/'native-nation-catalog.json')if r['uid']==765);assert nation['index']==139
settings=D/'ram_f01e90.c';minimum=D/'ram_f02010.c'
num=lambda s:int(s.strip(),0)
registered=[]
for m in re.finditer(r'FUN_00d63c10\(([^;]+)\);',settings.read_text(encoding='utf-8')):
 a=[num(x)for x in m.group(1).split(',')];assert len(a)==3;registered.append(dict(CompetitionUID=a[0],Level=a[1],RegistrationArgument=a[2],Catalogue=comps[a[0]]))
assert len(registered)==6
requirements=[]
for m in re.finditer(r'FUN_00d35180\(([^;]+)\);',minimum.read_text(encoding='utf-8')):
 a=[num(x)for x in m.group(1).split(',')];assert len(a)==6 and a[-2:]==[0,0];uid,fb,lo,hi,_,_=a
 requirements.append(dict(Country='England',CompetitionUID=uid,CatalogueIndex=comps[uid]['index'],Name=comps[uid]['names'][0],Minimum=lo,Maximum=lo if hi==0xfffffffe else None if hi==0xffffffff else hi,RawArguments=a,Registered=next((r for r in registered if r['CompetitionUID']==uid),None),ParentUID=150990 if uid in[5123054,5123055]else None,FormQualification='BothCurrent/effectiveALT+independentRegional counters must satisfyminimum/max; sourceonly nofutureloaderPASS'))
assert len(requirements)==16 and len([r for r in requirements if r['Maximum']==r['Minimum']])==7
frozen=REF/'input/X20-after-SI';freeze=read(REF/'source-freeze.json');server=frozen/'server_db.dat';assert sha(server)==freeze['hashes']['server_db.dat']
records=read(REF/'native-structure.json')['records'];world={r['ClubUID']:r for r in read(REF/'native-world-identities.json')};a=load(frozen,'server_db.dat');observed=[];snapshot=[]
for req in requirements:
 idx=req['CatalogueIndex'];members=[[],[]]
 for r in records:
  st=r['Start'];cur,prev,alt=struct.unpack_from('<iii',a,st+7);reg=struct.unpack_from('<i',a,st+47)[0];assert cur==r['CurrentDivisionIndex']and prev==r['PreviousDivisionIndex'];w=world.get(r['ClubUID']);effective=alt if alt>=0 else cur
  for bank,chosen in enumerate([cur,effective]):
   contributions=int(chosen==idx)+int(reg==idx)
   if contributions:
    members[bank].append(dict(ClubUID=r['ClubUID'],TeamIndex=r['TeamIndex'],Current=cur,Alternate=alt,EffectiveAlternate=effective,Regional=reg,CounterContributions=contributions,Country=w.get('TeamCountry')if w else None,NativeKind=w.get('NativeTeamKind')if w else None,ParentUID=w.get('ParentUID')if w else None,Names=w.get('Names',[])if w else [],IdentityResolved=bool(w)))
 counts=[sum(r['CounterContributions']for r in bank)for bank in members]
 for k,count in enumerate(counts):assert count>=req['Minimum']and(req['Maximum']is None or count<=req['Maximum']),(req['Name'],k,count)
 assert all(r['Country']is not None and r['IdentityResolved']for bank in members for r in bank)
 observed.append(dict(**req,ReferenceCurrentCount=counts[0],ReferenceEffectiveAlternateCount=counts[1],ReferenceKnownStockOnly=True,CurrentMembers=members[0],EffectiveAlternateMembers=members[1]));print(req['Name'],counts,req['Minimum'],req['Maximum'])
inputs=[settings,minimum,REF/'source-freeze.json',REF/'native-structure.json',REF/'native-world-identities.json',REF/'competition-catalog.json',REF/'native-nation-catalog.json',server]
dump(P/'native-competition-requirements.json',dict(Status='R5_DECLARATIONS_AND_PINNED_ACCEPTED_X20_REFERENCE_READBACK',Country='England',NativeNationIndex=139,NativeNationUID=765,RegisteredLevels=registered,PlayableGroups=7,ClassicPlayingCounts=[20,24,24,24,24,22,22],ClassicPlayingClubs=160,Requirements=observed,RawDeclarations=16,BothBankReferenceChecks=32,ReferenceNativeSource=str(frozen),ReferenceSelectionOnly=True,X21NotAccepted=True,NewFreeze=False,RuntimeExecuted=False,NativeWriterAllowed=False,NativeUIDAllocated=False,DatabaseWritten=False,Inputs={str(f):sha(f)for f in inputs},Caution='Referencecountsarenotfutureprojection. Modernsource160playing+4lowerchangesstillneedphysicalUIDmapandalllowerCurrent/ALT/regionalreconciliationbeforeDAT. LimitscomefromR5notcounts.'))
