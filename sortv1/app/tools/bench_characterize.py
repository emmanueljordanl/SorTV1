"""One explicit bounded action on BENCH firmware; records are not acceptance PASS."""
import argparse
import json
import threading
import time
from pathlib import Path
import serial

def crc16(data):
    crc=0xffff
    for b in data:
        crc ^= b<<8
        for _ in range(8): crc=((crc<<1)^0x1021)&0xffff if crc&0x8000 else (crc<<1)&0xffff
    return crc

def decode(raw):
    try:
        line=raw.strip();payload,check=line.rsplit(b'|',1)
        if len(check)!=4 or int(check,16)!=crc16(payload): return None
        p=payload.decode('ascii').split('|')
        if len(p)!=6 or p[0]!='BENCH1':return None
        return dict(boot=p[1],cmd=p[2],seq=int(p[3]),a=int(p[4]),b=int(p[5]))
    except (ValueError,UnicodeError):return None

def main():
    p=argparse.ArgumentParser(description='BENCH only. Production calibration stays false.')
    p.add_argument('--port',required=True);p.add_argument('--operator',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--actuator',choices=['step','servo'],required=True);p.add_argument('--steps',type=int,default=1);p.add_argument('--period-us',type=int,default=10000)
    p.add_argument('--pulse-us',type=int);p.add_argument('--duration-ms',type=int,default=100)
    p.add_argument('--fixture-checked',action='store_true',required=True);a=p.parse_args()
    if a.output.exists():p.error('Evidence path already exists')
    if a.actuator=='step' and not (1<=a.steps<=32 and 2000<=a.period_us<=10000):p.error('STEP bounds')
    if a.actuator=='servo' and not (a.pulse_us is not None and 500<=a.pulse_us<=2500 and 20<=a.duration_ms<=500):p.error('SERVO bounds')
    records=[];link=serial.Serial(a.port,115200,timeout=.05,write_timeout=.2);done=threading.Event();lock=threading.Lock();seq=0;boot=None
    def send(cmd,x=0,y=0):
        nonlocal seq
        with lock:
            seq+=1;body=f'BENCH1|{boot}|{cmd}|{seq}|{x}|{y}'.encode();link.write(body+f'|{crc16(body):04X}\n'.encode())
            records.append(dict(time_ns=time.monotonic_ns(),sent=cmd,seq=seq,a=x,b=y))
            return seq
    def receive():
        nonlocal boot
        while not done.is_set():
            msg=decode(link.read_until(b'\n',160))
            if msg:
                records.append(dict(time_ns=time.monotonic_ns(),received=msg))
                if msg['cmd']=='HELLO':
                    if boot is not None and boot!=msg['boot']:done.set()
                    else:boot=msg['boot']
    receiver=threading.Thread(target=receive,daemon=True);receiver.start()
    def heartbeat():
        while not done.wait(.1):
            try:send('PING')
            except Exception:done.set()
    heart=None
    try:
        deadline=time.monotonic()+5
        while boot is None and time.monotonic()<deadline and not done.is_set():time.sleep(.02)
        if boot is None:raise RuntimeError('No BENCH HELLO. Stop; do not use SORT firmware.')
        heart=threading.Thread(target=heartbeat,daemon=True);heart.start()
        print('Hold physical RESET deadman. Guards and actuator power must be closed. Only one actuator connected.')
        if input('Type EJECUTAR to request ONE action, or anything else to stop: ').strip()!='EJECUTAR':return
        if done.is_set():raise RuntimeError('Link changed; no action')
        send('STEP' if a.actuator=='step' else 'SERVO',a.steps if a.actuator=='step' else a.pulse_us,a.period_us if a.actuator=='step' else a.duration_ms)
        deadline=time.monotonic()+1
        while time.monotonic()<deadline and not done.is_set():time.sleep(.02)
        send('STOP');print('Power off. Review ACCEPTED/REJECTED and observed travel; no automatic retry.')
    finally:
        done.set()
        if heart:heart.join(timeout=1)
        receiver.join(timeout=1);link.close();a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(dict(source='PHYSICAL',mode='BENCH_ONLY',operator=a.operator,status='RECORDED',acceptance='PENDING',calibration_verified=False,records=records),indent=2)+'\n')
if __name__=='__main__':main()
