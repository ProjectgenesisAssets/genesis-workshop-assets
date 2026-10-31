#!/usr/bin/env python3
"""Consolidate static game-wall meshes by material without losing any triangles,
texture UVs, material data, or placed position. Only batches a WebGL copy.
Master Blender models and six Cycles renders remain unchanged.
Usage: blender -b --python scripts/batch_blacksmith_v010_for_webgl.py -- in.glb out.glb
"""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index("--")+1:]
assert len(args)==2,args
src,dst=map(Path,args)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(src))
bpy.context.view_layer.update()
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
assert len(meshes)>25, len(meshes)
before_triangles=sum(max(0,len(p.vertices)-2) for o in meshes for p in o.data.polygons)
before_faces=sum(len(o.data.polygons) for o in meshes)
before_uv=sum(len(o.data.uv_layers)>0 for o in meshes)
materials={}
for ob in meshes:
    # Every primitive in the source workshop asset has one assigned material.
    mats=[s.material for s in ob.material_slots if s.material]
    assert len(mats)==1,(ob.name,[m.name for m in mats])
    materials.setdefault(mats[0].name,[]).append(ob)

def mesh_bbox(objects):
    coords=[ob.matrix_world @ v.co for ob in objects for v in ob.data.vertices]
    return [[min(v[i] for v in coords) for i in range(3)],
            [max(v[i] for v in coords) for i in range(3)]]
before_box=mesh_bbox(meshes)
consolidated=[]
for group_name,group in materials.items():
    bpy.ops.object.select_all(action='DESELECT')
    for obj in group:obj.select_set(True)
    bpy.context.view_layer.objects.active=group[0]
    if len(group)>1:bpy.ops.object.join()
    joined=bpy.context.view_layer.objects.active
    joined.name="GENESIS_BATCH_"+group_name[:42]
    consolidated.append(joined)
bpy.context.view_layer.update()
after=[o for o in bpy.context.scene.objects if o.type=='MESH']
after_triangles=sum(max(0,len(p.vertices)-2) for o in after for p in o.data.polygons)
after_faces=sum(len(o.data.polygons) for o in after)
after_box=mesh_bbox(after)
assert before_triangles==after_triangles,(before_triangles,after_triangles)
assert before_faces==after_faces
assert len(after)<=len(materials)+1,(len(after),len(materials))
assert all(abs(before_box[k][i]-after_box[k][i])<.001 for k in range(2) for i in range(3)),(before_box,after_box)
# Texture-bearing materials require UVs; pure metal and mortar materials
# legitimately have no texture coordinates in the original GLB.
for ob in after:
    mats=[slot.material for slot in ob.material_slots if slot.material]
    needs_uv=any(m.use_nodes and any(n.type=='TEX_IMAGE' and n.image for n in m.node_tree.nodes) for m in mats)
    if needs_uv: assert len(ob.data.uv_layers)>0,("Missing texture UVs",ob.name)
bpy.ops.object.select_all(action='DESELECT')
for o in after:o.select_set(True)
bpy.context.view_layer.objects.active=after[0]
dst.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(dst),export_format="GLB",use_selection=True,
                          export_texcoords=True,export_normals=True)
assert dst.stat().st_size>1000
report={"status":"EXPERIMENTAL_WEBGL_BATCHED_UNAPPROVED",
        "source":str(src),"output":str(dst),
        "original_meshes":len(meshes),"batched_meshes":len(after),
        "triangles_before":before_triangles,"triangles_after":after_triangles,
        "faces_before":before_faces,"faces_after":after_faces,
        "material_groups":list(materials),"material_count":len(materials),
        "source_meshes_with_uv":before_uv,"output_meshes_with_uv":sum(bool(o.data.uv_layers) for o in after),
        "bounds_before":before_box,"bounds_after":after_box,
        "source_bytes":src.stat().st_size,"batched_bytes":dst.stat().st_size,
        "note":"Pure drawcall batching, no geometry resculpt, PlayCanvas FPS not yet tested"}
dst.with_suffix(".audit.json").write_text(json.dumps(report,indent=2),encoding="utf8")
print("GENESIS_BATCHED_WORKSHOP",json.dumps(report))
