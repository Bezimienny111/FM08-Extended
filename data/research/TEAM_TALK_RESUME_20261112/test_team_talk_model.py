"""Contract/fixture tests; these do not establish native match behavior."""
import struct
import unittest
from dataclasses import replace
from team_talk_model import *

VTABLE = 0x01588780
CONTEXT = Context("p1", "save1", "match1", 11, 22, "half2", "talk2", "halftime", "second_half")
ENTRY = Entry(8074, 0x8000, 1, 0, -1, 0x7F)

def ready():
    return Snapshot(
        context=CONTEXT, tick=1234, entries=(ENTRY,), execution="completed",
        execution_proof=Proof("fixture", "fixture:executor-return"),
        edit_state="locked", edit_proof=Proof("fixture", "fixture:locked"),
        period_running=True, source_is_live=True, local_single_player=True,
        own_team=True, source_hash_verified=True, class_identity_verified=True,
        entry_period_verified=True, phase=1, talk_kind_verified=True, match_finished=False)

def show(s, current=CONTEXT):
    return evaluate(s, s, current, allow_fixture_proofs=True)

def raw_entry(uid=8074, action=0x1234567812345678, effect=1, context=0xFEDCBA9876543210):
    raw = bytearray(ENTRY_BYTES)
    struct.pack_into("<I", raw, 0, VTABLE)
    struct.pack_into("<I", raw, 8, uid)
    struct.pack_into("<QQQhB", raw, 0x10, action, effect, context, -1, 0x7F)
    return bytes(raw)

class FakeMemory:
    def __init__(self, reads):
        self.reads = iter(reads)
        self.calls = []
    def read(self, address, count):
        self.calls.append((address, count))
        return next(self.reads)

class ContractTests(unittest.TestCase):
    def test_every_flag_and_all_low_combinations(self):
        # Exhaustive decoder coverage of 131072 combinations; no category collapse.
        for mask in range(1 << len(EFFECTS)):
            actual = decode_effect(mask)
            expected = tuple(EFFECTS[i] for i in range(17) if mask & (1 << i))
            self.assertEqual(actual.names, expected)
            self.assertEqual(actual.unknown_bits, 0)

    def test_mixed_reaction_is_preserved(self):
        self.assertEqual(decode_effect(1 | 0x400 | 0x10000).names,
                         ("motivate", "unhappy", "ignore"))

    def test_unknown_high_bits_are_retained(self):
        self.assertEqual(decode_effect((1 << 63) | 2).unknown_bits, 1 << 63)

    def test_invalid_effect_does_not_wrap(self):
        for bad in (-1, 1 << 64, True, "1"):
            with self.subTest(bad=bad), self.assertRaises(InvalidRead):
                decode_effect(bad)

    def test_exact_entry_layout_and_64_bit_fields(self):
        entry = parse_entry(raw_entry(), 8074, frozenset({VTABLE}))
        self.assertEqual(entry, Entry(8074, 0x1234567812345678, 1,
                                     0xFEDCBA9876543210, -1, 0x7F))

    def test_truncated_class_and_identity_rejected(self):
        raw = raw_entry()
        for value, uid, vtables in (
            (raw[:-1], 8074, {VTABLE}), (raw + b"x", 8074, {VTABLE}),
            (raw, 7, {VTABLE}), (raw, 8074, set()), (raw, 8074, {1})):
            with self.subTest(uid=uid, size=len(value)), self.assertRaises(InvalidRead):
                parse_entry(value, uid, frozenset(vtables))

    def test_double_read_and_pointer_bounds(self):
        raw = raw_entry()
        mem = FakeMemory([raw, raw])
        self.assertEqual(read_stable_entry(mem, 0x10000, 8074, frozenset({VTABLE})).uid, 8074)
        self.assertEqual(mem.calls, [(0x10000, ENTRY_BYTES)] * 2)
        with self.assertRaises(InvalidRead):
            read_stable_entry(FakeMemory([raw, raw_entry(effect=2)]), 0x10000, 8074, frozenset({VTABLE}))
        for pointer in (0, 0x10001, 0xFFFFFFF0):
            with self.subTest(pointer=pointer), self.assertRaises(InvalidRead):
                read_stable_entry(FakeMemory([]), pointer, 8074, frozenset({VTABLE}))

    def test_ready_requires_opt_in_for_fixture_proofs(self):
        s = ready()
        self.assertEqual(show(s).state, State.READY)
        self.assertEqual(evaluate(s, s, CONTEXT).state, State.UNVERIFIED)

    def test_selection_and_counter_are_not_completion(self):
        for execution in ("selected", "queued", "unknown"):
            with self.subTest(execution=execution):
                self.assertEqual(show(replace(ready(), execution=execution)).state, State.PENDING)

    def test_phase_never_bypasses_gates(self):
        for phase in range(6):
            self.assertEqual(show(replace(ready(), phase=phase, execution="unknown")).state, State.PENDING)
            self.assertEqual(show(replace(ready(), phase=phase, edit_state="unknown")).state, State.WAITING_LOCK)

    def test_running_and_locked_are_separate(self):
        for edit, running in (("editable", True), ("unknown", True), ("locked", False)):
            self.assertEqual(show(replace(ready(), edit_state=edit, period_running=running)).state,
                             State.WAITING_LOCK)

    def test_unknown_boundary_has_no_fallback_delay(self):
        for changes in ({"execution_proof": None}, {"edit_proof": None},
                        {"edit_proof": Proof("guessed", "offset")},
                        {"execution_proof": Proof("fixture", "")}):
            self.assertEqual(show(replace(ready(), **changes)).state, State.UNVERIFIED)

    def test_zero_effect_only_after_execution(self):
        s = replace(ready(), entries=(replace(ENTRY, effect=0),))
        self.assertEqual(show(s).state, State.READY)
        self.assertEqual(decode_effect(show(s).entries[0].effect).names, ())
        self.assertEqual(show(replace(s, execution="unknown")).state, State.PENDING)
        self.assertEqual(show(replace(s, entries=())).state, State.NO_DATA)

    def test_live_own_team_single_player_only(self):
        for field in ("source_is_live", "own_team", "local_single_player"):
            self.assertEqual(show(replace(ready(), **{field: False})).state, State.UNSUPPORTED)

    def test_invalidated_on_every_context_change(self):
        session = ReactionSession()
        for name in Context.__dataclass_fields__:
            session.refresh(ready(), ready(), CONTEXT, allow_fixture_proofs=True)
            value = getattr(CONTEXT, name)
            new = replace(CONTEXT, **{name: value + 1 if isinstance(value, int) else value + "-new"})
            view = session.refresh(ready(), ready(), new, allow_fixture_proofs=True)
            self.assertEqual(view.state, State.STALE)
            self.assertFalse(view.entries)

    def test_failed_refresh_does_not_keep_previous_values(self):
        session = ReactionSession()
        session.refresh(ready(), ready(), CONTEXT, allow_fixture_proofs=True)
        self.assertEqual(session.refresh(None, None, CONTEXT).state, State.NO_DATA)
        self.assertFalse(session.view.entries)

    def test_mutation_or_torn_snapshot_not_published(self):
        s = ready()
        for new in (replace(s, tick=s.tick+1), replace(s, entries=(replace(ENTRY, effect=2),)),
                    replace(s, execution="unknown")):
            self.assertEqual(evaluate(s, new, CONTEXT, allow_fixture_proofs=True).state, State.UNSTABLE)

    def test_foreign_period_or_unverified_artifact_hidden(self):
        for field in ("source_hash_verified", "class_identity_verified", "entry_period_verified"):
            self.assertEqual(show(replace(ready(), **{field: False})).state, State.UNVERIFIED)

    def test_corrupt_entries_are_not_partial_success(self):
        s = ready()
        for entries in ((ENTRY, ENTRY), (replace(ENTRY, uid=0xFFFFFFFF),),
                        (replace(ENTRY, effect=-1),), (replace(ENTRY, action=1 << 64),)):
            self.assertEqual(show(replace(s, entries=entries)).state, State.UNVERIFIED)

    def test_postmatch_and_other_talk_kinds_are_rejected(self):
        for kind in ("postmatch","substitution","unknown"):
            context=replace(CONTEXT,talk_kind=kind)
            s=replace(ready(),context=context)
            self.assertEqual(show(s,context).state,State.UNSUPPORTED)

    def test_second_half_clears_prematch_reaction(self):
        first=replace(CONTEXT,talk_kind="prematch",period_kind="first_half",period_identity="half1",talk_identity="talk1")
        pre=replace(ready(),context=first,phase=0)
        session=ReactionSession()
        self.assertEqual(session.refresh(pre,pre,first,allow_fixture_proofs=True).state,State.READY)
        self.assertEqual(session.refresh(pre,pre,CONTEXT,allow_fixture_proofs=True).state,State.STALE)
        self.assertFalse(session.view.entries)
        wrong=replace(ready(),context=replace(CONTEXT,talk_kind="prematch"))
        self.assertEqual(show(wrong,wrong.context).state,State.STALE)

    def test_end_of_match_clears_previous_reaction(self):
        session=ReactionSession()
        session.refresh(ready(),ready(),CONTEXT,allow_fixture_proofs=True)
        ended=replace(ready(),match_finished=True)
        self.assertEqual(session.refresh(ended,ended,CONTEXT,allow_fixture_proofs=True).state,State.UNSUPPORTED)
        self.assertFalse(session.view.entries)

    def test_kind_and_end_boundary_need_independent_verification(self):
        for changes in ({"talk_kind_verified":False},{"match_finished":None}):
            self.assertEqual(show(replace(ready(),**changes)).state,State.UNVERIFIED)
        context=replace(CONTEXT,period_kind="extra_time")
        self.assertEqual(show(replace(ready(),context=context),context).state,State.UNSUPPORTED)

    def test_native_ui_stage_regressions(self):
        # Native constants from phase transitions, NOT a completed/locked predicate.
        for flags, expected in ((0x220291, 1), (0x220261, 4),
                                (0x2202A1, 5), (0x8220200, 10),
                                (0x220208, 10), (0x40000, 8)):
            self.assertEqual(native_ui_stage(flags), expected)

if __name__ == "__main__":
    unittest.main(verbosity=2)
