#!/usr/bin/env python3
"""Non-destructive audit of the user-approved Project Genesis Herrero door V082-B GLB."""
import collections, hashlib, json, math, pathlib, struct, sys
P=pathlib.Path(sys.argv[1])
OUT=pathlib.Path(sys.argv[2]) if len(sys.argv)>2 else pathlib.Path("reports/door-herrero-v082b-baseline.json")
raw=P.read_bytes()
assert raw[:4]==b"glTF", "Not a GLB"
magic, version, length=struct.unpack_from("<4sII",raw,0)
assert version==2 and length==len(raw), "Invalid GLB 2 length"
chunks=[]
offset=12
while offset<len(raw):
    chunk_len, chunk_type=struct.unpack_from("<I4s",raw,offset)
    offset+=8
    chunks.append((chunk_type,chunk_len,offset))
    offset+=chunk_len
assert offset==len(raw) and chunks[0][0]==b"JSON"
doc=json.loads(raw[chunks[0][2]:chunks[0][2]+chunks[0][1]])
bytype={t.decode("ascii"):n for t,n,_ in chunks}
views=doc.get("bufferViews",[])
accessors=doc.get("accessors",[])
images=doc.get("images",[])
meshes=doc.get("meshes",[])
textures=doc.get("textures",[])
mats=doc.get("materials",[])
nodes=doc.get("nodes",[])
primitives=[p for m in meshes for p in m.get("primitives",[])]
render_triangles=0
for p in primitives:
    if p.get("mode",4)!=4:continue
    if "indices" in p:
        count=accessors[p["indices"]]["count"]
    else:
        count=accessors[p["attributes"]["POSITION"]]["count"]
    render_triangles+=count//3
image_report=[]
for i,im in enumerate(images):
    view=views[im["bufferView"]] if "bufferView" in im else {}
    image_report.append(dict(index=i,name=im.get("name"),mime=im.get("mimeType"),bytes=view.get("byteLength"),
       material_references=sum(1 for t in textures if t.get("source")==i),uri=im.get("uri")))
image_total=sum(im.get("bytes") or 0 for im in image_report)
matnames=[m.get("name","(unnamed)") for m in mats]
counts=collections.Counter(matnames)
report=dict(file=P.name,bytes=len(raw),size_mib=round(len(raw)/1024/1024,3),sha256=hashlib.sha256(raw).hexdigest(),
    chunks=bytype,images=image_report,image_bytes_total=image_total,image_fraction=round(image_total/len(raw),3),
    mesh_count=len(meshes),primitive_count=len(primitives),node_count=len(nodes),triangles=render_triangles,
    material_count=len(mats),unique_material_names=len(counts),
    repeated_material_names={k:v for k,v in counts.items() if v>1},
    accessors=len(accessors),buffer_views=len(views),
    textures=len(textures),extensions_used=doc.get("extensionsUsed",[]),extensions_required=doc.get("extensionsRequired",[]),
    buffer_bytes=sum(b.get("byteLength",0) for b in doc.get("buffers",[])),
    asset=doc.get("asset",{}))
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
print("DOOR_V082B_AUDIT_REPORT "+json.dumps(report,ensure_ascii=False))
print("DOOR_V082B_IMAGE_RANKING")
for im in sorted(image_report,key=lambda x:x.get("bytes") or 0,reverse=True)[:25]:
 print(f"image {im['index']:>3} bytes={im['bytes'] or 0:>10} mime={im['mime']} name={im['name']}")
