# 3DCreator v0.2.2 Candidate

Eigenstaendige lokale 3D-KI fuer Windows und AMD Radeon. Dieses Repository ist vom Desktop-Projekt `Mille` getrennt.

Aktueller Zielrechner:

- AMD Radeon RX 6800 XT, 16 GB VRAM
- Windows
- Python 3.12
- ROCm 10 / PyTorch ROCm
- TRELLIS.2 AMD ueber ComfyUI
- Blender fuer lokale Mesh-Reparatur

## Wichtig: Stable vs. Learning

3DCreator soll stetig lernen, aber eine funktionierende Version nicht durch neue Experimente verschlechtern.

Deshalb gibt es konzeptionell drei Kanaele:

- `stable`: reproduzierbar und benchmark-getestet
- `candidate`: naechste moegliche Stable-Version
- `learning`: neue Regeln, neue Modellfamilien, neue Toleranzen und experimentelle Strategien

Aktuell ist `0.2.2` ein **Candidate**. Die erste Stable-Version wird erst markiert, wenn der reale Hardware-Test auf der RX 6800 XT bestanden wurde.

Die Regeln stehen in:

- `agent.md`
- `AGENTS.md`
- `releases/release_state.json`

## Modellfamilien / Startwissen

3DCreator klassifiziert neue Projekte automatisch anhand von Projektname und Beschreibung. Das Startwissen liegt in:

`knowledge/model_families.json`

Aktuelle Familien:

- Flexi / Print-in-Place
- Vinyl-/Funko-Style Figur
- technisches Bauteil
- Kreatur / Pokemon-aehnliche Figur
- Anime-/Manga-Figur
- Bueste
- Statue / Displayfigur
- Deko / Displayobjekt

Die erkannte Familie wird zusammen mit dem Projekt gespeichert. Spaeter bestimmt sie unter anderem Generatorstrategie, Toleranzen, Teilung, Mindestwandstaerken und Druckbarkeitsregeln.

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
- automatische Modellfamilien-Klassifikation
- Stable/Candidate/Learning-Trennung als Release-Regel

## Was muss ich einmalig machen?

Die Kurzfassung steht auch in `FIRST_START.md`.

### 1. App einrichten

```powershell
powershell -ExecutionPolicy Bypass -File .\setup-app.ps1
```

Das Setup erkennt fehlendes Python 3.12 und kann es ueber `winget` installieren.

### 2. AMD/TRELLIS-Backend installieren

```powershell
powershell -ExecutionPolicy Bypass -File .\install-amd-backend.ps1
```

Das ist die eigentliche lokale 3D-KI. Ohne diesen einmaligen Schritt zeigt die App `ComfyUI offline` und kann kein Modell erzeugen.

### 3. Pruefen

```powershell
.\check-system.bat
```

## Danach im Alltag

Nur noch:

```powershell
.\start.bat
```

`start.bat` startet automatisch das ComfyUI/TRELLIS-Backend, falls es noch nicht laeuft, danach 3DCreator und den Browser.

App: `http://127.0.0.1:8765`

## Erster Hardware-Test

Zum Start immer:

- SingleView
- 512
- klares Frontbild
- danach Ergebnis bewerten

Erst wenn das stabil funktioniert:

1. MultiView
2. 1024
3. komplexere Modellfamilien

## Lernen

Ein Ergebnis wird nur dann als positives Lernbeispiel markiert, wenn:

- Bewertung mindestens 4/5
- `Fuer Lernen freigeben` explizit aktiviert wurde

1-2 Sterne bleiben als Negativbeispiele erhalten. Neue Lernregeln duerfen eine spaetere Stable-Konfiguration nicht automatisch ueberschreiben.

## Hinweis zu internen Namen

Einige interne Python-Paketnamen und Umgebungsvariablen heissen aktuell noch `mille3d` bzw. `MILLE_*`. Das ist nur ein technischer Altname aus dem ersten Prototyp und stellt keine Verbindung zum anderen Repository her. Diese interne Umbenennung erfolgt getrennt, damit der aktuelle Candidate nicht wegen einer kosmetischen Migration instabil wird.
