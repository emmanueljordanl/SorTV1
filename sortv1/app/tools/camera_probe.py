"""Collect physical camera evidence and measure existing quality quantities."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

def quantities(rgb, background):
    rgb=np.asarray(rgb);background=np.asarray(background)
    if rgb.dtype!=np.uint8 or rgb.ndim!=3 or rgb.shape[2]!=3 or min(rgb.shape[:2])<3 or rgb.shape!=background.shape:
        raise ValueError('RGB/background shapes must agree and contain at least 3x3 pixels')
    grey=rgb.astype(np.float32).mean(axis=2)
    lap=grey[1:-1,:-2]+grey[1:-1,2:]+grey[:-2,1:-1]+grey[2:,1:-1]-4*grey[1:-1,1:-1]
    return dict(mean=float(grey.mean()),laplacian_variance=float(lap.var()),clipped_fraction=float(((grey<=2)|(grey>=253)).mean()),presence_difference=float(np.abs(rgb.astype(np.float32)-background.astype(np.float32)).mean()))

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='mode',required=True)
    c=sub.add_parser('capture');c.add_argument('--output',type=Path,required=True);c.add_argument('--power-isolated',action='store_true',required=True)
    m=sub.add_parser('measure');m.add_argument('--background',type=Path,required=True);m.add_argument('--images',type=Path,nargs='+',required=True);m.add_argument('--roi',type=int,nargs=4,required=True);m.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():p.error('Refusing to overwrite evidence')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    if a.mode=='capture':
        from app.capture.picamera2_capture import PicameraCapture
        from app.contracts import Cycle
        from app.utils import load_json, write_json
        config=load_json(Path('config/camera.json'));config['roi']=None
        camera=PicameraCapture(config,calibration=True)
        try:
            cycle=Cycle('camera-measurement',1);camera.begin(cycle);frame=camera.capture(cycle)
            Image.fromarray(frame.rgb).save(a.output)
            write_json(a.output.with_suffix('.json'),dict(source='PHYSICAL',effective_controls=frame.controls,captured_ns=frame.captured_ns,status='MEASUREMENT_ONLY'))
            grid=Image.fromarray(frame.rgb).copy();draw=ImageDraw.Draw(grid)
            for x in range(0,grid.width,40):draw.line((x,0,x,grid.height),fill='yellow');draw.text((x+2,2),str(x),fill='black',stroke_width=1,stroke_fill='yellow')
            for y in range(0,grid.height,40):draw.line((0,y,grid.width,y),fill='yellow');draw.text((2,y+12),str(y),fill='black',stroke_width=1,stroke_fill='yellow')
            grid.save(a.output.with_name(a.output.stem+'-grid.png'));print(a.output)
        finally:camera.close()
    else:
        x,y,w,h=a.roi
        def crop(path):
            rgb=np.asarray(Image.open(path).convert('RGB'))
            if min(x,y)<0 or min(w,h)<3 or x+w>rgb.shape[1] or y+h>rgb.shape[0]:raise ValueError('ROI outside image')
            return rgb[y:y+h,x:x+w]
        background=crop(a.background)
        with a.output.open('w',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=['image','mean','laplacian_variance','clipped_fraction','presence_difference']);writer.writeheader()
            for path in a.images:writer.writerow(dict(image=str(path),**quantities(crop(path),background)))
        print(a.output)
if __name__=='__main__':main()
