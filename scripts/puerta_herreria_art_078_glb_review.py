"""V078: non-destructive PlayCanvas GLB export and inspection of V077 approved V011 mesh.

Runs the proven V077 Blender source in the same scene and exports ONLY the
visible door hierarchy with the B blackened-iron material. No new geometry,
scans, shaders, or artistic approvals are inferred.
"""
from pathlib import Path
import bpy
import hashlib
import json
import runpy
import struct

ctx=runpy.run_path("scripts/puerta_herreria_art_077.py")
door=ctx["door"]
root=ctx["root"]
metal_b=ctx["metal_b"]
baseout=Path("output_blacksmith_door_art_077")
out=Path("output_blacksmith_door_art_078")
out.mkdir(parents=True,exist_ok=True)

# Source renderer produces its own comparisons; the reviewed candidate here is B.
assert door.data.materials and door.data.materials[0]==metal_b, (
    "V077_FINAL_MATERIAL_DRIFT", [m.name for m in door.data.materials])
assert metal_b.name=="V077_TrueForgedIron_B", metal_b.name

# Fingerprint the actual approved mesh before and after export.
def geometry_fingerprint(ob):
    h=hashlib.sha256()
    for vert in ob.data.vertices:
        h.update(struct.pack("<3f",float(vert.co.x),float(vert.co.y),float(vert.co.z)))
    for poly in ob.data.polygons:
        h.update(struct.pack("<I",len(poly.vertices)))
        for vi in poly.vertices: h.update(struct.pack("<I",int(vi)))
    return h.hexdigest()

before=geometry_fingerprint(door)
bpy.ops.object.select_all(action="DESELECT")
root.select_set(True)
selected=[]
excluded=[]
for ob in root.children:
    if ob.type!="MESH":
        excluded.append({"name":ob.name,"why":"not_mesh"})
        continue
    if ob.hide_render:
        excluded.append({"name":ob.name,"why":"V077_hidden_cover"})
        continue
    assert ob.data.uv_layers.active is not None, ("MISSING_UV",ob.name)
    assert all(slot.material is not None for slot in ob.material_slots), ("EMPTY_MATERIAL",ob.name)
    ob.select_set(True)
    selected.append(ob)
assert len(selected)>=12, ("UNEXPECTED_TOO_FEW_PARTS",len(selected))
bpy.context.view_layer.objects.active=door
filepath=out/"Blacksmith_Door_V078_Blackened_Iron_Review.glb"
bpy.ops.export_scene.gltf(
    filepath=str(filepath.resolve()),
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
)
assert filepath.is_file() and filepath.stat().st_size>2048
after=geometry_fingerprint(door)
assert before==after, "EXPORT_MUTATED_APPROVED_V011_LEAF"

with filepath.open("rb") as f:
    header=f.read(12)
    magic,version,total_length=struct.unpack("<4sII",header)
    assert magic==b"glTF" and version==2
    assert total_length==filepath.stat().st_size, "GLB_LENGTH_DISAGREEMENT"
    chunk_len,chunk_kind=struct.unpack("<I4s",f.read(8))
    assert chunk_kind==b"JSON"
    document=json.loads(f.read(chunk_len).decode("utf-8").rstrip(" \x00"))

materials=document.get("materials",[])
meshdata=document.get("meshes",[])
images=document.get("images",[])
assert meshdata and materials and images, "GLB_MISSING_MESH_MATERIAL_OR_IMAGE"
matnames=[m.get("name","") for m in materials]
assert any("TrueForgedIron_B" in s for s in matnames), (
    "BLACK_IRON_MATERIAL_NOT_EXPORTED",matnames)
assert any("normalTexture" in m for m in materials), "GLTF_MISSING_NORMAL_TEXTURE"
assert any(m.get("pbrMetallicRoughness",{}).get("metallicRoughnessTexture")
           for m in materials), "GLTF_MISSING_MR_MAP"

dg=bpy.context.evaluated_depsgraph_get()
triangles=0
for ob in selected:
    ev=ob.evaluated_get(dg)
    me=ev.to_mesh()
    me.calc_loop_triangles()
    triangles+=len(me.loop_triangles)
    ev.to_mesh_clear()

report={
    "version":"V078",
    "operation":"first GLB compatibility candidate based strictly on V077 final B material",
    "reference_branch":"production/door-herrero",
    "approved_geometry":"V011_UNCHANGED",
    "source_script":"scripts/puerta_herreria_art_077.py",
    "source_material":"V077_TrueForgedIron_B",
    "door_mesh_sha256_before":before,
    "door_mesh_sha256_after":after,
    "geometry_unchanged":before==after,
    "visible_mesh_parts":len(selected),
    "excluded_hidden_or_nonmesh":excluded,
    "evaluated_triangles":triangles,
    "triangle_budget_target":25000,
    "triangle_budget_met":triangles<=25000,
    "glb_bytes":filepath.stat().st_size,
    "glb_meshes":len(meshdata),
    "glb_materials":matnames,
    "glb_images":len(images),
    "glb_normal_textures":sum(1 for m in materials if m.get("normalTexture")),
    "glb_metallic_roughness_textures":sum(
        1 for m in materials if m.get("pbrMetallicRoughness",{}).get("metallicRoughnessTexture")),
    "playcanvas_import_tested":False,
    "artistic_approval":"PENDING",
    "note":"Technical GLB export is not visual QA or GPU performance certification"
}
(out/"V078_GLTF_AUDIT.json").write_text(
    json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
print("V078_GLTF_AUDIT",json.dumps(report,ensure_ascii=False),flush=True)
