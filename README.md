# Male Anatomy 3D

An interactive 3D viewer for the male reproductive system, running entirely in the browser.

**Live page:** https://rossdavilla.github.io/Male-Anatomy-3D/

## Contents

| File | Description |
| --- | --- |
| `Male Reproductive System Viewer.html` | The viewer. Self-contained — the glTF model is embedded as base64, so the page needs no other local files. |
| `MaleSexualAnatomy 2.glb` | The source model that was embedded into the viewer. |
| `index.html` | Redirect to the viewer, so GitHub Pages serves it at the site root. |

## Running it

Open `Male Reproductive System Viewer.html` in any modern browser, or visit the live page above.

The only external dependency is [three.js](https://threejs.org/) r128, loaded from a CDN, so an internet connection is required on first load.

## Notes

The original Z-Anatomy source archive is excluded from this repository (see `.gitignore`) — it is large and not needed to run the viewer.
