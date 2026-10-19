# RayCarve — Benutzerhandbuch

**RayCarve** ist eine Blender-Erweiterung zum Simulieren und Planen von Edelsteinschliffen auf einer Konkav-Facettiermaschine. Du kannst damit einen Stein importieren, Walzen (Schleifwerkzeuge) erzeugen, Facetten mit Boolean-Operationen schleifen, jeden Schnitt protokollieren und den Stein optional live an den Begleit-Renderer **RayView** (Concave Ray Vision) senden, der ihn in Echtzeit raytracet.

Version: 1.16.0 — Autor: Tobias Wüthrich

Alle Panels findest du unter **3D Viewport → Sidebar (N-Panel) → RayCarve**. Die Bedienelemente in Blender sind englisch beschriftet; im Handbuch stehen die Originalbezeichnungen jeweils **fett**.

---

## Installation

1. `RayCarve-<version>.zip` herunterladen — die Datei nicht entpacken.
2. In Blender (4.5 oder neuer) **Edit → Preferences → Get Extensions** öffnen (Bearbeiten → Einstellungen).
3. Oben rechts auf **⌄** klicken, **Install from Disk…** wählen und die ZIP-Datei auswählen.
4. In der 3D-Ansicht `N` drücken und den Reiter **RayCarve** öffnen.

Für ein Update die neue ZIP-Datei gleich installieren und Blender neu starten.

---

## 1. Grundprinzip

RayCarve simuliert das Facettieren, indem ein 3D-Steinmodell mit einem Walzenmodell (Form der Schleifscheibe bzw. des Werkzeugs) über einen Boolean-Difference-Modifier geschnitten wird. Der Ablauf:

1. Stein importieren (STL- oder GCS-Datei).
2. Walze erzeugen oder importieren (Werkzeugform: runde Walze oder V-Walze).
3. Stein und Walze über Winkel, Höhe und Position ausrichten — genau wie mit den Einstellungen an einer echten Facettiermaschine.
4. Facette schleifen (Boolean übernehmen) und für jede Indexposition rund um den Stein wiederholen.
5. Jeder Schnitt wird als Zeile in der **Cut Table** (Schleiftabelle) gespeichert. So entsteht ein vollständiges Schleifprotokoll, das du als Textdatei speichern kannst (z. B. für die Arbeit an der Maschine).
6. Optional wird die aktuelle Steinform während der Arbeit live an RayView übertragen (siehe [Abschnitt 5](#5-live-rendering-mit-rayview)).

---

## 2. Die Panels im Detail

### 2.1 „1. Stone import"

- **Import GCS File** — importiert eine `.gcs`-XML-Datei mit einer Facettenbeschreibung (wie sie einige Facetten-Designprogramme exportieren). Die Originaldatei wird zusätzlich als Blender-Textblock abgelegt, benannt wie die Datei inklusive Endung (z. B. `MeinStein.gcs`). Aus den Facetten wird ein Mesh aufgebaut, daraus eine **konvexe Hülle** berechnet und wie beim STL-Import gedreht und skaliert.
- **Import STL file as Stone** — öffnet einen Dateidialog, um ein `.stl`-Modell als Stein zu importieren. Eine Kopie der Datei wird als Textblock mit dem Dateinamen abgelegt (z. B. `MeinStein.stl`); binäre STL-Dateien werden dabei als gleichwertige ASCII-STL gespeichert. Dabei wird automatisch:
  - der Standard-„Cube" gelöscht, falls vorhanden;
  - das Einheitensystem von Blender auf Metrisch / Millimeter gestellt;
  - das Modell um 90° um die Z-Achse gedreht und die Drehung übernommen;
  - der Stein auf den Wert **Resize stone to length** (siehe unten) skaliert;
  - der neue Stein mit leerem Schleifprotokoll und leerer Schleiftabelle angelegt (andere Steine in der Datei behalten ihre).
- **Resize stone to length** — Ziel-Länge (entlang Y), auf die der Stein beim Import oder bei jeder Änderung dieses Werts skaliert wird.
- **Dimensions** — zeigt Breite, Länge und Höhe des aktuellen Steins an (nur Anzeige).

### 2.2 „2. Mandrel Creation"

- **Mandrel Resolution** — Anzahl Segmente bzw. Punkte für runde Walzen (wird auch als Schrittzahl des SCREW-Modifiers für die runde V-Walze verwendet).
- Gruppe **Create Round Mandrel**:
  - **Mandrel Diameter** — Durchmesser der zylindrischen Walze.
  - **Create Round Mandrel** — erzeugt einen Zylinder (`RoundMandrel`) entlang Y und setzt ihn als aktive Walze.
- Gruppe **Create V-Mandrel**:
  - **V-Mandrel Angle** — Öffnungswinkel der V-Nut (0°–90°).
  - **V-Mandrel Diameter** — Durchmesser der Scheibe, in die das V geschnitten ist.
  - **V-Mandrel Width** — Breite der V-Öffnung.
  - **V-Mandrel Bevel Offset** / **Bevel Segments** — rundet die Spitze der V-Nut (bei der runden Variante auch den äusseren Rand) ab, damit keine unrealistisch scharfe Kante entsteht.
  - **Create V-Mandrel Slot** — erzeugt ein gerades, prismenförmiges V-Werkzeug (`VMandrel`), rundet die Innenkante ab und setzt es als aktive Walze.
  - **Create V-Mandrel Round** — erzeugt eine runde Scheibe mit demselben V-Profil, indem das Profil mit einem Screw-Modifier gedreht wird (`VMandrelR`). Innere Geometrie und doppelte Punkte werden bereinigt, danach wird die Scheibe als aktive Walze gesetzt.

### 2.3 „3. Concave Machine Setup"

- **Stone** / **Mandrel** — Objektauswahl, um festzulegen, welche Objekte der Szene als Stein und als Walze dienen — falls du ein anderes Mesh verwenden willst als das automatisch zugewiesene. Wird hier ein anderer Stein gewählt, wechselt RayCarve zu diesem Stein (siehe *Mit mehreren Steinen arbeiten*).

#### Mit mehreren Steinen arbeiten

Eine `.blend`-Datei kann mehrere Steine enthalten. Jeder Stein hat seine eigene **Schleiftabelle**, sein eigenes Schleifprotokoll (`<Stein>_concaveLog.txt`), seine importierte GCS-/STL-Datei und seine eigenen Maschineneinstellungen (Indexrad, Seite, Index, Facettenwinkel, Steinhöhe/-position, Walze und Walzenposition/-drehung, Symmetrie, Spiegelung, Steinlänge). Wählst du im Feld **Stone** einen anderen Stein:

- werden die Einstellungen des bisherigen Steins gemerkt und die des neu gewählten wiederhergestellt;
- zeigt das Panel Cut Table die Schnitte des neuen Steins;
- werden alle anderen Steine ausgeblendet, sodass nur der aktive sichtbar ist.

Ein weiterer importierter Stein wird ebenso zur Datei hinzugefügt; du kannst jederzeit zu früheren Steinen zurückwechseln. Dateien aus Versionen vor 1.18.0 werden beim Öffnen automatisch umgestellt: Ihre Schleiftabelle wird dem ausgewählten Stein zugeordnet.
- **Index gear** — Anzahl Indexpositionen am Teilkopf der Maschine (z. B. 96). Alle Indexwerte werden modulo dieser Zahl gerechnet.

### 2.4 „4. Carve"

Nur aktiv, wenn sowohl Stein als auch Walze gesetzt sind. Die Einstellungen entsprechen denen einer echten Konkav-Facettiermaschine:

- **Faceting side** — Pavillon oder Krone. Bestimmt, wie der Stein vor dem Schnitt gedreht wird (Drehung um X: 0° für Pavillon, 180° für Krone).
- **Index** — aktuelle Position des Indexrads (0…Index gear). Bestimmt die Drehung des Steins um Z für diese Facette.
- **Facet angle** — Schleifwinkel dieser Facette (0°–90°).
- **Stone height** — vertikaler Versatz des Steins zur Walze.
- **Stone position** — Versatz des Steins entlang seiner Ausrichtungsachse.
- **Mandrel position** — Versatz der Walze.
- **Mandrel rotation** — Feinjustierung der Walzendrehung um Z (-90°…90°), nützlich zum Ausrichten einer V-Walze.

Jede Änderung von **Index**, **Facet angle**, **Stone height/position**, **Mandrel position/rotation** oder **Faceting side** positioniert Stein und Walze sofort neu in der 3D-Ansicht (Live-Vorschau, über die interne Transformation `setStoneAngles`).

Befehle:

- **Carve** (`object.concave_boolean`) — fügt dem Stein einen nicht-destruktiven Boolean-Difference-Modifier (`ConcaveBoolean`, Manifold-Solver, Self-Intersection aktiv) mit der Walze hinzu und blendet die Walze aus. So siehst du den Schnitt, bevor du ihn übernimmst.
- **Cancel** — entfernt den ConcaveBoolean-Modifier, blendet die Walze wieder ein und verwirft die Vorschau.
- **Apply** (erscheint erst, wenn eine Carve-Vorschau existiert) — übernimmt den Boolean-Modifier endgültig ins Stein-Mesh, berechnet die Normalen von Stein und Walze neu, fügt eine Zeile zur **Cut Table** hinzu, sichert den Stein vor dem Schnitt und schreibt einen Eintrag ins Schleifprotokoll.
- **Show/Hide Mandrel** — blendet die Walze in der 3D-Ansicht ein oder aus.

### 2.5 „Carve Row" (Reihen schleifen)

Um mehrere Indexpositionen eines symmetrischen Musters in einem Schritt zu schleifen:

- **Symmetry** — Anzahl gleichmässig verteilter Wiederholungen des aktuellen Index über den ganzen Indexkreis (z. B. Symmetrie 3 bei einem 96er-Rad wiederholt den Schnitt alle 32 Positionen).
- **Mirror** — spiegelt jeden symmetrischen Index zusätzlich um ± so viele Zahnschritte (nützlich für Facetten, die als linkes/rechtes Paar auftreten).
- **Row: ex: 6-12-18** — frei editierbare, mit Bindestrichen getrennte Liste der Indexpositionen, die in diesem Durchgang geschliffen werden. Sie wird bei jeder Änderung von Index, Symmetry oder Mirror neu berechnet, kann aber auch direkt eingegeben oder angepasst werden.
- **Carve all** (`object.concave_batch`) — sichert den Stein und schleift dann **jede Indexposition der Row-Liste** in einem Durchgang (ohne Vorschau). Für die ganze Reihe wird eine einzige Zeile in der Cut Table angelegt.

### 2.6 „Cut Table"

Eine gespeicherte, editierbare Tabelle aller Schnitte am aktuellen Stein (jeder Stein hat seine eigene Tabelle, die mit ihm gespeichert wird) — eine Zeile pro **Apply** (Einzelschnitt) oder **Carve all** (Reihe). Spalten:

| Spalte | Bedeutung |
|---|---|
| Name | Frei wählbare Bezeichnung der Zeile |
| (Checkbox) | **Disable** — Zeile beim „Redo cutting" überspringen |
| Side | `P` (Pavillon) oder `C` (Krone) |
| Facet angle | Verwendeter Schleifwinkel |
| Indices | Index bzw. mit Bindestrichen getrennte Indexliste |
| Comment | Freies Notizfeld |
| Tool | Verwendete Walze |
| Stone height / Stone position | Verwendete Steinversätze |
| Mandrel position / Mandrel rotation | Verwendete Walzenversätze |

Schaltflächen rechts neben der Liste:

- **+ / Add Row** — fügt eine leere Zeile hinzu (z. B. zur Dokumentation).
- **− / Remove Row** — löscht die ausgewählte Zeile.
- **Redo cutting** (Pfeil-Symbol) — spielt die *gesamte* Schleiftabelle von vorne ab: Der gesicherte Originalstein (`<stein>_bak`) wird wiederhergestellt und danach jede nicht deaktivierte Zeile der Reihe nach mit ihren gespeicherten Werten geschliffen. Damit lässt sich der Stein neu erzeugen, nachdem du frühere Zeilen geändert hast oder die Datei neu geöffnet wurde. Zeilen mit **Disable** werden übersprungen — so kannst du testen, wie der Stein ohne eine bestimmte Facette aussähe.

### 2.7 „5. Save instructions"

- **Save cut instructions** — öffnet den Speicherdialog des Blender-Texteditors, um den Textblock `<Steinname>_concaveLog.txt` des aktuellen Steins (das fortlaufende Schleifprotokoll als Text, unabhängig von der Cut Table) zu speichern — praktisch, um die Anleitung für die Arbeit an der Maschine auszudrucken.
- **Export GCS file** / **Export STL file** — speichert die ursprüngliche GCS- bzw. STL-Datei, aus der der aktuelle Stein importiert wurde. Es erscheint nur der Knopf für den tatsächlich importierten Dateityp; wurde der Stein nicht aus einer Datei importiert (oder der Textblock gelöscht), erscheint keiner.

Das Protokoll (`<Steinname>_concaveLog.txt`, z. B. `Stone_concaveLog.txt`, wird beim ersten Schnitt automatisch angelegt) wird pro Stein geführt, sodass ein zweiter geladener Stein das Protokoll des ersten weder vermischt noch überschreibt. Es enthält einen Kopf (Name und Masse von Stein und Walze, Indexrad) und danach pro Schnitt bzw. Reihe einen Block mit Seite, Index(en), Facettenwinkel, Steinhöhe, Stein- und Walzenposition sowie Walzendrehung — alles in gut lesbaren Einheiten und Grad.

### 2.8 „Troubleshoot" (standardmässig eingeklappt)

Zum Beheben von Mesh-Problemen, die nach vielen Boolean-Operationen auftreten können:

- **Fix Boolean** (`object.recalculate_normals`) — berechnet die nach aussen zeigenden Normalen von Stein und Walze neu (blendet die Walze dafür bei Bedarf kurz ein). Hilft, wenn ein Schnitt umgedrehte oder schwarze Flächen erzeugt.
- **Fix Mesh** (`object.merge_by_distance`) — führt „Merge by Distance" (doppelte Punkte entfernen) am Stein-Mesh aus. Hilft, wenn Boolean-Schnitte fehlschlagen oder durch doppelte Punkte nicht-mannigfaltige Geometrie entsteht.

### 2.9 „Render synchronisation" (standardmässig eingeklappt)

Überträgt das aktuelle Stein-Mesh optional per HTTP an einen externen Renderer oder Viewer — nützlich für eine Live-WebGL-Vorschau während der Arbeit.

- **Auto. sync. enabled** — ist die Option aktiv, löst jede Änderung am `ConcaveBoolean`-Modifier automatisch einen Export und Upload im Hintergrund aus (unveränderte Zustände werden nicht erneut gesendet).
- **Synchronisation Status** — zeigt `Ok`, eine Fortschrittsmeldung oder einen Fehler, falls der letzte Upload fehlgeschlagen ist (bei einem Fehler schaltet sich die automatische Synchronisation ab).
- **Manual sync to web** — erzwingt sofort einen Export und Upload, auch wenn sich nichts geändert hat.

Technisch exportiert die Erweiterung den sichtbaren Stein (mit angewendeten Modifiern) als binäre STL in eine temporäre Datei und sendet sie per `POST` als Multipart-Formular an `http://localhost:3000/upload` — zusammen mit Objektname, Drehung (Euler X/Y/Z und als Tupel) und Position. Dafür muss ein lokaler Server auf Port 3000 laufen, der dieses Upload-Format annimmt; RayCarve selbst stellt diesen Server nicht bereit; das übernimmt **RayView** (siehe [Abschnitt 5](#5-live-rendering-mit-rayview)). Schlägt die Anfrage fehl (z. B. weil kein Server läuft), zeigt das Statusfeld einen Fehler und die automatische Synchronisation schaltet sich ab.

---

## 3. Typischer Ablauf

1. **Stone import →** STL (oder GCS) importieren, um den Rohstein zu laden; Ziel-Länge einstellen.
2. **Mandrel Creation →** runde Walze oder V-Walze passend zu deinem echten Werkzeug erzeugen.
3. **Machine Setup →** Stein und Walze prüfen und das Indexrad passend zum Teilkopf deiner Maschine einstellen.
4. **Carve →** Pavillon oder Krone wählen, Index, Facettenwinkel sowie Höhe und Positionen genau so einstellen wie an der echten Maschine. Mit **Carve** die Vorschau anzeigen, bei Bedarf anpassen und mit **Apply** übernehmen. Für jede Facette wiederholen.
   - Für Facetten, die sich rund um den Stein wiederholen (z. B. 8 Hauptfacetten), mit **Carve Row** und Symmetry/Mirror alle in einem **Carve all** schleifen.
5. Die **Cut Table** füllt sich dabei — sie ist dein Hauptprotokoll. Zeilen deaktivieren oder wieder aktivieren und mit **Redo cutting** das Ergebnis neu berechnen, wenn du frühere Werte änderst.
6. **Save instructions →** das Schleifprotokoll als Text für die Maschine exportieren.
7. (Optional) **Render synchronisation** aktivieren, während RayView läuft, um den Fortschritt live als geraytraceten Edelstein zu sehen.

---

## 4. Tipps & Fehlerbehebung

- Hinterlässt ein Schnitt dunkle oder umgedrehte Flächen, **Fix Boolean** (Panel Troubleshoot) ausführen.
- Schlagen weitere Schnitte fehl oder entsteht zerfranste Geometrie, zuerst mit **Fix Mesh** doppelte Punkte zusammenführen.
- Der Sicherungsstein (`<stein>_bak` in der ausgeblendeten Collection `rayCarveBackup`) wird beim ersten Apply bzw. Carve all automatisch angelegt. **Redo cutting** stellt den Stein daraus wieder her — nicht löschen, wenn du die Schnitte später neu abspielen möchtest.
- Alle Einheiten sind Millimeter und Grad; beim Import eines Steins wird die Szene automatisch auf Metrisch/mm umgestellt.
- Der Boolean-Modifier verwendet den „Manifold"-Solver — ist Stein oder Walze nicht mannigfaltig (non-manifold), können Schnitte fehlschlagen oder falsch aussehen. Prüfe die Geometrie in diesem Fall mit den Mesh-Analyse-Werkzeugen von Blender.

---

## 5. Live-Rendering mit RayView

**RayView** (Concave Ray Vision) ist der Begleit-Renderer zu RayCarve und wird ebenfalls von der Facettierergilde Schweiz entwickelt. Er verfolgt das Licht in Echtzeit durch den Stein — mit mehrfachen inneren Reflexionen, Brechungsindex (IOR), Dispersion und Fresnel-Reflexion — vor HDRI- oder Skybox-Umgebungen. Zusammen mit der **Render synchronisation** von RayCarve siehst du nach jedem Schnitt, wie der Stein tatsächlich funkeln wird.

Quellcode und Releases: <https://github.com/facettierergilde/rayview>

### 5.1 Download & Installation (Windows)

1. Die neueste Version öffnen: <https://github.com/facettierergilde/rayview/releases/latest>
2. Unter **Assets** die Datei `ConcaveRayVision-v<version>-win-x64.zip` herunterladen (aktuell: [v1.0.0](https://github.com/facettierergilde/rayview/releases/download/v1.0.0/ConcaveRayVision-v1.0.0-win-x64.zip)).
3. In einen beliebigen Ordner entpacken (z. B. `C:\Programme\ConcaveRayVision`).
4. `concaverayvision.exe` starten. Der Sync-Server für RayCarve startet automatisch mit.

Beim ersten Start kann Windows eine SmartScreen-Warnung anzeigen, da die App nicht signiert ist: **Weitere Informationen → Trotzdem ausführen** wählen. Fragt die Windows-Firewall nach, den Zugriff für private Netzwerke erlauben (die App lauscht nur lokal auf den Ports 3000 und 3001).

Unter macOS/Linux oder für die neueste Entwicklungsversion lässt sich RayView mit [Node.js](https://nodejs.org) 22+ aus dem Quellcode starten: Repository klonen, `npm install`, dann `npm run dev` (Viewer unter <http://localhost:5173>) und in einem zweiten Terminal `npm run server` (Sync-Server). Details im README von RayView.

### 5.2 RayView zusammen mit RayCarve verwenden

1. Zuerst **RayView** starten.
2. In Blender wie gewohnt einen Stein in RayCarve importieren.
3. Das Panel **Render synchronisation** (Abschnitt 2.9) öffnen und auf **Manual sync to web** klicken. Der Status zeigt `Ok`, und der Stein erscheint in RayView.
4. **Auto. sync. enabled** aktivieren. Ab jetzt wird jede Änderung (Vorschau-Schnitt, übernommener Schnitt, geänderter Winkel/Index) automatisch an RayView gesendet.
5. In RayView das Aussehen anpassen: Brechungsindex und Farbe des Steins, Anzahl Reflexionen, Dispersion, Umgebung (HDRI/Skybox), Belichtung, Kamera-Voreinstellungen und Drehteller-Animation.

Funktionsweise: RayCarve exportiert den Stein als STL und sendet ihn an `http://localhost:3000/upload`; der Sync-Server von RayView empfängt ihn und leitet ihn per WebSocket (Port 3001) an den Viewer weiter, der das Modell sofort neu lädt.

### 5.3 Fehlerbehebung

- **Status zeigt „Syncronisation failed and therefore disabled!"** — RayView lief nicht (oder noch nicht), als RayCarve senden wollte. RayView starten, dann **Manual sync to web** klicken und die automatische Synchronisation wieder aktivieren.
- **In RayView ändert sich nichts** — prüfen, dass kein anderes Programm die Ports 3000/3001 belegt und die Firewall die App zulässt.
- **Stein sieht falsch aus (dunkel/umgedreht)** — im Troubleshoot-Panel von RayCarve **Fix Boolean** bzw. **Fix Mesh** ausführen und erneut synchronisieren.
- RayView lässt sich auch eigenständig nutzen: Es lädt GLB-, GLTF-, STL- und OBJ-Modelle direkt.
