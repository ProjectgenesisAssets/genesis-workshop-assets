#!/usr/bin/env python3
"""Project Genesis V082-B approved door: strict lossless-first GLB audit/optimization.

Approved original GLB is immutable. No geometry decimation, no texture resize,
no PBR/material changes; PNG recompression must decode to EXACT same pixels.
These are binary technical checks; never infer 1.5%-2.5% aesthetic similarity
without matched Cycles HDRI renders and explicit user approval.
"""
import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops

EXPECTED_BYTES = 15887816
EXPECTED_BLOB = "eef69d28dd8d53b5934442279a8b027bdfbfa157"
VIEWS = ("front", "three_quarter", "side", "rear")

def sha256(buf):
    return hashlib.sha256(buf).hexdigest()

def read_glb(path):
    data = Path(path).read_bytes()
    assert data[:4] == b"glTF", "Invalid GLB magic"
    magic, ver, length = struct.unpack_from("<4sII", data)
    assert ver == 2 and length == len(data)
    off = 12
    chunks = []
    while off < len(data):
        size, typ = struct.unpack_from("<I4s", data, off)
        off += 8
        chunks.append((typ, data[off:off + size]))
        off += size
    assert off == len(data), "Corrupted chunk boundaries"
    assert [x[0] for x in chunks[:2]] == [b"JSON", b"BIN\x00"], "Expected one buffer GLB"
    doc = json.loads(chunks[0][1].decode("utf-8"))
    assert len(doc.get("buffers", [])) == 1, "Complex GLB: refuse unsafe repack"
    assert doc["buffers"][0].get("uri") is None
    return data, doc, chunks[1][1]

def image_info(blob):
    with Image.open(BytesIO(blob)) as im:
        im.load()
        return {
            "format": im.format,
            "mode": im.mode,
            "size": [im.width, im.height],
            "gamma": im.info.get("gamma"),
            "srgb": im.info.get("srgb"),
            "icc_sha256": sha256(im.info["icc_profile"].encode() if isinstance(im.info.get("icc_profile"), str) else im.info.get("icc_profile", b"")),
            "pixels_sha256": sha256(im.convert("RGBA").tobytes()),
        }

def audit(doc, bin_data):
    out = {}
    images = {}
    view_sums = {"geometry": 0, "embedded_images": 0, "other": 0}
    image_views = {i["bufferView"] for i in doc.get("images", []) if "bufferView" in i}
    for ix, im in enumerate(doc.get("images", [])):
        view = doc["bufferViews"][im["bufferView"]]
        start = view.get("byteOffset", 0)
        raw = bin_data[start:start + view["byteLength"]]
        images[str(ix)] = {
            "name": im.get("name", f"image_{ix}"),
            "mimeType": im.get("mimeType"),
            "byteLength": len(raw),
            **image_info(raw)
        }
    for j, view in enumerate(doc.get("bufferViews", [])):
        if view.get("buffer") != 0:
            raise ValueError("Other buffer found")
        k = "embedded_images" if j in image_views else "geometry" if view.get("target") in (34962, 34963) else "other"
        view_sums[k] += view["byteLength"]
    tri_count = 0
    for mesh in doc.get("meshes", []):
        for prim in mesh.get("primitives", []):
            if prim.get("mode", 4) == 4:
                indices = prim.get("indices")
                n = doc["accessors"][indices]["count"] if indices is not None else doc["accessors"][prim["attributes"]["POSITION"]]["count"]
                tri_count += n // 3
    out["triangles"] = tri_count
    out["mesh_count"] = len(doc.get("meshes", []))
    out["material_count"] = len(doc.get("materials", []))
    out["primitive_count"] = sum(len(m["primitives"]) for m in doc.get("meshes", []))
    out["node_count"] = len(doc.get("nodes", []))
    out["image_count"] = len(images)
    out["image_details"] = images
    out["bufferView_bytes_by_category"] = view_sums
    out["extensionsRequired"] = doc.get("extensionsRequired", [])
    return out

def git_blob_hash(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\x00" + data).hexdigest()

def optimize_images(doc, bin_data):
    view_to_image = {}
    for image_ix, image in enumerate(doc.get("images", [])):
        if image.get("mimeType") == "image/png" and "bufferView" in image:
            view_to_image.setdefault(image["bufferView"], []).append(image_ix)

    replacements = {}
    details = []
    with tempfile.TemporaryDirectory() as temp:
        for view_ix, ids in view_to_image.items():
            view = doc["bufferViews"][view_ix]
            src = bin_data[view.get("byteOffset", 0):view.get("byteOffset", 0)+view["byteLength"]]
            assert src[:8] == b"\x89PNG\r\n\x1a\n"
            fp = Path(temp) / f"image_{view_ix}.png"
            fp.write_bytes(src)
            result = subprocess.run(["optipng", "-quiet", "-o3", str(fp)], capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError("optipng failed " + result.stderr[:1000])
            candidate = fp.read_bytes()
            old = image_info(src)
            new = image_info(candidate)
            # Exact pixel equality; no changes to 8/16-bit channel values or color metadata.
            if old != new:
                raise RuntimeError(f"Lossless optimization changed pixels/metadata for images {ids}: {old} != {new}")
            if len(candidate) < len(src):
                replacements[view_ix] = candidate
            details.append({"view": view_ix, "images": ids, "original_bytes": len(src),
                            "optimized_bytes": len(candidate), "accepted_bytes": min(len(candidate), len(src)),
                            "saved_bytes": max(0, len(src)-len(candidate)), "pixels_identical": True})
    return replacements, details

def repack(doc, bin_data, replacements):
    # Preserve every original bufferView other than the optimized image bytes,
    # including vertex buffers and indices. Update byte offsets, not accessors.
    dst = bytearray()
    for i, view in enumerate(doc.get("bufferViews", [])):
        if view.get("buffer") != 0:
            raise RuntimeError("Cannot safely repack multiple GLB buffers")
        src = bin_data[view.get("byteOffset", 0):view.get("byteOffset", 0)+view["byteLength"]]
        payload = replacements.get(i, src)
        while len(dst) % 4:
            dst.append(0)
        view["byteOffset"] = len(dst)
        view["byteLength"] = len(payload)
        dst.extend(payload)
    doc["buffers"][0]["byteLength"] = len(dst)
    while len(dst) % 4:
        dst.append(0)
    json_bytes = json.dumps(doc, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    json_bytes += b" " * (-len(json_bytes) % 4)
    total = 12+8+len(json_bytes)+8+len(dst)
    return struct.pack("<4sII", b"glTF", 2, total) + struct.pack("<I4s", len(json_bytes), b"JSON") + json_bytes + struct.pack("<I4s", len(dst), b"BIN\x00") + dst

def compare_glb(original, candidate, allow_png_image_changes):
    old_buf, old_doc, old_bin = read_glb(original)
    new_buf, new_doc, new_bin = read_glb(candidate)
    assert old_doc["meshes"] == new_doc["meshes"]
    assert old_doc["nodes"] == new_doc["nodes"]
    assert old_doc["materials"] == new_doc["materials"]
    assert old_doc.get("textures") == new_doc.get("textures")
    assert old_doc.get("accessors") == new_doc.get("accessors")
    assert len(old_doc["bufferViews"]) == len(new_doc["bufferViews"])
    image_views = {x["bufferView"] for x in old_doc.get("images", []) if "bufferView" in x}
    for i, (old_v, new_v) in enumerate(zip(old_doc["bufferViews"], new_doc["bufferViews"])):
        old_data = old_bin[old_v.get("byteOffset",0):old_v.get("byteOffset",0)+old_v["byteLength"]]
        new_data = new_bin[new_v.get("byteOffset",0):new_v.get("byteOffset",0)+new_v["byteLength"]]
        if i in image_views and allow_png_image_changes:
            assert image_info(old_data) == image_info(new_data)
        else:
            assert old_data == new_data, "Original geometry/other buffer has changed!"
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    original, doc, b = read_glb(args.source)
    assert len(original) == EXPECTED_BYTES, (len(original), EXPECTED_BYTES)
    assert git_blob_hash(original) == EXPECTED_BLOB, "Source is not approved V082-B exact blob"
    base = audit(doc, b)
    replacements, details = optimize_images(doc, b)
    raw = repack(doc, b, replacements)
    candidate = out/"herrero_v082b_lossless_png.glb"
    candidate.write_bytes(raw)
    compare_glb(args.source, candidate, allow_png_image_changes=True)
    # Source immutability and exact pixel equality are stronger than any noisy render metric.
    pct = 100*(1 - len(raw)/len(original))
    report = {
      "source": args.source,
      "approved_blob_sha": EXPECTED_BLOB,
      "source_bytes": len(original),
      "lossless_candidate_bytes": len(raw),
      "source_sha256": sha256(original),
      "candidate_sha256": sha256(raw),
      "saved_percent": round(pct, 4),
      "quality_loss_percent": 0.0,
      "quality_loss_type": "EXACT_DECODED_PIXELS_AND_VERTEX_DATA",
      "images_optimized": details,
      "source_inventory": base,
      "technical_validation": "PASS",
      "gameplay_integration": False,
      "human_approved": False,
      "visual_loss_limit_percent": 2.5,
      "note": "0% decoded pixel/geometry change proven; final visual quality and game render still require comparison and user approval"
    }
    (out/"report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
    print("=== V082-B APPROVED SOURCE AUDIT ===")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    assert base["triangles"] > 0
    if pct <= 0:
        print("NOTE: Lossless recompression did not decrease GLB; do not replace approved original.")
    else:
        print("Lossless smaller candidate created and validated; approval not implied.")

if __name__ == "__main__":
    main()
