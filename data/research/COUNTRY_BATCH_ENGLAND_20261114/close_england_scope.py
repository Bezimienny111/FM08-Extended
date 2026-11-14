from pathlib import Path
import json,hashlib,datetime,sys,collections
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;P=B/'competition-prep';read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
dest=B/'scope-closures/England.json';assert not dest.exists()
comps=read(P/'source_competitions.json');previous={};inputs=[]
for c in comps:
 f=B/c['previous_completed_table_file'];inputs.extend([f,B/c['current_clubs_file'],B/c['SeasonMetadataFile']]);assert c['CurrentSeason']['name']=='26/27'and c['PreviousCompletedSeason']['name']=='25/26'
 for tab in read(f)['tables']:
  for r in tab['rows']:
   assert r['matches']==(38 if c['RealLevel']==1 else 46)
   previous[r['club_id']]=dict(r,PreviousLevel=c['RealLevel'],PreviousCompetition=c['id'],SourceFile=str(f.relative_to(B)))
profiles=read(P/'club-profiles-England.json');ids={r['TMID']:r for r in read(P/'club-identities-England.json')};assert len(profiles)==len(ids)==164 and all(r['SourceClubTypeID']==1 and not r['ParentTMID']and r['SourceRef']for r in ids.values())
downs=set()
for group in ['NLN6','NLS6']:
 continuing=[r for r in profiles if r['SourceCompetition']==group and previous.get(r['TMID'],{}).get('PreviousLevel')==6];continuing.sort(key=lambda r:previous[r['TMID']]['position']);downs.update(r['TMID']for r in continuing[-2:])
assert downs=={'38899','46842','4279','3936'}
main={'GB1':(11,7,1),'GB2':(12,8,2),'GB3':(13,9,3),'GB4':(14,10,4),'CNAT':(109201,99,5),'NLN6':(5123054,587,6),'NLS6':(5123055,588,6)}
lower={'38899':(5103715,581,'Norfolk; compatible historic Southern catchment'),'46842':(5103715,581,'Herefordshire; Southern Central catchment'),'4279':(5103715,581,'Hampshire; Southern South catchment'),'3936':(5103714,580,'Kent; Isthmian catchment')}
assign=[]
for r in profiles:
 t=r['TMID'];i=ids[t];uid,index,level=main[r['SourceCompetition']];reason='retain actual26/27 group membership'
 if t in downs:uid,index,region=lower[t];level=7;reason='lowest continuing eligible25/26 final rank in currentNorth/South; '+region
 assign.append(dict(r,ParentTMID=None,SourceClubTypeID=1,SourceCountryID=i['SourceCountryID'],SourcePhysicalCountryID=i['SourceCountryID'],ClubIdentityPending=False,SourceScope='closed_country_England',SourceIdentityEvidence=i['SourceRef'],TargetNativeLevel=level,TargetNativeCompetitionUID=uid,TargetNativeDivisionIndex=index,NativeUIDAllocated=False,NativeWriterAllowed=False,NativeCountryPolicy='Preserve existing typed native sporting affiliation from root identityreference; physical Wales191 is separate and does not imply nativecountry change',PreviousFacts=previous.get(t),ClassicPlacementReason=reason))
counts=collections.Counter(r['TargetNativeCompetitionUID']for r in assign);assert [counts[u]for u in [11,12,13,14,109201,5123054,5123055]]==[20,24,24,24,24,22,22];assert sum(r['TargetNativeLevel']==7 for r in assign)==4
inputs.extend([P/'club-profiles-England.json',P/'club-identities-England.json',P/'native-competition-requirements.json',B/'native-reference/club-identity-reference-plan.json',Path(__file__).resolve()])
dump(P/'source-cascade-England.json',dict(Status='CLOSED_SOURCE_PLAYABLE160_PLUS4REGIONAL_DOWNS_NOT_NATIVE_IMPORT',Assignments=assign,ClassicPlayingCounts=[20,24,24,24,24,22,22],ModernSourceClubs=164,PlayingClubs=160,Downs=[r for r in assign if r['TargetNativeLevel']==7],Parents=0,PhysicalWelshClubs=[r['Name']for r in assign if r['SourceCountryID']==191],NativeCountryPolicy='FivephysicalWelshclubs do not authorize changingexistingnativeTeamCountry; roottypedidentityreferencecontrols sporting affiliation',LowerPoolPolicy='Preserve all9R5requiredlowerpools at22/22/21 and20/20/16/16/18/19 minima. Fourincomingregisteredsourceclubs assignedbygeographicalcatchment, no massStep3rosters. FullnativephysicalUID+Current/ALT/regionalreconciliation remains separate importblock.',NativeALTPolicy='Root owns exact4historicalALTcleanup and32predictions; do not rerun prior reference reader or guessloaderoverlay.',NativeWriterAllowed=False,DatabaseWritten=False))
target=B/'scope-closures/England-targets.json';dump(target,assign)
dump(dest,dict(Status='CLOSED_NATIVE_CASCADE_CLUB_IDENTITIES_AND_PARENTS',Country='England',Clubs=164,PlayingClubs=160,RegionalDowns=4,TargetsSHA256=sha(target),SourceCollectionScopeApproved=True,AllParentsResolvedOrExplicitDeferred=True,PendingParentCount=0,NativeSchedulerEligibilityReviewed=True,EligibilityQualification='All164sourceclubtype1parentless;160playing+4lowercascade ranked exclusivelybyfinished25/26; nativeALT4cleanup andalllowerphysicalprojection remainindependent importgates.',NativeWriterAllowed=False,NativeUIDAllocated=False,DatabaseWritten=False,ClosedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),Inputs={str(f):sha(f)for f in inputs}))
dump(B/'source-targets.json',assign);dump(B/'source-competitions.json',comps)
m=read(B/'manifest.json');m.update(Status='SOURCE_SCOPE_CLOSED_ROSTER_COLLECTION_STARTING',SourceScopeClosed=True,SourceClubs=164,ClassicPlayingClubs=160,RegionalDowns=4,RostersStarted=True,NativeWriterAllowed=False);dump(B/'manifest.json',m)
(B/'WZNOWIENIE.md').write_text('# Anglia: scope164 zamknięty, zbiór kadr rozpoczynany\n\nGate:scope-closures/England.json i England-targets.json.160grywalnych+4down:KingsLynn/Hereford/Farnborough->SouthernPremier,Dover->Isthmian. Ranking tylko finished25/26.164profile gotowe,0parents,5physicalWales zachowane osobno od native sportingcountry.\n\nNativeALT i164typedidentityreference należą do root. BezDAT/UID/freeze/wersji do akceptacjiX22. Kolektor standardowy collect_rosters.py England pracuje przyrostowo zcache; postęp roster-progress/England-targets.json. Nie ponawiać ukończonych kadr ani7katalogów/164profile.\n',encoding='utf-8')
print('SCOPE_CLOSED164',sha(target),[(r['Name'],r['PreviousFacts']['position'],r['TargetNativeCompetitionUID'])for r in assign if r['TargetNativeLevel']==7])
