"""Fresh sensor exposures; SensorTimestamp is converted from BOOTTIME to monotonic."""
import time
from threading import Lock
from uuid import uuid4
import numpy as np
from app.contracts import Cycle, Frame


class PicameraCapture:
    def __init__(self, config: dict, *, calibration: bool = False, camera=None):
        self.config = config
        if not calibration and (not config.get("locked") or config.get("roi") is None):
            raise ValueError("Camera requires measured ROI and locked controls")
        if camera is None:
            from picamera2 import Picamera2
            camera = Picamera2()
        self.camera, self.lock = camera, Lock()
        # Picamera2 BGR888 has RGB byte ordering (libcamera little-endian packing).
        camera.configure(camera.create_video_configuration(main={"size": tuple(config["size"]), "format": "BGR888"},
                         controls={"FrameRate": config["fps"], **config["controls"]}, buffer_count=4, queue=False))
        camera.start()
        self.last_sensor = -1

    def begin(self, cycle: Cycle):
        self.cycle = cycle
        self.barrier = time.monotonic_ns() + int(self.config["settle_ms"] * 1_000_000)
        self.previous = 0

    def capture(self, cycle: Cycle) -> Frame:
        with self.lock:
            if getattr(self, "cycle", None) != cycle: self.begin(cycle)
            earliest = max(self.barrier, self.previous + self.config["spacing_ms"] * 1_000_000)
            delay = (earliest - time.monotonic_ns()) / 1e9
            if delay > 0: time.sleep(delay)
            deadline = time.monotonic() + self.config["timeout_s"]
            while time.monotonic() < deadline:
                # Asynchronous job has a bounded wait; never stamp an old buffer as new.
                job = self.camera.capture_request(wait=False, flush=True)
                request = self.camera.wait(job, timeout=self.config["timeout_s"])
                try:
                    metadata = request.get_metadata()
                    sensor = int(metadata["SensorTimestamp"])
                    offset = time.clock_gettime_ns(time.CLOCK_BOOTTIME) - time.monotonic_ns() if hasattr(time, "CLOCK_BOOTTIME") else 0
                    captured = sensor - offset
                    if captured < earliest or sensor <= self.last_sensor: continue
                    rgb = np.ascontiguousarray(request.make_array("main"))
                    roi = self.config.get("roi")
                    if roi is not None:
                        x, y, w, h = roi
                        if any(type(v) is not int for v in roi) or min(x, y) < 0 or min(w, h) <= 0 or x+w > rgb.shape[1] or y+h > rgb.shape[0]:
                            raise ValueError("ROI outside measured image")
                        rgb = rgb[y:y+h, x:x+w].copy()
                    self.last_sensor, self.previous = sensor, captured
                    return Frame(uuid4().hex, cycle, captured, rgb, metadata)
                finally: request.release()
            raise TimeoutError("No fresh camera exposure")

    def close(self):
        self.camera.stop(); self.camera.close()
