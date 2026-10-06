import json
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from dataclasses import asdict
from pathlib import Path
from app.contracts import Cycle, Decision, DecisionKind
from app.controller import Controller
from app.decision import decide
from app.evidence import Journal
from app.transport.serial_transport import SerialTransport
from app.utils import load_json, sha256
from app.operator_ui import create_server
import shutil


PICO_DECISION_TIMEOUT_MS = 2000  # state_machine.cpp: WAIT_DECISION -> REVIEW tras 2 s; plan §11/§12.
MIN_DECISION_MARGIN_MS = 250
MAX_INSPECTION_DEADLINE_MS = PICO_DECISION_TIMEOUT_MS - MIN_DECISION_MARGIN_MS
DEFAULT_INSPECTION_DEADLINE_MS = 1750  # CONFIGURED_BASELINE; PENDING_PHYSICAL_BENCHMARK.


class PhysicalService:
    def __init__(self, root: Path, *, diagnostic=False, enable_actuators=False, destination=None):
        self.root = root; self.settings = load_json(root / "config/physical.json")
        # Plazo duro de inspección en la Pi. La meta de aceptación p95 <= 1 s se mide aparte (inspection_ms);
        # No usar una métrica estadística como timeout; reservar el margen Pi -> USB -> Pico.
        deadline_ms = self.settings.get("inspection_deadline_ms", DEFAULT_INSPECTION_DEADLINE_MS)
        if type(deadline_ms) is not int or not 0 < deadline_ms <= MAX_INSPECTION_DEADLINE_MS:
            raise ValueError(f"inspection_deadline_ms must be an integer in [1, {MAX_INSPECTION_DEADLINE_MS}] ms")
        self.inspection_deadline_s = deadline_ms / 1000
        self.diagnostic, self.enable, self.destination = diagnostic, enable_actuators, destination
        self.mode = "DIAGNOSTIC" if diagnostic else "PHYSICAL_AUTO"
        self.journal = Journal(root / self.settings["journal"], "PHYSICAL", mode=self.mode)
        self.controller = Controller(self.journal); self.status = {}; self.results = queue.Queue(maxsize=1)
        self.pool = ThreadPoolExecutor(max_workers=1); self.future = None; self.inspection_deadline = 0
        self.link = SerialTransport(self.settings["serial"])
        self.camera = None; self.model = None; self.firmware_version = "UNKNOWN"
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
                    "cycle_id": cycle.number, "request": 1, "sensors": status, "model_sha256": None,
                    "firmware_version": self.firmware_version,
                    "config_sha256": {p.name: sha256(p) for p in (self.root / "config").glob("*.json")}}
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
                            inference_ms=[p.inference_ms for p in predictions], frame_age_ms=[q.age_ms for q in qualities],
                            score=[max(p.probabilities) for p in predictions],
                            margin=[sorted(p.probabilities)[-1]-sorted(p.probabilities)[-2] for p in predictions])
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
        state = self.status.get("state")
        label = "FALLO" if not self.link.boot or state == "FAULT" or self.journal.failed else "REVISIÓN" if self.controller.blocked or state in {"BOOT_SAFE", "REVIEW"} else "LISTO" if state == "READY" else "PROCESANDO"
        latest = next((e["data"] for e in reversed(self.journal.events) if e["event"] in {"DONE", "INTENT", "REVIEW"}), {})
        return {"estado": label, "modo": self.mode, "ultimo_ciclo": latest.get("cycle_key"), "clase": latest.get("predicted_class"),
                "confidence": latest.get("score"), "destino_solicitado": latest.get("requested_bin"), "destino_confirmado": latest.get("confirmed_bin"),
                "tiempo_ms": latest.get("cycle_ms"), "tapa": self.status.get("lid"), "puerta": self.status.get("service"),
                "paro": "COMPROBACIÓN FÍSICA; estado individual no instrumentado", "actuator_power": self.status.get("power"),
                "llenado_orientativo": self.status.get("fill"), "almacenamiento_libre_bytes": shutil.disk_usage(self.journal.path.parent).free,
                "modelo": self.model.model_sha256 if self.model else "DIAGNOSTIC_SIN_IA", "firmware": self.firmware_version,
                "motivo": self.status.get("reason"),
                "boot": self.controller.boot, "cycle": self.status.get("cycle"), "conteos_DONE": self.journal.counts(self.mode)}

    def run(self):
        server = None; ui_thread = None
        try:
            self.journal.append("SERVICE_START", {"mode": self.mode, "rearm": "PHYSICAL_ONLY"})
            self.link.start()
            server = create_server(self, self.settings["ui_port"])
            thread = threading.Thread(target=server.serve_forever, name="SorTV1OperatorUI")
            thread.start(); ui_thread = thread
            while True:
                try: message = self.link.events.get(timeout=0.05)
                except queue.Empty: message = None
                if message:
                    cmd = message["cmd"]
                    if cmd not in {"HELLO", "STATUS", "DISCONNECTED"} and message.get("boot") != self.controller.boot:
                        self.journal.append("IGNORED_STALE_BOOT", message)
                        continue
                    if cmd == "DISCONNECTED": self.controller.disconnected(message["reason"])
                    elif cmd in {"HELLO", "STATUS"}:
                        if cmd == "HELLO": self.firmware_version = message.get("firmware", "UNKNOWN")
                        if self.controller.boot != message["boot"]: self.controller.connect(message["boot"])
                        self.status = message; self.status["received_monotonic_ns"] = time.monotonic_ns()
                    elif cmd == "INSPECT":
                        cycle = Cycle(message["boot"], message["cycle"])
                        self.controller.inspect(cycle)
                        self.inspection_deadline = time.monotonic()+self.inspection_deadline_s
                        self.future = self.pool.submit(self.inspect, cycle, self.status.copy())
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
            # Every cleanup runs even if another fails. Join workers before closing the camera.
            with ExitStack() as cleanup:
                if self.camera: cleanup.callback(self.camera.close)
                cleanup.callback(self.pool.shutdown, wait=True, cancel_futures=True)
                if ui_thread: cleanup.callback(ui_thread.join)
                if server:
                    cleanup.callback(server.server_close)
                    if ui_thread: cleanup.callback(server.shutdown)
                cleanup.callback(self.link.close)
