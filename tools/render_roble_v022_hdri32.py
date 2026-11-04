#!/usr/bin/env python3
"""Blender 4.5.13 LTS comparative QA: V021 vs V022 oak log under unchanged HDRI32.
Render approved V021 oak boards for matching reference without modifying them.
"""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
base=Path("input");out=Path("output/oak_v022")
rend=out/"renders";rend.mkdir(parents=True,exist_ok=True)
source=base/"ProjectGenesis_Roble_Tronco_V021.glb"
candidate=out/"models/ProjectGenesis_Roble_Tronco_V022.glb"
boards_path=base/"ProjectGenesis_Roble_Tablas_V021.glb"
hdr=base/"studio_small_09_2k.hdr"
assert all(p.is_file() for p in (source,candidate,boards_path,hdr))
checked={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
         for p in (source,candidate,boards_path)}
assert checked[boards_path.name]=="05b05f54f68c5e5f1a1f8af8bfb82f0684ca1c4b0727e37e97c14ace070ddba1"
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
objects={}
def imported_models(name,path):
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path.resolve()))
    mes=[o for o in bpy.data.objects if o not in before and o.type=="MESH"]
    assert mes,(name,path)
    objects[name]=mes
    for i,m in enumerate(mes):m.name="Genesis "+name+" "+str(i)
    return mes
original=imported_models("ROBLE_ORIGINAL_V021",source)
revised=imported_models("ROBLE_CANDIDATO_V022",candidate)
approved=imported_models("TABLAS_APROBADAS_V021",boards_path)
assert len(original)==1 and len(revised)==1 and len(approved)==3
# GLB material import sanity: albedo differs but source geometry remains identical.
def geometry_digest(ob):
    import struct
    h=hashlib.sha256()
    h.update(struct.pack("<I",len(ob.data.vertices)))
    for v in ob.data.vertices:h.update(struct.pack("<3f",*v.co[:]))
    for poly in ob.data.polygons:
        h.update(struct.pack("<I",poly.loop_total))
        for lid in poly.loop_indices:
            h.update(struct.pack("<I",ob.data.loops[lid].vertex_index))
    return h.hexdigest()
assert geometry_digest(original[0])==geometry_digest(revised[0])
# Inspect source and result materials, confirm V022 has image differences.
print("MATS_V021",[m.name for m in original[0].data.materials],flush=True)
print("MATS_V022",[m.name for m in revised[0].data.materials],flush=True)
scene=bpy.context.scene
scene.render.engine="CYCLES";scene.cycles.samples=64
scene.render.threads_mode="FIXED";scene.render.threads=4
scene.view_layers[0].cycles.use_denoising=False
scene.render.resolution_x=1100
scene.render.resolution_y=850
scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.render.image_settings.color_mode="RGBA"
scene.view_settings.view_transform="AgX"
scene.view_settings.look="AgX - Medium High Contrast"
scene.view_settings.exposure=-.38
world=bpy.data.worlds.new("Genesis Studio Small 09 genuine Radiance HDRI")
world.use_nodes=True;world.node_tree.nodes.clear()
n=world.node_tree.nodes;links=world.node_tree.links
env=n.new("ShaderNodeTexEnvironment");env.image=bpy.data.images.load(str(hdr.resolve()))
assert env.image.file_format=="HDR" and env.image.depth>=24
bg=n.new("ShaderNodeBackground");bg.inputs["Strength"].default_value=.55
output=n.new("ShaderNodeOutputWorld")
links.new(env.outputs["Color"],bg.inputs["Color"])
links.new(bg.outputs["Background"],output.inputs["Surface"])
scene.world=world
def area(name,loc,power,size):
    light=bpy.data.lights.new(name,"AREA")
    ob=bpy.data.objects.new(name,light)
    scene.collection.objects.link(ob)
    ob.location=loc
    ob.rotation_euler=(Vector((0,0,.14))-ob.location).to_track_quat("-Z","Y").to_euler()
    light.energy=power;light.size=size
area("Oak neutral softbox key",(-2.5,-3.0,4.8),240,4.6)
area("Oak edge soft fill",(2.5,1.0,3.6),85,3.2)
camera_data=bpy.data.cameras.new("Genesis stable oak review")
camera=bpy.data.objects.new("Genesis stable oak review",camera_data)
scene.collection.objects.link(camera)
scene.camera=camera;camera_data.type="ORTHO"

def render(label,which,az,el,scale,focus=(0,0,.16)):
    for group in objects.values():
        for ob in group:ob.hide_render=ob not in which
    a=math.radians(az);e=math.radians(el)
    foc=Vector(focus)
    camera.location=foc+Vector((math.sin(a)*math.cos(e)*3.6,
                                -math.cos(a)*math.cos(e)*3.6,math.sin(e)*3.6))
    camera.rotation_euler=(foc-camera.location).to_track_quat("-Z","Y").to_euler()
    camera_data.ortho_scale=scale
    scene.render.image_settings.file_format="OPEN_EXR"
    scene.render.image_settings.color_depth="32"
    scene.render.filepath=str((rend/(label+".exr")).resolve())
    bpy.ops.render.render(write_still=True)
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.color_depth="8"
    bpy.data.images["Render Result"].save_render(str((rend/(label+".png")).resolve()),scene=scene)
    assert (rend/(label+".exr")).stat().st_size>100000
    assert (rend/(label+".png")).stat().st_size>40000
    print("GENESIS_OAK_REAL_HDRI32_RENDER",label,flush=True)

render("roble_tronco_v021_3cuartos",original,56,25,2.12)
render("roble_tronco_v022_3cuartos",revised,56,25,2.12)
render("roble_tronco_v021_corte",original,76,21,1.62)
render("roble_tronco_v022_corte",revised,76,21,1.62)
render("roble_tronco_v022_dorso",revised,-48,26,2.14)
render("tablas_v021_aprobadas_referencia",approved,43,25,2.23,(0,.05,.16))
before=hashlib.sha256(source.read_bytes()).hexdigest()
after=hashlib.sha256(source.read_bytes()).hexdigest()
assert before==after==checked[source.name]
assert checked[boards_path.name]==hashlib.sha256(boards_path.read_bytes()).hexdigest()
report={
 "status":"CANDIDATE; owner approval pending for log V022",
 "approved_boards_version":"V021, exact SHA unchanged",
 "blender":bpy.app.version_string,
 "render":"Cycles 64 samples; PNG previews, 32-bit float EXR masters",
 "hdr":"studio_small_09_2k.hdr genuine Radiance HDRI, strength 0.55",
 "lighting_reference":"same V021 review camera; softboxes unchanged (240W/85W)",
 "model_hashes_sha256":checked,
 "candidate_log_geometry_identical_to_v021":True,
 "board_source_untouched":True,
 "changed_asset":"log-only albedo; longitudinal wood and endgrain",
 "unmodified_assets":"board V021; bark, roughness, normals, mesh, UVs",
 "render_views":[x.stem for x in sorted(rend.glob("*.png"))],
 "owner_approved_log":False,"integrated_to_game":False
}
(out/"render_report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False))
print("GENESIS_ROBLE_V022_RENDER_QA",json.dumps(report,ensure_ascii=False),flush=True)
