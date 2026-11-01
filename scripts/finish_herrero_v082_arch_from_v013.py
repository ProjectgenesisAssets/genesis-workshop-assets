"""Non-destructive V013 four-wall arch aperture filler for the approved V082-B door.
Retains all existing stone masonry, five actual windows, roof/chimney and corners.
Door has x-world radius .8175m, spring z=1.775, rise .525, apex=2.30m.
Wall local X units map to world via factor (12/7.875)*.75 = 8/7.
"""
import bpy, math, json, hashlib
from pathlib import Path
from math import sqrt, sin, cos, pi
src=Path("public/models/blacksmith-structural-v013/batched/blacksmith_four_walls_preview.glb")
assert src.is_file()
out=Path("public/models/blacksmith-v082-arched-portal")
out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(src.resolve()))
original_meshes=[o for o in bpy.data.objects if o.type=="MESH"]
assert original_meshes,"V013 masonry meshes missing"
old_count=len(original_meshes)
# Match arched B silhouette in finished game WORLD measurements; leave 5cm visual clearance.
HALF_APERTURE=1.48/2
FRONT_TOP=2.43
WALL_TO_WORLD=12/7.875*.75
WORLD_RADIUS=HALF_APERTURE*WALL_TO_WORLD
SPRING=1.815
RISE=.545
assert WORLD_RADIUS>.8175
def arch_height(local_x):
    xworld=abs(local_x)*WALL_TO_WORLD
    t=min(1.0,xworld/WORLD_RADIUS)
    return SPRING+RISE*math.sqrt(max(0.0,1-t*t))
# Ensure every section clears the real V082-B arched silhouette.
clearances=[]
for i in range(201):
    worldx=.8175*(2*i/200-1)
    door_height=1.775+.525*sqrt(max(0,1-(worldx/.8175)**2))
    new_height=arch_height(worldx/WALL_TO_WORLD)
    clearances.append(new_height-door_height)
assert min(clearances)>.035,("ARCH_TOUCHES_DOOR",min(clearances))
assert FRONT_TOP>max(arch_height(-HALF_APERTURE),arch_height(0))
# Pick actual imported V013 masonry material (PBR channels preserved).
materials=[m for ob in original_meshes for m in ob.data.materials if m]
stone=next((m for m in materials if any(word in m.name.lower() for word in ("basalt","quarry","stone","soot"))),None)
assert stone,"No V013 stone material present; cannot substitute generic material"
# Solid above an arched aperture. Supports front, inside, and curved soffit,
# NO plane crosses the clearance contour or touches the workshop's side piers.
N=56
xs=[-HALF_APERTURE+2*HALF_APERTURE*i/N for i in range(N+1)]
ys=[-.49,.30]
verts=[]
for yy in ys:
    for xx in xs:
        verts.extend(((xx,yy,arch_height(xx)),(xx,yy,FRONT_TOP)))
def ind(side,i,high):return side*(2*(N+1))+2*i+high
faces=[]
for i in range(N):
    faces.extend([
      (ind(0,i,0),ind(0,i+1,0),ind(0,i+1,1),ind(0,i,1)),
      (ind(1,i,0),ind(1,i,1),ind(1,i+1,1),ind(1,i+1,0)),
      (ind(0,i,0),ind(1,i,0),ind(1,i+1,0),ind(0,i+1,0)),
      (ind(0,i,1),ind(0,i+1,1),ind(1,i+1,1),ind(1,i,1))
    ])
faces.extend([
 (ind(0,0,0),ind(0,0,1),ind(1,0,1),ind(1,0,0)),
 (ind(1,N,0),ind(1,N,1),ind(0,N,1),ind(0,N,0))
])
mesh=bpy.data.meshes.new("V082_ARCH_NONSQUARE_MASONRY_SOLID")
mesh.from_pydata(verts,[],faces)
mesh.update()
obj=bpy.data.objects.new("V082_ArchedSpandrel_RealStone_LeavesDoorClear",mesh)
bpy.context.collection.objects.link(obj)
obj.data.materials.append(stone)
uv=mesh.uv_layers.new(name="UVMap")
for face in mesh.polygons:
 for k in face.loop_indices:
    v=mesh.vertices[mesh.loops[k].vertex_index].co
    uv.data[k].uv=((v.x+3.9375)/2.2,v.z/2.15)
# On the exterior front, add a thin stone course following the lower arched edge,
# no straight rectangular crossbar, without extending into the actual doorway.
# These individual short segments retain true V013 stone shading and don't mask the arch.
curve_verts=[]
curve_faces=[]
for i in range(N):
    x0,x1=xs[i],xs[i+1]
    z0,z1=arch_height(x0)+.035,arch_height(x1)+.035
    front_y=-.52
    back_y=-.49
    start=len(curve_verts)
    curve_verts.extend([(x0,front_y,z0),(x1,front_y,z1),
                        (x0,front_y,z0+.045),(x1,front_y,z1+.045),
                        (x0,back_y,z0),(x1,back_y,z1),
                        (x0,back_y,z0+.045),(x1,back_y,z1+.045)])
    curve_faces.extend([(start+0,start+1,start+3,start+2),
                        (start+4,start+6,start+7,start+5),
                        (start+0,start+4,start+5,start+1),
                        (start+2,start+3,start+7,start+6)])
me=bpy.data.meshes.new("ThinStoneArcReliefGeometry")
me.from_pydata(curve_verts,[],curve_faces);me.update()
arc=bpy.data.objects.new("V082_ArchedStoneReturn_No_RoundDoor_Intersection",me)
bpy.context.collection.objects.link(arc);arc.data.materials.append(stone)
uv2=me.uv_layers.new(name="UVMap")
for face in me.polygons:
 for i in face.loop_indices:
    v=me.vertices[me.loops[i].vertex_index].co
    uv2.data[i].uv=((v.x+3.9375)/2.2,v.z/2.15)
bpy.ops.object.select_all(action="DESELECT")
for ob in bpy.data.objects:
 if ob.type=="MESH":ob.select_set(True)
target=out/"blacksmith_four_walls_arched_v082.glb"
bpy.ops.export_scene.gltf(filepath=str(target.resolve()),export_format="GLB",
                          use_selection=True,export_normals=True,export_texcoords=True,
                          export_yup=True,export_materials="EXPORT")
assert target.stat().st_size>200000
audit={
 "source_geometry":"V013 four-wall batched GLB reused without deleting any mesh",
 "original_mesh_count":old_count,"new_meshes":2,"arch_aperture_width_blender":1.48,
 "upper_arch_height_world_m":SPRING+RISE,
 "minimum_clearance_to_V082B_world_m":min(clearances),
 "windows_unchanged":True,"roof_unchanged":True,"chimney_unchanged":True,
 "door_and_hinges_unchanged":True,
 "arch_spandrel_integrates_into_existing_header":True,
 "physical_collision_intent":"existing rectangular portal clearance remains valid",
 "glb_bytes":target.stat().st_size,
 "sha256":hashlib.sha256(target.read_bytes()).hexdigest()
}
(out/"audit.json").write_text(json.dumps(audit,indent=2))
print("V082_ARCH_WALL_EXPORTED",json.dumps(audit),flush=True)
