"""Repository/environment report. PENDING hardware is distinct from software errors."""
import argparse
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'sortv1'))
from app.utils import load_json,sha256

def main():
    p=argparse.ArgumentParser();p.add_argument('--hardware',action='store_true');p.add_argument('--output',type=Path);a=p.parse_args()
    checks=[]
    for name,cmd in [('repository',[sys.executable,str(ROOT/'scripts/verify_repository.py')]),('canonical_hardware',[sys.executable,str(ROOT/'scripts/generate_hardware_views.py'),'--check']),('mvp_safety',[sys.executable,str(ROOT/'scripts/verify_mvp.py')])]:
        r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True);checks.append(dict(check=name,status='PASS' if r.returncode==0 else 'FAIL',detail=(r.stdout+r.stderr).strip()))
    packages={}
    for name in ['numpy','Pillow','pyserial','onnxruntime','torch','torchvision','roboflow-slim']:
        try:packages[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:packages[name]=None
    hardware=[]
    for name,file in [('camera','config/camera.json'),('quality','config/quality.json'),('firmware','firmware/config/calibration.json')]:
        c=load_json(ROOT/'sortv1'/file);hardware.append(dict(check=name,status=c['status']))
    model=ROOT/'sortv1/models/active'
    if model.exists():
        from app.inference.onnx_runtime import OnnxInference
        try:instance=OnnxInference(model);hardware.append(dict(check='model',status='NUMERICALLY_VERIFIED',sha256=instance.model_sha256))
        except Exception as e:checks.append(dict(check='model',status='FAIL',detail=str(e)))
    else:hardware.append(dict(check='model',status='PENDING_REAL_TRAINING'))
    if a.hardware:
        try:
            from serial.tools.list_ports import comports
            devices=[dict(device=p.device,vid=p.vid,pid=p.pid,serial_number=p.serial_number) for p in comports()]
            hardware.append(dict(check='USB',devices=devices,status='OBSERVED'))
        except ImportError:checks.append(dict(check='pyserial',status='FAIL'))
        try:
            from picamera2 import Picamera2
            cameras=Picamera2.global_camera_info();hardware.append(dict(check='CSI',cameras=cameras,status='OBSERVED' if cameras else 'PENDING_HARDWARE'))
        except ImportError:hardware.append(dict(check='CSI',status='PENDING_PI_SYSTEM_PICAMERA2'))
    report=dict(host=platform.node(),OS=platform.platform(),python=sys.version,packages=packages,software=checks,hardware=hardware,
                physical_acceptance={f'P{n:02}':'PENDING' for n in range(1,17)})
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));return int(any(c['status']=='FAIL' for c in checks))
if __name__=='__main__':raise SystemExit(main())
