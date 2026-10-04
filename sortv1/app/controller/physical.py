import json
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from app.contracts import Cycle, Decision, DecisionKind
from app.controller import Controller
from app.decision import decide
from app.evidence import Journal
from app.transport.serial_transport import SerialTransport
from app.utils import load_json, sha256


class PhysicalService:
    def __init__(self, root: Path, *, diagnostic=False, enable_actuators=False, destination=None):
        self.root = root; self.settings = load_json(root / "config/physical.json")
        self.diagnostic, self.enable, self.destination = diagnostic, enable_actuators, destination
        self.mode = "DIAGNOSTIC" if diagnostic else "PHYSICAL_AUTO"
        self.journal = Journal(root / self.settings["journal"], "PHYSICAL")
        self.controller = Controller(self.journal); self.status = {}; self.results = queue.Queue(maxsize=1)
        self.pool = ThreadPoolExecutor(max_workers=1); self.future = None; self.inspection_deadline = 0
        self.link = SerialTransport(self.settings["serial"])
        self.camera = None; self.model = None
        if not diagnostic:
            from app.capture.picamera2_capture import PicameraCapture
            from app.quality.image_quality import ImageQuality
            from app.inference.onnx_runtime import OnnxInference
            self.model = OnnxInference(root / self.settings["model_package"])
            if self.model.manifest.get("source") == "SYNTHETIC_TEST" or self.model.manifest.get("validation_domain") != "LOCAL_PHYSICAL":
                raise ValueError("Physical operation requires LOCAL_PHYSICAL model validation")
            quality = load_json(root / "config/quality.json")
            if quality.get("background_path"): quality["background_path"] = str(root / quality["background_path"])
            self.quality = ImageQuality(quality)
            self.camera = PicameraCapture(load_json(root / "config/camera.json"))

    def admission(self):
        path = self.settings.get("admission_record")
        if not path: return False
        try:
            data = load_json(self.root / path)
            return (data["operator"] == self.settings["operator"] and data["boot"] == self.controller.boot
                    and data["cycle"] == self.controller.active.number and data["single_object"] is True
                    and data["dry_known_catalog"] is True and data["within_size_mass_limits"] is True
                    and 0 <= time.time()-data["timestamp"] <= self.settings["admission_max_age_s"])
        except (OSError, ValueError, KeyError, AttributeError): return False

    def inspect(self, cycle, status):
        start = time.monotonic_ns()
        metadata = {"mode": self.mode, "operator": self.settings.get("operator"), "boot_id": cycle.boot,
                    "cycle_id": cycle.number, "request_id": 1, "sensors": status, "model_sha256": None}
        if self.diagnostic:
            decision = Decision(DecisionKind.ACCEPT, self.destination, None, "FORCED_DIAGNOSTIC") if self.enable and self.destination in range(4) else Decision(DecisionKind.REVIEW, None, None, "ACTUATORS_NOT_ENABLED")
        else:
            frames, predictions, qualities = [], [], []
            self.camera.begin(cycle)
            for _ in range(3):
                frame = self.camera.capture(cycle); frames.append(frame)
                quality = self.quality.assess(frame, cycle, time.monotonic_ns(), weight_present=status.get("presence") is True)
                qualities.append(quality)
                if quality.valid: predictions.append(self.model.predict(frame))
            thresholds = self.model.thresholds
            decision = decide(predictions, qualities, admitted=self.admission(),
                              bins_available=tuple(v == "AVAILABLE" for v in status.get("fill", [])),
                              top1_min=thresholds["top1_min_exclusive"], margin_min=thresholds["margin_min_exclusive"])
            metadata.update(model_sha256=self.model.model_sha256, frame_ids=[f.frame_id for f in frames],
                            controls=[f.controls for f in frames], probabilities=[p.probabilities for p in predictions],
                            quality=[asdict(q) for q in qualities], quality_measurements=self.quality.measurements.copy(),
                            inference_ms=[p.inference_ms for p in predictions])
            # Save actual evidence before any SORT can be sent.
            from PIL import Image
            paths = []
            for frame in frames:
                path = self.root / "evidence/photos" / cycle.boot / f"{cycle.number}-{frame.frame_id}.png"
                path.parent.mkdir(parents=True, exist_ok=True); Image.fromarray(frame.rgb).save(path)
                paths.append({"path": str(path), "sha256": sha256(path)})
            metadata["frames"] = paths
        metadata["inspection_ms"] = (time.monotonic_ns()-start)/1e6
        return cycle, decision, metadata

    def snapshot(self):
        return {"mode": self.mode, "source": "PHYSICAL", "status": self.status, "blocked": self.controller.blocked,
                "counts": self.journal.counts(), "pending": sorted(self.journal.pending_cycles()), "usb": self.link.metrics}

    def run(self):
        self.journal.append("SERVICE_START", {"mode": self.mode, "rearm": "PHYSICAL_ONLY"})
        self.link.start()
        service = self
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/api/status": payload = json.dumps(service.snapshot()).encode(); kind = "application/json"
                elif self.path == "/export.csv":
                    path = service.root / "evidence/experiments/export.csv"; service.journal.export_csv(path); payload = path.read_bytes(); kind = "text/csv"
                elif self.path == "/":
                    payload = b'<html lang="es"><title>SorTV1</title><h1>SorTV1: estado fisico</h1><pre id="s"></pre><a href="/export.csv">Exportar evidencia</a><script>setInterval(async()=>{s.textContent=JSON.stringify(await(await fetch("/api/status")).json(),null,2)},1000)</script></html>'; kind = "text/html"
                else: self.send_error(404); return
                self.send_response(200); self.send_header("Content-Type", kind); self.end_headers(); self.wfile.write(payload)
            def log_message(self, *args): pass
        server = ThreadingHTTPServer(("127.0.0.1", self.settings["ui_port"]), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            while True:
                try: message = self.link.events.get(timeout=0.05)
                except queue.Empty: message = None
                if message:
                    cmd = message["cmd"]
                    if cmd == "DISCONNECTED": self.controller.disconnected(message["reason"])
                    elif cmd in {"HELLO", "STATUS"}:
                        if self.controller.boot != message["boot"]: self.controller.connect(message["boot"])
                        self.status = message; self.status["received_monotonic_ns"] = time.monotonic_ns()
                    elif cmd == "INSPECT":
                        cycle = Cycle(message["boot"], message["cycle"])
                        self.controller.inspect(cycle)
                        self.future = self.pool.submit(self.inspect, cycle, self.status.copy())
                        self.inspection_deadline = time.monotonic()+1
                    else: self.controller.on_message(message)
                if self.future and self.future.done():
                    cycle, decision, metadata = self.future.result(); self.future = None
                    if cycle == self.controller.active and not self.controller.blocked:
                        if time.monotonic() > self.inspection_deadline: decision = Decision(DecisionKind.REVIEW, None, None, "INSPECTION_TIMEOUT")
                        if time.monotonic_ns()-self.status.get("received_monotonic_ns", 0) > 500_000_000: decision = Decision(DecisionKind.REVIEW, None, None, "STALE_SENSORS")
                        self.controller.metadata = metadata; command = self.controller.request_sort(decision)
                        if command: self.link.send(command)
                if self.future and time.monotonic() > self.inspection_deadline and not self.controller.blocked:
                    self.controller.request_sort(Decision(DecisionKind.REVIEW, None, None, "INSPECTION_TIMEOUT"))
        except Exception as error:
            self.controller.blocked = True
            try: self.journal.append("SERVICE_FAULT", {"mode": self.mode, "reason": type(error).__name__, "detail": str(error)})
            finally: raise
        finally:
            self.link.close(); server.shutdown(); self.pool.shutdown(wait=False, cancel_futures=True)
            if self.camera: self.camera.close()
