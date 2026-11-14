from pathlib import Path
import json,hashlib,datetime,sys
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;P=B/'competition-prep'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
dest=B/'scope-closures/Belgium.json';assert not dest.exists();stage=read(P/'source-cascade-Belgium-staged.json');assign=read(P/'belgium-staged-targets.json');assert len(assign)==61 and stage['UnfilledPlayableThird']==16
for r in assign:
 r['SourceScope']='closed_country_Belgium_DATA_ONLY_16physicalLegacyGap';r['TechnicalScopeGap']='16additionalseniorThirdplaying slots need individuallymappedknowncountryKind0physicalstand-ins; noModern68claim.9B/U23remainnonplayable withparent/nativeKindproofpending beforewriter.'
 r['NativeWriterAllowed']=False
 if r['ParentTMID']:r['NonplayableAssignmentStatus']='Catalog verifiesLowerCOMP1301432/index550; actualnativeKind,parent/current/effectiveALTassignment stillpending typedprojection, noCup1301404'
assert [sum(r['TargetNativeLevel']==l for r in assign)for l in[1,2,3,5]]==[18,18,16,9]
target=B/'scope-closures/Belgium-targets.json';dump(target,assign)
inputs=[P/'source-cascade-Belgium-staged.json',P/'belgium-previous-final-normalized.json',P/'club-identities-Belgium.json',P/'club-profiles-Belgium.json',P/'native-competition-requirements.json',Path(__file__).resolve(),B/'build_belgium_stage.py']
dump(dest,dict(Status='CLOSED_NATIVE_CASCADE_CLUB_IDENTITIES_AND_PARENTS',Country='Belgium',Clubs=61,TargetsSHA256=sha(target),SourceCollectionScopeApproved=True,AllParentsResolvedOrExplicitDeferred=True,PendingParentCount=0,NativeSchedulerEligibilityReviewed=False,NativeEligibilityStatus='SOURCE_ONLY_RESERVE_PERIOD_RULES_AND16PHYSICAL_STAND_INS_PENDING',NativeWriterAllowed=False,ProjectedModernPlayingClubs=52,ClassicPlayingTarget=68,UnfilledModernPlayingSlots=16,PhysicalLegacyStandInsProposed=16,All68Modernized=False,TechnicalScopeGap='Source61=52senior+9B/U23; 18top+18second+16Thirdsenior modernized sourceproof,16Thirdslotsneedrealindividuallegacyphysicalmapping. All9B/U23keptoutofSecond+Thirdplayoffs. LowerpoolCOMP1301432/index550catalogexists; nativeKind/parents/assignmentpending. NativeCurrent/ALT/minmax/allfourFourthminimums remainmandatory.',SourceBoundaryBudget='AgentTMandtwoRSSSFURLsempty; rootoneboundedTMlookupempty; no furthersearchbudgetrenewal. RootapprovedDATA-only61scopewithexplicit16physicallegacygap2026-11-14.',NativeUIDAllocated=False,DatabaseWritten=False,ClosedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),Inputs={str(f):sha(f)for f in inputs}))
old=read(B/'source-targets.json')if(B/'source-targets.json').exists()else[];assert not any(r['Country']=='Belgium'for r in old);dump(B/'source-targets.json',old+assign);print('CLOSED_SOURCE Belgium61',sha(target),'16PLAYING_SLOTS_STILL_NATIVE_MAPPING_GAP')
