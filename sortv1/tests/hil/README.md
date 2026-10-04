# HIL físico

Desde `sortv1`: `python -m app.tools.hil_protocol`, `hil_sensors` y `hil_cycle`. Sin actuadores por defecto. SOLO `hil_cycle --enable-actuators --dest 0` puede pedir un destino DIAGNOSTIC, tras calibración/rearme físico y permisos de sensores. No hay control STEP/PWM ni rearme remoto. Las observaciones se registran PHYSICAL, nunca se transforman automáticamente en PASS P01-P16.
