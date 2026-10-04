"""Scan tracked files, reachable Git blobs and local env files without printing matches."""
import io
import os
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = [
    re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}'),
    re.compile(rb'github_pat_[A-Za-z0-9_]{40,}'),
    re.compile(rb'AKIA[A-Z0-9]{16}'),
    re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(rb'(?:ROBOFLOW_API_KEY|api_key)\s*[:=]\s*[\x22\x27]([A-Za-z0-9_-]{20,})[\x22\x27]'),
    re.compile(rb'(?:api_key|access_token|X-Amz-Signature)=[A-Za-z0-9%/_+-]{24,}')
]


def unsafe(data, secret):
    if secret and secret in data:
        return True
    if any(pattern.search(data) for pattern in PATTERNS):
        return True
    if data.startswith(b'PK\x03\x04'):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                for info in archive.infolist():
                    if info.file_size <= 20*1024**2 and not info.is_dir():
                        child = archive.read(info)
                        if (secret and secret in child) or any(p.search(child) for p in PATTERNS):
                            return True
        except (zipfile.BadZipFile, RuntimeError):
            return True
    return False


def scan():
    secret = os.environ.get('ROBOFLOW_API_KEY', '').encode() or None
    # Capture git grep output: never send matching source lines to the terminal.
    subprocess.run(['git','grep','-l','-I','-E','ROBOFLOW_API_KEY|api_key|Authorization'],
                   cwd=ROOT, capture_output=True, check=False)
    paths = subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    for name in paths:
        if name and (ROOT/name).is_file() and unsafe((ROOT/name).read_bytes(),secret):
            return False
    for path in ROOT.rglob('.env*'):
        if path.is_file() and '.git' not in path.parts and path.name != '.env.example':
            if unsafe(path.read_bytes(),secret):
                return False
    objects = subprocess.check_output(['git','rev-list','--objects','--all'],cwd=ROOT)
    ids = b'\n'.join(line.split(b' ',1)[0] for line in objects.splitlines()) + b'\n'
    raw = subprocess.check_output(['git','cat-file','--batch'],input=ids,cwd=ROOT)
    stream = io.BytesIO(raw)
    while header := stream.readline():
        fields = header.split()
        if len(fields) != 3:
            raise ValueError('Git object scan failed')
        data = stream.read(int(fields[2])); stream.read(1)
        if fields[1] == b'blob' and unsafe(data,secret):
            return False
    return True


if __name__ == '__main__':
    try:
        passed = scan()
    except Exception:
        passed = False
    print('SECRET_SCAN = ' + ('PASS' if passed else 'FAIL'))
    raise SystemExit(0 if passed else 1)
