@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo 3DCreator ist noch nicht installiert. Starte setup-app.ps1 ...
  powershell -ExecutionPolicy Bypass -File "%~dp0setup-app.ps1" || exit /b 1
)
start "3DCreator" http://127.0.0.1:8765
".venv\Scripts\python.exe" -m uvicorn app:app --host 127.0.0.1 --port 8765
