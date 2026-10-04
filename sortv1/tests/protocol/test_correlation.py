from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from app.contracts import Cycle, Decision, DecisionKind
from app.controller import Controller, ControllerError
from app.evidence import Journal


class CorrelationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.journal = Journal(Path(self.tmp.name) / "log.jsonl", "SIMULATION")
        self.control = Controller(self.journal); self.control.connect("b")
        self.control.inspect(Cycle("b", 5))
        self.control.request_sort(Decision(DecisionKind.ACCEPT, 0, "PET", "OK"))

    def test_delayed_errors_do_not_block_current_cycle(self):
        for cmd in ("NACK", "FAULT"):
            for cycle, request in ((4, 1), (5, 0), (5, 2)):
                self.control.on_message(dict(v=1, boot="b", cycle=cycle, request=request,
                                             cmd=cmd, reason="DELAYED", seq=1))
                self.assertFalse(self.control.blocked)

    def test_current_fault_blocks(self):
        self.control.on_message(dict(v=1, boot="b", cycle=5, request=1, cmd="FAULT", reason="GUARD", seq=2))
        self.assertTrue(self.control.blocked)

    def test_old_boot_is_rejected_without_mutating_state(self):
        with self.assertRaises(ControllerError):
            self.control.on_message(dict(v=1, boot="old", cycle=5, request=1, cmd="FAULT", reason="OLD"))
        self.assertFalse(self.control.blocked)

    def test_disconnect_never_counts(self):
        self.control.disconnected()
        self.assertTrue(self.control.blocked)
        self.assertEqual(self.journal.counts(), [0] * 4)

    def test_manual_removal_is_auditable_and_not_done(self):
        evidence = Path(self.tmp.name) / "observation.txt"; evidence.write_text("fixture removed")
        self.control.manual_close("REMOVED", operator="test", reason="review", evidence=str(evidence),
                                  physical_state=dict(power_isolated=True, tray_empty=True, path_clear=True, gate_closed=True))
        self.assertEqual(self.journal.pending_cycles(), set())
        self.assertEqual(self.journal.counts(), [0] * 4)
        self.assertEqual(self.journal.events[-1]["event"], "REMOVED")
