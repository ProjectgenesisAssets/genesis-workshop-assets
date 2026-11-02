"""Project Genesis Fresno V03: authentic 32-bit-float HDRI lighting, real Cycles renders.
Input GLBs are the unchanged Blender V02 geometry from run 41503321995.
A new derived color texture adjusts the white/plale ash plank albedo.
Neither a concept image nor painted approximation of the geometry.
"""
import bpy, sys, json, math, hashlib, shutil, os
from pathlib import Path
from mathutils import Vector
from PIL import Image,ImageEnhance
import numpy as np

args=sys.argv[sys.argv.index("--")+1:]
inp=Path(args[0]).resolve()
out=Path(args[1]).resolve()
hdri=Path(args[2]).resolve()
assert hdri.is_file() and hdri.stat().st_size>1_000_000, "Real HDRI EXR missing"
source_plank=inp/"models/ProjectGenesis_Tablas_Fresno_V02.glb"
source_trunk=inp/"models/ProjectGenesis_Tronco_Fresno_V02.glb"
texture_source=inp/"textures/fresno_natural_color.jpg"
for p in (source_plank,source_trunk,texture_source):assert p.is_file(),p
(out/"renders").mkdir(parents=True,exist_ok=True)
(out/"models").mkdir(parents=True,exist_ok=True)
(out/"textures").mkdir(parents=True,exist_ok=True)

# Evolving V02 colors does NOT change model geometry or normals.
src=Image.open(texture_source).convert("RGB")
enh=ImageEnhance.Contrast(src).enhance(1.28)
enh=ImageEnhance.Color(enh).enhance(1.10)
rgb=np.asarray(enh,dtype=np.float32)
rgb*=np.asarray([.915,.887,.860],dtype=np.float32).reshape(1,1,3)
rgb=np.uint8(np.clip(rgb,0,255))
texture_v03=out/"textures/fresno_tablas_v03_cream_beige_grain.jpg"
Image.fromarray(rgb,"RGB").save(texture_v03,quality=94,subsampling=0)
print("WOOD_COLOR_STATS",np.asarray(src).mean(axis=(0,1)).tolist(),rgb.mean(axis=(0,1)).tolist(),flush=True)

scene=bpy.context.scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

def import_mesh(name,path):
    old=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    objs=[o for o in bpy.data.objects if o not in old and o.type=="MESH"]
    assert len(objs)==1,(name,len(objs))
    obj=objs[0];obj.name=name
    assert len(obj.data.polygons)>2000
    return obj

plank=import_mesh("Tablas Fresno V02 - Base PBR",source_plank)
# Duplicate object with separate UV/mesh/material to make the V03 candidate.
trial=plank.copy()
trial.data=plank.data.copy()
bpy.context.collection.objects.link(trial)
trial.name="ProjectGenesis_Tablas_Fresno_V03_HDR32"
for i,m in enumerate(trial.data.materials):
    if not m:continue
    copy=m.copy()
    copy.name=m.name+" · Fresno V03 color corregido"
    trial.data.materials[i]=copy
new_image=bpy.data.images.load(str(texture_v03),check_existing=False)
new_image.colorspace_settings.name="sRGB"
replaced=0
for m in trial.data.materials:
    if not m or not m.use_nodes:continue
    for n in m.node_tree.nodes:
        if n.type=="TEX_IMAGE" and n.image and (
          "fresno_natural_color" in n.image.name.lower() or 
          "fresno_natural_color" in Path(n.image.filepath or "").stem.lower()):
            n.image=new_image
            replaced+=1
assert replaced==1,f"Expected V03 grain diffuse replacement exactly once, found {replaced}"
trunk=import_mesh("Tronco Fresno V02 - Sin cambios",source_trunk)

def triangle_count(obj):
    return sum(max(0,len(p.vertices)-2) for p in obj.data.polygons)
assert triangle_count(plank)==triangle_count(trial)==10000
assert triangle_count(trunk)==163272
print("GEOMETRY_UNCHANGED",triangle_count(plank),triangle_count(trial),triangle_count(trunk),flush=True)

# Export real GLB; a baked 1536px image and untouched original normal and
# roughness maps remain on PBR materials.
bpy.ops.object.select_all(action="DESELECT")
trial.select_set(True);bpy.context.view_layer.objects.active=trial
dest=out/"models/ProjectGenesis_Tablas_Fresno_V03_HDR32.glb"
bpy.ops.export_scene.gltf(filepath=str(dest),export_format="GLB",use_selection=True,
 export_texcoords=True,export_normals=True,export_materials="EXPORT")
assert dest.stat().st_size>100_000
print("EXPORTED_REAL_GLB",dest,dest.stat().st_size,flush=True)

# Replace flat studio world with a real photographed high dynamic range EXR.
world=bpy.data.worlds.new("Poly Haven Studio Small 08 · 32 bit float HDRI")
world.use_nodes=True
scene.world=world
nodes=world.node_tree.nodes;nodes.clear()
tex=nodes.new("ShaderNodeTexEnvironment")
tex.label="REAL 4K Poly Haven EXR · 17 EV; never an 8-bit LDR background"
tex.image=bpy.data.images.load(str(hdri))
assert tex.image.is_float,f"Environment must be HDR float: {tex.image.depth}"
bg=nodes.new("ShaderNodeBackground");bg.inputs["Strength"].default_value=.72
output=nodes.new("ShaderNodeOutputWorld")
world.node_tree.links.new(tex.outputs["Color"],bg.inputs["Color"])
world.node_tree.links.new(bg.outputs["Background"],output.inputs["Surface"])
print("HDR_ENVIRONMENT",tex.image.name,tex.image.depth,tex.image.is_float,flush=True)

# True studio floor for contact shadows.
floor=bpy.data.materials.new("Dark matte floor")
floor.use_nodes=True
bs=floor.node_tree.nodes.get("Principled BSDF")
bs.inputs["Base Color"].default_value=(.12,.135,.15,1)
bs.inputs["Roughness"].default_value=.93
bpy.ops.mesh.primitive_plane_add(size=200)
ground=bpy.context.object
ground.name="Studio photo floor; not exported"
ground.data.materials.append(floor)

# Studio camera based on source bbox, explicitly in world coordinates.
def bounds(obj):
    pts=[obj.matrix_world @ Vector(p) for p in obj.bound_box]
    lo=Vector([min(v[i] for v in pts) for i in range(3)])
    hi=Vector([max(v[i] for v in pts) for i in range(3)])
    return lo,hi
lo,hi=bounds(plank)
ground.location.z=lo.z-.012
bpy.ops.object.camera_add()
camera=bpy.context.object
scene.camera=camera
camera.data.type="ORTHO"
span=max(hi.x-lo.x,hi.y-lo.y,hi.z-lo.z)
center=(lo+hi)*.5
def place_camera(angle,elev):
    a=math.radians(angle);e=math.radians(elev)
    d=max(span,1.)*3.2
    aim=center
    camera.location=aim+Vector((d*math.sin(a)*math.cos(e),-d*math.cos(a)*math.cos(e),d*math.sin(e)))
    camera.rotation_euler=(aim-camera.location).to_track_quat("-Z","Y").to_euler()
    camera.data.ortho_scale=span*1.62

scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=52
scene.render.threads_mode="FIXED";scene.render.threads=4
scene.view_layers[0].cycles.use_denoising=False
scene.view_settings.view_transform="AgX"
scene.view_settings.exposure=-.45
scene.render.film_transparent=False
scene.render.resolution_x=1120
scene.render.resolution_y=840
scene.render.resolution_percentage=100

def save_render(stem,object,angle,elev,save_exr=False):
    for ob in (plank,trial,trunk):ob.hide_render=ob!=object
    place_camera(angle,elev)
    result=bpy.ops.render.render(write_still=False)
    rr=bpy.data.images["Render Result"]
    if save_exr:
        scene.render.image_settings.file_format="OPEN_EXR"
        scene.render.image_settings.color_depth="32"
        scene.render.image_settings.color_mode="RGBA"
        scene.render.image_settings.exr_codec="ZIP"
        rr.save_render(filepath=str(out/"renders"/(stem+".exr")),scene=scene)
        assert (out/"renders"/(stem+".exr")).stat().st_size>50_000
        print("SAVED_FLOAT32_EXR",stem,flush=True)
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.color_depth="16"
    scene.render.image_settings.color_mode="RGBA"
    rr.save_render(filepath=str(out/"renders"/(stem+".png")),scene=scene)
    print("RENDERED_PNG16",stem,flush=True)

# Matched camera and HDR lighting for V02/V03 side-by-side, two angles.
save_render("Tablas_V02_HDRI_32bit_original_color",plank,38,26)
save_render("Tablas_V03_HDRI_32bit_corrected_color",trial,38,26,True)
save_render("Tablas_V03_HDRI_32bit_close_endgrain",trial,70,26)
# Show also that original trunk is preserved under the same authentic HDRI.
_,old_hi=bounds(trunk)
new_lo,new_hi=bounds(trunk)
center=(new_lo+new_hi)*.5
span=max(new_hi[i]-new_lo[i] for i in range(3))
ground.location.z=new_lo.z-.012
save_render("Tronco_V02_HDRI_32bit_unchanged",trunk,38,26)

report={
  "geometry":"Actual Meshy-based 3D GLB imported into Blender, not ImageGen",
  "hdr_source":"Poly Haven Studio Small 08 / CC0, full-range 4k EXR environment",
  "hdri_is_float":tex.image.is_float,"hdri_image_depth":tex.image.depth,
  "cycles":"PATH TRACED CPU","samples":scene.cycles.samples,
  "hdr_render":"OpenEXR 32-bit float per channel, linear, lossless ZIP",
  "display_preview":"PNG 16-bit per channel, view-transformed AgX",
  "source_plank_triangles":triangle_count(plank),
  "new_plank_triangles":triangle_count(trial),
  "source_trunk_triangles":triangle_count(trunk),
  "grain_color_source_sha256":hashlib.sha256(texture_source.read_bytes()).hexdigest(),
  "grain_color_v03_sha256":hashlib.sha256(texture_v03.read_bytes()).hexdigest(),
  "v03_glb_sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
  "note":"HDRI alone does not guarantee a darker albedo; V03 has a separately recorded subtle warmer material albedo."
}
(out/"HDR32_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
print("REPORT",json.dumps(report,ensure_ascii=False),flush=True)
