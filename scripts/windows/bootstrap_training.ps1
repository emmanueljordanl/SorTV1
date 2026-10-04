param([switch]$CpuOnly)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location -LiteralPath $repoRoot
py -3.14 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Python 3.14 required for pinned Windows environment' }
& .venv/Scripts/python.exe -m pip install --upgrade pip
$torchIndex = if ($CpuOnly) { 'https://download.pytorch.org/whl/cpu' } else { 'https://download.pytorch.org/whl/cu130' }
& .venv/Scripts/python.exe -m pip install torch==2.14.1 torchvision==0.29.1 --index-url $torchIndex
if ($LASTEXITCODE -ne 0) { throw 'PyTorch installation failed' }
& .venv/Scripts/python.exe -m pip install -r requirements/training.txt -r requirements/roboflow.txt cmake==4.4.3 ninja==1.13.2
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
& .venv/Scripts/python.exe -c "import torch; print(torch.__version__); print('CUDA',torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
& .venv/Scripts/python.exe scripts/doctor.py
