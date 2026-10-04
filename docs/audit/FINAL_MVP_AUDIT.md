# Auditoría final del candidato MVP

Auditoría de software experimental, no acta de aceptación física. P01–P16 PENDING. Rama feature/mvp-physical-integration basada en develop sincronizado con main mediante PR3, sin reescribir historial ni commits de desarrollo en main. PR de esta entrega hacia develop. Fuente Word original completa; no Plan(2) disponible.

Implementado: Picamera2 con exposiciones/timestamps reales, quality calibrable, preprocess común, ORT/SHA/labels/shapes/NaN, USB pySerial/heartbeat/reconnect/QUERY, controller/journal/CSV/UI, cierre manual, captura local/admisión, train/evaluate/export/benchmark, herramientas de descarga/import/COCO/classification de TrashIA con SDK oficial, firmware PicoSDK C++ y UF2, HIL/recorder, deploymentPi/systemd/Windows, canonBOM/pinout/conexiones/señales, documentación eléctrica/mecánica y13gates. [Inventario completo de archivos](CHANGE_INVENTORY.csv) con estados A/M/D/R respecto al develop de partida; los D son distribuciones generadas retiradas de fuente Git. El ZIP histórico se conserva por traslado. No placeholders de software necesarios.

| Validación ejecutada | Resultado y límites |
| --- | --- |
| Python | 48 tests locales, sin eliminar pruebas originales; regresiones de almacenamiento, correlación, DONE, USB, datos/TESTfreeze, cámara, quality/modelos y conteos por modo |
| C++ host | Contratos originales y máquina física/codec; 4 destinos, duplicados/conflictos, UNKNOWN/FULL, fallo power/heartbeat/WRONG_ROUTE/índices/gate y reset mantenido; CRC Python/C++ golden vectors PASS |
| PicoSDK | Windows ARM14.3.1 + SDK2.3.1; ELF/BIN/UF2 real, payload/header/familia verificados. LinuxCI picotool compila y publica UF2; sin flasheo ni prueba de sensores reales |
| Gemelo | 24/24 tests; build offline; BOM82 y datos históricos preservados. ZIP histórico íntegro, dist fuera de fuenteGit |
| ML CUDA | RTX4070Laptop, Torch2.14.1+cu130/Torchvision0.29.1, GPU cálculo y forward ImageNet reales; fixture entrenada1+1epochs, evaluación/ONNX equivalencia52 imágenes PASS_SOFTWARE_ONLY |
| ML CPU CI | Train/evaluate/export numéricos sobre fixtureSYNTHETIC_TEST; no precisión/recall físicos |
| Laptop benchmark | CPU PyTorch/ORT, warmup100/1000, archivo medido con modeloSYNTHETIC_TEST; no resultados Pi ni métrica de residuos |
| Repo/configs | verify_repository, canon --check, doctor; cotizaciones vacías y configs medidas null; P01–P16 conservados PENDING |
| TrashIA | SDK Project/Version y dependencias verificados, ZIP traversal rechazado. Página403/API401 y navegador no disponible; acceso/metadata/clases/versión/licencia reales siguen ACCESS_REQUIRED. No descarga afirmada ni mapeo de clase inventado |

CI verificada verde en los siete jobs de [run37176006179](https://github.com/xxMannexx/SorTV1/actions/runs/37176006179), SHA df8a344ee7fa9ca3cf0cc7d392c0758285abb5a1, incluida la calibración configurable de debounce e índices. [Registro estructurado de validación](software_validation.json) conserva origen, hashes y límites. Los commits posteriores de esta auditoría se verifican en el PR y Actions; artifacts incluyen SHA exacto del build. No se compara hash entre compiladores/commits distintos como si fueran mismo binario.

Bugs corregidos: errores retrasados identificados por boot/cycle/request; ACK legacy no consolida; DONE conflictivo bloquea; boot mismatch NACK no toma identidad de otro arranque; pérdidaUSB no reproduceSORT; pendientes sobreviven reinicio; REVIEW se cierra auditado sinDONE; TEST congelado antes de sobrescribir/evaluar; crops por anotación/original sin fuga; SHA duplicado rechazado; BatchNorm de bloques congelados no cambia; métricas de quality acotadas por ciclo; reset mantenido en boot no rearma; UNKNOWN noempty; watch/control guardas antes de salidas.

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
