#!/usr/bin/env python3
"""Visual QA for Genesis artist previews; objective defects only, never aesthetic approval.
Runs on GitHub Actions and inspects *real Blender PNGs* without local Blender.
"""
import argparse, json, math, pathlib, statistics
from PIL import Image, ImageChops, ImageStat
ASSETS = {
 "door": ("previews/door_v003", ("front","three_quarter","side","rear")),
 "anvil": ("previews/heroes_v002/anvil", ("front","three_quarter","rear","detail")),
 "forge": ("previews/heroes_v002/forge", ("front","three_quarter","rear","detail")),
 "bellows": ("previews/heroes_v002/bellows", ("front","three_quarter","rear","detail")),
}
def evaluate(path, asset):
    im=Image.open(path).convert("RGBA")
    w,h=im.size
    im.thumbnail((480,480))
    rgba=im
    pix=rgba.load()
    w,h=rgba.size
    alpha=rgba.getchannel("A")
    transparent=alpha.getextrema()[0]<240
    if transparent:
        mask=alpha.point(lambda a:255 if a>45 else 0)
    else:
        # Studio colors are fairly uniform at image borders: subtract border background
        rgb=rgba.convert("RGB")
        corners=[rgb.getpixel((x,y)) for x,y in ((0,0),(w-1,0),(0,h-1),(w-1,h-1))]
        bg=tuple(int(statistics.median([c[k] for c in corners])) for k in range(3))
        pixels=list(rgb.getdata())
        diffs=[sum(abs(p[k]-bg[k]) for k in range(3)) for p in pixels]
        mask=Image.new("L",(w,h))
        mask.putdata([255 if d>72 else 0 for d in diffs])
    bbox=mask.getbbox()
    issues=[]
    if not bbox: issues.append("EMPTY_IMAGE")
    else:
        left,top,right,bottom=bbox
        occupy=(right-left)*(bottom-top)/(w*h)
        margins=[left/w,top/h,(w-right)/w,(h-bottom)/h]
        if occupy<.06:issues.append("TINY_OBJECT")
        # Nontransparent studio backgrounds are hard to segment; only enforce hard frame-edge QA for alpha previews.
        if transparent and min(margins)<.009:issues.append("FRAME_CLIPPED")
    lum=rgba.convert("RGB").convert("L")
    hist=lum.histogram()
    total=sum(hist)
    clipped_high=sum(hist[250:])/total
    clipped_low=sum(hist[:6])/total
    if clipped_high>.62:issues.append("OVEREXPOSED_IMAGE")
    if clipped_low>.80:issues.append("UNDEREXPOSED_IMAGE")
    detail=sum(1 for x in lum.filter(__import__("PIL").ImageFilter.FIND_EDGES).getdata() if x>20)/(w*h)
    if detail<.005:issues.append("LOW_DETAIL_IMAGE")
    return {"file":str(path),"dimensions":list(Image.open(path).size),
            "alpha_background":transparent,"subject_bbox":list(bbox) if bbox else None,
            "edge_detail_fraction":round(detail,4),"white_pixel_fraction":round(clipped_high,4),
            "black_pixel_fraction":round(clipped_low,4),"issues":issues}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default=".")
    ap.add_argument("--output",default="reports/visual_quality.json")
    args=ap.parse_args()
    root=pathlib.Path(args.root)
    report={"model":"OBJECTIVE_PIXEL_QA_v1","aesthetic_score":None,
            "minimum_aesthetic_score_required":8.0,
            "approved":False,
            "note":"Image segmentation heuristics, NOT an artistic judge; requires human four-view review",
            "assets":{}}
    for asset,(folder,views) in ASSETS.items():
        stats=[]
        for view in views:
            fp=root/folder/(view+".png")
            if not fp.exists():stats.append({"file":str(fp),"issues":["PREVIEW_MISSING"]})
            else:stats.append(evaluate(fp,asset))
        report["assets"][asset]={"views":stats,"issues":sorted({x for s in stats for x in s["issues"]}),
                                  "technical_candidate":all(not s["issues"] for s in stats),
                                  "artist_approved":False}
    out=pathlib.Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    lines=["# Genesis - visual QA automatizada", "",
           "Diagnostico objetivo de PNG. Ninguna puntuacion de arte se inventa.","",
           "| Asset | Vistas | Problemas detectados |","|---|---:|---|"]
    for name,s in report["assets"].items():
        issues=", ".join(s["issues"]) if s["issues"] else "Sin fallos objetivos detectados"
        lines.append(f"| {name} | {len(s['views'])} | {issues} |")
    lines+=["","**Aprobados artisticamente: ninguno.** Los PNG deben revisarse para llegar a 8/10."]
    (out.parent/"visual_quality.md").write_text("\n".join(lines)+"\n")
    print("\n".join(lines))
if __name__=="__main__":
    from PIL import ImageFilter
    main()
