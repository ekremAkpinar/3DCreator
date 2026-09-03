@echo off
setlocal
cd /d "%~dp0"
title 3DCreator

if not exist ".venv\Scripts\python.exe" (
  echo 3DCreator App ist noch nicht eingerichtet.
  echo Starte setup-app.ps1 ...
  powershell -ExecutionPolicy Bypass -File "%~dp0setup-app.ps1" || exit /b 1
)

if not exist "runtime\ComfyUI\venv\Scripts\python.exe" (
  echo.
  echo ============================================================
  echo TRELLIS / ComfyUI Backend ist noch NICHT installiert.
  echo Das ist einmalig notwendig, bevor 3D-Modelle erzeugt werden.
  echo.
  echo Fuehre in diesem Ordner aus:
  echo powershell -ExecutionPolicy Bypass -File .\install-amd-backend.ps1
  echo.
  echo Danach reicht zukuenftig start.bat fuer App + Backend.
  echo ============================================================
  echo.
  pause
  exit /b 2
)

powershell -NoProfile -Command "try { $r=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8188/system_stats' -TimeoutSec 2; if($r.StatusCode -eq 200){exit 0}else{exit 1} } catch { exit 1 }"
if errorlevel 1 (
  echo Starte TRELLIS / ComfyUI Backend automatisch ...
  start "3DCreator Backend" cmd /k "call "%~dp0start-backend.bat""
) else (
  echo TRELLIS / ComfyUI laeuft bereits.
)

start "3DCreator" http://127.0.0.1:8765
".venv\Scripts\python.exe" -m uvicorn app:app --host 127.0.0.1 --port 8765
