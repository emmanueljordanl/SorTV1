from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app.contracts import Cycle, Decision, DecisionKind
from app.controller import Controller
from app.evidence import EvidenceError, Journal


class StorageTests(unittest.TestCase):
    def test_disk_full_prevents_sort_and_latches_journal(self):
        with TemporaryDirectory() as directory:
            journal = Journal(Path(directory) / "events.jsonl", "SIMULATION")
            controller = Controller(journal)
            controller.connect("b1")
            controller.inspect(Cycle("b1", 1))
            with patch("app.evidence.os.fsync", side_effect=OSError("ENOSPC")):
                with self.assertRaises(EvidenceError):
                    controller.request_sort(Decision(DecisionKind.ACCEPT, 0, "PET", "CONSENSUS"))
            self.assertIsNone(controller.intent)
            with self.assertRaises(EvidenceError):
                journal.append("ANY", {})

    def test_truncated_journal_is_not_silently_repaired(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            path.write_bytes(b'{"event":"DONE"')
            with self.assertRaises(EvidenceError):
                Journal(path, "SIMULATION")

    def test_simulated_journal_cannot_be_opened_as_physical(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            Journal(path, "SIMULATION").append("INSPECT", {"cycle_key": "b1:1"})
            with self.assertRaises(EvidenceError):
                Journal(path, "PHYSICAL")
