import unittest

from app.contracts import Cycle, DecisionKind, Frame, Prediction, QualityResult
from app.decision import decide
from app.quality import assess


class DecisionTests(unittest.TestCase):
    def run_decision(self, values, **kwargs):
        predictions = [Prediction(str(i), p, "same-model", 1) for i, p in enumerate(values)]
        return decide(predictions, [QualityResult(True, "OK", 0)] * 3,
                      admitted=kwargs.get("admitted", True),
                      bins_available=kwargs.get("bins", (True,) * 4))

    def test_consensus_uses_confident_votes(self):
        result = self.run_decision([(0.91, 0.03, 0.03, 0.03)] * 2 + [(0.02, 0.94, 0.02, 0.02)])
        self.assertEqual((result.kind, result.destination), (DecisionKind.ACCEPT, 0))

    def test_exact_threshold_is_rejection(self):
        result = self.run_decision([(0.80, 0.10, 0.05, 0.05)] * 3)
        self.assertEqual((result.kind, result.destination), (DecisionKind.REJECT, 3))

    def test_full_bin_does_not_reroute(self):
        result = self.run_decision([(0.91, 0.03, 0.03, 0.03)] * 3, bins=(False, True, True, True))
        self.assertEqual((result.kind, result.destination), (DecisionKind.REVIEW, None))

    def test_unknown_capacity_is_not_available(self):
        result = self.run_decision([(0.91, 0.03, 0.03, 0.03)] * 3, bins=(None, True, True, True))
        self.assertEqual(result.kind, DecisionKind.REVIEW)

    def test_domain_must_be_confirmed(self):
        result = self.run_decision([(0.91, 0.03, 0.03, 0.03)] * 3, admitted=False)
        self.assertEqual(result.kind, DecisionKind.REVIEW)

    def test_nan_and_wrong_sum_are_invalid(self):
        for values in [(float("nan"), 0.1, 0.1, 0.1), (0.9, 0.9, 0.9, 0.9)]:
            self.assertEqual(self.run_decision([values] * 3).reason, "INVALID_PROBABILITIES")

    def test_reject_and_known_other_are_distinct(self):
        other = self.run_decision([(0.02, 0.02, 0.02, 0.94)] * 3)
        rejected = self.run_decision([(0.25,) * 4] * 3)
        self.assertEqual(other.destination, rejected.destination)
        self.assertNotEqual(other.kind, rejected.kind)

    def test_old_cycle_and_empty_image_are_reviewed(self):
        cycle = Cycle("b1", 1)
        for frame, reason in [(Frame("f", Cycle("b1", 0), 0, b"rgb", {}), "WRONG_CYCLE"),
                              (Frame("f", cycle, 0, b"rgb", {}), "STALE_FRAME"),
                              (Frame("f", cycle, 400_000_000, None, {}), "NO_IMAGE")]:
            result = assess(frame, cycle, 400_000_000, occupied=True, exposure_ok=True, focus_ok=True)
            self.assertEqual(result.reason, reason)
