# 3DCreator Agent

Diese Datei ist die zentrale Arbeitsanweisung fuer alle Entwicklungs- und KI-Agenten, die an 3DCreator arbeiten.

## 1. Produktziel

3DCreator ist eine lokale, kostenlose 3D-KI fuer den eigenen Windows-PC. Zielhardware ist aktuell eine AMD Radeon RX 6800 XT mit 16 GB VRAM.

Das System soll aus Referenzbildern und Anforderungen moeglichst druckbare, visuell passende 3D-Modelle erzeugen. Es soll aus Nutzerfeedback lernen, ohne dabei eine funktionierende Stable-Version durch unkontrollierte Selbstveraenderung zu verschlechtern.

## 2. Grundregel: Stable und Learning strikt trennen

3DCreator hat zwei logisch getrennte Zustaende:

### Stable

- Stable ist reproduzierbar.
- Stable veraendert seine Regeln, Modelle, Workflows und Toleranzen nicht automatisch.
- Stable nutzt nur Wissen, das freigegeben und getestet wurde.
- Ein Stable-Release muss mit einem festen Benchmark-Katalog getestet werden.
- Ein schlechter neuer Lernversuch darf Stable niemals ueberschreiben.

### Learning / Candidate

- Neue Nutzerbewertungen, Korrekturen und erfolgreiche Modelle landen zuerst im Learning-Bereich.
- Neue Regeln gelten zunaechst als `candidate`.
- Candidate-Wissen darf ausprobiert und verglichen werden.
- Erst wenn Tests mindestens gleich gut oder besser als Stable sind, darf Candidate-Wissen in Stable uebernommen werden.

Merksatz: **Lernen darf experimentell sein. Stable muss langweilig, reproduzierbar und verlaesslich sein.**

## 3. Release-Kanaele

Es sollen langfristig drei Kanaele existieren:

1. `stable` - bekannte, getestete Konfiguration
2. `candidate` - naechster Release-Kandidat
3. `learning` - experimentelle Regeln, neue Toleranzen, neue Klassen und neue Generatorstrategien

Ein Stable-Release wird versioniert, z. B. `0.3.0`, und speichert mindestens:

- App-Version
- verwendeten Generator / Modellnamen
- Modell-/Workflow-Version oder Commit
- AMD/PyTorch/ROCm-Profil
- Workflowprofile
- Blender-Reparaturregeln
- Druckbarkeitsregeln
- Taxonomie-Version
- Benchmark-Ergebnisse

## 4. Modell-Taxonomie

3DCreator darf nicht alle 3D-Modelle gleich behandeln. Vor jeder Generation soll ein Modell einer oder mehreren Familien zugeordnet werden.

Die Startdefinitionen liegen in `knowledge/model_families.json`.

Wichtige Familien:

### flexi

Gelenkige, meist print-in-place gedruckte Modelle mit vielen verbundenen Segmenten.

Typische Anforderungen:

- bewegliche Gelenke
- definierte Spalte zwischen Segmenten
- keine zusammengewachsenen Gelenke
- moeglichst supportfrei
- stabile Verbindung der Segmente
- FDM-Toleranzen haben Vorrang vor maximaler Bildtreue

### vinyl_figure / funko_style

Stilisierte Sammelfigur mit grossem Kopf, vereinfachtem Koerper und reduzierten Details.

Typische Anforderungen:

- grosser Kopf im Verhaeltnis zum Koerper
- kompakte Silhouette
- grosse, druckbare Details
- stabile Beine / Standflaeche oder Sockel
- kleine, zerbrechliche Details vermeiden

`Funko` ist hier eine Stil-/Kategoriebezeichnung des Nutzers; 3DCreator soll keine Markenlogos automatisch hinzufuegen.

### mechanical_part

Technisches Bauteil, Halter, Adapter, Gehaeuse, Ersatzteil oder funktionales Teil.

Typische Anforderungen:

- Abmessungen und Toleranzen sind wichtiger als kuenstlerische Aehnlichkeit
- parametrische/CAD-Erzeugung bevorzugen
- Bohrungen, Wandstaerken, Radien, Passungen und Steckverbindungen explizit behandeln
- keine rein generative Sculpt-Pipeline verwenden, wenn CAD sinnvoller ist

### creature_character

Organische Kreatur oder Monsterfigur, einschliesslich Pokemon-aehnlicher Modelle.

Typische Anforderungen:

- Silhouette und charakteristische Merkmale priorisieren
- Ohren, Schweife, Hoerner und duenne Gliedmassen auf Druckbarkeit pruefen
- bei Bedarf Teile trennen und Steckverbinder vorsehen
- Referenztreue aus mehreren Ansichten ist wichtig

### anime_character

Humanoide Anime-/Manga-Figur.

Typische Anforderungen:

- Gesicht, Frisur und Silhouette sind hochgewichtet
- duenne Haare, Finger, Waffen und Kleidungselemente auf Mindeststaerke pruefen
- Standpose und Schwerpunkt beachten
- grosse Figuren ggf. automatisch in druckbare Teile zerlegen

### bust

Kopf-/Schulterbueste.

Typische Anforderungen:

- Gesichtsaehnlichkeit hoch priorisieren
- Rueckseite darf vereinfacht werden, wenn keine Referenz vorhanden ist
- Sockel und Halsuebergang stabil gestalten

### statue

Nicht bewegliche Ganzkoerperfigur / Displayfigur.

Typische Anforderungen:

- Pose, Silhouette und Details priorisieren
- Stabilitaet, Standflaeche und Schwerpunkt pruefen
- optionale Teilung fuer Druckbett und Supportreduktion

### decoration

Pokebaelle, Logos, Wanddeko, Schilder, Ornamente und andere Displayobjekte.

Typische Anforderungen:

- klare Formensprache
- gut druckbare Oberflaechen
- bei Mehrfarbdruck sinnvolle Trennlinien / Einzelteile

## 5. Klassifikation vor Generation

Vor jeder Generation soll 3DCreator langfristig diese Fragen beantworten:

1. Welche Modellfamilie ist es?
2. Ist Sculpt/Generative Mesh oder CAD/parametrisch besser?
3. Soll das Modell beweglich sein?
4. Muss es funktional belastbar sein?
5. Ist FDM-Druck vorgesehen?
6. Welche Zielgroesse in mm gilt?
7. Soll es einteilig oder mehrteilig sein?
8. Welche Merkmale duerfen niemals verloren gehen?

Wenn die Klasse unsicher ist, darf das System eine wahrscheinlichste Klasse verwenden und die Unsicherheit speichern.

## 6. Lernen

Ein Lerndatensatz besteht mindestens aus:

- Modellfamilie
- Nutzeranforderung / Prompt
- Referenzbilder und Ansichten
- verwendeter Generator und Workflow
- Rohmodell
- repariertes Modell
- Druckparameter, soweit bekannt
- automatische Qualitaetswerte
- Nutzerbewertung 1-5
- Nutzerkommentar
- markierte Fehlerarten
- explizite Lernfreigabe

### Positives Beispiel

Nur wenn:

- Bewertung >= 4
- Nutzer hat `Fuer Lernen freigeben` aktiviert
- Ergebnis ist technisch nicht offensichtlich kaputt

### Negatives Beispiel

Bewertung <= 2 wird als Negativbeispiel gespeichert. Daraus darf 3DCreator lernen, welche Entscheidungen vermieden werden sollen.

### Neutral

Bewertung 3 wird gespeichert, aber weder als gutes Stable-Wissen noch als hartes Negativbeispiel verwendet.

## 7. Lernen bedeutet nicht sofort Fine-Tuning

3DCreator soll zuerst aus wiederverwendbarem Wissen lernen:

- Toleranzen
- Mindestwandstaerken
- erfolgreiche Steckverbinder
- Teilungsstrategien
- bevorzugte Generatorprofile je Modellfamilie
- typische Fehler je Modellfamilie
- erfolgreiche Reparaturstrategien
- Retrieval aehnlicher frueherer Projekte

Neurales Fine-Tuning darf erst spaeter und nur auf kuratierten Datensaetzen erfolgen. Das komplette 4B-Modell darf nicht nach jeder Generation neu trainiert werden.

## 8. Stable-Promotion

Candidate -> Stable darf nur erfolgen, wenn ein Benchmark-Lauf bestanden wurde.

Mindestens folgende Benchmark-Familien sollen spaeter enthalten sein:

- 1 Flexi-Tier
- 1 stilisierte Vinylfigur
- 1 technischer Halter / Adapter
- 1 Kreaturenfigur
- 1 Animefigur
- 1 Bueste
- 1 mehrteiliges Dekoobjekt

Bewertet werden mindestens:

- Generation erfolgreich
- Datei lesbar
- Mesh-Manifold / Watertight
- offene Kanten
- Self-Intersections soweit messbar
- Mindestwandstaerke
- Bounding Box / Zielgroesse
- Standfaehigkeit
- druckkritische duenne Teile
- visuelle Referenztreue
- Anzahl benoetigter manueller Korrekturen

Eine Candidate-Version darf Stable nur ersetzen, wenn sie keine kritische Regression verursacht.

## 9. Schutz vor Selbstverschlechterung

Niemals:

- Stable-Dateien automatisch mit Learning-Dateien ueberschreiben
- aus einer einzelnen guten Bewertung eine globale Regel machen
- schlechte/ungepruefte Modelle als positive Beispiele verwenden
- Benutzerfeedback ohne Herkunft und Modellfamilie speichern
- automatisch neue Abhaengigkeiten oder Modellversionen in Stable uebernehmen

Immer:

- neue Regeln versionieren
- Herkunft speichern
- Rollback ermoeglichen
- vorher/nachher vergleichen
- Raw-Output erhalten

## 10. Generatorstrategie

Aktueller Start:

- Organische Modelle: TRELLIS.2 AMD / ComfyUI
- Reparatur: Blender headless
- spaeter Validierung: Trimesh/Open3D/Blender
- technische Bauteile: spaeter bevorzugt CadQuery/OpenSCAD statt TRELLIS

Die Modellfamilie soll bestimmen, welcher Generator bevorzugt wird.

## 11. Hardwareprofil

Aktuelles Zielprofil:

- AMD Radeon RX 6800 XT
- 16 GB VRAM
- Windows
- Python 3.12
- ROCm/PyTorch AMD-Kompatibilitaet

512 ist das konservative Standardprofil. 1024 ist experimentell, bis es auf der Zielhardware ausreichend stabil getestet wurde.

## 12. Entwicklungsregel fuer Agenten

Bei jeder Aenderung an 3DCreator:

1. Bestehende Stable-Funktion nicht stillschweigend entfernen.
2. Migrationen fuer bestehende lokale Daten vorsehen.
3. Offline/local-first beibehalten.
4. Keine kostenpflichtige Cloud-API als Pflichtabhaengigkeit einfuehren.
5. Nutzer-Rohmodelle und Lerndaten niemals automatisch loeschen.
6. Neue Lernlogik zuerst als Candidate behandeln.
7. Dokumentation und Startskripte mit aktualisieren.
8. Fehlertexte fuer Nicht-Entwickler verstaendlich formulieren.
9. Der Nutzer soll moeglichst mit einem einzigen Startskript arbeiten koennen.
10. Stable muss jederzeit reproduzierbar und rollback-faehig bleiben.
