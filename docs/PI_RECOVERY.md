# Recuperación Pi

Parar servicio y aislar actuadores. Conservar tarjeta/journal originales; copia antes de reparación. No eliminar líneas truncadas para desbloquear conteos. Doctor detecta modelo faltante/corrupto y calibraciones pendientes. Restaurar paquete desde copia con SHA registrado.

Reinicio no reenvía INTENT/SORT. Ciclos pendientes requieren [conciliación física](RECOVERY.md). Nuevo boot invalida órdenes; USB caído provoca FAULT y exige rearme físico. No generar request nuevo para la misma pieza. Tras cerrar pendientes y corregir causa, reiniciar desarmado con trayectoria vacía.

Servicio limita3 arranques/60s. Revisar almacenamiento, permisos video/render/dialout, CSI y serial. No usar root para ocultar fallos. Disco lleno después de caída: PENDING_PHYSICAL_RECONCILIATION, sin descarga duplicada ni DONE inventado. Restaurar imagen solo después de preservar evidencia actual.
