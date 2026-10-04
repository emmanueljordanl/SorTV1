# Raspberry Pi 5

Pi5 2GB, fuente oficial5.1V/5A, microSD≥64GB, Active Cooler, Camera Module3 estándar, CSI15→22 y USB de datos. Raspberry Pi OS Lite64bits; registrar imagen/versión/SHA. Instalar cooler y CSI sin alimentación; comprobar orientación según conectores reales.

Clonar repo y cambiar a feature/mvp-physical-integration. Desde raíz: `bash scripts/pi/bootstrap_pi.sh`, `bash scripts/pi/check_camera.sh`, `.venv/bin/python scripts/doctor.py --hardware`. Venv con system-site-packages: Picamera2/libcamera/NumPy/Pillow son apt; ORT es pip. No instalar entrenamiento en Pi ni sustituir NumPy del sistema sin verificar ABI. ORT wheel debe existir para Python/aarch64 del OS escogido; si no, seleccionar versión compatible con ADR, nunca ignorar errores.

Doctor lista USB VID/PID/serial. Fijar serial_number único observado, operador y modelo en sortv1/config/physical.json. COM/tty fijo solo fallback. Pico SDK USB suele VID0x2E8A/PID0x000A; confirmar con hardware. Puertos ambiguos se rechazan.

Sin actuadores: flashear UF2 BOOT_SAFE no calibrado. Desde sortv1: `../.venv/bin/python -m app.tools.hil_protocol`, luego hil_sensors. Observar calibrated=false y hx_raw/tof_mm reales o null. No hay rearme/movimiento remoto.

Completar [BRINGUP](BRINGUP.md), calibraciones y modelo validado LOCAL_PHYSICAL; copiar paquete completo a sortv1/models/active. Modelo sintético está bloqueado para AUTO. Configurar admission_record; sin admisión humana por ciclo, REVIEW.

Instalar servicio detenido: `bash scripts/pi/install_service.sh`. Revisar config/modelo en /opt/sortv1 y doctor con usuario sortv1. Tras gates: `sudo systemctl start sortv1`; `journalctl -u sortv1 -n 100`; UI http://127.0.0.1:8080. Laptop: túnel `ssh -L 8080:127.0.0.1:8080 usuario@pi`. Servicio no root, reintentos limitados, inicio desarmado. Habilitar al boot solo tras validar recuperación y supervisión.

API: [Picamera2](https://github.com/raspberrypi/picamera2), [manual](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf). BGR888 produce array RGB por orden de bytes; verificar carta roja/azul antes de entrenar. Se registra timestamp del sensor y controles efectivos, sin retimestamp de buffers antiguos.
