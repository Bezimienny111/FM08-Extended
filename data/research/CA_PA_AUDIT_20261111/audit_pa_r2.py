"""R2 provenance and dry scenarios; no database writes and no talent drawing."""
from pathlib import Path
from datetime import date
from collections import defaultdict,Counter
import csv,json,hashlib,unicodedata,statistics,sys,re,ast
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';I=ROOT/'FmLauncher/data/imports';B=R/'CA_PA_AUDIT_20261111';O=B/'R2';O.mkdir(exist_ok=True)
pins={}
def pin(p):pins[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
def js(p):pin(p);return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):
 pin(p)
 with p.open(encoding='utf-8-sig',newline='')as f:return list(csv.DictReader(f))
def dump(name,value):(O/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def save(name,data):
 with(O/name).open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(data[0])if data else['uid']);w.writeheader();w.writerows(data)
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKD',s).casefold()if c.isalnum())
current=rows(B/'players-latest-imported.csv');flat=rows(B/'flat-reused-candidates-review.csv');flatset={int(x['uid'])for x in flat}
young=[x for x in current if x['new_in_this_batch']=='False'and x['age']and int(x['age'])<=21 and 0<int(x['CA'])<=int(x['PA'])and int(x['PA'])-int(x['CA'])<=6]
targets={int(x['uid']):x for x in flat+young}
oldpath=I/'STRASBOURG_INTERNACIONAL_AUDIT_20261106/audit/players.csv'
old={int(x['ID']):x for x in rows(oldpath)}
new={int(x['ID']):x for x in rows(B/'fresh-X10/export/players.csv')}
stock={int(x['ID'])for x in rows(R/'FACEPACK_ALL_NEW_X8_VS_802_20261111/stock802-audit/players.csv')if int(x['PersonIndex'])!=0}
mappingpath=I/'FURTHER_MAPPING_AUDIT_20261106_1433/mapping-audit/mapping-results.json'
mapping=js(mappingpath);byuid=defaultdict(list)
for m in mapping:
 for u in m['current_uids']:byuid[int(u)].append(m)
repairpath=I/'POLAND_U17_REPAIR_20261106/repair-plan.csv';repairs={int(x['UID']):x for x in rows(repairpath)}
southpath=I/'STRASBOURG_INTERNACIONAL_AUDIT_20261106/mapping-audit/mapping-results.json'
south=js(southpath);defensor=next(x for x in south if x['tm_id']=='2619'and x['club_index']==1656)
archive=ROOT/'FM08-Database-Tools/archive/historical-squad-imports'
writer_by_block={1616:'UniversalNativeSquads.cs',1626:'EuropeRemainingNativeSquads.cs',1636:'SouthAmericaNativeSquads.cs',1646:'AsiaAfricaNativeSquads.cs',1656:'FallenGiantsNativeSquads.cs'}
# Newer EA candidates are possible calibration anchors, not proof of original rating provenance.
ea=rows(ROOT/'FMExt/data/fc27_players_all_2026_09_12.csv');eadob=defaultdict(list)
for x in ea:
 if x.get('gender')=="Men's Football":eadob[x['birthdate']].append(x)
classified=[];proofs=[]
for uid,row in sorted(targets.items()):
 n=new[uid];prior=old.get(uid);m=byuid.get(uid,[]);kind='unresolved';basis='';paths=[];detail={}
 identity=prior is not None and tuple(prior[k]for k in ['FirstName','LastName','BirthDate'])==tuple(n[k]for k in ['FirstName','LastName','BirthDate'])
 unchanged=prior is not None and(prior['CA'],prior['PA'])==(n['CA'],n['PA'])
 block=uid//1000000
 if uid in stock:kind='protected_stock802';basis='UID confirmed in stock802; original rating requires separate handling'
 elif identity and unchanged and len(m)==1 and m[0]['source_kind']=='TM':
  kind='source_proven_project_estimate';basis='Exact UID listed by saved historical TM mapping + identical older native identity/ratings + linked generator'
  paths=[str(mappingpath),str(oldpath),str(archive/m[0]['script'])]
  detail=m[0]
 elif identity and unchanged and len(m)==1 and m[0]['source_kind']=='FC27':
  kind='protected_FC27_source';basis='Exact UID in saved FC27 mapping; no automatic reset from team flatness'
  paths=[str(mappingpath),str(oldpath),str(archive/m[0]['script'])];detail=m[0]
 elif identity and unchanged and uid in repairs and block==1646:
  kind='source_proven_project_estimate';basis='Exact UID in U17 identity/source repair + historical AsiaAfrica allocation/generator; ratings unchanged'
  paths=[str(repairpath),str(oldpath),str(archive/'prepare_asia_africa_full.py')];detail=repairs[uid]
 elif identity and unchanged and block==1636 and int(prior['ClubIndex'])==1656 and defensor['status']=='normalized_name_match':
  kind='source_proven_project_estimate';basis='Exact old native UID/identity in SouthAmerica allocation + confirmed Defensor target TM2619 + generator; ratings unchanged'
  paths=[str(southpath),str(oldpath),str(ROOT/'FM08-Database-Tools/archive/historical-south-america/prepare_south_america_full.py')];detail=defensor
 if block in writer_by_block:paths.append(str(ROOT/'FM08-Database-Tools/scratch'/writer_by_block[block]))
 for s in paths:
  p=Path(s);assert p.exists();pin(p)
  if p.suffix=='.py'and 'archive'in p.parts:ast.parse(p.read_text(encoding='utf-8-sig'))
 matches=[e for e in eadob[row['source_dob']]if norm(row['name'])in {norm(e.get('first_name','')+' '+e.get('last_name','')),norm(e.get('common_name',''))}]
 unique={x['player_id']:x for x in matches};e=next(iter(unique.values()))if len(unique)==1 else{}
 c=dict(row,diagnostic_flat=uid in flatset,diagnostic_young_low_margin=uid in {int(y['uid'])for y in young},classification=kind,source_basis=basis,old_identity_equal=identity,old_CA_PA_equal=unchanged,original_age_market_raw_proved=False,execution_authorized=False,source_proven_for_dry_run=kind=='source_proven_project_estimate',evidence_paths=' | '.join(paths),current_EA_exact_DOB_name_ID=e.get('player_id',''),current_EA_OVR=e.get('overall_rating',''))
 classified.append(c);proofs.append(dict(uid=uid,classification=kind,historical_source_detail=detail,old_native=prior,current_native=n,evidence_paths=paths,original_raw_age_market='not_recovered',execution_authorized=False))
assert len(classified)==543
save('provenance-classification.csv',classified);dump('provenance-evidence.json',proofs)
eligible=[x for x in classified if x['classification']=='source_proven_project_estimate']
save('source-proven-estimates-dry-run-scope.csv',eligible)
save('protected-or-unresolved.csv',[x for x in classified if x['classification']!='source_proven_project_estimate'])
# Consolidate all available lottery journals; never call assign_club_talent here.
ledger=[]
v24path=I/'SQUADS_GAPS_20261106/prepared-r3/preparation-report.json';v24=js(v24path)
for c in v24['clubs']:ledger.append(dict(batch='V24',journal=str(v24path),club=c['club'],**c['lottery']))
batchpaths={'H1':'HUNGARY_DATABASE_2627_H1_20261109','B1':'WALES_USA_URUGUAY_2627_B1_20261109','X2':'UKRAINE_TURKEY_X2_20261109','X3':'SWEDEN_SWITZERLAND_X3_20261109','X7':'FOUR_COUNTRY_X7_20261110','X10':'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111'}
for tag,p in batchpaths.items():
 path=R/p/'prepared/talent-lottery.json'
 for x in js(path):ledger.append(dict(batch=tag,journal=str(path),**x))
history=rows(B/'history-all-import-facts.csv');id_to_uids=defaultdict(set)
def sourcekey(v):
 v=str(v)
 while v.startswith('tm:'):v=v[3:]
 return 'tm:'+v if v.isdigit()else v
for x in history:id_to_uids[sourcekey(x['source_player_id'])].add(int(x['uid']))
winners=[]
for x in ledger:
 if x['awarded']:
  k=sourcekey(x['source_player_id']);winners.append(dict(batch=x['batch'],club_uid=x['club_uid'],club=x.get('club',''),source_key=k,source_player_id=x['source_player_id'],known_uids=sorted(id_to_uids.get(k,set())),PA=x['pa'],band=x['band'],journal=x['journal']))
awardclub=defaultdict(set)
for x in winners:awardclub[int(x['club_uid'])].add(x['source_key'])
repeat={str(k):sorted(v)for k,v in awardclub.items()if len(v)>1}
dump('global-talent-draw-register.json',{'known_draws':ledger,'winners':winners,'repeat_different_winners_in_same_club':repeat,'known_only_not_complete_before_V24':True,'draw_function_called_in_R2':False,'legacy_manual_PA155_awards_not_fully_resolved':True})
winneruids={u for x in winners for u in x['known_uids']}
winnersources={x['source_key']for x in winners}
# Build latest row/proof lookup without executing any import script.
paths={'N4':'POLAND_DATABASE_2627_R1_20261108/native-V25-N4/prepared','N7':'POLAND_DATABASE_2627_R1_20261108/native-V25-N7/prepared-r2','I1':'ITALY_DATABASE_2627_IMPORT_I1_20261108/prepared-r4',**{k:v+'/prepared'for k,v in batchpaths.items()}}
nativebybatch={};proofbybatch={}
for tag in {x['batch']for x in classified}:
 p=R/paths[tag];nativebybatch[tag]={int(x['ExistingID']):x for x in rows(p/'native_players.csv')if int(x['ExistingID'])>0}
 pv=js(p/'provenance.json');proofbybatch[tag]={int(x.get('existing_id',-1)):x for x in pv if int(x.get('existing_id',-1))>0}
sys.path.insert(0,str(ROOT/'FMExt/scratch'))
import squad_update_policy as policy
from prepare_english_fc27 import ATTRIBUTES,scale_ca
policy.SOURCE_LEVELS.update({'B1L1':1,'B1L2':2,'B1L3':3,'B1L4':4})
calibration={'Wales':-35,'Uruguay':-15,'Ukraine':-15,'Turkey':-5,'Sweden':-15,'Switzerland':-10,'Scotland':-10,'Slovakia':-20,'Slovenia':-20,'Singapore':-45,'Serbia':-20,'Romania':-20,'South Africa':-35,'Russia':-10,'Poland':-15}
policy.COUNTRY_ADJUSTMENT.update(calibration)
for p in [ROOT/'FMExt/scratch/squad_update_policy.py',ROOT/'FMExt/scratch/prepare_missing_squads.py',ROOT/'FMExt/scratch/prepare_english_fc27.py']:pin(p)
def agegain(age):return 28 if age<=18 else 19 if age<=21 else 10 if age<=24 else 4 if age<=28 else 2
pa_only=[];full=[];afterpa={};afterfull={};attribute_targets=[];full_deferred=[]
for x in eligible:
 uid=int(x['uid']);ca=int(x['CA']);pa=int(x['PA']);dob=date.fromisoformat(x['source_dob']);age=2026-dob.year-((7,1)<(dob.month,dob.day));assert age==int(x['age'])
 guard=uid in winneruids or sourcekey(x['source_player_id'])in winnersources
 newpa=max(pa,min(200,ca+agegain(age)))
 if guard:newpa=pa
 pa_only.append(dict(uid=uid,name=x['name'],club=x['club'],country=x['country'],age=age,CA_before=ca,CA_after=ca,PA_before=pa,PA_after=newpa,gap_before=pa-ca,gap_after=newpa-ca,changed=pa!=newpa,award_guard=guard,formula='max(oldPA,min(200,CA+midpoint_age_gain)); no RNG',execution_authorized=False))
 afterpa[uid]=(ca,newpa)
 n=nativebybatch[x['batch']][uid];pv=proofbybatch[x['batch']][uid]
 if not x['source_level']or x['country']not in calibration:
  full_deferred.append(dict(uid=uid,name=x['name'],reason='source_level_missing'if not x['source_level']else'explicit_country_calibration_missing',CA=ca,PA=pa));continue
 role=(pv.get('known_positions')or[])[0]if pv.get('known_positions')else next((k[3:]for k,v in n.items()if k.startswith('Pos')and v=='20'),None)
 if not role:full_deferred.append(dict(uid=uid,name=x['name'],reason='verified_primary_position_missing',CA=ca,PA=pa));continue
 key='tm:'+pv['source_player_id']
 newca,modelpa,_=policy.abilities(key,x['country'],'B1L'+str(x['source_level']),dob,role)
 # A conditional diagnostic using current generic CA fallback, without fresh talent draws.
 newfullpa=max(pa,newca,min(200,newca+agegain(age)))
 if guard:newca,newfullpa=ca,pa
 afterfull[uid]=(newca,newfullpa)
 full.append(dict(uid=uid,name=x['name'],country=x['country'],club=x['club'],age=age,source_level=x['source_level'],CA_before=ca,CA_after=newca,PA_before=pa,PA_after=newfullpa,gap_before=pa-ca,gap_after=newfullpa-newca,changed=(ca,pa)!=(newca,newfullpa),CA_changed=ca!=newca,PA_changed=pa!=newfullpa,award_guard=guard,EA_anchor_available=bool(x['current_EA_exact_DOB_name_ID']),model='Existing generic CA + midpoint PA; DIAGNOSTIC not approved club-strength model',execution_authorized=False))
 rng=policy.seeded(key,'attributes');attrs={}
 for attr in ATTRIBUTES[:36]+['Determination']:
  base=round(5+newca/20)
  if attr in ['Reflexes','Handling','Kicking','AerialAbility','OneOnOnes']and role!='GK':base=2
  attrs[attr]=max(1,min(20,base+rng.randint(-2,2)))
 attribute_targets.append(dict(uid=uid,name=x['name'],CA_target=newca,attribute_before_image='NOT_EXPORTED; actual native values must be read before any execution',target_attributes=attrs,personality='preserve_existing; not part of this dry run',execution_authorized=False))
save('scenario-PA-only.csv',pa_only);save('scenario-full-CA-PA-diagnostic.csv',full);save('scenario-full-deferred.csv',full_deferred);dump('scenario-full-attribute-targets.json',attribute_targets)
def metrics(data,changes=None):
 v=[]
 for x in data:
  u=int(x['uid']);ca,pa=changes.get(u,(int(x['CA']),int(x['PA'])))if changes is not None else(int(x['CA']),int(x['PA']))
  v.append((ca,pa,pa-ca,int(x['age'])))
 return dict(n=len(v),CA_mean=round(statistics.mean(x[0]for x in v),3),CA_sd=round(statistics.pstdev(x[0]for x in v),3),PA_mean=round(statistics.mean(x[1]for x in v),3),gap_mean=round(statistics.mean(x[2]for x in v),3),gap_min=min(x[2]for x in v),gap_max=max(x[2]for x in v),U21_gap_le6=sum(x[3]<=21 and x[2]<=6 for x in v),PA_ge150=sum(x[1]>=150 for x in v),PA_ge166=sum(x[1]>=166 for x in v),PA_ge181=sum(x[1]>=181 for x in v))
stat=[]
for scope,group in [('all_candidates',classified),('source_proven_estimates',eligible),('young_source_proven',[x for x in eligible if int(x['age'])<=21])]:
 for scenario,change in [('before',None),('PA_only',afterpa),('full_diagnostic_partial',afterfull)]:
  stat.append(dict(scope=scope,scenario=scenario,**metrics(group,change)))
save('scenario-statistics.csv',stat)
clubs=[]
for key in sorted({(x['country'],x['club'])for x in classified}):
 group=[x for x in classified if(x['country'],x['club'])==key]
 for scenario,change in [('before',None),('PA_only',afterpa),('full_diagnostic_partial',afterfull)]:
  clubs.append(dict(country=key[0],club=key[1],scenario=scenario,**metrics(group,change)))
save('scenario-club-statistics.csv',clubs)
# Preserve report-source hashes; no public files are written.
db=ROOT/'Dane/db/TEST_X10';source_before=js(B/'fresh-X10/source-pins.json')['source_after'];dbnow={str(p.relative_to(db)):hashlib.sha256(p.read_bytes()).hexdigest()for p in db.rglob('*')if p.is_file()}
summary=dict(scope_candidates=len(classified),flat_candidates=len(flat),young_low_gap=len(young),additional_young_not_flat=len(set(targets)-flatset),classification=dict(Counter(x['classification']for x in classified)),confirmed_estimates_flat=sum(x['diagnostic_flat']for x in eligible),confirmed_estimates_extra_young=sum(not x['diagnostic_flat']for x in eligible),current_EA_anchor_available=sum(bool(x['current_EA_exact_DOB_name_ID'])for x in classified),PA_only_rows=len(pa_only),PA_only_changed=sum(x['changed']for x in pa_only),full_rows=len(full),full_deferred=len(full_deferred),full_changed=sum(x['changed']for x in full),full_CA_changed=sum(x['CA_changed']for x in full),full_PA_changed=sum(x['PA_changed']for x in full),known_lottery_draws=len(ledger),known_lottery_awards=len(winners),unique_awarded_clubs=len(awardclub),repeated_different_winners=repeat,scenario_new_awards=0,public_DB_unchanged_since_R1_readonly_audit=dbnow==source_before,execution_authorized=False,policy_approved=False,old_raw_age_market_recovered=False,source_estimate_provenance='Exact saved UID mapping or explicit repair/source allocation + static generator, corroborated by unchanged older native identity and CA/PA. Not original CSV row recovery.')
dump('summary.json',summary);dump('input-manifest.json',{'hashes':pins,'public_source_hashes':dbnow,'public_source_unchanged':dbnow==source_before,'no_database_or_pipeline_writes':True,'no_network':True,'no_new_random_talent_draws':True})
def tab(v):return '|'+v['scope']+'|'+v['scenario']+'|'+str(v['n'])+'|'+str(v['CA_mean'])+'|'+str(v['PA_mean'])+'|'+str(v['gap_mean'])+'|'+str(v['U21_gap_le6'])+'|'+str(v['PA_ge166'])+'|'
report=f"""# Audyt PA — etap R2, proweniencja i suche scenariusze

**Rozstrzygnięto pochodzenie 543 unikalnych kandydatów: 542 to wcześniejsze projektowe modele ocen z danych Transfermarkt, jeden ma źródło FC27. Nie zapisano żadnej oceny do bazy.** Lista źródłowo zakwalifikowana służy do audytu/symulacji; nie jest zatwierdzeniem wykonania korekty. Reguła preserve dla konkretnych UID nadal wymaga decyzji.

## Zakres i wynik klasyfikacji

Punkt wyjścia: 510 osób w 19 klubach z diagnostyki płaskich reuse (11 klubów X10 i 8 wcześniejszych). Dodatkowo sprawdzono wszystkich młodych reuse do21lat z dodatnim PA−CA≤6 w zbiorze23364ostatnio importowanychUID:203osoby, w tym170już w flat i33dodatkowe. Łącznie543. Oryginalne PA0/negativePA i PERSON0 wyłączono z tego kryterium, nie interpretując ich jako zwykłych punktów potencjału.

- 529 osób ma **dokładny UID** wpisany do zachowanego mapping-results.json ze źródłem TM. To nie samo dopasowanie numeru bloku ani nazwiska.
- Kolejne7ma dokładneUIDw naprawie źródła PolandU17. Pierwotny generator AsiaAfrica zawiera TM23136podpisany błędniePSM; raport naprawy wskazuje właściwych graczy. Naprawa klubów zachowała ich wcześniejsze oceny.
- Kolejne6ma potwierdzony ślad: UID w historycznym audycie Defensor, importer SouthAmerica i jego wyłączny zakres1636, katalog TM2619 i statyczny generator. To osobny jawny rodzaj dowodu, nie polecurrent_uids z katalogu europejskiego.
- **Jeden chroniony FC27: Luka Ilić UID1603002695, Red Star,115/121.** Trafił do diagnostyki, ponieważ również miałCA115. Nie wolno z tego powodu przeliczać go jak starego generycznegoTMprofilu.
- W tym zbiorze brak stock802 i brak nierozstrzygniętej klasy pochodzenia modelu. Nie oznacza to, że wszystkie oceny są indywidualnie wiarygodne albo że odtworzono każdą historyczną odpowiedź API.

Dla wszystkich543osób imię,nazwisko,DOB orazCA/PA są identyczne w historycznym audycie V24 i świeżymX10. Statyczny kod generatorów dowodzi, że były modelami: TM był źródłem osób i faktów, nie gotową oceną skautingowąCA/PA. Brakuje pierwotnych plikówCSV oraz surowego age/market_value dla każdego rekordu. **Pochodzenie modelu jest rozstrzygnięte; konkretne nullAPI nie są.** Załączony provenance-evidence.json pokazuje tę granicę perUID.

Znaleziono{summary['current_EA_anchor_available']}bieżących jednoznacznych kandydatur EA o identycznym pełnym imieniu/nazwisku i rzeczywistymDOB. Zaznaczono je jako możliwe kotwice późniejszej korekty, bez automatycznej podmiany ocen. Sama obecność w nowszymEA nie dowodzi, że pierwotna ocena pochodziła zEA.

## Co dokładnie jest nie tak

509z510flat to modele projektoweTM, jeden toFC27. Po dołączeniu33młodych poza flat daje542kandydatów modelowych. Nastolatek nie powinien otrzymywać marginesu dorosłego tylko dlatego, że stary importer użył p.age or25. Jeszcze inny stary generator FallenGiants w ogóle nie wykorzystuje wieku doPA: generate_attributes dajeCA+losowe3–16, a seed=hash((name,DOB,club)) zależy od procesuPythona. To wyjaśnia kolejną grupę młodych z niskim marginesem; obecna politykaSHA256nie naprawia tych zachowanych wyników.

„Zachowaj istniejące” musi odróżniać wcześniejszą ocenę źródłową od poprzedniego fallbacku. To rozstrzygnięcie nie daje zgody na masowy reset. Tę542-osobową listę można rozpatrywać jako konkretny zakres oddzielnej korekty, po zatwierdzeniu polityki i wyniku.

## Suchy wariant A: tylko PA

Dla źródłowo potwierdzonych modeli przyjęto **diagnostycznie środki bieżących przedziałów wieku**, bez nowego losowania: do18lat+28,19–21+19,22–24+10,25–28+4,29+ +2. Wiek wyliczono z rzeczywistegoDOB na1VII2026. PA_after=max(PA_before,min(200,CA_before+gain)). ZachowanePA nigdy nie maleje; CA, atrybuty, dane osoby i kontrakt pozostają.

To nowy, jawny wariant symulacji, NIE zatwierdzona produkcyjna polityka. Dotyczy542osób, zmieniłby **{summary['PA_only_changed']} PA**. Nie dodaje nagród talentu. Oznaczań EA/stock nie przelicza. Wynik usuwa zaniżony margines młodych w tym zakresie, ale **pozostawia jednakoweCAi atrybuty**. Nie naprawia samodzielnie siły całej kadry.

## Suchy wariant B: CA/PA i cele atrybutów

Dla wierszy z jawnym poziomem źródłowym i obecną kalibracją kraju odtworzono aktualny generyczny modelCA z jego dotychczasowym SHA256i pozycją, aPA ustawiono jako max(starePA,noweCA,noweCA+środkowyprzyrostwieku), limit200. Bez wywołania assign_club_talent. To **diagnostyka skutku obecnego modelu**, nie nowy model jakości klubu.

Wariant wylicza **{summary['full_rows']} osób**, pozostawia **{summary['full_deferred']}**bez pełnego przeliczenia z powodu braku jawnego poziomu/kalibracji. Dotyczyłby{summary['full_changed']}par ocen, w tym{summary['full_CA_changed']}zmianCAi{summary['full_PA_changed']}zmianPA. Nie wpisano cichego domyślnego wariantuWłoch/nieznanego poziomuPolski.

Przygotowano37docelowych atrybutów na osobę z istniejącego algorytmu modelu (36podstawowych+Determination), z osobnymseedemattributes; osobowość miałaby pozostać. **Nie przedstawiamy tego jako gotowego patcha atrybutów:** odczytCSVnie zawiera pełnych rzeczywistych atrybutów przed zmianą, więc przed wykonaniem potrzebny jest ich niezależny pełny eksport i porównanie. CSVdla reuse zawiera także niewykonane propozycje atrybutów; nie uznano ich za rzeczywistewartościbazy.

WariantB pokazuje, że da się zróżnicować dane szybko bez ponownego pobierania osób. Nadal nie uwzględnia siły klubu ani indywidualnych osiągnięć. Przed produkcyjną korektą należy ustalić kotwice: zweryfikowaneEA/przejrzane oceny indywidualne oraz jawny przedział siły klubów, a dopiero brakujące profile wypełniać deterministycznym rozrzutem. Nie należy podnosić wszystkich w mocnym klubie o tę samą liczbę.

## Porównanie przed/po

| Zakres | Wariant | Liczba | Średnie CA | Średnie PA | Średni PA−CA | U21 z gap≤6 | PA≥166 |
|---|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(tab(v)for v in stat)}

Full_diagnostic_partial zawiera cały zakres, lecz dla jawnie odłożonych wierszy zachowuje wartości sprzed symulacji. Nie wylicza rankingów źródłowych osób, których nie sprawdzono. Pełnebefore/afterperUID: scenario-PA-only.csv i scenario-full-CA-PA-diagnostic.csv; perklub: scenario-club-statistics.csv.

## Rejestr talentów i zakaz ponownego losowania

Zebrano **873zapisane oceny kwalifikacji klubów i130nagród w130klubach**:V24,H1,B1,X2,X3,X7,X10. W dostępnych dziennikach nie ma przypadku dwóch różnych wygranych osób w tym samymklubie. To konsolidacja zapisanychwyników, nie nowe losowanie. Rejestr wskazuje źródłowyIDi UID, gdy dostępna jest jednoznaczna ścieżka. Dla dawnych nagród/przedV24(wtym historycznego ręcznegoPA155) kompletność nie jest dowiedziona.

Oba scenariusze wykonują **0nowych losowańklubowych**, zachowują starePA jako minimum i dodatkowo nie zmieniają znanychzwycięzców. Ewentualne przyszłe losowanie wymagałoby niezależnego globalnegorejestru już rozpatrzonych klubów i osób. Nie wolno interpretować braku wpisu w starych niekompletnych danych jako nowej darmowej szansy.

## Dalsza decyzja

Użytkownik zlecił audyt, a nie zapis korekty. Nie ma nowejbazy, zmian wX10, importerze ani pipeline. Najszybszy bezpieczny wybór to osobne zatwierdzenie zakresu źródłowo udowodnionych dawnych szacunków i wariantuPA-only, jeżeli celem jest najpierw zapas rozwoju. PełneCA/PA/atrybuty wymagają dodatkowo zatwierdzonych kotwic klubów i jakości indywidualnej oraz rzeczywistego eksportu atrybutówprzedzmianą. Suchy wariantBnie jest takim zatwierdzonym modelem.

W żadnym wariancie nie tworzymy nowych osób, nie zmieniamyUID, umów, składów i ligi, nie dodajemy fikcyjnych potencjalnychgwiazd. TEST_X10 pozostaje nietknięta; jej obserwowane pliki są{'zgodne'if summary['public_DB_unchanged_since_R1_readonly_audit']else'nieidentyczne'}z pinami wcześniejszego odczytuR1.
"""
(O/'RAPORT_R2.md').write_text(report,encoding='utf-8')
(O/'WZNOWIENIE.md').write_text('# R2 audytu PA — gotowy, bez zmian DB\n543kandydatów=510flat+33młodych poza flat.542źródłowo potwierdzone projektowemodeleTM,1chronionyFC27LukaIlić. DokładneUIDw historycznychmapach/naprawach i identyczne stare/bieżące dane. Pierwotne raw age/market nadal nieodtworzone.\nSuchewarianty: PA-only z jawnym środkiem przedziałów wieku, fullcurrentgenericCA/PA+37celówatrybutów dla jawnychpoziomów/krajów. Produkcyjnapolityka i konkretneUID do zmiany NIEzatwierdzone.873zapisane kwalifikacje/130nagród w globalnym rejestrze;0nowychlosowań. OsobneCSV,summary,inputmanifest. TEST_X10nietknięta. RAPORT_R2.md.\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=True))
