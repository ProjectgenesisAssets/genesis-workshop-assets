#!/usr/bin/env python3
"""Download real CC0 PBR scans from ambientCG; strict provenance, no silent placeholder."""
import os,sys,json,urllib.request,urllib.parse,zipfile,io,hashlib,pathlib
kind=os.environ.get("ASSET_KIND","").replace("asset/","")
queries={"dry-oak-wood":"wood","dry-ash-wood":"wood","tanned-cowhide":"leather","tanned-goatskin":"leather","hemp-cord":"rope","linen-thread":"fabric"}
if kind not in queries:raise SystemExit("Unknown asset "+kind)
headers={"User-Agent":"ProjectGenesisAssetResearch/0.1"}
def get(url):
 req=urllib.request.Request(url,headers=headers)
 with urllib.request.urlopen(req,timeout=45) as r:return r.read()
params=urllib.parse.urlencode({"type":"material","q":queries[kind],"limit":30,"include":"title,tags,downloads"})
data=json.loads(get("https://ambientcg.com/api/v3/assets?"+params))
assets=data.get("assets",[])
tokens={"dry-oak-wood":["wood","oak"],"dry-ash-wood":["wood","ash"],"tanned-cowhide":["leather","cow"],"tanned-goatskin":["leather","goat"],"hemp-cord":["rope","hemp"],"linen-thread":["fabric","linen"]}[kind]
def rank(a):
 txt=(a.get("title","")+" "+str(a.get("tags",[]))).lower()
 return sum(3 if t in txt else 0 for t in tokens)
assets.sort(key=rank,reverse=True)
if not assets:raise SystemExit("No scans found; never silently substitute procedural textures")
asset=assets[0]
dls=asset.get("downloads",[])
choices=[d for d in dls if d.get("attributes")=="2K-JPG" and d.get("url")]
if not choices:raise SystemExit("No 2K-JPG pack: "+asset["id"])
dl=choices[0]
root=pathlib.Path("sources")/kind;root.mkdir(parents=True,exist_ok=True)
raw=get(dl["url"])
(root/"source.zip").write_bytes(raw)
with zipfile.ZipFile(io.BytesIO(raw)) as z:
 for member in z.infolist():
  if not member.is_dir() and member.filename.lower().endswith((".jpg",".jpeg",".png")):
   output=root/pathlib.Path(member.filename).name
   output.write_bytes(z.read(member))
manifest={"asset":kind,"selected_id":asset["id"],"title":asset.get("title"),"source_url":"https://ambientcg.com/a/"+asset["id"],"download_url":dl["url"],"license":"CC0 1.0","zip_sha256":hashlib.sha256(raw).hexdigest(),"query":queries[kind],"score_heuristic":rank(asset),"manual_reference_approval":False,"note":"Automatic category match only; verify species/fiber/hide identity before quality approval"}
(root/"provenance.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
