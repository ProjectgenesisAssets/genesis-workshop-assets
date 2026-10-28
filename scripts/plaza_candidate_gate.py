"""Independent GLB integrity and five-view appearance gate for Genesis plaza trees.

Accepts unlimited polygon reduction if render appearance survives. The 8% visual
threshold is a conservative *proxy*, not a scientifically exact perceptual score.
The candidate is NEVER artist-approved automatically.
"""
import argparse
import json
import shutil
import struct
from pathlib import Path

import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity


def glb_stats(path):
    with path.open("rb") as handle:
        head = handle.read(12)
        if len(head) != 12:
            raise ValueError("Short GLB: " + str(path))
        magic, version, length = struct.unpack("<4sII", head)
        if magic != b"glTF" or version != 2 or length != path.stat().st_size:
            raise ValueError("Invalid GLB header: " + str(path))
        json_length, chunk_type = struct.unpack("<I4s", handle.read(8))
        if chunk_type != b"JSON":
            raise ValueError("GLB JSON chunk missing")
        model = json.loads(handle.read(json_length))
    accessors = model.get("accessors", [])
    mesh_tris = []
    uv0_primitives = 0
    primitive_count = 0
    assigned_materials = set()
    for mesh in model.get("meshes", []):
        count = 0
        for primitive in mesh.get("primitives", []):
            mode = primitive.get("mode", 4)
            if mode not in (4, 5, 6):
                continue
            primitive_count += 1
            ref = primitive.get("indices")
            if ref is None:
                ref = primitive.get("attributes", {}).get("POSITION")
            if ref is None or ref >= len(accessors):
                raise ValueError("Invalid primitive accessor: " + str(path))
            n = accessors[ref]["count"]
            count += n // 3 if mode == 4 else max(0, n - 2)
            uv0_primitives += int("TEXCOORD_0" in primitive.get("attributes", {}))
            if "material" in primitive:
                assigned_materials.add(primitive["material"])
        mesh_tris.append(count)
    nodes = model.get("nodes", [])
    instances = [node["mesh"] for node in nodes if "mesh" in node]
    if any(i >= len(mesh_tris) for i in instances):
        raise ValueError("Invalid mesh node reference")
    return {
        "mesh_triangles": sum(mesh_tris),
        "scene_instance_triangles": sum(mesh_tris[i] for i in instances),
        "mesh_count": len(mesh_tris),
        "mesh_node_count": len(instances),
        "primitive_count": primitive_count,
        "uv0_primitives": uv0_primitives,
        "material_count": len(model.get("materials", [])),
        "materials_used": len(assigned_materials),
        "texture_count": len(model.get("textures", [])),
        "image_count": len(model.get("images", [])),
    }


def compare_view(reference_file, candidate_file):
    with Image.open(reference_file) as image:
        reference = np.asarray(image.convert("RGBA"), dtype=np.float32) / 255.0
    with Image.open(candidate_file) as image:
        candidate = np.asarray(image.convert("RGBA"), dtype=np.float32) / 255.0
    if reference.shape != candidate.shape:
        raise ValueError("Image dimensions differ")
    original = reference[:, :, 3] > 0.10
    reduced = candidate[:, :, 3] > 0.10
    union = original | reduced
    intersection = original & reduced
    if union.sum() < reference.shape[0] * reference.shape[1] * 0.01:
        raise ValueError("Rendered tree subject missing/too small")
    iou = float(intersection.sum() / union.sum())
    neutral = np.array((0.5, 0.5, 0.5), dtype=np.float32)
    ref_rgb = reference[:, :, :3] * reference[:, :, 3:] + (1.0 - reference[:, :, 3:]) * neutral
    cand_rgb = candidate[:, :, :3] * candidate[:, :, 3:] + (1.0 - candidate[:, :, 3:]) * neutral
    mean_delta = float(np.abs(ref_rgb - cand_rgb)[union].mean())
    ys, xs = np.where(union)
    pad = 16
    x0, x1 = max(0, int(xs.min()) - pad), min(reference.shape[1], int(xs.max()) + pad + 1)
    y0, y1 = max(0, int(ys.min()) - pad), min(reference.shape[0], int(ys.max()) + pad + 1)
    ssim = float(structural_similarity(
        ref_rgb[y0:y1, x0:x1], cand_rgb[y0:y1, x0:x1],
        data_range=1.0, channel_axis=2,
    ))
    return {
        "silhouette_iou": round(iou, 5),
        "foreground_color_delta_fraction": round(mean_delta, 5),
        "structural_similarity": round(ssim, 5),
        "passed": bool(iou >= 0.98 and mean_delta <= 0.08 and ssim >= 0.92),
    }


def check_glb(reference, candidate, minimum_textures, minimum_materials):
    reasons = []
    if reference["mesh_triangles"] <= 0 or candidate["mesh_triangles"] <= 0:
        reasons.append("EMPTY_GEOMETRY")
    if candidate["mesh_triangles"] >= reference["mesh_triangles"]:
        reasons.append("NO_POLYGON_REDUCTION")
    if reference["image_count"] < minimum_textures or reference["material_count"] < minimum_materials:
        reasons.append("SOURCE_MISSING_EXPECTED_FAB_TEXTURES_OR_MATERIALS")
    for field in ("material_count", "materials_used", "texture_count", "image_count", "uv0_primitives", "mesh_node_count"):
        if candidate[field] < reference[field]:
            reasons.append("LOST_" + field.upper())
    # UV coverage is compared by fraction too: the exporter can regroup primitives.
    if reference["primitive_count"] > 0 and candidate["primitive_count"] > 0:
        original_uv_fraction = reference["uv0_primitives"] / reference["primitive_count"]
        new_uv_fraction = candidate["uv0_primitives"] / candidate["primitive_count"]
        if new_uv_fraction + 0.0001 < original_uv_fraction:
            reasons.append("UV0_COVERAGE_REDUCED")
    return reasons


def run(folder, minimum_textures, minimum_materials):
    manifest = json.loads((folder / "blender_manifest.json").read_text(encoding="utf-8"))
    reference = glb_stats(folder / "baseline.glb")
    candidates = []
    for item in manifest["candidates"]:
        label = item["label"]
        candidate_file = folder / ("candidate_" + label + ".glb")
        candidate = glb_stats(candidate_file)
        errors = check_glb(reference, candidate, minimum_textures, minimum_materials)
        view_results = {}
        for view in manifest["render_views"]:
            try:
                view_results[view] = compare_view(
                    folder / "views" / "baseline" / (view + ".png"),
                    folder / "views" / ("candidate_" + label) / (view + ".png"),
                )
            except Exception as exc:
                view_results[view] = {"passed": False, "error": str(exc)}
        if not all(result["passed"] for result in view_results.values()):
            errors.append("VISUAL_COMPARISON_FAILED")
        candidates.append({
            "label": label, "glb": candidate_file.name,
            "remaining_ratio_requested": item["remaining_ratio_requested"],
            "mesh_triangles": candidate["mesh_triangles"],
            "removed_triangles": reference["mesh_triangles"] - candidate["mesh_triangles"],
            "reduction_fraction": round(
                1 - candidate["mesh_triangles"] / max(1, reference["mesh_triangles"]), 6,
            ),
            "integrity": candidate,
            "views": view_results,
            "passed_objective_gate": not errors,
            "reasons": errors,
        })
    approved_by_metrics = [item for item in candidates if item["passed_objective_gate"]]
    best = max(approved_by_metrics, key=lambda item: item["removed_triangles"], default=None)
    report = {
        "source": manifest["source"],
        "source_is_synthetic_smoke": manifest["smoke_only"],
        "source_license": "CC-BY-4.0 (Nicholas 3D, More Realistic Trees Free!)" if not manifest["smoke_only"] else "synthetic test",
        "baseline": reference,
        "visual_limits": {
            "silhouette_iou_min": 0.98,
            "foreground_color_delta_max_fraction": 0.08,
            "structural_similarity_min": 0.92,
            "views": manifest["render_views"],
        },
        "candidates": candidates,
        "best_objective_candidate": best["label"] if best else None,
        "artist_approved": False,
        "note": "Pixel/SSIM metrics approximate visual preservation; they do NOT prove an exact 8% perceptual detail loss. Human comparison at PlayCanvas gameplay distance is mandatory.",
    }
    (folder / "plaza_visual_qa.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if best:
        shutil.copyfile(folder / best["glb"], folder / "plaza_arboles_candidate_playcanvas.glb")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--minimum-textures", type=int, default=0)
    parser.add_argument("--minimum-materials", type=int, default=0)
    args = parser.parse_args()
    report = run(args.output_dir, args.minimum_textures, args.minimum_materials)
    print(json.dumps({
        "baseline_triangles": report["baseline"]["mesh_triangles"],
        "best_objective_candidate": report["best_objective_candidate"],
        "candidates": [{k: candidate[k] for k in ("label", "removed_triangles", "passed_objective_gate", "reasons")} for candidate in report["candidates"]],
        "artist_approved": False,
    }, ensure_ascii=False, indent=2))
    if report["best_objective_candidate"] is None:
        raise SystemExit("No candidate passed all appearance and integrity gates")


if __name__ == "__main__":
    main()
