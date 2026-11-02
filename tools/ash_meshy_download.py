"""Fetch public community model geometry via its publicly displayed Meshy 3D viewer.
No paid API, no credentials, no prompt generation; only verified public CC0 posts.
Never overwrite models from previous runs; validate actual bytes and GLB topology.
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
from urllib.parse import urlparse
import json,struct,re,traceback
from meshy_glb.core import ensure_loader,decrypt_meshy,validate_glb
SOURCE={
  "ash_log_single":"https://www.meshy.ai/posts/0197a3d6-0b61-781e-992c-8a412300cc44",
  "ash_logs_stack":"https://www.meshy.ai/posts/019fa73f-8d7b-7d49-b622-167c37bd8455",
  "ash_planks_stack":"https://www.meshy.ai/posts/01974a6a-ef37-715f-a9d5-0c7e2fc9d837",
  "ash_plank_rough":"https://www.meshy.ai/posts/01966174-dc40-7923-b80e-6efa99a6100f",
}
out=Path("output");out.mkdir(exist_ok=True)
report=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=["--no-sandbox","--use-gl=angle","--use-angle=swiftshader","--enable-webgl"])
    context=browser.new_context(viewport={"width":1370,"height":900})
    for slug,url in SOURCE.items():
        page=context.new_page()
        rec={"name":slug,"url":url,"events":[],"downloaded":False}
        target=out/(slug+".glb")
        encrypted=out/(slug+".meshy")
        def inspect_response(response):
            path=urlparse(response.url).path.lower()
            if path.endswith((".meshy",".glb")) or "/model.meshy" in path:
                event={"status":response.status,"path":path[:220]}
                rec["events"].append(event)
                if response.status!=200:return
                try:
                    data=response.body()
                    magic=data[:8]
                    if len(data)>1000 and len(data)<95_000_000 and magic in (b"MESHY.AI",b"glTF"):
                        dst=target if magic.startswith(b"glTF") else encrypted
                        dst.write_bytes(data)
                        event.update({"bytes":len(data),"magic":magic.decode("ascii","ignore"),"saved":dst.name})
                except Exception as e:
                    event["error"]=str(e)[:160]
        page.on("response",inspect_response)
        try:
            resp=page.goto(url,wait_until="domcontentloaded",timeout=48000)
            rec["page_status"]=resp.status if resp else None
            page.wait_for_timeout(16000)
            rec["title"]=page.title()
            rec["canvas_count"]=page.locator("canvas").count()
            if encrypted.exists() and not target.exists():
                js,wasm=ensure_loader()
                decrypt_meshy(str(encrypted),str(target),js,wasm)
            if target.exists():
                info=validate_glb(str(target))
                with target.open("rb") as stream:
                    hdr=stream.read(20)
                    length=struct.unpack("<I",hdr[12:16])[0]
                    doc=json.loads(stream.read(length))
                triangles=0
                for mesh in doc.get("meshes",[]):
                    for primitive in mesh.get("primitives",[]):
                        idx=primitive.get("indices")
                        if idx is not None:
                            triangles+=int(doc["accessors"][idx]["count"])//3
                rec.update({"downloaded":True,"valid_glb":True,"triangles":triangles,**info})
            print("RESULT",json.dumps(rec,ensure_ascii=False)[:1700],flush=True)
        except Exception as e:
            rec["error"]=str(e)[:500]
            print("FAILED",slug,rec["error"],flush=True)
        finally:
            encrypted.unlink(missing_ok=True)
            report.append(rec)
            (out/"models_3d_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
            page.close()
    browser.close()
print("DOWNLOAD_SUCCESSES",sum(r["downloaded"] for r in report),"OF",len(report),flush=True)
