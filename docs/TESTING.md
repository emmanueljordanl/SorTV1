# Verificación

Raíz: `python scripts/doctor.py`. Desde sortv1 con runtime instalado: `python -m unittest discover -s tests -v`; `python -m app --simulate`; `python -m training.datasets.validate training/datasets/manifest.csv --allow-empty`. Manifest vacío solo acredita esquema, no datos. --strict exige archivos/hash/provenance; evaluación final --require-local-eval.

Host C++17: firmware_contracts.cpp; physical_firmware.cpp junto a firmware/src/{state_machine,protocol}.cpp y -Ifirmware/include. Ejecutar ambos y `python scripts/check_cross_language.py RUTA_BIN` desde raíz. Verifica cuatro destinos, caída FREE/BLOCKED/FREE, calibración, reset mantenido en boot, heartbeat, UNKNOWN/FULL y contradicciones.

Gemelo: npm ci/test/run build. Canónicos: `python scripts/generate_hardware_views.py --check`. Pico: [Windows](DEV_SETUP_WINDOWS.md); CI usa SDK fijado/picotool. UF2 artifact incluye commit/hash y calibrated=false.

`python scripts/ml_smoke.py` entrena1+1 epochs sobre imágenes sintéticas y compara PyTorch/ONNX ≥50 imágenes, logits1e-4/probabilidades1e-5/top1 idéntico. PASS_SOFTWARE_ONLY no demuestra precisión real. No desplegar pesos sintéticos.

HIL sin potencia por defecto; hil_cycle requiere opción explícita y guardas. P01–P16: `python -m app.tools.acceptance_record --record RUTA_JSON` requiere source=PHYSICAL, campos completos y archivo/SHA real. Recorder facilita auditoría, no certifica que una foto demuestre PASS. Targets config/acceptance_targets.json; matriz original conservada y PENDING.

CI: Python3.11/3.14, CRC cruzado, C++ host, firmware UF2, ML numérico sintético, integridad/canónicos, gemelo. Sin hardware. Pi benchmark --target-pi, warmup100/1000 inferencias; monitor benchmark_system --minutes60. No usar simulación para completar P01–P16.
