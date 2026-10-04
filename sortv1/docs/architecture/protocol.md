# Protocolo v1

Transporte previsto: USB CDC, identidad USB estable, lectura con timeout. El codec de software es `app/transport/__init__.py`; el driver pySerial y el parser acotado del Pico están pendientes.

La trama es `JSON_ASCII_COMPACTO|HHHH\n`. CRC16-CCITT-FALSE sobre los bytes exactos del JSON, polinomio 0x1021, inicial 0xFFFF, sin reflexión ni XOR final. Vector `123456789` → `29B1`. Máximo 512 bytes incluyendo CRC y LF. No admite saltos internos, claves JSON duplicadas ni comandos libres de actuadores. Descartar hasta LF después de exceso o vencimiento parcial (250 ms de referencia).

| Mensaje | Origen | Significado |
| --- | --- | --- |
| HELLO / STATUS | Pico | Versión, boot, sensores y estado |
| INSPECT | Pico | Ciclo nuevo, inicia vencimiento local |
| SORT | Pi | Un destino 0–3 para el ciclo actual |
| ACK / NACK | Pico | Acepta o rechaza; ACK no confirma caída |
| DONE / FAULT | Pico | Resultado confirmado o fallo |
| HEARTBEAT | Ambos | Vigencia sin movimiento |
| QUERY | Pi | Consulta sin movimiento |

Ejemplo de payload: `{"v":1,"boot":"b17","cycle":42,"request":1,"cmd":"SORT","dest":2}`. DONE incluye `cycle`, `request`, `seq` y `confirmed_bin`; el firmware solo lo emite después de confirmar caída, bandeja vacía y cierre. FAULT/NACK incluyen una causa. HELLO/STATUS incorporarán snapshots de sensores al integrar el hardware.

Clave idempotente: boot + cycle + request. Duplicado idéntico devuelve resultado conocido; payload conflictivo se rechaza. Un request nuevo tampoco permite descargar el mismo ciclo otra vez. Boot anterior, ciclo viejo o estado incompatible no autorizan movimiento. Tras ACK perdido se usa QUERY o el mismo SORT. Un nuevo boot invalida permisos. Los historiales físicos deben ser acotados y su política de retención se verifica al integrar el Pico.

El codec comprueba trama y tipos. Las guardas de estado y la idempotencia pertenecen al Pico. `SimulatedPico` es un doble de software que prueba identidad y duplicación y devuelve DONE sintético inmediatamente; no valida movimientos, sensores ni temporizadores.
