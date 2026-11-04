#!/usr/bin/env python3
"""Non-destructive GLB byte accounting for approved Herrero door V082-B."""
import json, struct, os, hashlib, collections
from pathlib import Path
p=Path("source/herrero-v082b-approved.glb")
raw=p.read_bytes()
assert raw[:4]==b"glTF" and struct.unpack_from("<I",raw,8)[0]==len(raw)
offset=12; chunks={}
while offset<len(raw):
 n,tag=struct.unpack_from("<I4s",raw,offset);offset+=8
 chunks[tag]=raw[offset:offset+n];offset+=n
g=json.loads(chunks[b"JSON"]); b=chunks[b"BIN\x00"]
views=g.get("bufferViews",[]);images=g.get("images",[])
textures=g.get("textures",[]);meshes=g.get("meshes",[])
stats={"name":"Herrero V082-B approved original","bytes":len(raw),"megabytes":round(len(raw)/1e6,3),
 "source_sha256":hashlib.sha256(raw).hexdigest(),"json_bytes":len(chunks[b"JSON"]),"bin_bytes":len(b),
 "mesh_count":len(meshes),"node_count":len(g.get("nodes",[])),"material_count":len(g.get("materials",[])),
 "image_count":len(images),"textures_count":len(textures),"accessor_count":len(g.get("accessors",[])),"extensions":g.get("extensionsUsed",[]),
 "images":[]}
for i,im in enumerate(images):
 v=views[im["bufferView"]] if "bufferView" in im else {}
 part=b[v.get("byteOffset",0):v.get("byteOffset",0)+v.get("byteLength",0)] if v else b""
 stats["images"].append({"index":i,"mime":im.get("mimeType"),"name":im.get("name"),"bytes":len(part),"sha256":hashlib.sha256(part).hexdigest() if part else None})
stats["image_bytes"]=sum(i["bytes"] for i in stats["images"])
stats["image_percent"]=round(100*stats["image_bytes"]/len(raw),2)
stats["meshes_primitives"]=sum(len(m.get("primitives",[])) for m in meshes)
stats["triangles"] = sum((a.get("count",0)//3 if p.get("mode",4)==4 and p.get("indices") is not None else 0) for m in meshes for p in m["primitives"] for a in [g["accessors"][p["indices"]]] if p.get("indices") is not None)
stats["non_image_bytes_approx"]=len(raw)-stats["image_bytes"]
Path("reports").mkdir(exist_ok=True)
Path("reports/v082b-baseline.json").write_text(json.dumps(stats,ensure_ascii=False,indent=2))
print("GLB_BASELINE",json.dumps(stats,ensure_ascii=False))
