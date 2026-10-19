# RayCarve — User Manual

**RayCarve** is a Blender add-on for simulating and planning gemstone faceting on a concave/cabbing faceting machine. It lets you import a stone, create mandrels (cutting wheels), carve facets using boolean operations, log every cut, and optionally sync the in-progress stone to the companion renderer **RayView** (Concave Ray Vision) for a live, ray-traced preview.

Version: 1.16.0 — Author: Tobias Wüthrich

All panels are found in the **3D Viewport → Sidebar (N-panel) → RayCarve** tab.

---

## Installation

1. Download `RayCarve-<version>.zip` — do not unzip it.
2. In Blender (4.5 or newer) open **Edit → Preferences → Get Extensions**.
3. Click **⌄** in the top-right corner, choose **Install from Disk…** and select the ZIP file.
4. In the 3D Viewport press `N` and open the **RayCarve** tab.

To update, install the new ZIP the same way and restart Blender.

---

## 1. Concept overview

RayCarve simulates faceting by cutting a 3D stone mesh with a "mandrel" mesh (the cutting wheel/tool shape) using a Boolean Difference modifier. You:

1. Import a stone (STL or GCS file).
2. Create or import a mandrel (the tool shape: round wheel or V-groove wheel).
3. Position the stone and mandrel using angle/height/position parameters that mirror a real faceting machine's controls.
4. Carve a facet (apply the boolean), repeat for each facet index around the stone.
5. Every carve is recorded as a row in the **Cut Table**, building up a full cutting log you can save to a text file (e.g., for use at the physical machine).
6. Optionally, the current stone shape is synced live to RayView as you work (see [section 5](#5-live-rendering-with-rayview)).

---

## 2. Panel reference

### 2.1 "1. Stone import"

- **Import STL file as Stone** — opens a file browser to import an `.stl` mesh as the stone. Automatically:
  - Deletes the default "Cube" if present.
  - Sets Blender's unit system to Metric / millimeters.
  - Rotates the imported mesh 90° around Z and applies the rotation.
  - Resizes the stone to the **Resize stone to length** value (below).
  - Clears any previous cut log and cut table.
- **Import GCS File** — imports a `.gcs` XML facet-description file (as exported by some faceting design tools). The raw file is also stored as a Blender text block. The facet vertices/faces are parsed, a mesh is built, and a **convex hull** is computed and rotated/scaled the same way as STL import.
- **Resize stone to length** — target length (along Y) the stone is scaled to on import or whenever this value changes.
- **Dimensions** — read-only display of the current stone's width/length/height once one is set.

### 2.2 "2. Mandrel Creation"

- **Mandrel Resolution** — number of segments/vertices used when generating round mandrels (also used as the SCREW modifier step count for the round V-mandrel).
- **Create Round Mandrel** group:
  - **Mandrel Diameter** — diameter of the cylindrical mandrel.
  - **Create Round Mandrel** — creates a cylinder (`RoundMandrel`), oriented along Y, and sets it as the active mandrel.
- **Create V-Mandrel** group:
  - **V-Mandrel Angle** — included angle of the V groove (0°–90°).
  - **V-Mandrel Diameter** — diameter of the wheel the V is cut into.
  - **V-Mandrel Width** — width of the V opening.
  - **V-Mandrel Bevel Offset** / **Bevel Segments** — rounds the tip of the V groove (and the outer rim for the round variant) to avoid an unrealistic sharp edge.
  - **Create V-Mandrel Slot** — builds a straight, prism-shaped V-groove tool (`VMandrel`), bevels its inner edge, and sets it as the active mandrel.
  - **Create V-Mandrel Round** — builds a circular wheel with the same V profile by revolving it with a Screw modifier (`VMandrelR`), cleans up resulting interior geometry/duplicate verts, and sets it as the active mandrel.

### 2.3 "3. Concave Machine Setup"

- **Stone** / **Mandrel** — object pickers to (re)select which scene objects act as the stone and the mandrel, in case you want to point to a different mesh than the one auto-assigned.
- **Index gear** — the number of index positions on the machine's dop/index head (e.g., 96). All facet "index" values are taken modulo this number.

### 2.4 "4. Carve"

Only active once both Stone and Mandrel are set. Mirrors the controls of a physical concave faceting machine:

- **Faceting side** — Pavillion or Crown. Determines which way the stone is flipped (rotation around X: 0° for Pavillion, 180° for Crown) before cutting.
- **Index** — the current index-wheel position (0…Index gear). Determines the stone's rotation around Z for this facet.
- **Facet angle** — the cutting angle of this facet (0°–90°).
- **Stone height** — vertical offset of the stone relative to the mandrel.
- **Stone position** — offset of the stone along its facing axis.
- **Mandrel position** — offset of the mandrel.
- **Mandrel rotation** — fine rotation adjustment of the mandrel around Z (-90°…90°), useful for V-mandrel alignment.

Changing **Index**, **Facet angle**, **Stone height/position**, **Mandrel position/rotation**, or **Faceting side** immediately repositions the stone and mandrel in the viewport (live preview), via the internal `setStoneAngles` transform.

Commands:
- **Carve** (`object.concave_boolean`) — adds a non-destructive Boolean Difference modifier (`ConcaveBoolean`, Manifold solver, Self-intersection enabled) to the stone using the mandrel, and hides the mandrel. Lets you preview the cut before committing.
- **Cancel** — removes the ConcaveBoolean modifier and shows the mandrel again, discarding the preview.
- **Apply** (only shown once a Carve preview exists) — permanently applies the boolean modifier to the stone mesh, recalculates normals on stone and mandrel, adds a row to the **Cut Table**, backs up the pre-cut stone, and writes an entry to the cut log.
- **Show/Hide Mandrel** — toggles mandrel visibility in the viewport.

### 2.5 "Carve Row" (batch cutting)

For cutting several index positions in one symmetric pattern in a single action:

- **Symmetry** — number of equally spaced repeats of the current index around the full index-gear circle (e.g., symmetry 3 on a 96-gear repeats the cut every 32 indices).
- **Mirror** — additionally mirrors each symmetric index by ± this many gear steps (useful for facets that come in symmetric left/right pairs).
- **Row: ex: 6-12-18** — a manually editable, dash-separated list of index positions that will be cut in this batch; it is auto-recalculated whenever Index/Symmetry/Mirror change, but can also be typed/edited directly.
- **Carve all** (`object.concave_batch`) — backs up the stone, then carves and applies the boolean **for every index in the Row list**, in one go (no preview step). Adds a single Cut Table row covering the whole batch.

### 2.6 "Cut Table"

A persistent, editable spreadsheet-like log of every cut/batch performed on the current stone, with one row per **Apply** (single) or **Carve all** (batch) action. Columns:

| Column | Meaning |
|---|---|
| Name | Editable row label |
| (checkbox) | **Disable** — exclude this row from a "Redo cutting" replay |
| Side | `P` (Pavillion) or `C` (Crown) |
| Facet angle | Angle used for this cut |
| Indices | Index or dash-separated batch indices cut |
| Comment | Free-text notes field |
| Tool | The mandrel object used |
| Stone height / Stone position | Stone offsets used |
| Mandrel position / Mandrel rotation | Mandrel offsets used |

Toolbar buttons (right of the list):
- **+ / Add Row** — manually add a blank row (e.g., for documentation purposes).
- **− / Remove Row** — delete the selected row.
- **Redo cutting** (refresh icon) — replays the *entire* cut table from scratch: restores the backed-up original stone (`<stone>_bak`), then re-applies every non-disabled row in order with its saved parameters. Use this to regenerate the stone after editing earlier rows, or after closing/reopening the file. Rows with **Disable** checked are skipped, letting you test "what if I hadn't cut this facet".

### 2.7 "5. Save instructions"

- **Save cut instructions** — opens Blender's text editor save dialog to export the `concaveLog.txt` text block (the running plain-text cut log, distinct from the Cut Table) to disk — handy for printing instructions to follow at the physical machine.

The log (`concaveLog.txt`, auto-created on first cut) contains a header (stone name & dimensions, mandrel name & dimensions, index gear) followed by one block per cut/batch with side, index(es), facet angle, stone height, stone/mandrel position, and mandrel rotation — all in human-readable units/degrees.

### 2.8 "Troubleshoot" (collapsed by default)

For fixing mesh issues that can arise from repeated boolean operations:

- **Fix Boolean** (`object.recalculate_normals`) — recalculates outward-facing normals on both stone and mandrel (temporarily un-hides the mandrel if needed). Use this if a carve produces inverted/black faces.
- **Fix Mesh** (`object.merge_by_distance`) — runs "Merge by Distance" (remove doubles) on the stone mesh. Use this if booleans start failing or produce non-manifold geometry from duplicate vertices.

### 2.9 "Render synchronisation" (collapsed by default)

Optionally streams the current stone mesh to an external renderer/viewer over HTTP, useful for a live WebGL preview while you work.

- **Auto. sync. enabled** — when on, every modifier update on the `ConcaveBoolean` modifier automatically triggers a background export+upload (debounced by comparing object state so unchanged states aren't re-sent).
- **Synchronisation Status** — shows `Ok`, an in-progress message, or an error if the last upload failed (auto-sync disables itself on failure).
- **Manual sync to web** — forces an immediate export+upload regardless of whether anything changed.

Mechanically: the addon exports the visible stone (with modifiers applied) as a binary STL to a temporary file, then `POST`s it as multipart form data to `http://localhost:3000/upload` along with the object's name, rotation (Euler X/Y/Z and tuple), and position. This requires a local server listening on port 3000 that accepts this upload format — RayCarve itself does not provide that server; it is provided by **RayView** (see [section 5](#5-live-rendering-with-rayview)). If the request fails (e.g., no server running), the status field shows an error and auto-sync turns itself off.

---

## 3. Typical workflow

1. **Stone import →** Import STL (or GCS) to load your rough stone shape; set the target length.
2. **Mandrel Creation →** create a Round Mandrel or V-Mandrel matching your physical tool.
3. **Machine Setup →** confirm Stone/Mandrel pointers and set your Index gear to match your machine's dop head.
4. **Carve →** pick Pavillion or Crown, set Index, Facet angle, and the height/position offsets exactly as you'd dial them in on the real machine. Click **Carve** to preview, adjust if needed, then **Apply** to commit. Repeat for each facet.
   - For facets that repeat around the stone (e.g., 8 mains), use **Carve Row** with Symmetry/Mirror to cut them all in one **Carve all**.
5. Watch the **Cut Table** fill up — this is your master record. Disable/re-enable rows and use **Redo cutting** to regenerate the result if you change earlier parameters.
6. **Save instructions →** export the plain-text cut log to take to the machine.
7. (Optional) Enable **Render synchronisation** with RayView running, to see your progress live as a ray-traced gemstone.

---

## 4. Tips & troubleshooting

- If a boolean cut leaves dark/inverted faces, run **Fix Boolean** (Troubleshoot panel).
- If subsequent cuts start failing or producing garbled geometry, run **Fix Mesh** to merge duplicate vertices first.
- The "backup" stone (`<stone>_bak` in the hidden `rayCarveBackup` collection) is created automatically on your first Apply/Carve-all and is what **Redo cutting** restores from — don't delete it if you want to keep replay capability.
- All units are millimeters/degrees; importing a stone automatically switches the scene to Metric/mm.
- The Boolean modifier uses the "Manifold" solver — if you have a non-manifold mandrel or stone, cuts may fail or look wrong; check geometry with Blender's mesh analysis tools if so.

---

## 5. Live rendering with RayView

**RayView** (Concave Ray Vision) is the companion renderer to RayCarve, also developed by the Facettierer Gilde Schweiz. It ray-traces light through the stone in real time — multiple internal bounces, refractive index (IOR), dispersion and Fresnel reflections — against HDRI or skybox environments. Together with RayCarve's **Render synchronisation** it shows how the stone you're cutting will actually sparkle, updated after every cut.

Source code and releases: <https://github.com/facettierergilde/rayview>

### 5.1 Download & installation (Windows)

1. Open the latest release: <https://github.com/facettierergilde/rayview/releases/latest>
2. Under **Assets**, download `ConcaveRayVision-v<version>-win-x64.zip` (at the time of writing: [v1.0.0](https://github.com/facettierergilde/rayview/releases/download/v1.0.0/ConcaveRayVision-v1.0.0-win-x64.zip)).
3. Unzip it into a folder of your choice (e.g. `C:\Programs\ConcaveRayVision`).
4. Start `concaverayvision.exe`. The sync server for RayCarve starts automatically with the app.

Windows may show a SmartScreen warning the first time, because the app is not code-signed: click **More info → Run anyway**. If the Windows firewall asks, allow access for private networks (the app only listens locally on ports 3000 and 3001).

On macOS/Linux, or to run the latest development version, RayView can be started from source with [Node.js](https://nodejs.org) 22+: clone the repository, run `npm install`, then `npm run dev` (viewer at <http://localhost:5173>) and, in a second terminal, `npm run server` (sync server). See the RayView README for details.

### 5.2 Using RayView with RayCarve

1. Start **RayView** first.
2. In Blender, import a stone in RayCarve as usual.
3. Open the **Render synchronisation** panel (section 2.9) and click **Manual sync to web**. The status should read `Ok` and the stone appears in RayView.
4. Enable **Auto. sync. enabled**. From now on every change (preview carve, applied cut, changed angle/index) is sent to RayView automatically.
5. In RayView, adjust the look: refractive index and colour of the gem material, number of bounces, dispersion, environment (HDRI/skybox), exposure, camera presets and turntable animation.

How it works: RayCarve exports the stone as STL and posts it to `http://localhost:3000/upload`; RayView's sync server receives it and pushes it over a WebSocket (port 3001) to the viewer, which reloads the model immediately.

### 5.3 Troubleshooting

- **Status shows "Syncronisation failed and therefore disabled!"** — RayView was not running (or not yet started) when RayCarve tried to send. Start RayView, then click **Manual sync to web** and re-enable auto-sync.
- **Nothing updates in RayView** — make sure no other program uses ports 3000/3001 and that the firewall allows the app.
- **Stone looks wrong (dark/inverted)** — run **Fix Boolean** / **Fix Mesh** in RayCarve's Troubleshoot panel and sync again.
- RayView can also be used on its own: it loads GLB, GLTF, STL and OBJ models directly.
