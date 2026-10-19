# RayCarve

**A concave faceting machine for Blender.**

RayCarve is a Blender add-on for simulating and planning gemstone faceting on a concave faceting machine. Import a stone, build a mandrel (cutting wheel), carve facets with Boolean operations using the same controls as a real machine, and keep a log of every cut.

- **Website:** <https://www.facettieren.ch>
- **Manual:** [English](MANUAL.md) · [Deutsch](MANUAL.de.md)
- **Requires:** Blender 4.5 or newer

## Features

- Import stones from **STL** or **GCS** (faceting design) files, auto-scaled to a target length
- Generate **round** and **V-groove** mandrels (slot or round wheel) with adjustable diameter, angle, width and bevel
- Machine-style controls: faceting side (pavilion/crown), index gear and index, facet angle, stone height/position, mandrel position/rotation — with live viewport preview
- **Cut table** recording each carve, exportable as a text file for use at the physical machine
- Optional live sync of the in-progress stone to an external web viewer

## Installation

1. Download `RayCarve-<version>.zip` from the website (do not unzip it).
2. In Blender open **Edit → Preferences → Get Extensions**.
3. Click **⌄** (top right) → **Install from Disk…** and select the ZIP.
4. In the 3D Viewport press `N` and open the **RayCarve** tab.

See the [manual](MANUAL.md) for a full panel reference and typical workflow.

## Repository layout

| Path | Contents |
| --- | --- |
| `__init__.py`, `*_ops.py`, `panels.py`, `properties.py`, `sync.py`, `utils.py`, `mesh_utils.py` | Add-on source |
| `blender_manifest.toml` | Extension manifest (id, version, Blender version, license) |
| `MANUAL.md`, `MANUAL.de.md` | User manual (English / German) |
| `build.cmd` | Windows build script |
| `website/` | Static GitHub Pages site (landing page, downloads, versioned manual) — see [website/README.md](website/README.md) |
| `.github/workflows/pages.yml` | Deploys `website/` to GitHub Pages |

## Building

On Windows, run:

```bat
build.cmd
```

It reads the version from `blender_manifest.toml`, builds `dist/RayCarve-<version>.zip` via `blender --command extension build`, installs it into Blender, and copies the ZIP and manuals into `website/` for publishing. Adjust the `BLENDER` path at the top of the script to match your installation.

To release a new version: bump `version` in `blender_manifest.toml`, update both manuals, run `build.cmd`, then commit and push.

## License

GPL-3.0-or-later — see [LICENSE](LICENSE).
© 2018–2026 Tobias Wüthrich, Facetierer Gilde Schweiz
