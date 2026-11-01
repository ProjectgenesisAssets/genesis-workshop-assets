#!/usr/bin/env python3
"""V017 hemp: preserve CC0 PBR source and derive a restrained, real-fiber color/roughness map.
Original files remain untouched; derivative maps and manifests are versioned in run artifacts.
A digital image variation is NOT a new scan. No fabricated species certification.
"""
import os,pathlib,hashlib,json,math
import numpy as np
from PIL import Image
kind=os.environ["ASSET_KIND"].removeprefix("asset/")
if kind!="hemp-cord":
    print("V017 texture pass skipped for "+kind)
    raise SystemExit(0)
root=pathlib.Path("sources")/kind
images=sorted(x for x in root.iterdir() if x.suffix.lower() in (".png",".jpg",".jpeg"))
def source(*keys):
    matches=[p for p in images if any(k in p.name.lower() for k in keys) and not p.name.startswith("00_V017")]
    if not matches:raise RuntimeError("Original PBR source missing: "+str(keys))
    return matches[0]
src_color=source("color","albedo","diffuse")
src_rough=source("roughness")
with Image.open(src_color) as image:
    img=image.convert("RGB")
    w,h=img.size
    a=np.asarray(img,dtype=np.uint8)
# Slender, low amplitude pigment streaks following the existing scanned rope texture;
# this corrects flat color without overwriting real fibers.
y=np.arange(h,dtype=np.float32)[:,None]
x=np.arange(w,dtype=np.float32)[None,:]
streak=(.025*np.sin(x/26.0+1.4*np.sin(y/211.0))
        +.014*np.sin(x/7.3+y/123.0)
        +.009*np.sin(x/113.0-y/47.0))
var=np.clip(.98+streak,.90,1.055)
out=np.empty_like(a)
for k,tint in enumerate((.99,.96,.89)):
    out[:,:,k]=np.clip(a[:,:,k].astype(np.float32)*var*tint,0,255).astype(np.uint8)
color_path=root/"00_V017_hemp_Color.png"
Image.fromarray(out,"RGB").save(color_path,optimize=True)
with Image.open(src_rough) as im:
    rough=np.asarray(im.convert("L"),dtype=np.float32)
# Keep roughness high and granular: matte, dry natural hemp, not polished plastic.
rough=np.clip(np.maximum(rough,194)+7*np.sin(x/43+y/121),175,247).astype(np.uint8)
rough_path=root/"00_V017_hemp_Roughness.png"
Image.fromarray(rough,"L").save(rough_path,optimize=True)
manifest={
 "version":"V017","type":"CC0 photographic PBR derivative; not an additional scan",
 "license":"CC0-1.0","original_color":src_color.name,"original_roughness":src_rough.name,
 "derived":[{"file":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for p in (color_path,rough_path)],
 "note":"Manual botanical/fiber verification and final 8/10 artistic approval remain pending."
}
(root/"derivation_v017.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print(json.dumps({"material":kind,"image_dimensions":(w,h),"derivatives":[color_path.name,rough_path.name]}))
