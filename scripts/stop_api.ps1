$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
$projectPython = Join-Path $projectRoot '.venv-public/Scripts/python.exe'
& $projectPython -c "import sys; print(sys.executable)"
if ($LASTEXITCODE -ne 0) { throw 'Project Python unavailable' }
& $projectPython scripts/services.py stop api
if ($LASTEXITCODE -ne 0) { throw 'Owned API stop failed' }
