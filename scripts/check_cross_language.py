import argparse
import subprocess
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'sortv1'))
from app.transport import crc16
VECTORS=[b'123456789',b'',b'SorTV1',b'{"v":1,"boot":"golden","cmd":"HEARTBEAT"}']
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('host_binary',type=Path); a=p.parse_args()
    got=subprocess.check_output([str(a.host_binary.resolve())],text=True).splitlines()
    expected=[f'{crc16(v):04X}' for v in VECTORS]
    if got!=expected: raise SystemExit(f'Cross-language mismatch: {got} != {expected}')
    print('PASS: C++ state machine, framing and Python/C++ CRC vectors')
