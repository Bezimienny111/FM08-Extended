"""Read existing R5 declarations and reference UID catalogues; never infer league limits from row counts."""
from pathlib import Path
import re,json,hashlib,datetime,sys
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';O=Path(__file__).resolve().parent;D=R/'GHIDRA_ENGINE_20261107_R5/decompiled/functions';REF=R/'COUNTRY_BATCH_CZE_CRO_CHN_CHI_BGR_BRA_20261113/native-prep'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
comps={x['uid']:x for x in read(REF/'competition-catalog.json')};nations={x['uid']:x for x in read(REF/'native-nation-catalog.json')};world={x['ClubUID']:x for x in read(REF/'native-world-identities.json')}
files={'Belarus':('ram_e53a80.c','ram_e53b80.c'),'Belgium':('ram_ee7bd0.c','ram_ee7da0.c'),'Austria':('ram_e82380.c','ram_e824a0.c'),'Australia':('ram_e3f580.c','ram_e3f680.c'),'Argentina':('ram_ed2b90.c','ram_ed2d60.c')}
parent={7509144:7500118,7509145:7500118}
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
  a=[num(x) for x in match.group(1).split(',')];assert len(a) in [2,3];regs[a[0]]=dict(CompetitionUID=a[0],Level=a[1] if len(a)==3 else None,RegistrationArgument=a[2] if len(a)==3 else None,RawArguments=a,RawCallingConventionNeedsReview=len(a)!=3);registered.append(dict(Country=country,**regs[a[0]],NativeName=comps.get(a[0],{}).get('names',[]),SettingsFile=str(D/sf)))
 ownernation=next(x for x in nations.values() if country in x['names'] or country=='China' and 'China PR' in x['names'])
 for match in re.finditer(r'FUN_00d35180\(([^;]+)\);',mins):
  a=[num(x) for x in match.group(1).split(',')];assert len(a)==6;uid,fallback,lo,hi,form,last=a;assert form==0;rawflag_pending=last!=0
  scoped=uid==1301432;countnation=nations[fallback] if scoped else ownernation;maximum=lo if hi==0xfffffffe else None if hi==0xffffffff else hi
  q=dict(Country=countnation['names'][0] if scoped else country,RuleOwnerCountry=country,CompetitionUID=uid,CatalogueIndex=comps[uid]['index'],NativeName=comps[uid]['names'][0],Form0Min=lo,Form0Max=maximum,Form1DefaultMin=lo,Form1DefaultMax=maximum,CountrySpecific=scoped,CountryFallbackUID=fallback,NativeCountryIndex=countnation['index'],OwnerCountryIndex=ownernation['index'],Registration=regs.get(uid),ParentRegistration=regs.get(parent.get(uid)),MinimumFunctionFile=str(D/mf),RawArguments=a,RawFinalFlag=last,RawFlagSemanticsPending=rawflag_pending,Form1Qualification='D35180 Form0 initializes absent Form1 default; both actual Current and effective Alternate/regional inputs must be verified independently after known stock loader effects',CounterScope='typed TEAM-tail nation counter for generic1301432; all other COMP counted without fallback-country filtering',FixedPlayingFormatQualification='minimum and registration are evidence; non-exact minimum is not an exact playing-field size')
  q['DeclaredMinimum']=lo;q['DeclaredMaximum']=maximum
  if country=='China':
   q['Form0Min']=None;q['Form0Max']=None;q['Form1DefaultMin']=None;q['Form1DefaultMax']=None;q['Form1Qualification']='Raw finalflag0/1 interpretation pending native caller/consumer proof; no season/form label asserted'
  req.append(q)
 for match in re.finditer(r'FUN_00d35150\(([^;]+)\);',mins):
  uid=num(match.group(1));row=world.get(uid);mandatory.append(dict(Country=country,TEAMUID=uid,NativeNames=row['Names'] if row else [],NativeCountry=row['TeamCountry'] if row else None,SourceExpression=match.group(1),Meaning='D35150 resolves TEAM UID and appends selector-owned list+0x18; retain registry identity. Do not reinterpret as deletion/exclusion without consumer proof.'))
for f in ['ram_e9fa00.c','ram_d63c10.c','ram_d35180.c','ram_d35150.c','ram_d93030.c','ram_d35330.c','ram_d353f0.c']:
 pins[str(D/f)]=sha(D/f)
for f in ['competition-catalog.json','native-nation-catalog.json','native-world-identities.json']:pins[str(REF/f)]=sha(REF/f)
assert len(registered)==10
out=dict(Status='STATIC_DECLARATIONS_ONLY_SCHEDULER_ELIGIBILITY_NOT_CLOSED',CreatedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),ExecutableSHA256='157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d',requirements=req,PlayableRegistrations=registered,RequiredChecksBothForms=None,RawDeclarations=len(req),NominalBothFormSlots=len(req)*2,PlayableLevels=len(registered),RosterScopeClosed=False,BrazilThird=dict(CompetitionUID=107192,RawSelectorExact=128,VerifiedFrozenFirstTEAMPopulation=128,SchedulerOutParam3InitializerRaw=128,SchedulerRawByte08=16,SchedulerRawByte0B=8,PlayingField='UNKNOWN_UNTIL_CONSUMER_SCHEMA_PROVEN',RawStageFieldUnitsProven=False,SchedulerFile=str(D/'ram_e9fa00.c'),Prior64MemoryNotAccepted=True),D35150TEAMRegistrations=mandatory,SourcePins=pins,ReferenceCatalogueQualification='Accepted frozenX17 UID/name/index reference only; no nativebase selected for new batch. Raw selector declarations are not proof of complete scheduler eligibility or roster scope.',GroupedLinks=[dict(ChildUID=k,ParentUID=v)for k,v in parent.items()],EligibilityQualification='Each playable scheduler/selection predicate and reserve parent must be reviewed before roster scope closes. Preserve rawflag variants, especially China. Do not infer playingfield from min alone.',RuntimeStatus='PENDING',NativeDBWrites=False,UIDAllocation=False)
(O/'native-competition-requirements.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('EXTRACTED_NOT_SCOPE_CLOSED',len(req),'raw declarations',len(registered),'registered levels; scheduler/flag interpretation pending')
for c in files:print(c,'declarations',len([x for x in req if x['RuleOwnerCountry']==c]),'registered',len([x for x in registered if x['Country']==c]))

