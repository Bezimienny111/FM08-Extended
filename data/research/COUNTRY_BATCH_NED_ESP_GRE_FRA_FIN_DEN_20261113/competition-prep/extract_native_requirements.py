"""Read existing R5 declarations and reference UID catalogues; never infer league limits from row counts."""
from pathlib import Path
import re,json,hashlib,datetime,sys
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';O=Path(__file__).resolve().parent;D=R/'GHIDRA_ENGINE_20261107_R5/decompiled/functions';REF=R/'COUNTRY_BATCH_IDN_IND_HKG_20261112'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
comps={x['uid']:x for x in read(REF/'competition-catalog.json')};nations={x['uid']:x for x in read(REF/'native-nation-catalog.json')};world={x['ClubUID']:x for x in read(REF/'native-world-identities.json')}
files={'Netherlands':('ram_ec3af0.c','ram_ec3cc0.c'),'Spain':('ram_ec7580.c','ram_ec76a0.c'),'Greece':('ram_eb39b0.c','ram_eb3aa0.c'),'France':('ram_eb7950.c','ram_eb7a90.c'),'Finland':('ram_ee57e0.c','ram_ee5900.c'),'Denmark':('ram_ebc0b0.c','ram_ebc240.c')}
parent={69:121091,70:121091,71:121091,72:121091,1701138:8,1701139:8}
req=[];registered=[];mandatory=[];pins={}
def num(s):
 s=s.strip()
 if s.startswith('&'):
  m=re.search(r'_([0-9a-fA-F]{8})$',s);assert m,s;return int(m.group(1),16)
 return int(s,0)
for country,(sf,mf) in files.items():
 for f in [sf,mf]:pins[str(D/f)]=sha(D/f)
 settings=(D/sf).read_text(encoding='utf-8');mins=(D/mf).read_text(encoding='utf-8');regs={}
 for match in re.finditer(r'FUN_00d63c10\(([^;]+)\);',settings):
  a=[num(x) for x in match.group(1).split(',')];assert len(a)==3;regs[a[0]]=dict(CompetitionUID=a[0],Level=a[1],RegistrationArgument=a[2]);registered.append(dict(Country=country,**regs[a[0]],NativeName=comps.get(a[0],{}).get('names',[]),SettingsFile=str(D/sf)))
 ownernation=next(x for x in nations.values() if country in x['names'] or country=='Netherlands' and 'Holland' in x['names'])
 for match in re.finditer(r'FUN_00d35180\(([^;]+)\);',mins):
  a=[num(x) for x in match.group(1).split(',')];assert len(a)==6;uid,fallback,lo,hi,form,last=a;assert form==0 and last==0
  scoped=uid==1301432;countnation=nations[fallback] if scoped else ownernation;maximum=lo if hi==0xfffffffe else None if hi==0xffffffff else hi
  q=dict(Country=countnation['names'][0] if scoped else country,RuleOwnerCountry=country,CompetitionUID=uid,CatalogueIndex=comps[uid]['index'],NativeName=comps[uid]['names'][0],Form0Min=lo,Form0Max=maximum,Form1DefaultMin=lo,Form1DefaultMax=maximum,CountrySpecific=scoped,CountryFallbackUID=fallback,NativeCountryIndex=countnation['index'],OwnerCountryIndex=ownernation['index'],Registration=regs.get(uid),ParentRegistration=regs.get(parent.get(uid)),MinimumFunctionFile=str(D/mf),RawArguments=a,Form1Qualification='D35180 Form0 initializes absent Form1 default; both actual Current and effective Alternate/regional inputs must be verified independently after known stock loader effects',CounterScope='typed TEAM-tail nation counter for generic1301432; all other COMP counted without fallback-country filtering',FixedPlayingFormatQualification='minimum and registration are evidence; non-exact minimum is not an exact playing-field size')
  req.append(q)
 for match in re.finditer(r'FUN_00d35150\(([^;]+)\);',mins):
  uid=num(match.group(1));row=world.get(uid);mandatory.append(dict(Country=country,TEAMUID=uid,NativeNames=row['Names'] if row else [],NativeCountry=row['TeamCountry'] if row else None,SourceExpression=match.group(1),Meaning='D35150 resolves TEAM UID and appends selector-owned list+0x18; retain registry identity. Do not reinterpret as deletion/exclusion without consumer proof.'))
for f in ['ram_d35180.c','ram_d35150.c','ram_d93030.c','ram_d35330.c','ram_d353f0.c']:
 pins[str(D/f)]=sha(D/f)
for f in ['competition-catalog.json','native-nation-catalog.json','native-world-identities.json']:pins[str(REF/f)]=sha(REF/f)
assert len(req)==46 and len(registered)==16
out=dict(Status='STATIC_NATIVE_REQUIREMENTS_PINNED_SOURCE_COLLECTION_ONLY',CreatedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),ExecutableSHA256='157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d',requirements=req,PlayableRegistrations=registered,RequiredChecksBothForms=len(req)*2,PlayableLevels=len(registered),D35150TEAMRegistrations=mandatory,SourcePins=pins,ReferenceCatalogueQualification='UID/name/index reference is X16-after-SI before this batch. Fresh accepted X17 catalogue and physical Current/ALT/regional counts required before any future writer. No DB state inferred from these static declarations.',GroupedLinks=[dict(ChildUID=k,ParentUID=v)for k,v in parent.items()],FrenchOverseasCounterQualification='Seven generic1301432 requirements belong to France rule owner but use distinct territory national counters; Country is the actual counter nation, RuleOwnerCountry is France. Never filter them as mainland France.',RuntimeStatus='PENDING',NativeDBWrites=False,UIDAllocation=False)
(O/'native-competition-requirements.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('PASS',len(req),'requirements',len(req)*2,'formchecks',len(registered),'playablelevels',len(mandatory),'explicitTEAMregistrations')
for c in files:print(c,len([x for x in req if x['RuleOwnerCountry']==c]),[(r['NativeName'],r['Form0Min'],r['Form0Max']) for r in req if r['RuleOwnerCountry']==c])
