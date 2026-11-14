"""Isolated diagnostic prototype. No process discovery, injection or game calls.

Only PLAYER_TEAM_TALK_ENTRY parsing is backed by known native offsets.
The publication gates are an explicit contract, not a solved native adapter.
"""
from dataclasses import dataclass
from enum import Enum
import struct
from typing import Protocol

ENTRY_BYTES = 0x2B
KNOWN_EFFECT_MASK = (1 << 17) - 1
EFFECTS = (
    "motivate", "fire_up", "morale_boost", "morale_drop", "demotivate",
    "relieve_pressure", "pressurize", "lower_professionalism",
    "boost_professionalism", "happy", "unhappy", "anger", "victimised",
    "admired", "jealous_of_team_mate", "confused", "ignore",
)

class InvalidRead(ValueError):
    pass

class Memory(Protocol):
    def read(self, address: int, count: int) -> bytes: ...

@dataclass(frozen=True)
class Entry:
    uid: int
    action: int
    effect: int
    match_context: int
    position: int
    index: int

@dataclass(frozen=True)
class DecodedEffect:
    names: tuple[str, ...]
    unknown_bits: int

def decode_effect(effect: int) -> DecodedEffect:
    if type(effect) is not int or not 0 <= effect < (1 << 64):
        raise InvalidRead("effect is not uint64")
    return DecodedEffect(
        tuple(name for bit, name in enumerate(EFFECTS) if effect & (1 << bit)),
        effect & ~KNOWN_EFFECT_MASK,
    )

def parse_entry(raw: bytes, expected_uid: int, allowed_vtables: frozenset[int]) -> Entry:
    if len(raw) != ENTRY_BYTES:
        raise InvalidRead("short or oversized entry")
    if not allowed_vtables or struct.unpack_from("<I", raw, 0)[0] not in allowed_vtables:
        raise InvalidRead("unverified PLAYER_TEAM_TALK_ENTRY class")
    uid = struct.unpack_from("<I", raw, 8)[0]
    if not 0 < expected_uid < 0xFFFFFFFF or uid != expected_uid:
        raise InvalidRead("UID mismatch")
    return Entry(uid, *struct.unpack_from("<QQQ", raw, 0x10),
                 struct.unpack_from("<h", raw, 0x28)[0], raw[0x2A])

def read_stable_entry(memory: Memory, address: int, expected_uid: int,
                      allowed_vtables: frozenset[int]) -> Entry:
    if type(address) is not int or address < 0x10000 or address % 4 or address + ENTRY_BYTES > (1 << 32):
        raise InvalidRead("invalid x86 object pointer")
    first = memory.read(address, ENTRY_BYTES)
    second = memory.read(address, ENTRY_BYTES)
    if first != second:
        raise InvalidRead("entry changed during read")
    return parse_entry(first, expected_uid, allowed_vtables)

@dataclass(frozen=True)
class Context:
    process_generation: str
    career_generation: str
    match_identity: str
    team_uid: int
    manager_uid: int
    period_identity: str
    talk_identity: str
    talk_kind: str = "unknown"
    period_kind: str = "unknown"

@dataclass(frozen=True)
class Proof:
    kind: str
    reference: str

@dataclass(frozen=True)
class Snapshot:
    context: Context
    tick: int
    entries: tuple[Entry, ...]
    execution: str = "unknown"
    execution_proof: Proof | None = None
    edit_state: str = "unknown"
    edit_proof: Proof | None = None
    period_running: bool = False
    source_is_live: bool = False
    local_single_player: bool = False
    own_team: bool = False
    source_hash_verified: bool = False
    class_identity_verified: bool = False
    entry_period_verified: bool = False
    phase: int | None = None
    talk_kind_verified: bool = False
    match_finished: bool | None = None

class State(str, Enum):
    READY = "ready"
    NO_DATA = "no_data"
    UNSTABLE = "unstable"
    STALE = "stale_context"
    UNSUPPORTED = "unsupported_scope"
    UNVERIFIED = "unverified"
    PENDING = "pending_execution"
    WAITING_LOCK = "waiting_edit_lock"

@dataclass(frozen=True)
class View:
    state: State
    reason: str
    entries: tuple[Entry, ...] = ()

def evaluate(first: Snapshot | None, second: Snapshot | None, current: Context,
             *, allow_fixture_proofs: bool = False) -> View:
    # Fail closed: no previously successful data can survive a failed refresh.
    if first is None or second is None:
        return View(State.NO_DATA, "no complete snapshot")
    if first.context != current or second.context != current:
        return View(State.STALE, "different career/match/team/period/talk")
    if first != second:
        return View(State.UNSTABLE, "snapshot changed during collection")
    s = second
    if current.talk_kind not in {"prematch","halftime"}:
        return View(State.UNSUPPORTED, "only prematch and halftime talks are in scope")
    if s.match_finished is True:
        return View(State.UNSUPPORTED, "match ended; reaction view invalidated")
    if s.match_finished is None or not s.talk_kind_verified:
        return View(State.UNVERIFIED, "talk kind/end-of-match boundary not verified")
    expected={"first_half":"prematch","second_half":"halftime"}.get(current.period_kind)
    if expected is None:
        return View(State.UNSUPPORTED, "this match period is outside the supported scope")
    if current.talk_kind != expected:
        return View(State.STALE, "previous-period talk cannot survive the period transition")
    if not all((s.source_is_live, s.local_single_player, s.own_team)):
        return View(State.UNSUPPORTED, "only own team in live local single player")
    if not all((s.source_hash_verified, s.class_identity_verified, s.entry_period_verified)):
        return View(State.UNVERIFIED, "artifact/class/entry period not verified")
    if type(s.tick) is not int or s.tick < 0 or s.phase not in range(6):
        return View(State.UNVERIFIED, "invalid tick or unsupported native phase")
    if s.execution != "completed":
        return View(State.PENDING, "selected/queued/unknown is not completed")
    if s.edit_state != "locked" or not s.period_running:
        return View(State.WAITING_LOCK, "period not running or talk still editable")
    accepted = {"native_observed"}
    if allow_fixture_proofs:
        accepted.add("fixture")
    for proof in (s.execution_proof, s.edit_proof):
        if proof is None or proof.kind not in accepted or not proof.reference.strip():
            return View(State.UNVERIFIED, "no independently verified boundary evidence")
    # Phase alone never establishes completed execution or an edit lock.
    if not s.entries:
        return View(State.NO_DATA, "no entry for the relevant talk")
    seen = set()
    for entry in s.entries:
        if not 0 < entry.uid < 0xFFFFFFFF or entry.uid in seen:
            return View(State.UNVERIFIED, "invalid or duplicate UID")
        seen.add(entry.uid)
        for bits in (entry.action, entry.effect, entry.match_context):
            if type(bits) is not int or not 0 <= bits < (1 << 64):
                return View(State.UNVERIFIED, "invalid uint64 field")
        if not -1 <= entry.position <= 0x7FFF or not 0 <= entry.index <= 0xFF:
            return View(State.UNVERIFIED, "invalid position/index")
    return View(State.READY, "complete coherent snapshot with verified gates", s.entries)

class ReactionSession:
    def __init__(self):
        self.view = View(State.NO_DATA, "not observed")

    def refresh(self, first: Snapshot | None, second: Snapshot | None, current: Context,
                *, allow_fixture_proofs: bool = False) -> View:
        self.view = evaluate(first, second, current, allow_fixture_proofs=allow_fixture_proofs)
        return self.view

def native_ui_stage(flags: int) -> int:
    """Low-byte behavior of ad7eb0; distinct from MATCH+5f30c phase."""
    low = flags & 0xFF
    inverted_40 = (~(low >> 6)) & 1
    if flags & 0x10:
        return inverted_40 | (0 if flags & 1 else 2)
    if flags & 0x20:
        return inverted_40 | (4 if flags & 1 else 6)
    if not flags & 0x20000:
        return 8
    return 9 if flags & 4 else 10
