# SorTV1

Arquitectura inicial del contenedor clasificador basada en `../Plan_Construccion_SorTV1_6_Semanas.docx`. Incluye la estructura solicitada, contratos de Python y C++, lógica de decisión, codec con CRC16, orquestación, journal JSONL, validación del manifest y pruebas de software.

Estado: base de desarrollo v0.1.0. La demo es SIMULATION y utiliza datos sintéticos. No hay modelo entrenado, firmware flasheable, CAD aprobado ni adaptadores de hardware. La aceptación física está pendiente.

## Ejecutar y verificar

Desde esta carpeta, con Python 3.11 o posterior, sin dependencias externas para la demo y las pruebas:

```powershell
cd C:\Users\Manee\Downloads\SorTV1\sortv1
py -3 -m unittest discover -s tests -v
py -3 -m app --simulate
```

La demo recorre las cuatro clases y escribe un journal nuevo en `evidence/experiments/` con `source: SIMULATION`. El conteo esperado es `[1, 1, 1, 1]` aunque se reciba DONE repetido. Las probabilidades y confirmaciones son sintéticas y no miden IA ni mecánica. En Linux usar `python3` en lugar de `py -3`.

Para comprobar el dataset real cuando se hayan añadido imágenes al manifest:

```powershell
py -3 -m training.datasets.validate training/datasets/manifest.csv
```

El manifest inicial tiene solo encabezados; el validador lo rechaza por estar vacío. Detecta fuga por objeto, etiquetas contradictorias e imágenes repetidas. No verifica calidad visual ni existencia de cada imagen.

## Estructura

```text
sortv1/
├── app/          capture, quality, inference, decision, transport, controller, evidence
├── firmware/     state_machine, drivers, protocol, config
├── training/     datasets, train, evaluate, export
├── tests/        unit, protocol, integration, fault_injection, acceptance
├── config/
├── models/
├── hardware/     electrical, wiring, pinout, cad, bom
├── docs/         architecture, adr, procedures, risks
├── evidence/     benchmarks, experiments, acceptance, photos
└── README.md
```

La Pi solicita destinos; el Pico valida y ejecuta movimientos. ACK no equivale a caída. Las intenciones se persisten antes de emitir SORT; DONE consolida conteos una vez por ciclo. Reinicios con operaciones pendientes exigen conciliación manual. El gemelo digital web existente queda separado.

Leer [arquitectura](docs/architecture/system.md), [protocolo](docs/architecture/protocol.md), [plan de construcción](docs/procedures/construction.md), [puesta en marcha](docs/procedures/commissioning.md), [firmware](firmware/README.md) y [matriz de aceptación](tests/acceptance/matrix.csv).

Los parámetros son puntos de partida del plan. El presupuesto en `hardware/bom/bom.csv` suma $9,902 MXN y conserva referencias históricas y asignaciones por cotizar; no representa precios actuales ni compras realizadas. Las dimensiones, polaridades, componentes de protección y dependencias del entorno Pi/Pico necesitan verificación antes de integrar el equipo.
