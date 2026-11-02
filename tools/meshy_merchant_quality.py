import json, os, sys
from PIL import Image,ImageOps,ImageDraw
import numpy as np

out=sys.argv[1]
info=json.load(open(os.path.join(out,"geometry_metrics.json")))
ratios=info["candidates"]
images={}
for angle in (0,90,180):
    images[angle]=np.asarray(Image.open(f"{out}/original_{angle}.png").convert("RGBA"),dtype=np.float32)
ranked=[]
for item in ratios:
    ratio=item["ratio"]
    scores=[]
    for angle in (0,90,180):
        a=images[angle]
        b=np.asarray(Image.open(f"{out}/r{ratio:.2f}_{angle}.png").convert("RGBA"),dtype=np.float32)
        mask_a=a[:,:,3]>127
        mask_b=b[:,:,3]>127
        intersection=mask_a&mask_b
        change=np.count_nonzero(mask_a^mask_b)/max(1,np.count_nonzero(mask_a))
        # RGB differences in common visible model pixels, including the texture appearance.
        diff=np.mean(np.abs(a[:,:,:3]-b[:,:,:3])[intersection])/255 if intersection.any() else 1
        scores.append({"angle":angle,"silhouette_diff_pct":round(100*float(change),4),
                       "visible_rgb_mae_pct":round(100*float(diff),4)})
    worst_sil=max(s["silhouette_diff_pct"] for s in scores)
    worst_rgb=max(s["visible_rgb_mae_pct"] for s in scores)
    # An explicit conservative operational interpretation of the <=3% visual limit.
    passed=(worst_sil<=3 and worst_rgb<=3 and
            item["max_height_percent"]<=3 and item["p95_height_percent"]<=1)
    item.update({"views":scores,"worst_silhouette_pct":worst_sil,
                 "worst_rgb_mae_pct":worst_rgb,"passed":bool(passed)})
    ranked.append(item)
    print("CHECK",item["ratio"],"tris",item["triangles"],"sil",worst_sil,
          "rgb",worst_rgb,"geommax",round(item["max_height_percent"],3),"PASS",passed,flush=True)
passed=[x for x in ranked if x["passed"]]
if not passed:
    # No candidate may be passed off as <=3% when the actual tests fail.
    selected={"ratio":1.0,"triangles":info["source_triangles"],"passed":False,
              "reason":"No reduced mesh met all 3% constraints"}
else:
    best=min(passed,key=lambda x:x["triangles"])
    selected={**best,"passed":True}
with open(f"{out}/selected.json","w") as f:json.dump(selected,f,indent=2)
with open(f"{out}/candidate_report.json","w") as f:json.dump(ranked,f,indent=2)
print("SELECTED",json.dumps(selected),flush=True)

def composite(foreground):
    # Simple clean studio background; underlying image is a real Cycles render.
    im=foreground.convert("RGBA")
    width,height=im.size
    base=Image.new("RGBA",im.size,(35,42,54,255))
    base.alpha_composite(im)
    return base.convert("RGB")

def contact_sheet():
    angles=[0,45,90]
    w,h=880,1040
    canvas=Image.new("RGB",(w*3,h*2+96),(25,29,36))
    draw=ImageDraw.Draw(canvas)
    for row,label in enumerate(("original","optimized")):
        for col,angle in enumerate(angles):
            path=f"{out}/final_{label}_{angle}.png"
            if not os.path.isfile(path):continue
            im=composite(Image.open(path))
            canvas.paste(im,(col*w,row*(h+48)+48))
            draw.text((col*w+16,row*(h+48)+15),f"{label.upper()} - {angle} degrees",fill=(240,238,228))
    canvas.save(f"{out}/merchant_cycles_comparison.jpg",quality=92)
    im=composite(Image.open(f"{out}/final_optimized_45.png"))
    im.save(f"{out}/merchant_cycles_hero.png")
if os.path.isfile(f"{out}/final_optimized_45.png"):
    contact_sheet()
