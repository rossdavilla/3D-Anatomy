#!/usr/bin/env bash
#
# Shrink brain/limbic-system.glb from 46.6 MB to something a web page can load.
#
#   ./tools/reduce-limbic.sh
#
# The source is 98% geometry: 1.64 million triangles across 54 meshes, with only
# ~1 MB of texture. So the lever is mesh decimation, not texture compression.
#
#   weld      merge duplicated vertices left by the OBJ -> glTF conversion
#   simplify  meshoptimizer's decimator, down to ~5% of the triangles
#   dedup     drop repeated accessors and materials
#   prune     drop anything no longer referenced
#   textures  512px -> 256px; these atlases are flat colour with soft shading
#
# Node names survive all of it, which matters: the anatomy labels this model
# carries ("..._Left_hippocampus_obj") live on the nodes, not the meshes.
#
# Needs node/npm (for gltf-transform) and python3 with Pillow.

set -euo pipefail
cd "$(dirname "$0")/.."

SRC="brain/limbic-system.glb"
OUT="brain/limbic-system-reduced.glb"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# --ratio is the target fraction of triangles; --error is the ceiling on how far
# a vertex may move, as a fraction of mesh size, and is what actually stops the
# decimation. 0.005 keeps the small structures (fornix, mammillary bodies)
# recognisable while still cutting ~95% of the triangles.
RATIO="${RATIO:-0.05}"
ERROR="${ERROR:-0.005}"
TEXTURE_SIZE="${TEXTURE_SIZE:-256}"

GT="npx --yes @gltf-transform/cli@4"

echo "==> weld"
$GT weld "$SRC" "$WORK/1.glb"
echo "==> simplify (ratio $RATIO, error $ERROR)"
$GT simplify "$WORK/1.glb" "$WORK/2.glb" --ratio "$RATIO" --error "$ERROR"
echo "==> dedup + prune"
$GT dedup "$WORK/2.glb" "$WORK/3.glb"
$GT prune "$WORK/3.glb" "$WORK/4.glb"
echo "==> textures"
python3 tools/downscale_glb_textures.py "$WORK/4.glb" "$OUT" --size "$TEXTURE_SIZE"

echo
ls -lh "$SRC" "$OUT" | awk '{printf "  %-40s %s\n", $9, $5}'
