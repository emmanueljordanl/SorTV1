# Plan de construcción por seis semanas

Los hitos son relativos al inicio efectivo. El documento fuente propone del 15 de septiembre al 26 de octubre de 2026 y tres días de contingencia; el repositorio no acredita avances físicos ni modifica esas fechas.

| Semana | Entrega | Evidencia requerida |
| --- | --- | --- |
| 1 | Contratos, maqueta, presupuesto y banco protegido | Captura real, 50 pasos manuales, fuentes y entradas verificadas |
| 2 | Mecánica funcional y baseline | 50 descargas y 20 ciclos diagnósticos; modelo exportado |
| 3 | Integración de IA local | 50 ciclos con IA real y motivos de rechazo |
| 4 | Recuperación y congelación | 100 ciclos, fallos inyectados, versiones identificadas |
| 5 | Aceptación independiente | 200 ciclos autónomos y sesión térmica de 60 minutos |
| 6 | Corrección y entrega | Repetir gates afectados; respaldo, manual y demostración |

Prioridad de integración: cerrar hardware de protección y dimensiones → firmware con salidas deshabilitadas → captura real y checks visuales → entrenamiento/exportación → transporte USB → ciclo físico → aceptación. Cada cambio de cámara, fondo, mecanismo o modelo repite las pruebas afectadas. Después del día 28 se corrigen defectos; funciones secundarias pasan al backlog.

Pendientes de esta base: adaptadores de cámara y visuales, preprocesamiento validado, runtime ONNX, entrenamiento y evaluación del modelo, drivers USB/GPIO, máquina completa con temporizadores, panel local de consulta, rotación/exportación de registros y herramientas de conciliación manual. No existe un servicio systemd ni una imagen reproducible de Pi hasta congelar el entorno real.
