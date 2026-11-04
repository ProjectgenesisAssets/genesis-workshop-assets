#!/usr/bin/env python3
"""Project Genesis - incremental oak log V022 texture-only color correction.
Reads byte-exact V021 candidate (with approved V021 boards as read-only color reference).
Geometry, indices, UVs, normal maps, roughness and bark texture never change.
Modifies ONLY log-specific endgrain and exposed sidegrain albedo maps.
Writes NEW GLB, retains all source binary bytes as an intact prefix.
No edits to approved oak boards. CC0 photographic Wood049 source retained.
"""
from pathlib import Path
from PIL import Image
import io,struct,json,hashlib
import numpy as np

SOURCE=Path("input/ProjectGenesis_Roble_Tronco_V021.glb")
BOARDS=Path("input/ProjectGenesis_Roble_Tablas_V021.glb")
ROOT=Path("output/oak_v022")
OUT=ROOT/"models"/"ProjectGenesis_Roble_Tronco_V022.glb"
OUT.parent.mkdir(parents=True,exist_ok=True)
IMAGES=ROOT/"texture_validation"
IMAGES.mkdir(parents=True,exist_ok=True)
expected_source="08da7f3e9b345be1908a1b1318f128929243087f101c5e881ffa85f0edb36b8d"
expected_boards="05b05f54f68c5e5f1a1f8af8bfb82f0684ca1c4b0727e37e97c14ace070ddba1"
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==expected_source, "V021 original log mismatch"
assert hashlib.sha256(BOARDS.read_bytes()).hexdigest()==expected_boards, "APPROVED boards are not the exact file"

def read_glb(p):
    data=p.read_bytes()
    magic,ver,whole=struct.unpack_from("<4sII",data)
    assert (magic,ver,whole)==(b"glTF",2,len(data))
    jlen,jtype=struct.unpack_from("<I4s",data,12);assert jtype==b"JSON"
    gltf=json.loads(data[20:20+jlen])
    offs=20+jlen
    blen,btype=struct.unpack_from("<I4s",data,offs);assert btype==b"BIN\x00"
    blob=data[offs+8:offs+8+blen]
    assert len(blob)==blen
    return gltf,blob

gltf,source_binary=read_glb(SOURCE)
before_meta=json.loads(json.dumps(gltf,sort_keys=True))
b=bytearray(source_binary)
original_blobs={}
changes=[]
scale_by_image={
    # The photographed exposed grain was too pale compared with approved boards.
    # Mild darkening + warmth, preserve microscopic texture and wood pores.
    "Wood049_4K-PNG_Color":(0.93,0.90,0.84),
    # The endgrain appeared copper/orange. Muted chestnut-to-oak brown.
    "oak_v021_true_radial_endgrain":(0.92,1.05,1.12),
}
for img in gltf["images"]:
    name=img.get("name","")
    if name not in scale_by_image:continue
    idx=img["bufferView"];v=gltf["bufferViews"][idx]
    assert v.get("buffer",0)==0
    begin=v.get("byteOffset",0);length=v["byteLength"]
    orig=source_binary[begin:begin+length]
    picture=Image.open(io.BytesIO(orig)).convert("RGB")
    pixels=np.asarray(picture,dtype=np.float32)
    before_mean=pixels.mean(axis=(0,1)).round(3).tolist()
    multipliers=np.array(scale_by_image[name],dtype=np.float32)
    corrected=np.uint8(np.rint(np.clip(pixels*multipliers,0,255)))
    result=Image.fromarray(corrected,"RGB")
    mime="image/png" if name.startswith("oak_") else "image/jpeg"
    dest=io.BytesIO()
    if mime=="image/png":
        result.save(dest,format="PNG",compress_level=6)
        preview_name="roble_tronco_v022_endgrain.png"
    else:
        result.save(dest,format="JPEG",quality=96,subsampling=0)
        preview_name="roble_tronco_v022_exposed_grain.jpg"
    encoded=dest.getvalue()
    (IMAGES/preview_name).write_bytes(encoded)
    if len(b)%4:b.extend(b"\x00"*(4-len(b)%4))
    newidx=len(gltf["bufferViews"])
    gltf["bufferViews"].append({"buffer":0,"byteOffset":len(b),"byteLength":len(encoded)})
    b.extend(encoded)
    img["bufferView"]=newidx
    img["mimeType"]=mime
    img["name"]=name.replace("_V021","_V022")+"_V022_color_only" if "V021" not in name else name.replace("v021","v022")+"_color_only"
    after_mean=corrected.mean(axis=(0,1)).round(3).tolist()
    changes.append({"source_texture":name,"new_texture":img["name"],
                    "multipliers":scale_by_image[name],
                    "source_mean_rgb":before_mean,"new_mean_rgb":after_mean,
                    "source_buffer_view":idx,"new_buffer_view":newidx,
                    "source_sha256":hashlib.sha256(orig).hexdigest(),
                    "new_sha256":hashlib.sha256(encoded).hexdigest()})
assert len(changes)==2,changes
gltf["buffers"][0]["byteLength"]=len(b)
# Geometry and complete mesh definitions are strictly identical.
assert gltf["meshes"]==before_meta["meshes"]
assert gltf["accessors"]==before_meta["accessors"]
assert gltf["nodes"]==before_meta["nodes"]
assert gltf["materials"]==before_meta["materials"]
assert gltf["textures"]==before_meta["textures"]
assert gltf["bufferViews"][:len(before_meta["bufferViews"])]==before_meta["bufferViews"]
assert bytes(b[:len(source_binary)])==source_binary
def pack_glb(obj,blob):
    raw=json.dumps(obj,ensure_ascii=False,separators=(",",":"),sort_keys=True).encode("utf-8")
    raw+=b" " *((4-len(raw)%4)%4)
    binbytes=bytes(blob)+b"\x00"*((4-len(blob)%4)%4)
    total=12+8+len(raw)+8+len(binbytes)
    return (struct.pack("<4sII",b"glTF",2,total)
            +struct.pack("<I4s",len(raw),b"JSON")+raw
            +struct.pack("<I4s",len(binbytes),b"BIN\x00")+binbytes)
OUT.write_bytes(pack_glb(gltf,b))
new_gltf,new_binary=read_glb(OUT)
assert new_binary[:len(source_binary)]==source_binary
assert new_gltf["meshes"]==before_meta["meshes"]
assert new_gltf["nodes"]==before_meta["nodes"]
assert new_gltf["accessors"]==before_meta["accessors"]
assert new_gltf["materials"]==before_meta["materials"]
assert new_gltf["textures"]==before_meta["textures"]
def triangles(g):
    return sum(g["accessors"][prim["indices"]]["count"]//3 for m in g["meshes"] for prim in m["primitives"])
assert triangles(gltf)==triangles(before_meta)==7164
assert hashlib.sha256(BOARDS.read_bytes()).hexdigest()==expected_boards
report={
 "asset":"dry-oak-wood","candidate":"Tronco V022 PBR COLOR ONLY",
 "approved_boards":"V021 byte-identical and untouched",
 "approved_boards_sha256":expected_boards,
 "source_log":"V021","source_log_sha256":expected_source,
 "new_log_sha256":hashlib.sha256(OUT.read_bytes()).hexdigest(),
 "version":"V022","new_log_bytes":OUT.stat().st_size,
 "triangles":triangles(gltf),"geometry_unchanged":True,
 "mesh_indices_normals_uvs_unchanged":True,"roughness_unchanged":True,
 "normal_maps_unchanged":True,"bark_pbr_unchanged":True,
 "original_binary_prefix_unchanged":True,
 "albedo_changes":changes,
 "owner_approval":"NOT YET; only BOARDS V021 approved",
 "integrated_to_playcanvas":False
}
(ROOT/"color_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
print("GENESIS_OAK_LOG_COLOR_PATCH_VALID",json.dumps(report,ensure_ascii=False),flush=True)
