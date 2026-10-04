# Auditoría final del candidato MVP

Auditoría del cierre v0.2.0-mvp-rc1, no acta de aceptación física. P01–P16 PENDING. El MVP ya fue integrado en develop/main mediante los PR #4/#5. El PR #6 sincronizó develop con el merge de main; las correcciones de cierre y su integración se realizan mediante PR, sin commits de desarrollo en main ni reescritura del historial. Fuente Word original completa; no Plan(2) disponible.

La identidad final es el commit al que apunta el tag inmutable `v0.2.0-mvp-rc1`. [RELEASE_REPORT.json del release](https://github.com/xxMannexx/SorTV1/releases/download/v0.2.0-mvp-rc1/RELEASE_REPORT.json) conserva los SHA literales **final_commit**, **main_commit**, **develop_commit**, CI run/jobs y **UF2 SHA256** obtenidos después de integrar y sincronizar. Se publica fuera del árbol fuente para poder identificar el propio commit final sin una referencia circular. Los hashes anteriores se conservan exclusivamente como evidencia histórica, nunca como el release final.

```powershell
git fetch origin --tags
git rev-parse 'v0.2.0-mvp-rc1^{commit}'
git rev-parse origin/main
git rev-parse origin/develop
git diff --exit-code origin/main origin/develop
```

`main` y `develop` pueden tener distintos commits de merge y deben tener el mismo árbol funcional. Release assets: UF2/SHA, ZIP offline/SHA, GIT_COMMIT, BUILD_INFO y RELEASE_REPORT. CI del commit final debe estar completamente verde antes de crear el tag. [Validación local del cierre](release_validation.json) registra ensayos de software; los binarios de release proceden del CI exacto de main.

Implementado: Picamera2 con exposiciones/timestamps reales, quality calibrable, preprocess común, ORT/SHA/labels/shapes/NaN, USB pySerial/heartbeat/reconnect/QUERY, controller/journal/CSV/UI, cierre manual, captura local/admisión, train/evaluate/export/benchmark, herramientas de descarga/import/COCO/classification de TrashIA con SDK oficial, firmware PicoSDK C++ y UF2, HIL/recorder, deploymentPi/systemd/Windows, canonBOM/pinout/conexiones/señales, documentación eléctrica/mecánica y13gates. [Inventario completo de archivos](CHANGE_INVENTORY.csv) con estados A/M/D/R respecto al develop de partida; los D son distribuciones generadas retiradas de fuente Git. El ZIP histórico se conserva por traslado. No placeholders de software necesarios.

| Validación ejecutada | Resultado y límites |
| --- | --- |
| Python | 52 tests locales, sin eliminar pruebas originales; regresiones de almacenamiento, correlación, DONE, USB, datos/TESTfreeze, cámara, quality/modelos, conteos por modo y cierre TrashIA |
| C++ host | Contratos originales y máquina física/codec; 4 destinos, duplicados/conflictos, UNKNOWN/FULL, fallo power/heartbeat/WRONG_ROUTE/índices/gate y reset mantenido; CRC Python/C++ golden vectors PASS |
| PicoSDK | Windows ARM14.3.1 + SDK2.3.1; ELF/BIN/UF2 real, payload/header/familia verificados. LinuxCI picotool compila y publica UF2; sin flasheo ni prueba de sensores reales |
| Gemelo | 24/24 tests; build offline; BOM82 y datos históricos preservados. ZIP histórico íntegro, dist fuera de fuenteGit |
| ML CUDA | RTX4070Laptop, Torch2.14.1+cu130/Torchvision0.29.1, GPU cálculo y forward ImageNet reales; fixture entrenada1+1epochs, evaluación/ONNX equivalencia52 imágenes PASS_SOFTWARE_ONLY |
| ML CPU CI | Train/evaluate/export numéricos sobre fixtureSYNTHETIC_TEST; no precisión/recall físicos |
| Laptop benchmark | CPU PyTorch/ORT, warmup100/1000, archivo medido con modeloSYNTHETIC_TEST; no resultados Pi ni métrica de residuos |
| Repo/configs | verify_repository, canon --check, doctor; cotizaciones vacías y configs medidas null; P01–P16 conservados PENDING |
| TrashIA | Metadata pública v1/Object Detection/CC BY 4.0/clases 0–5 verificada el 2026-10-04. Project/version y SDK hosted header auth verificados en entorno separado Python3.13. La inferencia y el export autenticados requieren ROBOFLOW_API_KEY local; se registran por separado. Semántica/IDs de anotaciones PENDING_REVIEW, sin mapping inventado. [Reporte](../ml/TRASHIA_MAPPING_REPORT.md) |

CI de main previo al cierre verificado en [run37176730493](https://github.com/xxMannexx/SorTV1/actions/runs/37176730493), commit 74edbf2bab8705354319696a07a6913289842066; es la base de auditoría, no el commit final del candidato. El CI y los hashes finales constan en RELEASE_REPORT y BUILD_INFO de los assets. [Registro histórico anterior](software_validation.json) conserva resultados de la primera integración. No se compara hash entre compiladores/commits distintos como si fueran mismo binario.

Bugs corregidos: errores retrasados identificados por boot/cycle/request; ACK legacy no consolida; DONE conflictivo bloquea; boot mismatch NACK no toma identidad de otro arranque; pérdidaUSB no reproduceSORT; pendientes sobreviven reinicio; REVIEW se cierra auditado sinDONE; TEST congelado antes de sobrescribir/evaluar; crops por anotación/original sin fuga; SHA duplicado rechazado; BatchNorm de bloques congelados no cambia; métricas de quality acotadas por ciclo; reset mantenido en boot no rearma; UNKNOWN noempty; watch/control guardas antes de salidas. Cierre: inspección sin clave conserva metadata pública verificada, export registra SHA del ZIP y usa extracción segura; respuesta hosted guarda solo campos permitidos y nunca headers/URLs/claves. No se cambia arquitectura ni autoridad física.

Pendientes clasificados: **PHYSICAL** montaje/sensores/actuadores/cadena/aceptación; **CALIBRATION** polaridades/tare/escala/ToF/servo/índices/cámara; **DATA** acceso export/inferencia TrashIA, significado de clases y LOCAL_PHYSICAL; **OPTIONAL/POST_MVP** quedan fuera de este release. La búsqueda TODO/FIXME/HACK/XXX no encuentra tareas críticas en software MVP propio; el verificador contiene esos términos como patrones de búsqueda. Fuentes de terceros se conservan fijadas y con licencia. SECRET_SCAN debe ser PASS sobre archivos, env local e historial relevante antes de publicar.

Decisiones: [ADR0002](../adr/0002-physical-mvp.md). Estado/config hardware segura por defecto; mismo pinout baseline, ninguna asignación GPIO nueva. Datos canónicos lossless preservan82IDs/24presupuestos/104conexiones y añaden4compras/15conexiones propuestas. TBC_MODEL y referencias eléctricas no son aprobación de instalación. Un relé “10A” o servo histórico no se aprueba sin datasheet/corriente/ensayo DC real.

Riesgos restantes: montaje/corte independiente y contactos auxiliares/feedback/nEN deben verificarse; módulos eléctricos/modelos/fusibles/cables no seleccionados; drivers compilados sin medición física; ToF y presencia no certifican catálogo ni seguridad; cámara y100ms/20ms de barreras requieren calibración; ROI/focus/calidad pendientes; dataset local ausente y accesoTrashIA pendiente; no benchmarkPi/60min ni aceptación200/200; fiabilidad de disco/corrupción exige conciliación manual, no garantía de transacción física exactamente una vez. Journal rota archivos pero retiene índice/historial en RAM durante operación: revisar memoria en sesión60min antes de habilitar servicio prolongado.

Siguiente trabajo: comprar/recibir según [BOM](../../sortv1/hardware/bom/bom_mvp_minimum.csv), confirmar modelos y [wire-from/to](../../sortv1/hardware/wiring/wire_from_to.csv), [BRINGUP](../BRINGUP.md), doctor/HIL sin motores, calibrar, compilar/flashear con potencia aislada, registrarPHYSICAL y avanzar gate. TrashIA: clave local/ZIP real → inspect → versión explícita → revisión de clases → externoauxiliar. [ComandosWindows](../DEV_SETUP_WINDOWS.md), [Pi](../PI_INSTALL.md), [ML](../ml/ML_PIPELINE.md), [pruebas](../TESTING.md), [estado](../MVP_STATUS.md).

Comandos inmediatos desde la raíz en Windows, sin hardware:

```powershell
.venv/Scripts/python.exe scripts/doctor.py
.venv/Scripts/python.exe scripts/generate_hardware_views.py --check
Set-Location sortv1
../.venv/Scripts/python.exe -m unittest discover -s tests -v
../.venv/Scripts/python.exe -m app --simulate
Set-Location ..
```

Al recibir la Pi/cámara/Pico, desde la raíz del clon en Pi OS, con potencia de actuadores aislada:

```bash
bash scripts/pi/bootstrap_pi.sh
bash scripts/pi/check_camera.sh
.venv/bin/python scripts/doctor.py --hardware
cd sortv1
../.venv/bin/python -m app.tools.hil_protocol
../.venv/bin/python -m app.tools.hil_sensors
```

No avanzar a movimiento sin completar las precondiciones eléctricas, mecánicas y de calibración de BRINGUP.
