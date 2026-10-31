# Project Genesis — probe official CC0 photogrammetry of real dead hardwood
# No login, no paid services; accepts only official Poly Haven download URLs.
import requests, json, hashlib, pathlib, sys, zipfile, urllib.parse
out=pathlib.Path("output_charcoal_scan_v005");out.mkdir(exist_ok=True)
asset="dead_tree_trunk_02"
manifest={"asset":asset,"source":"https://polyhaven.com/a/"+asset,"license":"CC0-1.0","used_in_game":False}
url="https://api.polyhaven.com/files/"+asset
r=requests.get(url,timeout=35);manifest["api_http"]=r.status_code
if r.status_code!=200:
    (out/"MANIFEST.json").write_text(json.dumps(manifest,indent=2))
    print("No public scan accessible",r.status_code)
    sys.exit(0)
data=r.json();manifest["top_keys"]=list(data)
candidates=[]
def walk(obj,path=""):
    if isinstance(obj,dict):
        if isinstance(obj.get("url"),str):
            v=obj["url"]
            if v.startswith("https://dl.polyhaven.org/"):
                candidates.append({"path":path,"url":v,"size":obj.get("size")})
        for k,v in obj.items():walk(v,path+"/"+str(k))
    elif isinstance(obj,list):
        for i,v in enumerate(obj):walk(v,path+"/"+str(i))
walk(data)
manifest["candidate_count"]=len(candidates)
manifest["asset_options"]=[{"path":x["path"],"size":x["size"]} for x in candidates[:55]]
def score(it):
    p=it["path"].lower();u=it["url"].lower()
    pri=0
    if "gltf" in p:pri+=80
    if "glb" in p:pri+=80
    if "blend" in p:pri+=40
    if "zip" in p or ".zip" in u:pri+=35
    if "1k" in p or "1k" in u:pri+=35
    if "2k" in p or "2k" in u:pri+=23
    if "4k" in p or "4k" in u:pri-=25
    if "8k" in p or "8k" in u:pri-=65
    if "diff" in p or "normal" in p or "rough" in p:pri-=100
    return pri
candidates.sort(key=score,reverse=True)
for c in candidates[:10]:
    try:
        print("Scan candidate:",c["path"],"size",c["size"],"score",score(c))
        resp=requests.get(c["url"],timeout=90,stream=True)
        if resp.status_code!=200:continue
        ext=pathlib.Path(urllib.parse.urlparse(c["url"]).path).suffix.lower()
        if ext not in (".zip",".blend",".glb",".gltf"):continue
        dest=out/("wood_cc0_scan"+ext)
        h=hashlib.sha256();n=0
        with dest.open("wb") as f:
            for chunk in resp.iter_content(1024*256):
                if not chunk:continue
                n+=len(chunk)
                if n>90000000:raise RuntimeError("scan >90MB cutoff")
                h.update(chunk);f.write(chunk)
        if n<100000:dest.unlink();continue
        manifest.update({"downloaded":True,"format":ext,"path":str(dest),"bytes":n,"sha256":h.hexdigest(),"selected_variant":c["path"]})
        if ext==".zip":
            with zipfile.ZipFile(dest) as zz:
                manifest["zip_files"]=zz.namelist()[:80]
        break
    except Exception as ex:
        print("Candidate failed",repr(ex))
        continue
manifest.setdefault("downloaded",False)
(out/"MANIFEST.json").write_text(json.dumps(manifest,indent=2))
print("SCAN_PROBE",json.dumps({k:v for k,v in manifest.items() if k!="asset_options"}))
