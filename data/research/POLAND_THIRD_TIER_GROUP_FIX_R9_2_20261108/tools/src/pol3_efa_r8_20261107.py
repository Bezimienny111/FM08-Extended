"""Verified FM08 comps.efa reader and append-only packer (source/derived output only).

Public API:
  parse(raw: bytes) -> dict
  repack(archive: dict) -> bytes
  add_member(archive: dict, member_path: str, content: bytes) -> dict
  get_member(archive: dict, member_path: str) -> bytes
  verify_archive(path: Path) -> dict
  extract_templates(workspace: Path, output: Path) -> dict

Archive dictionaries contain decoded data bytes, an index tree and a member map.
add_member returns a new parsed archive and never changes its input. Existing
members cannot be replaced. No public function writes an input archive.
Only the uncompressed-member comps.efa variant verified on the original base
and update-802 resources is supported; unknown formats are rejected.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import struct
import zlib

OUTER_HEADER = b"\x02\x01afe.\x02\x00\x00"
INDEX_HEADER = b"\x02\x01fmf.\x02\x00\x00"
SOURCE_PATHS = ("data/comps.efa", "data/updates/update-802/data/comps.efa")
EXPECTED_SOURCE_SHA256 = {
    "data/comps.efa": "a16bdb9b26454374c1f224b96500e8c4a9e3dd134c83d5822acd611e358b3ead",
    "data/updates/update-802/data/comps.efa": "d5aed6f0058c10a1c4688474e1b2c9c819c052ccdf785d54e368409259473d78",
}
MAX_INDEX_BYTES = 16 * 1024 * 1024


def _require(value, message):
    if not value:
        raise ValueError(message)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _path(value):
    _require(isinstance(value, str) and value and "\\" not in value, "Expected a relative POSIX member path")
    parts = value.split("/")
    _require(all(part not in ("", ".", "..") and ":" not in part and "\x00" not in part for part in parts), "Unsafe member path")
    return "/".join(parts)


def _string(value):
    data = value.encode("utf-16-le")
    _require("\x00" not in value, "Index strings may not contain NUL")
    return struct.pack("<I", len(data) // 2) + data + (b"\x00\x00" if data else b"")


def _encode_tree(tree, depth=0):
    _require(depth < 128, "Directory nesting limit")
    files, directories = tree["files"], tree["directories"]
    _require(len(files) <= 65535 and len(directories) <= 65535, "Directory count exceeds uint16")
    result = bytearray(_string(tree["name"]) + struct.pack("<H", len(files)))
    for entry in files:
        result += _string(entry["name"]) + _string(entry["extension"])
        result += struct.pack("<III", entry["offset"], entry["size"], entry["stored_size"])
    result += struct.pack("<H", len(directories))
    for child in directories:
        result += _encode_tree(child, depth + 1)
    return bytes(result)


def parse(raw: bytes) -> dict:
    _require(isinstance(raw, bytes) and len(raw) >= 23, "Truncated EFA input")
    _require(raw[:9] == OUTER_HEADER, "Unsupported EFA outer header")
    body = bytes(value ^ 255 for value in raw[9:])
    offset = struct.unpack_from("<I", body)[0]
    _require(5 <= offset <= len(body) - 9, "Invalid EFA index offset")
    _require(body[offset:offset + 9] == INDEX_HEADER, "Unsupported EFA index header")
    decoder = zlib.decompressobj()
    index = decoder.decompress(body[offset + 9:], MAX_INDEX_BYTES + 1)
    _require(len(index) <= MAX_INDEX_BYTES and not decoder.unconsumed_tail, "EFA index exceeds size limit")
    index += decoder.flush()
    _require(decoder.eof and not decoder.unused_data and len(index) <= MAX_INDEX_BYTES, "Invalid or trailing EFA index stream")
    position = 0
    members = {}
    folded = set()
    occupied = []

    def number(fmt):
        nonlocal position
        size = struct.calcsize(fmt)
        _require(position + size <= len(index), "Truncated EFA index number")
        value = struct.unpack_from(fmt, index, position)[0]
        position += size
        return value

    def text():
        nonlocal position
        count = number("<I")
        _require(count <= (len(index) - position) // 2, "Invalid EFA string length")
        value = index[position:position + count * 2].decode("utf-16-le")
        position += count * 2
        if count:
            _require(index[position:position + 2] == b"\x00\x00", "Missing EFA string terminator")
            position += 2
        _require("\x00" not in value, "Embedded NUL in EFA index")
        return value

    def directory(parent="", depth=0):
        _require(depth < 128, "Directory nesting limit")
        name = text()
        _require(not parent or name, "Empty nested directory name")
        if name:
            _require("/" not in name and "\\" not in name and name not in (".", ".."), "Invalid directory name")
        path = "/".join(part for part in (parent, name) if part)
        tree = {"name": name, "files": [], "directories": []}
        for _ in range(number("<H")):
            stem, extension = text(), text()
            member_path = _path("/".join(part for part in (path, stem + extension) if part))
            file_offset, size, stored = number("<I"), number("<I"), number("<I")
            _require(size == stored, "Compressed EFA members are not supported by this profile")
            _require(file_offset >= 5 and file_offset + stored <= offset, "Member outside EFA payload")
            _require(member_path.casefold() not in folded, "Duplicate case-insensitive EFA member")
            folded.add(member_path.casefold())
            members[member_path] = body[file_offset:file_offset + stored]
            occupied.append((file_offset, file_offset + stored))
            tree["files"].append({"name": stem, "extension": extension, "offset": file_offset, "size": size, "stored_size": stored})
        directory_names = set()
        for _ in range(number("<H")):
            child = directory(path, depth + 1)
            _require(child["name"].casefold() not in directory_names, "Duplicate EFA directory")
            directory_names.add(child["name"].casefold())
            tree["directories"].append(child)
        return tree

    tree = directory()
    _require(tree["name"] == "", "Expected the verified empty root directory")
    _require(position == len(index), "Unread trailing bytes in EFA index")
    for previous, current in zip(sorted(occupied), sorted(occupied)[1:]):
        _require(previous[1] <= current[0], "Overlapping EFA members")
    _require(_encode_tree(tree) == index, "EFA index failed exact serialization check")
    return {"header": raw[:9], "data": body[:offset], "tree": tree, "members": members,
            "index_offset": offset, "index_bytes": index, "source_sha256": _sha(raw)}


def repack(archive: dict) -> bytes:
    _require(archive["header"] == OUTER_HEADER, "Unsupported output header")
    data = bytearray(archive["data"])
    _require(len(data) >= 5, "Truncated decoded payload")
    struct.pack_into("<I", data, 0, len(data))
    index = _encode_tree(archive["tree"])
    _require(len(index) <= MAX_INDEX_BYTES, "Output index size limit")
    body = bytes(data) + INDEX_HEADER + zlib.compress(index)
    raw = OUTER_HEADER + bytes(value ^ 255 for value in body)
    # Validate offsets/counts and use payload content, rather than trusting member metadata.
    parsed = parse(raw)
    _require(parsed["members"] == archive["members"], "Repacked member contents differ")
    return raw


def get_member(archive: dict, member_path: str) -> bytes:
    return archive["members"][_path(member_path)]


def add_member(archive: dict, member_path: str, content: bytes) -> dict:
    member_path = _path(member_path)
    _require(isinstance(content, bytes), "Member content must be bytes")
    if member_path.casefold() in {name.casefold() for name in archive["members"]}:
        raise FileExistsError("Refusing to replace EFA member: " + member_path)
    result = copy.deepcopy(archive)
    parts = member_path.split("/")
    directory = result["tree"]
    for name in parts[:-1]:
        children = [child for child in directory["directories"] if child["name"].casefold() == name.casefold()]
        if children:
            directory = children[0]
        else:
            child = {"name": name, "files": [], "directories": []}
            directory["directories"].append(child)
            directory = child
    filename = parts[-1]
    extension = PurePosixPath(filename).suffix
    stem = filename[:-len(extension)] if extension else filename
    _require(bool(stem), "Empty member stem")
    old_data = result["data"]
    directory["files"].append({"name": stem, "extension": extension, "offset": len(old_data), "size": len(content), "stored_size": len(content)})
    result["data"] = old_data + content
    result["members"][member_path] = content
    output = parse(repack(result))
    _require(all(output["members"][name] == data for name, data in archive["members"].items()), "Append changed an existing member")
    _require(archive["data"] == old_data, "Append changed its input archive")
    return output


def verify_archive(path: Path) -> dict:
    raw = path.read_bytes()
    archive = parse(raw)
    packed = repack(archive)
    _require(packed == raw, "Original archive did not roundtrip byte-for-byte")
    synthetic = b'<properties nation="999999"><integer id="version" value="1"/></properties>'
    path_in_archive = "pol/__efa_validation_only__.xml"
    appended = add_member(archive, path_in_archive, synthetic)
    _require(get_member(appended, path_in_archive) == synthetic, "Synthetic append missing")
    _require(parse(packed)["members"] == archive["members"], "Roundtrip changed members")
    _require(path.read_bytes() == raw, "Input archive changed during verification")
    return {"source": str(path), "source_sha256": _sha(raw), "member_count": len(archive["members"]),
            "index_offset": archive["index_offset"], "index_bytes": len(archive["index_bytes"]),
            "exact_archive_roundtrip": True, "append_preserves_existing_members": True, "input_unchanged": True}


def extract_templates(workspace: Path, output: Path) -> dict:
    workspace = workspace.resolve()
    output = output.resolve()
    _require(not output.exists(), "Template output already exists; refusing overwrite")
    sources = {}
    verification = []
    for relative in SOURCE_PATHS:
        path = workspace / relative
        raw = path.read_bytes()
        _require(_sha(raw) == EXPECTED_SOURCE_SHA256[relative], "Reference archive digest differs: " + relative)
        sources[relative] = parse(raw)
        verification.append(verify_archive(path))
    selections = [
        ("sco.xml", SOURCE_PATHS[1], "sco/sco.xml"),
        ("sco_third.xml", SOURCE_PATHS[0], "sco/sco_third.xml"),
        ("base-sco.xml", SOURCE_PATHS[0], "sco/sco.xml"),
        ("config.xml", SOURCE_PATHS[1], "config.xml"),
    ]
    prepared = [(filename, relative, member, get_member(sources[relative], member)) for filename, relative, member in selections]
    output.mkdir(parents=True, exist_ok=False)
    files = []
    for filename, relative, member, content in prepared:
        with (output / filename).open("xb") as handle:
            handle.write(content)
        files.append({"path": filename, "source_archive": relative, "source_archive_sha256": EXPECTED_SOURCE_SHA256[relative],
                      "member_path": member, "sha256": _sha(content), "bytes": len(content)})
    manifest = {"status": "verified_templates_extracted", "api_version": 1, "read_only_source_archives": True,
                "files": files, "archive_verification": verification,
                "runtime_verified": False, "note": "Scottish templates and exact resource config, not a ready Polish runtime package."}
    with (output / "manifest.json").open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    for relative in SOURCE_PATHS:
        _require(_sha((workspace / relative).read_bytes()) == EXPECTED_SOURCE_SHA256[relative], "Input resource changed after extraction")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--extract-templates", type=Path)
    args = parser.parse_args()
    if args.extract_templates:
        result = extract_templates(args.workspace, args.extract_templates)
        print(json.dumps({"status": result["status"], "templates": len(result["files"]), "sources_unchanged": True, "output": str(args.extract_templates)}, ensure_ascii=True))
    else:
        for relative in SOURCE_PATHS:
            print(json.dumps(verify_archive(args.workspace / relative), ensure_ascii=True))


if __name__ == "__main__":
    main()
