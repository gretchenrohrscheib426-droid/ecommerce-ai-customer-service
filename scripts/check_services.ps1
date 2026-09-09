param([string]$Python)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
if (-not $Python) { $Python=Join-Path $projectRoot '.venv-public/Scripts/python.exe' }
& $Python scripts/check_environment.py
exit $LASTEXITCODE
