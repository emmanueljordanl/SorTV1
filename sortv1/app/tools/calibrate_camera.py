"""Record measured camera controls, ROI and an empty-tray reference; operator supplies measured quality limits."""
import argparse
import time
from pathlib import Path
import numpy as np
from PIL import Image
from app.capture.picamera2_capture import PicameraCapture
from app.contracts import Cycle
from app.utils import load_json, write_json, sha256

def main():
    p=argparse.ArgumentParser(description="Isolate actuator power. Empty tray, actual illumination and measured focus required")
    p.add_argument('--roi',type=int,nargs=4,required=True);p.add_argument('--exposure-us',type=int,required=True)
    p.add_argument('--gain',type=float,required=True);p.add_argument('--colour-gains',type=float,nargs=2,required=True)
    p.add_argument('--lens-position',type=float,required=True);p.add_argument('--operator',required=True)
    for name in ['presence-min','laplacian-min','mean-min','mean-max','clipped-max']:p.add_argument('--'+name,type=float,required=True)
    p.add_argument('--power-isolated',action='store_true',required=True);p.add_argument('--tray-empty',action='store_true',required=True)
    a=p.parse_args()
    if not (a.exposure_us>0 and a.gain>0 and 0<=a.mean_min<a.mean_max<=255 and 0<a.clipped_max<=1 and a.presence_min>0 and a.laplacian_min>0):p.error('Invalid measured calibration')
    config=load_json(Path('config/camera.json'));config.update(roi=a.roi,locked=True,status='CALIBRATED')
    config['controls']={'AeEnable':False,'AwbEnable':False,'ExposureTime':a.exposure_us,'AnalogueGain':a.gain,'ColourGains':a.colour_gains,'AfMode':0,'LensPosition':a.lens_position}
    camera=PicameraCapture(config,calibration=True)
    try:
        camera.begin(Cycle('calibration',1)); frames=[camera.capture(Cycle('calibration',1)) for _ in range(3)]
        background=np.median(np.stack([f.rgb for f in frames]),axis=0).astype(np.uint8)
        path=Path('evidence/photos/calibration')/f'empty-{time.time_ns()}.png';path.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(background).save(path)
        quality=dict(status='CALIBRATED',max_age_ms=300,background_path=str(path),background_sha256=sha256(path),presence_difference_min=a.presence_min,
            laplacian_variance_min=a.laplacian_min,mean_min=a.mean_min,mean_max=a.mean_max,clipped_fraction_max=a.clipped_max)
        record={'source':'PHYSICAL','operator':a.operator,'camera':config,'quality':quality,'effective_controls':[f.controls for f in frames], 'status':'OPERATOR_CALIBRATION_REQUIRES_P08'}
        write_json(path.with_suffix('.json'),record);write_json(Path('config/camera.json'),config);write_json(Path('config/quality.json'),quality)
        print(path.with_suffix('.json'))
    finally:camera.close()
if __name__=='__main__':main()
