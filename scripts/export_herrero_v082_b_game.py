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
# Downsample ONLY ancillary metal maps to 1K; full 2K V082 leaf remains untouched.
reduced=[]
for obj in root.children:
    for material in obj.data.materials if getattr(obj,"data",None) and hasattr(obj.data,"materials") else ():
        if material==mat or not material or not material.use_nodes: continue
        for node in material.node_tree.nodes:
            if node.type=="TEX_IMAGE" and node.image and node.image.size[0]>1024:
                if node.image.name.startswith(("iron_v028_","copper_brass_v028_")):
                    node.image.scale(1024,1024)
                    reduced.append(node.image.name)
# Remove cameras, lights and source world from export selection.
bpy.ops.object.select_all(action='DESELECT')
root.select_set(True)
selected=[root]
for child in root.children:
    if child.type=="MESH":
        child.select_set(True); selected.append(child)
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
assert len(data.get("meshes",[]))>12, ("NO_HARDWARE_MESHES",len(data.get("meshes",[])))
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
 "reduced_ancillary_maps":sorted(set(reduced)),
 "browser_validated":False
}
(out/"audit.json").write_text(json.dumps(audit,indent=2,ensure_ascii=False))
print("EXPORT_V082_B_SUCCESS",json.dumps(audit,ensure_ascii=False),flush=True)
