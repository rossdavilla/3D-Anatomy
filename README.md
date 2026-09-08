# 3D Anatomy Viewers

Interactive 3D anatomy viewers that run entirely in the browser.

**Live site:** https://rossdavilla.github.io/3D-Anatomy/

## Viewers

| File | Description |
| --- | --- |
| `Male Reproductive System Viewer.html` | Self-contained three.js viewer — the glTF model is embedded as base64, so the page needs no other local files. Click a structure to see its name and description. |
| `Brain Neocortex Viewer.html` | Self-contained three.js viewer of the cerebral cortex, split into its four lobes plus the insula, with the cerebellum, brainstem, corpus callosum and pituitary gland alongside. Click a structure or pick one from the legend. |
| `Brain Limbic System Viewer.html` | The limbic system: 23 named structures inside a transparent cortical shell. Click one, or pick it from the legend, and everything else fades to a ghost. Toggles drop the cortex and cut the brain to a hemisection. Loads `brain/limbic-system-reduced.glb` at runtime, so it needs a web server. |
| `Brain Limbic System Simplified Viewer.html` | The same model and the same loader, narrowed to seven structures: hippocampus, amygdala, hypothalamus and pituitary, thalamus, pons, brainstem, cerebellum. Everything else is still drawn, but held back as translucent context and not clickable. Selecting a structure leaves the brain whole; an eye toggle beside the (i) fades everything else away, and the setting is sticky across selections. |
| `Female Reproductive System Viewer.html` | Female reproductive and urinary anatomy. The source model carries no per-organ names, so parts are separated into connected components and each was identified by hand. Self-contained: the model is embedded as base64. |
| `index.html` | Landing page linking to the viewers. |

## Building the brain viewer

`brain/neocortex.glb` ships as six generically named parts (`Brain_Part_01`…) sharing
one texture that paints the lobes in flat colours — good to look at, useless to click on.
`tools/build_neocortex_viewer.py` reads the texture colour under every triangle, splits
each hemisphere into one named mesh per lobe, drops the UVs and texture in favour of flat
material colours, and embeds the result into `tools/brain-viewer-template.html`:

```bash
python3 tools/build_neocortex_viewer.py
```

That regenerates `Brain Neocortex Viewer.html`. Edit the template or the script rather
than the generated page. Needs `numpy` and `Pillow`.

The lobe boundaries are only as good as the colours the model's author painted: the
inferior surface of the brain is not painted per-lobe in the source, so the orbital
surface of the frontal lobe reads as temporal there. The viewer says as much in its
attribution line.

## The hemisection view

Both limbic viewers can hide the left half of the brain, which gives the midsagittal view
the structures are usually taught from. It works because this model is built as mirrored
pairs: every one of its 54 meshes sits wholly on one side of the midline, so the cut is
just a matter of hiding each mesh whose centre falls on the `+x` side. The midline is
measured from the model's own bounding box rather than hard-coded, and `+x` is the
subject's left, so what remains is the right half seen from its cut face.

## Reducing the limbic system model

`brain/limbic-system.glb` is 46.6 MB, and 98% of that is geometry — 1.64 million
triangles across 54 meshes, against barely 1 MB of texture. Mesh decimation is the only
lever that matters. `tools/reduce-limbic.sh` runs it:

```bash
./tools/reduce-limbic.sh
```

It welds duplicate vertices, decimates to ~5% of the triangles with meshoptimizer, drops
what is then unreferenced, and halves the texture atlases to 256px — producing
`brain/limbic-system-reduced.glb`.

| | triangles | size |
| --- | --- | --- |
| source | 1,644,745 | 46.6 MB |
| reduced | 92,270 | 2.6 MB (2.1 MB gzipped) |

At that level the difference is not visible at any reasonable zoom, including on the
small structures — fornix, mammillary bodies, stria terminalis. The script keeps the
node names, which matters: this model's anatomy labels live on the nodes
(`..._Left_hippocampus_obj`), not on the meshes, which are just `mesh0`, `mesh1`, …

Needs `node`/`npm` (it fetches `@gltf-transform/cli` through `npx`) and `python3` with
Pillow. `tools/downscale_glb_textures.py` does the texture step and works on any `.glb`.

## Other files

| File | Description |
| --- | --- |
| `MaleSexualAnatomy 2.glb` | Source model embedded into the male reproductive system viewer. Not loaded at runtime. |
| `brain/neocortex.glb` | Source model for the brain viewer. Read at build time only. |
| `brain/limbic-system.glb` | Raw source model, 46.6 MB. Excluded from the repository; run `tools/reduce-limbic.sh` on it. |
| `brain/limbic-system-reduced.glb` | The reduced model, 2.6 MB. Loaded at runtime by both limbic system viewers. |

## How the viewers load their models

The male reproductive system, neocortex and female reproductive system viewers embed their
model as base64, so each is a single self-contained file you can open straight from disk. The
limbic system model is too big for that, so both limbic viewers fetch
`brain/limbic-system-reduced.glb` over the network and need to be served by a web server —
GitHub Pages is fine, and locally:

```bash
python3 -m http.server 8000
```

They also use three.js's own `GLTFLoader` rather than the hand-written reader the embedded
viewers share, because this model interleaves its vertex attributes and carries 38 textures
and 13 transparent materials — none of which the minimal reader handles.

## Running it

Open the male reproductive system, neocortex or female reproductive system viewer in a
modern browser, or visit the live site above. The two limbic system viewers need a server,
as above.

The viewers need an internet connection: they all load
[three.js](https://threejs.org/) r128 from a CDN.

## Credits

Model data for the male reproductive system viewer is based on Z-Anatomy / BodyParts3D,
licensed CC BY-SA 4.0.

The brain model is *Brain Project* by
[Dean Lavery](https://sketchfab.com/dean.lavery), licensed
[CC BY 4.0](http://creativecommons.org/licenses/by/4.0/) and hosted on
[Sketchfab](https://sketchfab.com/3d-models/brain-project-24ec03412dd8432bb0d3e750a72608e0).

The female reproductive system model is *Realistic Vagina Cutaway 3D Model* by Leo3DCG,
obtained via [Fab](https://www.fab.com/) (Epic Games) under the Fab Standard License. Unlike
the other models here it is not Creative Commons, and the viewer embeds its geometry as
base64 rather than linking to a hosted copy, so the asset ships with this repository.

## Notes

Large local source assets (the Z-Anatomy archive, raw `.glb`/`.fbx`/`.blend` files, and
reference model downloads) are excluded from this repository — see `.gitignore`. They are
not needed to run any viewer.
