# ADR: implementación física, entrega experimental

Decisión aceptada en candidato0.2.0-mvp-rc1. Mantener interfaces/simuladores/contratos antiguos y añadir adaptadores reales desacoplados. Pi solicita destino; autoridad física exclusivamente Pico. CRC/identidades comunes; request1 único por ciclo, historial8, no replay ni rearme remoto. NACK BOOT_MISMATCH referencia el boot de la operación rechazada, server_boot informa emisor, para no confundir error de otro arranque con ciclo actual.

Modelo requiere hashes, contrato numérico/equivalencia≥50 y validación LOCAL. Datasource externo auxiliar solamente train_external/challenge. TEST freeze antes de escribir/evaluar. Umbrales por imagen no demuestran consenso temporal/éxito físico. Sin modelo/admisión/calibración: bloqueo/REVIEW. RECHAZO es decisión separada de etiquetas.

Canon hardware conserva lossless JSON de fuentes del gemelo en CSV; campos de compras/adiciones y cableado propuesto separados, sin sustituir mediciones. Escena/CAD ilustrativos tienen semántica propia y no se regeneran como CAD aprobado. ZIP original movido a archivo histórico; builds nuevos artifacts con commit/SHA/licencias.

PicoSDK2.3.1 y Pololu VL53L0X MIT fijados; no radio ni ROS/nube. SDK oficial picotool en LinuxCI; Windows conversor BIN→UF2 verificado por formato/payload, sin flashear. Compilar drivers no acredita hardware. GPIO baseline no cambia; no ECN de GPIO. ECN de terminales/modelos/rating pendiente de seleccionar piezas reales.

CHECK_HOME seguro confirma índice conocido con mecanismo vacío; no buscar a ciegas. Si no se conoce posición, reposicionamiento manual con energía aislada antes del rearme. Bancos de motor/servo no puentean sensores: requieren completar calibraciones/guardas. P01–P16 son aceptación PHYSICAL, siguen PENDING. V1.0 bloqueado por aceptación pendiente; documentación y auditoría expresan límites sin resultados ficticios.
