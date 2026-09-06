# 3D Anatomy Viewers

Interactive 3D anatomy viewers that run entirely in the browser.

**Live site:** https://rossdavilla.github.io/Male-Anatomy-3D/

## Viewers

| File | Description |
| --- | --- |
| `Male Reproductive System Viewer.html` | Self-contained three.js viewer — the glTF model is embedded as base64, so the page needs no other local files. Click a structure to see its name and description. |
| `Vagina Cutaway Viewer.html` | Cutaway model embedded from Sketchfab via iframe. Requires an internet connection. |
| `index.html` | Landing page linking to both viewers. |

## Other files

| File | Description |
| --- | --- |
| `MaleSexualAnatomy 2.glb` | Source model that was embedded into the male reproductive system viewer. Not loaded at runtime. |

## Running it

Open either viewer HTML file in a modern browser, or visit the live site above.

Both viewers need an internet connection: the male viewer loads [three.js](https://threejs.org/) r128 from a CDN, and the cutaway viewer embeds a remotely hosted model.

## Credits

The cutaway model is *Realistic Vagina Cutaway 3D Model* by [Leo_3D](https://sketchfab.com/leo_3dcg), hosted on Sketchfab.

Model data for the male reproductive system viewer is based on Z-Anatomy / BodyParts3D, licensed CC BY-SA 4.0.

## Notes

Large local source assets (the Z-Anatomy archive, raw `.glb`/`.fbx`/`.blend` files, and reference model downloads) are excluded from this repository — see `.gitignore`. They are not needed to run either viewer.
