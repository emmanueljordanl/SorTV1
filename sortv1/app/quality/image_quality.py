import hashlib
import numpy as np
from PIL import Image
from app.contracts import Cycle, Frame, QualityResult
from app.utils import sha256


class ImageQuality:
    def __init__(self, config: dict, background=None):
        self.config = config
        keys = ("presence_difference_min", "laplacian_variance_min", "mean_min", "mean_max", "clipped_fraction_max")
        if any(config.get(k) is None for k in keys): raise ValueError("Quality requires measured calibration")
        if background is None:
            if sha256(config["background_path"]) != config["background_sha256"]: raise ValueError("Background hash mismatch")
            background = np.asarray(Image.open(config["background_path"]).convert("RGB"))
        self.background = np.asarray(background).astype(np.float32)
        self.cycle = None; self.seen = set(); self.last_ns = -1; self.measurements = {}

    def assess(self, frame: Frame, cycle: Cycle, now_ns: int, *, weight_present: bool) -> QualityResult:
        age = (now_ns - frame.captured_ns) / 1e6
        def result(reason): return QualityResult(reason == "OK", reason, age)
        if frame.cycle != cycle: return result("WRONG_CYCLE")
        if age < 0 or age > self.config["max_age_ms"]: return result("STALE_FRAME")
        rgb = np.asarray(frame.rgb)
        if rgb.ndim != 3 or rgb.shape[2] != 3 or rgb.dtype != np.uint8 or min(rgb.shape[:2]) < 3: return result("NO_IMAGE")
        if self.cycle != cycle: self.cycle = cycle; self.seen.clear()
        digest = hashlib.sha256(rgb.tobytes()).hexdigest()
        if frame.frame_id in self.seen or digest in self.seen or frame.captured_ns <= self.last_ns: return result("REPEATED_FRAME")
        self.seen.update((digest, frame.frame_id)); self.last_ns = frame.captured_ns
        if rgb.shape != self.background.shape: return result("BACKGROUND_SHAPE")
        grey = rgb.astype(np.float32).mean(axis=2)
        lap = grey[1:-1, :-2] + grey[1:-1, 2:] + grey[:-2, 1:-1] + grey[2:, 1:-1] - 4*grey[1:-1, 1:-1]
        measures = {"mean": float(grey.mean()), "laplacian_variance": float(lap.var()),
                    "clipped_fraction": float(((grey <= 2) | (grey >= 253)).mean()),
                    "presence_difference": float(np.abs(rgb.astype(np.float32)-self.background).mean())}
        self.measurements[frame.frame_id] = measures
        if not weight_present or measures["presence_difference"] < self.config["presence_difference_min"]: return result("EMPTY_TRAY")
        if not self.config["mean_min"] <= measures["mean"] <= self.config["mean_max"] or measures["clipped_fraction"] > self.config["clipped_fraction_max"]: return result("EXPOSURE")
        if measures["laplacian_variance"] < self.config["laplacian_variance_min"]: return result("FOCUS")
        return result("OK")
