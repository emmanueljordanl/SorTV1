# Laptop Windows 11

Entorno verificado: Python 3.14.7, Torch 2.14.1+cu130, Torchvision 0.29.1+cu130 y NVIDIA RTX 4070 Laptop. Se ejecutó cálculo CUDA, entrenamiento técnico 1+1 epochs, evaluación y equivalencia ONNX en ≥50 imágenes sintéticas. Esto no mide clasificación de residuos reales. Windows nativo; no requiere WSL.

Desde raíz PowerShell: `./scripts/windows/bootstrap_training.ps1`. CUDA usa el índice oficial cu130; `-CpuOnly` usa CPU. Configurar ROBOFLOW_API_KEY en entorno local sin pegarla en Git, argumentos o informes. `.env.example` solo contiene el nombre; scripts no leen implícitamente .env.

Batch 32, workers 0 y threads 4 en baseline.yaml. Ante VRAM insuficiente bajar batch; cerrar programas pesados. No consumir los 16 GB completos. Entrenamiento productivo: ImageNet, head 5 epochs LR1e-3, últimos 3 bloques hasta20 epochs LR1e-4 y patience5, seed42. Hiperparámetros centralizados, BatchNorm congelado en bloques congelados.

Instalar Arm GNU14.3.rel1 oficial, CMake4.4.3 y Ninja1.13.2. Clonar Pico SDK y checkout de `079c6f39023649b154152db30f1d781e884879bc` (2.3.1); inicializar `lib/tinyusb`. Compilación real usada desde raíz:

```powershell
$env:PICO_SDK_PATH = "$PWD/.tools/pico-sdk"
$env:PATH = "$PWD/.tools/arm-toolchain/bin;$PWD/.venv/Scripts;$env:PATH"
cmake -S sortv1/firmware -B build/pico -G Ninja -DPICO_TOOLCHAIN_PATH="$PWD/.tools/arm-toolchain" -DPICO_NO_PICOTOOL=1
cmake --build build/pico -j 4
```

Windows genera UF2 con conversor propio de formato, verificado contra BIN real del ELF, familia RP2040 y direcciones de flash. Linux CI usa picotool del SDK. No flashear con potencia de actuadores. Headers portables host se compilan con g++ o `python -m ziglang c++` (Zig0.16.0).

Entrenar: `./scripts/windows/train.ps1`. Exportar: `./scripts/windows/export.ps1 -Checkpoint RUTA -Manifest RUTA -Output RUTA`. Datos: [ML_PIPELINE](ml/ML_PIPELINE.md). Fuentes: [PyTorch](https://pytorch.org/get-started/locally/), [Pico SDK](https://github.com/raspberrypi/pico-sdk/tree/2.3.1), [Arm GNU](https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads).
