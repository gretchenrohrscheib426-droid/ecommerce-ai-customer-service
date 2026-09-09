param([string]$Python)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
if (-not $Python) { $Python=Join-Path $projectRoot '.venv-public/Scripts/python.exe' }
$projectPython=(Resolve-Path -LiteralPath $Python).Path
$env:ECOMMERCE_ROOT=$projectRoot
$env:PYTHONPATH=Join-Path $projectRoot 'src'
$env:PYTHONUTF8='1'
& $projectPython -c "import sys; print(sys.executable)"
$apiPort=& $projectPython -c "from ecommerce_graph_agent.config import Settings; print(Settings.load().api_port)"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $projectPython -m uvicorn ecommerce_graph_agent.web.app:app --host 127.0.0.1 --port $apiPort
exit $LASTEXITCODE
