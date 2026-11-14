import argparse
import hashlib
import shutil
import struct
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path


def occurrences(data, pattern):
    position = data.find(pattern)
    while position >= 0:
        yield position
        position = data.find(pattern, position + 1)


def inspect(data, unique_id):
    tables = set()
    for identity in (unique_id, unique_id - 1):
        positions = list(occurrences(data, struct.pack('<i', identity)))
        print(f'  ID {identity}: {len(positions)} hits')
        for position in positions:
            if unique_id != 11133:
                print(f'    {position:#x}: {data[max(0, position - 16):position + 48].hex(" ")}')
            if identity != unique_id - 1 or position < 4:
                continue
            row_start = position - 4
            row_index = struct.unpack_from('<i', data, row_start)[0]
            table_start = row_start - row_index * 89
            if row_index < 0 or table_start < 0 or table_start + 3 * 89 > len(data):
                continue
            if all(struct.unpack_from('<i', data, table_start + index * 89)[0] == index
                   for index in range(3)):
                tables.add(table_start)
                print(f'    VALID T89: row={row_index}, start={table_start}, row_bytes={data[row_start:row_start + 89].hex(" ")}')
    return tables


def retirement_table(data):
    signature = bytes.fromhex('24 00 d8 07 6d 00 00 00 ff ff ff ff')
    for position in occurrences(data, signature):
        if position + 17 > len(data):
            continue
        count = struct.unpack_from('<i', data, position + 12)[0]
        if count < 0 or position + 17 + count * 18 > len(data):
            continue
        print(f'  Retirement candidate: offset={position:#x}, count={count}, section_flag={data[position + 16]}')
        extras = []
        for index in range(count):
            record = position + 17 + index * 18
            identity, day, year, flag, order, extra, padding = struct.unpack_from('<iHHBiiB', data, record)
            extras.append(extra)
            if identity == 11133:
                print(f'    Buffon: ID={identity}, DOY={day}, year={year}, flag={flag}, index={order}, extra={extra}, padding={padding}')
        print(f'    Extra field: minus_one={extras.count(-1)}, other={sum(extra != -1 for extra in extras)}, last={extras[-5:]}')


def native_person_table_end(data):
    total, personalities, players = struct.unpack_from('<3i', data)
    player_start = None
    for location in occurrences(data, struct.pack('<i', 11132)):
        if location < 4:
            continue
        index = struct.unpack_from('<i', data, location - 4)[0]
        start = location - 4 - index * 89 - 81
        if start < 4 or start + players * 89 > len(data):
            continue
        if struct.unpack_from('<i', data, start - 4)[0] == players and all(struct.unpack_from('<i', data, start + row * 89 + 81)[0] == row for row in range(4)):
            player_start = start
            break
    assert player_start is not None, 'Player table not found'
    end = player_start - 8 - personalities * 17
    assert struct.unpack_from('<i', data, end)[0] == personalities
    return end


def native_person_records(data):
    total = struct.unpack_from('<i', data)[0]
    end = native_person_table_end(data)
    position = 16
    records = {}
    order = []
    for record_number in range(total):
        index = struct.unpack_from('<i', data, position)[0]
        assert 0 <= index < total, (record_number, position, index)
        pattern = struct.pack('<i', index)
        footer = data.find(pattern, position + 5, end)
        while footer >= 0:
            following = footer + 8
            valid_next = following + 5 <= end and 0 <= struct.unpack_from('<i', data, following)[0] < total and 1 <= data[following + 4] <= 5
            if following != end and not valid_next:
                following += 2
            if following <= end:
                identity = struct.unpack_from('<i', data, footer + 4)[0]
                if identity > 0 and identity not in records and (following == end or (following + 5 <= end and 0 <= struct.unpack_from('<i', data, following)[0] < total and 1 <= data[following + 4] <= 5)):
                    break
            footer = data.find(pattern, footer + 1, end)
        if footer < 0:
            candidates = []
            for candidate in occurrences(data[position + 5:min(end, position + 10000)], pattern):
                location = position + 5 + candidate
                candidates.append((location, data[location:location + 24].hex(' ')))
            raise AssertionError(('Missing person footer', record_number, position, index, candidates[:8]))
        identity = struct.unpack_from('<i', data, footer + 4)[0]
        records[identity] = data[position:footer + 8]
        order.append(identity)
        position = following
    assert position == end, ('Person table end mismatch', position, end, len(records))
    return records, order


def write_order_probe(root):
    source = root / 'TEST_FMEXT_NATIVEEDIT'
    destination = root / 'TEST_FMEXT_ORDER'
    if destination.exists():
        raise FileExistsError(f'Refusing to overwrite {destination}')
    raw = (source / 'people_db.dat').read_bytes()
    people = zlib.decompress(raw[9:])
    person_end = native_person_table_end(people)
    spans = []
    for identity in (1600000000, 1600000006):
        positions = list(occurrences(people, struct.pack('<i', identity)))
        assert len(positions) == 1
        end = positions[0] + 4
        start = end - 234
        assert 16 <= start < end <= person_end
        assert people[start + 4] == 2
        assert people[start:start + 4] == people[end - 8:end - 4]
        spans.append((start, end))
    records = b''.join(people[start:end] for start, end in sorted(spans))
    stripped = people
    for start, end in sorted(spans, reverse=True):
        stripped = stripped[:start] + stripped[end:]
    insertion = person_end - len(records)
    probe = stripped[:insertion] + records + stripped[insertion:]
    assert len(probe) == len(people)
    assert probe[:insertion] + probe[insertion + len(records):] == stripped
    assert native_person_table_end(probe) == person_end
    compressed = raw[:9] + zlib.compress(probe)
    assert zlib.decompress(compressed[9:]) == probe
    shutil.copytree(source, destination)
    (destination / 'people_db.dat').write_bytes(compressed)
    for metadata in destination.glob('*.xml'):
        tree = ET.parse(metadata)
        for element in tree.getroot().iter('string'):
            if element.get('id') == 'name':
                element.set('value', destination.name)
        metadata.unlink()
        tree.write(destination / (destination.name + '.xml'), encoding='utf-8', xml_declaration=True)
    for original in source.glob('*.dat'):
        if original.name != 'people_db.dat':
            assert original.read_bytes() == (destination / original.name).read_bytes()
    print(f'PASS: order-only runtime probe created at {destination}')
    print(f'Only the two known person records were relocated to {insertion}; all other DAT files are byte-identical to the official resave.')


def known_person_span(data, identity):
    positions = list(occurrences(data, struct.pack('<i', identity)))
    assert len(positions) == 1, (identity, positions)
    end = positions[0] + 4
    index = struct.unpack_from('<i', data, end - 8)[0]
    prefix = struct.pack('<iB', index, 2)
    starts = list(occurrences(data[max(16, end - 8192):end - 8], prefix))
    assert len(starts) == 1, (identity, index, starts)
    return max(16, end - 8192) + starts[0], end


def write_juve_probe(root):
    source = root / 'TEST_FMEXT_JUVE_CONTROL'
    destination = root / 'TEST_FMEXT_JUVE_NATIVE'
    if destination.exists():
        raise FileExistsError(f'Refusing to overwrite {destination}')
    raw_people = (source / 'people_db.dat').read_bytes()
    raw_server = (source / 'server_db.dat').read_bytes()
    people = zlib.decompress(raw_people[9:])
    server = zlib.decompress(raw_server[9:])
    baseline_server = zlib.decompress((root / 'TEST_FMEXT_NATIVEEDIT' / 'server_db.dat').read_bytes()[9:])
    owner_start, owner_end = known_person_span(people, 1600000000)
    target_start, target_end = known_person_span(people, 1600000006)
    owner, target = people[owner_start:owner_end], people[target_start:target_end]
    assert len(owner) == 299 and len(target) == 234
    assert struct.unpack_from('<i', owner, 171)[0] == 995 and owner[198] == 1
    assert struct.unpack_from('<i', target, 171)[0] == -1 and target[198] == 0
    owner_index = struct.unpack_from('<i', owner)[0]
    target_index = struct.unpack_from('<i', target)[0]
    contract = bytearray(owner[199:264])
    assert struct.unpack_from('<i', contract, 26)[0] == owner_index
    struct.pack_into('<i', contract, 26, target_index)
    changed = bytearray(target[:199] + contract + target[199:])
    changed[171:181] = owner[171:181]
    changed[198] = 1
    assert changed[264:] == target[199:]
    assert changed[:171] == target[:171] and changed[181:198] == target[181:198]
    restored = bytearray(changed[:199] + changed[264:])
    restored[171:181] = target[171:181]
    restored[198] = target[198]
    assert bytes(restored) == target
    updated_people = people[:target_start] + changed + people[target_end:]
    locations = list(occurrences(server, struct.pack('<i', owner_index)))
    assert len(locations) == 1
    member_end = locations[0] + 4
    candidates = []
    for count in range(1, 255):
        count_position = member_end - 2 - count * 4
        if count_position < 0 or struct.unpack_from('<H', server, count_position)[0] != count:
            continue
        if struct.unpack_from('<H', baseline_server, count_position)[0] != count - 1:
            continue
        if server[count_position + 2:member_end - 4] != baseline_server[count_position + 2:member_end - 4]:
            continue
        if server[member_end:member_end + 32] != baseline_server[member_end - 4:member_end + 28]:
            continue
        members = struct.unpack_from(f'<{count}i', server, count_position + 2)
        if all(0 <= member < struct.unpack_from('<i', people)[0] for member in members) and list(members) == sorted(set(members)):
            candidates.append((count_position, members))
    assert len(candidates) == 1, candidates
    count_position, members = candidates[0]
    assert members[-1] == owner_index < target_index
    assert target_index not in members
    updated_server = bytearray(server[:member_end] + struct.pack('<i', target_index) + server[member_end:])
    struct.pack_into('<H', updated_server, count_position, len(members) + 1)
    assert struct.unpack_from(f'<{len(members) + 1}i', updated_server, count_position + 2) == members + (target_index,)
    assert updated_server[member_end + 4:] == server[member_end:]
    assert updated_people[:16] == people[:16]
    assert native_person_table_end(updated_people) == native_person_table_end(people) + 65
    for identity, expected_index in ((1600000000, owner_index), (1600000006, target_index)):
        start, end = known_person_span(updated_people, identity)
        record = updated_people[start:end]
        assert len(record) == 299 and struct.unpack_from('<i', record, 171)[0] == 995
        assert struct.unpack_from('<i', record, 225)[0] == expected_index
        assert record[198] == 1
    start, end = known_person_span(updated_people, 1600000000)
    assert updated_people[start:end] == owner
    outputs = {}
    for filename, raw, data in (('people_db.dat', raw_people, updated_people), ('server_db.dat', raw_server, updated_server)):
        compressed = raw[:9] + zlib.compress(data)
        assert zlib.decompress(compressed[9:]) == data
        outputs[filename] = compressed
    shutil.copytree(source, destination)
    for filename, data in outputs.items():
        (destination / filename).write_bytes(data)
    for metadata in destination.glob('*.xml'):
        tree = ET.parse(metadata)
        for element in tree.getroot().iter('string'):
            if element.get('id') == 'name':
                element.set('value', destination.name)
        metadata.unlink()
        tree.write(destination / (destination.name + '.xml'), encoding='utf-8', xml_declaration=True)
    for original in source.glob('*.dat'):
        if original.name not in outputs:
            assert original.read_bytes() == (destination / original.name).read_bytes()
    print(f'PASS: created {destination} without modifying the control database.')
    print(f'PASS: both players have club 995, independent contract owners {owner_index}/{target_index}, and distinct preserved identities.')
    print(f'PASS: squad count {len(members)} -> {len(members) + 1}; person counts and all existing records preserved.')
    print('PASS: people delta=65 bytes, server delta=4 bytes; other DAT files unchanged; compression round-trip verified.')
    print('Runtime acceptance of the newly written contract still requires the game test; official-editor load/save remains the temporary finishing step.')


def compare_club(root):
    folders = ('TEST_FMEXT_NATIVEEDIT', 'TEST_FMEXT_JUVE_CONTROL')
    for path in sorted((root / folders[0]).glob('*.dat')):
        buffers = []
        for folder in folders:
            raw = (root / folder / path.name).read_bytes()
            compressed = len(raw) >= 11 and raw[9] & 15 == 8 and int.from_bytes(raw[9:11], 'big') % 31 == 0
            buffers.append(zlib.decompress(raw[9:]) if compressed else raw)
        before, after = buffers
        print(f'CLUB FILE {path.name}: identical={before == after}, sizes={len(before)},{len(after)}')
        if path.name == 'server_db.dat':
            for folder, data in zip(folders, buffers):
                for identity in (334476, 1600000000):
                    for location in occurrences(data, struct.pack('<i', identity)):
                        print(f'CLUB LINK {folder} value={identity} offset={location}: {data[max(0, location - 48):location + 48].hex(" ")}')
        if path.name != 'people_db.dat':
            continue
        stripped = []
        for folder, data in zip(folders, buffers):
            spans = []
            print(f'COUNTS {folder}: {struct.unpack_from("<4i", data)}')
            for identity in (1600000000, 1600000006):
                start, end = known_person_span(data, identity)
                spans.append((start, end))
                print(f'PERSON {folder} UID={identity}: start={start}, length={end - start}')
                for offset in range(0, end - start, 32):
                    print(f'  +{offset:03d}: {data[start + offset:min(end, start + offset + 32)].hex(" ")}')
            for start, end in sorted(spans, reverse=True):
                data = data[:start] + data[end:]
            stripped.append(data)
        print(f'OUTSIDE TWO PERSONS identical={stripped[0] == stripped[1]}, sizes={len(stripped[0])},{len(stripped[1])}')
        differences = []
        changed_count = 0
        for offset in range(0, len(stripped[0]), 65536):
            old_block, new_block = (data[offset:offset + 65536] for data in stripped)
            if old_block != new_block:
                changed = [(offset + index, old, new) for index, (old, new) in enumerate(zip(old_block, new_block)) if old != new]
                changed_count += len(changed)
                differences.extend(changed[:max(0, 12 - len(differences))])
        print(f'OUTSIDE PERSON CHANGES count={changed_count}, first={differences}')
        old_start, old_end = known_person_span(before, 1600000000)
        new_start, new_end = known_person_span(after, 1600000000)
        old_record, new_record = before[old_start:old_end], after[new_start:new_end]
        assert new_record[264:] == old_record[199:]
        print(f'CONTRACT 65-BYTE BLOCK: {new_record[199:264].hex(" ")}')
    print('PASS: club-control comparison completed without modifying either database.')


def compare_resave(root, folders, people_only=False):
    for path in sorted((root / folders[0]).glob('*.dat')):
        if people_only and path.name != 'people_db.dat':
            continue
        buffers = []
        print(f'\n=== RESAVE {path.name} ===')
        for folder in folders:
            raw = (root / folder / path.name).read_bytes()
            compressed = len(raw) >= 11 and raw[9] & 15 == 8 and int.from_bytes(raw[9:11], 'big') % 31 == 0
            data = zlib.decompress(raw[9:]) if compressed else raw
            buffers.append(data)
            print(f'{folder}: raw_header={raw[:11].hex(" ")}, expanded={len(data)}, sha256={hashlib.sha256(data).hexdigest()}')
        before, after = buffers
        print(f'  Identical={before == after}, size_delta={len(after) - len(before)}')
        if len(before) == len(after) and before != after:
            differences = []
            changed_count = 0
            for block in range(0, len(before), 65536):
                old_block = before[block:block + 65536]
                new_block = after[block:block + 65536]
                if old_block == new_block:
                    continue
                changed = [(block + offset, old, new) for offset, (old, new) in enumerate(zip(old_block, new_block)) if old != new]
                changed_count += len(changed)
                differences.extend(changed[:max(0, 12 - len(differences))])
            print(f'  Changed bytes={changed_count}, first={differences}')
        if path.name == 'server_db.dat':
            for data in buffers:
                retirement_table(data)
        if path.name not in ('people_db.dat', 'server_db.dat', 'client_db.dat'):
            continue
        if path.name in ('server_db.dat', 'client_db.dat'):
            name_tables = []
            without_names = []
            for data in buffers:
                first = data.find(b'\x00' + struct.pack('<i', 4) + 'Brak'.encode('utf-16le')) - 4
                names_start = first
                tables = []
                for category in range(2):
                    count = struct.unpack_from('<i', data, first)[0]
                    position = first + 4
                    records = {}
                    for index in range(count):
                        length = struct.unpack_from('<i', data, position + 1)[0]
                        footer = position + 14 + length * 2
                        stored, identity = struct.unpack_from('<ii', data, footer)
                        assert stored == index
                        records[identity] = (data[position + 5:position + 5 + length * 2].decode('utf-16le'), data[position + 5 + length * 2:footer], index)
                        position = footer + 8
                    tables.append(records)
                    runs = []
                    for text, metadata, index in records.values():
                        nation = struct.unpack_from('<i', metadata, 5)[0]
                        if runs and runs[-1][0] == nation:
                            runs[-1][2] = index
                        else:
                            runs.append([nation, index, index])
                    print(f'  NAME NATION RUNS category={category}: {runs[:12]}, total_runs={len(runs)}')
                    first = position
                name_tables.append(tables)
                without_names.append(data[:names_start] + data[first:])
            print(f'  OUTSIDE NAME TABLES: identical={without_names[0] == without_names[1]}, lengths={[len(data) for data in without_names]}')
            outside_changes = []
            outside_count = 0
            previous = -1000
            for block in range(0, len(without_names[0]), 65536):
                old_block = without_names[0][block:block + 65536]
                new_block = without_names[1][block:block + 65536]
                if old_block == new_block:
                    continue
                for offset, (old, new) in enumerate(zip(old_block, new_block)):
                    if old == new:
                        continue
                    absolute = block + offset
                    outside_count += 1
                    if absolute - previous > 32 and len(outside_changes) < 12:
                        outside_changes.append(absolute)
                    previous = absolute
            print(f'  OUTSIDE CHANGED BYTES: {outside_count}, groups={outside_changes}')
            for offset in outside_changes:
                print(f'  OUTSIDE WINDOW {offset}: old={without_names[0][max(0, offset - 16):offset + 40].hex(" ")}, new={without_names[1][max(0, offset - 16):offset + 40].hex(" ")}')
            for category in range(2):
                old_records, new_records = (tables[category] for tables in name_tables)
                changes = [(identity, old_records[identity], new_records[identity]) for identity in old_records.keys() & new_records.keys() if old_records[identity][:2] != new_records[identity][:2]]
                print(f'  NAME TABLE {category}: old={len(old_records)}, new={len(new_records)}, payload_changes={len(changes)}, changed={changes[:12]}')
        for label, data in zip(folders, buffers):
            if path.name in ('server_db.dat', 'client_db.dat'):
                for name in ('Brak', 'Imienia', 'NativeProbeFirst', 'NativeProbeLast', 'NativeProbeSecond'):
                    pattern = b'\x00' + struct.pack('<i', len(name)) + name.encode('utf-16le')
                    position = data.find(pattern)
                    if position >= 0:
                        payload_end = position + 22 + len(name) * 2
                        print(f'  NAME {label} {name}: offset={position}, before={data[max(0, position - 48):position].hex(" ")}, row={data[position:payload_end].hex(" ")}')
        for identity in (1600000000, 1600000001, 1600000002, 1600000003, 1600000004, 1600000005, 1600000006, 1600000007, 1600000008, 1600000009):
            positions = [list(occurrences(data, struct.pack('<i', identity))) for data in buffers]
            print(f'  UID {identity}: offsets={positions}')
            if path.name == 'people_db.dat' and all(len(found) == 1 for found in positions):
                length = 234 if identity in (1600000000, 1600000006) else 17 if identity in (1600000002, 1600000007) else 89
                records = [data[found[0] + 4 - length:found[0] + 4] for data, found in zip(buffers, positions)]
                changes = [(offset, old, new) for offset, (old, new) in enumerate(zip(*records)) if old != new]
                print(f'    Record length={length}, changes={changes}')
                for label, record in zip(folders, records):
                    print(f'    {label}: {record.hex(" ")}')
        if path.name == 'people_db.dat':
            print(f'  Counts: {[struct.unpack_from("<4i", data) for data in buffers]}')
            stripped = []
            for label, data in zip(folders, buffers):
                spans = []
                for identity in (1600000000, 1600000006):
                    location = data.find(struct.pack('<i', identity))
                    assert location >= 230
                    spans.append((location - 230, location + 4))
                print(f'  NEW PERSON SPANS {label}: {spans}')
                for start, end in sorted(spans, reverse=True):
                    data = data[:start] + data[end:]
                stripped.append(data)
            old_stripped, new_stripped = stripped
            differences = []
            changed_count = 0
            for block in range(0, len(old_stripped), 65536):
                old_block = old_stripped[block:block + 65536]
                new_block = new_stripped[block:block + 65536]
                if old_block != new_block:
                    changed = [(block + offset, old, new) for offset, (old, new) in enumerate(zip(old_block, new_block)) if old != new]
                    changed_count += len(changed)
                    differences.extend(changed[:max(0, 20 - len(differences))])
            print(f'  WITHOUT NEW PERSONS: lengths={[len(data) for data in stripped]}, changed_bytes={changed_count}, first={differences}')
            for offset, old, new in differences[:8]:
                print(f'  ALIGNED DIFFERENCE {offset}: old={old_stripped[offset - 24:offset + 40].hex(" ")}, new={new_stripped[offset - 24:offset + 40].hex(" ")}')
            try:
                parsed = [native_person_records(data) for data in buffers]
            except AssertionError as error:
                print(f'  FULL PERSON PARSE UNRESOLVED: {error}')
                continue
            old_records, old_order = parsed[0]
            new_records, new_order = parsed[1]
            assert old_records.keys() == new_records.keys(), 'Person identities changed'
            changes = []
            for identity, old_record in old_records.items():
                new_record = new_records[identity]
                if old_record != new_record:
                    changed = [(offset, old, new) for offset, (old, new) in enumerate(zip(old_record, new_record)) if old != new]
                    changes.append((identity, len(old_record), len(new_record), changed[:20]))
            moved = sum(old != new for old, new in zip(old_order, new_order))
            print(f'  PERSON RECORDS: total={len(old_records)}, changed_payloads={len(changes)}, moved_positions={moved}, changes={changes[:20]}')
            for label, records, order in zip(folders, (old_records, new_records), (old_order, new_order)):
                runs = []
                for identity in order:
                    kind = records[identity][4]
                    if runs and runs[-1][0] == kind:
                        runs[-1][1] += 1
                    else:
                        runs.append([kind, 1])
                print(f'  PERSON TYPE RUNS {label}: {runs[:40]}, total_runs={len(runs)}')
    print('PASS: resave comparison completed without modifying either database.')


def compare_controlled_contract(root, folders, identity, destination=None):
    if destination is not None and destination.exists():
        raise FileExistsError(f'Refusing to overwrite {destination}')
    paths = [root / folder / filename for folder in folders
             for filename in ('people_db.dat', 'server_db.dat', 'client_db.dat')]
    raw = [path.read_bytes() for path in paths]
    before = [hashlib.sha256(data).digest() for data in raw]
    people_a, server_a, client_a, people_b, server_b, client_b = [
        zlib.decompress(data[9:]) for data in raw]
    start_a, end_a = known_person_span(people_a, identity)
    start_b, end_b = known_person_span(people_b, identity)
    free = people_a[start_a:end_a]
    contracted = people_b[start_b:end_b]
    assert len(free) == 234 and len(contracted) == 299
    assert struct.unpack_from('<i', free, 171)[0] == -1 and free[198] == 0
    assert struct.unpack_from('<4i', people_a) == struct.unpack_from('<4i', people_b)
    index = struct.unpack_from('<i', free)[0]
    club = struct.unpack_from('<i', contracted, 171)[0]
    assert struct.unpack_from('<i', contracted)[0] == index and club > 0

    block = bytearray(65)
    block[1] = 1
    block[25] = 100
    struct.pack_into('<i', block, 26, index)
    block[31] = 47
    block[32] = 3
    struct.pack_into('<i', block, 35, 10000)
    struct.pack_into('<HH', block, 39, 181, 2008)
    block[43] = 2
    block[44] = 255
    struct.pack_into('<HH', block, 54, 181, 2007)
    block[59] = 25
    block[60] = 255
    generated = bytearray(free[:199] + block + free[199:])
    struct.pack_into('<i', generated, 171, club)
    struct.pack_into('<HH', generated, 176, 181, 2007)
    generated[198] = 1
    differences = [(offset, old, new) for offset, (old, new) in
                   enumerate(zip(generated, contracted)) if old != new]
    assert generated == contracted, ('SI player reconstruction differs', differences)
    print(f'PASS: all 299 player bytes match SI; UID={identity}, person index={index}, club index={club}.')
    print('PASS: primary type=1, status field=47, wage=10000, start=01.07.2007, expiry=30.06.2008.')

    candidates = []
    for member in occurrences(server_b, struct.pack('<i', index)):
        end = member + 4
        for count in range(1, 256):
            position = end - 2 - count * 4
            if position < 0 or struct.unpack_from('<H', server_b, position)[0] != count:
                continue
            if struct.unpack_from('<H', server_a, position)[0] != count - 1:
                continue
            old_members = server_a[position + 2:member]
            if server_b[position + 2:member] != old_members:
                continue
            if server_b[end:end + 32] != server_a[member:member + 32]:
                continue
            members = struct.unpack_from(f'<{count}i', server_b, position + 2)
            if list(members) == sorted(set(members)) and all(0 <= value <= index for value in members):
                candidates.append((position, members))
    assert len(candidates) == 1, ('Ambiguous controlled roster addition', candidates)
    position, members = candidates[0]
    assert members[-1] == index
    assert len(people_b) - len(people_a) == 65
    assert len(server_b) - len(server_a) == 4
    assert len(client_b) == len(client_a)
    print(f'PASS: native roster at {position} grows {len(members) - 1} -> {len(members)} by exactly the test player.')
    print('NOTE: SI also rewrites other records/references; this verifies the controlled player and roster, not whole-file equality.')
    assert before == [hashlib.sha256(path.read_bytes()).digest() for path in paths], 'Samples changed during inspection.'
    print('PASS: both original samples remain byte-for-byte unchanged.')
    if destination is None:
        return

    source = root / folders[0]
    metadata = list(source.glob('*.xml'))
    assert len(metadata) == 1, ('Expected one SI metadata file', metadata)
    tree = ET.parse(metadata[0])
    names = [element for element in tree.getroot().iter('string') if element.get('id') == 'name']
    assert len(names) == 1, 'Expected one database name in metadata.'
    updated_people = people_a[:start_a] + generated + people_a[end_a:]
    member_end = position + 2 + (len(members) - 1) * 4
    updated_server = bytearray(server_a[:member_end] + struct.pack('<i', index) + server_a[member_end:])
    struct.pack_into('<H', updated_server, position, len(members))
    assert updated_server[position:member_end + 4] == server_b[position:member_end + 4]
    assert updated_server[:position] == server_a[:position]
    assert updated_server[member_end + 4:] == server_a[member_end:]
    generated_start, generated_end = known_person_span(updated_people, identity)
    assert updated_people[generated_start:generated_end] == contracted
    assert updated_people[:start_a] == people_a[:start_a]
    assert updated_people[generated_end:] == people_a[end_a:]
    outputs = {}
    for filename, header_source, data in (
            ('people_db.dat', raw[0], updated_people),
            ('server_db.dat', raw[1], updated_server)):
        outputs[filename] = header_source[:9] + zlib.compress(data)
        assert zlib.decompress(outputs[filename][9:]) == data

    shutil.copytree(source, destination)
    for filename, data in outputs.items():
        (destination / filename).write_bytes(data)
    names[0].set('value', destination.name)
    (destination / metadata[0].name).unlink()
    tree.write(destination / (destination.name + '.xml'), encoding='utf-8', xml_declaration=True)
    for original in source.rglob('*'):
        if original.is_file():
            relative = original.relative_to(source)
            if relative not in (Path('people_db.dat'), Path('server_db.dat'), Path(metadata[0].name)):
                assert original.read_bytes() == (destination / relative).read_bytes(), ('Unexpected copied-file change', relative)
    assert before == [hashlib.sha256(path.read_bytes()).digest() for path in paths], 'Samples changed during export.'
    assert zlib.decompress((destination / 'people_db.dat').read_bytes()[9:]) == updated_people
    assert zlib.decompress((destination / 'server_db.dat').read_bytes()[9:]) == updated_server
    print(f'PASS: created {destination}; only the test player, roster entry and database name change from A.')
    print('SI acceptance of this independently generated copy is still required; the shared importer is unchanged.')


def controlled_player_span(data, identity):
    total = struct.unpack_from('<i', data)[0]
    matches = []
    for uid_position in occurrences(data, struct.pack('<i', identity)):
        if uid_position < 4:
            continue
        index = struct.unpack_from('<i', data, uid_position - 4)[0]
        if not 0 <= index < total:
            continue
        lower = max(16, uid_position - 8192)
        prefix = struct.pack('<iB', index, 2)
        for relative in occurrences(data[lower:uid_position - 4], prefix):
            start = lower + relative
            if data[start + 26:start + 30] == bytes.fromhex('6c 07 10 27'):
                matches.append((start, uid_position + 4))
    assert len(matches) == 1, ('Missing or ambiguous controlled PERSON record', identity, matches)
    return matches[0]


def controlled_loan_table(data, person_index):
    tables = set()
    for position in occurrences(data, struct.pack('<i', person_index)):
        row = position - 1
        if row < 0 or row + 32 > len(data) or data[row] != 0:
            continue
        index = struct.unpack_from('<i', data, row + 24)[0]
        start = row - index * 32
        if index < 0 or start < 4:
            continue
        count = struct.unpack_from('<i', data, start - 4)[0]
        end = start + count * 32
        if not index < count <= 1000000 or end > len(data):
            continue
        if all(data[start + i * 32] == 0 and
               struct.unpack_from('<i', data, start + i * 32 + 24)[0] == i
               for i in range(count)):
            tables.add((start - 4, count))
    assert len(tables) == 1, ('Missing or ambiguous controlled loan table', person_index, tables)
    return next(iter(tables))


def export_controlled_database(source, destination, payloads):
    if destination.exists():
        raise FileExistsError(f'Refusing to overwrite {destination}')
    metadata = list(source.glob('*.xml'))
    assert len(metadata) == 1, ('Expected one SI metadata file', metadata)
    tree = ET.parse(metadata[0])
    names = [element for element in tree.getroot().iter('string') if element.get('id') == 'name']
    assert len(names) == 1, 'Expected one database name in metadata'
    outputs = {}
    for filename, payload in payloads.items():
        raw = (source / filename).read_bytes()
        outputs[filename] = raw[:9] + zlib.compress(payload)
        assert zlib.decompress(outputs[filename][9:]) == payload
    shutil.copytree(source, destination)
    for filename, data in outputs.items():
        (destination / filename).write_bytes(data)
    names[0].set('value', destination.name)
    (destination / metadata[0].name).unlink()
    tree.write(destination / (destination.name + '.xml'), encoding='utf-8', xml_declaration=True)
    for original in source.rglob('*'):
        if original.is_file():
            relative = original.relative_to(source)
            if relative not in [Path(name) for name in payloads] + [Path(metadata[0].name)]:
                assert original.read_bytes() == (destination / relative).read_bytes(), \
                    ('Unexpected copied-file change', relative)
    for filename, payload in payloads.items():
        assert zlib.decompress((destination / filename).read_bytes()[9:]) == payload


def compare_controlled_coownership(root, folders, identity, destination=None):
    if destination is not None and destination.exists():
        raise FileExistsError(f'Refusing to overwrite {destination}')
    paths = [root / folder / filename for folder in folders
             for filename in ('people_db.dat', 'server_db.dat', 'client_db.dat')]
    hashes = [hashlib.sha256(path.read_bytes()).digest() for path in paths]
    people = [zlib.decompress((root / folder / 'people_db.dat').read_bytes()[9:])
              for folder in folders]
    spans = [controlled_player_span(data, identity) for data in people]
    records = [data[start:end] for data, (start, end) in zip(people, spans)]
    original, edited = records
    index = struct.unpack_from('<i', original)[0]
    assert len(original) - len(edited) == 65, 'SI did not remove exactly one contract block'
    assert struct.unpack_from('<4i', people[0]) == struct.unpack_from('<4i', people[1])
    candidates = []
    for contract in range(1, len(original) - 130 - 7):
        if original[contract - 1] != 2 or original[contract + 23] != 1:
            continue
        if (struct.unpack_from('<i', original, contract + 26)[0] != index or
                struct.unpack_from('<i', original, contract + 65 + 26)[0] != index):
            continue
        generated = bytearray(original[:contract + 65] + original[contract + 130:])
        generated[contract - 1] = 1
        generated[contract + 23] = 0
        if generated == edited:
            candidates.append((contract, bytes(generated)))
    assert len(candidates) == 1, ('Coownership removal differs from the controlled SI record', candidates)
    contract, generated = candidates[0]
    primary = bytearray(original[contract:contract + 65])
    primary[23] = 0
    assert edited[contract:contract + 65] == primary
    assert len(people[1]) == len(people[0]) - 65
    print(f'PASS: all {len(edited)} edited PERSON bytes match SI; UID={identity}, person={index}.')
    print(f'PASS: second 65-byte block removed at person +{contract + 65}; '
          f'count 2 -> 1, first-block coownership flag +23 cleared.')
    print('PASS: first block is the main contract regardless of its byte +1; '
          'all main fields and trailing clauses remain unchanged.')
    assert hashes == [hashlib.sha256(path.read_bytes()).digest() for path in paths]
    if destination is None:
        return
    start, end = spans[0]
    updated = people[0][:start] + generated + people[0][end:]
    assert updated[:start] == people[0][:start] and updated[start + len(generated):] == people[0][end:]
    export_controlled_database(root / folders[0], destination, {'people_db.dat': updated})
    assert hashes == [hashlib.sha256(path.read_bytes()).digest() for path in paths], \
        'Samples changed during coownership export'
    print(f'PASS: created {destination}; only the controlled PERSON record and metadata name change.')
    print('Server/client and other files unchanged; SI acceptance is still required; no retirement was set.')


def compare_controlled_loan(root, folders, identity, destination=None):
    if destination is not None and destination.exists():
        raise FileExistsError(f'Refusing to overwrite {destination}')
    paths = [root / folder / filename for folder in folders
             for filename in ('people_db.dat', 'server_db.dat', 'client_db.dat')]
    before = [hashlib.sha256(path.read_bytes()).digest() for path in paths]
    people = [zlib.decompress((root / folder / 'people_db.dat').read_bytes()[9:])
              for folder in folders]
    spans = [controlled_player_span(data, identity) for data in people]
    records = [data[start:end] for data, (start, end) in zip(people, spans)]
    assert records[0] == records[1], 'SI changed the controlled person record'
    person_index = struct.unpack_from('<i', records[0])[0]
    print(f'PASS: UID {identity}, person index {person_index}: '
          f'all {len(records[0])} PERSON bytes unchanged, including the original contract.')
    del people

    servers = [zlib.decompress((root / folder / 'server_db.dat').read_bytes()[9:])
               for folder in folders]
    header_a, count_a = controlled_loan_table(servers[0], person_index)
    start_a = header_a + 4
    rows = [servers[0][start_a + i * 32:start_a + (i + 1) * 32]
            for i in range(count_a)]
    removed = [row for row in rows if struct.unpack_from('<i', row, 1)[0] == person_index]
    assert len(removed) == 1, ('Expected one controlled loan', len(removed))
    retained = [row for row in rows if struct.unpack_from('<i', row, 1)[0] != person_index]
    assert retained, 'No retained loan available to locate the edited table'
    anchor = struct.unpack_from('<i', retained[0], 1)[0]
    header_b, count_b = controlled_loan_table(servers[1], anchor)
    assert count_b == count_a - 1, 'SI did not remove exactly one loan'
    expected = bytearray(struct.pack('<i', count_b) + b''.join(retained))
    for index in range(count_b):
        struct.pack_into('<i', expected, 4 + index * 32 + 24, index)
    end_a = start_a + count_a * 32
    end_b = header_b + 4 + count_b * 32
    assert bytes(expected) == servers[1][header_b:end_b], 'Retained loan data differs from SI'
    assert len(servers[1]) == len(servers[0]) - 32, 'Unexpected server size change'
    row = removed[0]
    club = struct.unpack_from('<i', row, 5)[0]
    start_day, start_year, end_day, end_year = struct.unpack_from('<4H', row, 9)
    print(f'PASS: removed 32-byte loan to club {club}: '
          f'start DOY/year {start_day}/{start_year}, end {end_day}/{end_year}.')
    print(f'PASS: table count {count_a} -> {count_b}; all {count_b} retained loans '
          'match SI byte-for-byte after footer-index renumbering.')
    for label, left, right in (
            ('before loan table', servers[0][:header_a], servers[1][:header_b]),
            ('after loan table', servers[0][end_a:], servers[1][end_b:])):
        assert len(left) == len(right), ('Unexpected outside-table size change', label)
        changed = sum(a != b for a, b in zip(left, right))
        print(f'SI save differences {label}: {changed} bytes; '
              'not reproduced as part of loan cancellation.')
    assert before == [hashlib.sha256(path.read_bytes()).digest() for path in paths], \
        'Comparison modified an input file'
    print('PASS: both input databases remain unchanged.')
    if destination is None:
        return

    source = root / folders[0]
    updated_server = servers[0][:header_a] + bytes(expected) + servers[0][end_a:]
    assert len(updated_server) == len(servers[0]) - 32
    assert controlled_loan_table(updated_server, anchor) == (header_a, count_b)
    assert updated_server[header_a:header_a + len(expected)] == servers[1][header_b:end_b]
    export_controlled_database(source, destination, {'server_db.dat': updated_server})
    assert before == [hashlib.sha256(path.read_bytes()).digest() for path in paths], \
        'Samples changed during loan export'
    print(f'PASS: created {destination}; only the loan table and database name change from A.')
    print('SI acceptance of this independently generated copy is still required; no retirement was set.')


def controlled_club_record_candidate(data, start, person_count):
    if start < 8 or start + 65 >= len(data) or data[start] != 10:
        return None
    club = struct.unpack_from('<i', data, start - 8)[0] + 1
    if not 0 < club < person_count or struct.unpack_from('<i', data, start - 4)[0] <= 0:
        return None
    count_position = start + 63 + data[start + 62] * 4
    if count_position + 2 > len(data):
        return None
    count = struct.unpack_from('<H', data, count_position)[0]
    roster_end = count_position + 2 + count * 4
    if roster_end + 9 > len(data):
        return None
    players = struct.unpack_from('<' + str(count) + 'i', data, count_position + 2)
    if list(players) != sorted(set(players)) or any(p < 0 or p >= person_count for p in players):
        return None
    footers = [roster_end + relative
               for relative in occurrences(data[roster_end:min(len(data), roster_end + 301)],
                                           struct.pack('<i', club))
               if roster_end + relative + 8 < len(data) and
               struct.unpack_from('<i', data, roster_end + relative + 4)[0] > 0 and
               data[roster_end + relative + 8] == 10]
    if len(footers) != 1:
        return None
    return club, start, footers[0] + 8


def controlled_club_span(data, club, person_count):
    candidates = set()
    for footer in occurrences(data, struct.pack('<i', club)):
        if footer + 9 >= len(data) or data[footer + 8] != 10:
            continue
        lower = max(0, footer - 1048576)
        previous = data.rfind(struct.pack('<i', club - 1), lower, max(0, footer - 70))
        while previous >= 0:
            candidate = controlled_club_record_candidate(data, previous + 8, person_count)
            if candidate is not None and candidate[0] == club and candidate[2] == footer + 8:
                candidates.add(candidate[1:])
                break
            previous = data.rfind(struct.pack('<i', club - 1), lower, previous)
    assert len(candidates) == 1, ('Missing or ambiguous controlled club record', club, candidates)
    return next(iter(candidates))


def controlled_club_field_members(data, value, field_offset, person_count):
    members = {}
    for position in occurrences(data, struct.pack('<i', value)):
        candidate = controlled_club_record_candidate(data, position - field_offset, person_count)
        if candidate is not None:
            club, start, end = candidate
            assert club not in members, ('Duplicate club field record', club, field_offset)
            members[club] = (start, end)
    return set(members)


def controlled_division_members(data, division, person_count):
    return controlled_club_field_members(data, division, 7, person_count)


def compare_controlled_european_swap(root, folders, clubs, destination=None):
    if destination is not None and destination.exists():
        raise FileExistsError(f'Refusing to overwrite {destination}')
    assert len(set(clubs)) == 2, 'Choose two distinct clubs: outgoing, incoming'
    paths = [root / folder / filename for folder in folders
             for filename in ('people_db.dat', 'server_db.dat', 'client_db.dat')]
    hashes = [hashlib.sha256(path.read_bytes()).digest() for path in paths]
    servers = [zlib.decompress((root / folder / 'server_db.dat').read_bytes()[9:])
               for folder in folders]
    people = zlib.decompress((root / folders[0] / 'people_db.dat').read_bytes()[9:])
    person_count = struct.unpack_from('<i', people)[0]
    del people
    assert len(servers[0]) == len(servers[1]), 'Unexpected SI server size change'
    spans = [[controlled_club_span(server, club, person_count) for club in clubs]
             for server in servers]
    competitions = [struct.unpack_from('<i', servers[0], start + 33)[0]
                    for start, end in spans[0]]
    assert competitions[0] >= 0 and competitions[1] == -1, \
        ('Expected outgoing participant and unassigned incoming club', competitions)
    generated = bytearray(servers[0])
    for index, club in enumerate(clubs):
        start, end = spans[0][index]
        reference_start, reference_end = spans[1][index]
        target = competitions[1 - index]
        struct.pack_into('<i', generated, start + 33, target)
        assert generated[start:end] == servers[1][reference_start:reference_end], \
            ('Additional SI club changes beyond European assignment', club)
        print(f'PASS: club {club}, European assignment +33: '
              f'{competitions[index]} -> {target}; complete club record matches SI.')
    competition = competitions[0]
    before = controlled_club_field_members(servers[0], competition, 33, person_count)
    after = controlled_club_field_members(servers[1], competition, 33, person_count)
    expected = (before - {clubs[0]}) | {clubs[1]}
    assert clubs[0] in before and clubs[1] not in before
    assert after == expected and len(after) == len(before), 'Unexpected European participants'
    assert controlled_club_field_members(generated, competition, 33, person_count) == expected
    print(f'PASS: European competition index {competition}: '
          f'{len(before)} -> {len(after)} participants; exact replacement.')
    identities = clubs + [struct.unpack_from('<i', servers[0], end - 4)[0]
                          for start, end in spans[0]]
    for identity in identities:
        pattern = struct.pack('<i', identity)
        for side, other in ((servers[0], servers[1]), (servers[1], servers[0])):
            assert all(side[position:position + 4] == other[position:position + 4]
                       for position in occurrences(side, pattern)), \
                ('SI also changed a club index/UID reference', identity)
    print('PASS: no other removed/added club-index or club-UID references in server.')
    allowed = {start + 33 + byte for start, end in spans[0] for byte in range(4)}
    changed = {position for position, (a, b) in enumerate(zip(servers[0], generated)) if a != b}
    assert changed <= allowed, ('Unexpected outside-field byte changes', changed - allowed)
    print(f'PASS: minimal server changes exactly {len(changed)} bytes; leagues, rosters, '
          'other club fields, rules and unrelated bytes remain original.')
    assert hashes == [hashlib.sha256(path.read_bytes()).digest() for path in paths]
    if destination is not None:
        export_controlled_database(root / folders[0], destination, {'server_db.dat': bytes(generated)})
        assert hashes == [hashlib.sha256(path.read_bytes()).digest() for path in paths], \
            'Samples changed during European export'
        print(f'PASS: created {destination}; only European assignments and metadata name change.')
        print('Independent SI acceptance and a separate career test are still required.')


def compare_controlled_league_swap(root, folders, clubs, destination=None):
    if destination is not None and destination.exists():
        raise FileExistsError(f'Refusing to overwrite {destination}')
    assert len(set(clubs)) == 2, 'Choose two distinct clubs'
    paths = [root / folder / name for folder in folders
             for name in ('people_db.dat', 'server_db.dat', 'client_db.dat')]
    hashes = [hashlib.sha256(path.read_bytes()).digest() for path in paths]
    servers = [zlib.decompress((root / folder / 'server_db.dat').read_bytes()[9:])
               for folder in folders]
    people = zlib.decompress((root / folders[0] / 'people_db.dat').read_bytes()[9:])
    person_count = struct.unpack_from('<i', people)[0]
    spans = [[controlled_club_span(server, club, person_count) for club in clubs]
             for server in servers]
    divisions = [struct.unpack_from('<i', servers[0], start + 7)[0] for start, end in spans[0]]
    assert len(set(divisions)) == 2 and all(d >= 0 for d in divisions), 'Choose two populated divisions'
    assert len(servers[0]) == len(servers[1]), 'SI changed the server size unexpectedly'
    generated = bytearray(servers[0])
    for index, club in enumerate(clubs):
        start, end = spans[0][index]
        target_start, target_end = spans[1][index]
        division = divisions[1 - index]
        struct.pack_into('<i', generated, start + 7, division)
        assert generated[start:end] == servers[1][target_start:target_end], \
            ('SI changed additional club fields', club)
        print(f'PASS: club {club}, current division {divisions[index]} -> {division}; '
              'all other club fields and roster bytes unchanged.')
    for index, division in enumerate(divisions):
        before = controlled_division_members(servers[0], division, person_count)
        after = controlled_division_members(servers[1], division, person_count)
        expected = (before - {clubs[index]}) | {clubs[1 - index]}
        assert clubs[index] in before and after == expected and len(before) == len(after), \
            ('SI division participants differ from the exact swap', division)
        assert controlled_division_members(generated, division, person_count) == expected
        print(f'PASS: division {division} has {len(before)} -> {len(after)} clubs; exact participant swap.')
    changed = [position for position, (a, b) in enumerate(zip(servers[0], generated)) if a != b]
    assert set(changed) <= {start + 7 + byte for start, end in spans[0] for byte in range(4)}
    print(f'PASS: generated server changes only two current-division int32 fields ({len(changed)} changed bytes).')
    print('SI also normalizes unrelated data; generated rules, histories and other files stay original.')
    assert hashes == [hashlib.sha256(path.read_bytes()).digest() for path in paths]
    if destination is not None:
        export_controlled_database(root / folders[0], destination, {'server_db.dat': bytes(generated)})
        assert hashes == [hashlib.sha256(path.read_bytes()).digest() for path in paths], \
            'Samples changed during league export'
        print(f'PASS: created {destination}; only the two division fields and metadata name change.')
        print('SI acceptance and a separate career test are still required.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(r'D:\Gry\FM08\Dane\db'))
    parser.add_argument('--compare-resave', action='store_true')
    parser.add_argument('--folders', nargs=2, default=('TEST_FMEXT_NATIVE', 'TEST_FMEXT_NATIVEEDIT'))
    parser.add_argument('--people-only', action='store_true')
    parser.add_argument('--write-order-probe', action='store_true')
    parser.add_argument('--compare-club', action='store_true')
    parser.add_argument('--write-juve-probe', action='store_true')
    parser.add_argument('--controlled-contract', action='store_true')
    parser.add_argument('--controlled-loan', action='store_true')
    parser.add_argument('--controlled-coownership', action='store_true')
    parser.add_argument('--controlled-league-swap', action='store_true')
    parser.add_argument('--controlled-european-swap', action='store_true')
    parser.add_argument('--club-indices', nargs=2, type=int)
    parser.add_argument('--uid', type=int)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    controlled_modes = sum((args.controlled_contract, args.controlled_loan,
                            args.controlled_coownership, args.controlled_league_swap,
                            args.controlled_european_swap))
    if controlled_modes > 1:
        parser.error('Choose only one controlled comparison mode')
    if args.output is not None and controlled_modes != 1:
        parser.error('--output requires a controlled comparison mode')
    if args.controlled_league_swap:
        if args.club_indices is None:
            parser.error('--controlled-league-swap requires --club-indices')
        compare_controlled_league_swap(args.root, args.folders, args.club_indices, args.output)
        return
    if args.controlled_european_swap:
        if args.club_indices is None:
            parser.error('--controlled-european-swap requires --club-indices outgoing incoming')
        compare_controlled_european_swap(args.root, args.folders, args.club_indices, args.output)
        return
    if args.controlled_coownership:
        if args.uid is None:
            parser.error('--controlled-coownership requires --uid')
        compare_controlled_coownership(args.root, args.folders, args.uid, args.output)
        return
    if args.controlled_loan:
        if args.uid is None or args.controlled_contract:
            parser.error('--controlled-loan requires --uid and cannot be combined with --controlled-contract')
        compare_controlled_loan(args.root, args.folders, args.uid, args.output)
        return
    if args.controlled_contract:
        if args.uid is None:
            parser.error('--controlled-contract requires --uid')
        compare_controlled_contract(args.root, args.folders, args.uid, args.output)
        return
    if args.write_juve_probe:
        write_juve_probe(args.root)
        return
    if args.compare_club:
        compare_club(args.root)
        return
    if args.write_order_probe:
        write_order_probe(args.root)
        return
    if args.compare_resave:
        compare_resave(args.root, args.folders, args.people_only)
        return
    folders = ('TEST_KONTROLA', 'TEST_EMERYTURA', 'TEST_NOWY')
    for filename in sorted(path.name for path in (args.root / folders[0]).glob('*.dat')):
        print(f'\n=== {filename} ===')
        baseline = None
        for folder in folders:
            raw = (args.root / folder / filename).read_bytes()
            compressed = len(raw) >= 11 and raw[9] & 15 == 8 and int.from_bytes(raw[9:11], 'big') % 31 == 0
            if compressed:
                decompressor = zlib.decompressobj()
                data = decompressor.decompress(raw[9:]) + decompressor.flush()
                if not decompressor.eof or decompressor.unused_data:
                    raise ValueError(f'Unexpected compressed stream: {folder}/{filename}')
            else:
                data = raw
                print('  No zlib wrapper: comparing raw bytes')
            print(f'{folder}: raw={len(raw)}, expanded={len(data)}, sha256={hashlib.sha256(data).hexdigest()}')
            if baseline is None:
                baseline = data
            else:
                print(f'  Size delta={len(data) - len(baseline)}, identical={data == baseline}')
                if data != baseline:
                    limit = min(len(data), len(baseline))
                    first = 0
                    while first + 65536 <= limit and data[first:first + 65536] == baseline[first:first + 65536]:
                        first += 65536
                    while first < limit and data[first] == baseline[first]:
                        first += 1
                    print(f'  First difference={first:#x}')
                    print(f'  Baseline: {baseline[max(0, first - 8):first + 32].hex(" ")}')
                    print(f'  Modified: {data[max(0, first - 8):first + 32].hex(" ")}')
            if filename in ('people_db.dat', 'server_db.dat'):
                print(f'  Header: {data[:64].hex(" ")}')
                inspect(data, 1394631309)
                inspect(data, 1394631308)
                if folder == 'TEST_NOWY':
                    for name in ('Brak', 'Imienia'):
                        for name_position in list(occurrences(data, name.encode('utf-16le')))[:5]:
                            print(f'  Name {name}: offset={name_position:#x}, bytes={data[max(0, name_position - 32):name_position + 64].hex(" ")}')
                if filename == 'server_db.dat':
                    retirement_table(data)
                else:
                    tables = inspect(data, 11133)
                    print(f'  First four header integers: {struct.unpack_from("<4i", data)}')
                    count = struct.unpack_from('<i', data, 8)[0]
                    if folder == 'TEST_NOWY':
                        for location in occurrences(data, struct.pack('<i', 2096)):
                            if location < 15 or data[location + 11:location + 15] != bytes.fromhex('6c 07 10 27'):
                                continue
                            record = location - 15
                            own_index = struct.unpack_from('<i', data, record)[0]
                            print(f'  BUFFON PERSON CANDIDATE: offset={location}, start={record}, index={own_index}, bytes={data[record:record + 48].hex(" ")}')
                            for footer in range(record + 200, record + 4096):
                                if struct.unpack_from('<i', data, footer)[0] == own_index and struct.unpack_from('<i', data, footer + 4)[0] > 0:
                                    print(f'  BUFFON FOOTER CANDIDATE: relative={footer - record}, bytes={data[footer:footer + 24].hex(" ")}')
                    for table_start in tables:
                        payload_start = table_start - 81
                        assert struct.unpack_from('<i', data, payload_start - 4)[0] == count
                        secondary_count = struct.unpack_from('<i', data, 4)[0]
                        secondary_start = payload_start - 4 - secondary_count * 17
                        assert struct.unpack_from('<i', data, secondary_start - 4)[0] == secondary_count
                        print(f'  STRUCTURE: person_end={secondary_start - 4}, secondary_start={secondary_start}, player_start={payload_start}')
                        print(f'  SECONDARY FINAL: {data[payload_start - 21:payload_start - 4].hex(" ")}')
                        print(f'  PLAYER FINAL: {data[payload_start + (count - 1) * 89:payload_start + count * 89].hex(" ")}')
                        for row_index, (stored_index, stored_identity) in enumerate(struct.iter_unpack('<ii81x', data[table_start:table_start + count * 89])):
                            if stored_index != row_index:
                                mismatch = table_start + row_index * 89
                                print(f'  T89 FIRST DISCONTINUITY: row={row_index}, stored={stored_index}, identity={stored_identity}, offset={mismatch:#x}, bytes={data[mismatch - 32:mismatch + 96].hex(" ")}')
                                break
                        else:
                            print('  T89 indices: complete contiguous table')
                        last_row = table_start + (count - 1) * 89
                        print(f'  Final T89 row: offset={last_row:#x}, fields={struct.unpack_from("<2i", data, last_row)}, bytes={data[last_row:last_row + 89].hex(" ")}')
                    inspect(data, 1394631301)
                    if folder == 'TEST_NOWY':
                        position = data.find(struct.pack('<i', 1394631308))
                        print(f'  New player attribute boundary: {data[position - 32:position + 128].hex(" ")}')
                        person_end = data.find(struct.pack('<i', 1394631309))
                        template_start = person_end - 230
                        print(f'  PERSON TEMPLATE: {data[template_start:person_end + 4].hex(" ")}')
                        for relative in range(0, 234, 8):
                            print(f'  TEMPLATE +{relative}: {data[template_start + relative:min(template_start + relative + 8, person_end + 4)].hex(" ")}')
                        for relative in range(234 - 6):
                            if data[template_start + relative:template_start + relative + 6] == bytes.fromhex('6c 07 ff ff ff ff'):
                                print(f'  NAME MARKER +{relative}: {struct.unpack_from("<4i", data, template_start + relative + 6)}')
                        for offset in range(person_end - 288, person_end + 32, 16):
                            print(f'  PERSON {offset:#x}: {data[offset:offset + 16].hex(" ")}')
                        for identity in (334475, 347896, 273507, 83407, 83408, 192717, 192718):
                            positions = list(occurrences(data, struct.pack('<i', identity)))
                            print(f'  INDEX {identity}: {positions[:30]}')
                if folder == 'TEST_NOWY' and filename == 'server_db.dat':
                    for identity in (1394631310, 1394631311):
                        position = data.find(struct.pack('<i', identity))
                        print(f'  NAME FOOTER {identity}: offset={position}, bytes={data[position - 60:position + 8].hex(" ")}')
                        name = 'Brak' if identity == 1394631310 else 'Imienia'
                        name_position = next(offset for offset in occurrences(data, name.encode('utf-16le')) if position - 40 <= offset < position)
                        payload = name_position - 5
                        name_count = struct.unpack_from('<i', data, payload - 4)[0]
                        for name_index in range(name_count):
                            length = struct.unpack_from('<i', data, payload + 1)[0]
                            assert 0 < length < 1000
                            footer = payload + 14 + length * 2
                            assert struct.unpack_from('<i', data, footer)[0] == name_index
                            if name_index < 2:
                                print(f'  NATIVE NAME: count={name_count}, index={name_index}, value={data[payload + 5:payload + 5 + length * 2].decode("utf-16le")}, uid={struct.unpack_from("<i", data, footer + 4)[0]}')
                            payload = footer + 8
    print('\nPASS: compressed streams decoded and checksums validated; other files compared raw; source files were not modified.')


if __name__ == '__main__':
    main()