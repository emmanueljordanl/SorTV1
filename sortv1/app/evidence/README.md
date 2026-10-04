# Persistencia de eventos

Journal JSONL con source y result_kind, reloj monótono Pi y reloj de pared. Escrituras con flush/fsync; fallo de persistencia bloquea el journal. Conteo por DONE deduplicado y recuperación de ciclos incompletos. Pendientes: rotación, espacio libre, exportación CSV y conciliación humana documentada.
