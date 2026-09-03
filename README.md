# 3DCreator v0.2.1

Eigenstaendige lokale 3D-KI fuer Windows und AMD Radeon. Dieses Repository ist vom Desktop-Projekt `Mille` getrennt.

Aktueller Zielrechner:

- AMD Radeon RX 6800 XT, 16 GB VRAM
- Windows 11
- Python 3.12
- ROCm 10 / PyTorch ROCm
- TRELLIS.2 AMD ueber ComfyUI
- Blender fuer lokale Mesh-Reparatur

## Funktionen

- SingleView und natives TRELLIS-MultiView
- Front, Rueckseite, links und rechts explizit zuordnen
- 512- und 1024-Profile
- automatisches lokales Workflow-Setup
- RX-6800-XT-Profil mit `aule`, `flex_gemm` und `low_vram`
- lokaler 3D-Viewer
- Raw-Modell und separate `repaired.glb`
- Blender Auto-Repair
- lokale SQLite-Projekte und Feedback/Lerndaten

## Installation

PowerShell im Repository oeffnen und ausfuehren:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup-app.ps1
```

Das Setup erkennt fehlendes Python 3.12 und kann es ueber `winget` installieren.

Danach AMD/TRELLIS installieren:

```powershell
powershell -ExecutionPolicy Bypass -File .\install-amd-backend.ps1
```

Pruefen:

```powershell
.\check-system.bat
```

Backend starten:

```powershell
.\start-backend.bat
```

In einem zweiten Fenster die App starten:

```powershell
.\start.bat
```

Danach: `http://127.0.0.1:8765`

## Hinweis zu internen Namen

Einige interne Python-Paketnamen und Umgebungsvariablen heissen aktuell noch `mille3d` bzw. `MILLE_*`. Das ist nur ein technischer Altname aus dem ersten Prototyp und stellt keine Verbindung zum anderen Repository her. Eine spaetere reine Umbenennung kann separat erfolgen.
