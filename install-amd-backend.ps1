param([string]$ComfyDir = "$PSScriptRoot\runtime\ComfyUI")
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Invoke-Native {
  param(
    [Parameter(Mandatory=$true)][string]$Exe,
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$Args
  )
  & $Exe @Args
  if ($LASTEXITCODE -ne 0) {
    throw "Befehl fehlgeschlagen ($LASTEXITCODE): $Exe $($Args -join ' ')"
  }
}

function Find-Python312 {
  if (Get-Command py -ErrorAction SilentlyContinue) {
    try {
      $exe = (& py -3.12 -c "import sys; print(sys.executable)" 2>$null | Select-Object -Last 1).Trim()
      if ($LASTEXITCODE -eq 0 -and $exe -and (Test-Path $exe)) { return $exe }
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

Write-Host "3DCreator - TRELLIS.2 AMD Backend" -ForegroundColor Cyan
Write-Host "Zielprofil: RX 6800 XT / gfx1030 / Windows / Python 3.12" -ForegroundColor Gray
Write-Host "Installationsordner: $ComfyDir" -ForegroundColor DarkGray

$python312 = Find-Python312
if (-not $python312) {
  throw "Python 3.12 fehlt. Fuehre zuerst setup-app.ps1 aus oder installiere Python 3.12."
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  $winget = Get-Command winget -ErrorAction SilentlyContinue
  if (-not $winget) {
    throw "Git fehlt und winget ist nicht verfuegbar. Installiere Git fuer Windows und starte das Skript erneut."
  }
  Write-Host "Git fehlt - installiere Git fuer Windows automatisch ..." -ForegroundColor Yellow
  Invoke-Native winget install --id Git.Git --exact --accept-package-agreements --accept-source-agreements
  $gitCandidate = "$env:ProgramFiles\Git\cmd\git.exe"
  if (Test-Path $gitCandidate) {
    Set-Alias git $gitCandidate -Scope Script
  } elseif (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git wurde installiert, ist in diesem Terminal aber noch nicht sichtbar. PowerShell neu oeffnen und Installer erneut starten."
  }
}

if (-not (Test-Path $ComfyDir)) {
  Write-Host "Lade ComfyUI ..." -ForegroundColor Cyan
  Invoke-Native git clone https://github.com/comfyanonymous/ComfyUI.git $ComfyDir
}

Set-Location $ComfyDir
if (-not (Test-Path "venv\Scripts\python.exe")) {
  Write-Host "Erstelle eigene Python-Umgebung fuer das GPU-Backend ..." -ForegroundColor Cyan
  Invoke-Native $python312 -m venv venv
}
$python = Join-Path $ComfyDir "venv\Scripts\python.exe"

Invoke-Native $python -m pip install --upgrade pip

Write-Host "Installiere ROCm 10 / PyTorch fuer gfx1030 ..." -ForegroundColor Cyan
Invoke-Native $python -m pip install --extra-index-url https://stable.repo.amd.com/rocm/whl-next/ `
  "torch[device-gfx1030]==2.13.0+rocm10.0.0" `
  "torchvision[device-gfx1030]==0.28.0+rocm10.0.0" `
  "torchaudio==2.11.0.2+rocm10.0.0" `
  "rocm[libraries,device-gfx1030]==10.0.0"

Write-Host "Installiere ComfyUI-Abhaengigkeiten ..." -ForegroundColor Cyan
Invoke-Native $python -m pip install -r requirements.txt

$custom = Join-Path $ComfyDir "custom_nodes\ComfyUI-Trellis2-AMD"
if (-not (Test-Path $custom)) {
  Write-Host "Lade TRELLIS.2 AMD Nodes ..." -ForegroundColor Cyan
  Invoke-Native git clone https://github.com/dmonkman/ComfyUI-Trellis2-AMD.git $custom
}
Set-Location $custom

$wheelDir = Join-Path $custom "wheels\Windows\Python3.12"
$wheels = @(
  "cumesh-1.0+rocm10.0-cp312-cp312-win_amd64.whl",
  "flex_gemm-1.0.0+rocm10.0-cp312-cp312-win_amd64.whl",
  "o_voxel-0.0.1+rocm.10.0-cp312-cp312-win_amd64.whl",
  "nvdiffrast-0.4.0+rocm10.0-cp312-cp312-win_amd64.whl"
)
foreach ($wheel in $wheels) {
  $path = Join-Path $wheelDir $wheel
  if (-not (Test-Path $path)) {
    throw "Erforderliches AMD-Wheel fehlt: $path"
  }
  Invoke-Native $python -m pip install $path
}

Write-Host "Installiere TRELLIS-Abhaengigkeiten ..." -ForegroundColor Cyan
Invoke-Native $python -m pip install -r requirements.txt

Write-Host "Pruefe RX 6800 XT / ROCm ..." -ForegroundColor Cyan
Invoke-Native $python -c "import torch; print('Torch:', torch.__version__); print('HIP:', torch.version.hip); print('GPU verfuegbar:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO GPU'); assert torch.cuda.is_available(), 'ROCm GPU wurde nicht erkannt'"

Set-Location $PSScriptRoot
Write-Host "" 
Write-Host "Backend erfolgreich eingerichtet." -ForegroundColor Green
Write-Host "Die 3DCreator-Workflows werden von setup-app.ps1 / setup-workflows.ps1 verwaltet." -ForegroundColor Green
Write-Host "Beim ersten echten TRELLIS-Lauf koennen zusaetzliche Modellgewichte automatisch heruntergeladen werden." -ForegroundColor Yellow
Write-Host "" 
Write-Host "Naechster Schritt: .\check-system.bat" -ForegroundColor Cyan
Write-Host "Danach genuegt im Alltag: .\start.bat" -ForegroundColor Cyan
