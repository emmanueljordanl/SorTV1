# Firmware del Pico W

Proyecto real C++17 PicoSDK2.3.1: CMakeLists.txt, src/include/vendor producen ELF/BIN/UF2 para PicoW, sin enlazar radios. Host contracts originales preservados; implementación física ejecutable es src/include. Build local y CI verificados, sin flasheo/prueba física disponible. Calibration.hpp verified=false por defecto: salidas motrices bloqueadas.

BOOT_SAFE nEN deshabilitado/sin PWM, boot nuevo, órdenes previas inválidas, rearme físico tras soltar/pulsar. CHECK_HOME confirma índice único100ms con trayectoria/bandeja vacías; no gira a ciegas si no hay posición conocida. Estados del plan completos, tick objetivo1ms, STEP por temporizador, servoPWM, watchdog después de sensores/guardas. Historial8 idempotente, QUERY solo consulta; request nuevo no repite pieza. Caída exige barrera correcta FREE/BLOCKED/FREE; WRONG_ROUTE, contradicciones, timeout, heartbeat/corte→FAULT.

Drivers GPIO/debounce20ms, gate/lid/service/reset/power/index/fall, HX711 y VL53L0X reales; XSHUT secuencial0x30–33 cada boot, mediana/histéresis/UNKNOWN. Error no es empty/cero. [Compilar](../../docs/DEV_SETUP_WINDOWS.md), [calibrar/bring-up](../../docs/BRINGUP.md), [dependencia MIT fijada](vendor/README.md). Firmware compilado no acredita circuito ni sensores.

El corte de potencia de tapa, servicio y paro es independiente del software. El contrato de protocolo completo está en `../docs/architecture/protocol.md` y el pinout en `../hardware/pinout/pico.csv`. Los adaptadores de entradas deben convertir polaridad eléctrica y estados inválidos explícitamente; las guardas no son un circuito de protección.
