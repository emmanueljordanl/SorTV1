from collections import Counter
from math import isfinite

from app.contracts import Decision, DecisionKind, LABELS, Prediction, QualityResult


def decide(predictions: list[Prediction], qualities: list[QualityResult], *,
           admitted: bool, bins_available: tuple[bool, bool, bool, bool],
           top1_min: float = 0.80, margin_min: float = 0.15) -> Decision:
    def review(reason: str) -> Decision:
        return Decision(DecisionKind.REVIEW, None, None, reason)

    if not admitted:
        return review("OUTSIDE_PHYSICAL_DOMAIN")
    if len(bins_available) != 4:
        return review("INVALID_BIN_STATUS")
    if len(qualities) != 3 or not all(q.valid for q in qualities):
        return review("IMAGE_QUALITY")
    if len(predictions) != 3 or len({p.frame_id for p in predictions}) != 3:
        return review("THREE_NEW_FRAMES_REQUIRED")
    if len({p.model_sha256 for p in predictions}) != 1:
        return review("MODEL_CHANGED")
    votes: list[int] = []
    for prediction in predictions:
        values = prediction.probabilities
        if (len(values) != 4 or not all(isfinite(p) and 0 <= p <= 1 for p in values)
                or abs(sum(values) - 1) > 1e-5):
            return review("INVALID_PROBABILITIES")
        order = sorted(range(4), key=lambda i: values[i], reverse=True)
        if values[order[0]] > top1_min and values[order[0]] - values[order[1]] > margin_min:
            votes.append(order[0])
    if votes:
        winner, count = Counter(votes).most_common(1)[0]
        if count >= 2:
            if bins_available[winner] is not True:
                return review("DESTINATION_UNAVAILABLE")
            return Decision(DecisionKind.ACCEPT, winner, LABELS[winner], "CONSENSUS")
    if bins_available[3] is not True:
        return review("REJECTION_BIN_UNAVAILABLE")
    return Decision(DecisionKind.REJECT, 3, None, "UNCERTAINTY")
