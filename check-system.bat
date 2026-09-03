@echo off
setlocal
cd /d "%~dp0"
echo === 3DCreator Systemcheck ===

echo.
echo [1/5] AMD / ROCm Backend
if exist "runtime\ComfyUI\venv\Scripts\python.exe" (
  "runtime\ComfyUI\venv\Scripts\python.exe" tools\check_amd.py
) else (
  echo FEHLT: Backend ist noch nicht installiert.
  echo Einmalig ausfuehren: powershell -ExecutionPolicy Bypass -File .\install-amd-backend.ps1
)

echo.
echo [2/5] TRELLIS Plugin Import
if exist "runtime\ComfyUI\venv\Scripts\python.exe" (
  "runtime\ComfyUI\venv\Scripts\python.exe" tools\check_trellis_import.py
  if errorlevel 1 (
    echo.
    echo TRELLIS Plugin ist nicht importierbar.
    echo Reparatur: powershell -ExecutionPolicy Bypass -File .\repair-amd-backend.ps1
  )
) else (
  echo Nicht moeglich, Backend-Python fehlt.
)

echo.
echo [3/5] 3DCreator App
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import fastapi,requests; import mille3d; print('3DCreator Python:', mille3d.__version__)"
) else (
  echo FEHLT: App-Python. setup-app.ps1 zuerst ausfuehren.
)

echo.
echo [4/5] TRELLIS Workflows
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" tools\check_workflows.py
) else (
  echo Workflowcheck nicht moeglich, weil App-Python fehlt.
)

echo.
echo [5/5] Live ComfyUI Node-Registrierung
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" tools\check_comfy_nodes.py
) else (
  echo Live-Nodecheck nicht moeglich, weil App-Python fehlt.
)

echo.
pause
