#!/usr/bin/env python3
"""Merge V011's independent water tracks, audit PlayCanvas GLB optimization.

No geometry decimation; preserves scanned marble, dolphin sculpture, animation
paths, 8-second loop and node hierarchy. Actual compression is applied by
@gltf-transform/cli in GitHub Actions.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

SRC = Path("public/models/PG_Dolphin_Fountain_V011_PlayCanvas_Animated.glb")
MERGED = Path("public/models/PG_Dolphin_Fountain_V011_Combined_Staging.glb")
HQ = Path("public/models/PG_Dolphin_Fountain_V011_PlayCanvas_HQ_Optimized.glb")
MOBILE = Path("public/models/PG_Dolphin_Fountain_V011_PlayCanvas_Mobile_Optimized.glb")
REPORT = Path("public/models/PG_Dolphin_Fountain_V011_Optimization.json")


def load_glb(p):
    data = p.read_bytes()
    assert len(data) >= 20 and data[:4] == b"glTF", f"Not a GLB: {p}"
    version, reported = struct.unpack_from("<II", data, 4)
    assert version == 2 and reported == len(data), f"Invalid GLB length: {p}"
    pos, chunks = 12, []
    while pos < len(data):
        length, typ = struct.unpack_from("<I4s", data, pos)
        pos += 8
        payload = data[pos:pos + length]
        assert len(payload) == length and length % 4 == 0
        chunks.append((typ, payload))
        pos += length
    assert pos == len(data) and chunks[0][0] == b"JSON"
    obj = json.loads(chunks[0][1].decode("utf-8"))
    return obj, chunks, data


def write_glb(p, doc, chunks):
    encoded = json.dumps(doc, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    encoded += b" " * ((-len(encoded)) % 4)
    out_chunks = [(b"JSON", encoded)] + chunks[1:]
    content = bytearray(b"glTF" + struct.pack("<II", 2, 12 + sum(8 + len(c) for _, c in out_chunks)))
    for typ, data in out_chunks:
        content += struct.pack("<I4s", len(data), typ)
        content += data
    assert len(content) == struct.unpack_from("<I", content, 8)[0]
    p.write_bytes(content)


def clip_info(gltf):
    animations = gltf.get("animations", [])
    acc = gltf.get("accessors", [])
    count = sum(len(a.get("channels", [])) for a in animations)
    values = []
    for a in animations:
        for sample in a.get("samplers", []):
            accessor = acc[sample["input"]]
            if "max" in accessor and "min" in accessor:
                values.append(accessor["max"][0] - accessor["min"][0])
    return len(animations), count, max(values, default=0)


def targets(gltf):
    return [
        (channel.get("target", {}).get("node"), channel.get("target", {}).get("path"))
        for a in gltf.get("animations", [])
        for channel in a.get("channels", [])
    ]


def prepare():
    gltf, chunks, data = load_glb(SRC)
    orig = gltf.get("animations", [])
    assert len(orig) >= 2, "Expected independently exported animation clips"
    before = clip_info(gltf)
    pairs = targets(gltf)
    assert len(pairs) == len(set(pairs)), "Clips contain overlapping node/path targets; unsafe to merge"
    combined = {"name": "Genesis_Dolphin_Water_8s", "channels": [], "samplers": [],
                "extras": {"durationSeconds": 8, "sourceAnimationCount": len(orig)}}
    for anim in orig:
        offset = len(combined["samplers"])
        combined["samplers"].extend(anim.get("samplers", []))
        for channel in anim.get("channels", []):
            ch = dict(channel)
            ch["sampler"] = channel["sampler"] + offset
            combined["channels"].append(ch)
    gltf["animations"] = [combined]
    write_glb(MERGED, gltf, chunks)
    final, _, _ = load_glb(MERGED)
    assert targets(final) == pairs
    assert clip_info(final)[1] == before[1]
    print("MERGED_WATER_CLIPS", json.dumps({
        "source_bytes": len(data), "source_clips": before[0],
        "single_loop_channels": before[1], "duration_s": before[2]
    }))


def inspect():
    orig, _, source_bytes = load_glb(SRC)
    assert len(source_bytes) > 1_000_000
    original_targets = set(targets(orig))
    materials = {m.get("name", "") for m in orig.get("materials", [])}
    named_nodes = {n.get("name", "") for n in orig.get("nodes", [])}
    assert any("DELFIN_ESCULPIDO" in n for n in named_nodes)
    assert any(n.startswith("AGUA_") for n in materials)
    source_animation_count = clip_info(orig)
    results = {}
    for label, path, texture_cap in [
        ("hq", HQ, 2048),
        ("mobile", MOBILE, 1024),
    ]:
        obj, _, binary = load_glb(path)
        after = clip_info(obj)
        required = set(obj.get("extensionsRequired", []))
        current_materials = {m.get("name", "") for m in obj.get("materials", [])}
        current_nodes = {n.get("name", "") for n in obj.get("nodes", [])}
        assert len(obj.get("animations", [])) == 1, f"Multiple clips in {label}"
        assert set(targets(obj)) == original_targets, f"Missing or modified animation targets in {label}"
        assert after[1] == source_animation_count[1], f"Lost animation channels: {label}"
        assert 7.5 <= after[2] <= 8.1, f"Invalid loop duration {label}: {after[2]}"
        assert materials.issubset(current_materials), f"Lost materials: {label}"
        assert any("DELFIN_ESCULPIDO" in n for n in current_nodes), f"Lost dolphin: {label}"
        assert any("Anim_" in n for n in current_nodes), f"Lost water jets: {label}"
        assert "KHR_draco_mesh_compression" in (set(obj.get("extensionsUsed", [])) | required), f"No Draco in {label}"
        assert "EXT_meshopt_compression" not in required, f"PlayCanvas compatibility issue in {label}"
        assert not (set(obj.get("extensionsUsed", [])) - set(orig.get("extensionsUsed", [])) - {"KHR_draco_mesh_compression", "KHR_mesh_quantization"}), f"Unexpected extensions in {label}"
        assert len(binary) < len(source_bytes) * (0.92 if label == "hq" else 0.79), f"Insufficient savings for {label} ({len(binary)} bytes)"
        if label == "mobile":
            assert len(binary) < len(load_glb(HQ)[2]), "Mobile version must be smaller than HQ"
        results[label] = {
            "file": str(path), "bytes": len(binary), "megabytes": round(len(binary)/1e6,2),
            "sha256": hashlib.sha256(binary).hexdigest(), "texture_max": texture_cap,
            "clip_count": after[0], "channels": after[1], "loop_seconds": round(after[2], 3),
            "meshes": len(obj.get("meshes", [])), "materials": len(obj.get("materials", [])),
            "extensions_required": sorted(required),
            "saving_percent": round(100*(1-len(binary)/len(source_bytes)), 2),
        }
    manifest = {
        "asset": "Project Genesis Dolphin Fountain V011",
        "status": "BINARY_OPTIMIZED_NOT_YET_IN_GAME_VISUALLY_APPROVED",
        "source_bytes": len(source_bytes),
        "source_animation_clips": source_animation_count[0],
        "source_animation_channels": source_animation_count[1],
        "animation": "Single merged synchronized 8-second glTF animation; PlayCanvas material ripple UV scroll requires companion JS",
        "geometry": "No mesh decimation or topology-simplification; Draco encodes geometry",
        "playcanvas_decoder": "DracoDecoderModule must be configured before GLB loading",
        "variants": results,
        "artistic_approval": "PENDING",
        "on_device_fps": "NOT_YET_TESTED"
    }
    REPORT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("GLB_OPTIMIZATION_VALIDATED", json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "inspect"))
    mode = parser.parse_args().mode
    {"prepare": prepare, "inspect": inspect}[mode]()
