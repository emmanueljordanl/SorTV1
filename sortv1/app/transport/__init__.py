"""Protocolo USB CDC v1, sin dependencia de pySerial para sus pruebas."""

import json
from typing import Any

MAX_BYTES = 512
COMMANDS = {"HELLO", "STATUS", "INSPECT", "SORT", "ACK", "NACK", "DONE",
            "FAULT", "HEARTBEAT", "QUERY"}


class ProtocolError(ValueError):
    pass


def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def validate(message: dict[str, Any]) -> None:
    if not isinstance(message, dict):
        raise ProtocolError("OBJECT_REQUIRED")
    if type(message.get("v")) is not int or message["v"] != 1:
        raise ProtocolError("VERSION")
    if not isinstance(message.get("boot"), str) or not message["boot"]:
        raise ProtocolError("BOOT")
    cmd = message.get("cmd")
    if not isinstance(cmd, str) or cmd not in COMMANDS:
        raise ProtocolError("COMMAND")
    for name in ("cycle", "request", "seq"):
        if name in message and (type(message[name]) is not int or not 0 <= message[name] <= 0xFFFFFFFF):
            raise ProtocolError(name.upper())
    if cmd in {"NACK", "FAULT"}:
        if not isinstance(message.get("reason"), str) or not message["reason"]:
            raise ProtocolError("REASON_REQUIRED")
        if ("cycle" in message) != ("request" in message):
            raise ProtocolError("ERROR_IDENTITY")
    if cmd in {"INSPECT", "SORT", "ACK", "DONE"} and "cycle" not in message:
        raise ProtocolError("CYCLE_REQUIRED")
    if cmd == "SORT":
        if "request" not in message or type(message.get("dest")) is not int or message["dest"] not in range(4):
            raise ProtocolError("SORT_FIELDS")
        if set(message) != {"v", "boot", "cycle", "request", "cmd", "dest"}:
            raise ProtocolError("SORT_FIELDS")
    if cmd == "DONE":
        if ("request" not in message or "seq" not in message
                or type(message.get("confirmed_bin")) is not int
                or message["confirmed_bin"] not in range(4)):
            raise ProtocolError("DONE_FIELDS")


def encode(message: dict[str, Any]) -> bytes:
    validate(message)
    payload = json.dumps(message, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("ascii")
    line = payload + f"|{crc16(payload):04X}\n".encode("ascii")
    if len(line) > MAX_BYTES:
        raise ProtocolError("OVERSIZE")
    return line


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolError("DUPLICATE_KEY")
        result[key] = value
    return result


def decode(line: bytes) -> dict[str, Any]:
    if len(line) > MAX_BYTES or not line.endswith(b"\n"):
        raise ProtocolError("FRAMING")
    try:
        payload, checksum = line[:-1].rsplit(b"|", 1)
        if len(checksum) != 4 or any(c not in b"0123456789abcdefABCDEF" for c in checksum):
            raise ProtocolError("CRC_FORMAT")
        if crc16(payload) != int(checksum, 16):
            raise ProtocolError("CRC")
        if b"\n" in payload or b"\r" in payload:
            raise ProtocolError("INTERNAL_NEWLINE")
        message = json.loads(payload.decode("ascii"), object_pairs_hook=_unique_object,
                             parse_constant=lambda _: (_ for _ in ()).throw(ProtocolError("NONFINITE")))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ProtocolError(str(exc)) from exc
    validate(message)
    return message


class StreamParser:
    """Buffer acotado; tras exceso descarta hasta LF, nunca ejecuta el sufijo."""

    def __init__(self, timeout_ms: int = 250):
        self.timeout_ms = timeout_ms
        self.buffer = bytearray()
        self.started_ms: int | None = None
        self.discarding = False
        self.errors: list[str] = []

    def feed(self, data: bytes, now_ms: int) -> list[dict[str, Any]]:
        self.errors = []
        if self.started_ms is not None and now_ms - self.started_ms >= self.timeout_ms:
            self.buffer.clear()
            self.started_ms = None
            self.discarding = True
            self.errors.append("PARTIAL_TIMEOUT")
        messages = []
        for byte in data:
            if self.discarding:
                if byte == 10:
                    self.discarding = False
                continue
            if self.started_ms is None:
                self.started_ms = now_ms
            self.buffer.append(byte)
            if len(self.buffer) > MAX_BYTES:
                self.errors.append("OVERSIZE")
                self.buffer.clear()
                self.started_ms = None
                self.discarding = byte != 10
            elif byte == 10:
                try:
                    messages.append(decode(bytes(self.buffer)))
                except ProtocolError as exc:
                    self.errors.append(str(exc))
                self.buffer.clear()
                self.started_ms = None
        return messages
