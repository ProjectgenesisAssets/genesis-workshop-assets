"""Reject global averages that conceal holes around hands, props or bags."""
import sys,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw

phase=sys.argv[1]
folder=Path(sys.argv[2])
angles=(0,45,90,180,270)
def analyze(a_path,b_path):
    a=np.asarray(Image.open(a_path).convert("RGBA"),dtype=np.int16)
    b=np.asarray(Image.open(b_path).convert("RGBA"),dtype=np.int16)
    assert a.shape==b.shape
    A=a[:,:,3]>127
    B=b[:,:,3]>127
    common=A&B
    base_px=max(1,int(A.sum()))
    silhouette=100*np.count_nonzero(A^B)/base_px
    color_a=a[:,:,:3].mean(axis=2)
    color_b=b[:,:,:3].mean(axis=2)
    delta=np.abs(a[:,:,:3]-b[:,:,:3])
    mae=(float(delta[common].mean())/255*100) if common.any() else 100
    dark=common&(color_a>78)&(color_b<45)&((color_a-color_b)>55)
    severe=common&(color_a>95)&((color_a-color_b)>75)
    # Limit localized errors. 10x10 tiles are compared within the object's alpha bounds.
    rows,cols=np.where(A)
    local=[]
    if len(rows):
        y0,y1=max(0,int(rows.min())-2),min(A.shape[0],int(rows.max())+3)
        x0,x1=max(0,int(cols.min())-2),min(A.shape[1],int(cols.max())+3)
        for iy in range(10):
            ys=y0+round((y1-y0)*iy/10)
            ye=y0+round((y1-y0)*(iy+1)/10)
            for ix in range(10):
                xs=x0+round((x1-x0)*ix/10)
                xe=x0+round((x1-x0)*(ix+1)/10)
                mask=common[ys:ye,xs:xe]
                if mask.sum()<75:continue
                color_delta=delta[ys:ye,xs:xe]
                local.append(float(color_delta[mask].mean())/255*100)
    return {"silhouette_pct":round(float(silhouette),5),
            "visible_rgb_mae_pct":round(float(mae),5),
            "new_dark_pixels":int(dark.sum()),"large_darkening_pixels":int(severe.sum()),
            "worst_local_tile_mae_pct":round(max(local) if local else 100,5),
            "local_tile_count":len(local)}

def decide(stats,highres=False):
    # For 480px previews, use stricter gate to avoid accepting a candidate
    # that only develops unacceptable localized changes at 900px.
    factor=4 if highres else 1
    max_color=1.1 if highres else .62
    max_local=5 if highres else 1.2
    max_silhouette=.30 if highres else .16
    return (stats["silhouette_pct"]<=max_silhouette and
            stats["visible_rgb_mae_pct"]<=max_color and
            stats["new_dark_pixels"]<=18*factor and
            stats["large_darkening_pixels"]<=38*factor and
            stats["worst_local_tile_mae_pct"]<=max_local)

def write_board(path,prefix_a,prefix_b):
    # Two rows (0,45 degrees) and one zoom at 90 degrees.
    w,h=900,1100
    board=Image.new("RGB",(w*3,h*2+50),(35,42,54))
    draw=ImageDraw.Draw(board)
    for i,angle in enumerate((0,45,90)):
        for row,prefix in enumerate((prefix_a,prefix_b)):
            pic=Image.open(folder/f"{prefix}_{angle}.png").convert("RGBA")
            pic.thumbnail((w,h),Image.Resampling.LANCZOS)
            back=Image.new("RGBA",pic.size,(35,42,54,255))
            back.alpha_composite(pic)
            px=i*w+(w-pic.width)//2
            py=row*(h+25)+25
            board.paste(back.convert("RGB"),(px,py))
            draw.text((i*w+15,row*(h+25)+6),
                      f"{'V01 ORIGINAL' if row==0 else 'V02 CANDIDATE'} - {angle} degrees",
                      fill=(245,245,240))
    board.save(path,quality=94)
    # Inspect one close crop (center of hands and waist).
    for angle in (0,45):
        images=[]
        for prefix in (prefix_a,prefix_b):
            src=Image.open(folder/f"{prefix}_{angle}.png").convert("RGBA")
            # Preserve the full width at 2x resolution in critical waist/hand band.
            x0=int(src.width*.19);x1=int(src.width*.81)
            y0=int(src.height*.37);y1=int(src.height*.73)
            im=src.crop((x0,y0,x1,y1))
            bg=Image.new("RGBA",im.size,(35,42,54,255))
            bg.alpha_composite(im)
            images.append(bg.convert("RGB"))
        canvas=Image.new("RGB",(images[0].width*2,images[0].height),(35,42,54))
        canvas.paste(images[0],(0,0));canvas.paste(images[1],(images[0].width,0))
        canvas.save(folder/f"hands_waist_before_after_{angle}.png")

if phase=="candidates":
    metadata=json.loads((folder/"geometry_candidates.json").read_text())
    for row in metadata:
        views={}
        for angle in angles:
            views[str(angle)]=analyze(folder/f"base_{angle}.png",
                folder/f"r{row['ratio']:.2f}_{angle}.png")
        row["views"]=views
        row["worst_silhouette_pct"]=max(v["silhouette_pct"] for v in views.values())
        row["worst_global_color_pct"]=max(v["visible_rgb_mae_pct"] for v in views.values())
        row["worst_local_tile_pct"]=max(v["worst_local_tile_mae_pct"] for v in views.values())
        row["dark_pixels_total"]=sum(v["new_dark_pixels"] for v in views.values())
        row["passed"]=all(decide(v) for v in views.values())
        print("TRIAL",json.dumps({k:v for k,v in row.items() if k!="views"}),flush=True)
    passing=[row for row in metadata if row["passed"]]
    choice=min(passing,key=lambda x:x["triangles"]) if passing else None
    selected={**choice,"passed":True} if choice else {"passed":False,"reason":"No V01 candidate met all 5-view safety gates"}
    (folder/"candidate_quality_report.json").write_text(json.dumps(metadata,indent=2))
    (folder/"selected.json").write_text(json.dumps(selected,indent=2))
    print("SELECTION",json.dumps({k:v for k,v in selected.items() if k!="views"}),flush=True)
    # An unsuccessful screening is a valid QA result, NOT approval.
elif phase=="final":
    selected=json.loads((folder/"selected.json").read_text())
    if not selected.get("passed"):raise SystemExit("No approved candidate available")
    views={}
    for angle in angles:
        v=analyze(folder/f"final_original_{angle}.png",folder/f"final_candidate_{angle}.png")
        v["passed"]=decide(v,highres=True)
        views[str(angle)]=v
    passed=all(v["passed"] for v in views.values())
    report={"selected_ratio":selected["ratio"],"triangles":selected["triangles"],
        "source_triangles":108525,"reduction_pct":100*(1-selected["triangles"]/108525),
        "highres_all_passed":passed,"views":views}
    (folder/"final_quality_report.json").write_text(json.dumps(report,indent=2))
    write_board(folder/"merchant_V01_vs_V02_cycles.jpg","final_original","final_candidate")
    print("FINAL_QA",json.dumps(report),flush=True)
    if not passed:raise SystemExit("High-res QA failed: V02 not approved")
else:raise SystemExit("Unsupported QA phase")
