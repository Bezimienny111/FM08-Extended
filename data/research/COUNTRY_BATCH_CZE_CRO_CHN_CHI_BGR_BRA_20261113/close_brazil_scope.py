"""Brazil source-only adapter: factual A/B/C/D+exact12 previousD lowerfillers, no nativeUIDs."""
from pathlib import Path
import json,hashlib,datetime,sys,collections,re,html
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;P=B/'competition-prep';ROOT=B.parents[3];read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not(B/'scope-closures/Brazil.json').exists()
main=read(P/'club-profiles-Brazil.json');extra=read(P/'club-profiles-Brazil-supplement.json');reg={x['TMID']:x for x in read(P/'club-identities-Brazil.json')+read(P/'club-identities-Brazil-supplement.json')};assert len(main)==156 and len(extra)==12 and len(reg)==168
assert collections.Counter(x['SourceCompetition'] for x in main)=={'BRA1':20,'BRA2':20,'BRA3':20,'BRA4':96}
assert all(r['SourceCountryID']==26 and r['SourceClubTypeID']==1 and r['ParentTMID'] is None and r['SourceRef'] for r in reg.values())
inputs=[];previous={};phase=[]
for c in [c for c in read(P/'source_competitions.json') if c['Country']=='Brazil']:
 assert c['CurrentSeason']['name']=='2026' and c['CurrentSeason']['id']=='2025' and c['PreviousCompletedSeason']['name']=='2025' and c['PreviousCompletedSeason']['id']=='2024'
 f=B/c['previous_completed_table_file'];tables=read(f)['tables'];inputs +=[f,B/c['current_clubs_file'],B/c['SeasonMetadataFile']]
 for table in tables:
  phase.append(dict(Competition=c['id'],Name=table['name'],Rows=len(table['rows']),SourceFile=str(f.relative_to(B)),SourceSHA256=sha(f)))
  if c['id']=='BRA3' and len(table['rows'])!=20:continue
  for row in table['rows']:
   t=str(row['club_id']);assert t not in previous
   previous[t]=dict(TMID=t,PreviousCompetition=c['id'],PreviousLevel=c['RealLevel'],RawGroup=table['name'],FinalPosition=row['position'],Matches=row['matches'],Points=row['points'],Wins=row['wins'],GoalsFor=row['goals_for'],GoalsAgainst=row['goals_against'],SourceFile=str(f.relative_to(B)),SourceSHA256=sha(f),TableContext='BRA4completedregionalfirstphase14matches; BRA3saved20clubfirstphase, promotiongroupsseparate; NOT inventedoverall finalrank')
assert all(x['TMID'] in previous and previous[x['TMID']]['PreviousCompetition']=='BRA4' and previous[x['TMID']]['Matches']==14 and previous[x['TMID']]['FinalPosition']>=5 for x in extra)
S=P/'sources/supplemental';proofs={}
proofmap={'22332':('brazil-horizonte-active','Activefirstclub2026 officialclubnews dated2026-11-09; sitecachedtable still2025 and NOT used as currenttable'),'51851':('brazil-fnf-santa-cruz-final2026','OfficialPotiguar2026homologatedfinal6thSantaCruzdeNatal'),'96026':('brazil-ua-2026-fixtures','SameTM96026currentUA brand, fixtures17Jan..14Mar2026 Tocantinense; pagedisplay25/26 preserved, actualdates2026 authoritative for sourceyear'),'5752':('brazil-fgf-active-goiania-goianesia','OfficialFGF2026DivisaodeAcesso participantsGoi+Goianesia; source fullnamemismatch kept before nativereuse'),'31428':('brazil-fgf-active-goiania-goianesia','OfficialFGF2026DivisaodeAcesso participantGoianesia'),'11266':('brazil-boavista-rjgov2026','RJpublicradio2026Carioca squadannouncement inwebparsedprimarypublicsource; HTTPtimeout distinct from observedarticle'),'25671':('brazil-fpf-monteazul-active','OfficialFPF2026PaulistaoA2table identifiesAtleticoMonteAzul/MonteAzulPaulista')}
for x in extra:
 t=x['TMID'];profile=read(B/x['ProfileFile']);league=profile.get('league') or {}
 if t in proofmap:
  key,reason=proofmap[t];m=S/(key+'.json');capture=read(m);proofs[t]=dict(Reason=reason,URL=capture['URL'],CaptureMetadata=str(m.relative_to(B)),CaptureMetadataSHA256=sha(m),RawHTTP=bool(capture.get('BodySHA256')),RawBodyFile=capture.get('BodyFile'),RawBodySHA256=capture.get('BodySHA256'),FetchError=capture.get('FetchError'))
 else:
  assert league.get('id') in ['BRCB','BRAL','BRES','BRCM']
  proofs[t]=dict(Reason='Currentliveprofile regionalchampionship association, fetched/snapshot13XI2026, nationalcurrentlevelunassigned',SourceProfile=x['ProfileFile'],ProfileSHA256=sha(B/x['ProfileFile']),RawClubSource=reg[t]['SourceRef'],CurrentRegionalLeague=league)
# Parsed publicpage receipt must not be represented as successful rawHTTP.
proofs['11266']['ParsedObservation']=dict(URL='https://www.rj.gov.br/radioroquettepinto/node/14029',Heading='Boavista divulga elenco para a disputa do Campeonato Carioca de2026',ObservedAt='2026-11-13',Facts='ClubSaquarema firstteam,2026Carioca campaign,senior squadannouncement; no externalplayerfacts imported',RawCapture=False)
# Reject a known irrelevant genericFERJpage: its current rawbody has noBoavista; it is NOT an evidencepin for activity.
ignored=dict(URL='https://fferj.com.br/noticias/campeonatos/profissional/estadual?pg=2',Reason='Searchsnippet and openedrawpage differ; rawpage doesnot containBoavista. Not used as currentactivityproof.')
witness=P/'brazil-native-review/decision.json';assert sha(witness)=='6d72b3395699639c066ab6abd87d99b29076b31f25b26958c2aca9e625996429'
warnings=[dict(TMID='96026',CurrentProviderName='UA Carmolandense',RawOfficialName='Uniao AtleticoAraguainense',Action='KeepcurrentphysicalTMentity/sourcefacts; historical/nativeUIDcontinuity must be proved separately, no automatic historicalreuse'),dict(TMID='5752',CurrentProviderName='GoianiaEC',RawOfficialName='RCGoiania',Action='OfficialFGFcurrentGoiania confirmsactivity; rawfullnameconflict preserved; do not overwrite/legalize historicalnativeidentity from namealone')]
assign=[]
for x in main+extra:
 t=x['TMID'];r=reg[t];level=x['RealLevel'] if x in main and x['RealLevel'] in [1,2] else 3;uid={1:102423,2:107191,3:107192}[level];idx={1:73,2:85,3:86}[level]
 a=dict(x,ParentTMID=None,SourceClubTypeID=1,SourceCountryID=26,SourceScope='closed_country_Brazil',ClubIdentityPending=False,SourceIdentityEvidence=r['SourceRef'],TargetNativeLevel=level,TargetNativeCompetitionUID=uid,TargetNativeDivisionIndex=idx,SourcePreviousRank=previous.get(t),NativeUIDAllocated=False,ReadyForNativeImport=False,ClassicPlacementReason='RetainmodernA20/B20; configuredclassicC128=currentC20+currentD96+12realpreviousDnonqualifiers activein2026regional/lower football, not a currentnationalmembership claim')
 if x in extra:a.update(RealLevel=None,CurrentNationalLevelUnknown=True,Active2026Evidence=proofs[t],PreviousRealLevel=4,NativeHistoricalIdentityPending=t in ['96026','5752'])
 assign.append(a)
assert len(assign)==168 and collections.Counter(x['TargetNativeLevel'] for x in assign)=={1:20,2:20,3:128}
closed=B/'scope-closures/Brazil-targets.json';dump(closed,assign)
guards=['ConfiguredBRA_THIRDfirstphase16groupsx8=128 provedtypedunits; actualTEAMruntime/gameacceptance notobserved','All168 currentphysicalsourceentities parentlessfirstteams/country26, but existingnativeUIDs must be resolved separately','Nativehistoricalcontinuity for96026/5752 unresolved; sourcecollection doesnot authorize UIDreuse or merge histories','Reconcile all27inheritedstatepools/selectorrequirements without changingenginefieldsize; no sourceprofile currentnationalclaim for12extras','Futurepreflight exactcurrent/ALT/regionalcounts, schedulereligiblefirstTEAM128, deterministicclassic16x8draw and fullnativeidentityguards mandatory','No sourceCA_PA/personality/DOBshift or personUIDcreation; shortageslefttoengine']
dump(P/'source-cascade-Brazil.json',dict(Status='CLOSED_SOURCE_COUNTRY_SCOPE_NOT_NATIVE_PREFLIGHT',SourceCounts=dict(CurrentA20=20,CurrentB20=20,CurrentC20=20,CurrentD96=96,AdditionalRealPreviousD12=12,Total168=168),ClassicCounts={'A20':20,'B20':20,'C128':128},ConfiguredNativeFieldProof=dict(File=str(witness.relative_to(B)),SHA256=sha(witness),Groups16=16,TeamsPerGroup8=8,ConfiguredSlots128=128,LiveRuntimeObserved=False),PreviousTableContexts=phase,RequiredFillers=sorted([dict(TMID=x['TMID'],Name=x['Name'],Previous=previous[x['TMID']],Active2026Evidence=proofs[x['TMID']]) for x in extra],key=lambda x:(x['Previous']['FinalPosition'],-x['Previous']['Points']/x['Previous']['Matches'],x['TMID'])),EarlyNativeIdentityExceptions=warnings,IgnoredEvidence=[ignored],Assignments=assign,MandatoryBeforeNativeWrite=guards))
inputs +=[witness,P/'club-identities-Brazil.json',P/'club-identities-Brazil-supplement.json',P/'brazil-supplement-targets.json'];inputs +=[S/(key+'.json') for key in {x[0] for x in proofmap.values()}]
dump(B/'scope-closures/Brazil.json',dict(Status='CLOSED_NATIVE_CASCADE_CLUB_IDENTITIES_AND_PARENTS',Country='Brazil',Clubs=168,TargetsSHA256=sha(closed),SourceCollectionScopeApproved=True,AllParentsResolvedOrExplicitDeferred=True,PendingParentCount=0,NativeSchedulerEligibilityReviewed=False,NativeEligibilityStatus='CONFIGURED_FIELD128_PROVED_RUNTIME_AND_NATIVEIDENTITY_PREFLIGHT_PENDING',HistoricalNativeIdentityExceptions=warnings,MandatoryBeforeNativeWrite=guards,NativeUIDAllocated=False,DatabaseWritten=False,ClosedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),Inputs={str(p):sha(p) for p in inputs}))
old=read(B/'source-targets.json');assert not any(x['Country']=='Brazil' for x in old);assert all('PlayersFetched' in x for x in old),'No concurrentrosterwriter when appendingclosedcountry';dump(B/'source-targets.json',old+assign);print('BRAZIL_SOURCE_CLOSED168',collections.Counter(x['TargetNativeLevel'] for x in assign),'allcountrytargets',len(old+assign))
