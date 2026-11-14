"""Build Polish third-tier R9 promotion XML using verified FM08 XML donors.

Only writes an explicitly selected new output directory. Never changes R8,
archives, databases, executable, or Ghidra projects. build_xml() is pure in-memory.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
sys.dont_write_bytecode = True
import pol3_efa_r8_20261107 as efa

ROOT = Path(__file__).resolve().parents[2]
R8 = ROOT / 'FmLauncher/data/research/POLAND_THIRD_TIER_PROTOTYPE_R8_20261107'
R9 = ROOT / 'FmLauncher/data/research/POLAND_THIRD_TIER_FATES_R9_20261107'
SOURCE_UID = 1800001000
TARGET_UID = 129559
EXE_SHA = '157f484be2ead4ab27006d1002c2c666a7228197b88b14c8d026e76f31b1d62d'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def serialize(element):
    tree = copy.deepcopy(element)
    ET.indent(tree, space='  ')
    return ET.tostring(tree, encoding='utf-8', xml_declaration=False) + b'\n'


def set_value(parent, kind, name, value):
    matches = [node for node in parent if node.get('id') == name]
    if len(matches) > 1:
        raise ValueError('Duplicate XML property: ' + name)
    node = matches[0] if matches else ET.SubElement(parent, kind, {'id': name})
    if node.tag != kind:
        raise ValueError('XML property has another type: ' + name)
    node.set('value', str(value))
    return node


def build_xml(base_xml, source_uid=SOURCE_UID, target_uid=TARGET_UID):
    root = ET.fromstring(base_xml)
    if root.get('competition') != str(source_uid):
        raise ValueError('Unexpected base competition UID')
    stages = root.find("list[@id='stages']")
    league = stages.find("record[@id='leag']") if stages is not None else None
    if league is None or league.get('index') != '0':
        raise ValueError('Missing base league stage')
    for key, expected in [('number_teams', '18'), ('number_rounds', '2')]:
        if league.find("integer[@id='%s']" % key).get('value') != expected:
            raise ValueError('Unexpected league format')
    if any(node.get('index') == '1' for node in stages):
        raise ValueError('Stage index 1 already occupied')
    if league.find("record[@id='promotion']") is not None:
        raise ValueError('Promotion rule already exists')
    if league.find("record[@id='top_playoff']") is not None:
        raise ValueError('Top playoff rule already exists')

    archive_path = ROOT / 'data/updates/update-802/data/comps.efa'
    archive_bytes = archive_path.read_bytes()
    if sha(archive_bytes) != efa.EXPECTED_SOURCE_SHA256['data/updates/update-802/data/comps.efa']:
        raise ValueError('Original donor archive hash differs')
    donor_bytes = efa.get_member(efa.parse(archive_bytes), 'ita/ita_c1_division.xml')
    donor = ET.fromstring(donor_bytes)
    promotion = copy.deepcopy(donor.find("list[@id='stages']/record[@id='tppl']"))
    if promotion is None:
        raise ValueError('Missing proven four-team donor')
    promotion.set('index', '1')
    # Source table supplies [3rd,4th,5th,6th]. Keys [1,3,2,0] sort this to
    # [6th,3rd,5th,4th]; fixed pairing and higher-seed home produce 3v6,4v5.
    assert [int(x.get('value')) for x in promotion.find("list[@id='team_order']")] == [1,3,2,0]
    assert [int(x.get('value')) for x in promotion.find("list[@id='seeding']")] == [0,1,2,3]
    selector = promotion.find("list[@id='teams']/record")
    set_value(selector, 'integer', 'competition', source_uid)
    set_value(selector, 'integer', 'next_stage_main_stage_name', 21)
    set_value(promotion, 'integer', 'stage_name', 21)
    rounds = promotion.find("list[@id='rounds']")
    if len(rounds) != 2:
        raise ValueError('Donor does not have semi-final and final')
    for ordinal, round_node in enumerate(rounds):
        stage_name = 18 if ordinal == 0 else 20
        set_value(round_node, 'integer', 'stage_name', stage_name)
        # Remove every inherited date, leg 2, draw date and financial setting.
        for node in list(round_node):
            if node.get('id') in {'date','date_2','draw_date','winner_prize_money','loser_prize_money','appearance_money'}:
                round_node.remove(node)
        date = ET.SubElement(round_node, 'record', {'id':'date','day_of_week':'sun',
                 'day_of_month':'3' if ordinal == 0 else '10','month':'jun',
                 'year':'2001','time':'1800'})
        ET.SubElement(date, 'flags', {'id':'match_rules','value':'extra_time, pen'})
        if ordinal == 0:
            ET.SubElement(round_node, 'record', {'id':'draw_date','day_of_week':'mon',
                'day_of_month':'28','month':'may','year':'2001','time':'1200'})
        else:
            ET.SubElement(round_node, 'record', {'id':'draw_date','previous_round_name':'18',
                'day_offset':'1','time':'1200'})
        for key, val in [('number_legs',1),('number_replays',0),
                         ('number_teams',4 if ordinal == 0 else 2),
                         ('number_matches',2 if ordinal == 0 else 1)]:
            set_value(round_node, 'integer', key, val)
        set_value(round_node, 'flags', 'draw_rules', 'fixed_draw, higher_seeded_team_at_home')
        set_value(round_node, 'flags', 'subs_rules', 'three_from_seven')
        set_value(round_node, 'flags', 'priority', 'league_high')
        set_value(round_node, 'flags', 'stadium_rules', 'home')
        ranking = round_node.find("list[@id='ranking_levels']")
        if ranking is not None:
            round_node.remove(ranking)
        ranking = ET.SubElement(round_node,'list',{'id':'ranking_levels'})
        if ordinal == 0:
            ET.SubElement(ranking,'record',{'team':'winner','current':'2','high':'2','low':'4'})
            ET.SubElement(ranking,'record',{'team':'loser','current':'4'})
        else:
            ET.SubElement(ranking,'record',{'team':'winner','current':'2'})
            ET.SubElement(ranking,'record',{'team':'loser','current':'3'})
    for action in promotion.find("list[@id='fate_actions']"):
        action.set('competition',str(source_uid))
        if action.get('new_fate') not in {'none','promoted'}:
            raise ValueError('Unexpected promotion fate')
    additions = ET.Element('record')
    direct = ET.SubElement(additions,'record',{'id':'promotion','number_places':'2',
        'competition':str(target_uid),'min_places':'3','max_places':'3'})
    top = ET.SubElement(additions,'record',{'id':'top_playoff','number_places':'4',
        'next_stage_main_stage_name':'21'})
    league.append(copy.deepcopy(direct))
    league.append(copy.deepcopy(top))
    stages.append(copy.deepcopy(promotion))
    # Pure structural/model checks, deliberately not labelled game verification.
    original_positions = [3,4,5,6]
    keys = [1,3,2,0]
    ordered = [position for _,position in sorted(zip(keys,original_positions))]
    pairs = [tuple(sorted(ordered[i:i+2])) for i in range(0,4,2)]
    if pairs != [(3,6),(4,5)]:
        raise ValueError('Ordering keys do not encode intended pairs')
    final_cases = [{'semi_winners':[a,b],'home':min(a,b),'away':max(a,b)}
                   for a in [3,6] for b in [4,5]]
    report = dict(status='promotion_xml_prepared_static_verified',source_competition=source_uid,
        target_competition=target_uid,direct_positions=[1,2],playoff_positions=original_positions,
        promotion_min_max=[3,3],number_top_playoff_places=4,team_order_keys=keys,
        sorted_participant_positions=ordered,semifinal_home_away=[list(x) for x in pairs],
        original_seeds=[0,1,2,3],draw_rule_mask='0x204',number_legs=[1,1],
        number_replays=[0,0],extra_time=True,penalties=True,away_goals=False,
        final_home_model_cases=final_cases,total_promoted_per_season=3,
        donor=dict(archive=str(archive_path),archive_sha256=sha(archive_bytes),
            member='ita/ita_c1_division.xml',member_sha256=sha(donor_bytes)),
        input_xml_sha256=sha(base_xml),input_xml_unchanged=True,
        game_executed=False,game_verified=False,season_rollover_verified=False,
        unknowns=['Runtime test of playoff qualifier table order, despite static table-row iteration proof',
                  'Runtime test of higher original seed hosting every possible final',
                  'Full season rollover together with second-tier relegation count and destinations',
                  'Save/reload inside playoffs and after season rollover',
                  'Dates in June must be checked against actual career calendar'])
    return dict(full_xml=serialize(root),promotion_stage_xml=serialize(promotion),
                league_additions_xml=serialize(additions),report=report)


def prepare(output):
    output = Path(output)
    if output.exists():
        raise FileExistsError('Refusing to overwrite promotion output')
    base_path = R8 / 'resources/pol_third.xml'
    source = base_path.read_bytes()
    if sha((ROOT/'fm.exe').read_bytes()) != EXE_SHA:
        raise ValueError('Executable identity differs')
    built = build_xml(source)
    output.mkdir(parents=True,exist_ok=False)
    for name,key in [('promotion-stage.xml','promotion_stage_xml'),
                     ('league-promotion.xml','league_additions_xml'),
                     ('pol_third-promotion.xml','full_xml')]:
        (output/name).write_bytes(built[key])
    evidence = []
    for address in ['dca6e0','dca8c0','d732d0','dd2da0','e08730','e086b0',
                    'e0ec00','e11e40','e17790','e10d80','e10ec0','e495d0']:
        path = ROOT/'FmLauncher/data/research/GHIDRA_ENGINE_20261107_R5/decompiled/functions'/('ram_'+address+'.c')
        evidence.append(dict(address='0x00'+address.upper(),path=str(path),sha256=sha(path.read_bytes())))
    built['report']['evidence_files'] = evidence
    built['report']['output_hashes'] = {p.name:sha(p.read_bytes()) for p in output.glob('*.xml')}
    (output/'report.json').write_text(json.dumps(built['report'],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (output/'README.md').write_text('''# Polish third-tier promotion R9\n\nPrepared XML: direct promotion for places1-2; four-team playoff for places3-6, with single semi-finals and final, higher original league position at home. Three promoted in total to UID129559.\n\n`promotion-stage.xml`: append to competition stages, index1. `league-promotion.xml`: children append to league stage. `pol_third-promotion.xml`: complete R8 XML extended with promotion only; root integrator may add relegation separately. Do not replace R8 files.\n\nStatic evidence: DCA6E0 parses promotion number_places into+14 and min/max3 into promotion action; DCA8C0 parses top_playoff4 into+15 and action21; D732D0/DD2DA0 collect qualified table rows in ascending row order. E08730 writes original seeding+4; E086B0 writes ordering key+5 then qsortE07070 subtracts signed keys. Keys1,3,2,0 reorder positions3,4,5,6 to6,3,5,4. Fixed pairing from donorITA yields6v3 and5v4; higher_seeded_team_at_home0x200 viaE0EC00 compares preserved original seeds and swaps home/away throughE05DC0. Seeds are attached to participant entries, not overwritten after rounds.\n\nE17790/E16170 parse set_league_fate actions: semi losers none, final winner promoted, final loser none. DCA6E0 promotion min/max3 specifies total movement including playoff winner, while number_places2 specifies direct places. CUP_SETTINGS serialization uses E10D80 writer,E10EC0 reader,E495D0 action factory.\n\nNo runtime verification performed here. Parent must test playoff participants/pairs, original-seed final home selection, all three promotions, second-tier reciprocal relegation and save/load/next season. June dates use base2000/2001 like source definitions, not real2026/27 dates.\n''',encoding='utf-8')
    if base_path.read_bytes()!=source:
        raise RuntimeError('Protected R8 source changed during preparation')
    print(json.dumps({key:built['report'][key] for key in ['status','direct_positions','playoff_positions','semifinal_home_away','total_promoted_per_season','game_verified']}))
    return built['report']


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=R9/'promotion')
    args=parser.parse_args()
    prepare(args.output)
