# Flujo Git para las seis semanas

Se adopta un flujo de dos ramas permanentes y tareas cortas. `develop` permite integrar percepción, firmware y mecánica durante el prototipo, manteniendo una base reproducible en `main`. Se evita un Git Flow completo con ramas permanentes por módulo: para dos personas y seis semanas añade sincronización sin ayudar a cerrar el recorrido físico.

La mecánica no se fusiona solo por existir CAD: el PR registra dimensiones, versión de hardware y pruebas afectadas. Un cambio de pinout, clase, preprocesamiento o sensor requiere revisar el contrato compartido.

| Rama de tarea sugerida | Dependencia principal | Criterio para integrar |
| --- | --- | --- |
| feature/protocol-v1 | Contratos boot/ciclo y destinos | CRC, parser, identidad e idempotencia comprobados |
| feature/pico-state-machine | Drivers y señales reales | Arranque desarmado, guardas, tiempos y recuperación verificados |
| feature/camera-pipeline | Cámara y recinto final | Frames nuevos, RGB, ROI y calidad medidos |
| feature/safety-interlocks | Circuito de corte y firmware | Tapa, servicio y paro ensayados; sin rearme automático |
| feature/mechanical-indexing | Recorrido por gravedad y sensores | Índice real confirmado; rotor vacío; descarga observable |
| feature/pi-inference | Dataset, exportación y captura | Equivalencia ONNX, labels y benchmark en Pi |
| test/fault-injection | Ciclo integrado | Casos de fallos y evidencias identificadas |

Estas ramas se crean desde `develop` cuando comienza su tarea; no se crean siete copias vacías de la misma base. Se suben al remoto al primer commit y se eliminan después de integrarlas. La lista es una guía de trabajo y no acredita funcionalidades implementadas.

Semanas 1–2: contratos, banco, captura y baseline. Semanas 3–4: integración, recuperación y congelación. Semanas 5–6: aceptación y correcciones. Registrar tags v0.x de bases reproducibles, sin presentarlos como aceptación física. `release/v1.0` solo si hace falta aislar la congelación del día 28.

`main` y `develop` deben exigir PR, comprobaciones CI, conversaciones resueltas y bloquear borrado/force push. Inicialmente pueden funcionar con cero aprobaciones obligatorias si hay un solo colaborador disponible; al incorporar al segundo integrante, exigir una aprobación. Los cambios de entrega entran mediante merge commit; las tareas pueden usar squash.

Referencias: [GitHub flow](https://docs.github.com/en/get-started/using-github/github-flow) describe ramas de tarea y PR; [protección de ramas](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches) permite exigir comprobaciones y revisión. La rama de integración `develop` es una decisión específica para la construcción SorTV1.
