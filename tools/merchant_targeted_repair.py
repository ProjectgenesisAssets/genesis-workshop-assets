# Targeted geometry cleanup for the public Meshy merchant, baseline = 108652 triangles.
# Blender 4.x, deterministic, no texture painting, no deformation or decimation.
import bpy, bmesh, json, math, os, sys
from collections import defaultdict
from mathutils import Vector
from pathlib import Path

argv=sys.argv[sys.argv.index("--")+1:]
source,out=argv[0],Path(argv[1])
out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=source)
models=[o for o in bpy.context.scene.objects if o.type=="MESH"]
assert len(models)==1, f"Expected 1 model mesh, got {len(models)}"
mesh=models[0]
mesh.name="ProjectGenesis_Mercader_Reparado"
data=mesh.data
before_tris=sum(len(p.vertices)-2 for p in data.polygons)
vtx=len(data.vertices)
print("BEFORE_TRIS",before_tris,"VERTICES",vtx,flush=True)
assert 108500<=before_tris<=108800
co=[v.co[:] for v in data.vertices]
n=len(co)
parent=list(range(n))
def root(x):
    while parent[x]!=x:
        parent[x]=parent[parent[x]]
        x=parent[x]
    return x
def union(x,y):
    a,b=root(x),root(y)
    if a!=b:parent[b]=a
for poly in data.polygons:
    v=poly.vertices
    for i in range(1,len(v)):
        union(v[0],v[i])
groups=defaultdict(list)
verts=defaultdict(set)
for p in data.polygons:
    component=root(p.vertices[0])
    groups[component].append(p.index)
    verts[component].update(p.vertices)
picked=[]
face_ids=[]
for component,faces in groups.items():
    vv=[mesh.matrix_world @ Vector(co[i]) for i in verts[component]]
    lo=[min(v[axis] for v in vv) for axis in range(3)]
    hi=[max(v[axis] for v in vv) for axis in range(3)]
    # glTF is Y-up, Blender is Z-up. Transform source bounds (x,y,z)
    # into Blender world (x,-z,y); never use local-space thresholds.
    if (
      -.311 <= lo[0] and hi[0] <= -.281 and
      -.033 <= lo[1] and hi[1] <= .017 and
      .150 <= lo[2] and hi[2] <= .267 and
      2 <= len(faces) <= 40
    ):
        face_ids.extend(faces)
        picked.append({"triangles":len(faces),"min":[round(x,5) for x in lo],"max":[round(x,5) for x in hi]})
print("OBJECT_MATRIX",str(mesh.matrix_world),flush=True)
print("WORLD_BBOX",[(min((mesh.matrix_world @ Vector(c))[i] for c in mesh.bound_box),max((mesh.matrix_world @ Vector(c))[i] for c in mesh.bound_box)) for i in range(3)],flush=True)
print("COMPONENTS_MATCHED",json.dumps(picked),flush=True)
# Require exactly the six previously diagnosed connected-component shards.
assert len(picked)==6 and len(face_ids)==127, "Geometry layout changed; refusing unsafe repair."
bm=bmesh.new()
bm.from_mesh(data)
bm.faces.ensure_lookup_table()
bm.verts.ensure_lookup_table()
faces_to_delete=[bm.faces[i] for i in face_ids]
bmesh.ops.delete(bm,geom=faces_to_delete,context="FACES")
orphan=[v for v in bm.verts if not v.link_faces]
if orphan:bmesh.ops.delete(bm,geom=orphan,context="VERTS")
bm.to_mesh(data)
bm.free()
data.update()
after_tris=sum(len(p.vertices)-2 for p in data.polygons)
assert after_tris==before_tris-127
# Preserve original texture/material UV and do not recalculate normals.
assert len(data.materials)==1
bpy.ops.object.select_all(action="DESELECT")
mesh.select_set(True)
bpy.context.view_layer.objects.active=mesh
dst=out/"ProjectGenesis_Mercader_Reparado_108525.glb"
bpy.ops.export_scene.gltf(filepath=str(dst),export_format="GLB",use_selection=True,
    export_apply=False,export_texcoords=True,export_normals=True,export_materials="EXPORT")
report={"source_triangles":before_tris,"result_triangles":after_tris,"removed_triangles":127,
        "removed_connected_components":len(picked),"method":"Remove isolated floating shard only",
        "unchanged_geometry":"All other vertices, UVs and mesh faces; no decimation",
        "note":"Other black texture/shadow details may persist; inspect renders",
        "component_boxes":picked}
(out/"repair_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("REPAIR_REPORT",json.dumps(report),flush=True)

# Controlled real Cycles renders - compare the same cameras/light/material on
# both original candidate and fixed candidate, no image generation.
original=mesh.copy()
original.data=bpy.data.meshes.new("Original_Candidate_Mesh")
# Load pristine baseline separately to avoid Blender data copying selected geometry.
bpy.ops.import_scene.gltf(filepath=source)
allmeshes=[o for o in bpy.context.scene.objects if o.type=="MESH" and o!=mesh]
assert len(allmeshes)==1
before=allmeshes[0]
before.name="Before_repair_original_108652"
# Remove our unused copy without linking.
bpy.data.meshes.remove(original.data)

corners=[mesh.matrix_world @ Vector(v) for v in mesh.bound_box]
mn=Vector([min(v[i] for v in corners) for i in range(3)])
mx=Vector([max(v[i] for v in corners) for i in range(3)])
center=(mn+mx)*.5
height=mx.z-mn.z
span=max(*(mx[i]-mn[i] for i in range(3)))
world=bpy.data.worlds.new("Soft Studio World")
bpy.context.scene.world=world
world.use_nodes=True
world.node_tree.nodes.get("Background").inputs["Color"].default_value=(.32,.38,.45,1)
world.node_tree.nodes.get("Background").inputs["Strength"].default_value=.7
def light(name,pos,power,size):
    objd=bpy.data.lights.new(name,"AREA")
    obj=bpy.data.objects.new(name,objd)
    bpy.context.collection.objects.link(obj)
    obj.location=center+Vector((pos[0]*span,pos[1]*span,pos[2]*span))
    obj.rotation_euler=(center-obj.location).to_track_quat("-Z","Y").to_euler()
    objd.energy=power
    objd.shape="DISK"
    objd.size=size*span
light("Key softbox",(-1.5,-2,2.4),700,3)
light("Fill softbox",(2,-.8,1),420,3)
light("Rim softbox",(.5,2,2),850,2.2)
scene=bpy.context.scene
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=30
scene.render.threads_mode="FIXED"
scene.render.threads=4
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGBA"
scene.render.film_transparent=True
scene.render.resolution_percentage=100
scene.view_settings.view_transform="AgX"
bpy.ops.object.camera_add()
cam=bpy.context.object
scene.camera=cam
cam.data.type="ORTHO"
def setcam(degrees,target,zoom=1.48):
    ang=math.radians(degrees)
    d=span*3.3
    cam.location=center+Vector((d*math.sin(ang),-d*math.cos(ang),d*.14))
    target=center+Vector(target)
    cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.ortho_scale=span*zoom
def render(filename,ob,angle,zoom=1.48,target=(0,0,0.06),w=880,h=1040):
    for o in (before,mesh):o.hide_render=o!=ob
    setcam(angle,tuple(x*span for x in target),zoom)
    scene.render.resolution_x=w
    scene.render.resolution_y=h
    scene.render.filepath=str(out/filename)
    bpy.ops.render.render(write_still=True)
    print("RENDERED",filename,flush=True)
for angle in (0,45,90):
    for obj,name in ((before,"before"),(mesh,"repaired")):
        render(f"merchant_{name}_{angle}.png",obj,angle)
for obj,name in ((before,"before"),(mesh,"repaired")):
    # Close-up around the waist; same framing.
    render(f"waist_{name}.png",obj,0,zoom=.55,target=(0,0,.01),w=1000,h=780)
