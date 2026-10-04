#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
if [[ "$(uname -m)" != "aarch64" ]]; then echo 'Raspberry Pi OS 64-bit required'; exit 1; fi
sudo apt-get update
sudo apt-get install -y python3-venv python3-picamera2 python3-numpy python3-pil python3-serial python3-psutil python3-yaml
python3 -m venv --system-site-packages "$repo_root/.venv"
# Use OS numpy/Pillow with apt Picamera2/libcamera ABI, never install a training stack on Pi.
"$repo_root/.venv/bin/python" -m pip install onnxruntime==1.30.0
"$repo_root/.venv/bin/python" "$repo_root/scripts/doctor.py" --hardware
