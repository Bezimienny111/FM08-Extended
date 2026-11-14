import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib

from compare_native_player_tests import controlled_club_span, export_controlled_database, occurrences

if not __debug__:
    raise RuntimeError("Native database creation requires enabled validation; do not use python -O")


PROFILE_SERVER_SHA = "ac8624d8aefe4f969467e6524d08d744a6bd2f28779cc94dac8c22a378aa36c3"
TEAM_INDEX = 23624
TREE_INDEX = 23394
TEAM_UID = 1800000087
TREE_COUNT_OFFSET = 983048
CLUB_COUNT_OFFSET = 22280931
CLIENT_COUNT_OFFSET = 981485


def unique(data, pattern):
    positions = list(occurrences(data, pattern))
    if len(positions) != 1:
        raise ValueError("Missing or ambiguous controlled identity: " + pattern.hex())
    return positions[0]


def patched(data, edits):
    result = data
    for offset, length, replacement in sorted(edits, reverse=True):
        result = result[:offset] + replacement + result[offset + length:]
    return result


def language_blocks(raw):
    count = raw[9]
    entries = [struct.unpack_from("<ii", raw, 10 + index * 8) for index in range(count)]
    assert count == 20 and entries[0][1] == 1 + count * 8
    assert len(set(language for language, _ in entries)) == count
    blocks = []
    for index, (language, offset) in enumerate(entries):
        end = entries[index + 1][1] + 9 if index + 1 < count else len(raw)
        assert 9 + offset < end <= len(raw)
        decoder = zlib.decompressobj()
        block = decoder.decompress(raw[offset + 9:end]) + decoder.flush()
        assert decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail
        blocks.append((language, block))
    return blocks


def assemble_languages(before, result):
    offset = 1 + len(result) * 8
    header = bytearray(before[:9] + bytes([len(result)]))
    for language, compressed in result:
        header.extend(struct.pack("<ii", language, offset))
        offset += len(compressed)
    return bytes(header) + b"".join(compressed for _, compressed in result)


def create_language(before, si_after):
    original = language_blocks(before)
    reference = language_blocks(si_after)
    assert [language for language, _ in original] == [language for language, _ in reference]
    result = []
    evidence = []
    entity = struct.pack("<i", TEAM_UID) + bytes(24)
    for (language, source), (_, target) in zip(original, reference):
        insert = unique(target, struct.pack("<i", TEAM_UID))
        assert target[insert:insert + 28] == entity
        normalized = target[:insert] + target[insert + 28:]
        assert len(normalized) == len(source)
        count_offset = next(index for index, (a, b) in enumerate(zip(source, normalized)) if a != b)
        assert struct.unpack_from("<i", source, count_offset)[0] == TREE_INDEX
        assert struct.unpack_from("<i", normalized, count_offset)[0] == TREE_INDEX + 1
        generated = patched(source, [(count_offset, 4, struct.pack("<i", TREE_INDEX + 1)), (insert, 0, entity)])
        assert generated == target, "Language edits do not reproduce the entire SI block"
        result.append((language, zlib.compress(generated)))
        evidence.append({"language": language, "count_offset": count_offset, "insert_offset": insert})
    output = assemble_languages(before, result)
    assert language_blocks(output) == reference
    return output, evidence


def create(before, reference, source, parent, parent_tree):
    assert hashlib.sha256((before / "server_db.dat").read_bytes()).hexdigest() == PROFILE_SERVER_SHA
    for name in ("server_db.dat", "client_db.dat", "people_db.dat", "lang_db.dat"):
        assert (before / name).read_bytes() == (source / name).read_bytes(), "Source differs from the pinned SI A: " + name
    a = zlib.decompress((before / "server_db.dat").read_bytes()[9:])
    b = zlib.decompress((reference / "server_db.dat").read_bytes()[9:])
    ca = zlib.decompress((before / "client_db.dat").read_bytes()[9:])
    cb = zlib.decompress((reference / "client_db.dat").read_bytes()[9:])
    people = zlib.decompress((source / "people_db.dat").read_bytes()[9:])
    person_count = struct.unpack_from("<i", people)[0]
    for data in (a, ca, people):
        assert struct.pack("<i", TEAM_UID) not in data, "New team UID already exists"
    parent_start, parent_end = controlled_club_span(a, parent, person_count)
    parent_uid = struct.unpack_from("<i", a, parent_end - 4)[0]
    parent_footer = unique(a, struct.pack("<ii", parent_tree, parent_uid))
    marker = bytes.fromhex("ff00006c0700000000")
    name_start = a.rfind(marker, max(0, parent_footer - 2048), parent_footer)
    assert name_start >= 0
    family_offset = name_start + unique(a[name_start:parent_footer], b"\x01" + struct.pack("<i", parent))
    assert struct.unpack_from("<i", a, TREE_COUNT_OFFSET)[0] == TREE_INDEX
    assert struct.unpack_from("<i", a, CLUB_COUNT_OFFSET)[0] == TEAM_INDEX
    assert struct.unpack_from("<i", ca, CLIENT_COUNT_OFFSET)[0] == TREE_INDEX

    native_footer = unique(b, struct.pack("<ii", TEAM_INDEX, TEAM_UID))
    native = bytearray(b[native_footer - 105:native_footer + 8])
    assert len(native) == 113 and native[0] == 10 and native[62:65] == bytes(3)
    assert struct.unpack_from("<ii", native, 87) == (9, 815)
    previous_uid = struct.unpack_from("<i", b, native_footer - 109)[0]
    previous_identity = struct.pack("<ii", TEAM_INDEX - 1, previous_uid)
    native_insert = unique(a, previous_identity) + 8
    assert b[native_footer - 113:native_footer - 105] == previous_identity
    tree_footer = unique(b, struct.pack("<ii", TREE_INDEX, TEAM_UID))
    tree = b[tree_footer - 204:tree_footer + 8]
    assert len(tree) == 212 and tree[0] == 0
    tree_identity = struct.pack("<ii", TREE_INDEX - 1, previous_uid)
    assert b[tree_footer - 212:tree_footer - 204] == tree_identity
    tree_insert = unique(a, tree_identity) + 8
    client_footer = unique(cb, struct.pack("<ii", TREE_INDEX, TEAM_UID))
    client = cb[client_footer - 35:client_footer + 8]
    assert len(client) == 43 and client[0] == 0
    assert cb[client_footer - 43:client_footer - 35] == tree_identity
    client_insert = unique(ca, tree_identity) + 8
    struct.pack_into("<i", native, 91, parent_tree)
    new_family = b"\x02" + struct.pack("<ii", parent, TEAM_INDEX)
    server = patched(a, [
        (TREE_COUNT_OFFSET, 4, struct.pack("<i", TREE_INDEX + 1)),
        (CLUB_COUNT_OFFSET, 4, struct.pack("<i", TEAM_INDEX + 1)),
        (family_offset, 5, new_family),
        (tree_insert, 0, tree),
        (native_insert, 0, bytes(native)),
    ])
    client_data = patched(ca, [
        (CLIENT_COUNT_OFFSET, 4, struct.pack("<i", TREE_INDEX + 1)),
        (client_insert, 0, client),
    ])
    assert len(server) == len(a) + 329 and len(client_data) == len(ca) + 43
    assert people == zlib.decompress((source / "people_db.dat").read_bytes()[9:])
    language, language_evidence = create_language((before / "lang_db.dat").read_bytes(), (reference / "lang_db.dat").read_bytes())
    return {"server_db.dat": server, "client_db.dat": client_data}, language, {
        "parent_index": parent, "parent_uid": parent_uid, "parent_tree_index": parent_tree,
        "team_index": TEAM_INDEX, "team_uid": TEAM_UID, "team_tree_index": TREE_INDEX,
        "server_count_offset": CLUB_COUNT_OFFSET, "server_tree_count_offset": TREE_COUNT_OFFSET,
        "parent_family_offset": family_offset, "native_insert_offset": native_insert,
        "tree_insert_offset": tree_insert, "client_insert_offset": client_insert,
        "language_changes": language_evidence, "status": "native_creation_generated_not_yet_accepted_in_si",
    }


def create_batch(before, reference, source, parents):
    if not parents or len(set(parent for parent, _ in parents)) != len(parents):
        raise ValueError("Missing or duplicate U23 parents")
    single, _, evidence = create(before, reference, source, *parents[0])
    server = zlib.decompress((source / "server_db.dat").read_bytes()[9:])
    client = zlib.decompress((source / "client_db.dat").read_bytes()[9:])
    people = zlib.decompress((source / "people_db.dat").read_bytes()[9:])
    person_count = struct.unpack_from("<i", people)[0]
    footer = unique(single["server_db.dat"], struct.pack("<ii", TEAM_INDEX, TEAM_UID))
    native = single["server_db.dat"][footer - 105:footer + 8]
    footer = unique(single["server_db.dat"], struct.pack("<ii", TREE_INDEX, TEAM_UID))
    tree = single["server_db.dat"][footer - 204:footer + 8]
    footer = unique(single["client_db.dat"], struct.pack("<ii", TREE_INDEX, TEAM_UID))
    client_node = single["client_db.dat"][footer - 35:footer + 8]
    native_nodes, tree_nodes, client_nodes, teams = [], [], [], []
    edits = [
        (TREE_COUNT_OFFSET, 4, struct.pack("<i", TREE_INDEX + len(parents))),
        (CLUB_COUNT_OFFSET, 4, struct.pack("<i", TEAM_INDEX + len(parents))),
    ]
    for number, (parent, parent_tree) in enumerate(parents):
        uid, club_index, tree_index = TEAM_UID + number, TEAM_INDEX + number, TREE_INDEX + number
        for data in (server, client, people):
            assert struct.pack("<i", uid) not in data, "Allocated U23 UID already exists"
        start, end = controlled_club_span(server, parent, person_count)
        parent_uid = struct.unpack_from("<i", server, end - 4)[0]
        parent_footer = unique(server, struct.pack("<ii", parent_tree, parent_uid))
        marker = server.rfind(bytes.fromhex("ff00006c0700000000"), parent_footer - 2048, parent_footer)
        assert marker >= 0
        family = marker + unique(server[marker:parent_footer], b"\x01" + struct.pack("<i", parent))
        edits.append((family, 5, b"\x02" + struct.pack("<ii", parent, club_index)))
        node = bytearray(native)
        struct.pack_into("<i", node, 91, parent_tree)
        struct.pack_into("<ii", node, 105, club_index, uid)
        native_nodes.append(bytes(node))
        node = bytearray(tree)
        struct.pack_into("<ii", node, 204, tree_index, uid)
        tree_nodes.append(bytes(node))
        node = bytearray(client_node)
        struct.pack_into("<ii", node, 35, tree_index, uid)
        client_nodes.append(bytes(node))
        teams.append({"parent_index": parent, "parent_uid": parent_uid, "parent_tree_index": parent_tree,
                      "team_index": club_index, "team_uid": uid, "team_tree_index": tree_index,
                      "source_family_offset": family})
    edits.extend([(evidence["tree_insert_offset"], 0, b"".join(tree_nodes)),
                  (evidence["native_insert_offset"], 0, b"".join(native_nodes))])
    generated_server = patched(server, edits)
    generated_client = patched(client, [
        (CLIENT_COUNT_OFFSET, 4, struct.pack("<i", TREE_INDEX + len(parents))),
        (evidence["client_insert_offset"], 0, b"".join(client_nodes)),
    ])
    raw_language = (source / "lang_db.dat").read_bytes()
    blocks = language_blocks(raw_language)
    language_edits = evidence["language_changes"]
    entities = b"".join(struct.pack("<i", team["team_uid"]) + bytes(24) for team in teams)
    compressed, expected_blocks = [], []
    for (language, block), change in zip(blocks, language_edits):
        assert language == change["language"]
        for team in teams:
            assert struct.pack("<i", team["team_uid"]) not in block
        generated = patched(block, [
            (change["count_offset"], 4, struct.pack("<i", TREE_INDEX + len(parents))),
            (change["insert_offset"], 0, entities),
        ])
        expected_blocks.append((language, generated))
        compressed.append((language, zlib.compress(generated)))
    language = assemble_languages(raw_language, compressed)
    assert language_blocks(language) == expected_blocks
    assert len(generated_server) == len(server) + len(parents) * 329
    assert len(generated_client) == len(client) + len(parents) * 43
    return {"server_db.dat": generated_server, "client_db.dat": generated_client}, language, {
        "status": "batch_native_u23_created_squads_pending", "teams": teams,
        "language_changes": language_edits, "protected_person_count": person_count,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Controlled native U23 creation from the hash-pinned Inter SI A/B profile.")
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--parent", type=int, action="append", required=True)
    parser.add_argument("--parent-tree", type=int, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if len(args.parent) != len(args.parent_tree):
        parser.error("Each parent requires a corresponding parent-tree index")
    parents = list(zip(args.parent, args.parent_tree))
    payloads, language, report = (create(args.before, args.reference, args.source, *parents[0])
                                  if len(parents) == 1 else create_batch(args.before, args.reference, args.source, parents))
    export_controlled_database(args.source, args.output, payloads)
    (args.output / "lang_db.dat").write_bytes(language)
    for path in args.source.rglob("*"):
        if path.is_file() and path.name not in ("server_db.dat", "client_db.dat", "lang_db.dat") and path.suffix.lower() != ".xml":
            assert path.read_bytes() == (args.output / path.relative_to(args.source)).read_bytes()
    with (args.output.parent / (args.output.name + "_creation.json")).open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print("PASS: native U23 teams created:", len(parents), "; people unchanged.")
    print("PASS: all 20 language blocks validated; indexed offsets rebuilt.")
    print("Created controlled stage:", args.output)
