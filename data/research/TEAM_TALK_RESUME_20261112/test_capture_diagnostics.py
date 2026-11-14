import copy
import json
from pathlib import Path
import unittest
from capture_diagnostics import diagnostic, Rejected, native_null_context_labels, fingerprint

class DiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).parent/"captures"
        cls.h=json.loads((p/"frontend_human_8020_20261112T103744526014Z.json").read_text("utf-8"))
        cls.h2=json.loads((p/"second_half_8020_20261112T100418461655Z.json").read_text("utf-8"))
        cls.ht=json.loads((p/"halftime_8020_20261112T095958781693Z.json").read_text("utf-8"))
    def mutate(self,fn):
        d=copy.deepcopy(self.h2);fn(d["first"]);d["second"]=copy.deepcopy(d["first"]);return d
    def test_h2_replaces_prematch_and_matches_only_current_packet(self):
        d=diagnostic(self.h2,self.h)
        self.assertEqual(d["observed_talk_kind"],"halftime")
        self.assertTrue(d["talk_relevant_to_current_phase"])
        self.assertEqual(d["matching_event7"],[{"timestamp":19863,"phase":1,"tick_after_timestamp":True}])
        self.assertEqual(d["effect_histogram"],{"0x0":3,"0x100":5,"0x1":3})
        self.assertFalse(d["publication_ready"])
    def test_halftime_rejects_old_prematch_as_current(self):
        d=diagnostic(self.ht,self.h)
        self.assertFalse(d["talk_relevant_to_current_phase"])
        self.assertEqual(d["stored_talk_phase"],0)
    def test_later_human_not_promoted_to_simultaneous_proof(self):
        self.assertEqual(diagnostic(self.h2,self.h)["own_scope"],"LATER_FRONTEND_TEAM_CORRELATION_ONLY")
    def test_process_generation_rejected(self):
        h=copy.deepcopy(self.h);h["process"]["creation_filetime"]+=1
        with self.assertRaises(Rejected):diagnostic(self.h2,h)
    def test_ambiguous_match_rejected(self):
        d=self.mutate(lambda s:s["match_slots"].__setitem__("controller_2648",1234))
        with self.assertRaises(Rejected):diagnostic(d,self.h)
    def test_invalid_uid_rejected(self):
        d=self.mutate(lambda s:s["matches"]["controller_3c"]["teams"][0]["manager"]["last_or_staged_talk"]["entries"][0].__setitem__("uid",0xffffffff))
        with self.assertRaises(Rejected):diagnostic(d,self.h)
    def test_bad_backlink_rejected(self):
        d=self.mutate(lambda s:s["matches"]["controller_3c"]["teams"][0]["manager"].__setitem__("match_backlink",1234))
        with self.assertRaises(Rejected):diagnostic(d,self.h)
    def test_duplicate_fingerprint_rejected(self):
        with self.assertRaises(Rejected):fingerprint([{"uid":1,"action":2,"context":3}]*2)
    def test_native_mixed_flags_not_contradictory_text(self):
        for effect in (0x2010,0x2011):
            self.assertEqual(native_null_context_labels(effect)["labels"],["Looked delighted"])
    def test_raw_motivation_alone_does_not_gain_native_text(self):
        self.assertEqual(native_null_context_labels(1)["labels"],["Nothing specific noted"])
        self.assertEqual(native_null_context_labels(0x100)["labels"],["Nothing specific noted"])
    def test_unknown_effect_not_hidden(self):
        self.assertEqual(native_null_context_labels(1<<63)["status"],"unsupported_unknown_bits")
if __name__=="__main__":unittest.main()
