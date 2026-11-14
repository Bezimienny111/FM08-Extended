from pathlib import Path
p=Path('J:/FM08dev/FmLauncher/data/research/X19_RUNTIME_ERROR_20261113/replay-readonly/derive_apr18_parent_proof.py');s=p.read_text(encoding='utf-8-sig')
s=s.replace("shared_equal=[view(c) for c in v1['Competitions']]==[view(c) for c in d['Competitions']];assert shared_equal", """shared_equal=[view(c) for c in v1['Competitions']]==[view(c) for c in d['Competitions']]
# One unrelated raw TEAM+50 changed between independent stable snapshots.
# Record it exactly; require every stage/settings/row and all other TEAM bytes.
team_differences=[]
def compare_stages(a,b):
 assert a['RawHeaderHex']==b['RawHeaderHex'] and a.get('Settings',{}).get('RawHex')==b.get('Settings',{}).get('RawHex')
 for x,y in zip(a.get('Rows',[]),b.get('Rows',[])):
  assert x['RawHex']==y['RawHex'] and x['TEAM']['UID']==y['TEAM']['UID']
  for off,(xx,yy) in enumerate(zip(bytes.fromhex(x['TEAM']['RawHex']),bytes.fromhex(y['TEAM']['RawHex']))):
   if xx!=yy:team_differences.append(dict(TEAMUID=x['TEAM']['UID'],Offset=off,Before=xx,After=yy))
 for x,y in zip(a.get('Children',[]),b.get('Children',[])):compare_stages(x,y)
for x,y in zip(v1['Competitions'],d['Competitions']):
 assert x['RawHex']==y['RawHex'][:0xd8*2]
 for a,b in zip(x['Stages'],y['Stages']):compare_stages(a,b)
assert team_differences==[dict(TEAMUID=1009,Offset=0x50,Before=3,After=2)]
replay_path=B/'crash-replay-2009-04-19-v2.json';assert sha(replay_path)=='863166eb48f2045fe02e85c7cd66329c9e3e2e9daf152e3a2628f9d60c128259';replay=read(replay_path);assert replay['Status']=='PASS_STABLE_READ_ONLY_SNAPSHOT';rr=replay['QualificationSummary'];assert rr['PeriodPureStatusValues']==[2]*6 and rr['RetainedFate2']==6 and rr['ActualSettingsQUALQuota']==8 and rr['Dirty43']==0
""")
s=s.replace("[E,p,B/'precrash-2009-04-18.json'", "[E,p,replay_path,B/'precrash-2009-04-18.json'")
s=s.replace("Apr18V1V2SharedHeadersRowsEqual=shared_equal,", "Apr18V1V2FullTEAMBytesEqual=shared_equal,Apr18V1V2StageHeadersSettingsRowBytesEqual=True,Apr18V1V2ExplicitTEAMDifferences=team_differences,Apr18V1V2ProofFieldsEqual=True,")
s=s.replace("NextApril20ReplayPending=True", "NextApril20ReplayPending=False,PermanentPeriodParentCycleFalsifiedByApr19=True")
s=s.replace("RemainingGaps=['Whether later replay reaches same playoff shortage depends on simulation/finalization order'", "April19Replay=dict(Source=str(replay_path),SHA256=sha(replay_path),Date=replay['Date'],Summary=rr,MainCompleted=True,AllSixPeriodsStatus2ProvedFromHeader20And21zero=True,NoAutomaticRefillObserved=True,PeriodReservationCountNow0=True,WouldHaveRemainingQuotaIfRecomputed=2,Warning='No claim producer executed: Dirty43=0 and retained6. Apr18 negative counterfactual must not be used as Apr19 request.'),RemainingGaps=['Why main qualification pool was not refilled after parent completion: ordering/finalization remains to locate'")
s=s.replace("Czekamy na rezultat powtórki20kwietnia; nie wybrano poprawki danych.", "Powtórka19kwietnia potwierdziła wszystkie6okresów ukończone(status2), nadal6kwalifikantów i dirty43=0. To obala trwały cykl okresów, lecz wskazuje brak późniejszego uzupełnienia kwalifikacji. Wynik−3 z18kwietnia nie jest żądaniem z19kwietnia. Nie wybrano ani nie zastosowano tu poprawki danych.")
s=s.replace("Odczyty V1/V2 z18kwietnia mają identyczne wspólne nagłówki i wiersze.", "Odczyty V1/V2 z18kwietnia mają identyczne nagłówki faz, ustawienia i wiersze tabel. Jeden nieużywany przez ten dowód bajt TEAM1009+50 zmienił się3→2; różnica została jawnie zachowana w raporcie.")
p.write_text(s,encoding='utf-8')
