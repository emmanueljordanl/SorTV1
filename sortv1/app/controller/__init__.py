from dataclasses import asdict

from app.contracts import Cycle, Decision
from app.evidence import Journal
from app.transport import validate


class ControllerError(RuntimeError):
    pass


class Controller:
    """Orquestador sin acceso a motores. No rearma ni reenvía al reiniciar."""

    def __init__(self, journal: Journal):
        self.journal = journal
        self.boot: str | None = None
        self.active: Cycle | None = None
        self.intent: dict | None = None
        self.blocked = bool(journal.pending_cycles())
        self.seen: set[str] = {e["data"]["cycle_key"] for e in journal.events
                               if e["event"] in {"INSPECT", "INTENT", "DONE"}}
        self.completed = {e["data"]["cycle_key"]: e["data"] for e in journal.events
                          if e["event"] == "DONE"}

    def connect(self, boot: str) -> None:
        if not isinstance(boot, str) or not boot:
            raise ControllerError("BOOT_INVALID")
        if self.active is not None or self.journal.pending_cycles():
            self.blocked = True
        self.active = None
        self.intent = None
        self.boot = boot

    def inspect(self, cycle: Cycle) -> None:
        if self.blocked or self.active is not None or cycle.boot != self.boot or cycle.key in self.seen:
            raise ControllerError("INSPECT_NOT_ALLOWED")
        self.journal.append("INSPECT", {"cycle_key": cycle.key})
        self.seen.add(cycle.key)
        self.active = cycle

    def request_sort(self, decision: Decision) -> dict | None:
        if self.blocked or self.active is None or self.intent is not None:
            raise ControllerError("NO_ACTIVE_INSPECTION")
        if decision.kind.value == "REVIEW" and decision.destination is not None:
            raise ControllerError("INVALID_DECISION")
        if decision.destination is None:
            self.journal.append("REVIEW", {"cycle_key": self.active.key, "decision": asdict(decision)})
            self.blocked = True
            return None
        command = {"v": 1, "boot": self.active.boot, "cycle": self.active.number,
                   "request": 1, "cmd": "SORT", "dest": decision.destination}
        validate(command)
        # Si fsync falla, esta función no devuelve la orden al transporte.
        self.journal.append("INTENT", {"cycle_key": self.active.key, "command": command,
                                      "decision": asdict(decision)})
        self.intent = command
        return command.copy()

    def on_message(self, message: dict) -> None:
        validate(message)
        if message["boot"] != self.boot:
            raise ControllerError("STALE_BOOT")
        cmd = message["cmd"]
        if cmd == "FAULT":
            self.journal.append("FAULT", message)
            self.blocked = True
            return
        if cmd == "NACK":
            self.journal.append("NACK", message)
            self.blocked = True
            return
        if cmd != "DONE":
            return  # ACK jamás consolida un resultado físico.
        key = f"{message['boot']}:{message['cycle']}"
        if key in self.completed:
            previous = self.completed[key]
            if any(previous[field] != message[field] for field in ("confirmed_bin", "request", "seq")):
                self.blocked = True
                raise ControllerError("DONE_CONFLICT")
            return
        if (self.blocked or self.active is None or self.active.key != key or self.intent is None
                or message["request"] != self.intent["request"]
                or message["confirmed_bin"] != self.intent["dest"]):
            self.blocked = True
            raise ControllerError("UNEXPECTED_DONE")
        data = {**message, "cycle_key": key, "physical_result": "DONE"}
        self.journal.append("DONE", data)
        self.completed[key] = data
        self.active = None
        self.intent = None
