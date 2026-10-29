#!/usr/bin/env python3
"""Compose 24 real Cycles frames into 24-bit APNG with subtle fire bloom.
GIF is compatibility-only; quality reference is APNG, never palettized."""
import sys
from pathlib import Path
from PIL import Image, ImageChops, ImageFilter
out=Path(sys.argv[1]).resolve()
frames=sorted(out.glob("flicker_frame_*.png"))
assert len(frames)==24, f"V038 requires 24 frames, found {len(frames)}"
full=[]
for path in frames:
    with Image.open(path) as source:
        rgb=source.convert("RGB")
        r,g,b=rgb.split()
        # Warm fire isolation avoids blooming bright neutral stones.
        hot=ImageChops.subtract(r,g,scale=1.45)
        hot=ImageChops.subtract(hot,b,scale=1.35)
        halo=hot.filter(ImageFilter.GaussianBlur(radius=10)).point(lambda x:min(255,int(x*.85)))
        warm=Image.merge("RGB",(halo,halo.point(lambda x:int(x*.29)),halo.point(lambda x:int(x*.06))))
        full.append(ImageChops.screen(rgb,warm))
apng=out/"flicker_preview.png"
full[0].save(apng,format="PNG",save_all=True,append_images=full[1:],duration=167,loop=0,disposal=2,blend=0,optimize=False)
assert apng.stat().st_size>90000
# GIF is provided only for systems that do not play APNG.
gif=[im.quantize(colors=256,method=Image.Quantize.MEDIANCUT) for im in full]
gif[0].save(out/"flicker_preview.gif",save_all=True,append_images=gif[1:],duration=170,loop=0,optimize=False,disposal=2)
print("GENESIS_V038_24BIT_APNG_GLOW_OK",apng,apng.stat().st_size,flush=True)
