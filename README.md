# 3DCreator v0.2.3 Candidate

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

Deshalb gibt es drei logische Kanaele:

- `stable`: reproduzierbar und benchmark-getestet
- `candidate`: naechste moegliche Stable-Version
- `learning`: neue Regeln, neue Modellfamilien, neue Toleranzen und experimentelle Strategien

Aktuell ist `0.2.3` ein **Candidate**. Die erste Stable-Version wird erst markiert, wenn der reale Hardware-Test auf der RX 6800 XT bestanden wurde.

Die Regeln stehen in:

- `agent.md`
- `AGENTS.md`
- `releases/release_state.json`
- `benchmarks/benchmark_suite.json`

## Modellfamilien / Startwissen

3DCreator klassifiziert neue Projekte automatisch oder ueber eine manuelle Nutzerauswahl. Das Startwissen liegt in:

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

Manuelle Klassifikationen werden als Nutzer-Ground-Truth gespeichert und sollen spaeter hoeher gewichtet werden als eine automatische Keyword-Vermutung.

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
- automatische und manuelle Modellfamilien-Klassifikation
- Stable/Candidate/Learning-Trennung
- automatischer ComfyUI-Start
- Live-Pruefung, ob die benoetigten TRELLIS-Nodes wirklich registriert sind
- Offline-Python-Importcheck fuer den TRELLIS-Custom-Node
- `repair-amd-backend.ps1` fuer `missing_node_type` und Plugin-Importfehler

## Was muss ich einmalig machen?

Die Kurzfassung steht auch in `FIRST_START.md`.

### 1. App einrichten

```powershell
powershell -ExecutionPolicy Bypass -File .\setup-app.ps1
```

### 2. AMD/TRELLIS-Backend installieren

```powershell
powershell -ExecutionPolicy Bypass -File .\install-amd-backend.ps1
```

Der Installer prueft nicht mehr nur, ob PyTorch die GPU sieht, sondern importiert danach den TRELLIS-Custom-Node mit der echten Backend-Python-Umgebung. Ein Plugin-Importfehler wird dadurch bereits bei der Installation sichtbar.

### 3. Pruefen

```powershell
.\check-system.bat
```

Der Systemcheck prueft:

1. AMD / ROCm
2. TRELLIS-Plugin-Import
3. 3DCreator App
4. Workflowprofile
5. Live-Node-Registrierung, falls ComfyUI bereits laeuft

## Fehler: `missing_node_type`

Wenn ComfyUI meldet, dass z. B. `Trellis2LoadImageWithTransparency` nicht gefunden wurde, ist ComfyUI selbst online, aber der TRELLIS-Custom-Node wurde nicht erfolgreich geladen.

Dann zuerst das Fenster `3DCreator Backend` schliessen und ausfuehren:

```powershell
powershell -ExecutionPolicy Bypass -File .\repair-amd-backend.ps1
```

Das Skript:

- aktualisiert `ComfyUI-Trellis2-AMD`
- installiert dessen Python-Abhaengigkeiten erneut
- installiert die vier AMD/ROCm-Wheels erneut
- fuehrt `pip check` aus
- importiert den TRELLIS-Custom-Node direkt
- zeigt bei einem Fehler den entscheidenden Python-Traceback

## Danach im Alltag

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
