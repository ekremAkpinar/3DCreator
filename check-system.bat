@echo off
setlocal
cd /d "%~dp0"
echo === Mille 3D Systemcheck ===

echo.
echo [1/3] AMD / ROCm Backend
if exist "runtime\ComfyUI\venv\Scripts\python.exe" (
  "runtime\ComfyUI\venv\Scripts\python.exe" tools\check_amd.py
) else (
  echo Backend-Python fehlt. install-amd-backend.ps1 zuerst ausfuehren.
)

echo.
echo [2/3] Mille App
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import fastapi,requests; import mille3d; print('Mille App Python:', mille3d.__version__)"
) else (
  echo App-Python fehlt. setup-app.ps1 zuerst ausfuehren.
)

echo.
echo [3/3] TRELLIS Workflows
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" tools\check_workflows.py
) else (
  echo Workflowcheck nicht moeglich, weil App-Python fehlt.
)

echo.
pause
