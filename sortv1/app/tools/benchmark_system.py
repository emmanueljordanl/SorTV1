import argparse
import json
import queue
import time
from pathlib import Path
import numpy as np
import psutil
from app.transport.serial_transport import SerialTransport
from app.utils import load_json,write_json

def main():
    p=argparse.ArgumentParser(description='Passive real-system monitor. Does not request motion')
    p.add_argument('--minutes',type=float,default=60);p.add_argument('--output',type=Path,default=Path('evidence/benchmarks/system.json'))
    a=p.parse_args();link=SerialTransport(load_json(Path('config/physical.json'))['serial']);link.start();start=time.monotonic();samples=[]
    try:
        while time.monotonic()-start<a.minutes*60:
            try:m=link.events.get(timeout=1)
            except queue.Empty:continue
            if m['cmd']=='STATUS':
                temp=Path('/sys/class/thermal/thermal_zone0/temp')
                samples.append(dict(elapsed_s=time.monotonic()-start,status=m,ram_available=psutil.virtual_memory().available,temperature_c=float(temp.read_text())/1000 if temp.exists() else None))
    finally:link.close()
    write_json(a.output,dict(source='PHYSICAL',elapsed_s=time.monotonic()-start,samples=samples,status='RECORDED' if samples else 'NO_HARDWARE',acceptance='PENDING'))
    if not samples:raise SystemExit('No hardware; no benchmark PASS')
if __name__=='__main__':main()
