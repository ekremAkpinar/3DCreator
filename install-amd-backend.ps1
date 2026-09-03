param([string]$ComfyDir = "$PSScriptRoot\runtime\ComfyUI")
$ErrorActionPreference = "Stop"

Write-Host "Mille 3D - TRELLIS.2 AMD Backend" -ForegroundColor Cyan
Write-Host "Ziel: RX 6800 XT / gfx1030 / Windows 11 / Python 3.12" -ForegroundColor Gray

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Git fehlt." }
if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw "Python Launcher fehlt." }

if (-not (Test-Path $ComfyDir)) {
  git clone https://github.com/comfyanonymous/ComfyUI.git $ComfyDir
}
Set-Location $ComfyDir
if (-not (Test-Path venv)) { py -3.12 -m venv venv }
$python = Join-Path $ComfyDir "venv\Scripts\python.exe"

& $python -m pip install --upgrade pip
Write-Host "Installiere ROCm 10 / PyTorch fuer gfx1030 ..."
& $python -m pip install --extra-index-url https://stable.repo.amd.com/rocm/whl-next/ `
  "torch[device-gfx1030]==2.13.0+rocm10.0.0" `
  "torchvision[device-gfx1030]==0.28.0+rocm10.0.0" `
  "torchaudio==2.11.0.2+rocm10.0.0" `
  "rocm[libraries,device-gfx1030]==10.0.0"

& $python -m pip install -r requirements.txt
$custom = Join-Path $ComfyDir "custom_nodes\ComfyUI-Trellis2-AMD"
if (-not (Test-Path $custom)) {
  git clone https://github.com/dmonkman/ComfyUI-Trellis2-AMD.git $custom
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
  if (-not (Test-Path $path)) { throw "Wheel fehlt: $path. Upstream-Repository pruefen." }
  & $python -m pip install $path
}
& $python -m pip install -r requirements.txt

Write-Host "Pruefe GPU ..." -ForegroundColor Cyan
& $python -c "import torch; print(torch.__version__, torch.version.hip, torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO GPU')"
Write-Host "Backend-Basis installiert. DINOv3-Modell und TRELLIS-Workflow gemaess Upstream-README ergaenzen." -ForegroundColor Yellow
Write-Host "Danach ComfyUI starten: $python main.py --listen 127.0.0.1 --port 8188"
