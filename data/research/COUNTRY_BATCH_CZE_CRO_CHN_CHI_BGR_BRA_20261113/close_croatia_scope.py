"""Croatia configuration adapter using saved ranking and captured final/current evidence."""
from pathlib import Path
from fractions import Fraction
import json,hashlib,ast,re,html,datetime,sys,collections
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;P=B/'competition-prep';ROOT=B.parents[3];read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not(B/'scope-closures/Croatia.json').exists()
main=read(P/'club-profiles-Croatia.json');extra=read(P/'club-profiles-Croatia-supplement.json');reg={x['TMID']:x for x in read(P/'club-identities-Croatia.json')+read(P/'club-identities-Croatia-supplement.json')};assert len(main)==26 and len(extra)==2 and len(reg)==28
previous={};inputs=[]
for c in [c for c in read(P/'source_competitions.json') if c['Country']=='Croatia']:
 assert c['CurrentSeason']['name']=='26/27' and c['CurrentSeason']['id']=='2026' and c['PreviousCompletedSeason']['name']=='25/26'
 f=B/c['previous_completed_table_file'];tables=read(f)['tables'];assert len(tables)==1
 for r in tables[0]['rows']:
  previous[str(r['club_id'])]=dict(TMID=str(r['club_id']),Name=r['club_name'],PreviousLevel=c['RealLevel'],PreviousCompetition=c['id'],FinalPosition=r['position'],Matches=r['matches'],Wins=r['wins'],Draws=r['draws'],Losses=r['losses'],GoalDifference=r['goal_difference'],GoalsFor=r['goals_for'],GoalsAgainst=r['goals_against'],Points=r['points'],SourceFile=str(f.relative_to(B)),SourceSHA256=sha(f))
 inputs+=[f,B/c['current_clubs_file'],B/c['SeasonMetadataFile']]
f=P/'sources/supplemental/croatia-previous-third.html';s=f.read_text(encoding='utf-8');table=re.search(r'<table[^>]*>(.*?)</table>',s[s.index('Ukupna ljestvica'):],re.S).group(1);rows=[]
known={1:'552',2:'12817',3:'17671',4:'22766',5:'34147'}
for tr in re.findall(r'<tr[^>]*>(.*?)</tr>',table,re.S):
 cells=[html.unescape(re.sub('<[^>]+>','',c)).strip() for c in re.findall(r'<td[^>]*>(.*?)</td>',tr,re.S)]
 if not cells or not cells[0].isdigit():continue
 n=int(cells[0]);r=dict(TMID=known.get(n),Name=cells[1],PreviousLevel=3,PreviousCompetition='HNS-DRUGA-NL',FinalPosition=n,Matches=int(cells[2]),Wins=int(cells[3]),Draws=int(cells[4]),Losses=int(cells[5]),GoalsFor=int(cells[6]),GoalsAgainst=int(cells[7]),GoalDifference=int(cells[8]),Points=int(cells[9]),SourceFile=str(f.relative_to(B)),SourceSHA256=sha(f));rows.append(r)
 if r['TMID']:assert r['TMID'] not in previous;previous[r['TMID']]=r
assert len(rows)==16 and all(x['Matches']==30 for x in rows)
dump(P/'croatia-previous-third-normalized.json',dict(SourceURL='https://sportnet.hr/statistika/805/ljestvice/',DisplayedSeason='2025/26',Completed=True,Rows=rows,MappingQualification='Only exact already-established club identities/top5 mapped to TMID; remaining regionalidentities unassigned'))
observed=dict(SourceURL='https://semafor.hns.family/klubovi/1555/nk-grobnican/?cid=114348039',Competition='SuperSport Druga NL',DisplayedSeason='2026/27',EvidenceMode='webtool parsed primarypage observed2026-11-13; direct rawHTTP403, NOT fullHTTPcapture',CurrentClubNames=['Uskok','Dugo Selo','Uljanik','Jarun','Bjelovar','Inker','Solin','Zagora','Trnje','Slavonija Pozega','Radnik Krizevci','Hrvatski dragovoljac','Grobnican','Lucko','Varteks','Koprivnica'],SelectedExtras={'45478':'NK Jarun','34147':'NK Uljanik'},MissingRawHTTP=True)
dump(P/'croatia-current-third-observed.json',observed)
engine=ROOT/'FmLauncher/data/research/COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/competition-prep/build_source_cascade_plan.py';tree=ast.parse(engine.read_text(encoding='utf-8-sig'));exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='ranking_key'],type_ignores=[]),str(engine),'exec'),globals())
first=[x for x in main if x['RealLevel']==1];second=[x for x in main if x['RealLevel']==2];assert len(first)==10 and len(second)==16
eligible=[x for x in second if not reg[x['TMID']]['ParentTMID'] and x['TMID'] in previous];ordered=sorted(eligible,key=ranking_key);promoted={x['TMID'] for x in ordered[:2]};assert len(promoted)==2
# Fill missing nativeSecond places: savedpreviousKR2relegatedJarun then best remainingeligiblepreviousThirdUljanikrank5.
assert previous['45478']['PreviousLevel']==2 and previous['45478']['FinalPosition']==12 and previous['34147']['FinalPosition']==5
assign=[]
for x in main+extra:
 t=x['TMID'];r=reg[t];assert r['SourceCountryID']==37 and r['SourceRef'];level=1 if x['RealLevel']==1 or t in promoted else 2
 parent=r['ParentTMID']
 if parent:assert t=='44796' and parent=='419' and level==2 and any(y['TMID']==parent and y['RealLevel']==1 for y in first)
 assert r['SourceClubTypeID']==(2 if parent else 1)
 assign.append(dict(x,ParentTMID=parent,SourceClubTypeID=r['SourceClubTypeID'],SourceCountryID=37,SourceScope='closed_country_Croatia',SourceIdentityEvidence=r['SourceRef'],ClubIdentityPending=False,TargetNativeLevel=level,TargetNativeCompetitionUID=129645 if level==1 else 129646,TargetNativeDivisionIndex=144 if level==1 else 145,SourcePreviousRank=previous.get(t),NativeUIDAllocated=False,ClassicPlacementReason='currentTop10 plus2savedrank eligible firstteams ->classic12; remainingcurrentsecond14 plusJarunprevious2 andUljanikprevious3rank5 ->classic16'))
assert collections.Counter(x['TargetNativeLevel'] for x in assign)=={1:12,2:16}
closed=B/'scope-closures/Croatia-targets.json';dump(closed,assign)
guards=['Preserve DinamoII sportingparent419 and source reservekind; do not inventkind16 or promote alongsideparent','Before nativewriter prove schedulerparent/reserve eligibility and preserve/technicallydefer nativeidentity; sourceclosure is not NativeEligibilityPASS','Reconcile inherited lowerpools and both counterforms in future nativepreflight','DirectHNSHTTP403 is a provenancegap; webtool primarycurrentpage evidence is distinct from rawcapture']
dump(P/'source-cascade-Croatia.json',dict(Status='CLOSED_SOURCE_COUNTRY_SCOPE_NOT_NATIVE_PREFLIGHT',SourceCounts=dict(Main26=26,RequiredFillers2=2,Total28=28),ClassicCounts={'Top12':12,'Second16':16},PromotedBySavedPreviousRank=[dict(TMID=x['TMID'],Name=x['Name'],Previous=previous[x['TMID']]) for x in ordered[:2]],RankGaps=[dict(TMID=x['TMID'],Name=x['Name']) for x in main if x['TMID'] not in previous],ParentGuards=[dict(TMID='44796',ParentTMID='419',ParentTier=1,ChildTier=2)],Assignments=assign,MandatoryBeforeNativeWrite=guards))
inputs +=[f,engine,P/'croatia-current-third-observed.json',P/'club-identities-Croatia.json',P/'club-identities-Croatia-supplement.json',P/'native-competition-requirements.json']
dump(B/'scope-closures/Croatia.json',dict(Status='CLOSED_NATIVE_CASCADE_CLUB_IDENTITIES_AND_PARENTS',Country='Croatia',Clubs=28,TargetsSHA256=sha(closed),SourceCollectionScopeApproved=True,AllParentsResolvedOrExplicitDeferred=True,PendingParentCount=0,NativeSchedulerEligibilityReviewed=False,NativeEligibilityStatus='INHERITED_RESERVE_SCHEDULER_GUARD_UNKNOWN_NOT_NATIVE_PASS',MandatoryBeforeNativeWrite=guards,NativeUIDAllocated=False,DatabaseWritten=False,ClosedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),Inputs={str(p):sha(p) for p in inputs}))
old=read(B/'source-targets.json');assert not any(x['Country']=='Croatia' for x in old);dump(B/'source-targets.json',old+assign);print('CROATIA_CLOSED28',sorted(promoted),'parentguard1; SourceOnly')
