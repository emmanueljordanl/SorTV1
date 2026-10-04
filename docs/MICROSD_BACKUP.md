# Respaldo microSD

Actuadores aislados, servicio parado y Pi apagada correctamente. Crear imagen desde otro equipo/lector con herramienta que verifique lectura; nunca escribir sobre fuente. Registrar tarjeta, capacidad, OS, fecha, Git SHA, firmware/modelo/config/journal hashes.

Guardar imagen fuera de Git con SHA256 y evidencia separada. Probar restauración en otra microSD de capacidad suficiente; confirmar boot desarmado y doctor/HIL sin motores. Backup sin restauración sigue pendiente. Dispositivo y capacidad reales: TBC_MEASURE; no usar un comando destructivo sobre un disco supuesto. Restaurar backup no concilia ciclos posteriores.
