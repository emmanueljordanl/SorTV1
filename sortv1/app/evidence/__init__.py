import json
import os
from pathlib import Path
from time import monotonic_ns, time_ns
from typing import Any


class EvidenceError(RuntimeError):
    pass


class Journal:
    """Journal durable. Una línea truncada exige conciliación, no se descarta."""

    def __init__(self, path: Path, source: str):
        if source not in {"SIMULATION", "PHYSICAL"}:
            raise ValueError("source debe ser SIMULATION o PHYSICAL")
        self.path = path
        self.source = source
        self.failed = False
        self.events: list[dict[str, Any]] = []
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                for line in path.read_bytes().splitlines(keepends=True):
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
        record = {"event": kind, "source": self.source,
                  "result_kind": "SIMULATED" if self.source == "SIMULATION" else "PHYSICAL",
                  "wall_time_ns": time_ns(), "pi_monotonic_ns": monotonic_ns(), "data": data}
        line = json.dumps(record, ensure_ascii=True, separators=(",", ":"), allow_nan=False) + "\n"
        try:
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
        completed = {e["data"]["cycle_key"] for e in self.events if e["event"] == "DONE"}
        return intents - completed

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
