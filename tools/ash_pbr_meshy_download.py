from pathlib import Path
from io import BytesIO
from PIL import Image
import urllib.request,urllib.error,zipfile,hashlib,json
base="https://cdn.meshy.ai/landing-assets/textures/wood"
sources={
 "ash_wood_grain": "ash-wood-grain",
 "weathered_tree_bark": "weathered-tree-bark",
 "smooth_beige_ash": "smooth-beige-ash-wood",
}
dest=Path("output");dest.mkdir(exist_ok=True)
results=[]
for label,slug in sources.items():
    item={"material":label,"page_url":f"https://www.meshy.ai/textures/wood/{slug}","attempts":[]}
    for size in ("4k","2k"):
        url=f"{base}/{slug}/{slug}-pbr-{size}.zip"
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req,timeout=75) as response:
                ct=response.headers.get("Content-Type","")
                data=response.read(100_000_000)
            if not zipfile.is_zipfile(BytesIO(data)):raise ValueError("Not a ZIP archive")
            z=zipfile.ZipFile(BytesIO(data))
            details=[]
            for name in z.namelist():
                info=z.getinfo(name)
                if info.is_dir():continue
                meta={"name":name,"bytes":info.file_size}
                try:
                    raw=z.read(name)
                    with Image.open(BytesIO(raw)) as im:
                        meta["resolution"]=list(im.size)
                except Exception:
                    pass
                details.append(meta)
            if not any("resolution" in v for v in details):raise ValueError("No texture images in ZIP")
            final=dest/f"{label}_pbr_{size}.zip";final.write_bytes(data)
            item.update({"downloaded":True,"bytes":len(data),"size":size,"zip":final.name,
                         "sha256":hashlib.sha256(data).hexdigest(),"contents":details})
            print("PBR_SUCCESS",label,size,len(data),"maps",len(details),flush=True)
            break
        except Exception as e:
            item["attempts"].append(f"{size}: {type(e).__name__}: {str(e)[:120]}")
            print("PBR_TRY_FAILED",label,size,str(e)[:130],flush=True)
    results.append(item)
    (dest/"pbr_texture_download_report.json").write_text(json.dumps(results,indent=2,ensure_ascii=False))
print("TEXTURE_PACKS_DOWNLOADED",sum(bool(x.get("downloaded")) for x in results),flush=True)
