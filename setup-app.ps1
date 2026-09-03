$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Find-Python312 {
  $py = Get-Command py -ErrorAction SilentlyContinue
  if ($py) {
    try {
      $exe = (& py -3.12 -c "import sys; print(sys.executable)" 2>$null | Select-Object -Last 1).Trim()
      if ($LASTEXITCODE -eq 0 -and $exe -and (Test-Path $exe)) { return $exe }
    } catch {}
  }

  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) {
    try {
      $version = (& python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null | Select-Object -Last 1).Trim()
      if ($LASTEXITCODE -eq 0 -and $version -eq '3.12') { return $python.Source }
    } catch {}
  }

  $candidates = @(
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:ProgramFiles\Python312\python.exe"
  )
  foreach ($candidate in $candidates) {
    if (Test-Path $candidate) { return $candidate }
  }
  return $null
}

$python312 = Find-Python312
if (-not $python312) {
  Write-Host 'Python 3.12 wurde nicht gefunden.' -ForegroundColor Yellow
  $winget = Get-Command winget -ErrorAction SilentlyContinue
  if (-not $winget) {
    throw 'Python 3.12 fehlt und winget ist nicht verfuegbar. Installiere Python 3.12 (64-bit) und starte setup-app.ps1 danach erneut.'
  }

  Write-Host 'Installiere Python 3.12 automatisch mit winget ...' -ForegroundColor Cyan
  & winget install --id Python.Python.3.12 --exact --accept-package-agreements --accept-source-agreements
  if ($LASTEXITCODE -ne 0) {
    throw 'Die automatische Python-3.12-Installation ist fehlgeschlagen. Fuehre manuell aus: winget install --id Python.Python.3.12 --exact'
  }

  $python312 = Find-Python312
  if (-not $python312) {
    throw 'Python 3.12 wurde installiert, ist in diesem Terminal aber noch nicht sichtbar. Schliesse PowerShell, oeffne sie neu und starte setup-app.ps1 erneut.'
  }
}

Write-Host "Python 3.12: $python312" -ForegroundColor Green

if (-not (Test-Path '.venv\Scripts\python.exe')) {
  if (Test-Path '.venv') {
    Write-Host 'Unvollstaendige .venv gefunden - wird neu erstellt.' -ForegroundColor Yellow
    Remove-Item '.venv' -Recurse -Force
  }
  Write-Host 'Erstelle lokale Python-Umgebung (.venv) ...'
  & $python312 -m venv .venv
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path '.venv\Scripts\python.exe')) {
    throw 'Die virtuelle Python-Umgebung konnte nicht erstellt werden.'
  }
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

New-Item -ItemType Directory -Force -Path '.\static\vendor' | Out-Null
$viewer = '.\static\vendor\model-viewer.min.js'
if (-not (Test-Path $viewer)) {
  Write-Host 'Lade lokalen 3D-Viewer einmalig herunter ...'
  Invoke-WebRequest -Uri 'https://unpkg.com/@google/model-viewer@4.1.0/dist/model-viewer.min.js' -OutFile $viewer
}

Write-Host 'Richte lokale TRELLIS-AMD-Workflowprofile ein ...'
& .\.venv\Scripts\python.exe -c "import json; from mille3d.workflow_setup import setup_workflows; print(json.dumps(setup_workflows(), indent=2))"
if ($LASTEXITCODE -ne 0) {
  Write-Warning 'Workflow-Download konnte nicht abgeschlossen werden. Die App kann ihn spaeter erneut starten.'
}

Write-Host '3DCreator v0.2.3 Candidate eingerichtet.' -ForegroundColor Green
Write-Host 'Einmalig als Naechstes: install-amd-backend.ps1. Bei missing_node_type: repair-amd-backend.ps1.' -ForegroundColor Cyan
