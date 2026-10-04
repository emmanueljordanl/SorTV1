# SorTV1

Repositorio del contenedor experimental de clasificación de residuos secos: una pieza por ciclo, cuatro destinos, percepción local en Raspberry Pi y control físico independiente en Pico W.

**Estado v0.1.0: arquitectura inicial y simulación ejecutable.** El modelo entrenado, firmware flasheable, CAD aprobado e integración física están pendientes. Las pruebas digitales no acreditan aceptación física.

| Ruta | Contenido |
| --- | --- |
| [sortv1/](sortv1/README.md) | Arquitectura de construcción, Python, contratos C++, configuración, hardware, entrenamiento y pruebas |
| [Gemelo digital](SorTV1_Digital_Twin_Web_v1.0/sortv1-digital-twin/README.md) | Aplicación web de ingeniería, simulación y distribución offline |
| [Plan de seis semanas](Plan_Construccion_SorTV1_6_Semanas.docx) | Documento fuente del plan de construcción |
| [Documento del gemelo](SorTV1_Engineering_Digital_Twin_v1.0.docx) | Especificación del precursor digital |
| [ZIP original](SorTV1_Digital_Twin_Web_v1.0.zip) | Archivo de la distribución aportada; se conserva como referencia |

## Inicio rápido

Python 3.11 o posterior, desde la raíz del repositorio:

```powershell
cd sortv1
py -3 -m unittest discover -s tests -v
py -3 -m app --simulate
```

Para el gemelo digital, Node.js 22 o posterior:

```powershell
cd SorTV1_Digital_Twin_Web_v1.0/sortv1-digital-twin
npm ci
npm test
npm start
```

El gemelo abre en `http://127.0.0.1:4173`. La distribución `dist/` permite ejecutar `node scripts/serve-dist.mjs` sin instalar paquetes. En Linux usar `python3` en lugar de `py -3`.

## Trabajo con Git

Git es obligatorio. `main` conserva bases estables versionadas; `develop` integra trabajo. Las tareas parten de `develop` en ramas cortas `feature/*`, `fix/*`, `test/*` o `docs/*` y regresan mediante pull requests con CI. Una base estable de software no equivale a una máquina físicamente aceptada.

```text
main ← PR de entrega ← develop ← PR de tarea ← feature/* o test/*
```

Leer [CONTRIBUTING.md](CONTRIBUTING.md) y [flujo de construcción](sortv1/docs/procedures/git-workflow.md). No trabajar directamente en `main`, reescribir su historia ni usar force push en ramas compartidas.

Se versionan código, configuración, manifiestos, documentación, documentos originales y distribución offline. Dependencias, cachés, entornos locales y registros de trabajo se excluyen; las evidencias elegidas se conservan con fuente y versión explícitas. El journal de ejemplo es sintético.

La licencia GPL-3.0 del repositorio se conserva en [LICENSE](LICENSE). Los componentes de terceros conservan sus avisos propios, incluido Three.js en la distribución offline.
