"""Finalize only from successful independently verified private roster+ratings phases."""
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone
import csv,json,hashlib,statistics
B=Path(__file__).resolve().parent;P=B/'prepared'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pins(d):return{str(p.relative_to(d)):sha(p)for p in sorted(d.rglob('*'))if p.is_file()}
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write(p,v,cols=None):
 with p.open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.DictWriter(f,fieldnames=cols or list(v[0]));w.writeheader();w.writerows(v)
def main():
 m=read(P/'manifest.json');full=read(P/'full-native.json');verified=read(P/'independent-verification.json');rating=read(B/'ratings-patch-independent.json')
 assert full['status']==verified['status']==rating['status']=='pass'
 source=Path(m['source']);output=Path(rating['output']);assert Path(full['output'])==Path(rating['source'])
 assert pins(source)==full['source_hashes']and pins(output)==rating['output_hashes']
 audit={int(x['ID']):x for x in rows(B/'ratings-audit-after/players.csv')}
 ps=rows(P/'native_players.csv');ids=rows(P/'identities.csv');proofs=read(P/'provenance.json');subjects={int(x['id90']):x for x in full['subjects']};ledger=[];talents=[]
 assert len(ps)==len(ids)==len(proofs)==len(subjects)==7533
 for p,i,proof in zip(ps,ids,proofs):
  uid=subjects[int(i['SubjectID'])]['uid'];actual=audit[uid]
  assert(int(actual['CA']),int(actual['PA']))==(int(p['CA']),int(p['PA'])),('final ratings',uid)
  assert actual['BirthDate']==i['TargetDOB']and int(actual['ClubIndex'])==int(i['OwnerClubIndex'])
  v=dict(TMID=proof['TMID'],UID=uid,SubjectID=i['SubjectID'],FirstName=p['FirstName'],LastName=p['LastName'],RealDOB=proof['source_dob'],NativeDOB=i['TargetDOB'],PlayingTEAM=int(i['PlayingClubIndex']),OwnerTEAM=int(i['OwnerClubIndex']),New=int(i['ExistingID'])<0,CA=int(actual['CA']),PA=int(actual['PA']),ModelVersion=proof['model_version'],SeedUID=proof['seed_uid'],AbilitySource=proof['ability_source'],TalentAward=bool(proof.get('talent_estimate')),Source=proof['bio_source'])
  ledger.append(v)
  if v['TalentAward']:talents.append(v)
 assert len({v['UID']for v in ledger})==len(ledger)and len({v['TMID']for v in ledger})==len(ledger)
 write(B/'final-native-player-UID-ledger.csv',ledger);dump(B/'talent-native-UID-ledger.json',talents)
 clubs=rows(P/'club_map.csv');classrows=rows(P/'rating-source-classification.csv');counts=Counter(x['Class']for x in classrows);defer=read(P/'deferred.json');gap=read(P/'source-gaps.json');guard=read(B/'preserved-unresolved-source-records.json')
 status=dict(status='PRIVATE_NATIVE_VERIFIED_READY_FOR_ROOT_PUBLICATION_REVIEW',source=str(source),private_output=str(output),planned_public_output=str(B.parents[3]/'Dane/db/TEST_X14'),counts=m['counts'],native=True,SI=False,new_career=False,season=False,source_hashes=pins(source),output_hashes=pins(output),root_structure_verification=str(B/'structure-regional-root/root-independent-verification.json'),roster_inverse=str(P/'independent-verification.json'),ratings_inverse=str(B/'ratings-patch-independent.json'),all7533final_CA_PA_DOB_owner_readback=True,actual_new_UIDs=sum(x['New']for x in ledger),classes=dict(counts),new_talent_awards=len(talents),unresolved_source_records_preserved=len(guard['records']),deferred_reasons=dict(Counter(x['Reason']for x in defer)),random_seed='SHA256(modelversion|stable_sourceUID_or_existingUID|purpose)',rerolls=0,public_database_mutated=False,recorded_at=datetime.now(timezone.utc).isoformat())
 status['planned_public_output']='J:/FM08dev/Dane/db/TEST_X14'
 dump(B/'native-ready-for-root-review.json',status)
 manifest=read(B/'manifest.json');manifest['current_native_stage']=status;dump(B/'manifest.json',manifest)
 lines=['# X14 — Portugalia, Peru, Norwegia i przegląd luk Polski','',
 'Prywatny wynik natywny zweryfikowany; publikacja TEST_X14 wymaga przeglądu root. SI, nowa kariera i sezon pozostają PENDING dla nowej bazy.','',
 '## Zakres','',
 '- 292 kluby z bieżących katalogów:112 Portugalia,144 Norwegia,36 Peru; 291 z potwierdzonymi osobami i1 jawnie pusty.',
 '- Klasyczne grywalne obsady: Portugalia16+16+4×14=88; Norwegia14+16+4×14=86; Peru12. Razem186. Pozostałe106 klubów w niższych pulach; nie są deklarowane jako grywalne poziomy FM08.',
 '- 7533 graczy:1149 ponownie używanych i6384 nowych;289 kompletnych aktywnych wypożyczeń, także spoza tych krajów. Nie ustawiamy obowiązkowego wykupu ani nieznanej opcji/kwoty.',
 '- 86 nowych TEAM (74core+12foreign-owner),61 rodzin,187 stadionów. Własne rodziny wcześniej istniejących rezerw zachowane; kontrakt RosenborguII wskazuje natywną rodzinę1376/1025 przy własnej rodzinie2336.',
 '- Wszystkie385 projektowych rodzin Sugar Daddy OFF, jawny natywny odczyt root.',
 '- Polska:126 klubów/2456 poprzednio potwierdzonych UID zweryfikowanych w X11;16 pustych źródłowych datDOB pozostało lukami. Zero ponownego masowego pobierania, pierwszeństwo90minut, brak nowych wymyślonych profili.','',
 '## CA i PA','',
 '- Model squad-spread-2026-27-v2: deterministyczny seed UID+wersja+cel; wiek, realny poziom i kraj; dodatni zapas rozwoju zależny od wieku. PA>=CA.',
 '- Wiarygodne oceny natywne/FC27, stare talenty i naprawione542 osoby X11 chronione. Dla71 dowiedzionych starych szacunków projektowych zmiana wyłącznie słów CA/PA:70CA i63PA; PA nie obniżono.',
 '- Nowe U21 bez FC27 zachowują zasadę20% klubów z pasmami80/17/2.8/0.2. Stare nieznane losowania nie otrzymują darmowego ponownego losowania. Rzeczywiste przydziały i finalne UID w talent-native-UID-ledger.json.',
 '- Rzeczywiste rozkłady w prepared/rating-distribution.csv i rating-distribution-by-provenance.csv; kontrola koncentracji starych ocen w flat-reuse-before-after.csv. Klasy: '+json.dumps(dict(counts),ensure_ascii=False)+'.','',
 '## Luki i ochrona','',
 '- 76 odłożonych kandydatów;744 wszystkich źródłowych luk. Nie szukano ich na siłę. Niedobór kadry/GK uzupełnia silnik.',
 '- '+str(len(guard['records']))+' dawnych niezweryfikowanych rekordów bez DOB lub dodatnich CA/PA zachowano dokładnie; lista preserved-unresolved-source-records.json. Nie zwalniamy nieudowodnionego formatu.',
 '- Stare różne obsady Chaves w śladach wyłącznieTM pozostają jawnie sprzeczne; dowód kwalifikuje wyłącznie pochodzenie oceny i dokładną tożsamość, nie historyczny klub. PAfloor i ochrony zachowane.','',
 '## Weryfikacja','',
 '- Negatywne kontrole7/7 PASS; błędny pin źródła/CSV/kraje/nieznana pusta drużyna/pusta z aktorami/brak deklaracji/mandatory buy odrzucone przed zapisem.',
 '- Pilot1320 osób,195 wypożyczeń i183 kluby z aktorami, wszystkie1149 reuse; niezależny pełny PEOPLE/SERVER/CLIENT inverse PASS.',
 '- Pełny import: niezależny PEOPLE/SERVER/CLIENT inverse, kontrakty, aktywne wypożyczenia, nazwy, daty, narodowości, nowe89B i poprawna kolejność nowych17B PASS. Stare17B/89B identyczne.',
 '- Końcowy71-UID patch CA/PA: cały PEOPLE inverse i odczyt wszystkich osób, tylko dozwolone słowa zmienione; atrybuty, osobowość, umowy, kadry, pożyczki, UID i daty zachowane.',
 '- 7533/7533 końcowe CA/PA/DOB/owner ponownie odczytane i porównane z CSV. Registry źródłowe/finalneUID: final-native-player-UID-ledger.csv.',
 '- Struktura:36 kontroli obu formularzy,186 obsad zgodnych, oddzielny regionalny4B patch Povoense48→−1; wszystko w structure-regional-root.',
 '- Wcześniejsze błędy zatrzymały wyłącznie prywatne próby przed zapisem; pilot-r4 przerwany po wykryciu starej listy ochronnej, brak outputu. R5 używa zamkniętej poprawnej listy.','',
 '## Następny krok','',
 'Root sprawdza native-ready-for-root-review.json i manifesty inverse, tworzy metadata/nazwę TEST_X14 w nowej publicznej kopii. Dopiero wtedy test SI i nowej kariery. Nie nadpisano X11, X12, X13 ani źródeł. Przy kolejnym imporcie dodać ten prepared/ do rejestru wcześniejszych paczek oraz zachować ledger talentów; nie losować ponownie.',
 '','Prywatny output: '+str(output)]
 (B/'RAPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 (B/'WZNOWIENIE.md').write_text('# X14 — gotowa prywatna baza do root review\n\n'+str(output)+'\n\n7533 osób/292core/289loans;6384new/1149reuse;71 ratingrepair. Native PASS, SI/kariera/sezon PENDING. Szczegóły RAPORT.md i native-ready-for-root-review.json. Root publikuje nową TEST_X14 po review; żadna zaakceptowana baza niezmieniona.\n',encoding='utf-8')
 dump(B/'final-artifact-pins.json',{str(p.relative_to(B)):sha(p)for p in[B/'RAPORT.md',B/'WZNOWIENIE.md',B/'native-ready-for-root-review.json',B/'final-native-player-UID-ledger.csv',B/'talent-native-UID-ledger.json',P/'manifest.json',P/'independent-verification.json',B/'ratings-patch-independent.json']})
 print('READY_FOR_ROOT',len(ledger),'actual people',sum(x['New']for x in ledger),'new;',len(talents),'new awards;',output)
if __name__=='__main__':main()
