#!/usr/bin/env python3
"""Mirror approved runtime asset URLs and all external glTF dependencies.
No geometry, materials, textures or animations are modified.
"""
import argparse, hashlib, json, pathlib, posixpath, struct, time, urllib.parse, urllib.request

LIMIT=75*1024*1024
def download(url):
    scheme=urllib.parse.urlsplit(url).scheme
    if scheme != "https":
        raise ValueError("Only HTTPS asset sources accepted: "+url)
    last=None
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"ProjectGenesisAssetMirror/1.0","Accept":"*/*"})
            with urllib.request.urlopen(req,timeout=75) as rsp:
                if rsp.status!=200: raise ValueError("HTTP "+str(rsp.status))
                data=rsp.read(LIMIT+1)
            if not data or len(data)>LIMIT: raise ValueError("Empty or oversized asset")
            return data
        except Exception as e:
            last=e
            if attempt<2: time.sleep(3*(attempt+1))
    raise RuntimeError(f"{url}: {last}")
def save(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(data)
    return {"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()}
def check_model(filename,data):
    suffix=filename.lower().split("?")[0].rsplit(".",1)[-1]
    if suffix=="glb":
        if len(data)<20 or data[:4]!=b"glTF" or struct.unpack_from("<I",data,8)[0]!=len(data):
            raise ValueError("Invalid GLB header / length")
        return []
    if suffix!="gltf": raise ValueError("Only GLB/glTF can be mirrored: "+filename)
    model=json.loads(data.decode("utf-8"))
    if model.get("asset",{}).get("version")!="2.0":
        raise ValueError("Not glTF 2.0")
    return [o["uri"] for tag in ("buffers","images") for o in model.get(tag,[]) if o.get("uri") and not o["uri"].startswith("data:")]
def local_relative(uri):
    p=urllib.parse.urlsplit(uri)
    if p.scheme or p.netloc or p.query: raise ValueError("External/nondeterministic glTF subresource: "+uri)
    raw=urllib.parse.unquote(p.path).replace("\\","/")
    normalized=posixpath.normpath("src/"+raw)
    if normalized.startswith("../") or normalized==".." or normalized.startswith("/") or not normalized.startswith("src/"):
        raise ValueError("Unsafe glTF texture or buffer path: "+uri)
    return normalized
def mirror_one(item, root):
    ident=item["id"]
    if not ident.replace("_","").isalnum(): raise ValueError("Invalid id")
    origin=item["source"]
    name=urllib.parse.unquote(urllib.parse.urlsplit(origin).path.rsplit("/",1)[-1])
    if "/" in name or name in (".",".."): raise ValueError("Invalid filename")
    target=root/ident/"src"/name
    primary=download(origin)
    dependencies=check_model(name,primary)
    files={str(target.relative_to(root)):save(target,primary)}
    for uri in dependencies:
        rel=local_relative(uri)
        url=urllib.parse.urljoin(origin,uri)
        subtarget=root/ident/rel
        files[str(subtarget.relative_to(root))]=save(subtarget,download(url))
    return {"id":ident,"source":origin,"entry":str(target.relative_to(root)).replace("\\","/"),"files":files}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",required=True)
    p.add_argument("--root",required=True)
    p.add_argument("--lock",required=True)
    a=p.parse_args()
    manifest=json.loads(pathlib.Path(a.manifest).read_text(encoding="utf-8"))
    root=pathlib.Path(a.root).resolve()
    successes=[];failures=[]
    for item in manifest["items"]:
        try:
            info=mirror_one(item,root);successes.append(info)
            print(f"OK {info['id']}: {len(info['files'])} files",flush=True)
        except Exception as e:
            failures.append({"id":item["id"],"reason":str(e)})
            print(f"FAILED {item['id']}: {e}",flush=True)
    result={"schema":1,"assets":successes,"failures":failures,"complete":not failures}
    pathlib.Path(a.lock).parent.mkdir(parents=True,exist_ok=True)
    pathlib.Path(a.lock).write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"Mirror: {len(successes)} successful, {len(failures)} failed.")
    if failures: raise SystemExit(1)
if __name__=="__main__":main()
