# Fuentes canónicas

Editar los CSV aquí y ejecutar `python scripts/generate_hardware_views.py` desde la raíz. CI usa `--check`. Los campos JSON conservan todos los datos originales (82 filas de gemelo, 24 asignaciones presupuestarias del plan, 104 conexiones, 26 GPIO y componentes enriquecidos); no se reconstruyen perdiendo información. `bom_master` contiene cuatro adiciones de MVP identificadas aparte y todas las columnas de cotización vacías.

Las vistas del gemelo conservan su diseño histórico y sus BLOCKER. La vista física wire-from/to agrega los componentes ausentes; cada conexión necesita seleccionar el módulo, confirmar terminales y medir antes de aprobarla. Los indicadores opcionales no consumen GPIO: no se conectarán hasta un ECN con driver y señales aprobadas.

Excepciones: CAD, escena 3D, dimensiones ilustrativas, procedimientos, estados y contratos antiguos de simulación tienen semánticas distintas. Se conservan con procedencia, no se generan desde una tabla eléctrica. El protocolo físico ejecutable está en `firmware/src/protocol.cpp` y `app/transport`; CRC y estados se comprueban juntos. No hay segunda tabla de valores medidos.
