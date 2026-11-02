"""Project Genesis Ash V03: source GLBs -> true HDRI Cycles renders.
Only the boards receive new albedo; log remains exactly V02 geometry and material.
Exports actual GLBs. All 32-bit EXRs are full-float, non-tonemapped linear data.
"""
import bpy,math,json,sys,hashlib
from pathlib import Path
from mathutils import Vector
from PIL import Image,ImageEnhance
import numpy as np

src=Path(sys.argv[sys.argv.index("--")+1]).resolve()
out=Path(sys.argv[sys.argv.index("--")+2]).resolve()
models=out/"models";renders=out/"renders";textures=out/"textures"
for p in (models,renders,textures):p.mkdir(parents=True,exist_ok=True)
boards_path=src/"ProjectGenesis_Tablas_Fresno_V02.glb"
log_path=src/"ProjectGenesis_Tronco_Fresno_V02.glb"
hdri=src/"studio_small_09_2k.hdr"
assert all(p.is_file() for p in (boards_path,log_path,hdri))
wood_orig=src/"fresno_natural_color.jpg"
end_orig=src/"fresno_corte_anillos.png"
assert wood_orig.is_file() and end_orig.is_file()

# Actual material change: image pixel data, not a generated image.
def adjust_color(inpath,outpath,wood_kind):
    srcimg=Image.open(inpath).convert("RGB")
    arr=np.asarray(srcimg,dtype=np.float32)/255
    if wood_kind=="long":
        # Natural creamy ash, subdued warm beige, greater wood grain separation.
        # Nonlinear contrast around the median, slightly lower brightness.
        arr=np.clip((arr-.52)*1.23+.52,0,1)
        arr=np.clip(arr*np.array([.85,.825,.79],dtype=np.float32),0,1)
        # Subtle brown contrast in long fibers, with non-orange color.
        lum=np.mean(arr,axis=2,keepdims=True)
        arr=np.clip(lum+(arr-lum)*1.08,0,1)
    else:
        arr=np.clip((arr-.50)*1.13+.50,0,1)
        arr=np.clip(arr*np.array([.93,.90,.86],dtype=np.float32),0,1)
    Image.fromarray(np.uint8(np.rint(arr*255)),mode="RGB").save(
      outpath,quality=95,subsampling=0)
    return {'source_mean_rgb':list(np.round(np.asarray(srcimg).mean(axis=(0,1)),1)),
      'result_mean_rgb':list(np.round((arr*255).mean(axis=(0,1)),1))}
wood_name=textures/"fresno_v03_natural_calido.jpg"
end_name=textures/"fresno_v03_testas_anillos.png"
stats={}
stats["wood"]=adjust_color(wood_orig,wood_name,"long")
stats["ends"]=adjust_color(end_orig,end_name,"end")
print("MATERIAL_COLOR_STATS",json.dumps(stats),flush=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
objects={}
for key,path in (("boards",boards_path),("log",log_path)):
    existing=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes=[o for o in bpy.data.objects if o not in existing and o.type=="MESH"]
    if len(meshes)!=1:raise ValueError(f"{key}: expected 1 mesh, got {len(meshes)}")
    obj=meshes[0]
    objects[key]=obj
    obj.name="Project Genesis "+("Tablas Fresno V03" if key=="boards" else "Tronco Fresno V02")
    print("IMPORT",key,len(obj.data.polygons),"UV",len(obj.data.uv_layers),
          "materials",[m.name for m in obj.data.materials],flush=True)

# After import Blender loads images embedded inside GLB. Replace ONLY color
# slots, keeping all existing imported PBR maps, UVs and surfaces untouched.
boards=objects["boards"]
long_img=bpy.data.images.load(str(wood_name),check_existing=True)
end_img=bpy.data.images.load(str(end_name),check_existing=True)
replaced=[]
for mat in boards.data.materials:
    if not mat or not mat.use_nodes:continue
    for node in mat.node_tree.nodes:
        if node.type!="TEX_IMAGE" or not node.image:continue
        prev=node.image.name.lower()
        if "fresno_natural_color" in prev or ("fresno" in prev and "color" in prev and "natural" in prev):
            node.image=long_img;replaced.append([mat.name,prev,wood_name.name])
        elif "fresno_corte_anillos" in prev:
            node.image=end_img;replaced.append([mat.name,prev,end_name.name])
print("REPLACED_IMAGES",json.dumps(replaced),flush=True)
assert len(replaced)>=2, "Could not identify original wood and end-grain albedo in imported GLB"
assert len(boards.data.uv_layers)==1

bpy.ops.object.select_all(action="DESELECT")
boards.select_set(True)
bpy.context.view_layer.objects.active=boards
export=models/"ProjectGenesis_Tablas_Fresno_V03_Calido_HDRI.glb"
bpy.ops.export_scene.gltf(filepath=str(export),export_format="GLB",
                          use_selection=True,export_texcoords=True,export_normals=True,export_materials="EXPORT")
print("GLB_EXPORTED",export,export.stat().st_size,flush=True)

# HDRI must contribute genuine scene-linear lighting. Radiance HDR is an
# HDR float environment, NOT an 8-bit PNG/JPG pretending to be an HDRI.
world=bpy.data.worlds.new("Poly Haven Studio Small 09 · real high dynamic range")
scene=bpy.context.scene
scene.world=world
world.use_nodes=True
nt=world.node_tree
nt.nodes.clear()
tex=nt.nodes.new("ShaderNodeTexEnvironment")
tex.image=bpy.data.images.load(str(hdri),check_existing=True)
tex.label="Poly Haven Studio Small 09 HDRI · CC0"
tex.location=(-260,30)
bg=nt.nodes.new("ShaderNodeBackground");bg.inputs["Strength"].default_value=.42
bg.location=(0,30)
wo=nt.nodes.new("ShaderNodeOutputWorld");wo.location=(250,30)
nt.links.new(tex.outputs["Color"],bg.inputs["Color"])
nt.links.new(bg.outputs["Background"],wo.inputs["Surface"])
assert tex.image.depth>=24, "HDRI source is not high dynamic range"

# Controlled neutral studio floor, subdued enough for realistic wood contrast.
mat=bpy.data.materials.new("Studio charcoal neutral")
mat.use_nodes=True
bs=mat.node_tree.nodes.get("Principled BSDF")
bs.inputs["Base Color"].default_value=(.083,.093,.103,1)
bs.inputs["Roughness"].default_value=.91
bpy.ops.mesh.primitive_plane_add(size=200)
plane=bpy.context.object
plane.name="Render stage (not exported)"
plane.location.z=-.015
plane.data.materials.append(mat)
# Moderate softbox fill: preserve directional HDRI without bleaching.
def area(name,location,power,size):
    li=bpy.data.lights.new(name,"AREA")
    ob=bpy.data.objects.new(name,li)
    bpy.context.collection.objects.link(ob)
    ob.location=location
    ob.rotation_euler=(Vector((0,0,.15))-ob.location).to_track_quat("-Z","Y").to_euler()
    li.energy=power;li.size=size
area("Key broad softbox",(-2.4,-3.0,4.5),360,4.2)
area("Edge fill",(2.5,1.0,3.4),160,3.0)

bpy.ops.object.camera_add()
camera=bpy.context.object;camera.name="Ash Studio Camera"
scene.camera=camera
camera.data.type="ORTHO"
scene.render.engine="CYCLES"
scene.cycles.device="CPU";scene.cycles.samples=64
scene.render.threads_mode="FIXED";scene.render.threads=4
scene.view_layers[0].cycles.use_denoising=False
scene.render.resolution_x=1200;scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.render.film_transparent=False
scene.view_settings.view_transform="AgX"
scene.view_settings.look="Medium High Contrast"
scene.view_settings.exposure=-0.45
scene.view_settings.gamma=1.0

def export_render(obj,prefix,az,el,scale,targetz):
    for k,o in objects.items():o.hide_render=(o is not obj)
    a=math.radians(az);e=math.radians(el)
    focus=Vector((0,0,targetz))
    camera.location=focus+Vector((math.sin(a)*math.cos(e)*3.8,-math.cos(a)*math.cos(e)*3.8,math.sin(e)*3.8))
    camera.rotation_euler=(focus-camera.location).to_track_quat("-Z","Y").to_euler()
    camera.data.ortho_scale=scale
    # Render to 32-bit float EXR, retaining scene-linear values.
    scene.render.image_settings.file_format="OPEN_EXR"
    scene.render.image_settings.color_mode="RGBA"
    scene.render.image_settings.color_depth="32"
    scene.render.image_settings.exr_codec="ZIP"
    scene.render.filepath=str(renders/(prefix+".exr"))
    bpy.ops.render.render(write_still=True)
    # The PNG is only the tone-mapped display preview, not the 32-bit master.
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.color_mode="RGBA"
    scene.render.image_settings.color_depth="8"
    scene.render.filepath=str(renders/(prefix+".png"))
    bpy.ops.render.render(write_still=True)
    print("REAL_CYCLES_RENDERED",prefix,"32BIT_EXR_AND_PNG",flush=True)

export_render(boards,"Tablas_Fresno_V03_HDRI_3cuartos",38,26,2.06,.12)
export_render(boards,"Tablas_Fresno_V03_HDRI_cantos",74,24,2.08,.12)
# Log unchanged (V02) so user can inspect under exactly the same lighting.
export_render(objects["log"],"Tronco_Fresno_V02_HDRI_3cuartos",38,26,1.85,.16)
export_render(objects["log"],"Tronco_Fresno_V02_HDRI_corte",76,23,1.90,.16)
report={"source_board_glb":str(boards_path.name),"board_source_sha256":hashlib.sha256(boards_path.read_bytes()).hexdigest(),
        "source_log_glb":str(log_path.name),"log_modified":False,
        "colors":stats,"albedo_replacements":replaced,
        "hdri":{"source":"Poly Haven Studio Small 09, CC0","image":hdri.name,"depth":tex.image.depth},
        "render":{"samples":64,"render_engine":"Cycles CPU","scene_world":"HDRI+moderate fill",
        "master":"32-bit FLOAT OpenEXR scene-linear","preview":"AgX tone mapped PNG 8-bit"},
        "model":"ProjectGenesis_Tablas_Fresno_V03_Calido_HDRI.glb"}
(out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
print("V03_COMPLETE",json.dumps(report),flush=True)
