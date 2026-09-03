# 3DCreator - Was muss ich machen?

## Einmalig

### 1. App einrichten

PowerShell im 3DCreator-Ordner oeffnen:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup-app.ps1
```

### 2. AMD/TRELLIS-Backend installieren

Das ist der Teil, der die eigentliche 3D-KI auf der RX 6800 XT ausfuehrt:

```powershell
powershell -ExecutionPolicy Bypass -File .\install-amd-backend.ps1
```

Dieser Schritt kann viele Pakete und Modelle herunterladen und braucht Internet und freien Speicherplatz.

### 3. System pruefen

```powershell
.\check-system.bat
```

Wichtig ist, dass die AMD-GPU erkannt wird und die vier Workflowprofile als `[OK]` angezeigt werden.

## Danach im Alltag

Nur noch:

```powershell
.\start.bat
```

`start.bat` startet ab jetzt automatisch:

1. TRELLIS / ComfyUI Backend auf Port 8188, falls es noch nicht laeuft
2. 3DCreator auf Port 8765
3. den Browser

Wenn das Backend noch nicht installiert ist, beendet sich `start.bat` bewusst und zeigt den einmaligen Installationsbefehl an.

## Erster Test

Fuer den allerersten Test:

- SingleView
- 512
- ein klares Frontbild
- Blender Auto-Repair kann aktiviert bleiben

Erst wenn das stabil funktioniert:

1. MultiView testen
2. danach 1024 testen

## Was bedeutet `ComfyUI offline`?

Die Weboberflaeche von 3DCreator laeuft, aber der eigentliche lokale 3D-KI-Prozess auf Port 8188 ist nicht gestartet.

Ab der aktuellen Version soll `start.bat` das automatisch erledigen, sofern `install-amd-backend.ps1` vorher einmal erfolgreich durchgelaufen ist.

## `GET /favicon.ico 404`

Dieser Eintrag ist harmlos und hat nichts mit der 3D-Generation zu tun.
