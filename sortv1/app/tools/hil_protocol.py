import argparse
import json
import queue
import time
from pathlib import Path
from app.transport.serial_transport import SerialTransport
from app.utils import load_json, write_json

def run(kind="protocol"):
    p = argparse.ArgumentParser(description="Real USB HIL. Default is read-only; heartbeat cannot arm MCU")
    p.add_argument("--config", type=Path, default=Path("config/physical.json")); p.add_argument("--seconds", type=float, default=10)
    p.add_argument("--output", type=Path, default=Path("evidence/experiments/hil.json"))
    p.add_argument("--enable-actuators", action="store_true"); p.add_argument("--dest", type=int, choices=range(4))
    a = p.parse_args()
    if a.enable_actuators and (kind != "cycle" or a.dest is None): p.error("Movement requires hil_cycle and explicit --dest")
    link = SerialTransport(load_json(a.config)["serial"]); link.start(); records = []; sent = False; status = {}; deadline = time.monotonic()+a.seconds
    try:
        while time.monotonic() < deadline:
            try: m = link.events.get(timeout=0.2)
            except queue.Empty: continue
            records.append({"monotonic_ns": time.monotonic_ns(), "message": m})
            print(json.dumps(m))
            if m["cmd"] == "STATUS": status = m
            if m["cmd"] == "HELLO": link.send({"v": 1, "cmd": "QUERY", "boot": m["boot"]})
            if a.enable_actuators and not sent and m["cmd"] == "INSPECT":
                if not all(status.get(k) is True for k in ("calibrated", "lid", "service", "power", "gate_closed", "presence")) or status.get("fill", [])[a.dest] != "AVAILABLE":
                    raise RuntimeError("Physical guards do not permit diagnostic SORT")
                link.send({"v": 1, "cmd": "SORT", "boot": m["boot"], "cycle": m["cycle"], "request": 1, "dest": a.dest}); sent = True
    finally:
        link.close(); write_json(a.output, {"source": "PHYSICAL", "mode": "DIAGNOSTIC", "tool": kind, "records": records,
                                           "status": "RECORDED" if records else "NO_HARDWARE", "acceptance": "PENDING"})
    if not records: raise SystemExit("No hardware connected; no test PASS")
if __name__ == "__main__": run()
