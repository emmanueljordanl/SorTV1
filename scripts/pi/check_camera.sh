#!/usr/bin/env bash
set -euo pipefail
rpicam-hello --list-cameras
python3 -c 'from picamera2 import Picamera2; print(Picamera2.global_camera_info())'
