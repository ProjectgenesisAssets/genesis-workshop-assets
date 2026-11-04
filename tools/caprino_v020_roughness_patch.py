#!/usr/bin/env python3
"""Project Genesis: V020 caprino, tiny roughness-only change to existing V019 glTF.
Reuses all original geometry, UV, normals and base color byte-for-byte.
Only raises G channel of packed metallicRoughness maps +15/255 (about 0.059).
Creates new files; never overwrites source GLBs or alters approved objects.
"""
import hashlib, io, json, pathlib, struct
from PIL import Image

ROOT = pathlib.Path("output/tanned-goatskin")
DEST = ROOT / "V020_roughness_only"
DELTA = 15  # subtle increase in physically based roughness
SOURCES = {
    "web": ("tanned-goatskin.glb", "3d893fde2f32651178ecb4d849754d4b7ca738062a9b280a1efda773051a2b61"),
    "master": ("tanned-goatskin_master.glb", "f60de9cb3cbcf1e30c60f30b4c5d8a704f68028d6935c93c09872f4a2607f22f"),
}
DEST.mkdir(parents=True, exist_ok=True)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def pack_glb(document, bin_data):
    b = json.dumps(document, separators=(",", ":"), ensure_ascii=False).encode("utf8")
    b += b" " * ((-len(b)) % 4)
    bin_data += b"\x00" * ((-len(bin_data)) % 4)
    size = 12 + 8 + len(b) + 8 + len(bin_data)
    return (struct.pack("<4sII", b"glTF", 2, size)
            + struct.pack("<I4s", len(b), b"JSON") + b
            + struct.pack("<I4s", len(bin_data), b"BIN\x00") + bin_data)

def unpack_glb(data):
    magic, version, size = struct.unpack_from("<4sII", data)
    assert magic == b"glTF" and version == 2 and size == len(data)
    jl, jt = struct.unpack_from("<I4s", data, 12)
    assert jt == b"JSON"
    document = json.loads(data[20:20+jl])
    bo = 20 + jl
    bl, bt = struct.unpack_from("<I4s", data, bo)
    assert bt == b"BIN\x00"
    original_bin = data[bo+8:bo+8+bl]
    return document, original_bin

reports = []
for variant, (filename, expected_hash) in SOURCES.items():
    source = ROOT / filename
    original = source.read_bytes()
    assert sha(original) == expected_hash, f"{filename}: V019 source identity mismatch"
    gltf, original_bin = unpack_glb(original)
    old_doc = json.loads(json.dumps(gltf))
    rough_images = set()
    for mat in gltf["materials"]:
        pbr = mat.get("pbrMetallicRoughness", {})
        r = pbr.get("metallicRoughnessTexture")
        assert r, "Missing photographed roughness texture in V019 material"
        image_id = gltf["textures"][r["index"]]["source"]
        rough_images.add(image_id)
    bin_data = bytearray(original_bin)
    for idx in sorted(rough_images):
        entry = gltf["images"][idx]
        view = gltf["bufferViews"][entry["bufferView"]]
        start = view.get("byteOffset", 0)
        data = bytes(original_bin[start:start+view["byteLength"]])
        image = Image.open(io.BytesIO(data)).convert("RGB")
        rr, gg, bb = image.split()
        before = list(gg.resize((64,64)).getdata())
        gg = gg.point([min(255, x + DELTA) for x in range(256)])
        after = list(gg.resize((64,64)).getdata())
        assert sum(after) > sum(before)
        patched = Image.merge("RGB", (rr, gg, bb))
        new_png = io.BytesIO()
        patched.save(new_png, "PNG", optimize=True)
        payload = new_png.getvalue()
        while len(bin_data) % 4: bin_data.append(0)
        offset = len(bin_data)
        bin_data.extend(payload)
        view_id = len(gltf["bufferViews"])
        gltf["bufferViews"].append({"buffer": 0, "byteOffset": offset, "byteLength": len(payload)})
        gltf["images"][idx]["bufferView"] = view_id
        gltf["images"][idx]["mimeType"] = "image/png"
        patched.save(DEST / f"caprino_{variant}_roughness_G_plus15.png")
    gltf["buffers"][0]["byteLength"] = len(bin_data) + ((-len(bin_data)) % 4)
    assert gltf["meshes"] == old_doc["meshes"]
    assert gltf["accessors"] == old_doc["accessors"]
    assert gltf["nodes"] == old_doc["nodes"]
    assert gltf["materials"] == old_doc["materials"]
    # Confirm original binary bytes are present, untouched: only a new map is appended.
    assert bin_data[:len(original_bin)] == original_bin
    target = DEST / f"caprino_v020_roughness_{variant}.glb"
    content = pack_glb(gltf, bytes(bin_data))
    target.write_bytes(content)
    parsed, parsed_bin = unpack_glb(content)
    assert parsed["meshes"] == old_doc["meshes"]
    assert parsed_bin[:len(original_bin)] == original_bin
    assert source.read_bytes() == original
    reports.append({
        "variant": variant, "original": filename, "original_sha256": expected_hash,
        "patched_glb": str(target), "patched_sha256": sha(content),
        "original_bytes": len(original), "patched_bytes": len(content),
        "roughness_image_ids": sorted(rough_images),
        "delta_green_channel": DELTA,
        "geometry_uv_normals_albedo_unchanged": True,
        "original_binary_bytes_preserved": True
    })
report = {"asset": "tanned-goatskin", "base": "V019_distinct_candidate",
          "candidate": "V020_roughness_only", "approved": False,
          "scope": "roughness channel G +15/255; all other visual data untouched",
          "reports": reports}
(DEST/"patch_report.json").write_text(json.dumps(report, indent=2), encoding="utf8")
print(json.dumps(report, indent=2))
