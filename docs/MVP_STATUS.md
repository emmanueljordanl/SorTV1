# Estado MVP candidato 0.2.0-mvp-rc1

No es v1.0 ni máquina físicamente aceptada. P01–P16 PENDING. Fuentes: plan original completo y repo/gemelo preservados; no Plan(2). El MVP ya está integrado en main mediante los PR #4/#5; el cierre y la sincronización de develop se realizan mediante PR, sin reescribir historia. La identidad final se resuelve con el tag v0.2.0-mvp-rc1 y su RELEASE_REPORT.

| Categoría | Estado/siguiente acción |
| --- | --- |
| IMPLEMENTED_AND_TESTED_SOFTWARE | Codec/CRC/correlación/idempotencia, journal/cierre manual, datos/leakage/TESTfreeze, quality/preprocess/ONNX, cámara/USB mock, simulación/gemelo. MobileNet CUDA RTX4070 y CPU CI con imágenes sintéticas, export/equivalencia≥50. Sin métricas de residuos. |
| COMPILES_NOT_PHYSICALLY_TESTED | Firmware PicoSDK2.3.1 ELF/BIN/UF2 reales: GPIO, STEPtimer, servoPWM, HX711, VL53L0X. Calibration=false; sin Pico disponible para flashear. |
| REQUIRES_DATA | TrashIA solo auxiliar; nombres numéricos 0–5 sin semántica verificada. Faltan datos LOCAL_PHYSICAL train/validation/test y modelo real; model_manifest permanece NOT_TRAINED. |
| REQUIRES_HARDWARE | Pi/cámara/Pico/actuadores/sensores/cadenaDC/mecánica. Comprar BOM y confirmar modelos/terminales/datasheets antes de conectar. |
| REQUIRES_CALIBRATION | GPIO/polaridades/fallos, tare/escala/ruido, ToF/histéresis, servo endpoints y STEP; ROI/exposure/AWB/focus/background/quality. Sin valores medidos. |
| REQUIRES_PHYSICAL_ACCEPTANCE | P01–P16, 200diagnóstico/200AUTO, sesión60min, recall/purity/coverage LOCAL, Pi latencias/RAM/temp y corte/recuperación/cero no autorizados. |
| REQUIRES_EXTERNAL_ACCESS | Metadata pública TrashIA v1 verificada: Object Detection/CC BY 4.0. Acceso MCP/API/inferencia/export evaluado por separado en [reporte](ml/TRASHIA_MAPPING_REPORT.md). Clave exclusivamente en ROBOFLOW_API_KEY local; nunca en Git/Actions. Mapping numérico CHALLENGE_OOD, reviewed=false. |

| Recibir/comprar | Conectar/medir | Compilar/flashear/ejecutar | Observar/registrar/gate |
| --- | --- | --- | --- |
| Pi5/PSU/SD/cooler | Fuente oficial propia; CSI sin energía; no12V en Pi | OS Lite64, bootstrap_pi, doctor/check_camera | OS/SHA/temp/CSI reales; fase1/10 |
| PicoW/USBdatos | USB lógico, sin motores; nEN pull-up3V3 | Build UF2 seguro, BOOTSEL, hil_protocol | Nuevo boot, BOOT_SAFE, noPWM/calibrated=false; SHA/Git, fase1 |
| Paro/tapa/servicio/corte/fusibles | NC independientes de monitorGPIO, DC rating real, feedbackadaptado | HIL lectura y carga protegida sin motores | Corte con MCU bloqueado, sin autoenergizar. Medir y fase2 antes de potencia |
| DRV/NEMA/acople/eje/rodamientos | Bobinas/RSENSE/VREF/desacoplo, eje soportado | Calibrar tras sensores; destino DIAGNOSTIC explícito | Corriente/temp/posición/corte; fases3/5/9, sin puentes |
| Servo/buck/varillaje | Nominal y buck medidos, extremos mecánicos manuales | Endpoints/guardas completas | Sin choque/atasco/movimiento boot; fases4/5/9 |
| Índices/gate/reset/barreras | Niveles/polaridades, GPIO conforme canon | hil_sensors, mover manualmente sin energía | Índice único, gate excluyente, caída correcta; fases5/6 |
| HX/celda/topes | Topes/DOUT≤3V3, masa patrón | hx_raw, tare/escala/span, configurar firmware | UNKNOWN≠0, ≤200g; evidencia fase7 |
| 4ToF | I2C3V3/pullups/XSHUT highZ | Reiniciar/hil_sensors, medir tof_mm | Direcciones30–33 por boot/UNKNOWN/full/hysteresis; fase8 |
| Cámara/LED/mate | Objeto límite completo, ROI/controles reales | calibrate_camera/capture_dataset | Exposiciones nuevas100ms, controles/SHA, objetos independientes; fase10 |
| Dataset/modelo | TrashIA autorizado auxiliar + LOCAL train/val/test | prepare/train/evaluate/export/Pibenchmark | Testfreeze/equivalencia≥50/targets; fase11 |
| Mecanismo/4bins | Trayecto/rotor vacío antes de giro, resguardos | Rearme físico, DIAGNOSTIC200, AUTO200/60min | DONE físico correcto; recorder P01–P16, fases9/12 |

Comprar: [BOM86 filas](../sortv1/hardware/bom/bom_mvp_minimum.csv), 82IDs+4 adiciones, categorías y cotizaciones vacías. TBC_MODEL no permite omitir seguridad. Plan9902MXN histórico separado. Conectar: [119 conexiones](../sortv1/hardware/wiring/wire_from_to.csv), 104referencias+15adiciones propuestas; aprobar terminales reales. No es instalación certificada.

[BRINGUP](BRINGUP.md) define PRECONDITION/PROCEDURE/EXPECTED/STOP/EVIDENCE para13 fases. Ante STOP aislar energía/parar servicio/preservar logs/[RECOVERY](RECOVERY.md). REVIEW se cierra REMOVED con evidencia, nunca DONE falso. [Windows](DEV_SETUP_WINDOWS.md), [Pi](PI_INSTALL.md), [ML](ml/ML_PIPELINE.md), [operación](OPERATION.md), [pruebas](TESTING.md), [auditoría final](audit/FINAL_MVP_AUDIT.md).
