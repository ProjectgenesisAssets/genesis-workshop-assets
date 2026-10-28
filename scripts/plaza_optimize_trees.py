"""Generate full-quality reference and independently decimated PlayCanvas GLB candidates.

Blender 4.5.13:
 blender -b -t 2 --python-exit-code 1 --python scripts/plaza_optimize_trees.py -- \
   --source source.glb --output-dir output/plaza --ratios 0.5,0.3,0.15
The source is never overwritten. Visual approval is a separate gate.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--ratios", default="0.50,0.30,0.15")
    parser.add_argument("--samples", type=int, default=16)
    return parser.parse_args(args)


def load_source(source, smoke):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if smoke:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=64)
        obj = bpy.context.object
        obj.name = "SYNTHETIC_QA_SPHERE_NOT_FAB"
        mat = bpy.data.materials.new("Synthetic foliage")
        mat.diffuse_color = (0.15, 0.32, 0.09, 1.0)
        obj.data.materials.append(mat)
        return
    if not source or not source.is_file():
        raise RuntimeError("A source .blend or .glb file is required")
    if source.suffix.lower() == ".glb":
        bpy.ops.import_scene.gltf(filepath=str(source.resolve()))
    elif source.suffix.lower() == ".blend":
        bpy.ops.wm.open_mainfile(filepath=str(source.resolve()))
        reconnect_fab_textures(source)
    else:
        raise ValueError("Unsupported source; use .blend or .glb")


def reconnect_fab_textures(source):
    """Reconnect images from the original outer Fab ZIP, without changing meshes."""
    if not source or source.suffix.lower() != ".blend":
        return
    extracted_root = next((p for p in source.parents if (p / "outer").is_dir()), None)
    if extracted_root is None:
        print("TEXTURE_RECONNECT: no outer directory found; checking embedded image data")
        return
    filenames = {}
    for file in (extracted_root / "outer").rglob("*"):
        if file.is_file() and file.suffix.lower() in {".png", ".jpg", ".jpeg", ".tga", ".webp"}:
            filenames.setdefault(file.name.casefold(), file)
    rebound = 0
    missing = []
    for img in bpy.data.images:
        if img.source != "FILE" or img.packed_file is not None:
            continue
        old_name = Path(img.filepath.replace("\\", "/")).name.casefold()
        img_name = Path(img.name.replace("\\", "/")).name.casefold()
        path = filenames.get(old_name) or filenames.get(img_name)
        if path is None:
            if old_name:
                missing.append(img.name)
            continue
        img.filepath = str(path.resolve())
        try:
            img.reload()
        except RuntimeError as error:
            raise RuntimeError("Unable to load Fab texture %s: %s" % (path, error))
        rebound += 1
    print("TEXTURE_RECONNECT: %d images reconnected from Fab; %d unmatched: %s" % (
        rebound, len(missing), missing[:10]))
    if rebound == 0 and not any(image.packed_file for image in bpy.data.images):
        raise RuntimeError("External Fab images were not reconnected; refusing textureless export")


def scene_meshes():
    return [o for o in bpy.context.scene.objects if o.type == "MESH" and not o.hide_render]


def count_tris(objects):
    total = 0
    for obj in objects:
        obj.data.calc_loop_triangles()
        total += len(obj.data.loop_triangles)
    return total


def geometry_bounds(objects):
    points = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    if not points:
        raise RuntimeError("Source has no visible meshes")
    minimum = Vector(tuple(min(v[i] for v in points) for i in range(3)))
    maximum = Vector(tuple(max(v[i] for v in points) for i in range(3)))
    center = (minimum + maximum) / 2
    size = max(maximum[i] - minimum[i] for i in range(3))
    if not math.isfinite(size) or size < 1e-5:
        raise RuntimeError("Invalid source dimensions")
    return center, size


VIEWS = [
    ("front", 0, 0.25, 1.45, 0),
    ("right", 90, 0.25, 1.45, 0),
    ("back", 180, 0.25, 1.45, 0),
    ("left", 270, 0.25, 1.45, 0),
    ("canopy_detail", 45, 0.85, 0.85, 0.20),
]


def setup_render(center, size, samples):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.render.resolution_x = 960
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.new("GENESIS_QA_WORLD")
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.7, 0.74, 0.79, 1)
    background.inputs["Strength"].default_value = 0.7
    scene.world = world
    for name, xyz, energy in [
        ("QA_KEY", (2, -3.5, 5), 1800),
        ("QA_FILL", (-3.5, 2, 3), 1100),
    ]:
        bpy.ops.object.light_add(type="AREA", location=center + Vector(xyz) * size)
        light = bpy.context.object
        light.name = name
        light.data.shape = "DISK"
        light.data.size = size * 2
        light.data.energy = energy
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.name = "GENESIS_QA_CAMERA"
    camera.data.type = "ORTHO"
    scene.camera = camera
    return camera


def render_views(folder, center, size, camera):
    folder.mkdir(parents=True, exist_ok=True)
    for name, azimuth, elevation, zoom, offset in VIEWS:
        theta = math.radians(azimuth)
        target = center + Vector((0, 0, size * offset))
        direction = Vector((math.sin(theta), -math.cos(theta), elevation)).normalized()
        camera.location = target + direction * size * 3
        camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera.data.ortho_scale = size * zoom
        bpy.context.scene.render.filepath = str((folder / (name + ".png")).resolve())
        bpy.ops.render.render(write_still=True)


def export_glb(path):
    bpy.ops.export_scene.gltf(
        filepath=str(path.resolve()),
        export_format="GLB",
        export_cameras=False,
        export_lights=False,
        export_texcoords=True,
        export_normals=True,
        export_materials="EXPORT",
        export_image_format="AUTO",
    )
    if not path.is_file() or path.stat().st_size < 100:
        raise RuntimeError("GLB export failed: " + str(path))


def decimate(objects, remaining):
    for obj in objects:
        obj.data.calc_loop_triangles()
        if len(obj.data.loop_triangles) < 256 or obj.data.shape_keys:
            continue
        if obj.data.users > 1:
            obj.data = obj.data.copy()
        bpy.ops.object.select_all(action="DESELECT")
        obj.hide_set(False)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        modifier = obj.modifiers.new("GENESIS_CANDIDATE_ONLY", "DECIMATE")
        modifier.decimate_type = "COLLAPSE"
        modifier.ratio = remaining
        bpy.ops.object.modifier_apply(modifier=modifier.name)


def main():
    args = parse_args()
    ratios = [float(value.strip()) for value in args.ratios.split(",")]
    if not ratios or len(set(ratios)) != len(ratios) or any(not 0.05 <= r < 1 for r in ratios):
        raise ValueError("Supply unique remaining ratios from 0.05 to less than 1")
    if args.samples < 1 or args.samples > 128:
        raise ValueError("Invalid Cycles sample count")
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    load_source(args.source, args.smoke)
    original_objects = scene_meshes()
    original_triangles = count_tris(original_objects)
    if original_triangles == 0:
        raise RuntimeError("Source has no triangles")
    center, size = geometry_bounds(original_objects)
    export_glb(out / "baseline.glb")
    camera = setup_render(center, size, args.samples)
    render_views(out / "views" / "baseline", center, size, camera)
    manifest = {
        "source": str(args.source) if args.source else "synthetic smoke fixture",
        "smoke_only": args.smoke,
        "baseline_triangles_blender": original_triangles,
        "render_views": [v[0] for v in VIEWS],
        "candidates": [],
        "artist_approved": False,
    }
    for remaining in ratios:
        # Every candidate starts again from the untouched original.
        load_source(args.source, args.smoke)
        objects = scene_meshes()
        if count_tris(objects) != original_triangles:
            raise RuntimeError("Source triangle count changed across imports")
        decimate(objects, remaining)
        resulting_tris = count_tris(objects)
        label = "r%03d" % round(remaining * 100)
        export_glb(out / ("candidate_" + label + ".glb"))
        camera = setup_render(center, size, args.samples)
        render_views(out / "views" / ("candidate_" + label), center, size, camera)
        manifest["candidates"].append({
            "label": label, "remaining_ratio_requested": remaining,
            "triangles_blender": resulting_tris,
            "triangles_removed": original_triangles - resulting_tris,
        })
    (out / "blender_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("GENESIS_PLAZA_MANIFEST", json.dumps(manifest))


if __name__ == "__main__":
    main()
