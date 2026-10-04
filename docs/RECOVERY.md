# Conciliación de ciclos

FAULT/REVIEW/corte/USB/fallo de evidencia: aislar potencia, parar servicio, conservar boot/cycle/request y estado de pieza/destino. Inspeccionar bandeja, rotor, trayecto y recipientes. Retirar pieza manualmente, despejar y cerrar compuerta. Fotografiar; registrar operador/motivo/estado conocido. No inferir caída por ACK o timeout.

Desde sortv1 con servicio parado:

```bash
python -m app.tools.reconcile --journal evidence/experiments/physical.jsonl --cycle BOOT:NUM --outcome REMOVED --operator OPERADOR --reason MOTIVO --evidence RUTA_REAL --power-isolated --tray-empty --path-clear --gate-closed
```

ABORTED/RECONCILED son alternativas auditables; no cuentan ni se vuelven DONE. Si cayó pero no se persistió, RECONCILED conserva discrepancia en conteos y evidencia. No modificar eventos previos.

Journal truncado: conservar copia/SHA; bloqueo deliberado. Recuperación debe conservar bytes dañados, últimos eventos válidos y explicación, nunca truncamiento→éxito automático. Corregir causa/cerrar pendientes, reiniciar desarmado y rearme físico con bandeja vacía. Ninguna orden se reproduce tras reconectar.
