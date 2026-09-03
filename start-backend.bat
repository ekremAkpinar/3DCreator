@echo off
setlocal
title 3DCreator Backend
set "COMFY=%~dp0runtime\ComfyUI"
if not exist "%COMFY%\venv\Scripts\python.exe" (
  echo TRELLIS / ComfyUI Backend ist noch nicht installiert.
  echo Einmalig ausfuehren:
  echo powershell -ExecutionPolicy Bypass -File .\install-amd-backend.ps1
  exit /b 1
)
cd /d "%COMFY%"
"venv\Scripts\python.exe" main.py --listen 127.0.0.1 --port 8188
