param([Parameter(Mandatory=$true)][string]$Python, [int]$BoltPort=7689, [int]$HttpPort=7476, [int]$ApiPort=8012)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
$Python=(Resolve-Path -LiteralPath $Python).Path
& $Python -c "import sys; print(sys.executable); assert sys.version_info[:2]==(3,12), 'Python 3.12 required'"
if ($LASTEXITCODE -ne 0) { throw 'Python version check failed' }
$projectPython=Join-Path $projectRoot '.venv-public/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) { & $Python -m venv (Join-Path $projectRoot '.venv-public') }
if ($LASTEXITCODE -ne 0) { throw 'venv creation failed' }
$env:PYTHONUTF8='1';$env:PIP_CACHE_DIR=Join-Path $projectRoot '.cache/pip'
& $projectPython -c "import sys; print(sys.executable)"
& $projectPython -m pip install pip==26.2 setuptools==83.0.0
if ($LASTEXITCODE -ne 0) { throw 'Packaging tool security patches failed' }
& $projectPython -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.14.0
if ($LASTEXITCODE -ne 0) { throw 'CPU torch installation failed' }
$publicLock=Join-Path $projectRoot 'envs/locks/public/public-pip-win64.txt'
if (Test-Path -LiteralPath $publicLock) { & $projectPython -m pip install -r $publicLock -e . }
else { & $projectPython -m pip install -r envs/public-requirements.in -e . }
if ($LASTEXITCODE -ne 0) { throw 'Public dependencies failed' }
& $projectPython -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dependency conflict' }
& $projectPython scripts/download_runtimes.py --public
if ($LASTEXITCODE -ne 0) { throw 'Runtime download/verification failed' }
& $projectPython scripts/download_models.py --bge-only
if ($LASTEXITCODE -ne 0) { throw 'BGE download/verification failed' }
& $projectPython scripts/sample_demo.py configure --bolt-port $BoltPort --http-port $HttpPort --api-port $ApiPort
if ($LASTEXITCODE -ne 0) { throw 'Configuration failed' }
Write-Host 'Installation complete; follow docs/RUN_PUBLIC_WINDOWS.md to build and serve the independent graph.'
