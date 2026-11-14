from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone
import csv,json,hashlib,statistics,sys
sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent;P=B/'prepared';ROOT=Path('J:/FM08dev')
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pins(p):return{str(f.relative_to(p)):sha(f)for f in sorted(p.rglob('*'))if f.is_file()}
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def save(p,v):
 with p.open('w',encoding='utf-8-sig',newline='')as f:w=csv.DictWriter(f,fieldnames=list(v[0]));w.writeheader();w.writerows(v)
m=read(P/'manifest.json');full=read(P/'full-native.json');verified=read(P/'independent-verification.json');rating=read(B/'ratings-patch-independent.json');qa=read(B/'root-selection-qa/regression.json')
assert full['status']==verified['status']==rating['status']=='pass'
assert qa['Status']=='NUMERIC_SELECTION_REGRESSION_PASS' and not qa['NewRegressions'] and not qa['CurrentSixCountryFailures']
source=Path(m['source']);output=Path(rating['output'])
assert Path(full['output'])==Path(rating['source'])
assert pins(source)==full['source_hashes']and pins(output)==rating['output_hashes']
audit={int(r['ID']):r for r in rows(B/'ratings-audit-after/players.csv')};beforeaudit={int(r['ID']):r for r in rows(B/'audit/players.csv')}
assert audit[1608001583]==beforeaudit[1608001583],'Deferred EricVoufack source player changed'
ps=rows(P/'native_players.csv');ids=rows(P/'identities.csv');proof=read(P/'provenance.json');subjects={int(r['id90']):r for r in full['subjects']};clubs={r['TeamIndex']:r for r in rows(P/'club_map.csv')};ledger=[];talents=[]
assert len(ps)==len(ids)==len(proof)==len(subjects)==m['counts']['prepared']
for p,i,v in zip(ps,ids,proof):
 u=subjects[int(i['SubjectID'])]['uid'];a=audit[u]
 assert(int(a['CA']),int(a['PA']))==(int(p['CA']),int(p['PA'])),('final_CA_PA',u)
 assert a['BirthDate']==i['TargetDOB']and int(a['ClubIndex'])==int(i['OwnerClubIndex']),('final_DOB_owner',u)
 c=clubs[i['PlayingClubIndex']]
 record=dict(TMID=v['TMID'],UID=u,SubjectID=i['SubjectID'],FirstName=p['FirstName'],LastName=p['LastName'],ClubUID=int(c['ClubUID']),Club=c['ClubName'],Country=c['Country'],RealDOB=v['source_dob'],NativeDOB=i['TargetDOB'],PlayingTEAM=int(i['PlayingClubIndex']),OwnerTEAM=int(i['OwnerClubIndex']),New=int(i['ExistingID'])<0,CA=int(a['CA']),PA=int(a['PA']),ModelVersion=v['model_version'],SeedUID=v['seed_uid'],AbilitySource=v['ability_source'],TalentAward=bool(v.get('talent_estimate')),Source=v['bio_source'])
 ledger.append(record)
 if record['TalentAward']:talents.append(record)
assert len({r['UID']for r in ledger})==len(ledger)and len({r['TMID']for r in ledger})==len(ledger)
assert sum(r['New']for r in ledger)==m['counts']['new'] and len(read(P/'deferred.json'))==m['counts']['deferred']
save(B/'final-native-player-UID-ledger.csv',ledger);dump(B/'talent-native-UID-ledger.json',talents)
scope=defaultdict(list)
for r in ledger:scope[r['Country']].append(r)
summary=[]
for country,rs in scope.items():
 ca=[r['CA']for r in rs];pa=[r['PA']for r in rs];summary.append(dict(Country=country,Clubs=sum(c['Country']==country for c in clubs.values()),Players=len(rs),New=sum(r['New']for r in rs),CAmin=min(ca),CAmax=max(ca),CAmean=round(statistics.mean(ca),2),CAstd=round(statistics.pstdev(ca),2),DistinctCA=len(set(ca)),PAmin=min(pa),PAmax=max(pa),MeanDevelopmentGap=round(statistics.mean(y-x for x,y in zip(ca,pa)),2)))
save(B/'final-coverage-ratings.csv',summary)

structure=read(B/'structure-root/root-independent-verification.json')
assert structure['status']=='PASS_PRIVATE_NATIVE_STRUCTURE_NOT_SI_OR_RUNTIME' and len(structure['both_forms'])==58
freeze=read(B/'source-freeze.json')
assert pins(Path(freeze['frozen']))==freeze['hashes']and pins(Path(freeze['source']))==freeze['hashes'],'X15 source drift'
assert read(B/'full-N4-identity-preflight.json')['status']=='PASS_NO_NEW_IDENTITY_COLLISION'
negative=read(B/'negative-tests.json');assert len(negative)==6 and all(v['rejected']for v in negative)
pilot=read(Path(m['pilot_verification_path']));assert pilot['status']=='pass'and sha(Path(m['pilot_verification_path']))==m['pilot_verification_sha256']
meta=dict(people=len(ledger),new=sum(r['New']for r in ledger),reused=sum(not r['New']for r in ledger),loans=len(rows(P/'loans.csv')),clubs=len(clubs),actor_clubs=m['counts']['actor_clubs'],partial_extra_clubs=14,legacy_rating_repairs=rating['scoped_UIDs'],legacy_CA_changed=rating['CA_changed'],legacy_PA_changed=rating['PA_changed'],new_talent_awards=len(talents),deferred=len(read(P/'deferred.json')),source_gaps=len(read(P/'source-gaps.json')))
readback=dict(status='pass',rated_output=str(output),rated_hashes=pins(output),prepared_manifest_sha256=sha(P/'manifest.json'),prepared_players_sha256=sha(P/'native_players.csv'),prepared_identities_sha256=sha(P/'identities.csv'),prepared_loans_sha256=sha(P/'loans.csv'),source_freeze_sha256=sha(B/'source-freeze.json'),roster_inverse_sha256=sha(P/'independent-verification.json'),ratings_inverse_sha256=sha(B/'ratings-patch-independent.json'),selection_qa_sha256=sha(B/'root-selection-qa/regression.json'),ledger_sha256=sha(B/'final-native-player-UID-ledger.csv'),all_imported_CA_PA_DOB_owner_verified=True,UID_and_TMID_unique=True,original_public_X15_and_frozen_X15_hashes_unchanged=True,deferred_EricVoufack1608001583_all_audit_fields_unchanged=True,counts=meta,recorded_at=datetime.now(timezone.utc).isoformat())
dump(B/'final-readback.json',readback)
carry=read(Path(freeze['frozen'])/'next-batch-fixes.json')
newgaps=dict(inherited_unresolved=carry,current_deferred_profiles=read(P/'deferred.json'),source_gaps=read(P/'source-gaps.json'),loan_owner_gaps=read(B/'foreign-owner-finalization.json')['deferred_source_owners'],foundation_year_unconfirmed=['MaccabiKiryatGat'],legal_identity_distinction='Galway official sporting continuity1937 retained; new legal project2013 acknowledged; Cork existing evidence unchanged',partial_club_rosters=[x for x in read(P/'coverage.json')if x['Confirmed']==0])
dump(B/'next-batch-fixes.json',newgaps)
status=dict(status='PRIVATE_NATIVE_VERIFIED_READY_FOR_ROOT_PUBLICATION_REVIEW',private_output=str(output),planned_public_output='J:/FM08dev/Dane/db/TEST_X16',source=str(source),source_X15_accepted_SI=True,source_X15_accepted_new_career=True,source_X15_season='USER_PASS_2008_German_3Liga',counts=meta,native=True,SI=False,new_career=False,season=False,source_hashes=pins(source),output_hashes=pins(output),structure=structure,global_selection_qa=dict(status=qa['Status'],conditions=qa['TotalChecks'],new_regressions=len(qa['NewRegressions']),new_country_null=len(qa['NewCountryNullTeams']),runtime_test=False),root_selection_qa_path=str(B/'root-selection-qa/regression.json'),final_readback=str(B/'final-readback.json'),final_ledger=str(B/'final-native-player-UID-ledger.csv'),metadata='Private DAT verified. Inherited X15/roster-db metadata/XML must be replaced by root when publishing X16.',public_database_mutated=False,EXE_modified=False,recorded_at=datetime.now(timezone.utc).isoformat())
status['private_NATION_reader_fix']=dict(proof=str(B/'nation-reader-fix/verification.json'),proof_sha256=sha(B/'nation-reader-fix/verification.json'),binary=str(B/'tools/FM08_Database_Editor.exe'),binary_sha256=sha(B/'tools/FM08_Database_Editor.exe'),all229_maps_unchanged=True,all1608_raw_reuse_unchanged=True,pilot_subset_proof=str(B/'pilot-subset-reader-fix-proof.json'))
dump(B/'native-ready-for-root-review.json',status)
manifest=read(B/'manifest.json');manifest.update(status=status['status'],current_native_stage=status);dump(B/'manifest.json',manifest)
report=['# TEST_X16 ? sze?? kraj?w','', 'Prywatny wynik do kontroli i publikacji root: '+str(output),'', 'Native PASS. Zapis SI, nowa kariera i sezon X16 pozostaj? NIEPRZETESTOWANE. Podstawa X15 po SI/nowej karierze i sezonie2008 zosta?a zachowana bez zmian.','', 'Zakres: Korea Po?udniowa, Kolumbia, Izrael, Islandia, Irlandia P??nocna, Irlandia.181 rzeczywistych klub?w:167 ?r?d?owych kadr oraz14 jawnie cz??ciowych klub?w granicznych (NI trzeci poziom12, irlandzkie zaplecze2).','', 'Klasyczny format: Korea14+12; Kolumbia18+18; Izrael12+12; Islandia10+12 dla form0 oraz12+12 dla form1, zachowana natywna ekspansja; NI16+12+12; Irlandia12+10.170 miejsc grywalnych form0 /172 form1. Pozosta?e11/9 klub?w w odpowiedniej dolnej puli. Nie zmieniano EXE ani regu? silnika.','', 'Profile: '+str(meta['people'])+' potwierdzonych zawodnik?w, '+str(meta['new'])+' nowych UID, '+str(meta['reused'])+' reuse. '+str(meta['loans'])+' aktywnych ?r?d?owo wypo?ycze?, tak?e mi?dzy krajami, z kanonicznym w?a?cicielem klubu; bez obowi?zku wykupu i bez zgadywania ko?c?w lub cen. Daty ?r?d?owe zachowano; natywne starty wypo?ycze? stosuj? odziedziczon? techniczn? granic?1VII2007.','', 'CA/PA: modelv2 z du?ym odtwarzalnym rozrzutem. Wiarygodne ?r?d?a, przyj?te wcze?niej profile i talenty chronione. '+str(meta['legacy_rating_repairs'])+' dowiedzionych starszych szacunk?w zmieniono wy??cznie w s?owach CA/PA ('+str(meta['legacy_CA_changed'])+'CA /'+str(meta['legacy_PA_changed'])+'PA), bez obni?ania PA. Wszystkie pozosta?e bajty cech, osobowo?ci, um?w i to?samo?ci zachowane. Nowe przyznania talentu: '+str(len(talents))+'.','', 'Struktura:33 nowe TEAM/33FAMILY/124stadiony.462 rodziny projektu SugarDaddyOFF, jawny zapis i niezale?ny odczyt.33 luki stadionowe bez wymy?lonych miejscowo?ci.','', 'To?samo?ci: AlianzaFC poprawnie309345AlianzaPetrolera/Colombia, nie5512639Uruguay. RealCundinamarca8830832Valledupar, nieCartagena. Gwangju i Gimcheon oddzielne. Nowe m.in. KerryFC, TreatyUnited, StrabaneAthletic; stare podmioty zachowane. Galway przyjmuje oficjaln? sportow? histori?1937 z odnotowaniem nowego projektu prawnego2013. Niepotwierdzonego roku za?o?enia KiryatGat nie wpisywano.','', 'W?a?ciciele: Buriram/Nacional oraz angielskie kluby macierzyste rozstrzygni?te po dowodach; nie tworzono fikcyjnych pierwszych dru?yn U21. Nierozstrzygni?ty Ludogorets od?o?ony wy??cznie dla dotkni?tego zawodnika. Od?o?enia: '+str(meta['deferred'])+' profili i '+str(meta['source_gaps'])+' ??cznych luk. Brakuj?cych os?b/DOB nie szukano na si??; cz??ciowe kadry pozostawiono silnikowi. Poprzednie od?o?enia Kolding/Voufack/Cejudo i role rezerw zachowane w next-batch-fixes.json.','', 'Techniczne backfill NI7slot?w korzysta z zachowanego natywnego katalogu i raportu ka?dego UID; nie oznacza potwierdzenia wsp??czesnej ligi tych klub?w. Nie dopisano niezweryfikowanych nowych klub?w dla wype?nienia puli.','', 'Walidacja:6 negatywnych kontroli PASS; pilot i pe?ny odczyt/ca?e PEOPLE+SERVER+CLIENTinverse PASS; globalny N4 preflight bez kolizji;0 konflikt?w przysz?ych transfer?w.727-wordplan patch ma pe?ny PEOPLEinverse, por?wnanie wszystkich wierszy audytu i brak zmiany tabel89B/17B. Ko?cowy ledger ponownie por?wnano z CA/PA/DOB/w?a?cicielem ka?dego importowanego UID.','', 'Selektory:58 obuform dla nowych6kraj?w oraz215 globalnych warunk?w liczbowych PASS,0 nowych regresji/country-null. To kontrola danych z wcze?niej potwierdzonymi overlayami, nie runtime PASS wszystkich kraj?w.','', 'Dalej: root przygotowuje now? TEST_X16, metadane/XML/ZIP z dok?adnie zweryfikowanych DAT. Jeden wsp?lny test SI i nowej kariery wszystkich6 kraj?w; osobny sezon Islandii powinien zachowa? zmian?10?12.']
(B/'RAPORT.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
(B/'WZNOWIENIE.md').write_text('# TEST_X16 ? Native ready do root review\n\n'+str(output)+'\n\n'+str(meta)+'\n\nNativePASS; SI/kariera/sezonX16PENDING. final-readback.json i native-ready-for-root-review.json przypinaj? rated-db i wej?cia. ?r?d?owa X15/ZIP i gra nietkni?te. Root publikuje po review i podmienia odziedziczone metadane.\n',encoding='utf-8')
artifacts=[B/'RAPORT.md',B/'WZNOWIENIE.md',B/'native-ready-for-root-review.json',B/'final-readback.json',B/'final-native-player-UID-ledger.csv',B/'talent-native-UID-ledger.json',B/'next-batch-fixes.json',P/'manifest.json',P/'independent-verification.json',B/'ratings-patch-independent.json',B/'root-selection-qa/regression.json',B/'typed-family-witness-proof.json',B/'full-N4-identity-preflight.json',B/'nation-reader-fix/verification.json',B/'nation-reader-fix/build-manifest.json',B/'pilot-subset-reader-fix-proof.json',B/'tools/roster-build-manifest.json']
dump(B/'final-artifact-pins.json',{str(p.relative_to(B)):sha(p)for p in artifacts})
print('READY_FOR_ROOT',meta,str(output))
