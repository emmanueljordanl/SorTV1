# Simulación SorTV1

## 27 Máquina de estados

La máquina tiene un único ciclo activo. DONE es un evento de resultado, no un estado duradero adicional. La UI lee la transición y anima la planta; no elige una transición libre para dibujar éxito.

Todas las maniobras exigen resguardos y energía válidos. Antes de girar se requiere CLOSED y guía considerada libre. Antes de abrir, un índice exclusivo confirmado. Antes de DONE, OPEN observado, secuencia de haz correcta, bandeja vacía y CLOSED sin OPEN. Si se rompe un invariante, se corta permiso y se enclava el motivo.

Heartbeat cada200 ms; pérdida≈1000 ms. WAIT_DECISION≈2 s; POSITIONING≈3 s; OPEN≈1 s; caída≈2 s después de OPEN; CLOSE≈1 s. Plazo global de ciclo≈10 s para evitar acumulaciones. Las metas p95 son independientes: no se suman p95 parciales ni se ensanchan timeouts para ocultar un atasco.

READY permite abrir tapa como carga normal y no ordena movimiento. Una apertura durante inspección cancela esa inspección. Una apertura durante CHECK_HOME/POSITIONING/DISPENSING/VERIFY_CLOSE lleva a FAULT. Servicio abierto invalida operación. La recuperación implica retirar el objeto con potencia aislada; cerrar puertas nunca salta directamente a la maniobra suspendida.

El código verifica reed vigente durante dispensado y cierre. No supone que un índice observado una vez siga siendo correcto después de un desplazamiento no esperado. Las barreras se verifican por flancos y el contador solo incrementa tras el conjunto de confirmaciones.
| Estado | Evento y acción | Guarda de salida | Plazo / fallo |
| --- | --- | --- | --- |
| BOOT_SAFE | Reinicio; nEN HIGH; PWM inactivo; nuevo boot; sin rearme | rearme físico y recorrido vacío → CHECK_HOME | reposo ms; FAULT/REVIEW según causa |
| CHECK_HOME | Rearme válido; Girar vacío lentamente a ROT0 | CLOSED, resguardos, energía, ROT0 exclusivo 100 ms → READY | 3000 ms; FAULT/REVIEW según causa |
| READY | Homing o DONE; Quieto; permitir carga, tapa abierta corta potencia | Objeto único, tapa cerrada → WAIT_STABLE | reposo ms; FAULT/REVIEW según causa |
| WAIT_STABLE | Tapa cerrada; Leer masa y estabilidad | Presencia estable; ≤200 g; recorrido libre → WAIT_DECISION | 2000 ms; FAULT/REVIEW según causa |
| WAIT_DECISION | INSPECT; Pipeline Pi; un ciclo activo | SORT válido; permisos físicos y destino disponible → POSITIONING | 2000 ms; FAULT/REVIEW según causa |
| POSITIONING | SORT aceptado; STEP/DIR; guía vacía; CLOSED | Reed destino exclusivo y estable 100 ms → DISPENSING | 3000 ms; FAULT/REVIEW según causa |
| DISPENSING | Índice confirmado; Abrir una sola vez; observar OPEN y haz | OPEN confirmado; ruta y vacío válidos → VERIFY_CLOSE | 3000 ms; FAULT/REVIEW según causa |
| VERIFY_CLOSE | Caída confirmada; Cerrar; observar CLOSED sin OPEN | Haz correcto completo y bandeja vacía → READY + DONE único | 1000 ms; FAULT/REVIEW según causa |
| FAULT | Fallo físico; Deshabilitar; enclavar; evidencia | Inspección, retirar objeto, cerrar, rearme → CHECK_HOME | reposo ms; FAULT/REVIEW según causa |
| REVIEW | Calidad/capacidad/peso inválido; Sin descarga; revisión explícita | Retiro y rearme físico; nuevo ciclo → CHECK_HOME | reposo ms; FAULT/REVIEW según causa |
## 28 Ciclo completo

El storyboard de la lata contiene 39 frames conceptuales. No son 39 fotografías medidas. La aplicación mantiene en cada evento sensores, estado Pico, fase Pi, potencia, actuadores, mensajes y evidencia. La exportación JSONL permite inspeccionar esos canales simultáneamente. El archivo normal-cycle.json conserva una ejecución digital y storyboard.json el orden narrado.

El movimiento continuo se calcula entre eventos; el objeto permanece retenido hasta liberación de la hoja y recorre guía y boca sin teletransportarse al destino. El paso por el haz es un evento independiente del ángulo. Si el objeto cae sin haz, el ciclo queda FAULT aunque el dibujo lo muestre dentro del bin.

Los valores de tiempo de una ejecución del modelo son SIMULADOS. La secuencia no prueba velocidad de Pi, servo o firmware. La captura y las probabilidades son sintéticas; la política sí se evalúa. Después de DONE, la persistencia y el contador son acciones separadas y deduplicadas.
| Frame | Vista física y causa | Pico / Pi / señales y evidencia |
| --- | --- | --- |
| 00 | READY | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. READY y lógica supervisando. |
| 01 | Verde nominal | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. READY y lógica supervisando. |
| 02 | Abrir tapa | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Actuadores OFF; lógica ON. |
| 03 | Actuadores OFF | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Actuadores OFF; lógica ON. |
| 04 | Depositar lata | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Actuadores OFF; lógica ON. |
| 05 | Masa presente | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Actuadores OFF; lógica ON. |
| 06 | Cerrar tapa | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Retención CLOSED; captura y decisión. |
| 07 | Estabilidad | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Retención CLOSED; captura y decisión. |
| 08 | Nuevo cycle_id | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Retención CLOSED; captura y decisión. |
| 09 | INSPECT | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Retención CLOSED; captura y decisión. |
| 10 | Luz estable | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Retención CLOSED; captura y decisión. |
| 11 | Frame A | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Retención CLOSED; captura y decisión. |
| 12 | Frame B | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Retención CLOSED; captura y decisión. |
| 13 | Frame C | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Retención CLOSED; captura y decisión. |
| 14 | Quality PASS | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Retención CLOSED; captura y decisión. |
| 15 | Inferencia A B C | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Retención CLOSED; captura y decisión. |
| 16 | METAL_LATAS | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Retención CLOSED; captura y decisión. |
| 17 | Consenso ACCEPT | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Retención CLOSED; captura y decisión. |
| 18 | SORT dest2 | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Retención CLOSED; captura y decisión. |
| 19 | Guardas Pico | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Retención CLOSED; captura y decisión. |
| 20 | nEN activo | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. CLOSED; guía vacía; nEN activo; reed real. |
| 21 | Giro NEMA | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. CLOSED; guía vacía; nEN activo; reed real. |
| 22 | Guía vacía gira | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. CLOSED; guía vacía; nEN activo; reed real. |
| 23 | ROT2 detectado | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. CLOSED; guía vacía; nEN activo; reed real. |
| 24 | ROT2 estable100ms | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. CLOSED; guía vacía; nEN activo; reed real. |
| 25 | Motor detenido | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. CLOSED; guía vacía; nEN activo; reed real. |
| 26 | Servo apertura | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Índice confirmado; OPEN; caída y haz correctos. |
| 27 | OPEN confirmado | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Índice confirmado; OPEN; caída y haz correctos. |
| 28 | Liberación lata | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Índice confirmado; OPEN; caída y haz correctos. |
| 29 | Paso por guía | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Índice confirmado; OPEN; caída y haz correctos. |
| 30 | Haz BIN2 FREE-BLOCKED-FREE | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Índice confirmado; OPEN; caída y haz correctos. |
| 31 | Bandeja vacía | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. Índice confirmado; OPEN; caída y haz correctos. |
| 32 | Servo cierre | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. CLOSED y resultado consolidado sin duplicar. |
| 33 | CLOSED confirmado | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. CLOSED y resultado consolidado sin duplicar. |
| 34 | DONE | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. CLOSED y resultado consolidado sin duplicar. |
| 35 | JSONL persistido | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. CLOSED y resultado consolidado sin duplicar. |
| 36 | Contador BIN2 +1 | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. CLOSED y resultado consolidado sin duplicar. |
| 37 | ToF actualizado | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. CLOSED y resultado consolidado sin duplicar. |
| 38 | READY | Ver registro por evento: physical, sensors, pico, pi, power, protocol, actuators, evidence. CLOSED y resultado consolidado sin duplicar. |
## 29 Panel operador y navegación

El estado principal se traduce a LISTO, PROCESANDO, REVISIÓN o FALLO, con BOOT_SAFE sin armar. El panel muestra tapa, servicio, energía, enlace Pico, boot/cycle, clase, destino solicitado/confirmado, resultado, latencia virtual, niveles, almacenamiento, versión de software/firmware y estado del modelo. El hash de modelo es null cuando no hay modelo entrenado; no se fabrica un hash de pesos inexistentes.

La UI productiva es de consulta/exportación. Los botones del gemelo «rearme», «depositar», «abrir tapa» y «E-STOP» son estímulos de laboratorio virtual. No abren un puerto físico ni envían PWM al prototipo. No hay botón abierto «mover motor» ni «servo+10°».

Navegación: PRODUCTO, INTERIOR, EXPLODED, MECÁNICA, ELECTRÓNICA, CABLEADO, SEÑALES, SOFTWARE, ESTADOS, SIMULACIÓN, FALLOS, ENSAMBLAJE, MEDICIONES, BOM, MANTENIMIENTO, COMMISSIONING, TEST CENTER y EVIDENCIA. El selector V01–V20 cambia cámara y representación del mismo modelo.

Play/Pause controlan reloj virtual; STEP avanza hasta el siguiente evento observable, incluidos subestados de percepción. La velocidad cambia el ritmo de reproducción, no los timeouts expresados en tiempo de simulación. El monitor causal explica causa, señal, decisión, actuación, confirmación y evidencia. Un evento histórico abre su snapshot registrado; no se hace pasar por el estado actual de sensores.

En montaje, el panel lateral puede ampliarse; las etapas muestran qué necesita medirse, fijarse, cablearse y verificarse. En mediciones, seleccionar dos superficies calcula distancia virtual; introducir una cifra medida y congelarla son operaciones diferentes. Los checks de commissioning siguen siendo SIMULADOS.
## 30 Logging y observabilidad

SW-07 registra por separado inspección, predicción, decisión, SORT, ACK, posición, OPEN, caída, CLOSE y DONE. Cada evento conserva boot, cycle, request cuando aplica, timestamp local, versiones y fuente. Los datos de imágenes incluyen frame_id y edad al inicio de inferencia.

Antes de enviar SORT, la Pi real debe persistir intención con flush/fsync y comprobar espacio. Después de DONE se consolida el resultado una sola vez por boot:cycle. En el gemelo, journal y conteos reproducen esa semántica lógica; la durabilidad física de una microSD y la pérdida real de energía no se simulan como garantía.

Un reinicio tras caída y antes de guardar deja una intención pendiente. Se registra PENDING_PHYSICAL_RECONCILIATION y no se emite otro SORT para «completar». El operador revisa pieza, bin y registros. La conciliación debe añadir un evento con autor y evidencia, sin reescribir silenciosamente un fallo como DONE.

Ejemplo de esquema: cycle_id="sim-b17:42", predicted_class="METAL_LATAS", score=0.91, decision="ACCEPT", requested_bin=2, confirmed_bin=2, physical_result="DONE", source="SIMULATION", result_kind="SIMULATED", model_sha256=null, model_status="SIMULATED_NO_MODEL", cycle_ms=<reloj virtual>, error_code=null. La cifra0.91 es una probabilidad sintética; los tiempos exportados son del reloj virtual.

JSONL ofrece eventos completos; JSON agrupa eventos y contadores; CSV conserva tipo, origen, tiempo, identidad, estado y detalle. Los archivos físicos futuros deberán generarse por software del equipo con source=PHYSICAL. Nunca rellenar resultados físicos a partir de una exportación digital.
## 31 Simulaciones de fallo

F01–F30 se inyectan como cambios de planta, sensores o enlace. El controlador reacciona mediante sus guardas y timeouts; no se limita a imprimir un mensaje. E-STOP/tapa/puerta modifican energía y señales; fallos mecánicos impiden confirmación; los fallos de percepción evitan SORT; duplicados prueban idempotencia.

Después de fallo no se permite una nueva descarga ni un homing con recorrido incierto. La lógica puede permanecer energizada para registrar. El modelo corta autorización y congela actuadores de forma ideal; el equipo real conserva energía cinética y posibilidad de retroceso, por lo que el volumen de parada necesita ensayo.

F27 y F29 no tienen sensor adicional de voltaje/corriente: el estado se descubre por falta de OPEN/CLOSED. F17 demuestra que masa cero y dibujo del objeto dentro de un bin no sustituyen al haz. F30 separa caída física probable de persistencia confirmada. F08 debe terminar normalmente, con una única apertura y contador.

La matriz siguiente especifica estímulo, observación, estado, evidencia y recuperación. Para todos los casos distintos de F08: prohibir nuevas maniobras hasta el procedimiento correspondiente; conservar Pi/Pico para diagnóstico cuando su alimentación siga disponible. Ningún resultado de esta matriz se etiqueta MEDIDO.
| Fallo y fase | Observación y detector | Estado / energía | Recuperación y evidencia |
| --- | --- | --- | --- |
| F01 E-STOP durante giro / POSITIONING | Corte NC inmediato; GPIO28 cae; E-STOP visible; FW-01 guardas/temporizadores | FAULT; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Liberar, inspeccionar guía, retirar residuo y rearme; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F02 Tapa abierta durante movimiento / POSITIONING | GPIO12 abre y GPIO28 cae; FW-01 guardas/temporizadores | FAULT; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Cerrar tras inspección; rearme; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F03 Puerta servicio abierta / POSITIONING | GPIO27 abre y GPIO28 cae; FW-01 guardas/temporizadores | FAULT; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Reponer bins, cerrar y rearme; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F04 USB desconectado / POSITIONING | Heartbeat ausente 1000 ms; USB desconectado; FW-01 guardas/temporizadores | FAULT; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Reconectar, sesión nueva y rearme; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F05 Pi congelada / POSITIONING | Heartbeat vencido aunque cable presente; FW-01 guardas/temporizadores | FAULT; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Reiniciar servicio; reconciliar ciclo y rearme; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F06 Pico reiniciado / POSITIONING | Nuevo boot_id; nEN seguro; permiso anterior perdido; FW-01 guardas/temporizadores | BOOT_SAFE; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Retiro manual, homing con nuevo boot; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F07 CRC inválido / WAIT_DECISION | Parser CRC rechaza; timeout decisión; FW-01 y SW-02/04/05/07 | REVIEW; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Comprobar enlace; retirar y repetir con ciclo nuevo; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F08 SORT duplicado / WAIT_DECISION | ACK duplicado sin nueva operación; FW-01 y SW-02/04/05/07 | READY; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Ninguna si DONE único; no es fallo físico; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F09 destination=4 / WAIT_DECISION | NACK DEST; timeout sin movimiento; FW-01 y SW-02/04/05/07 | REVIEW; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Corregir contrato y rearme; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F10 Reed destino no aparece / POSITIONING | Sin índice confirmado al vencer 3 s; FW-01 guardas/temporizadores | FAULT; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Medir imán/cable/alineación; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F11 Dos reed activos / POSITIONING | Más de un índice activo; FW-01 guardas/temporizadores | FAULT; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Inspeccionar corona e imán único; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F12 Compuerta no abre / DISPENSING | OPEN ausente en 1 s; FW-01 guardas/temporizadores | FAULT; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Aislar, revisar enlace y switch; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F13 Compuerta no cierra / VERIFY_CLOSE | CLOSED ausente en 1 s; FW-01 guardas/temporizadores | FAULT; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Aislar, revisar obstáculo y switch; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F14 Objeto atascado / DISPENSING | No caída; masa o recorrido incierto al timeout; FW-01 guardas/temporizadores | FAULT; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Retirar manualmente con energía aislada; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F15 Caída a depósito incorrecto / DISPENSING | Barrera otro bin activa; no DONE; FW-01 guardas/temporizadores | FAULT; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Conciliar destino manual y calibrar guía; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F16 Barrera queda bloqueada / DISPENSING | FREE-BLOCKED sin retorno FREE; FW-01 guardas/temporizadores | FAULT; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Limpiar y realinear, retirar objeto; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F17 Papel no activa barrera / DISPENSING | Bandeja vacía sin secuencia de haz; FW-01 guardas/temporizadores | FAULT; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | No inferir éxito; revisar cobertura óptica; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F18 Celda inestable / WAIT_STABLE | Dispersión de masa fuera de ventana; FW-01 y SW-02/04/05/07 | REVIEW; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Eliminar vibración/rutas paralelas y tarar; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F19 Sobrepeso / WAIT_STABLE | Masa >200 g; FW-01 y SW-02/04/05/07 | REVIEW; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Retirar; inspeccionar topes/celda; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F20 ToF inválido / WAIT_DECISION | Destino UNKNOWN; FW-01 y SW-02/04/05/07 | REVIEW; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Limpiar óptica y recalibrar; no inferir vacío; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F21 Depósito lleno / WAIT_DECISION | Nivel persistente FULL; FW-01 y SW-02/04/05/07 | REVIEW; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Aislar y vaciar; presencia manual; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F22 Cámara tapada / WAIT_DECISION | Calidad exposición/presencia falla; FW-01 y SW-02/04/05/07 | REVIEW; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Limpiar, verificar imagen antes rearme; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F23 Imagen desenfocada / WAIT_DECISION | Calidad foco falla; FW-01 y SW-02/04/05/07 | REVIEW; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Fijar cámara y enfocar; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F24 Frame viejo / WAIT_DECISION | Edad >300 ms; FW-01 y SW-02/04/05/07 | REVIEW; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Vaciar buffers; verificar relojes locales; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F25 Modelo ausente / WAIT_DECISION | Carga/verificación paquete falla; FW-01 y SW-02/04/05/07 | REVIEW; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Restaurar paquete y hash; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F26 Almacenamiento lleno / WAIT_DECISION | No se puede persistir intención; FW-01 y SW-02/04/05/07 | REVIEW; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Exportar/rotar evidencia antes nuevo ciclo; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F27 Caída alimentación servo / DISPENSING | Sin OPEN/CLOSED a tiempo; no voltímetro adicional; FW-01 guardas/temporizadores | FAULT; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Medir 6 V con multímetro externo; revisar buck; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F28 DRV pierde pasos / POSITIONING | Reed no corresponde dentro plazo; FW-01 guardas/temporizadores | FAULT; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Revisar corriente/roce/acople; nuevo homing; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F29 Servo en stall / DISPENSING | Movimiento no confirmado; timeout, no sensor de corriente; FW-01 guardas/temporizadores | FAULT; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Aislar, enfriar, medir torque y tensión; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
| F30 Reinicio tras caída antes de persistencia / VERIFY_CLOSE | Journal pendiente; caída posible no reconciliada; FW-01 guardas/temporizadores | REVIEW; OFF ante FAULT/REVIEW/reinicio; F08 conserva nominal | Inspección manual; jamás repetir descarga antigua; FAULT/NACK/REVIEW + sensores + boot/cycle/request; source SIMULATION |
