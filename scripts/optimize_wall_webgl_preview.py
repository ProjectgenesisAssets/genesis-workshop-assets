#!/usr/bin/env python3
"""Convert Blender's heavy test GLBs to standard WebGL-friendly glTF 2 GLBs.

Conserves every vertex, material, UV, mesh and node; only resizes/re-encodes
embedded raster textures. No custom glTF compression extension is required.
"""
import io, json, struct, sys
from pathlib import Path
from PIL import Image

def pad(data, char=b"\0"):
    return data + char*((-len(data))%4)

def unpack(path):
    buf=Path(path).read_bytes()
    assert buf[:4]==b"glTF" and struct.unpack_from("<I",buf,4)[0]==2
    assert struct.unpack_from("<I",buf,8)[0]==len(buf)
    json_size, json_type=struct.unpack_from("<I4s",buf,12)
    assert json_type==b"JSON"
    doc=json.loads(buf[20:20+json_size])
    at=20+json_size
    bin_size,bin_type=struct.unpack_from("<I4s",buf,at)
    assert bin_type==b"BIN\0"
    payload=buf[at+8:at+8+bin_size]
    assert len(payload)==bin_size
    return doc,payload

def convert(source,destination,edge=1024,quality=79):
    doc,src=unpack(source)
    image_by_view={}
    for image in doc.get("images",[]):
        if "bufferView" in image:
            image_by_view.setdefault(image["bufferView"],[]).append(image)
    views=doc.get("bufferViews",[])
    new_bin=bytearray()
    converted=0
    for idx,v in enumerate(views):
        start=v.get("byteOffset",0)
        blob=src[start:start+v["byteLength"]]
        assert len(blob)==v["byteLength"]
        imgs=image_by_view.get(idx,[])
        if imgs:
            try:
                im=Image.open(io.BytesIO(blob));im.load()
                if max(im.size)>edge:
                    r=edge/max(im.size)
                    im=im.resize((max(1,round(im.width*r)),max(1,round(im.height*r))),Image.Resampling.LANCZOS)
                has_alpha=im.mode in ("RGBA","LA") and im.getchannel("A").getextrema()[0]<255
                out=io.BytesIO()
                if has_alpha:
                    im.convert("RGBA").save(out,format="PNG",optimize=True,compress_level=9)
                    mime="image/png"
                else:
                    im.convert("RGB").save(out,format="JPEG",quality=quality,optimize=True,subsampling=0)
                    mime="image/jpeg"
                blob=out.getvalue()
                for image in imgs:
                    image["mimeType"]=mime
                converted+=1
            except Exception as ex:
                raise RuntimeError(f"Cannot optimize embedded image view {idx}") from ex
        new_bin.extend(b"\0" * ((-len(new_bin))%4))
        v["byteOffset"]=len(new_bin)
        v["byteLength"]=len(blob)
        new_bin.extend(blob)
    assert converted>=2, "Expected embedded PBR textures"
    doc["buffers"][0]["byteLength"]=len(new_bin)
    js=pad(json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode('utf8'),b' ')
    binary=pad(bytes(new_bin),b"\0")
    total=12+8+len(js)+8+len(binary)
    result=(struct.pack("<4sII",b"glTF",2,total)
            +struct.pack("<I4s",len(js),b"JSON")+js
            +struct.pack("<I4s",len(binary),b"BIN\0")+binary)
    Path(destination).parent.mkdir(parents=True,exist_ok=True)
    Path(destination).write_bytes(result)
    document,payload=unpack(destination)
    assert len(payload)==len(binary)
    assert len(document.get("meshes",[]))==len(doc.get("meshes",[]))
    assert len(document.get("nodes",[]))==len(doc.get("nodes",[]))
    info={"source":str(source),"output":str(destination),
          "original_bytes":Path(source).stat().st_size,"preview_bytes":len(result),
          "textures_reencoded":converted,"max_texture_edge":edge,
          "geometry_unchanged":True,"status":"PREVIEW_NOT_APPROVED"}
    Path(destination+".json").write_text(json.dumps(info,indent=2))
    print(json.dumps(info))
if __name__=="__main__":
    convert(sys.argv[1],sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else 1024)
