"""Pure in-memory COMP schema helpers for the isolated Polish third-tier prototype.

No filesystem mutation occurs on import or function calls. Proven on original 802:
CLIENT fixed54; SERVER68+7*n; LANG three names, two suffix bytes, no NUL for empty.
Creation acceptance in SI/game is NOT established by this structural module.
"""
import struct


def i32(data, offset):
    return struct.unpack_from('<i', data, offset)[0]


def u32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


def _hits(data, needle):
    offset = -1
    while True:
        offset = data.find(needle, offset + 1)
        if offset < 0:
            return
        yield offset


def find_client_comp_table(data, expected_count=1332):
    candidates = []
    for header in _hits(data, struct.pack('<i', expected_count)):
        start = header + 4
        end = start + expected_count * 54
        if end > len(data):
            continue
        if any(i32(data, start + index * 54 + 46) != index
               for index in range(expected_count)):
            continue
        records = []
        for index in range(expected_count):
            at = start + index * 54
            records.append(dict(index=index, uid=i32(data, at + 50), start=at,
                                end=at + 54, raw=data[at:at + 54]))
        if len({row['uid'] for row in records}) != expected_count:
            continue
        candidates.append(dict(count=expected_count, count_offset=header,
                               start=start, end=end, records=records))
    if len(candidates) != 1:
        raise ValueError('CLIENT COMP table missing/ambiguous')
    return candidates[0]


def find_server_comp_table(data, client_table):
    candidates = []
    count = client_table['count']
    first = client_table['records'][0]['raw'][:32]
    for start in _hits(data, first):
        if start < 4 or i32(data, start - 4) != count:
            continue
        records = []
        at = start
        try:
            for client in client_table['records']:
                history_count = u32(data, at + 42)
                end = at + 68 + history_count * 7
                if end > len(data):
                    raise ValueError('COMP variable tail outside data')
                raw = data[at:end]
                if raw[:32] + raw[46 + history_count * 7:] != client['raw']:
                    raise ValueError('SERVER/CLIENT COMP mirror mismatch')
                records.append(dict(index=client['index'], uid=client['uid'],
                                    start=at, end=end, raw=raw,
                                    variable_count=history_count))
                at = end
        except (ValueError, struct.error):
            continue
        candidates.append(dict(count=count, count_offset=start - 4,
                               start=start, end=at, records=records))
    if len(candidates) != 1:
        raise ValueError('SERVER COMP table missing/ambiguous')
    return candidates[0]


def parse_language_comp_record(data, offset):
    start = offset
    uid = i32(data, offset)
    offset += 4
    names = []
    suffixes = []
    for field in range(3):
        units = u32(data, offset)
        offset += 4
        if units > 4096 or offset + units * 2 > len(data):
            raise ValueError('COMP language string length')
        names.append(data[offset:offset + units * 2].decode('utf-16-le'))
        offset += units * 2
        if units:
            if data[offset:offset + 2] != bytes(2):
                raise ValueError('COMP language nonempty string terminator')
            offset += 2
        if field < 2:
            suffixes.append(data[offset])
            offset += 1
    return dict(uid=uid, names=names, suffixes=suffixes, start=start,
                end=offset, raw=data[start:offset])


def find_language_comp_table(data, competition_uids):
    expected = set(competition_uids)
    count = len(expected)
    candidates = []
    for header in _hits(data, struct.pack('<i', count)):
        at = header + 4
        seen = set()
        records = []
        try:
            for _ in range(count):
                row = parse_language_comp_record(data, at)
                if row['uid'] not in expected or row['uid'] in seen:
                    raise ValueError('COMP language UID set differs')
                records.append(row)
                seen.add(row['uid'])
                at = row['end']
        except (ValueError, struct.error, IndexError, UnicodeError):
            continue
        if seen == expected:
            candidates.append(dict(count=count, count_offset=header,
                                   start=header + 4, end=at, records=records))
    if len(candidates) != 1:
        raise ValueError('LANG COMP table missing/ambiguous')
    return candidates[0]


def make_language_comp_record(uid, names, suffixes):
    if len(names) != 3 or len(suffixes) != 2:
        raise ValueError('COMP requires three names and two suffixes')
    out = bytearray(struct.pack('<i', uid))
    for index, name in enumerate(names):
        raw = name.encode('utf-16-le')
        out.extend(struct.pack('<I', len(raw) // 2))
        out.extend(raw)
        if raw:
            out.extend(bytes(2))
        if index < 2:
            out.append(suffixes[index])
    return bytes(out)


def append_record(data, table, record):
    """Return a new bytes object; existing table body and trailing data preserved."""
    header = table['count_offset']
    end = table['end']
    return (data[:header] + struct.pack('<i', table['count'] + 1)
            + data[header + 4:end] + record + data[end:])


def clone_server_comp_record(table, template_uid, new_uid, level=2):
    if new_uid in {row['uid'] for row in table['records']}:
        raise ValueError('COMP UID collision')
    source = next(row for row in table['records'] if row['uid'] == template_uid)
    if source['variable_count'] != 0 or len(source['raw']) != 68:
        raise ValueError('Prototype only clones a simple 68-byte competition')
    raw = bytearray(source['raw'])
    raw[19] = level
    struct.pack_into('<ii', raw, 60, table['count'], new_uid)
    return bytes(raw)


def client_mirror_of_server_record(raw):
    count = u32(raw, 42)
    if len(raw) != 68 + count * 7:
        raise ValueError('SERVER COMP record length')
    return raw[:32] + raw[46 + count * 7:]
