import argparse
from pathlib import Path
from app.evidence import Journal

def main():
    p = argparse.ArgumentParser(description="Stop service and isolate actuator power before recording closure")
    p.add_argument("--journal", type=Path, required=True); p.add_argument("--cycle", required=True)
    p.add_argument("--outcome", choices=["REMOVED", "ABORTED", "RECONCILED"], required=True)
    for name in ("operator", "reason", "evidence"): p.add_argument("--"+name, required=True)
    for name in ("power-isolated", "tray-empty", "path-clear", "gate-closed"): p.add_argument("--"+name, action="store_true", required=True)
    a = p.parse_args(); Journal(a.journal, "PHYSICAL").close_manual(a.cycle, a.outcome, operator=a.operator, reason=a.reason,
        evidence=a.evidence, physical_state={k: getattr(a, k) for k in ("power_isolated", "tray_empty", "path_clear", "gate_closed")})
if __name__ == "__main__": main()
