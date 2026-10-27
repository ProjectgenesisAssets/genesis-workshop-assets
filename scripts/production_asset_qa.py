#!/usr/bin/env python3
"""Objective QA for an auto-iterated Genesis asset. NEVER grants artistic approval."""
import argparse, json, os, re, struct
from pathlib import Path
from PIL import Image, ImageChops, ImageStat, ImageDraw, ImageFont

VIEWS = {
    "door": ("front","three_quarter","side","rear"),
    "forge": ("front","three_quarter","rear","detail"),
    "bellows": ("front","three_quarter","rear","detail"),
    "anvil": ("front","hero","rear","top"),
}
def preview_candidates(asset):
    if asset=="door": return sorted(Path("previews").glob("door_v[0-9]*"),reverse=True)
    if asset=="anvil": return sorted(Path("previews").glob("yunque_v[0-9]*"),reverse=True)
    return sorted(Path("previews").glob("heroes_v[0-9]*"),reverse=True)

def candidate_pngs(out,asset):
    if asset=="door":
        return dict(zip(VIEWS[asset],[out/"front_orthographic.png",out/"three_quarter.png",out/"side_orthographic.png",out/"rear_orthographic.png"]))
    if asset=="anvil":
        paths={
          "front":list(out.glob("*vista_01.png")),
          "hero":list(out.glob("*hero.png")),
          "rear":list(out.glob("*vista_09.png")),
          "top":list(out.glob("*superior.png")),
        }
        return {key:(v[0] if len(v)==1 else Path("__MISSING__")) for key,v in paths.items()}
    return {name:out/(name+".png") for name in VIEWS[asset]}

def glb_stats(path):
    with path.open("rb") as f:
        magic,version,total=struct.unpack("<III",f.read(12))
        assert magic==0x46546c67 and version==2 and total==path.stat().st_size
        n,kind=struct.unpack("<I4s",f.read(8))
        assert kind==b"JSON"
        doc=json.loads(f.read(n))
    triangles=0
    for mesh in doc.get("meshes",[]):
        for prim in mesh.get("primitives",[]):
            if prim.get("mode",4)!=4:continue
            ix=prim.get("indices")
            count=doc["accessors"][ix]["count"] if ix is not None else doc["accessors"][prim["attributes"]["POSITION"]]["count"]
            triangles+=count//3
    bindings={}
    for mat in doc.get("materials",[]):
        pbr=mat.get("pbrMetallicRoughness",{})
        tex=pbr.get("baseColorTexture")
        image_name=None
        if tex:
            texture=doc["textures"][tex["index"]]
            image_name=doc["images"][texture["source"]].get("name")
        bindings[mat.get("name","unnamed")]={"base_color_image":image_name,
            "emissive_texture":bool(mat.get("emissiveTexture"))}
    textured=sum(bool(v["base_color_image"]) for v in bindings.values())
    return {"triangles":triangles,"meshes":len(doc.get("meshes",[])),
            "materials":len(doc.get("materials",[])),"base_color_textured_materials":textured,
            "embedded_images":len(doc.get("images",[])),"texture_bindings":bindings}

def load(path):
    with Image.open(path) as im:
        assert im.width>=600 and im.height>=600,(str(path),im.size)
        return im.convert("RGBA").resize((512,512),Image.Resampling.LANCZOS)

def main():
    p=argparse.ArgumentParser()
    for k in ("asset","output","task-id","source"):p.add_argument("--"+k,required=True)
    args=p.parse_args()
    asset=args.asset
    assert asset in VIEWS
    out=Path(args.output)
    assert out.is_dir()
    glbs=list(out.glob("*.glb"))
    blends=list(out.glob("*.blend"))
    audits=list(out.glob("*AUDIT*.json"))
    assert len(glbs)==1 and len(blends)==1 and audits,(glbs,blends,audits)
    stats=glb_stats(glbs[0])
    if asset=="bellows" and "oxblood" in args.task_id:
        matches=[v for k,v in stats["texture_bindings"].items() if "leather" in k.lower()]
        assert any("oxblood" in (m["base_color_image"] or "").lower() for m in matches),("LEATHER_PBR_NOT_BOUND_IN_GLB",matches)
    assert 100<stats["triangles"]<350000,stats
    assert stats["materials"]>=1
    paths=candidate_pngs(out,asset)
    for name,path in paths.items():assert path.is_file(),("MISSING_RENDER",name,str(path))
    baseline=None
    for folder in preview_candidates(asset):
        base=folder/asset if asset in ("forge","bellows") else folder
        if all((base/(view+".png")).is_file() for view in VIEWS[asset]):
            baseline=base
            break
    assert baseline,("NO_BASELINE",asset)
    qa=Path("reports/production_auto")/f"{asset}-{args.task_id}"
    qa.mkdir(parents=True,exist_ok=True)
    tile=450
    contact=Image.new("RGB",(tile*4,tile*2),(31,35,41))
    changes=[]
    silhouettes=[]
    for i,view in enumerate(VIEWS[asset]):
        old=load(baseline/(view+".png"))
        new=load(paths[view])
        diff=ImageChops.difference(old,new)
        delta=sum(ImageStat.Stat(diff.convert("RGB")).mean)/(255*3)
        a0=old.getchannel("A").point(lambda x:255 if x>=32 else 0)
        a1=new.getchannel("A").point(lambda x:255 if x>=32 else 0)
        union=ImageStat.Stat(ImageChops.lighter(a0,a1)).sum[0]
        intersect=ImageStat.Stat(ImageChops.darker(a0,a1)).sum[0]
        iou=intersect/max(union,1)
        changes.append({"view":view,"rgb_delta":round(delta,5),"silhouette_iou":round(iou,5)})
        silhouettes.append(iou)
        for row,img in enumerate((old,new)):
            frame=Image.new("RGBA",(tile,tile),(31,35,41,255))
            img.thumbnail((tile-16,tile-35))
            frame.alpha_composite(img,((tile-img.width)//2,(tile-35-img.height)//2))
            d=ImageDraw.Draw(frame)
            d.text((12,tile-26),f"{asset} {view} "+("baseline" if row==0 else "candidate"),fill=(240,240,235))
            contact.paste(frame.convert("RGB"),(i*tile,row*tile))
    contact.save(qa/"four_view_comparison.jpg",quality=84,optimize=True)
    visual_changed=max(x["rgb_delta"] for x in changes)>.001
    report={
      "asset":asset,"task_id":args.task_id,"source_sha":args.source,
      "baseline":str(baseline),"candidate":str(out),
      "glb":glbs[0].name,"blend":blends[0].name,
      "glb_stats":stats,"audit_files":[p.name for p in audits],
      "comparison":changes,"visual_changed":visual_changed,
      "technical_pass":visual_changed and min(silhouettes)>.75,
      "artistic_score":None,"artist_approved":False,
      "note":"Real Blender renders, objective technical checks only; final artistic approval is human."
    }
    (qa/"QA.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(report,indent=2))
    if not report["technical_pass"]:
        raise SystemExit("Candidate is unapproved and failed objective comparison")

if __name__=="__main__":main()
