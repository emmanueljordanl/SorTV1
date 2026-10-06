# ADR: implementación física, entrega experimental

Decisión aceptada en candidato0.2.0-mvp-rc1. Mantener interfaces/simuladores/contratos antiguos y añadir adaptadores reales desacoplados. Pi solicita destino; autoridad física exclusivamente Pico. CRC/identidades comunes; request1 único por ciclo, historial8, no replay ni rearme remoto. NACK BOOT_MISMATCH referencia el boot de la operación rechazada, server_boot informa emisor, para no confundir error de otro arranque con ciclo actual.

Modelo requiere hashes, contrato numérico/equivalencia≥50 y validación LOCAL. Datasource externo auxiliar solamente train_external/challenge. TEST freeze antes de escribir/evaluar. Umbrales por imagen no demuestran consenso temporal/éxito físico. Sin modelo/admisión/calibración: bloqueo/REVIEW. RECHAZO es decisión separada de etiquetas.

Canon hardware conserva lossless JSON de fuentes del gemelo en CSV; campos de compras/adiciones y cableado propuesto separados, sin sustituir mediciones. Escena/CAD ilustrativos tienen semántica propia y no se regeneran como CAD aprobado. ZIP original movido a archivo histórico; builds nuevos artifacts con commit/SHA/licencias.

PicoSDK2.3.1 y Pololu VL53L0X MIT fijados; no radio ni ROS/nube. SDK oficial picotool en LinuxCI; Windows conversor BIN→UF2 verificado por formato/payload, sin flashear. Compilar drivers no acredita hardware. GPIO baseline no cambia; no ECN de GPIO. ECN de terminales/modelos/rating pendiente de seleccionar piezas reales.

CHECK_HOME seguro confirma índice conocido con mecanismo vacío; no buscar a ciegas. Si no se conoce posición, reposicionamiento manual con energía aislada antes del rearme. Bancos de motor/servo no puentean sensores: requieren completar calibraciones/guardas. P01–P16 son aceptación PHYSICAL, siguen PENDING. V1.0 bloqueado por aceptación pendiente; documentación y auditoría expresan límites sin resultados ficticios.

## Desviación explícita del homing inicial del plan

El plan inicial proponía buscar lentamente el índice0. El MVP no implementa ese movimiento: CHECK_HOME solo verifica exactamente un índice conocido estable con mecanismo vacío y guardas válidas. Sin índice no se acepta el rearme; si desaparece durante CHECK_HOME, outputs permanecen OFF y el timeout termina en FAULT. Dos índices son contradicción y FAULT.

Razón: evitar movimiento con posición y trayectoria desconocidas, carga atrapada, sensor/cable roto o sentido de giro aún no validado. Procedimiento manual: aislar potencia, vaciar trayecto, reposicionar rotor a un índice único, restaurar guardas, ACTUATOR_ENABLE, PHYSICAL_RESET y CHECK_HOME. Reconsiderar homing automático solo en una versión futura con sensores/guardas/calibración medidos, ruta de búsqueda y límites de tiempo/movimiento definidos, análisis de fallos, pruebas físicas y revisión explícita de este ADR.

## Carga normal, interfaces eléctricas y tiempos

READY puede esperar power=false con outputs OFF después de abrir/cerrar tapa; no restaura potencia ni comienza WAIT_STABLE sin todas las guardas. El operador pulsa ACTUATOR_ENABLE separado del PHYSICAL_RESET del Pico. Las pérdidas de potencia en POSITIONING/DISPENSING/VERIFY_CLOSE conservan FAULT; link/heartbeat mantienen los bloqueos existentes. Recuperaciones FAULT/REVIEW/E-STOP/SERVICE/reinicio requieren servicio parado, aislamiento/inspección y rearme; la carga normal desde READY no.

Nueve contactos secos usan pull-up externo3V3 y contacto aGND. 10kΩ1%1/4W es CONFIGURED_BASELINE, no medición; nEN tiene pull físico del lado driver hacia3V3 persistente al retirar Pico. Salidas HX711/barreras/feedback requieren interfaz específica, no pulls de contacto aplicados indiscriminadamente. Modelos/terminales son TBC_MODEL; polaridad/debounce son TBC_CALIBRATE y validación eléctrica PENDING_PHYSICAL_VALIDATION. No cambiar calibration::verified=false.

TARGET inspection p95≤1000 ms se evalúa con inspection_ms; HARD PI DEADLINE inicial1750 ms con máximo1750 preserva250 ms frente al timeout Pico2000 ms. Es CONFIGURED_BASELINE y PENDING_PHYSICAL_BENCHMARK, no latencia físicamente validada. No cambia ML, admisión humana ni P01–P16.
