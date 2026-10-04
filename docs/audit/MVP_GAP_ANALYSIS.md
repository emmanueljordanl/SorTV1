# Auditoría inicial para integración física SorTV1

Fecha: 2026-10-03. Base auditada: develop `10b30af`, main/tag v0.1.0 `b94fbd0`, árboles de contenido idénticos. Se leyeron los 339 archivos versionados, separando assets binarios, librería Three.js y copias generadas de `dist/`. Solo existe `Plan_Construccion_SorTV1_6_Semanas.docx`; no se encontró la variante `(2)`. El plan v1.0 es la fuente de requisitos vigente.

Verificación inicial: 27 pruebas Python PASS, 24 pruebas del gemelo PASS, build offline PASS, `verify_repository.py` PASS. Los contratos C++ existentes fueron aprobados por CI en la base; no hay compilador C++ ni Pico SDK instalado en PATH local al iniciar la auditoría. Se preparará el entorno y se repetirá compilación nativa y cruzada. Ningún resultado anterior acredita hardware.

La GPU detectada es NVIDIA GeForce RTX 4070 Laptop, 8188 MiB y driver 610.88. No hay dependencias ML instaladas en el Python 3.14 detectado. Esto acredita inventario del equipo, no rendimiento de entrenamiento.

| Requisito | Fuente | Implementado | Parcial | Ausente | Riesgo | Archivo responsable | Prueba | Acción |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CRC/framing acotado | Plan 12; solicitud 3A | Sí | — | — | Compatibilidad entre lenguajes | app/transport, firmware/protocol | CRC golden y fragmentación existentes | Conservar y ampliar schema |
| Errores ligados a operación | Solicitud 3A | — | NACK/FAULT sin correlación | Correlación completa | Mensaje tardío bloquea otro ciclo | app/controller | Nuevas pruebas de retraso | Correlacionar boot/cycle/request |
| Idempotencia física | Plan 10–12 | — | Doble Python | Historial en Pico real | Doble descarga | firmware/src/state_machine.cpp | Host y HIL | Implementar operación por ciclo e historial acotado |
| Cierre REVIEW/abortado | Solicitud 3B | — | Bloqueo conservador | REMOVED/RECONCILED | Bloqueo permanente o falsa conciliación | app/evidence, controller | Recuperación y registro de operador | Cerrar sin convertir a DONE |
| Journal persistente | Plan 18 | fsync y conteos | Sin rotación/exportación/espacio | Métricas y recuperación operativa | Pérdida de trazabilidad | app/evidence | ENOSPC y truncado | Ampliar sin debilitar persistencia |
| Fuente hardware única | Solicitud 3C | — | CSV Pi y JSON gemelo | Fuentes canónicas/generador | Divergencia de BOM/pinout | hardware/source; scripts | Comparación sin pérdida | Migrar conservando campos digitales |
| Distribución como artifact | Solicitud 3D | — | dist y ZIP versionados | Build/release automático | Copias manuales inconsistentes | .github/workflows | Regeneración offline | Archivar ZIP original, sacar dist del índice |
| TrashIA real | Solicitud 4–8 | — | URL conocida | Metadata/clases/version/licencia verificadas | Mapeo inseguro o licencia desconocida | scripts/fetch_trashia.py | SDK y ZIP local | API 401; Universe 403: solicitar acceso y no inventar metadata |
| Manifest de datos | Plan 15 | Validador por objeto | Solo esquema de 9 columnas | Hashes/archivos/provenance | Fuga de evaluación | training/datasets | Casos object/source/hash | Ampliar compatible |
| Captura local dataset | Solicitud 7 | — | Interfaz Frame | Herramienta Camera Module 3 | Datos fuera de dominio | app/tools/capture_dataset | Mock camera y manifest | Captura con etiquetas y provenance |
| Entrenamiento MobileNet | Plan 16 | — | baseline JSON | PyTorch real | CNN nunca entrenada | training/train | Smoke técnico sin métricas de producto | Dos fases y registro reproducible |
| Evaluación y umbrales | Plan 16–17 | — | Política de confianza | Métricas y búsqueda VALIDATION | Ajuste usando TEST | training/evaluate | Métricas conocidas y congelación | Implementar separación local/externo |
| Exportación ONNX | Plan 16 | — | Especificación | Export y equivalencia | Modelo corrupto/desalineado | training/export | 50 imágenes cuando existan | Paquete con hashes y tolerancia |
| Benchmark | Plan 17 | — | Targets | Herramienta de medición | Confundir metas con resultados | training/benchmark | Smoke y formato | Medir solo equipos disponibles |
| Picamera2 | Plan 14 | — | Protocol Capture | Adaptador real | Buffers viejos/canales RGB | app/capture | Mock request/metadata | Leer timestamp de sensor y controles |
| Calidad visual | Plan 14 | Edad/ciclo | Señales booleanas inyectadas | Imagen/foco/exposición/presencia reales | Clasificar fondo | app/quality | Imágenes técnicas sintéticas | Métricas calibrables y rechazo de repetición |
| ONNX Runtime | Plan 13–16 | — | Protocol Inference | Runtime validado | Modelo/labels/preproceso distintos | app/inference | NaN/hash/shape y modelo de smoke | Validar paquete antes de operación |
| pySerial USB CDC | Plan 12 | — | Codec | Driver/reconexión/heartbeat | USB perdido sin parada | app/transport | Serial fake y HIL | Comunicación real sin repetir request |
| Orquestador físico | Solicitud 17 | Un ciclo e intención | Sin pipeline real | Lazo de eventos/timeout | Bloqueo del heartbeat | app/controller | Integración de adaptadores | Worker de inspección y transporte independiente |
| UI local | Plan 18 | — | UI del gemelo | Consulta del hardware real | Autoridad indebida de UI | app/operator_ui | Rutas de solo consulta | Mostrar snapshot/export sin motores/rearme |
| Deployment Pi | Plan 13 | — | Instrucciones conceptuales | Scripts/systemd | Root/arranque con permiso antiguo | deploy; scripts/pi | Validación shell y docs | Servicio no root y sesión desarmada |
| Firmware Pico SDK | Plan 10–11 | — | Headers/guardas | Programa, drivers y UF2 | No existe control físico compilable | firmware | Compile cross y host | Estado físico cooperativo y watchdog |
| HX711/ToF | Plan 07,18 | — | Gemelo virtual | Drivers reales/calibración | UNKNOWN interpretado vacío | firmware/src/sensors.cpp | Host y HIL | Lectura no bloqueante y parámetros TBC |
| Corte DC/interlocks | Plan 06 | — | Riesgos/documentación | Circuito elegido y validación física | Acceso a mecanismo con energía | hardware/electrical | P02/P03 PENDING | Especificar circuito y contactos sin inventar ratings |
| Rotor/caída/cierre | Plan 10–11 | — | Simulación | Señales y secuencia físicas | DONE falso/atasco | firmware state machine | Host escenarios y P10/P11 | Índice estable, FREE/BLOCKED/FREE, vacío y CLOSED |
| BOM/arnés/CAD | Plan 04–09 | Pinout de referencia | Presupuesto/README | BOM compra, conexiones y checklist | Compra/cableado sin cerrar | hardware | Integridad/trazabilidad | Todo dato eléctrico no confirmado TBC |
| HIL y aceptación | Plan 23 | Matriz P01–P16 | Suite software | Herramientas/recorder HIL | PASS físico ficticio | tests/hil; tools | Mock y recorder | Conservar PENDING hasta evidencia PHYSICAL |
| Entorno reproducible/CI | Solicitud 38–40 | CI Python/JS/headers | Sin dependencias runtime/ML | Pico build y ML smoke | Código no ejecutable | requirements, workflow | CI sin hardware | Fijar versiones y producir UF2 artifact |

Orden de implementación: contratos/evidencia → fuentes de hardware/datos → ML → captura/inferencia/USB/orquestación → firmware → deployment/HIL/documentación → auditoría final. Este archivo conserva el estado previo; el estado final se registrará en FINAL_MVP_AUDIT y MVP_STATUS.

Bloqueos externos iniciales: hardware no conectado; ROI, peso, llenado, servo, velocidad, polaridades y ratings requieren medición; TrashIA requiere API key o exportación con metadata. No se sustituirán con resultados inventados.
