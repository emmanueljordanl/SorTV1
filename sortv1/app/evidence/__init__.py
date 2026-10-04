import json
import os
import shutil
import csv
from pathlib import Path
from time import monotonic_ns, time_ns
from typing import Any


class EvidenceError(RuntimeError):
    pass


class Journal:
    """Journal durable. Una línea truncada exige conciliación, no se descarta."""

    def __init__(self, path: Path, source: str, *, minimum_free_bytes: int = 16 * 1024 * 1024,
                 rotate_bytes: int = 16 * 1024 * 1024):
        if source not in {"SIMULATION", "PHYSICAL"}:
            raise ValueError("source debe ser SIMULATION o PHYSICAL")
        self.path = path
        self.source = source
        self.failed = False
        self.minimum_free_bytes = minimum_free_bytes
        self.rotate_bytes = rotate_bytes
        self.events: list[dict[str, Any]] = []
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            for segment in sorted(path.parent.glob(path.name + ".[0-9]*")) + ([path] if path.exists() else []):
                for line in segment.read_bytes().splitlines(keepends=True):
                    if not line.endswith(b"\n"):
                        raise EvidenceError("Journal truncado: requiere conciliación manual")
                    event = json.loads(line)
                    if not isinstance(event, dict) or event.get("source") != source:
                        raise EvidenceError("Journal incompatible con el origen solicitado")
                    if not isinstance(event.get("event"), str) or not isinstance(event.get("data"), dict):
                        raise EvidenceError("Evento de journal inválido")
                    self.events.append(event)
        except (OSError, ValueError) as exc:
            raise EvidenceError(f"No se puede recuperar evidencia: {exc}") from exc

    def append(self, kind: str, data: dict[str, Any]) -> None:
        if self.failed:
            raise EvidenceError("Persistencia bloqueada después de un error de escritura")
        fields = ("cycle_id", "boot_id", "request", "firmware_version", "model_sha256", "config_sha256",
                  "frame_ids", "frame_age_ms", "inference_ms", "predicted_class", "score", "margin", "decision",
                  "requested_bin", "ack", "confirmed_bin", "physical_result", "cycle_ms", "error_code", "mode")
        data = {**dict.fromkeys(fields), **data}
        data["boot_id"] = data.get("boot_id") or data.get("boot")
        data["cycle_id"] = data.get("cycle_id") if data.get("cycle_id") is not None else data.get("cycle")
        if kind in {"FAULT", "NACK"}: data["error_code"] = data.get("reason")
        if kind == "ACK": data["ack"] = True
        record = {"event": kind, "source": self.source,
                  "result_kind": "SIMULATED" if self.source == "SIMULATION" else "PHYSICAL",
                  "wall_time_ns": time_ns(), "pi_monotonic_ns": monotonic_ns(), "data": data}
        line = json.dumps(record, ensure_ascii=True, separators=(",", ":"), allow_nan=False) + "\n"
        try:
            if shutil.disk_usage(self.path.parent).free < self.minimum_free_bytes:
                raise OSError("Insufficient storage")
            if self.path.exists() and self.path.stat().st_size >= self.rotate_bytes:
                index = 1
                while self.path.with_name(self.path.name + f".{index:06d}").exists():
                    index += 1
                self.path.rename(self.path.with_name(self.path.name + f".{index:06d}"))
            with self.path.open("ab") as handle:
                payload = line.encode("ascii")
                if handle.write(payload) != len(payload):
                    raise OSError("Escritura incompleta")
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            self.failed = True
            raise EvidenceError(f"No se pudo persistir {kind}: {exc}") from exc
        self.events.append(record)

    def pending_cycles(self) -> set[str]:
        intents = {e["data"]["cycle_key"] for e in self.events if e["event"] in {"INSPECT", "INTENT"}}
        completed = {e["data"]["cycle_key"] for e in self.events
                     if e["event"] in {"DONE", "REMOVED", "ABORTED", "RECONCILED"}}
        return intents - completed

    def close_manual(self, cycle_key: str, outcome: str, *, operator: str, reason: str,
                     evidence: str, physical_state: dict) -> None:
        if outcome not in {"REMOVED", "ABORTED", "RECONCILED"} or cycle_key not in self.pending_cycles():
            raise EvidenceError("Invalid manual closure")
        if not operator.strip() or not reason.strip() or not Path(evidence).is_file():
            raise EvidenceError("Operator, reason and existing evidence required")
        if not all(physical_state.get(k) is True for k in
                   ("power_isolated", "tray_empty", "path_clear", "gate_closed")):
            raise EvidenceError("Known safe physical state must be recorded")
        self.append(outcome, {"cycle_key": cycle_key, "operator": operator, "reason": reason,
                             "evidence": str(Path(evidence).resolve()), "physical_state": physical_state})

    def export_csv(self, path: Path) -> None:
        fields = ["cycle_id", "boot_id", "request", "firmware_version", "model_sha256", "frame_ids", "frame_age_ms",
                  "inference_ms", "predicted_class", "score", "margin", "requested_bin", "ack", "confirmed_bin",
                  "physical_result", "cycle_ms", "error_code", "mode"]
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["event", "source", "result_kind", "wall_time_ns",
                                                        "pi_monotonic_ns", *fields, "data_json"])
            writer.writeheader()
            for event in list(self.events):
                row = {key: value for key, value in event.items() if key != "data"}
                values = {f: event["data"].get(f) for f in fields}
                values = {k: json.dumps(v) if isinstance(v, (dict, list, tuple)) else v for k, v in values.items()}
                writer.writerow({**row, **values, "data_json": json.dumps(event["data"], ensure_ascii=True)})

    def counts(self) -> list[int]:
        counts = [0, 0, 0, 0]
        seen: set[str] = set()
        for event in self.events:
            if event["event"] != "DONE":
                continue
            data = event["data"]
            if data["cycle_key"] not in seen:
                seen.add(data["cycle_key"])
                counts[data["confirmed_bin"]] += 1
        return counts
