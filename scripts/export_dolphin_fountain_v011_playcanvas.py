#!/usr/bin/env python3
"""Export reviewed V011 fountain to a PlayCanvas-oriented animated GLB.

Keep the original 4K scanned material sources and Blender authoring file intact.
Produce a 2K texture variant with baked object animations. Water normal-map
movement is implemented in the companion PlayCanvas script (not glTF material
animation, which glTF does not support).
"""
from pathlib import Path
import bpy
import json
import struct
import hashlib
import os

ROOT=Path.cwd()
GEN=ROOT/"scripts/plaza_fuente_delfin_marmol_v011_still.py"
MARKER="# Save master and export only fountain meshes, never staging lights/cameras."
source=GEN.read_text(encoding="utf-8")
assert source.count(MARKER)==1, "V011 generator structure changed: aborting"
# Generator produces authoring geometry, PBR and 192-frame animation before marker.
namespace={"__name__":"__main__","__file__":str(GEN)}
exec(compile(source.split(MARKER)[0],str(GEN),"exec"),namespace)
parts=namespace["parts"]
stone_images=namespace["stone_images"]
out=ROOT/"public/models"
out.mkdir(parents=True,exist_ok=True)
tex_dir=ROOT/"output_fountain_dolphin_v011"/"textures"/"playcanvas_2k"
tex_dir.mkdir(parents=True,exist_ok=True)

# 2K runtime copies: authoring 4K source files remain unchanged on disk.
for channel,img in stone_images.items():
    fmt="JPEG" if channel in ("Diffuse","Rough") else "PNG"
    extension=".jpg" if fmt=="JPEG" else ".png"
    dest=tex_dir/("scanned_marble_"+channel+"_2k"+extension)
    img.scale(2048,2048)
    img.filepath_raw=str(dest.resolve())
    img.file_format=fmt
    img.save()
    assert dest.exists() and dest.stat().st_size>10000
    print("WEB_TEXTURE",channel,dest.stat().st_size)

scene=bpy.context.scene
scene.frame_start=1
scene.frame_end=192
scene.render.fps=24
scene.frame_set(1)
bpy.ops.object.select_all(action="DESELECT")
for o in parts:
    assert o.type=="MESH"
    o.select_set(True)
bpy.context.view_layer.objects.active=parts[0]

glb=out/"PG_Dolphin_Fountain_V011_PlayCanvas_Animated.glb"
props={p.identifier for p in bpy.ops.export_scene.gltf.get_rna_type().properties}
kw={
    "filepath":str(glb.resolve()),
    "export_format":"GLB",
    "use_selection":True,
    "export_animations":True,
    "export_materials":"EXPORT",
    "export_texcoords":True,
}
optional={
    "export_animation_mode":"SCENE",
    "export_frame_range":True,
    "export_force_sampling":True,
    "export_optimize_animation_size":True,
    "export_optimize_animation_keep_anim_armature":True,
    "export_image_format":"AUTO",
    "export_cameras":False,
    "export_lights":False,
    "export_skins":False,
    "export_tangents":True,
    "export_apply":False,
}
kw.update({k:v for k,v in optional.items() if k in props})
print("EXPORT_ARGS",json.dumps(kw,default=str))
result=bpy.ops.export_scene.gltf(**kw)
assert "FINISHED" in result, result
blob=glb.read_bytes()
assert len(blob)>100000 and len(blob)<90_000_000, f"Unexpected GLB size {len(blob)}"
assert blob[:4]==b"glTF" and struct.unpack_from("<I",blob,4)[0]==2
assert struct.unpack_from("<I",blob,8)[0]==len(blob),"Broken GLB header"
jsonlen,kind=struct.unpack_from("<I4s",blob,12)
assert kind==b"JSON"
gltf=json.loads(blob[20:20+jsonlen])
anims=gltf.get("animations",[])
assert anims,"Export lost animated transforms"
assert any(a.get("channels") for a in anims),"Empty animations"
names=[n.get("name","") for n in gltf.get("nodes",[])]
assert any("DELFIN_ESCULPIDO" in n for n in names),"Dolphin geometry absent"
assert any("Anim_" in n for n in names),"Water stream geometry absent"
materials=[m.get("name","") for m in gltf.get("materials",[])]
assert any(n.startswith("AGUA_") for n in materials),"Water materials missing"
durations=[]
channels=0
for anim in anims:
    channels+=len(anim.get("channels",[]))
    for sampler in anim.get("samplers",[]):
        acc=gltf.get("accessors",[])[sampler["input"]]
        if "max" in acc and "min" in acc:
            durations.append(acc["max"][0]-acc["min"][0])
assert durations and max(durations)>=7.3, "Expected the 8s animated water cycle"
assert channels>=10,"Too few animated water channels"
sha=hashlib.sha256(blob).hexdigest()
summary={
 "asset":"PG_Dolphin_Fountain_V011_PlayCanvas_Animated",
 "source_script":str(GEN.relative_to(ROOT)),
 "status":"GLB_STATIC_VALIDATED_NOT_YET_PLAYCANVAS_VISUALLY_APPROVED",
 "glb":str(glb.relative_to(ROOT)),
 "bytes":len(blob),
 "sha256":sha,
 "meshes":len(gltf.get("meshes",[])),
 "materials":materials,
 "animations":len(anims),
 "animation_channels":channels,
 "max_animation_duration_s":round(max(durations),3),
 "target_fps":24,
 "loop_s":8,
 "source_geometry_objects":len(parts),
 "runtime_pbr_texture_max":2048,
 "authoring_pbr_texture_resolution":4096,
 "diameter_m":4.26,
 "height_m":2.65,
 "water_material_animation":"PlayCanvas companion JS required for UV scrolling normals; GLB embeds stream/droplet/splash mesh animation",
 "water_runtime_script":"playcanvas/fountain_water_animated_v011.js",
 "source_preserved":True,
 "playcanvas_integration":"PENDING_IN_GAME_RENDER_AND_MOBILE_PERFORMANCE",
 "artistic_approval":"PENDING",
}
(out/"PG_Dolphin_Fountain_V011_PlayCanvas_Animated.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
print("GLB_V011_EXPORT_VALIDATED",json.dumps(summary,ensure_ascii=False))
