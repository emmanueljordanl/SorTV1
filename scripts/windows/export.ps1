param([Parameter(Mandatory)][string]$Checkpoint,[Parameter(Mandatory)][string]$Manifest,[Parameter(Mandatory)][string]$Output)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location -LiteralPath (Join-Path $repoRoot 'sortv1')
& ../.venv/Scripts/python.exe -m training.export.export_onnx --checkpoint $Checkpoint --manifest $Manifest --output $Output
if ($LASTEXITCODE -ne 0) { throw 'Export/equivalence gate failed. Do not deploy' }
