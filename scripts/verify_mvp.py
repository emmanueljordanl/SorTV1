"""Required software artifacts, safe initial configuration and physical-pending audit."""
import csv
import json
import re
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REQUIRED='''docs/audit/MVP_GAP_ANALYSIS.md docs/audit/FINAL_MVP_AUDIT.md docs/MVP_STATUS.md docs/BRINGUP.md docs/OPERATION.md docs/RECOVERY.md docs/PI_INSTALL.md docs/PI_RECOVERY.md docs/MICROSD_BACKUP.md docs/DEV_SETUP_WINDOWS.md docs/TESTING.md docs/ml/TRASHIA_MAPPING_REPORT.md
sortv1/app/capture/picamera2_capture.py sortv1/app/inference/onnx_runtime.py sortv1/app/transport/serial_transport.py sortv1/app/controller/physical.py sortv1/app/operator_ui/__init__.py
sortv1/app/tools/hil_protocol.py sortv1/app/tools/hil_sensors.py sortv1/app/tools/hil_cycle.py sortv1/app/tools/capture_dataset.py
sortv1/firmware/CMakeLists.txt sortv1/firmware/src/main.cpp sortv1/firmware/src/state_machine.cpp sortv1/firmware/src/protocol.cpp sortv1/firmware/src/sensors.cpp sortv1/firmware/src/actuators.cpp
sortv1/training/configs/baseline.yaml sortv1/training/train/train.py sortv1/training/evaluate/evaluate.py sortv1/training/export/export_onnx.py sortv1/training/benchmark/benchmark_onnx.py sortv1/training/tools/prepare_dataset.py
sortv1/hardware/source/bom_master.csv sortv1/hardware/source/pinout_master.csv sortv1/hardware/source/connections_master.csv sortv1/hardware/source/signals_master.csv sortv1/hardware/bom/bom_mvp_minimum.csv sortv1/hardware/bom/bom_traceability.csv sortv1/hardware/wiring/wire_from_to.csv sortv1/hardware/wiring/terminal_matrix.csv sortv1/hardware/wiring/fuse_matrix.csv deploy/systemd/sortv1.service'''.split()

def main():
    for path in REQUIRED:
        if not (ROOT/path).is_file() or not (ROOT/path).stat().st_size:raise ValueError('MVP artifact absent: '+path)
    if (ROOT/'.env.example').read_text().strip()!='ROBOFLOW_API_KEY=':raise ValueError('Env example must contain only key name')
    source=ROOT/'sortv1'
    camera=json.loads((source/'config/camera.json').read_text())
    if camera['roi'] is not None or camera['locked'] is not False:raise ValueError('Unmeasured camera must be blocked by default')
    if 'verified=false' not in (source/'firmware/include/calibration.hpp').read_text():raise ValueError('Committed default firmware must stay uncalibrated')
    with (source/'tests/acceptance/matrix.csv').open(newline='',encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=16 or any(r['status']!='PENDING' for r in rows):raise ValueError('Initial physical P01-P16 must remain PENDING')
    for path in [ROOT/name for name in subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0') if name]:
        if path.suffix in {'.py','.json','.yaml','.yml','.md','.txt','.csv','.ps1','.sh','.hpp','.cpp'}:
            text=path.read_text(encoding='utf-8',errors='replace')
            if re.search(r'(?m)^\s*ROBOFLOW_API_KEY\s*=\s*[^\s\n#]+',text):raise ValueError('Potential credential assignment: '+str(path))
            if path.suffix in {'.py','.cpp','.hpp'} and 'vendor' not in path.parts and re.search(r'(?m)^\s*(?:#|//).*\b(?:TODO|FIXME)\b',text):raise ValueError('Unresolved software marker: '+str(path))
    print('PASS: MVP artifacts, safe defaults, no physical PASS or credential assignment')
if __name__=='__main__':main()
