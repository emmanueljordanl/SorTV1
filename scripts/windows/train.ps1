param([string]$Config = 'training/configs/baseline.yaml')
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location -LiteralPath (Join-Path $repoRoot 'sortv1')
& ../.venv/Scripts/python.exe -m training.train.train --config $Config
if ($LASTEXITCODE -ne 0) { throw 'Training failed' }
