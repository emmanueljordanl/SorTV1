"""Generate compile-time values only from operator-signed physical calibration."""
import argparse
import json
import math
from pathlib import Path

def generate(path, output):
    c = json.loads(path.read_text())
    if c.get("status") != "CALIBRATED" or not c.get("operator") or not Path(c.get("evidence_path", "")).is_file(): raise ValueError("Physical calibration evidence required")
    for key in ("hx711_offset", "hx711_mg_per_count", "presence_mg", "stable_span_mg", "overweight_mg", "servo_closed_us", "servo_open_us", "step_period_us"):
        if type(c.get(key)) not in (int, float) or not math.isfinite(c[key]): raise ValueError(key)
    if not (0 < c["presence_mg"] < c["overweight_mg"] <= 200000) or c["stable_span_mg"] <= 0 or c["hx711_mg_per_count"] == 0: raise ValueError("Weight calibration range")
    if any(not 500 <= c[k] <= 2500 for k in ("servo_closed_us", "servo_open_us")) or c["servo_closed_us"] == c["servo_open_us"]: raise ValueError("Servo measured endpoints")
    if type(c["step_period_us"]) is not int or c["step_period_us"] < 20 or type(c.get("direction")) is not bool: raise ValueError("STEP timing/direction")
    if not isinstance(c.get("active_high"), list) or len(c["active_high"]) != 29 or any(type(x) is not bool for x in c["active_high"]): raise ValueError("Measured GPIO polarity required")
    for k in ("tof_full_mm", "tof_hysteresis_mm"):
        if not isinstance(c.get(k), list) or len(c[k]) != 4 or any(type(v) is not int or v <= 0 for v in c[k]): raise ValueError(k)
    lines = ['#pragma once', '#include <array>', 'namespace calibration {', 'constexpr bool verified=true;']
    for k, typ in [("active_high", "bool"), ("tof_full_mm", "unsigned"), ("tof_hysteresis_mm", "unsigned")]:
        values = ','.join(str(v).lower() for v in c[k]); lines.append(f'constexpr std::array<{typ},{len(c[k])}> {k}{{{{{values}}}}};')
    for key, typ, name in [("hx711_offset", "int", "hx_offset"), ("hx711_mg_per_count", "float", "mg_per_count"), ("presence_mg", "int", "presence_mg"), ("stable_span_mg", "int", "stable_span_mg"), ("overweight_mg", "int", "overweight_mg"), ("servo_closed_us", "unsigned", "servo_closed_us"), ("servo_open_us", "unsigned", "servo_open_us"), ("step_period_us", "unsigned", "step_period_us"), ("direction", "bool", "direction")]:
        value = str(c[key]).lower(); lines.append(f'constexpr {typ} {name}={value};')
    output.write_text('\n'.join(lines)+'\n}\n')
if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--calibration',type=Path,required=True); p.add_argument('--output',type=Path,default=Path('sortv1/firmware/include/calibration.hpp'))
    a=p.parse_args(); generate(a.calibration,a.output)
