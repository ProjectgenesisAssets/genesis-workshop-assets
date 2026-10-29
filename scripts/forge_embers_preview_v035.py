#!/usr/bin/env python3
"""Assemble 12 actual Blender Cycles material-flicker frames into a looped GIF."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path(sys.argv[1]).resolve()
frames = sorted(out.glob("flicker_frame_*.png"))
assert len(frames) == 12, f"Need twelve Cycles flicker frames; found {len(frames)}"
pictures = []
for item in frames:
    with Image.open(item) as image:
        image = image.convert("RGB")
        # Preserve most charcoal/stone colors; no palette intended for game use.
        picture = image.quantize(colors=192, method=Image.Quantize.MEDIANCUT)
        pictures.append(picture.copy())
dest = out / "flicker_preview.gif"
pictures[0].save(dest, save_all=True, append_images=pictures[1:],
                 duration=110, loop=0, optimize=False, disposal=2)
assert dest.stat().st_size > 40_000, dest
print("GENESIS_V035_FLICKER_GIF_OK", dest, dest.stat().st_size, flush=True)
