param([string]$Python)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
if (-not $Python) { $Python=Join-Path $projectRoot '.venv-public/Scripts/python.exe' }
& $Python -c "import sys; print(sys.executable)"
& $Python -m ruff check .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $Python -m compileall -q src
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $Python -m pytest tests/unit tests/e2e -v
exit $LASTEXITCODE
