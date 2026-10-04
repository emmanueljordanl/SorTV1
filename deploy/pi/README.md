# Despliegue Pi

Usar Raspberry Pi OS Lite **64 bits**. Ejecutar `scripts/pi/bootstrap_pi.sh`; conservar NumPy/Pillow/Picamera2/libcamera del sistema en venv con `--system-site-packages`. No instalar Torch en la Pi. Copiar solamente el paquete ONNX verificado a `sortv1/models/active`. Completar `config/{camera,quality,physical}.json` con los datos medidos. Instalar el servicio detenido con `scripts/pi/install_service.sh`. Procedimiento completo en [PI_INSTALL](../../docs/PI_INSTALL.md).
