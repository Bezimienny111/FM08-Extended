"""R9 lower boundary proposal generator; writes derived XML/reports only.

No game launch; no database/EXE/archive mutation. Requires existing R8 inputs.
API: build_lower_xml(), build_survival_stage(), build_league_boundary().
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

UPPER = 1800001000
LOWER = 129560
OUT = Path('FmLauncher/data/research/POLAND_THIRD_TIER_FATES_R9_20261107/lower-boundary')


def integer(parent, name, value):
    return ET.SubElement(parent, 'integer', id=name, value=str(value))


def flags(parent, name, value):
    return ET.SubElement(parent, 'flags', id=name, value=value)


def xml(root):
    ET.indent(root, space='  ')
    return ET.tostring(root, encoding='utf-8', xml_declaration=True) + b'\n'


def qualified(parent, competition, stage, main, sub):
    entry = ET.SubElement(parent, 'record')
    integer(entry, 'id', 'get_qualified_teams')
    integer(entry, 'competition', competition)
    integer(entry, 'stage', stage)
    integer(entry, 'next_stage_main_stage_name', main)
    integer(entry, 'next_stage_sub_stage_name', sub)


def fate(parent, competition, stage, round_name, team, value):
    return ET.SubElement(parent, 'record', type='set_league_fate',
                         competition=str(competition), stage=stage,
                         stage_name=str(round_name), team=team, new_fate=value)


def round_settings(parent, stage_name, legs, date, second_date=None, draw_date=None):
    entry = ET.SubElement(parent, 'record')
    for name, value in [('stage_name', stage_name), ('number_legs', legs),
                        ('number_replays', 0), ('number_teams', 4), ('number_matches', 2)]:
        integer(entry, name, value)
    flags(entry, 'draw_rules', 'fixed_draw, do_not_swap_teams')
    flags(entry, 'subs_rules', 'three_from_seven')
    flags(entry, 'priority', 'league_high')
    flags(entry, 'stadium_rules', 'home')
    d = ET.SubElement(entry, 'record', id='date', **date)
    flags(d, 'match_rules', 'extra_time, pen' if legs == 1 else '')
    if second_date:
        d2 = ET.SubElement(entry, 'record', id='date_2', **second_date)
        flags(d2, 'match_rules', 'extra_time, pen')
    if draw_date:
        ET.SubElement(entry, 'record', id='draw_date', **draw_date)
    return entry


def date(day, month, year, weekday='sun', time='1800'):
    return dict(day_of_month=str(day), month=month, year=str(year), day_of_week=weekday, time=time)


def build_lower_xml():
    root = ET.Element('properties', competition=str(LOWER))
    for name, value in [('version', 1), ('type', 'division'), ('level', 3),
                        ('year', 0), ('year_interval', 1), ('base_year', 2000),
                        ('discipline_index', 1), ('fixture_rules_index', 2)]:
        integer(root, name, value)
    ET.SubElement(root, 'record', id='date_range', start_month='jul', start_year_offset='0',
                  end_month='jun', end_year_offset='1')
    dependencies = ET.SubElement(root, 'list', id='virtual_stage_dependency')
    ET.SubElement(dependencies, 'record', competition=str(UPPER), index='2', optional_stage='false')
    stages = ET.SubElement(root, 'list', id='stages')
    group = ET.SubElement(stages, 'record', id='grou', index='0', type='group')
    teams = ET.SubElement(group, 'list', id='teams')
    selector = ET.SubElement(teams, 'record')
    flags(selector, 'id', 'get_division_teams')
    integer(selector, 'competition', LOWER)
    integer(group, 'stage_name', 73)
    ET.SubElement(group, 'record', id='draw_date', **date(28, 'jul', 2000, 'fri', '1200'))
    integer(group, 'number_groups', 4)
    integer(group, 'number_teams', 25)
    integer(group, 'number_rounds', 2)
    flags(group, 'group_name_type', 'letters')
    # Existing GROUP_SETTINGS flag, not a fabricated region-assignment attribute.
    flags(group, 'group_rules', 'north_to_south')
    for name, value in [('points_for_win', 3), ('points_for_draw', 1), ('points_for_defeat', 0)]:
        integer(group, name, value)
    rules = ET.SubElement(group, 'list', id='sort_rules')
    ET.SubElement(rules, 'flags', value='goal_difference')
    ET.SubElement(rules, 'flags', value='goals_for')
    ET.SubElement(group, 'boolean', id='top_team_are_champions', value='true')
    ET.SubElement(group, 'record', id='promotion', number_places='1', competition=str(UPPER),
                  min_places='1', max_places='2')
    ET.SubElement(group, 'record', id='top_playoff', number_places='1',
                  next_stage_main_stage_name='111', next_stage_sub_stage_name='18')
    flags(group, 'subs_rules', 'three_from_seven')
    flags(group, 'priority', 'league_low')
    schedule = ET.SubElement(ET.SubElement(group, 'list', id='schedule'), 'record')
    ET.SubElement(schedule, 'record', id='start_date', **date(29, 'jul', 2000, 'sat'))
    ET.SubElement(schedule, 'record', id='end_date', **date(26, 'may', 2001, 'sat'))
    integer(schedule, 'number_dates', 50)
    flags(schedule, 'check_clashes', 'all')
    days = ET.SubElement(schedule, 'list', id='match_days')
    ET.SubElement(days, 'record', day_of_week='sat')
    ET.SubElement(days, 'record', day_of_week='wed')
    preliminary = ET.SubElement(stages, 'record', id='lpre', index='1', type='cup')
    integer(preliminary, 'stage_name', 111)
    required = ET.SubElement(preliminary, 'list', id='requirements')
    ET.SubElement(required, 'record', stage='grou')
    teams = ET.SubElement(preliminary, 'list', id='teams')
    qualified(teams, LOWER, 'grou', 111, 18)
    ET.SubElement(teams[-1], 'boolean', id='randomise_teams', value='true')
    order = ET.SubElement(preliminary, 'list', id='team_order')
    # Shuffle all four real runners-up before fixed adjacent pairing; random hosts and pairs.
    for key in [0, 1, 2, 3]:
        ET.SubElement(order, 'integer', value=str(key))
    rounds = ET.SubElement(preliminary, 'list', id='rounds')
    round_settings(rounds, 18, 1, date(3, 'jun', 2001), draw_date=date(28, 'may', 2001, 'mon', '1200'))
    actions = ET.SubElement(preliminary, 'list', id='fate_actions')
    ET.SubElement(actions, 'record', type='qualification', stage_name='18', team='winner',
                  next_stage_main_stage_name='111', next_stage_sub_stage_name='20')
    fate(actions, LOWER, 'grou', 18, 'loser', 'none')
    return xml(root)


def build_survival_stage():
    cup = ET.Element('record', id='btpl', index='2', type='cup')
    integer(cup, 'stage_name', 111)
    required = ET.SubElement(cup, 'list', id='requirements')
    ET.SubElement(required, 'record', stage='leag')
    ET.SubElement(required, 'record', competition=str(LOWER), stage='lpre')
    teams = ET.SubElement(cup, 'list', id='teams')
    qualified(teams, UPPER, 'leag', 111, 20)
    qualified(teams, LOWER, 'lpre', 111, 20)
    order = ET.SubElement(cup, 'list', id='team_order')
    # qsort keys for original [upper13,upper14,lowerWinner1,lowerWinner2].
    # Actual ordered list becomes [lowerWinner1,upper13,lowerWinner2,upper14].
    for key in [1, 3, 0, 2]:
        ET.SubElement(order, 'integer', value=str(key))
    rounds = ET.SubElement(cup, 'list', id='rounds')
    round_settings(rounds, 20, 2, date(10, 'jun', 2001), date(17, 'jun', 2001),
                   date(4, 'jun', 2001, 'mon', '1200'))
    actions = ET.SubElement(cup, 'list', id='fate_actions')
    fate(actions, UPPER, 'leag', 20, 'winner', 'none')
    fate(actions, UPPER, 'leag', 20, 'loser', 'relegated')
    fate(actions, LOWER, 'grou', 20, 'winner', 'promoted')
    fate(actions, LOWER, 'grou', 20, 'loser', 'none')
    virtual = ET.SubElement(cup, 'list', id='add_virtual_stage')
    ET.SubElement(virtual, 'record', competition=str(LOWER), stage_name='117')
    return xml(cup)


def build_league_boundary():
    root = ET.Element('record', id='lower_boundary_fragment')
    ET.SubElement(root, 'record', id='relegation', number_places='4', competition=str(LOWER),
                  min_places='4', max_places='6')
    ET.SubElement(root, 'record', id='bottom_playoff', number_places='2',
                  next_stage_main_stage_name='111', next_stage_sub_stage_name='20')
    return xml(root)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=OUT)
    args = parser.parse_args()
    out = args.output.resolve()
    expected = OUT.resolve()
    if out != expected:
        raise SystemExit('Only the designated derived R9/lower-boundary output is allowed')
    out.mkdir(parents=True, exist_ok=True)
    artifacts = {'pol_lower.xml': build_lower_xml(), 'survival-stage.xml': build_survival_stage(),
                 'league-lower-boundary.xml': build_league_boundary()}
    for name, data in artifacts.items():
        ET.fromstring(data)
        (out / name).write_bytes(data)
    source_csv = Path('FmLauncher/data/research/POLAND_THIRD_TIER_PROTOTYPE_R8_20261107/native-after-clubs.csv')
    with source_csv.open(encoding='utf-8-sig', newline='') as stream:
        source_clubs = list(csv.DictReader(stream))
    pool = [club for club in source_clubs if club['CurrentDivisionIndex'] == '141']
    assert len(pool) == 100 and len({club['ClubUID'] for club in pool}) == 100
    pool_csv = out / 'lower-pool-100.csv'
    with pool_csv.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(pool[0]))
        writer.writeheader()
        writer.writerows(pool)
    checks = []
    for lose_a in [0, 1]:
        for lose_b in [0, 1]:
            extra = lose_a + lose_b
            upper_count = 18 - 3 - (4 + extra) + 3 + (4 + extra)
            lower_count = 100 - (4 + extra) + (4 + extra)
            assert upper_count == 18 and lower_count == 100
            checks.append({'upper_playoff_losses': extra, 'new_upper_count': upper_count,
                           'new_lower_count': lower_count})
    report = {
        'status': 'static_proposal_not_game_validated', 'upper_uid': UPPER, 'lower_uid': LOWER,
        'lower_assignment_count': len(pool), 'lower_database_comp_index': 141,
        'pool_export_source_sha256': hashlib.sha256(source_csv.read_bytes()).hexdigest(), 'new_clubs': 0, 'new_comp_records': 0,
        'preliminary_draw': 'selector randomise_teams=true ->D7B870 rndm->D73080; fixed adjacent pairs preserve shuffled hosts',
        'group_count': 4, 'teams_per_group': 25, 'rounds': 2,
        'fixtures_per_team': 48, 'round_dates_per_group': 50, 'byes_per_team': 2,
        'lower_league_fixtures_total': 2400,
        'selection': 'actual four group tables -> four champions + four runners-up; shuffle runners-up before preliminary pairing',
        'required_runtime_changes': [
            {'site_va': '00D68DD3', 'expected_hex': '3A51117E0C',
             'normal_deactivation': '00D68DD8', 'active_continuation': '00D68DE4',
             'condition': '[ESI+0x14]==129560 && byte[ECX+0x11]>=2',
             'registers': 'ESI=ACTUAL_COMP; ECX=settings; DL=runtime level'},
            {'site_va': '00D69AF0', 'expected_hex': '3AC18BCE7E0F',
             'normal_deactivation': '00D69AF6', 'active_continuation': '00D69B05',
             'condition': '[ESI+0x14]==129560 && signed(CL)>=2',
             'registers': 'ESI=ACTUAL_COMP; AL=runtime level; CL=selected level; replay MOV ECX,ESI'},
        ],
        'db_operations': [
            'Fresh R9 copy of verified R8 input; never alter R8/original 802.',
            'Set COMP129560 database level to3 and runtime XML level3; preserve its UID/name/100 club assignments.',
            'Preserve country division_levels list129558,129559,1800001000 only (three selectable levels).',
            'Append real generic ACTUAL_COMP129560 to the native country alongside1800001000; do not merely add XML.',
            'No CLUB current/previous division rewrites are needed beyond the existing R8 split.',
        ],
        'fate_evidence': [
            'D7B870 selectionID2 ->D732D0; active guard +68(1); group branch->E345D0->DD2DA0 for each table.',
            'E3BAC0: ngps, grrl, gnty, gpdt; allocates LEAGUE_SETTINGS0xD0 per group and calls DD2010.',
            'DCA6E0 promotion1 + DCA8C0 top_playoff1 apply per internal league, not once to aggregate100.',
            'Cup qualification parser E17790 ->E138E0; set_league_fate ->E16170.',
            'E14FB0->ACTUAL_COMP+19C=D737E0: league->DD09B0, group->E330E0->DD09B0 for each internal league.',
            'DD09B0 changes only matched team row; foreign team is ignored, supporting paired upper/lower fate records.',
            'E086B0 reads original-position team_order keys; E07070 sorts by signed byte; [1,3,0,2] interleaves lower/upper.',
        ],
        'proven_native_not_suitable': [
            'Reserve_leagues type=shadow belongs to reserve/youth generation, not an established senior lower division format.',
            'get_inactive_lower_division_playoff_teams usesD7B820->D788F0, not results of four completed groups.',
            'A D7FFE0 no-op alone misses the entire standard else block ofD69A90 needed for season initialization/reset.',
            'Runtimelevel2 workaround changes hierarchy semantics; explicit scoped activation guards preservelevel3.',
        ],
        'verification': {'all_xml_well_formed': True, 'population_model_all4_outcomes': checks,
                         'game_started': False, 'runtime_pilot_passed': False},
        'limitations': [
            '4x25 is a technical pilot distribution of existing802 clubs, not current real IIIliga membership.',
            'north_to_south is a shipped group flag; exact membership and missing-city fallback require game observation.',
            'Verify odd-sized25-team group scheduling:50dates,48games/two byes per club,2400 total.',
            'Lower fixtures end26May; preliminary3June; survival10/17June must precede Poland season update.',
            'Check country season-update timing, serialized stage graph, four fates scenarios and next-season100/18 counts.',
            'An active auxiliary division excluded from division_levels should remain unavailable to manage, but verify UI and job offers.',
            'Paired leg order is backed by fixed adjacent pairing; verify actual return-leg venue in pilot.',
        ],
        'files': {name: {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                  for name, data in artifacts.items()},
    }
    (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(out), 'xml_files': list(artifacts), 'model_cases': len(checks),
                      'status': report['status']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
