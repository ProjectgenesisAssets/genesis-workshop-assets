from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import numpy as np
import json

root=Path("output")
reports=[]
def metrics(path,original):
    a=np.asarray(Image.open(original).convert("RGBA")).astype(np.float32)
    b=np.asarray(Image.open(path).convert("RGBA")).astype(np.float32)
    rgb_a=np.mean(a[:,:,:3],axis=2)
    rgb_b=np.mean(b[:,:,:3],axis=2)
    valid=(a[:,:,3]>127)&(b[:,:,3]>127)
    silhouette=np.logical_xor(a[:,:,3]>127,b[:,:,3]>127)
    dark=(rgb_a>65)&(rgb_b<50)&((rgb_a-rgb_b)>45)&valid
    dramatic=(rgb_a-rgb_b>65)&(rgb_a>100)&valid
    return {"silhouette_pct":float(silhouette.sum()/max(1,(a[:,:,3]>127).sum())*100),
           "rgb_mae_pct":float(np.mean(np.abs(a[:,:,:3]-b[:,:,:3])[valid])/255*100),
           "new_dark_pixels":int(dark.sum()),"large_color_drop_pixels":int(dramatic.sum())}
for tag in ("r40","r50"):
    d=root/tag
    record={"label":tag,"views":{}}
    for angle in (0,45,90):
        record["views"][str(angle)]=metrics(d/f"final_optimized_{angle}.png",d/f"final_original_{angle}.png")
    print("CONTROL",json.dumps(record,ensure_ascii=False),flush=True)
    reports.append(record)
    # Side by side detailed front view, without changing camera/brightness.
    image=Image.new("RGB",(1320,950),(30,36,47))
    draw=ImageDraw.Draw(image)
    crop=(225,285,655,750)
    for n,model in enumerate(("original","optimized")):
        src=Image.open(d/f"final_{model}_0.png").convert("RGBA").crop(crop)
        src=src.resize((645,697),Image.Resampling.LANCZOS)
        bg=Image.new("RGBA",src.size,(35,43,55,255))
        bg.alpha_composite(src)
        image.paste(bg.convert("RGB"),(n*660,68))
        draw.text((12+n*660,18),f"{tag}  {model.upper()} torso/hand/bag",fill=(255,255,255))
    image.save(root/f"{tag}_hands_inspection.png")

# Produce a compact 2-row board, full frontal and 45 degree from two settings.
W,H=500,610
board=Image.new("RGB",(W*4,H*2+60),(32,38,49))
d=ImageDraw.Draw(board)
for ri,tag in enumerate(("r40","r50")):
    for ci,(model,angle) in enumerate((("original",0),("optimized",0),("original",45),("optimized",45))):
        src=Image.open(root/tag/f"final_{model}_{angle}.png").convert("RGBA")
        src.thumbnail((W,H-35),Image.Resampling.LANCZOS)
        bg=Image.new("RGBA",src.size,(35,43,55,255))
        bg.alpha_composite(src)
        x=ci*W+(W-src.width)//2
        y=ri*H+55
        board.paste(bg.convert("RGB"),(x,y))
        d.text((ci*W+20,ri*H+18),f"{tag}: {model.upper()} {angle} deg",fill=(245,245,245))
board.save(root/"merchant_repair_comparison.jpg",quality=95)
(root/"repair_comparison_metrics.json").write_text(json.dumps(reports,indent=2))
