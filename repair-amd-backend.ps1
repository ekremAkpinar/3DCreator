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

Write-Host "3DCreator - TRELLIS AMD Reparatur" -ForegroundColor Cyan
Write-Host "Diese Reparatur behebt insbesondere 'missing_node_type' / fehlende TRELLIS-Nodes." -ForegroundColor Gray

$connection = Get-NetTCPConnection -LocalPort 8188 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($connection) {
  throw "ComfyUI laeuft noch auf Port 8188. Schliesse zuerst das Fenster '3DCreator Backend' und starte repair-amd-backend.ps1 danach erneut."
}

$python = Join-Path $ComfyDir "venv\Scripts\python.exe"
$custom = Join-Path $ComfyDir "custom_nodes\ComfyUI-Trellis2-AMD"

if (-not (Test-Path $python)) {
  throw "Backend-Python fehlt. Fuehre zuerst install-amd-backend.ps1 aus."
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  throw "Git wurde nicht gefunden. Installiere Git oder starte eine neue PowerShell, falls Git gerade installiert wurde."
}

if (-not (Test-Path $custom)) {
  Write-Host "TRELLIS AMD Plugin fehlt - klone neu ..." -ForegroundColor Yellow
  Invoke-Native git clone https://github.com/dmonkman/ComfyUI-Trellis2-AMD.git $custom
} else {
  Write-Host "Aktualisiere TRELLIS AMD Plugin ..." -ForegroundColor Cyan
  Invoke-Native git -C $custom fetch origin
  Invoke-Native git -C $custom checkout main
  Invoke-Native git -C $custom pull --ff-only origin main
}

Write-Host "Aktualisiere pip ..." -ForegroundColor Cyan
Invoke-Native $python -m pip install --upgrade pip

Write-Host "Stelle TRELLIS-Abhaengigkeiten wieder her ..." -ForegroundColor Cyan
Invoke-Native $python -m pip install -r (Join-Path $custom "requirements.txt")

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
  Write-Host "Installiere $wheel neu ..." -ForegroundColor DarkCyan
  Invoke-Native $python -m pip install --force-reinstall --no-deps $path
}

Write-Host "Pruefe Python-Paketkonsistenz ..." -ForegroundColor Cyan
& $python -m pip check
if ($LASTEXITCODE -ne 0) {
  Write-Warning "pip check meldet Konflikte. Der folgende TRELLIS-Importcheck zeigt, ob sie fuer das Plugin kritisch sind."
}

Write-Host ""
Write-Host "Fuehre echten TRELLIS-Plugin-Importcheck aus ..." -ForegroundColor Cyan
& $python (Join-Path $PSScriptRoot "tools\check_trellis_import.py")
if ($LASTEXITCODE -ne 0) {
  throw "TRELLIS kann weiterhin nicht importiert werden. Kopiere die Ausgabe ab '[FEHLER] TRELLIS-Custom-Node' inklusive Traceback und sende sie mir."
}

Write-Host ""
Write-Host "TRELLIS-Plugin ist lokal importierbar." -ForegroundColor Green
Write-Host "Starte jetzt .\start.bat und pruefe danach erneut die Generation." -ForegroundColor Green
