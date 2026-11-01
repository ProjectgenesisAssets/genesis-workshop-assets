#!/usr/bin/env python3
"""Separate V012 real photogrammetric wood mesh experiment. Never auto-approve species.
Import actual 3D scan, decimate, generate five views and independent PlayCanvas GLB."""
import bpy,math,json,os,pathlib,struct
from mathutils import Vector
K=os.environ["ASSET_KIND"]
scan={"dry-oak-wood":"dead_tree_trunk","dry-ash-wood":"dead_tree_trunk_02"}[K]
source=pathlib.Path("sources")/K/"photogrammetry_v012"
manifest=json.loads((source/"manifest.json").read_text())
out=pathlib.Path("output")/K
out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str((source/(scan+"_2k.gltf")).resolve()))
objects=[o for o in bpy.context.scene.objects if o.type=="MESH"]
if not objects:raise RuntimeError("3D photogrammetry source did not import a mesh")
# Reduce the real scan topology to a WebGL-suitable budget, without inventing shapes.
src_tri=sum(sum(len(f.vertices)-2 for f in o.data.polygons) for o in objects)
ratio=min(1,8600/max(src_tri,1))
if ratio<.99:
 for o in objects:
  bpy.ops.object.select_all(action="DESELECT");o.select_set(True)
  bpy.context.view_layer.objects.active=o
  mod=o.modifiers.new("V012_scan_retessellation","DECIMATE")
  mod.ratio=ratio
  bpy.ops.object.modifier_apply(modifier=mod.name)
# Two independently transformed copies retain the real surface complexity.
# All cameras are built from the actual object bounds.
def bounds(oo):
 corners=[o.matrix_world @ Vector(c) for o in oo for c in o.bound_box]
 return [min(v[i] for v in corners) for i in range(3)],[max(v[i] for v in corners) for i in range(3)]
lo,hi=bounds(objects);center=Vector([(a+b)*.5 for a,b in zip(lo,hi)])
spans=[b-a for a,b in zip(lo,hi)];major=max(range(3),key=lambda i:spans[i])
# Rotate the long axis to horizontal X and fit roughly 1.4 m.
scale=1.45/max(spans[major],.01)
from mathutils import Matrix
axis=[Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))][major]
q=axis.rotation_difference(Vector((1,0,0)))
rot=q.to_matrix().to_4x4()
transform=Matrix.Diagonal((scale,scale,scale,1)) @ Matrix.Translation(-center)
base=Matrix.Diagonal(((.87 if K=='dry-oak-wood' else .91), (1.72 if K=='dry-oak-wood' else 1.32), (1.72 if K=='dry-oak-wood' else 1.32), 1)) @ rot @ transform
for o in objects:
 o.matrix_world=base @ o.matrix_world
bpy.context.view_layer.update()
# A three-piece irregular bundle, rather than two mechanically identical parallel scans.
# Triangular stacking, varied yaw and roll make the captured bark physically readable.
copies=[]
for variation,offset,azimuth,roll in [
    (1,(-.11,.21,.025),-.19,.11),
    (2,(.14,.045,.19),.23,-.15)]:
 for original in objects:
  dupe=original.copy();dupe.data=original.data.copy()
  bpy.context.collection.objects.link(dupe)
  dupe.name=original.name+"_independent_scanned_piece_"+str(variation)
  dupe.matrix_world=original.matrix_world.copy()
  dupe.rotation_euler.rotate_axis("Z",azimuth)
  dupe.rotation_euler.rotate_axis("X",roll)
  dupe.location+=Vector(offset)
  copies.append(dupe)
for original in objects:
 original.location+=Vector((-.04,-.16,-.02))
allmesh=objects+copies
total_tris=sum(sum(len(f.vertices)-2 for f in o.data.polygons) for o in allmesh)
if total_tris>30000:raise RuntimeError("Real scan over 30k-triangle WebGL budget: "+str(total_tris))
# Retain the source photogrammetric photographic materials. Tint minimally only
# to suggest a visual dry wood variation; this does NOT identify botanical species.
for m in bpy.data.materials:
 if not m.use_nodes:continue
 bs=m.node_tree.nodes.get("Principled BSDF")
 if not bs:continue
 links=m.node_tree.links;nodes=m.node_tree.nodes
 incoming=bs.inputs["Base Color"].links
 if incoming:
  src_link=incoming[0].from_socket
  mix=nodes.new("ShaderNodeMixRGB");mix.blend_type="MULTIPLY"
  mix.inputs[0].default_value=1.0
  mix.inputs[2].default_value=((.86,.81,.74,1) if K=="dry-oak-wood" else (.94,.88,.77,1))
  links.new(src_link,mix.inputs[1]);links.new(mix.outputs["Color"],bs.inputs["Base Color"])
 bs.inputs["Metallic"].default_value=0
# Studio lighting, no environment maps required. Five reproducible render angles.
scene=bpy.context.scene
scene.render.engine="CYCLES";scene.cycles.samples=38;scene.cycles.use_denoising=False
for vl in scene.view_layers:vl.cycles.use_denoising=False
scene.render.resolution_x=900;scene.render.resolution_y=900
scene.render.resolution_percentage=100;scene.render.film_transparent=True
scene.render.image_settings.file_format="PNG";scene.render.image_settings.color_mode="RGBA"
bpy.ops.object.camera_add()
cam=bpy.context.object;scene.camera=cam
cam.data.type="ORTHO";cam.data.ortho_scale=2.0
for loc,energy,size in [((3,-4,5),730,4.2),((-3,1,4),480,3.4)]:
 bpy.ops.object.light_add(type="AREA",location=loc)
 l=bpy.context.object;l.data.energy=energy;l.data.size=size
lo,hi=bounds(allmesh)
target=Vector([(lo[i]+hi[i])/2 for i in range(3)])
for name,off in [("three_quarter",(2.6,-3.4,2.3)),("front",(0,-4.4,1.0)),
                 ("side",(4.4,0,1.0)),("top",(0,0,5)),("detail",(1.3,-2.1,1.6))]:
 offset=Vector(off)
 cam.location=target+offset
 cam.rotation_euler=(-offset).to_track_quat("-Z","Y").to_euler()
 cam.data.ortho_scale=1.05 if name=="detail" else 2.0
 scene.render.filepath=str(out/(name+".png"))
 bpy.ops.render.render(write_still=True)
bpy.ops.object.select_all(action="DESELECT")
for o in allmesh:o.select_set(True)
bpy.context.view_layer.objects.active=allmesh[0]
bpy.ops.export_scene.gltf(filepath=str(out/(K+"_master.glb")),export_format="GLB",use_selection=True)
# Downsample every photogrammetric albedo/ARM/normal consistently for browser memory.
used={}
for m in bpy.data.materials:
 if not m.use_nodes:continue
 for node in m.node_tree.nodes:
  if node.type!="TEX_IMAGE" or node.image is None:continue
  im=node.image;key=im.as_pointer()
  if key not in used:
   small=im.copy();small.name=im.name+"_V012_web_1k"
   small.scale(1024,max(1,round(1024*im.size[1]/im.size[0])))
   small.filepath_raw=str((out/(small.name+".jpg")).resolve())
   small.file_format="JPEG";small.save()
   used[key]=small
  node.image=used[key]
bpy.ops.export_scene.gltf(filepath=str(out/(K+".glb")),export_format="GLB",use_selection=True)
report={"asset":K,"version":"V012_photogrammetry_candidate","photogrammetry":True,
 "license":"CC0-1.0","species_verified":False,"source":manifest["asset_page"],
 "scanned_triangles_before_decimation":src_tri,"triangles_mesh":total_tris,
 "glb_bytes":(out/(K+".glb")).stat().st_size,
 "master_bytes":(out/(K+"_master.glb")).stat().st_size,
 "quality_approved":False,"visual_score":None,
 "note":"Three individually transformed CC0-scanned geometry pieces, not species authenticated. Candidate for artistic review only."}
(out/"validation.json").write_text(json.dumps(report,indent=2))
print("V012_REAL_PHOTOGRAMMETRY "+json.dumps(report))
