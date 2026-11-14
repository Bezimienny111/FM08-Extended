"""Read-only native preflight and approved Dutch twelve Current moves; no DB writer."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import sys,json,hashlib,struct,zlib,itertools,math
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev'); R=ROOT/'FmLauncher/data/research'
O=Path(__file__).resolve().parent
N=R/'COUNTRY_BATCH_CZE_CRO_CHN_CHI_BGR_BRA_20261113/native-prep'
P=R/'COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
draft=read(O/'draft-8-team-moves.json')
for p,h in draft['SourcePins'].items(): assert sha(Path(p))==h,('pin',p)
freeze=read(N/'source-freeze.json'); src=N/'input/X19-after-SI'
assert len(freeze['hashes'])==24
for name,h in freeze['hashes'].items(): assert sha(src/name)==h,('source',name)
raw=(src/'server_db.dat').read_bytes(); dec=zlib.decompressobj(); server=dec.decompress(raw[9:])+dec.flush()
assert dec.eof and not dec.unused_data and not dec.unconsumed_tail
world={x['ClubUID']:x for x in read(N/'native-world-identities.json')}
records=read(N/'native-structure.json')['records']; by={x['ClubUID']:x for x in records}
assert len(by)==len(records)==len(world)==24131
catalog={x['index']:x for x in read(N/'competition-catalog.json')}
original_plan={x['TMID']:x for x in read(P/'native-prep/club-plan.json')}
assignments=read(P/'native-prep/root-structure/source-allocation/assignments.json')
tablepath=P/'competition-prep/sources/tm-competitions/NTD-previous_completed-label25-26-id2025-table.json'
table=read(tablepath)['tables'][0]['rows']; ranks={x['club_id']:x for x in table}
selected=[1030,2330,2349,2360]; reserves=[1800220153,856118,1800220154,1800220155]
backfill=[102884,115257,100884,1800220089]
tm={x['ProjectedClubUID']:x['TMID'] for x in original_plan.values() if x['Country']=='Netherlands'}
assert [ranks[tm[u]]['position'] for u in selected]==[1,2,3,4]
assert [ranks[tm[u]]['position'] for u in backfill]==[11,13,15,16]
# Prove all available modern NTD ordinary source actors in550; no ranking by current table.
candidates=[]
for t,x in original_plan.items():
 u=x['ProjectedClubUID']
 if x['Country']=='Netherlands' and x['SourceCompetition']=='NTD' and u in world:
  w=world[u]
  if w['CurrentDivision']==550 and w['NativeTeamKind']==0 and w['ParentUID'] is None:
   candidates.append(dict(ClubUID=u,TMID=t,Name=x['Name'],FinalPosition=ranks.get(t,{}).get('position'),PreviousLevel=3 if t in ranks else None))
ranked=sorted((x for x in candidates if x['FinalPosition'] is not None),key=lambda x:(x['FinalPosition'],x['TMID']))
assert [x['ClubUID'] for x in ranked[:4]]==backfill
# Geography chooses among fixed four freed slots, keeping the change at12 TEAMs.
ll=lambda u:(original_plan[tm[u]]['PublicStadium']['latitude'],original_plan[tm[u]]['PublicStadium']['longitude'])
def distance(a,b):
 return 12742*math.asin(math.sqrt(math.sin(math.radians(b[0]-a[0])/2)**2+math.cos(math.radians(a[0]))*math.cos(math.radians(b[0]))*math.sin(math.radians(b[1]-a[1])/2)**2))
slots=[1030,2360,2349,2330]
perms=sorted((sum(distance(ll(u),ll(v)) for u,v in zip(q,slots)),q) for q in itertools.permutations(backfill))
geo={u:by[v]['CurrentDivisionIndex'] for u,v in zip(perms[0][1],slots)}
assert geo=={100884:464,115257:464,102884:465,1800220089:469}
rawtriple={}
for row in records:
 u=row['ClubUID']; assert server[row['Start']]==10 and struct.unpack_from('<iI',server,row['Footer'])==(row['TeamIndex'],u)
 rawtriple[u]=[struct.unpack_from('<i',server,row['Start']+off)[0] for off in [7,15,47]]
 assert rawtriple[u][0]==row['CurrentDivisionIndex']==world[u]['CurrentDivision']
 assert all(v==-1 or v in catalog for v in rawtriple[u])
def witness(u):
 w=world[u]; r=by[u]; at=w['FamilyProofOffset']; end=r['Footer']+8
 assert server[at-4]==w['NativeTeamKind'] and server[at-3]==0
 assert struct.unpack_from('<i',server,at)[0]==w['TeamTailFamilyIndex']
 assert struct.unpack_from('<H',server,r['RosterOffset'])[0]==r['RosterSize']
 return dict(Native=w,TEAM=r,RawTriple=rawtriple[u],TEAMSHA256=hashlib.sha256(server[r['Start']:end]).hexdigest(),RosterSize=r['RosterSize'])
moves=[]
for u in reserves+selected+backfill:
 w=world[u];before=rawtriple[u]; assert before[1:]==[-1,-1]
 assert w['TeamCountry']==158
 assert (w['NativeTeamKind']==16 and w['ParentUID'] is not None) if u in reserves else (w['NativeTeamKind']==0 and w['ParentUID'] is None)
 after=550 if u in reserves else 21 if u in selected else geo[u]
 moves.append(dict(ClubUID=u,TMID=tm[u],Slot='CurrentDivision',Before=before[0],After=after,BeforeCOMPUID=catalog[before[0]]['uid'],AfterCOMPUID=catalog[after]['uid'],AlternateBefore=-1,AlternateAfter=-1,RegionalBefore=-1,RegionalAfter=-1,Role='reserve_to_generic_lower' if u in reserves else 'ranked_first_team_in' if u in selected else 'lower_pool_backfill',NativeTeamKindGuard=w['NativeTeamKind'],ParentUIDGuard=w['ParentUID']))
assert len(moves)==len({x['ClubUID'] for x in moves})==12
projection={u:list(v) for u,v in rawtriple.items()}
for m in moves: projection[m['ClubUID']][0]=m['After']
def count(triples,form,country=None):
 counts=Counter()
 for u,(cur,alt,regional) in triples.items():
  if country is not None and world[u]['TeamCountry']!=country: continue
  for c in {cur if form==0 or alt==-1 else alt,regional}-{-1}: counts[c]+=1
 return counts
reqs=read(P/'native-prep/root-structure/qa/requirements.json')
checks=[]
for q in reqs:
 if q['uid'] not in {29,30,862765,862766,862767,862768,862769,862770}: continue
 c=next(i for i,v in catalog.items() if v['uid']==q['uid']); form=q['form']
 before=count(rawtriple,form)[c];after=count(projection,form)[c]
 passed=after>=q['minimum'] and(q['maximum'] is None or after<=q['maximum'])
 checks.append(dict(**q,CompetitionIndex=c,Before=before,After=after,Passed=passed))
assert len(checks)==16 and all(x['Passed'] for x in checks)
assert all(count(rawtriple,f)==count(projection,f) for f in [0,1])
assert all(count(rawtriple,f,158)==count(projection,f,158) for f in [0,1])
# Simulated in-memory edit and exact inverse; never saved or recompressed asDAT.
changed=bytearray(server);edits=[]
for m in moves:
 r=by[m['ClubUID']];at=r['Start']+7;old=bytes(changed[at:at+4]);new=struct.pack('<i',m['After']);changed[at:at+4]=new
 edits.append(dict(ClubUID=m['ClubUID'],SourceOffset=at,BeforeHex=old.hex(),AfterHex=new.hex()))
for e in edits:changed[e['SourceOffset']:e['SourceOffset']+4]=bytes.fromhex(e['BeforeHex'])
assert changed==server
stock=[witness(u) for u in [1800220152,1800220156]]
assert all(x['Native']['NativeTeamKind']==16 and x['RawTriple']==[550,-1,-1] for x in stock)
pinpaths={Path(p) for p in draft['SourcePins']}|{N/'source-freeze.json',N/'native-world-identities.json',N/'native-structure.json',N/'competition-catalog.json',P/'native-prep/club-plan.json',P/'native-prep/root-structure/source-allocation/assignments.json',Path(__file__),ROOT/'FM08-Database-Tools/docs/DATABASE_UPDATE_RULES.md'}
for u in selected+backfill:
 p=original_plan[tm[u]];pinpaths.update(Path(p[k]) for k in ['ProfileFile','RosterFile'])
pins={str(p):sha(p) for p in sorted(pinpaths,key=str)}
plan=dict(Status='ROOT_APPROVED_POLICY_READY_FOR_COMMON_WRITER_INTEGRATION',CreatedUTC=datetime.now(timezone.utc).isoformat(),Source=str(src),SourcePins=pins,SourceHashes=freeze['hashes'],RootApproval='2026-11-13 parent /root message: accepts12 Current-only; minimum geographic reassignment with hard slot capacity; no historical weekday requirement for modernNTD',Moves=moves,OrdinarySelection=[dict(ClubUID=u,TMID=tm[u],PreviousFinalFacts=ranks[tm[u]]) for u in selected],BackfillSelection=[dict(ClubUID=u,TMID=tm[u],PreviousFinalFacts=ranks[tm[u]]) for u in backfill],Available550SourceCandidates=candidates,Geography=dict(Rule='minimize sum haversine distance to four freed slot locations; hard slots464x2/465x1/469x1; permutation tie ClubUID',Permutations=24,MinimumSumKilometres=perms[0][0],Assignments=[dict(ClubUID=u,OldSlotClubUID=v,Destination=by[v]['CurrentDivisionIndex'],SourceLocation=ll(u),FreedSlotLocation=ll(v),DistanceKm=distance(ll(u),ll(v))) for u,v in zip(perms[0][1],slots)],Compromise='Native six-pool approximation; do not claim modern Saturday/Sunday equivalence. Capacity forces AFC into465 and IJsselmeervogels into469. Root explicitly accepted this policy.'),NativeWitnesses=[witness(u) for u in reserves+selected+backfill],Generic550ReserveWitnesses=stock,ChecksBothForms=checks,GlobalRawCountersBothFormsUnchanged=True,DutchCountersBothFormsUnchanged=True,Preserve=draft['Preserve'],DBWrites=False,NewFetches=0,RuntimeCalls=False,NativeVerification='READ_ONLY_PLAN_TECHNICAL_PREFLIGHT_PASS; target_pending',SIAcceptance='PENDING',NewCareerAcceptance='PENDING',SeasonAcceptance='PENDING',ExistingSaveRepair=False,CommonWriterIntegration='root appends Moves to next6 cfg.moves, source-relative offsets resolved by typed UID, no separate public database')
pre=dict(Status='PASS_READ_ONLY_PLAN_PREFLIGHT',Source24HashesPass=True,TypedTeamRecordsChecked=len(records),ChangedTeams=12,CurrentFields=12,PermittedSemanticBytes=48,InverseSimulationPass=True,GlobalBothFormsCountersUnchanged=True,DutchBothFormsCountersUnchanged=True,ChecksBothForms=checks,Generic550NLBefore=count(rawtriple,0,158)[550],Generic550NLAfter=count(projection,0,158)[550],EditsSourceOffsetsOnly=edits,NoDiskDBWrite=True,NoRuntime=True,Season='PENDING')
report='''# Holandia: zaakceptowany plan12 zmian Current

Root zaakceptowal polityke klasycznej naprawy13XI2026. Plik approved-12-team-moves.json jest gotowym planem do dolaczenia do wspolnego writera nastepnej szostki, bez osobnej publikacji. Nie zapisano DAT/EXE/ZIP ani save. Stary draft8 pozostaje historyczny i niezatwierdzony.

4Jong (PSV1800220153, Ajax856118, AZ1800220154, Utrecht1800220155) przechodza z21 do550. Pule550 ma juz NL kind16 Sparta1800220152 i Almere1800220156, zachowujace rodzicow; to swiadek zgodnosci klasycznej puli, nie dowod sezonu po naprawie.

First21 zachowuje20 miejsc: QuickBoys1030, DeTreffers2330, Hoek2349 i RijnsburgseBoys2360 zajmuja4 zwolnione miejsca wedlug zamknietej NTD25/26 pozycje1..4. Uprawnione pierwsze zespoly, wszystkie juz z kadrą.

Do dolnych pul wchodza z550 najlepsi dostepni ordinary z zamknietej NTD25/26: AFC102884 (#11)->465; RKAV115257 (#13)->464; HFC100884 (#15)->464; IJsselmeervogels1800220089 (#16)->469. Pozostaly ROHDA1800220090 to beniaminek bez pozycji w tej NTD; nie wypiera wyzej sklasyfikowanych kontynuujacych. Nie szukano nowych osob ani nie pobierano kraju. Kadry backfill30/27/24/24 zostaja bitowo chronione.

Przydzial regionalny minimalizuje odleglosc do4 zwolnionych miejsc (24 permutacje; suma281.943061km), z twarda pojemnoscia464x2/465x1/469x1. To jawna aproksymacja klasycznych pul. Wspolczesna NTD nie ma dowiedzionej ekwiwalencji sobota/niedziela. AFC w465 oraz IJsselmeervogels w469 sa kompromisem pojemnosci/geografii; root zaakceptowal brak wymogu historycznych dni. Nie dodajemy dalszych roszad tylko dla nazw pul.

Native preflight:24 piny zrodla identyczne;24131 rekordow ma zgodny typ/footer/UID/current;12 planowanych aktorow sprawdzono z kind/rodzicem/rosterem/ALT/Regional. ALT=-1 i Regional=-1 dla wszystkich12 zostaja.16 warunkow obu form PASS: Prem18, First20,464/465/466/468/469 po14,467=13. Globalne i holenderskie liczniki obu form identyczne;550 dostaje4 rezerwy i oddaje4ordinary. Symulacja48B pol w RAM i pelny inverse PASS, bez zapisu DB. To projekcja, nie wynik commonwritera.

Zmienia sie tylko Current12 TEAM. Kind, parent, FAMILY, poprzednia liga, ALT/Regional, PEOPLE, kadry, umowy, loans, kraj, nazwy, stadion i finanse chronione. Root ma sprawdzic piny/plany przed integracja. Wspolny import musi rozliczyc reszte6 krajow oraz inverse i niezalezny readback wszystkich zmian.

Diagnoza bez ponawiania runtime:18IV2009 parent-gate przy Prem33/34;19IV wszystkie6 okresow juz2, lecz First kwalifikacja6/8 i playoff8/10 z OOBindex8. Trwaly cykl eurocup obalony. Plan ogranicza ekspozycje rezerw w First; mechanizm utraty refill/invalidation nadal nie jest calkowicie udowodniony.

Statusy: plan/read-only technical preflight PASS; finalny native target PENDING; SI PENDING; nowa kariera PENDING; wielosezonowy test Holandii PENDING. Obecny uszkodzony save nie jest naprawiony przez zmiane bazy.
'''
outputs={'approved-12-team-moves.json':json.dumps(plan,ensure_ascii=False,indent=2)+'\n','technical-preflight-12.json':json.dumps(pre,ensure_ascii=False,indent=2)+'\n','REPORT-12.md':report}
for name,value in outputs.items():
 path=O/name;assert not path.exists(),('do_not_overwrite',path);path.write_text(value,encoding='utf-8')
for name,h in freeze['hashes'].items():assert sha(src/name)==h
manifest=dict(Status='PLAN_READY_NO_DB_WRITE',Artifacts={str(O/n):sha(O/n) for n in outputs},ScriptSHA256=sha(Path(__file__)),SourceFreezeSHA256=sha(N/'source-freeze.json'))
assert not (O/'plan12-pins.json').exists();(O/'plan12-pins.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps(manifest,indent=2))
