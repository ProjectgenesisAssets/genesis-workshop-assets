"""Download verified CC0 scan for V019 Blender render on GitHub Actions only.
Source: https://polyhaven.com/a/rusty_metal_sheet
API credit: Powered by Poly Haven - https://polyhaven.com/our-api
Never download private Genesis V175 textures into a public repository.
"""
from pathlib import Path
from io import BytesIO
import json,urllib.request
from PIL import Image,ImageStat

SLUG="rusty_metal_sheet"
BASE="https://api.polyhaven.com/files/"
out=Path("ph_scans_v019")/SLUG
out.mkdir(parents=True,exist_ok=True)
headers={"User-Agent":"Genesis-Asset-Render/1.0 (CC0 Poly Haven preview)"}
def get(url):
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req,timeout=90) as response:
        return response.read()
data=json.loads(get(BASE+SLUG))
print("POLYHAVEN_AVAILABLE_MAPS",list(data),flush=True)
receipt={"provider":"Poly Haven","asset":SLUG,
    "license":"CC0","page":"https://polyhaven.com/a/"+SLUG,
    "api_credit":"Powered by Poly Haven","maps":{}}
for kind in ("diff","rough","nor_gl"):
    entry=data.get(kind)
    if entry is None:
        aliases={"diff":("Diffuse","albedo","diffuse"),
                 "rough":("Rough","roughness"),
                 "nor_gl":("Normal (GL)","normal_gl","norm")}
        for alternate in aliases[kind]:
            if alternate in data:
                entry=data[alternate]
                break
    if entry is None:raise RuntimeError(f"Poly Haven texture type {kind} absent. Found {list(data)}")
    option=entry.get("2k") or entry.get("4k") or entry.get("1k")
    if not option:raise RuntimeError(f"No supported resolution for {kind}: {list(entry)}")
    record=option.get("jpg") or option.get("png")
    if not record:raise RuntimeError(f"No web-safe texture format for {kind}: {list(option)}")
    url=record["url"]
    assert url.startswith("https://"),url
    b=get(url)
    with Image.open(BytesIO(b)) as im:
        im=im.convert("RGB")
        assert min(im.size)>=1024,(kind,im.size)
        im.thumbnail((2048,2048),Image.Resampling.LANCZOS)
        target=out/(kind+".jpg")
        im.save(target,quality=94,subsampling=0)
        std=ImageStat.Stat(im.resize((256,256))).stddev
        assert max(std)>3.0,(kind,std)
        receipt["maps"][kind]={"url":url,"pixel_size":im.size,"stddev_rgb":std}
    print("POLYHAVEN_CC0_MAP_READY",kind,target,target.stat().st_size,flush=True)
(out/"SOURCE_RECEIPT.json").write_text(json.dumps(receipt,indent=2))
