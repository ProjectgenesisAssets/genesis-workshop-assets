"""Project Genesis: isolated 32-bit HDRI render of V020 caprino roughness-only candidate."""
import bpy, json, pathlib, hashlib
from mathutils import Vector
root=pathlib.Path("output/tanned-goatskin")
model=root/"V020_roughness_only"/"caprino_v020_roughness_master.glb"
hdri=pathlib.Path("/tmp/studio_small_09_2k.hdr")
assert model.is_file() and hdri.is_file()
before=hashlib.sha256(model.read_bytes()).hexdigest()
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(model.resolve()))
meshes=[ob for ob in bpy.context.scene.objects if ob.type=="MESH"]
assert len(meshes)>0
scene=bpy.context.scene
scene.render.engine="CYCLES"
scene.cycles.samples=64
scene.cycles.use_denoising=False
scene.render.resolution_x=1080
scene.render.resolution_y=1080
scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGBA"
scene.view_settings.view_transform="Standard"
scene.world=bpy.data.worlds.new("Genesis Studio HDRI 32bit")
scene.world.use_nodes=True
nodes=scene.world.node_tree.nodes
links=scene.world.node_tree.links
nodes.clear()
output=nodes.new("ShaderNodeOutputWorld")
background=nodes.new("ShaderNodeBackground")
env=nodes.new("ShaderNodeTexEnvironment")
env.image=bpy.data.images.load(str(hdri.resolve()))
assert env.image.file_format=="HDR",env.image.file_format
background.inputs["Strength"].default_value=.82
links.new(env.outputs["Color"],background.inputs["Color"])
links.new(background.outputs["Background"],output.inputs["Surface"])
camera_data=bpy.data.cameras.new("approved_v019_camera")
camera=bpy.data.objects.new("approved_v019_camera",camera_data)
scene.collection.objects.link(camera)
scene.camera=camera
camera_data.type="ORTHO"
focus=Vector((0,-.24,.18))
dest=root/"HDRI32_V020_RoughnessOnly"
dest.mkdir(parents=True,exist_ok=True)
views=[("three_quarter",(2.7,-3.2,2.5),1.90),("front",(0,-4,1.),1.90),("side",(4,0,1.),1.90),("top",(0,0,5.),1.90),("detail",(1.2,-2.3,1.1),.78)]
for name,point,scale in views:
    camera.location=point
    camera.rotation_euler=(focus-camera.location).to_track_quat("-Z","Y").to_euler()
    camera.data.ortho_scale=scale
    scene.render.image_settings.file_format="OPEN_EXR"
    scene.render.image_settings.color_depth="32"
    scene.render.filepath=str((dest/(name+".exr")).resolve())
    bpy.ops.render.render(write_still=True)
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.color_depth="8"
    bpy.data.images["Render Result"].save_render(str((dest/(name+".png")).resolve()),scene=scene)
after=hashlib.sha256(model.read_bytes()).hexdigest()
assert before==after
result={"asset":"tanned-goatskin","version":"V020_roughness_only","study":"HDRI 32-bit, +15/255 roughness green only","hdr":"studio_small_09_2k.hdr","format":"Radiance RGBE 32bpp input, 32-bit float EXR output","blender":bpy.app.version_string,"source_sha256":before,"candidate_glb_unchanged_during_render":True, "v019_source_intact":True,"render_views":[v[0] for v in views],"approval":False}
(dest/"report.json").write_text(json.dumps(result,indent=2))
print("GENESIS_HDRI32",json.dumps(result))
