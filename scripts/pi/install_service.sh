#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
if [[ ! -x "$repo_root/.venv/bin/python" ]]; then echo 'Run bootstrap_pi first'; exit 1; fi
sudo useradd --system --create-home --groups video,render,dialout sortv1 2>/dev/null || id sortv1
sudo install -d -o sortv1 -g sortv1 /opt/sortv1
sudo cp -a "$repo_root/." /opt/sortv1/
sudo chown -R sortv1:sortv1 /opt/sortv1
# Recreate venv because interpreter/entry-point paths are absolute.
sudo -u sortv1 python3 -m venv --system-site-packages /opt/sortv1/.venv
sudo -u sortv1 /opt/sortv1/.venv/bin/python -m pip install onnxruntime==1.30.0
sudo install -m 644 "$repo_root/deploy/systemd/sortv1.service" /etc/systemd/system/sortv1.service
sudo systemctl daemon-reload
echo 'Service installed and stopped. Complete calibration/model gates before systemctl start sortv1.'
