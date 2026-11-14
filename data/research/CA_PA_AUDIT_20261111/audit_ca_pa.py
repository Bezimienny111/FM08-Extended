"""Read-only CA/PA audit. Writes reports only, never database data."""
from pathlib import Path
from datetime import date
from collections import defaultdict,Counter
import csv,json,hashlib,statistics,sys
sys.dont_write_bytecode=True
ROOT=Path('J:/FM08dev');R=ROOT/'FmLauncher/data/research';B=R/'SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111';O=R/'CA_PA_AUDIT_20261111';O.mkdir(exist_ok=True)
PINS={}
def pin(p):PINS[str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
def js(p):pin(p);return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):
 pin(p)
 with p.open(encoding='utf-8-sig',newline='')as f:return list(csv.DictReader(f))
def save(name,data):
 if not data:return
 with (O/name).open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
def dump(name,data):(O/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
PACKS=[
 ('N4','POLAND_DATABASE_2627_R1_20261108/native-V25-N4','prepared','Poland',True),
 ('N7','POLAND_DATABASE_2627_R1_20261108/native-V25-N7/prepared-r2','','Poland',False),
 ('I1','ITALY_DATABASE_2627_IMPORT_I1_20261108/prepared-r4','','Italy',False),
 ('H1','HUNGARY_DATABASE_2627_H1_20261109/prepared','','Hungary',False),
 ('B1','WALES_USA_URUGUAY_2627_B1_20261109/prepared','','',False),
 ('X2','UKRAINE_TURKEY_X2_20261109/prepared','','',False),
 ('X3','SWEDEN_SWITZERLAND_X3_20261109/prepared','','',False),
 ('X7','FOUR_COUNTRY_X7_20261110/prepared','','',False),
 ('X10','SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/prepared','','',False)]
current=rows(O/'fresh-X10/export/players.csv')
actual={int(x['ID']):x for x in current if int(x['PersonIndex'])!=0}
stock=rows(R/'FACEPACK_ALL_NEW_X8_VS_802_20261111/stock802-audit/players.csv')
stock=[x for x in stock if int(x['PersonIndex'])!=0];stockuids={int(x['ID'])for x in stock}
latest={};created={};history=[];lotteries=[];clubs={};mismatch=[];public_mismatch=[];batchmeta=[]
x10plans={str(x['TMID']):x for x in js(B/'club-plan.json')}
def level(c,tag):
 if tag=='X10':return x10plans[str(c['TMID'])]['RealLevel']
 v=str(c.get('RealLeague',''))
 if v.isdigit():return int(v)
 if tag=='I1' and v in ['A','B','C']:return {'A':1,'B':2,'C':3}[v]
 if tag=='H1' and v in ['I','II','III']:return {'I':1,'II':2,'III':3}[v]
 if tag=='N4':return 2
 return ''
for tag,path,sub,country,old in PACKS:
 p=R/path;q=p/sub
 journal=js(p/'full-native.json');ids=rows(q/'identities.csv')
 native=rows(q/('native-players.csv'if old else'native_players.csv'))
 proofs=js(q/('profile-provenance.json'if old else'provenance.json'))
 cm=rows(q/('club-map.csv'if old else'club_map.csv'))
 for c in cm:
  c['Country']=c.get('Country')or country
  if c['Country']=='Liechtenstein':c['Country']='Switzerland'
  c['SourceLevel']=level(c,tag);clubs[int(c['TeamIndex'])]=c
 lp=q/'talent-lottery.json'
 if lp.exists():
  for v in js(lp):lotteries.append(dict(batch=tag,**v))
 for field in ['released_uids','duplicate_retire_uids']:
  for u in journal.get(field,[]):
   if int(u)in latest:latest[int(u)]['state']='retired'if field=='duplicate_retire_uids'else'released'
 sb={int(x['id90']):x for x in journal['subjects']}if not old else{}
 for ix,(n,i,pv)in enumerate(zip(native,ids,proofs)):
  s=journal['subjects'][ix]if old else sb[int(i.get('SubjectID')or i['ID90'])]
  u=int(s['uid']);eid=int(i['UID'if old else'ExistingID']);isnew=eid<0
  if isnew:created[u]=tag
  playing=int(s['club']if old else'splaying') if False else int(s['club']if old else s['playing'])
  c=clubs[playing]
  ca=int(s.get('CA',n['CA']));pa=int(s.get('PA',n['PA']))
  if (ca,pa)!=(int(n['CA']),int(n['PA'])):mismatch.append([tag,u,ca,pa,n['CA'],n['PA']])
  age=pv.get('age');real=pv.get('source_dob')or pv.get('sourceDOB')or pv.get('real_dob')or''
  if real:
   dob=date.fromisoformat(real);realage=2026-dob.year-((7,1)<(dob.month,dob.day))
   if age is not None and age!=realage:mismatch.append([tag,u,'age',age,realage])
   age=realage
  if u in actual:
   liveca,livepa=int(actual[u]['CA']),int(actual[u]['PA'])
  else:liveca=livepa=None
  if tag=='X10'and(liveca,livepa)!=(ca,pa):public_mismatch.append([u,ca,pa,liveca,livepa])
  record=dict(uid=u,name=(s['first']+' '+s['last']).strip(),batch=tag,origin_batch=created.get(u,'preexisting_before_N4'),new_in_this_batch=isnew,new_in_N4_X10_lineage=u in created,uid_in_stock802=u in stockuids,country=c['Country'],club=c['ClubName'],playing_team_index=playing,club_uid=int(c['ClubUID']),source_level=c['SourceLevel'],source_dob=real,age=age,age_band='unknown'if age is None else'<=18'if age<=18 else'19-21'if age<=21 else'22-24'if age<=24 else'25-28'if age<=28 else'>=29',CA=liveca if liveca is not None else ca,PA=livepa if livepa is not None else pa,journal_CA=ca,journal_PA=pa,gap=(livepa-liveca)if livepa is not None and livepa>0 else None,PA_kind='negative_code'if pa<0 else'unknown_zero'if pa==0 else'fixed_positive',ability_source='preserved_native_profile'if not isnew else pv.get('ability_source','unknown'),proof_ability_source=pv.get('ability_source','unknown'),source_player_id=pv.get('source_player_id',''),talent_estimate=bool(pv.get('talent_estimate')),state='confirmed_import',evidence=str(q/'provenance.json')if not old else str(q/'profile-provenance.json'))
  latest[u]=record;history.append(dict(record))
 batchmeta.append(dict(batch=tag,subjects=journal['rows'],new=journal['added'],reuse=journal['reused'],path=str(q)))
alllatest=list(latest.values());active=[x for x in alllatest if x['state']=='confirmed_import'and x['uid']in actual];x10=[x for x in active if x['batch']=='X10'];x8=[x for x in active if x['batch']!='X10']
assert not public_mismatch,public_mismatch[:5]
save('players-latest-imported.csv',active);save('history-all-import-facts.csv',history)
def pctile(v,p):
 if not v:return None
 v=sorted(v);f=(len(v)-1)*p/100;l=int(f);h=min(l+1,len(v)-1)
 return round(v[l]+(v[h]-v[l])*(f-l),3)
def stats(v):
 ca=[x['CA']for x in v if x['CA']is not None];pa=[x['PA']for x in v if x['PA']>0];gap=[x['PA']-x['CA']for x in v if x['PA']>0 and x['CA']>0]
 out={'n':len(v),'positive_PA':len(pa),'negative_PA':sum(x['PA']<0 for x in v),'zero_PA':sum(x['PA']==0 for x in v)}
 for key,a in [('CA',ca),('PA_positive',pa),('gap_fixed',gap)]:
  out.update({key+'_mean':round(statistics.mean(a),3)if a else None,key+'_min':min(a)if a else None,key+'_max':max(a)if a else None,key+'_p10':pctile(a,10),key+'_p50':pctile(a,50),key+'_p90':pctile(a,90),key+'_p95':pctile(a,95),key+'_p99':pctile(a,99)})
 out.update(gap_zero=sum(v==0 for v in gap),gap_le3=sum(v<=3 for v in gap),gap_lt0=sum(v<0 for v in gap),PA_ge150=sum(v>=150 for v in pa),PA_ge166=sum(v>=166 for v in pa),PA_ge181=sum(v>=181 for v in pa),CA_distinct=len(set(ca)))
 return out
aggregates=[]
for scope,data in [('X10',x10),('earlier_latest_X8_lineage',x8),('all_latest_imported',active)]:
 for fields in [(),('new_in_this_batch',),('age_band',),('country',),('country','source_level'),('new_in_this_batch','age_band'),('country','source_level','new_in_this_batch','age_band')]:
  groups=defaultdict(list)
  for x in data:groups[tuple(x[f]for f in fields)].append(x)
  for key,group in groups.items():
   aggregates.append(dict(scope=scope,group_fields='|'.join(fields)or'all',group_key='|'.join(map(str,key))or'all',**stats(group)))
save('statistics-country-tier-age-new-reuse.csv',aggregates)
# Club flatness is diagnostic, not an automatic instruction to change a rating.
clubstats=[];flat_uids=set()
for scope,data in [('X10',x10),('earlier_latest_X8_lineage',x8)]:
 groups=defaultdict(list)
 for x in data:groups[x['playing_team_index']].append(x)
 for ti,group in groups.items():
  c=clubs[ti];reuse=[x for x in group if not x['new_in_this_batch']];new=[x for x in group if x['new_in_this_batch']]
  counts=Counter(x['CA']for x in group);mode,n=counts.most_common(1)[0];dominance=n/len(group)
  reuse_flat=len(reuse)>=10 and len({x['CA']for x in reuse})==1
  if reuse_flat:flat_uids.update(x['uid']for x in reuse)
  clubstats.append(dict(scope=scope,country=c['Country'],club=c['ClubName'],club_uid=int(c['ClubUID']),source_level=c['SourceLevel'],n=len(group),new=len(new),reuse=len(reuse),CA_mean=round(statistics.mean(x['CA']for x in group),3),CA_sd=round(statistics.pstdev(x['CA']for x in group),3),CA_min=min(x['CA']for x in group),CA_max=max(x['CA']for x in group),CA_distinct=len(counts),CA_mode=mode,CA_mode_n=n,CA_mode_share=round(dominance,4),reuse_all_same_CA_atleast10=reuse_flat,reuse_CA_distinct=len({x['CA']for x in reuse}),PA_max=max(x['PA']for x in group),U21_fixed_gap_le6=sum(x['age']is not None and x['age']<=21 and 0<x['PA'] and x['PA']-x['CA']<=6 for x in group)))
save('club-flatness.csv',clubstats)
flat=[x for x in active if x['uid']in flat_uids];save('flat-reused-candidates-review.csv',flat)
save('top-CA-X10.csv',sorted(x10,key=lambda x:-x['CA'])[:100]);save('top-PA-X10.csv',sorted(x10,key=lambda x:-x['PA'])[:100]);save('top-PA-all-imported.csv',sorted(active,key=lambda x:-x['PA'])[:200]);save('negative-PA-preserved.csv',[x for x in active if x['PA']<0])
# 802 is a 2007 world, used only as an internal 1..200 and growth-margin reference.
stockplayers=[]
for x in stock:
 try:
  d=date.fromisoformat(x['BirthDate']);age=2007-d.year-((7,1)<(d.month,d.day))
 except ValueError:continue
 if not 14<=age<=50:continue
 stockplayers.append(dict(CA=int(x['CA']),PA=int(x['PA']),age=age,age_band='<=18'if age<=18 else'19-21'if age<=21 else'22-24'if age<=24 else'25-28'if age<=28 else'>=29'))
stockstats=[dict(age_band=age,**stats([x for x in stockplayers if age=='all'or x['age_band']==age]))for age in ['all','<=18','19-21','22-24','25-28','>=29']]
save('stock802-age-reference.csv',stockstats)
# Reproduce X10 estimates and talent draw without writing or changing random values.
sys.path.insert(0,str(ROOT/'FMExt/scratch'))
import squad_update_policy as policy
policy.SOURCE_LEVELS.update({'B1L1':1,'B1L2':2,'B1L3':3,'B1L4':4})
policy.COUNTRY_ADJUSTMENT.update({'Serbia':-20,'Romania':-20,'South Africa':-35,'Russia':-10})
proofs=js(B/'prepared/provenance.json');native=rows(B/'prepared/native_players.csv');cm=rows(B/'prepared/club_map.csv');byti={int(x['TeamIndex']):x for x in cm};check=[];replay=[]
for pv,n in zip(proofs,native):
 if pv['existing_id']>=0:continue
 c=byti[int(pv['playing_club'])];plan=x10plans[c['TMID']]
 if pv['ability_source']=='estimated_source_league_and_age':
  ca,pa,src=policy.abilities('tm:'+pv['source_player_id'],c['Country'],'B1L'+str(plan['RealLevel']),date.fromisoformat(pv['source_dob']),pv['known_positions'][0])
  assert ca==int(n['CA'])
  if not pv.get('talent_estimate'):assert pa==int(n['PA'])
  replay.append(dict(pv,pa=pa))
 else:replay.append(dict(pv))
lottery=js(B/'prepared/talent-lottery.json')
for c,expected in zip(cm,lottery):
 got=policy.assign_club_talent(int(c['ClubUID']),[x for x in replay if x['playing_club']==int(c['TeamIndex'])])
 assert got=={k:v for k,v in expected.items()if k!='club'},(c['ClubName'],got,expected)
check={'status':'PASS','public_X10_matches_journal_subjects':len(x10),'CA_PA_mismatches_public_vs_native':public_mismatch,'prepared_vs_journal_and_age_mismatches':mismatch,'model_reproduced_new_nonEA':sum(x['ability_source']=='estimated_source_league_and_age'for x in replay),'talent_draw_reproduced_clubs':len(lottery),'new_EA_profiles':sum(x['ability_source'].startswith('fc27')for x in replay),'negative_PA_excluded_from_numeric_gap':True,'PERSON0_excluded_in_both_audits':True}
dump('verification.json',check)
lotteryinfo=[]
for tag in [v[0]for v in PACKS]:
 ls=[v for v in lotteries if v['batch']==tag]
 if ls:lotteryinfo.append(dict(batch=tag,clubs=len(ls),eligible_clubs=sum(x['eligible_players']>0 for x in ls),awarded=sum(x['awarded']for x in ls),bands=dict(Counter(str(x.get('band'))for x in ls if x['awarded']))))
dump('lottery-summary.json',lotteryinfo)
summary={'date':'2026-11-11','X10':stats(x10),'X10_new':stats([x for x in x10 if x['new_in_this_batch']]),'X10_reuse':stats([x for x in x10 if not x['new_in_this_batch']]),'earlier_latest_X8':stats(x8),'all_latest_imported':stats(active),'X10_flat_reused_clubs':sum(x['scope']=='X10'and x['reuse_all_same_CA_atleast10']for x in clubstats),'X10_flat_reused_players':sum(x['batch']=='X10'for x in flat),'earlier_flat_reused_clubs':sum(x['scope']!='X10'and x['reuse_all_same_CA_atleast10']for x in clubstats),'earlier_flat_reused_players':sum(x['batch']!='X10'for x in flat),'lotteries':lotteryinfo,'full_world_recalibration_done':False,'original_802_age_reference_date':'2007-07-01','modern_source_age_reference_date':'2026-07-01','SI_and_new_career_X10':'user_confirmed','season_X10':'pending','current_public_files':'stable_during_readonly_audit','new_vs_reuse_scope':'new per latest import operation; reuse does NOT imply stock or reliable scouting'}
dump('summary.json',summary)
sources=['FMExt/OCENY_KADR_2026_27.md','FMExt/scratch/squad_update_policy.py','FMExt/scratch/prepare_missing_squads.py','FMExt/scratch/prepare_english_fc27.py','FM08-Database-Tools/scratch/x7prep_rosters_20261110.py','FmLauncher/data/research/SERBIA_ROMANIA_RSA_RUSSIA_X10_20261111/x10_prepare_players.py','FM08-Database-Tools/archive/historical-squad-imports/prepare_bulk_europe_b.py','FM08-Database-Tools/archive/historical-squad-imports/prepare_remaining_europe_full.py','FM08-Database-Tools/docs/DATABASE_UPDATE_RULES.md','FMExt/IMPORT_LIG_KROK_PO_KROKU.md']
for p in sources:pin(ROOT/p)
dump('input-manifest.json',{'source_hashes':PINS,'batches':batchmeta,'writes':'Reports only. No DB, source policy, import pipeline, EXE or running game changes.'})
def line(label,v):return '|'+label+'|'+str(v['n'])+'|'+str(v['CA_mean'])+'|'+str(v['PA_positive_mean'])+'|'+str(v['gap_fixed_mean'])+'|'+str(v['gap_zero'])+'|'+str(v['PA_ge166'])+'|'
age_lines=[]
for kind in [True,False]:
 for age in ['<=18','19-21','22-24','25-28','>=29']:
  v=stats([x for x in x10 if x['new_in_this_batch']==kind and x['age_band']==age]);age_lines.append(line(('Nowi 'if kind else'Reuse ')+age,v))
examples=[]
for club in ['Red Star Belgrade','FK Vojvodina Novi Sad','OFK Beograd','FK Cukaricki','FK Radnicki 1923 Kragujevac','FC Orenburg']:
 v=next(x for x in clubstats if x['club']==club)
 examples.append('|'+club+'|'+str(v['n'])+'|'+str(v['CA_mode'])+' × '+str(v['CA_mode_n'])+'|'+str(v['PA_max'])+'|'+str(v['U21_fixed_gap_le6'])+'|')
report=f"""# Audyt CA/PA — TEST_X10 i wcześniejsza linia do X8

**Diagnoza: skarga o płaskich ocenach jest zasadna. Najbardziej jednoznaczny problem leży w odziedziczonych, szacowanych kadrach: całe kluby mają identyczne CA, a niektórzy nastolatkowie jedynie 2–6 punktów zapasu PA. X10 zachował te oceny zgodnie z dotychczasową regułą ochrony istniejących profili. Nie jest to awaria zapisu SI ani globalne ustawienie PA=CA.**

Odczyt publicznej TEST_X10 wykonano bez zapisu bazy. Wszystkie 4230 osób mają CA/PA zgodne z natywnym dziennikiem importu; hashe bieżących plików przed i po odczycie identyczne (fresh-X10/source-pins.json). Użytkownik potwierdził zapis SI i nową karierę; sezon osobno oczekuje. To odczyt obecnych plików bazy, nie odczyt ocen już przeliczonych w karierze. Wykluczono PERSONindex0 w stock802 i bieżącym audycie ze względu na wcześniej ustaloną niepewność granicy rekordu. Baza, pipeline i oceny nie zostały zmienione.

## Najważniejsze wyniki

| Zakres | Liczba | Średnie CA | Średnie dodatnie PA | Średni PA−CA | PA=CA | PA≥166 |
|---|---:|---:|---:|---:|---:|---:|
{line('X10 wszyscy',summary['X10'])}
{line('X10 nowi',summary['X10_new'])}
{line('X10 reuse',summary['X10_reuse'])}
{line('Wcześniejsze ostatnie importy, bez ponownego liczenia UID X10',summary['earlier_latest_X8'])}

NegativePA i PA=0 nie są numerycznym potencjałem. Nie liczymy dla nich PA−CA, średnich dodatniego PA ani progów gwiazd. X10 zawiera 9 zachowanych negativePA; nie nadano ich nowym osobom. Kodów ujemnych nie zamieniamy automatycznie na arbitralny przedział; nie weryfikowano tutaj ich losowania przez silnik.

| Grupa wieku na 1 VII 2026 | Liczba | Średnie CA | Średnie dodatnie PA | Średni PA−CA | PA=CA | PA≥166 |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(age_lines)}

Nowi U18 i U21 mają realny zapas rozwoju. Natomiast w reuse U18 minimum dodatniego marginesu wynosi2, mimo że bieżąca polityka nowych szacunków daje20–35. Równość CA/PA u starszych nie jest sama w sobie błędem. Liczba PA≥166 także nie dowodzi błędu: cztery kraje i wiele niższych poziomów nie powinny automatycznie dostawać wielu światowych gwiazd.

## Płaskie odziedziczone kluby

| Klub | Importowanych | Dominujące CA | Maksymalne PA | U21 z dodatnim PA−CA≤6 |
|---|---:|---|---:|---:|
{chr(10).join(examples)}

Przykłady: Bogdan Bogdanović (Vojvodina,18lat)98/104; Vuk Barlov (OFK,18lat)90/93; Strahinja Aleksić (Radnički1923,18lat)88/92. To potwierdzone wartości bazy i dokładny wiek z dołączonego źródłowego DOB, nie propozycje docelowych ocen.

W X10 wykryto **{summary['X10_flat_reused_clubs']} klubów**, gdzie co najmniej10 ponownie użytych osób ma dokładnie to samo CA, razem **{summary['X10_flat_reused_players']} osób**. We wcześniejszych ostatnich importach do X8 analogicznie **{summary['earlier_flat_reused_clubs']} klubów / {summary['earlier_flat_reused_players']} osób**. To wskaźnik diagnostyczny, nie dowód, że każda z tych osób wymaga zmiany. Lista UID: flat-reused-candidates-review.csv, pełne rozkłady klubów: club-flatness.csv.

Porównanie z tego samego źródłowego poziomu Serbii: Vojvodina, drugie miejsce poprzedniego finału źródła, ma CA98 u wszystkich32graczy; IMT, pozycja9po połączeniu faz, ma średnie CA116,1. Vojvodina składa się z reuse, IMT z nowych szacunków. Sama tabela nie przesądza ocen konkretnych ludzi, ale pokazuje niezgodność skal pomiędzy generacjami importu. Porównujemy wszystkich importowanych, a nie wyłącznie podstawową11.

## Rzeczywista ścieżka X7/X10

x10_prepare_players.py ustawia konfigurację i uruchamia x7prep_rosters_20261110.py. Ten woła prepare_missing_squads.generate_profile → squad_update_policy.abilities, następnie po ustaleniu reuse woła assign_club_talent dla każdego klubu. Stara włoska tabela z procedury7.2 NIE jest formułą X10.

Wiek modelu liczy się na **2026-07-01**, niezależnie od snapshotu 2026-11-11; datę do FM przesuwa się o19lat tylko raz. Bieżące nowe szacunki CA:
- Dorosłe przedziały poziomu1:125–160,2:100–140,3:75–115,4:60–100,5:45–85,6:35–75.
- X10 korekty: Serbia−20, Rumunia−20, Rosja−10, RPA−35. X7: Szkocja−10, Słowacja/Słowenia−20, Singapur−45. To jawne stałe projektowe, nie reputacja ligi czy ranking UEFA pobrany z gry.
- Wiek: poniżej18−25;18–20−15;21–23−5;24+bez tej korekty. Z pola30–32dodatkowo−3,33+−8; GK−5dopiero36+. Clamp20–180.
- Nie ma mnożnika siły klubu, statusu zawodnika, minut, reprezentacji ani indywidualnej reputacji w tej gałęzi. Z tego powodu nowy rezerwowy i nowy lider tego samego wieku/poziomu dostają tę samą dystrybucję. To rozsądny awaryjny szacunek, ale słaby model końcowej jakości kadr.
- PA bez EA: przyrost20–35do18lat,12–25w19–21,5–15w22–24,0–8w25–28,0–3od29; clamp200.
- FC27: nieliniowa scale_ca; OVR91+ daje190,90→187,89→184,88→181,87→177,86→173,85→169,84→165,83→160,82→155,81→151,80→147;70–79i60–69interpolowane, poniżej60max(40,round(OVR*1.45)). Gdy brak potwierdzonego potential, PA przyrost26–35do19,16–24do22,6–12do26,0–3później. X10 ma jedynie6nowych EA i2816nowych szacunków.
- Reuse: bezwarunkowo zachowywane CA/PA i atrybuty, nawet jeżeli powstały wcześniej z płaskiego fallbacku. **Pochodzenie istniejącego rekordu nie jest rozróżniane jako zaufana ocena/legacy szacunek.** To najważniejsza luka polityki.

Ziarno abilities: SHA256(\"squad-estimates-2026-27-v1|\"+key+\"|abilities\"), następnie random.Random(int.from_bytes(...,\"big\")). W X10 generujący adapter przekazuje source_player_id już z prefiksem tm:, a generate_profile dodaje kolejny tm:, czyli faktyczny key to **tm:tm:<TMID>**. Jest deterministyczny; nie jest to brak seeda. Nie poprawiać prefiksu podczas drobnej korekty, bo przelosowałby wszystkie osoby. Atrybuty mają oddzielne purpose=\"attributes\".

Deterministycznie odtworzono wszystkie2816nowych szacunków CA i bazowego PA, a także154wyniki loterii, bez wpisywania nowych ocen do bazy. Są zgodne z zachowanymi wynikami.

## Czy działa loteria talentów?

**Tak.** W X10 sprawdzono154kluby;112miało uprawnionego kandydata,20otrzymało talent:18w paśmie150–165 i2w166–180. To odpowiada20%szansie bez gwarancji. Warunki: tylko NOWY profil, nie-EA, wiek≤21, bazowe PA<150; max1na klub w tym przygotowaniu. Reuse nigdy nie wchodzi do losowania — nawet18-latek z płaskim PA104. To tłumaczy brak dodatkowej szansy w znanych klubach z pełną starą kadrą.

Ziarno klubu: SHA256 wersja|clubUID|club-talent; wybór kandydata przez minimum SHA256 wersja|clubUID|sourceID; pasma po sukcesie:80%150–165,17%166–180,2,8%181–195,0,2%196–200. Brak PA181+ przy112kwalifikujących się klubach nie jest anomalią: szansa zera wynosi w przybliżeniu(1−0,2×0,03)^112≈51%. NajwyższePA X10: Dmitriy Kuchugura21lat123/179, Denis Bokov20lat78/169; oba to jawne szacunki loterii, nie potwierdzone indywidualne oceny skautingowe. Pełne listy top z nazwiskami/klubami i provenance w CSV.

## Starsze generatory: co wiadomo, a czego nie potwierdzono

Archiwalny prepare_bulk_europe_b.py zawiera dosłownie Vojvodina98,OFK90,Čukarički92 jako bazę klubu. calculate_ca zwraca dokładną bazę, gdy market_value jest puste. calculate_pa dla wieku25–28 daje CA+losowe2–6; wywołanie korzysta z **p.age or25**. prepare_remaining_europe_full.py zawiera Orenburg115 i ten sam schemat. To mechanizm zdolny wytworzyć obserwowaną płaskość oraz zaniżony zapas nastolatka przy brakującym wieku API.

Dowód kodu i zgodnego wzorca w DB jest mocny; nie odnaleziono w tym krótkim audycie kompletnego surowego wejścia historycznego, które dowodziłoby p.age=None i market_value=None dla każdego wskazanego profilu. Dlatego nie nazywamy konkretnego braku danych historycznie udowodnionym. Te stare skrypty nie mają wywołania random.seed, używają globalnego random i NIE zostały uruchomione. Nie należy ich ponownie używać.

## Porównanie z oryginalną 8.0.2 i kompletność

stock802-age-reference.csv pokazuje oryginalny świat2007 (data wieku1VII2007) z osobnymi ujemnymi kodami PA i PA0. To wewnętrzna referencja zakresu1–200 i zapasu wieku, **nie współczesny ranking tych krajów**. Nie porównujemy bezpośrednio średniej globalnego2007ze średnią czterech krajów2026. Tabele zawierają percentyle10/50/90/95/99 i skrajne wartości, także dla modernizacji według kraju, poziomu źródłowego, wieku i new/reuse.

Audyt obejmuje pełny aktualny zbiór importowanych UID z dzienników N4,N7,I1,H1,B1,X2,X3,X7,X10, po deduplikacji i późniejszych zwolnieniach/retire. Wcześniejszych V21–V25 nie nazywa kompletnie przeskautowanymi; ich osoby są uwzględnione, gdy zostały reuse w tych dziennikach. Nie wykonano pełnej ponownej kalibracji wszystkich305tysPLAYER świata. „New” oznacza nowy w danej operacji; reused może być współczesną osobą utworzoną wcześniej, nie stock802. Nie każdy historyczny klub ma jawny poziom źródłowy w dzienniku; pozostawiono pusty zamiast zgadywania. all-latest statystyki opierają się na świeżych CA/PA publicznej X10.

## Propozycja szybkiej, bezpiecznej korekty — wymaga decyzji, niewykonana

1. Zachować TEST_X10 poSI jako punkt odniesienia. Następna wersja ma osobny numer; bez zmiany bieżącej kariery ani UID, kadr, umów, wypożyczeń i dat.
2. Zmienić ochronę ocen z „każdy reuse” na **ochrona wiarygodnego pochodzenia**. EA/zweryfikowane indywidualne oceny i prawdziwe stockowe oceny pozostają; płaskie historyczne szacunki mają osobną jawną allowlistę UID (załączona lista diagnostyczna to kandydaci, jeszcze nie automatyczna allowlista).
3. Najpierw poprawić z potwierdzonym wiekiem młodych legacy z marginesem2–6 i kluby o płaskimCA. Najszybszy fallback to obecna deterministyczna polityka dla jawnie uznanych starych szacunków, stosowana również do tych reuse. Daje zróżnicowanie i właściwy margines wieku, ale pozostaje szacunkiem.
4. Dla sensownej jakości końcowej rozszerzyć fallback o jawny docelowy przedział siły klubu i indywidualną kategorię wynikającą z wiarygodnych danych. Potwierdzone indywidualne EA/ratings mają pierwszeństwo. Nie utożsamiać surowej wartości transferowej z umiejętnością i nie wpisywać na ślepo wyższych ocen wszystkim w mocniejszym klubie.
5. Nie gwarantować gwiazdy każdemu klubowi, nie podnosić wszystkimPA o stałą i nie tworzyć nowego losu przy każdym imporcie. Ewentualne ponowne dopuszczenie naprawianych legacy do talentów wymaga globalnego rejestru rozdań, żeby nie powtarzać loterii na tę samą osobę/klub.
6. Oceny bazowe i atrybuty są powiązane. Sama podmianaPA jest szybka i nie zmienia bieżącej siły, ale sama nie usuwa jednakowegoCA ani płaskich atrybutów; przebudowaCA powinna mieć zgodną kalibrację atrybutów. Potrzebne są scope/old→new/niezależny readback; poprawka samych danych nie wymaga pełnego builda edytora.
7. Przed publikacją dodać bramkę jakości: raport koncentracjiCA w klubach, marginesów U18/U21, outlierów i top potencjału z pochodzeniem. To nie nowa bramka niedoboru kadrowego. Nie odrzucać prawidłowej małej kadry ani dodawać fikcyjnych osób.

**Nakład:** samo wyciągnięcie i przeliczenie potwierdzonej allowlisty jest automatyzowalne jednym przebiegiem; brak potrzeby ponownego pobierania wszystkich kadr. Czasochłonne byłoby dopiero indywidualne skautowanie całego świata. Proponowane minimum to naprawa udowodnionych legacy szacunków z lokalnego cache i polityki, z jednym zbiorczym raportem do akceptacji, zamiast pytań o każdego gracza.

## Pliki
summary.json; verification.json; statistics-country-tier-age-new-reuse.csv; club-flatness.csv; flat-reused-candidates-review.csv; players-latest-imported.csv; history-all-import-facts.csv; top-CA-X10.csv; top-PA-X10.csv; top-PA-all-imported.csv; negative-PA-preserved.csv; stock802-age-reference.csv; lottery-summary.json; input-manifest.json; fresh-X10/export i source-pins.json.
"""
(O/'RAPORT.md').write_text(report,encoding='utf-8')
(O/'WZNOWIENIE.md').write_text('# Audyt CA/PA — gotowy, 11 XI 2026\nWyłącznie raporty; DB/pipeline/oceny niezmienione. Fresh publicX10 odczyt stabilny,4230CA/PA zgodne z native journal. SI/kariera userPASS,sezonpending. Główna przyczyna płaskości: chronione reuse z dawnych szacunków całych klubów; nowe U18 mają średnio28,5zapasPA, lecz stare U18 czasem2–6. Loteria działa20/112kwalifikującychklubów. Szczegóły RAPORT.md,CSV,hashy. Następna zmiana danych dopiero po decyzji, osobna wersja, bez nadpisaniaX10. Old age/market fallbackmechanism znaleziony w archiwalnym kodzie, dokładny brak input dla każdej osoby niepotwierdzony.\n',encoding='utf-8')
print(json.dumps({'status':'PASS','X10':len(x10),'earlier':len(x8),'flatX10clubs':summary['X10_flat_reused_clubs'],'flatX10players':summary['X10_flat_reused_players'],'flatEarlierClubs':summary['earlier_flat_reused_clubs'],'flatEarlierPlayers':summary['earlier_flat_reused_players'],'report':str(O/'RAPORT.md')},ensure_ascii=True))
