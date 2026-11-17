# 3D Anatomy Viewers

Interactive three.js anatomy viewers that run in the browser, used in **PSY001 (Intro)** and
**PSY175 (Human Sexuality)**. Live at <https://rossdavilla.github.io/3D-Anatomy/>.

**`README.md` is the real documentation** — it covers every viewer, both build pipelines, the
hemisection trick, the model-reduction numbers, and the licensing of each model. Read it before
touching anything here. These notes only flag what matters most.

## The three traps

1. **`Brain Neocortex Viewer.html` is generated. Do not edit it.**
   `tools/build_neocortex_viewer.py` splits the lobes out of `brain/neocortex.glb` by reading the
   texture colour under every triangle and embeds the result into
   `tools/brain-viewer-template.html`. Edit the template or the script, then
   `python3 tools/build_neocortex_viewer.py` (needs `numpy` and `Pillow`). A hand edit to the
   generated page is thrown away on the next build.

2. **Two viewers need a web server; three do not.**
   The male reproductive, neocortex and female reproductive viewers embed their model as base64,
   so they open straight from disk. Both limbic viewers fetch `brain/limbic-system-reduced.glb`
   at runtime and need to be served (`python3 -m http.server 8000`, or GitHub Pages). All of them
   load three.js r128 from a CDN, so none works offline.

3. **The raw limbic model is not in the repo.**
   `brain/limbic-system.glb` is 46.6 MB and gitignored; the committed
   `brain/limbic-system-reduced.glb` (2.6 MB) is what ships. Regenerate it with
   `./tools/reduce-limbic.sh`, which keeps the node names — the anatomy labels live on the nodes
   (`..._Left_hippocampus_obj`), not the meshes, which are just `mesh0`, `mesh1`, …

## Licensing

Not all models are Creative Commons. The female reproductive model is a Fab Standard License
asset, which is why its geometry is embedded rather than hosted. Keep the credits block in the
README and the attribution line in each viewer accurate — including the honest note that the
neocortex lobe boundaries are only as good as the colours the model's author painted.

## Publishing

GitHub Pages serves `main` from the repository root, so a push to `main` is the deploy.

After adding a viewer, add it to `README.md`'s table **and** to `data/sites.json` in the
[`rossdavilla.github.io`](https://github.com/rossdavilla/rossdavilla.github.io) repo — each
viewer gets its own card with `"shot": { "delay": 5000 }` so the screenshotter waits for the
model to render. `tools/**` and `index.html` are in this repo's `ignore` list there.
