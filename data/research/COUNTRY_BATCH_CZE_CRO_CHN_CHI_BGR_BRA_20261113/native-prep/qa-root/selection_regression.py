"""Read-only six-country selection QA on the pinned X18 typed reader.
Preflight reads declarations/catalogues/evidence only. Target requires a root-pinned
closed-output manifest; numeric results do not establish scheduling/game support.
"""
from pathlib import Path
from collections import Counter
import argparse, copy, datetime, hashlib, importlib.util, json, sys
sys.dont_write_bytecode = True
ROOT = Path('J:/FM08dev')
R = ROOT/'FmLauncher/data/research'
B = R/'COUNTRY_BATCH_CZE_CRO_CHN_CHI_BGR_BRA_20261113'
N = B/'native-prep'
O = Path(__file__).resolve().parent
TEMPLATE = R/'COUNTRY_BATCH_NED_ESP_GRE_FRA_FIN_DEN_20261113/native-prep/root-structure/qa/selection_regression.py'
spec = importlib.util.spec_from_file_location('x18_selection_reader', TEMPLATE)
x18 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(x18)
read, sha = x18.read, x18.sha
GENERIC = 1301432
SLOTS = ('Current', 'Alternate', 'Regional')
GROUPS = ('moves', 'alternate_moves', 'regional_moves')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def dump(name, value):
    path = O/name
    require(not path.exists(), 'Preserve existing QA artifact: '+str(path))
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2)+'\n', encoding='utf-8')


def pin(path, pins, expected=None):
    path = Path(path).resolve()
    actual = sha(path)
    require(expected is None or actual == expected.lower(), 'Changed pin: '+str(path))
    require(str(path) not in pins or pins[str(path)] == actual, 'Conflicting pin: '+str(path))
    pins[str(path)] = actual
    return actual


def condition_key(q):
    return q['uid'], q['form'], q.get('country')


def limits(raw, lo):
    if raw in (-2, 4294967294):
        return lo
    if raw in (-1, 4294967295):
        return None
    return raw


def normalize(rows):
    # Model D35180 assignment order. Each bank0 writes Current and initializes
    # each still-zero Alternate threshold independently; bank1 overwrites ALT.
    states = {}
    for i, row in enumerate(rows):
        args = row['RawArguments']
        require(len(args) == 6 and args[0] == row['CompetitionUID'], 'D35180 ABI/declaration mismatch')
        uid, nation, lo, hi, aux, bank = args
        require(bank in (0, 1) and bank == row['RawFinalFlag'], 'Unsupported bank')
        country = row['Country'] if row['CountrySpecific'] else None
        require(country is None or uid == GENERIC, 'Unexpected native nation scope')
        key = uid, country
        state = states.setdefault(key, dict(bounds=[[0, 0], [0, 0]], provenance=[], row=row))
        maximum = limits(hi, lo)
        require(lo >= 0 and (maximum is None or maximum >= lo), 'Invalid thresholds')
        state['bounds'][bank] = [lo, maximum]
        if bank == 0:
            for j, value in enumerate((lo, maximum)):
                if state['bounds'][1][j] == 0:
                    state['bounds'][1][j] = value
        state['provenance'].append(dict(RawIndex=i, Bank=bank, Arguments=args))
    result = []
    for (uid, country), state in states.items():
        require(any(p['Bank'] == 0 for p in state['provenance']), 'No Current declaration')
        for form, (lo, hi) in enumerate(state['bounds']):
            result.append(dict(uid=uid, form=form, minimum=lo, maximum=hi, country=country,
                               country_fallback_uid=state['row'].get('CountryFallbackUID'),
                               origin='six_country_native_D353F0', semantics='native_country_nonnull_additive_regional',
                               RawProvenance=state['provenance']))
    return result


def definitions():
    old, pins = x18.requirements()
    require(len(old) == 325 and len({condition_key(q) for q in old}) == 325, 'Historical325 changed')
    old = copy.deepcopy(old)
    path = B/'competition-prep/native-competition-requirements.json'
    data = read(path)
    pin(path, pins)
    require(len(data['requirements']) == 99, 'Raw declaration count changed')
    new = normalize(data['requirements'])
    require(len(new) == 190 and len({condition_key(q) for q in new}) == 190, 'Normalized190 changed')
    for path, expected in data['SourcePins'].items():
        pin(path, pins, expected)
    review_path = B/'competition-prep/bounded-native-review-pins.json'
    reviews = read(review_path)
    pin(review_path, pins)
    decisions = {}
    for name, receipt in reviews.items():
        path = B/receipt['File']
        pin(path, pins, receipt['SHA256'])
        decision = read(path)
        decisions[name] = decision
        for p, h in decision.get('SourcePins', {}).items():
            pin(p, pins, h)
        if 'AsmFile' in decision:
            pin(decision['AsmFile'], pins, decision['AsmSHA256'])
    for row in decisions['China']['Requirements']:
        for form, prefix in enumerate(('Current', 'EffectiveAlternate')):
            q = next(q for q in new if q['uid'] == row['CompetitionUID'] and q['form'] == form)
            require((q['minimum'], q['maximum']) == (row[prefix+'Minimum'], row[prefix+'Maximum']), 'China bank proof mismatch')
    brazil = decisions['Brazil']['NativeFirstPhase']
    require(brazil['GroupCount'] == 16 and brazil['TeamsPerChildLeague'] == 8 and brazil['TotalConfiguredScheduledSlots'] == 128, 'Brazil128 proof changed')
    require({w['NativeUID']: w['NativeKind'] for w in decisions['Czech Republic']['NativeReserveWitnesses']} == {136207: 3, 136178: 3}, 'Czech native kind3 proof changed')
    cat_path = N/'competition-catalog.json'
    catalog = read(cat_path)
    pin(cat_path, pins)
    index = {v['index']: v['uid'] for v in catalog}
    require(len(index) == len(catalog) and len(set(index.values())) == len(catalog), 'Duplicate catalogue index/UID')
    require(index[73] == 102423 and index[86] == 107192, 'Brazil catalogue mismatch')
    for row in data['requirements']:
        require(index[row['CatalogueIndex']] == row['CompetitionUID'], 'Stale declaration catalogue index')
    for p in [N/'source-freeze.json', N/'native-structure.json', TEMPLATE, Path(__file__)]:
        pin(p, pins)
    # Pin every inherited script in the reader/requirements chain without re-running audits.
    module = x18
    while module is not None:
        pin(module.__file__, pins)
        module = getattr(module, 'prev', None)
    overlay_path = R/'SWEDEN_SELECTION_REPAIR_X5_20261110/runtime-X5-Sweden-members.json'
    overlays = read(overlay_path)['load_time_changes']
    require(len(overlays) == 14, 'Sweden14 proof changed')
    pin(overlay_path, pins)
    overlap = sorted(set(map(condition_key, old)) & set(map(condition_key, new)), key=str)
    union = len(set(map(condition_key, old)) | set(map(condition_key, new)))
    return old, new, pins, overlays, dict(RawDeclarations=99, HistoricalConditions=325,
        NewScopedCompetitions=len(new)//2, NewBankConditions=len(new), OverlapKeys=overlap,
        UniqueConditionKeys=union, Evaluations=len(old)+len(new),
        Qualification='Legacy and native semantics remain separate even if condition keys overlap')


def add_native_counts(profile):
    counts, scoped = [Counter(), Counter()], [Counter(), Counter()]
    collisions, null_relevant = [], []
    for uid, (cur, alt, regional) in profile['loaded'].items():
        country = profile['countries'][uid]
        if country is None:
            null_relevant.append(dict(UID=uid, Raw=profile['raw'][uid], Loaded=[cur, alt, regional], Kind=profile['kinds'][uid]))
            continue
        for bank, selected in enumerate((cur, alt if alt is not None else cur)):
            if selected is not None:
                if selected == GENERIC:
                    scoped[bank][(country, selected)] += 1
                else:
                    counts[bank][selected] += 1
            # D353F0 regional goes to COMP table, even for generic UID. It does
            # not enter the nation table and does not deduplicate selected.
            if regional is not None:
                counts[bank][regional] += 1
            if selected is not None and selected == regional:
                collisions.append(dict(UID=uid, Form=bank, CompetitionUID=selected, Country=country))
    profile.update(nativecounts=counts, nativecountrycounts=scoped,
                   NativeSelectedRegionalCollisions=collisions, NativeCountryNullSkipped=null_relevant)
    return profile


def native_checks(reqs, profile):
    rows = []
    for q in reqs:
        if q['country'] is None:
            n = profile['nativecounts'][q['form']][q['uid']]
        else:
            ci = profile['nationnames'][q['country'].casefold()]
            require(profile['nations'][ci] == q['country_fallback_uid'], 'Native country UID mismatch')
            n = profile['nativecountrycounts'][q['form']][(ci, q['uid'])]
        rows.append(dict(q, Count=n, Passed=n >= q['minimum'] and (q['maximum'] is None or n <= q['maximum'])))
    return rows


def paired(reqs, before, after):
    return [dict(q, before=a['Count'], after=z['Count'], before_passed=a['Passed'], after_passed=z['Passed'])
            for q, a, z in zip(reqs, before, after)]


def selfcheck():
    # Distinguish null-country exclusion and additive Regional from legacy set().
    fixture = dict(raw={1:[11,None,11],2:[11,None,11],3:[12,11,11],4:[GENERIC,None,GENERIC]},
                   loaded={1:[11,None,11],2:[11,None,11],3:[12,11,11],4:[GENERIC,None,GENERIC]},
                   countries={1:3,2:None,3:3,4:3}, kinds={1:0,2:0,3:3,4:0})
    add_native_counts(fixture)
    require(fixture['nativecounts'][0][11] == 3 and fixture['nativecounts'][1][11] == 4, 'Additive native count failed')
    require(len(fixture['NativeSelectedRegionalCollisions']) == 5, 'Collision diagnostics failed')
    require(len(fixture['NativeCountryNullSkipped']) == 1, 'Null-country diagnostic failed')
    require(fixture['nativecountrycounts'][0][(3, GENERIC)] == 1 and fixture['nativecounts'][0][GENERIC] == 1, 'Generic Regional belongs to COMP table')
    x18.selfcheck()
    return dict(Status='PASS_NATIVE_ADDITIVE_NULL_SCOPE_AND_INHERITED_LOADER_BOUNDARIES', DBRead=False)


def preflight(old, new, pins, summary):
    # Deliberately no read_profile/source-cache/world audit in this mode.
    tests = selfcheck()
    freeze = read(N/'source-freeze.json')
    require(freeze['status'] == 'PASS_SOURCE_COPY_AFTER_IDENTICAL', 'Source freeze incomplete')
    dump('requirements.json', dict(HistoricalLegacy=old, NativeCurrentBatch=new, Summary=summary))
    template = dict(Status='CLOSED_TARGET_READY_FOR_QA', source_freeze_sha256=sha(N/'source-freeze.json'),
                    files={k:dict(path='ROOT_SUPPLIES_ABSOLUTE_PATH', sha256='ROOT_SUPPLIES_SHA256')
                           for k in ('report','inverse','export','config')},
                    new_teams=[dict(uid='INTEGER',raw=['CURRENT_COMP_UID_OR_NULL','ALT_COMP_UID_OR_NULL','REGIONAL_COMP_UID_OR_NULL'],country='TYPED_COUNTRY_INDEX_OR_NULL',kind='INTEGER')],
                    country_changes=[dict(uid='INTEGER',before='COUNTRY_INDEX_OR_NULL',after='COUNTRY_INDEX_OR_NULL')],
                    kind_changes=[],
                    Contract='new_teams must exactly cover target minus source; country/kind changes exact, no unused authorizations; config moves/alternate_moves/regional_moves use catalogue indices and ClubUID/Before/After; expected_count_deltas covers raw Current globally including -1/null')
    dump('target-manifest-template.json', template)
    out = dict(Status='READY_DECLARATIONS_CATALOGUE_ONLY_TARGET_NOT_READ', Summary=summary,
               SelfChecks=tests, EvidencePins=pins, SourceFreezeSHA256=sha(N/'source-freeze.json'),
               SourceStatus={k:freeze[k] for k in ('source_SI','source_new_career','source_season')},
               SourceDBRead=False, TargetRead=False, DBWrites=False, WorldAuditDuplicated=False,
               SourceGaps='Population/source failures are not evaluated by declaration preflight; pending fresh source/target typed read',
               GameStatus='Scheduler/new-career/season NOT established by numeric QA', ScriptSHA256=sha(Path(__file__)))
    dump('code-preflight.json', out)
    print(json.dumps(dict(Status=out['Status'], **summary)), flush=True)


def deltas(a, z):
    return [dict(Form=bank, CompetitionUID=uid, Before=a[bank][uid], After=z[bank][uid])
            for bank in range(len(a)) for uid in sorted(set(a[bank])|set(z[bank]), key=lambda v: -1 if v is None else v)
            if a[bank][uid] != z[bank][uid]]


def counter_slots(profile):
    return [Counter(v[slot] for v in profile['raw'].values()) for slot in range(3)]


def verify_declared(source, target, cfg, manifest):
    idx = {i:u for i,u in enumerate(source['names'])}
    idx[-1] = None
    declared = {}
    for slot, group in enumerate(GROUPS):
        for move in cfg.get(group, []):
            key = move['ClubUID'], slot
            require(key not in declared and key[0] in source['raw'], 'Duplicate/unknown existing TEAM move')
            require(move['Before'] in idx and move['After'] in idx, 'Unknown move catalogue index')
            declared[key] = idx[move['Before']], idx[move['After']]
    actual = {(u,slot):(source['raw'][u][slot],target['raw'][u][slot]) for u in source['raw'] for slot in range(3)
              if source['raw'][u][slot] != target['raw'][u][slot]}
    require(actual == declared, 'Actual raw3 selection moves differ from exact config declarations')
    newteams = manifest['new_teams']
    byuid = {t['uid']:t for t in newteams}
    require(len(byuid) == len(newteams) and set(byuid) == set(target['raw'])-set(source['raw']), 'New TEAM list mismatch')
    predicted = copy.deepcopy(source)
    for (uid, slot), (before, after) in declared.items():
        predicted['raw'][uid][slot] = after
    for uid, t in byuid.items():
        require(len(t['raw']) == 3 and target['raw'][uid] == t['raw'] and target['countries'][uid] == t['country'] and target['kinds'][uid] == t['kind'], 'New TEAM selection/identity mismatch')
        predicted['raw'][uid] = list(t['raw'])
    for field, key in (('countries','country_changes'),('kinds','kind_changes')):
        rows = manifest.get(key, [])
        expected = {r['uid']:(r['before'],r['after']) for r in rows}
        observed = {u:(source[field][u],target[field][u]) for u in source['raw'] if source[field][u] != target[field][u]}
        require(len(expected) == len(rows) and expected == observed, 'Undeclared or unused '+key)
    for uid in (136207,136178):
        require(source['kinds'][uid] == target['kinds'][uid] == 3, 'Czech stock kind3 must be preserved')
    expected_raw = counter_slots(predicted)
    observed_raw = counter_slots(target)
    require(expected_raw == observed_raw, 'Global raw3 slot count deltas mismatch')
    source_raw = counter_slots(source)
    observed_current = {uid:observed_raw[0][uid]-source_raw[0][uid] for uid in set(observed_raw[0])|set(source_raw[0]) if observed_raw[0][uid]!=source_raw[0][uid]}
    cfg_delta = {idx[int(k)]:v for k,v in cfg['expected_count_deltas'].items() if v}
    require(cfg_delta == observed_current, 'Root global raw Current delta declaration mismatch')
    return dict(ExistingRawSlotChanges=len(actual), NewTEAM=len(byuid), RawThreeSlotDeltas=deltas(counter_slots(source), observed_raw), CountryChanges=manifest.get('country_changes',[]), KindChanges=manifest.get('kind_changes',[]), CzechStockKind3Preserved=True)


def target_pinned(args, old, new, pins, overlays, summary):
    require(args.target_manifest and args.target_manifest_sha256, 'Require root target manifest AND its SHA256')
    require(not (O/'regression.json').exists(), 'Preserve completed target QA')
    pre = read(O/'code-preflight.json')
    require(pre['EvidencePins'] == pins and pre['ScriptSHA256'] == sha(Path(__file__)), 'Preflight/code/evidence changed')
    pin(args.target_manifest, pins, args.target_manifest_sha256)
    manifest = read(Path(args.target_manifest))
    require(manifest['Status'] == 'CLOSED_TARGET_READY_FOR_QA', 'Target not closed')
    require(manifest['source_freeze_sha256'] == sha(N/'source-freeze.json'), 'Target source freeze mismatch')
    inputs = {}
    for key in ('report','inverse','export','config'):
        entry = manifest['files'][key]
        pin(entry['path'], pins, entry['sha256'])
        inputs[key] = Path(entry['path'])
    report, inverse, cfg = (read(inputs[k]) for k in ('report','inverse','config'))
    require(inverse['status'].startswith('PASS_'), 'Root inverse not PASS')
    require(report.get('inverse_verified') is True, 'Root structure report inverse not verified')
    require({k:v.lower() for k,v in inverse['output_hashes'].items()} == {k:v.lower() for k,v in report['output_hashes'].items()}, 'Report/inverse output hash mismatch')
    freeze = read(N/'source-freeze.json')
    require({k:v.lower() for k,v in report['source_hashes'].items()} == {k:v.lower() for k,v in freeze['hashes'].items()}, 'Writer source hashes differ from frozen source')
    source_path, target_path = Path(freeze['frozen']), Path(report['output'])
    require(source_path.resolve() != target_path.resolve(), 'Source may not be target')
    for rel, expected in freeze['hashes'].items():
        pin(source_path/rel, pins, expected)
    for rel, expected in report['output_hashes'].items():
        pin(target_path/rel, pins, expected)
    relevant = {q['uid'] for q in old+new}
    # The inherited typed reader validates TEAM boundaries/tails, FAMILY country,
    # COMP/nation catalogues, source hash before/after, and all historic overlays.
    source = add_native_counts(x18.profile(source_path,freeze['hashes'],N/'native-structure.json',overlays,relevant))
    target = add_native_counts(x18.profile(target_path,report['output_hashes'],inputs['export'],overlays,relevant))
    require(set(source['raw']) <= set(target['raw']), 'Existing TEAM removed')
    require(source['nations'] == target['nations'] and list(source['names']) == list(target['names']), 'Catalogue identity/order changed')
    for overlay in overlays:
        uid = overlay['uid']
        require(source['raw'][uid] == target['raw'][uid] and source['countries'][uid] == target['countries'][uid], 'Sweden14 raw input/country changed')
    declared = verify_declared(source,target,cfg,manifest)
    legacy = paired(old,x18.checks_for(old,source),x18.checks_for(old,target))
    native = paired(new,native_checks(new,source),native_checks(new,target))
    regression = [q for q in legacy if q['before_passed'] and not q['after_passed']]
    current_fail = [q for q in native if not q['after_passed']]
    inherited = [q for q in legacy if not q['before_passed'] and not q['after_passed']]
    old_null = {u for u in source['raw'] if source['countries'][u] is None}
    new_null = [r for r in target['NativeCountryNullSkipped'] if r['UID'] not in old_null]
    prior_relevant_null = {(r['UID'],tuple(r['Divisions'])) for r in source['nullrelevant']}
    new_relevant_null = [r for r in target['nullrelevant'] if (r['UID'],tuple(r['Divisions'])) not in prior_relevant_null]
    legacy_new_before, legacy_new_after = x18.checks_for(new,source),x18.checks_for(new,target)
    differences = [dict(uid=q['uid'],form=q['form'],country=q['country'],SourceLegacy=a['Count'],SourceNative=n['before'],TargetLegacy=z['Count'],TargetNative=n['after'])
                   for q,a,z,n in zip(new,legacy_new_before,legacy_new_after,native) if a['Count']!=n['before'] or z['Count']!=n['after']]
    # Confirm every pinned input and both frozen DAT sets still match after reads.
    for path, expected in pins.items():
        require(sha(Path(path)) == expected, 'Input mutated during QA: '+path)
    findings = bool(regression or current_fail or new_null or new_relevant_null)
    out = dict(Status='FINDINGS_REQUIRE_REVIEW' if findings else 'NUMERIC_SELECTION_REGRESSION_PASS',
               CreatedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(), Summary=summary,
               HistoricalLegacyChecks=legacy, NativeCurrentBatchChecks=native, NewLegacyRegressions=regression,
               NativeCurrentBatchFailures=current_fail, InheritedLegacyFailures=inherited,
               SourceNativeFailures=[q for q in native if not q['before_passed']],
               NewCountryNullTeams=new_null, NewCountryNullParticipants=new_relevant_null,
               CountryNullDiagnostics=[dict(Path=p['path'],AllSkipped=p['NativeCountryNullSkipped'],Relevant=p['nullrelevant']) for p in (source,target)],
               NativeSelectedRegionalCollisions=[dict(Path=p['path'],Rows=p['NativeSelectedRegionalCollisions']) for p in (source,target)],
               NativeVersusLegacyDifferences=differences, DeclaredChangesVerification=declared,
               LegacyGlobalCountDeltas=deltas(source['counts'],target['counts']), NativeGlobalCountDeltas=deltas(source['nativecounts'],target['nativecounts']),
               Replay=[dict(Path=p['path'],Sweden=p['replays'],Indonesia=p['indonesia_replay'],SpainAndTerritory=p['extra_replay']) for p in (source,target)],
               EvidencePins=pins, SourceTargetPins=[dict(Path=p['path'],Hashes=p['pins'],TEAM=p['records']) for p in (source,target)],
               ScriptSHA256=sha(Path(__file__)), TargetRead=True, DBWrites=False, RuntimeTest=False,
               Limits='Static numeric selection only. Legacy325 retains ALLphysical/dedup; native190 excludes null country and adds Regional independently. Scheduler/SI/new-career/season separate and pending.')
    dump('regression.json', out)
    dump('pins.json',dict(Status=out['Status'],ReportSHA256=sha(O/'regression.json'),ScriptSHA256=sha(Path(__file__)),EvidencePins=pins))
    print(json.dumps(dict(Status=out['Status'],LegacyRegressions=len(regression),NativeFailures=len(current_fail),InheritedFailures=len(inherited),NewNullTeams=len(new_null),NewNullParticipants=len(new_relevant_null),TargetRead=True)),flush=True)
    if findings:
        raise SystemExit(2)


def main():
    require(__debug__, 'Python -O is forbidden; inherited reader uses assertions')
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--preflight', action='store_true')
    mode.add_argument('--target-pinned', action='store_true')
    parser.add_argument('--target-manifest', type=Path)
    parser.add_argument('--target-manifest-sha256')
    args = parser.parse_args()
    old,new,pins,overlays,summary = definitions()
    if args.preflight:
        preflight(old,new,pins,summary)
    else:
        target_pinned(args,old,new,pins,overlays,summary)


if __name__ == '__main__':
    main()
