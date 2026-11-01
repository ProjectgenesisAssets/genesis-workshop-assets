"""Export approved V082-B from exact existing Blender source without rerendering 4 studio previews.
Door pivot at left hinge (0,0,0) after rebase. No topology or ornament changes.
"""
from pathlib import Path
import bpy, json, hashlib, math, runpy
source=Path("scripts/puerta_herreria_art_082.py").read_text(encoding="utf-8")
marker="# Fixed illumination and camera across both material experiments;"
assert marker in source, "V082 source changed, inspect export point"
# Build identical approved V082 geometry + art materials then stop BEFORE expensive 4 stills.
code=source.split(marker,1)[0]
ctx={"__name__":"__main__","__file__":"scripts/puerta_herreria_art_082.py"}
exec(compile(code,"scripts/puerta_herreria_art_082.py","exec"),ctx)
root=ctx["root"]; door=ctx["door"]; mat=ctx["metal_c"]
assert abs(root.location.x+.603)<.001, "Hinge origin drifted"
door.data.materials.clear()
door.data.materials.append(mat)
# Rebase all children from source x=-0.603 hinge to a local hinge at x=0.
root.location.x=0.0
bpy.context.view_layer.update()
assert abs(root.location.x)<1e-5
# Unused hidden preview cover geometry must not appear in GLB.
for child in list(root.children):
    if child.hide_render:
        bpy.data.objects.remove(child,do_unlink=True)
# Exact 4K original scan is preserved on disk, but shipping it at 4K loaded
# >58MB of source textures. WebGL downscale affects texture resolution ONLY.
# Target: 1K original ferric scan, 1.5K approved V082-B leaf, 768px trim.
# Preserve every material, geometry vertex and approved V082 colour treatment.
reduced=[]
seen=set()
for obj in tuple(root.children):
    if obj.type!="MESH": continue
    for material in obj.data.materials:
        if not material or not material.use_nodes: continue
        for node in material.node_tree.nodes:
            if node.type!="TEX_IMAGE" or not node.image:continue
            im=node.image
            if im.name in seen: continue
            seen.add(im.name)
            oldsize=tuple(im.size[:])
            if im.name.startswith("rusted-scratched-iron_4k"):
                dim=1024
            elif im.name.startswith("V082_B_subtle_"):
                dim=1536
            else:
                dim=768
            if im.size[0]>dim or im.size[1]>dim:
                im.scale(dim,dim)
                reduced.append([im.name,oldsize,[dim,dim]])
# Draw calls matter more than raw mesh count. Preserve all materials and UVs,
# join rigid door mesh pieces to a single glTF node. Parent hinge stays at 0.
mesh_children=[ob for ob in root.children if ob.type=="MESH"]
assert len(mesh_children)>100,("Unexpected missing hardware",len(mesh_children))
bpy.ops.object.select_all(action="DESELECT")
for ob in mesh_children: ob.select_set(True)
bpy.context.view_layer.objects.active=door
bpy.ops.object.join()
bpy.context.view_layer.update()
assert len([ob for ob in root.children if ob.type=="MESH"])==1
assert door.parent is root
# Keep the root as independent animation pivot and export joined leaf as child.
bpy.ops.object.select_all(action='DESELECT')
root.select_set(True);door.select_set(True)
bpy.context.view_layer.objects.active=root
out=Path("public/models/door-herrero-v082-b")
out.mkdir(parents=True,exist_ok=True)
target=out/"door-herrero-v082-b.glb"
bpy.ops.export_scene.gltf(filepath=str(target.resolve()),export_format="GLB",
     use_selection=True,export_cameras=False,export_lights=False,
     export_yup=True,export_materials="EXPORT",export_normals=True,export_texcoords=True)
assert target.is_file() and target.stat().st_size>100000
# Check GLB header and embedded JSON mesh count as an additional safeguard.
import struct
with target.open('rb') as f:
    header=f.read(20)
    magic,version,size,json_len,json_magic=struct.unpack('<4sIIII',header)
    assert magic==b'glTF' and version==2 and size==target.stat().st_size
    assert json_magic==0x4E4F534A
    data=json.loads(f.read(json_len))
assert len(data.get("meshes",[]))==1, ("BATCHED_DOOR_MESH_NOT_FOUND",len(data.get("meshes",[])))
assert len(data["meshes"][0].get("primitives",[]))>=4
assert len(data.get("materials",[]))>=3
audit={
 "version":"V082-B", "source":"scripts/puerta_herreria_art_082.py",
 "artist_approval":"visual approved as preferred V082-B",
 "door_width_source_m":1.20,"door_height_source_m":2.31,
 "hinge":"left; rotation around local origin", "handle":"right",
 "proposed_game_swing":"outward toward plaza, -92 degrees around Y",
 "geometry_modified":False, "ornaments_modified":False,
 "source_pivot_corrected_to_origin":True,
 "model_scale_game":[2.18/1.20,1,2.18/1.20],
 "gltf_mesh_count":len(data["meshes"]),
 "materials":len(data["materials"]),
 "triangle_budget_target":25000,
 "glb_bytes":target.stat().st_size,
 "sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
 "downsampled_export_only_textures":reduced,
 "batched_draw_meshes":len(data["meshes"]),
 "browser_validated":False
}
(out/"audit.json").write_text(json.dumps(audit,indent=2,ensure_ascii=False))
print("EXPORT_V082_B_SUCCESS",json.dumps(audit,ensure_ascii=False),flush=True)
