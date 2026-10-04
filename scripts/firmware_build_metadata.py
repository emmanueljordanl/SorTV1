"""Record the actual build commit/compiler/SDK/UF2; never hardware acceptance."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from bin_to_uf2 import verify

ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--build', type=Path, default=ROOT/'build/pico')
    args = parser.parse_args()
    uf2 = args.build/'sortv1_pico.uf2'
    record = {
        'git_commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'sdk_commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=args.sdk,text=True).strip(),
        'sdk_version': '2.3.1',
        'compiler': subprocess.check_output(['arm-none-eabi-g++','--version'],text=True).splitlines()[0],
        'uf2_sha256': hashlib.sha256(uf2.read_bytes()).hexdigest(),
        'uf2_bytes': uf2.stat().st_size,
        'flash_blocks': verify(uf2,args.build/'sortv1_pico.bin'),
        'calibrated': False, 'physical_acceptance': 'PENDING'
    }
    if record['sdk_commit'] != '079c6f39023649b154152db30f1d781e884879bc':
        raise ValueError('Unexpected SDK commit')
    if 'verified=false' not in (ROOT/'sortv1/firmware/include/calibration.hpp').read_text():
        raise ValueError('Release build must use safe uncalibrated defaults')
    (args.build/'BUILD_INFO.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record))
