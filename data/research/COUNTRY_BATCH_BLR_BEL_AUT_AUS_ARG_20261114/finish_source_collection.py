from pathlib import Path
import json,hashlib,subprocess,sys,csv,collections,datetime
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent
COUNTRIES=['Belarus','Belgium','Austria','Australia','Argentina']
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,x):(B/n).write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
def sig(rows):return sorted((str(c['TMID']),c['Country'],str(c['APISeason']))for c in rows)
alltargets=[];scopepins={};scopegaps={}
for country in COUNTRIES:
 slug=country.replace(' ','-');gatefile=B/'scope-closures'/(slug+'.json');closedfile=B/'scope-closures'/(slug+'-targets.json');progressfile=B/'roster-progress'/(slug+'-targets.json')
 gate=read(gatefile);closed=read(closedfile);progress=read(progressfile)
 assert gate['Status']=='CLOSED_NATIVE_CASCADE_CLUB_IDENTITIES_AND_PARENTS'and gate['SourceCollectionScopeApproved']and gate['AllParentsResolvedOrExplicitDeferred']
 assert gate['TargetsSHA256']==sha(closedfile)and sig(closed)==sig(progress)
 assert all('PlayersFetched'in c and not c.get('FetchError')for c in progress)
 assert all((B/c['ProfileFile']).exists()and (B/c['RosterFile']).exists()for c in progress)
 scopepins[country]=dict(Clubs=len(progress),GateFile=str(gatefile.relative_to(B)),GateSHA256=sha(gatefile),TargetsSHA256=sha(closedfile),ProgressSHA256=sha(progressfile),NativeWriteAllowed=False)
 scopegaps[country]={k:v for k,v in gate.items() if any(w in k.lower() for w in ['gap','pending','qualification','deferred','fallback'])}
 alltargets+=progress
assert len({str(c['TMID'])for c in alltargets})==len(alltargets)and {c['Country']for c in alltargets}==set(COUNTRIES)
assert not(B/'source-ready-for-root-review.json').exists(),'Preserve completed source handoff'
dump('collected-source-targets.json',alltargets)
z=subprocess.run([sys.executable,'-B',str(B/'analyze_sources.py')],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180);(B/'source-analysis.log').write_text(z.stdout+z.stderr,encoding='utf-8');assert z.returncode==0,z.stdout[-1000:]+z.stderr[-2000:]
summary=read(B/'source-progress.json');facts=read(B/'roster-facts.json');accepted=[x for x in facts if x['AcceptedFactCandidate']]
assert summary['status']=='SOURCE_COLLECTION_COMPLETE'and summary['collected_clubs']==len(alltargets)
players=collections.defaultdict(list)
for x in accepted:players[x['TMID']].append(x)
conflicts=[dict(TMID=t,DOBs=sorted({x['RealDOB']for x in rows}))for t,rows in players.items()if len({x['RealDOB']for x in rows})!=1]
assert not conflicts,('sourceDOBconflict',conflicts)
parents=[dict(TMID=c['TMID'],ParentTMID=c.get('ParentTMID'),Country=c['Country'])for c in alltargets if c.get('ParentTMID')]
summary.update(unique_accepted_player_ids=len(players),SourceDatesRealUnshifted=True,CA_PA_Generated=False,NativeUIDAllocated=False,DatabaseWritten=False)
dump('source-progress.json',summary)
qa=dict(Status='PASS_SOURCE_ONLY_SCOPE_FACTS_CACHE_NOT_NATIVE_IMPORT',ScopePins=scopepins,ScopeGaps=scopegaps,AllCountriesCollected=True,FullNativeAllocationClosed=False,AngliaExcluded=True,UniqueClubTMID=True,RawDatesUnshifted=True,SourceDOBConflicts=conflicts,ParentPairs=parents,MissingPlayersNotForced=True,APIFootballCalls=0,DatabaseWrite=False,NativeWriteAllowed=False)
dump('source-qa.json',qa)
lines=['# Dane kolejnej paczki: piec krajow poza Anglia','', 'Zebrano dane zrodlowe. To nie jest import ani nowa wersja bazy. TEST_X20 pozostaje w testach uzytkownika.','', '| Kraj | Kluby | Wpisy kadrowe | Potwierdzone wiersze | Potwierdzone wypozyczenia |','|---|---:|---:|---:|---:|']
for c in summary['countries']:lines.append('| '+c['Country']+' | '+str(c['CollectedClubs'])+' | '+str(c['Cards'])+' | '+str(c['ConfirmedCandidateRows'])+' | '+str(c['AcceptedLoanRows'])+' |')
lines+=['','Potwierdzone unikalne osoby: '+str(len(players))+'. Braki i odlozone fakty: '+str(summary['source_gaps'])+'. Wiersze wieloklubowe wymagaja rozstrzygniecia przed importem; nie tworzymy duplikatow osob.','', '## Zakres i pozostale ograniczenia','', 'Obsady i kaskady wedlug koncowych tabel poprzednich sezonow sa w competition-prep oraz scope-closures. Pelna gotowosc natywnego przydzialu NIE jest potwierdzona.','', '- Bialorus: zebrano 34 kluby. Dolna niegrywalna pula wymaga zachowania 10 zweryfikowanych istniejacych klubow obok 6 przesunietych. Nie jest to modernizacja wszystkich amatorskich klubow.', '- Belgia: zebrano 61 wspolczesnych klubow. Brakuje danych 16 uprawnionych seniorow do calkowitej modernizacji dawnych lig; istniejace kluby moga pozostac tylko po sprawdzeniu tozsamosci i liczebnosci. Dziewiec rezerw wymaga dozwolonej puli niegrywalnej i zachowania rodzicow. Numer 1301404 jest pucharem, nie pula ligowa; odrzucony.','', 'Szczegoly luk per kraj:']
for country,gaps in scopegaps.items():
 lines+=['',country+':', '```json',json.dumps(gaps,ensure_ascii=False,indent=2),'```']
lines+=['', 'Nie poszukujemy na sile brakujacych zawodnikow; potwierdzone luki pozostaja dla silnika. Daty pozostaja rzeczywiste, bez przesuniecia. Nie losowano CA/PA i nie przydzielano UID. Anglia nie byla zbierana jako liga. Dane wlascicieli wypozyczen moga dotyczyc klubow spoza pieciu krajow.','', 'Cache zachowuje oryginalne odpowiedzi, URL, czas i SHA. Liczba zapytan API-football: 0. Nie zmieniano TEST_X20, zapisu SI, ZIP, gry ani launchera.']
(B/'SOURCE_RAPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
(B/'WZNOWIENIE.md').write_text('# Dane pieciu krajow zebrane\n\nBialorus, Belgia, Austria, Australia, Argentyna. Handoff: source-ready-for-root-review.json, source-qa.json i SOURCE_RAPORT.md. Nie powtarzac pobierania kadr ani zamknietych zrodel. Nie wykonano importu DAT, przydzialu UID ani ocen CA/PA.\n\nPrzed przyszlym importem: potwierdzic wynik testow X20 i wybrac nieruchoma podstawe po SI; rozstrzygnac przypisania wieloklubowe; zamknac dokladne natywne mapowanie pul. Bialorus: 10 lower stand-ins. Belgia: 16 seniorow jako luka modernizacji oraz 9 rezerw do bezpiecznej puli niegrywalnej. Bez tych map writer pozostaje zablokowany. Anglia poza zakresem.\n',encoding='utf-8')
manifest=read(B/'manifest.json');manifest.update(Status='SOURCE_COLLECTION_COMPLETE_FACTS_QA_PASS_NATIVE_NOT_IMPORTED',Counts=summary,VersionReserved=False,NativeWriteAllowed=False);dump('manifest.json',manifest)
files=['manifest.json','collected-source-targets.json','source-progress.json','source-qa.json','roster-facts.json','loan-facts.json','loan-owner-catalogue.json','stadium-catalogue.json','raw-source-index.json','coverage.json','coverage-by-country.csv','collected/global-player-registry.json','SOURCE_RAPORT.md','WZNOWIENIE.md']
sm=dict(Status='SOURCE_COMPLETE_QA_PASS_NO_NATIVEWRITE',ScopePins=scopepins,Files={n:sha(B/n)for n in files},Snapshot='2026-11-14',SourceResponsesOriginalTimeURLSHA256Preserved=True,APIFootballCalls=0,DatabaseWrite=False)
dump('source-manifest.json',sm)
ready=dict(Status='READY_SOURCE_DATA_ONLY_NOT_IMPORTED',Countries=COUNTRIES,Counts=summary,SourceQAFile='source-qa.json',SourceQASHA256=sha(B/'source-qa.json'),SourceManifestSHA256=sha(B/'source-manifest.json'),ReportSHA256=sha(B/'SOURCE_RAPORT.md'),TargetsFile='collected-source-targets.json',TargetsSHA256=sha(B/'collected-source-targets.json'),NativeWriteAllowed=False,UIDAllocation=False,SourceDatesRealUnshifted=True,ExistingUIDsUnchanged=True,DatabaseWritten=False)
dump('source-ready-for-root-review.json',ready)
print(json.dumps(dict(Status=ready['Status'],Clubs=len(alltargets),Cards=len(facts),AcceptedRows=len(accepted),UniqueAcceptedPeople=len(players),Loans=summary['accepted_loan_rows'],SourceGaps=summary['source_gaps'],ReadySHA256=sha(B/'source-ready-for-root-review.json'))),flush=True)
