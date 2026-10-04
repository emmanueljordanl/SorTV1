# Puesta en marcha y recuperación

1. Sin fuentes conectadas, comprobar polaridad, continuidad, conexiones y resguardos. Medir convertidores antes de conectar cargas.
2. Energizar solo Pi, Pico y sensores; verificar arranque sin movimiento y señales reales.
3. Comprobar que tapa, servicio y paro interrumpen físicamente potencia de actuadores. Verificar feedback aislado de GPIO28.
4. Con recorrido vacío y resguardos, calibrar índices, compuerta, corriente y velocidades. Homing solo después de inspección manual.
5. Ejecutar descargas diagnósticas y registrarlas aparte. Activar IA real después de validar modelo y preprocesamiento.
6. Registrar P01–P16 con identidad del hardware, versión, estímulo, resultado esperado/observado y evidencia. Todo comienza PENDING.

Un fallo enclavado requiere aislar potencia, revisar bandeja/guía, retirar residuos, restaurar resguardos y pulsar rearme. Soltar paro o cerrar una puerta no reanuda el ciclo. Ante intención incompleta en el journal: conservar archivos, inspeccionar el depósito real y documentar conciliación antes de permitir nuevas operaciones. Esta base bloquea la operación y no ofrece una herramienta automática de conciliación.

Antes de cada sesión: cuatro recipientes presentes, guía vacía, bandeja limpia, cámara firme, luz uniforme, tara estable, almacenamiento disponible y ciclo por destino. Después de transporte, revisar alineación. No declarar aceptación física usando resultados del simulador.
