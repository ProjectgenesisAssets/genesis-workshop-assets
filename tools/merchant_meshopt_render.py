"""Render the untouched V01 and gltfpack variants with identical Cycles settings."""
import bpy,sys,math,json,os
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index("--")+1:]
src=Path(args[0]).resolve()
directory=Path(args[1]).resolve()
out=Path(args[2]).resolve()
out.mkdir(exist_ok=True,parents=True)
scene=bpy.context.scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
paths=[("v01",src)]+[(p.stem,p) for p in sorted(directory.glob("*.glb"))]
objects={}
for tag,path in paths:
    pre=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes=[o for o in bpy.data.objects if o not in pre and o.type=="MESH"]
    assert len(meshes)==1,(tag,len(meshes))
    objects[tag]=meshes[0]
    print("IMPORTED",tag,path.stat().st_size,len(meshes[0].data.polygons),flush=True)

base=objects["v01"]
corners=[base.matrix_world@Vector(v) for v in base.bound_box]
mn=Vector([min(v[i] for v in corners) for i in range(3)])
mx=Vector([max(v[i] for v in corners) for i in range(3)])
center=(mn+mx)*.5
span=max(mx[i]-mn[i] for i in range(3))
height=mx.z-mn.z
world=bpy.data.worlds.new("Clean Studio")
scene.world=world
world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(.32,.38,.45,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.7
for name,pos,power,size in [
  ("Key",(-1.5,-2,2.4),700,3),("Fill",(2,-.8,1),420,3),("Rim",(.5,2,2),850,2.2)]:
    data=bpy.data.lights.new(name,"AREA")
    o=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(o)
    o.location=center+Vector((pos[0]*span,pos[1]*span,pos[2]*span))
    o.rotation_euler=(center-o.location).to_track_quat("-Z","Y").to_euler()
    data.energy=power
    data.size=size*span
    data.shape="DISK"
bpy.ops.object.camera_add()
cam=bpy.context.object
scene.camera=cam
cam.data.type="ORTHO"
cam.data.ortho_scale=span*1.48
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=int(os.environ.get("MERCHANT_SAMPLES","25"))
scene.render.threads_mode="FIXED"
scene.render.threads=4
scene.view_layers[0].cycles.use_denoising=False
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGBA"
scene.render.film_transparent=True
scene.render.resolution_x=int(os.environ.get("MERCHANT_WIDTH","650"))
scene.render.resolution_y=int(os.environ.get("MERCHANT_HEIGHT","820"))
scene.view_settings.view_transform="AgX"
for deg in (0,45,90,180,270):
    angle=math.radians(deg)
    d=span*3.3
    cam.location=center+Vector((d*math.sin(angle),-d*math.cos(angle),d*.14))
    aim=center+Vector((0,0,.06*height))
    cam.rotation_euler=(aim-cam.location).to_track_quat("-Z","Y").to_euler()
    for tag,obj in objects.items():
        for candidate in objects.values():
            candidate.hide_render=(candidate!=obj)
        scene.render.filepath=str(out/f"{tag}_{deg}.png")
        bpy.ops.render.render(write_still=True)
        print("RENDER",tag,deg,flush=True)
