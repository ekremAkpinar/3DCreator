@echo off
setlocal
set "COMFY=%~dp0runtime\ComfyUI"
if not exist "%COMFY%\venv\Scripts\python.exe" (
  echo TRELLIS/ComfyUI Backend ist noch nicht installiert.
  echo Starte zuerst install-amd-backend.ps1
  exit /b 1
)
cd /d "%COMFY%"
"venv\Scripts\python.exe" main.py --listen 127.0.0.1 --port 8188
