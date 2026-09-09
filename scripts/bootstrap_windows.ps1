param([Parameter(Mandatory=$true)][string]$Python)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
$basePython=(Resolve-Path -LiteralPath $Python).Path
& $basePython -c "import sys; print(sys.executable); assert sys.version_info[:2]==(3,12)"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$condaCommand=Get-Command conda -ErrorAction SilentlyContinue
Write-Host ("Conda found: " + [bool]$condaCommand)
& (Join-Path $PSScriptRoot 'public_bootstrap.ps1') -Python $basePython
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if (-not (Test-Path -LiteralPath '.env')) { Copy-Item -LiteralPath '.env.example' -Destination '.env' }
$projectPython=Join-Path $projectRoot '.venv-public/Scripts/python.exe'
& $projectPython scripts/check_environment.py
exit $LASTEXITCODE
