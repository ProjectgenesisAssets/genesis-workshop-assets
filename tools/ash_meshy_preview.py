from PIL import Image,ImageDraw,ImageFont,ImageOps
from pathlib import Path
from io import BytesIO
import json,urllib.request,time
src=Path("input/meshy_candidate_posts.json")
items=json.loads(src.read_text())
dst=Path("output");dst.mkdir(exist_ok=True)
W,H=300,270
C=4
R=(len(items)+C-1)//C
canvas=Image.new("RGB",(W*C,H*R),(34,38,46))
draw=ImageDraw.Draw(canvas)
report=[]
for i,item in enumerate(items):
    img=item.get("image")
    status="missing"
    picture=None
    if img:
        try:
            req=urllib.request.Request(img,headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req,timeout=25) as r:
                data=r.read(6_000_000)
            picture=Image.open(BytesIO(data)).convert("RGB")
            picture.thumbnail((W-24,H-68))
            status=f"loaded {len(data)} bytes"
        except Exception as e:status=f"FAILED {type(e).__name__}: {str(e)[:80]}"
    x=(i%C)*W;y=(i//C)*H
    draw.rectangle((x+2,y+2,x+W-4,y+H-4),outline=(93,100,114),width=1)
    if picture:canvas.paste(picture,(x+(W-picture.width)//2,y+(H-70-picture.height)//2+7))
    draw.text((x+10,y+H-56),f"{i+1:02d}. {item['title'][:33]}",fill=(241,238,225))
    draw.text((x+10,y+H-36),item["post"].split("/")[-1][-19:],fill=(157,165,182))
    report.append({"id":i+1,"title":item["title"],"url":item["post"],"preview":item.get("image"),"status":status})
    print("PREVIEW",i+1,item["title"],status,flush=True)
canvas.save(dst/"meshy_ash_3d_geometry_candidates.jpg",quality=94)
(dst/"candidate_list.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
