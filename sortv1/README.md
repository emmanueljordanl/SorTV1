# SorTV1

Arquitectura inicial del contenedor clasificador basada en `../Plan_Construccion_SorTV1_6_Semanas.docx`. Incluye la estructura solicitada, contratos de Python y C++, lógica de decisión, codec con CRC16, orquestación, journal JSONL, validación del manifest y pruebas de software.

Estado candidato 0.2.0-mvp-rc1: adaptadores Picamera2/ONNX/pySerial, pipeline MobileNetV3 y firmware PicoSDK/UF2 implementados. No hay modelo de residuos validado ni CAD aprobado; aceptación física PENDING. [MVP_STATUS](../docs/MVP_STATUS.md) contiene estado real y próximos gates. La demo sigue exclusivamente SIMULATION.

## Ejecutar y verificar

Desde esta carpeta con Python3.11/3.14 y `pip install -r ../requirements/runtime.txt` para la suite ampliada; la demo conserva stdlib:

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

Manifest inicial solo encabezados: se rechaza salvo --allow-empty para esquema. --strict comprueba archivos/hashes/imagen/provenance; detecta leakage por objeto/original/hash y etiquetas contradictorias. TEST queda congelado por prepare_dataset. [Pipeline ML](../docs/ml/ML_PIPELINE.md) y [pruebas](../docs/TESTING.md).

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

Pi solicita destinos, Pico conserva autoridad física. ACK no equivale a caída; INTENT/fsync antes de SORT y DONE consistente consolida una vez. Reinicios/cortes requieren conciliación, nunca reproducción de órdenes. `python -m app --mode diagnostic` requiere --enable-actuators/--dest y todas las guardas para destino forzado sin IA; `--mode physical` exige modelo LOCAL/calibración/admision. HIL consulta sin energía por defecto. Herramientas/UI/include/src/source/benchmark amplían la estructura inicial.

Leer [arquitectura](docs/architecture/system.md), [protocolo](docs/architecture/protocol.md), [plan de construcción](docs/procedures/construction.md), [puesta en marcha](docs/procedures/commissioning.md), [firmware](firmware/README.md) y [matriz de aceptación](tests/acceptance/matrix.csv).

Los parámetros son puntos de partida del plan. El presupuesto en `hardware/bom/bom.csv` suma $9,902 MXN y conserva referencias históricas y asignaciones por cotizar; no representa precios actuales ni compras realizadas. Las dimensiones, polaridades, componentes de protección y dependencias del entorno Pi/Pico necesitan verificación antes de integrar el equipo.
