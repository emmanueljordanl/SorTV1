# SorTV1

Repositorio del contenedor experimental de clasificación de residuos secos: una pieza por ciclo, cuatro destinos, percepción local en Raspberry Pi y control físico independiente en Pico W.

**Candidato v0.2.0-mvp-rc1**, integrado en `main` mediante PR. Hay captura Picamera2, quality calibrable, ONNX Runtime, USB pySerial, MobileNetV3Small, HIL y firmware Pico SDK que genera UF2 real. Los procedimientos y el BOM preparan el bring-up; **NO EXISTE ACEPTACIÓN FÍSICA AÚN**. P01–P16 permanecen PENDING y el modelo de producción NOT_TRAINED. La metadata pública de TrashIA v1 está verificada; inferencia, exportación y semántica de clases se verifican por separado. La operación normal sigue siendo local, sin nube.

El [release candidate](https://github.com/xxMannexx/SorTV1/releases/tag/v0.2.0-mvp-rc1) identifica el commit final y contiene UF2/SHA, ZIP offline, GIT_COMMIT y RELEASE_REPORT. El tag representa software, firmware y procedimientos para bring-up; no una máquina validada. `main` y `develop` conservan la misma base funcional tras sincronización mediante PR.

Abrir [MVP_STATUS](docs/MVP_STATUS.md) para comprar, conectar, medir, compilar, flashear y avanzar gates. [BRINGUP](docs/BRINGUP.md), [Windows](docs/DEV_SETUP_WINDOWS.md), [Pi](docs/PI_INSTALL.md), [ML](docs/ml/ML_PIPELINE.md), [pruebas](docs/TESTING.md), [auditoría final](docs/audit/FINAL_MVP_AUDIT.md). Pi jamás controla STEP/PWM/rearme. ACK no cuenta; solo DONE consistente consolida. P01–P16 PENDING; no v1.0 físico.

| Ruta | Contenido |
| --- | --- |
| [sortv1/](sortv1/README.md) | Arquitectura de construcción, Python, contratos C++, configuración, hardware, entrenamiento y pruebas |
| [Gemelo digital](SorTV1_Digital_Twin_Web_v1.0/sortv1-digital-twin/README.md) | Aplicación web de ingeniería, simulación y distribución offline |
| [Plan de seis semanas](Plan_Construccion_SorTV1_6_Semanas.docx) | Documento fuente del plan de construcción |
| [Documento del gemelo](SorTV1_Engineering_Digital_Twin_v1.0.docx) | Especificación del precursor digital |
| [ZIP histórico](archives/legacy/README.md) | Aportación íntegra preservada; nuevos ZIP/build son artifacts con SHA/commit |

## Inicio rápido

Python 3.11/3.14 con runtime; Windows nativo desde raíz:

```powershell
./scripts/windows/bootstrap_training.ps1
./.venv/Scripts/python.exe scripts/doctor.py
cd sortv1
../.venv/Scripts/python.exe -m unittest discover -s tests -v
../.venv/Scripts/python.exe -m app --simulate
```

Para el gemelo digital, Node.js 22 o posterior:

```powershell
cd SorTV1_Digital_Twin_Web_v1.0/sortv1-digital-twin
npm ci
npm test
npm start
```

El gemelo abre en `http://127.0.0.1:4173`. Generar `dist/` con `npm run build`; ZIP con commit/SHA mediante `python scripts/build_distribution.py` desde raíz. CI publica artifact. HIL real desde sortv1: `python -m app.tools.hil_protocol` sin actuadores. AUTO: `python -m app --mode physical` exige calibración, paquete LOCAL_PHYSICAL y admisión humana por ciclo; inicia desarmado.

## Trabajo con Git

Git es obligatorio. `main` conserva bases estables versionadas; `develop` integra trabajo. Las tareas parten de `develop` en ramas cortas `feature/*`, `fix/*`, `test/*` o `docs/*` y regresan mediante pull requests con CI. Una base estable de software no equivale a una máquina físicamente aceptada.

```text
main ← PR de entrega ← develop ← PR de tarea ← feature/* o test/*
```

Leer [CONTRIBUTING.md](CONTRIBUTING.md) y [flujo de construcción](sortv1/docs/procedures/git-workflow.md). No trabajar directamente en `main`, reescribir su historia ni usar force push en ramas compartidas.

Se versionan código, configuración, manifiestos, documentación y documentos originales. Builds/datos/pesos/claves/entornos locales se excluyen; evidencia elegida conserva fuente/versión. Dist no es fuente primaria; ZIP histórico y tag v0.1.0 preservan la entrega anterior. No se reescribe historial. Hardware deriva de CSV canónicos sin perder IDs/campos del gemelo.

La licencia GPL-3.0 del repositorio se conserva en [LICENSE](LICENSE). Los componentes de terceros conservan sus avisos propios, incluido Three.js en la distribución offline.
