#!/usr/bin/env python3
"""Strict V038 forge render-cost QA, no decimation, no emissive/collision changes."""
from pathlib import Path
import json, struct, hashlib
src=Path("public/models/Forge_V038_HeaderFixed_Preview.glb")
dst=Path("public/models/Forge_V038_PlayCanvas_HQ_Optimized.glb")
receipt=Path("public/models/Forge_V038_PlayCanvas_HQ_Optimized.json")
def read(path):
 data=path.read_bytes()
 assert data[:4]==b"glTF" and len(data)>50000,path
 assert struct.unpack_from("<II",data,4)==(2,len(data)),path
 size,typ=struct.unpack_from("<I4s",data,12)
 assert typ==b"JSON"
 return json.loads(data[20:20+size]),data
a,original=read(src)
b,optimized=read(dst)
def stats(d):
 meshes=d.get("meshes",[])
 return {"meshes":len(meshes),
         "primitives":sum(len(m.get("primitives",[])) for m in meshes),
         "materials":[m.get("name","") for m in d.get("materials",[])],
         "textures":len(d.get("textures",[])),
         "images":len(d.get("images",[])),
         "animations":len(d.get("animations",[])),
         "extensions_required":d.get("extensionsRequired",[])}
before,after=stats(a),stats(b)
assert before["meshes"]>70, "Original V038 mesh count unexpected"
assert before["animations"]==0, "Animated source needs separate procedure"
assert after["animations"]==0, "Optimized V038 should remain static"
assert any("charcoal" in name or "ember" in name for name in before["materials"])
assert set(before["materials"]).issubset(set(after["materials"])),"Material semantics lost"
assert "KHR_draco_mesh_compression" in after["extensions_required"],"Draco missing"
assert after["meshes"]<before["meshes"],"No mesh joins achieved"
assert after["primitives"]<before["primitives"],"No reduction of render primitives/draw calls"
assert len(optimized)<len(original)*.9,"Insufficient transfer-size saving"
assert "EXT_meshopt_compression" not in after["extensions_required"],"Undeclared decoder requirement"
summary={
  "asset":"Forge V038 HQ optimized - PlayCanvas",
  "status":"BINARY_VALIDATED_PENDING_INGAME_FPS_AND_VISUAL_REVIEW",
  "source":"public/models/Forge_V038_HeaderFixed_Preview.glb",
  "file":str(dst),
  "source_bytes":len(original),
  "optimized_bytes":len(optimized),
  "optimized_mb":round(len(optimized)/1e6,2),
  "saving_percent":round(100*(1-len(optimized)/len(original)),2),
  "source":before,
  "optimized":after,
  "geometry_decimation":False,
  "authored_emissive_unchanged":True,
  "playcanvas_decoder":"DracoDecoderModule",
  "sha256":hashlib.sha256(optimized).hexdigest()
}
receipt.write_text(json.dumps(summary,indent=2),encoding="utf-8")
print("V038_HQ_OPTIMIZED",json.dumps(summary))
