# RayCarve website

Static site for GitHub Pages: landing page (`index.html`) and a versioned manual (`manual/`) in German and English. No build step or dependencies.

```
website/
├─ index.html              landing page (DE/EN)
├─ versions.json           released versions – single source of truth
├─ downloads/              RayCarve-<version>.zip
├─ manual/
│  ├─ index.html           manual viewer (?v=1.16.0&lang=de)
│  └─ <version>/en.md, de.md
└─ assets/                 style.css, site.js, manual.js, gem.svg
```

## Releasing a new version

1. Bump `version` in `blender_manifest.toml`, update `MANUAL.md` (English) and `MANUAL.de.md` (German).
2. Run `build.cmd`. Besides building and installing the extension, it:
   - copies the zip to `website/downloads/`,
   - copies the manuals to `website/manual/<version>/en.md` and `de.md`,
   - adds the version to `versions.json` and marks the newest as `latest`.
3. Commit and push the `website` folder.

Older manual versions stay online and can be picked in the version menu.

## Publishing on GitHub Pages

GitHub Pages can only publish the repository root or a `/docs` folder directly. Two options:

**A – own repository (simplest):** create a repo (e.g. `raycarve`), put the *contents* of this folder in its root, push, then *Settings → Pages → Deploy from a branch → main / (root)*.

**B – keep it in the plugin repository:** add `.github/workflows/pages.yml` in the repo root and set *Settings → Pages → Source: GitHub Actions*:

```yaml
name: Deploy website
on:
  push:
    branches: [main]
    paths: ["website/**"]
  workflow_dispatch:
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: { name: github-pages, url: "${{ steps.deploy.outputs.page_url }}" }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/upload-pages-artifact@v3
        with: { path: website }
      - id: deploy
        uses: actions/deploy-pages@v4
```

## Local preview

The manual loads its Markdown with `fetch`, which browsers block for `file://` pages. Start a small server in this folder:

```
python -m http.server 8000
```

and open <http://localhost:8000/>.
