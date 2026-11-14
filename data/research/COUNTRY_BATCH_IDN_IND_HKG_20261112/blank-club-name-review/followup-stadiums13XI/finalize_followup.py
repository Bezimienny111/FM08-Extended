from pathlib import Path
import json,csv,hashlib
O=Path(__file__).resolve().parent;B=O.parent.parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
f=read(O/'stadium-and-name-readback.json');ledger=list(csv.DictReader((B/'final-native-player-UID-ledger.csv').open(encoding='utf-8-sig')))
er=[r for r in ledger if r['UID']=='1710010015'];assert len(er)==1;er=er[0]
assert er['TMID']=='1475354' and er['ClubUID']=='1800200060' and er['PlayingTEAM']=='24179' and er['SourceName']=='Er Deva'
confirmed=[1800200042,1800200058,1800200060];assert {r['UID']for r in f['Clubs']if r['UID']in confirmed}==set(confirmed)
report=dict(Status='THREE_USER_REPORTED_BLANK_CLUB_IDENTITIES_CONFIRMED_RUNTIME_CAUSE_UNPROVEN',ConfirmedUIDs=confirmed,Clubs=[r for r in f['Clubs']if r['UID']in confirmed],ExcludedSriwedariCandidate=1800200030,UserEvidence={'Kudungga':'Persikutim United stadium','Delhi_NFL':'Punjab FC stadium','Sriwedari_Goalkeeper':'User explicitly names Er Deva; final import ledger uniquely associates him with Kendal Tornado FC'},ErDevaToKendalWitness=dict(LedgerPath=str(B/'final-native-player-UID-ledger.csv'),LedgerSHA256=sha(B/'final-native-player-UID-ledger.csv'),Row=er),Findings={'FullAndShortPLENLabelsPresent':True,'LANGUIDOrderHasThreeInversions':True,'UIDAndFamilyLANGPositionAlignmentIntact':True,'ActualNativeLookupRequirementProven':False,'BinarySearchSimulationsNotEquivalentToRuntimeAndNotExactlyThreeFailures':True,'Cause':'UNKNOWN_NATIVE_LOOKUP_OR_RUNTIME_STATE'},UnderlyingReadbackPath=str(O/'stadium-and-name-readback.json'),UnderlyingReadbackSHA256=sha(O/'stadium-and-name-readback.json'),DatabaseChanged=False,FixOnlyInNextVersion=True)
dump(O/'confirmed-three-clubs.json',report)
plan=dict(Status='THREE_UID_SCOPE_CONFIRMED_NEXT_BATCH_ONLY',UIDs=confirmed,SourceEvidence='confirmed-three-clubs.json',Preflight='One grouped name/UID-order preflight across acceptedX17 carried names plus next6country allocations before writer. Preserve existingUIDs and all physical references; flag non-monotonic order before append. Do not equate nonempty localization dictionaries with successful native display.',RepairDecision='Native UID-order/lookup cause remains unproven. Before applying a reorder establish which native table is required sorted and whether language records are UID-based or position-coupled. Do not blindly sort onlyLANG, renumberUIDs, reindexfamilies, or change club identities. If a precise safe correction is not proved, keep the named3UID defect explicit rather than report a fixed state.',ExistingDataProtection='No changes to X17/SI/ZIP/career. Nextversion correction must preserve all3UIDs, players/contracts/loans/country/membership/SugarOFF. Independent exact diff and targeted name readback, no broad rebuild.',RuntimeTest='In nextversion check display of PersikutimUnited/PunjabFC/KendalTornado; report native and actual career UI statuses separately.')
dump(O/'next-batch-plan.json',plan)
text='''# X17 - trzy puste nazwy: tozsamosci ustalone

- Persikutim United: UID1800200042, TM92053, Stadion Kudungga (native stadium1800210088).
- Punjab FC: UID1800200058, TM85902, Jawaharlal Nehru Stadium New Delhi (1800210033).
- Kendal Tornado FC: UID1800200060, TM92039, Stadion Sriwedari Solo (1800210087).

Kendal potwierdzil podany przez uzytkownika bramkarz Er Deva: UID1710010015/TM1475354, PlayingTEAM24179, ClubUID1800200060. Jednoznaczny wiersz oraz hash rejestru sa w confirmed-three-clubs.json. PSBS Biak (UID1800200030), drugi klub uzywajacy nazwy Sriwedari, zostal wykluczony.

Wszystkie trzy maja poprawne niepuste full/short w EN/PL oraz zgodne FAMILYindex i pozycje LANG w publicznej X17 po SI. W LANG i kolejnosci FAMILY potwierdzono trzy zejscia UID:1800200058->1800200020,1800200059->1800200024,1800200060->1800200042. To nie jest brak tekstow w DAT. Kolejnosc przestala byc rosnaca po zachowaniu starych57 przydzialow i dolaczeniu nowych UID58/59/60 podczas R2.

Przyczyna runtime pozostaje NIEUDOWODNIONA: dwa standardowe warianty wyszukiwania binarnego daja8 lub11 brakow wsrod86, nie dokladnie trzy. Bez istniejacego dowodu semantyki getter/lookup nie wolno przedstawic prostej symulacji jako zachowania FM08 ani slepo posortowac LANG, ktore teraz jest zgodne pozycyjnie z FAMILY.

Nastepna paczka: jeden zbiorczy preflight nazw, tozsamosci i kolejnosciUID przed writerem. Minimalna poprawka dopiero po potwierdzeniu konkretnej tablicy/warunku lookup; zachowac wszystkieUID i referencje. Szczegoly next-batch-plan.json. Zadnych zmian X17/SI/ZIP/karierze; brak dostepu do procesu lub pamieci gry.
'''
(O/'RAPORT.md').write_text(text,encoding='utf-8')
files=['audit_followup.py','stadium-and-name-readback.json','confirmed-three-clubs.json','next-batch-plan.json','RAPORT.md']
dump(O/'pins.json',{p:sha(O/p)for p in files})
print(report['Status'],confirmed)