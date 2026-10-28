"""V027 art-review comparison. Run only in Blender 4.5.13 GitHub Actions."""
import os, bpy
from pathlib import Path
from mathutils import Vector
model=Path(os.environ["PG_COMPARE_MODEL"])
output=Path(os.environ["PG_COMPARE_OUTPUT"])
assert model.exists() and model.read_bytes()[:4]==b"glTF",model
output.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(model))
meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
assert len(meshes)>=100,len(meshes)
def area(loc,power,size):
    light=bpy.data.lights.new("Matched studio area","AREA")
    obj=bpy.data.objects.new("Matched studio area",light)
    bpy.context.collection.objects.link(obj)
    obj.location=loc
    light.energy=power;light.shape="DISK";light.size=size
    obj.rotation_euler=(Vector((0,0,1.15))-obj.location).to_track_quat("-Z","Y").to_euler()
area((-3,-4,4),1120,4)
area((4.8,1.1,2.9),850,3)
area((1,-2,3),195,2.4)
area((-2,4.5,3.2),570,4)
bpy.ops.object.camera_add(location=(2.3,-5,1.7))
camera=bpy.context.object
camera.rotation_euler=(Vector((0,0,1.15))-camera.location).to_track_quat("-Z","Y").to_euler()
camera.data.type="ORTHO";camera.data.ortho_scale=2.53
sc=bpy.context.scene
sc.camera=camera
sc.render.engine="CYCLES"
sc.cycles.samples=int(os.environ.get("PG_CYCLES_SAMPLES","36"))
bpy.context.view_layer.cycles.use_denoising=True
sc.render.resolution_x=1000;sc.render.resolution_y=1333
sc.render.resolution_percentage=100
sc.render.film_transparent=True
sc.view_settings.view_transform="AgX"
try:
    sc.use_nodes=True
    comp=sc.node_tree
    comp.nodes.clear()
    source=comp.nodes.new("CompositorNodeRLayers")
    glare=comp.nodes.new("CompositorNodeGlare")
    glare.glare_type="FOG_GLOW";glare.quality="HIGH"
    glare.threshold=1.6;glare.size=7;glare.mix=-.62
    end=comp.nodes.new("CompositorNodeComposite")
    comp.links.new(source.outputs["Image"],glare.inputs["Image"])
    comp.links.new(glare.outputs["Image"],end.inputs["Image"])
except Exception as e:
    print("BLOOM_DISABLED",e,flush=True)
    sc.use_nodes=False
sc.render.filepath=str(output)
sc.render.image_settings.file_format="PNG"
bpy.ops.render.render(write_still=True)
assert output.exists() and output.stat().st_size>10000
print("COMPARE_RENDER_OK",str(model),str(output),len(meshes),flush=True)
