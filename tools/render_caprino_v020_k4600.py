#!/usr/bin/env python3
"""Caprino V020, one controlled change: warm area key 4600K vs neutral key 6000K.
Same approved-study HDRI environment, exact V020 GLB, camera, Cycles setup,
key intensity/position/size. Color temperature is from Blender Blackbody shader.
Original HDRI-only study is separately preserved, without claiming it was 6000K.
"""
import bpy
import json
import hashlib
import pathlib
from mathutils import Vector

root=pathlib.Path("output/tanned-goatskin")
model=root/"caprino_v020_roughness_master.glb"
hdr=pathlib.Path("/tmp/studio_small_09_2k.hdr")
assert model.is_file() and hdr.is_file()
expected="4f74f18234e23a0e266a53bc52756e91fb170afe6eb7ae7f35dd6abd6020bf95"
before=hashlib.sha256(model.read_bytes()).hexdigest()
assert before==expected,("V020 reference GLB mismatch",before)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(model.resolve()))
meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
assert meshes
scene=bpy.context.scene
scene.render.engine="CYCLES"
scene.cycles.samples=64
scene.cycles.use_denoising=False
scene.render.resolution_x=1080
scene.render.resolution_y=1080
scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.render.image_settings.color_mode="RGBA"
scene.view_settings.view_transform="Standard"

world=bpy.data.worlds.new("Genesis HDRI 32-bit studio_small_09")
world.use_nodes=True
wn=world.node_tree.nodes
wl=world.node_tree.links
wn.clear()
outnode=wn.new("ShaderNodeOutputWorld")
bg=wn.new("ShaderNodeBackground")
texture=wn.new("ShaderNodeTexEnvironment")
texture.image=bpy.data.images.load(str(hdr.resolve()))
assert texture.image.file_format=="HDR"
bg.inputs["Strength"].default_value=.82
wl.new(texture.outputs["Color"],bg.inputs["Color"])
wl.new(bg.outputs["Background"],outnode.inputs["Surface"])
scene.world=world

light_data=bpy.data.lights.new("Genesis 4600K-6000K key",type="AREA")
light_obj=bpy.data.objects.new("Genesis color temp controlled area key",light_data)
scene.collection.objects.link(light_obj)
light_obj.location=(3.0,-4.0,5.0)
light_data.shape="DISK"
light_data.size=4.0
light_data.energy=12.0
light_data.use_nodes=True
nodes=light_data.node_tree.nodes
links=light_data.node_tree.links
emission=next((n for n in nodes if n.type=="EMISSION"),None)
if emission is None:
    emission=nodes.new("ShaderNodeEmission")
output=next((n for n in nodes if n.type=="OUTPUT_LIGHT"),None)
if output is None:
    output=nodes.new("ShaderNodeOutputLight")
links.new(emission.outputs["Emission"],output.inputs["Surface"])
emission.inputs["Strength"].default_value=12.0
blackbody=nodes.new("ShaderNodeBlackbody")
links.new(blackbody.outputs["Color"],emission.inputs["Color"])
camera_data=bpy.data.cameras.new("V020 original approved-review camera")
camera=bpy.data.objects.new("V020 original approved-review camera",camera_data)
scene.collection.objects.link(camera)
scene.camera=camera
camera_data.type="ORTHO"
focus=Vector((0,-.24,.18))
views=[
    ("three_quarter",(2.7,-3.2,2.5),1.90),
    ("side",(4.0,0.0,1.0),1.90),
    ("detail",(1.2,-2.3,1.1),.78)
]

dst=root/"HDRI32_V020_4600K_study"
dst.mkdir(parents=True,exist_ok=True)
for kelvin in (6000,4600):
    blackbody.inputs["Temperature"].default_value=float(kelvin)
    folder=dst/str(kelvin)
    folder.mkdir(exist_ok=True)
    for name,loc,scale in views:
        camera.location=loc
        camera.rotation_euler=(focus-camera.location).to_track_quat("-Z","Y").to_euler()
        camera.data.ortho_scale=scale
        scene.render.image_settings.file_format="OPEN_EXR"
        scene.render.image_settings.color_depth="32"
        scene.render.filepath=str((folder/(name+".exr")).resolve())
        bpy.ops.render.render(write_still=True)
        scene.render.image_settings.file_format="PNG"
        scene.render.image_settings.color_depth="8"
        bpy.data.images["Render Result"].save_render(str((folder/(name+".png")).resolve()),scene=scene)
        assert (folder/(name+".png")).stat().st_size>20000
    print("GENESIS_CAPRINO_CCT_RENDER",kelvin,flush=True)
after=hashlib.sha256(model.read_bytes()).hexdigest()
assert after==before
report={
    "asset":"tanned-goatskin",
    "model":"V020_roughness_only",
    "study":"4600K vs 6000K controlled area key, HDRI unchanged",
    "control":"6000K KEY; NOT a claim about original HDRI color temperature",
    "comparison":"4600K KEY; original same HDRI 32bit environment",
    "lamp_temperature_shader":"ShaderNodeBlackbody",
    "kelvin_tested":[6000,4600],
    "area_light":{"location":[3,-4,5],"size":4.0,"power":12},
    "environment":{"image":"studio_small_09_2k.hdr","radiance":"RGBE high dynamic range","strength":.82},
    "blender":bpy.app.version_string,
    "cycles_samples":64,
    "views":[v[0] for v in views],
    "master_sha256":before,
    "original_glb_unchanged":before==after,
    "geometry_changed":False,
    "roughness_changed":False,
    "normal_strength_changed":False,
    "art_approval":"pending_owner"
}
(dst/"render_report.json").write_text(json.dumps(report,indent=2))
print("GENESIS_CAPRINO_4600K_REPORT",json.dumps(report),flush=True)
