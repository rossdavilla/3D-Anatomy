"""
Shrink the textures embedded in a .glb, in place of the originals.

The limbic system model carries 38 separate 512x512 JPEG atlases, one per
structure, and they are almost all low-frequency: a flat body colour with soft
shading. Halving them to 256x256 costs nothing visible and saves ~0.8 MB.

    python3 tools/downscale_glb_textures.py in.glb out.glb [--size 256] [--quality 85]

Only images stored in a bufferView are touched (that is all of them in a .glb).
Geometry, materials and the node tree are copied through untouched.
"""

import argparse
import io
import json
import struct
import sys
from pathlib import Path

from PIL import Image

JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942


def read_glb(path):
    data = Path(path).read_bytes()
    if data[:4] != b"glTF":
        raise SystemExit("%s is not a binary glTF file" % path)
    total = struct.unpack("<I", data[8:12])[0]
    offset, gltf, blob = 12, None, b""
    while offset < total:
        chunk_len, chunk_type = struct.unpack("<II", data[offset : offset + 8])
        body = data[offset + 8 : offset + 8 + chunk_len]
        if chunk_type == JSON_CHUNK:
            gltf = json.loads(body.decode("utf-8"))
        elif chunk_type == BIN_CHUNK:
            blob = body
        offset += 8 + chunk_len
    return gltf, blob


def write_glb(path, gltf, blob):
    json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    json_bytes += b" " * (-len(json_bytes) % 4)
    blob = blob + b"\0" * (-len(blob) % 4)
    total = 12 + 8 + len(json_bytes) + 8 + len(blob)
    with open(path, "wb") as fh:
        fh.write(struct.pack("<III", 0x46546C67, 2, total))
        fh.write(struct.pack("<II", len(json_bytes), JSON_CHUNK))
        fh.write(json_bytes)
        fh.write(struct.pack("<II", len(blob), BIN_CHUNK))
        fh.write(blob)
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("dest")
    ap.add_argument("--size", type=int, default=256, help="max edge in pixels (default 256)")
    ap.add_argument("--quality", type=int, default=85, help="JPEG quality (default 85)")
    args = ap.parse_args()

    gltf, blob = read_glb(args.source)
    images = gltf.get("images", [])
    if not images:
        raise SystemExit("no embedded images in %s" % args.source)

    # Re-encode every image, then rebuild the binary chunk around the new sizes.
    # Views are rewritten from scratch so the shrunken images do not leave holes.
    replacement = {}
    before = after = 0
    for image in images:
        if "bufferView" not in image:
            continue
        view = gltf["bufferViews"][image["bufferView"]]
        start = view.get("byteOffset", 0)
        raw = blob[start : start + view["byteLength"]]
        before += len(raw)

        picture = Image.open(io.BytesIO(raw)).convert("RGB")
        if max(picture.size) > args.size:
            scale = args.size / max(picture.size)
            new_size = (max(1, round(picture.width * scale)), max(1, round(picture.height * scale)))
            picture = picture.resize(new_size, Image.LANCZOS)
        buffer = io.BytesIO()
        picture.save(buffer, format="JPEG", quality=args.quality, optimize=True)
        replacement[image["bufferView"]] = buffer.getvalue()
        after += buffer.tell()
        image["mimeType"] = "image/jpeg"

    rebuilt = bytearray()
    for index, view in enumerate(gltf["bufferViews"]):
        while len(rebuilt) % 4:
            rebuilt.append(0)
        start = view.get("byteOffset", 0)
        payload = replacement.get(index, blob[start : start + view["byteLength"]])
        view["byteOffset"] = len(rebuilt)
        view["byteLength"] = len(payload)
        rebuilt.extend(payload)

    gltf["buffers"] = [{"byteLength": len(rebuilt) + (-len(rebuilt) % 4)}]
    total = write_glb(args.dest, gltf, bytes(rebuilt))

    print(
        "%d textures: %s -> %s (max edge %dpx)"
        % (len(replacement), fmt(before), fmt(after), args.size)
    )
    print("%s -> %s (%s)" % (fmt(Path(args.source).stat().st_size), fmt(total), args.dest))


def fmt(n):
    return "%.2f MB" % (n / 1e6) if n >= 1e6 else "%.0f KB" % (n / 1e3)


main()
