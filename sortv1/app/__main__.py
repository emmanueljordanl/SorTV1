"""Demostración de contratos. Todos los datos son sintéticos y rotulados."""

import argparse
import json
from pathlib import Path
from time import monotonic_ns
from uuid import uuid4

from app.contracts import Cycle, Frame, LABELS, Prediction
from app.controller import Controller
from app.controller.simulator import SimulatedPico
from app.decision import decide
from app.evidence import Journal
from app.quality import assess
from app.transport import decode, encode


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--mode", choices=["physical", "diagnostic"])
    parser.add_argument("--enable-actuators", action="store_true")
    parser.add_argument("--dest", type=int, choices=range(4))
    parser.add_argument("--journal", type=Path, default=None)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.mode:
        from app.controller.physical import PhysicalService
        PhysicalService(root, diagnostic=args.mode == "diagnostic", enable_actuators=args.enable_actuators, destination=args.dest).run()
        return
    if not args.simulate: parser.error("Choose --simulate or --mode")
    settings = json.loads((root / "config/system.json").read_text())
    thresholds = json.loads((root / "config/thresholds.json").read_text())
    boot = "sim-" + uuid4().hex
    path = args.journal or root / "evidence/experiments" / f"{boot}.jsonl"
    journal = Journal(path, "SIMULATION")
    controller = Controller(journal)
    pico = SimulatedPico(boot)
    controller.connect(boot)
    for destination in range(4):
        cycle = Cycle(boot, destination + 1)
        inspection = decode(encode(pico.inspect(cycle.number)))
        controller.inspect(Cycle(inspection["boot"], inspection["cycle"]))
        predictions, qualities = [], []
        for index in range(3):
            now = monotonic_ns()
            frame = Frame(f"{cycle.key}:{index}", cycle, now, b"SYNTHETIC_RGB", {})
            qualities.append(assess(frame, cycle, now, occupied=True, exposure_ok=True,
                                    focus_ok=True, max_age_ms=settings["frame_max_age_ms"]))
            values = tuple(0.94 if i == destination else 0.02 for i in range(4))
            predictions.append(Prediction(frame.frame_id, values, "SIMULATED_NO_MODEL", 0))
        decision = decide(predictions, qualities, admitted=True, bins_available=(True,) * 4,
                          top1_min=thresholds["top1_min_exclusive"],
                          margin_min=thresholds["margin_min_exclusive"])
        command = controller.request_sort(decision)
        assert command is not None
        result = pico.sort(decode(encode(command)))
        controller.on_message(decode(encode(result)))
        controller.on_message(result)  # Prueba visible de deduplicación.
        print(f"SIMULATION | {cycle.key} | {LABELS[destination]} | DONE sintético")
    print(json.dumps({"source": "SIMULATION", "counts": journal.counts(), "journal": str(path)}))


if __name__ == "__main__":
    main()
