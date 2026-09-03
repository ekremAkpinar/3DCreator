$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if (-not (Test-Path '.venv\Scripts\python.exe')) {
  throw '3DCreator ist noch nicht eingerichtet. Zuerst setup-app.ps1 ausfuehren.'
}

& .\.venv\Scripts\python.exe -c "import json; from mille3d.workflow_setup import setup_workflows; print(json.dumps(setup_workflows(force=True), indent=2))"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host 'TRELLIS-AMD-Workflows wurden neu erzeugt.' -ForegroundColor Green
