from pathlib import Path
from meshy_glb.core import fetch_glb,download_stream,decrypt_meshy,ensure_loader,validate_glb
import json,struct
out=Path("output");out.mkdir(exist_ok=True)
target=out/"ash_logs_stack.glb"
task_id="019fa664-ec99-77e5-be30-95e77a8867fe"
url=f"https://www.meshy.ai/3d-models/stacked-logs-{task_id}"
errors=[]
try:
    print("TASK_RESOLVE",url,flush=True)
    fetch_glb(url,str(target))
except Exception as exc:
    errors.append("task api: "+str(exc))
    print("TASK_UNAVAILABLE",str(exc)[:240],flush=True)
if not target.is_file():
    encrypted=out/"ash_logs_stack.meshy"
    uri="https://www.meshy.ai/misc/cdn-models/05505003-bd10-42da-9744-bb289c596aaa/tasks/019fa664-ec99-77e5-be30-95e77a8867fe/output/model.meshy"
    try:
        print("DIRECT_PUBLIC_VIEWER_ASSET",uri,flush=True)
        download_stream(uri,str(encrypted))
        assert encrypted.stat().st_size>1000
        print("ENCRYPTED_ASSET_READY",encrypted.stat().st_size,flush=True)
        js,wasm=ensure_loader()
        decrypt_meshy(str(encrypted),str(target),js,wasm)
    except Exception as exc:
        errors.append("public asset: "+str(exc))
        print("PUBLIC_ASSET_UNAVAILABLE",str(exc)[:300],flush=True)
    finally:
        encrypted.unlink(missing_ok=True)
info={"url":"https://www.meshy.ai/posts/019fa73f-8d7b-7d49-b622-167c37bd8455","attempts":errors,"downloaded":target.is_file()}
if target.exists():
    info.update(validate_glb(str(target)))
    with target.open("rb") as f:
        head=f.read(20)
        length=struct.unpack("<I",head[12:16])[0]
        glb=json.loads(f.read(length))
    tris=sum(glb["accessors"][pr["indices"]]["count"]//3 for m in glb["meshes"] for pr in m["primitives"] if "indices" in pr)
    info["triangles"]=tris
(out/"stacked_logs_report.json").write_text(json.dumps(info,ensure_ascii=False,indent=2))
print("FINAL_REPORT",json.dumps(info,ensure_ascii=False)[:1800],flush=True)
