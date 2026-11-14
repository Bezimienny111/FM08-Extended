import json
from pathlib import Path
import unittest
from team_talk_gates import standard_talk_window
class WindowTests(unittest.TestCase):
    def test_real_h1_h2_admitted_as_context_only(self):
        for status,phase,counter in [(0x220250,0,1),(0x220290,1,2)]:
            w=standard_talk_window(status,phase,phase,counter)
            self.assertTrue(w.admitted);self.assertTrue(w.standard_edit_locked)
            self.assertFalse(w.completion_verified)
    def test_actual_halftime_clears_old_prematch(self):
        self.assertFalse(standard_talk_window(0x220291,1,0,1).admitted)
    def test_phase_write_at_start_of_fulltime_clears_before_status_write(self):
        self.assertFalse(standard_talk_window(0x220290,5,1,2).admitted)
    def test_native_fulltime_variants_rejected(self):
        for status in (0x8220200,0x220208,0x220290|8,0x220290|4):
            self.assertFalse(standard_talk_window(status,1,1,2).admitted)
    def test_transition_extra_time_and_wrong_period_rejected(self):
        for args in ((0x220290|0x10000000,1,1,2),(0x220290|0x8000000,1,1,2),
                     (0x220261,2,2,3),(0x220250,1,1,2),(0x220290,0,0,1)):
            self.assertFalse(standard_talk_window(*args).admitted)
    def test_later_talk_must_not_overwrite_pinned_standard_slot(self):
        self.assertFalse(standard_talk_window(0x220290,1,1,3).admitted)
    def test_raw_input_type_rejected(self):
        self.assertFalse(standard_talk_window(True,0,0,1).admitted)
if __name__=="__main__":unittest.main()
