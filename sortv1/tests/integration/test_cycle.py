from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from app.contracts import Cycle, Decision, DecisionKind
from app.controller import Controller, ControllerError
from app.controller.simulator import SimulatedPico
from app.evidence import Journal


class CycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.journal = Journal(Path(self.temp.name) / "events.jsonl", "SIMULATION")
        self.controller = Controller(self.journal)
        self.controller.connect("b1")
        self.controller.inspect(Cycle("b1", 1))
        self.command = self.controller.request_sort(Decision(DecisionKind.ACCEPT, 2, "METAL_LATAS", "CONSENSUS"))
        self.pico = SimulatedPico("b1")
        self.pico.inspect(1)

    def test_ack_does_not_count_and_duplicate_done_counts_once(self):
        self.controller.on_message({"v": 1, "boot": "b1", "cycle": 1, "cmd": "ACK"})
        self.assertEqual(self.journal.counts(), [0, 0, 0, 0])
        done = self.pico.sort(self.command)
        self.controller.on_message(done)
        self.controller.on_message(done)
        recovered = Journal(self.journal.path, "SIMULATION")
        self.assertEqual(recovered.counts(), [0, 0, 1, 0])
        self.assertEqual(recovered.pending_cycles(), set())

    def test_lost_ack_same_request_and_new_request(self):
        done = self.pico.sort(self.command)
        self.assertEqual(self.pico.sort(self.command), done)
        self.assertEqual(self.pico.sort({**self.command, "request": 2})["cmd"], "NACK")
        self.assertEqual(self.pico.executions, 1)

    def test_conflict_and_stale_boot_do_not_execute(self):
        self.pico.sort(self.command)
        for message in [{**self.command, "dest": 0}, {**self.command, "boot": "old"}]:
            self.assertEqual(self.pico.sort(message)["cmd"], "NACK")
        self.assertEqual(self.pico.executions, 1)

    def test_restart_with_unresolved_intent_blocks(self):
        recovered = Controller(Journal(self.journal.path, "SIMULATION"))
        recovered.connect("b2")
        with self.assertRaises(ControllerError):
            recovered.inspect(Cycle("b2", 2))

    def test_restart_before_decision_keeps_inspection_pending(self):
        separate_path = self.journal.path.parent / "inspection.jsonl"
        journal = Journal(separate_path, "SIMULATION")
        first = Controller(journal)
        first.connect("b3")
        first.inspect(Cycle("b3", 1))
        recovered = Controller(Journal(separate_path, "SIMULATION"))
        recovered.connect("b4")
        with self.assertRaises(ControllerError):
            recovered.inspect(Cycle("b4", 1))

    def test_reconnect_during_cycle_requires_reconciliation(self):
        self.controller.connect("b1")
        with self.assertRaises(ControllerError):
            self.controller.inspect(Cycle("b1", 2))

    def test_wrong_destination_blocks_confirmation(self):
        done = self.pico.sort(self.command)
        with self.assertRaises(ControllerError):
            self.controller.on_message({**done, "confirmed_bin": 0})
        self.assertEqual(self.journal.counts(), [0, 0, 0, 0])
        self.assertTrue(self.controller.blocked)
