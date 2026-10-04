# SorTV1 Digital Twin Web v1.0

Aplicación local de ingeniería: 82 entradas de BOM, representación 3D paramétrica, estados, protocolo USB conceptual, sensores, energía, 30 fallos, montaje y evidencia.

**Estado: precursor digital ejecutable, con bloqueos de ingeniería abiertos. No está liberado para fabricación ni controla hardware.** Consulte `data/risks.json` y `data/audit.json`. No se declara DIGITAL BASELINE COMPLETE mientras exista una condición incompleta de la auditoría.

## Requisitos e instalación

Node.js 22 o posterior, npm y navegador de escritorio con WebGL 2. Three.js está fijado en 0.186.0 y `package-lock.json` conserva su integridad. Se recomienda trabajar con el navegador actualizado y aceleración gráfica habilitada.

```bash
cd sortv1-digital-twin
npm ci
npm start
```

Abra `http://127.0.0.1:4173`. El servidor escucha solo en el equipo local. No abra `index.html` con `file://`: los módulos ES y datos JSON necesitan HTTP.

## Uso sin internet

El ZIP contiene `dist/` con Three.js y los assets locales ya empaquetados. Para utilizar ese build no hace falta descargar dependencias:

```bash
cd sortv1-digital-twin
node scripts/serve-dist.mjs
```

El desarrollo requiere `npm ci` una vez. Después de instalar las dependencias, `npm start`, `npm test` y `npm run build` funcionan sin internet. El sitio no usa APIs comerciales, CDN, telemetría, nube ni Google Fonts.

## Primer ciclo

1. Abra **SIMULACIÓN** o **INTERIOR**.
2. Pulse **Rearme físico simulado**. Los ToF ya completaron su inicialización virtual; el rotor busca ROT0.
3. Espere **LISTO**.
4. Elija un objeto y pulse **Depositar una pieza y cerrar tapa**. La selección es un estímulo de simulación, no una orden de destino.
5. Observe INSPECT, los tres frames, SORT, ACK, índice, OPEN, haz, vacío, CLOSED y DONE.
6. Pause o avance **Evento** para inspeccionar causalidad y señales. `×0.25`, `×0.5`, `×1`, `×2` y `×5` modifican el reloj virtual, no los límites del contrato.

Los números del ciclo proceden de una planta cinemática de referencia. No son mediciones sobre Raspberry Pi, Pico ni actuadores reales.

## Controles y vistas

Arrastrar con botón izquierdo: orbitar. Rueda: zoom. Botón derecho: desplazar. Clic sobre una pieza: identidad, alimentación, GPIO, fijación, calibración y pruebas. **Enfocar pieza** cambia cámara. **Ver conexiones** resalta relaciones.

V01–V20 ofrecen producto, caras ortogonales, inferior, puerta abierta, cortes, transparencia, exploded, inspección, rotor, electrónica, arnés, bins, trayectoria, mantenimiento y riesgos. El slider de carcasa controla opacidad; el de exploded separa A–O sin cambiar IDs. La vista electrónica muestra las fuentes externas y el panel posterior. Use los filtros POWER ONLY, SIGNAL ONLY, SENSOR BUS, I2C, ACTUATORS o ALL.

El panel se amplía con **↗**. BOM y mediciones tienen mucho contenido; se pueden consultar junto a la maqueta.

## Fallos

Seleccione **FALLOS**, arme F01–F30 y vuelva a **SIMULACIÓN** para depositar una pieza. El fallo se aplica al alcanzar su fase. F08 es un ensayo de duplicado y debe concluir normalmente con una sola descarga. E-STOP, tapa y servicio también pueden activarse manualmente desde los controles de estímulo.

Liberar el paro no rearma. Use **Inspeccionar y retirar**, que representa una intervención humana con potencia aislada, y después **Rearme físico simulado**. No implica que la máquina física pueda limpiar por sí misma un atasco.

## Mediciones y cotas

`data/dimensions.json` es el registro central. `value` siempre contiene un número de visualización y `status` declara REFERENCE, TBC-MEDIR, MEASURED o FROZEN. Ningún valor inicial está físicamente congelado. Los valores TBC son envolventes gráficas, no cotas para taladrar.

La herramienta de dos puntos mide la geometría virtual. Los botones **Medido** y **Congelar** son distintos. Se guardan cambios en el navegador local; **Exportar dimensions.json** produce una envoltura `{source, dimensions}`. Para incorporarla al proyecto, reemplace el contenido de `data/dimensions.json` por el objeto `dimensions` exportado. Reinicie o recargue. Para restaurar el archivo original en la UI, elimine `sortv1_dimensions_user` del almacenamiento local del navegador.

Cotas de catálogo no equivalen a mediciones de la pieza comprada. Los modelos procedurales son conceptuales y no incluyen roscas, tolerancias de ajuste ni todos los radios de manufactura. Las envolventes calculadas identifican riesgos; no sustituyen CAD verificado ni 50 descargas manuales.

## Ensamblaje y puesta en marcha

**ENSAMBLAJE** contiene las 22 etapas con entrada, trabajo, medición, PASS, error típico y condición de parada. Las piezas futuras se ocultan por grupo; algunas operaciones tempranas son mediciones y no montaje.

**COMMISSIONING** recorre C0–C10 en orden. Se requieren todas las casillas de una etapa. Todos los checks se guardan como SIMULATION. El resultado físico permanece `null`.

**TEST CENTER** ejecuta P01–P16 en su parte lógica. P09 usa probabilidades sintéticas; no produce recall ni pureza reales. P15 avanza una hora de reposo virtual; no mide temperatura. P16 realiza 200 ciclos deterministas del modelo, no ensayos mecánicos físicos. Los resultados físicos se recolectan fuera del simulador con evidencia independiente.

## Evidencia y protocolo

Los monitores muestran sensores, GPIO, protocolo RAW/DECODED, eventos, causalidad, actuadores y estados. El protocolo calcula CRC16-CCITT-FALSE sobre los bytes ASCII exactos y limita cada línea a 512 bytes. `123456789` debe producir `29B1`.

**EVIDENCIA** exporta JSON, JSONL y CSV con `source: SIMULATION` y `result_kind: SIMULATED`. Un `physical_result: DONE` dentro de un evento sigue siendo resultado de la planta virtual porque su `source` es SIMULATION. Los registros futuros del equipo deberán generarse por su software real con `source: PHYSICAL`; el navegador no los crea.

## Estructura y separación del hardware

- `src/core/`: reloj, eventos, autoridad conceptual y coordinación.
- `src/simulation/`: planta, inspección sintética e inyección de fallos.
- `src/sensors/`: inicialización, mediana e histéresis de ToF.
- `src/protocol/`: CRC, serialización y parser incremental acotado.
- `src/three/`: geometría de producto, selección, cámaras, capas, cables y animación.
- `src/engineering/`: mediciones, comprobaciones conservadoras y pruebas P01–P16.
- `src/evidence/`: registros y exportaciones.
- `src/main.js`: UI; solo solicita estímulos virtuales y observa estado.
- `data/`: BOM, componentes, dimensiones, GPIO, conexiones, procedimientos, riesgos y trazabilidad.
- `docs/`: documento fuente, contratos de producción y guías.
- `tests/`: T01–T24 y sus pruebas de comportamiento.
- `scripts/`: servidor local, build y auditoría.
- `dist/`: copia autosuficiente para uso offline.

Esta estructura agrupa los módulos visuales pequeños en `ModelBuilder.js` y `SceneManager.js` para mantener una única definición geométrica. No son archivos vacíos por cada pieza. El software real conserva `app/capture.py`, `quality.py`, `inference.py`, `decision.py`, `transport.py`, `controller.py`, `evidence.py`, `operator_ui/`, `training/`, `firmware/`, `tests/`, `config/`, `models/`, `docs/` y `evidence/`; sus contratos se especifican en `docs/production-contracts.md`. **No se entrega firmware flasheable, un modelo entrenado ni software de producción listo para mover motores.** Son entregables de construcción física posteriores; Three.js nunca se instala como autoridad física.

## Pruebas, cobertura y auditoría

```bash
npm test
npm run audit:twin
npm run build
```

La auditoría compara la BOM base con la BOM digital y ejecuta los 30 fallos y P01–P16. `data/traceability.json` relaciona requisito, capítulo, ID, módulo y prueba. Un PASS digital solo acredita la comprobación indicada. Revise las limitaciones y los campos `INCOMPLETE`.

## Bloqueos principales

La BOM no especifica el circuito de retención/rearme y los contactos independientes de resguardos, la interfaz de feedback de 12 V a GPIO28, el pull-up externo de nEN, los drivers de los tres indicadores de 12 V ni el tipo eléctrico del LED blanco. No se agregan silenciosamente: aparecen como conexiones pendientes y ECN no aceptadas. Tampoco se simulan sensores nuevos de corriente, tensión, presencia de bins o atasco. Estos fallos se detectan por las señales y timeouts disponibles.

## Aislamiento de VizionarIA

Repositorio, BOM, presupuesto, hardware, cronograma, versiones, pruebas y deuda técnica son exclusivos de SorTV1. Solo se transfiere conocimiento. Nada de este proyecto es requisito previo para avanzar VizionarIA.
