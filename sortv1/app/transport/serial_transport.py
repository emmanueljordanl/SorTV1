"""One reader, independent heartbeat, bounded writes; reconnect never replays SORT."""
import queue
import threading
import time
from app.transport import StreamParser, encode


class SerialTransport:
    def __init__(self, config: dict, *, serial_factory=None, ports_factory=None):
        import serial
        from serial.tools.list_ports import comports
        self.config = config; self.serial_factory = serial_factory or serial.Serial
        self.ports_factory = ports_factory or comports
        self.events = queue.Queue(maxsize=128); self.stop = threading.Event()
        self.lock = threading.RLock(); self.serial = None; self.boot = None
        self.parser = StreamParser(); self.generation = 0
        self.metrics = {"rx": 0, "tx": 0, "errors": 0, "reconnects": 0}

    def select_port(self):
        ports = [p for p in self.ports_factory() if p.vid == self.config["vid"] and p.pid == self.config["pid"]
                 and (not self.config.get("serial_number") or p.serial_number == self.config["serial_number"])
                 and (not self.config.get("port") or p.device == self.config["port"])]
        if len(ports) != 1: raise OSError("USB identity absent or ambiguous; configure serial_number")
        return ports[0].device

    def start(self):
        self.reader = threading.Thread(target=self._read, daemon=True, name="usb-reader")
        self.heartbeat = threading.Thread(target=self._heartbeat, daemon=True, name="usb-heartbeat")
        self.reader.start(); self.heartbeat.start()

    def _event(self, value):
        try: self.events.put_nowait(value)
        except queue.Full:
            self.metrics["errors"] += 1; self._disconnect("RX_QUEUE_OVERFLOW")

    def send(self, message):
        data = encode(message)
        with self.lock:
            if self.serial is None or message["boot"] != self.boot: raise OSError("USB session changed")
            if self.serial.write(data) != len(data): raise OSError("USB partial write")
            self.metrics["tx"] += 1

    def _disconnect(self, reason):
        with self.lock:
            had_connection = self.serial is not None
            if self.serial is not None:
                try: self.serial.close()
                except OSError: pass
            self.serial = None; self.boot = None; self.parser = StreamParser()
        if had_connection:
            try: self.events.put_nowait({"cmd": "DISCONNECTED", "reason": reason})
            except queue.Full: pass

    def _read(self):
        while not self.stop.is_set():
            try:
                if self.serial is None:
                    port = self.select_port()
                    with self.lock:
                        self.serial = self.serial_factory(port=port, baudrate=115200, timeout=0.05, write_timeout=0.05)
                        self.serial.reset_input_buffer(); self.generation += 1; self.metrics["reconnects"] += 1
                data = self.serial.read(512)
                for message in self.parser.feed(data, int(time.monotonic()*1000)):
                    self.metrics["rx"] += 1
                    if message["cmd"] in {"HELLO", "STATUS"}:
                        if self.boot is not None and self.boot != message["boot"]: self._event({"cmd": "DISCONNECTED", "reason": "MCU_REBOOT"})
                        self.boot = message["boot"]
                    self._event(message)
                self.metrics["errors"] += len(self.parser.errors)
            except Exception as exc:
                self._disconnect(type(exc).__name__); self.stop.wait(0.5)

    def _heartbeat(self):
        while not self.stop.wait(0.2):
            try:
                if self.boot: self.send({"v": 1, "cmd": "HEARTBEAT", "boot": self.boot})
            except Exception: self._disconnect("HEARTBEAT_WRITE_FAILED")

    def close(self):
        self.stop.set(); self._disconnect("SHUTDOWN")
        for name in ("reader", "heartbeat"):
            thread = getattr(self, name, None)
            if thread: thread.join(timeout=2)
