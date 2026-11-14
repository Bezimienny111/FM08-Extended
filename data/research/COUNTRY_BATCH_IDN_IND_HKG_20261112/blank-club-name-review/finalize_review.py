from pathlib import Path
from collections import Counter
import json,csv,hashlib
B=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
r=read(B/'all-86-slots.json');proof=read(B/'initial-findings.json');old={x['UID']:x for x in r if x['Snapshot']=='private_R2'};now={x['UID']:x for x in r if x['Snapshot']=='public_X17_after_SI'}
assert len(old)==len(now)==86 and not proof['Findings']
changes=[u for u in old if old[u]['AllLanguages']!=now[u]['AllLanguages'] or old[u]['EmbeddedFull']!=now[u]['EmbeddedFull'] or old[u]['EmbeddedShort']!=now[u]['EmbeddedShort']]
assert not changes
candidates=[]
for u,x in now.items():
 tier='India NFL'if x['Country']=='India'else'Indonesia Premier'if x['DivisionIndex']in[617,618]else'Indonesia First'
 candidates.append(dict(UID=u,TMID=x['TMID'],Club=x['ExpectedClub'],League=tier,FullPL=x['Polish'][0],ShortPL=x['Polish'][1],FullEN=x['English'][0],ShortEN=x['English'][1],EmbeddedFull=x['EmbeddedFull'],EmbeddedShort=x['EmbeddedShort'],EnglishAbbreviation=x['English'][2],PolishAbbreviation=x['Polish'][2],BlankUserClubIdentity='UNKNOWN_NOT_MATCHED_TO_UID'))
with(B/'candidates-86.csv').open('w',encoding='utf-8-sig',newline='')as f:w=csv.DictWriter(f,fieldnames=list(candidates[0]));w.writeheader();w.writerows(candidates)
empty_embedded=[x['UID']for x in now.values()if not x['EmbeddedFull'].strip() or not x['EmbeddedShort'].strip()]
plan=dict(Status='AWAIT_EXACT_USER_VISIBLE_UID_OR_VIEW_EVIDENCE_NO_SPECULATIVE_DATA_FIX',ApplyTo='NEXT_TEST_X_VERSION_ONLY',Protected=['TEST_X17_public_after_SI','TEST_X17_ZIP','active_career','private_R2'],ExactAffectedUIDs=None,UserObservedCount=3,ObservedByLeague={'India NFL':1,'Indonesia Premier':1,'Indonesia First':1},CandidateList='candidates-86.csv',CandidateCount=86,ImmediateDatabaseChanges=[],SingleNextBatchPreflight=[
 'Use the accepted frozen post-SI X17 source and the next batch union club-map; once only, compare all86 carried playable slots plus the next batch clubs.',
 'Require exact UID-to-family/client and language-record alignment; verify full and short labels in English/Polish and unchanged old values. Log embedded full/short fallback and optional abbreviations separately; absence alone is not proof of this3club defect.',
 'Resolve each observed blank to a concrete UID/view before changing data; if still unknown preserve records and carry the open issue. Do not replace identities from name similarity.',
 'For a proven missing localized full/short value, patch only that UID/field/language from the already pinned club-map/profile. Preserve owner/family/nation/membership/SugarDaddy/players; exact inverse and independent field readback.',
 'If the displayed blank persists while all authoritative data labels are present, report a runtime/view/localization issue instead of inventing a native data repair; a future test in the next version is separate from native PASS.'
],NoBuildRequiredForDataChange=True,NoAdditionalGlobalTestRequested=True)
dump(B/'next-batch-single-preflight.json',plan)
report=dict(Status='UNKNOWN_UI_BLANK_NOT_REPRODUCED_IN_LOCALIZED_DAT_LABELS',UserReportedBlanks=3,IdentifiedAffectedUIDs=[],UnknownAffectedUIDCount=3,PlayableSlotsAudited=len(now),ByLeague=dict(Counter(x['League']for x in candidates)),LanguagesRead=20,EnglishAndPolishFullShortPresent=86,LocalizedAndEmbeddedLabelsUnchangedAfterSI=True,UIDsWithEmptyEmbeddedFallback=empty_embedded,EmptyEmbeddedFallbackCount=len(empty_embedded),PolishOptionalAbbreviationEmpty=86,NoReasonToSelectExactly3FromThesePatterns=True,SourcePins=proof['SnapshotPins'],InputsBefore=proof['InputsBefore'],InputsAfter=proof['InputsAfter'],PublicDatabaseMutated=False,GameOrProcessAccess=False,FixDeferredToNextBatch=True,MinimalPlan='next-batch-single-preflight.json')
dump(B/'report.json',report)
text='''# X17: trzy puste nazwy klubow - waski odczyt

Status: UNKNOWN. Nie ustalono trzech UID bez zgadywania.

Uzytkownik zglosil jeden klub w indyjskim NFL oraz po jednym w indonezyjskich Premier i First. Sprawdzono zbiorczo wszystkie86 miejsc:10+36+40. W prywatnej zamknietej strukturzeR2 i publicznejX17 po zapisieSI kazdy klub ma pelna i skrocona nazwe w polskim i angielskim LANG. Lokalizacje i embedded CLIENT pozostaly identyczne po SI. To nie potwierdza poprawnego wyswietlenia w uruchomionej karierze, lecz wyklucza proste wskazanie trzech brakujacych pol full/short w tych dwoch lokalizacjach.

Opcjonalne skroty sa puste w polskim u86/86 klubow. Puste embedded fallback dotycza '''+str(len(empty_embedded))+''' rodzin, a nie trzech. Te wzorce nie uprawniaja do wybrania trzech winnych UID ani do automatycznej korekty wszystkich rodzin.

Pelna lista kandydatow: candidates-86.csv; wartosci20 jezykow i obu snapshotow: all-86-slots.json. report.json przypina odczytane pliki przed/po i rozdziela dowod od niewyjasnionego objawu.

Poprawka dopiero w nastepnej paczce po jednoznacznym powiazaniu pustej pozycji z UID/widokiem. Jeden wspolny preflight dla przenoszonych86 klubow i nowej paczki opisuje next-batch-single-preflight.json; tylko udowodnione pole/UID moze byc naprawione na podstawie istniejacych zrodel. Bez nowych frameworkow, globalnego buildu lub ponawiania zamknietych testow.

X17, ZIP i kariera pozostaly bez zmian. Nie odczytywano procesu ani pamieci gry.
'''
(B/'RAPORT.md').write_text(text,encoding='utf-8')
files=['audit_names.py','all-86-slots.json','initial-findings.json','candidates-86.csv','report.json','next-batch-single-preflight.json','RAPORT.md']
dump(B/'pins.json',{f:hashlib.sha256((B/f).read_bytes()).hexdigest()for f in files})
print(json.dumps({k:report[k]for k in ['Status','PlayableSlotsAudited','ByLeague','EnglishAndPolishFullShortPresent','EmptyEmbeddedFallbackCount']},ensure_ascii=True))