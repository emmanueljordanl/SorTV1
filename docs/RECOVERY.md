# Conciliación de ciclos

FAULT/REVIEW/corte/USB/fallo de evidencia: aislar potencia, parar servicio, conservar boot/cycle/request y estado de pieza/destino. Inspeccionar bandeja, rotor, trayecto y recipientes. Retirar pieza manualmente, despejar y cerrar compuerta. Fotografiar; registrar operador/motivo/estado conocido. No inferir caída por ACK o timeout.

Desde sortv1 con servicio parado:

```bash
python -m app.tools.reconcile --journal evidence/experiments/physical.jsonl --cycle BOOT:NUM --outcome REMOVED --operator OPERADOR --reason MOTIVO --evidence RUTA_REAL --power-isolated --tray-empty --path-clear --gate-closed
```

ABORTED/RECONCILED son alternativas auditables; no cuentan ni se vuelven DONE. Si cayó pero no se persistió, RECONCILED conserva discrepancia en conteos y evidencia. No modificar eventos previos.

Journal truncado: conservar copia/SHA; bloqueo deliberado. Recuperación debe conservar bytes dañados, últimos eventos válidos y explicación, nunca truncamiento→éxito automático. Corregir causa/cerrar pendientes, reiniciar desarmado y rearme físico con bandeja vacía. Ninguna orden se reproduce tras reconectar.

Secuencia FAULT/REVIEW/E-STOP/SERVICE/reinicio: servicio parado y potencia aislada → retirar/reparar → verificar trayecto/bandeja vacíos y gate cerrado → restaurar guardas → iniciar servicio desarmado → ACTUATOR_ENABLE físico (latch12V) → PHYSICAL_RESET (GPIO15) tras soltarlo → CHECK_HOME → READY. No unir12V a GPIO15. Servicio parado implica pérdida de heartbeat y estado seguro; un feedback power=false no identifica qué guarda cortó. Cerrar tapa/servicio o desbloquear E-STOP nunca autoriza reenergización automática.

CHECK_HOME exige exactamente un índice activo estable. Sin índice, no hay búsqueda automática: aislar potencia, trayecto vacío, reposicionar rotor manualmente hasta un solo índice, restaurar guardas, habilitar y rearmar. Dos índices→FAULT. Si se pierde el índice durante CHECK_HOME, outputs OFF y HOME_TIMEOUT según la política existente. Ver [ADR0002](adr/0002-physical-mvp.md).

La carga normal desde READY es distinta: abrir tapa→actuator power OFF→cargar→cerrar→ACTUATOR_ENABLE. READY espera seguro sin potencia y no falla exclusivamente por power=false; no hace falta rearme por esa carga. En POSITIONING/DISPENSING/VERIFY_CLOSE la pérdida de potencia sigue siendo FAULT. Inspection deadline expirado produce REVIEW, nunca un SORT tardío; retirar y conciliar como cualquier REVIEW.
