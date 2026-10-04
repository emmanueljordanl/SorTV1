from app.contracts import Cycle, Frame, QualityResult


def assess(frame: Frame, cycle: Cycle, now_ns: int, *, occupied: bool,
           exposure_ok: bool, focus_ok: bool, max_age_ms: int = 300) -> QualityResult:
    """Recibe comprobaciones visuales medidas por un adaptador, no las inventa."""
    age = (now_ns - frame.captured_ns) / 1_000_000
    reason = "OK"
    if frame.cycle != cycle:
        reason = "WRONG_CYCLE"
    elif age < 0 or age > max_age_ms:
        reason = "STALE_FRAME"
    elif frame.rgb is None:
        reason = "NO_IMAGE"
    elif not occupied:
        reason = "EMPTY_TRAY"
    elif not exposure_ok:
        reason = "EXPOSURE"
    elif not focus_ok:
        reason = "FOCUS"
    return QualityResult(reason == "OK", reason, age)
