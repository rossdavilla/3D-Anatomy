"""
Build "Brain Neocortex Viewer.html" from brain/neocortex.glb.

Run from the repository root:

    python3 tools/build_neocortex_viewer.py

The Sketchfab source has six generically named parts ("Brain_Part_01"...) and a
single material whose base-colour texture paints the cortical lobes in flat
colours. That looks fine but is useless to click on, so this script:

  * splits each cerebral hemisphere into one mesh per lobe, by reading the
    texture colour under each triangle,
  * gives every mesh an anatomical name and a flat base colour,
  * drops the UVs, the texture and the (identity) wrapper transforms,
  * rewrites indices as uint16,

then base64-encodes the result into tools/brain-viewer-template.html so the
finished page is a single self-contained file, like the male viewer.

Needs numpy and Pillow.
"""

import base64
import io
import json
import struct
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "brain" / "neocortex.glb"
TEMPLATE = ROOT / "tools" / "brain-viewer-template.html"
OUT_HTML = ROOT / "Brain Neocortex Viewer.html"

# Lobe colours as painted in the source texture, sampled from the model.
LOBE_COLOURS = {
    (52, 166, 157): "Frontal lobe",
    (223, 220, 64): "Parietal lobe",
    (52, 181, 56): "Temporal lobe",
    (195, 42, 42): "Occipital lobe",
    (226, 166, 118): "Insula",
}

# Flat colours used in the viewer: the source hues, pulled back a little so the
# model sits comfortably on the site's dark background.
DISPLAY_COLOUR = {
    "Frontal lobe": (0.31, 0.62, 0.60),
    "Parietal lobe": (0.80, 0.72, 0.38),
    "Temporal lobe": (0.34, 0.60, 0.37),
    "Occipital lobe": (0.72, 0.31, 0.31),
    "Insula": (0.85, 0.65, 0.53),
    "Cerebellum": (0.56, 0.33, 0.20),
    "Brainstem": (0.62, 0.42, 0.29),
    "Corpus callosum": (0.80, 0.72, 0.63),
    "Pituitary gland": (0.78, 0.56, 0.47),
}

# The four whole-mesh parts, identified from their position in the model.
WHOLE_PARTS = {
    0: "Pituitary gland",
    1: "Cerebellum",
    2: "Corpus callosum",
    4: "Brainstem",
}
HEMISPHERES = {3: ".r", 5: ".l"}  # part 04 is +x, part 06 is -x

COMPONENT_DTYPE = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}
TYPE_COUNT = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def read_glb(path):
    data = open(path, "rb").read()
    total = struct.unpack("<I", data[8:12])[0]
    offset, gltf, bin_offset = 12, None, None
    while offset < total:
        chunk_len, chunk_type = struct.unpack("<II", data[offset : offset + 8])
        if chunk_type == 0x4E4F534A:
            gltf = json.loads(data[offset + 8 : offset + 8 + chunk_len].decode("utf-8"))
        elif chunk_type == 0x004E4942:
            bin_offset = offset + 8
        offset += 8 + chunk_len
    return data, gltf, bin_offset


def accessor(data, gltf, bin_offset, index):
    acc = gltf["accessors"][index]
    view = gltf["bufferViews"][acc["bufferView"]]
    count = TYPE_COUNT[acc["type"]]
    start = bin_offset + view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    arr = np.frombuffer(
        data,
        dtype=np.dtype(COMPONENT_DTYPE[acc["componentType"]]),
        count=acc["count"] * count,
        offset=start,
    )
    return arr.reshape(acc["count"], count) if count > 1 else arr


def classify_triangles(tris, uv, texture):
    """Label every triangle with a lobe, by majority vote over its three
    corners plus its centroid. Sampling four points instead of one keeps
    triangles that straddle a painted boundary from flipping on JPEG noise."""
    height, width, _ = texture.shape
    refs = np.array(list(LOBE_COLOURS.keys()), dtype=float)
    names = list(LOBE_COLOURS.values())

    def sample(uvs):
        px = np.clip((uvs[:, 0] % 1.0 * width).astype(int), 0, width - 1)
        py = np.clip((uvs[:, 1] % 1.0 * height).astype(int), 0, height - 1)
        cols = texture[py, px].astype(float)
        dist = ((cols[:, None, :] - refs[None, :, :]) ** 2).sum(axis=2)
        return dist.argmin(axis=1)

    corner_votes = np.stack([sample(uv[tris[:, i]]) for i in range(3)], axis=1)
    centroid_uv = uv[tris].mean(axis=1)
    votes = np.concatenate([corner_votes, sample(centroid_uv)[:, None]], axis=1)

    labels = np.empty(len(tris), dtype=object)
    for i, row in enumerate(votes):
        # Ties fall to the centroid sample, which is the last column.
        counts = Counter(row.tolist())
        best = max(counts.items(), key=lambda kv: (kv[1], kv[0] == row[3]))[0]
        labels[i] = names[best]
    return labels


def compact(positions, normals, tris):
    """Reduce a triangle subset to its own tight vertex buffer."""
    used = np.unique(tris)
    remap = np.full(positions.shape[0], -1, dtype=np.int64)
    remap[used] = np.arange(len(used))
    return positions[used], normals[used], remap[tris].astype(np.uint16)


def main():
    data, gltf, bin_offset = read_glb(SRC)

    image_view = gltf["bufferViews"][gltf["images"][0]["bufferView"]]
    image_start = bin_offset + image_view.get("byteOffset", 0)
    jpeg = data[image_start : image_start + image_view["byteLength"]]
    texture = np.asarray(Image.open(io.BytesIO(jpeg)).convert("RGB"))

    parts = []  # (name, positions, normals, indices)

    for mesh_index, name in sorted(WHOLE_PARTS.items()):
        prim = gltf["meshes"][mesh_index]["primitives"][0]
        pos = accessor(data, gltf, bin_offset, prim["attributes"]["POSITION"]).astype(np.float32)
        nrm = accessor(data, gltf, bin_offset, prim["attributes"]["NORMAL"]).astype(np.float32)
        idx = accessor(data, gltf, bin_offset, prim["indices"]).astype(np.int64)
        parts.append((name, pos, nrm, idx.astype(np.uint16)))

    for mesh_index, side in sorted(HEMISPHERES.items()):
        prim = gltf["meshes"][mesh_index]["primitives"][0]
        pos = accessor(data, gltf, bin_offset, prim["attributes"]["POSITION"]).astype(np.float32)
        nrm = accessor(data, gltf, bin_offset, prim["attributes"]["NORMAL"]).astype(np.float32)
        uv = accessor(data, gltf, bin_offset, prim["attributes"]["TEXCOORD_0"]).astype(float)
        tris = accessor(data, gltf, bin_offset, prim["indices"]).astype(np.int64).reshape(-1, 3)

        labels = classify_triangles(tris, uv, texture)
        for lobe in LOBE_COLOURS.values():
            subset = tris[labels == lobe]
            if len(subset) == 0:
                continue
            sub_pos, sub_nrm, sub_idx = compact(pos, nrm, subset)
            parts.append((lobe + side, sub_pos, sub_nrm, sub_idx.reshape(-1)))
            print("%-22s %6d tris %6d verts" % (lobe + side, len(subset), len(sub_pos)))

    # ---- assemble the output glb -------------------------------------------
    blob = bytearray()
    accessors, views, meshes, materials, nodes = [], [], [], [], []
    material_of = {}

    def add_view(payload, target):
        while len(blob) % 4:
            blob.append(0)
        offset = len(blob)
        blob.extend(payload)
        views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(payload), "target": target})
        return len(views) - 1

    for name, pos, nrm, idx in parts:
        base = name.rsplit(".", 1)[0]
        if base not in material_of:
            r, g, b = DISPLAY_COLOUR[base]
            materials.append(
                {
                    "name": base,
                    "doubleSided": True,
                    "pbrMetallicRoughness": {
                        "baseColorFactor": [r, g, b, 1.0],
                        "metallicFactor": 0.0,
                        "roughnessFactor": 0.55,
                    },
                }
            )
            material_of[base] = len(materials) - 1

        pos_view = add_view(pos.tobytes(), 34962)
        accessors.append(
            {
                "bufferView": pos_view,
                "componentType": 5126,
                "count": len(pos),
                "type": "VEC3",
                "min": pos.min(axis=0).tolist(),
                "max": pos.max(axis=0).tolist(),
            }
        )
        pos_acc = len(accessors) - 1

        nrm_view = add_view(nrm.tobytes(), 34962)
        accessors.append({"bufferView": nrm_view, "componentType": 5126, "count": len(nrm), "type": "VEC3"})
        nrm_acc = len(accessors) - 1

        idx_view = add_view(idx.astype(np.uint16).tobytes(), 34963)
        accessors.append({"bufferView": idx_view, "componentType": 5123, "count": len(idx), "type": "SCALAR"})
        idx_acc = len(accessors) - 1

        meshes.append(
            {
                "name": name,
                "primitives": [
                    {
                        "attributes": {"POSITION": pos_acc, "NORMAL": nrm_acc},
                        "indices": idx_acc,
                        "material": material_of[base],
                    }
                ],
            }
        )
        nodes.append({"name": name, "mesh": len(meshes) - 1})

    out = {
        "asset": {
            "version": "2.0",
            "generator": "3D-Anatomy repack of Sketchfab 'Brain Project'",
            "extras": {
                "author": "Dean Lavery (https://sketchfab.com/dean.lavery)",
                "license": "CC-BY-4.0",
                "source": "https://sketchfab.com/3d-models/brain-project-24ec03412dd8432bb0d3e750a72608e0",
            },
        },
        "scene": 0,
        "scenes": [{"nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "meshes": meshes,
        "materials": materials,
        "accessors": accessors,
        "bufferViews": views,
        "buffers": [{"byteLength": len(blob)}],
    }

    bin_bytes = bytes(blob) + b"\0" * (-len(blob) % 4)
    out["buffers"][0]["byteLength"] = len(bin_bytes)
    json_bytes = json.dumps(out, separators=(",", ":")).encode("utf-8")
    json_bytes += b" " * (-len(json_bytes) % 4)

    total = 12 + 8 + len(json_bytes) + 8 + len(bin_bytes)
    glb = bytearray()
    glb += struct.pack("<III", 0x46546C67, 2, total)
    glb += struct.pack("<II", len(json_bytes), 0x4E4F534A)
    glb += json_bytes
    glb += struct.pack("<II", len(bin_bytes), 0x004E4942)
    glb += bin_bytes
    print("\n%d meshes, %d bytes of glb" % (len(meshes), len(glb)))

    template = TEMPLATE.read_text()
    page = template.replace("__MODEL_BASE64__", base64.b64encode(glb).decode("ascii"))
    if "__MODEL_BASE64__" in page or page == template:
        raise SystemExit("template placeholder __MODEL_BASE64__ not found")
    OUT_HTML.write_text(page)
    print("wrote %s (%d bytes)" % (OUT_HTML.name, len(page)))


main()
