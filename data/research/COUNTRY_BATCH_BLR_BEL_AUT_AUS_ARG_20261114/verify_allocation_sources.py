from pathlib import Path
import json,hashlib,sys,ast,datetime,collections
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;P=B/'competition-prep'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
countries=['Belarus','Belgium','Austria','Australia','Argentina'];alltargets=[];checks=[]
for country in countries:
 gatefile=B/'scope-closures'/(country+'.json');targetfile=B/'scope-closures'/(country+'-targets.json');gate=read(gatefile);targets=read(targetfile)
 assert gate['Status']=='CLOSED_NATIVE_CASCADE_CLUB_IDENTITIES_AND_PARENTS'and gate['SourceCollectionScopeApproved']and gate['AllParentsResolvedOrExplicitDeferred']and gate['PendingParentCount']==0
 assert gate['TargetsSHA256']==sha(targetfile)and gate['Clubs']==len(targets)
 assert all(r['Country']==country and r['ClubIdentityPending']is False and r.get('ProfileFile')and r.get('SourceIdentityEvidence')for r in targets)
 for f,h in gate['Inputs'].items():assert sha(Path(f))==h,('immutableinputchanged',country,f)
 rawids=read(P/('club-identities-'+country+'.json'));identities={r['TMID']:r for r in rawids};targetids={r['TMID']for r in targets}
 for r in targets:
  i=identities[r['TMID']];assert i['SourceRef']and i['SourceCountryID']==r['SourceCountryID']and i['ParentTMID']==r['ParentTMID']
  rawfile=B/i['SourceRef']['RawFile'];raw=read(rawfile);assert sha(rawfile)==i['SourceRef']['FileSHA256']and hashlib.sha256(raw['body'].encode()).hexdigest()==i['SourceRef']['BodySHA256']
  assert (B/r['ProfileFile']).exists()
  if r['ParentTMID']:assert r['ParentTMID']in targetids and r['ParentIdentityEvidence']
 checks.append(dict(Country=country,Clubs=len(targets),Parents=sum(bool(r['ParentTMID'])for r in targets),GateSHA256=sha(gatefile),TargetsSHA256=sha(targetfile),ProjectionCounts=dict(collections.Counter(str(r['TargetNativeLevel'])for r in targets)),AllIdentityAndParentSourcePinsVerified=True,NativeWriterAllowed=False,FullNativeAllocationClosed=False if country in ['Belarus','Belgium']else None))
 alltargets+=targets
master=read(B/'source-targets.json');assert len(alltargets)==201 and len(master)==201 and len({r['TMID']for r in alltargets})==201
assert {(r['Country'],r['TMID'])for r in master}=={(r['Country'],r['TMID'])for r in alltargets}
assert all(r['Country']!='England'for r in master)
for country in ['Australia']:
 rows=[r for r in master if r['Country']==country];assert sum(r['SourceCountryID']==120 for r in rows)==2
for f in [*B.glob('close_*scope.py'),B/'build_belgium_stage.py']:
 ast.parse(f.read_text(encoding='utf-8-sig'),filename=str(f))
# Keep already-pinned rawv1 immutable; produce a scoped corrected view without stale priorbatchmetadata.
rawreq=P/'native-competition-requirements.json';v=read(rawreq);requirements=v['requirements'];registrations=v['PlayableRegistrations'];assert len(requirements)==37 and len(registrations)==10 and {r['Country']for r in registrations}==set(countries)
regbyid={r['CompetitionUID']:r for r in registrations};scoped=[]
for q in requirements:
 q=dict(q)
 if q['Country']=='Belgium'and q['CompetitionUID']in[3,4]:q['ParentRegistration']=regbyid[8154824];q['ParentCompetitionUID']=8154824
 scoped.append(q)
dump(P/'native-competition-requirements-scoped-r2.json',dict(Status='STATIC_R5_REQUIREMENTS_ONLY_NOT_NATIVE_PROJECTION_PASS',SourceRawV1=str(rawreq),SourceRawV1SHA256=sha(rawreq),ExecutableSHA256=v['ExecutableSHA256'],requirements=scoped,PlayableRegistrations=registrations,RawDeclarations=37,PlayableLevels=10,NominalBothFormSlots=74,GroupedLinks=[dict(ChildUID=3,ParentUID=8154824),dict(ChildUID=4,ParentUID=8154824)],ScopeErrata='Pinnedrawv1prior-adapterBrazilThird/GroupedLinks metadata are outsidecurrentcountries and notacceptedfindings. Scopedr2removesthese, correctsBelgian3/4parent8154824. Actualmin/maxrowsunchanged.37declarations/10registrationsverifiedfromR5files; no countsusedtoinferlimits.',NativeProjectionPerformed=False,NativeWriterAllowed=False,SourcePins=v['SourcePins']))
result=dict(Status='PASS_SOURCE_SCOPE_IDENTITIES_AND_IMMUTABLE_PINS_WITH_EXPLICIT_NATIVE_GAPS',CheckedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),Countries=checks,SourceTargets=201,SourceParents=17,AllScopeAndRawBodyHashesVerified=True,WholeNativeAllocationClosed=False,NativeWriterAllowed=False,DatabaseWritten=False,UIDAllocated=False,EnglandLeagueExcluded=True,APIFootballCalls=0,MassPlayerRostersFetchedByThisAgent=False,NativeRequirements=dict(Declarations=37,RegisteredLevels=10,NominalBothBankSlots=74,Status='STATIC_NOT_EXECUTED_NATIVE_QA',ScopedFile='native-competition-requirements-scoped-r2.json',SHA256=sha(P/'native-competition-requirements-scoped-r2.json')),RequiredFutureNativeWork=['Belarus:10physicalKind0knowncountryThirdstand-ins beside6modernsources;exactThird16+Lower8; historical14to16andactualALTprojection','Belgium:16individualphysicalseniorThirdstand-ins;9B/U23nonplayabletypedKind/parentassignmentbeforeDAT;Fourthminima15/14/14/15','Allcountries:typedidentitymap,Current/effectiveALT/regional/loaderbothbanks/fullnativecountervalidation; noformatrelaxation','Native/SI/newcareer/seasonstatusesindependent; userTEST_X20holidaypendingrootstatus'])
dump(P/'allocation-source-readback.json',result)
report='''# Obsada pięciu krajów: zamknięte źródła, bez importu bazy

Lista do zbierania kadr jest zamknięta: 201 klubów. Każdy kraj ma osobny, niezmienny gate i plik `scope-closures/<Country>-targets.json`. Zweryfikowano wszystkie hashe tych plików, ich wejść oraz surowych profili klubów. Anglia nie jest objęta ligową listą. Nie używano API-Football. Ten agent nie pobierał masowo kadr ani nie zapisywał DAT.

| Kraj | Kluby źródłowe | Rodzice rezerw | Rozmieszczenie źródeł |
| --- | ---: | ---: | --- |
| Australia | 12 | 0 | 8 A-League, 4 dolne pule regionalne |
| Argentyna | 66 | 0 | 20 Premier, 20 Second, 26 nonplayable Third |
| Austria | 28 | 4 | 10 Premier, 12 First, 6 do Regional |
| Białoruś | 34 | 4 | 14 Highest, 14 First, 6 do Second; 10 miejsc dolnej puli wymaga legacy |
| Belgia | 61 | 9 | 18 First, 18 Second, 16 znanych seniorów Third; 16 miejsc Third wymaga legacy, 9 B/U23 poza ligami grywalnymi |

## Źródła i decyzje

Kalendarzowe sezony Białorusi i Argentyny to 2026 z poprzednią zakończoną klasyfikacją 2025. Pozostałe kraje korzystają z 26/27 i zakończonego 25/26. Identyfikatory dostawcy zostały rozstrzygnięte niezależnie po metadanych każdego turnieju; nie stosowano wspólnego odejmowania roku. Bieżących tabel nie używano do kaskady.

Australia: cztery najsłabsze zespoły według zakończonej tabeli 25/26 trafiają do NSW, Brisbane i WA. Auckland i Wellington zachowują rzeczywisty kraj Nową Zelandię (źródłowe countryId120). Nie utożsamiać Auckland FC z historycznym New Zealand Knights.

Argentyna: tabela roczna 2025 łączy wyłącznie obie zakończone fazy regularne, zgodnie z art.24.1/24.2 oficjalnego regulaminu [AFA6616](https://assets1.afa.com.ar/6616.pdf); PDF zachowano. Dziesięć najsłabszych zespołów kontynuujących Premier schodzi niżej, beniaminkowie są chronieni. Drugą ligę uzupełnia pełna kaskada z pierwszeństwem wcześniejszego wyższego poziomu. Czterech nowych uczestników Second potwierdzono w katalogach poprzedniego trzeciego poziomu.

Austria: końcowy porządek grupy mistrzowskiej i kwalifikacyjnej jest globalny (1–6 i 7–12). Surowa tabela TM zachowała anulowane mecze Stripfing; użyto zakończonej tabeli 28 meczów z [RSSSF](https://www.rsssf.org/tableso/oost2026.html), bez ponownego odejmowania kar. Granica kaskady pozostała jednoznaczna. StockA2 ma rzeczywistych uczestników Kind14 z rodzicami (Austria Wien i Salzburg Amateure), dlatego rezerw nie zakazano zbiorczo. Wszystkie cztery współczesne relacje rodziców potwierdzone; rodzice pozostają w top10. Nowe identyfikatory Regionalliga South/North/West nie mają sezonu 25/26; nie stworzono fikcyjnych poprzednich tabel. Nie były potrzebne do dwóch grywalnych lig i sześciu spadków do odpowiednich pul.

Białoruś: skończone tabele 2025 mają 30/34 meczów. Trzech realnych beniaminków Highest zachowano. Cztery źródłowe rezerwy mają rodziców w projektowanej top14. R5 wykazuje historyczną ekspansję formatu 14→16 od 2008; nie deklarowano ALT automatycznie równych Current. Źródłowe34 można zbierać, lecz przed DAT trzeba rozliczyć dziesięć rzeczywistych, jednoznacznych physical legacy TEAM (Kind0, poprawny kraj) do wymaganej dokładnie 16-zespołowej Second League. Nie są one opisane jako zmodernizowane kluby 2026 ani wybrane według pewnego współczesnego rankingu.

Belgia: do tabeli regularnej FFA dołączono zakończone B3AB/BE3B z metadanymi 25/26. Zachowano końcowy oficjalny porządek i punkty. Cały sezon liczy 22+10 meczów; surowe10 to tylko play-off. Nie sumowano punktów z niezgodnych faz. Do Second przechodzą RWDM Brussels, Olympic Charleroi, Knokke, Mons, Roeselare, Tubize-Braine i Belisia Bilzen. Dziewięć B/U23 zachowuje rodziców i źródłowy typ; brak stockowego dowodu ich udziału w belgijskich okresach/barażach nie pozwala uznać ich za seniorów ani przenieść problemu do Third. W katalogu potwierdzono generic Lower COMP1301432/index550; rzeczywiste natywne przypisania i Kind nadal wymagają audytu. Roboczy trop1301404 został odrzucony — jest to Belgian Cup i nie użyto go w żadnym przypisaniu. Źródłowe52 seniorów pozostawia16 miejsc Third do jawnych physical legacy stand-ins, po indywidualnym mapowaniu i zachowaniu czterech minimów Fourth15/14/14/15. Limit dodatkowych źródeł wyczerpano, bez dalszych poszukiwań całego kraju.

## Dowód i ograniczenia

`allocation-source-readback.json` weryfikuje 201 źródłowych tożsamości i 17 rodziców wraz z surowymi odpowiedziami. `native-competition-requirements-scoped-r2.json` zawiera37 deklaracji minimum/maksimum i10 rejestracji lig grywalnych z istniejącego R5, bez wywodzenia limitów z liczby rekordów. Plik r2 usuwa niezwiązane metadane odziedziczone po konfiguracji poprzedniej paczki i poprawnie wiąże belgijskie grupy3/4 z rodzicem8154824. Oryginalny v1 pozostaje niezmienny, ponieważ zamknięcia krajów już przypięły jego hash.

FullNativeAllocationClosed=False. NativeWriterAllowed=False. Przed jakimkolwiek przyszłym zapisem nadal wymagane: pełne mapy fizycznych TEAM, kraje i Kind, rodzice, wszystkie Current/efektywne ALT i Regional po historycznych nadpisaniach loadera, oba banki ograniczeń oraz dokładne rozliczenie luk Białorusi i Belgii. Brak zgody na osłabienie walidacji. Te zamknięcia oznaczają gotowość zbierania danych, nie Native/SI/nową karierę ani sezon PASS. Zaakceptowane TEST_X20, ZIP, zapisy SI/FM i launcher pozostają poza zakresem zapisów.
'''
(P/'ALLOCATION_REPORT.md').write_text(report,encoding='utf-8');print('PASS201SOURCE/17PARENTS/5IMMUTABLEGATES; nativeallocationnotclosed;R5static37/10');print('AUDIT_SHA256',sha(P/'allocation-source-readback.json'))
