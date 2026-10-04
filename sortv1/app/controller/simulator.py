"""Doble de protocolo exclusivamente de software; no emula la mecánica."""

from app.transport import validate


class SimulatedPico:
    def __init__(self, boot: str):
        self.boot = boot
        self.cycle: int | None = None
        self.history: dict[tuple[str, int, int], dict] = {}
        self.commands: dict[tuple[str, int, int], dict] = {}
        self.executions = 0

    def inspect(self, cycle: int) -> dict:
        self.cycle = cycle
        return {"v": 1, "cmd": "INSPECT", "boot": self.boot, "cycle": cycle}

    def sort(self, command: dict) -> dict:
        validate(command)
        if command["cmd"] != "SORT":
            raise ValueError("SORT_REQUIRED")
        key = command["boot"], command["cycle"], command["request"]
        def nack(reason: str) -> dict:
            return {"v": 1, "cmd": "NACK", "boot": self.boot, "reason": reason}
        if command["boot"] != self.boot:
            return nack("STALE_BOOT")
        if key in self.history:
            return self.history[key].copy() if command == self.commands[key] else nack("ID_CONFLICT")
        if command["cycle"] != self.cycle:
            return nack("STALE_CYCLE")
        if any(k[:2] == key[:2] for k in self.history):
            return nack("CYCLE_ALREADY_CLAIMED")
        self.executions += 1
        result = {"v": 1, "cmd": "DONE", "boot": self.boot, "cycle": command["cycle"],
                  "request": command["request"], "seq": self.executions,
                  "confirmed_bin": command["dest"]}
        self.commands[key] = command.copy()
        self.history[key] = result
        return result.copy()
