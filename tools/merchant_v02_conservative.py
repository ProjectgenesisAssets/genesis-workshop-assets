"""Project Genesis merchant V02 safe mesh trial.

Input is the APPROVED merchant V01 (108525 tris), never overwritten.
All candidate decimations begin from the same V01.
A separate QA program selects a candidate with per-region image gates.
Only a passing candidate is allowed to export.
"""
import bpy, sys, os, math, json
from pathlib import Path
from mathutils import Vector

args=sys.argv[sys.argv.index("--")+1:]
mode=args[0]
source=Path(args[1]).resolve()
out=Path(args[2]).resolve()
out.mkdir(parents=True,exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(source))
meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
assert len(meshes)==1, "Expected exactly 1 character mesh."
base=meshes[0]
base.name="Merchant_V01_Approved_ReadOnly"
tris=lambda obj:sum(len(face.vertices)-2 for face in obj.data.polygons)
assert tris(base)==108525,f"Unexpected source topology: {tris(base)} (V01 requires 108525)"
assert len(base.data.materials)==1
assert len(base.data.uv_layers)>=1

corner=[base.matrix_world @ Vector(v) for v in base.bound_box]
mn=Vector([min(v[i] for v in corner) for i in range(3)])
mx=Vector([max(v[i] for v in corner) for i in range(3)])
center=(mn+mx)/2
span=max(mx[i]-mn[i] for i in range(3))
height=mx.z-mn.z
assert span>0

world=bpy.data.worlds.new("merchant_softbox")
bpy.context.scene.world=world
world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(.32,.38,.45,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.7

def addlight(name,pos,power,size):
    data=bpy.data.lights.new(name,"AREA")
    obj=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    obj.location=center+Vector((pos[0]*span,pos[1]*span,pos[2]*span))
    obj.rotation_euler=(center-obj.location).to_track_quat("-Z","Y").to_euler()
    data.energy=power
    data.size=size*span
    data.shape="DISK"
addlight("Key",(-1.5,-2,2.4),700,3)
addlight("Fill",(2,-.8,1),420,3)
addlight("Rim",(.5,2,2),850,2.2)

scene=bpy.context.scene
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.render.threads_mode="FIXED"
scene.render.threads=4
scene.view_layers[0].cycles.use_denoising=False
scene.render.film_transparent=True
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGBA"
scene.render.resolution_percentage=100
scene.view_settings.view_transform="AgX"

bpy.ops.object.camera_add()
cam=bpy.context.object
scene.camera=cam
cam.data.type="ORTHO"
cam.data.ortho_scale=span*1.48
def angle_cam(deg):
    a=math.radians(deg)
    d=span*3.3
    cam.location=center+Vector((d*math.sin(a),-d*math.cos(a),d*.14))
    aim=center+Vector((0,0,.06*height))
    cam.rotation_euler=(aim-cam.location).to_track_quat("-Z","Y").to_euler()

def render(obj,path,angle,samples,width,h):
    base.hide_render=(obj is not base)
    if obj is not base:obj.hide_render=False
    angle_cam(angle)
    scene.cycles.samples=samples
    scene.render.resolution_x=width
    scene.render.resolution_y=h
    scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True)
    print("RENDERED",path,flush=True)

def make_decimation(ratio):
    obj=base.copy()
    obj.data=base.data.copy()
    bpy.context.collection.objects.link(obj)
    obj.matrix_world=base.matrix_world.copy()
    obj.name=f"merchant_{ratio:.2f}"
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active=obj
    mod=obj.modifiers.new("Safe_reduction","DECIMATE")
    mod.decimate_type="COLLAPSE"
    mod.ratio=ratio
    mod.use_collapse_triangulate=True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    assert len(obj.data.uv_layers)>=1
    return obj

angles=[0,45,90,180,270]
if mode=="candidates":
    for angle in angles:
        render(base,out/f"base_{angle}.png",angle,15,480,600)
    metrics=[]
    for ratio in (.95,.90,.85,.80,.75,.70,.65,.60):
        c=make_decimation(ratio)
        row={"ratio":ratio,"triangles":tris(c),"vertices":len(c.data.vertices),
             "material_count":len(c.data.materials),"uv_layer_count":len(c.data.uv_layers)}
        metrics.append(row)
        print("CANDIDATE",json.dumps(row),flush=True)
        for angle in angles:
            render(c,out/f"r{ratio:.2f}_{angle}.png",angle,15,480,600)
        bpy.data.objects.remove(c,do_unlink=True)
    (out/"geometry_candidates.json").write_text(json.dumps(metrics,indent=2))
elif mode=="final":
    selected=json.loads((out/"selected.json").read_text())
    assert selected.get("passed"),"QA did not approve a candidate; refusing export"
    ratio=float(selected["ratio"])
    c=make_decimation(ratio)
    assert tris(c)==selected["triangles"]
    c.name="ProjectGenesis_Mercader_V02_SafeCandidate"
    bpy.ops.object.select_all(action="DESELECT")
    c.select_set(True)
    bpy.context.view_layer.objects.active=c
    dst=out/"ProjectGenesis_Mercader_V02_Candidato.glb"
    bpy.ops.export_scene.gltf(filepath=str(dst),export_format="GLB",use_selection=True,
            export_texcoords=True,export_normals=True,export_materials="EXPORT")
    for angle in angles:
        render(base,out/f"final_original_{angle}.png",angle,48,900,1100)
        render(c,out/f"final_candidate_{angle}.png",angle,48,900,1100)
    print("EXPORTED",str(dst),dst.stat().st_size,"TRIANGLES",tris(c),flush=True)
else:raise RuntimeError("Unknown Blender mode "+mode)
